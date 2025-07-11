# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['main.py'],
    pathex=["."],
    binaries=[('whisper.cpp/build/bin/whisper-cli', 'whisper.cpp/build/bin'),],
    datas=[
        ("viewer_assets/*", "viewer_assets"),
        ('whisper.cpp/models/ggml-base.en.bin', 'whisper.cpp/models'),
        ('audio', 'audio'),
        ("venvs/*", "venvs"),
        ("generate_image.py", "."),
        ("generate_model.py", "."),
        ("venvs/flux_env/bin/python", "_internal/venvs/flux_env/bin"),
        ("venvs/spa3d_env/bin/python", "_internal/venvs/spa3d_env/bin"),
        ("stable-point-aware-3d/run.py", "stable-point-aware-3d"),
    ],
    hiddenimports = [
        "PySide6",
        "PySide6.QtWidgets",
        "PySide6.QtGui",
        "PySide6.QtCore",
        "PySide6.QtWebEngineWidgets",
        "PySide6.QtWebEngineCore",
        "PySide6.QtOpenGL",
        "PySide6.QtNetwork",
        "PySide6.QtPrintSupport",
        "PySide6.QtPositioning",
        "shiboken6",
        "sounddevice",
        "_hashlib",
        "_blake2",
        "_sha3",
        "_md5",
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='SpeakAndSee3D',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='SpeakAndSee3D',
)
