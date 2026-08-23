"""Automatic Python package dependency resolver and installer for DocSummarizer.

Checks required Python modules at startup, maps module import names to PyPI package
names, installs missing dependencies using pip, and verifies imports cleanly.
"""

from __future__ import annotations

import importlib
import importlib.util
import subprocess
import sys
from collections.abc import Callable

from docsummarizer.logger import log_error, log_info

# Mapping of module import names to their official PyPI package names
MODULE_TO_PIP_MAP: dict[str, str] = {
    "pypdf": "pypdf",
    "docx": "python-docx",
    "striprtf": "striprtf",
    "chardet": "chardet",
    "huggingface_hub": "huggingface_hub",
    "tqdm": "tqdm",
    "psutil": "psutil",
    "PySide6": "PySide6",
    "requests": "requests",
    "llama_cpp": "llama-cpp-python",
    "yaml": "PyYAML",
    "PIL": "Pillow",
}

# Core required Python modules for DocSummarizer
CORE_REQUIRED_MODULES: list[str] = [
    "pypdf",
    "docx",
    "striprtf",
    "chardet",
    "huggingface_hub",
    "tqdm",
    "psutil",
    "PySide6",
    "requests",
]


def check_missing_dependencies(
    modules: list[str] | None = None,
) -> list[dict[str, str]]:
    """Check which required Python modules are missing or unimportable.

    Returns a list of dicts: ``[{"module": "docx", "package": "python-docx"}]``.
    """
    target_modules = modules if modules is not None else CORE_REQUIRED_MODULES
    missing: list[dict[str, str]] = []

    for mod_name in target_modules:
        try:
            importlib.import_module(mod_name)
        except Exception as exc:  # noqa: PERF203
            pip_pkg = MODULE_TO_PIP_MAP.get(mod_name, mod_name)
            log_info(f"Dependency check: module '{mod_name}' is missing ({exc})")
            missing.append(
                {
                    "module": mod_name,
                    "package": pip_pkg,
                    "reason": str(exc),
                }
            )

    return missing


def install_package(
    package_name: str,
    progress_callback: Callable[[float, str], None] | None = None,
) -> tuple[bool, str]:
    """Programmatically install a Python package using sys.executable -m pip.

    Returns ``(success: bool, output_message: str)``.
    """
    if progress_callback:
        progress_callback(10.0, f"Installing {package_name} via pip...")

    log_info(f"Auto-installer: running pip install {package_name}")
    cmd = [sys.executable, "-m", "pip", "install", package_name]

    # Hide console window on Windows GUI builds
    creation_flags = 0
    if sys.platform == "win32":
        creation_flags = getattr(subprocess, "CREATE_NO_WINDOW", 0x08000000)

    try:
        proc = subprocess.Popen(  # noqa: S603
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            creationflags=creation_flags,
        )

        output_lines: list[str] = []
        if proc.stdout:
            for line in iter(proc.stdout.readline, ""):
                line_str = line.strip()
                if line_str:
                    output_lines.append(line_str)
                    if progress_callback:
                        progress_callback(50.0, f"{package_name}: {line_str[:50]}")

        proc.wait(timeout=300)
        full_output = "\n".join(output_lines)
    except Exception as exc:
        log_error(f"Auto-installer: exception installing {package_name}: {exc}")
        return False, str(exc)
    else:
        if proc.returncode == 0:
            log_info(f"Auto-installer: successfully installed {package_name}")
            if progress_callback:
                progress_callback(100.0, f"Successfully installed {package_name}")
            return True, full_output
        log_error(f"Auto-installer: pip install {package_name} failed code {proc.returncode}")
        return False, full_output or f"pip exited with status code {proc.returncode}"


def auto_install_missing_dependencies(
    progress_callback: Callable[[float, str], None] | None = None,
) -> tuple[bool, list[dict[str, str]]]:
    """Verify and automatically install all missing Python dependencies.

    Returns ``(all_ok: bool, failed_packages: list[dict])``.
    """
    missing = check_missing_dependencies()
    if not missing:
        if progress_callback:
            progress_callback(100.0, "All Python dependencies verified.")
        return True, []

    total_count = len(missing)
    failed: list[dict[str, str]] = []

    for idx, item in enumerate(missing, start=1):
        mod_name = item["module"]
        pip_pkg = item["package"]

        pct = (idx / total_count) * 90.0
        if progress_callback:
            progress_callback(pct, f"Installing required component {idx}/{total_count}: {pip_pkg}")

        success, err_msg = install_package(pip_pkg, progress_callback)
        if success:
            # Re-verify import after installation
            try:
                importlib.invalidate_caches()
                importlib.import_module(mod_name)
            except Exception as exc:
                failed.append(
                    {
                        "module": mod_name,
                        "package": pip_pkg,
                        "reason": f"Import failed post-install: {exc}",
                    }
                )
        else:
            failed.append(
                {
                    "module": mod_name,
                    "package": pip_pkg,
                    "reason": err_msg,
                }
            )

    all_ok = len(failed) == 0
    if progress_callback:
        if all_ok:
            progress_callback(100.0, "All dependencies resolved and verified.")
        else:
            progress_callback(100.0, f"Dependency setup completed with {len(failed)} error(s).")

    return all_ok, failed
