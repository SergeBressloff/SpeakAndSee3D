import subprocess
import os, sys
import shutil
from utils import resource_path

FLUX_PY = resource_path("venvs/flux_env/bin/python")
FLUX_SCRIPT = resource_path("generate_image.py")

base_dir = os.path.dirname(sys.executable)
print("base_dir:", base_dir)

def generate_3d_model(prompt: str) -> str:
    output_dir = os.path.abspath("output")
    print("Resolved output_dir:", output_dir)
    os.makedirs(output_dir, exist_ok=True)

    image_path = os.path.join(output_dir, "generated_image.png")
    model_path = os.path.join(output_dir, "0", "mesh.glb")

    # Call Flux.1 image generation
    try:
        subprocess.run([
            FLUX_PY,
            FLUX_SCRIPT,
            prompt,
            image_path
        ], check=True)
    except subprocess.CalledProcessError as e:
        print(f"Flux.1 image generation failed: {e}")
        return None

    # Call Stable Point Aware 3D model generation
    try:
        subprocess.run([
            os.path.join(base_dir, "generate_model"),  # No 'python' call
            image_path,
            output_dir
        ], check=True)
    except subprocess.CalledProcessError as e:
        print(f"3D model generation failed: {e}")
        return None

    # Return path to the generated model
    if os.path.exists(model_path):
        final_path = os.path.join("viewer_assets", "generated_model.glb")
        shutil.copy(model_path, final_path)
        return "generated_model.glb"
    else:
        print("Model file not found after generation.")
        return None
