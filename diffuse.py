import os
import subprocess
import sys
import json
import tempfile
from utils import get_models_dir, resource_path

def main():
    print("Starting diffuse executable", flush=True)

    if len(sys.argv) != 3:
        print("Usage: diffuse <input_json> <output_json>", flush=True)
        sys.exit(1)

    input_json = sys.argv[1]
    output_json = sys.argv[2]
    
    with open(input_json, "r") as f:
        input_data = json.load(f)

    prompt = input_data.get("prompt")
    if not prompt:
        raise ValueError("No prompt found in input JSON")

    model_base_path = get_models_dir()
    model_name = input_data.get("model_name", "onnx-stable-diffusion-2-1")

    model_path = os.path.join(model_base_path, model_name)
    print("Model path:", model_path)

    python_exe = os.path.join("venvs", "stable_env", "Scripts", "python.exe")
    python_env = resource_path(python_exe)

    print(f"[DEBUG] Using Python: {python_env}", flush=True)

    if not os.path.exists(model_path):
        raise FileNotFoundError(f"Model directory not found: {model_path}")

    output_image_path = os.path.join(tempfile.gettempdir(), "generated_image.png")

    if model_name.startswith("flux"):
        run_script = resource_path("run_flux.py")
    elif model_name.startswith("LCM"):
        run_script = resource_path("run_stable_diffusion.py")
    elif model_name.startswith("onnx"):
        run_script = resource_path("run_onnx.py")
    print("Run Script:", run_script)

    print(f"Running {model_name} with prompt '{prompt}', output: {output_image_path}", flush=True)

    try:
        subprocess.run([
            python_env,
            run_script,
            model_path,
            prompt,
            output_image_path
        ], check=True)

        if not os.path.exists(output_image_path):
            raise FileNotFoundError("Image not generated")

        with open(output_json, "w") as f:
            json.dump({"image_path": output_image_path}, f)

        print(f"Image path written to: {output_json}", flush=True)

    except Exception as e:
        print("[ERROR] Diffusion failed:", e, flush=True)
        with open(output_json, "w") as f:
            json.dump({"error": str(e)}, f)
        sys.exit(1)

if __name__ == "__main__":
    main()