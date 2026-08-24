<div align="center">

# DocSummarizer

**Privacy-first document summarization powered by local language models.**

Summarize PDFs, Word documents, text files, and images entirely on your machine. Zero cloud calls, zero telemetry, 100% private.

[![CI](https://github.com/Balaji268268/Document-Analyzer/actions/workflows/ci.yml/badge.svg?branch=master)](https://github.com/Balaji268268/Document-Analyzer/actions/workflows/ci.yml)
[![Python](https://img.shields.io/badge/Python-3.10%2B-blue)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green)](LICENSE)
[![Code style: Ruff](https://img.shields.io/badge/Code%20Style-Ruff-black)](https://docs.astral.sh/ruff/)
[![Types: mypy](https://img.shields.io/badge/Types-mypy-blue)](https://mypy-lang.org/)

</div>

---

## ⚡ Quick Start

### Option 1: Run Locally (Python 3.10+)

```bash
# 1. Clone repository
git clone https://github.com/Balaji268268/Document-Analyzer.git
cd Document-Analyzer

# 2. Setup virtual environment
python -m venv .venv
# Windows:
.venv\Scripts\activate
# Linux/macOS:
source .venv/bin/activate

# 3. Install dependencies
pip install -e ".[gui,runtime]"

# 4. Launch application
python run.py
```

### Option 2: Run with Docker (Web UI)

```bash
# Build and run container
docker build -t docsummarizer .
docker run -p 8080:8080 docsummarizer

# Open in browser: http://localhost:8080
```

---

## ✨ Key Features

- **Multi-Format Ingestion**: Supports `.pdf`, `.docx`, `.rtf`, `.txt`, `.md`, `.png`, `.jpg`, `.jpeg`, `.webp`, `.bmp`, and `.tiff`.
- **Automatic OCR Fallback**: Extracts native digital text; automatically falls back to Tesseract OCR for scanned pages and images.
- **Local AI Inference**: Runs quantized models (`Qwen3-4B`, `Llama-3.2-3B`) via `llama.cpp` or local Ollama without internet access.
- **Map-Reduce for Long Files**: Automatically chunks large documents to summarize 50+ page files without context limits.
- **Interactive Citations**: Click any summary point to highlight its exact matching sentence in the source text.
- **Dual Interface**: Native GPU-accelerated desktop UI (PySide6 / QML) and web browser mode with drag-and-drop file upload.

---

## 🏗️ Architecture & Pipeline

```
┌─────────────────┐     ┌───────────────────────┐     ┌────────────────────────┐
│  Upload Document │ ──> │ Extract Text / OCR    │ ──> │ Map-Reduce Chunker     │
│  PDF/DOCX/Images│     │ pypdf / pytesseract   │     │ (for long documents)   │
└─────────────────┘     └───────────────────────┘     └────────────────────────┘
                                                                   │
                                                                   ▼
┌─────────────────┐     ┌───────────────────────┐     ┌────────────────────────┐
│ QML Desktop UI  │ <── │ Provenance Grounding  │ <── │ Local LLM Inference    │
│ & Web Streaming │     │ Sentence Offset Match │     │ llama.cpp / Ollama     │
└─────────────────┘     └───────────────────────┘     └────────────────────────┘
```

### Core Components

| Module | Path | Description |
|---|---|---|
| **Document Parser** | [`src/docsummarizer/document_parser.py`](file:///d:/Doc-Summarizer/src/docsummarizer/document_parser.py) | Extracts text from digital documents and runs OCR on images/scans. |
| **Model Manager** | [`src/docsummarizer/model_manager.py`](file:///d:/Doc-Summarizer/src/docsummarizer/model_manager.py) | Manages GGUF model downloads, prompt formatting, and map-reduce summarization. |
| **Provenance Engine** | [`src/docsummarizer/provenance.py`](file:///d:/Doc-Summarizer/src/docsummarizer/provenance.py) | Matches generated key points to source sentences using fuzzy matching. |
| **UI Bridge** | [`src/docsummarizer/ui/bridge.py`](file:///d:/Doc-Summarizer/src/docsummarizer/ui/bridge.py) | Connects the PySide6 QML frontend to background inference workers. |
| **Web Server** | [`src/docsummarizer/web_app.py`](file:///d:/Doc-Summarizer/src/docsummarizer/web_app.py) | Serves REST APIs and proxies noVNC desktop streaming in Docker mode. |

---

## 🔌 REST API Endpoints

When running in web/container mode, DocSummarizer exposes clean HTTP endpoints:

### 1. Upload File
`POST /api/upload` (Multipart Form Data)
```bash
curl -X POST -F "file=@sample.pdf" http://localhost:8080/api/upload
```
**Response:**
```json
{
  "success": true,
  "filename": "sample.pdf",
  "path": "/tmp/docsummarizer/uploads/sample.pdf",
  "text_preview": "Document content preview..."
}
```

### 2. Check System Status
`GET /api/status`
```bash
curl http://localhost:8080/api/status
```
**Response:**
```json
{
  "status": "ready",
  "ollama_running": true,
  "default_model": "qwen3:4b"
}
```

---

## 🧪 Testing & Code Quality

```bash
# Run test suite with coverage
pytest -ra --cov=docsummarizer --cov-report=term-missing

# Run static type checks
mypy .

# Run linter checks
ruff check .

# Format code
ruff format .
```

---

## 📄 License

Distributed under the **MIT License**. See [`LICENSE`](file:///d:/Doc-Summarizer/LICENSE) for details.
