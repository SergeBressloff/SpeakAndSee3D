from PySide6.QtWebEngineWidgets import QWebEngineView
from PySide6.QtCore import QUrl, QFileInfo
from utils import get_viewer_assets
import os

class ModelViewer(QWebEngineView):
    def __init__(self, model_path=None, parent=None):
        super().__init__(parent)

        viewer_assets_dir = get_viewer_assets()

        local_html_path = os.path.join(viewer_assets_dir, "index.html")
        if not os.path.exists(local_html_path):
            raise FileNotFoundError("Missing HTML viewer at: " + local_html_path)

        # Pass model path as query param or inject via JS if needed
        self.load(QUrl.fromLocalFile(local_html_path))


    # model_viewer.py (add inside ModelViewer class)
    def load_model(self, model_filename):
        if not os.path.isfile(model_filename):
            print(f"Model file does not exist: {model_filename}")
            return
        model_url = QUrl.fromLocalFile(model_filename).toString()
        js_code = f"""
        if (typeof loadModel === 'function') {{
            loadModel('{model_url}');
        }} else {{
            console.error('loadModel function not found in page');
        }}
        """
        self.page().runJavaScript(js_code)

    def clear_model(self):
        js_code = """
        if (typeof clearModel === 'function') {
            clearModel();
        } else {
            console.error('clearModel function not found in page');
        }
        """
        self.page().runJavaScript(js_code)