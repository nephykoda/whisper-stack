#!/bin/bash
# Simple audio recorder for macOS
# Usage: ./record.sh [duration_seconds]

DURATION=${1:-30}
OUTPUT_DIR="$HOME/Desktop/whisper-recordings"
mkdir -p "$OUTPUT_DIR"

TIMESTAMP=$(date +%Y%m%d-%H%M%S)
OUTPUT="$OUTPUT_DIR/recording-$TIMESTAMP.wav"

echo "🎙️  Recording for $DURATION seconds..."
echo "📁 Output: $OUTPUT"
echo ""
echo "▶️  Speak now!"
echo ""

# Record using ffmpeg
ffmpeg -f avfoundation -i ":0" -t "$DURATION" -ar 16000 -ac 1 -y "$OUTPUT" 2>&1 | grep -E "(size|Duration|Permission)" || true

echo ""
echo "✅ Recording saved to: $OUTPUT"
echo ""
echo "To transcribe, run:"
echo "  ./transcribe-file.sh \"$OUTPUT\""
