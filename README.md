# DocSummarizer

[![CI](https://github.com/Wintersta7e/Doc-Summarizer/actions/workflows/ci.yml/badge.svg?branch=master)](https://github.com/Wintersta7e/Doc-Summarizer/actions/workflows/ci.yml)
[![Python](https://img.shields.io/badge/python-3.10%20%7C%203.11%20%7C%203.12-blue)](https://www.python.org/)
[![License](https://img.shields.io/github/license/Wintersta7e/Doc-Summarizer)](LICENSE)
[![Latest release](https://img.shields.io/github/v/release/Wintersta7e/Doc-Summarizer?label=release&sort=semver)](https://github.com/Wintersta7e/Doc-Summarizer/releases/latest)
[![Platforms](https://img.shields.io/badge/platform-Windows%20%7C%20macOS%20%7C%20Linux-lightgrey)](#system-requirements)

A fully offline document summarization tool powered by a local AI model. Designed for scientists and researchers who need to quickly summarize academic papers and documents without sending data to external services.

## Features

- **100% Offline**: After the initial model download, everything runs locally on your machine
- **Privacy-First**: Documents never leave your computer - no cloud services, no data collection
- **Multiple Formats**: Supports PDF, DOCX, RTF, TXT, and Markdown files
- **Batch Processing**: Summarize entire folders of documents at once
- **Flexible Output**: Choose between brief, detailed, or structured summaries
- **Long Documents**: Documents larger than the context window are summarized in chunks, not truncated
- **Cross-Platform**: Works on Windows, macOS, and Linux
- **Adjustable CPU Usage**: Control how many CPU threads to use via Settings
- **Optional GPU Acceleration**: Offload the model to an NVIDIA GPU for much faster summaries

## System Requirements

| Requirement | Minimum | Recommended |
|-------------|---------|-------------|
| OS | Windows 10, macOS 10.14, Linux | Latest version |
| RAM | 8 GB | 16 GB |
| Storage | 4 GB free | 8 GB free |
| CPU | 4 cores | 8+ cores |
| Python | 3.10+ | 3.11+ |

**Note**: The tool runs on CPU by default. GPU acceleration is optional — enable it in **Settings** (or pass `--gpu` on the CLI). It needs a CUDA build of `llama-cpp-python`; see [DEVELOPMENT.md](DEVELOPMENT.md) for setup.

## Quick Start

### Option A: Download Standalone Executable (Easiest)

Download the latest release for your platform - no Python required:

1. Go to [Releases](https://github.com/Wintersta7e/Doc-Summarizer/releases/latest)
2. Download:
   - **Windows**: `DocSummarizer.exe`
   - **Linux**: `DocSummarizer`
3. Run the executable
4. On first launch, click "Download Model" (~2.5 GB, one-time)

### Option B: Run from Source

#### 1. Clone or Download

```bash
git clone https://github.com/Wintersta7e/Doc-Summarizer.git
cd Doc-Summarizer
```

#### 2. Run Setup Script

**Windows:**
```cmd
setup_and_run.bat
```

**Linux/macOS:**
```bash
chmod +x setup_and_run.sh
./setup_and_run.sh
```

#### 3. First Launch

On first launch, the application will:
1. Create a virtual environment
2. Install dependencies
3. Prompt you to download the AI model (~2.5 GB, one-time)

After setup, the GUI will open automatically.

## Usage

### Graphical Interface (GUI)

1. Launch with `python run.py` or use the setup script
2. Click **Select File** to choose a document
3. Select summary type: **Brief**, **Detailed**, or **Structured**
4. Click **Summarize** and wait for processing
5. Save the result using **Save Summary**

### Command Line Interface (CLI)

```bash
# Summarize a single file
docsummarizer-cli document.pdf

# Choose summary type
docsummarizer-cli document.pdf -t structured
docsummarizer-cli document.pdf -t brief
docsummarizer-cli document.pdf -t detailed

# Save output to file
docsummarizer-cli document.pdf -o summary.txt

# Batch process a folder
docsummarizer-cli ./papers/ -o ./summaries/

# Offload to the GPU for this run (overrides the saved setting)
docsummarizer-cli document.pdf --gpu

# Download model only (no processing)
docsummarizer-cli --download-only
```

### Summary Types

| Type | Description | Best For |
|------|-------------|----------|
| **Brief** | 1 paragraph (3-5 sentences) | Quick overview |
| **Detailed** | Comprehensive with key points | Understanding content |
| **Structured** | Organized sections (Purpose, Methods, Conclusions, etc.) | Academic papers |

## Project Structure

```
DocSummarizer/
├── run.py                       # GUI entry point
├── pyproject.toml               # Package metadata, deps, lint/type/test config
├── README.md                    # This file
├── DEVELOPMENT.md               # Developer documentation
├── DocSummarizer.spec           # PyInstaller build configuration
├── setup_and_run.bat            # Windows launcher
├── setup_and_run.sh             # Linux/macOS launcher
├── .github/                     # CI workflow + Dependabot config
├── src/
│   └── docsummarizer/           # Installable package
│       ├── __init__.py
│       ├── ui/                  # Qt/QML desktop UI (ConsoleBridge + qml/)
│       ├── provenance.py        # Summary point → source sentence grounding
│       ├── cli.py               # Command-line interface
│       ├── document_parser.py   # Document text extraction
│       ├── model_manager.py     # LLM download and inference
│       ├── settings.py          # Persisted user settings (threads, GPU)
│       ├── io_helpers.py        # Shared summary-writing helpers
│       └── logger.py            # Logging and diagnostics
└── tests/                       # pytest suite
```

## How It Works

1. **Document Parsing**: Extracts text from PDF, DOCX, and other formats using `pypdf` and `python-docx`
2. **Chunking**: Documents larger than the context window are split so the whole document is summarized (map-reduce), not truncated
3. **Local LLM Inference**: Uses `llama-cpp-python` to run a quantized Qwen3 4B model, applying the model's own chat template
4. **Summary Generation**: The model generates a summary based on the selected type

## Model Information

| Property | Value |
|----------|-------|
| Model | Qwen3 4B Instruct 2507 |
| Quantization | Q4_K_M (4-bit) |
| Size | ~2.5 GB |
| Source | HuggingFace (Unsloth) |
| Context Window | 8192 tokens (longer documents are chunked) |

The model is downloaded on first launch and stored in:
- **Windows**: `%LOCALAPPDATA%\DocSummarizer\models\`
- **macOS**: `~/Library/Application Support/DocSummarizer/models/`
- **Linux**: `~/.local/share/DocSummarizer/models/`

## Performance

| Document Size | Processing Time (CPU) |
|---------------|----------------------|
| Short (1-5 pages) | 20-45 seconds |
| Medium (5-15 pages) | 1-2 minutes |
| Long (15+ pages) | 2-3 minutes |

**Note**: Times vary with CPU and thread settings. By default the tool uses half of the available CPU cores to balance speed and responsiveness — adjust in **Settings > CPU Threads**. Enabling **GPU acceleration** (Settings, or `--gpu`) is several times faster on a supported NVIDIA GPU.

## Troubleshooting

### Model download fails
- Check internet connection
- Ensure 3+ GB free disk space
- Try running as administrator

### Out of memory
- Close other applications
- Ensure at least 8 GB RAM
- Process smaller documents

### Slow performance
- Normal on CPU - the model is computationally intensive
- Enable **GPU acceleration** in Settings (or `--gpu`) if you have a supported NVIDIA GPU
- Increase CPU threads in Settings for faster processing
- Close other applications to free resources

### High CPU usage
- Go to **Settings > CPU Threads** and lower the thread count
- Using fewer threads reduces CPU load but increases processing time

### Checking logs for errors
Log files are stored at:
- **Windows**: `%LOCALAPPDATA%\DocSummarizer\logs\`
- **macOS**: `~/Library/Application Support/DocSummarizer/logs/`
- **Linux**: `~/.local/share/DocSummarizer/logs/`

Logs contain startup info, performance metrics, and error details (no document content is logged).

### PDF extraction issues
- Some scanned PDFs (image-only) cannot be parsed
- Password-protected PDFs are not supported
- Try converting to DOCX first

## Privacy & Security

- **No internet required** after model download
- **No telemetry** or usage tracking
- **No data collection** - documents processed in memory only
- **Open source** - audit the code yourself

## License

MIT License - See LICENSE file for details.

## Acknowledgments

- [llama.cpp](https://github.com/ggerganov/llama.cpp) - Efficient LLM inference
- [Qwen](https://github.com/QwenLM/Qwen3) - Base model (Qwen3 4B Instruct)
- [Unsloth](https://huggingface.co/unsloth) - Quantized GGUF models
- [PySide6 / Qt](https://doc.qt.io/qtforpython/) - Native Qt/QML desktop UI
