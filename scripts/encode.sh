#!/usr/bin/env bash
# Encode frames + narration into the main deliverable: 1080p MP4 with burned-in captions.
# usage: encode.sh path/to/video.json [output-name]
set -euo pipefail
D="$(cd "$(dirname "$1")" && pwd)"; B="$D/build"
NAME="${2:-$(python3 -c "import json,sys;print(json.load(open(sys.argv[1])).get('output','explainer'))" "$1")}"
ffmpeg -y -v error -framerate 30 -i "$B/frames/%05d.jpg" -i "$B/narration.wav" \
  -c:v libx264 -preset medium -crf 25 -tune animation -pix_fmt yuv420p \
  -c:a aac -b:a 160k -shortest -movflags +faststart "$D/$NAME.mp4"
ffprobe -v error -show_entries format=duration,size -of default=nw=1 "$D/$NAME.mp4"
echo "wrote $D/$NAME.mp4"
