"""Ollama health detector, service manager, model manager, and installer for DocSummarizer.

Provides comprehensive, non-blocking environment management for Ollama:
- Detection of executable, HTTP service status (11434), and available models.
- Automatic background service starting.
- Automatic download and silent background installation of Ollama.
- Model pulling and progress streaming.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.request
from collections.abc import Callable
from pathlib import Path

from docsummarizer.logger import log_error, log_info

OLLAMA_STATUS_READY = "READY"
OLLAMA_STATUS_STOPPED = "STOPPED"
OLLAMA_STATUS_NOT_INSTALLED = "NOT_INSTALLED"
OLLAMA_STATUS_MODEL_MISSING = "MODEL_MISSING"

OLLAMA_BASE_URL = "http://localhost:11434"
OLLAMA_INSTALLER_URL = "https://ollama.com/download/OllamaSetup.exe"
DEFAULT_OLLAMA_MODEL = "llama3"


def find_ollama_executable() -> Path | None:
    """Locate the Ollama executable on PATH or standard installation locations."""
    which_path = shutil.which("ollama")
    if which_path:
        return Path(which_path)

    if sys.platform == "win32":
        local_app_data = os.environ.get("LOCALAPPDATA", "")
        if local_app_data:
            candidate = Path(local_app_data) / "Programs" / "Ollama" / "ollama.exe"
            if candidate.exists():
                return candidate
        program_files = os.environ.get("PROGRAMFILES", "C:\\Program Files")
        candidate_pf = Path(program_files) / "Ollama" / "ollama.exe"
        if candidate_pf.exists():
            return candidate_pf
    else:
        candidates = [
            Path.home() / ".local" / "bin" / "ollama",
            Path("/usr/local/bin/ollama"),
            Path("/usr/bin/ollama"),
        ]
        for cand in candidates:
            if cand.exists():
                return cand

    return None


def get_available_ollama_models(host: str = OLLAMA_BASE_URL) -> list[str]:
    """Query the Ollama API (/api/tags) for currently installed models."""
    url = f"{host}/api/tags"
    req = urllib.request.Request(url, headers={"User-Agent": "DocSummarizer"})
    try:
        with urllib.request.urlopen(req, timeout=3) as resp:
            if resp.status == 200:
                data = json.loads(resp.read().decode("utf-8"))
                models = data.get("models", [])
                names: list[str] = []
                for m in models:
                    name = m.get("name", "")
                    if name:
                        names.append(name)
                        if ":" in name:
                            names.append(name.split(":", maxsplit=1)[0])
                return names
    except Exception as exc:
        log_info(f"Ollama API /api/tags unreachable: {exc}")

    return []


def check_ollama_status(
    model_name: str = DEFAULT_OLLAMA_MODEL,
    host: str = OLLAMA_BASE_URL,
) -> dict[str, str | bool | list[str]]:
    """Determine comprehensive Ollama environment status."""
    exe_path = find_ollama_executable()
    installed = exe_path is not None
    available_models = get_available_ollama_models(host)
    running = len(available_models) > 0 or _ping_ollama(host)

    if not installed and not running:
        return {
            "code": OLLAMA_STATUS_NOT_INSTALLED,
            "message": "Ollama is not installed on this machine.",
            "installed": False,
            "running": False,
            "model_present": False,
            "exe_path": "",
            "models": [],
        }

    if installed and not running:
        return {
            "code": OLLAMA_STATUS_STOPPED,
            "message": "Ollama is installed, but the background service is not running.",
            "installed": True,
            "running": False,
            "model_present": False,
            "exe_path": str(exe_path),
            "models": [],
        }

    target_clean = model_name.split(":", maxsplit=1)[0].lower()
    model_present = any(target_clean in m.lower() for m in available_models)

    if not model_present:
        return {
            "code": OLLAMA_STATUS_MODEL_MISSING,
            "message": f"Ollama service is active, but required model '{model_name}' is not found.",
            "installed": True,
            "running": True,
            "model_present": False,
            "exe_path": str(exe_path) if exe_path else "system",
            "models": available_models,
        }

    return {
        "code": OLLAMA_STATUS_READY,
        "message": f"Ollama is ready and model '{model_name}' is loaded.",
        "installed": True,
        "running": True,
        "model_present": True,
        "exe_path": str(exe_path) if exe_path else "system",
        "models": available_models,
    }


def _ping_ollama(host: str = OLLAMA_BASE_URL) -> bool:
    """Check if HTTP service at host is alive."""
    try:
        with urllib.request.urlopen(f"{host}/", timeout=2) as resp:
            return bool(resp.status == 200)
    except Exception:
        return False


def start_ollama_service() -> bool:
    """Launch Ollama background service if installed."""
    exe_path = find_ollama_executable()
    if not exe_path:
        log_error("start_ollama_service: cannot start because Ollama is not installed")
        return False

    log_info(f"Launching Ollama service from {exe_path}")
    creation_flags = 0
    if sys.platform == "win32":
        creation_flags = getattr(subprocess, "CREATE_NO_WINDOW", 0x08000000)

    try:
        subprocess.Popen(  # noqa: S603
            [str(exe_path), "serve"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            creationflags=creation_flags,
        )
    except Exception as exc:
        log_error(f"Failed to start Ollama service process: {exc}")
        return False
    else:
        return True


def _install_ollama_linux(
    progress_callback: Callable[[float, str], None] | None = None,
) -> tuple[bool, str]:
    if progress_callback:
        progress_callback(20.0, "Executing Linux Ollama installer script...")

    if find_ollama_executable():
        start_ollama_service()
        if progress_callback:
            progress_callback(100.0, "Ollama is already installed and service launched!")
        return True, "Ollama is already installed."

    cmd = "curl -fsSL https://ollama.com/install.sh | sh"
    if hasattr(os, "geteuid") and os.geteuid() != 0 and shutil.which("sudo"):
        cmd = "curl -fsSL https://ollama.com/install.sh | sudo -E sh"

    try:
        res = subprocess.run(  # noqa: S603
            ["sh", "-c", cmd],  # noqa: S607
            capture_output=True,
            text=True,
            check=False,
        )
        if res.returncode == 0:
            start_ollama_service()
            if progress_callback:
                progress_callback(100.0, "Ollama installed successfully!")
            return True, "Ollama installed successfully."
    except Exception as exc:
        log_info(f"Linux install.sh execution failed: {exc}")

    # Fallback for rootless containers/Render: download standalone user-space Ollama binary
    if progress_callback:
        progress_callback(50.0, "Downloading standalone user-space Ollama binary...")

    try:
        user_bin_dir = Path.home() / ".local" / "bin"
        user_bin_dir.mkdir(parents=True, exist_ok=True)
        tar_path = Path(tempfile.gettempdir()) / "ollama-linux-amd64.tgz"

        dl_cmd = f"curl -fsSL https://ollama.com/download/ollama-linux-amd64.tgz -o {tar_path} && tar -C {user_bin_dir} -xzf {tar_path}"
        res_user = subprocess.run(  # noqa: S603
            ["sh", "-c", dl_cmd],  # noqa: S607
            capture_output=True,
            text=True,
            check=False,
        )
    except Exception as exc:
        return False, f"User-space installation error: {exc}"
    else:
        if res_user.returncode == 0:
            start_ollama_service()
            if progress_callback:
                progress_callback(100.0, "Standalone Ollama binary installed!")
            return True, "Standalone Ollama binary installed successfully."
        output_msg = res_user.stderr.strip() or res_user.stdout.strip()
        return False, f"Ollama installation failed: {output_msg}"


def _install_ollama_windows(
    progress_callback: Callable[[float, str], None] | None = None,
) -> tuple[bool, str]:
    if progress_callback:
        progress_callback(10.0, "Connecting to Ollama download server...")

    log_info(f"Downloading Ollama installer from {OLLAMA_INSTALLER_URL}")
    temp_dir = Path(tempfile.gettempdir())
    installer_path = temp_dir / "OllamaSetup.exe"

    try:
        req = urllib.request.Request(OLLAMA_INSTALLER_URL, headers={"User-Agent": "DocSummarizer"})
        with urllib.request.urlopen(req, timeout=60) as resp:
            total_size = int(resp.headers.get("Content-Length", 0))
            downloaded = 0
            block_size = 1024 * 64

            with installer_path.open("wb") as out_file:
                while True:
                    chunk = resp.read(block_size)
                    if not chunk:
                        break
                    out_file.write(chunk)
                    downloaded += len(chunk)
                    if total_size > 0 and progress_callback:
                        pct = 10.0 + (downloaded / total_size) * 75.0
                        mb_done = downloaded / (1024 * 1024)
                        mb_total = total_size / (1024 * 1024)
                        progress_callback(
                            pct, f"Downloading Ollama: {mb_done:.1f} / {mb_total:.1f} MB"
                        )

        if progress_callback:
            progress_callback(88.0, "Running automated silent Ollama setup...")

        log_info(f"Launching silent installer executable: {installer_path}")
        proc = subprocess.Popen([str(installer_path), "/S"])  # noqa: S603
        proc.wait()

        if progress_callback:
            progress_callback(95.0, "Verifying Ollama installation & starting service...")

        for _ in range(10):
            if find_ollama_executable():
                start_ollama_service()
                time.sleep(2)
                if progress_callback:
                    progress_callback(100.0, "Ollama installed & service active!")
                return True, "Ollama installed and background service started."
            time.sleep(1)

    except Exception as exc:
        log_error(f"Ollama download/install failed: {exc}")
        return False, f"Download failed: {exc}"

    if progress_callback:
        progress_callback(100.0, "Installer completed. Please click Check Again.")
    return True, "Installer executed successfully."


def download_and_install_ollama(
    progress_callback: Callable[[float, str], None] | None = None,
) -> tuple[bool, str]:
    """Download official Ollama installer and execute silent automated installation."""
    if sys.platform == "win32":
        return _install_ollama_windows(progress_callback)
    else:  # noqa: RET505
        return _install_ollama_linux(progress_callback)


def pull_ollama_model(  # noqa: PLR0912
    model_name: str = DEFAULT_OLLAMA_MODEL,
    progress_callback: Callable[[float, str], None] | None = None,
    host: str = OLLAMA_BASE_URL,
) -> tuple[bool, str]:
    """Pull an AI model via HTTP API stream or CLI."""
    if progress_callback:
        progress_callback(5.0, f"Requesting model '{model_name}' download...")

    url = f"{host}/api/pull"
    payload = json.dumps({"name": model_name, "stream": True}).encode("utf-8")
    req = urllib.request.Request(url, data=payload, headers={"Content-Type": "application/json"})

    try:
        with urllib.request.urlopen(req, timeout=600) as resp:
            for line in resp:
                line_str = line.decode("utf-8").strip()
                if not line_str:
                    continue
                try:
                    data = json.loads(line_str)
                    status_text = data.get("status", "")
                    total = data.get("total", 0)
                    completed = data.get("completed", 0)

                    if total > 0 and progress_callback:
                        pct = (completed / total) * 100.0
                        progress_callback(
                            pct, f"Downloading {model_name}: {status_text} ({pct:.0f}%)"
                        )
                    elif progress_callback and status_text:
                        progress_callback(50.0, f"{model_name}: {status_text}")
                except json.JSONDecodeError:
                    pass
    except Exception as exc:
        log_info(f"HTTP pull failed ({exc}), falling back to CLI 'ollama pull {model_name}'")
        exe_path = find_ollama_executable()
        if not exe_path:
            return False, f"Ollama not found to pull {model_name}"

        try:
            cmd = [str(exe_path), "pull", model_name]
            proc = subprocess.Popen(  # noqa: S603
                cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True
            )
            if proc.stdout:
                for line in iter(proc.stdout.readline, ""):
                    if line.strip() and progress_callback:
                        progress_callback(50.0, f"Pulling: {line.strip()[:60]}")
            proc.wait()
        except Exception as cli_exc:
            log_error(f"CLI pull failed: {cli_exc}")
            return False, str(cli_exc)
        else:
            if proc.returncode == 0:
                if progress_callback:
                    progress_callback(100.0, f"Model '{model_name}' downloaded.")
                return True, f"Model '{model_name}' pulled."
            return False, f"CLI pull exited with code {proc.returncode}"
    else:
        if progress_callback:
            progress_callback(100.0, f"Model '{model_name}' successfully downloaded.")
        return True, f"Model '{model_name}' ready."
