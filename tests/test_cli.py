"""Tests for the CLI argument parser and runtime resolution.

These cover the new ``--gpu`` / ``--threads`` flags and the rule that explicit
flags override saved settings. They don't invoke ``main()`` (which loads the
model and touches the filesystem); the testable logic is factored into
``_build_parser`` and ``_resolve_runtime``.
"""

from __future__ import annotations

from docsummarizer.cli import _build_parser, _resolve_runtime
from docsummarizer.settings import Settings


def test_parser_defaults() -> None:
    args = _build_parser().parse_args(["doc.pdf"])
    assert args.input == "doc.pdf"
    assert args.type == "detailed"
    assert args.gpu is None
    assert args.threads is None


def test_parser_gpu_flags() -> None:
    assert _build_parser().parse_args(["d", "--gpu"]).gpu is True
    assert _build_parser().parse_args(["d", "--no-gpu"]).gpu is False


def test_parser_threads_and_type() -> None:
    args = _build_parser().parse_args(["d", "--threads", "6", "-t", "brief"])
    assert args.threads == 6
    assert args.type == "brief"


def test_resolve_runtime_uses_settings_without_flags() -> None:
    args = _build_parser().parse_args(["d"])
    assert _resolve_runtime(args, Settings(n_threads=4, use_gpu=False)) == (4, 0)


def test_resolve_runtime_flags_override_settings() -> None:
    args = _build_parser().parse_args(["d", "--gpu", "--threads", "8"])
    assert _resolve_runtime(args, Settings(n_threads=4, use_gpu=False)) == (8, -1)


def test_resolve_runtime_no_gpu_forces_cpu() -> None:
    args = _build_parser().parse_args(["d", "--no-gpu"])
    assert _resolve_runtime(args, Settings(use_gpu=True)) == (None, 0)
