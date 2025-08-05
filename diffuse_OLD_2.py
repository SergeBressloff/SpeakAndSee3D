import os
import sys
import json
import tempfile
from optimum.onnxruntime import ORTStableDiffusionPipeline
from PIL import Image

def generate_image(prompt, model_path, output_path):
    print("Loading ONNX diffusion model...", flush=True)

    # Load pipeline
    pipe = ORTStableDiffusionPipeline.from_pretrained(model_path)
    print("Model loaded.", flush=True)

    print(f"Generating image for prompt: '{prompt}'", flush=True)

    image = pipe(prompt=prompt).images[0]

    image.save(output_path)
    print(f"Image saved to: {output_path}", flush=True)

def main():
    print("Starting ONNX diffuse executable", flush=True)

    if len(sys.argv) != 3:
        print("Usage: diffuse <input_json> <output_json>", flush=True)
        sys.exit(1)

    input_json = sys.argv[1]
    output_json = sys.argv[2]

    try:
        with open(input_json, "r") as f:
            input_data = json.load(f)

        prompt = input_data.get("prompt")
        if not prompt:
            raise ValueError("No prompt found in input JSON")

        # Determine base path
        if getattr(sys, 'frozen', False):
            base_path = os.path.dirname(sys.executable)
        else:
            base_path = os.path.dirname(os.path.abspath(__file__))

        model_name = input_data.get("model_name", "onnx-stable-diffusion-2-1")
        model_path = os.path.join(base_path, "models", model_name)

        if not os.path.exists(model_path):
            raise FileNotFoundError(f"Model directory not found: {model_path}")

        output_image_path = os.path.join(tempfile.gettempdir(), "generated_image.png")

        generate_image(prompt, model_path, output_image_path)

        if not os.path.exists(output_image_path):
            raise FileNotFoundError("Image not generated")

        with open(output_json, "w") as f:
            json.dump({"image_path": output_image_path}, f)

        print(f"Output JSON written to: {output_json}", flush=True)

    except Exception as e:
        print("[ERROR] Diffusion failed:", e, flush=True)
        with open(output_json, "w") as f:
            json.dump({"error": str(e)}, f)
        sys.exit(1)

if __name__ == "__main__":
    main()
