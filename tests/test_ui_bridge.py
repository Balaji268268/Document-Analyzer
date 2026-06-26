"""Tests for the Qt <-> QML bridge controller (headless / offscreen).

The bridge runs long ops on a thread pool in production; tests use its
``synchronous=True`` seam so flows run inline and deterministically. A fake
summarizer stands in for the llama-cpp-backed one.
"""

from __future__ import annotations

import pytest
from PySide6.QtGui import QGuiApplication
from PySide6.QtTest import QSignalSpy

from docsummarizer.model_manager import (
    SUMMARY_TYPE_DETAILED,
    StructuredSummary,
    SummaryPoint,
)
from docsummarizer.provenance import SourceSpan
from docsummarizer.settings import load_settings
from docsummarizer.ui import bridge as bridge_mod
from docsummarizer.ui.bridge import ConsoleBridge, _quant_label, summary_to_variant


@pytest.fixture(scope="session")
def qapp() -> QGuiApplication:
    return QGuiApplication.instance() or QGuiApplication([])


class _FakeSummarizer:
    def __init__(self) -> None:
        self.closed = False

    def summarize_structured(
        self, text: str, summary_type: str = SUMMARY_TYPE_DETAILED
    ) -> StructuredSummary:
        return StructuredSummary(
            summary_type,
            "the lead",
            [SummaryPoint("a point", SourceSpan(0, 5, "Hello", 1.0))],
            None,
            "rendered text",
        )

    def summarize(self, text: str, summary_type: str = SUMMARY_TYPE_DETAILED) -> str:
        return "FAKE PLAIN SUMMARY"

    def close(self) -> None:
        self.closed = True


def _bridge(synchronous: bool = True) -> ConsoleBridge:
    return ConsoleBridge(summarizer_factory=lambda *_: _FakeSummarizer(), synchronous=synchronous)


# --------------------------------------------------------------------------- #
# Pure marshalling
# --------------------------------------------------------------------------- #
def test_quant_label_parses_gguf_filename() -> None:
    assert _quant_label("Qwen3-4B-Instruct-2507-Q4_K_M.gguf") == "Q4_K_M"
    assert _quant_label("model-without-quant.gguf") == ""


def test_summary_to_variant_shapes_points_and_sections() -> None:
    summary = StructuredSummary(
        "structured",
        None,
        [],
        {
            "PURPOSE": [SummaryPoint("p", SourceSpan(2, 7, "world", 0.9))],
            "CONCLUSIONS": [SummaryPoint("c", None)],
        },
        "txt",
    )
    variant = summary_to_variant(summary)
    assert variant["summaryType"] == "structured"
    purpose = variant["sections"]["PURPOSE"][0]
    assert purpose["start"] == 2
    assert purpose["end"] == 7
    assert purpose["hasCitation"] is True
    assert variant["sections"]["CONCLUSIONS"][0]["hasCitation"] is False


# --------------------------------------------------------------------------- #
# Model lifecycle + summarize flow
# --------------------------------------------------------------------------- #
def test_check_model_loads_when_present(qapp, monkeypatch) -> None:
    monkeypatch.setattr(bridge_mod, "is_model_downloaded", lambda: True)
    bridge = _bridge()
    bridge.checkModel()
    assert bridge._get_model_ready() is True


def test_summarize_emits_marshalled_summary(qapp, monkeypatch, tmp_path) -> None:
    monkeypatch.setattr(bridge_mod, "is_model_downloaded", lambda: True)
    bridge = _bridge()
    bridge.checkModel()

    doc = tmp_path / "d.txt"
    doc.write_text("Hello world. More text follows here.", encoding="utf-8")
    bridge.loadDocument(str(doc))
    assert bridge._get_can_summarize() is True

    spy = QSignalSpy(bridge.summaryReady)
    bridge.summarize()
    assert spy.count() == 1
    variant = spy.at(0)[0]
    assert variant["summaryType"] == "detailed"
    assert variant["lead"] == "the lead"
    assert variant["points"][0]["text"] == "a point"
    assert variant["points"][0]["hasCitation"] is True
    assert bridge._get_busy() is False


def test_load_document_error_blocks_summarize(qapp, monkeypatch) -> None:
    monkeypatch.setattr(bridge_mod, "is_model_downloaded", lambda: True)
    bridge = _bridge()
    bridge.checkModel()
    bridge.loadDocument("/nonexistent/file.txt")
    assert bridge._get_has_doc() is False
    assert bridge._get_can_summarize() is False
    assert bridge._status_color == "error"


# --------------------------------------------------------------------------- #
# Settings: GPU persists immediately; threads persist only on reload
# --------------------------------------------------------------------------- #
def test_toggle_gpu_persists_immediately(qapp) -> None:
    bridge = _bridge()
    bridge.toggleGpu(True)
    assert bridge._settings.use_gpu is True
    assert load_settings().use_gpu is True


def test_threads_arm_reload_but_persist_only_on_reload(qapp, monkeypatch) -> None:
    monkeypatch.setattr(bridge_mod, "is_model_downloaded", lambda: True)
    bridge = _bridge()
    bridge.checkModel()  # model loaded so reload can arm

    bridge.setThreads(3)
    assert bridge._settings.n_threads == 3
    assert bridge._get_reload_armed() is True
    assert load_settings().n_threads is None  # not persisted yet

    bridge.reloadModel()
    assert load_settings().n_threads == 3  # persisted on reload
    assert bridge._get_reload_armed() is False


def test_set_appearance_persists(qapp) -> None:
    bridge = _bridge()
    bridge.setAppearance("Dark")
    assert load_settings().appearance == "Dark"


def test_reload_not_armed_without_loaded_model(qapp) -> None:
    bridge = _bridge()  # no checkModel → no summarizer
    bridge.setThreads(5)
    assert bridge._get_reload_armed() is False


# --------------------------------------------------------------------------- #
# Batch
# --------------------------------------------------------------------------- #
def test_batch_process_summarizes_folder(qapp, monkeypatch, tmp_path) -> None:
    monkeypatch.setattr(bridge_mod, "is_model_downloaded", lambda: True)
    bridge = _bridge()
    bridge.checkModel()

    (tmp_path / "a.txt").write_text("Document A content here.", encoding="utf-8")
    (tmp_path / "b.md").write_text("Document B content here.", encoding="utf-8")
    (tmp_path / "ignore.png").write_bytes(b"not a document")
    out = tmp_path / "out"
    out.mkdir()

    spy = QSignalSpy(bridge.batchComplete)
    bridge.batchProcess(str(tmp_path), str(out))

    assert spy.count() == 1
    done_count, total, failures, _out_dir = spy.at(0)
    assert done_count == 2
    assert total == 2  # the .png is not a supported document
    assert failures == []
    assert (out / "a_summary.txt").exists()
    assert (out / "b_summary.txt").exists()


def test_batch_process_no_documents_emits_toast(qapp, monkeypatch, tmp_path) -> None:
    monkeypatch.setattr(bridge_mod, "is_model_downloaded", lambda: True)
    bridge = _bridge()
    bridge.checkModel()
    out = tmp_path / "out"
    out.mkdir()
    spy = QSignalSpy(bridge.toast)
    bridge.batchProcess(str(tmp_path), str(out))  # empty folder
    assert spy.count() == 1
