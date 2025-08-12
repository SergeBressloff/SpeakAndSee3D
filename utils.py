import os, sys, shutil,builtins

def get_app_dir():
    if "__compiled__" in globals():
        abs_pth = os.path.abspath(sys.argv[0])
        app_dir = os.path.dirname(abs_pth)
    else:
        app_dir = os.path.dirname(os.path.abspath(__file__))
    return app_dir

def get_models_dir():
    """
    Get absolute path to models dir, whether bundled by Nuitka or run in dev.
    """
    if "__compiled__" in globals():
        app_dir = get_app_dir()
        models_dir = os.path.join(app_dir, "models")
    else:
        base_path = os.path.dirname(os.path.abspath(__file__))
        models_dir = os.path.join(base_path, "models")
    return models_dir

def get_data_dir():
    if "__compiled__" in globals():
        app_dir = get_app_dir()
        data_dir = os.path.join(app_dir, "data")
        return data_dir
    else:
        base_path = os.path.dirname(os.path.abspath(__file__))
        return base_path

def get_viewer_assets():
    """
    Get absolute path to viewer_assets, whether bundled by Nuitka or run in dev.
    """
    if "__compiled__" in globals():
        app_dir = get_app_dir()
        viewer_assets = os.path.join(app_dir, "data", "viewer_assets")
    else:
        base_path = os.path.dirname(os.path.abspath(__file__))
        viewer_assets = os.path.join(base_path, "viewer_assets")
    return viewer_assets

def get_icons_dir():
    if "__compiled__" in globals():
        app_dir = get_app_dir()
        icons_dir = os.path.join(app_dir, "data", "icons")
    else:
        base_path = os.path.dirname(os.path.abspath(__file__))
        icons_dir = os.path.join(base_path, "icons")
    return icons_dir

def get_audio_dir():
    if "__compiled__" in globals():
        app_dir = get_app_dir()
        audio_dir = os.path.join(app_dir, "data", "audio")
    else:
        base_path = os.path.dirname(os.path.abspath(__file__))
        audio_dir = os.path.join(base_path, "audio")
    return audio_dir