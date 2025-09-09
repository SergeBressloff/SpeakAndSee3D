import json
from pathlib import Path
import pytest
import generate_nui

def run_script(args):
    import sys
    old = sys.argv
    try:
        sys.argv = args
        generate_nui.main()
    finally:
        sys.argv = old

def test_generate_path(tmp_path, fake_triposr, monkeypatch):
    in_json = tmp_path / "in.json"
    out_json = tmp_path / "out.json"
    img = tmp_path / "img.png"
    img.write_bytes(b"\x89PNG\r\n\x1a\n")

    # point viewer assets + models to temp dirs
    viewer_dir = tmp_path / "viewer"
    viewer_dir.mkdir()
    models_dir = tmp_path / "models"
    (models_dir / "TripoSR").mkdir(parents=True)

    import generate_nui
    monkeypatch.setattr(generate_nui, "viewer_assets_dir", str(viewer_dir), raising=True)
    from generate_nui import get_models_dir as _get_models_dir
    # intercept utils.get_models_dir to return our temp models dir
    import utils
    monkeypatch.setattr(utils, "get_models_dir", lambda: str(models_dir), raising=True)

    in_json.write_text(json.dumps({"image_path": str(img)}))
    run_script(["generate_nui.py", str(in_json), str(out_json)])

    data = json.loads(out_json.read_text())
    model_path = Path(data["model_path"])
    assert model_path.exists()
    assert model_path.name == "generated_model.obj"

def test_generate_missing_image(tmp_path):
    in_json = tmp_path / "in.json"
    out_json = tmp_path / "out.json"
    in_json.write_text(json.dumps({"image_path": str(tmp_path / "missing.png")}))

    import pytest
    with pytest.raises(SystemExit) as e:
        run_script(["generate_nui.py", str(in_json), str(out_json)])
    assert e.value.code == 1
