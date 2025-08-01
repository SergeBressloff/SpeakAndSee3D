import os
import subprocess
import sys
import json
import tempfile

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

    # Determine base path for model
    if getattr(sys, 'frozen', False):
        model_base_path = os.path.dirname(sys.executable)
    else:
        model_base_path = os.path.dirname(os.path.abspath(__file__))

    model_name = input_data.get("model_name", "onnx-stable-diffusion-2-1")
    model_path = os.path.join(model_base_path, "models", model_name)

    # Determine base path for environment
    if getattr(sys, 'frozen', False):
        env_base_path = sys._MEIPASS
        python_env = os.path.join(env_base_path, "venvs", "stable_env", "Scripts", "python.exe")
    else:
        env_base_path = os.path.dirname(os.path.abspath(__file__))
        python_env = os.path.join(env_base_path, "venvs", "stable_env", "Scripts", "python.exe")

    print(f"[DEBUG] Using Python: {python_env}", flush=True)

    if not os.path.exists(model_path):
        raise FileNotFoundError(f"Model directory not found: {model_path}")

    output_image_path = os.path.join(tempfile.gettempdir(), "generated_image.png")
    run_script = os.path.join(env_base_path, "run_flux.py")

    print(f"Running run_flux.py with prompt '{prompt}', output: {output_image_path}", flush=True)

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