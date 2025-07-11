import subprocess
import os
import shutil
from utils import resource_path

FLUX_PY = "/Users/sergebressloff/.pyenv/versions/flux_env/bin/python"
SPA3D_PY = "/Users/sergebressloff/.pyenv/versions/spa3d_env/bin/python"
FLUX_SCRIPT = resource_path("generate_image.py")
SPA3D_SCRIPT = resource_path("generate_model.py")

def generate_3d_model(prompt: str) -> str:
    output_dir = os.path.abspath("output")
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
            SPA3D_PY,
            SPA3D_SCRIPT,
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
