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
    QFrame
)
from PySide6.QtCore import Qt, QTimer, QPropertyAnimation, QRect
from PySide6.QtGui import QFont, QIcon
from pipeline import Pipeline
from audio_recorder import AudioRecorder
from model_viewer import ModelViewer
from model_selector import ModelSelector
from utils import resource_path, get_writable_viewer_assets
import os, sys, multiprocessing, shutil
import time

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
        self.model_dropdown = QComboBox()
        self.model_dropdown.addItems([
            "onnx-stable-diffusion-2-1",
            "flux_1_schnell",
            "LCM_Dreamshaper_v7"
        ])
        self.model_dropdown.setFixedWidth(250)

        self.model_dropdown_container = QWidget()
        model_layout = QHBoxLayout(self.model_dropdown_container)
        model_layout.setContentsMargins(0, 0, 0, 0)
        model_layout.addWidget(self.model_dropdown)
        self.model_dropdown_container.setFixedHeight(40)

        self.model_dropdown.setVisible(False)  # hidden initially

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

        # Set button icons and sizes
        self.record_btn.setIcon(QIcon(resource_path(os.path.join("icons", "mic.svg"))))
        self.record_btn.setFixedWidth(100)
        self.search_btn.setIcon(QIcon(resource_path(os.path.join("icons", "search.svg"))))
        self.search_btn.setFixedWidth(100)
        self.save_del_btn.setIcon(QIcon(resource_path(os.path.join("icons", "save.svg"))))
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

        # Reconfigure save button behavior and appearance
        if is_generate:
            self.save_del_btn.setToolTip("Save 3D Model")
            self.save_del_btn.setIcon(QIcon(resource_path(os.path.join("icons", "save.svg"))))
            self.save_del_btn.clicked.connect(self.handle_save)
        else:
            self.save_del_btn.setToolTip("Delete 3D Model")
            self.save_del_btn.setIcon(QIcon(resource_path(os.path.join("icons", "rubbish.svg"))))
            self.save_del_btn.clicked.connect(self.handle_delete)

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
            self.record_btn.setIcon(QIcon(resource_path(os.path.join("icons", "mic.svg"))))
            self.audio_recorder.stop()

            try:
                # Determine base path
                # Need to go through all files and use resource path for this
                if getattr(sys, 'frozen', False):
                    base_path = os.path.dirname(sys.executable)
                else:
                    cwd = os.path.dirname(os.path.abspath(__file__))
                    base_path = os.path.join(cwd, "bin")
                print("Base path:", base_path)

                self.TRANSCRIBE_BIN = os.path.join(base_path, "transcribe.exe")

                audio_path = self.audio_recorder.filename
                transcribe_input = {"audio_path": audio_path}
                print("Audio path:", audio_path)
                print("Transcribe bin:", self.TRANSCRIBE_BIN)
                transcribe_output = Pipeline.run_stage(self.TRANSCRIBE_BIN, transcribe_input)
                text = transcribe_output.get("transcription")

                if not text:
                    self.message.setText("Transcription failed.")
                    return

                # If generate, after recording, it shows the user what they have recorded, and 
                # then asks them if they want to proceed with generation.

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
            self.message.setText(text)
        else:
            self.message.setText(f"{text} (no model match)")

    # Model generation
    def generate_model(self, text):
        self._start_time = time.time()
        self.elapsed_timer.start(100)

        try:
            pipe = Pipeline()
            model_name = self.model_dropdown.currentText().strip()
            print("Model name: ", model_name)
            result = pipe.run_pipeline(text, model_name)

            self.message.setText(f"Model for: {result['text']}")
            print("Model path/name:", result['model'])
            self.viewer.load_model(result['model'])

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

    # Need to check and complete!
    def handle_save(self):
        filename, ok = QInputDialog.getText(self, "Save Model", "Enter filename (without extension):")
        if not ok or not filename.strip():
            self.message.setText("Save canceled: No filename entered.")
            return

        filename = filename.strip()
        if not filename.lower().endswith(".obj"):
            filename += ".obj"

        # File path needs to be model currently in viewer
        file_path = ''

        # Copy file to viewer_assets directory
        try:
            download_dir = os.path.join(get_writable_viewer_assets(), "3d_models")
            os.makedirs(download_dir, exist_ok=True)

            dest_path = os.path.join(download_dir, filename)
            with open(file_path, "rb") as src, open(dest_path, "wb") as dst:
                dst.write(src.read())
        except Exception as e:
            self.message.setText(f"Error saving file: {str(e)}")
            return

        # Ask user for description
        description, ok = QInputDialog.getText(self, "Model Description", "Enter description for the uploaded model:")
        if ok and description.strip():
            self.selector.add_model(filename, description.strip())
            self.message.setText(f"Saved: {filename}")
        else:
            self.message.setText("Save canceled: No description entered.")

    # Need to check and complete!
    def handle_delete(self):
        filename, ok = QInputDialog.getText(self, "Delete Model", "Enter filename to delete (without extension):")
        if not ok or not filename.strip():
            self.message.setText("Delete canceled.")
            return

        filename = filename.strip()
        if not filename.lower().endswith(".obj"):
            filename += ".obj"

        try:
            file_path = os.path.join(get_writable_viewer_assets(), "3d_models", filename)
            if os.path.exists(file_path):
                os.remove(file_path)
                self.selector.remove_model(filename)
                self.message.setText(f"Deleted: {filename}")
            else:
                self.message.setText("File not found.")
        except Exception as e:
            self.message.setText(f"Error deleting file: {str(e)}")

def load_stylesheet(filename):
    with open(filename, "r") as f:
        return f.read()


if __name__ == '__main__':
    multiprocessing.freeze_support()
    app = QApplication(sys.argv)
    app.setStyleSheet(load_stylesheet("style.qss"))
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
