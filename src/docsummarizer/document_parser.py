"""
Document Parser Module
Extracts text from various document formats: PDF, DOCX, TXT, RTF
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

    # Also extract text from tables
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


def extract_text(file_path: str) -> tuple[str, str | None]:
    """
    Extract text from a document file.

    Args:
        file_path: Path to the document

    Returns:
        Tuple of (extracted_text, error_message)
        If successful, error_message is None
    """
    path = Path(file_path)

    if not path.exists():
        return "", f"File not found: {file_path}"

    suffix = path.suffix.lower()

    # Legacy binary `.doc` (OLE compound) is not handled — python-docx only
    # reads the XML-based `.docx` format. The prior mapping `.doc -> docx`
    # silently failed on real `.doc` files.
    extractors = {
        ".pdf": extract_from_pdf,
        ".docx": extract_from_docx,
        ".rtf": extract_from_rtf,
        ".txt": extract_from_txt,
        ".md": extract_from_txt,
        ".text": extract_from_txt,
    }

    extractor = extractors.get(suffix)

    if extractor is None:
        return "", f"Unsupported file format: {suffix}"

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

    # Call stat() once. The previous code called .stat() twice independently,
    # which can race on network filesystems (file disappears between calls,
    # raising FileNotFoundError on the second call).
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


# Supported extensions for file dialogs. Legacy binary `.doc` is intentionally
# excluded: python-docx cannot read OLE compound documents — only the XML-based
# `.docx` format — and the previous mapping silently failed on real `.doc`s.
SUPPORTED_EXTENSIONS = [
    ("All Supported", "*.pdf *.docx *.rtf *.txt *.md"),
    ("PDF Files", "*.pdf"),
    ("Word Documents", "*.docx"),
    ("RTF Files", "*.rtf"),
    ("Text Files", "*.txt *.md"),
]
