"""
Google Play Store APK downloader using PlaystoreDownloader CLI.

Architecture:
  1. Resolve version name → numeric version code via Play Store API
  2. Download splits targeting arm64-v8a, density NONE (nodpi) first
  3. If NONE is rejected by Play servers, retry with density 480 (xxhdpi)
  4. Merge any split APKs into a single monolithic APK via APKEditor
  5. Return the path to the merged APK for signing/patching downstream

PlaystoreDownloader is invoked as a subprocess (CLI tool), NOT imported.
Credentials come from credentials/credentials.json (gitignored locally,
injected from PLAYSTORE_CREDENTIALS_JSON secret in CI).
"""

import json
import logging
import os
import re
import shutil
import subprocess
import tempfile
from pathlib import Path

_CREDS_PATH = Path("credentials/credentials.json")
_TOOL = "playstore-downloader"
_ARCH = "arm64-v8a"
# Device codename that presents as a real arm64 device to Google Play
_DEVICE = "hero2lte"


# ──────────────────────────────────────────────────────────────────────────────
# Internal helpers
# ──────────────────────────────────────────────────────────────────────────────

def _creds_available() -> bool:
    return _CREDS_PATH.exists() and _CREDS_PATH.stat().st_size > 10


def _run(cmd: list[str], **kwargs) -> subprocess.CompletedProcess:
    logging.info(f"PlayStore: running {' '.join(cmd)}")
    return subprocess.run(cmd, **kwargs)


def _resolve_version_code(package: str, version_name: str) -> str | None:
    """
    Ask PlaystoreDownloader to list all available version codes for a package,
    then find the one whose versionName matches the requested string.
    Returns the numeric versionCode as a string, or None if not found.
    """
    if not _creds_available():
        logging.warning("PlayStore: credentials.json not found — skipping version code resolution")
        return None

    try:
        result = _run(
            [_TOOL, "-c", str(_CREDS_PATH), "--list-versions", package],
            capture_output=True, text=True, timeout=60
        )
        if result.returncode != 0:
            logging.warning(f"PlayStore: --list-versions failed: {result.stderr[:200]}")
            return None

        data = json.loads(result.stdout)
        for item in data.get("versions", []):
            # Exact match first
            if item.get("versionName") == version_name:
                return str(item["versionCode"])

        # Prefix-tolerant match: "2.371.0" matches "2.371.0.1", "2.371.0-release", etc.
        for item in data.get("versions", []):
            vn = item.get("versionName", "")
            if vn.startswith(version_name + ".") or vn.startswith(version_name + "-"):
                logging.info(
                    f"PlayStore: prefix-matched '{vn}' to target '{version_name}'"
                )
                return str(item["versionCode"])

        # If still nothing, return the highest available version code
        versions = data.get("versions", [])
        if versions:
            best = max(versions, key=lambda v: v.get("versionCode", 0))
            logging.warning(
                f"PlayStore: exact version '{version_name}' not found; "
                f"using latest available '{best.get('versionName')}'"
            )
            return str(best["versionCode"])

    except json.JSONDecodeError:
        logging.warning("PlayStore: could not parse --list-versions JSON output")
    except subprocess.TimeoutExpired:
        logging.warning("PlayStore: --list-versions timed out")
    except Exception as e:
        logging.warning(f"PlayStore: error resolving version code: {e}")

    return None


def _download_splits(
    package: str,
    version_code: str,
    output_dir: Path,
    density: str,
) -> bool:
    """
    Call PlaystoreDownloader to download a package into output_dir.
    density: "NONE" for nodpi, "480" for xxhdpi fallback.
    Returns True if at least one file was downloaded successfully.
    """
    if output_dir.exists():
        shutil.rmtree(output_dir)
    output_dir.mkdir(parents=True)

    cmd = [
        _TOOL,
        "-c", str(_CREDS_PATH),
        "-p", package,
        "--version-code", version_code,
        "--device-codename", _DEVICE,
        "--arch", _ARCH,
        "-o", str(output_dir),
    ]
    if density and density != "NONE":
        cmd += ["--density", density]
    # density="NONE" means we omit the flag entirely → Play serves nodpi/universal

    try:
        result = _run(cmd, timeout=300)
        if result.returncode != 0:
            logging.warning(f"PlayStore: download exited {result.returncode} (density={density})")
            return False

        files = list(output_dir.iterdir())
        if not files:
            logging.warning(f"PlayStore: no files downloaded (density={density})")
            return False

        logging.info(
            f"PlayStore: ✓ downloaded {len(files)} file(s) with density={density}"
        )
        return True

    except subprocess.TimeoutExpired:
        logging.warning("PlayStore: download timed out")
        return False
    except Exception as e:
        logging.warning(f"PlayStore: download error: {e}")
        return False


def _merge_splits(splits_dir: Path, output_apk: Path) -> bool:
    """
    Use APKEditor to merge a directory of split APKs into one monolithic APK.
    If the directory contains a single .apk, rename it directly (no merge needed).
    """
    files = list(splits_dir.iterdir())
    apk_files = [f for f in files if f.suffix in (".apk", ".apks", ".xapk")]

    if not apk_files:
        logging.error("PlayStore: no APK files found after download")
        return False

    # Single .apk — no merge needed
    if len(apk_files) == 1 and apk_files[0].suffix == ".apk":
        apk_files[0].rename(output_apk)
        logging.info(f"PlayStore: single APK, renamed to {output_apk.name}")
        return True

    # Need APKEditor
    apkeditor = _find_or_download_apkeditor()
    if not apkeditor:
        logging.error("PlayStore: APKEditor not available for split merge")
        return False

    try:
        result = _run(
            ["java", "-jar", str(apkeditor), "m",
             "-i", str(splits_dir), "-o", str(output_apk)],
            timeout=300
        )
        if result.returncode != 0:
            logging.error("PlayStore: APKEditor merge failed")
            return False

        if not output_apk.exists():
            logging.error("PlayStore: merged APK not created")
            return False

        logging.info(f"PlayStore: ✓ merged splits → {output_apk.name}")
        return True

    except subprocess.TimeoutExpired:
        logging.error("PlayStore: APKEditor merge timed out")
        return False
    except Exception as e:
        logging.error(f"PlayStore: merge error: {e}")
        return False


def _find_or_download_apkeditor() -> Path | None:
    """Find APKEditor JAR in current directory, or download it from GitHub."""
    # Check current directory first
    for jar in Path(".").glob("APKEditor*.jar"):
        return jar

    # Try to download
    try:
        from src import utils
        release = utils.detect_github_release("REAndroid", "APKEditor", "latest")
        for asset in release.get("assets", []):
            if asset["name"].startswith("APKEditor") and asset["name"].endswith(".jar"):
                from src.downloader import download_resource
                return download_resource(asset["browser_download_url"])
    except Exception as e:
        logging.warning(f"PlayStore: could not fetch APKEditor: {e}")

    return None


# ──────────────────────────────────────────────────────────────────────────────
# Public interface (matches the contract used by downloader.py)
# ──────────────────────────────────────────────────────────────────────────────

def get_latest_version(app_name: str, config: dict) -> str | None:
    """Return the latest version name available on Google Play."""
    if not _creds_available():
        return None

    package = config.get("package", "")
    if not package:
        return None

    try:
        result = _run(
            [_TOOL, "-c", str(_CREDS_PATH), "--list-versions", package],
            capture_output=True, text=True, timeout=60
        )
        if result.returncode != 0:
            return None

        data = json.loads(result.stdout)
        versions = data.get("versions", [])
        if not versions:
            return None

        best = max(versions, key=lambda v: v.get("versionCode", 0))
        ver = best.get("versionName")
        logging.info(f"PlayStore: latest version for {app_name} is {ver}")
        return ver

    except Exception as e:
        logging.warning(f"PlayStore: get_latest_version failed: {e}")
        return None


def get_download_link(version: str, app_name: str, config: dict) -> str | None:
    """
    Download the APK from Google Play and return the path to the merged APK.

    Strategy:
      Phase 1 — density NONE  (nodpi, smallest/purest download)
      Phase 2 — density 480   (xxhdpi, universal fallback)

    Returns the local file path (not an HTTP URL) so downloader.py can
    treat it like any other downloaded resource.
    """
    if not _creds_available():
        logging.warning(
            "PlayStore: credentials.json missing at credentials/credentials.json — "
            "skipping Google Play source. "
            "Run `playstore-downloader --setup` to generate it."
        )
        return None

    package = config.get("package", "")
    if not package:
        logging.error(f"PlayStore: no package name in config for {app_name}")
        return None

    # Resolve numeric version code from the version name
    version_code = _resolve_version_code(package, version)
    if not version_code:
        logging.error(
            f"PlayStore: could not resolve version code for {package} {version}"
        )
        return None

    output_apk = Path(f"{app_name}-playstore-v{version}.apk")

    for density_label, density_flag in [("NONE (nodpi)", "NONE"), ("480 (xxhdpi)", "480")]:
        logging.info(f"PlayStore: trying density {density_label} for {package} {version}")

        splits_dir = Path(f"playstore_splits_{package}")
        success = _download_splits(package, version_code, splits_dir, density_flag)

        if not success:
            logging.warning(f"PlayStore: density {density_label} failed, trying next…")
            if splits_dir.exists():
                shutil.rmtree(splits_dir, ignore_errors=True)
            continue

        merged = _merge_splits(splits_dir, output_apk)
        if splits_dir.exists():
            shutil.rmtree(splits_dir, ignore_errors=True)

        if merged and output_apk.exists():
            logging.info(
                f"PlayStore: ✓ {app_name} {version} ready at {output_apk} "
                f"(density={density_label})"
            )
            # Return the local path — downloader.py checks for file existence
            return str(output_apk)

        logging.warning(f"PlayStore: merge failed for density {density_label}")

    logging.error(
        f"PlayStore: all density strategies exhausted for {app_name} {version}"
    )
    return None
