import os
import sys
import subprocess
import json

def main():
    print("Starting transcribe executable", flush=True)

    if len(sys.argv) != 3:
        print("Usage: transcribe <input_json> <output_json>")
        sys.exit(1)

    input_json = sys.argv[1]
    output_json = sys.argv[2]

    with open(input_json, "r") as f:
        input_data = json.load(f)

    audio_path = input_data.get("audio_path")
    if not audio_path or not os.path.exists(audio_path):
        print(f"Invalid or missing audio file: {audio_path}")
        sys.exit(1)

    if getattr(sys, 'frozen', False):
        base_path = sys._MEIPASS
    else:
        base_path = os.path.dirname(os.path.abspath(__file__))

    whisper_bin = os.path.join(base_path, "whisper.cpp/build/bin/whisper-cli")
    model_path = os.path.join(base_path, "whisper.cpp/models/ggml-base.en.bin")

    print(f"Running whisper-cli on: {audio_path}", flush=True)

    try:
        subprocess.run([
            whisper_bin,
            "-m", model_path,
            "-f", audio_path,
            "-otxt"
        ], check=True)

        txt_path = audio_path + ".txt"
        if not os.path.exists(txt_path):
            raise FileNotFoundError(f"Expected output not found: {txt_path}")

        with open(txt_path, "r") as f:
            transcription = f.read().strip()

        with open(output_json, "w") as f:
            json.dump({ "transcription": transcription }, f)

        print(f"Transcription written to {output_json}", flush=True)

    except Exception as e:
        print(f"[ERROR] Transcription failed: {e}", flush=True)
        with open(output_json, "w") as f:
            json.dump({ "error": str(e) }, f)
        sys.exit(1)

if __name__ == "__main__":
    main()
