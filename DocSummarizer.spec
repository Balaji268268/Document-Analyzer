# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller spec file for DocSummarizer.
Build with: pyinstaller DocSummarizer.spec
"""

import importlib.util
from pathlib import Path


def _llama_cpp_lib_dir() -> Path | None:
    """Locate the llama_cpp/lib directory of the active interpreter.

    Works across Windows, macOS, and Linux without hardcoded venv paths.
    Returns None if llama_cpp isn't importable from this interpreter.
    """
    spec = importlib.util.find_spec("llama_cpp")
    if spec is None or spec.origin is None:
        return None
    lib = Path(spec.origin).parent / "lib"
    return lib if lib.exists() else None


spec_dir = Path(SPECPATH)

# Collect llama_cpp shared libraries (.dll on Windows, .dylib on macOS, .so on Linux).
llama_binaries = []
llama_cpp_lib = _llama_cpp_lib_dir()
if llama_cpp_lib is not None:
    for f in llama_cpp_lib.iterdir():
        if f.suffix in (".dll", ".so", ".dylib"):
            llama_binaries.append((str(f), "llama_cpp/lib"))


a = Analysis(
    [str(spec_dir / "run.py")],
    pathex=[str(spec_dir / "src")],
    binaries=llama_binaries,
    datas=[],
    hiddenimports=[
        # Package modules — PyInstaller's static analysis sometimes misses
        # these because the GUI imports them via relative paths inside __init__.
        "docsummarizer",
        "docsummarizer.gui",
        "docsummarizer.cli",
        "docsummarizer.document_parser",
        "docsummarizer.logger",
        "docsummarizer.model_manager",
        # Third-party
        "llama_cpp",
        "pypdf",
        "docx",
        "striprtf",
        "chardet",
        "customtkinter",
        "huggingface_hub",
        "tqdm",
        "tiktoken",
        "tiktoken_ext",
        "tiktoken_ext.openai_public",
        "psutil",
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name="DocSummarizer",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,
)
