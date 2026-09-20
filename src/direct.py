"""
Manual direct-link APK source.

Some apps (e.g. Brave) are unreliable on every automated scraper but publish
official APKs at stable, predictable URLs (GitHub releases, official CDN).
This module lets those apps declare a manual download URL:

    apps/direct/<app>.json (static pin):
    {
      "package": "com.brave.browser",
      "version": "1.95.101",
      "url": "https://github.com/.../brave-1.95.101.apk"
    }

    apps/direct/brave.json (dynamic — no version bumps needed):
    {
      "package": "com.brave.browser",
      "version": "",
      "url": "https://github.com/brave/brave-browser/releases/download/v{version}/Bravemonoarm64.apk"
    }

Behavior:
  - Static: get_download_link() returns the pinned `url` ONLY when the
    requested version matches the pinned version (exact or prefix).
  - Dynamic: `{version}` is substituted with whatever version the patches
    currently require, HEAD-verified, and returned — future patch updates
    need no config change.
  - Anything unmatched, unreachable, or unconfigured returns None so the
    normal scraper cascade is used as fallback.

The `direct` source is intentionally first in the __main__.py download
cascade: when a manual link matches, it always wins; otherwise the build
falls through to Play Store / scrapers.
"""

import logging

from src import session


def _url_exists(url: str) -> bool | None:
    """HEAD-check a templated URL. True = reachable, False = 404, None = unknown (network error)."""
    try:
        resp = session.head(url, allow_redirects=True, timeout=20)
        if resp.status_code == 200:
            return True
        if resp.status_code == 404:
            return False
        return resp.status_code < 400
    except Exception as e:
        logging.debug(f"Direct: HEAD probe failed for {url[:100]}: {e}")
        return None


def get_latest_version(app_name: str, config: dict) -> str | None:
    """Return the pinned version from apps/direct/<app>.json (no network)."""
    version = (config.get("version") or "").strip()
    if version:
        logging.info(f"Direct: pinned version for {app_name} is {version}")
        return version
    logging.debug(f"Direct: no pinned version for {app_name}")
    return None


def get_download_link(version: str, app_name: str, config: dict) -> str | None:
    """Return the pinned URL when it matches the requested version.

    Two modes:
      Static:  "url": "https://.../brave-1.95.101.apk" (+ optional "version"
               pin — mismatched versions fall through to scrapers).
      Dynamic: "url": "https://github.com/brave/brave-browser/releases/download/v{version}/Bravemonoarm64.apk"
               — {version} is substituted with whatever version the patches
               currently require, so no manual bump is needed on patch updates.
               The URL is HEAD-verified (GitHub returns 404 for unknown tags);
               unreachable/unknown versions fall through to scrapers.
    An empty/missing `url` means "not configured yet" → None.
    """
    url = (config.get("url") or "").strip()
    if not url:
        logging.debug(f"Direct: no URL configured for {app_name}, falling through to scrapers")
        return None

    wanted = (version or "").strip()
    if "{version}" in url:
        import re
        clean = re.sub(r"\(\d+\)$", "", wanted).strip()
        if not clean:
            logging.debug(f"Direct: no version to template for {app_name}")
            return None
        built = url.replace("{version}", clean)
        if not built.startswith(("http://", "https://")):
            logging.warning(f"Direct: ignoring non-HTTP URL for {app_name}: {built[:60]}")
            return None
        reachable = _url_exists(built)
        if reachable is False:
            logging.info(f"Direct: templated URL 404 for {app_name} {clean}, falling through to scrapers")
            return None
        logging.info(f"Direct: using dynamic URL for {app_name} {clean}")
        return built

    if not url.startswith(("http://", "https://")):
        logging.warning(f"Direct: ignoring non-HTTP URL for {app_name}: {url[:60]}")
        return None

    pinned = (config.get("version") or "").strip()
    if pinned and wanted and not (
        wanted == pinned
        or pinned.startswith(wanted + ".")
        or pinned.startswith(wanted + "-")
        or wanted.startswith(pinned + ".")
        or wanted.startswith(pinned + "-")
    ):
        logging.info(
            f"Direct: pinned {pinned} does not match requested {wanted} "
            f"for {app_name}, falling through to scrapers"
        )
        return None

    logging.info(f"Direct: using manual URL for {app_name} {pinned or wanted}")
    return url
