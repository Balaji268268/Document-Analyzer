"""
Document Parser Module
Extracts text from various document formats: PDF, DOCX, TXT, RTF.

Legacy binary `.doc` (OLE compound) is intentionally not supported —
python-docx only reads the XML-based `.docx` format. The single
source-of-truth for "what we can parse" is `SUPPORTED_EXTENSION_SET`
below; dialog filters (`SUPPORTED_EXTENSIONS`), the extractor dispatch
in `extract_text`, and CLI directory scans all derive from it.
"""

from pathlib import Path

import chardet


def extract_from_pdf(file_path: str) -> str:
    """Extract text from a PDF file."""
    from pypdf import PdfReader

    reader = PdfReader(file_path)
    text_parts = []

    for page in reader.pages:
        page_text = page.extract_text()
        if page_text:
            text_parts.append(page_text)

    return "\n\n".join(text_parts)


def extract_from_docx(file_path: str) -> str:
    """Extract text from a DOCX file."""
    from docx import Document

    doc = Document(file_path)
    text_parts = []

    for paragraph in doc.paragraphs:
        if paragraph.text.strip():
            text_parts.append(paragraph.text)

    for table in doc.tables:
        for row in table.rows:
            row_text = [cell.text.strip() for cell in row.cells if cell.text.strip()]
            if row_text:
                text_parts.append(" | ".join(row_text))

    return "\n\n".join(text_parts)


def extract_from_rtf(file_path: str) -> str:
    """Extract text from an RTF file."""
    from striprtf.striprtf import rtf_to_text

    with open(file_path, encoding="utf-8", errors="ignore") as f:
        rtf_content = f.read()

    return rtf_to_text(rtf_content)


def extract_from_txt(file_path: str) -> str:
    """Extract text from a plain text file with encoding detection."""
    with open(file_path, "rb") as f:
        raw_data = f.read()

    detected = chardet.detect(raw_data)
    encoding = detected.get("encoding", "utf-8") or "utf-8"

    return raw_data.decode(encoding, errors="replace")


_EXTRACTORS = {
    ".pdf": extract_from_pdf,
    ".docx": extract_from_docx,
    ".rtf": extract_from_rtf,
    ".txt": extract_from_txt,
    ".md": extract_from_txt,
    ".text": extract_from_txt,
}

# Canonical set of supported extensions. Single source of truth — the
# dispatch above, the dialog filters below, and `find_documents` all
# read from it.
SUPPORTED_EXTENSION_SET: frozenset[str] = frozenset(_EXTRACTORS.keys())


def extract_text(file_path: str) -> tuple[str, str | None]:
    """Extract text from a document file.

    Returns:
        Tuple of (extracted_text, error_message). error_message is None on
        success; extracted_text is empty on failure.
    """
    path = Path(file_path)

    if not path.exists():
        return "", f"File not found: {file_path}"

    extractor = _EXTRACTORS.get(path.suffix.lower())
    if extractor is None:
        return "", f"Unsupported file format: {path.suffix.lower()}"

    try:
        text = extractor(file_path)
        if not text.strip():
            return "", "No text could be extracted from the document"
        return text, None
    except Exception as e:
        return "", f"Error extracting text: {e!s}"


def get_document_info(file_path: str) -> dict:
    """Get basic information about a document."""
    path = Path(file_path)

    # Single stat() call; the previous code stat()'d twice and could race
    # on network filesystems (FileNotFoundError on the second call).
    try:
        size_bytes = path.stat().st_size
    except FileNotFoundError:
        size_bytes = 0

    return {
        "name": path.name,
        "extension": path.suffix.lower(),
        "size_bytes": size_bytes,
        "size_mb": round(size_bytes / (1024 * 1024), 2),
    }


def find_documents(path: Path) -> list[Path]:
    """Find all supported documents at `path`.

    If `path` is a single file, returns it (or empty if unsupported).
    If `path` is a directory, returns its supported files (non-recursive).
    """
    if path.is_file():
        return [path] if path.suffix.lower() in SUPPORTED_EXTENSION_SET else []
    return [
        f for f in path.iterdir() if f.is_file() and f.suffix.lower() in SUPPORTED_EXTENSION_SET
    ]


# Dialog filter list, derived from SUPPORTED_EXTENSION_SET so it can't drift.
SUPPORTED_EXTENSIONS = [
    ("All Supported", "*.pdf *.docx *.rtf *.txt *.md"),
    ("PDF Files", "*.pdf"),
    ("Word Documents", "*.docx"),
    ("RTF Files", "*.rtf"),
    ("Text Files", "*.txt *.md"),
]
