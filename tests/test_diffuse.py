import json
from pathlib import Path
import pytest
import diffuse_nui

def run_script(args):
    import sys
    old = sys.argv
    try:
        sys.argv = args
        diffuse_nui.main()
    finally:
        sys.argv = old

def test_diffuse_path(tmp_path, fake_diffusers, monkeypatch):
    in_json = tmp_path / "in.json"
    out_json = tmp_path / "out.json"

    # Stub models dir to a fake folder with a recognizable name (to test infer_kind)
    models_root = tmp_path / "models"
    flux_model = models_root / "cool-flux-model"
    flux_model.mkdir(parents=True, exist_ok=True)

    # utils.get_models_dir -> our fake root
    import diffuse_nui, utils
    monkeypatch.setattr(diffuse_nui, "get_models_dir", lambda: str(models_root), raising=False)

    cfg = {
        "prompt": "a cat riding a bike",
        "model_name": "cool-flux-model",
        "steps": 5,
        "guidance_scale": 0.0,
        "seed": 42,
    }
    in_json.write_text(json.dumps(cfg))

    run_script(["diffuse_nui.py", str(in_json), str(out_json)])

    data = json.loads(out_json.read_text())
    img_path = Path(data["image_path"])
    assert img_path.exists(), "image was saved by fake pipeline"

def test_diffuse_missing_prompt(tmp_path, fake_diffusers, monkeypatch):
    in_json = tmp_path / "in.json"
    out_json = tmp_path / "out.json"
    models_root = tmp_path / "models"
    (models_root / "lcm-model").mkdir(parents=True, exist_ok=True)

    import diffuse_nui
    monkeypatch.setattr(diffuse_nui, "get_models_dir", lambda: str(models_root), raising=False)

    in_json.write_text(json.dumps({"model_name": "lcm-model"}))

    with pytest.raises(SystemExit) as e:
        run_script(["diffuse_nui.py", str(in_json), str(out_json)])
    assert e.value.code == 1
    err = json.loads(out_json.read_text())["error"]
    assert "Missing 'prompt'" in err

def test_diffuse_missing_model_dir(tmp_path, fake_diffusers, monkeypatch):
    in_json = tmp_path / "in.json"
    out_json = tmp_path / "out.json"

    import diffuse_nui
    monkeypatch.setattr(diffuse_nui, "get_models_dir", lambda: str(tmp_path / "nope"), raising=False)

    in_json.write_text(json.dumps({"prompt": "x", "model_name": "not-there"}))

    import pytest
    with pytest.raises(SystemExit):
        run_script(["diffuse_nui.py", str(in_json), str(out_json)])
    err = json.loads(out_json.read_text())["error"]
    assert "Model directory not found" in err
