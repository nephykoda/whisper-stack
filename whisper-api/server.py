#!/usr/bin/env python3
"""
HTTP API server for Whisper transcription.
Other computers on your network can send audio files to this.
"""

import json
import os
import subprocess
import tempfile
import zipfile
from pathlib import Path
from typing import Optional

from flask import Flask, request, jsonify, send_file
from werkzeug.utils import secure_filename

# Paths
SCRIPT_DIR = Path(__file__).parent.parent
WHISPER_CPP = SCRIPT_DIR / "whisper.cpp"
WHISPER_CLI = WHISPER_CPP / "build" / "bin" / "whisper-cli"
MODEL = WHISPER_CPP / "models" / "ggml-large-v3-turbo.bin"

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 100 * 1024 * 1024  # 100MB max


@app.route('/')
def index():
    """API info page."""
    return jsonify({
        "service": "Whisper Transcription API",
        "version": "1.0.0",
        "endpoints": {
            "POST /transcribe": "Transcribe an audio file",
            "POST /record": "Record from microphone (Mac only)",
            "GET /status": "Check service status",
            "GET /model": "Model information"
        },
        "features": [
            "Mixed Chinese/English support",
            "Verbatim transcription (stammers, pauses)",
            "100% offline & private"
        ]
    })


@app.route('/status')
def status():
    """Check if service is ready."""
    return jsonify({
        "ready": all([
            WHISPER_CLI.exists(),
            MODEL.exists()
        ]),
        "model": str(MODEL),
        "model_size_gb": MODEL.stat().st_size / (1024**3),
        "hostname": os.uname().nodename
    })


@app.route('/model')
def model_info():
    """Get model details."""
    return jsonify({
        "name": "large-v3-turbo",
        "size_gb": MODEL.stat().st_size / (1024**3),
        "path": str(MODEL),
        "capabilities": {
            "multilingual": True,
            "mixed_language": True,
            "verbatim": True,
            "languages": ["en", "zh", "auto", "100+ more"]
        }
    })


@app.route('/transcribe', methods=['POST'])
def transcribe():
    """
    Transcribe an audio file.

    Form data:
        file: Audio file (mp3, wav, m4a, etc.)
        verbatim: Include word timestamps (default: true)
        language: Language code or 'auto' (default: auto)
    """
    # Check file
    if 'file' not in request.files:
        return jsonify({"error": "No file provided"}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "No file selected"}), 400

    verbatim = request.form.get('verbatim', 'true').lower() == 'true'
    language = request.form.get('language', 'auto')

    # Save uploaded file
    with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as temp_wav:
        temp_wav_path = temp_wav.name

    try:
        # Convert to WAV format
        with tempfile.NamedTemporaryFile(delete=False) as temp_input:
            temp_input_path = temp_input.name
            file.save(temp_input_path)

        # Convert using ffmpeg
        convert_result = subprocess.run(
            ["ffmpeg", "-i", temp_input_path,
             "-ar", "16000", "-ac", "1",
             "-c:a", "pcm_s16le", temp_wav_path, "-y"],
            capture_output=True,
            timeout=60
        )

        if convert_result.returncode != 0:
            return jsonify({"error": f"Conversion failed: {convert_result.stderr.decode()}"}), 400

        # Build whisper command
        cmd = [
            str(WHISPER_CLI),
            "-m", str(MODEL),
            "-f", temp_wav_path,
            "-l", language,
            "--word-thold", "0.01",
            "-otxt",
            "-ojf"
        ]

        if verbatim:
            cmd.append("-owts")

        # Run transcription
        with tempfile.TemporaryDirectory() as temp_dir:
            output_base = os.path.join(temp_dir, "output")
            cmd.extend(["-of", output_base])

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300
            )

            if result.returncode != 0:
                return jsonify({"error": f"Transcription failed: {result.stderr}"}), 500

            # Read outputs
            response = {"success": True}

            txt_path = f"{output_base}.txt"
            json_path = f"{output_base}.json.full"
            wts_path = f"{output_base}.words"

            if os.path.exists(txt_path):
                with open(txt_path, "r") as f:
                    response["transcript"] = f.read().strip()

            if os.path.exists(json_path):
                with open(json_path, "r") as f:
                    response["details"] = json.load(f)

            if os.path.exists(wts_path):
                with open(wts_path, "r") as f:
                    response["word_timestamps"] = f.read()

        return jsonify(response)

    except subprocess.TimeoutExpired:
        return jsonify({"error": "Transcription timed out"}), 500
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        # Cleanup
        if os.path.exists(temp_wav_path):
            os.unlink(temp_wav_path)
        if 'temp_input_path' in locals() and os.path.exists(temp_input_path):
            os.unlink(temp_input_path)


@app.route('/record', methods=['POST'])
def record():
    """
    Record from microphone (Mac only).

    JSON body:
        duration: Recording duration in seconds (default: 30)
        verbatim: Include word timestamps (default: true)
    """
    data = request.get_json() or {}
    duration = min(int(data.get('duration', 30)), 300)  # Max 5 minutes
    verbatim = data.get('verbatim', True)

    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_file:
        temp_path = temp_file.name

    try:
        # Record using ffmpeg
        result = subprocess.run(
            ["ffmpeg", "-f", "avfoundation",
             "-i", ":0",
             "-t", str(duration),
             "-ar", "16000",
             "-ac", "1",
             "-y", temp_path],
            capture_output=True,
            timeout=duration + 10
        )

        if result.returncode != 0:
            return jsonify({
                "error": "Recording failed",
                "hint": "Grant microphone permission to Terminal",
                "details": result.stderr.decode()
            }), 500

        # Transcribe the recording
        cmd = [
            str(WHISPER_CLI),
            "-m", str(MODEL),
            "-f", temp_path,
            "-l", "auto",
            "--word-thold", "0.01",
            "-otxt",
            "-ojf"
        ]

        if verbatim:
            cmd.append("-owts")

        with tempfile.TemporaryDirectory() as temp_dir:
            output_base = os.path.join(temp_dir, "output")
            cmd.extend(["-of", output_base])

            result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)

            response = {"success": True, "duration_seconds": duration}

            if os.path.exists(f"{output_base}.txt"):
                with open(f"{output_base}.txt") as f:
                    response["transcript"] = f.read().strip()

            if os.path.exists(f"{output_base}.json.full"):
                with open(f"{output_base}.json.full") as f:
                    response["details"] = json.load(f)

            return jsonify(response)

    finally:
        if os.path.exists(temp_path):
            os.unlink(temp_path)


if __name__ == '__main__':
    print("""
    🎙️ Whisper Transcription API
    ================================
    Starting server on http://0.0.0.0:5001

    Other computers can access via:
    - Your Mac's IP address: http://YOUR_IP:5001
    - Bonjour name: http://YOUR_MAC.local:5001

    Endpoints:
    - POST /transcribe  - Upload audio file for transcription
    - POST /record      - Record from Mac's microphone
    - GET  /status      - Check service status
    - GET  /model       - Model information
    """)

    # Get local IP
    import socket
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        local_ip = s.getsockname()[0]
        s.close()
        print(f"📡 Local IP: http://{local_ip}:5001")
    except:
        pass

    app.run(host='0.0.0.0', port=5001, debug=False)
