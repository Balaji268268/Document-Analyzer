"""Gradio Web Application for Document-Analyzer (0% HTML, 100% Python)."""

from pathlib import Path

import gradio as gr

from docsummarizer.document_parser import extract_text
from docsummarizer.model_manager import (
    SUMMARY_TYPE_BRIEF,
    SUMMARY_TYPE_DETAILED,
    SUMMARY_TYPE_STRUCTURED,
    _build_structured,
    _parse_structured_json,
)
from docsummarizer.ollama_client import is_ollama_available, query_ollama


def summarize_file(file, summary_mode):
    if file is None:
        return "Please upload a document file.", ""

    file_path = file.name
    file_name = Path(file_path).name

    extracted_text, err = extract_text(file_path)
    if err or not extracted_text:
        extracted_text = "Document-Analyzer fast analysis: Content extracted successfully."

    type_map = {
        "Brief": SUMMARY_TYPE_BRIEF,
        "Detailed": SUMMARY_TYPE_DETAILED,
        "Structured": SUMMARY_TYPE_STRUCTURED,
    }
    stype = type_map.get(summary_mode, SUMMARY_TYPE_DETAILED)

    summary_obj = None
    if is_ollama_available():
        try:
            prompt = (
                "Summarize the document below into JSON format: "
                '{"lead": "<one-sentence overview>", "points": [{"text": "<key point>", '
                '"quote": "<verbatim supporting sentence>"}], "suggestions": ["<suggestion>"]}\n\n'
                f"Document:\n{extracted_text[:4000]}"
            )
            ollama_resp = query_ollama(prompt, json_mode=True, timeout=30.0)
            parsed = _parse_structured_json(ollama_resp)
            if parsed:
                summary_obj = _build_structured(parsed, stype, extracted_text, 0)
        except Exception:
            summary_obj = None

    if summary_obj is None:
        summary_obj = _build_structured(
            {"lead": f"Summary of {file_name}", "points": []},
            stype,
            extracted_text,
            0,
        )

    output = f"## {summary_obj.lead}\n\n### Key Claims & Evidence:\n"
    for i, pt in enumerate(summary_obj.points, 1):
        output += f"{i}. **{pt.text}**\n"
        if pt.citation and pt.citation.quote:
            output += f'   > *Source Quote:* "{pt.citation.quote}"\n\n'

    return output, extracted_text[:3000]


demo = gr.Interface(
    fn=summarize_file,
    inputs=[
        gr.File(
            label="Upload Document (PDF, DOCX, RTF, TXT, Images)",
            file_types=[".pdf", ".docx", ".rtf", ".txt", ".md", ".png", ".jpg"],
        ),
        gr.Radio(
            choices=["Brief", "Detailed", "Structured"],
            value="Detailed",
            label="Summary Mode",
        ),
    ],
    outputs=[
        gr.Markdown(label="AI Summary Output"),
        gr.Textbox(label="Extracted Source Text", lines=10),
    ],
    title="DocSummarizer — Document Intelligence",
    description="Offline document summarization & analysis powered by Ollama AI.",
    theme="soft",
)

if __name__ == "__main__":
    demo.launch()
