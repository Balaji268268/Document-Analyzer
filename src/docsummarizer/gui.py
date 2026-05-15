"""
DocSummarizer GUI
Modern cross-platform GUI using CustomTkinter.
"""

import contextlib
import os
import sys
import threading
from collections.abc import Callable
from pathlib import Path
from tkinter import filedialog, messagebox
from typing import Any

import customtkinter as ctk

from .document_parser import extract_text, get_document_info
from .io_helpers import write_summary_docx, write_summary_txt
from .logger import log_debug, log_error, log_info, log_startup
from .model_manager import (
    DEFAULT_MODEL,
    Summarizer,
    download_model,
    get_model_path,
    is_model_downloaded,
)

# Appearance settings
ctk.set_appearance_mode("System")  # "System", "Dark", "Light"
ctk.set_default_color_theme("blue")


class LoadingDialog(ctk.CTkToplevel):
    """A small loading dialog that appears during long operations."""

    def __init__(self, parent, message: str = "Loading..."):
        super().__init__(parent)

        self.title("")
        self.geometry("300x100")
        self.resizable(False, False)
        self.transient(parent)
        self.grab_set()
        self.overrideredirect(True)

        self.update_idletasks()
        parent_x = parent.winfo_x()
        parent_y = parent.winfo_y()
        parent_w = parent.winfo_width()
        parent_h = parent.winfo_height()
        x = parent_x + (parent_w - 300) // 2
        y = parent_y + (parent_h - 100) // 2
        self.geometry(f"300x100+{x}+{y}")

        self.frame = ctk.CTkFrame(self, corner_radius=10)
        self.frame.pack(fill="both", expand=True, padx=2, pady=2)

        self.message_label = ctk.CTkLabel(self.frame, text=message, font=ctk.CTkFont(size=14))
        self.message_label.pack(pady=(20, 10))

        self.progress = ctk.CTkProgressBar(self.frame, width=250)
        self.progress.pack(pady=(0, 20))
        self.progress.configure(mode="indeterminate")
        self.progress.start()

    def update_message(self, message: str):
        """Update the loading message."""
        self.message_label.configure(text=message)
        self.update()

    def close(self):
        """Close the loading dialog."""
        self.progress.stop()
        self.grab_release()
        self.destroy()


class DocSummarizerApp(ctk.CTk):
    """Main application window."""

    def __init__(self):
        super().__init__()

        log_startup()
        log_info("GUI initialization starting")

        self.title("DocSummarizer - Offline Document Summarization")
        self.geometry("900x700")
        self.minsize(700, 500)

        # `_summarizer` is touched by worker threads (load, reload, download
        # completion) and the main UI thread (button-state checks, summarize
        # action). All access goes through _get_summarizer / _set_summarizer
        # so we never read a half-assigned reference.
        self._summarizer: Summarizer | None = None
        self._summarizer_lock = threading.RLock()

        self.current_file: str | None = None
        self.extracted_text: str | None = None
        self._is_closing = False
        self._initial_load_dialog: LoadingDialog | None = None

        self.protocol("WM_DELETE_WINDOW", self._on_close)

        self._create_widgets()
        self._check_model_status()
        log_info("GUI initialization complete")

    # ------------------------------------------------------------------ #
    # Thread-safety helpers
    # ------------------------------------------------------------------ #

    def _ui(self, fn: Callable[..., Any], *args: Any, **kwargs: Any) -> None:
        """Marshal a UI mutation back onto the Tk main thread.

        Tkinter's C layer is not thread-safe; calling .configure / .set /
        .insert from a worker thread produces random crashes and silent
        corruption under load. Every worker-thread UI update must go
        through this helper.
        """
        self.after(0, lambda: fn(*args, **kwargs))

    def _get_summarizer(self) -> Summarizer | None:
        with self._summarizer_lock:
            return self._summarizer

    def _set_summarizer(self, summarizer: Summarizer | None) -> None:
        with self._summarizer_lock:
            old = self._summarizer
            self._summarizer = summarizer
        if old is not None and old is not summarizer:
            # Release llama.cpp memory eagerly; __del__ is best-effort
            del old

    # ------------------------------------------------------------------ #
    # Lifecycle
    # ------------------------------------------------------------------ #

    def _on_close(self):
        """Clean shutdown when window is closed."""
        if self._is_closing:
            return

        log_info("Application closing...")
        self._is_closing = True

        for widget in self.winfo_children():
            if isinstance(widget, ctk.CTkToplevel):
                with contextlib.suppress(Exception):
                    widget.destroy()

        if self._get_summarizer() is not None:
            log_debug("Releasing model from memory")
            self._set_summarizer(None)

        log_info("Application closed")

        with contextlib.suppress(Exception):
            self.destroy()

        sys.exit(0)

    # ------------------------------------------------------------------ #
    # Widget construction
    # ------------------------------------------------------------------ #

    def _create_widgets(self):
        """Create all GUI widgets."""
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)

        self.header_frame = ctk.CTkFrame(self)
        self.header_frame.grid(row=0, column=0, padx=10, pady=(10, 5), sticky="ew")
        self.header_frame.grid_columnconfigure(1, weight=1)

        self.title_label = ctk.CTkLabel(
            self.header_frame, text="DocSummarizer", font=ctk.CTkFont(size=24, weight="bold")
        )
        self.title_label.grid(row=0, column=0, padx=10, pady=5)

        self.status_label = ctk.CTkLabel(
            self.header_frame, text="Checking model status...", font=ctk.CTkFont(size=12)
        )
        self.status_label.grid(row=0, column=1, padx=10, pady=5, sticky="e")

        self.file_frame = ctk.CTkFrame(self)
        self.file_frame.grid(row=1, column=0, padx=10, pady=5, sticky="ew")
        self.file_frame.grid_columnconfigure(1, weight=1)

        self.select_btn = ctk.CTkButton(
            self.file_frame, text="Select File", command=self._select_file, width=120
        )
        self.select_btn.grid(row=0, column=0, padx=10, pady=10)

        self.file_label = ctk.CTkLabel(self.file_frame, text="No file selected", anchor="w")
        self.file_label.grid(row=0, column=1, padx=10, pady=10, sticky="ew")

        self.select_folder_btn = ctk.CTkButton(
            self.file_frame, text="Batch (Folder)", command=self._select_folder, width=120
        )
        self.select_folder_btn.grid(row=0, column=2, padx=10, pady=10)

        self.tabview = ctk.CTkTabview(self)
        self.tabview.grid(row=2, column=0, padx=10, pady=5, sticky="nsew")

        self.tab_summary = self.tabview.add("Summary")
        self.tab_text = self.tabview.add("Extracted Text")
        self.tab_settings = self.tabview.add("Settings")

        self.tab_summary.grid_columnconfigure(0, weight=1)
        self.tab_summary.grid_rowconfigure(0, weight=1)
        self.tab_text.grid_columnconfigure(0, weight=1)
        self.tab_text.grid_rowconfigure(0, weight=1)

        self.summary_text = ctk.CTkTextbox(self.tab_summary, wrap="word")
        self.summary_text.grid(row=0, column=0, padx=5, pady=5, sticky="nsew")
        self.summary_text.insert("1.0", "Summary will appear here after processing...")
        self.summary_text.configure(state="disabled")

        self.extracted_textbox = ctk.CTkTextbox(self.tab_text, wrap="word")
        self.extracted_textbox.grid(row=0, column=0, padx=5, pady=5, sticky="nsew")
        self.extracted_textbox.insert("1.0", "Extracted text will appear here...")
        self.extracted_textbox.configure(state="disabled")

        self._create_settings_tab()

        self.controls_frame = ctk.CTkFrame(self)
        self.controls_frame.grid(row=3, column=0, padx=10, pady=(5, 10), sticky="ew")
        self.controls_frame.grid_columnconfigure(1, weight=1)

        self.summary_type_label = ctk.CTkLabel(self.controls_frame, text="Summary Type:")
        self.summary_type_label.grid(row=0, column=0, padx=(10, 5), pady=10)

        self.summary_type_var = ctk.StringVar(value="detailed")
        self.summary_type_menu = ctk.CTkOptionMenu(
            self.controls_frame,
            variable=self.summary_type_var,
            values=["brief", "detailed", "structured"],
            width=120,
        )
        self.summary_type_menu.grid(row=0, column=1, padx=5, pady=10, sticky="w")

        self.progress_bar = ctk.CTkProgressBar(self.controls_frame)
        self.progress_bar.grid(row=0, column=2, padx=10, pady=10, sticky="ew")
        self.progress_bar.set(0)
        self.controls_frame.grid_columnconfigure(2, weight=1)

        self.summarize_btn = ctk.CTkButton(
            self.controls_frame,
            text="Summarize",
            command=self._start_summarization,
            width=120,
            state="disabled",
        )
        self.summarize_btn.grid(row=0, column=3, padx=5, pady=10)

        self.save_btn = ctk.CTkButton(
            self.controls_frame,
            text="Save Summary",
            command=self._save_summary,
            width=120,
            state="disabled",
        )
        self.save_btn.grid(row=0, column=4, padx=(5, 10), pady=10)

    def _create_settings_tab(self):
        """Create the settings tab content."""
        self.tab_settings.grid_columnconfigure(0, weight=1)

        model_label = ctk.CTkLabel(
            self.tab_settings, text="Model Settings", font=ctk.CTkFont(size=16, weight="bold")
        )
        model_label.grid(row=0, column=0, padx=10, pady=(10, 5), sticky="w")

        self.model_info_label = ctk.CTkLabel(
            self.tab_settings, text="Model: Checking...", anchor="w"
        )
        self.model_info_label.grid(row=1, column=0, padx=10, pady=5, sticky="w")

        self.download_btn = ctk.CTkButton(
            self.tab_settings,
            text="Download Model",
            command=self._start_model_download,
            width=150,
        )
        self.download_btn.grid(row=2, column=0, padx=10, pady=10, sticky="w")

        performance_label = ctk.CTkLabel(
            self.tab_settings, text="Performance", font=ctk.CTkFont(size=16, weight="bold")
        )
        performance_label.grid(row=3, column=0, padx=10, pady=(20, 5), sticky="w")

        cpu_count = os.cpu_count() or 8
        default_threads = max(4, cpu_count // 2)
        self.threads_var = ctk.IntVar(value=default_threads)

        threads_frame = ctk.CTkFrame(self.tab_settings, fg_color="transparent")
        threads_frame.grid(row=4, column=0, padx=10, pady=5, sticky="w")

        threads_label = ctk.CTkLabel(threads_frame, text="CPU Threads:")
        threads_label.grid(row=0, column=0, padx=(0, 10))

        self.threads_slider = ctk.CTkSlider(
            threads_frame,
            from_=2,
            to=cpu_count,
            number_of_steps=cpu_count - 2,
            variable=self.threads_var,
            width=200,
            command=self._on_threads_changed,
        )
        self.threads_slider.grid(row=0, column=1, padx=5)

        self.threads_value_label = ctk.CTkLabel(
            threads_frame, text=f"{default_threads} / {cpu_count}", width=60
        )
        self.threads_value_label.grid(row=0, column=2, padx=5)

        threads_hint = ctk.CTkLabel(
            self.tab_settings,
            text="Lower = less CPU usage but slower. Requires model reload.",
            font=ctk.CTkFont(size=11),
            text_color="gray",
        )
        threads_hint.grid(row=5, column=0, padx=10, pady=(0, 5), sticky="w")

        self.reload_model_btn = ctk.CTkButton(
            self.tab_settings,
            text="Reload Model",
            command=self._reload_model,
            width=150,
            state="disabled",
        )
        self.reload_model_btn.grid(row=6, column=0, padx=10, pady=5, sticky="w")

        appearance_label = ctk.CTkLabel(
            self.tab_settings, text="Appearance", font=ctk.CTkFont(size=16, weight="bold")
        )
        appearance_label.grid(row=7, column=0, padx=10, pady=(20, 5), sticky="w")

        self.appearance_var = ctk.StringVar(value="System")
        self.appearance_menu = ctk.CTkOptionMenu(
            self.tab_settings,
            variable=self.appearance_var,
            values=["System", "Light", "Dark"],
            command=self._change_appearance,
            width=150,
        )
        self.appearance_menu.grid(row=8, column=0, padx=10, pady=5, sticky="w")

        about_label = ctk.CTkLabel(
            self.tab_settings, text="About", font=ctk.CTkFont(size=16, weight="bold")
        )
        about_label.grid(row=9, column=0, padx=10, pady=(20, 5), sticky="w")

        about_text = ctk.CTkLabel(
            self.tab_settings,
            text="DocSummarizer - Offline Document Summarization Tool\n"
            "Uses a local AI model to summarize documents.\n"
            "No internet required after initial model download.\n\n"
            "Supported formats: PDF, DOCX, RTF, TXT, MD",
            anchor="w",
            justify="left",
        )
        about_text.grid(row=10, column=0, padx=10, pady=5, sticky="w")

    # ------------------------------------------------------------------ #
    # Model lifecycle
    # ------------------------------------------------------------------ #

    def _check_model_status(self):
        """Check if the model is downloaded and update UI accordingly."""
        if is_model_downloaded():
            self.status_label.configure(text="Model ready", text_color="green")
            self.model_info_label.configure(
                text=f"Model: {DEFAULT_MODEL['name']} ({DEFAULT_MODEL['size_gb']} GB) - Downloaded"
            )
            self.download_btn.configure(state="disabled", text="Model Downloaded")
            self._load_model()
        else:
            self.status_label.configure(text="Model not downloaded", text_color="orange")
            self.model_info_label.configure(
                text=f"Model: {DEFAULT_MODEL['name']} ({DEFAULT_MODEL['size_gb']} GB) - Not downloaded"
            )
            self.download_btn.configure(state="normal")

    def _load_model(self):
        """Load the model in a background thread."""
        n_threads = self.threads_var.get()
        # Show a loading dialog so the user has feedback during the
        # multi-second model load. _reload_model already did this; the
        # initial load was missing it.
        self._initial_load_dialog = LoadingDialog(self, f"Loading model ({n_threads} threads)...")
        # Disable file-selection buttons until the model is ready.
        self.select_btn.configure(state="disabled")
        self.select_folder_btn.configure(state="disabled")
        self.status_label.configure(text=f"Loading model ({n_threads} threads)...")

        def load():
            try:
                model_path = get_model_path()
                summarizer = Summarizer(model_path, n_threads=n_threads)
                self._set_summarizer(summarizer)
                self._ui(self._on_load_complete, True, None)
            except Exception as e:
                log_error(f"Model loading failed: {e!s}")
                self._ui(self._on_load_complete, False, str(e))

        threading.Thread(target=load, daemon=True).start()

    def _on_load_complete(self, success: bool, error: str | None) -> None:
        """Finalize state after _load_model finishes (main thread)."""
        if self._initial_load_dialog is not None:
            self._initial_load_dialog.close()
            self._initial_load_dialog = None
        self.select_btn.configure(state="normal")
        self.select_folder_btn.configure(state="normal")
        if success:
            self.status_label.configure(text="Ready", text_color="green")
            self.reload_model_btn.configure(state="disabled")
            self._update_button_states()
        else:
            self.status_label.configure(text=f"Error loading model: {error}", text_color="red")

    def _on_threads_changed(self, _value):
        """Handle CPU threads slider change."""
        threads = int(self.threads_var.get())
        cpu_count = os.cpu_count() or 8
        self.threads_value_label.configure(text=f"{threads} / {cpu_count}")
        if self._get_summarizer() is not None:
            self.reload_model_btn.configure(state="normal")

    def _reload_model(self):
        """Reload the model with new thread settings."""
        n_threads = self.threads_var.get()
        log_info(f"Reloading model with {n_threads} threads")

        loading = LoadingDialog(self, f"Reloading model with {n_threads} threads...")

        def reload():
            try:
                self._set_summarizer(None)
                model_path = get_model_path()
                summarizer = Summarizer(model_path, n_threads=n_threads)
                self._set_summarizer(summarizer)
                self._ui(self._on_reload_complete, loading, True, None)
            except Exception as e:
                log_error(f"Model reload failed: {e!s}")
                self._ui(self._on_reload_complete, loading, False, str(e))

        threading.Thread(target=reload, daemon=True).start()

    def _on_reload_complete(
        self, loading_dialog: LoadingDialog, success: bool, error: str | None
    ) -> None:
        """Handle model reload completion (main thread)."""
        loading_dialog.close()
        if success:
            self.status_label.configure(text="Ready", text_color="green")
            self.reload_model_btn.configure(state="disabled")
            self._update_button_states()
        else:
            self.status_label.configure(text=f"Error: {error}", text_color="red")

    def _start_model_download(self):
        """Start downloading the model in a background thread."""
        self.download_btn.configure(state="disabled", text="Downloading...")
        self.progress_bar.set(0)

        def on_progress(percent: float, message: str) -> None:
            # Called from huggingface_hub's download thread. Marshal to UI.
            self._ui(self.progress_bar.set, percent / 100)
            self._ui(self.status_label.configure, text=message)

        def download():
            _path, error = download_model(progress_callback=on_progress)
            if error:
                self._ui(self.status_label.configure, text=error, text_color="red")
                self._ui(self.download_btn.configure, state="normal", text="Retry Download")
            else:
                self._ui(self.download_btn.configure, text="Model Downloaded")
                self._ui(self._load_model)

        threading.Thread(target=download, daemon=True).start()

    # ------------------------------------------------------------------ #
    # File handling
    # ------------------------------------------------------------------ #

    def _select_file(self):
        """Open file dialog to select a document."""
        filetypes = [
            ("All Supported", "*.pdf *.docx *.rtf *.txt *.md"),
            ("PDF Files", "*.pdf"),
            ("Word Documents", "*.docx"),
            ("Text Files", "*.txt *.md *.rtf"),
        ]

        filepath = filedialog.askopenfilename(title="Select Document", filetypes=filetypes)

        if filepath:
            self._process_file(filepath)

    def _select_folder(self):
        """Open folder dialog for batch processing."""
        folder = filedialog.askdirectory(title="Select Folder with Documents")

        if folder:
            extensions = (".pdf", ".docx", ".rtf", ".txt", ".md")
            files = [
                f for f in Path(folder).iterdir() if f.is_file() and f.suffix.lower() in extensions
            ]

            if not files:
                messagebox.showinfo(
                    "No Files", "No supported documents found in the selected folder."
                )
                return

            result = messagebox.askyesno(
                "Batch Processing", f"Found {len(files)} document(s). Process all?"
            )

            if result:
                self._batch_process(files)

    def _process_file(self, filepath: str):
        """Extract text from the selected file."""
        self.current_file = filepath
        info = get_document_info(filepath)
        self.file_label.configure(text=f"{info['name']} ({info['size_mb']} MB)")

        self.status_label.configure(text="Extracting text...")
        text, error = extract_text(filepath)

        if error:
            self.status_label.configure(text=error, text_color="red")
            self.extracted_text = None
        else:
            self.extracted_text = text
            self.status_label.configure(text="Text extracted", text_color="green")

            self.extracted_textbox.configure(state="normal")
            self.extracted_textbox.delete("1.0", "end")
            self.extracted_textbox.insert("1.0", text)
            self.extracted_textbox.configure(state="disabled")

        self._update_button_states()

    def _update_button_states(self):
        """Update button states based on current state."""
        can_summarize = self._get_summarizer() is not None and self.extracted_text is not None
        self.summarize_btn.configure(state="normal" if can_summarize else "disabled")

    # ------------------------------------------------------------------ #
    # Summarization
    # ------------------------------------------------------------------ #

    def _start_summarization(self):
        """Start the summarization process in a background thread."""
        summarizer = self._get_summarizer()
        if summarizer is None or not self.extracted_text:
            return

        text_to_summarize = self.extracted_text
        summary_type = self.summary_type_var.get()

        self.summarize_btn.configure(state="disabled", text="Processing...")
        self.progress_bar.set(0.3)
        self.status_label.configure(text="Generating summary...")

        def summarize():
            try:
                summary = summarizer.summarize(text_to_summarize, summary_type=summary_type)
                self._ui(self._on_summary_complete, summary, None)
            except Exception as e:
                log_error(f"Summarization failed: {e!s}")
                self._ui(self._on_summary_complete, None, str(e))

        threading.Thread(target=summarize, daemon=True).start()

    def _on_summary_complete(self, summary: str | None, error: str | None) -> None:
        """Render summarization result on the main thread."""
        try:
            if error is not None:
                self.status_label.configure(text=f"Error: {error}", text_color="red")
                return
            self.progress_bar.set(1.0)
            self.status_label.configure(text="Summary complete", text_color="green")
            self.summary_text.configure(state="normal")
            self.summary_text.delete("1.0", "end")
            self.summary_text.insert("1.0", summary or "")
            self.summary_text.configure(state="disabled")
            self.save_btn.configure(state="normal")
            self.tabview.set("Summary")
        finally:
            self.summarize_btn.configure(state="normal", text="Summarize")
            self.progress_bar.set(0)

    def _batch_process(self, files: list[Path]):
        """Process multiple files and save summaries."""
        output_folder = filedialog.askdirectory(title="Select Output Folder for Summaries")
        if not output_folder:
            return

        summarizer = self._get_summarizer()
        if summarizer is None:
            messagebox.showerror("No Model", "The model is still loading. Try again in a moment.")
            return

        summary_type = self.summary_type_var.get()
        self.summarize_btn.configure(state="disabled")

        def process_batch():
            total = len(files)
            success_count = 0
            failures: list[tuple[str, str]] = []

            for i, filepath in enumerate(files):
                self._ui(
                    self.status_label.configure,
                    text=f"Processing {i + 1}/{total}: {filepath.name}",
                )
                self._ui(self.progress_bar.set, (i + 0.5) / total)

                text, error = extract_text(str(filepath))
                if error:
                    failures.append((filepath.name, error))
                    continue

                try:
                    summary = summarizer.summarize(text, summary_type=summary_type)
                    output_path = Path(output_folder) / f"{filepath.stem}_summary.txt"
                    write_summary_txt(
                        output_path,
                        source_name=filepath.name,
                        summary=summary,
                        summary_type=summary_type,
                    )
                    success_count += 1
                except Exception as e:
                    log_error(f"Batch processing failed for {filepath}: {e!s}")
                    failures.append((filepath.name, str(e)))

                self._ui(self.progress_bar.set, (i + 1) / total)

            self._ui(self._on_batch_complete, success_count, total, failures, output_folder)

        threading.Thread(target=process_batch, daemon=True).start()

    def _on_batch_complete(
        self,
        success_count: int,
        total: int,
        failures: list[tuple[str, str]],
        output_folder: str,
    ) -> None:
        """Render batch completion on the main thread."""
        self.status_label.configure(
            text=f"Batch complete: {success_count}/{total} files summarized",
            text_color="green" if success_count == total else "orange",
        )
        self.summarize_btn.configure(state="normal")

        message = f"Processed {success_count}/{total} files.\nSummaries saved to: {output_folder}"
        if failures:
            preview = "\n".join(f"  - {name}: {err}" for name, err in failures[:5])
            more = f"\n  ... and {len(failures) - 5} more" if len(failures) > 5 else ""
            message += f"\n\nFailed:\n{preview}{more}"
        messagebox.showinfo("Batch Complete", message)

    # ------------------------------------------------------------------ #
    # Save / appearance
    # ------------------------------------------------------------------ #

    def _save_summary(self):
        """Save the current summary to a file."""
        if not self.current_file:
            return

        default_name = Path(self.current_file).stem + "_summary.txt"

        filepath = filedialog.asksaveasfilename(
            title="Save Summary",
            defaultextension=".txt",
            initialfile=default_name,
            filetypes=[
                ("Text File", "*.txt"),
                ("Markdown", "*.md"),
                ("Word Document", "*.docx"),
            ],
        )

        if not filepath:
            return

        self.summary_text.configure(state="normal")
        content = self.summary_text.get("1.0", "end-1c")
        self.summary_text.configure(state="disabled")

        source_name = Path(self.current_file).name
        if filepath.endswith(".docx"):
            write_summary_docx(filepath, source_name=source_name, summary=content)
        else:
            # The on-screen textbox already includes whatever the user is
            # looking at; writing it verbatim (no header) matches existing
            # behavior for the manual Save flow. Batch-mode saves do add
            # a standard header — those go through write_summary_txt.
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(content)

        self.status_label.configure(text=f"Saved: {Path(filepath).name}", text_color="green")

    def _change_appearance(self, mode: str):
        """Change the application appearance mode."""
        ctk.set_appearance_mode(mode)


def main():
    """Main entry point."""
    app = DocSummarizerApp()
    app.mainloop()


if __name__ == "__main__":
    main()
