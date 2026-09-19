from __future__ import annotations

from pathlib import Path
from typing import Any

from .models import ResearchTask


class TaskStore:
    """JSON-file-backed store for research tasks."""

    def __init__(self, root: Path):
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)
        self._tasks: dict[str, ResearchTask] = {}
        self._load_all()

    def _load_all(self) -> None:
        for f in self.root.glob("*.json"):
            try:
                task = ResearchTask.model_validate_json(f.read_text(encoding="utf-8"))
                self._tasks[task.id] = task
            except Exception:
                continue

    def _path(self, task_id: str) -> Path:
        return self.root / f"{task_id}.json"

    def get(self, task_id: str) -> ResearchTask | None:
        return self._tasks.get(task_id)

    def upsert(self, task: ResearchTask) -> Any:
        self._tasks[task.id] = task
        self._path(task.id).write_text(task.model_dump_json(indent=2), encoding="utf-8")
        return task

    def list(self) -> list[ResearchTask]:
        return sorted(self._tasks.values(), key=lambda t: t.updated_at, reverse=True)

    def delete(self, task_id: str) -> bool:
        if task_id in self._tasks:
            del self._tasks[task_id]
            self._path(task_id).unlink(missing_ok=True)
            return True
        return False