import torch
from diffusers import FluxPipeline
import sys, os
from PIL import Image

prompt = sys.argv[1]
output_path = sys.argv[2]

pipe = FluxPipeline.from_pretrained("black-forest-labs/FLUX.1-schnell", torch_dtype=torch.bfloat16)
pipe.to("mps" if torch.mps.is_available() else "cpu")

image = pipe(
    prompt,
    guidance_scale=0.0,
    num_inference_steps=4,
    max_sequence_length=256,
    generator=torch.Generator("mps").manual_seed(0)
).images[0]
image.save(output_path)