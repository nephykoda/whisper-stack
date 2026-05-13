# Whisper Local MCP Server

Local MCP server for Claude Desktop that provides offline audio transcription using whisper.cpp.

## Features
- **100% free & private** - All processing happens on your Mac
- **Mixed language** - Auto-detects English ↔️ Mandarin code-switching
- **Verbatim mode** - Preserves stammers, pauses, fillers ("um", "ah")
- **MP3 support** - Transcribe any audio file via Claude Desktop

## Installation
```bash
# MCP server is already installed in development mode
# To reinstall if needed:
cd /Users/lungs/Developer/whisper-stack/whisper-mcp-server
python3.10 -m pip install -e .
```

## Usage in Claude Desktop
After restarting Claude Desktop, you'll have these tools:

### `transcribe_file`
Upload an audio file for transcription.
- Supports: MP3, WAV, M4A, OGG, etc.
- Auto-detects language (English + Chinese)
- Optional verbatim mode with timestamps

### `check_status`
Verify that whisper.cpp is properly installed.

## Configuration
Already added to `~/Library/Application Support/Claude/claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "whisper-local": {
      "command": "python3.10",
      "args": ["-m", "whisper_local_mcp.server"],
      "cwd": "/Users/lungs/Developer/whisper-stack/whisper-mcp-server"
    }
  }
}
```

## Testing
```bash
# Test the server directly
cd /Users/lungs/Developer/whisper-stack/whisper-mcp-server
python3.10 -m whisper_local_mcp.server
```

## Troubleshooting
- If Claude Desktop can't connect, check the Developer Console for errors
- Ensure whisper.cpp is built: `cd ../whisper.cpp && make`
- Verify model exists: `ls -lh ../whisper.cpp/models/ggml-large-v3-turbo.bin`
