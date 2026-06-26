# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller spec for DocSummarizer (Qt/QML "Abstract Console" UI).

Build a single portable executable with:
    pyinstaller DocSummarizer.spec        # -> dist/DocSummarizer[.exe]

Builds for the HOST platform (PyInstaller does not cross-compile): run it on
Windows to produce the portable .exe. The ~2.5 GB model is NOT bundled — it is
downloaded into the app-data dir on first run.
"""

import importlib.util
from pathlib import Path

from PyInstaller.utils.hooks import collect_all


def _llama_cpp_lib_dir() -> Path | None:
    """Locate the llama_cpp/lib directory of the active interpreter, if present."""
    spec = importlib.util.find_spec("llama_cpp")
    if spec is None or spec.origin is None:
        return None
    lib = Path(spec.origin).parent / "lib"
    return lib if lib.exists() else None


spec_dir = Path(SPECPATH)
src_dir = spec_dir / "src"

# Collect llama_cpp shared libraries (.dll/.so/.dylib) if the runtime extra is
# installed in the build environment.
llama_binaries = []
llama_cpp_lib = _llama_cpp_lib_dir()
if llama_cpp_lib is not None:
    for f in llama_cpp_lib.iterdir():
        if f.suffix in (".dll", ".so", ".dylib"):
            llama_binaries.append((str(f), "llama_cpp/lib"))

# Collect everything PySide6 needs: Qt libraries, the QML plugins for the
# modules we import (QtQuick, Controls.Basic, Layouts), and platform plugins.
pyside_datas, pyside_binaries, pyside_hiddenimports = collect_all("PySide6")

# Ship the QML sources as data, preserving the package-relative layout so
# app.py's ``Path(__file__).parent / "qml"`` resolves inside the bundle.
qml_root = src_dir / "docsummarizer" / "ui" / "qml"
qml_datas = [
    (str(f), str(f.parent.relative_to(src_dir)))
    for f in qml_root.rglob("*")
    if f.is_file()
]


a = Analysis(
    [str(spec_dir / "run.py")],
    pathex=[str(src_dir)],
    binaries=llama_binaries + pyside_binaries,
    datas=qml_datas + pyside_datas,
    hiddenimports=[
        # Package modules — PyInstaller's static analysis can miss these because
        # the entry point imports them via relative paths.
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
        # Qt modules used by the QML UI.
        "PySide6.QtCore",
        "PySide6.QtGui",
        "PySide6.QtQml",
        "PySide6.QtQuick",
        "PySide6.QtQuickControls2",
        # Third-party.
        "llama_cpp",
        "pypdf",
        "docx",
        "striprtf",
        "chardet",
        "huggingface_hub",
        "tqdm",
        "tiktoken",
        "tiktoken_ext",
        "tiktoken_ext.openai_public",
        "psutil",
        *pyside_hiddenimports,
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=["customtkinter", "tkinter"],
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
    # UPX can corrupt Qt's shared libraries; keep it off for a reliable build.
    upx=False,
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
