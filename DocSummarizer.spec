# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller spec for DocSummarizer (Qt/QML UI)."""

import importlib.util
import shutil
from pathlib import Path


def _llama_cpp_lib_dir() -> Path | None:
    """Locate llama_cpp/lib directory if present."""
    spec = importlib.util.find_spec("llama_cpp")
    if spec is None or spec.origin is None:
        return None
    lib = Path(spec.origin).parent / "lib"
    return lib if lib.exists() else None


spec_dir = Path(SPECPATH)
src_dir = spec_dir / "src"

llama_binaries = []
llama_cpp_lib = _llama_cpp_lib_dir()
if llama_cpp_lib is not None:
    for f in llama_cpp_lib.iterdir():
        if f.suffix in (".dll", ".so", ".dylib"):
            llama_binaries.append((str(f), "llama_cpp/lib"))

a = Analysis(
    [str(spec_dir / "run.py")],
    pathex=[str(src_dir)],
    binaries=llama_binaries,
    datas=[],
    hiddenimports=[
        "docsummarizer",
        "docsummarizer.ui.app",
        "docsummarizer.ui.bridge",
        "docsummarizer.ui.workers",
        "docsummarizer.cli",
        "docsummarizer.document_parser",
        "docsummarizer.provenance",
        "docsummarizer.logger",
        "docsummarizer.model_manager",
        "docsummarizer.settings",
        "PySide6.QtCore",
        "PySide6.QtGui",
        "PySide6.QtQml",
        "PySide6.QtQuick",
        "PySide6.QtQuickControls2",
        "llama_cpp",
        "pypdf",
        "docx",
        "striprtf",
        "chardet",
        "huggingface_hub",
        "tqdm",
        "psutil",
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        "customtkinter",
        "tkinter",
        "PySide6.QtMultimedia",
        "PySide6.QtMultimediaWidgets",
        "PySide6.QtWebEngineCore",
        "PySide6.QtWebEngineWidgets",
        "PySide6.QtWebEngineQuick",
    ],
    noarchive=False,
    optimize=0,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="DocSummarizer",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,
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
    upx=False,
    upx_exclude=[],
    name="DocSummarizer",
)

# Guaranteed QML asset bundling step
dest_qml = Path(DISTPATH) / "DocSummarizer" / "_internal" / "docsummarizer" / "ui" / "qml"
dest_qml.parent.mkdir(parents=True, exist_ok=True)
if dest_qml.exists():
    shutil.rmtree(dest_qml)
shutil.copytree(src_dir / "docsummarizer" / "ui" / "qml", dest_qml)
print(f"POST-BUILD: Copied QML resources to {dest_qml}")
