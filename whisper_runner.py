import subprocess
import os, sys

print("Starting whisper", flush=True)

if getattr(sys, 'frozen', False):
    # Running from PyInstaller bundle
    base_path = sys._MEIPASS
else:
    # Running from source
    base_path = os.path.dirname(os.path.abspath(__file__))

AUDIO_PATH = sys.argv[1]
WHISPER_BIN = os.path.join(base_path, "whisper.cpp/build/bin/whisper-cli")
MODEL_PATH = os.path.join(base_path, "whisper.cpp/models/ggml-base.en.bin")

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
            result = f.read().strip()
            print(result)
    else:
        print("No transcription found") 
except Exception as e:
    print("Whisper error:", e)
