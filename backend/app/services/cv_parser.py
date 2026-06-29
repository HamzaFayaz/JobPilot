"""Extract plain text from .docx CV files."""

from pathlib import Path

from docx import Document


def extract_text_from_docx(path: Path) -> str:
    doc = Document(str(path))
    paragraphs = [p.text.strip() for p in doc.paragraphs if p.text.strip()]
    return "\n".join(paragraphs)
