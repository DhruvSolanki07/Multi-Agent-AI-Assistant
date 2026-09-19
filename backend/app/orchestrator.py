from __future__ import annotations

import asyncio
from datetime import datetime, timezone

from .agents.critic import CriticAgent
from .agents.documenter import DocumenterAgent
from .agents.planner import PlannerAgent
from .agents.searcher import SearchAgent, SearchProvider
from .agents.summarizer import SummarizerAgent
from .agents.writer import WriterAgent
from .config import get_settings
from .llm import LLMClient
from .models import AgentStage, AgentType, ResearchTask, TaskStatus


class ResearchOrchestrator:
    """Runs the multi-agent research pipeline and records progress events.

    Pipeline order: planner -> documenter + searcher (parallel) -> summarizer
    -> writer -> critic. A failure in any stage marks the task as failed while
    keeping whatever partial results were produced.
    """

    def __init__(self, on_updated=None) -> None:
        self.settings = get_settings()
        self._llm = LLMClient(self.settings)
        self._searcher_provider = SearchProvider(self.settings)
        self._on_updated = on_updated

    async def aclose(self) -> None:
        await self._llm.aclose()
        await self._searcher_provider.aclose()

    def _persist(self, task: ResearchTask) -> None:
        if self._on_updated:
            self._on_updated(task)

    def _mk_emit(self, task: ResearchTask):
        async def emit(event) -> None:
            event.seq = len(task.agent_events) + 1
            task.agent_events.append(event)
            self._persist(task)

        return emit

    async def run(self, task: ResearchTask, documents: list | None = None) -> None:
        task.status = TaskStatus.running
        context: dict = {
            "plan": [],
            "sources": [],
            "findings": [],
            "documents": documents or [],
            "document_texts": {},
        }

        try:
            planner = PlannerAgent(self._mk_emit(task), self._llm)
            plan = await planner.run(task, context)
            context["plan"] = plan
            task.plan = plan

            async def run_docs() -> list:
                agent = DocumenterAgent(self._mk_emit(task))
                return await agent.run(task, context)

            async def run_search() -> list:
                agent = SearchAgent(self._mk_emit(task), self._searcher_provider)
                return await agent.run(task, context)

            doc_sources, web_sources = await asyncio.gather(run_docs(), run_search())
            merged: list = []
            for src in [*doc_sources, *web_sources]:
                if src not in merged:
                    merged.append(src)
            task.sources = merged
            context["sources"] = merged

            summarizer = SummarizerAgent(self._mk_emit(task))
            findings = await summarizer.run(task, context)
            task.findings = findings
            context["findings"] = findings

            writer = WriterAgent(self._mk_emit(task), self._llm)
            report = await writer.run(task, context)
            task.report = report
            task.report_markdown = report

            critic = CriticAgent(self._mk_emit(task), self._llm)
            gaps = await critic.run(task, context)
            task.gaps = gaps

            task.status = TaskStatus.done
            task.updated_at = _now()
            task.record(AgentType.planner, AgentStage.done, "Research pipeline complete", {"status": "done"})
            self._persist(task)
        except Exception as exc:  # noqa: BLE001
            task.status = TaskStatus.failed
            task.error = str(exc)
            task.updated_at = _now()
            task.record(AgentType.writer, AgentStage.failed, "Pipeline aborted", {"error": str(exc)})
            self._persist(task)


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()
