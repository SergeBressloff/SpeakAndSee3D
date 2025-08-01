import os
import sys
import json
import tempfile
import torch
from diffusers import StableDiffusionPipeline

def generate_image(prompt, output_path):
    print("Loading diffusion model...", flush=True)

    if getattr(sys, 'frozen', False):
        base_path = os.path.dirname(sys.executable)
    else:
        base_path = os.path.dirname(os.path.abspath(__file__))

    local_model_path = os.path.join(base_path, "./models/dreamshaper/models--SimianLuo--LCM_Dreamshaper_v7/snapshots/a85df6a8bd976cdd08b4fd8f3b73f229c9e54df5")

    pipe = StableDiffusionPipeline.from_pretrained(
        local_model_path,
        torch_dtype=torch.float16 if torch.cuda.is_available() else torch.float32,
        local_files_only=True
    )

    device = "mps" if torch.backends.mps.is_available() else "cuda" if torch.cuda.is_available() else "cpu"
    print(f"Using device: {device}", flush=True)
    pipe.to(device)

    print(f"Generating image for prompt: '{prompt}'", flush=True)

    image = pipe(
        prompt=prompt,
        num_inference_steps=10,
        guidance_scale=1.5,
        generator=torch.Generator(device).manual_seed(0)
    ).images[0]

    image.save(output_path)
    print(f"Image saved to: {output_path}", flush=True)

def main():
    print("Starting diffuse executable", flush=True)

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

        output_image_path = os.path.join(tempfile.gettempdir(), "generated_image.png")
        os.environ["PYTORCH_ENABLE_MPS_FALLBACK"] = "1"

        generate_image(prompt, output_image_path)

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