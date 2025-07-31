import os
import subprocess
import sys
import json
import tempfile

def main():
    print("Starting diffuse executable", flush=True)

    if len(sys.argv) != 3:
        print("Usage: diffuse <input_json> <output_json>")
        sys.exit(1)

    input_json = sys.argv[1]
    output_json = sys.argv[2]

    with open(input_json, "r") as f:
        input_data = json.load(f)

    prompt = input_data.get("prompt")
    if not prompt:
        print("No prompt found in input JSON", flush=True)
        sys.exit(1)

    # Temp output path for the image
    output_image_path = os.path.join(tempfile.gettempdir(), "generated_image.png")

    os.environ["PYTORCH_ENABLE_MPS_FALLBACK"] = "1"

    if getattr(sys, 'frozen', False):
        base_path = sys._MEIPASS
    else:
        base_path = os.path.dirname(os.path.abspath(__file__))
    
    python_exe = "python"

    print("Base Path: ", base_path)
    print("Python Exe: ", python_exe)

    run_script = os.path.join(base_path, "run_flux.py")
    print("Run Script: ", run_script)

    print(f"Running run_flux.py with prompt: '{prompt}', output: {output_image_path}", flush=True)

    try:
        subprocess.run([
            python_exe,
            run_script,
            prompt,
            output_image_path
        ], check=True)

        if not os.path.exists(output_image_path):
            raise FileNotFoundError("Image not generated")

        with open(output_json, "w") as f:
            json.dump({ "image_path": output_image_path }, f)

        print(f"Image path written to: {output_json}", flush=True)

    except Exception as e:
        print("[ERROR] Diffusion failed:", e)
        with open(output_json, "w") as f:
            json.dump({ "error": str(e) }, f)
        sys.exit(1)

if __name__ == "__main__":
    main()
