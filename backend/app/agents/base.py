from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Awaitable, Callable

from ..models import AgentEvent, ResearchTask

EmitCallback = Callable[[AgentEvent], Awaitable[None]]


class BaseAgent(ABC):
    """Base class for all research agents.

    Agents emit structured progress events through `emit` which is wired to the
    orchestrator's SSE stream so the frontend can render a live task wall.
    """

    name: str = "agent"

    def __init__(self, emit: EmitCallback):
        self._emit = emit

    async def emit(self, stage, message: str = "", detail: dict | None = None) -> None:
        from ..models import AgentStage

        await self._emit(AgentEvent(
            seq=0,
            agent=self.name,
            stage=AgentStage(stage),
            message=message,
            detail=detail,
        ))

    @abstractmethod
    async def run(self, task: Any, context: dict[str, Any]) -> Any:
        """Execute this agent's responsibility for the given research task."""
        raise NotImplementedError