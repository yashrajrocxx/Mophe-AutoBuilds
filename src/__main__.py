import json
import logging
import re
from sys import exit
from pathlib import Path
from os import getenv
import subprocess
from dotenv import load_dotenv

load_dotenv()

from src import (
    r2,
    utils,
    release,
    downloader
)

def _should_retry_with_older_version(output: str | None) -> bool:
    """Detect common patterns that indicate the chosen app version is not
    actually compatible with the selected patches (fingerprint mismatch, etc.)."""
    if not output:
        return False
    t = output.lower()
    return (
        "failed to match the fingerprint" in t
        or "patch.patchexception" in t
        or ("fingerprint" in t and "failed" in t)
        or "patching aborted" in t
    )

def _record_failed_patches(app_name: str, output: str):
    """Scan CLI output for failed patches and record them."""
    if not output:
        return
        
    failed_patches = []
    # Match lines like "FAILED: Disable email confirmation dialog" or "Failed to apply patch: ..."
    for line in output.splitlines():
        match = re.search(r'(?:FAILED:\s+|Failed to apply patch:\s*)(.+?)$', line, re.IGNORECASE)
        if match:
            patch_name = match.group(1).strip()
            # Avoid recording duplicates
            if patch_name not in failed_patches:
                failed_patches.append(patch_name)
    
    if failed_patches:
        import json
        out_path = Path("build_records/failed_patches.json")
        out_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Load existing
        data = {}
        if out_path.exists():
            try:
                with open(out_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
            except Exception:
                pass
                
        # Update and save
        data[app_name] = failed_patches
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
            

def run_build(app_name: str, source: str, arch: str = "universal", report: dict = None) -> str:
    """Build APK for specific architecture"""
    download_files, name = downloader.download_required(source)

    # Log downloaded files for debugging
    logging.info(f"📦 Downloaded {len(download_files)} files for {source}:")
    for file in download_files:
        logging.info(f"  - {file.name} ({file.stat().st_size} bytes)")

    # DETECT SOURCE TYPE BASED ON DOWNLOADED FILES
    is_morphe = False
    is_revanced = False

    # Check file contents to determine source type
    for file in download_files:
        if "morphe-cli" in file.name.lower():
            is_morphe = True
            break
        elif "revanced-cli" in file.name.lower():
            is_revanced = True
            break

    # If not detected by CLI name, check patch file extension
    if not is_morphe and not is_revanced:
        for file in download_files:
            if file.suffix == ".mpp":
                is_morphe = True
                break
            elif file.suffix in [".rvp", ".jar"] and "patches" in file.name.lower():
                is_revanced = True
                break

    # If still not detected, fallback to source name
    if not is_morphe and not is_revanced:
        is_morphe = "morphe" in source.lower() or "custom" in source.lower()
        is_revanced = not is_morphe  # Default to ReVanced if not Morphe

    logging.info(f"🔍 Detected: {'Morphe' if is_morphe else 'ReVanced'} source type")

    # FIND FILES BASED ON DETECTED TYPE
    if is_morphe:
        # Find Morphe files - prefer non-dev version
        cli = utils.find_file(download_files, contains="morphe-cli", suffix=".jar", exclude=["dev"])
        if not cli:
            # Fallback to any Morphe CLI
            cli = utils.find_file(download_files, contains="morphe", suffix=".jar")
        
        if not cli:
            cli = utils.find_file(download_files, suffix=".jar")
        patches = utils.find_file(download_files, contains="patches", suffix=".mpp")
        if not patches:
            # Fallback to any .mpp file
            patches = utils.find_file(download_files, suffix=".mpp")
    else:
        # Find ReVanced files
        cli = utils.find_file(download_files, contains="revanced-cli", suffix=".jar")
        patches = utils.find_file(download_files, contains="patches", suffix=".rvp")
        
        if not patches:
            # Try .jar extension for patches
            patches = utils.find_file(download_files, contains="patches", suffix=".jar")

    # Validate tools
    if not cli:
        logging.error(f"❌ CLI not found for source: {source}")
        logging.error(f"Available files: {[f.name for f in download_files]}")
        return None
    if not patches:
        logging.error(f"❌ Patches not found for source: {source}")
        logging.error(f"Available files: {[f.name for f in download_files]}")
        return None

    logging.info(f"✅ Using CLI: {cli.name}")
    logging.info(f"✅ Using patches: {patches.name}")

    download_methods = [
        downloader.download_playstore,   # 1. Google Play (Canonical split fallback via gplaydl)
        downloader.download_apkmirror,   # 2. APKMirror (Fastest scraper, high availability of universal packages)
        downloader.download_uptodown,    # 3. Uptodown (Robust scraper alternative)
        downloader.download_apkpure,     # 4. APKPure
        downloader.download_aptoide,     # 5. Aptoide
        downloader.download_github,      # 6. GitHub releases
    ]

    # 1. Fetch package name
    package_name = None
    for platform in ["playstore", "apkmirror", "uptodown", "apkpure"]:
        config_path = Path("apps") / platform / f"{app_name}.json"
        if config_path.exists():
            with config_path.open() as f:
                package_name = json.load(f).get("package")
            if package_name:
                break
    
    # 2. Get supported versions from CLI
    supported_versions = utils.get_supported_versions(package_name, str(cli), str(patches)) if package_name else []
    if not supported_versions:
        # Fallback to a single attempt with latest
        supported_versions = [None]
        logging.warning("No supported versions found, will attempt to fetch latest.")

    exclude_patches = []
    include_patches = []

    patches_path = Path("patches") / f"{app_name}-{source}.txt"
    if patches_path.exists():
        with patches_path.open('r') as patches_file:
            for line in patches_file:
                line = line.strip()
                if line.startswith('-'):
                    exclude_patches.extend(["-d", line[1:].strip()])
                elif line.startswith('+'):
                    include_patches.extend(["-e", line[1:].strip()])

    # Start the grand loop!
    for attempt_idx, ver in enumerate(supported_versions):
        if ver:
            logging.info(f"Targeting version: {ver}")
        
        input_apk = None
        version = None
        
        # Source fallback loop
        dl_method_name = None
        for method in download_methods:
            try:
                input_apk, dl_ver, _ = method(app_name, str(cli), str(patches), arch, override_version=ver)
                if input_apk:
                    version = dl_ver
                    dl_method_name = method.__name__
                    break
            except Exception as e:
                logging.debug(f"{method.__name__} failed: {e}")
                continue
                
        if not input_apk or not version:
            logging.warning(f"Failed to download version {ver or 'latest'} from all sources.")
            if report is not None:
                report["error"] = f"Failed to download version {ver or 'latest'}"
            continue # Try next version

        # --- Normalize/merge input into .apk when needed ---
        if input_apk.suffix != ".apk":
            logging.warning("Input file is not .apk, using APKEditor to merge")
            apk_editor = downloader.download_apkeditor()

            merged_apk = input_apk.with_suffix(".apk")

            utils.run_process([
                "java", "-jar", apk_editor, "m",
                "-i", str(input_apk),
                "-o", str(merged_apk)
            ], silent=True)

            input_apk.unlink(missing_ok=True)

            if not merged_apk.exists():
                logging.error("Merged APK file not found")
                raise RuntimeError("Merged APK file not found")

            # Clean up filename: remove build number like (1575420) and -1575420.
            # Only strip 6+ digit build-number tokens so legitimate short version
            # segments (e.g. "app-2_0") are not mangled.
            clean_name = re.sub(r'\(\d+\)', '', merged_apk.name)  # Remove (1575420)
            clean_name = re.sub(r'-\d{6,}_', '_', clean_name)  # Remove -1575420_ -> _
            if clean_name != merged_apk.name:
                clean_apk = merged_apk.with_name(clean_name)
                merged_apk.rename(clean_apk)
                merged_apk = clean_apk

            input_apk = merged_apk
            logging.info(f"Merged APK file generated: {input_apk}")

        # --- ARCHITECTURE-SPECIFIC PROCESSING ---
        if arch != "universal":
            logging.info(f"Processing APK for {arch} architecture...")
            if arch == "arm64-v8a":
                utils.run_process([
                    "zip", "--delete", str(input_apk),
                    "lib/x86/*", "lib/x86_64/*", "lib/armeabi-v7a/*"
                ], silent=True, check=False)
            elif arch == "armeabi-v7a":
                utils.run_process([
                    "zip", "--delete", str(input_apk),
                    "lib/x86/*", "lib/x86_64/*", "lib/arm64-v8a/*"
                ], silent=True, check=False)
        else:
            utils.run_process([
                "zip", "--delete", str(input_apk),
                "lib/x86/*", "lib/x86_64/*"
            ], silent=True, check=False)

        # FIX: Repair corrupted APK (e.g. from Uptodown) ONLY when integrity check fails.
        # Previously this ran on every build and could silently alter healthy APKs.
        logging.info("Checking APK integrity...")
        try:
            integrity = subprocess.run(
                ["zip", "-T", str(input_apk)],
                check=False, capture_output=True, text=True,
            )
            if integrity.returncode != 0:
                logging.warning(f"APK integrity check failed; attempting repair: {integrity.stdout.strip()}")
                fixed_apk = Path(f"{app_name}-fixed-v{version}.apk")
                subprocess.run([
                    "zip", "-FF", str(input_apk), "--out", str(fixed_apk)
                ], check=False, capture_output=True)

                if fixed_apk.exists() and fixed_apk.stat().st_size > 0:
                    input_apk.unlink(missing_ok=True)
                    fixed_apk.rename(input_apk)
                    logging.info("APK fixed successfully")
                else:
                    logging.warning("Repair produced no usable file; keeping original APK")
            else:
                logging.info("APK integrity OK; no repair needed")
        except Exception as e:
            logging.warning(f"Could not check/fix APK: {e}")
            
        # Inject dynamic global patches based on download source
        # Note: In morphe-cli, -e stands for --enable (not exclude)
        dynamic_includes = []
        if dl_method_name:
            if "disable-play-store-updates" not in include_patches and "-e disable-play-store-updates" not in include_patches:
                dynamic_includes.extend(["-e", "disable-play-store-updates"])
            if dl_method_name != "download_playstore":
                if "change-installer-source" not in include_patches and "-e change-installer-source" not in include_patches:
                    dynamic_includes.extend(["-e", "change-installer-source"])
        
        current_include_patches = include_patches + dynamic_includes

        if report is not None:
            report["version"] = version
            report["dl_method"] = dl_method_name
            report["patches"] = current_include_patches
            
        if dynamic_includes:
            logging.info(f"💉 Dynamically injected global patches: {[p for p in dynamic_includes if p != '-e']}")

        # Include architecture in output filename
        output_apk = Path(f"{app_name}-{arch}-patch-v{version}.apk")

        try:
            # USE DIFFERENT COMMANDS BASED ON SOURCE TYPE
            if is_morphe:
                logging.info("🔧 Using Morphe patching system...")
                patch_error: subprocess.CalledProcessError | None = None
                try:
                    morphe_cmd = [
                        "java", "-jar", str(cli),
                        "patch", "--continue-on-error", "--patches", str(patches),
                        "--out", str(output_apk), str(input_apk),
                        *exclude_patches, *current_include_patches
                    ]
                    output = utils.run_process(morphe_cmd, capture=True, stream=True)
                    _record_failed_patches(app_name, output)
                except subprocess.CalledProcessError as e:
                    # Remember the original failure so the retry logic below can
                    # decide whether to fall back to an older version. We still
                    # try the alternative argument format as a best-effort.
                    patch_error = e
                    logging.info("Trying alternative Morphe command format...")
                    morphe_cmd = [
                        "java", "-jar", str(cli),
                        "--continue-on-error",
                        "--patches", str(patches),
                        "--input", str(input_apk),
                        "--output", str(output_apk)
                    ]
                    try:
                        output = utils.run_process(morphe_cmd, capture=True, stream=True)
                        _record_failed_patches(app_name, output)
                    except subprocess.CalledProcessError as e2:
                        raise e2 from e
                if patch_error is not None:
                    # Fallback path succeeded; clear the error so we don't retry.
                    patch_error = None
            else:
                logging.info("🔧 Using ReVanced patching system...")
                cli_name = Path(cli).name.lower()
                is_revanced_v6_or_newer = (
                    'revanced-cli-6' in cli_name or 'revanced-cli-7' in cli_name or 'revanced-cli-8' in cli_name
                )

                if is_revanced_v6_or_newer:
                    output = utils.run_process([
                        "java", "-jar", str(cli),
                        "patch", "-p", str(patches), "-b",
                        "--out", str(output_apk), str(input_apk),
                        *exclude_patches, *current_include_patches
                    ], capture=True, stream=True)
                    _record_failed_patches(app_name, output)
                else:
                    output = utils.run_process([
                        "java", "-jar", str(cli),
                        "-m", str(integrations),
                        "-b", str(patches),
                        "-a", str(input_apk),
                        "-o", str(output_apk),
                        *exclude_patches, *current_include_patches
                    ], capture=True, stream=True)
                    _record_failed_patches(app_name, output)

        except subprocess.CalledProcessError as e:
            # Remove temp input apk; we'll re-download if retrying.
            input_apk.unlink(missing_ok=True)
            output_apk.unlink(missing_ok=True)

            if attempt_idx < len(supported_versions) - 1 and _should_retry_with_older_version(getattr(e, "output", None)):
                continue
            raise

        # Patch succeeded -> cleanup input and sign.
        input_apk.unlink(missing_ok=True)

        signed_apk = Path(f"{app_name}-{arch}-{name}-v{version}.apk")

        apksigner = utils.find_apksigner()
        if not apksigner:
            raise RuntimeError("apksigner not found")

        try:
            utils.run_process([
                str(apksigner), "sign", "--verbose",
                "--ks", "keystore/public.jks",
                "--ks-pass", "pass:public",
                "--key-pass", "pass:public",
                "--ks-key-alias", "public",
                "--in", str(output_apk), "--out", str(signed_apk)
            ], capture=True, stream=True)
        except Exception as e:
            logging.warning(f"Standard signing failed: {e}")
            logging.info("Trying alternative signing method...")

            utils.run_process([
                str(apksigner), "sign", "--verbose",
                "--min-sdk-version", "21",
                "--ks", "keystore/public.jks",
                "--ks-pass", "pass:public",
                "--key-pass", "pass:public",
                "--ks-key-alias", "public",
                "--in", str(output_apk), "--out", str(signed_apk)
            ], capture=True, stream=True)

        output_apk.unlink(missing_ok=True)
        print(f"✅ APK built: {signed_apk.name}")
        return str(signed_apk)

    # If we got here, every candidate version failed.
    return None

def main():
    app_name = getenv("APP_NAME")
    source = getenv("SOURCE")

    if not app_name or not source:
        logging.error("APP_NAME and SOURCE environment variables must be set")
        exit(1)

    # Read arch-config.json
    arch_config_path = Path("arch-config.json")
    if arch_config_path.exists():
        with open(arch_config_path) as f:
            arch_config = json.load(f)
        
        # Find arches for this app
        arches = [(getenv("ARCH") or "universal").strip()]
        for config in arch_config:
            if not getenv("ARCH") and config["app_name"] == app_name and config["source"] == source:
                arches = config["arches"]
                break
        
        # Build for each architecture
        built_apks = []
        build_reports = []
        for arch in arches:
            logging.info(f"🔨 Building {app_name} for {arch} architecture...")
            report = {"app": app_name, "arch": arch, "source": source, "status": "failed", "version": None, "patches": []}
            apk_path = run_build(app_name, source, arch, report=report)
            if apk_path:
                built_apks.append(apk_path)
                report["status"] = "success"
                report["apk"] = Path(apk_path).name
            build_reports.append(report)
            if apk_path:
                print(f"✅ Built {arch} version: {Path(apk_path).name}")
        
        Path("build_records").mkdir(exist_ok=True)
        with open(f"build_records/build_report_{app_name}.json", "w") as f:
            json.dump(build_reports, f)
        
        # Summary
        print(f"\n🎯 Built {len(built_apks)} APK(s) for {app_name}:")
        for apk in built_apks:
            print(f"  📱 {Path(apk).name}")
        
    else:
        # Fallback to single universal build
        logging.warning("arch-config.json not found, building universal only")
        report = {"app": app_name, "arch": "universal", "source": source, "status": "failed", "version": None, "patches": []}
        apk_path = run_build(app_name, source, "universal", report=report)
        if apk_path:
            report["status"] = "success"
            report["apk"] = Path(apk_path).name
            print(f"🎯 Final APK path: {apk_path}")
            
        Path("build_records").mkdir(exist_ok=True)
        with open(f"build_records/build_report_{app_name}.json", "w") as f:
            json.dump([report], f)

if __name__ == "__main__":
    main()
