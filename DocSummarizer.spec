# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller spec file for DocSummarizer.
Build with: pyinstaller DocSummarizer.spec
"""

import sys
import os
from pathlib import Path

block_cipher = None

# Get the directory containing this spec file
spec_dir = Path(SPECPATH)

# Find llama_cpp lib directory (contains DLLs/shared libraries)
if sys.platform == 'win32':
    venv_site_packages = spec_dir / 'venv' / 'Lib' / 'site-packages'
else:
    # Linux: find the python version dynamically
    venv_lib = spec_dir / 'venv_linux' / 'lib'
    if venv_lib.exists():
        py_dirs = [d for d in venv_lib.iterdir() if d.name.startswith('python')]
        venv_site_packages = py_dirs[0] / 'site-packages' if py_dirs else None
    else:
        venv_site_packages = None

llama_cpp_lib = venv_site_packages / 'llama_cpp' / 'lib' if venv_site_packages else None

# Collect llama_cpp binaries
llama_binaries = []
if llama_cpp_lib and llama_cpp_lib.exists():
    for f in llama_cpp_lib.iterdir():
        if f.suffix in ('.dll', '.so', '.dylib'):
            llama_binaries.append((str(f), 'llama_cpp/lib'))

a = Analysis(
    [str(spec_dir / 'run.py'),
     str(spec_dir / 'src' / 'logger.py'),
     str(spec_dir / 'src' / 'gui.py'),
     str(spec_dir / 'src' / 'model_manager.py'),
     str(spec_dir / 'src' / 'document_parser.py')],
    pathex=[str(spec_dir / 'src')],
    binaries=llama_binaries,
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
        'logger',
        'psutil',
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
