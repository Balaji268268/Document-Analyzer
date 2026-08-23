"""Qt/QML application entry point.

Boots a ``QQmlApplicationEngine``, wires the ``ConsoleBridge`` in as the ``bridge``
context object, and loads ``App/Main.qml``. Run with ``python -m docsummarizer.ui.app``
(a console entry point replaces ``run.py`` when the CustomTkinter GUI is retired).
"""

from __future__ import annotations

import sys
from pathlib import Path

from PySide6.QtCore import QUrl
from PySide6.QtGui import QGuiApplication
from PySide6.QtQml import QQmlApplicationEngine

from docsummarizer.logger import log_error, log_startup
from docsummarizer.ui.bridge import ConsoleBridge

_QML_DIR = Path(__file__).parent / "qml"
_MAIN_QML = _QML_DIR / "App" / "Main.qml"


def create_engine(app: QGuiApplication) -> tuple[QQmlApplicationEngine, ConsoleBridge]:
    """Build the QML engine + bridge and load the root window.

    Returns the engine and bridge (kept alive by the caller). Raises
    ``RuntimeError`` if the QML failed to instantiate.
    """
    from docsummarizer.ui.fonts import register_fonts

    engine = QQmlApplicationEngine()
    bridge = ConsoleBridge()
    register_fonts()  # so QML resolves Cormorant/Chakra/Saira/Share Tech Mono
    engine.addImportPath(str(_QML_DIR))
    engine.rootContext().setContextProperty("bridge", bridge)
    app.aboutToQuit.connect(bridge.shutdown)
    engine.load(QUrl.fromLocalFile(str(_MAIN_QML)))
    if not engine.rootObjects():
        raise RuntimeError(f"Failed to load QML from {_MAIN_QML}")
    return engine, bridge


def _install_excepthook(bridge: ConsoleBridge) -> None:
    """Route uncaught exceptions to the log + a best-effort toast.

    A windowed (no-console) build discards stderr, so without this an uncaught
    exception in a Qt slot vanishes silently. Logging it makes the next such
    failure diagnosable from the log file.
    """
    import contextlib
    import traceback
    from types import TracebackType

    def hook(
        exc_type: type[BaseException],
        exc_value: BaseException,
        exc_tb: TracebackType | None,
    ) -> None:
        log_error(
            "Uncaught exception:\n"
            + "".join(traceback.format_exception(exc_type, exc_value, exc_tb))
        )
        with contextlib.suppress(Exception):  # best-effort during a crash
            bridge.toast.emit("Something went wrong — see the log file")
        sys.__excepthook__(exc_type, exc_value, exc_tb)

    sys.excepthook = hook


def main() -> int:
    """Launch the DocSummarizer console UI."""
    log_startup()
    # Perform startup Python dependency check & auto-resolution
    try:
        from docsummarizer import dependency_manager

        dependency_manager.auto_install_missing_dependencies()
    except Exception as exc:
        from docsummarizer.logger import log_error

        log_error(f"Startup dependency resolution warning: {exc}")

    try:
        import threading
        from docsummarizer.web_app import run_web_server

        web_thread = threading.Thread(
            target=run_web_server, kwargs={"port": 8081, "host": "0.0.0.0"}, daemon=True
        )
        web_thread.start()
    except Exception as exc:
        log_error(f"Background web server startup warning: {exc}")

    app = QGuiApplication(sys.argv)
    app.setApplicationName("DocSummarizer")
    app.setOrganizationName("DocSummarizer")
    # Keep the engine referenced for the app's lifetime (GC would tear down the
    # window). bridge is owned by the engine's context but used here too.
    _engine, bridge = create_engine(app)
    _install_excepthook(bridge)
    bridge.checkModel()
    bridge.checkDependencies()
    bridge.checkOllamaStatus()
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
