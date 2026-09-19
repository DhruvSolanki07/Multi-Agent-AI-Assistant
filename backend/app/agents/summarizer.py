from __future__ import annotations

import re
from typing import Any

from ..models import SourceRef
from .base import BaseAgent
from .searcher import SearchResult


class SummarizerAgent(BaseAgent):
    name = "summarizer"

    async def run(self, task: Any, context: dict[str, Any]) -> list[str]:
        sources: list[SourceRef] = context.get("sources", [])
        await self.emit("running", f"Summarizing {len(sources)} gathered sources")
        findings: list[str] = []
        for i, src in enumerate(sources):
            derived = _summarize_source(src)
            findings.append(derived)
            await self.emit("done", f"Summarized source {i + 1}/{len(sources)}")
        await self.emit("done", f"Produced {len(findings)} knowledge points", {"count": len(findings)})
        return findings


def _summarize_source(src: SourceRef) -> str:
    title = src.title or "Untitled"
    snippet = re.sub(r"\s+", " ", src.snippet or "").strip()
    origin = f"[{src.source_type}] {title}" + (f" ({src.url})" if src.url else "")
    try:
        words = snippet.split()
        core = " ".join(words[:28]) if words else "Source provides context on the topic."
        return f"{origin}: {core}"
    except Exception:  # noqa: BLE001
        return f"{origin}: available source noted for the report."