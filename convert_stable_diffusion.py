from optimum.onnxruntime import ORTStableDiffusionPipeline

pipeline = ORTStableDiffusionPipeline.from_pretrained(
    "stabilityai/stable-diffusion-2-1",
    export=True
)

prompt = "realistic 3D model of a lion"
image = pipeline(prompt).images[0]

image.save("sd21-output.png")
pipeline.save_pretrained("./onnx-stable-diffusion-2-1")
