#!/usr/bin/env python3
"""
Local MCP server for Whisper audio transcription.
Uses whisper.cpp binaries for offline, private transcription.
"""

import asyncio
import io
import json
import os
import subprocess
import sys
import tempfile
import wave
from pathlib import Path
from typing import Any

import sounddevice as sd
import numpy as np

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

# Paths
SCRIPT_DIR = Path(__file__).parent.parent.parent
WHISPER_CPP = SCRIPT_DIR / "whisper.cpp"
WHISPER_CLI = WHISPER_CPP / "build" / "bin" / "whisper-cli"
WHISPER_STREAM = WHISPER_CPP / "build" / "bin" / "whisper-stream"
MODEL = WHISPER_CPP / "models" / "ggml-large-v3-turbo.bin"

app = Server("whisper-local-mcp")


def record_audio(duration: int, sample_rate: int = 16000) -> bytes:
    """Record audio from microphone using ffmpeg (better macOS permissions)."""
    print(f"\n🎙️  Recording for {duration} seconds... (speak now)", file=sys.stderr)
    print(f"📝 Please speak clearly into your microphone", file=sys.stderr)

    # Use ffmpeg to record from macOS default audio input
    # This works better than sounddevice for subprocess contexts
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_file:
        temp_path = temp_file.name

    try:
        # Record using ffmpeg with macOS avfoundation
        result = subprocess.run(
            [
                "ffmpeg",
                "-f", "avfoundation",          # macOS audio input
                "-i", ":0",                     # Default audio input (no video)
                "-t", str(duration),            # Duration in seconds
                "-ar", str(sample_rate),        # Sample rate
                "-ac", "1",                     # Mono
                "-y",                           # Overwrite
                temp_path
            ],
            capture_output=True,
            timeout=duration + 10
        )

        if result.returncode != 0:
            error_msg = result.stderr.decode()
            # Check if it's a permissions issue
            if "Permission" in error_msg or "denied" in error_msg.lower():
                raise PermissionError(
                    "Microphone access denied. Please grant ffmpeg microphone permission:\n"
                    "System Settings → Privacy & Security → Microphone → Terminal (or Claude Desktop)"
                )
            raise RuntimeError(f"ffmpeg recording failed: {error_msg}")

        print(f"✅ Recording complete! Transcribing...", file=sys.stderr)

        # Read the recorded file
        with open(temp_path, "rb") as f:
            return f.read()

    finally:
        if os.path.exists(temp_path):
            os.unlink(temp_path)


def check_dependencies() -> dict[str, Any]:
    """Check if whisper.cpp is properly installed."""
    issues = []

    if not WHISPER_CLI.exists():
        issues.append(f"whisper-cli not found at {WHISPER_CLI}")
    if not MODEL.exists():
        issues.append(f"Model not found at {MODEL}")
    if not WHISPER_STREAM.exists():
        issues.append(f"whisper-stream not found (live recording unavailable)")

    return {
        "ready": len(issues) == 0,
        "whisper_cpp": str(WHISPER_CPP),
        "model": str(MODEL),
        "model_size_gb": MODEL.stat().st_size / (1024**3) if MODEL.exists() else None,
        "issues": issues,
    }


@app.list_tools()
async def list_tools() -> list[Tool]:
    """List available transcription tools."""
    status = check_dependencies()

    tools = [
        Tool(
            name="transcribe_file",
            description="Transcribe an audio file (MP3, WAV, M4A, etc.) to text. "
            "Supports mixed English/Chinese auto-detection. "
            "Preserves verbatim details including stammers and pauses.",
            inputSchema={
                "type": "object",
                "properties": {
                    "file_path": {
                        "type": "string",
                        "description": "Absolute path to the audio file",
                    },
                    "verbatim": {
                        "type": "boolean",
                        "description": "Include word-level timestamps and fillers (um, ah)",
                        "default": False,
                    },
                    "output_format": {
                        "type": "string",
                        "enum": ["text", "json", "both"],
                        "description": "Output format",
                        "default": "text",
                    },
                },
                "required": ["file_path"],
            },
        ),
        Tool(
            name="check_status",
            description="Check if the local Whisper installation is ready",
            inputSchema={
                "type": "object",
                "properties": {},
            },
        ),
    ]

    if status["ready"]:
        tools.append(
            Tool(
                name="record_and_transcribe",
                description="🎙️ Record directly from microphone and transcribe. "
                "Perfect for interview prep, voice notes, or practice sessions. "
                "Supports mixed English/Chinese with automatic language detection. "
                "Use this tool to speak and get immediate transcription with Claude.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "duration_seconds": {
                            "type": "number",
                            "description": "How long to record (5-300 seconds)",
                            "default": 30,
                            "minimum": 5,
                            "maximum": 300,
                        },
                        "verbatim": {
                            "type": "boolean",
                            "description": "Include word-level timestamps and fillers (um, ah, pauses)",
                            "default": True,
                        },
                    },
                    "required": [],
                },
            )
        )

    return tools


@app.call_tool()
async def call_tool(name: str, arguments: Any) -> list[TextContent]:
    """Handle tool calls."""

    if name == "check_status":
        status = check_dependencies()
        return [TextContent(
            type="text",
            text=json.dumps(status, indent=2)
        )]

    elif name == "transcribe_file":
        file_path = arguments.get("file_path")
        verbatim = arguments.get("verbatim", False)
        output_format = arguments.get("output_format", "text")

        if not file_path or not os.path.exists(file_path):
            return [TextContent(
                type="text",
                text=f"Error: File not found: {file_path}"
            )]

        # Convert audio to WAV
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_wav:
            temp_wav_path = temp_wav.name

        try:
            # Convert using ffmpeg
            convert_result = subprocess.run(
                ["ffmpeg", "-i", file_path, "-ar", "16000", "-ac", "1",
                 "-c:a", "pcm_s16le", temp_wav_path, "-y"],
                capture_output=True,
                timeout=60
            )

            if convert_result.returncode != 0:
                return [TextContent(
                    type="text",
                    text=f"FFmpeg conversion failed: {convert_result.stderr.decode()}"
                )]

            # Build whisper command
            cmd = [
                str(WHISPER_CLI),
                "-m", str(MODEL),
                "-f", temp_wav_path,
                "-la", "auto",  # Auto-detect language
                "--word-thold", "0.01",  # Low threshold for verbatim
            ]

            output_files = []
            with tempfile.TemporaryDirectory() as temp_dir:
                output_base = os.path.join(temp_dir, "output")

                # Add output format flags
                if output_format in ("text", "both"):
                    cmd.extend(["-otxt", "-of", output_base])
                    output_files.append(f"{output_base}.txt")
                if output_format in ("json", "both") or verbatim:
                    cmd.extend(["-ojf", "-of", output_base])
                    output_files.append(f"{output_base}.json.full")
                if verbatim:
                    cmd.extend(["-owts", "-of", output_base])
                    output_files.append(f"{output_base}.words")

                # Run transcription
                result = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    timeout=300  # 5 minutes max
                )

                # Read outputs
                outputs = {}
                for f in output_files:
                    if os.path.exists(f):
                        with open(f, "r") as f:
                            content = f.read()
                        if f.endswith(".txt"):
                            outputs["text"] = content
                        elif f.endswith(".json.full"):
                            outputs["json"] = json.loads(content)
                        elif f.endswith(".words"):
                            outputs["words"] = content

            response = {
                "success": result.returncode == 0,
                "file": os.path.basename(file_path),
            }

            if "text" in outputs:
                response["transcript"] = outputs["text"].strip()
            if "json" in outputs:
                response["details"] = outputs["json"]
            if "words" in outputs:
                response["word_timestamps"] = outputs["words"]

            if result.returncode != 0:
                response["error"] = result.stderr

            return [TextContent(
                type="text",
                text=json.dumps(response, indent=2, ensure_ascii=False)
            )]

        finally:
            if os.path.exists(temp_wav_path):
                os.unlink(temp_wav_path)

    elif name == "record_and_transcribe":
        duration = arguments.get("duration_seconds", 30)

        # macOS prevents subprocess microphone access
        # Provide instructions for manual recording workflow
        record_script = SCRIPT_DIR / "record.sh"

        return [TextContent(
            type="text",
            text=json.dumps({
                "workflow": "Due to macOS security, please use this two-step process:",
                "step_1": f"Run this command in a terminal to record:\n  cd {SCRIPT_DIR} && ./record.sh {duration}",
                "step_2": "Then come back here and use transcribe_file with the recorded file path",
                "example": f'The recording will be saved to ~/Desktop/whisper-recordings/',
                "note": "First time? Terminal will ask for microphone permission - click 'Allow'.",
            }, indent=2)
        )]

    return [TextContent(
        type="text",
        text=f"Unknown tool: {name}"
    )]


async def main():
    """Start the MCP server."""
    async with stdio_server() as (read_stream, write_stream):
        await app.run(
            read_stream,
            write_stream,
            app.create_initialization_options()
        )


if __name__ == "__main__":
    asyncio.run(main())
