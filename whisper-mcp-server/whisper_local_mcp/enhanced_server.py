#!/usr/bin/env python3
"""
Enhanced MCP server with structured outputs for LLM workflows.
Returns both verbatim and cleaned transcripts to save context tokens.
"""

import asyncio
import json
import os
import re
import subprocess
import tempfile
import sys
from pathlib import Path
from typing import Any

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

# Paths
SCRIPT_DIR = Path(__file__).parent.parent.parent
WHISPER_CPP = SCRIPT_DIR / "whisper.cpp"
WHISPER_CLI = WHISPER_CPP / "build" / "bin" / "whisper-cli"
MODEL = WHISPER_CPP / "models" / "ggml-large-v3-turbo.bin"

app = Server("whisper-local-mcp")


def clean_transcript(text: str) -> str:
    """Remove filler words and clean up transcript for LLM analysis."""
    # Remove common fillers
    fillers = [
        r'\bum\b', r'\buh\b', r'\bah\b',
        r'\blike\b', r'\byou know\b',
        r'\bsort of\b', r'\bkind of\b'
    ]
    cleaned = text
    for filler in fillers:
        cleaned = re.sub(filler, '', cleaned, flags=re.IGNORECASE)

    # Clean up extra whitespace and commas
    cleaned = re.sub(r'\s+', ' ', cleaned)
    cleaned = re.sub(r',\s*,', ',', cleaned)
    cleaned = re.sub(r'^\s*,\s*', '', cleaned, flags=re.MULTILINE)

    return cleaned.strip()


def count_filler_words(text: str) -> dict[str, int]:
    """Count filler words in transcript."""
    fillers = {
        "um": len(re.findall(r'\bum\b', text, re.IGNORECASE)),
        "uh": len(re.findall(r'\buh\b', text, re.IGNORECASE)),
        "ah": len(re.findall(r'\bah\b', text, re.IGNORECASE)),
        "like": len(re.findall(r'\blike\b', text, re.IGNORECASE)),
        "you know": len(re.findall(r'\byou know\b', text, re.IGNORECASE)),
    }
    return fillers


def analyze_speech_patterns(text: str) -> dict[str, Any]:
    """Analyze speech patterns for interview prep feedback."""
    words = text.split()
    sentences = [s.strip() for s in text.split('.') if s.strip()]

    return {
        "total_words": len(words),
        "total_sentences": len(sentences),
        "avg_words_per_sentence": len(words) / len(sentences) if sentences else 0,
        "longest_pause": "N/A",  # Would need timestamps
        "speaking_rate_wpm": 0,  # Would need duration
    }


@app.list_tools()
async def list_tools() -> list[Tool]:
    """List available transcription tools."""
    return [
        Tool(
            name="transcribe_file",
            description="Transcribe audio file with structured output for LLM analysis. "
            "Returns both verbatim (with fillers) and cleaned transcripts plus speech metrics.",
            inputSchema={
                "type": "object",
                "properties": {
                    "file_path": {
                        "type": "string",
                        "description": "Absolute path to audio file",
                    },
                    "language": {
                        "type": "string",
                        "enum": ["auto", "en", "zh", "es", "fr", "de", "ja"],
                        "description": "Language code (auto for mixed)",
                        "default": "auto",
                    },
                    "include_cleaned": {
                        "type": "boolean",
                        "description": "Include cleaned transcript (fillers removed)",
                        "default": True,
                    },
                    "include_metrics": {
                        "type": "boolean",
                        "description": "Include speech pattern analysis",
                        "default": True,
                    },
                },
                "required": ["file_path"],
            },
        ),
        Tool(
            name="get_recording_help",
            description="Get instructions for recording on macOS (due to security restrictions)",
            inputSchema={
                "type": "object",
                "properties": {
                    "duration": {
                        "type": "number",
                        "description": "Recording duration in seconds",
                        "default": 60,
                    },
                },
            },
        ),
    ]


@app.call_tool()
async def call_tool(name: str, arguments: Any) -> list[TextContent]:
    """Handle tool calls."""

    if name == "get_recording_help":
        duration = arguments.get("duration", 60)
        return [TextContent(
            type="text",
            text=json.dumps({
                "workflow": "Two-step process required for macOS security:",
                "step_1": f"Run in terminal: cd {SCRIPT_DIR} && ./record-and-transcribe.sh {duration}",
                "step_2": "Use transcribe_file tool with the output file path",
                "note": "Grant microphone permission to Terminal when prompted",
            }, indent=2)
        )]

    elif name == "transcribe_file":
        file_path = arguments.get("file_path")
        language = arguments.get("language", "auto")
        include_cleaned = arguments.get("include_cleaned", True)
        include_metrics = arguments.get("include_metrics", True)

        if not file_path or not os.path.exists(file_path):
            return [TextContent(
                type="text",
                text=json.dumps({"error": f"File not found: {file_path}"})
            )]

        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_wav:
            temp_wav_path = temp_wav.name

        try:
            # Convert audio
            with tempfile.NamedTemporaryFile(delete=False) as temp_input:
                temp_input_path = temp_input.name
                subprocess.run(
                    ["ffmpeg", "-i", file_path, "-ar", "16000", "-ac", "1",
                     "-c:a", "pcm_s16le", temp_wav_path, "-y"],
                    capture_output=True, timeout=60
                )

            # Transcribe
            cmd = [
                str(WHISPER_CLI), "-m", str(MODEL),
                "-f", temp_wav_path, "-l", language,
                "--word-thold", "0.01",
                "-otxt", "-ojf", "-owts"
            ]

            with tempfile.TemporaryDirectory() as temp_dir:
                output_base = os.path.join(temp_dir, "output")
                cmd.extend(["-of", output_base])

                result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)

                if result.returncode != 0:
                    return [TextContent(
                        type="text",
                        text=json.dumps({"error": "Transcription failed"})
                    )]

                # Read outputs
                verbatim = ""
                language_detected = None
                duration = None
                word_timestamps = []

                txt_path = f"{output_base}.txt"
                json_path = f"{output_base}.json.full"
                wts_path = f"{output_base}.words"

                if os.path.exists(txt_path):
                    with open(txt_path, "r") as f:
                        verbatim = f.read().strip()

                if os.path.exists(json_path):
                    with open(json_path, "r") as f:
                        data = json.load(f)
                        language_detected = data.get("result", {}).get("language")
                        segments = data.get("transcription", [])
                        if segments:
                            # Calculate duration
                            last_seg = segments[-1]
                            to_time = last_seg.get("timestamps", {}).get("to", "")
                            if to_time:
                                # Parse "00:00:05,590" format
                                h, m, s_ms = to_time.split(':')
                                duration = float(h) * 3600 + float(m) * 60 + float(s_ms.replace(',', '.'))

                if os.path.exists(wts_path):
                    with open(wts_path, "r") as f:
                        word_timestamps = f.read()

                # Build structured response
                response = {
                    "success": True,
                    "language": language_detected,
                    "duration_seconds": duration,
                    "transcript": {
                        "verbatim": verbatim,
                    }
                }

                if include_cleaned:
                    response["transcript"]["cleaned"] = clean_transcript(verbatim)
                    response["transcript"]["word_count"] = len(verbatim.split())

                if include_metrics:
                    response["metrics"] = {
                        "filler_words": count_filler_words(verbatim),
                        "speech_patterns": analyze_speech_patterns(verbatim),
                    }

                if word_timestamps:
                    response["word_timestamps_sample"] = word_timestamps[:500]  # First 500 chars

            return [TextContent(
                type="text",
                text=json.dumps(response, indent=2, ensure_ascii=False)
            )]

        finally:
            if os.path.exists(temp_wav_path):
                os.unlink(temp_wav_path)

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
