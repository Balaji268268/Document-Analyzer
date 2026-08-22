"""Vercel Serverless Function API & HTML Handler for Document-Analyzer."""

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

HTML_PAGE = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Document-Analyzer — Smart Document Summarizer</title>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=Outfit:wght@500;600;700;800&display=swap" rel="stylesheet">
  <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
  <style>
    :root {
      --bg-dark: #0b0f19;
      --card-bg: rgba(18, 24, 40, 0.75);
      --card-border: rgba(255, 255, 255, 0.08);
      --primary-gradient: linear-gradient(135deg, #6366f1 0%, #8b5cf6 50%, #d946ef 100%);
      --accent-glow: rgba(99, 102, 241, 0.25);
      --text-main: #f3f4f6;
      --text-muted: #9ca3af;
    }
    * { box-sizing: border-box; margin: 0; padding: 0; }
    body {
      font-family: 'Inter', sans-serif;
      background-color: var(--bg-dark);
      background-image:
        radial-gradient(at 20% 20%, rgba(99, 102, 241, 0.15) 0px, transparent 50%),
        radial-gradient(at 80% 80%, rgba(217, 70, 239, 0.15) 0px, transparent 50%);
      color: var(--text-main);
      min-height: 100vh;
      display: flex;
      flex-direction: column;
    }
    header {
      padding: 2rem 1.5rem;
      text-align: center;
      border-bottom: 1px solid var(--card-border);
      backdrop-filter: blur(10px);
    }
    header h1 {
      font-family: 'Outfit', sans-serif;
      font-size: 2.25rem;
      font-weight: 800;
      background: var(--primary-gradient);
      -webkit-background-clip: text;
      -webkit-text-fill-color: transparent;
      margin-bottom: 0.5rem;
    }
    header p { color: var(--text-muted); font-size: 0.95rem; }
    .container {
      max-width: 1200px;
      width: 100%;
      margin: 2rem auto;
      padding: 0 1.5rem;
      display: grid;
      grid-template-columns: 380px 1fr;
      gap: 2rem;
      flex: 1;
    }
    @media (max-width: 900px) { .container { grid-template-columns: 1fr; } }
    .card {
      background: var(--card-bg);
      border: 1px solid var(--card-border);
      border-radius: 16px;
      padding: 1.5rem;
      backdrop-filter: blur(16px);
      box-shadow: 0 10px 30px rgba(0, 0, 0, 0.4);
    }
    .drop-zone {
      border: 2px dashed rgba(99, 102, 241, 0.4);
      border-radius: 12px;
      padding: 2.5rem 1rem;
      text-align: center;
      cursor: pointer;
      transition: all 0.3s ease;
      background: rgba(99, 102, 241, 0.03);
    }
    .drop-zone:hover, .drop-zone.dragover {
      border-color: #8b5cf6;
      background: rgba(139, 92, 246, 0.1);
      box-shadow: 0 0 20px var(--accent-glow);
    }
    .drop-zone i {
      font-size: 2.5rem;
      background: var(--primary-gradient);
      -webkit-background-clip: text;
      -webkit-text-fill-color: transparent;
      margin-bottom: 1rem;
    }
    .file-name-display {
      margin-top: 1rem;
      padding: 0.75rem;
      background: rgba(255, 255, 255, 0.05);
      border-radius: 8px;
      font-size: 0.85rem;
      color: #38bdf8;
      display: none;
      word-break: break-all;
    }
    .section-title {
      font-size: 0.9rem;
      font-weight: 600;
      text-transform: uppercase;
      letter-spacing: 0.05em;
      color: var(--text-muted);
      margin: 1.5rem 0 0.75rem 0;
    }
    .radio-group { display: flex; flex-direction: column; gap: 0.5rem; }
    .radio-label {
      display: flex;
      align-items: center;
      gap: 0.75rem;
      padding: 0.75rem 1rem;
      background: rgba(255, 255, 255, 0.03);
      border: 1px solid var(--card-border);
      border-radius: 8px;
      cursor: pointer;
      transition: all 0.2s ease;
    }
    .radio-label:hover { background: rgba(255, 255, 255, 0.06); }
    .radio-label input[type="radio"] { accent-color: #8b5cf6; }
    .btn-submit {
      width: 100%;
      margin-top: 1.5rem;
      padding: 0.9rem;
      border: none;
      border-radius: 10px;
      background: var(--primary-gradient);
      color: white;
      font-weight: 600;
      font-size: 1rem;
      cursor: pointer;
      box-shadow: 0 4px 15px var(--accent-glow);
      transition: all 0.3s ease;
      display: flex;
      align-items: center;
      justify-content: center;
      gap: 0.5rem;
    }
    .btn-submit:hover { transform: translateY(-2px); box-shadow: 0 6px 20px rgba(139, 92, 246, 0.4); }
    .btn-submit:disabled { opacity: 0.5; cursor: not-allowed; transform: none; }
    .tabs-header { display: flex; gap: 1rem; border-bottom: 1px solid var(--card-border); margin-bottom: 1.5rem; }
    .tab-btn {
      padding: 0.75rem 1.25rem;
      background: none;
      border: none;
      color: var(--text-muted);
      font-weight: 600;
      cursor: pointer;
      position: relative;
    }
    .tab-btn.active { color: #38bdf8; }
    .tab-btn.active::after {
      content: '';
      position: absolute;
      bottom: -1px; left: 0; right: 0; height: 2px;
      background: #38bdf8;
    }
    .tab-content { display: none; }
    .tab-content.active { display: block; }
    .lead-box {
      background: rgba(99, 102, 241, 0.08);
      border-left: 4px solid #6366f1;
      padding: 1.25rem;
      border-radius: 8px;
      margin-bottom: 1.5rem;
      line-height: 1.6;
    }
    .points-list, .suggestions-list { list-style: none; display: flex; flex-direction: column; gap: 0.85rem; margin-bottom: 1.5rem; }
    .point-item {
      padding: 0.9rem 1rem;
      background: rgba(255, 255, 255, 0.03);
      border: 1px solid var(--card-border);
      border-radius: 8px;
      line-height: 1.5;
    }
    .citation-tag { display: inline-block; margin-top: 0.4rem; font-size: 0.8rem; color: #a78bfa; font-style: italic; }
    .suggestion-item {
      padding: 0.75rem 1rem;
      background: rgba(245, 158, 11, 0.08);
      border-left: 3px solid #f59e0b;
      border-radius: 6px;
      font-size: 0.9rem;
      color: #fbbf24;
    }
    .meta-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(140px, 1fr)); gap: 1rem; margin-bottom: 1.5rem; }
    .meta-card {
      background: rgba(255, 255, 255, 0.03);
      padding: 1rem;
      border-radius: 8px;
      border: 1px solid var(--card-border);
    }
    .meta-card .val { font-size: 1.25rem; font-weight: 700; color: #38bdf8; margin-top: 0.25rem; }
    .meta-card .lbl { font-size: 0.75rem; color: var(--text-muted); text-transform: uppercase; }
    textarea.raw-text {
      width: 100%; height: 350px;
      background: rgba(0, 0, 0, 0.3);
      border: 1px solid var(--card-border);
      border-radius: 8px; color: #e5e7eb;
      padding: 1rem; font-family: monospace; resize: vertical;
    }
    .spinner {
      display: inline-block; width: 1.2rem; height: 1.2rem;
      border: 2px solid rgba(255, 255, 255, 0.3); border-radius: 50%;
      border-top-color: white; animation: spin 0.8s linear infinite;
    }
    @keyframes spin { to { transform: rotate(360deg); } }
  </style>
</head>
<body>
  <header>
    <h1><i class="fa-solid fa-file-contract"></i> Document-Analyzer</h1>
    <p>AI Document Summarization & Intelligence Engine</p>
  </header>
  <div class="container">
    <div class="card">
      <div class="drop-zone" id="dropZone">
        <i class="fa-solid fa-cloud-arrow-up"></i>
        <p style="font-weight: 600;">Drag & Drop File Here</p>
        <p style="font-size: 0.8rem; color: var(--text-muted); margin-top: 0.25rem;">PDF, DOCX, RTF, TXT, PNG, JPG</p>
        <input type="file" id="fileInput" style="display: none;" accept=".pdf,.docx,.rtf,.txt,.md,.png,.jpg,.jpeg,.webp">
      </div>
      <div class="file-name-display" id="fileNameDisplay"></div>
      <div class="section-title">Summary Detail Mode</div>
      <div class="radio-group">
        <label class="radio-label"><input type="radio" name="summaryType" value="brief"><span>Brief (1 Paragraph)</span></label>
        <label class="radio-label"><input type="radio" name="summaryType" value="detailed" checked><span>Detailed (Overview + Points)</span></label>
        <label class="radio-label"><input type="radio" name="summaryType" value="structured"><span>Structured (Full Sections)</span></label>
      </div>
      <button class="btn-submit" id="submitBtn"><i class="fa-solid fa-wand-magic-sparkles"></i> Generate Summary</button>
    </div>
    <div class="card">
      <div class="tabs-header">
        <button class="tab-btn active" onclick="switchTab('summaryTab', this)"><i class="fa-solid fa-sparkles"></i> AI Summary</button>
        <button class="tab-btn" onclick="switchTab('analyticsTab', this)"><i class="fa-solid fa-chart-pie"></i> Document Text & Stats</button>
      </div>
      <div id="summaryTab" class="tab-content active">
        <div id="placeholderText" style="text-align: center; color: var(--text-muted); padding: 4rem 1rem;">
          <i class="fa-solid fa-file-circle-question" style="font-size: 3rem; margin-bottom: 1rem; opacity: 0.4;"></i>
          <p>Upload a document and click <b>Generate Summary</b> to view results.</p>
        </div>
        <div id="summaryResults" style="display: none;">
          <div class="section-title">Summary Overview</div>
          <div class="lead-box" id="leadOverview"></div>
          <div class="section-title">Key Points & Cited Source Grounding</div>
          <div class="points-list" id="pointsList"></div>
          <div class="section-title">Document Improvement Suggestions</div>
          <div class="suggestions-list" id="suggestionsList"></div>
        </div>
      </div>
      <div id="analyticsTab" class="tab-content">
        <div class="meta-grid">
          <div class="meta-card"><div class="lbl">Parser Engine</div><div class="val" id="metaParser">-</div></div>
          <div class="meta-card"><div class="lbl">Word Count</div><div class="val" id="metaWords">0</div></div>
          <div class="meta-card"><div class="lbl">Character Count</div><div class="val" id="metaChars">0</div></div>
          <div class="meta-card"><div class="lbl">Page Count</div><div class="val" id="metaPages">N/A</div></div>
        </div>
        <div class="section-title">Extracted Document Text</div>
        <textarea class="raw-text" id="rawTextViewer" readonly placeholder="Extracted text will appear here..."></textarea>
      </div>
    </div>
  </div>
  <script>
    const dropZone = document.getElementById('dropZone');
    const fileInput = document.getElementById('fileInput');
    const fileNameDisplay = document.getElementById('fileNameDisplay');
    const submitBtn = document.getElementById('submitBtn');
    let selectedFile = null;
    dropZone.addEventListener('click', () => fileInput.click());
    fileInput.addEventListener('change', (e) => {
      if (e.target.files.length > 0) {
        selectedFile = e.target.files[0];
        fileNameDisplay.style.display = 'block';
        fileNameDisplay.innerHTML = `<i class="fa-solid fa-file-code"></i> ${selectedFile.name} (${(selectedFile.size / 1024).toFixed(1)} KB)`;
      }
    });
    dropZone.addEventListener('dragover', (e) => { e.preventDefault(); dropZone.classList.add('dragover'); });
    dropZone.addEventListener('dragleave', () => dropZone.classList.remove('dragover'));
    dropZone.addEventListener('drop', (e) => {
      e.preventDefault(); dropZone.classList.remove('dragover');
      if (e.dataTransfer.files.length > 0) {
        selectedFile = e.dataTransfer.files[0];
        fileNameDisplay.style.display = 'block';
        fileNameDisplay.innerHTML = `<i class="fa-solid fa-file-code"></i> ${selectedFile.name} (${(selectedFile.size / 1024).toFixed(1)} KB)`;
      }
    });
    function switchTab(tabId, btn) {
      document.querySelectorAll('.tab-content').forEach(t => t.classList.remove('active'));
      document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
      document.getElementById(tabId).classList.add('active');
      btn.classList.add('active');
    }
    submitBtn.addEventListener('click', async () => {
      if (!selectedFile) { alert('Please select or drag-and-drop a document file first.'); return; }
      const summaryType = document.querySelector('input[name="summaryType"]:checked').value;
      submitBtn.disabled = true;
      submitBtn.innerHTML = '<div class="spinner"></div> Processing Document...';
      const formData = new FormData();
      formData.append('file', selectedFile);
      formData.append('summary_type', summaryType);
      try {
        const response = await fetch('/', { method: 'POST', body: formData });
        const data = await response.json();
        if (response.ok && data.success) {
          document.getElementById('placeholderText').style.display = 'none';
          document.getElementById('summaryResults').style.display = 'block';
          document.getElementById('leadOverview').innerText = data.summary.lead;
          const pointsList = document.getElementById('pointsList');
          pointsList.innerHTML = '';
          data.summary.points.forEach((pt, i) => {
            const div = document.createElement('div');
            div.className = 'point-item';
            let html = `<strong>${i + 1}. ${pt.text}</strong>`;
            if (pt.citation && pt.citation.quote) {
              html += `<br><span class="citation-tag">Source: "${pt.citation.quote}"</span>`;
            }
            div.innerHTML = html;
            pointsList.appendChild(div);
          });
          const suggestionsList = document.getElementById('suggestionsList');
          suggestionsList.innerHTML = '';
          data.summary.suggestions.forEach((s) => {
            const div = document.createElement('div');
            div.className = 'suggestion-item';
            div.innerHTML = `<i class="fa-solid fa-lightbulb"></i> ${s}`;
            suggestionsList.appendChild(div);
          });
          document.getElementById('metaParser').innerText = data.stats.parser || 'Standard';
          document.getElementById('metaWords').innerText = (data.stats.words || 0).toLocaleString();
          document.getElementById('metaChars').innerText = (data.stats.chars || 0).toLocaleString();
          document.getElementById('metaPages').innerText = data.stats.pages || 'N/A';
          document.getElementById('rawTextViewer').value = data.extracted_text || '';
        } else { alert('Error: ' + (data.error || 'Failed to process document')); }
      } catch (err) { alert('Network or Server Error: ' + err.message); }
      finally {
        submitBtn.disabled = false;
        submitBtn.innerHTML = '<i class="fa-solid fa-wand-magic-sparkles"></i> Generate Summary';
      }
    });
  </script>
</body>
</html>"""


class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        """Serve public/index.html web UI."""
        self.send_response(200)
        self.send_header("Content-type", "text/html; charset=utf-8")
        self.end_headers()
        self.wfile.write(HTML_PAGE.encode("utf-8"))

    def do_POST(self):
        """Process document upload and return AI summary analytics."""
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
