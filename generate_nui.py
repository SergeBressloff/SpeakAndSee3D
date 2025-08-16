import os
import subprocess
import sys
import json
import shutil
import importlib
import pkgutil
from utils import get_viewer_assets, get_models_dir

viewer_assets_dir = get_viewer_assets()

def alias_package_tree(src_pkg_name: str, alias_root: str) -> None:
    """
    Make everything under `src_pkg_name` importable as `alias_root`.
    Example: alias_package_tree("TripoSR.tsr", "tsr")
    """
    src_pkg = importlib.import_module(src_pkg_name)

    # Alias the root package (tsr)
    sys.modules[alias_root] = src_pkg

    # Alias all submodules/packages (tsr.xxx -> TripoSR.tsr.xxx)
    if hasattr(src_pkg, "__path__"):  # must be a package
        prefix = src_pkg.__name__ + "."
        for _, fullname, _ in pkgutil.walk_packages(src_pkg.__path__, prefix):
            try:
                mod = importlib.import_module(fullname)
                alias = alias_root + fullname[len(src_pkg_name):]
                sys.modules[alias] = mod
            except Exception:
                pass

def run_triposr(image_path, model_path, output_dir):
    # checks whether running from Nuitka build or in dev
    is_frozen = "__compiled__" in globals() or getattr(sys, "frozen", False)

    if is_frozen:
        # If there is no top-level 'tsr', alias the whole TripoSR.tsr tree to 'tsr'
        try:
            importlib.import_module("tsr")
        except ImportError:
            alias_package_tree("TripoSR.tsr", "tsr")

        argv_backup = sys.argv[:]
        try:
            sys.argv = [
                "TripoSR.run",
                image_path,
                "--pretrained-model-name-or-path", model_path,
                "--output-dir", output_dir,
            ]
            importlib.import_module("TripoSR.run")
        finally:
            sys.argv = argv_backup
    else:
        run_script = os.path.abspath(os.path.join("TripoSR", "run.py"))
        subprocess.run([
            sys.executable,
            run_script,
            image_path,
            "--pretrained-model-name-or-path", model_path,
            "--output-dir", output_dir
        ], check=True)


def main():
    print("Starting generate executable", flush=True)

    if len(sys.argv) != 3:
        print("Usage: generate <input_json> <output_json>")
        sys.exit(1)

    input_json = sys.argv[1]
    output_json = sys.argv[2]

    with open(input_json, "r") as f:
        input_data = json.load(f)

    image_path = input_data.get("image_path")
    if not image_path or not os.path.exists(image_path):
        print(f"[ERROR] Invalid or missing image path: {image_path}", flush=True)
        sys.exit(1)

    model_path = os.path.join(get_models_dir(), "TripoSR")

    asset_output_dir = os.path.join(viewer_assets_dir, "output")
    os.makedirs(asset_output_dir, exist_ok=True)

    asset_path = os.path.join(asset_output_dir, "0", "mesh.obj")

    print(f"Running TripoSR with image {image_path} → {asset_output_dir}", flush=True)

    try:
        run_triposr(image_path, model_path, asset_output_dir)

        if os.path.exists(asset_path):
            final_path = os.path.join(viewer_assets_dir, "generated_model.obj")
            try:
                if os.path.exists(final_path):
                    os.remove(final_path)
                shutil.copy(asset_path, final_path)
            except Exception as copy_err:
                print(f"[ERROR] Failed to copy model: {copy_err}", flush=True)

            with open(output_json, "w") as f:
                json.dump({"model_path": final_path}, f)
        else:
            print("Model file not found after generation.", flush=True)
            with open(output_json, "w") as f:
                json.dump({"error": "Model file not found after generation."}, f)
            sys.exit(1)

    except Exception as e:
        print("[ERROR] Model generation failed:", e, flush=True)
        with open(output_json, "w") as f:
            json.dump({"error": str(e)}, f)
        sys.exit(1)

if __name__ == "__main__":
    main()
