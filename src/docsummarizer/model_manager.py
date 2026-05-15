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

# Alternative smaller model for low-resource systems
SMALL_MODEL = {
    "repo_id": "TheBloke/Phi-3-mini-4k-instruct-GGUF",
    "filename": "phi-3-mini-4k-instruct.Q4_K_M.gguf",
    "name": "Phi-3 Mini",
    "size_gb": 2.4,
}


def get_models_directory() -> Path:
    """Get the directory where models are stored."""
    # Use user's home directory for model storage
    if sys.platform == "win32":
        base = Path(os.environ.get("LOCALAPPDATA", Path.home() / "AppData" / "Local"))
    elif sys.platform == "darwin":
        base = Path.home() / "Library" / "Application Support"
    else:
        base = Path(os.environ.get("XDG_DATA_HOME", Path.home() / ".local" / "share"))

    models_dir = base / "DocSummarizer" / "models"
    models_dir.mkdir(parents=True, exist_ok=True)
    return models_dir


def is_model_downloaded(model_config: dict = None) -> bool:
    """Check if the model file exists locally."""
    if model_config is None:
        model_config = DEFAULT_MODEL

    model_path = get_models_directory() / model_config["filename"]
    return model_path.exists()


def get_model_path(model_config: dict = None) -> Path:
    """Get the full path to the model file."""
    if model_config is None:
        model_config = DEFAULT_MODEL

    return get_models_directory() / model_config["filename"]


def download_model(
    model_config: dict = None, progress_callback: Callable[[float, str], None] | None = None
) -> tuple[Path, str | None]:
    """
    Download the model from HuggingFace.

    Args:
        model_config: Model configuration dict
        progress_callback: Optional callback(progress_percent, status_message)

    Returns:
        Tuple of (model_path, error_message)
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

        # Download from HuggingFace
        downloaded_path = hf_hub_download(
            repo_id=model_config["repo_id"],
            filename=model_config["filename"],
            local_dir=models_dir,
            local_dir_use_symlinks=False,
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

    def __init__(self, model_path: Path, n_ctx: int = 8192, n_threads: int = None):
        """
        Initialize the summarizer with a model.

        Args:
            model_path: Path to the GGUF model file
            n_ctx: Context window size (default 8192 for longer documents)
            n_threads: Number of CPU threads (None = auto)
        """
        from llama_cpp import Llama

        self.n_ctx = n_ctx
        # Use half of available cores to reduce CPU load while maintaining decent speed
        cpu_count = os.cpu_count() or 8
        default_threads = max(4, cpu_count // 2)
        self.n_threads = n_threads or default_threads

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
            n_threads_batch=self.n_threads,  # Also limit batch processing threads
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
        progress_callback: Callable[[str], None] | None = None,
    ) -> str:
        """
        Generate a summary of the given text.

        Args:
            text: The text to summarize
            summary_type: "brief", "detailed", or "structured"
            max_tokens: Maximum tokens in the response
            progress_callback: Optional callback for streaming output

        Returns:
            The generated summary
        """
        original_length = len(text)
        log_info(f"Starting summarization: type={summary_type}, input_chars={original_length}")
        log_debug(f"Max tokens for response: {max_tokens}")

        # Truncate text if too long for context window
        # Rough estimate: ~4 chars per token, leave room for prompt (~500 tokens) and response
        max_input_tokens = self.n_ctx - 1500  # Reserve for prompt and output
        max_input_chars = max_input_tokens * 3  # Conservative: 3 chars per token
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

        # Generate response
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

        # Log performance metrics
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
