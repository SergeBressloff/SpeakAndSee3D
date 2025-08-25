import os
import sys
import json
import tempfile
import traceback
import torch
from diffusers import DiffusionPipeline
from diffusers import LCMScheduler
from utils import get_models_dir

def determine_device():
    if hasattr(torch, "backends") and getattr(torch.backends, "mps", None) and torch.backends.mps.is_available():
        return "mps"
    if torch.cuda.is_available():
        return "cuda"
    return "cpu"

def determine_dtype(device: str) -> torch.dtype:
    if device == "cuda":
        return torch.float16
    elif device == "mps":
        return torch.bfloat16 
    else: 
        return torch.float32

def infer_kind(model_dir: str) -> str:
    if "flux" in os.path.basename(model_dir).lower():
        return "flux"
    elif "lcm" in os.path.basename(model_dir).lower():
        return "lcm"  
    return "auto"

def load(kind: str, model_dir: str, device: str, cfg: dict):
    dtype = determine_dtype(device)
    seed = cfg.get("seed")
    generator = None

    print(f"[INFO] Loading Diffusion pipeline: {model_dir} (dtype={dtype})", flush=True)
    pipe = DiffusionPipeline.from_pretrained(model_dir, torch_dtype=dtype)
    pipe.to(device)

    if seed is not None:
        generator = torch.Generator(device=device).manual_seed(int(seed))

    return {"pipe": pipe, "kind": kind, "generator": generator}

@torch.inference_mode()
def run(bundle: dict, cfg: dict, out_path: str):
    prompt = cfg["prompt"]
    negative = cfg.get("negative_prompt")
    steps = int(cfg.get("steps", 20))
    guidance = float(cfg.get("guidance_scale", 1.5))

    kind = bundle["kind"]
    pipe = bundle["pipe"]

    # reduces peak RAM/VRAM
    if hasattr(pipe, "enable_attention_slicing"):
        pipe.enable_attention_slicing("auto")
        pass

    if kind == "flux":
        s = int(cfg.get("steps", 4))
        g = float(cfg.get("guidance_scale", 0.0))
        max_seq_len = int(cfg.get("max_sequence_length", 256))
        img = pipe(
            prompt=prompt,
            guidance_scale=g,
            num_inference_steps=s,
            max_sequence_length=max_seq_len,
            generator=bundle.get("generator"),
        ).images[0]
        img.save(out_path)
        return

    elif kind == "lcm":
        pipe.scheduler = LCMScheduler.from_config(pipe.scheduler.config)
        img = pipe(
            prompt=prompt,
            negative_prompt=negative,
            num_inference_steps=steps,
            guidance_scale=guidance,
            generator=bundle.get("generator"),
        ).images[0]
        img.save(out_path)
        return

    else:
        img = pipe(
            prompt=prompt,
            negative_prompt=negative,
            num_inference_steps=steps,
            guidance_scale=guidance,
            generator=bundle.get("generator"),
        ).images[0]
        img.save(out_path)
        return

def main():
    if len(sys.argv) != 3:
        print("Usage: diffuse <input_json> <output_json>", flush=True)
        sys.exit(1)

    input_json, output_json = sys.argv[1], sys.argv[2]

    try:
        with open(input_json, "r") as f:
            cfg = json.load(f)

        prompt = cfg.get("prompt")
        if not prompt:
            raise ValueError("Missing 'prompt' in input JSON.")

        models_root = get_models_dir()
        model_name = cfg.get("model_name")
        if not model_name:
            raise ValueError("Missing 'model_name' in input JSON.")
        model_dir = os.path.join(models_root, model_name)

        if not os.path.isdir(model_dir):
            raise FileNotFoundError(f"Model directory not found: {model_dir}")

        kind = infer_kind(model_dir)
        dev = determine_device()
        print(f"[INFO] Pipeline={kind}  Device={dev}", flush=True)

        bundle = load(kind, model_dir, dev, cfg)

        out_img = cfg.get("output_image_path") or os.path.join(tempfile.gettempdir(), "generated_image.png")
        run(bundle, cfg, out_img)

        with open(output_json, "w") as f:
            json.dump({"image_path": out_img}, f)
        print(f"[OK] Image saved → {out_img}", flush=True)

    except Exception as e:
        print("[ERROR] Diffusion failed:", e, flush=True)
        traceback.print_exc()
        with open(output_json, "w") as f:
            json.dump({"error": str(e)}, f)
        sys.exit(1)

if __name__ == "__main__":
    main()
