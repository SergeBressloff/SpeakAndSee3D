from PySide6.QtWidgets import (
    QApplication, 
    QMainWindow, 
    QPushButton, 
    QVBoxLayout, 
    QWidget, 
    QLabel, 
    QComboBox,
    QLineEdit, 
    QHBoxLayout, 
    QSizePolicy, 
    QSpacerItem, 
    QFileDialog, 
    QFileDialog,
    QInputDialog,
    QFrame,
    QDialog, 
    QFormLayout, 
    QDialogButtonBox, 
    QSpinBox, 
    QDoubleSpinBox
)
from PySide6.QtCore import Qt, QTimer, QPropertyAnimation, QRect
from PySide6.QtGui import QFont, QIcon
from pipeline import Pipeline
from audio_recorder import AudioRecorder
from model_viewer import ModelViewer
from model_selector import ModelSelector
from utils import get_app_dir, get_data_dir, get_viewer_assets, get_models_dir, get_icons_dir
import os, sys, multiprocessing, shutil
import time
import contextlib

def is_flux(model_name: str) -> bool:
    return "flux" in (model_name or "").lower()

def is_lcm_dreamshaper(model_name: str) -> bool:
    return (model_name or "").lower() == "lcm_dreamshaper_v7"

def defaults_for(model_name: str) -> dict:
    name = (model_name or "").lower()
    if is_flux(name):
        return {"steps": 4, "guidance_scale": 0.0, "max_sequence_length": 256, "seed": 0}
    if is_lcm_dreamshaper(name):
        return {"steps": 20, "guidance_scale": 1.5, "seed": 0}
    # Generic SD-ish defaults
    return {"steps": 20, "guidance_scale": 7.5, "seed": 0}


class ConfigDialog(QDialog):
    def __init__(self, parent, model_name: str, preset: dict | None = None):
        super().__init__(parent)
        self.setWindowTitle("Generation Settings")
        self.model_name = model_name
        self._is_flux = is_flux(model_name)

        # start from model defaults, then overlay preset if provided
        d = defaults_for(model_name)
        if preset:
            d.update({k: v for k, v in preset.items() if v is not None})

        form = QFormLayout(self)

        # Optional negative prompt
        self.neg_prompt_edit = QLineEdit(self)
        self.neg_prompt_edit.setPlaceholderText("Optional negative prompt")
        self.neg_prompt_edit.setText(str(d.get("negative_prompt", "")))
        form.addRow(QLabel("Negative Prompt:"), self.neg_prompt_edit)

        # Steps
        self.steps = QSpinBox(self)
        self.steps.setRange(1, 200)
        self.steps.setValue(int(d.get("steps", 20)))
        form.addRow(QLabel("Steps:"), self.steps)

        # Guidance
        self.guidance = QDoubleSpinBox(self)
        self.guidance.setDecimals(2)
        self.guidance.setRange(0.0, 50.0)
        self.guidance.setSingleStep(0.1)
        self.guidance.setValue(float(d.get("guidance_scale", 7.5)))
        form.addRow(QLabel("Guidance Scale:"), self.guidance)

        # Flux-only: max_sequence_length
        self.max_seq_label = QLabel("Max Sequence Length:")
        self.max_seq = QSpinBox(self)
        self.max_seq.setRange(32, 4096)
        self.max_seq.setValue(int(d.get("max_sequence_length", 256)))
        if self._is_flux:
            form.addRow(self.max_seq_label, self.max_seq)
        else:
            self.max_seq_label.hide()
            self.max_seq.hide()

        # Seed
        self.seed = QSpinBox(self)
        self.seed.setRange(0, 2**31 - 1)
        self.seed.setValue(int(d.get("seed", 0)))
        form.addRow(QLabel("Seed:"), self.seed)

        # OK/Cancel
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel, self)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        form.addWidget(buttons)

    def values(self) -> dict:
        cfg = {
            "steps": int(self.steps.value()),
            "guidance_scale": float(self.guidance.value()),
            "seed": int(self.seed.value()),
        }
        neg = self.neg_prompt_edit.text().strip()
        if neg:
            cfg["negative_prompt"] = neg
        if is_flux(self.model_name):
            cfg["max_sequence_length"] = int(self.max_seq.value())
        return cfg


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Speak & See 3D")
        self.setGeometry(600, 600, 600, 700)

        # Title
        self.title = QLabel("Speak & See 3D")
        self.title.setObjectName("TitleLabel")
        font = QFont()
        font.setPointSize(24)
        font.setBold(True)
        self.title.setFont(font)
        self.title.setAlignment(Qt.AlignCenter)

        # Instruction label
        self.instruction_label = QLabel("Describe a 3D model by speaking or typing")
        self.instruction_label.setAlignment(Qt.AlignCenter)

        self.title.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)
        self.instruction_label.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)

        # Title block
        title_block = QVBoxLayout()
        title_block.setSpacing(2)
        title_block.setContentsMargins(0, 0, 0, 0)
        title_block.addWidget(self.title, alignment=Qt.AlignCenter)
        title_block.addWidget(self.instruction_label, alignment=Qt.AlignCenter)

        # Input Row: Voice + Text
        self.record_btn = QPushButton("")
        self.record_btn.setToolTip("Use your voice to describe the model")
        self.is_recording = False
        self.audio_recorder = AudioRecorder()
        self.record_btn.clicked.connect(self.toggle_recording)

        self.text_input = QLineEdit()
        self.text_input.setPlaceholderText("e.g., 3D model of a dinosaur")
        self.text_input.setMinimumWidth(240)

        self.search_btn = QPushButton("")
        self.search_btn.setToolTip("Search for a model using the typed description")
        self.search_btn.clicked.connect(self.handle_text_input)

        self.text_input.returnPressed.connect(self.handle_text_input)

        input_row_layout = QHBoxLayout()
        input_row_layout.addStretch()
        input_row_layout.addWidget(self.record_btn)
        input_row_layout.addSpacing(10)
        input_row_layout.addWidget(self.text_input)
        input_row_layout.addSpacing(10)
        input_row_layout.addWidget(self.search_btn)
        input_row_layout.addStretch()

        # Mode Toggle: Load or Generate
        self.mode_toggle_layout = QHBoxLayout()
        self.load_btn = QPushButton("Load")
        self.generate_btn = QPushButton("Generate")

        for btn in [self.load_btn, self.generate_btn]:
            btn.setCheckable(True)
            btn.setMinimumWidth(100)

        self.load_btn.setChecked(True)
        self.load_btn.clicked.connect(lambda: self.set_mode("Load"))
        self.generate_btn.clicked.connect(lambda: self.set_mode("generate"))

        self.mode_toggle_layout.addStretch()
        self.mode_toggle_layout.addWidget(self.load_btn)
        self.mode_toggle_layout.addWidget(self.generate_btn)
        self.mode_toggle_layout.addStretch()

        # Model Dropdown
        models_dir = get_models_dir()
        self.model_dropdown = QComboBox()
        models = [
            name for name in os.listdir(models_dir) 
            if name != ".DS_Store"
            and name != "all-MiniLM-L6-v2"
            and name != "TripoSR"
        ]
        self.model_dropdown.addItems(models)
        self.model_dropdown.setFixedWidth(250)

        # --- Settings button (opens config dialog) ---
        self.settings_btn = QPushButton("")
        self.settings_btn.setToolTip("Configure generation settings")
        gear_icon = (os.path.join(get_icons_dir(), "gear.svg"))
        self.settings_btn.setIcon(QIcon(gear_icon))
        self.settings_btn.clicked.connect(self.open_settings_dialog)

        # store per-model settings here
        self.per_model_cfg = {}

        self.model_dropdown_container = QWidget()
        model_layout = QHBoxLayout(self.model_dropdown_container)
        model_layout.setContentsMargins(0, 0, 0, 0)
        model_layout.addStretch()
        model_layout.addWidget(self.model_dropdown)
        model_layout.addSpacing(8)
        model_layout.addWidget(self.settings_btn)
        model_layout.addStretch()
        self.model_dropdown_container.setFixedHeight(40)

        self.model_dropdown.setVisible(False)  # hidden initially
        self.settings_btn.setVisible(False)

        self.model_dropdown.currentTextChanged.connect(
            lambda _: self.message.setText(
                "Using saved settings for this model"
                if self.model_dropdown.currentText() in self.per_model_cfg
                else "Using defaults for this model"
            )
        )

        # Timer
        self.timer_label = QLabel("")
        self.timer_label.setObjectName("TimerLabel")
        self.elapsed_timer = QTimer()
        self.elapsed_timer.timeout.connect(self.update_timer)
        self._start_time = None

        # Save/Delete 3D Model
        self.save_del_btn = QPushButton("")

        # Message
        self.message = QLabel("")
        self.message.setObjectName("MessageLabel")

        # Message, timer, save
        footer_layout = QHBoxLayout()
        footer_layout.addWidget(self.message, 1)
        footer_layout.addStretch()
        footer_layout.addWidget(self.timer_label)
        footer_layout.addStretch()
        footer_layout.addWidget(self.save_del_btn)

        # Viewer/selector setup
        self.viewer = ModelViewer()
        self.selector = ModelSelector()
        self.current_model_path = None

        # Set button icons and sizes
        self.record_btn.setIcon(QIcon(os.path.join(get_icons_dir(), "mic.svg")))
        self.record_btn.setFixedWidth(100)
        self.search_btn.setIcon(QIcon(os.path.join(get_icons_dir(), "search.svg")))
        self.search_btn.setFixedWidth(100)
        self.save_del_btn.setIcon(QIcon(os.path.join(get_icons_dir(), "save.svg")))
        self.save_del_btn.setFixedWidth(100)

        # Main Layout
        layout = QVBoxLayout()
        layout.setContentsMargins(20, 10, 20, 20)
        layout.setSpacing(8)

        # Wrap top controls
        top_section = QVBoxLayout()
        top_section.setSpacing(8)
        top_section.setContentsMargins(0, 0, 0, 0)
        top_section.addLayout(title_block)
        top_section.addLayout(input_row_layout)
        top_section.addLayout(self.mode_toggle_layout)
        top_section.addWidget(self.model_dropdown_container)
        top_section.addLayout(footer_layout)

        top_wrapper = QWidget()
        top_wrapper.setLayout(top_section)
        top_wrapper.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Maximum)

        # Add to main layout
        layout.addWidget(top_wrapper)
        layout.addWidget(self.viewer, stretch=1)

        layout.setStretch(0, 0)  # top_wrapper
        layout.setStretch(1, 1)  # viewer expands

        # Set as central widget
        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)

        # Set default to load
        self.set_mode("Load")

    # Determine whether in generate mode
    def is_generate_mode(self):
        return self.generate_btn.isChecked()

    def set_mode(self, mode):
        is_generate = mode == "generate"
        self.load_btn.setChecked(not is_generate)
        self.generate_btn.setChecked(is_generate)

        # Show model dropdown only when in generate mode
        self.model_dropdown.setVisible(is_generate)
        self.settings_btn.setVisible(is_generate)

        # Safely disconnect signal to prevent duplicates
        with contextlib.suppress(TypeError, RuntimeError):
            self.save_del_btn.clicked.disconnect()

        # Reconfigure save button behavior and appearance
        if is_generate:
            self.save_del_btn.setToolTip("Save 3D Model")
            self.save_del_btn.setIcon(QIcon(os.path.join(get_icons_dir(), "save.svg")))
            self.save_del_btn.clicked.connect(self.handle_save)
        else:
            self.save_del_btn.setToolTip("Delete 3D Model")
            self.save_del_btn.setIcon(QIcon(os.path.join(get_icons_dir(), "rubbish.svg")))
            self.save_del_btn.clicked.connect(self.handle_delete)

    def open_settings_dialog(self):
        model_name = self.model_dropdown.currentText().strip()
        preset = self.per_model_cfg.get(model_name)
        dlg = ConfigDialog(self, model_name, preset=preset)
        if dlg.exec() == QDialog.Accepted:
            cfg = dlg.values()
            # keep whatever user set for this model
            self.per_model_cfg[model_name] = cfg
            self.message.setText("Settings saved.")
        else:
            self.message.setText("Settings unchanged.")

    # Turn recording on and off - need to add spacebar control
    def toggle_recording(self):
        if not self.is_recording:
            self.is_recording = True
            self.instruction_label.setText("Recording... Click again to stop.")
            self.record_btn.setText("Stop")
            self.record_btn.setIcon(QIcon())
            self.audio_recorder.start()
        else:
            self.is_recording = False
            self.instruction_label.setText("Describe a 3D model by speaking or typing")
            self.record_btn.setText("")
            self.record_btn.setIcon(QIcon(os.path.join(get_icons_dir(), "mic.svg")))
            self.audio_recorder.stop()

            try:
                # Determine base path
                base_path = get_app_dir()
                print("Base path:", base_path)
                self.transcribe_exe = os.path.join(base_path, "transcribe.exe")

                audio_path = self.audio_recorder.filename
                transcribe_input = {"audio_path": audio_path}
                print("Audio path:", audio_path)
                print("Transcribe bin:", self.transcribe_exe)
                transcribe_output = Pipeline.run_stage(self.transcribe_exe, transcribe_input)
                text = transcribe_output.get("transcription")

                if not text:
                    self.message.setText("Transcription failed.")
                    return

                self.message.setText(text)
                if self.is_generate_mode():
                    self.generate_model(text)
                else:
                    self.load_model_from_text(text)

            except Exception as e:
                self.message.setText("Error processing audio.")
                print("[ERROR]", e)

    # Use spacebar to start/stop recording
    def keyPressEvent(self, event):
        # Ignore spacebar if typing in the text input
        if self.text_input.hasFocus():
            return super().keyPressEvent(event)

        if event.key() == Qt.Key_Space:
            self.toggle_recording()
        else:
            super().keyPressEvent(event)

    # text input
    def handle_text_input(self):
        text = self.text_input.text().strip()
        if not text:
            self.message.setText("Please type something first.")
            return

        if self.is_generate_mode():
            self.generate_model(text)
        else:
            self.load_model_from_text(text)

    # Load from text
    def load_model_from_text(self, text):
        model_file, score = self.selector.get_best_match(text)
        print("Model file:", model_file)
        if model_file:
            # self.message.setText(f"{text} (matched: {model_file}, score={score:.2f})")
            self.viewer.load_model(model_file)
            self.current_model_path = model_file
            self.message.setText(text)
        else:
            self.message.setText(f"{text} (no model match)")

    # Model generation
    def generate_model(self, text):
        self._start_time = time.time()
        self.elapsed_timer.start(100)

        try:
            model_name = self.model_dropdown.currentText().strip()
            print("Model name: ", model_name)

            # Use saved settings if available; otherwise start from model defaults
            cfg = dict(defaults_for(model_name))
            cfg.update(self.per_model_cfg.get(model_name, {}))

            pipe = Pipeline()
            result = pipe.run_pipeline(text, model_name, cfg)

            self.message.setText(f"Model for: {result['text']}")
            print("Model path/name:", result['model'])
            self.viewer.load_model(result['model'])
            self.current_model_path = result['model']

            total_time = time.time() - self._start_time
            self.timer_label.setText(f"Total time: {total_time:.2f} seconds")
        except Exception as e:
            self.message.setText("Pipeline failed")
            self.timer_label.setText("")
            print("[ERROR]", e)
        finally:
            self.elapsed_timer.stop()

    # timer for model generation
    def update_timer(self):
        if self._start_time:
            elapsed = time.time() - self._start_time
            self.timer_label.setText(f"Elapsed time: {elapsed:.1f}s")

    # Save a generated model
    def handle_save(self):
        print("[DEBUG] current_model_path:", self.current_model_path)

        if not self.current_model_path:
            self.message.setText("No model to save.")
            return

        if not os.path.isfile(self.current_model_path):
            print("[DEBUG] File does not exist:", self.current_model_path)
            self.message.setText("No model to save. (File does not exist)")
            return

        filename, ok = QInputDialog.getText(self, "Save Model", "Enter filename (without extension):")
        if not ok or not filename.strip():
            self.message.setText("Save canceled: No filename entered.")
            return

        filename = filename.strip()
        if not filename.lower().endswith(".obj"):
            filename += ".obj"

        try:
            download_dir = os.path.join(get_viewer_assets(), "3d_assets")
            os.makedirs(download_dir, exist_ok=True)

            dest_path = os.path.join(download_dir, filename)
            print("[DEBUG] dest path:", dest_path)

            print("[DEBUG] Source exists before copy:", os.path.exists(self.current_model_path))

            shutil.copy(self.current_model_path, dest_path)

            print("[DEBUG] Destination exists after copy:", os.path.exists(dest_path))

            description, ok = QInputDialog.getText(self, "Model Description", "Enter description for the uploaded model:")
            if ok and description.strip():
                self.selector.add_model(filename, description.strip())
                self.message.setText(f"Saved: {filename}")
            else:
                self.message.setText("Save canceled: No description entered.")

        except Exception as e:
            self.message.setText(f"Error saving file: {str(e)}")

    # Delete a loaded model
    def handle_delete(self):
        if not self.current_model_path or not os.path.isfile(self.current_model_path):
            self.message.setText("No model loaded to delete.")
            return

        try:
            filename = os.path.basename(self.current_model_path)

            os.remove(self.current_model_path)
            self.selector.remove_model(filename)

            self.viewer.clear_model()
            self.current_model_path = None
            self.message.setText(f"Deleted: {filename}")
        except Exception as e:
            self.message.setText(f"Error deleting file: {str(e)}")

def load_stylesheet(filename):
    with open(filename, "r") as f:
        return f.read()


if __name__ == '__main__':
    multiprocessing.freeze_support()
    app = QApplication(sys.argv)
    style_sheet = os.path.join(get_data_dir(), "style.qss")
    app.setStyleSheet(load_stylesheet(style_sheet))
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
