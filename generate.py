import os
import subprocess
import sys
import json
import shutil
from utils import get_writable_viewer_assets, get_models_dir, resource_path

VIEWER_ASSETS_DIR = get_writable_viewer_assets()

def main():
    print("Starting generate executable", flush=True)

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

    model_path = os.path.join(get_models_dir(), "TripoSR")
    print("Model path:", model_path)

    python_exe = os.path.join("venvs", "tripo_env", "Scripts", "python.exe")
    python_env = resource_path(python_exe)

    run_script = resource_path(os.path.join("TripoSR", "run.py"))

    model_output_dir = os.path.abspath("output")
    os.makedirs(model_output_dir, exist_ok=True)

    obj_model_path = os.path.join(model_output_dir, "0", "mesh.obj")

    print("python_env: ", python_env)
    print(f"Running: {run_script} with image {image_path} → {model_output_dir}", flush=True)

    try:
        print("before subprocess")
        subprocess.run([
            python_env,
            run_script,
            image_path,
            "--pretrained-model-name-or-path", model_path,
            "--output-dir", model_output_dir
        ], check=True)
        print("after subprocess")

        # Return path to the generated model
        if os.path.exists(obj_model_path):
            print("Object model path:", obj_model_path)
            final_path = os.path.join(VIEWER_ASSETS_DIR, "generated_model.obj")
            print(f"[DEBUG] obj_model_path exists: {os.path.exists(obj_model_path)}")
            print(f"[DEBUG] Copying to final_path: {final_path}")
            try:
                if os.path.exists(final_path):
                    os.remove(final_path)
                shutil.copy(obj_model_path, final_path)
                print(f"[DEBUG] Copied model to: {final_path}")
            except Exception as copy_err:
                print(f"[ERROR] Failed to copy model: {copy_err}")
            with open(output_json, "w") as f:
                json.dump({ "model_path": final_path }, f)
            print(f"Model path written to: {output_json}", flush=True)
        else:
            print("Model file not found after generation.")
            return None

    except Exception as e:
        print("[ERROR] Model generation failed:", e)
        with open(output_json, "w") as f:
            json.dump({ "error": str(e) }, f)
        sys.exit(1)

if __name__ == "__main__":
    main()
