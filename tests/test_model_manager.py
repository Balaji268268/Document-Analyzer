"""Tests for `docsummarizer.model_manager`.

We exercise only the parts that don't touch the actual llama.cpp engine —
path resolution, model existence checks, and the tqdm progress wrapper.
The Llama() constructor is imported lazily inside Summarizer.__init__,
so we don't even need llama-cpp-python installed for these tests.
"""

from __future__ import annotations

import io
from pathlib import Path

import pytest

from docsummarizer import model_manager
from docsummarizer.model_manager import (
    SUMMARY_TYPE_BRIEF,
    SUMMARY_TYPE_DETAILED,
    SUMMARY_TYPE_STRUCTURED,
    SUMMARY_TYPES,
    ModelConfig,
)

_MB = 1024 * 1024


@pytest.fixture
def mistral_filename() -> str:
    return model_manager.DEFAULT_MODEL.filename


def test_default_model_is_dataclass() -> None:
    assert isinstance(model_manager.DEFAULT_MODEL, ModelConfig)
    # Frozen — assignment must raise.
    with pytest.raises(Exception):
        model_manager.DEFAULT_MODEL.filename = "other.gguf"  # type: ignore[misc]


def test_summary_types_tuple_matches_constants() -> None:
    assert SUMMARY_TYPES == (SUMMARY_TYPE_BRIEF, SUMMARY_TYPE_DETAILED, SUMMARY_TYPE_STRUCTURED)


def test_models_directory_uses_isolated_path(tmp_path: Path) -> None:
    """`conftest._isolated_app_dirs` redirects platform env vars to tmp_path;
    the resolved models dir must land under it."""
    d = model_manager.get_models_directory()
    assert str(d).startswith(str(tmp_path))
    assert d.name == "models"
    assert d.exists()


def test_is_model_downloaded_when_missing() -> None:
    assert model_manager.is_model_downloaded() is False


def test_is_model_downloaded_when_present(mistral_filename: str) -> None:
    models_dir = model_manager.get_models_directory()
    (models_dir / mistral_filename).write_bytes(b"fake gguf payload")
    assert model_manager.is_model_downloaded() is True


def test_get_model_path_default(mistral_filename: str) -> None:
    p = model_manager.get_model_path()
    assert p.name == mistral_filename
    assert p.parent == model_manager.get_models_directory()


def test_get_model_path_with_custom_config() -> None:
    custom = ModelConfig(
        repo_id="irrelevant",
        filename="custom-model.gguf",
        name="custom",
        size_gb=1.0,
    )
    p = model_manager.get_model_path(custom)
    assert p.name == "custom-model.gguf"


def test_download_model_short_circuits_when_file_exists(
    monkeypatch: pytest.MonkeyPatch, mistral_filename: str
) -> None:
    """If the model file is already present, download_model must not call
    hf_hub_download and must report success.
    """
    models_dir = model_manager.get_models_directory()
    (models_dir / mistral_filename).write_bytes(b"fake")

    def _fake_download(**_kwargs):
        raise AssertionError("hf_hub_download must not be invoked when the file exists")

    monkeypatch.setattr(model_manager, "hf_hub_download", _fake_download)

    progress_log: list[tuple[float, str]] = []
    path, error = model_manager.download_model(
        progress_callback=lambda pct, msg: progress_log.append((pct, msg))
    )

    assert error is None
    assert path.name == mistral_filename
    assert progress_log == [(100.0, "Model already downloaded")]


def test_download_model_short_circuit_fires_progress_callback(
    monkeypatch: pytest.MonkeyPatch, mistral_filename: str
) -> None:
    """The 100% sentinel still goes out so the GUI can hide its spinner."""
    models_dir = model_manager.get_models_directory()
    (models_dir / mistral_filename).write_bytes(b"fake")
    monkeypatch.setattr(
        model_manager,
        "hf_hub_download",
        lambda **_: pytest.fail("must not be called"),
    )

    calls: list[tuple[float, str]] = []
    model_manager.download_model(progress_callback=lambda pct, msg: calls.append((pct, msg)))
    assert calls == [(100.0, "Model already downloaded")]


def test_progress_tqdm_fires_callback_per_megabyte() -> None:
    """`_build_progress_tqdm` throttles to one callback per whole MB step.

    Anything finer would flood the GUI's Tk main loop during a multi-GB
    download (one update per HTTP chunk = thousands of no-op redraws).
    """
    calls: list[tuple[float, str]] = []
    Klass = model_manager._build_progress_tqdm(lambda pct, msg: calls.append((pct, msg)))

    bar = Klass(total=4 * _MB, file=io.StringIO(), mininterval=0)
    for _ in range(4):
        bar.update(_MB)
    bar.close()

    # 4 MB total, fired once per whole-MB transition => 4 callbacks.
    assert len(calls) == 4
    pcts = [c[0] for c in calls]
    assert pcts == sorted(pcts)
    assert calls[-1][0] == pytest.approx(100.0)


def test_progress_tqdm_swallows_callback_errors() -> None:
    """A misbehaving callback must not break the download."""

    def bad_cb(_pct, _msg):
        raise RuntimeError("callback exploded")

    Klass = model_manager._build_progress_tqdm(bad_cb)
    bar = Klass(total=2 * _MB, file=io.StringIO(), mininterval=0)
    bar.update(_MB)
    bar.update(_MB)
    bar.close()


def test_summarizer_close_is_idempotent_without_llama_cpp() -> None:
    """`close()` must work even if llama-cpp wasn't importable.

    We don't actually exercise Summarizer.__init__ here (it'd require
    llama-cpp-python in the test env); we verify close() is callable on a
    fresh shell so a future refactor doesn't break the contract.
    """
    # Build a Summarizer-shaped shell — exercise the close() shape only.
    s = object.__new__(model_manager.Summarizer)
    s.llm = None
    s.close()  # should be a no-op
    s.close()  # second call must also be a no-op
