"""Unit tests for docsummarizer.ollama_manager."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from docsummarizer import ollama_manager


def test_check_ollama_status_not_installed() -> None:
    """When Ollama executable is not found and service is unreachable, returns NOT_INSTALLED status."""
    with (
        patch("docsummarizer.ollama_manager.find_ollama_executable", return_value=None),
        patch("docsummarizer.ollama_manager.get_available_ollama_models", return_value=[]),
        patch("docsummarizer.ollama_manager._ping_ollama", return_value=False),
    ):
        status = ollama_manager.check_ollama_status("llama3")
        assert status["code"] == ollama_manager.OLLAMA_STATUS_NOT_INSTALLED
        assert status["installed"] is False
        assert status["running"] is False


def test_check_ollama_status_stopped() -> None:
    """When Ollama executable is present but HTTP API is unreachable, returns STOPPED status."""
    fake_path = MagicMock()
    fake_path.__str__.return_value = "/usr/bin/ollama"
    with (
        patch("docsummarizer.ollama_manager.find_ollama_executable", return_value=fake_path),
        patch("docsummarizer.ollama_manager.get_available_ollama_models", return_value=[]),
        patch("docsummarizer.ollama_manager._ping_ollama", return_value=False),
    ):
        status = ollama_manager.check_ollama_status("llama3")
        assert status["code"] == ollama_manager.OLLAMA_STATUS_STOPPED
        assert status["installed"] is True
        assert status["running"] is False


def test_check_ollama_status_model_missing() -> None:
    """When service is running but model is missing, returns MODEL_MISSING status."""
    with (
        patch("docsummarizer.ollama_manager.find_ollama_executable", return_value=MagicMock()),
        patch("docsummarizer.ollama_manager.get_available_ollama_models", return_value=["qwen2.5"]),
        patch("docsummarizer.ollama_manager._ping_ollama", return_value=True),
    ):
        status = ollama_manager.check_ollama_status("llama3")
        assert status["code"] == ollama_manager.OLLAMA_STATUS_MODEL_MISSING
        assert status["installed"] is True
        assert status["running"] is True
        assert status["model_present"] is False


def test_check_ollama_status_ready() -> None:
    """When service is running and model is present, returns READY status."""
    with (
        patch("docsummarizer.ollama_manager.find_ollama_executable", return_value=MagicMock()),
        patch(
            "docsummarizer.ollama_manager.get_available_ollama_models",
            return_value=["llama3:latest"],
        ),
        patch("docsummarizer.ollama_manager._ping_ollama", return_value=True),
    ):
        status = ollama_manager.check_ollama_status("llama3")
        assert status["code"] == ollama_manager.OLLAMA_STATUS_READY
        assert status["installed"] is True
        assert status["running"] is True
        assert status["model_present"] is True
