# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['generate_model.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('stable-point-aware-3d/run.py', 'stable-point-aware-3d'),
        ('stable-point-aware-3d/config.yaml', 'stable-point-aware-3d'),
        ('stable-point-aware-3d/model.safetensors', 'stable-point-aware-3d'),
    ],
    hiddenimports=[
        'spar3d.models.mesh.quad_remesh', 
        'spar3d.models.mesh.triangle_remesh',
        'transparent_background',
        'PIL.Image',
    ],
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
    [],
    exclude_binaries=True,
    name='generate_model',
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
    name='generate_model',
)
