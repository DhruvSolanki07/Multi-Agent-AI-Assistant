from __future__ import annotations

import re
from typing import Any

from ..llm import LLMClient
from .base import BaseAgent
from .planner import PlannerAgent

CRITIC_SYSTEM = """You are a rigorous research critic. Review the draft report and the user's question.
Identify concrete gaps: missing subtopics, unsupported claims, weak areas, or follow-up questions
worth answering. Respond with STRICT JSON: {"gaps": ["...", ...]}, max 5 items."""


class CriticAgent(BaseAgent):
    name = "critic"

    def __init__(self, emit, llm: LLMClient):
        super().__init__(emit)
        self._llm = llm

    async def run(self, task: Any, context: dict[str, Any]) -> list[str]:
        draft = context.get("draft", task.report or "")
        await self.emit("running", "Reviewing draft for gaps and weak spots")
        if not draft:
            await self.emit("done", "No draft to critique")
            return []
        fallback = _fallback_gaps(task.query, draft)
        try:
            if self._llm.configured:
                data = await self._llm.complete_json(CRITIC_SYSTEM, draft[:6000], fallback={"gaps": fallback})
                gaps = [g.strip() for g in data.get("gaps", []) if g.strip()]
                fallback = gaps or fallback
        except Exception:
            pass
        await self.emit("done", f"Identified {len(fallback)} gaps / follow-ups", {"gaps": fallback})
        return fallback


def _fallback_gaps(query: str, draft: str) -> list[str]:
    gaps = [
        "Coverage is still thin around recent quantitative evidence; verify with primary sources.",
        "Please confirm the currency of cited sources before relying on figures.",
        f"Consider explicitly addressing alternative viewpoints on “{query}”.",
        "Add concrete examples or short case studies to ground the abstract points.",
    ]
    if "future" not in draft.lower():
        gaps.append("Include a dedicated section on future outlook and open questions.")
    return gaps[:4]