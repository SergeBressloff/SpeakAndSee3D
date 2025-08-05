from PySide6.QtWidgets import (
    QApplication, 
    QMainWindow, 
    QPushButton, 
    QVBoxLayout, 
    QWidget, 
    QLabel, 
    QProgressBar,
    QComboBox
)
from PySide6.QtCore import QTimer
from pipeline import Pipeline
from audio_recorder import record_audio
from model_viewer import ModelViewer
from utils import resource_path, get_writable_viewer_assets
import os, sys, multiprocessing, shutil
import time

VIEWER_ASSETS_DIR = get_writable_viewer_assets()

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Speak and See 3D")
        self.setGeometry(200, 200, 400, 300)

        self.transcription_label = QLabel("Press Speak to see in 3D...")
        self.record_btn = QPushButton("Speak")

        self.model_dropdown = QComboBox()
        self.model_dropdown.addItems([
            "onnx-stable-diffusion-2-1",
            "flux_1_schnell",
            "LCM_Dreamshaper_v7"
        ])

        self.timer_label = QLabel("")
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 0)  # Indeterminate progress
        self.progress_bar.setVisible(False)
        self.elapsed_timer = QTimer()
        self.elapsed_timer.timeout.connect(self.update_timer)
        self._start_time = None  # Store start time

        self.record_btn.clicked.connect(self.handle_record)

        # Placeholder path
        self.viewer = ModelViewer()

        layout = QVBoxLayout()
        layout.addWidget(self.transcription_label)
        layout.addWidget(self.record_btn)
        layout.addWidget(self.model_dropdown)
        layout.addWidget(self.timer_label)
        layout.addWidget(self.progress_bar)
        layout.addWidget(self.viewer)
        layout.setStretch(0, 0)  # transcription_label
        layout.setStretch(1, 0)  # record_btn
        layout.setStretch(2, 0)  # model_dropdown
        layout.setStretch(3, 1)  # viewer gets all extra space

        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)

    def handle_record(self):
        self.transcription_label.setText("Recording...")
        record_audio()
        audio_path = resource_path("audio\\recording.wav")
        print("Audio path: ", audio_path)

        self.transcription_label.setText("Processing...")

        # Start timer and progress
        self._start_time = time.time()
        self.elapsed_timer.start(100)
        self.progress_bar.setVisible(True)

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
            self.progress_bar.setVisible(False)

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
