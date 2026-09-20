"""
APKCombo APK downloader.

APKCombo stores APKs on Cloudflare R2 storage and serves them via signed
redirect URLs at https://apkcombo.com/r2?u=<encoded-r2-url>.

Scraping flow (confirmed working via live testing, Sept 2026):
  1. GET https://apkcombo.com/{slug}/{package}/download/phone-{version}-apk
     → HTML page containing /r2?u=<url-encoded R2 storage URL> links
  2. Parse all /r2?u= links; prefer non-SECONDARY .apk over .apks bundles
  3. Return the full https://apkcombo.com/r2?u=<encoded> URL — apkcombo.com
     acts as the signed redirect proxy for the R2 CDN, which then serves the
     real APK bytes (200 OK, correct Content-Type).

App slug discovery:
  - Configured via apps/apkcombo/{app}.json: { "slug": "youtube", "package": "..." }
  - If slug is missing/wrong, fall back to APKCombo's search endpoint.
  - Slug can also be inferred from the package name (e.g. com.google.android.youtube
    → try "youtube", "android", etc.).

No Cloudflare protection on the actual download flow — only the R2 proxy step
requires going through apkcombo.com/r2, which does not challenge bots.
"""

import re
import logging
import time
from urllib.parse import quote, unquote, urlencode

from bs4 import BeautifulSoup
from curl_cffi import requests as cffi_requests

_BASE = "https://apkcombo.com"

# Use a modern Chrome fingerprint — APKCombo is much lighter than APKMirror CF
_SESSION = None


def _session():
    global _SESSION
    if _SESSION is None:
        _SESSION = cffi_requests.Session(impersonate="chrome124")
    return _SESSION


def _get(url: str, **kwargs) -> cffi_requests.Response:
    """Polite GET with a short delay."""
    time.sleep(1.0)
    kwargs.setdefault("timeout", 25)
    return _session().get(url, **kwargs)


# ──────────────────────────────────────────────────────────────────────────────
# Slug discovery
# ──────────────────────────────────────────────────────────────────────────────

def _slug_candidates(config: dict) -> list[str]:
    """Return candidate APKCombo slugs to try, most-specific first."""
    slug = config.get("slug", "")
    package = config.get("package", "")
    parts = package.split(".")

    candidates = []
    if slug:
        candidates.append(slug)

    # Infer slug from package name parts
    if len(parts) >= 3:
        candidates.append(parts[-1])           # e.g. "youtube"
        candidates.append(parts[1])            # e.g. "google"
        candidates.append(f"{parts[1]}-{parts[-1]}")  # e.g. "google-youtube"

    # Deduplicate, preserve order
    seen = set()
    result = []
    for c in candidates:
        if c and c not in seen:
            seen.add(c)
            result.append(c)
    return result


# Two-letter path segments on APKCombo are locale prefixes (e.g. /pt/...),
# never app slugs. Reserved path heads are not slugs either.
_LOCALE_OR_RESERVED = {
    "search", "download", "app", "apps", "category", "categories",
    "developer", "developers", "collection", "downloader", "old-versions",
}


def _discover_slug(package: str) -> str | None:
    """Search APKCombo for the app to discover its slug.

    APKCombo search pages are locale-prefixed (e.g. /pt/search/<pkg>) and
    result lists render via JS, so the only reliable signal is an href ending
    in /{package}: the slug is the segment immediately before the package,
    skipping any locale/reserved segment.
    """
    try:
        url = f"{_BASE}/search?q={quote(package)}"
        logging.info(f"APKCombo: searching slug for {package}")
        resp = _get(url)
        if resp.status_code != 200:
            return None
        soup = BeautifulSoup(resp.content, "html.parser")
        for a in soup.find_all("a", href=True):
            href = a["href"].split("?", 1)[0].strip("/")
            parts = [p for p in href.split("/") if p]
            if len(parts) < 2 or parts[-1] != package:
                continue
            slug = parts[-2]
            if len(slug) == 2 or slug.lower() in _LOCALE_OR_RESERVED:
                # Locale prefix (e.g. pt/jiohotstar/<pkg>) — step one more up
                if len(parts) >= 3:
                    slug = parts[-3]
                else:
                    continue
            if slug and len(slug) != 2 and slug.lower() not in _LOCALE_OR_RESERVED:
                logging.info(f"APKCombo: discovered slug '{slug}' for {package}")
                return slug
    except Exception as e:
        logging.debug(f"APKCombo: slug discovery error: {e}")
    return None


# ──────────────────────────────────────────────────────────────────────────────
# Version list scraping
# ──────────────────────────────────────────────────────────────────────────────

def _scrape_versions(slug: str, package: str) -> list[dict] | None:
    """Scrape the old-versions page for a package.

    Returns a list of {"version": str, "path": str} dicts or None on failure.
    Example path: /youtube/com.google.android.youtube/download/phone-21.37.42-apk
    """
    url = f"{_BASE}/{slug}/{package}/old-versions/"
    try:
        resp = _get(url)
        if resp.status_code != 200:
            return None
        soup = BeautifulSoup(resp.content, "html.parser")
        entries = []
        seen = set()
        for a in soup.find_all("a", href=re.compile(r"/download/phone-[^/]+-apk")):
            href = a.get("href", "")
            m = re.search(r"/download/phone-([^/]+)-apk", href)
            if m:
                ver = m.group(1)
                if ver not in seen:
                    seen.add(ver)
                    entries.append({"version": ver, "path": href})
        if entries:
            logging.info(f"APKCombo: found {len(entries)} versions for {package} at {url}")
        return entries or None
    except Exception as e:
        logging.debug(f"APKCombo: version list fetch failed for {url}: {e}")
        return None


# ──────────────────────────────────────────────────────────────────────────────
# Download link extraction
# ──────────────────────────────────────────────────────────────────────────────

def _extract_download_link(slug: str, package: str, version: str) -> str | None:
    """Scrape the version download page and return the best APKCombo R2 proxy URL.

    APKCombo hosts files on Cloudflare R2. The download page contains
    /r2?u=<url-encoded R2 URL> hrefs. Following these through apkcombo.com
    delivers the actual APK (the R2 URL is signed and time-limited, but
    going via apkcombo.com/r2 refreshes the signature automatically).

    We prefer:
      1. Non-SECONDARY .apk files (primary build)
      2. SECONDARY .apk files
      3. .apks bundles (require APKEditor merge)
    """
    url = f"{_BASE}/{slug}/{package}/download/phone-{version}-apk"
    try:
        resp = _get(url)
        if resp.status_code != 200:
            logging.debug(f"APKCombo: download page {url} returned {resp.status_code}")
            return None

        # Extract all /r2?u= raw hrefs from the page
        r2_raw = re.findall(r'/r2\?u=([^\s"\'<>&]+)', resp.text)
        if not r2_raw:
            logging.debug(f"APKCombo: no /r2 links found on {url}")
            return None

        # Decode and categorise each link
        apk_primary = []
        apk_secondary = []
        apks_bundles = []

        for raw in r2_raw:
            decoded = unquote(raw)
            if "SECONDARY" in decoded.upper():
                if ".apk?" in decoded or decoded.endswith(".apk"):
                    apk_secondary.append(raw)
                else:
                    apks_bundles.append(raw)
            elif ".apk?" in decoded or decoded.endswith(".apk"):
                apk_primary.append(raw)
            elif ".apks?" in decoded or decoded.endswith(".apks"):
                apks_bundles.append(raw)

        # Pick the best available link
        chosen = None
        if apk_primary:
            chosen = apk_primary[0]
            logging.info(f"APKCombo: selected primary APK for {package} {version}")
        elif apk_secondary:
            chosen = apk_secondary[0]
            logging.warning(f"APKCombo: using SECONDARY APK for {package} {version} (no primary found)")
        elif apks_bundles:
            chosen = apks_bundles[0]
            logging.warning(f"APKCombo: using .apks bundle for {package} {version} (no standalone APK found)")

        if chosen:
            download_url = f"{_BASE}/r2?u={chosen}"
            logging.info(f"APKCombo: download URL for {package} {version}: {download_url[:120]}")
            return download_url

    except Exception as e:
        logging.debug(f"APKCombo: error extracting download link from {url}: {e}")
    return None


# ──────────────────────────────────────────────────────────────────────────────
# Public interface
# ──────────────────────────────────────────────────────────────────────────────

def get_latest_version(app_name: str, config: dict) -> str | None:
    """Return the latest version string available on APKCombo for this app."""
    package = config.get("package", "")

    all_slugs = _slug_candidates(config)

    for slug in all_slugs:
        entries = _scrape_versions(slug, package)
        if entries:
            # Versions on the page are newest-first; take the first one
            latest = entries[0]["version"]
            logging.info(f"APKCombo: latest version for {app_name} is {latest}")
            return latest

    # Discover slug via search and try again
    discovered = _discover_slug(package)
    if discovered:
        entries = _scrape_versions(discovered, package)
        if entries:
            return entries[0]["version"]

    logging.error(f"APKCombo: could not determine latest version for {app_name}")
    return None


def get_download_link(version: str, app_name: str, config: dict) -> str | None:
    """Return the APKCombo R2-proxy download URL for a specific version.

    Args:
        version:  Version string as returned by get_latest_version or the CLI
                  (e.g. "21.37.42"). Parenthetical build suffixes are stripped.
        app_name: App key used for logging only.
        config:   Dict from apps/apkcombo/{app}.json.

    Returns:
        A https://apkcombo.com/r2?u=... URL that serves the APK when followed,
        or None if the version was not found.
    """
    package = config.get("package", "")

    # Strip parenthetical build number if present (e.g. "21.37.42(1234)" → "21.37.42")
    version = re.sub(r'\(\d+\)$', '', version).strip()

    all_slugs = _slug_candidates(config)

    # Try all known slugs first
    for slug in all_slugs:
        dl = _extract_download_link(slug, package, version)
        if dl:
            return dl

        # Also check the version list to find a close match
        entries = _scrape_versions(slug, package)
        if not entries:
            continue

        # Find exact or prefix-matching version
        for entry in entries:
            ev = entry["version"]
            is_match = (
                ev == version
                or ev.startswith(version + ".")
                or ev.startswith(version + "-")
            )
            if is_match:
                dl = _extract_download_link(slug, package, ev)
                if dl:
                    if ev != version:
                        logging.warning(
                            f"APKCombo: exact version {version} not found; "
                            f"using prefix match '{ev}' for {app_name}"
                        )
                    return dl

    # Discover slug via search and retry
    discovered = _discover_slug(package)
    if discovered and discovered not in all_slugs:
        dl = _extract_download_link(discovered, package, version)
        if dl:
            return dl

    logging.error(f"APKCombo: no download link found for {app_name} {version}")
    return None
