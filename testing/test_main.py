# tests/test_mainwindow_file_ops.py
from pathlib import Path
import builtins
import pytest
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QInputDialog, QFileDialog, QMessageBox
import main

def _patch_env(monkeypatch, tmp_assets):
    monkeypatch.setattr(main, "get_models_dir", lambda: str(tmp_assets["models"]))
    monkeypatch.setattr(main, "get_icons_dir",  lambda: str(tmp_assets["icons"]))
    monkeypatch.setattr(main, "get_data_dir",   lambda: str(tmp_assets["data"]))
    monkeypatch.setattr(main, "get_viewer_assets", lambda: str(tmp_assets["viewer"]))
    monkeypatch.setattr(main, "ModelViewer", __import__("tests.conftest", fromlist=["FakeViewer"]).FakeViewer)
    monkeypatch.setattr(main, "ModelSelector", __import__("tests.conftest", fromlist=["FakeSelector"]).FakeSelector)
    monkeypatch.setattr(main, "AudioRecorder", __import__("tests.conftest", fromlist=["FakeRecorder"]).FakeRecorder)
    monkeypatch.setattr(main, "Pipeline", __import__("tests.conftest", fromlist=["FakePipeline"]).FakePipeline)

def test_load_model_from_text(qtbot, monkeypatch, tmp_assets, tmp_path):
    _patch_env(monkeypatch, tmp_assets)
    w = main.MainWindow(); qtbot.addWidget(w)
    # fake a matching result
    fp = tmp_path / "match.obj"; fp.write_text("# obj")
    w.selector.best_match = (str(fp), 0.9)
    w.load_model_from_text("chair")
    assert w.viewer.loaded == str(fp)
    assert w.current_model_path == str(fp)
    assert w.message.text() == "chair"

def test_generate_model_runs_pipeline_and_updates_view(qtbot, monkeypatch, tmp_assets, tmp_path):
    _patch_env(monkeypatch, tmp_assets)
    w = main.MainWindow(); qtbot.addWidget(w)
    w.set_mode("generate")
    # per-model settings override check
    model = "dreamshaper-7"
    idx = w.model_dropdown.findText(model)
    if idx >= 0:
        w.model_dropdown.setCurrentIndex(idx)
    # Run
    w.generate_model("castle on a hill")
    assert w.viewer.loaded == "/tmp/fake_model.obj"
    assert w.current_model_path == "/tmp/fake_model.obj"
    assert "3D asset for: castle on a hill" in w.message.text()

def test_handle_save_and_delete(qtbot, monkeypatch, tmp_assets, tmp_path):
    _patch_env(monkeypatch, tmp_assets)
    w = main.MainWindow(); qtbot.addWidget(w)
    w.set_mode("generate")

    # make a fake generated file
    src = tmp_path / "gen.obj"; src.write_text("# obj")
    w.current_model_path = str(src)

    # Mock two QInputDialog.getText calls (filename, then description)
    answers = iter([("my_model", True), ("a nice model", True)])
    monkeypatch.setattr(QInputDialog, "getText", lambda *a, **k: next(answers))

    w.handle_save()
    dest = Path(tmp_assets["viewer"]) / "3d_assets" / "my_model.obj"
    assert dest.exists()
    assert w.selector.added[-1] == ("my_model.obj", "a nice model")
    assert "Saved: my_model.obj" in w.message.text()

    # Now delete
    w.current_model_path = str(dest)
    w.set_mode("Load")
    w.handle_delete()
    assert not dest.exists()
    assert w.selector.removed[-1] == "my_model.obj"
    assert w.viewer.cleared
    assert "Deleted: my_model.obj" in w.message.text()

def test_handle_import(qtbot, monkeypatch, tmp_assets, tmp_path):
    _patch_env(monkeypatch, tmp_assets)
    w = main.MainWindow(); qtbot.addWidget(w)

    src = tmp_path / "asset.obj"; src.write_text("# obj")
    monkeypatch.setattr(QFileDialog, "getOpenFileName", lambda *a, **k: (str(src), "OBJ"))
    monkeypatch.setattr(QInputDialog, "getText", lambda *a, **k: ("a desc", True))

    w.handle_import()
    dest = Path(tmp_assets["viewer"]) / "3d_assets" / "asset.obj"
    assert dest.exists()
    assert w.selector.added[-1] == ("asset.obj", "a desc")
    assert w.viewer.loaded == str(dest)
    assert "Uploaded: asset.obj" in w.message.text()

def test_show_models_dialog_empty_shows_message(qtbot, monkeypatch, tmp_assets):
    _patch_env(monkeypatch, tmp_assets)
    w = main.MainWindow(); qtbot.addWidget(w)

    # No entries → should inform user
    monkeypatch.setattr(w, "load_model_descriptions", lambda: {})
    seen = {}
    monkeypatch.setattr(QMessageBox, "information", lambda *a, **k: seen.setdefault("called", True))
    w.show_models_dialog()
    assert seen.get("called") is True

def test_keyboard_shortcuts(qtbot, monkeypatch, tmp_assets):
    _patch_env(monkeypatch, tmp_assets)
    w = main.MainWindow(); qtbot.addWidget(w)
    w.show()

    # 'T' focuses the text field
    qtbot.keyClick(w, "t")
    assert w.text_input.hasFocus()

    # ESC clears focus back to window
    qtbot.keyClick(w.text_input, Qt.Key_Escape)
    assert not w.text_input.hasFocus()

    # Left/Right toggle modes (when not typing)
    qtbot.keyClick(w, Qt.Key_Right)
    assert w.is_generate_mode()
    qtbot.keyClick(w, Qt.Key_Left)
    assert not w.is_generate_mode()

    # ENTER while typing triggers handle_text_input
    called = {}
    monkeypatch.setattr(w, "handle_text_input", lambda: called.setdefault("enter", True))
    w.text_input.setFocus()
    qtbot.keyClick(w.text_input, Qt.Key_Return)
    assert called.get("enter") is True
