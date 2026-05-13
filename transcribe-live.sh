#!/bin/bash
# Live microphone transcription with auto language detection (Mandarin + English)
# Usage: ./transcribe-live.sh

cd "$(dirname "$0")/whisper.cpp"

exec ./build/bin/whisper-stream \
  -m models/ggml-large-v3-turbo.bin \
  -t 8 \
  --step 500 \
  --length 5000 \
  -la auto
