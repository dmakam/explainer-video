#!/usr/bin/env bash
# One-time setup: Python packages, the Kokoro voice model, and fonts.
# Everything is cached in $EXPLAINER_CACHE (default ~/.cache/explainer-video).
set -euo pipefail
CACHE="${EXPLAINER_CACHE:-$HOME/.cache/explainer-video}"
mkdir -p "$CACHE/fonts"
PIP="pip install -q"; python3 -m pip --version >/dev/null 2>&1 && PIP="python3 -m pip install -q"
$PIP kokoro-onnx soundfile playwright pillow numpy 2>/dev/null || $PIP --break-system-packages kokoro-onnx soundfile playwright pillow numpy
python3 -c "import playwright" && (python3 -m playwright install chromium >/dev/null 2>&1 || echo "note: using an existing Chromium")
command -v ffmpeg >/dev/null || { echo "ffmpeg is required (apt install ffmpeg / brew install ffmpeg)"; exit 1; }
REL=https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0
[ -s "$CACHE/kokoro.onnx" ] || curl -sSL -o "$CACHE/kokoro.onnx" "$REL/kokoro-v1.0.int8.onnx"
[ -s "$CACHE/voices.bin" ]  || curl -sSL -o "$CACHE/voices.bin"  "$REL/voices-v1.0.bin"
cd "$CACHE/fonts"
if [ ! -s poppins-latin-600-normal.woff2 ]; then
  npm pack -s @fontsource/poppins >/dev/null && tar xzf fontsource-poppins-*.tgz
  cp package/files/poppins-latin-{400,500,600}-normal.woff2 . && rm -rf package fontsource-poppins-*.tgz
fi
if [ ! -s material-icons.woff2 ]; then
  npm pack -s material-icons >/dev/null && tar xzf material-icons-*.tgz
  cp package/iconfont/material-icons.woff2 . && rm -rf package material-icons-*.tgz
fi
echo "Setup complete. Cache: $CACHE"
