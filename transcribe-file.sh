#!/bin/bash
# Transcribe an audio file with auto language detection (Mandarin + English)
# Usage: ./transcribe-file.sh /path/to/audio.mp3

if [ -z "$1" ]; then
  echo "Usage: $0 <audio-file>"
  echo "Supported formats: mp3, wav, m4a, ogg, opus, mov, mp4"
  exit 1
fi

INPUT="$1"
cd "$(dirname "$0")/whisper.cpp"

# Convert to 16kHz WAV if needed
TEMP_WAV=$(mktemp -t whisper-XXXXXX.wav)
ffmpeg -i "$INPUT" -ar 16000 -ac 1 -c:a pcm_s16le "$TEMP_WAV" -y 2>/dev/null

# Transcribe
./build/bin/whisper-cli \
  -m models/ggml-large-v3-turbo.bin \
  -f "$TEMP_WAV" \
  -la auto \
  -otxt

# Cleanup
rm -f "$TEMP_WAV"
