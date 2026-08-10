#!/bin/bash
#
# Downloads ONE recorded live session from its streaming URL.
#
# Usage:
#   ./rippalive.sh <streamingUrl> [output_name] [seconds]
#
# The URL is the "streamingUrl" field of a live session in the source JSON, e.g.
#   https://livesessionprod.westeurope.streaming.mediakind.com/<guid>/lesson_311_20260702_232920.ism/manifest(format=m3u8-cmaf)
# That one URL is enough: it is the HLS master playlist, and ffmpeg follows the
# video/audio child playlists and their segments on its own. ALWAYS QUOTE IT --
# it contains parentheses, which the shell would otherwise interpret.
#
# [output_name] defaults to "<date>_<idVideo>" read off the URL itself.
#
# [seconds] grabs only the first X seconds, handy to check a manifest works
# before committing to a 4h download. 0 (the default) means the whole video.
# Can also be given as the LIMIT_SECONDS environment variable.
#
# Output goes to downloaded_lives/ (override with OUTPUT_DIR=...).
#
# The video is stream-copied, but the audio is re-encoded from HE-AAC to AAC-LC,
# because a stream-copied HE-AAC track plays as silent in QuickTime and Finder.
# Set AUDIO_COPY=1 to stream-copy the audio too (faster, but likely silent).
#
# Notes on these manifests (vs the "clip" ones rippaclippa.sh handles):
#   - they carry ONE audio track, not two, so the hardcoded "-map 0:a:1" of
#     rippaclippa.sh aborts before downloading anything
#   - the audio stream comes FIRST, so mapping is done by type, not by index
#   - recordings run up to ~4 hours, hence the reconnect options
#

set -uo pipefail

OUTPUT_DIR="${OUTPUT_DIR:-downloaded_lives}"

if [ $# -eq 0 ] || [ "$1" = "-h" ] || [ "$1" = "--help" ]; then
    # Print the header comment block: everything after the shebang up to the
    # first non-comment line, with the leading "# " stripped.
    awk 'NR==1 { next } /^#/ { sub(/^# ?/, ""); print; next } { exit }' "$0"
    exit 0
fi

URL="$1"
OUTPUT_NAME="${2:-}"
LIMIT_SECONDS="${3:-${LIMIT_SECONDS:-0}}"

if [[ "$URL" != http://* && "$URL" != https://* ]]; then
    echo "Error: expected a streamingUrl starting with http(s)://, got: $URL"
    exit 1
fi

if ! [[ "$LIMIT_SECONDS" =~ ^[0-9]+$ ]]; then
    echo "Error: seconds must be a non-negative integer, got: $LIMIT_SECONDS"
    exit 1
fi

# --- output filename -------------------------------------------------------

if [ -n "$OUTPUT_NAME" ]; then
    name="${OUTPUT_NAME%.mp4}"
elif [[ "$URL" =~ lesson_([0-9]+)_([0-9]{8})_ ]]; then
    # ".../lesson_<idVideo>_<date>_<time>.ism/..." -> "<date>_<idVideo>"
    name="${BASH_REMATCH[2]}_${BASH_REMATCH[1]}"
else
    name="live_session"
fi

mkdir -p "$OUTPUT_DIR"
outfile="${OUTPUT_DIR}/${name}.mp4"

echo "================================================"
echo "Downloading: ${name}.mp4"
echo "================================================"
echo "   source: $URL"
echo "   output: $outfile"
if [ "$LIMIT_SECONDS" -gt 0 ]; then
    echo "   ⚠️  partial download: first ${LIMIT_SECONDS}s only"
fi

if [ -f "$outfile" ]; then
    echo "⏭  Already present, not overwriting: $outfile"
    exit 0
fi

# Probe the audio track count, purely informational. ffprobe lists each stream
# once per program plus once globally, so dedupe on the index.
n_audio=$(ffprobe -v error -select_streams a -show_entries stream=index \
    -of csv=p=0 "$URL" 2>/dev/null | sort -u | grep -c .)
echo "   audio tracks found: $n_audio"
echo ""

# Download to a temporary name so an interrupted run is never mistaken for a
# finished file by the skip check above.
tmpfile="${outfile}.part.mp4"

# 0 means no -t at all, i.e. the whole video.
limit_args=()
[ "$LIMIT_SECONDS" -gt 0 ] && limit_args=(-t "$LIMIT_SECONDS")

# The source audio is HE-AAC (AAC+/SBR). Stream-copying it into .mp4 yields a
# file that QuickTime and Finder preview play as SILENT, even though the track
# is there and is not empty. Re-encoding to plain AAC-LC fixes playback; it is
# audio-only so it costs little, and levels are unchanged. AUDIO_COPY=1 keeps
# the original stream untouched.
if [ "${AUDIO_COPY:-0}" = "1" ]; then
    audio_args=(-c:a copy)
else
    audio_args=(-c:a aac -b:a 160k)
fi

ffmpeg -hide_banner \
  -reconnect 1 \
  -reconnect_streamed 1 \
  -reconnect_on_network_error 1 \
  -reconnect_delay_max 30 \
  -rw_timeout 30000000 \
  -i "$URL" \
  -map 0:v:0 \
  -map '0:a?' \
  -c:v copy \
  "${audio_args[@]}" \
  -movflags +faststart \
  ${limit_args[@]+"${limit_args[@]}"} \
  -y "$tmpfile"
status=$?

echo ""
if [ $status -eq 0 ] && [ -s "$tmpfile" ]; then
    mv "$tmpfile" "$outfile"
    echo "✅ Successfully downloaded: $outfile"
    exit 0
else
    rm -f "$tmpfile"
    echo "❌ Failed to download: ${name}.mp4"
    exit 1
fi
