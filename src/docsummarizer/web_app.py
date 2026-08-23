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
from http import HTTPStatus
from http.server import HTTPServer, SimpleHTTPRequestHandler
from pathlib import Path
from socketserver import ThreadingMixIn
from urllib.parse import urlparse

# Ensure src/ is on Python path
CURRENT_DIR = Path(__file__).resolve().parent
PACKAGE_ROOT = CURRENT_DIR.parent
if str(PACKAGE_ROOT) not in sys.path:
    sys.path.insert(0, str(PACKAGE_ROOT))

from docsummarizer.document_parser import extract_text  # noqa: E402
from docsummarizer.logger import log_error, log_info  # noqa: E402
from docsummarizer.provenance import locate_quote, split_sentences  # noqa: E402
from docsummarizer.structured_summary import (  # type: ignore[import-not-found]  # noqa: E402
    generate_structured_summary,
)

WEB_STATIC_DIR = CURRENT_DIR / "web"


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

    def do_GET(self) -> None:
        """Handle GET requests for web pages and static assets."""
        parsed = urlparse(self.path)
        if parsed.path == "/api/health":
            self._send_json({"status": "healthy", "service": "DocSummarizer Web API"})
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

    def _handle_summarize(self) -> None:
        """Handle text/document summarization request."""
        try:
            content_length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(content_length)
            data = json.loads(body.decode("utf-8"))

            text = data.get("text", "").strip()
            summary_type = data.get("summary_type", "detailed").lower()

            if not text:
                self._send_json({"error": "No text provided for summarization."}, status=400)
                return

            log_info(f"Web API: Summarizing text of length {len(text)} ({summary_type})")

            # Generate structured summary
            summary = generate_structured_summary(text, summary_type=summary_type)

            # Compute sentence grounding citations
            sentences = split_sentences(text)
            provenance: list[dict[str, object]] = []
            if summary.points:
                for pt in summary.points:
                    span = locate_quote(pt.text, text, sentences)
                    if span:
                        provenance.append(
                            {
                                "summary_sentence": pt.text,
                                "source_sentence": span.quote,
                                "confidence": span.score,
                            }
                        )

            response_data = {
                "success": True,
                "summary": summary.to_dict(),
                "summary_text": summary.to_text(),
                "provenance": provenance,
                "word_count": len(text.split()),
                "char_count": len(text),
            }
            self._send_json(response_data)

        except Exception as exc:
            log_error(f"Web API /api/summarize error: {exc}")
            self._send_json({"error": f"Failed to generate summary: {exc}"}, status=500)

    def _handle_parse_file(self) -> None:
        """Handle file upload and text extraction."""
        try:
            content_type = self.headers.get("Content-Type", "")
            content_length = int(self.headers.get("Content-Length", 0))
            raw_body = self.rfile.read(content_length)

            if "multipart/form-data" not in content_type:
                # Handle raw base64 or JSON upload
                data = json.loads(raw_body.decode("utf-8"))
                filename = data.get("filename", "document.txt")
                content_bytes = data.get("content_bytes", b"")
            else:
                self._send_json(
                    {"error": "Please send JSON body with base64/text content."}, status=400
                )
                return

            # Extract text using document parser
            with tempfile.NamedTemporaryFile(delete=False, suffix=Path(filename).suffix) as tmp:
                tmp.write(bytes(content_bytes))
                tmp_path = Path(tmp.name)

            extracted_text = extract_text(str(tmp_path))
            tmp_path.unlink(missing_ok=True)

            self._send_json(
                {
                    "success": True,
                    "filename": filename,
                    "extracted_text": extracted_text,
                    "char_count": len(extracted_text),
                }
            )

        except Exception as exc:
            log_error(f"Web API /api/parse error: {exc}")
            self._send_json({"error": f"Failed to parse document: {exc}"}, status=500)

    def _send_json(self, data: dict[str, object], status: int = 200) -> None:
        """Send JSON response with proper headers."""
        body = json.dumps(data).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
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
    port_env = int(os.environ.get("PORT", "8080"))
    run_web_server(port=port_env)
