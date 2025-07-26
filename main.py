from PySide6.QtWidgets import QApplication, QMainWindow, QPushButton, QVBoxLayout, QWidget, QLabel, QProgressBar
from PySide6.QtCore import QTimer
from whisper_runner import transcribe_whisper
from audio_recorder import record_audio
from model_viewer import ModelViewer
from utils import resource_path
from model_generator import generate_3d_model
import os, sys, multiprocessing
import time

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Speak and See 3D")
        self.setGeometry(200, 200, 400, 300)

        self.transcription_label = QLabel("Press Speak to see in 3D...")
        self.record_btn = QPushButton("Speak")

        self.timer_label = QLabel("")
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 0)  # Indeterminate progress
        self.progress_bar.setVisible(False)
        self.elapsed_timer = QTimer()
        self.elapsed_timer.timeout.connect(self.update_timer)
        self._start_time = None  # Store start time

        self.record_btn.clicked.connect(self.handle_record)

        # Placeholder path
        self.viewer = ModelViewer(resource_path("viewer_assets/lion.glb"))

        layout = QVBoxLayout()
        layout.addWidget(self.transcription_label)
        layout.addWidget(self.record_btn)
        layout.addWidget(self.timer_label)
        layout.addWidget(self.progress_bar)
        layout.addWidget(self.viewer)
        layout.setStretch(0, 0)  # transcription_label
        layout.setStretch(1, 0)  # record_btn
        layout.setStretch(2, 1)  # viewer gets all extra space

        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)

    def handle_record(self):
        self.transcription_label.setText("Recording...")
        record_audio()

        self.transcription_label.setText("Transcribing...")
        text = transcribe_whisper()

        if not text:
            self.transcription_label.setText("Transcription failed")
            return

        self.transcription_label.setText(f"Generating 3D model from: {text}")

        # Start timer and progress
        self._start_time = time.time()
        self.elapsed_timer.start(100)
        self.progress_bar.setVisible(True)

        model_path = generate_3d_model(prompt=text)

        # Stop timer/progress
        self.elapsed_timer.stop()
        self.progress_bar.setVisible(False)

        if model_path:
            self.viewer.load_model(model_path)
            total_time = time.time() - self._start_time
            self.transcription_label.setText(f"Model generated for: {text}")
            self.timer_label.setText(f"Total time: {total_time:.2f} seconds")
        else:
            self.transcription_label.setText("Model generation failed")
            self.timer_label.setText("")

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
