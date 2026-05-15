# Development Guide

Technical documentation for developers and advanced users.

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                     User Interface                          │
│  ┌─────────────────────┐    ┌─────────────────────────┐     │
│  │   GUI (gui.py)      │    │    CLI (cli.py)         │     │
│  │   CustomTkinter     │    │    argparse             │     │
│  └──────────┬──────────┘    └───────────┬─────────────┘     │
│             │                           │                   │
│             └─────────────┬─────────────┘                   │
│                           ▼                                 │
│  ┌─────────────────────────────────────────────────────┐   │
│  │           Document Parser (document_parser.py)       │   │
│  │   PDF: pypdf  │  DOCX: python-docx  │  RTF: striprtf│   │
│  └─────────────────────────┬───────────────────────────┘   │
│                            ▼                                │
│  ┌─────────────────────────────────────────────────────┐   │
│  │           Model Manager (model_manager.py)           │   │
│  │   Download: huggingface_hub  │  Inference: llama-cpp │   │
│  └─────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

## Development Setup

```bash
# Clone repository
git clone https://github.com/Wintersta7e/Doc-Summarizer.git
cd DocSummarizer

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/macOS
# or: venv\Scripts\activate  # Windows

# Install the package (and dev tools) in editable mode
pip install -e ".[dev]"

# Quick smoke tests
python -c "from docsummarizer.document_parser import extract_text; print('Parser OK')"
python -c "from docsummarizer.model_manager import is_model_downloaded; print('Model manager OK')"

# Full test suite
pytest
ruff check .
```

## Module Documentation

### document_parser.py

Handles text extraction from various document formats.

**Functions:**
- `extract_text(file_path) -> tuple[str, Optional[str]]` - Main extraction function
- `extract_from_pdf(file_path) -> str` - PDF extraction using pypdf
- `extract_from_docx(file_path) -> str` - Word document extraction
- `extract_from_rtf(file_path) -> str` - RTF extraction
- `extract_from_txt(file_path) -> str` - Plain text with encoding detection
- `get_document_info(file_path) -> dict` - File metadata

**Supported formats:**
- `.pdf` - PDF documents (via pypdf)
- `.docx` - Microsoft Word (modern XML format only; legacy `.doc` OLE files are not supported)
- `.rtf` - Rich Text Format
- `.txt`, `.md` - Plain text (with chardet-based encoding detection)

### model_manager.py

Handles LLM model downloading and inference.

**Classes:**
- `Summarizer` - Main summarization class

**Functions:**
- `get_models_directory() -> Path` - Get model storage location
- `is_model_downloaded() -> bool` - Check if model exists
- `get_model_path() -> Path` - Get full model path
- `download_model(progress_callback) -> tuple[Path, Optional[str]]` - Download from HuggingFace

**Summarizer Methods:**
- `__init__(model_path, n_ctx=8192, n_threads=None)` - Load model
- `summarize(text, summary_type, max_tokens) -> str` - Generate summary

### gui.py

CustomTkinter-based graphical interface.

**Classes:**
- `DocSummarizerApp(ctk.CTk)` - Main application window

**Features:**
- File selection dialog
- Batch folder processing
- Summary type selection
- Progress indication
- Save to file (TXT, MD, DOCX)
- Settings tab (appearance, model info)

### cli.py

Command-line interface for terminal usage.

**Usage:**
```bash
docsummarizer-cli <input> [-t TYPE] [-o OUTPUT] [--download-only]
```

## GPU Acceleration (Optional)

For faster inference, you can enable GPU support. This requires additional setup.

### NVIDIA GPU (CUDA)

```bash
# 1. Install CUDA Toolkit (https://developer.nvidia.com/cuda-downloads)

# 2. Uninstall CPU version
pip uninstall llama-cpp-python -y

# 3. Install with CUDA support
CMAKE_ARGS="-DGGML_CUDA=on" pip install llama-cpp-python --no-cache-dir

# 4. Verify
python -c "from llama_cpp import Llama; print('CUDA support enabled')"
```

### AMD GPU (ROCm)

```bash
# 1. Install ROCm (https://rocm.docs.amd.com/)

# 2. Reinstall with ROCm
CMAKE_ARGS="-DGGML_HIPBLAS=on" pip install llama-cpp-python --no-cache-dir
```

### Apple Silicon (Metal)

Metal support is usually automatic on macOS with Apple Silicon:

```bash
CMAKE_ARGS="-DGGML_METAL=on" pip install llama-cpp-python --no-cache-dir
```

### Performance Comparison

| Hardware | ~Processing Time | Notes |
|----------|------------------|-------|
| CPU (8 cores) | 60-120 sec | Default, works everywhere |
| NVIDIA RTX 3060 | 5-10 sec | Requires CUDA |
| NVIDIA RTX 4090 | 2-5 sec | Requires CUDA |
| Apple M1/M2 | 10-20 sec | Metal acceleration |

## Building Standalone Executable

### Prerequisites

```bash
pip install pyinstaller
```

### Build Commands

**Windows:**
```cmd
pyinstaller DocSummarizer.spec
```

**Linux/macOS:**
```bash
pyinstaller DocSummarizer.spec
```

The executable will be in `dist/DocSummarizer` (or `dist/DocSummarizer.exe` on Windows).

### Build Size

- Executable: ~50-100 MB
- Model (separate download): ~4.4 GB

**Note:** The model is NOT bundled in the executable. Users download it on first run.

## Adding New Document Formats

To add support for a new format:

1. Add extraction function in `document_parser.py`:
```python
def extract_from_newformat(file_path: str) -> str:
    # Your extraction logic
    return extracted_text
```

2. Register in the `extractors` dictionary:
```python
extractors = {
    '.pdf': extract_from_pdf,
    '.newformat': extract_from_newformat,  # Add here
    # ...
}
```

3. Update `SUPPORTED_EXTENSIONS` for file dialogs.

## Adding New Models

To add support for a different LLM:

1. Add model configuration in `model_manager.py`:
```python
NEW_MODEL = {
    'repo_id': 'organization/model-name-GGUF',
    'filename': 'model-name.Q4_K_M.gguf',
    'name': 'Model Display Name',
    'size_gb': 4.0,
}
```

2. Ensure the model uses the Mistral/Llama chat format, or adjust the prompts.

## Customizing Prompts

Summary prompts are defined in `model_manager.py` in the `summarize()` method. To customize:

```python
prompts = {
    "brief": """Your custom brief prompt...""",
    "detailed": """Your custom detailed prompt...""",
    "structured": """Your custom structured prompt...""",
    "custom_type": """Add new summary types here...""",
}
```

## Thread Control

To limit CPU usage, modify the `Summarizer` initialization:

```python
# Use half of available cores
summarizer = Summarizer(model_path, n_threads=os.cpu_count() // 2)

# Use specific number of threads
summarizer = Summarizer(model_path, n_threads=4)
```

## Testing

### Manual Testing

```bash
# Test document parser
python -c "
from docsummarizer.document_parser import extract_text
text, err = extract_text('test.pdf')
print(f'Extracted {len(text)} chars, error: {err}')
"

# Test model loading
python -c "
from docsummarizer.model_manager import Summarizer, get_model_path
s = Summarizer(get_model_path())
print('Model loaded successfully')
"

# Test summarization
docsummarizer-cli test.pdf -t brief
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## Known Limitations

- Scanned PDFs (image-only) are not supported - text extraction required
- Maximum document length limited by context window (~20,000 chars)
- Very long documents are truncated
- Password-protected files not supported
- Complex tables may not extract cleanly
