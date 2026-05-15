#!/usr/bin/env python3
"""
DocSummarizer - Offline Document Summarization Tool
Main entry point.
"""

import os
import sys


class _NullWriter:
    """Discard writes when stdout/stderr is unavailable (Windows GUI mode)."""

    def write(self, _text):
        pass

    def flush(self):
        pass


# Windows GUI processes can have sys.stdout / sys.stderr set to None. Libraries
# like huggingface_hub write to stdout during downloads and would crash with
# "'NoneType' object has no attribute 'write'".
if sys.stdout is None:
    sys.stdout = _NullWriter()
if sys.stderr is None:
    sys.stderr = _NullWriter()


try:
    from docsummarizer.gui import main
except ImportError:
    # Running from source without `pip install -e .`. Make src/ importable.
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))
    from docsummarizer.gui import main


if __name__ == "__main__":
    main()
