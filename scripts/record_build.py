#!/usr/bin/env python3
"""Record per-build APK filenames into manifest entries (one entry per built APK).

Used inside the build-apps matrix job: after a successful build, run this with
APP_NAME, SOURCE, ARCH, APK_PATH set so we can write a tiny per-build JSON that
the release job will merge into the final manifest.json.

Output file: ./build_records/<app>__<source>__<arch>.json
Content:    {"key": "app|source|arch", "apk": "<filename>",
             "resolved_version": "<version>", "app_name","source","arch"}
"""
import os
import re
import sys
import json
from pathlib import Path

# Add project root to sys.path to access src.utils
ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

try:
    from src import utils
except ImportError:
    utils = None

REC_DIR = Path("build_records")

# Known architecture tokens that may appear in the APK filename
KNOWN_ARCHES = ("arm64-v8a", "armeabi-v7a", "x86_64", "x86", "universal")


def detect_arch_from_filename(apk_name: str, default: str = "universal") -> str:
    """APK files are named like {app}-{arch}-{name}-v{version}.apk.
    Try to detect the arch token from the filename."""
    if not apk_name:
        return default
    base = apk_name.lower()

    # Check for specific arch tokens in the filename
    # Order matters: check more specific ones first
    if "arm64-v8a" in base:
        return "arm64-v8a"
    if "armeabi-v7a" in base:
        return "armeabi-v7a"
    if "x86_64" in base:
        return "x86_64"
    if "x86" in base:
        return "x86"
    if "universal" in base:
        return "universal"

    return default


def extract_version_from_filename(apk_name: str) -> str:
    """Extract the app version from the APK filename.

    APKs are named ``{app}-{arch}-{name}-v{version}.apk``, e.g.
    ``youtube-arm64-v8a-morphe-v21.16.256.apk`` -> ``21.16.256``.

    The version marker is the rightmost ``-v`` immediately followed by a dotted
    version (``-v<digit>.<digit>...``). We require the dotted shape because
    architecture tokens also contain ``-v<digit>``: ``arm64-v8a`` and
    ``armeabi-v7a``. A naive ``-v\\d`` match grabs ``8a-...`` / ``7a-...`` from
    those arch tokens instead of the real version. Real app versions in this
    project always contain a dot (e.g. ``21.16.256``), and build/release
    suffixes like ``(1575420)``, ``build 002`` or ``-release`` are still captured
    by the trailing character class after the required ``\\d+.\\d`` prefix.

    This mirrors the identity-prefix logic in cleanup_old_apks.py (which uses the
    same rightmost ``-v`` marker to split identity from version) so the two
    scripts always agree on where the version begins.

    Returns '' if no version marker is found.
    """
    if not apk_name:
        return ""
    stem = apk_name[:-4] if apk_name.lower().endswith(".apk") else apk_name
    # finditer() scans left-to-right; take the last match so that, if a name
    # ever contained two dotted "-v" tokens, the trailing version wins. The
    # dotted-shape requirement is what actually excludes arch tokens.
    matches = list(re.finditer(r"-v(\d+\.\d[\w.+\-() ]*)$", stem))
    if not matches:
        return ""
    return matches[-1].group(1).strip()


def main() -> int:
    app = os.environ.get("APP_NAME", "").strip()
    src = os.environ.get("SOURCE", "").strip()
    apk_path = os.environ.get("APK_PATH", "").strip()
    arch_env = os.environ.get("ARCH", "").strip()

    if not app or not src:
        print("APP_NAME / SOURCE missing; skipping manifest record")
        return 0

    apk_name = Path(apk_path).name if apk_path else ""

    # Prefer explicit ARCH env, otherwise detect from filename, fallback universal
    arch = arch_env or detect_arch_from_filename(apk_name) or "universal"

    # Extract the resolved app version from the filename so the manifest can
    # compare it on the next run and detect when a newer version is available
    # (or when patches add support for a new version). Without this, the manifest
    # only ever stored the (often empty) config 'version' field, so apps pinned
    # to "latest" never triggered a rebuild when a new APK version shipped.
    resolved_version = extract_version_from_filename(apk_name)

    # Dynamically extract actual patched package name and metadata from the built APK
    actual_package = None
    manifest_vc = None
    if apk_path and Path(apk_path).exists() and utils:
        try:
            info = utils.get_apk_manifest_info(apk_path)
            if info.get("package"):
                actual_package = info["package"]
            if info.get("versionCode"):
                manifest_vc = info["versionCode"]
            if not resolved_version and info.get("versionName"):
                resolved_version = info["versionName"]
        except Exception as e:
            print(f"[WARN] Error extracting manifest from {apk_path}: {e}")

    # Fallback to configured patched_package if not extracted from APK
    if not actual_package:
        for platform in ("playstore", "apkmirror", "uptodown", "apkpure", "aptoide"):
            cfg_path = ROOT_DIR / "apps" / platform / f"{app}.json"
            if cfg_path.exists():
                try:
                    with cfg_path.open("r", encoding="utf-8") as f:
                        cfg_data = json.load(f)
                    if cfg_data.get("patched_package") or cfg_data.get("custom_package"):
                        actual_package = cfg_data.get("patched_package") or cfg_data.get("custom_package")
                        break
                except Exception:
                    pass

    import datetime
    built_at = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    REC_DIR.mkdir(parents=True, exist_ok=True)
    record = {
        "key": f"{app}|{src}|{arch}",
        "apk": apk_name,
        "resolved_version": resolved_version,
        "app_name": app,
        "source": src,
        "arch": arch,
        "built_at": built_at,
    }
    if actual_package:
        record["package"] = actual_package
    if manifest_vc:
        record["version_code"] = manifest_vc

    safe = f"{app}__{src}__{arch}".replace("/", "_")
    fp = REC_DIR / f"{safe}.json"
    with fp.open("w", encoding="utf-8") as f:
        json.dump(record, f, indent=2)
    print(f"Recorded build: {fp} -> {record}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
