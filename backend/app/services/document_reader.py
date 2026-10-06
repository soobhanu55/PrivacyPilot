"""Extract plain text from an uploaded company document (TXT, Markdown, PDF, DOCX)."""
from __future__ import annotations

from pathlib import Path

SUPPORTED = {".txt", ".md", ".pdf", ".docx"}


def read_document(path: str | Path) -> str:
    path = Path(path)
    suffix = path.suffix.lower()
    if suffix not in SUPPORTED:
        raise ValueError(f"unsupported file type {suffix!r}; supported: {sorted(SUPPORTED)}")
    if suffix == ".pdf":
        from pypdf import PdfReader

        return "\n\n".join((page.extract_text() or "") for page in PdfReader(str(path)).pages)
    if suffix == ".docx":
        import docx

        return "\n\n".join(p.text for p in docx.Document(str(path)).paragraphs)
    return path.read_text(encoding="utf-8", errors="replace")
