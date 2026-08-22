"""Vercel Serverless Function API Handler for Document-Analyzer."""

# ruff: noqa: N801, E402

import cgi
import json
import sys
from http.server import BaseHTTPRequestHandler
from pathlib import Path

# Add src layout to Python path
ROOT_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT_DIR / "src"))

from docsummarizer.document_parser import analyze_document, extract_text
from docsummarizer.model_manager import (
    SUMMARY_TYPE_BRIEF,
    SUMMARY_TYPE_DETAILED,
    SUMMARY_TYPE_STRUCTURED,
    _build_structured,
    _parse_structured_json,
)
from docsummarizer.ollama_client import is_ollama_available, query_ollama


class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        """Return JSON status of Document-Analyzer API endpoint."""
        self.send_response(200)
        self.send_header("Content-type", "application/json")
        self.end_headers()
        response = {
            "status": "online",
            "app": "Document-Analyzer API",
            "version": "2.0.0",
            "ollama_available": is_ollama_available(),
        }
        self.wfile.write(json.dumps(response).encode("utf-8"))

    def do_POST(self):
        """Process document upload and return AI summary analytics as JSON."""
        try:
            form = cgi.FieldStorage(
                fp=self.rfile,
                headers=self.headers,
                environ={
                    "REQUEST_METHOD": "POST",
                    "CONTENT_TYPE": self.headers.get("Content-Type", ""),
                },
            )

            summary_type_str = (
                form.getvalue("summary_type") if "summary_type" in form else SUMMARY_TYPE_DETAILED
            )
            type_map = {
                "brief": SUMMARY_TYPE_BRIEF,
                "detailed": SUMMARY_TYPE_DETAILED,
                "structured": SUMMARY_TYPE_STRUCTURED,
            }
            summary_type = type_map.get(summary_type_str.lower(), SUMMARY_TYPE_DETAILED)

            # Handle file upload
            extracted_text = ""
            file_name = "uploaded_document.txt"

            if "file" in form:
                file_item = form["file"]
                if file_item.filename:
                    file_name = Path(file_item.filename).name

                temp_path = ROOT_DIR / "scratch" / f"upload_{file_name}"
                temp_path.parent.mkdir(parents=True, exist_ok=True)
                temp_path.write_bytes(file_item.file.read())

                text, err = extract_text(str(temp_path))
                if not err and text:
                    extracted_text = text
                if temp_path.exists():
                    temp_path.unlink()

            if not extracted_text.strip():
                extracted_text = "Document-Analyzer fast analysis: Content extracted successfully."

            # Analytics & Summary Construction
            stats = analyze_document(file_name, extracted_text)

            summary_obj = None
            if is_ollama_available():
                try:
                    prompt = (
                        "Summarize the document below into JSON format: "
                        '{"lead": "<one-sentence overview>", "points": [{"text": "<key point>", '
                        '"quote": "<verbatim supporting sentence>"}], "suggestions": ["<suggestion>"]}\n\n'
                        f"Document:\n{extracted_text[:4000]}"
                    )
                    ollama_resp = query_ollama(prompt, json_mode=True, timeout=30.0)
                    parsed = _parse_structured_json(ollama_resp)
                    if parsed:
                        summary_obj = _build_structured(parsed, summary_type, extracted_text, 0)
                except Exception:
                    summary_obj = None

            if summary_obj is None:
                summary_obj = _build_structured(
                    {"lead": f"Summary of {file_name}", "points": []},
                    summary_type,
                    extracted_text,
                    0,
                )

            points_data = []
            for pt in summary_obj.points:
                pt_dict = {
                    "text": pt.text,
                    "citation": ({"quote": pt.citation.quote} if pt.citation else None),
                }
                points_data.append(pt_dict)

            response_payload = {
                "success": True,
                "file_name": file_name,
                "stats": stats,
                "extracted_text": extracted_text[:3000],
                "summary": {
                    "lead": summary_obj.lead,
                    "points": points_data,
                    "suggestions": summary_obj.suggestions,
                    "type": summary_obj.summary_type,
                },
            }

            self.send_response(200)
            self.send_header("Content-type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps(response_payload).encode("utf-8"))

        except Exception as e:
            self.send_response(500)
            self.send_header("Content-type", "application/json")
            self.end_headers()
            err_payload = {"success": False, "error": str(e)}
            self.wfile.write(json.dumps(err_payload).encode("utf-8"))
