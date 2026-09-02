#!/usr/bin/env python3
"""
Generate sleek, human-written release notes for Morphe AutoBuilds releases.

Includes:
1. Sleek summary & Web App Store portal banner.
2. Clean table of newly updated/rebuilt apps in this specific build cycle.
3. What's New in Patches (upstream patch notes for updated sources).
4. Known Issues / Failed Patches (if any).
5. Credits to patch creators.
"""
import os
import re
import sys
import json
from pathlib import Path
from typing import Dict, List, Optional

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


def clean_changelog_body(body: str, max_lines: int = 35) -> str:
    """Format and sanitize release notes body for inclusion in GitHub release markdown."""
    if not body:
        return "*No upstream changelog description provided.*"
    
    text = body.replace("\r\n", "\n").strip()
    text = re.sub(r'<!--.*?-->', '', text, flags=re.DOTALL)
    
    lines = text.splitlines()
    if len(lines) > max_lines:
        truncated = lines[:max_lines]
        truncated.append(f"\n*... (and {len(lines) - max_lines} more lines in upstream release)*")
        text = "\n".join(truncated)
        
    return text.strip()


def detect_arch(filename: str) -> str:
    fn = filename.lower()
    if "arm64-v8a" in fn or "arm64" in fn:
        return "ARM64"
    elif "armeabi-v7a" in fn or "armv7" in fn:
        return "ARMv7"
    elif "x86_64" in fn:
        return "x86_64"
    elif "x86" in fn:
        return "x86"
    return "Universal"


def format_app_display(app_name: str) -> str:
    name_map = {
        "youtube": "YouTube",
        "youtube-music": "YouTube Music",
        "reddit": "Reddit",
        "instagram": "Instagram",
        "x": "X (Twitter)",
        "pinterest": "Pinterest",
        "telegram": "Telegram",
        "vn": "VN Video Editor",
        "sdmaidse": "SD Maid 2 / SE",
        "threads": "Threads",
        "google-photos": "Google Photos",
        "tradingview": "TradingView",
        "pocketcasts": "Pocket Casts",
        "depthwallpaper": "Depth Wallpaper",
        "minimalwidgets": "Minimal Widgets",
        "protonpass": "Proton Pass",
        "serverauditor": "Server Auditor (Termius)",
        "vocabulary": "Vocabulary",
        "pinnit": "Pinnit",
        "gboard": "Gboard",
        "vivaldi-snapshot": "Vivaldi Snapshot",
        "taskmanager": "TaskManager",
        "habitkit": "HabitKit",
        "notesnook": "Notesnook",
        "duolingo": "Duolingo",
        "brave": "Brave Browser",
    }
    return name_map.get(app_name.lower().strip(), app_name.replace("-", " ").title())


def get_source_display_name(source: str) -> str:
    source_map = {
        "morphe": "Morphe Patches",
        "piko": "Piko Patches",
        "piko-dev": "Piko (Dev) Patches",
        "paresh": "Paresh Patches",
        "durgesh": "Durgesh (Chiggi) Patches",
        "rookie": "Rookie Patches",
        "rushiranpise": "Rushi (Doom) Patches",
        "browzomje": "Browzomje Patches",
        "dh6k": "dh6k Patches",
        "morning-entree": "Morning Entree Patches",
        "hxreborn": "hxreborn Patches",
        "ample": "Ample Patches",
        "jasonwu": "Jasonwu (Gboard) Patches",
        "kveld9": "kveld9 Patches",
        "hoodles": "Hoodles Patches",
    }
    return source_map.get(source.lower(), f"{source.capitalize()} Patches")


def parse_apk_details(filename: str) -> tuple[str, str, str]:
    """Extract (app_key, source, version) from standard apk name: {app}-{arch}-{source}-v{ver}.apk"""
    name_no_ext = filename.replace(".apk", "")
    parts = name_no_ext.split("-")
    app_key = parts[0] if parts else "app"
    
    # Try to extract version
    ver_match = re.search(r'-v?(\d+\.[\w\.\-]+)$', name_no_ext)
    version = f"v{ver_match.group(1)}" if ver_match else ""
    
    # Try to extract source
    source = ""
    known_sources = [
        "morphe", "piko-dev", "piko", "paresh", "durgesh", "chiggi", 
        "rookie", "rushiranpise", "rushi", "browzomje", "dh6k", 
        "morning-entree", "entree", "hxreborn", "ample", "jasonwu", "kveld9", "hoodles"
    ]
    for s in known_sources:
        if f"-{s}-" in name_no_ext or f"-{s}" in name_no_ext:
            source = s
            break
            
    return app_key, source, version


def main() -> int:
    release_notes_file = Path("release_notes.md")
    patch_changelogs_file = Path("patch_changelogs.json")
    
    # Check for failed patches file
    failed_patches_file = None
    for fp in [Path("./release-apks/failed_patches.json"), Path("./build_records/failed_patches.json"), Path("failed_patches.json")]:
        if fp.exists():
            failed_patches_file = fp
            break

    # Read patch changelogs
    changelogs_data: Dict[str, dict] = {}
    if patch_changelogs_file.exists():
        try:
            with patch_changelogs_file.open("r", encoding="utf-8") as f:
                changelogs_data = json.load(f)
        except Exception as e:
            print(f"⚠️ Error reading patch_changelogs.json: {e}")

    # Read failed patches
    failed_patches: Dict[str, list] = {}
    if failed_patches_file and failed_patches_file.exists():
        try:
            with failed_patches_file.open("r", encoding="utf-8") as f:
                failed_patches = json.load(f)
        except Exception as e:
            print(f"⚠️ Error reading failed patches: {e}")

    # Identify ONLY newly rebuilt APKs in this cycle
    rebuilt_apks: List[Path] = []
    search_dirs = [Path("./release-apks"), Path("./build_records"), Path(".")]
    for sdir in search_dirs:
        if sdir.exists():
            for apk in sdir.glob("*.apk"):
                if apk.name not in [a.name for a in rebuilt_apks]:
                    rebuilt_apks.append(apk)

    # Read build records or manifest for exact metadata
    built_records_map = {}
    records_dir = Path("build_records")
    if records_dir.exists():
        for rf in records_dir.glob("*.json"):
            try:
                with rf.open("r", encoding="utf-8") as f:
                    rdata = json.load(f)
                    if isinstance(rdata, dict) and "apk" in rdata:
                        built_records_map[rdata["apk"]] = rdata
            except Exception:
                pass

    repo_name = os.environ.get("GITHUB_REPOSITORY", "yashrajrocxx/Mophe-AutoBuilds")
    pages_url = f"https://{repo_name.split('/')[0]}.github.io/{repo_name.split('/')[1]}/" if "/" in repo_name else "https://yashrajrocxx.github.io/Mophe-AutoBuilds/"

    # Start human-written sleek markdown
    content: List[str] = []
    content.append("# ⚡ Morphe AutoBuilds — Latest Release\n")
    content.append("Automated compilation of custom patched Android apps with verified ad-blocking, background playback, and premium features.\n")
    
    # Sleek Callout Banner to Web Store
    content.append(f"> 🌐 **Full App Catalog:** Browse all apps with instant search, categories, and direct APK downloads on our [**Web Store Portal**]({pages_url}).\n")

    # 1. Newly Rebuilt Apps Table (ONLY apps built in this release run)
    if rebuilt_apks:
        content.append("## 🚀 Rebuilt & Updated Apps in This Release\n")
        content.append("| Application | Version | Patch Source | Architecture | Direct Download |")
        content.append("| :--- | :--- | :--- | :---: | :--- |")

        for apk in sorted(rebuilt_apks, key=lambda a: a.name.lower()):
            fn = apk.name
            arch = detect_arch(fn)
            dl_url = f"https://github/{repo_name}/releases/download/latest/{fn}".replace("https://github/", "https://github.com/")

            record = built_records_map.get(fn, {})
            app_key = record.get("app_name")
            source = record.get("source")
            version = record.get("built_version")

            if not app_key or not version:
                parsed_app, parsed_src, parsed_ver = parse_apk_details(fn)
                app_key = app_key or parsed_app
                source = source or parsed_src
                version = version or parsed_ver or "Latest"

            app_title = format_app_display(app_key)
            src_title = get_source_display_name(source).replace(" Patches", "") if source else "Custom"
            ver_display = f"`{version}`" if version else "`Latest`"

            content.append(f"| **{app_title}** | {ver_display} | {src_title} | `{arch}` | [Download APK]({dl_url}) |")
        content.append("")
    elif changelogs_data:
        # If no APKs in current folder yet (e.g. dry-run check), show affected apps from changelogs
        all_affected = set()
        for s in changelogs_data.values():
            for a in s.get("affected_apps", []):
                all_affected.add(a)
        if all_affected:
            content.append("## 🚀 Updated Apps in This Cycle\n")
            apps_list = ", ".join([f"**{format_app_display(a)}**" for a in sorted(all_affected)])
            content.append(f"The following applications received patch updates in this build cycle: {apps_list}.\n")

    # 2. What's New in Patches / Upstream Changelogs
    if changelogs_data:
        content.append("## 📦 What's New in Upstream Patches\n")
        
        for source_key, sdata in changelogs_data.items():
            source_display = get_source_display_name(source_key)
            old_tag = sdata.get("old_tag", "")
            new_tag = sdata.get("new_tag") or sdata.get("tag", "")
            url = sdata.get("url", "")
            body = sdata.get("body", "")
            affected_apps = sdata.get("affected_apps", [])
            published_at = sdata.get("published_at", "")
            if published_at and "T" in published_at:
                published_at = published_at.split("T")[0]

            version_transition = f"`{old_tag}` ➔ `{new_tag}`" if old_tag and old_tag != new_tag else f"`{new_tag}`"
            
            content.append(f"### ✨ {source_display} ({version_transition})")
            
            meta_items = []
            if affected_apps:
                apps_str = ", ".join([f"**{format_app_display(a)}**" for a in affected_apps])
                meta_items.append(f"**Target Apps:** {apps_str}")
            if url:
                release_link = f"[{new_tag}]({url})" if new_tag else f"[View Source]({url})"
                if published_at:
                    meta_items.append(f"**Released:** {release_link} ({published_at})")
                else:
                    meta_items.append(f"**Released:** {release_link}")

            if meta_items:
                content.append(f"> {' • '.join(meta_items)}\n")

            cleaned_body = clean_changelog_body(body)
            content.append("<details>")
            content.append("<summary><b>View Detailed Patch Notes</b></summary>\n")
            content.append(cleaned_body)
            content.append("\n</details>\n")
            content.append("---\n")

    # 3. Known Issues / Failed Patches (if any)
    if failed_patches:
        has_any = any(len(p) > 0 for p in failed_patches.values())
        if has_any:
            content.append("## ⚠️ Compatibility Notes\n")
            for app, patches in failed_patches.items():
                if patches:
                    patches_str = ", ".join([f"`{p}`" for p in patches])
                    content.append(f"- **{format_app_display(app)}**: `{len(patches)}` patch skipped due to upstream version change ({patches_str})")
            content.append("")

    # 4. Credits & References
    content.append("## 🛠️ Credits & Toolchains\n")
    content.append("Built with [Morphe](https://github.com/MorpheApp) CLI. Credits to all open-source patch developers:")
    content.append("- **Morphe/ReVanced:** [MorpheApp/morphe-patches](https://github.com/MorpheApp/morphe-patches)")
    content.append("- **Piko:** [crimera/piko](https://github.com/crimera/piko)")
    content.append("- **Paresh:** [Paresh-Maheshwari/paresh-patches](https://gitlab.com/Paresh-Maheshwari/paresh-patches)")
    content.append("- **Rushi (Doom):** [rushiranpise/morphe-patches](https://github.com/rushiranpise/morphe-patches)")
    content.append("- **Morning Entree:** [Entree3k/Morning-Entree-Patches](https://github.com/Entree3k/Morning-Entree-Patches)")
    content.append("- **Gboard Patches:** [jasonwu1994/Gboard-patches](https://github.com/jasonwu1994/Gboard-patches)")
    content.append("- **kveld9 Patches:** [kveld9/kveld-morphe-patches](https://github.com/kveld9/kveld-morphe-patches)")
    content.append("- **Ample Patches:** [AmpleReVanced/revanced-patches](https://github.com/AmpleReVanced/revanced-patches)")
    content.append("- **Hoodles:** [hoo-dles/morphe-patches](https://github.com/hoo-dles/morphe-patches)")
    content.append("- **hxreborn Patches:** [hxreborn/morphe-patches](https://github.com/hxreborn/morphe-patches)")
    content.append("- **Rookie Patches:** [RookieEnough/De-ReVanced](https://github.com/RookieEnough/De-ReVanced)")
    content.append("- **Durgesh/Chiggi:** [durgesh0505/chiggi_morphe_patches](https://github.com/durgesh0505/chiggi_morphe_patches)")
    content.append("- **Browzomje:** [browzomje/browzomje-patches](https://github.com/browzomje/browzomje-patches)")
    content.append("- **dh6k:** [dh6k/morphe-patches](https://github.com/dh6k/morphe-patches)\n")

    # 5. Non-root Note
    content.append("## ℹ️ Notes")
    content.append("Non-root GmsCore / MicroG-RE is recommended for Google account sign-in on patched Google apps.\n")

    full_text = "\n".join(content)
    release_notes_file.write_text(full_text, encoding="utf-8")
    print(f"Generated {release_notes_file} ({len(full_text)} characters)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
