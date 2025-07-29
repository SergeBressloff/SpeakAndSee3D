import os
import subprocess
import sys

print("Starting generate_image.py", flush=True)

prompt = sys.argv[1]
output_path = sys.argv[2]

os.environ["PYTORCH_ENABLE_MPS_FALLBACK"] = "1"

if getattr(sys, 'frozen', False):
    # Running from PyInstaller bundle
    base_path = sys._MEIPASS
    python_exe = os.path.join(base_path, "venvs", "flux_env", "bin", "python")
else:
    # Running from source
    base_path = os.path.dirname(os.path.abspath(__file__))
    python_exe = sys.executable  # Use current interpreter for dev/testing

run_script = os.path.join(base_path, "run_flux.py")

print(f"About to run run_flux.py with prompt: '{prompt}', output: {output_path}", flush=True)
print(f"Using script at: {run_script}", flush=True)
print(f"Using interpreter: {python_exe}", flush=True)

subprocess.run([
    python_exe,
    run_script,
    prompt,
    output_path
], check=True)
