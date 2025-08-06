import subprocess, tempfile, json, os, sys

# Determine base path
if getattr(sys, 'frozen', False):
    base_path = os.path.dirname(sys.executable)
else:
    cwd = os.path.dirname(os.path.abspath(__file__))
    base_path = os.path.join(cwd, "bin")
print("Base path:", base_path)

DIFFUSE_BIN = os.path.join(base_path, "diffuse.exe")
GENERATE_BIN = os.path.join(base_path, "generate.exe")

class Pipeline:
    def run_pipeline(self, text, model_name="onnx-stable-diffusion-2-1"):
        print("Running pipeline")

        # Step 1: Diffuse image
        diffuse_input = { 
            "prompt": text,
            "model_name": model_name 
        }
        diffuse_output = self.run_stage(DIFFUSE_BIN, diffuse_input)
        image_path = diffuse_output.get("image_path")
        print("Image path:", image_path)

        if not os.path.exists(image_path):
            raise RuntimeError("Image generation failed")

        # Step 2: Generate 3D
        generate_input = { "image_path": image_path }
        generate_output = self.run_stage(GENERATE_BIN, generate_input)
        model_path = generate_output.get("model_path")
        print("Model path:", model_path)

        # REMEMBER, generate is returning just generated_model.glb instead of the whole file path. Need to change this.
        # if not os.path.exists(model_path):
            # raise RuntimeError("3D model generation failed")

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
