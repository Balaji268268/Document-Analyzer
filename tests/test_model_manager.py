"""Tests for `docsummarizer.model_manager`.

We exercise only the parts that don't touch the actual llama.cpp engine —
path resolution, model existence checks, and the tqdm progress wrapper.
The Llama() constructor is imported lazily inside Summarizer.__init__,
so we don't even need llama-cpp-python installed for these tests.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from docsummarizer import model_manager


@pytest.fixture
def mistral_filename() -> str:
    return model_manager.DEFAULT_MODEL["filename"]


def test_models_directory_linux(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setattr(model_manager.sys, "platform", "linux")
    monkeypatch.setenv("XDG_DATA_HOME", str(tmp_path))
    d = model_manager.get_models_directory()
    assert d == tmp_path / "DocSummarizer" / "models"
    assert d.exists()


def test_models_directory_darwin(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setattr(model_manager.sys, "platform", "darwin")
    monkeypatch.setenv("HOME", str(tmp_path))
    d = model_manager.get_models_directory()
    assert d == tmp_path / "Library" / "Application Support" / "DocSummarizer" / "models"


def test_models_directory_win32(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setattr(model_manager.sys, "platform", "win32")
    monkeypatch.setenv("LOCALAPPDATA", str(tmp_path))
    d = model_manager.get_models_directory()
    assert d == tmp_path / "DocSummarizer" / "models"


def test_is_model_downloaded_when_missing(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setenv("XDG_DATA_HOME", str(tmp_path))
    monkeypatch.setattr(model_manager.sys, "platform", "linux")
    assert model_manager.is_model_downloaded() is False


def test_is_model_downloaded_when_present(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, mistral_filename: str
) -> None:
    monkeypatch.setenv("XDG_DATA_HOME", str(tmp_path))
    monkeypatch.setattr(model_manager.sys, "platform", "linux")
    models_dir = tmp_path / "DocSummarizer" / "models"
    models_dir.mkdir(parents=True, exist_ok=True)
    (models_dir / mistral_filename).write_bytes(b"fake gguf payload")
    assert model_manager.is_model_downloaded() is True


def test_get_model_path_default(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, mistral_filename: str
) -> None:
    monkeypatch.setenv("XDG_DATA_HOME", str(tmp_path))
    monkeypatch.setattr(model_manager.sys, "platform", "linux")
    p = model_manager.get_model_path()
    assert p.name == mistral_filename
    assert p.parent == tmp_path / "DocSummarizer" / "models"


def test_get_model_path_with_custom_config(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setenv("XDG_DATA_HOME", str(tmp_path))
    monkeypatch.setattr(model_manager.sys, "platform", "linux")
    custom = {
        "repo_id": "irrelevant",
        "filename": "custom-model.gguf",
        "name": "custom",
        "size_gb": 1.0,
    }
    p = model_manager.get_model_path(custom)
    assert p.name == "custom-model.gguf"


def test_download_model_short_circuits_when_file_exists(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, mistral_filename: str
) -> None:
    """If the model file is already present, download_model must not call
    hf_hub_download and must report success.
    """
    monkeypatch.setenv("XDG_DATA_HOME", str(tmp_path))
    monkeypatch.setattr(model_manager.sys, "platform", "linux")

    models_dir = tmp_path / "DocSummarizer" / "models"
    models_dir.mkdir(parents=True, exist_ok=True)
    (models_dir / mistral_filename).write_bytes(b"fake")

    called = {"n": 0}

    def _fake_download(**_kwargs):
        called["n"] += 1
        raise AssertionError("hf_hub_download must not be invoked when the file exists")

    monkeypatch.setattr(model_manager, "hf_hub_download", _fake_download)

    progress_log: list[tuple[float, str]] = []

    def cb(pct, msg):
        progress_log.append((pct, msg))

    path, error = model_manager.download_model(progress_callback=cb)
    assert error is None
    assert path.name == mistral_filename
    assert called["n"] == 0
    assert progress_log == [(100.0, "Model already downloaded")]


def test_progress_tqdm_invokes_callback_on_update() -> None:
    """`_build_progress_tqdm` must fire its callback as tqdm.update() is called."""
    import io

    calls: list[tuple[float, str]] = []

    def cb(pct, msg):
        calls.append((pct, msg))

    Klass = model_manager._build_progress_tqdm(cb)
    # `disable=True` short-circuits tqdm.update() entirely (no self.n update);
    # use a sink file instead so the bar actually tracks progress but its
    # rendering goes nowhere.
    bar = Klass(total=100, file=io.StringIO(), mininterval=0)
    bar.update(25)
    bar.update(25)
    bar.update(50)
    bar.close()

    assert len(calls) == 3
    pcts = [c[0] for c in calls]
    assert pcts == sorted(pcts)
    assert calls[-1][0] == pytest.approx(100.0)


def test_progress_tqdm_swallows_callback_errors() -> None:
    """A misbehaving callback must not break the download."""
    import io

    def bad_cb(_pct, _msg):
        raise RuntimeError("callback exploded")

    Klass = model_manager._build_progress_tqdm(bad_cb)
    bar = Klass(total=10, file=io.StringIO(), mininterval=0)
    # Must not raise:
    bar.update(5)
    bar.update(5)
    bar.close()
