from __future__ import annotations

from enum import Enum
from typing import Any, Literal

from pydantic import BaseModel, Field


class AgentType(str, Enum):
    """The different specialized research agents in the pipeline."""
    planner = "planner"
    searcher = "searcher"
    documenter = "documenter"
    summarizer = "summarizer"
    critic = "critic"
    writer = "writer"


class AgentStage(str, Enum):
    pending = "pending"
    running = "running"
    done = "done"
    failed = "failed"


class TaskStatus(str, Enum):
    queued = "queued"
    running = "running"
    done = "done"
    failed = "failed"


class SourceRef(BaseModel):
    title: str
    url: str | None = None
    snippet: str = ""
    source_type: Literal["web", "document", "local"] = "web"
    doc_id: str | None = None


class EvidenceItem(BaseModel):
    claim: str
    source: str
    url: str | None = None
    confidence: Literal["high", "medium", "low"] = "medium"


class AgentEvent(BaseModel):
    """A progress event emitted by an agent during a task run."""
    seq: int
    agent: AgentType
    stage: AgentStage
    message: str = ""
    detail: Any | None = None


class ResearchTask(BaseModel):
    id: str
    query: str = ""
    status: TaskStatus = TaskStatus.queued
    created_at: str = ""
    updated_at: str = ""
    agent_events: list[AgentEvent] = Field(default_factory=list)
    plan: list[str] = Field(default_factory=list)
    sources: list[SourceRef] = Field(default_factory=list)
    findings: list[str] = Field(default_factory=list)
    report: str = ""
    report_markdown: str = ""
    gaps: list[str] = Field(default_factory=list)
    error: str | None = None

    def record(self, agent: AgentType, stage: AgentStage, message: str = "", detail: dict | None = None) -> AgentEvent:
        event = AgentEvent(
            seq=len(self.agent_events) + 1,
            agent=agent,
            stage=stage,
            message=message,
            detail=detail,
        )
        self.agent_events.append(event)
        return event