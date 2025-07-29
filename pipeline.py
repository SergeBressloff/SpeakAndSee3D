import subprocess, tempfile, json, os
from utils import resource_path

BIN_DIR = resource_path("bin")
TRANSCRIBE_BIN = os.path.join(BIN_DIR, "transcribe")
DIFFUSE_BIN = os.path.join(BIN_DIR, "diffuse")
GENERATE_BIN = os.path.join(BIN_DIR, "generate")

class Pipeline:
    def run_pipeline(self, audio_path):
        with tempfile.TemporaryDirectory() as tmpdir:
            # Step 1: Transcribe
            transcribe_input = { "audio_path": audio_path }
            transcribe_output = self.run_stage(TRANSCRIBE_BIN, transcribe_input)
            text = transcribe_output.get("transcription")

            if not text:
                raise RuntimeError("Transcription failed")

            # Step 2: Diffuse image
            diffuse_input = { "prompt": text }
            diffuse_output = self.run_stage(DIFFUSE_BIN, diffuse_input)
            image_path = diffuse_output.get("image_path")

            if not os.path.exists(image_path):
                raise RuntimeError("Image generation failed")

            # Step 3: Generate 3D
            generate_input = { "image_path": image_path }
            generate_output = self.run_stage(GENERATE_BIN, generate_input)
            model_path = generate_output.get("model_path")

            # REMEMBER, generate is returning just generated_model.glb instead of the whole file path. Need to change this.
            # if not os.path.exists(model_path):
                # raise RuntimeError("3D model generation failed")

            return {
                "text": text,
                "image": image_path,
                "model": model_path
            }

    def run_stage(self, exe, input_dict):
        with tempfile.NamedTemporaryFile("w+", delete=False, suffix=".json") as infile, \
             tempfile.NamedTemporaryFile("r", delete=False, suffix=".json") as outfile:

            json.dump(input_dict, infile)
            infile.flush()

            subprocess.run([exe, infile.name, outfile.name], check=True)

            return json.load(outfile)
