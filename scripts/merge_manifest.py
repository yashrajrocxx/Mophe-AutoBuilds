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
    if not new_manifest_path.exists():
        print("No new_manifest.json found; nothing to merge")
        return 0

    with new_manifest_path.open("r", encoding="utf-8") as f:
        manifest = json.load(f)

    manifest["updated_at"] = datetime.datetime.now(datetime.timezone.utc).isoformat()
    entries = manifest.setdefault("entries", {})

    # Embed patch changelogs if available
    patch_changelogs_path = Path("patch_changelogs.json")
    if patch_changelogs_path.exists():
        try:
            with patch_changelogs_path.open("r", encoding="utf-8") as f:
                changelogs_data = json.load(f)
            if changelogs_data:
                manifest["patch_changelogs"] = changelogs_data
        except Exception as e:
            print(f"⚠️ Warning reading patch_changelogs.json: {e}")

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
            key = rec.get("key")
            apk = rec.get("apk", "")
            resolved_version = (rec.get("resolved_version") or "").strip()
            if not key:
                continue
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
            if rec.get("built_at"):
                entry["built_at"] = rec.get("built_at")
                
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
                
    if all_reports:
        with open("build_report.json", "w", encoding="utf-8") as f:
            json.dump(all_reports, f, indent=2)
        print(f"Wrote build_report.json with {len(all_reports)} build reports")
        
    return 0


if __name__ == "__main__":
    sys.exit(main())
