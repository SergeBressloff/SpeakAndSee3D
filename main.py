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
from utils import resource_path
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

        # Message & Viewer
        self.message = QLabel("")
        self.viewer = ModelViewer()
        self.selector = ModelSelector()

        # Set button sizes
        self.record_btn.setFixedWidth(100)
        self.search_btn.setFixedWidth(100)
        self.upload_btn.setFixedWidth(140)

        # === Main Layout ===
        layout = QVBoxLayout()
        layout.addWidget(self.title)
        layout.addWidget(self.transcription_label)
        layout.addLayout(input_row_layout)
        layout.addWidget(self.upload_btn)
        layout.addWidget(self.message)
        layout.addWidget(self.viewer)

        # Stretching behavior
        layout.setStretch(0, 0)  # title
        layout.setStretch(1, 0)  # instructions
        layout.setStretch(2, 0)  # input row
        layout.setStretch(3, 0)  # model dropdown
        layout.setStretch(4, 0)  # timer
        layout.setStretch(5, 0)  # message
        layout.setStretch(6, 1)  # viewer

        # Set as central widget
        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)

    def handle_record(self):
        self.transcription_label.setText("Recording...")
        record_audio()
        audio_path = resource_path("audio\\recording.wav")
        print("Audio path: ", audio_path)

        self.transcription_label.setText("Processing...")

        # Start timer
        self._start_time = time.time()
        self.elapsed_timer.start(100)

        try:
            pipe = Pipeline()
            model_name = self.model_dropdown.currentText().strip()
            print("Model name: ", model_name)
            result = pipe.run_pipeline(audio_path, model_name)

            self.transcription_label.setText(f"Model for: {result['text']}")
            self.viewer.load_model(result['model'])

            total_time = time.time() - self._start_time
            self.timer_label.setText(f"Total time: {total_time:.2f} seconds")
        except Exception as e:
            self.transcription_label.setText("Pipeline failed")
            self.timer_label.setText("")
            print("[ERROR]", e)
        finally:
            self.elapsed_timer.stop()

    def update_timer(self):
        if self._start_time:
            elapsed = time.time() - self._start_time
            self.timer_label.setText(f"Elapsed time: {elapsed:.1f}s")


if __name__ == '__main__':
    multiprocessing.freeze_support()
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
