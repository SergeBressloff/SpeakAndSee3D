import os
import subprocess
import sys
from utils import resource_path

print("Starting generate_model.py", flush=True)

image_path = sys.argv[1]
output_dir = sys.argv[2]

os.environ["PYTORCH_ENABLE_MPS_FALLBACK"] = "1"

python_exe = sys.executable
run_script = resource_path(os.path.join("stable-point-aware-3d", "run.py"))

print("About to run run.py with image:", image_path, "output:", output_dir, flush=True)

subprocess.run([
    python_exe,
    run_script,
    image_path,
    "--output-dir", output_dir
], check=True)