import os
import subprocess
import sys

print("Starting generate_model.py", flush=True)

image_path = sys.argv[1]
output_dir = sys.argv[2]

os.environ["PYTORCH_ENABLE_MPS_FALLBACK"] = "1"

if getattr(sys, 'frozen', False):
    # Running from a PyInstaller bundle
    base_path = sys._MEIPASS
    python_exe = os.path.join(base_path, "venvs", "spa3d_env", "bin", "python")
else:
    # Running from source
    base_path = os.path.dirname(os.path.abspath(__file__))

run_script = os.path.join(base_path, "stable-point-aware-3d", "run.py")

print(f"About to run run.py with image: {image_path}, output: {output_dir}", flush=True)
print(f"Using script at: {run_script}", flush=True)
print(f"Using interpreter: {python_exe}", flush=True)

subprocess.run([
    python_exe,
    run_script,
    image_path,
    "--output-dir", output_dir
], check=True)
