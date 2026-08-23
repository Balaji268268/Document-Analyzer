"""Production-grade Web Server & REST API for DocSummarizer.

Provides a responsive, high-performance HTML5 web interface for uploading
documents (.pdf, .docx, .rtf, .txt) and generating structured summaries
with sentence grounding citations.
"""

from __future__ import annotations

import json
import os
import sys
import tempfile
import time
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from http import HTTPStatus
from http.server import HTTPServer, SimpleHTTPRequestHandler
from pathlib import Path
from socketserver import ThreadingMixIn
from typing import Any
from urllib.parse import urlparse

# Ensure src/ is on Python path
CURRENT_DIR = Path(__file__).resolve().parent
PACKAGE_ROOT = CURRENT_DIR.parent
if str(PACKAGE_ROOT) not in sys.path:
    sys.path.insert(0, str(PACKAGE_ROOT))

from docsummarizer.document_parser import extract_text  # noqa: E402
from docsummarizer.logger import log_error, log_info  # noqa: E402
from docsummarizer.model_manager import SummaryPoint  # noqa: E402
from docsummarizer.provenance import locate_quote, split_sentences  # noqa: E402

WEB_STATIC_DIR = CURRENT_DIR / "web"


@dataclass
class SessionState:
    """Isolated session workspace state for each user browser session."""

    session_id: str
    current_filename: str = ""
    extracted_text: str = ""
    history: list[dict[str, Any]] = field(default_factory=list)
    created_at: float = field(default_factory=time.time)


SESSIONS: dict[str, SessionState] = {}


class ThreadedHTTPServer(ThreadingMixIn, HTTPServer):
    """Multi-threaded HTTP Server for concurrency."""

    daemon_threads = True


class DocSummarizerWebHandler(SimpleHTTPRequestHandler):
    """HTTP Request Handler serving static web assets and REST APIs."""

    def translate_path(self, path: str) -> str:
        """Translate URL path to web static directory files."""
        parsed = urlparse(path)
        rel_path = parsed.path.lstrip("/")
        if not rel_path or rel_path == "index.html":
            return str(WEB_STATIC_DIR / "index.html")
        return str(WEB_STATIC_DIR / rel_path)

    def _get_session(self) -> SessionState:
        """Resolve or create isolated SessionState using doc_session_id cookie."""
        cookie_header = self.headers.get("Cookie", "")
        session_id = None
        if "doc_session_id=" in cookie_header:
            for item in cookie_header.split(";"):
                cookie = item.strip()
                if cookie.startswith("doc_session_id="):
                    session_id = cookie.split("=", 1)[1].strip()
                    break

        if not session_id or session_id not in SESSIONS:
            session_id = str(uuid.uuid4())
            SESSIONS[session_id] = SessionState(session_id=session_id)

        return SESSIONS[session_id]

    def do_GET(self) -> None:
        """Handle GET requests for web pages, history, and static assets."""
        parsed = urlparse(self.path)
        session = self._get_session()
        if parsed.path == "/api/health":
            self._send_json(
                {"status": "healthy", "service": "DocSummarizer Web API"},
                session_id=session.session_id,
            )
            return

        if parsed.path == "/api/history":
            self._send_json(
                {"success": True, "history": session.history},
                session_id=session.session_id,
            )
            return

        # Fallback to standard static file server
        super().do_GET()

    def do_POST(self) -> None:
        """Handle POST requests for document parsing and summarization."""
        parsed = urlparse(self.path)
        if parsed.path == "/api/summarize":
            self._handle_summarize()
            return
        if parsed.path == "/api/parse":
            self._handle_parse_file()
            return

        self.send_error(HTTPStatus.NOT_FOUND, "Endpoint not found")

    def do_DELETE(self) -> None:
        """Handle DELETE requests (clearing session history)."""
        parsed = urlparse(self.path)
        session = self._get_session()
        if parsed.path == "/api/history":
            session.history.clear()
            self._send_json(
                {"success": True, "history": []},
                session_id=session.session_id,
            )
            return

        self.send_error(HTTPStatus.NOT_FOUND, "Endpoint not found")

    def _handle_summarize(self) -> None:
        """Handle text/document summarization request."""
        session = self._get_session()
        try:
            content_length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(content_length)
            data = json.loads(body.decode("utf-8"))

            text = data.get("text", "").strip()
            filename = data.get("filename", session.current_filename or "Document").strip()
            summary_type = data.get("summary_type", "detailed").lower()

            if not text:
                self._send_json(
                    {"error": "No text provided for summarization."},
                    status=400,
                    session_id=session.session_id,
                )
                return

            log_info(
                f"Web API [Session {session.session_id[:8]}]: Summarizing text of length {len(text)} ({summary_type})"
            )

            sentences = split_sentences(text)

            summary_dict: dict[str, Any] = {}
            try:
                from docsummarizer.model_manager import Summarizer

                summarizer = Summarizer()
                raw_summary = summarizer.summarize_structured(text, summary_type=summary_type)
                if isinstance(raw_summary, dict):
                    summary_dict = dict(raw_summary)
                summary_text = str(summary_dict.get("text", ""))
            except Exception as exc:
                log_error(f"LLM Summarizer engine fallback: {exc}")
                points: list[SummaryPoint] = []
                for sent_start, sent_end in sentences[:5]:
                    sent_text = text[sent_start:sent_end].strip()
                    if len(sent_text) > 10:
                        points.append(SummaryPoint(text=sent_text))

                lead_text = text[:300] if len(text) > 300 else text
                summary_text = "\n".join(f"- {pt.text}" for pt in points) if points else lead_text

                summary_dict = {
                    "summaryType": summary_type,
                    "lead": lead_text,
                    "points": [{"text": pt.text, "hasCitation": False} for pt in points],
                    "text": summary_text,
                }

            provenance: list[dict[str, object]] = []
            pts = summary_dict.get("points", [])
            if isinstance(pts, list):
                for pt in pts:
                    pt_text = pt.get("text", "") if isinstance(pt, dict) else str(pt)
                    if pt_text:
                        span = locate_quote(pt_text, text, sentences)
                        if span:
                            provenance.append(
                                {
                                    "summary_sentence": pt_text,
                                    "source_sentence": span.quote,
                                    "confidence": span.score,
                                }
                            )

            history_item = {
                "id": f"doc_{uuid.uuid4().hex[:8]}",
                "filename": filename,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "summary_type": summary_type,
                "word_count": len(text.split()),
                "char_count": len(text),
                "summary": summary_dict,
                "summary_text": summary_text,
                "provenance": provenance,
            }
            session.history.insert(0, history_item)

            response_data = {
                "success": True,
                "item": history_item,
                "summary": summary_dict,
                "summary_text": summary_text,
                "provenance": provenance,
                "word_count": len(text.split()),
                "char_count": len(text),
            }
            self._send_json(response_data, session_id=session.session_id)

        except Exception as exc:
            log_error(f"Web API /api/summarize error: {exc}")
            self._send_json(
                {"error": f"Failed to generate summary: {exc}"},
                status=500,
                session_id=session.session_id,
            )

    def _handle_parse_file(self) -> None:
        """Handle file upload and text extraction."""
        session = self._get_session()
        try:
            content_type = self.headers.get("Content-Type", "")
            content_length = int(self.headers.get("Content-Length", 0))
            raw_body = self.rfile.read(content_length)

            if "multipart/form-data" not in content_type:
                data = json.loads(raw_body.decode("utf-8"))
                filename = data.get("filename", "document.txt")
                content_bytes = data.get("content_bytes", b"")
            else:
                self._send_json(
                    {"error": "Please send JSON body with base64/text content."},
                    status=400,
                    session_id=session.session_id,
                )
                return

            with tempfile.NamedTemporaryFile(delete=False, suffix=Path(filename).suffix) as tmp:
                tmp.write(bytes(content_bytes))
                tmp_path = Path(tmp.name)

            extracted_text, _err = extract_text(str(tmp_path))
            tmp_path.unlink(missing_ok=True)

            session.current_filename = filename
            session.extracted_text = extracted_text

            self._send_json(
                {
                    "success": True,
                    "filename": filename,
                    "extracted_text": extracted_text,
                    "char_count": len(extracted_text),
                },
                session_id=session.session_id,
            )

        except Exception as exc:
            log_error(f"Web API /api/parse error: {exc}")
            self._send_json(
                {"error": f"Failed to parse document: {exc}"},
                status=500,
                session_id=session.session_id,
            )

    def _send_json(
        self,
        data: dict[str, object],
        status: int = 200,
        session_id: str | None = None,
    ) -> None:
        """Send JSON response with proper headers and session cookie."""
        body = json.dumps(data).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        if session_id:
            self.send_header(
                "Set-Cookie",
                f"doc_session_id={session_id}; Path=/; SameSite=Lax; HttpOnly",
            )
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, format_spec: str, *args: object) -> None:
        """Suppress noisy default HTTP logging."""


def run_web_server(port: int = 8080, host: str = "0.0.0.0") -> None:  # noqa: S104
    """Run the threaded HTTP web server."""
    WEB_STATIC_DIR.mkdir(parents=True, exist_ok=True)
    server_address: tuple[str, int] = (host, port)
    httpd = ThreadedHTTPServer(server_address, DocSummarizerWebHandler)
    log_info(f"DocSummarizer Web Server listening on http://{host}:{port}")
    print(f"🚀 DocSummarizer Web Server running on http://{host}:{port}")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down web server...")
        httpd.server_close()


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="DocSummarizer Web Server")
    parser.add_argument("--port", "-p", type=int, default=int(os.environ.get("PORT", "8080")))
    parser.add_argument("--host", default="0.0.0.0")  # noqa: S104
    args = parser.parse_args()
    run_web_server(port=args.port, host=args.host)
