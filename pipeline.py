import subprocess, tempfile, json, os, sys
from utils import get_app_dir

# Determine base path
base_path = get_app_dir()
print("Base path:", base_path)

diffuse_exe = os.path.join(base_path, "diffuse_nui.exe")
generate_exe = os.path.join(base_path, "generate_nui.exe")

if not os.path.exists(diffuse_exe) or not os.path.exists(generate_exe):
    print("[ERROR] Diffuse and generate executables need to be in the same folder as the main app.") 

class Pipeline:
    def run_pipeline(self, text, model_name="onnx-stable-diffusion-2-1", cfg=None):
        print("Running pipeline")
        cfg = cfg or {}

        # Step 1: Diffuse image
        diffuse_input = { 
            "prompt": text,
            "model_name": model_name,
            **cfg
        }
        diffuse_output = self.run_stage(diffuse_exe, diffuse_input)
        image_path = diffuse_output.get("image_path")
        print("Image path:", image_path)

        if not os.path.exists(image_path):
            raise RuntimeError("Image generation failed")

        # Step 2: Generate 3D
        generate_input = { "image_path": image_path }
        generate_output = self.run_stage(generate_exe, generate_input)
        model_path = generate_output.get("model_path")
        print("Model path:", model_path)

        if not os.path.exists(model_path):
            raise RuntimeError("3D model generation failed")

        return {
            "text": text,
            "image": image_path,
            "model": model_path
        }

    @staticmethod
    def run_stage(exe, input_dict):
        with tempfile.NamedTemporaryFile("w+", delete=False, suffix=".json") as infile, \
             tempfile.NamedTemporaryFile("r", delete=False, suffix=".json") as outfile:

            json.dump(input_dict, infile)
            infile.flush()

            subprocess.run([exe, infile.name, outfile.name], check=True)
            
            return json.load(outfile)
