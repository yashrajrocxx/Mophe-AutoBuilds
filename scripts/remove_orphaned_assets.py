import json
import subprocess
import sys

def main():
    try:
        with open('patch-config.json', 'r') as f:
            config = json.load(f)
        
        app_names = [item['app_name'] for item in config.get('patch_list', [])]
    except Exception as e:
        print(f"Error loading patch-config.json: {e}")
        sys.exit(1)

    print("Checking for orphaned assets on GitHub release 'latest'...")
    result = subprocess.run(
        ['gh', 'release', 'view', 'latest', '--json', 'assets', '--jq', '.assets[].name'], 
        capture_output=True, text=True
    )
    
    if result.returncode != 0:
        print(f"Could not fetch release assets or release doesn't exist: {result.stderr}")
        sys.exit(0)

    assets = [line.strip() for line in result.stdout.splitlines() if line.strip()]
    
    for asset in assets:
        if asset == 'manifest.json':
            continue
            
        # Check if asset belongs to an active app from our patch config
        # Asset names are typically formatted as {app_name}-{arch}-patch-v{version}.apk
        is_active = any(asset.startswith(f"{app_name}-") for app_name in app_names)
        
        if not is_active:
            print(f"🗑️ Deleting orphaned asset: {asset}")
            delete_res = subprocess.run(
                ['gh', 'release', 'delete-asset', 'latest', asset, '-y'],
                capture_output=True, text=True
            )
            if delete_res.returncode == 0:
                print(f"✅ Successfully deleted {asset}")
            else:
                print(f"❌ Failed to delete {asset}: {delete_res.stderr}")

if __name__ == "__main__":
    main()
