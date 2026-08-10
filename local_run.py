#!/usr/bin/env python3
import os
import sys
import json
import subprocess
import shutil
from pathlib import Path

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
    # Let's check using our project helper logic
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
        # Check if an account is linked by running `gplaydl auth`
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



def main():
    root = Path(__file__).resolve().parent
    patch_config_path = root / "patch-config.json"
    
    if not patch_config_path.exists():
        print(f"❌ patch-config.json not found in {root}")
        sys.exit(1)
        
    if not check_prerequisites():
        print("❌ Prerequisites check failed. Please fix the issues above and try again.")
        sys.exit(1)

    with open(patch_config_path, "r", encoding="utf-8") as f:
        patch_config = json.load(f)
        
    patch_list = patch_config.get("patch_list", [])
    if not patch_list:
        print("❌ No apps configured in patch-config.json")
        sys.exit(1)
        
    # Create local logs dir
    logs_dir = root / "local_logs"
    logs_dir.mkdir(exist_ok=True)
    
    print(f"🚀 Starting local compilation for {len(patch_list)} apps...")
    print(f"📁 Logs will be saved separately under: {logs_dir}/\n")
    
    success_count = 0
    failed_apps = []
    
    for index, item in enumerate(patch_list, 1):
        app_name = item["app_name"]
        source = item["source"]
        
        print(f"[{index:02d}/{len(patch_list):02d}] 🔨 Building {app_name} (patches: {source})... ", end="", flush=True)
        
        log_file = logs_dir / f"{app_name}_{source}.log"
        
        # Prepare environment
        env = os.environ.copy()
        env["APP_NAME"] = app_name
        env["SOURCE"] = source
        # Force arm64 build for local run
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
                
                # Check outcome
                if res.returncode == 0:
                    # Let's inspect the log to see if it failed to download or skipped
                    with open(log_file, "r", encoding="utf-8") as rlf:
                        log_content = rlf.read()
                    
                    if "All download sources failed" in log_content or "Failed to download APK" in log_content:
                        print("⚠️ SKIPPED (Download failed - see log)")
                        failed_apps.append(f"{app_name} (download failed)")
                    elif "Built 0 APK(s)" in log_content:
                        print("⚠️ SKIPPED (No APK built - see log)")
                        failed_apps.append(f"{app_name} (0 APKs)")
                    else:
                        # Find the output APK name in log or directory
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
                
    print("\n🏁 ============================================= 🏁")
    print(f"🏁 Local build finished! Success: {success_count}/{len(patch_list)}")
    if failed_apps:
        print(f"❌ Failed/Skipped apps: {failed_apps}")
        print(f"💡 Check the log files in {logs_dir}/ for detailed tracebacks.")
    else:
        print("🎉 Congratulations! All builds compiled successfully!")
    print("🏁 ============================================= 🏁")

if __name__ == "__main__":
    main()
