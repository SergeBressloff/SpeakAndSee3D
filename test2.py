import os

whisper_bin = os.path.join(base_path, "whisper.cpp", "build", "bin", "Release", "whisper-cli.exe")
print(f"whisper_bin: {whisper_bin} | exists: {os.path.exists(whisper_bin)}")