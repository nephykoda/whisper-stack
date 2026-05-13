#!/bin/bash
# Record and immediately transcribe - all in one command
# Usage: ./record-and-transcribe.sh [duration_seconds]

DURATION=${1:-60}
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
OUTPUT_DIR="$HOME/Desktop/whisper-recordings"
mkdir -p "$OUTPUT_DIR"

TIMESTAMP=$(date +%Y%m%d-%H%M%S)
OUTPUT="$OUTPUT_DIR/recording-$TIMESTAMP.wav"

echo "🎙️  Recording for $DURATION seconds..."
echo "▶️  Speak now!"
echo ""

# Record
ffmpeg -f avfoundation -i ":0" -t "$DURATION" -ar 16000 -ac 1 -y "$OUTPUT" 2>&1 | grep -E "size|Duration" || true

echo ""
echo "✅ Recording complete! Transcribing..."
echo ""

# Transcribe
cd "$SCRIPT_DIR/whisper.cpp"
./build/bin/whisper-cli \
  -m models/ggml-large-v3-turbo.bin \
  -f "$OUTPUT" \
  -l auto \
  --word-thold 0.01 \
  -otxt \
  -ojf \
  -owts \
  -of "../output/latest" 2>&1 | grep -E "\[.*\]|transcri|language"

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📝 TRANSCRIPT:"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
cat "$SCRIPT_DIR/output/latest.txt"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "💾 Full details saved to: $SCRIPT_DIR/output/latest.json"
echo "🎵 Original audio: $OUTPUT"
