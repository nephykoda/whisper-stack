#!/bin/bash
# One-line installer for Whisper Transcription Suite

set -e

echo "🎙️ Whisper Transcription Suite - Installer"
echo "=========================================="
echo ""

# Check macOS
if [[ "$OSTYPE" != "darwin"* ]]; then
    echo "❌ This installer is for macOS only"
    exit 1
fi

# Check Apple Silicon
if [[ ! $(uname -m) == "arm64" ]]; then
    echo "⚠️  Warning: Apple Silicon recommended (M1/M2/M3/M4)"
fi

# Install Homebrew dependencies
echo "📦 Installing dependencies..."
brew install ffmpeg cmake sdl2 python@3.10 2>/dev/null || true

# Clone whisper.cpp if not present
if [ ! -d "whisper.cpp" ]; then
    echo "📥 Cloning whisper.cpp..."
    git clone --depth 1 https://github.com/ggerganov/whisper.cpp.git
fi

# Download model
echo "📥 Downloading Whisper model (1.5GB)..."
cd whisper.cpp
bash ./models/download-ggml-model.sh large-v3-turbo

# Build
echo "🔨 Building whisper.cpp..."
cmake -B build
cmake --build build --config Release

# Build with SDL2 for streaming
echo "🎤 Building microphone support..."
cmake -B build -DWHISPER_SDL2=ON
cmake --build build --config Release --target whisper-stream

# Install Python dependencies
echo "🐍 Installing Python dependencies..."
cd ..
python3.10 -m pip install mcp flask sounddevice numpy --quiet
cd whisper-mcp-server
python3.10 -m pip install -e . --quiet
cd ..

# Make scripts executable
chmod +x *.sh

echo ""
echo "✅ Installation complete!"
echo ""
echo "Quick start:"
echo "  ./record-and-transcribe.sh 30    # Record and transcribe"
echo "  ./transcribe-file.sh file.mp3   # Transcribe existing file"
echo ""
echo "For HTTP API:"
echo "  ./start-api-server.sh"
echo ""
echo "For Claude Desktop:"
echo "  Add whisper-mcp-server to your claude_desktop_config.json"
echo "  See README.md for details"
