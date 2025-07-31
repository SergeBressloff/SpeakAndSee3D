import torch
from diffusers import StableDiffusionPipeline
import sys
import os

prompt = sys.argv[1]
output_path = sys.argv[2]

# Get the base directory of the executable (diffuse.exe inside bin/)
if getattr(sys, 'frozen', False):
    base_path = os.path.dirname(sys.executable)
else:
    base_path = os.path.dirname(os.path.abspath(__file__))

# Go up one level from bin/ to project/
project_root = os.path.dirname(base_path)

local_model_path = os.path.join(
    project_root,
    "models",
    "dreamshaper",
    "models--SimianLuo--LCM_Dreamshaper_v7",
    "snapshots",
    "a85df6a8bd976cdd08b4fd8f3b73f229c9e54df5"
)

pipe = StableDiffusionPipeline.from_pretrained(
    local_model_path,
    torch_dtype=torch.float16 if torch.cuda.is_available() else torch.float32,
    local_files_only=True
)

device = "mps" if torch.backends.mps.is_available() else "cuda" if torch.cuda.is_available() else "cpu"
pipe.to(device)

# Inference settings
image = pipe(
    prompt=prompt,
    num_inference_steps=10,
    guidance_scale=1.5,
    generator=torch.Generator(device).manual_seed(0)
).images[0]

image.save(output_path)