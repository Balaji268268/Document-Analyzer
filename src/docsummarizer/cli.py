#!/usr/bin/env python3
"""
DocSummarizer Command Line Interface
For users who prefer terminal over GUI.
"""

import argparse
import sys
from pathlib import Path

from .document_parser import extract_text, get_document_info
from .model_manager import (
    DEFAULT_MODEL,
    Summarizer,
    download_model,
    get_model_path,
    is_model_downloaded,
)


def print_progress(percent: float, message: str):
    """Print progress to console."""
    bar_length = 40
    filled = int(bar_length * percent / 100)
    bar = "=" * filled + "-" * (bar_length - filled)
    print(f"\r[{bar}] {percent:.1f}% - {message}", end="", flush=True)
    if percent >= 100:
        print()


def ensure_model() -> bool:
    """Ensure the model is downloaded."""
    if is_model_downloaded():
        return True

    print(
        f"Model not found. Downloading {DEFAULT_MODEL['name']} ({DEFAULT_MODEL['size_gb']} GB)..."
    )
    print("This is a one-time download.\n")

    path, error = download_model(progress_callback=print_progress)

    if error:
        print(f"\nError: {error}")
        return False

    print("Model downloaded successfully!\n")
    return True


def summarize_file(
    filepath: str, summarizer: Summarizer, summary_type: str = "detailed", output_path: str = None
) -> bool:
    """Summarize a single file."""
    info = get_document_info(filepath)
    print(f"Processing: {info['name']} ({info['size_mb']} MB)")

    # Extract text
    text, error = extract_text(filepath)
    if error:
        print(f"  Error: {error}")
        return False

    print(f"  Extracted {len(text)} characters")

    # Generate summary
    print("  Generating summary...")
    try:
        summary = summarizer.summarize(text, summary_type=summary_type)
    except Exception as e:
        print(f"  Error: {e!s}")
        return False

    # Output
    if output_path:
        out_file = Path(output_path)
        if out_file.is_dir():
            out_file = out_file / f"{Path(filepath).stem}_summary.txt"

        write_summary_txt(
            out_file,
            source_name=info["name"],
            summary=summary,
            summary_type=summary_type,
            separator_width=60,
        )

        print(f"  Saved to: {out_file}")
    else:
        print("\n" + "=" * 60)
        print(f"SUMMARY ({summary_type})")
        print("=" * 60 + "\n")
        print(summary)
        print("\n" + "=" * 60)

    return True


def find_documents(path: Path) -> list[Path]:
    """Find all supported documents in a directory."""
    extensions = (".pdf", ".docx", ".doc", ".rtf", ".txt", ".md")

    if path.is_file():
        return [path] if path.suffix.lower() in extensions else []

    return [f for f in path.iterdir() if f.is_file() and f.suffix.lower() in extensions]


def main():
    parser = argparse.ArgumentParser(
        description="DocSummarizer - Offline Document Summarization",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s document.pdf                     Summarize a single file
  %(prog)s document.pdf -t structured       Use structured summary format
  %(prog)s ./documents/ -o ./summaries/     Batch process a folder
  %(prog)s report.docx -o summary.txt       Save to specific file
        """,
    )

    parser.add_argument(
        "input",
        nargs="?",  # Optional when using --download-only
        help="Input file or directory to process",
    )

    parser.add_argument(
        "-t",
        "--type",
        choices=["brief", "detailed", "structured"],
        default="detailed",
        help="Summary type (default: detailed)",
    )

    parser.add_argument(
        "-o", "--output", help="Output file or directory (default: print to console)"
    )

    parser.add_argument(
        "--download-only", action="store_true", help="Only download the model, do not process files"
    )

    args = parser.parse_args()

    # Ensure model is available
    if not ensure_model():
        sys.exit(1)

    if args.download_only:
        print("Model is ready.")
        sys.exit(0)

    # Check that input was provided
    if args.input is None:
        parser.error("the following arguments are required: input")

    # Find files to process
    input_path = Path(args.input)
    if not input_path.exists():
        print(f"Error: Path does not exist: {args.input}")
        sys.exit(1)

    files = find_documents(input_path)
    if not files:
        print(f"Error: No supported documents found in: {args.input}")
        sys.exit(1)

    # Load model
    print("Loading model...")
    try:
        summarizer = Summarizer(get_model_path())
    except Exception as e:
        print(f"Error loading model: {e}")
        sys.exit(1)

    print(f"Model loaded. Processing {len(files)} file(s)...\n")

    # Process files
    success_count = 0
    for filepath in files:
        if summarize_file(str(filepath), summarizer, args.type, args.output):
            success_count += 1
        print()

    print(f"Done. Successfully processed {success_count}/{len(files)} file(s).")


if __name__ == "__main__":
    main()
