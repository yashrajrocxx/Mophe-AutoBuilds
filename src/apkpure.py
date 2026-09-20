import re
import logging
import time
import requests as std_requests

from src import session
from bs4 import BeautifulSoup
from urllib.parse import quote

# Standard browser headers for web scraping (apkpure.net — no Cloudflare)
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                  'AppleWebKit/537.36 (KHTML, like Gecko) '
                  'Chrome/124.0.0.0 Safari/537.36',
    'Accept-Language': 'en-US,en;q=0.9',
    'Referer': 'https://apkpure.net/',
}

# Headers for the unofficial APKPure mobile app API (api.pureapk.com).
# This API is reverse-engineered from the APKPure Android app.
# It returns version_code per version, which is critical for resolving
# historical versionCodes without relying on Exodus Privacy.
_MOBILE_API_HEADERS = {
    'User-Agent': 'APKPure/3.20.2 (Linux; U; Android 11; en_US)',
    'x-sv': '7',           # security version — tied to APKPure app release
    'x-abis': 'arm64-v8a,armeabi-v7a,armeabi',
    'x-gp': '1',
    'Accept': 'application/json',
}

_MOBILE_API_BASE = "https://api.pureapk.com/m/v3/cms"
_CDN_BASE = "https://d.apkpure.net/b/APK"

BASE = "https://apkpure.net"
_SLEEP = 1.2


def _get(url: str, **kwargs):
    time.sleep(_SLEEP)
    kwargs.setdefault("headers", HEADERS)
    kwargs.setdefault("timeout", 20)
    return session.get(url, **kwargs)


def _slug_candidates(config: dict) -> list[str]:
    """Return candidate APKPure URL slugs to try, most-specific first."""
    name = config.get("name", "")
    package = config.get("package", "")
    parts = package.split(".")
    candidates = [name]
    if len(parts) >= 3:
        # e.g. com.instagram.android -> instagram, editor
        candidates.append(f"{parts[1]}-{parts[-1]}")
        candidates.append(parts[-1])
        candidates.append(parts[1])
    candidates.append(package.replace(".", "-"))
    # Deduplicate preserving order
    seen = set()
    result = []
    for c in candidates:
        if c and c not in seen:
            seen.add(c)
            result.append(c)
    return result


def _discover_slug(package: str) -> str | None:
    """Search APKPure by package name to find the correct app slug.
    This is the most reliable way since the package name is unique."""
    try:
        search_url = f"{BASE}/search?q={quote(package)}"
        logging.info(f"APKPure: searching for package {package}")
        resp = _get(search_url)
        if resp.status_code != 200:
            return None
        soup = BeautifulSoup(resp.content, "html.parser")
        # APKPure search results: links like /instagram/com.instagram.android
        for a in soup.find_all("a", href=True):
            href = a["href"].strip("/")
            # Pattern: {slug}/{package}
            if href.endswith(f"/{package}") or href.endswith(f"/{package}/"):
                slug = href.split("/")[0]
                if slug:
                    logging.info(f"APKPure: discovered slug '{slug}' for {package}")
                    return slug
    except Exception as e:
        logging.debug(f"APKPure slug discovery failed: {e}")
    return None


# ──────────────────────────────────────────────────────────────────────────────
# APKPure Mobile API helpers
# ──────────────────────────────────────────────────────────────────────────────

def get_version_code_from_api(package: str, version_name: str) -> int | None:
    """Query the unofficial APKPure mobile API for the versionCode of a specific version.

    The API at api.pureapk.com is reverse-engineered from the APKPure Android app.
    It returns version_code per version and has no Cloudflare protection.

    This is the primary replacement for Exodus Privacy versionCode resolution.

    Args:
        package:      Android package name (e.g. "com.google.android.youtube")
        version_name: Human-readable version string (e.g. "19.16.39")

    Returns:
        The integer versionCode, or None if the version wasn't found / API unavailable.
    """
    try:
        url = f"{_MOBILE_API_BASE}/app_version?pkg={package}"
        logging.info(f"APKPure API: resolving versionCode for {package} {version_name}")
        resp = std_requests.get(url, headers=_MOBILE_API_HEADERS, timeout=20)
        if resp.status_code != 200:
            logging.debug(f"APKPure API: status {resp.status_code} for {package}")
            return None

        data = resp.json()
        # Response structure: {"data": {"list": [{"version_name": "...", "version_code": "..."}]}}
        version_list = (
            data.get("data", {}).get("list")
            or data.get("list")
            or (data if isinstance(data, list) else [])
        )
        if not version_list:
            logging.debug(f"APKPure API: empty version list for {package}")
            return None

        # Collect all matching entries (same version name may have multiple ABIs)
        codes = []
        for entry in version_list:
            vn = entry.get("version_name") or entry.get("version", "")
            vc = entry.get("version_code") or entry.get("versionCode")
            if not vc:
                continue
            # Exact match or prefix match (e.g. "19.16.39" matches "19.16.39-arm64")
            if vn == version_name or vn.startswith(version_name + ".") or vn.startswith(version_name + "-"):
                try:
                    codes.append(int(vc))
                except (ValueError, TypeError):
                    pass

        if codes:
            resolved = max(codes)  # Prefer the highest code (most specific ABI variant)
            logging.info(f"APKPure API: resolved {package} {version_name} → versionCode {resolved}")
            return resolved

        logging.debug(f"APKPure API: version '{version_name}' not found in list for {package}")
    except Exception as e:
        logging.debug(f"APKPure API: error resolving versionCode for {package}: {e}")
    return None


def _cdn_download_url(package: str, version_name: str | None = None) -> str | None:
    """Build a direct APKPure CDN download URL.

    APKPure's CDN at d.apkpure.net serves APKs directly without HTML scraping.
    This is faster and more reliable than following the web scraper flow.

    Preferred: resolve versionCode via mobile API → ?versioncode={vc}.
    Fallback (spec): https://d.apkpure.net/b/APK/{package}?version={version}
    Latest:          https://d.apkpure.net/b/APK/{package}?version=latest

    URLs are returned optimistically — the downloader verifies bytes on GET.
    A best-effort HEAD is attempted to resolve redirects, but HEAD failure
    does not discard the URL (HEAD is often blocked while GET works).

    Args:
        package:      Android package name
        version_name: Specific version to download; None/empty = latest

    Returns:
        The direct CDN URL, or None only when no URL could be constructed.
    """
    try:
        if version_name:
            vc = get_version_code_from_api(package, version_name)
            if vc:
                url = f"{_CDN_BASE}/{package}?versioncode={vc}"
                logging.info(f"APKPure CDN: direct download URL for {package} {version_name} (vc={vc}): {url}")
                return url
            # Spec fallback: version query param (no slug discovery needed)
            url = f"{_CDN_BASE}/{package}?version={quote(version_name)}"
        else:
            url = f"{_CDN_BASE}/{package}?version=latest"

        # Best-effort reachability probe. A 403/404/410 means this exact
        # build is not on the CDN (e.g. region-specific apps like JioHotstar)
        # — return None so the caller falls through to HTML scraping instead
        # of handing the downloader a dead URL. Other statuses and network
        # errors keep the optimistic URL (HEAD is sometimes blocked while
        # GET works, and the downloader verifies bytes on GET anyway).
        try:
            resp = std_requests.head(url, headers={**_MOBILE_API_HEADERS, 'User-Agent': 'Mozilla/5.0'},
                                     allow_redirects=True, timeout=20)
            if resp.status_code in (403, 404, 410):
                logging.info(f"APKPure CDN: {resp.status_code} for {package} {version_name or 'latest'} — falling back to HTML scrape")
                return None
            if resp.status_code == 200 and resp.url:
                logging.info(f"APKPure CDN: resolved {package} → {str(resp.url)[:120]}")
                return str(resp.url)
        except Exception as e:
            logging.debug(f"APKPure CDN: HEAD probe failed for {package} (using direct URL): {e}")
        logging.info(f"APKPure CDN: direct download URL for {package} {version_name or 'latest'}: {url}")
        return url
    except Exception as e:
        logging.debug(f"APKPure CDN: direct URL failed for {package}: {e}")
    return None

def _try_get_version_list(slug: str, package: str) -> list[dict] | None:
    """Fetch the version list page for a given (slug, package) combo.
    Returns a list of {version, download_url} dicts, or None on failure."""
    url = f"{BASE}/{slug}/{package}/versions"
    try:
        resp = _get(url)
        if resp.status_code != 200:
            return None
        logging.info(f"APKPure: version list found at {resp.url}")
        soup = BeautifulSoup(resp.content, "html.parser")
        entries = []

        # APKPure version list: each version is in a <div class="ver-item"> or similar
        # The version number is in data-dt-version, href has the download path
        for item in soup.find_all(attrs={"data-dt-version": True}):
            ver = item.get("data-dt-version", "").strip()
            # Find closest anchor to get the version-specific URL
            a = item.find("a", href=True) or (item if item.name == "a" else None)
            if not a:
                # search parent
                parent = item.parent
                a = parent.find("a", href=True) if parent else None
            href = a["href"] if a else None
            if ver:
                entries.append({"version": ver, "href": href})

        # Fallback: look for links to /download/{version}
        if not entries:
            for a in soup.find_all("a", href=True):
                m = re.search(r"/download/([0-9][^/\"']+)", a["href"])
                if m:
                    entries.append({"version": m.group(1), "href": a["href"]})

        return entries if entries else None
    except Exception as e:
        logging.debug(f"APKPure version list fetch failed for {url}: {e}")
        return None


def _get_direct_download(slug: str, package: str, version: str) -> str | None:
    """Try the direct download URL pattern (APKPure's canonical structure)."""
    url = f"{BASE}/{slug}/{package}/download/{version}"
    try:
        resp = _get(url)
        if resp.status_code != 200:
            return None
        soup = BeautifulSoup(resp.content, "html.parser")

        # Try various known selectors for the actual file link
        for selector in [
            "a#download_link",
            "a.download-start-btn",
            "a[href*='apkpure-asset']",
            "a[href*='.apk']",
        ]:
            tag = soup.select_one(selector)
            if tag and tag.get("href"):
                href = tag["href"]
                if href.startswith("http"):
                    return href
                return BASE + href

    except Exception as e:
        logging.debug(f"APKPure direct download failed for {url}: {e}")
    return None


def _normalize(ver: str) -> tuple:
    """Normalize a version string to a comparable tuple of ints."""
    parts = re.split(r"[.\-]", ver)
    result = []
    for p in parts:
        m = re.match(r"(\d+)", p)
        result.append(int(m.group(1)) if m else 0)
    return tuple(result)


def get_latest_version(app_name: str, config: dict) -> str | None:
    package = config.get("package", "")
    # Try candidates in order
    for slug in _slug_candidates(config):
        entries = _try_get_version_list(slug, package)
        if entries:
            # Return the lexicographically highest version
            try:
                best = max(entries, key=lambda e: _normalize(e["version"]))
                logging.info(f"APKPure: latest version for {app_name} is {best['version']}")
                return best["version"]
            except Exception:
                pass

    # Last resort: discover the slug via search
    discovered = _discover_slug(package)
    if discovered:
        entries = _try_get_version_list(discovered, package)
        if entries:
            try:
                best = max(entries, key=lambda e: _normalize(e["version"]))
                return best["version"]
            except Exception:
                pass

    logging.error(f"APKPure: could not determine latest version for {app_name}")
    return None


def get_download_link(version: str, app_name: str, config: dict) -> str | None:
    package = config.get("package", "")
    target_norm = _normalize(version)

    # ── Priority 1: Direct CDN via mobile API versionCode (fastest, most reliable) ──
    cdn_url = _cdn_download_url(package, version)
    if cdn_url:
        logging.info(f"APKPure: CDN direct download for {app_name} {version}")
        return cdn_url

    # ── Priority 2: HTML scraping cascade (slug-based) ──
    all_slugs = list(_slug_candidates(config))

    # Also search APKPure to discover the actual slug (package name is unique)
    discovered = _discover_slug(package)
    if discovered and discovered not in all_slugs:
        all_slugs.insert(0, discovered)  # try discovered first

    for slug in all_slugs:
        # 1. Try the direct download URL (fastest path)
        dl = _get_direct_download(slug, package, version)
        if dl:
            logging.info(f"APKPure: Direct download found for {app_name} {version}")
            return dl

        # 2. Scan the version list for prefix match or closest version
        entries = _try_get_version_list(slug, package)
        if not entries:
            continue

        best_match = None
        closest_entry = None
        closest_diff = None

        for entry in entries:
            ev = entry.get("version", "")
            # Prefix match: "2.371.0" matches "2.371.0", "2.371.0.1", "2.371.0-android"
            is_match = (
                ev == version
                or ev.startswith(version + ".")
                or ev.startswith(version + "-")
            )
            if is_match:
                best_match = entry
                break

            # Track closest for fallback
            try:
                ev_norm = _normalize(ev)
                diff = sum(abs(a - b) * (1000 ** i)
                           for i, (a, b) in enumerate(zip(reversed(ev_norm), reversed(target_norm))))
                if closest_diff is None or diff < closest_diff:
                    closest_diff = diff
                    closest_entry = entry
            except Exception:
                pass

        chosen = best_match or closest_entry
        if chosen:
            chosen_ver = chosen.get("version", "?")
            if not best_match:
                logging.warning(
                    f"APKPure: exact version {version} not found; "
                    f"using closest '{chosen_ver}' for {app_name}"
                )
            # Try the href from the listing page if present
            href = chosen.get("href")
            if href:
                dl_url = href if href.startswith("http") else BASE + href
                # Follow the version page to get the actual download link
                try:
                    resp = _get(dl_url)
                    if resp.status_code == 200:
                        soup = BeautifulSoup(resp.content, "html.parser")
                        for selector in [
                            "a#download_link",
                            "a.download-start-btn",
                            "a[href*='apkpure-asset']",
                            "a[href*='.apk']",
                        ]:
                            tag = soup.select_one(selector)
                            if tag and tag.get("href"):
                                final = tag["href"]
                                return final if final.startswith("http") else BASE + final
                except Exception as e:
                    logging.debug(f"APKPure: failed to follow version href: {e}")

            # Last resort: construct direct download URL with chosen version
            dl = _get_direct_download(slug, package, chosen_ver)
            if dl:
                return dl

    logging.error(f"APKPure: no download link found for {app_name} {version}")
    return None
