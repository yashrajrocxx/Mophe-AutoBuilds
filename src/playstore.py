"""
Google Play APK downloader using gplaydl (pip install gplaydl).

gplaydl is a real PyPI package: https://pypi.org/project/gplaydl/

Architecture:
  1. Run `gplaydl info` to get the latest version code from Play Store
  2. Run `gplaydl download` targeting arm64, fetching splits + base APK
  3. Merge any split APKs into a single monolithic APK via APKEditor
  4. Return the local file path to the merged APK

Setup (one-time, on any Android phone):
  - Install the gplaydl Authenticator app from https://dispenser.gplaydl.com
  - Sign into your bot Google account
  - Tap "Link gplaydl" and run: gplaydl link <code>
  After that, gplaydl remembers the token automatically (no credentials file
  to manage — it stores auth in the system keyring / config dir).

gplaydl is invoked via subprocess (CLI), not imported as a module.
"""

import json
import logging
import os
import re
import shutil
import subprocess
from pathlib import Path

_TOOL = "gplaydl"
_ARCH = "arm64"   # gplaydl uses 'arm64', not 'arm64-v8a'


# ─────────────────────────────────────────────────────────────────────────────
# Internal helpers
# ─────────────────────────────────────────────────────────────────────────────

def _tool_available() -> bool:
    """Check that gplaydl is installed and has a linked account."""
    if not shutil.which(_TOOL):
        logging.warning("PlayStore: gplaydl not found in PATH — install with `pip install gplaydl`")
        return False
    return True


def _run(cmd: list[str], **kwargs) -> subprocess.CompletedProcess:
    logging.info(f"PlayStore: {' '.join(cmd)}")
    return subprocess.run(cmd, **kwargs)


def _get_version_code(package: str) -> str | None:
    """
    Use `gplaydl info` to fetch the latest version code from Google Play.
    Returns the numeric versionCode as a string, or None on failure.
    """
    try:
        result = _run(
            [_TOOL, "info", package, "--arch", _ARCH],
            capture_output=True, text=True, timeout=60
        )
        if result.returncode != 0:
            logging.warning(
                f"PlayStore: `gplaydl info` failed (rc={result.returncode}): "
                f"{result.stderr[:200]}"
            )
            return None

        # gplaydl info outputs a rich table; parse version code from it
        # Lines like: "│ Version    │ 2.372.0 (29663417)  │"
        for line in result.stdout.splitlines():
            m = re.search(r"Version\s*│\s*([^\s]+)\s*\((\d+)\)", line, re.IGNORECASE)
            if m:
                return m.group(2)

        logging.warning(f"PlayStore: could not parse version code from gplaydl info output")
    except subprocess.TimeoutExpired:
        logging.warning("PlayStore: gplaydl info timed out")
    except Exception as e:
        logging.warning(f"PlayStore: error getting version code: {e}")

    return None


def _download_splits(
    package: str,
    output_dir: Path,
    version_code: str | None = None,
) -> bool:
    """
    Call `gplaydl download` to fetch the APK + splits into output_dir.
    If version_code is provided, requests that specific build.
    Returns True if files were downloaded.
    """
    if output_dir.exists():
        shutil.rmtree(output_dir)
    output_dir.mkdir(parents=True)

    cmd = [
        _TOOL, "download", package,
        "--arch", _ARCH,
        "--output", str(output_dir),
        "--no-extras",   # skip OBB/asset packs — we only need the APK
    ]
    if version_code:
        cmd += ["--version", version_code]

    try:
        result = _run(cmd, timeout=600)
        if result.returncode != 0:
            logging.warning(
                f"PlayStore: gplaydl download failed (rc={result.returncode})"
            )
            return False

        # Verify files exist
        apk_files = list(output_dir.glob("**/*.apk"))
        if not apk_files:
            logging.warning("PlayStore: no APK files found after download")
            return False

        logging.info(
            f"PlayStore: ✓ downloaded {len(apk_files)} file(s) for {package}"
        )
        return True

    except subprocess.TimeoutExpired:
        logging.warning("PlayStore: gplaydl download timed out")
        return False
    except Exception as e:
        logging.warning(f"PlayStore: download error: {e}")
        return False


def _merge_splits(splits_dir: Path, output_apk: Path) -> bool:
    """
    Use APKEditor to merge a directory of split APKs into one monolithic APK.
    If only a single .apk exists, rename it directly (no merge needed).
    """
    apk_files = list(splits_dir.glob("**/*.apk"))

    if not apk_files:
        logging.error("PlayStore: no APK files to merge")
        return False

    # Single base APK with no splits — just move it
    if len(apk_files) == 1:
        apk_files[0].rename(output_apk)
        logging.info(f"PlayStore: single APK → {output_apk.name}")
        return True

    # Multiple files — need APKEditor
    apkeditor = _find_or_download_apkeditor()
    if not apkeditor:
        # Fallback: take the largest file as the base APK
        biggest = max(apk_files, key=lambda f: f.stat().st_size)
        biggest.rename(output_apk)
        logging.warning(
            f"PlayStore: APKEditor unavailable — using largest split {biggest.name} "
            f"as fallback (may be incomplete)"
        )
        return True

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
            logging.error("PlayStore: merged APK not produced")
            return False

        logging.info(f"PlayStore: ✓ merged {len(apk_files)} splits → {output_apk.name}")
        return True

    except subprocess.TimeoutExpired:
        logging.error("PlayStore: APKEditor merge timed out")
        return False
    except Exception as e:
        logging.error(f"PlayStore: merge error: {e}")
        return False


def _find_or_download_apkeditor() -> Path | None:
    """Find APKEditor JAR in the current directory, or try to download it."""
    # Check working directory first
    for jar in sorted(Path(".").glob("APKEditor*.jar"), reverse=True):
        return jar

    # Try downloading latest release from GitHub
    try:
        from src import gh
        repo = gh.get_repo("REAndroid/APKEditor")
        release = repo.get_latest_release()
        for asset in release.get_assets():
            if asset.name.startswith("APKEditor") and asset.name.endswith(".jar"):
                from src.downloader import download_resource
                path = download_resource(asset.browser_download_url)
                logging.info(f"PlayStore: downloaded APKEditor to {path}")
                return path
    except Exception as e:
        logging.warning(f"PlayStore: could not fetch APKEditor: {e}")

    return None


# ─────────────────────────────────────────────────────────────────────────────
# Public interface (matches the contract used by downloader.py)
# ─────────────────────────────────────────────────────────────────────────────

def get_latest_version(app_name: str, config: dict) -> str | None:
    """Return the latest version name available on Google Play."""
    if not _tool_available():
        return None

    package = config.get("package", "")
    if not package:
        return None

    try:
        result = _run(
            [_TOOL, "info", package, "--arch", _ARCH],
            capture_output=True, text=True, timeout=60
        )
        if result.returncode != 0:
            return None

        # Parse version name from output
        for line in result.stdout.splitlines():
            m = re.search(r"Version\s*│\s*([^\s]+)\s*\((\d+)\)", line, re.IGNORECASE)
            if m:
                ver = m.group(1)
                logging.info(f"PlayStore: latest version for {app_name} is {ver}")
                return ver

    except Exception as e:
        logging.warning(f"PlayStore: get_latest_version failed: {e}")

    return None


def get_download_link(version: str, app_name: str, config: dict) -> str | None:
    """
    Download the APK from Google Play and return the local path to the merged APK.

    gplaydl handles the NONE vs 480 DPI selection automatically based on the
    device profile (arm64 profile = modern high-DPI device, so Play serves the
    best quality split set automatically).

    Returns a local file path string (not an HTTP URL).
    downloader.py detects this and skips the HTTP download step.
    """
    if not _tool_available():
        return None

    package = config.get("package", "")
    if not package:
        logging.error(f"PlayStore: no package in config for {app_name}")
        return None

    # Resolve the numeric version code that matches the requested version name.
    # We get the latest from Play, then check if it matches; if not, we proceed
    # without a version pin (gets latest, which is what patches usually want).
    version_code: str | None = None

    latest_info = _run(
        [_TOOL, "info", package, "--arch", _ARCH],
        capture_output=True, text=True, timeout=60
    )
    if latest_info.returncode == 0:
        play_version = None
        play_code = None
        for line in latest_info.stdout.splitlines():
            m = re.search(r"Version\s*│\s*([^\s]+)\s*\((\d+)\)", line, re.IGNORECASE)
            if m:
                play_version = m.group(1)
                play_code = m.group(2)

        if play_version and play_code:
            logging.info(
                f"PlayStore: Play has {app_name} {play_version} "
                f"(code {play_code}), target is {version}"
            )
            # If Play's latest matches our target (exact or prefix), use the code
            if (play_version == version
                    or play_version.startswith(version + ".")
                    or play_version.startswith(version + "-")):
                version_code = play_code
                logging.info(f"PlayStore: version match ✓ using code {version_code}")
            else:
                # Target version differs, Play Store only gives the latest.
                # We MUST fail here so the downloader falls back to scrapers
                # (Uptodown/APKMirror) which can fetch older versions.
                logging.warning(
                    f"PlayStore: target={version} but Play only serves {play_version}. "
                    f"Failing to trigger scraper fallback."
                )
                return None

    output_apk = Path(f"{app_name}-playstore-v{version}.apk")
    splits_dir = Path(f"playstore_splits_{package}")

    success = _download_splits(package, splits_dir, version_code)
    if not success:
        if splits_dir.exists():
            shutil.rmtree(splits_dir, ignore_errors=True)
        logging.error(f"PlayStore: download failed for {app_name} {version}")
        return None

    merged = _merge_splits(splits_dir, output_apk)
    if splits_dir.exists():
        shutil.rmtree(splits_dir, ignore_errors=True)

    if not merged or not output_apk.exists():
        logging.error(f"PlayStore: merge failed for {app_name} {version}")
        return None

    logging.info(f"PlayStore: ✓ {app_name} {version} → {output_apk}")
    return str(output_apk)
