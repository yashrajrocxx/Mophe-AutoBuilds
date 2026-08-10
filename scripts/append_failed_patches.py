import json
import os

def main():
    failed_patches_file = './release-apks/failed_patches.json'
    release_notes_file = 'release_notes.md'

    if not os.path.exists(failed_patches_file):
        return

    try:
        with open(failed_patches_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
            
        if not data:
            return
            
        with open(release_notes_file, 'a', encoding='utf-8') as rn:
            rn.write('\n## ⚠️ Known Issues / Failed Patches\n')
            for app, patches in data.items():
                if patches:
                    rn.write(f"- **{app}**: Failed to apply `{len(patches)}` patches ({ ', '.join(patches) })\n")
    except Exception as e:
        print(f"Failed to append failed patches to release notes: {e}")

if __name__ == '__main__':
    main()
