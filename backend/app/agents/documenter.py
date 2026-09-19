from __future__ import annotations

import io
from pathlib import Path
from typing import Any

from ..models import SourceRef
from .base import BaseAgent


class DocumentExtractionError(RuntimeError):
    pass


class DocumenterAgent(BaseAgent):
    """Extracts text from uploaded source documents and adds them as local sources."""

    name = "documenter"

    async def run(self, task: Any, context: dict[str, Any]) -> list[SourceRef]:
        files: list[Path] = context.get("documents", [])
        if not files:
            await self.emit("done", "No documents provided, skipping document ingestion", {"added": 0})
            return []
        await self.emit("running", f"Reading {len(files)} uploaded document(s)")
        added: list[SourceRef] = []
        for path in files:
            try:
                text = await self._extract(path)
            except Exception as exc:  # noqa: BLE001
                await self.emit("done", f"Could not parse {path.name}: {exc}")
                continue
            name = path.name
            source = SourceRef(
                title=f"Uploaded document: {name}",
                url=None,
                snippet=text[:500],
                source_type="document",
                doc_id=name,
            )
            added.append(source)
            context.setdefault("document_texts", {})[name] = text
            await self.emit("done", f"Extracted text from {name} ({len(text)} chars)")
        return added

    @staticmethod
    async def _extract(path: Path) -> str:
        suffix = path.suffix.lower()
        raw = path.read_bytes()
        if suffix == ".pdf":
            return _pdf_text(raw)
        if suffix in {".txt", ".md", ".csv", ".json"}:
            for enc in ("utf-8", "utf-16", "latin-1"):
                try:
                    return raw.decode(enc)
                except UnicodeDecodeError:
                    continue
        if suffix in {".docx", ".doc"}:
            return _docx_text(raw)
        raise DocumentExtractionError(f"Unsupported file type {suffix or '(none)'}")


def _pdf_text(raw: bytes) -> str:
    try:
        import pypdf  # optional extra
    except ImportError:
        raise DocumentExtractionError("pypdf not installed; cannot read PDFs")
    reader = pypdf.PdfReader(io.BytesIO(raw))
    return "\n".join(page.extract_text() or "" for page in reader.pages)


def _docx_text(raw: bytes) -> str:
    try:
        from docx import Document  # optional extra
    except ImportError:
        raise DocumentExtractionError("python-docx not installed; cannot read .docx")
    doc = Document(io.BytesIO(raw))
    return "\n".join(p.text for p in doc.paragraphs)