#!/usr/bin/env python3
"""Generate Obtainium configuration and deep links from manifest.json.

This script reads manifest.json (the source of truth for all built/released APKs),
derives exact regex filters and version extraction patterns for each app, and produces:
  1. obtainium.json (bulk import file for Obtainium, containing the "apps" array)
  2. pages/public/obtainium.json (public web asset for one-click bulk import)
  3. Updates manifest.json entries with 'obtainium_url' (web redirect deep link)
     and 'obtainium_deep_link' (direct protocol link).
"""
import os
import re
import sys
import json
import urllib.parse
from pathlib import Path
from typing import Dict, Any, List

if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

DEFAULT_REPO = "yashrajrocxx/Mophe-AutoBuilds"
DEFAULT_AUTHOR = "yashrajrocxx"

NAME_MAP = {
    "youtube":          "YouTube",
    "youtube-music":    "YouTube Music",
    "reddit":           "Reddit",
    "instagram":        "Instagram",
    "twitter":          "X (Twitter)",
    "pinterest":        "Pinterest",
    "telegram":         "Telegram",
    "sdmaidse":         "SD Maid 2 / SE",
    "threads":          "Threads",
    "google-photos":    "Google Photos",
    "pocketcasts":      "Pocket Casts",
    "depthwallpaper":   "Depth Wallpaper",
    "minimalwidgets":   "Minimal Widgets",
    "protonpass":       "Proton Pass",
    "serverauditor":    "Server Auditor (Termius)",
    "vocabulary":       "Vocabulary",
    "gboard":           "Gboard",
    "vivaldi":          "Vivaldi Browser",
    "habitkit":         "HabitKit",
    "notesnook":        "Notesnook",
    "duolingo":         "Duolingo",
    "brave":            "Brave Browser",
    "jiohotstar":       "JioHotstar",
}


def get_display_name(app_name: str) -> str:
    """Format app name for human-readable display."""
    return NAME_MAP.get(app_name.lower().strip(), app_name.replace("-", " ").title())


def extract_identity_prefix(apk_name: str) -> str:
    """Extract identity prefix from an APK filename.
    
    APKs follow the pattern: {app}-{arch}-{source}-v{version}.apk.
    Splitting off the version portion gives the exact prefix.
    """
    if not apk_name:
        return ""
    match = re.search(r"^(.*)-v\d+\.\d[\w.+\-]*\.apk$", apk_name)
    if match:
        return match.group(1)
    
    # Fallback to splitting by -v if needed
    if "-v" in apk_name:
        stem = apk_name[:-4] if apk_name.lower().endswith(".apk") else apk_name
        parts = stem.rsplit("-v", 1)
        return parts[0]
    
    return ""


def build_obtainium_app(
    entry_key: str,
    entry: Dict[str, Any],
    repo_slug: str,
    author: str,
    arch_counts: Dict[str, int],
    pages_url: str,
) -> Dict[str, Any]:
    """Construct an Obtainium App entry for a single manifest entry.

    Entries use the HTML app source pointed at the generated downloads page.
    This is deliberate: our single rolling GitHub release is tagged "latest"
    for every app, and current Obtainium applies versionExtractionRegEx to
    the *release tag* for GitHub sources — a filename-targeted regex can
    never match "latest" and every install fails version detection. The
    HTML source instead applies the regex to the matched download link,
    where our filenames carry the per-app version.
    """
    app_name = entry.get("app_name", "")
    arch = entry.get("arch", "arm64-v8a")
    apk = entry.get("apk", "")
    pkg = entry.get("package") or f"org.morphe.{app_name}"

    prefix = extract_identity_prefix(apk)
    if not prefix:
        raise ValueError(f"Could not determine identity prefix from APK filename: {apk}")

    # Identity head: "{app}-{arch}-". The patch-source name is deliberately
    # NOT baked in — sources get renamed (dh6k → kveld9, …) and baked regexes
    # then match zero assets. We target just the app+arch prefix so source
    # renames never break the filter.
    head = f"{app_name}-{arch}-"
    if not prefix.startswith(head):
        # Unexpected filename layout — fall back to the exact baked prefix.
        head = prefix.rsplit("-", 1)[0] + "-" if "-" in prefix else prefix + "-"

    base_name = get_display_name(app_name)
    # If this app has builds for multiple architectures, disambiguate with arch in name
    display_name = f"{base_name} ({arch})" if arch_counts.get(app_name, 0) > 1 else base_name

    # ── Regex patterns (NO /.../ delimiters — Obtainium uses raw regex strings) ──
    # Obtainium's HTML source matches against the full download link URL, so the
    # pattern needs to match the filename portion. Do NOT wrap in /.../ — Obtainium
    # is not JavaScript; delimiters cause "No APK found" every time.
    # [^/]+ in the version group avoids over-matching across path separators.
    filter_pat = f"{head}.*-v.*\\.apk$"
    ver_pat    = f"{head}.*-v([^/]+)\\.apk$"

    additional_settings = json.dumps({
        "apkFilterRegEx": filter_pat,
        "versionExtractionRegEx": ver_pat,
        "matchGroupToUse": "1"
    }, separators=(',', ':'))


    return {
        "id": pkg,
        "url": pages_url,
        "author": author,
        "name": display_name,
        "preferredApkIndex": 0,
        "additionalSettings": additional_settings
    }


def make_deep_links(app_obj: Dict[str, Any]) -> tuple[str, str]:
    """Generate both direct obtainium:// and https redirect links for an app entry."""
    json_str = json.dumps(app_obj, separators=(',', ':'))
    encoded_json = urllib.parse.quote(json_str)
    direct_link = f"obtainium://app/{encoded_json}"
    redirect_url = f"https://apps.obtainium.imranr.dev/redirect?r={urllib.parse.quote(direct_link, safe='')}"
    return direct_link, redirect_url


def main() -> int:
    manifest_path = Path("manifest.json")
    if not manifest_path.exists():
        print("[ERROR] manifest.json not found; cannot generate Obtainium configurations")
        return 1

    with manifest_path.open("r", encoding="utf-8") as f:
        manifest = json.load(f)

    entries = manifest.get("entries", {})
    if not entries:
        print("[WARN] No entries found in manifest.json")
        return 0

    repo_slug = os.environ.get("GITHUB_REPOSITORY", "").strip() or DEFAULT_REPO
    author = repo_slug.split("/")[0] if "/" in repo_slug else DEFAULT_AUTHOR
    repo_name = repo_slug.split("/")[1] if "/" in repo_slug else repo_slug
    pages_url = f"https://{author}.github.io/{repo_name}/downloads.html"

    # Count architectures per app to label disambiguated names if needed
    arch_counts: Dict[str, int] = {}
    for entry in entries.values():
        if entry.get("apk") and entry.get("built_version"):
            app = entry.get("app_name", "")
            arch_counts[app] = arch_counts.get(app, 0) + 1

    obtainium_apps: List[Dict[str, Any]] = []
    generated_count = 0

    for key, entry in entries.items():
        apk = entry.get("apk", "").strip()
        built_version = entry.get("built_version", "").strip()

        # Skip entries that have no produced APK or version
        if not apk or not built_version:
            print(f"  Skipping {key} (no APK or built_version yet)")
            continue

        try:
            app_obj = build_obtainium_app(key, entry, repo_slug, author, arch_counts, pages_url)
            direct_link, redirect_url = make_deep_links(app_obj)

            # Store links in manifest entry for direct web consumption
            entry["obtainium_url"] = redirect_url
            entry["obtainium_deep_link"] = direct_link

            obtainium_apps.append(app_obj)
            generated_count += 1
            print(f"  [OK] {entry.get('app_name')} ({entry.get('arch')}): {app_obj['name']}")
        except Exception as e:
            print(f"  [ERROR] Error processing {key}: {e}")

    # 1. Update manifest.json with deep links
    with manifest_path.open("w", encoding="utf-8", newline="\n") as f:
        json.dump(manifest, f, indent=2)
    print(f"[OK] Updated manifest.json with Obtainium links for {generated_count} apps")

    # 2. Write obtainium.json bundle file
    bundle_data = {"apps": obtainium_apps}
    obtainium_file = Path("obtainium.json")
    with obtainium_file.open("w", encoding="utf-8", newline="\n") as f:
        json.dump(bundle_data, f, indent=2)
    print(f"[OK] Generated obtainium.json ({len(obtainium_apps)} apps)")

    # 3. Mirror obtainium.json to pages/public/ if directory exists
    pages_public = Path("pages/public")
    if pages_public.exists():
        pages_obtainium = pages_public / "obtainium.json"
        with pages_obtainium.open("w", encoding="utf-8", newline="\n") as f:
            json.dump(bundle_data, f, indent=2)
        print(f"[OK] Copied obtainium.json to pages/public/obtainium.json")

    return 0


if __name__ == "__main__":
    sys.exit(main())
