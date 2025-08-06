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
    QInputDialog
)
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QFont
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
        self.setWindowTitle("Speak and See 3D")
        self.setGeometry(600, 600, 600, 500)

        # Title
        self.title = QLabel("Speak & See 3D")
        font = QFont()
        font.setPointSize(24)
        font.setBold(True)
        self.title.setFont(font)
        self.title.setAlignment(Qt.AlignCenter)

        # Instruction
        self.transcription_label = QLabel("Describe a 3D model by speaking or typing")
        self.transcription_label.setAlignment(Qt.AlignCenter)

        # Input Row: Voice + Text
        self.record_btn = QPushButton("🎙️ Speak")
        self.record_btn.setToolTip("Use your voice to describe the model")
        self.is_recording = False
        self.audio_recorder = AudioRecorder()
        self.record_btn.clicked.connect(self.toggle_recording)

        self.text_input = QLineEdit()
        self.text_input.setPlaceholderText("e.g., 3D model of a dinosaur")
        self.text_input.setMinimumWidth(240)

        self.search_btn = QPushButton("🔍 Search")
        self.search_btn.setToolTip("Search for a model using the typed description")
        self.search_btn.clicked.connect(self.handle_text_input)

        input_row_layout = QHBoxLayout()
        input_row_layout.addWidget(self.record_btn)
        input_row_layout.addSpacing(20)
        input_row_layout.addWidget(self.text_input)
        input_row_layout.addWidget(self.search_btn)
        input_row_layout.addStretch()

        # Mode Toggle: Retrieve or Generate
        self.mode_toggle = QComboBox()
        self.mode_toggle.addItems(["Retrieve", "Generate"])
        self.mode_toggle.setToolTip("Choose whether to retrieve or generate a 3D model")

        # Model Dropdown
        self.model_dropdown = QComboBox()
        self.model_dropdown.addItems([
            "onnx-stable-diffusion-2-1",
            "flux_1_schnell",
            "LCM_Dreamshaper_v7"
        ])

        # Timer
        self.timer_label = QLabel("")
        self.elapsed_timer = QTimer()
        self.elapsed_timer.timeout.connect(self.update_timer)
        self._start_time = None  # Store start time

        # Save Model
        self.save_btn = QPushButton("Save Model")
        self.save_btn.setToolTip("Save 3D Model")
        self.save_btn.clicked.connect(self.handle_save)

        # Message & Viewer
        self.message = QLabel("")
        self.viewer = ModelViewer()
        self.selector = ModelSelector()

        # Set button sizes
        self.record_btn.setFixedWidth(100)
        self.search_btn.setFixedWidth(100)
        self.save_btn.setFixedWidth(140)

        # === Main Layout ===
        layout = QVBoxLayout()
        layout.addWidget(self.title)
        layout.addWidget(self.transcription_label)
        layout.addLayout(input_row_layout)
        layout.addWidget(self.mode_toggle)
        layout.addWidget(self.model_dropdown)
        layout.addWidget(self.timer_label)
        layout.addWidget(self.save_btn)
        layout.addWidget(self.message)
        layout.addWidget(self.viewer)

        # Stretching behavior
        layout.setStretch(0, 0)  # title
        layout.setStretch(1, 0)  # instructions
        layout.setStretch(2, 0)  # input row
        layout.setStretch(3, 0)  # toggle
        layout.setStretch(4, 0)  # model dropdown
        layout.setStretch(5, 0)  # timer
        layout.setStretch(6, 0)  # save model
        layout.setStretch(7, 0)  # message
        layout.setStretch(8, 1)  # viewer

        # Set as central widget
        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)

    # Determine whether in generate mode
    def is_generate_mode(self):
        return self.mode_toggle.currentText().lower() == "generate"

    # Turn recording on and off - need to add spacebar control
    def toggle_recording(self):
        if not self.is_recording:
            self.is_recording = True
            self.transcription_label.setText("Recording... Click again to stop.")
            self.record_btn.setText("Stop")
            self.audio_recorder.start()
        else:
            self.is_recording = False
            self.transcription_label.setText("Press Speak to See in 3D")
            self.record_btn.setText("Speak")
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

    # Retrieve from text
    def load_model_from_text(self, text):
        model_file, score = self.selector.get_best_match(text)
        print("Model file:", model_file)
        if model_file:
            # self.message.setText(f"{text} (matched: {model_file}, score={score:.2f})")
            self.viewer.load_model(model_file)
            self.message.setText(text)
        else:
            self.message.setText(f"{text} (no model match)")

    # generate model!!
    def generate_model(self, text):
        self._start_time = time.time()
        self.elapsed_timer.start(100)

        try:
            pipe = Pipeline()
            model_name = self.model_dropdown.currentText().strip()
            print("Model name: ", model_name)
            result = pipe.run_pipeline(text, model_name)

            self.transcription_label.setText(f"Model for: {result['text']}")
            print("Model path/name:", result['model'])
            self.viewer.load_model(result['model'])

            total_time = time.time() - self._start_time
            self.timer_label.setText(f"Total time: {total_time:.2f} seconds")
        except Exception as e:
            self.transcription_label.setText("Pipeline failed")
            self.timer_label.setText("")
            print("[ERROR]", e)
        finally:
            self.elapsed_timer.stop()

    # timer for model generation
    def update_timer(self):
        if self._start_time:
            elapsed = time.time() - self._start_time
            self.timer_label.setText(f"Elapsed time: {elapsed:.1f}s")

    # Only want this to be an option when a model has been generated, not retrieved
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


if __name__ == '__main__':
    multiprocessing.freeze_support()
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
