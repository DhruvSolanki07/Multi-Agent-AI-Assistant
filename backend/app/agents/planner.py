from __future__ import annotations

import re
from typing import Any

from ..llm import LLMClient
from .base import BaseAgent

PLANNER_SYSTEM = """You are an expert research planner. Break a user research request into 3-6
focused subtopics. Respond with STRICT JSON: {"topics": ["...", "..."]}. Each topic must be
a self-contained, searchable research question. Do NOT include markdown."""


class PlannerAgent(BaseAgent):
    name = "planner"

    def __init__(self, emit, llm: LLMClient):
        super().__init__(emit)
        self._llm = llm

    async def run(self, task: Any, context: dict[str, Any]) -> list[str]:
        await self.emit("running", "Analyzing the research request")
        fallback = _fallback_plan(task.query)
        try:
            from ..config import get_settings

            if self._llm.configured:
                data = await self._llm.complete_json(PLANNER_SYSTEM, task.query, fallback={"topics": fallback})
                topics = [t.strip() for t in data.get("topics", fallback) if t.strip()]
                topics = topics[:6] if topics else fallback
            else:
                topics = fallback
        except Exception:
            topics = fallback
        await self.emit("done", f"Research plan ready: {len(topics)} subtopics", {"topics": topics})
        return topics


def _fallback_plan(query: str) -> list[str]:
    q = re.sub(r"\s+", " ", query.strip())
    suffixes = [
        f"Overview and key concepts of: {q}",
        f"Recent developments, trends, and data on: {q}",
        f"Ities of challenges, risks, and open issues around: {q}",
        f"Best practices, applications, and future outlook for: {q}",
    ]
    return suffixes