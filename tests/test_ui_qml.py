"""Headless QML smoke test: the root window must instantiate without errors.

Runs under the offscreen platform (set in conftest). A non-empty
``rootObjects()`` means the whole `App` module — Main, TopBar, Rail,
SegmentedControl, SummaryScreen, and the Theme singleton — parsed, resolved,
and instantiated. It does not assert anything visual (that needs a display).
"""

from __future__ import annotations

import pytest
from PySide6.QtGui import QGuiApplication


@pytest.fixture(scope="session")
def qapp() -> QGuiApplication:
    return QGuiApplication.instance() or QGuiApplication([])


def test_main_qml_loads_without_errors(qapp) -> None:
    from docsummarizer.ui.app import create_engine

    engine, _bridge = create_engine(qapp)
    assert engine.rootObjects(), "Main.qml failed to load (QML parse/type error)"
