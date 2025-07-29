import torch
from diffusers import FluxPipeline
import sys

prompt = sys.argv[1]
output_path = sys.argv[2]

# local_model_path = "./models/flux_1_schnell"          to download model into project

pipe = FluxPipeline.from_pretrained(
    "black-forest-labs/FLUX.1-schnell",
    # cache_dir=local_model_path,                       to download model into project
    torch_dtype=torch.bfloat16)
pipe.to("mps" if torch.mps.is_available() else "cpu")

image = pipe(
    prompt,
    guidance_scale=0.0,
    num_inference_steps=4,
    max_sequence_length=256,
    generator=torch.Generator("mps").manual_seed(0)
).images[0]
image.save(output_path)
print(f"Image saved to {output_path}")