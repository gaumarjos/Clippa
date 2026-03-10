import requests
import json
import sys
import os

# Load JSON from file
json_file = 'source_jsons/FLEX_MA_videos.json'  # Change this to your JSON filename

if not os.path.exists(json_file):
    print(f"❌ Error: File '{json_file}' not found!")
    print(f"Please create a file named '{json_file}' with your video data.")
    sys.exit(1)

print(f"📂 Loading video data from {json_file}...")
with open(json_file, 'r', encoding='utf-8') as f:
    data = json.load(f)

# Create a session to maintain cookies
session = requests.Session()

manifests = []

for video in data['data']:
    title = video['title']
    video_url = video['videoURL']
    id_video = video['idVideo']

    print(f"Processing: {title}")

    try:
        # Step 1: Load the embed page to establish session
        print(f"  Loading embed page...")
        embed_response = session.get(video_url)

        if embed_response.status_code != 200:
            print(f"  ❌ Failed to load embed page: {embed_response.status_code}")
            continue

        # Step 2: Call reviewVideo to get manifest
        print(f"  Fetching manifest...")
        review_response = session.post(
            'https://mip.fe.medialivesystem.com/Embed/reviewVideo',
            data={'step': '2'}
        )

        if review_response.status_code != 200:
            print(f"  ❌ Failed to get manifest: {review_response.status_code}")
            continue

        # Parse the response
        video_data = review_response.json()

        # Extract manifest URLs
        if 'formatiVideo' in video_data and len(video_data['formatiVideo']) > 0:
            # Type 3 = HLS (.m3u8), Type 4 = DASH (.mpd)
            for formato in video_data['formatiVideo']:
                if formato['Type'] == 4:  # MPD format (good for ffmpeg)
                    manifest_url = formato['Url']
                    manifests.append({
                        'title': title,
                        'idVideo': id_video,
                        'manifest': manifest_url
                    })
                    print(f"  ✅ Manifest: {manifest_url}")
                    break
        else:
            print(f"  ❌ No manifest found in response")

    except Exception as e:
        print(f"  ❌ Error: {str(e)}")

# Save all manifests to a file
print(f"\n📝 Saving {len(manifests)} manifests to file...")
with open('manifests.json', 'w', encoding='utf-8') as f:
    json.dump(manifests, f, indent=2, ensure_ascii=False)

print("\n✅ Done! Manifests saved to manifests.json")

# Print ffmpeg commands
print("\n🎬 FFmpeg download commands:")
print("-" * 80)
for item in manifests:
    safe_title = "".join(c for c in item['title'] if c.isalnum() or c in (' ', '-', '_')).strip()
    print(f'ffmpeg -i "{item["manifest"]}" -c copy "{safe_title}.mp4"')
