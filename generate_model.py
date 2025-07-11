import os
import subprocess
import sys

image_path = sys.argv[1]
output_dir = sys.argv[2]

os.environ["PYTORCH_ENABLE_MPS_FALLBACK"] = "1"

python_exe = sys.executable
run_script = os.path.join(os.path.dirname(__file__), "stable-point-aware-3d", "run.py")

subprocess.run([
    python_exe,
    run_script,
    image_path,
    "--output-dir", output_dir
], check=True)