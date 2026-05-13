# whisper-stack

> **Private, offline speech-to-text for agents and automation**
> Multilingual transcription with CLI, HTTP API, and MCP integration

## Features

- 🌐 **Multilingual** — Auto-detects mixed English/Chinese (100+ languages)
- 🔒 **100% private** — Everything runs locally, no API keys needed
- 🚀 **Fast** — Optimized for Apple Silicon (M1/M2/M3/M4)
- 🤖 **Agent-ready** — Structured JSON outputs for LLM workflows
- 📝 **Multi-format** — Export as TXT, SRT, VTT, or JSON

## Quick Start

```bash
# Clone and install (downloads 1.5GB model)
git clone https://github.com/nephykoda/whisper-stack.git
cd whisper-stack
bash scripts/install.sh

# Record and transcribe
./record-and-transcribe.sh 60

# Transcribe existing file
./transcribe-with-subs.sh meeting.mp3

# Start HTTP API
./start-api-server.sh
```

> **Note**: First install downloads Whisper model (~1.5GB). Everything runs offline after that.

## Usage

| Command | Purpose |
|---------|---------|
| `./record-and-transcribe.sh 60` | Record 60s, get transcript immediately |
| `./transcribe-with-subs.sh file.mp3` | Transcribe + export SRT/VTT subtitles |
| `./start-api-server.sh` | Start HTTP API on port 5001 |
| `python3.10 hotkey_recorder.py` | Global hotkey dictation (Cmd+Option+Space) |

## Claude Desktop Integration

Add to `~/Library/Application Support/Claude/claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "whisper": {
      "command": "python3.10",
      "args": ["-m", "whisper_local_mcp.server"],
      "cwd": "/path/to/whisper-stack/whisper-mcp-server"
    }
  }
}
```

## API Endpoints

```
POST /v1/transcribe   — Transcribe audio, returns JSON with transcript + metrics
GET  /v1/health       — Health check
GET  /v1/capabilities — Discover features
```

## Requirements

- macOS with Apple Silicon (M1/M2/M3/M4)
- Homebrew
- Python 3.10+
- ~2GB disk space (for model + build)

## What Gets Installed

| Component | Size | Purpose |
|-----------|------|---------|
| whisper.cpp engine | ~500MB | Core transcription |
| large-v3-turbo model | ~1.5GB | Multilingual accuracy |
| Build artifacts | ~100MB | Compiled binaries |

## License

MIT
