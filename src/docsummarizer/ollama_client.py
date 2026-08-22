"""Ollama API Client & Auto-Tunnel Module for Document-Analyzer.

Provides HTTP client integration to connect with Ollama instances (local
or remote cloud server) for LLM text generation and structured JSON summarization.
Automatically manages background Cloudflare tunnels for zero-configuration setup.
"""

# ruff: noqa: S310, PLR0917, S603, PLW0603

import json
import os
import re
import subprocess
import threading
import time
import urllib.request
from pathlib import Path
from typing import Any

from .logger import log_debug, log_error, log_info

_TUNNEL_PROCESS: subprocess.Popen[str] | None = None
_TUNNEL_URL: str | None = None


def start_auto_tunnel() -> str | None:
    """Auto-launch background Cloudflare tunnel to local Ollama if not running.

    Returns:
        The live public trycloudflare.com URL, or None if tunnel setup failed.
    """
    global _TUNNEL_PROCESS
    if _TUNNEL_URL:
        return _TUNNEL_URL

    root_dir = Path(__file__).parent.parent.parent
    cloudflared_bin = root_dir / "cloudflared.exe"
    bin_path = str(cloudflared_bin) if cloudflared_bin.exists() else "cloudflared"

    try:
        cmd = [
            bin_path,
            "tunnel",
            "--protocol",
            "http2",
            "--url",
            "http://localhost:11434",
        ]
        _TUNNEL_PROCESS = subprocess.Popen(
            cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True
        )

        def _capture_tunnel_url():
            global _TUNNEL_URL
            if _TUNNEL_PROCESS and _TUNNEL_PROCESS.stdout:
                for line in _TUNNEL_PROCESS.stdout:
                    match = re.search(r"https://[a-zA-Z0-9-]+\.trycloudflare\.com", line)
                    if match:
                        _TUNNEL_URL = match.group(0)
                        os.environ["OLLAMA_HOST"] = _TUNNEL_URL
                        log_info(f"Auto-tunnel started: {_TUNNEL_URL}")
                        break

        thread = threading.Thread(target=_capture_tunnel_url, daemon=True)
        thread.start()

        start_time = time.time()
        while not _TUNNEL_URL and time.time() - start_time < 10.0:
            time.sleep(0.5)
    except Exception as exc:
        log_debug(f"Auto-tunnel initialization skipped: {exc!s}")

    return _TUNNEL_URL


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
    """Send a generation request to the Ollama API."""
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
