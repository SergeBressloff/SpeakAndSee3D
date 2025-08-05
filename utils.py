import os, sys

def resource_path(relative_path):
    """
    Get absolute path to resource, whether bundled by PyInstaller or run in dev.
    """
    if hasattr(sys, '_MEIPASS'):
        # Running from PyInstaller bundle
        base_path = sys._MEIPASS
    else:
        # Running in development
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

def get_writable_viewer_assets():
    if getattr(sys, 'frozen', False):
        writable_dir = os.path.join(os.path.expanduser("~"), ".speak_and_see", "viewer_assets")
        if not os.path.exists(writable_dir):
            src = os.path.join(sys._MEIPASS, "viewer_assets")
            shutil.copytree(src, writable_dir)
        return writable_dir
    else:
        # In dev mode, just use the local folder
        return os.path.abspath("viewer_assets")