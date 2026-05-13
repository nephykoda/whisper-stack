#!/bin/bash
# Start the Whisper HTTP API server
# Other computers on your network can then use this service

# Get script directory (works from anywhere)
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR/whisper-api"

echo "🎙️ whisper-stack API Server..."
echo ""
echo "Once started, other devices can access:"
echo "  - http://$(ipconfig getifaddr en0 2>/dev/null || echo "YOUR_IP"):5001"
echo ""

python3.10 server.py
