"""Shared pytest fixtures.

The big concern is that the production code derives its log/model
directories from real OS env vars (LOCALAPPDATA, XDG_DATA_HOME) and
falls back to the user's home folder. Tests must never write to those
real locations — `_isolated_app_dirs` redirects them to tmp_path
automatically for every test.
"""

from __future__ import annotations

import logging
import os
from pathlib import Path

import pytest

# Skip the Qt UI tests where PySide6 isn't installed (keeps a minimal env green).
try:
    import PySide6  # noqa: F401
except ImportError:
    collect_ignore_glob = ["test_ui_*.py"]

# Qt UI tests run headless: offscreen platform + software Qt Quick backend so no
# display or GPU/GL is required.
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
os.environ.setdefault("QT_QUICK_BACKEND", "software")


@pytest.fixture(autouse=True)
def _isolated_app_dirs(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> Path:
    """Redirect platform app-data locations to a per-test tmp dir.

    Covers Linux (XDG_DATA_HOME), Windows (LOCALAPPDATA), and macOS
    (~/Library/Application Support — by remapping HOME). Yields the
    base tmp dir so tests can inspect what was written.
    """
    monkeypatch.setenv("XDG_DATA_HOME", str(tmp_path))
    monkeypatch.setenv("LOCALAPPDATA", str(tmp_path))
    monkeypatch.setenv("HOME", str(tmp_path))
    monkeypatch.setenv("USERPROFILE", str(tmp_path))
    return tmp_path


@pytest.fixture(autouse=True)
def _reset_logger_singleton(monkeypatch: pytest.MonkeyPatch):
    """Reset the lazy `_logger` between tests.

    `docsummarizer.logger._logger` is a process-wide singleton; without
    resetting it, the first test creates a logger pointing at one
    tmp_path and every subsequent test inherits it (with a stale file
    handler pointing at a now-deleted tmp dir).
    """
    from docsummarizer import logger as logger_module

    monkeypatch.setattr(logger_module, "_logger", None)
    # Detach any existing handlers from the named logger so re-init is clean.
    named = logging.getLogger("DocSummarizer")
    for handler in list(named.handlers):
        handler.close()
        named.removeHandler(handler)
    yield
    named = logging.getLogger("DocSummarizer")
    for handler in list(named.handlers):
        handler.close()
        named.removeHandler(handler)
