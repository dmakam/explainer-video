#!/usr/bin/env bash
# Lighter copies for embedding on a web page: 720p MP4 + WebM, a poster image, and an embed snippet.
# usage: web.sh path/to/video.json [poster-time-seconds]
set -euo pipefail
D="$(cd "$(dirname "$1")" && pwd)"; B="$D/build"
NAME="$(python3 -c "import json,sys;print(json.load(open(sys.argv[1])).get('output','explainer'))" "$1")"
SRC="$D/$NAME.mp4"; PT="${2:-3}"
ffmpeg -y -v error -i "$SRC" -vf scale=1280:720:flags=lanczos -c:v libx264 -preset slow -crf 27 -tune animation -pix_fmt yuv420p -c:a aac -b:a 96k -movflags +faststart "$D/$NAME-720p.mp4"
ffmpeg -y -v error -i "$SRC" -vf scale=1280:720:flags=lanczos -c:v libvpx-vp9 -b:v 0 -crf 44 -row-mt 1 -deadline good -cpu-used 3 -c:a libopus -b:a 80k "$D/$NAME-720p.webm"
rm -f "$B/qa"/t_*.jpg; python3 "$(dirname "$0")/shots.py" "$1" "$PT" --clean >/dev/null
python3 - "$B/qa" "$D/$NAME-poster.jpg" <<'PY'
import glob,sys; from PIL import Image
f=sorted(glob.glob(sys.argv[1]+"/t_*.jpg"))[-1]; Image.open(f).convert("RGB").resize((1280,720),Image.LANCZOS).save(sys.argv[2],quality=84,optimize=True,progressive=True)
PY
cat > "$D/$NAME-embed.html" <<HTML
<!-- Only the poster loads with the page; the video downloads when someone presses play. -->
<video controls playsinline preload="none" width="1280" height="720" poster="$NAME-poster.jpg"
  style="width:100%;height:auto;aspect-ratio:16/9;border-radius:16px">
  <source src="$NAME-720p.webm" type="video/webm">
  <source src="$NAME-720p.mp4" type="video/mp4">
</video>
HTML
ls -la "$D/$NAME"-720p.* "$D/$NAME-poster.jpg" "$D/$NAME-embed.html"
