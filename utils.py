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