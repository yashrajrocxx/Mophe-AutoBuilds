#!/usr/bin/env python3
"""
Generate comprehensive release notes for Morphe AutoBuilds releases.

Includes:
1. Patched APK assets table with direct download links.
2. What's New in Patches & Upstream Changelogs (from patch_changelogs.json).
3. Known Issues / Failed Patches (from failed_patches.json).
4. Credits & References.
5. Disclaimer.
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


def clean_changelog_body(body: str, max_lines: int = 40) -> str:
    """Format and sanitize release notes body for inclusion in GitHub release markdown."""
    if not body:
        return "*No upstream changelog description provided.*"
    
    # Strip carriage returns
    text = body.replace("\r\n", "\n").strip()
    
    # Remove HTML comments
    text = re.sub(r'<!--.*?-->', '', text, flags=re.DOTALL)
    
    # If changelog is extremely long, truncate gracefully
    lines = text.splitlines()
    if len(lines) > max_lines:
        truncated = lines[:max_lines]
        truncated.append(f"\n*... (and {len(lines) - max_lines} more lines in upstream release)*")
        text = "\n".join(truncated)
        
    return text.strip()


def detect_arch(filename: str) -> str:
    fn = filename.lower()
    if "arm64-v8a" in fn:
        return "arm64-v8a"
    elif "armeabi-v7a" in fn:
        return "armeabi-v7a"
    elif "x86_64" in fn:
        return "x86_64"
    elif "x86" in fn:
        return "x86"
    return "universal"


def get_source_display_name(source: str) -> str:
    source_map = {
        "morphe": "Morphe Patches",
        "piko": "Piko Patches",
        "piko-dev": "Piko (Dev) Patches",
        "paresh": "Paresh Patches",
        "durgesh": "Durgesh (Chiggi) Patches",
        "rookie": "Rookie Patches",
        "rushiranpise": "Rushi Patches",
        "browzomje": "Browzomje Patches",
        "dh6k": "dh6k Patches",
        "morning-entree": "Morning Entree Patches",
        "hxreborn": "hxreborn Patches",
        "ample": "Ample Patches",
    }
    return source_map.get(source.lower(), f"{source.capitalize()} Patches")


def main() -> int:
    release_notes_file = Path("release_notes.md")
    release_assets_file = Path("release_assets.txt")
    patch_changelogs_file = Path("patch_changelogs.json")
    
    # Check for failed patches file in common locations
    failed_patches_file = None
    for fp in [Path("./release-apks/failed_patches.json"), Path("./build_records/failed_patches.json"), Path("failed_patches.json")]:
        if fp.exists():
            failed_patches_file = fp
            break

    # Determine asset list
    asset_names: List[str] = []
    if release_assets_file.exists():
        with release_assets_file.open("r", encoding="utf-8") as f:
            for line in f:
                name = line.strip()
                if name and name != "manifest.json" and name != "build_report.json":
                    asset_names.append(name)
    else:
        # Fallback: inspect directory
        search_dirs = [Path("./release-apks"), Path(".")]
        for sdir in search_dirs:
            if sdir.exists():
                for apk in sorted(sdir.glob("*.apk")):
                    if apk.name not in asset_names:
                        asset_names.append(apk.name)

    asset_names = sorted(set(asset_names))

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

    # Build Markdown Content
    content: List[str] = []
    content.append("# 🔧 Morphe APKs - Custom Build\n")
    content.append("Automated compilation of custom patched Android applications using community ReVanced toolchains.\n")

    # 1. Assets Table
    content.append("## 📱 Patched Assets in This Release\n")
    repo_name = os.environ.get("GITHUB_REPOSITORY", "yashrajrocxx/Mophe-AutoBuilds")
    if asset_names:
        content.append("| Application File | Architecture | Direct Download |")
        content.append("| :--- | :---: | :--- |")
        for filename in asset_names:
            arch = detect_arch(filename)
            dl_url = f"https://github.com/{repo_name}/releases/download/latest/{filename}"
            content.append(f"| **{filename}** | `{arch}` | [Download]({dl_url}) |")
    else:
        content.append("*No APK assets found in this release.*")
    content.append("")

    # 2. What's New in Patches / Changelogs Section
    if changelogs_data:
        content.append("## 🚀 What's New in Patches & Upstream Changes\n")
        
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
            
            content.append(f"### 📦 {source_display} ({version_transition})")
            
            meta_items = []
            if affected_apps:
                apps_str = ", ".join([f"`{a.capitalize()}`" for a in affected_apps])
                meta_items.append(f"**Apps Affected:** {apps_str}")
            if url:
                release_link = f"[{new_tag}]({url})" if new_tag else f"[View Release]({url})"
                if published_at:
                    meta_items.append(f"**Upstream Release:** {release_link} • *{published_at}*")
                else:
                    meta_items.append(f"**Upstream Release:** {release_link}")

            if meta_items:
                content.append(f"> {' | '.join(meta_items)}\n")

            cleaned_body = clean_changelog_body(body)
            content.append("<details open>")
            content.append("<summary><b>Changelog Details</b></summary>\n")
            content.append(cleaned_body)
            content.append("\n</details>\n")
            content.append("---\n")

    # 3. Known Issues / Failed Patches
    if failed_patches:
        content.append("## ⚠️ Known Issues / Failed Patches\n")
        for app, patches in failed_patches.items():
            if patches:
                patches_str = ", ".join([f"`{p}`" for p in patches])
                content.append(f"- **{app}**: Failed to apply `{len(patches)}` patch(es) ({patches_str})")
        content.append("")

    # 4. Credits & References
    content.append("## 🛠️ Credits & References\n")
    content.append("This project is powered by [Morphe](https://github.com/MorpheApp) tools. Credits to all patch developers:")
    content.append("- **Morphe/ReVanced Patches:** [MorpheApp/morphe-patches](https://github.com/MorpheApp/morphe-patches)")
    content.append("- **Piko Patches:** [crimera/piko](https://github.com/crimera/piko)")
    content.append("- **Paresh Patches:** [Paresh-Maheshwari/paresh-patches](https://gitlab.com/Paresh-Maheshwari/paresh-patches)")
    content.append("- **Durgesh/Chiggi Patches:** [durgesh0505/chiggi_morphe_patches](https://github.com/durgesh0505/chiggi_morphe_patches)")
    content.append("- **Rookie Patches:** [RookieEnough/De-ReVanced](https://github.com/RookieEnough/De-ReVanced)")
    content.append("- **Rushi Patches:** [rushiranpise/morphe-patches](https://github.com/rushiranpise/morphe-patches)")
    content.append("- **Browzomje Patches:** [browzomje/browzomje-patches](https://github.com/browzomje/browzomje-patches)")
    content.append("- **dh6k Patches:** [dh6k/morphe-patches](https://github.com/dh6k/morphe-patches)")
    content.append("- **Morning Entree Patches:** [Entree3k/Morning-Entree-Patches](https://github.com/Entree3k/Morning-Entree-Patches)")
    content.append("- **hxreborn Patches:** [hxreborn/morphe-patches](https://github.com/hxreborn/morphe-patches)")
    content.append("- **Ample Patches:** [AmpleReVanced/revanced-patches](https://github.com/AmpleReVanced/revanced-patches)\n")

    # 5. Disclaimer
    content.append("## ⚠️ Disclaimer")
    content.append("These APKs are built automatically. Use at your own risk. Non-root GmsCore/MicroG-RE is required for Google-dependent apps.\n")

    full_text = "\n".join(content)
    release_notes_file.write_text(full_text, encoding="utf-8")
    print(f"Generated {release_notes_file} ({len(full_text)} characters)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
