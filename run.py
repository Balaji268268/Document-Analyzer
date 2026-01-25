#!/usr/bin/env python3
"""
DocSummarizer - Offline Document Summarization Tool
Main entry point.
"""

import sys
import os


class NullWriter:
    """Null writer to prevent errors when stdout/stderr is None (Windows GUI mode)."""
    def write(self, text):
        pass

    def flush(self):
        pass


# Fix for Windows GUI mode where stdout/stderr can be None
# This prevents "'NoneType' object has no attribute 'write'" errors
# from libraries like huggingface_hub that write to stdout
if sys.stdout is None:
    sys.stdout = NullWriter()
if sys.stderr is None:
    sys.stderr = NullWriter()

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from gui import main

if __name__ == "__main__":
    main()
