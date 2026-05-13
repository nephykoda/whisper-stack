#!/usr/bin/env python3
"""
Global hotkey dictation for whisper-stack.
Press Option+Space to record, then automatically paste transcription.

Requirements: pip install pynput
"""

import subprocess
import tempfile
import time
import os
from pathlib import Path
from pynput import keyboard
from pynput.keyboard import Key, Controller

# Config
# Auto-detect whisper-stack directory from script location
SCRIPT_DIR = Path(__file__).parent.resolve()
WHISPER_DIR = os.environ.get("WHISPER_STACK_DIR", SCRIPT_DIR)
RECORD_DURATION = 10  # seconds
HOTKEY = {Key.cmd_l, Key.alt_l, Key.space}  # Cmd+Option+Space

keyboard_controller = Controller()


def record_and_transcribe():
    """Record audio and return transcript."""
    print("🎙️ Recording...")

    # Record using ffmpeg
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp:
        temp_path = temp.name

    try:
        subprocess.run([
            "ffmpeg", "-f", "avfoundation", "-i", ":0",
            "-t", str(RECORD_DURATION), "-ar", "16000",
            "-ac", "1", "-y", temp_path
        ], capture_output=True, timeout=RECORD_DURATION + 5)

        # Transcribe
        result = subprocess.run([
            WHISPER_DIR / "whisper.cpp" / "build" / "bin" / "whisper-cli",
            "-m", WHISPER_DIR / "whisper.cpp" / "models" / "ggml-large-v3-turbo.bin",
            "-f", temp_path,
            "-l", "auto",
            "-otxt",
            "-of", "/tmp/hotkey_output"
        ], capture_output=True, text=True, timeout=30)

        # Read transcript
        with open("/tmp/hotkey_output.txt") as f:
            transcript = f.read().strip()

        return transcript

    finally:
        if os.path.exists(temp_path):
            os.unlink(temp_path)


def paste_text(text):
    """Paste text at cursor position."""
    # Copy to clipboard
    subprocess.run(["pbcopy"], input=text.encode())

    # Simulate Cmd+V
    time.sleep(0.1)
    keyboard_controller.press(Key.cmd)
    keyboard_controller.press('v')
    keyboard_controller.release('v')
    keyboard_controller.release(Key.cmd)


def on_activate():
    """Hotkey triggered."""
    print("\n🎙️ Recording started...")
    transcript = record_and_transcribe()
    print(f"📝 Transcript: {transcript}")
    paste_text(transcript)
    print("✅ Pasted!")


def main():
    """Start hotkey listener."""
    print("""
    🎙️ whisper-stack Hotkey Dictation
    ================================
    Press Cmd+Option+Space to record (10 seconds)
    Transcription will be pasted automatically.

    Press Ctrl+C to quit.
    """)

    with keyboard.GlobalHotKeys({
        '<cmd>+<alt>+<space>': on_activate
    }) as h:
        h.join()


if __name__ == "__main__":
    main()
