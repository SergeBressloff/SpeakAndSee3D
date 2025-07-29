import os
import subprocess
import sys
import json
import tempfile

def main():
    print("Starting generate_model executable", flush=True)

    if len(sys.argv) != 3:
        print("Usage: generate <input_json> <output_json>")
        sys.exit(1)

    input_json = sys.argv[1]
    output_json = sys.argv[2]

    with open(input_json, "r") as f:
        input_data = json.load(f)

    image_path = input_data.get("image_path")
    if not image_path or not os.path.exists(image_path):
        print(f"[ERROR] Invalid or missing image path: {image_path}", flush=True)
        sys.exit(1)

    os.environ["PYTORCH_ENABLE_MPS_FALLBACK"] = "1"

    if getattr(sys, 'frozen', False):
        base_path = sys._MEIPASS
        python_exe = os.path.join(base_path, "venvs", "spa3d_env", "bin", "python")
    else:
        base_path = os.path.dirname(os.path.abspath(__file__))
        python_exe = sys.executable

    run_script = os.path.join(base_path, "stable-point-aware-3d", "run.py")

    # Use a temp output dir
    model_output_dir = os.path.join(tempfile.gettempdir(), "generated_model")
    os.makedirs(model_output_dir, exist_ok=True)

    print(f"Running: {run_script} with image {image_path} → {model_output_dir}", flush=True)

    try:
        subprocess.run([
            python_exe,
            run_script,
            image_path,
            "--output-dir", model_output_dir
        ], check=True)

        # Assume the .glb file is the output
        output_model_path = None
        for file in os.listdir(model_output_dir):
            if file.endswith(".glb"):
                output_model_path = os.path.join(model_output_dir, file)
                break

        if not output_model_path or not os.path.exists(output_model_path):
            raise FileNotFoundError("Model output (.glb) not found")

        with open(output_json, "w") as f:
            json.dump({ "model_path": output_model_path }, f)

        print(f"Model path written to: {output_json}", flush=True)

    except Exception as e:
        print("[ERROR] Model generation failed:", e)
        with open(output_json, "w") as f:
            json.dump({ "error": str(e) }, f)
        sys.exit(1)

if __name__ == "__main__":
    main()

