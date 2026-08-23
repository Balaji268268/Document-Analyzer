"""Unit tests for docsummarizer.dependency_manager."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from docsummarizer import dependency_manager


def test_check_missing_dependencies_all_present() -> None:
    """When all requested modules exist, check_missing_dependencies returns an empty list."""
    missing = dependency_manager.check_missing_dependencies(["sys", "os", "pathlib"])
    assert missing == []


def test_check_missing_dependencies_detects_missing() -> None:
    """When a non-existent module is checked, it returns a dict with details."""
    missing = dependency_manager.check_missing_dependencies(["non_existent_fake_module_12345"])
    assert len(missing) == 1
    assert missing[0]["module"] == "non_existent_fake_module_12345"
    assert missing[0]["package"] == "non_existent_fake_module_12345"


def test_module_to_pip_mapping() -> None:
    """Verify known module to pip package mappings."""
    assert dependency_manager.MODULE_TO_PIP_MAP.get("docx") == "python-docx"
    assert dependency_manager.MODULE_TO_PIP_MAP.get("llama_cpp") == "llama-cpp-python"
    assert dependency_manager.MODULE_TO_PIP_MAP.get("pypdf") == "pypdf"


@patch("docsummarizer.dependency_manager.subprocess.Popen")
def test_install_package_success(mock_popen: MagicMock) -> None:
    """Test successful package installation via pip."""
    proc_mock = MagicMock()
    proc_mock.stdout.readline.side_effect = ["Successfully installed test-pkg\n", ""]
    proc_mock.wait.return_value = 0
    proc_mock.returncode = 0
    mock_popen.return_value = proc_mock

    success, msg = dependency_manager.install_package("test-pkg")
    assert success is True
    assert "Successfully installed test-pkg" in msg
