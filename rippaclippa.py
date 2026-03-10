#!/usr/bin/env python3

import json
import subprocess
import os
import re
import sys

# Check if manifests.json exists
if not os.path.exists('manifests.json'):
    print("❌ Error: manifests.json not found!")
    sys.exit(1)

# Create output directory
os.makedirs('downloaded_videos', exist_ok=True)

# Load manifests
with open('manifests.json', 'r', encoding='utf-8') as f:
    manifests = json.load(f)

print(f"Found {len(manifests)} videos to download.\n")

successful = 0
failed = 0
skipped = 0

for i, item in enumerate(manifests, 1):
    title = item['title']
    manifest = item['manifest']

    # Sanitize filename (remove invalid characters)
    safe_title = re.sub(r'[<>:"/\\|?*]', '_', title)
    filepath = f"downloaded_videos/{safe_title}.mp4"

    # Check if already exists
    if os.path.exists(filepath):
        print(f"⏭️  [{i}/{len(manifests)}] Skipping (exists): {title}")
        skipped += 1
        continue

    print(f"📥 [{i}/{len(manifests)}] Downloading: {title}")

    # Run ffmpeg
    result = subprocess.run([
        'ffmpeg', '-i', manifest,
        '-map', '0:v:0',
        '-map', '0:a:0',
        '-map', '0:a:1',
        '-c', 'copy',
        filepath,
        '-loglevel', 'error'
    ])

    if result.returncode == 0:
        print(f"✅ Done\n")
        successful += 1
    else:
        print(f"❌ Failed\n")
        failed += 1

# Summary
print("=" * 60)
print("Download Summary:")
print(f"  ✅ Successful: {successful}")
print(f"  ❌ Failed: {failed}")
print(f"  ⏭️  Skipped: {skipped}")
print(f"  📊 Total: {len(manifests)}")
print("=" * 60)
