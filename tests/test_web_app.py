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

    DocSummarizerWebHandler.do_GET(handler)
    handler._send_json.assert_called_once_with(
        {
            "status": "healthy",
            "service": "DocSummarizer Web API",
        }
    )


def test_web_handler_summarize_endpoint() -> None:
    """Test /api/summarize POST endpoint returns structured summary."""
    handler = MagicMock()
    mock_body = json.dumps(
        {"text": "This is a test document text.", "summary_type": "detailed"}
    ).encode("utf-8")
    handler.headers = {"Content-Length": str(len(mock_body))}
    handler.rfile = io.BytesIO(mock_body)

    DocSummarizerWebHandler._handle_summarize(handler)
    handler._send_json.assert_called_once()
    args, _ = handler._send_json.call_args
    assert args[0]["success"] is True
    assert "summary" in args[0]


def test_web_handler_summarize_empty_text() -> None:
    """Test /api/summarize POST endpoint returns 400 when text is empty."""
    handler = MagicMock()
    mock_body = json.dumps({"text": ""}).encode("utf-8")
    handler.headers = {"Content-Length": str(len(mock_body))}
    handler.rfile = io.BytesIO(mock_body)

    DocSummarizerWebHandler._handle_summarize(handler)
    handler._send_json.assert_called_once_with(
        {"error": "No text provided for summarization."}, status=400
    )


def test_web_handler_parse_file_endpoint() -> None:
    """Test /api/parse POST endpoint parses file content."""
    handler = MagicMock()
    mock_body = json.dumps(
        {"filename": "test.txt", "content_bytes": list(b"Sample document text.")}
    ).encode("utf-8")
    handler.headers = {
        "Content-Type": "application/json",
        "Content-Length": str(len(mock_body)),
    }
    handler.rfile = io.BytesIO(mock_body)

    DocSummarizerWebHandler._handle_parse_file(handler)
    handler._send_json.assert_called_once()
    args, _ = handler._send_json.call_args
    assert args[0]["success"] is True
    assert args[0]["filename"] == "test.txt"


def test_web_handler_do_post_routing() -> None:
    """Test do_POST routes endpoints correctly."""
    handler = MagicMock()
    handler.path = "/api/summarize"
    DocSummarizerWebHandler.do_POST(handler)
    handler._handle_summarize.assert_called_once()

    handler_parse = MagicMock()
    handler_parse.path = "/api/parse"
    DocSummarizerWebHandler.do_POST(handler_parse)
    handler_parse._handle_parse_file.assert_called_once()


def test_web_handler_not_found() -> None:
    """Test invalid POST endpoint calls send_error 404."""
    handler = MagicMock()
    handler.path = "/api/unknown"

    DocSummarizerWebHandler.do_POST(handler)
    handler.send_error.assert_called_once()


def test_web_handler_translate_path() -> None:
    """Test URL translation to static web directory."""
    handler = MagicMock()
    index_path = DocSummarizerWebHandler.translate_path(handler, "/")
    assert "index.html" in index_path

    asset_path = DocSummarizerWebHandler.translate_path(handler, "/style.css")
    assert "style.css" in asset_path


def test_web_handler_send_json() -> None:
    """Test _send_json formats response headers and body."""
    handler = MagicMock()
    handler.wfile = io.BytesIO()

    DocSummarizerWebHandler._send_json(handler, {"result": "ok"}, status=200)
    handler.send_response.assert_called_once_with(200)
    handler.send_header.assert_any_call("Content-Type", "application/json; charset=utf-8")
    assert b'{"result": "ok"}' in handler.wfile.getvalue()


def test_web_handler_parse_file_multipart_error() -> None:
    """Test _handle_parse_file returns error when multipart is passed."""
    handler = MagicMock()
    handler.headers = {"Content-Type": "multipart/form-data; boundary=something"}
    handler.rfile = io.BytesIO(b"data")

    DocSummarizerWebHandler._handle_parse_file(handler)
    handler._send_json.assert_called_once_with(
        {"error": "Please send JSON body with base64/text content."}, status=400
    )


def test_web_handler_summarize_exception_handling() -> None:
    """Test _handle_summarize catches exceptions and returns 500 status."""
    handler = MagicMock()
    handler.headers = {"Content-Length": "invalid"}

    DocSummarizerWebHandler._handle_summarize(handler)
    handler._send_json.assert_called_once()
    _args, kwargs = handler._send_json.call_args
    assert kwargs.get("status") == 500
