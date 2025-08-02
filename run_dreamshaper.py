import torch
from diffusers import StableDiffusionPipeline
import sys

model_path = sys.argv[1]
prompt = sys.argv[2]
output_path = sys.argv[3]

pipe = StableDiffusionPipeline.from_pretrained(
    model_path,  # os.path.join("dreamshaper", "SimianLuo/LCM_Dreamshaper_v7")
    torch_dtype=torch.float16 if torch.cuda.is_available() else torch.float32
)

device = "mps" if torch.backend.mps.is_available() else "cuda" if torch.cuda.is_available() else "cpu"
pipe.to(device)

image = pipe(
    prompt=prompt,
    num_inference_steps=25,
    guidance_scale=1.5,
    generator=torch.Generator(device).manual_seed(0)
).images[0]

image.save(output_path)