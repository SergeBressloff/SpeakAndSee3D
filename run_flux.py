import torch
from optimum.onnxruntime import ORTStableDiffusionPipeline
import sys

model_path = sys.argv[1]
prompt = sys.argv[2]
output_path = sys.argv[3]

print("Loading ONNX diffusion model...", flush=True)

pipe = ORTStableDiffusionPipeline.from_pretrained(model_path)
print("Model loaded.", flush=True)

image = pipe(prompt=prompt).images[0]
image.save(output_path)
print(f"Image saved to {output_path}")