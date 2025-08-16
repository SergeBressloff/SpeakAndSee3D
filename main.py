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
    QDoubleSpinBox,
    QTextBrowser,
    QMessageBox,
    QGridLayout
)
from PySide6.QtCore import Qt, QTimer, QPropertyAnimation, QRect, QEvent, QUrl
from PySide6.QtGui import QFont, QIcon
from pipeline import Pipeline
from audio_recorder import AudioRecorder
from model_viewer import ModelViewer
from model_selector import ModelSelector
from utils import get_app_dir, get_data_dir, get_viewer_assets, get_models_dir, get_icons_dir
import os, sys, multiprocessing, shutil
import time
import contextlib
import json

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
    # defaults
    return {"steps": 20, "guidance_scale": 7.5, "seed": 0}


class ConfigDialog(QDialog):
    def __init__(self, parent, model_name: str, preset: dict | None = None):
        super().__init__(parent)
        self.setWindowTitle("Diffusion Configuration")
        self.model_name = model_name
        self._is_flux = is_flux(model_name)

        # load model defaults, then overlay preset if provided
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
        self.setGeometry(800, 600, 800, 700)

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

        # Help, About + Theme Buttons
        self.help_btn = QPushButton("")
        self.help_btn.setToolTip("Help / Shortcuts")
        self.help_btn.setIcon(QIcon(os.path.join(get_icons_dir(), "help.svg")))
        self.help_btn.clicked.connect(self.show_help_dialog)

        self.about_btn = QPushButton("")
        self.about_btn.setToolTip("About Speak & See 3D")
        self.about_btn.setIcon(QIcon(os.path.join(get_icons_dir(), "info.svg")))
        self.about_btn.clicked.connect(self.show_about_dialog)

        self.theme_btn = QPushButton("")
        self.theme_btn.setToolTip("Toggle viewer theme (Dark/Light)")
        self.theme_btn.setIcon(QIcon(os.path.join(get_icons_dir(), "moon.svg")))
        self.theme_btn.clicked.connect(self.toggle_theme)
        self.viewer_theme = "dark"

        # Button bar
        button_bar = QWidget()
        bbx = QHBoxLayout(button_bar)
        bbx.setContentsMargins(0, 0, 0, 0)
        bbx.setSpacing(6)
        bbx.addWidget(self.help_btn)
        bbx.addWidget(self.about_btn)
        bbx.addWidget(self.theme_btn)
        button_bar.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)

        # Create a left balancer with same width as the button bar,
        # so the title stays visually centered.
        left_balancer = QWidget()
        left_balancer.setFixedWidth(button_bar.sizeHint().width())
        left_balancer.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)

        # Title block
        title_row = QHBoxLayout()
        title_row.setContentsMargins(0, 0, 0, 0)
        title_row.setSpacing(8)
        title_row.addWidget(left_balancer)           # left side weight
        title_row.addWidget(self.title, 1)           # stretch the title
        title_row.addWidget(button_bar)              # right buttons

        title_block = QVBoxLayout()
        title_block.setSpacing(2)
        title_block.setContentsMargins(0, 0, 0, 0)
        title_block.addLayout(title_row)
        title_block.addWidget(self.instruction_label, alignment=Qt.AlignCenter)

        # Input Row: Voice + Text
        self.record_btn = QPushButton("")
        self.record_btn.setToolTip("Use your voice to describe a 3D model")
        self.record_btn.setIcon(QIcon(os.path.join(get_icons_dir(), "mic.svg")))
        self.record_btn.setFixedWidth(100)
        self.is_recording = False
        self.audio_recorder = AudioRecorder()
        self.record_btn.clicked.connect(self.toggle_recording)

        self.text_input = QLineEdit()
        self.text_input.setPlaceholderText("e.g., 3D model of a dinosaur")
        self.text_input.setMinimumWidth(240)

        self.search_btn = QPushButton("")
        self.search_btn.setToolTip("Search for a model using the typed description")
        self.search_btn.setIcon(QIcon(os.path.join(get_icons_dir(), "search.svg")))
        self.search_btn.setFixedWidth(100)
        self.search_btn.clicked.connect(self.handle_text_input)

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
        self.load_btn.setToolTip("Load a saved 3D model")
        self.generate_btn = QPushButton("Generate")
        self.generate_btn.setToolTip("Generate a new 3D model")

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
            # Exclude non-diffusion models
            if name != ".DS_Store"
            and name != "all-MiniLM-L6-v2"
            and name != "TripoSR"
        ]
        self.model_dropdown.addItems(models)
        self.model_dropdown.setMinimumWidth(240)

        # Settings button (opens config dialog)
        self.settings_btn = QPushButton("")
        self.settings_btn.setToolTip("Configure generation settings")
        gear_icon = (os.path.join(get_icons_dir(), "gear.svg"))
        self.settings_btn.setIcon(QIcon(gear_icon))
        self.settings_btn.clicked.connect(self.open_settings_dialog)

        # store per-model settings
        self.per_model_cfg = {}

        # model dropdown and config
        self.model_dropdown_container = QWidget()
        self.model_dropdown.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.model_dropdown_container.setFixedHeight(40)

        outer = QHBoxLayout(self.model_dropdown_container)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)
        outer.addStretch()

        row = QWidget()
        row_l = QHBoxLayout(row)
        row_l.setContentsMargins(0, 0, 0, 0)
        row_l.setSpacing(0)

        # Make some left padding to match the size of the settings button
        left_pad = QWidget()
        left_pad.setFixedWidth(self.settings_btn.sizeHint().width())
        row_l.addWidget(left_pad)
        row_l.addWidget(self.model_dropdown)
        row_l.addSpacing(8)
        row_l.addWidget(self.settings_btn)

        outer.addWidget(row, 0, Qt.AlignHCenter)
        outer.addStretch()

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

        # Import 3D model
        self.import_btn = QPushButton("")
        self.import_btn.setToolTip("Import a 3D model")
        self.import_btn.setIcon(QIcon(os.path.join(get_icons_dir(), "import.svg")))
        self.import_btn.clicked.connect(self.handle_import)

        self.show_models_btn = QPushButton("")
        self.show_models_btn.setToolTip("View names and descriptions of saved 3D models")
        self.show_models_btn.setIcon(QIcon(os.path.join(get_icons_dir(), "list.svg")))
        self.show_models_btn.clicked.connect(self.show_models_dialog)

        # Button bar
        button_bar_2 = QWidget()
        bbx = QHBoxLayout(button_bar_2)
        bbx.setContentsMargins(0, 0, 0, 0)
        bbx.setSpacing(6)
        bbx.addWidget(self.import_btn)
        bbx.addWidget(self.show_models_btn)
        bbx.addWidget(self.save_del_btn)
        button_bar_2.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)

        # Message
        self.message = QLabel("")
        self.message.setObjectName("MessageLabel")

        # Message, timer, save
        footer_layout = QHBoxLayout()
        footer_layout.addWidget(self.message, 1)
        footer_layout.addStretch()
        footer_layout.addWidget(self.timer_label)
        footer_layout.addStretch()
        footer_layout.addWidget(button_bar_2)

        # Viewer/selector setup
        self.viewer = ModelViewer()
        self.selector = ModelSelector()
        self.current_model_path = None

        # Prevent buttons from grabbing keyboard focus so Space/Enter won't click them
        for btn in [
            self.record_btn, 
            self.search_btn, 
            self.load_btn, 
            self.generate_btn, 
            self.settings_btn, 
            self.save_del_btn, 
            self.help_btn, 
            self.about_btn,
            self.theme_btn,
            self.import_btn,
            self.show_models_btn
            ]:
            btn.setFocusPolicy(Qt.NoFocus)

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
        layout.setStretch(1, 1)  # viewer takes rest of space

        # Set as central widget
        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)

        # Set default to load
        self.set_mode("Load")

        # Set up event filters
        self.installEventFilter(self)
        self.centralWidget().installEventFilter(self)
        self.viewer.installEventFilter(self)

        # Let non-edit areas take focus when clicked
        self.viewer.setFocusPolicy(Qt.ClickFocus)        # viewer can grab focus on click
        self.model_dropdown.setFocusPolicy(Qt.StrongFocus)  # dropdown focusable so can cycle through models
        self.centralWidget().setFocusPolicy(Qt.ClickFocus)  # allow clicks on empty areas to clear focus

        self.text_input.clearFocus() # stop text input from taking focus on app launch
        self.setFocus(Qt.OtherFocusReason) # give the main window focus

    # Determine whether in generate mode
    def is_generate_mode(self):
        return self.generate_btn.isChecked()

    # change functionality depending on mode
    def set_mode(self, mode):
        is_generate = mode == "generate"
        self.load_btn.setChecked(not is_generate)
        self.generate_btn.setChecked(is_generate)

        # Show model dropdown only when in generate mode
        self.model_dropdown.setVisible(is_generate)
        self.settings_btn.setVisible(is_generate)

        # Safely disconnect signal from save/delete button
        with contextlib.suppress(TypeError, RuntimeError):
            self.save_del_btn.clicked.disconnect()

        # Switch between save and delete depending on mode
        if is_generate:
            self.save_del_btn.setToolTip("Save 3D Model")
            self.save_del_btn.setIcon(QIcon(os.path.join(get_icons_dir(), "save.svg")))
            self.save_del_btn.clicked.connect(self.handle_save)
        else:
            self.save_del_btn.setToolTip("Delete 3D Model")
            self.save_del_btn.setIcon(QIcon(os.path.join(get_icons_dir(), "rubbish.svg")))
            self.save_del_btn.clicked.connect(self.handle_delete)

    # switch theme
    def toggle_theme(self):
        if self.viewer_theme == "dark":
            self.viewer_theme = "light"
            self.theme_btn.setIcon(QIcon(os.path.join(get_icons_dir(), "sun.svg")))
        else:
            self.viewer_theme = "dark"
            self.theme_btn.setIcon(QIcon(os.path.join(get_icons_dir(), "moon.svg")))
        
        self.viewer.set_theme(self.viewer_theme)

    # About Dialog
    def show_about_dialog(self):
        about_text = (
            "Developed by: Serge Bressloff\n"
            "Supervised by: Prof. Dean Mohamedally\n"
            "In collaboration with: Intel Corp and Cisco\n"
            "University College London (c) 2025+\n"
            "Published by MotionInput Games Ltd."
        )
        QMessageBox.about(self, "About Speak & See 3D", about_text)

    # Help dialog
    def show_help_dialog(self):
        dlg = QDialog(self)
        dlg.setWindowTitle("Help — Speak & See 3D")
        dlg.resize(600, 700)

        v = QVBoxLayout(dlg)
        browser = QTextBrowser(dlg)

        # Try load an external help page from your data dir
        help_path = os.path.join(get_data_dir(), "help.html")
        if os.path.exists(help_path):
            browser.setSource(QUrl.fromLocalFile(help_path))
        else:
            print("[ERROR] Help file has been removed from the data directory.")

        v.addWidget(browser)

        buttons = QDialogButtonBox(QDialogButtonBox.Close, parent=dlg)
        buttons.rejected.connect(dlg.reject)  # Close
        v.addWidget(buttons)

        dlg.exec()

    # settings dialog. Shows defaults unless user has changed them
    def open_settings_dialog(self):
        model_name = self.model_dropdown.currentText().strip()
        preset = self.per_model_cfg.get(model_name)
        dlg = ConfigDialog(self, model_name, preset=preset)
        if dlg.exec() == QDialog.Accepted:
            cfg = dlg.values()
            self.per_model_cfg[model_name] = cfg # keep whatever user set for this model
            self.message.setText("Settings saved.")
        else:
            self.message.setText("Settings unchanged.")

    # Keyboard shortcuts
    def eventFilter(self, obj, event):
        if event.type() == QEvent.MouseButtonPress:
            gp = event.globalPosition().toPoint() # Which widget is under the mouse?
            w = QApplication.widgetAt(gp)
            if w and w is not self.text_input and not self.text_input.isAncestorOf(w):
                self.text_input.clearFocus()
                # If the target can take focus, give it focus so caret visibly leaves the line edit
                if w.focusPolicy() != Qt.NoFocus:
                    w.setFocus(Qt.MouseFocusReason)
            return False  # keep normal click behavior

        if event.type() != QEvent.KeyPress:
            return super().eventFilter(obj, event)

        key = event.key()
        mods = event.modifiers()

        # typing in the text field?
        typing = self.text_input.hasFocus()

        # --- SPACE: toggle recording (unless actively typing) ---
        if not typing and key == Qt.Key_Space:
            self.toggle_recording()
            return True

        # --- ENTER/RETURN: trigger search ---
        if typing and key in (Qt.Key_Return, Qt.Key_Enter):
            self.handle_text_input()
            return True

        # --- LEFT/RIGHT: toggle mode (ignore when typing) ---
        if not typing and key in (Qt.Key_Left, Qt.Key_Right):
            if key == Qt.Key_Left:
                self.set_mode("Load")
            else:
                self.set_mode("generate")
            return True

        # --- UP/DOWN: cycle model dropdown (only in Generate mode, ignore while typing) ---
        if not typing and key in (Qt.Key_Up, Qt.Key_Down) and self.is_generate_mode():
            idx = self.model_dropdown.currentIndex()
            count = self.model_dropdown.count()
            if count > 0:
                if key == Qt.Key_Up:
                    idx = (idx - 1) % count
                else:
                    idx = (idx + 1) % count
                self.model_dropdown.setCurrentIndex(idx)
            return True

        # --- 'T' to input text
        if key == Qt.Key_T and not typing:
            self.text_input.setFocus(Qt.ShortcutFocusReason)
            self.text_input.setCursorPosition(len(self.text_input.text())) # puts caret at end
            return True

        # --- ESC to clear focus from the text input ---
        if key == Qt.Key_Escape and typing:
            self.text_input.clearFocus()
            self.setFocus(Qt.OtherFocusReason)  # return focus to main window
            return True

        # --- 'S' to save (only if Save is the active action i.e., Generate mode) ---
        if key == Qt.Key_S and mods == Qt.NoModifier and self.is_generate_mode():
            self.handle_save()
            return True

        # --- 'C' for config (only if config button is visible i.e., Geneate mode) ---
        if key == Qt.Key_C and mods == Qt.NoModifier and self.is_generate_mode():
            self.open_settings_dialog()
            return True

        # --- 'D' to delete (only if Delete is the active action i.e., Load mode) ---
        if key == Qt.Key_D and mods == Qt.NoModifier and not self.is_generate_mode():
            self.handle_delete()
            return True

        # --- F1: open Help ---
        if key == Qt.Key_F1:
            self.show_help_dialog()
            return True

        # --- 'I' to open info/About box ---
        if key == Qt.Key_I and not typing:
            self.show_about_dialog()
            return True

        # --- 'L' to toggle theme (lighting) ---
        if key == Qt.Key_L and not typing:
            self.toggle_theme()
            return True

        # --- 'U' to import (upload) 3D asset ---
        if key == Qt.Key_U and not typing:
            self.handle_import()

        # --- 'V' to view names and descriptions of saved 3D assets ---
        if key == Qt.Key_V and not typing:
            self.show_models_dialog()

        return super().eventFilter(obj, event)

    # Turn recording on and off
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
                base_path = get_app_dir() # Determine base path to main executable
                self.transcribe_exe = os.path.join(base_path, "transcribe.exe") # Transcribe executable next to main executable

                if not os.path.exists(self.transcribe_exe):
                    print("[ERROR] Transcribe executable needs to be in the same folder as the main app.") 

                audio_path = self.audio_recorder.filename
                transcribe_input = {"audio_path": audio_path}
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
            print("Using diffusion model:", model_name)

            # Use saved settings if available; otherwise start from model defaults
            cfg = dict(defaults_for(model_name))
            cfg.update(self.per_model_cfg.get(model_name, {}))

            self.message.setText("Generating 3D model. Please wait...")

            pipe = Pipeline()
            result = pipe.run_pipeline(text, model_name, cfg)

            self.message.setText(f"3D asset for: {result['text']}")
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

        if not self.current_model_path:
            self.message.setText("No model to save.")
            return

        if not os.path.isfile(self.current_model_path):
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
            shutil.copy(self.current_model_path, dest_path)

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

    # Upload a 3D asset
    def handle_import(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select 3D Model File",
            "",
            "3D Model Files (*.glb *.obj);;GLB Files (*.glb);;OBJ Files (*.obj)"
        )

        if file_path and os.path.isfile(file_path):
            filename = os.path.basename(file_path)

            # Copy file to viewer_assets directory
            try:
                upload_dir = os.path.join(get_viewer_assets(), "3d_assets")
                dest_path = os.path.join(upload_dir, filename)
                with open(file_path, "rb") as src, open(dest_path, "wb") as dst:
                    dst.write(src.read())
            except Exception as e:
                self.message.setText(f"Error saving file: {str(e)}")
                return

            # Ask user for description
            description, ok = QInputDialog.getText(self, "Model Description", "Enter description for the uploaded model:")
            if ok and description.strip():
                self.selector.add_model(filename, description.strip())
                self.message.setText(f"Uploaded: {filename}")
                self.viewer.load_model(dest_path)
            else:
                self.message.setText("Upload canceled: No description entered.")
        else:
            self.message.setText("No valid file selected.")

    # load 3D model descriptions from json file
    def load_model_descriptions(self) -> dict:
        try:
            json_path = os.path.join(get_viewer_assets(), "model_descriptions.json")
            if os.path.exists(json_path):
                with open(json_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    if isinstance(data, dict):
                        return data
        except Exception as e:
            print("[WARN] Could not read model_descriptions.json:", e)

    # show names and descriptions of 3D models
    def show_models_dialog(self):
        entries = self.load_model_descriptions()
        if not entries:
            QMessageBox.information(self, "Saved Models", "No saved models found.")
            return

        rows = []
        rows.append("<table style='width:100%; border-collapse:collapse;'>")
        rows.append("<thead><tr>"
                    "<th style='text-align:left; border-bottom:1px solid #888; padding:4px;'>Filename</th>"
                    "<th style='text-align:left; border-bottom:1px solid #888; padding:4px;'>Description</th>"
                    "</tr></thead><tbody>")
        for filename, desc in sorted(entries.items(), key=lambda kv: kv[0].lower()):
            safe_name = self._escape_html(filename)
            safe_desc = self._escape_html(desc) if desc else "<i>(no description)</i>"
            rows.append(
                f"<tr>"
                f"<td style='padding:4px; vertical-align:top;'>{safe_name}</td>"
                f"<td style='padding:4px; vertical-align:top;'>{safe_desc}</td>"
                f"</tr>"
            )
        rows.append("</tbody></table>")
        html = "\n".join(rows)

        dlg = QDialog(self)
        dlg.setWindowTitle("Saved 3D Models")
        dlg.resize(360, 480)

        v = QVBoxLayout(dlg)
        browser = QTextBrowser(dlg)
        browser.setHtml(html)
        v.addWidget(browser)

        buttons = QDialogButtonBox(QDialogButtonBox.Close, parent=dlg)
        buttons.rejected.connect(dlg.reject)
        v.addWidget(buttons)

        dlg.exec()

    def _escape_html(self, s: str) -> str:
        """Very small HTML escaper for filenames/descriptions."""
        return (
            s.replace("&", "&amp;")
                .replace("<", "&lt;")
                .replace(">", "&gt;")
        )


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
