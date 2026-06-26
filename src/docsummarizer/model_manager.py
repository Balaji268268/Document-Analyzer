"""
Model Manager Module
Handles downloading, loading, and running the local LLM.
"""

import os
import time
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from huggingface_hub import hf_hub_download

from .logger import get_memory_usage_mb, log_debug, log_error, log_info
from .paths import app_data_dir

# Supported summary types. Kept as module-level string constants (rather than
# enum.StrEnum, which requires Python 3.11+) so callers can keep passing plain
# strings without an extra import.
SUMMARY_TYPE_BRIEF = "brief"
SUMMARY_TYPE_DETAILED = "detailed"
SUMMARY_TYPE_STRUCTURED = "structured"
SUMMARY_TYPES = (SUMMARY_TYPE_BRIEF, SUMMARY_TYPE_DETAILED, SUMMARY_TYPE_STRUCTURED)


@dataclass(frozen=True)
class ModelConfig:
    """Static metadata for a GGUF model on HuggingFace."""

    repo_id: str
    filename: str
    name: str
    size_gb: float


# Qwen3 4B Instruct (2507 refresh): a non-thinking instruct model that, in
# side-by-side testing, produced markedly more structured and faithful
# summaries than the previous Mistral 7B v0.2 default while being smaller
# (2.5 GB vs 4.4 GB) and faster. GGUFs are sourced from Unsloth, since the
# old TheBloke repos are no longer maintained.
DEFAULT_MODEL = ModelConfig(
    repo_id="unsloth/Qwen3-4B-Instruct-2507-GGUF",
    filename="Qwen3-4B-Instruct-2507-Q4_K_M.gguf",
    name="Qwen3 4B Instruct 2507",
    size_gb=2.5,
)

# Summarization tuning -------------------------------------------------------
# Conservative chars-per-token estimate, used to keep prompts within the
# context window without taking on a tokenizer dependency.
_CHARS_PER_TOKEN = 3
# Tokens reserved for everything in a request that isn't the document itself
# (system prompt, instruction, chat-template overhead).
_SCAFFOLD_TOKENS = 400
# Floor on the per-chunk token budget, so a tiny n_ctx can't yield degenerate
# one-character chunks.
_MIN_CHUNK_TOKENS = 512

_CLOSED_MESSAGE = "Summarizer has been closed; create a new instance."

_SYSTEM_PROMPT = (
    "You are a precise document-summarization assistant. Produce only the "
    "requested summary, based solely on the provided document. Do not add a "
    "preamble, a sign-off, or follow-up questions."
)

_SUMMARY_INSTRUCTIONS = {
    SUMMARY_TYPE_BRIEF: (
        "Summarize the document below in one concise paragraph (3-5 sentences), "
        "focusing on the main topic, key findings, and conclusions."
    ),
    SUMMARY_TYPE_DETAILED: (
        "Provide a detailed summary of the document below. Include the main topic "
        "and purpose, the key points and arguments, important findings or "
        "conclusions, and any significant methods or approaches mentioned."
    ),
    SUMMARY_TYPE_STRUCTURED: (
        "Analyze the document below and provide a structured summary with these "
        "sections, each on its own line:\n"
        "**Title/Topic:** What is this document about?\n"
        "**Purpose:** Why was this written?\n"
        "**Key Points:** Main arguments or findings, as bullet points.\n"
        "**Methods:** If applicable, how the work was conducted.\n"
        "**Conclusions:** The main takeaways.\n"
        "**Significance:** Why it matters."
    ),
}


def _split_into_chunks(text: str, max_chars: int) -> list[str]:
    """Split `text` into chunks no larger than `max_chars`.

    Prefers paragraph boundaries (blank-line separated), keeping chunks
    coherent. A single paragraph longer than `max_chars` is hard-split as a
    last resort. Pure function (no model state) so it can be unit-tested
    directly.
    """
    if max_chars <= 0 or len(text) <= max_chars:
        return [text]

    chunks: list[str] = []
    current = ""
    for para in text.split("\n\n"):
        if len(para) > max_chars:
            if current:
                chunks.append(current)
                current = ""
            chunks.extend(para[i : i + max_chars] for i in range(0, len(para), max_chars))
            continue
        candidate = f"{current}\n\n{para}" if current else para
        if len(candidate) <= max_chars:
            current = candidate
        else:
            if current:
                chunks.append(current)
            current = para
    if current:
        chunks.append(current)
    return chunks


def get_models_directory() -> Path:
    """Get the directory where models are stored."""
    return app_data_dir("models")


def is_model_downloaded(model_config: ModelConfig = DEFAULT_MODEL) -> bool:
    """Check if the model file exists locally."""
    return (get_models_directory() / model_config.filename).exists()


def get_model_path(model_config: ModelConfig = DEFAULT_MODEL) -> Path:
    """Get the full path to the model file."""
    return get_models_directory() / model_config.filename


def _build_progress_tqdm(callback: Callable[[float, str], None]) -> type[Any]:
    """Build a tqdm subclass that fires `callback` on each whole-MB step.

    huggingface_hub instantiates this for `hf_hub_download`. tqdm calls
    `update()` once per HTTP chunk (~thousands over a multi-GB download); we
    coalesce to one callback per integer megabyte so the GUI doesn't burn
    Tk main-loop wakeups on no-op text changes.
    """
    from tqdm.auto import tqdm as _BaseTqdm  # noqa: N812

    class _ProgressTqdm(_BaseTqdm):  # type: ignore[misc]
        _last_reported_mb = -1

        def update(self, n: int = 1) -> Any:
            ret = super().update(n)
            try:
                if not self.total or self.total <= 0:
                    return ret
                mb_done = int(self.n / (1024 * 1024))
                if mb_done == self._last_reported_mb:
                    return ret
                self._last_reported_mb = mb_done
                pct = (self.n / self.total) * 100.0
                mb_total = self.total / (1024 * 1024)
                callback(pct, f"Downloading {mb_done} / {mb_total:.0f} MB")
            except Exception as exc:
                # Progress reporting must never break the download itself.
                log_debug(f"Progress callback raised: {exc!s}")
            return ret

    return _ProgressTqdm


def download_model(
    model_config: ModelConfig = DEFAULT_MODEL,
    progress_callback: Callable[[float, str], None] | None = None,
) -> tuple[Path, str | None]:
    """Download the model from HuggingFace.

    Returns ``(model_path, error_message)``; ``error_message`` is None on
    success. ``progress_callback`` (if given) receives ``(percent, message)``
    updates as bytes arrive, plus a final 100% / "Download complete" call.
    """
    models_dir = get_models_directory()
    model_path = models_dir / model_config.filename

    log_info(f"Model download requested: {model_config.name}")
    log_debug(f"Model path: {model_path}")
    log_debug(f"Models directory: {models_dir}")

    if model_path.exists():
        file_size_gb = model_path.stat().st_size / (1024**3)
        log_info(f"Model already exists: {model_path.name} ({file_size_gb:.2f} GB)")
        if progress_callback:
            progress_callback(100.0, "Model already downloaded")
        return model_path, None

    try:
        log_info(f"Starting download: {model_config.repo_id}/{model_config.filename}")
        log_info(f"Expected size: ~{model_config.size_gb} GB")

        if progress_callback:
            progress_callback(
                0.0, f"Downloading {model_config.name} (~{model_config.size_gb} GB)..."
            )

        start_time = time.time()

        tqdm_class = _build_progress_tqdm(progress_callback) if progress_callback else None

        downloaded_path = hf_hub_download(
            repo_id=model_config.repo_id,
            filename=model_config.filename,
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

    def __init__(
        self,
        model_path: Path,
        n_ctx: int = 8192,
        n_threads: int | None = None,
        n_gpu_layers: int = 0,
    ):
        """Initialize the summarizer with a model.

        Args:
            model_path: Path to the GGUF model file
            n_ctx: Context window size (default 8192). Documents longer than
                this are summarized via map-reduce chunking.
            n_threads: Number of CPU threads. `None` = auto (half of available
                cores). `0` means "let llama.cpp decide" and is passed through.
            n_gpu_layers: Model layers to offload to the GPU. `0` (default)
                keeps inference fully on the CPU for portability; `-1` offloads
                all layers. Ignored by CPU-only llama-cpp builds.
        """
        from llama_cpp import Llama

        self.n_ctx = n_ctx
        cpu_count = os.cpu_count() or 8
        default_threads = max(4, cpu_count // 2)
        self.n_threads = default_threads if n_threads is None else n_threads
        self.n_gpu_layers = n_gpu_layers

        log_info("Initializing Summarizer")
        log_info(f"Model path: {model_path}")
        log_info(f"Context window: {n_ctx} tokens")
        log_info(f"CPU threads: {self.n_threads} of {cpu_count} available")
        log_info(
            f"GPU layers: {n_gpu_layers} ({'GPU offload enabled' if n_gpu_layers else 'CPU only'})"
        )
        log_debug(f"Memory before loading: {get_memory_usage_mb()} MB")

        start_time = time.time()

        self.llm: Llama | None = Llama(
            model_path=str(model_path),
            n_ctx=n_ctx,
            n_threads=self.n_threads,
            n_threads_batch=self.n_threads,
            n_gpu_layers=n_gpu_layers,
            verbose=False,
        )

        load_time = time.time() - start_time
        log_info(f"Model loaded successfully in {load_time:.2f}s")
        log_debug(f"Memory after loading: {get_memory_usage_mb()} MB")

    def summarize(
        self,
        text: str,
        summary_type: str = SUMMARY_TYPE_DETAILED,
        max_tokens: int = 1024,
    ) -> str:
        """Generate a summary of the given text.

        Documents that fit the context window are summarized in a single pass.
        Longer documents are handled with a map-reduce strategy: the text is
        split into context-sized chunks, each is summarized, and the partial
        summaries are synthesized into one — so no content is silently dropped.

        Args:
            text: The text to summarize
            summary_type: one of `SUMMARY_TYPES`. Unknown values fall back to
                "detailed" to preserve the prior tolerant behavior.
            max_tokens: Maximum tokens in the response

        Returns:
            The generated summary
        """
        if self.llm is None:
            raise RuntimeError(_CLOSED_MESSAGE)

        text = text.strip()
        log_info(f"Starting summarization: type={summary_type}, input_chars={len(text)}")

        budget_tokens = max(self.n_ctx - max_tokens - _SCAFFOLD_TOKENS, _MIN_CHUNK_TOKENS)
        budget_chars = budget_tokens * _CHARS_PER_TOKEN

        if len(text) <= budget_chars:
            start_time = time.time()
            summary = self._summarize_once(text, summary_type, max_tokens)
            self._log_speed(summary, time.time() - start_time)
            return summary

        # Document exceeds the context budget: map-reduce.
        chunks = _split_into_chunks(text, budget_chars)
        log_info(f"Document exceeds context budget; summarizing in {len(chunks)} chunks")
        start_time = time.time()

        partials = []
        for i, chunk in enumerate(chunks, 1):
            log_info(f"Summarizing chunk {i}/{len(chunks)} ({len(chunk)} chars)")
            partials.append(self._summarize_once(chunk, summary_type, max_tokens))
        combined = "\n\n".join(partials)

        # Reduce. If the combined partials still overflow (a very long
        # document with many chunks), recurse — each pass strictly shrinks the
        # text, so this terminates.
        if len(combined) > budget_chars:
            log_info("Combined section summaries still exceed budget; reducing again")
            return self.summarize(combined, summary_type, max_tokens)

        summary = self._synthesize(combined, summary_type, max_tokens)
        self._log_speed(summary, time.time() - start_time)
        return summary

    def _summarize_once(self, text: str, summary_type: str, max_tokens: int) -> str:
        """Summarize text that fits within the context window in one call."""
        instruction = _SUMMARY_INSTRUCTIONS.get(
            summary_type, _SUMMARY_INSTRUCTIONS[SUMMARY_TYPE_DETAILED]
        )
        return self._chat(f"{instruction}\n\nDocument:\n{text}", max_tokens)

    def _synthesize(self, partials_text: str, summary_type: str, max_tokens: int) -> str:
        """Combine per-chunk summaries into one coherent summary."""
        instruction = _SUMMARY_INSTRUCTIONS.get(
            summary_type, _SUMMARY_INSTRUCTIONS[SUMMARY_TYPE_DETAILED]
        )
        prompt = (
            "Below are summaries of consecutive sections of a single document. "
            "Combine them into one coherent summary, removing redundancy.\n\n"
            f"{instruction}\n\nSection summaries:\n{partials_text}"
        )
        return self._chat(prompt, max_tokens)

    def _chat(self, user_content: str, max_tokens: int) -> str:
        """Run one chat completion, applying the model's own chat template.

        Using ``create_chat_completion`` (rather than a raw prompt string) lets
        llama.cpp wrap the message in whatever instruction format the loaded
        model expects, so swapping models doesn't require hand-editing prompts.
        """
        llm = self.llm
        if llm is None:
            raise RuntimeError(_CLOSED_MESSAGE)
        response = llm.create_chat_completion(
            messages=[
                {"role": "system", "content": _SYSTEM_PROMPT},
                {"role": "user", "content": user_content},
            ],
            max_tokens=max_tokens,
            temperature=0.3,
            top_p=0.9,
        )
        content = response["choices"][0]["message"].get("content") or ""
        return str(content).strip()

    def _log_speed(self, summary: str, elapsed: float) -> None:
        approx_tokens = max(len(summary) // 4, 1)
        tokens_per_sec = approx_tokens / elapsed if elapsed > 0 else 0
        log_info(
            f"Summary generated in {elapsed:.2f}s "
            f"(~{approx_tokens} tokens, {tokens_per_sec:.1f} tok/s)"
        )
        log_debug(f"Memory usage: {get_memory_usage_mb()} MB")

    def close(self) -> None:
        """Release the underlying llama.cpp model.

        Safe to call multiple times. After close(), `summarize()` raises;
        instantiate a new Summarizer to reload. Prefer this to relying on
        `__del__`, which is unreliable during interpreter shutdown.
        """
        if self.llm is not None:
            del self.llm
            self.llm = None

    def __enter__(self) -> "Summarizer":
        return self

    def __exit__(self, exc_type: object, exc_val: object, exc_tb: object) -> None:
        self.close()
