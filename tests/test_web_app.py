"""Tests for web_app module REST API and HTTP handlers."""

from __future__ import annotations

import io
import json
from unittest.mock import MagicMock

from docsummarizer.web_app import DocSummarizerWebHandler


def test_web_handler_health_check() -> None:
    """Test /api/health GET endpoint returns 200 OK."""
    handler = MagicMock()
    handler.path = "/api/health"
    handler._send_json = MagicMock()

    DocSummarizerWebHandler.do_GET(handler)
    handler._send_json.assert_called_once_with({
        "status": "healthy",
        "service": "DocSummarizer Web API",
    })


def test_web_handler_summarize_endpoint() -> None:
    """Test /api/summarize POST endpoint returns structured summary."""
    handler = MagicMock()
    handler.path = "/api/summarize"
    mock_body = json.dumps(
        {"text": "This is a test document text.", "summary_type": "detailed"}
    ).encode("utf-8")
    handler.headers = {"Content-Length": str(len(mock_body))}
    handler.rfile = io.BytesIO(mock_body)
    handler._send_json = MagicMock()

    DocSummarizerWebHandler.do_POST(handler)
    handler._send_json.assert_called_once()
    args, _ = handler._send_json.call_args
    assert args[0]["success"] is True
    assert "summary" in args[0]


def test_web_handler_summarize_empty_text() -> None:
    """Test /api/summarize POST endpoint returns 400 when text is empty."""
    handler = MagicMock()
    handler.path = "/api/summarize"
    mock_body = json.dumps({"text": ""}).encode("utf-8")
    handler.headers = {"Content-Length": str(len(mock_body))}
    handler.rfile = io.BytesIO(mock_body)
    handler._send_json = MagicMock()

    DocSummarizerWebHandler.do_POST(handler)
    handler._send_json.assert_called_once_with(
        {"error": "No text provided for summarization."}, status=400
    )


def test_web_handler_parse_file_endpoint() -> None:
    """Test /api/parse POST endpoint parses file content."""
    handler = MagicMock()
    handler.path = "/api/parse"
    mock_body = json.dumps(
        {"filename": "test.txt", "content_bytes": list(b"Sample document text.")}
    ).encode("utf-8")
    handler.headers = {
        "Content-Type": "application/json",
        "Content-Length": str(len(mock_body)),
    }
    handler.rfile = io.BytesIO(mock_body)
    handler._send_json = MagicMock()

    DocSummarizerWebHandler.do_POST(handler)
    handler._send_json.assert_called_once()
    args, _ = handler._send_json.call_args
    assert args[0]["success"] is True
    assert args[0]["filename"] == "test.txt"


def test_web_handler_not_found() -> None:
    """Test invalid POST endpoint calls send_error 404."""
    handler = MagicMock()
    handler.path = "/api/unknown"
    handler.send_error = MagicMock()

    DocSummarizerWebHandler.do_POST(handler)
    handler.send_error.assert_called_once()
