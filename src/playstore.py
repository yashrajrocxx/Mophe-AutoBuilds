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
import requests
from bs4 import BeautifulSoup
from src.utils import get_cli_version_code

_TOOL = "gplaydl"
_ARCH = "arm64"   # gplaydl uses 'arm64', not 'arm64-v8a'

_exodus_cache = {}

_JSON_SUPPORTED: bool | None = None


def _gplaydl_supports_json() -> bool:
    """Detect whether installed gplaydl supports `--json` (newer releases do)."""
    global _JSON_SUPPORTED
    if _JSON_SUPPORTED is not None:
        return _JSON_SUPPORTED
    try:
        result = subprocess.run(
            [_TOOL, "info", "--help"],
            capture_output=True, text=True, timeout=15,
        )
        _JSON_SUPPORTED = "--json" in (result.stdout + result.stderr)
    except Exception:
        _JSON_SUPPORTED = False
    return _JSON_SUPPORTED


def _parse_info_output(output: str) -> tuple[str | None, str | None]:
    """Parse `gplaydl info` output (JSON or table) → (version_name, version_code)."""
    if not output:
        return None, None
    # JSON-ish output: {"versionName": "...", "versionCode": 123} or "versionCode": 123
    m = re.search(r'"versionCode"\s*:\s*"?(\d{6,})"?', output)
    code = m.group(1) if m else None
    ver = None
    m = re.search(r'"versionName"\s*:\s*"([^"]+)"', output)
    if m:
        ver = m.group(1)
    else:
        m = re.search(r"Version\s*[│|]\s*([^\s│|]+)\s*\((\d{6,})\)", output, re.IGNORECASE)
        if m:
            ver, code = m.group(1), m.group(2)
        else:
            m = re.search(r'version[_\s]?code\s*[=:]\s*(\d{6,})', output, re.IGNORECASE)
            if m and not code:
                code = m.group(1)
    return ver, code


def _run_info(package: str):
    """Run `gplaydl info`, preferring `--json` when supported."""
    if _gplaydl_supports_json():
        try:
            result = _run(
                [_TOOL, "info", package, "--arch", _ARCH, "--json"],
                capture_output=True, text=True, timeout=60,
            )
            if result.returncode == 0 and result.stdout.strip():
                return result
        except Exception:
            pass
    return _run(
        [_TOOL, "info", package, "--arch", _ARCH],
        capture_output=True, text=True, timeout=60,
    )

class VersionNotFound(Exception):
    pass

class ExodusApiError(Exception):
    pass


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

def scrape_exodus_version_code(package_name: str, version_name: str) -> int | None:
    """Scrape the public Exodus Privacy web report for a package and version without authentication."""
    search_url = f"https://reports.exodus-privacy.eu.org/reports/search/{package_name}"
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
    try:
        logging.info(f"PlayStore: Checking Exodus public web reports for {package_name} {version_name}")
        resp = requests.get(search_url, headers=headers, timeout=15)
        if resp.status_code != 200:
            logging.debug(f"PlayStore: Exodus web search returned HTTP {resp.status_code}")
            return None
        soup = BeautifulSoup(resp.content, "html.parser")
    except Exception as e:
        logging.debug(f"PlayStore: Exodus web search failed: {e}")
        return None

    # Search report cards
    for card in soup.find_all("div", class_=lambda c: c and "position-static" in c):
        v_el = card.find("div", class_="small")
        a_el = card.find("a", class_=lambda c: c and "report-link" in c)
        if not v_el or not a_el:
            continue
        v_text = v_el.get_text()
        m = re.search(r"Version\s+([^\s-]+)", v_text, re.IGNORECASE)
        if m and m.group(1).strip() == version_name:
            report_href = a_el["href"]
            report_url = f"https://reports.exodus-privacy.eu.org{report_href}" if report_href.startswith("/") else report_href
            try:
                rep_resp = requests.get(report_url, headers=headers, timeout=15)
                if rep_resp.status_code == 200:
                    rep_soup = BeautifulSoup(rep_resp.content, "html.parser")
                    for pre in rep_soup.find_all(["pre", "code"]):
                        try:
                            data = json.loads(pre.get_text())
                            if "version_code" in data:
                                return int(data["version_code"])
                        except Exception:
                            continue
            except Exception as e:
                logging.debug(f"PlayStore: Error scraping report page {report_url}: {e}")
                continue

    return None

def resolve_version_code(package_name: str, version_name: str, arch: str = None) -> int:
    """Resolve Android versionCode from a human-readable version name.

    Resolution priority:
      1. CLI-provided versionCode (from Morphe/ReVanced `list-versions` output) — instant
      2. gplaydl info output — works when the requested version is the *latest* on Play
      3. APKPure mobile API — api.pureapk.com returns per-version versionCode, no CF
      4. APKMirror scrape — versionCode extracted from release variant rows, no extra deps
      5. Exodus public web scraper — last resort (slow, may miss recent versions)

    Raises VersionNotFound if none of the above succeeded.
    """
    cache_key = f"{package_name}:{version_name}"
    if cache_key in _exodus_cache:
        return _exodus_cache[cache_key]

    # ── 1. CLI-provided code (fastest) ──────────────────────────────────────────
    cli_code = get_cli_version_code(package_name, version_name, arch)
    if cli_code:
        logging.info(f"PlayStore: versionCode {cli_code} for {package_name} {version_name} (from CLI)")
        _exodus_cache[cache_key] = cli_code
        return cli_code

    # ── 2. gplaydl info (works when target == latest on Play Store) ─────────────
    if _tool_available():
        try:
            info_res = _run_info(package_name)
            if info_res.returncode == 0:
                play_version, play_code = _parse_info_output(info_res.stdout)
                if play_version and play_code and (
                    play_version == version_name
                    or play_version.startswith(version_name + ".")
                    or play_version.startswith(version_name + "-")
                ):
                    _exodus_cache[cache_key] = int(play_code)
                    logging.info(f"PlayStore: versionCode {play_code} for {package_name} {version_name} (from gplaydl info)")
                    return int(play_code)
        except Exception as e:
            logging.debug(f"PlayStore: gplaydl info lookup failed for {package_name}: {e}")

    # ── 3. APKPure mobile API — primary historical versionCode resolver ──────────
    # api.pureapk.com returns versionCode per version with no Cloudflare.
    # This replaces the Exodus API which has had persistent 401 issues.
    try:
        from src.apkpure import get_version_code_from_api as _apkpure_vc
        vc = _apkpure_vc(package_name, version_name)
        if vc:
            logging.info(f"PlayStore: versionCode {vc} for {package_name} {version_name} (from APKPure API)")
            _exodus_cache[cache_key] = vc
            return vc
    except Exception as e:
        logging.debug(f"PlayStore: APKPure API lookup failed for {package_name}: {e}")

    # ── 4. APKMirror scrape — versionCode from release variant rows ──────────────
    try:
        from src import apkmirror as _apkmirror
        vc = _apkmirror.get_version_code(package_name, version_name)
        if vc:
            logging.info(f"PlayStore: versionCode {vc} for {package_name} {version_name} (from APKMirror)")
            _exodus_cache[cache_key] = vc
            return vc
    except Exception as e:
        logging.debug(f"PlayStore: APKMirror lookup failed for {package_name}: {e}")

    # ── 5. Exodus public web scraper (last resort) ───────────────────────────────
    web_code = scrape_exodus_version_code(package_name, version_name)
    if web_code is not None:
        logging.info(f"PlayStore: versionCode {web_code} for {package_name} {version_name} (from Exodus web)")
        _exodus_cache[cache_key] = web_code
        return web_code

    raise VersionNotFound(
        f"versionCode for '{package_name}' {version_name} not found. "
        "Tried: CLI list-versions → gplaydl info → APKPure API → APKMirror → Exodus web scraper. "
        "Provide a --version-code or ensure the package is indexed by APKPure."
    )


def _get_version_code(package: str) -> str | None:
    """Use `gplaydl info` to fetch the latest version code from Google Play.

    Returns the numeric versionCode as a string, or None on failure.

    Handles multiple gplaydl output formats (prefers `--json` when supported):
      • JSON:        {"versionName": "2.372.0", "versionCode": 29663417}
      • Table format:  │ Version    │ 2.372.0 (29663417)  │
      • Plain text:    Version: 2.372.0 (29663417) or versionCode=29663417
    """
    try:
        result = _run_info(package)
        if result.returncode != 0:
            logging.warning(
                f"PlayStore: `gplaydl info` failed (rc={result.returncode}): "
                f"{result.stderr[:200]}"
            )
            return None

        ver, code = _parse_info_output(result.stdout)
        if code:
            logging.info(f"PlayStore: gplaydl info → {ver or '?'} (vc={code})")
            return code

        # Last resort: any bare large integer that looks like a versionCode
        candidates = re.findall(r'\b(\d{7,12})\b', result.stdout)
        if candidates:
            vc = candidates[0]
            logging.warning(f"PlayStore: gplaydl info — inferred versionCode={vc} (heuristic)")
            return vc

        logging.warning(
            f"PlayStore: could not parse version code from gplaydl info output.\n"
            f"Output was:\n{result.stdout[:600]}"
        )
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
            f"PlayStore: Downloaded {len(apk_files)} file(s) for {package}"
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

        logging.info(f"PlayStore: Merged {len(apk_files)} splits -> {output_apk.name}")
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
        result = _run_info(package)
        if result.returncode != 0:
            return None

        ver, _ = _parse_info_output(result.stdout)
        if ver:
            logging.info(f"PlayStore: latest version for {app_name} is {ver}")
            return ver

        # Legacy line-by-line fallback
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

    version_code: str | None = None

    # First, check if the requested version is simply the latest version on Play Store.
    # This avoids querying resolvers for brand new versions that indexes haven't caught yet.
    latest_info = _run_info(package)
    if latest_info.returncode == 0:
        play_version, play_code = _parse_info_output(latest_info.stdout)
        if not play_version or not play_code:
            for line in latest_info.stdout.splitlines():
                m = re.search(r"Version\s*│\s*([^\s]+)\s*\((\d+)\)", line, re.IGNORECASE)
                if m:
                    play_version = m.group(1)
                    play_code = m.group(2)

        if play_version and play_code:
            if (play_version == version
                    or play_version.startswith(version + ".")
                    or play_version.startswith(version + "-")):
                version_code = play_code
                logging.info(f"PlayStore: target is latest version, using code {version_code}")

    # If it wasn't the latest version (or `info` failed), resolve via full chain
    if not version_code:
        try:
            version_code_int = resolve_version_code(package, version, config.get('arch'))
            version_code = str(version_code_int)
            logging.info(f"PlayStore: Resolved historical {version} to versionCode {version_code}")
        except VersionNotFound as e:
            logging.warning(f"PlayStore: {e} - Triggering scraper fallback.")
            return None
        except ExodusApiError as e:
            logging.warning(f"PlayStore: Exodus API unavailable ({e}) - Triggering scraper fallback.")
            return None
        except Exception as e:
            logging.warning(f"PlayStore: Unexpected error resolving version ({e}) - Triggering scraper fallback.")
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

    logging.info(f"PlayStore: {app_name} {version} -> {output_apk}")
    return str(output_apk)
