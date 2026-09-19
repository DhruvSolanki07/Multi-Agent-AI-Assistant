import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from backend.app.models import ResearchTask, TaskStatus
from backend.app.orchestrator import ResearchOrchestrator


async def main() -> None:
    orch = ResearchOrchestrator()
    task = ResearchTask(id="smoke1", query="What is the state of ocean plastic pollution in 2025?")
    try:
        await orch.run(task)
        print("status:", task.status)
        print("error:", task.error)
        print("last events:", [(e.agent, e.stage, e.message) for e in task.agent_events][-4:])
        print("plan:", task.plan)
        print("sources:", len(task.sources))
        print("findings:", len(task.findings))
        print("gaps:", task.gaps)
        print("report head:", (task.report or "")[:200])
        print("events:", [(e.agent, e.stage) for e in task.agent_events][:6])
        assert task.status == TaskStatus.done, "pipeline did not finish"
        print("SMOKE OK")
    finally:
        await orch.aclose()


if __name__ == "__main__":
    asyncio.run(main())