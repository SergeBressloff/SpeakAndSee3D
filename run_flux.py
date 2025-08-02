import torch
from diffusers import FluxPipeline
import sys

model_path = sys.argv[1]
prompt = sys.argv[2]
output_path = sys.argv[3]

pipe = FluxPipeline.from_pretrained(
    model_path,  # "os.path.join("flux_1_schnell", "black-forest-labs/Flux.1-schnell")
    torch_dtype=torch.bfloat16
)

device = (
    "mps" if hasattr(torch, "backends") and torch.backends.mps.is_available()
    else "cuda" if torch.cuda.is_available()
    else "cpu"
)
pipe.to(device)

image = pipe(
    prompt=prompt,
    guidance_scale=0.0,
    num_inference_steps=4,
    max_sequence_length=256,
    generator=torch.Generator(device).manual_seed(0)
).images[0]

image.save(output_path)
print(f"Image saved to {output_path}")