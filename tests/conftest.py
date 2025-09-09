import os, sys
import json
import shutil
import types
import pytest
from pathlib import Path

# Add the repository root (one level up from tests/) to sys.path
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

@pytest.fixture
def tmp_json(tmp_path):
    """Return (input_json_path, output_json_path) in a temp dir."""
    in_json = tmp_path / "in.json"
    out_json = tmp_path / "out.json"
    return in_json, out_json

class FakeImage:
    def __init__(self, path_to_write):
        self.path_to_write = path_to_write
    def save(self, out_path):
        # create a real file to simulate an image
        Path(out_path).write_bytes(b"\x89PNG\r\n\x1a\n")

class FakePipeline:
    def __init__(self, dtype, device, image_target):
        self.dtype = dtype
        self.device = device
        self.image_target = image_target
        self.scheduler = types.SimpleNamespace(config={"dummy": True})
    def to(self, device):
        self.device = device
        return self
    def enable_attention_slicing(self, *_args, **_kwargs):
        pass
    def __call__(self, *args, **kwargs):
        # simulate Diffusers returning an object with `.images`
        return types.SimpleNamespace(images=[FakeImage(self.image_target)])

@pytest.fixture
def fake_diffusers(monkeypatch, tmp_path):
    """
    Monkeypatch DiffusionPipeline and LCMScheduler so no models are downloaded.
    """
    target_img = tmp_path / "generated.png"

    class _FakeDP:
        @staticmethod
        def from_pretrained(model_dir, torch_dtype=None):
            return FakePipeline(torch_dtype, device=None, image_target=target_img)

    class _FakeLCM:
        @staticmethod
        def from_config(_cfg):
            return "LCM_SCHEDULER"

    import sys
    # Patch in place where used: diffuse_nui
    import diffuse_nui
    monkeypatch.setattr(diffuse_nui, "DiffusionPipeline", _FakeDP, raising=True)
    monkeypatch.setattr(diffuse_nui, "LCMScheduler", _FakeLCM, raising=True)

    return target_img

@pytest.fixture
def fake_whisper_cli(monkeypatch, tmp_path):
    """
    Monkeypatch subprocess.run used by transcribe to 'create' the .txt output.
    """
    created = {}
    def _fake_run(argv, check):
        # argv includes ... "-f", <audio_path>, "-otxt"
        audio_idx = argv.index("-f") + 1
        audio_path = argv[audio_idx]
        txt_path = Path(audio_path + ".txt")
        txt_path.write_text("hello world")
        created["txt"] = txt_path
        return types.SimpleNamespace(returncode=0)
    import transcribe
    monkeypatch.setattr(transcribe.subprocess, "run", _fake_run, raising=True)
    return created

@pytest.fixture
def fake_triposr(monkeypatch, tmp_path):
    """
    Monkeypatch run_triposr to create the expected mesh file.
    """
    def _fake_run_triposr(image_path, model_path, output_dir):
        mesh = Path(output_dir) / "0" / "mesh.obj"
        mesh.parent.mkdir(parents=True, exist_ok=True)
        mesh.write_text("# fake obj")
    import generate_nui
    monkeypatch.setattr(generate_nui, "run_triposr", _fake_run_triposr, raising=True)

