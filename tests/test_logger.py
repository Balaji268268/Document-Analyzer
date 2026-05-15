"""Tests for `docsummarizer.logger`."""

from __future__ import annotations

import logging
from pathlib import Path

import pytest

from docsummarizer import logger as logger_module


def test_get_log_directory_linux(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setattr(logger_module.sys, "platform", "linux")
    monkeypatch.setenv("XDG_DATA_HOME", str(tmp_path))
    d = logger_module.get_log_directory()
    assert d == tmp_path / "DocSummarizer" / "logs"
    assert d.exists()


def test_get_log_directory_darwin(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setattr(logger_module.sys, "platform", "darwin")
    monkeypatch.setenv("HOME", str(tmp_path))
    d = logger_module.get_log_directory()
    assert d == tmp_path / "Library" / "Application Support" / "DocSummarizer" / "logs"
    assert d.exists()


def test_get_log_directory_win32(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setattr(logger_module.sys, "platform", "win32")
    monkeypatch.setenv("LOCALAPPDATA", str(tmp_path))
    d = logger_module.get_log_directory()
    assert d == tmp_path / "DocSummarizer" / "logs"
    assert d.exists()


def test_get_logger_returns_singleton() -> None:
    a = logger_module.get_logger()
    b = logger_module.get_logger()
    assert a is b


def test_setup_logger_avoids_duplicate_handlers() -> None:
    """Calling setup_logger twice must not stack file handlers."""
    first = logger_module.setup_logger()
    handler_count = len(first.handlers)
    second = logger_module.setup_logger()
    assert second is first
    assert len(second.handlers) == handler_count


def test_get_logger_thread_safe(monkeypatch: pytest.MonkeyPatch) -> None:
    """Concurrent first-callers must not produce duplicate handlers.

    Pre-fix: the lazy init was `if _logger is None: _logger = setup_logger()`
    with no lock. Two simultaneous first calls could both pass the check
    and both add a FileHandler.
    """
    import threading

    barrier = threading.Barrier(8)
    results: list[logging.Logger] = []

    def worker():
        barrier.wait()
        results.append(logger_module.get_logger())

    threads = [threading.Thread(target=worker) for _ in range(8)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    assert len(results) == 8
    # All callers got the same logger object.
    first = results[0]
    assert all(r is first for r in results)
    # And only one FileHandler is attached.
    file_handlers = [h for h in first.handlers if isinstance(h, logging.FileHandler)]
    assert len(file_handlers) == 1


def test_system_info_has_expected_fields() -> None:
    info = logger_module.get_system_info()
    for key in ("platform", "architecture", "cpu_count", "python_version"):
        assert key in info, f"missing {key!r}"


def test_timer_logs_elapsed(caplog: pytest.LogCaptureFixture) -> None:
    # Ensure the named logger forwards records into caplog
    logging.getLogger("DocSummarizer").addHandler(caplog.handler)
    logging.getLogger("DocSummarizer").setLevel(logging.DEBUG)

    with caplog.at_level(logging.INFO, logger="DocSummarizer"), logger_module.Timer("widget"):
        pass

    messages = "\n".join(r.getMessage() for r in caplog.records)
    assert "Starting: widget" in messages
    assert "Completed: widget" in messages


def test_timer_logs_failure_on_exception(caplog: pytest.LogCaptureFixture) -> None:
    logging.getLogger("DocSummarizer").addHandler(caplog.handler)
    logging.getLogger("DocSummarizer").setLevel(logging.DEBUG)

    with (
        caplog.at_level(logging.ERROR, logger="DocSummarizer"),
        pytest.raises(ValueError, match="boom"),
        logger_module.Timer("widget"),
    ):
        raise ValueError("boom")

    messages = "\n".join(r.getMessage() for r in caplog.records)
    assert "Failed: widget" in messages
