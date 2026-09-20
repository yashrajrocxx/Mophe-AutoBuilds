"""
Manual direct-link APK source.

Some apps (e.g. Brave, Vivaldi) are unreliable on every automated scraper
but publish official APKs at stable URLs (GitHub releases, official CDN).
This module lets those apps pin a manually-provided download URL:

    apps/direct/<app>.json:
    {
      "package": "com.brave.browser",
      "version": "1.95.101",
      "url": "https://github.com/.../brave-1.95.101.apk"
    }

Behavior:
  - get_latest_version() returns the pinned `version` (no network).
  - get_download_link() returns the pinned `url` ONLY when the requested
    version matches the pinned version (exact or prefix). Otherwise it
    returns None so the normal scraper cascade can try other versions.
  - An empty/missing `url` means "not configured yet" → returns None so
    scrapers are used as fallback until the user fills in the link.

The `direct` source is intentionally first in the __main__.py download
cascade: when a manual link matches, it always wins; when absent or
version-mismatched, the build falls through to Play Store / scrapers.
"""

import logging


def get_latest_version(app_name: str, config: dict) -> str | None:
    """Return the pinned version from apps/direct/<app>.json (no network)."""
    version = (config.get("version") or "").strip()
    if version:
        logging.info(f"Direct: pinned version for {app_name} is {version}")
        return version
    logging.debug(f"Direct: no pinned version for {app_name}")
    return None


def get_download_link(version: str, app_name: str, config: dict) -> str | None:
    """Return the pinned URL when it matches the requested version."""
    url = (config.get("url") or "").strip()
    if not url:
        logging.debug(f"Direct: no URL configured for {app_name}, falling through to scrapers")
        return None
    if not url.startswith(("http://", "https://")):
        logging.warning(f"Direct: ignoring non-HTTP URL for {app_name}: {url[:60]}")
        return None

    pinned = (config.get("version") or "").strip()
    wanted = (version or "").strip()
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
