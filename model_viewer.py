from PySide6.QtWebEngineWidgets import QWebEngineView
from PySide6.QtCore import QUrl, QFileInfo
from utils import resource_path, get_writable_viewer_assets
import os

class ModelViewer(QWebEngineView):
    def __init__(self, model_path=None, parent=None):
        super().__init__(parent)

        VIEWER_ASSETS_DIR = get_writable_viewer_assets()

        local_html_path = os.path.join(VIEWER_ASSETS_DIR, "index.html")
        if not os.path.exists(local_html_path):
            raise FileNotFoundError("Missing HTML viewer at: " + local_html_path)

        # Pass model path as query param or inject via JS if needed
        self.load(QUrl.fromLocalFile(local_html_path))


    # model_viewer.py (add inside ModelViewer class)
    def load_model(self, model_filename):
        js_code = f"""
        if (typeof loadModel === 'function') {{
            loadModel('{model_filename}');
        }} else {{
            console.error('loadModel function not found in page');
        }}
        """
        self.page().runJavaScript(js_code)
