#!/usr/bin/env python3
"""Merge per-build records into the final manifest.json before uploading.

Inputs:
  - new_manifest.json      (planning-time manifest, has all entries with old apk
                            filenames as fallback for carry-overs)
  - patch_changelogs.json  (extracted changelogs for updated patch sources)
  - build_records/*.json   (one record per built APK, written by record_build.py)

Output:
  - manifest.json          (final manifest to attach to the release)
"""
import json
import sys
import datetime
from pathlib import Path

if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass


def main() -> int:
    new_manifest_path = Path("new_manifest.json")
    if new_manifest_path.exists():
        with new_manifest_path.open("r", encoding="utf-8") as f:
            manifest = json.load(f)
    elif Path("manifest.json").exists():
        with open("manifest.json", "r", encoding="utf-8") as f:
            manifest = json.load(f)
    else:
        manifest = {"entries": {}}

    manifest["updated_at"] = datetime.datetime.now(datetime.timezone.utc).isoformat()
    entries = manifest.setdefault("entries", {})

    # One-off request builds (apps built for a requester but not kept in the
    # catalog) stay downloadable in the release, but must not show up in the
    # store, the README or the Obtainium bundle. patch-config.json is the list
    # of published apps, so records for anything else are skipped.
    catalog_apps = None
    catalog_path = Path("patch-config.json")
    if catalog_path.exists():
        try:
            with catalog_path.open("r", encoding="utf-8") as f:
                catalog_data = json.load(f)
            catalog_apps = {
                str(item.get("app_name") or "").strip().lower()
                for item in catalog_data.get("patch_list", [])
                if isinstance(item, dict)
            }
        except Exception as e:
            print(f"[WARN] could not read patch-config.json ({e}); merging every record")

    # Embed patch changelogs if available
    patch_changelogs_path = Path("patch_changelogs.json")
    if patch_changelogs_path.exists():
        try:
            with patch_changelogs_path.open("r", encoding="utf-8") as f:
                changelogs_data = json.load(f)
            if changelogs_data:
                manifest["patch_changelogs"] = changelogs_data
        except Exception as e:
            print(f"[WARN] Warning reading patch_changelogs.json: {e}")

    rec_dir = Path("build_records")
    if rec_dir.exists():
        for rec_file in sorted(rec_dir.rglob("*.json")):
            try:
                with rec_file.open("r", encoding="utf-8") as f:
                    rec = json.load(f)
            except Exception as e:
                print(f"  skip bad record {rec_file}: {e}")
                continue
            
            if isinstance(rec, list):
                # This is likely a build_report file, skip it for manifest
                continue
            if catalog_apps is not None:
                rec_app = str(rec.get("app_name") or "").strip().lower()
                if rec_app and rec_app not in catalog_apps:
                    print(f"  skip {rec_file}: '{rec_app}' is not in the build catalog (one-off request build)")
                    continue
            key = rec.get("key")
            apk = rec.get("apk", "")
            resolved_version = (rec.get("resolved_version") or "").strip()
            if not key:
                continue

            # If this record is universal (e.g. via fallback or config), remove any superseded arm64-v8a entry
            if rec.get("arch") == "universal":
                arm_key = f"{rec.get('app_name')}|{rec.get('source')}|arm64-v8a"
                if arm_key in entries and arm_key != key:
                    print(f"  removing superseded entry {arm_key} in favor of universal")
                    del entries[arm_key]

            entry = entries.get(key)
            if not entry:
                entry = {
                    "app_name": rec.get("app_name", ""),
                    "source": rec.get("source", ""),
                    "arch": rec.get("arch", "universal"),
                    "config_version": "",
                    "source_sig": "",
                    "apk": "",
                    "built_version": "",
                }
                entries[key] = entry
            if apk:
                entry["apk"] = apk
            if resolved_version:
                entry["built_version"] = resolved_version
            if rec.get("package"):
                entry["package"] = rec["package"]
            if rec.get("version_code"):
                entry["version_code"] = rec["version_code"]
            if rec.get("built_at"):
                entry["built_at"] = rec.get("built_at")
            else:
                entry["built_at"] = datetime.datetime.now(datetime.timezone.utc).isoformat() + "Z"
                
            pending_sig = entry.get("pending_source_sig", "")
            if pending_sig:
                entry["source_sig"] = pending_sig
                del entry["pending_source_sig"]
            print(f"  merged {key} -> apk={apk!r} built_version={resolved_version!r}")

    for entry in entries.values():
        entry.pop("pending_source_sig", None)

    with open("manifest.json", "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)
    print(f"Wrote manifest.json with {len(entries)} entries")

    # Synchronize arch-config.json if any app fell back to universal
    arch_config_path = Path("arch-config.json")
    if arch_config_path.exists() and rec_dir.exists():
        try:
            with arch_config_path.open("r", encoding="utf-8") as f:
                ac_data = json.load(f)
            updated_ac = False
            for rec_file in sorted(rec_dir.rglob("*.json")):
                try:
                    with rec_file.open("r", encoding="utf-8") as f:
                        rdata = json.load(f)
                    if isinstance(rdata, dict) and rdata.get("arch") == "universal":
                        rapp = rdata.get("app_name")
                        rsrc = rdata.get("source")
                        for item in ac_data:
                            if item.get("app_name") == rapp and item.get("source") == rsrc:
                                if item.get("arches") != ["universal"]:
                                    print(f"  updating arch-config.json for {rapp} ({rsrc}) -> ['universal']")
                                    item["arches"] = ["universal"]
                                    updated_ac = True
                except Exception:
                    continue
            if updated_ac:
                with arch_config_path.open("w", encoding="utf-8", newline="\n") as f:
                    json.dump(ac_data, f, indent=2)
                print("[OK] Synchronized arch-config.json with universal build fallback")
        except Exception as e:
            print(f"[WARN] Failed to synchronize arch-config.json: {e}")
    
    # Also merge build reports
    all_reports = []
    if rec_dir.exists():
        for rec_file in sorted(rec_dir.rglob("build_report_*.json")):
            try:
                with rec_file.open("r", encoding="utf-8") as f:
                    data = json.load(f)
                    if isinstance(data, list):
                        all_reports.extend(data)
            except Exception as e:
                print(f"  skip bad build report {rec_file}: {e}")
                
    if all_reports and catalog_apps is not None:
        filtered_reports = []
        for report in all_reports:
            report_app = str(report.get("app") or "").strip().lower()
            if report_app and report_app not in catalog_apps:
                print(f"  skip build report for '{report_app}' (one-off request build)")
                continue
            filtered_reports.append(report)
        all_reports = filtered_reports

    if all_reports:
        with open("build_report.json", "w", encoding="utf-8") as f:
            json.dump(all_reports, f, indent=2)
        print(f"Wrote build_report.json with {len(all_reports)} build reports")
        
    return 0


if __name__ == "__main__":
    sys.exit(main())
