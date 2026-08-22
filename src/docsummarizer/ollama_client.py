"""Ollama API Client Module for Document-Analyzer.

Provides HTTP client integration to connect with Ollama instances (local
or remote cloud server) for LLM text generation and structured JSON summarization.
"""

# ruff: noqa: S310, PLR0917

import json
import os
import urllib.request
from typing import Any

from .logger import log_debug, log_error, log_info


def get_ollama_host() -> str:
    """Get the active Ollama host endpoint."""
    return os.getenv("OLLAMA_HOST", "http://localhost:11434").rstrip("/")


def get_ollama_model() -> str:
    """Get the active Ollama model name."""
    return os.getenv("OLLAMA_MODEL", "llama3")


def is_ollama_available(host: str | None = None, timeout: float = 3.0) -> bool:
    """Check if the Ollama service is reachable."""
    target_host = (host or get_ollama_host()).rstrip("/")
    url = f"{target_host}/api/tags"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Document-Analyzer"})
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.status == 200
    except Exception as exc:
        log_debug(f"Ollama health check failed for {target_host}: {exc!s}")
        return False


def query_ollama(
    prompt: str,
    system_prompt: str | None = None,
    model: str | None = None,
    json_mode: bool = False,
    host: str | None = None,
    timeout: float = 60.0,
) -> str:
    """Send a generation request to the Ollama API.

    Args:
        prompt: The main user prompt text.
        system_prompt: Optional system instruction.
        model: Model name (defaults to OLLAMA_MODEL or llama3).
        json_mode: If True, instructs Ollama to format output as JSON.
        host: Ollama server endpoint (defaults to OLLAMA_HOST or http://localhost:11434).
        timeout: Request timeout in seconds.

    Returns:
        The generated text response.
    """
    target_host = (host or get_ollama_host()).rstrip("/")
    target_model = model or get_ollama_model()
    url = f"{target_host}/api/generate"

    payload: dict[str, Any] = {
        "model": target_model,
        "prompt": prompt,
        "stream": False,
    }
    if system_prompt:
        payload["system"] = system_prompt
    if json_mode:
        payload["format"] = "json"

    log_info(f"Sending prompt to Ollama ({target_model}) at {target_host}")

    try:
        data_bytes = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            url,
            data=data_bytes,
            headers={
                "Content-Type": "application/json",
                "User-Agent": "Document-Analyzer",
            },
        )
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            body = resp.read().decode("utf-8")
            result = json.loads(body)
            return str(result.get("response", "")).strip()
    except Exception as exc:
        log_error(f"Ollama API request failed: {exc!s}")
        raise
