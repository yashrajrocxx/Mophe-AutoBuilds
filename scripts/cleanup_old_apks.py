#!/usr/bin/env python3
"""Delete superseded (older-version) APK assets from the 'latest' release.

Problem this solves
-------------------
APK filenames embed the app version, e.g.::

    youtube-arm64-v8a-morphe-v2.5.0.apk

When a new version is built and uploaded, the *old* APK
(``youtube-arm64-v8a-morphe-v2.4.0.apk``) was never removed, because the previous
workflow step only deleted assets whose filename matched a *new* APK exactly
(i.e. it could only overwrite identical names). Old versions therefore
accumulated indefinitely.

Strategy
--------
For every newly-built APK, derive its *identity prefix*
``{app}-{arch}-`` (everything before ``-v{version}.apk``) and delete any *other*
APK in the release that shares that prefix but is not in the keep-set. This is
identity-based, so v2.5 correctly supersedes v2.4.

Inputs
------
- ``--keep-file``: a newline-delimited file of APK basenames to PRESERVE
  (typically ``release-apks/current_assets.txt``). Anything listed here is never
  deleted.
- ``--release``: release tag to clean (default ``latest``).

The current APK asset names are read via ``gh release view --json assets`` so we
never need to download the heavy APK files.

Safety
------
- Only ``.apk`` assets are ever considered for deletion.
- Anything in the keep-set is always preserved.
- Every deletion is best-effort (logged + non-fatal).
- A ``--dry-run`` flag prints what would be deleted without deleting.
"""
import argparse
import json
import re
import subprocess
import sys
from pathlib import Path
from typing import List, Set

# APK names look like: {app}-{arch}-{name}-v{version}.apk
# We want to keep everything up to the version marker as the "identity".
# The version marker must be restricted to genuine version characters (digits,
# dots, parentheses for build numbers, hyphen, plus) so that the architecture
# tokens "v8a"/"v7a" inside arm64-v8a / armeabi-v7a do NOT match (they have a
# letter right after the digit, e.g. "v8a"). Otherwise the identity prefix would
# be truncated at the arch segment.
VERSION_MARKER = re.compile(r"-v\d[\d.()+\-]*\.apk$", re.IGNORECASE)


def detect_arch_from_filename(apk_name: str, default: str = "") -> str:
    """Detect the architecture token embedded in an APK filename."""
    base = apk_name.lower()
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


def gh_release_assets(release: str) -> List[dict]:
    """Return asset dicts (with 'name' + 'id') currently attached to the release.
    Only APK assets are returned."""
    try:
        result = subprocess.run(
            ["gh", "release", "view", release, "--json", "assets"],
            capture_output=True, text=True, check=True,
        )
        assets = json.loads(result.stdout or "{}").get("assets", []) or []
        return [a for a in assets if isinstance(a, dict)
                and str(a.get("name", "")).endswith(".apk")]
    except Exception as e:
        print(f"[WARN] could not list release assets: {e}", file=sys.stderr)
        return []


def identity_prefix(apk_name: str) -> str:
    """Return the identity prefix of an APK filename (everything before the
    version marker). E.g. ``youtube-arm64-v8a-morphe-v2.5.0.apk`` ->
    ``youtube-arm64-v8a-morphe``. Falls back to the stem if no marker matches."""
    m = VERSION_MARKER.search(apk_name)
    return (apk_name[: m.start()] if m else Path(apk_name).stem).lower()


def load_keep_set(keep_file: Path) -> Set[str]:
    if not keep_file or not keep_file.exists():
        return set()
    names = set()
    for line in keep_file.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line:
            names.add(line)
    return names


def delete_asset_by_name(release: str, name: str) -> tuple:
    """Delete a single asset by name using `gh release delete-asset`.
    NOTE: `gh release delete <tag> <asset>` deletes the WHOLE release, not the
    asset — that was the original bug. The correct subcommand is `delete-asset`.
    Returns (ok, message)."""
    try:
        subprocess.run(
            ["gh", "release", "delete-asset", release, name, "--yes"],
            capture_output=True, text=True, check=True,
        )
        return True, ""
    except subprocess.CalledProcessError as e:
        return False, (e.stderr or e.stdout or str(e)).strip()
    except Exception as e:
        return False, str(e)


def delete_asset_by_id(name: str, asset_id: str) -> tuple:
    """Fallback: delete an asset by its numeric ID via the REST API.
    Used when `gh release delete-asset` is unavailable (older gh) or fails.
    Returns (ok, message)."""
    repo = _repo_slug()
    if not repo:
        return False, "GITHUB_REPOSITORY not set for API fallback"
    try:
        subprocess.run(
            ["gh", "api", "-X", "DELETE",
             f"repos/{repo}/releases/assets/{asset_id}"],
            capture_output=True, text=True, check=True,
        )
        return True, ""
    except subprocess.CalledProcessError as e:
        return False, (e.stderr or e.stdout or str(e)).strip()
    except Exception as e:
        return False, str(e)


def _repo_slug() -> str:
    """Return 'owner/name' from the GITHUB_REPOSITORY env var, or ''."""
    import os
    return (os.environ.get("GITHUB_REPOSITORY") or "").strip()


def delete_asset(release: str, name: str, asset_id: str = "") -> bool:
    """Delete a single release asset. Tries `gh release delete-asset` first,
    falls back to the REST API (by asset id) on failure. Returns True on
    success. Every failure is logged to stderr but never fatal."""
    ok, msg = delete_asset_by_name(release, name)
    if ok:
        return True
    print(f"  [WARN] delete-asset failed for {name}: {msg[:200]}", file=sys.stderr)

    if asset_id:
        ok2, msg2 = delete_asset_by_id(name, asset_id)
        if ok2:
            return True
        print(f"  [WARN] API fallback failed for {name} (id={asset_id}): {msg2[:200]}",
              file=sys.stderr)
    else:
        print(f"  [WARN] no asset id available for {name}; API fallback skipped",
              file=sys.stderr)
    return False


def main() -> int:
    parser = argparse.ArgumentParser(description="Delete superseded APK assets from a release.")
    parser.add_argument("--release", default="latest", help="release tag (default: latest)")
    parser.add_argument("--keep-file", required=True,
                        help="newline-delimited file of APK basenames to preserve")
    parser.add_argument("--dry-run", action="store_true", help="list deletions without performing them")
    args = parser.parse_args()

    keep = load_keep_set(Path(args.keep_file))
    assets = gh_release_assets(args.release)  # list of {name, id, ...} dicts

    if not assets:
        print("No existing APK assets to clean up.")
        return 0

    # Identity prefixes that must be preserved (one or more of the keep-set may
    # share a prefix when multiple arches of the same app are kept).
    keep_prefixes = {identity_prefix(n) for n in keep}

    arch_config_path = Path("arch-config.json")
    active_arches_by_app: dict[str, set[str]] = {}
    if arch_config_path.exists():
        try:
            with arch_config_path.open("r", encoding="utf-8") as f:
                ac_data = json.load(f)
            for item in ac_data:
                app_name = item.get("app_name", "")
                if app_name:
                    active_arches_by_app.setdefault(app_name, set()).update(item.get("arches", []))
        except Exception:
            pass

    to_delete = []  # list of asset dicts
    for asset in assets:
        name = str(asset.get("name", ""))
        if not name or name in keep:
            continue  # explicitly kept (or unnamed)
        if identity_prefix(name) in keep_prefixes:
            to_delete.append(asset)  # same app/arch, but a different (older) version
        elif active_arches_by_app:
            # Check if this asset belongs to an app being kept, but its arch is no longer active
            for app_name, valid_arches in active_arches_by_app.items():
                if name.startswith(f"{app_name}-"):
                    asset_arch = detect_arch_from_filename(name)
                    if asset_arch and asset_arch not in valid_arches:
                        to_delete.append(asset)
                    break
        # else: an app/arch we didn't rebuild this run -> leave it untouched

    if not to_delete:
        print("No superseded APK assets found.")
        return 0

    print(f"Found {len(to_delete)} superseded APK asset(s) to remove:")
    deleted = 0
    for asset in to_delete:
        name = str(asset.get("name", ""))
        asset_id = str(asset.get("id") or asset.get("apiUri", "")).strip()
        # If gh gave us a URL instead of a bare id, extract the trailing number.
        if asset_id and "/" in asset_id:
            asset_id = asset_id.rstrip("/").rsplit("/", 1)[-1]
        if args.dry_run:
            print(f"  [dry-run] would delete: {name}")
        else:
            if delete_asset(args.release, name, asset_id):
                print(f"  deleted: {name}")
                deleted += 1

    action = "would delete" if args.dry_run else "deleted"
    print(f"Done. {action} {len(to_delete) if args.dry_run else deleted} superseded asset(s).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
