import subprocess
import os
import uuid
from utils import resource_path

AUDIO_PATH = resource_path(os.path.join("audio", "recording.wav"))
WHISPER_BIN = resource_path("whisper.cpp/build/bin/whisper-cli")
MODEL_PATH = resource_path("whisper.cpp/models/ggml-base.en.bin")

def transcribe_whisper():
    if not os.path.exists(AUDIO_PATH):
        return "No audio file found"

    try:
        cmd = [
            WHISPER_BIN,
            "-m", MODEL_PATH,
            "-f", AUDIO_PATH,
            "-otxt"
        ]
        subprocess.run(cmd, check=True)
        txt_path = AUDIO_PATH + ".txt"
        if os.path.exists(txt_path):
            with open(txt_path, "r") as f:
                return f.read().strip()
        else:
            return "No transcription found"
    except Exception as e:
        print("Whisper error:", e)
        return None
