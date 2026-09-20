#!/usr/bin/env python3
"""Validate Obtainium configuration against manifest.json and downloads.html.

Our entries use the HTML app source pointed at the generated downloads page
(see scripts/generate_downloads_page.py): apkFilterRegEx selects the app's
download link(s) and versionExtractionRegEx reads the version from the
matched link URL. This mirrors Obtainium semantics (unanchored search for
the filter, extraction on the link) — including the critical property that
the patterns must NEVER be applied to a release tag.

Strict checks per app entry:
  1. Schema (id, name, pages downloads URL, additionalSettings JSON).
  2. apkFilterRegEx matches EXACTLY ONE link in downloads.html.
  3. versionExtractionRegEx extracts EXACTLY the manifest built_version
     from that link.
Also verifies every manifest APK is linked from downloads.html.

Exit code 0 on success, 1 on any error.
"""
import re
import sys
import json
from pathlib import Path
from typing import Dict, Any, List

if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

if sys.stderr and hasattr(sys.stderr, "reconfigure"):
    try:
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass


def validate_obtainium_bundle(obtainium_path: Path, manifest_path: Path) -> bool:
    if not obtainium_path.exists():
        print(f"[ERROR] Obtainium file not found: {obtainium_path}", file=sys.stderr)
        return False

    if not manifest_path.exists():
        print(f"[ERROR] Manifest file not found: {manifest_path}", file=sys.stderr)
        return False

    try:
        with obtainium_path.open("r", encoding="utf-8") as f:
            bundle = json.load(f)
    except Exception as e:
        print(f"[ERROR] Failed to parse JSON from {obtainium_path}: {e}", file=sys.stderr)
        return False

    try:
        with manifest_path.open("r", encoding="utf-8") as f:
            manifest = json.load(f)
    except Exception as e:
        print(f"[ERROR] Failed to parse JSON from {manifest_path}: {e}", file=sys.stderr)
        return False

    apps: List[Dict[str, Any]] = bundle.get("apps", [])
    if not apps:
        print(f"[ERROR] No apps found in {obtainium_path}", file=sys.stderr)
        return False

    entries: Dict[str, Any] = manifest.get("entries", {})

    # Download links, parsed from the generated page (same markup Obtainium sees)
    downloads_path = obtainium_path.parent / "pages" / "public" / "downloads.html"
    if not downloads_path.exists():
        downloads_path = Path("pages/public/downloads.html")
    page_links: List[str] = []
    if downloads_path.exists():
        page_links = re.findall(r'<a[^>]+href="([^"]+)"', downloads_path.read_text(encoding="utf-8"))
    else:
        print(f"[WARN] {downloads_path} not found; falling back to manifest-derived URLs", file=sys.stderr)
        page_links = [
            f"https://github.com/x/y/releases/download/latest/{e['apk']}"
            for e in entries.values() if e.get("apk")
        ]

    # Map apk filename -> manifest entry for exact version verification
    apk_to_entry: Dict[str, Dict[str, Any]] = {
        e["apk"]: e for e in entries.values() if e.get("apk")
    }

    errors: List[str] = []

    # Every manifest APK must be linked from the downloads page
    for apk in apk_to_entry:
        if not any(link.rsplit("/", 1)[-1] == apk for link in page_links):
            errors.append(f"[page] manifest APK '{apk}' has no link in downloads.html")

    print(f"Validating {len(apps)} Obtainium app configurations against {len(page_links)} download links...\n")

    for idx, app in enumerate(apps, 1):
        app_name = app.get("name", f"App #{idx}")
        app_id = app.get("id", "")
        url = app.get("url", "")
        settings_str = app.get("additionalSettings", "")

        # 1. Validate required fields — entries must point at the downloads page
        if not app_id:
            errors.append(f"[{app_name}] Missing required 'id' field")
            continue
        if not url or "/downloads.html" not in url:
            errors.append(f"[{app_name}] 'url' must be the downloads page, got: {url}")
            continue
        if not settings_str:
            errors.append(f"[{app_name}] Missing 'additionalSettings'")
            continue

        # 2. Parse additionalSettings JSON
        try:
            settings = json.loads(settings_str)
        except Exception as e:
            errors.append(f"[{app_name}] additionalSettings is not valid JSON string: {e}")
            continue

        filter_regex_str = settings.get("apkFilterRegEx", "")
        ver_regex_str = settings.get("versionExtractionRegEx", "")
        group_to_use = settings.get("matchGroupToUse", "1")

        if not filter_regex_str:
            errors.append(f"[{app_name}] Missing 'apkFilterRegEx' in additionalSettings")
            continue
        if not ver_regex_str:
            errors.append(f"[{app_name}] Missing 'versionExtractionRegEx' in additionalSettings")
            continue

        # 3. Test apkFilterRegEx
        try:
            filter_pattern = re.compile(filter_regex_str)
        except re.error as e:
            errors.append(f"[{app_name}] Invalid regex in apkFilterRegEx '{filter_regex_str}': {e}")
            continue

        matching_links = [link for link in page_links if filter_pattern.search(link)]

        if len(matching_links) == 0:
            errors.append(f"[{app_name}] apkFilterRegEx '{filter_regex_str}' matched 0 download links")
            continue
        elif len(matching_links) > 1:
            errors.append(
                f"[{app_name}] apkFilterRegEx '{filter_regex_str}' matched MULTIPLE ({len(matching_links)}) links: {matching_links}"
            )
            continue

        matched_link = matching_links[0]
        matched_apk = matched_link.rsplit("/", 1)[-1]
        entry = apk_to_entry.get(matched_apk, {})
        expected_version = entry.get("built_version", "")

        # 4. Test versionExtractionRegEx
        try:
            ver_pattern = re.compile(ver_regex_str)
        except re.error as e:
            errors.append(f"[{app_name}] Invalid regex in versionExtractionRegEx '{ver_regex_str}': {e}")
            continue

        match = ver_pattern.search(matched_link)
        if not match:
            errors.append(
                f"[{app_name}] versionExtractionRegEx '{ver_regex_str}' failed to match link '{matched_link}'"
            )
            continue

        try:
            group_idx = int(group_to_use)
            extracted_version = match.group(group_idx)
        except Exception as e:
            errors.append(
                f"[{app_name}] Could not extract group '{group_to_use}' with versionExtractionRegEx: {e}"
            )
            continue

        if extracted_version != expected_version:
            errors.append(
                f"[{app_name}] Extracted version '{extracted_version}' does not match manifest built_version '{expected_version}' for '{matched_apk}'"
            )
            continue

        print(f"  [OK] {app_name:<28} -> {matched_apk} (v{extracted_version})")

    print("")
    if errors:
        print(f"[ERROR] Obtainium validation failed with {len(errors)} error(s):", file=sys.stderr)
        for err in errors:
            print(f"  - {err}", file=sys.stderr)
        return False

    print(f"All {len(apps)} Obtainium apps passed strict validation successfully!")
    return True


def main() -> int:
    obtainium_path = Path("obtainium.json")
    manifest_path = Path("manifest.json")

    success = validate_obtainium_bundle(obtainium_path, manifest_path)
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
