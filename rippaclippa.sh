#!/bin/bash

# Array of manifest URLs
MPD_URLS=(
    #"https://westeurope.av.mk.io/streamingcdn-mkio/90a7112c-f7f9-4c95-9e16-7b3777fa3399/457fdeb825c34557b6bb82b7f38de6aa.ism/manifest(format=mpd-time-cmaf)"
    #"https://westeurope.av.mk.io/streamingcdn-mkio/4ea2745b-aa0f-4b75-a4a5-4e0dc05ed47a/07015a5445f74f41b2946167ab3a401d.ism/manifest(format=mpd-time-cmaf)"
    #"https://westeurope.av.mk.io/streamingcdn-mkio/2ce3557e-63e5-47ce-992d-631abcfcdabb/e8346c48347d46cd8d85eb5fd75e4697.ism/manifest(format=mpd-time-cmaf)"
    #"https://westeurope.av.mk.io/streamingcdn-mkio/82a900c9-2095-40cb-88f8-9736c91d7a5f/282a6b71c5254ae7b44af957dae84dc8.ism/manifest(format=mpd-time-cmaf)"
    #"https://westeurope.av.mk.io/streamingcdn-mkio/e38fcb1f-4a4b-4ff7-9391-ddb9f5c0d427/72436656e2b44e809cee9c3e46d1d084.ism/manifest(format=mpd-time-cmaf)"
    #"https://westeurope.av.mk.io/streamingcdn-mkio/0c6a27a7-5ae5-4884-9fea-6b25b3e96245/d95a6f42fe6045b89334b2cc622d3471.ism/manifest(format=mpd-time-cmaf)"
    #"https://westeurope.av.mk.io/streamingcdn-mkio/78076655-1851-4e19-ae3c-b534df3893fa/fb7523679d8a457ea739bca3f70ceb49.ism/manifest(format=mpd-time-cmaf)"
    "https://livesessionprod.westeurope.streaming.mediakind.com/25eef402-c7a3-419a-af92-f4a0d7ff786b/lesson_311_20260702_232920.ism/manifest(format=m3u8-cmaf)"
)

# Array of output filenames (must match the length of MPD_URLS)
OUTPUT_NAMES=(
    #"4.4"
    #"4.5"
    #"4.6"
    #"4.12"
    #"4.13"
    #"4.14"
    #"4.15"
    "OM_recording1"
)

# Check if arrays have the same length
if [ ${#MPD_URLS[@]} -ne ${#OUTPUT_NAMES[@]} ]; then
    echo "Error: The number of URLs (${#MPD_URLS[@]}) does not match the number of names (${#OUTPUT_NAMES[@]})"
    exit 1
fi

# Loop through all videos
total=${#MPD_URLS[@]}
for i in "${!MPD_URLS[@]}"; do
    url="${MPD_URLS[$i]}"
    name="${OUTPUT_NAMES[$i]}"
    current=$((i + 1))

    echo "================================================"
    echo "Downloading video $current/$total: $name.mp4"
    echo "================================================"

    ffmpeg \
      -i "$url" \
      -map 0:v:0 \
      -map 0:a:0 \
      -map 0:a:1 \
      -c copy \
      "${name}.mp4"

    if [ $? -eq 0 ]; then
        echo "✅ Successfully downloaded: ${name}.mp4"
    else
        echo "❌ Failed to download: ${name}.mp4"
    fi
    echo ""
done

echo "================================================"
echo "Download complete! Processed $total videos."
echo "================================================"
