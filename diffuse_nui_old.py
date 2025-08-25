import os
import sys
import json
import tempfile
import traceback
import torch

from diffusers import StableDiffusionPipeline
from diffusers import FluxPipeline
from utils import get_models_dir

def _device():
    if hasattr(torch, "backends") and getattr(torch.backends, "mps", None) and torch.backends.mps.is_available():
        return "mps"
    if torch.cuda.is_available():
        return "cuda"
    return "cpu"

def _dtype_for(device: str, pref: str | None) -> torch.dtype:
    pref = (pref or "").lower()
    if pref == "float32":
        return torch.float32
    if device == "cuda":
        if pref == "float16":
            return torch.float16
        # default to fp16 on CUDA for speed
        return torch.float16
    # mps likes fp32/bf16; cpu = fp32
    return torch.bfloat16 if (device == "mps" and pref == "bfloat16") else torch.float32

def _infer_kind(model_dir: str, cfg: dict) -> str:
    explicit = (cfg.get("pipeline") or "").lower().strip()
    if explicit in {"sd", "flux", "onnx"}:
        return explicit
    # Detect ONNX by files
    for root, _, files in os.walk(model_dir):
        if any(f.endswith(".onnx") for f in files):
            return "onnx"
    # Heuristic for Flux by name
    if "flux" in os.path.basename(model_dir).lower():
        return "flux"
    # Default
    return "sd"

def _load(kind: str, model_dir: str, device: str, cfg: dict):
    dtype = _dtype_for(device, cfg.get("dtype"))
    seed = cfg.get("seed")
    generator = None

    if kind == "onnx":
        print(f"[INFO] Loading ONNX pipeline: {model_dir}", flush=True)
        pipe = ORTStableDiffusionPipeline.from_pretrained(model_dir)
        return {"pipe": pipe, "kind": "onnx"}  # ORT manages device internally

    if kind == "flux":
        print(f"[INFO] Loading Flux pipeline: {model_dir} (dtype={dtype})", flush=True)
        pipe = FluxPipeline.from_pretrained(model_dir, torch_dtype=dtype)
        pipe.to(device)
        if seed is not None:
            generator = torch.Generator(device=device).manual_seed(int(seed))
        return {"pipe": pipe, "kind": "flux", "generator": generator}

    print(f"[INFO] Loading StableDiffusion pipeline: {model_dir} (dtype={dtype})", flush=True)
    pipe = StableDiffusionPipeline.from_pretrained(model_dir, torch_dtype=dtype)
    pipe.to(device)
    if seed is not None:
        generator = torch.Generator(device=device).manual_seed(int(seed))
    return {"pipe": pipe, "kind": "sd", "generator": generator}

@torch.inference_mode()
def _run(bundle: dict, cfg: dict, out_path: str):
    prompt = cfg["prompt"]
    negative = cfg.get("negative_prompt")
    steps = int(cfg.get("steps", 20))
    guidance = float(cfg.get("guidance_scale", 1.5))

    kind = bundle["kind"]
    pipe = bundle["pipe"]

    # Light VRAM tweaks (safe across devices)
    if hasattr(pipe, "enable_attention_slicing"):
        pipe.enable_attention_slicing("auto")
    if hasattr(pipe, "enable_sequential_cpu_offload") and _device() == "cuda":
        # Uncomment if you want aggressive VRAM savings:
        # pipe.enable_sequential_cpu_offload()
        pass

    if kind == "onnx":
        img = pipe(
            prompt=prompt,
            negative_prompt=negative,
            num_inference_steps=steps,
            guidance_scale=guidance
        ).images[0]
        img.save(out_path)
        return

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

    # classic SD
    img = pipe(
        prompt=prompt,
        negative_prompt=negative,
        num_inference_steps=steps,
        guidance_scale=guidance,
        generator=bundle.get("generator"),
    ).images[0]
    img.save(out_path)

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

        kind = _infer_kind(model_dir, cfg)
        dev = _device()
        print(f"[INFO] Pipeline={kind}  Device={dev}", flush=True)

        bundle = _load(kind, model_dir, dev, cfg)

        out_img = cfg.get("output_image_path") or os.path.join(tempfile.gettempdir(), "generated_image.png")
        _run(bundle, cfg, out_img)

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
