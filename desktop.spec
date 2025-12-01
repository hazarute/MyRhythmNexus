# -*- mode: python ; coding: utf-8 -*-

import os
import sys

# Add current directory to path
current_dir = os.path.dirname(os.path.abspath(SPEC))

a = Analysis(
    ['desktop/main.py'],
    pathex=[current_dir],
    binaries=[],
    datas=[
        # Include backend directory for imports
        ('backend', 'backend'),
        # Include desktop assets if any
        ('desktop/assets', 'desktop/assets'),
    ],
    hiddenimports=[
        'customtkinter',
        'PIL',
        'PIL.Image',
        'PIL.ImageTk',
        'cv2',
        'httpx',
        'pydantic',
        'pydantic_settings',
        'sqlalchemy',
        'alembic',
        'fastapi',
        'uvicorn',
        'pydantic_core',
        'pydantic_core._pydantic_core',
        'requests',
        'desktop.core.updater',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=None,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=None)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='MyRhythmNexus-Desktop',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,  # Set to True for debugging
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,  # Add icon file path if you have one
)