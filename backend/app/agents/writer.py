from __future__ import annotations

from typing import Any

from ..llm import LLMClient
from .base import BaseAgent

WRITER_SYSTEM = """You are a research writer for a multi-agent research assistant. Produce a clear,
well-structured Markdown research report for the user's question. Structure: Executive Summary,
Key Findings, Deep Dive by Subtopic, Supporting Sources (numbered list with titles/URLs),
Suggested Next Steps. Cite sources inline as [1], [2] referencing the numbered source list.
Keep it factual and note uncertainty when sources don't support a claim. Do not fabricate
citations. Use the supplied sources and findings."""


class WriterAgent(BaseAgent):
    name = "writer"

    def __init__(self, emit, llm: LLMClient):
        super().__init__(emit)
        self._llm = llm

    async def run(self, task: Any, context: dict[str, Any]) -> str:
        findings = context.get("findings", [])
        sources = context.get("sources", [])
        topics = context.get("plan", [])
        await self.emit("running", "Drafting the final research report")
        fallback = _compose_fallback(task.query, topics, sources, findings)
        try:
            if self._llm.configured:
                prompt = _writer_prompt(task.query, topics, sources, findings)
                report = await self._llm.complete_text(WRITER_SYSTEM, prompt, default=fallback)
                report = report if report.strip() else fallback
            else:
                report = fallback
        except Exception:
            report = fallback
        await self.emit("done", f"Report written ({len(report)} chars)")
        return report


def _writer_prompt(query: str, topics: list[str], sources: list[Any], findings: list[str]) -> str:
    source_lines = "\n".join(f"  - {s.title} ({s.url or 'uploaded document'})" for s in sources) or "no sources"
    finding_lines = "\n".join(f"- {f}" for f in findings) or "no findings"
    topic_lines = "; ".join(topics) or "open research direction"
    return f"Q: {query}\n\nSubtopics: {topic_lines}\n\nSources:\n{source_lines}\n\nFindings:\n{finding_lines}"


def _compose_fallback(query: str, topics: list[str], sources: list[Any], findings: list[str]) -> str:
    src_items = "\n".join(
        f"{i}. {s.title} — {s.url or 'uploaded document'}" for i, s in enumerate(sources, 1)
    ) or "No external sources were fetched for this run."
    finding_items = "\n".join(f"- {f}" for f in findings) or "- No findings were produced yet."
    topic_items = "\n".join(f"- {t}" for t in topics) or "- Open research direction."

    return f"""# {query}

## Executive Summary
This report consolidates the multi-agent research pass on **{query}**. {len(sources)} source(s) were
gathered and {len(findings)} finding(s) synthesized by the research agents. The pipeline ran with
{len(topics)} planned subtopics.

## Key Findings
{finding_items}

## Deep Dive by Subtopic
{topic_items}

## Supporting Sources
{src_items}

## Suggested Next Steps
Consult the critic agent's gap review to prioritize follow-up research questions.
""".strip()