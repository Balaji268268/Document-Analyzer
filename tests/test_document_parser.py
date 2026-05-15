"""Tests for `docsummarizer.document_parser`."""

from __future__ import annotations

from pathlib import Path

import pytest

from docsummarizer.document_parser import (
    SUPPORTED_EXTENSIONS,
    extract_text,
    get_document_info,
)


def test_extract_unsupported_extension(tmp_path: Path) -> None:
    target = tmp_path / "thing.xyz"
    target.write_text("doesn't matter")
    text, error = extract_text(str(target))
    assert text == ""
    assert error is not None
    assert "Unsupported" in error


def test_extract_missing_file(tmp_path: Path) -> None:
    text, error = extract_text(str(tmp_path / "nope.txt"))
    assert text == ""
    assert error is not None
    assert "not found" in error.lower()


def test_extract_txt_utf8(tmp_path: Path) -> None:
    target = tmp_path / "hello.txt"
    target.write_text("hello world\n", encoding="utf-8")
    text, error = extract_text(str(target))
    assert error is None
    assert "hello world" in text


def test_extract_txt_latin1_encoding_detection(tmp_path: Path) -> None:
    target = tmp_path / "latin.txt"
    # Write text that's not valid UTF-8 — chardet should pick up latin-1
    # (or similar) and decode it.
    target.write_bytes("caf\xe9 m\xfcnchen\n".encode("latin-1"))
    text, error = extract_text(str(target))
    assert error is None
    # We don't promise exact decoding, only that we got *something*
    # printable and didn't choke.
    assert "caf" in text.lower()


def test_extract_md_routes_to_txt(tmp_path: Path) -> None:
    target = tmp_path / "notes.md"
    target.write_text("# heading\n\nbody\n", encoding="utf-8")
    text, error = extract_text(str(target))
    assert error is None
    assert "heading" in text


def test_extract_docx_basic(tmp_path: Path) -> None:
    docx = pytest.importorskip("docx")
    target = tmp_path / "doc.docx"
    document = docx.Document()
    document.add_paragraph("first paragraph")
    document.add_paragraph("second paragraph")
    document.save(str(target))

    text, error = extract_text(str(target))
    assert error is None
    assert "first paragraph" in text
    assert "second paragraph" in text


def test_extract_rtf_basic(tmp_path: Path) -> None:
    pytest.importorskip("striprtf")
    target = tmp_path / "doc.rtf"
    target.write_text(r"{\rtf1\ansi hello rtf body}", encoding="utf-8")
    text, error = extract_text(str(target))
    assert error is None
    assert "hello rtf body" in text


def test_legacy_doc_not_supported(tmp_path: Path) -> None:
    """`.doc` (binary OLE) was dropped: python-docx can't read it."""
    target = tmp_path / "old.doc"
    target.write_bytes(b"\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1")  # OLE magic
    text, error = extract_text(str(target))
    assert text == ""
    assert error is not None
    assert "Unsupported" in error


def test_supported_extensions_excludes_doc() -> None:
    """Dialog filter must match the parser dispatch."""
    all_listed = " ".join(f for _label, f in SUPPORTED_EXTENSIONS)
    assert "*.doc " not in all_listed
    assert "*.doc," not in all_listed
    # `.docx` should still appear (substring is fine; we just want absence of
    # the bare `.doc` token).


def test_get_document_info_existing(tmp_path: Path) -> None:
    target = tmp_path / "f.txt"
    payload = b"x" * 2048  # exactly 2 KiB
    target.write_bytes(payload)

    info = get_document_info(str(target))
    assert info["name"] == "f.txt"
    assert info["extension"] == ".txt"
    assert info["size_bytes"] == 2048
    assert info["size_mb"] == round(2048 / (1024 * 1024), 2)


def test_get_document_info_missing(tmp_path: Path) -> None:
    info = get_document_info(str(tmp_path / "missing.txt"))
    assert info["size_bytes"] == 0
    assert info["size_mb"] == 0
