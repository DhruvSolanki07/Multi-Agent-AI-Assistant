from __future__ import annotations

import asyncio
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, PlainTextResponse, StreamingResponse

from .config import get_settings
from .models import ResearchTask, TaskStatus
from .orchestrator import ResearchOrchestrator
from .storage import TaskStore

settings = get_settings()

store = TaskStore(settings.data_dir)
_upload_dir = Path(settings.upload_dir)
_upload_dir.mkdir(parents=True, exist_ok=True)


def _on_updated(task: ResearchTask) -> None:
    try:
        store.upsert(task)
    except Exception:
        pass


orchestrator = ResearchOrchestrator(on_updated=_on_updated)


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield
    await orchestrator.aclose()


app = FastAPI(title=settings.app_name, lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/health")
async def health() -> dict:
    return {
        "ok": True,
        "llm_configured": settings.llm_configured,
        "search_configured": settings.search_configured,
        "agents": ["planner", "searcher", "documenter", "summarizer", "writer", "critic"],
    }


@app.post("/api/research")
async def create_research(
    query: str = Form(...),
    documents: list[UploadFile] = File(default=[]),
):
    if not query.strip():
        raise HTTPException(status_code=422, detail="query must not be empty")

    task_id = uuid4().hex[:12]
    now = datetime.now(timezone.utc).isoformat()
    task = ResearchTask(
        id=task_id,
        query=query.strip(),
        status=TaskStatus.queued,
        created_at=now,
        updated_at=now,
    )

    saved_paths: list[Path] = []
    for upload in documents:
        if not upload.filename:
            continue
        if upload.size is not None and upload.size > settings.max_runs_bytes:
            raise HTTPException(status_code=413, detail=f"{upload.filename} exceeds the size limit")
        data = await upload.read()
        safe_name = Path(upload.filename).name.replace(" ", "_")
        path = _upload_dir / f"{task_id}_{safe_name}"
        path.write_bytes(data)
        saved_paths.append(path)

    _on_updated(task)

    async def runner() -> None:
        await orchestrator.run(task, documents=saved_paths)
        _on_updated(task)

    asyncio.create_task(runner())
    return {"id": task.id, "status": task.status}


@app.get("/api/tasks")
async def list_tasks() -> list[dict]:
    return [t.model_dump(mode="json") for t in store.list()]


@app.get("/api/tasks/{task_id}")
async def get_task(task_id: str) -> dict:
    return _get_or_404(task_id).model_dump(mode="json")


@app.delete("/api/tasks/{task_id}")
async def delete_task(task_id: str) -> JSONResponse:
    if not store.delete(task_id):
        raise HTTPException(status_code=404, detail="task not found")
    return JSONResponse({"deleted": task_id})


@app.get("/api/tasks/{task_id}/events")
async def task_events(task_id: str):
    _get_or_404(task_id)

    async def event_source():
        last_seq = 0
        try:
            while True:
                current = store.get(task_id)
                if current is None:
                    yield _sse({"type": "closed", "task_id": task_id})
                    return
                finished = current.status in {TaskStatus.done, TaskStatus.failed}
                for ev in current.agent_events:
                    if ev.seq > last_seq:
                        last_seq = ev.seq
                        yield _sse({"type": "event", "task_id": task_id, **ev.model_dump()})
                if finished:
                    yield _sse({"type": "done", "task_id": task_id, "status": current.status})
                    return
                await asyncio.sleep(0.25)
        except asyncio.CancelledError:
            pass

    return StreamingResponse(event_source(), media_type="text/event-stream")


@app.get("/api/tasks/{task_id}/report")
async def download_report(task_id: str) -> PlainTextResponse:
    task = _get_or_404(task_id)
    body = task.report_markdown or task.report or "# No report yet\n"
    return PlainTextResponse(body, media_type="text/markdown")


def _sse(payload: dict) -> str:
    import json

    return f"data: {json.dumps(payload)}\n\n"


def _get_or_404(task_id: str) -> ResearchTask:
    task = store.get(task_id)
    if task is None:
        raise HTTPException(status_code=404, detail="task not found")
    return task