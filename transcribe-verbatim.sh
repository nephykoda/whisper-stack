#!/bin/bash
# Verbatim transcription with timestamps (preserves stammers, pauses, fillers)
# Usage: ./transcribe-verbatim.sh /path/to/audio.mp3

if [ -z "$1" ]; then
  echo "Usage: $0 <audio-file>"
  echo "Outputs: text, full JSON, word-level timestamps"
  exit 1
fi

INPUT="$1"
BASENAME=$(basename "$INPUT" | sed 's/\.[^.]*$//')
cd "$(dirname "$0")/whisper.cpp"

# Convert to 16kHz WAV
TEMP_WAV=$(mktemp -t whisper-XXXXXX.wav)
ffmpeg -i "$INPUT" -ar 16000 -ac 1 -c:a pcm_s16le "$TEMP_WAV" -y 2>/dev/null

echo "🎙️  Transcribing: $INPUT"
echo "---"

# Verbatim transcription with word timestamps
./build/bin/whisper-cli \
  -m models/ggml-large-v3-turbo.bin \
  -f "$TEMP_WAV" \
  -la auto \
  --word-thold 0.01 \
  -otxt \
  -ojf \
  -owts \
  -of "../output/$BASENAME"

# Cleanup
rm -f "$TEMP_WAV"

echo ""
echo "✅ Output files:"
echo "   - ../output/${BASENAME}.txt"
echo "   - ../output/${BASENAME}.json.full"
echo "   - ../output/${BASENAME}.words"
