#!/usr/bin/env python3
import os
import sys
import json
import argparse
import subprocess
import shutil
from pathlib import Path

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

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

def check_prerequisites():
    print("🔍 Checking local build prerequisites...")
    
    # 1. Java check
    java = shutil.which("java")
    if not java:
        print("❌ Java JDK is not installed or not in PATH!")
        print("👉 Please install JDK 17 or JDK 21 (e.g. 'sudo apt install openjdk-21-jdk' on Ubuntu).")
        return False
    print("  ✓ Java found in PATH")
    
    # 2. Python dependencies check
    try:
        import bs4
        import requests
    except ImportError:
        print("❌ Python packages 'requests' or 'beautifulsoup4' are missing.")
        print("👉 Please run: pip install requests beautifulsoup4")
        return False
    print("  ✓ Python dependencies (requests, bs4) are installed")

    # 3. apksigner check
    root = Path(__file__).resolve().parent
    sys.path.insert(0, str(root))
    try:
        from src.utils import find_apksigner
        apksigner_path = find_apksigner()
        if not apksigner_path:
            print("❌ apksigner not found!")
            print("👉 Please install Android SDK build-tools and put apksigner on PATH or set ANDROID_HOME.")
            print("   (On Debian/Ubuntu, you can run: sudo apt install apksigner)")
            return False
        print(f"  ✓ apksigner found at: {apksigner_path}")
    except Exception as e:
        print(f"⚠️ Warning during apksigner check: {e}")

    # 4. gplaydl (Google Play) check — non-fatal, scrapers are fallbacks
    gplaydl_bin = shutil.which("gplaydl")
    if not gplaydl_bin:
        print("  ⚠️  gplaydl not found in PATH")
        print("     Google Play source will be skipped.")
        print("     To install: pip install gplaydl")
    else:
        print(f"  ✓ gplaydl found at: {gplaydl_bin}")
        try:
            test = subprocess.run(
                ["gplaydl", "info", "--help"],
                capture_output=True, text=True, timeout=5
            )
            if test.returncode == 0:
                print("  ✓ gplaydl is operational")
                print("     ℹ️  If no account is linked yet, run: gplaydl link <code>")
                print("        (get the code from the gplaydl Authenticator app)")
        except Exception:
            pass

    print("✅ All prerequisites checked!\n")
    return True


def run_update_check(root: Path) -> dict:
    """Run check_app_updates.py and return the plan data."""
    print("🔍 Checking for patch and app updates from upstream sources...")
    check_script = root / "scripts" / "check_app_updates.py"
    
    res = subprocess.run(
        [sys.executable, str(check_script)],
        cwd=str(root),
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace"
    )
    
    plan = {
        "build_matrix": [],
        "carry_over": [],
        "patch_changelogs": {},
        "raw_output": res.stdout
    }

    bm_path = root / "build_matrix.json"
    if bm_path.exists():
        try:
            with open(bm_path, "r", encoding="utf-8") as f:
                plan["build_matrix"] = json.load(f)
        except Exception:
            pass

    co_path = root / "carry_over.json"
    if co_path.exists():
        try:
            with open(co_path, "r", encoding="utf-8") as f:
                plan["carry_over"] = json.load(f)
        except Exception:
            pass

    pc_path = root / "patch_changelogs.json"
    if pc_path.exists():
        try:
            with open(pc_path, "r", encoding="utf-8") as f:
                plan["patch_changelogs"] = json.load(f)
        except Exception:
            pass

    return plan


def display_patch_changelogs(patch_changelogs: dict):
    """Print beautifully formatted patch changelogs in the console."""
    if not patch_changelogs:
        print("ℹ️  No new patch updates found. All patch sources are up to date.")
        return

    print("\n" + "=" * 70)
    print("🚀  WHAT'S NEW IN UPSTREAM PATCHES")
    print("=" * 70)

    for source_key, sdata in patch_changelogs.items():
        source_name = source_key.capitalize()
        old_tag = sdata.get("old_tag", "")
        new_tag = sdata.get("new_tag") or sdata.get("tag", "")
        url = sdata.get("url", "")
        body = sdata.get("body", "").strip()
        affected_apps = sdata.get("affected_apps", [])
        published_at = sdata.get("published_at", "")
        if published_at and "T" in published_at:
            published_at = published_at.split("T")[0]

        tag_str = f"{old_tag} ➔ {new_tag}" if old_tag and old_tag != new_tag else new_tag
        print(f"\n📦 {source_name} Patches [{tag_str}]")
        if affected_apps:
            print(f"   📱 Affected Apps: {', '.join([a.capitalize() for a in affected_apps])}")
        if url:
            print(f"   🔗 Upstream URL : {url} ({published_at or 'latest'})")

        if body:
            print("   📝 Changelog Highlights:")
            lines = body.replace("\r\n", "\n").splitlines()
            shown = 0
            for line in lines:
                if line.strip().startswith(("#", "*", "-", "+")) and shown < 12:
                    print(f"      {line.strip()}")
                    shown += 1
            if len(lines) > 12:
                print(f"      ... (view full release on GitHub for {len(lines) - shown} more lines)")
        print("-" * 70)


def main():
    parser = argparse.ArgumentParser(description="Morphe AutoBuilds Local Runner")
    parser.add_argument("--check", "--check-updates", dest="check_only", action="store_true", help="Only check for patch and app updates and display changelogs without building")
    parser.add_argument("--incremental", "-i", action="store_true", help="Only build apps that have patch or version updates")
    parser.add_argument("--all", "-a", action="store_true", help="Force rebuild all configured apps")
    args = parser.parse_args()

    root = Path(__file__).resolve().parent
    patch_config_path = root / "patch-config.json"
    
    if not patch_config_path.exists():
        print(f"❌ patch-config.json not found in {root}")
        sys.exit(1)

    # 1. Update check
    plan = run_update_check(root)
    display_patch_changelogs(plan.get("patch_changelogs", {}))

    if args.check_only:
        print("\n📊 Update Summary:")
        print(f"  - Apps needing rebuild : {len(plan.get('build_matrix', []))}")
        print(f"  - Apps carried over    : {len(plan.get('carry_over', []))}")
        print(f"  - Updated patch sources: {len(plan.get('patch_changelogs', {}))}")
        return

    if not check_prerequisites():
        print("❌ Prerequisites check failed. Please fix the issues above and try again.")
        sys.exit(1)

    with open(patch_config_path, "r", encoding="utf-8") as f:
        patch_config = json.load(f)
        
    all_patch_list = patch_config.get("patch_list", [])
    if not all_patch_list:
        print("❌ No apps configured in patch-config.json")
        sys.exit(1)

    # Determine which apps to build
    if args.incremental:
        build_matrix = plan.get("build_matrix", [])
        if not build_matrix:
            print("\n🎉 Everything is up to date! No apps need rebuilding.")
            return
        patch_list = build_matrix
        print(f"\n⚡ Incremental mode: Building {len(patch_list)} updated app(s)...")
    else:
        patch_list = all_patch_list
        print(f"\n🚀 Starting local compilation for {len(patch_list)} apps...")

    # Create local logs dir
    logs_dir = root / "local_logs"
    logs_dir.mkdir(exist_ok=True)
    
    print(f"📁 Logs will be saved separately under: {logs_dir}/\n")
    
    success_count = 0
    failed_apps = []
    
    for index, item in enumerate(patch_list, 1):
        app_name = item["app_name"]
        source = item["source"]
        
        print(f"[{index:02d}/{len(patch_list):02d}] 🔨 Building {app_name} (patches: {source})... ", end="", flush=True)
        
        log_file = logs_dir / f"{app_name}_{source}.log"
        
        env = os.environ.copy()
        env["APP_NAME"] = app_name
        env["SOURCE"] = source
        env["ARCH"] = "arm64-v8a"
        
        with open(log_file, "w", encoding="utf-8") as lf:
            try:
                res = subprocess.run(
                    [sys.executable, "-m", "src"],
                    env=env,
                    stdout=lf,
                    stderr=subprocess.STDOUT,
                    text=True,
                    cwd=str(root)
                )
                
                if res.returncode == 0:
                    with open(log_file, "r", encoding="utf-8") as rlf:
                        log_content = rlf.read()
                    
                    if "All download sources failed" in log_content or "Failed to download APK" in log_content:
                        print("⚠️ SKIPPED (Download failed - see log)")
                        failed_apps.append(f"{app_name} (download failed)")
                    elif "Built 0 APK(s)" in log_content:
                        print("⚠️ SKIPPED (No APK built - see log)")
                        failed_apps.append(f"{app_name} (0 APKs)")
                    else:
                        apks = list(root.glob(f"*{app_name}*.apk"))
                        if apks:
                            apk_names = ", ".join([a.name for a in apks])
                            print(f"✅ SUCCESS! ({apk_names})")
                        else:
                            print("✅ SUCCESS!")
                        success_count += 1
                else:
                    print("❌ FAILED (Check log)")
                    failed_apps.append(f"{app_name} (compilation error)")
                    
            except Exception as e:
                lf.write(f"\nLocal runner exception:\n{e}\n")
                print(f"❌ ERROR: {e}")
                failed_apps.append(f"{app_name} (exception)")
                
    # Merge manifest and generate local release notes
    merge_script = root / "scripts" / "merge_manifest.py"
    gen_notes_script = root / "scripts" / "generate_release_notes.py"
    try:
        subprocess.run([sys.executable, str(merge_script)], cwd=str(root), capture_output=True)
        subprocess.run([sys.executable, str(gen_notes_script)], cwd=str(root), capture_output=True)
    except Exception:
        pass

    print("\n🏁 ============================================= 🏁")
    print(f"🏁 Local build finished! Success: {success_count}/{len(patch_list)}")
    if failed_apps:
        print(f"❌ Failed/Skipped apps: {failed_apps}")
        print(f"💡 Check the log files in {logs_dir}/ for detailed tracebacks.")
    else:
        print("🎉 Congratulations! All requested builds compiled successfully!")
    print(f"📄 Local release notes updated: {root / 'release_notes.md'}")
    print("🏁 ============================================= 🏁")

if __name__ == "__main__":
    main()
