#!/bin/bash
# Transcribe with multiple output formats
# Generates: .txt, .srt (subtitles), .vtt (web), .json (full)

if [ -z "$1" ]; then
  echo "Usage: $0 <audio-file> [language]"
  echo ""
  echo "Output formats generated:"
  echo "  - .txt     - Plain text transcript"
  echo "  - .srt     - SubRip subtitles (for video players)"
  echo "  - .vtt     - WebVTT subtitles (for web)"
  echo "  - .json    - Full JSON with all details"
  exit 1
fi

INPUT="$1"
LANGUAGE="${2:-auto}"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

# Get filename without extension
BASENAME=$(basename "$INPUT")
FILENAME="${BASENAME%.*}"

echo "🎙️ Transcribing: $INPUT"
echo "📝 Language: $LANGUAGE"
echo ""

# Convert to WAV
TEMP_WAV=$(mktemp -t whisper-XXXXXX.wav)
ffmpeg -i "$INPUT" -ar 16000 -ac 1 -c:a pcm_s16le "$TEMP_WAV" -y 2>/dev/null

# Transcribe with all formats
cd "$SCRIPT_DIR/whisper.cpp"
./build/bin/whisper-cli \
  -m models/ggml-large-v3-turbo.bin \
  -f "$TEMP_WAV" \
  -l "$LANGUAGE" \
  --word-thold 0.01 \
  -otxt \
  -osrt \
  -ovtt \
  -ojf \
  -of "../output/$FILENAME"

# Cleanup
rm -f "$TEMP_WAV"

echo ""
echo "✅ Done! Output files in output/:"
echo "   - $FILENAME.txt"
echo "   - $FILENAME.srt"
echo "   - $FILENAME.vtt"
echo "   - $FILENAME.json"
