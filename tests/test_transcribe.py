import json
from pathlib import Path
import transcribe

def run_script(args):
    # helper to simulate CLI call to main() without spawning a process
    import sys
    old = sys.argv
    try:
        sys.argv = args
        transcribe.main()
    finally:
        sys.argv = old

def test_transcribe_path(tmp_path, tmp_json, fake_whisper_cli, monkeypatch):
    in_json, out_json = tmp_json
    audio = tmp_path / "audio.wav"
    audio.write_bytes(b"RIFF....")  # placeholder content

    in_json.write_text(json.dumps({"audio_path": str(audio)}))

    # Ensure we run in "dev" path branch (not frozen)
    monkeypatch.setattr(transcribe.sys, "frozen", False, raising=False)

    run_script(["transcribe.py", str(in_json), str(out_json)])

    result = json.loads(out_json.read_text())
    assert result["transcription"] == "hello world"

def test_transcribe_missing_audio(tmp_json, monkeypatch):
    in_json, out_json = tmp_json
    in_json.write_text(json.dumps({"audio_path": "missing.wav"}))

    # run and expect SystemExit(1)
    import pytest
    with pytest.raises(SystemExit) as e:
        run_script(["transcribe.py", str(in_json), str(out_json)])
    assert e.value.code == 1
    # output_json should contain error
    data = json.loads(out_json.read_text())
    assert "error" in data or "Invalid or missing audio file" in data.get("error","")
