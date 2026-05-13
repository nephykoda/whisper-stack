#!/usr/bin/env python3
"""
Agent-friendly transcription server with standardized JSON outputs.
Designed for LLM agents and automation workflows.
"""

import json
import os
import subprocess
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any

from flask import Flask, request, jsonify
from pydantic import BaseModel, Field

try:
    from whisper_stack import __version__
except ImportError:
    __version__ = "1.0.0"

VERSION = __version__

# Paths
SCRIPT_DIR = Path(__file__).parent.parent.parent
WHISPER_CPP = SCRIPT_DIR / "whisper.cpp"
WHISPER_CLI = WHISPER_CPP / "build" / "bin" / "whisper-cli"
MODEL = WHISPER_CPP / "models" / "ggml-large-v3-turbo.bin"

app = Flask(__name__)


class TranscriptionRequest(BaseModel):
    """Standard agent request schema."""
    language: str = Field(default="auto", description="Language code or 'auto'")
    verbatim: bool = Field(default=True, description="Include fillers and stammers")
    timestamps: bool = Field(default=True, description="Include word timestamps")
    sentiment: bool = Field(default=False, description="Include sentiment analysis")
    summary: bool = Field(default=False, description="Include auto-summary")


class AgentResponse(BaseModel):
    """Standardized agent response format."""
    success: bool
    transcript: Optional[str] = None
    language: Optional[str] = None
    duration_seconds: Optional[float] = None
    word_count: Optional[int] = None
    filler_words: Optional[Dict[str, int]] = None
    timestamps: Optional[list] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
    error: Optional[str] = None


@app.route('/v1/transcribe', methods=['POST'])
def transcribe_v1():
    """
    Agent-focused transcription endpoint.
    Returns standardized JSON for LLM consumption.

    Form data:
        file: Audio file
        language: auto, en, zh, etc.
        verbatim: true/false (default: true)
        timestamps: true/false (default: true)
    """
    if 'file' not in request.files:
        return jsonify(AgentResponse(
            success=False,
            error="No file provided"
        ).model_dump()), 400

    file = request.files['file']
    verbatim = request.form.get('verbatim', 'true').lower() == 'true'
    language = request.form.get('language', 'auto')
    include_timestamps = request.form.get('timestamps', 'true').lower() == 'true'

    with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as temp_wav:
        temp_wav_path = temp_wav.name

    try:
        # Convert audio
        with tempfile.NamedTemporaryFile(delete=False) as temp_input:
            temp_input_path = temp_input.name
            file.save(temp_input_path)

        subprocess.run(
            ["ffmpeg", "-i", temp_input_path, "-ar", "16000", "-ac", "1",
             "-c:a", "pcm_s16le", temp_wav_path, "-y"],
            capture_output=True, timeout=60
        )

        # Build command
        cmd = [
            str(WHISPER_CLI), "-m", str(MODEL),
            "-f", temp_wav_path, "-l", language,
            "--word-thold", "0.01", "-otxt", "-ojf"
        ]
        if verbatim:
            cmd.append("-owts")

        # Transcribe
        with tempfile.TemporaryDirectory() as temp_dir:
            output_base = os.path.join(temp_dir, "output")
            cmd.extend(["-of", output_base])

            result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)

            if result.returncode != 0:
                return jsonify(AgentResponse(
                    success=False,
                    error="Transcription failed"
                ).model_dump()), 500

            # Parse outputs
            txt_path = f"{output_base}.txt"
            json_path = f"{output_base}.json.full"

            transcript = None
            language_detected = None
            duration = None
            word_count = 0
            filler_counts = {"um": 0, "uh": 0, "like": 0, "you know": 0}

            if os.path.exists(txt_path):
                with open(txt_path, "r") as f:
                    transcript = f.read().strip()
                    word_count = len(transcript.split())

                    # Count filler words
                    text_lower = transcript.lower()
                    for filler in filler_counts:
                        filler_counts[filler] = text_lower.count(filler)

            if os.path.exists(json_path):
                with open(json_path, "r") as f:
                    data = json.load(f)
                    language_detected = data.get("result", {}).get("language")
                    # Calculate duration from segments
                    segments = data.get("transcription", [])
                    if segments:
                        last_seg = segments[-1]
                        duration = float(last_seg["timestamps"]["to"].split(',')[0].replace('(', '')) / 1000

            response = AgentResponse(
                success=True,
                transcript=transcript,
                language=language_detected,
                duration_seconds=duration,
                word_count=word_count,
                filler_words=filler_counts if verbatim else None,
                metadata={
                    "model": "large-v3-turbo",
                    "timestamp": datetime.now().isoformat(),
                    "verbatim": verbatim
                }
            )

        return jsonify(response.model_dump())

    except Exception as e:
        return jsonify(AgentResponse(
            success=False,
            error=str(e)
        ).model_dump()), 500
    finally:
        if os.path.exists(temp_wav_path):
            os.unlink(temp_wav_path)
        if 'temp_input_path' in locals() and os.path.exists(temp_input_path):
            os.unlink(temp_input_path)


@app.route('/v1/health', methods=['GET'])
def health():
    """Health check for load balancers/orchestrators."""
    return jsonify({
        "status": "healthy",
        "model_loaded": MODEL.exists(),
        "whisper_cli": WHISPER_CLI.exists(),
        "version": VERSION
    })


@app.route('/v1/capabilities', methods=['GET'])
def capabilities():
    """Return agent capabilities for auto-discovery."""
    return jsonify({
        "name": "whisper-stack",
        "version": VERSION,
        "type": "speech-to-text",
        "features": {
            "multilingual": True,
            "verbatim": True,
            "timestamps": True,
            "offline": True,
            "languages": ["en", "zh", "es", "fr", "de", "ja", "ko", "auto"],
        },
        "endpoints": {
            "transcribe": "/v1/transcribe",
            "health": "/v1/health",
            "capabilities": "/v1/capabilities"
        },
        "formats": ["mp3", "wav", "m4a", "ogg", "flac", "mp4"],
        "max_file_size_mb": 100
    })


if __name__ == '__main__':
    print("""
    🤖 whisper-stack Agent Server
    =============================
    Version: 1.0.0
    Port: 5001

    Agent Endpoints:
    - POST /v1/transcribe  - Transcribe audio
    - GET  /v1/health      - Health check
    - GET  /v1/capabilities - Discover features

    Example:
    curl -X POST http://localhost:5001/v1/transcribe \\
      -F "file=@audio.mp3" \\
      -F "verbatim=true"
    """)

    app.run(host='0.0.0.0', port=5001, debug=False)
