import os

output_dir = os.path.abspath("output")

image_path = os.path.join(output_dir, "generated_image.png")
model_path = os.path.join(output_dir, "0", "mesh.glb")  # Expected output

print(f"Checking for model file at: '{model_path}'")
print(f"File exists? {os.path.exists(model_path)}")
print("Output from os.listdir():")
print(os.listdir(os.path.dirname(model_path)))

print("CWD:", os.getcwd())
print("Absolute model path:", os.path.abspath(model_path))