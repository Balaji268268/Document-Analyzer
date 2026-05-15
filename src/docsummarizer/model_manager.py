"""
Model Manager Module
Handles downloading, loading, and running the local LLM.
"""

import os
import sys
import time
from collections.abc import Callable
from pathlib import Path

from huggingface_hub import hf_hub_download

from .logger import get_memory_usage_mb, log_debug, log_error, log_info, log_warning

# Default model configuration
DEFAULT_MODEL = {
    "repo_id": "TheBloke/Mistral-7B-Instruct-v0.2-GGUF",
    "filename": "mistral-7b-instruct-v0.2.Q4_K_M.gguf",
    "name": "Mistral 7B Instruct",
    "size_gb": 4.4,
}


def get_models_directory() -> Path:
    """Get the directory where models are stored."""
    if sys.platform == "win32":
        base = Path(os.environ.get("LOCALAPPDATA", Path.home() / "AppData" / "Local"))
    elif sys.platform == "darwin":
        base = Path.home() / "Library" / "Application Support"
    else:
        base = Path(os.environ.get("XDG_DATA_HOME", Path.home() / ".local" / "share"))

    models_dir = base / "DocSummarizer" / "models"
    models_dir.mkdir(parents=True, exist_ok=True)
    return models_dir


def is_model_downloaded(model_config: dict | None = None) -> bool:
    """Check if the model file exists locally."""
    if model_config is None:
        model_config = DEFAULT_MODEL

    return (get_models_directory() / model_config["filename"]).exists()


def get_model_path(model_config: dict | None = None) -> Path:
    """Get the full path to the model file."""
    if model_config is None:
        model_config = DEFAULT_MODEL

    return get_models_directory() / model_config["filename"]


def _build_progress_tqdm(callback: Callable[[float, str], None]):
    """Build a tqdm subclass that fires `callback(percent, message)` on each update.

    huggingface_hub accepts a `tqdm_class` parameter for `hf_hub_download`, but
    the only "progress" the GUI ever saw was the 0% and 100% sentinels emitted
    by `download_model`. Wiring a custom tqdm in lets a long (~4.4 GB) download
    actually update the GUI bar as bytes arrive.
    """
    from tqdm.auto import tqdm as _BaseTqdm

    class _ProgressTqdm(_BaseTqdm):
        def update(self, n: int = 1):
            ret = super().update(n)
            try:
                if self.total and self.total > 0:
                    pct = (self.n / self.total) * 100.0
                    mb_done = self.n / (1024 * 1024)
                    mb_total = self.total / (1024 * 1024)
                    callback(pct, f"Downloading {mb_done:.0f} / {mb_total:.0f} MB")
            except Exception as exc:
                # Progress reporting must never break the download itself.
                log_debug(f"Progress callback raised: {exc!s}")
            return ret

    return _ProgressTqdm


def download_model(
    model_config: dict | None = None,
    progress_callback: Callable[[float, str], None] | None = None,
) -> tuple[Path, str | None]:
    """Download the model from HuggingFace.

    Returns ``(model_path, error_message)``; ``error_message`` is None on
    success. ``progress_callback`` (if given) receives ``(percent, message)``
    updates as bytes arrive, plus a final 100% / "Download complete" call.
    """
    if model_config is None:
        model_config = DEFAULT_MODEL

    models_dir = get_models_directory()
    model_path = models_dir / model_config["filename"]

    log_info(f"Model download requested: {model_config['name']}")
    log_debug(f"Model path: {model_path}")
    log_debug(f"Models directory: {models_dir}")

    if model_path.exists():
        file_size_gb = model_path.stat().st_size / (1024**3)
        log_info(f"Model already exists: {model_path.name} ({file_size_gb:.2f} GB)")
        if progress_callback:
            progress_callback(100.0, "Model already downloaded")
        return model_path, None

    try:
        log_info(f"Starting download: {model_config['repo_id']}/{model_config['filename']}")
        log_info(f"Expected size: ~{model_config['size_gb']} GB")

        if progress_callback:
            progress_callback(
                0.0, f"Downloading {model_config['name']} (~{model_config['size_gb']} GB)..."
            )

        start_time = time.time()

        tqdm_class = _build_progress_tqdm(progress_callback) if progress_callback else None

        downloaded_path = hf_hub_download(
            repo_id=model_config["repo_id"],
            filename=model_config["filename"],
            local_dir=models_dir,
            tqdm_class=tqdm_class,
        )

        elapsed = time.time() - start_time
        file_size_gb = Path(downloaded_path).stat().st_size / (1024**3)
        log_info(f"Download complete: {file_size_gb:.2f} GB in {elapsed:.1f}s")

        if progress_callback:
            progress_callback(100.0, "Download complete")

        return Path(downloaded_path), None

    except Exception as e:
        error_msg = f"Failed to download model: {e!s}"
        log_error(error_msg)
        log_error(f"Exception type: {type(e).__name__}")
        if progress_callback:
            progress_callback(0.0, error_msg)
        return model_path, error_msg


class Summarizer:
    """Handles text summarization using the local LLM."""

    def __init__(self, model_path: Path, n_ctx: int = 8192, n_threads: int | None = None):
        """Initialize the summarizer with a model.

        Args:
            model_path: Path to the GGUF model file
            n_ctx: Context window size (default 8192 for longer documents)
            n_threads: Number of CPU threads. `None` = auto (half of available
                cores). Note: `0` is a legitimate llama.cpp value meaning
                "let the library decide" and is passed through.
        """
        from llama_cpp import Llama

        self.n_ctx = n_ctx
        cpu_count = os.cpu_count() or 8
        default_threads = max(4, cpu_count // 2)
        # Use `is None` rather than truthiness: callers may legitimately pass
        # `0` to mean "let llama.cpp decide", and `n_threads or default` would
        # silently override that.
        self.n_threads = default_threads if n_threads is None else n_threads

        log_info("Initializing Summarizer")
        log_info(f"Model path: {model_path}")
        log_info(f"Context window: {n_ctx} tokens")
        log_info(f"CPU threads: {self.n_threads} of {cpu_count} available")
        log_debug(f"Memory before loading: {get_memory_usage_mb()} MB")

        start_time = time.time()

        self.llm = Llama(
            model_path=str(model_path),
            n_ctx=n_ctx,
            n_threads=self.n_threads,
            n_threads_batch=self.n_threads,
            verbose=False,
        )

        load_time = time.time() - start_time
        log_info(f"Model loaded successfully in {load_time:.2f}s")
        log_debug(f"Memory after loading: {get_memory_usage_mb()} MB")

    def summarize(
        self,
        text: str,
        summary_type: str = "detailed",
        max_tokens: int = 1024,
    ) -> str:
        """Generate a summary of the given text.

        Args:
            text: The text to summarize
            summary_type: "brief", "detailed", or "structured"
            max_tokens: Maximum tokens in the response

        Returns:
            The generated summary
        """
        original_length = len(text)
        log_info(f"Starting summarization: type={summary_type}, input_chars={original_length}")
        log_debug(f"Max tokens for response: {max_tokens}")

        # Rough estimate: ~3 chars per token (conservative for the prompt
        # template); reserve ~1500 tokens for the prompt scaffolding and
        # response.
        max_input_tokens = self.n_ctx - 1500
        max_input_chars = max_input_tokens * 3
        if len(text) > max_input_chars:
            text = text[:max_input_chars] + "\n\n[Document truncated due to length...]"
            log_warning(f"Text truncated from {original_length} to {max_input_chars} chars")

        prompts = {
            "brief": """Summarize the following document in one concise paragraph (3-5 sentences).
Focus on the main topic, key findings, and conclusions.

Document:
{text}

Summary:""",
            "detailed": """Provide a detailed summary of the following document. Include:
- Main topic and purpose
- Key points and arguments
- Important findings or conclusions
- Any significant methods or approaches mentioned

Document:
{text}

Detailed Summary:""",
            "structured": """Analyze the following document and provide a structured summary with these sections:

**Title/Topic:** (What is this document about?)
**Purpose:** (Why was this written?)
**Key Points:** (Main arguments or findings, as bullet points)
**Methods:** (If applicable, how was the research/work conducted?)
**Conclusions:** (What are the main takeaways?)
**Significance:** (Why does this matter?)

Document:
{text}

Structured Summary:""",
        }

        prompt = prompts.get(summary_type, prompts["detailed"]).format(text=text)
        prompt_tokens_estimate = len(prompt) // 3
        log_debug(f"Prompt size: {len(prompt)} chars (~{prompt_tokens_estimate} tokens)")

        log_info("Generating summary (LLM inference starting)...")
        start_time = time.time()

        response = self.llm(
            prompt,
            max_tokens=max_tokens,
            temperature=0.3,
            top_p=0.9,
            stop=["Document:", "\n\n\n"],
            echo=False,
        )

        elapsed = time.time() - start_time
        summary = response["choices"][0]["text"].strip()

        output_tokens = response.get("usage", {}).get("completion_tokens", len(summary) // 4)
        tokens_per_sec = output_tokens / elapsed if elapsed > 0 else 0

        log_info(f"Summary generated in {elapsed:.2f}s")
        log_info(f"Output: {len(summary)} chars, ~{output_tokens} tokens")
        log_info(f"Speed: {tokens_per_sec:.1f} tokens/sec")
        log_debug(f"Memory usage: {get_memory_usage_mb()} MB")

        return summary

    def __del__(self):
        """Cleanup when the summarizer is destroyed."""
        if hasattr(self, "llm"):
            del self.llm
