# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller spec file for DocSummarizer.
Build with: pyinstaller DocSummarizer.spec
"""

import sys
from pathlib import Path

block_cipher = None

# Get the directory containing this spec file
spec_dir = Path(SPECPATH)

a = Analysis(
    [str(spec_dir / 'run.py')],
    pathex=[str(spec_dir / 'src')],
    binaries=[],
    datas=[],
    hiddenimports=[
        'llama_cpp',
        'pypdf',
        'docx',
        'striprtf',
        'chardet',
        'customtkinter',
        'huggingface_hub',
        'tqdm',
        'tiktoken',
        'tiktoken_ext',
        'tiktoken_ext.openai_public',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='DocSummarizer',
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
    icon=None,  # Add icon path here if desired
)
