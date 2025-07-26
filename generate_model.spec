# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['generate_model.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('stable-point-aware-3d/*', 'stable-point-aware-3d'),
        ('venvs/spa3d_env/*', 'venvs/spa3d_env'),
    ],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='generate_model',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
