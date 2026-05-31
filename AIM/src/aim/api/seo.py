"""
SEO Audit API Endpoint

POST /api/seo/audit — Start async SEO audit (background CI pipeline)
GET  /api/seo/audit/{task_id} — Poll audit status + results

Wires Hermes tool run_seo_audit → Competitive Intelligence pipeline.
"""
import logging
import os
import asyncio
import time
from dataclasses import dataclass, field
from typing import Optional

from fastapi import APIRouter, HTTPException

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/seo", tags=["seo"])

# ── Background task store ─────────────────────────────────────────
@dataclass
class AuditTask:
    task_id: str
    status: str = "pending"  # pending → running → done / error
    result: Optional[dict] = None
    error: Optional[str] = None
    started_at: float = 0.0
    finished_at: float = 0.0
    progress: str = ""

    def to_dict(self) -> dict:
        """Serialize AuditTask to dict for JSON persistence."""
        return {
            "task_id": self.task_id,
            "status": self.status,
            "result": self.result,
            "error": self.error,
            "started_at": self.started_at,
            "finished_at": self.finished_at,
            "progress": self.progress,
        }

    @staticmethod
    def from_dict(d: dict) -> "AuditTask":
        """Deserialize AuditTask from dict (JSON persistence)."""
        return AuditTask(
            task_id=d.get("task_id", ""),
            status=d.get("status", "pending"),
            result=d.get("result"),
            error=d.get("error"),
            started_at=d.get("started_at", 0.0),
            finished_at=d.get("finished_at", 0.0),
            progress=d.get("progress", ""),
        )

_tasks: dict[str, AuditTask] = {}

# Lazy-initialized orchestrator
_orchestrator = None
_init_lock = asyncio.Lock()


async def _get_orchestrator():
    """Lazy-init CIOrchestrator with EventBus (singleton)."""
    global _orchestrator
    if _orchestrator is not None:
        return _orchestrator

    async with _init_lock:
        if _orchestrator is not None:
            return _orchestrator

        from meai.events.event_bus import EventBus
        from aim.subagents.competitive_intel.orchestrator.ci_orchestrator import CIOrchestrator

        database_url = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./data/aim.db")
        event_bus = EventBus()
        await event_bus.initialize()

        _orchestrator = CIOrchestrator(
            agent_id="hermes-seo-api",
            event_bus=event_bus,
            database_url=database_url,
            vault_path="AIM/obsidian/ci-orchestrator",
        )
        logger.info("CIOrchestrator initialized for SEO API")
        return _orchestrator


async def _run_audit_background(task: AuditTask, payload: dict):
    """Execute CI pipeline in background, update task store on completion."""
    try:
        task.status = "running"
        task.started_at = time.time()

        orchestrator = await _get_orchestrator()
        task.progress = "Запускаю анализ конкурентов…"

        url = payload.get("url", "")
        if isinstance(url, dict):
            url = url.get("url", "")
        url = url.strip() if isinstance(url, str) else ""

        competitors = payload.get("competitors", [])
        niche = payload.get("niche", "medical")
        tier = payload.get("tier", "deep")
        all_urls = [url] + [c for c in competitors if c != url]

        result = await orchestrator.execute_ci_analysis(
            task_data={
                "task_id": task.task_id,
                "niche": niche,
                "geo": "ru",
                "tier": tier,
                "competitors": all_urls,
                "target_audience": payload.get("target_audience", ""),
                "price_segment": payload.get("price_segment", "mid"),
            }
        )

        task.result = result
        task.status = "done"
        task.finished_at = time.time()
        logger.info("SEO audit completed: %d phases, %d competitors (task %s)",
                     len(result.get("phases_executed", [])),
                     result.get("competitors_analyzed", 0),
                     task.task_id)

    except Exception as e:
        logger.exception("SEO audit failed (task %s)", task.task_id)
        task.error = str(e)
        task.status = "error"
        task.finished_at = time.time()


@router.post("/audit")
async def start_seo_audit(payload: dict):
    """Start async SEO audit via Competitive Intelligence pipeline.

    Request body:
        {
            "url": "https://clinic.ru",
            "competitors": ["https://competitor1.ru"],
            "niche": "стоматология",
            "tier": "deep"
        }

    Returns task_id immediately. Poll GET /api/seo/audit/{task_id} for results.
    """
    url = payload.get("url", "")
    if isinstance(url, dict):
        url = url.get("url", "")
    url = url.strip() if isinstance(url, str) else ""
    if not url:
        raise HTTPException(status_code=400, detail="url is required")

    task_id = f"seo-audit-{int(time.time())}"
    task = AuditTask(task_id=task_id)
    _tasks[task_id] = task

    # Fire and forget — background task updates _tasks dict
    asyncio.create_task(_run_audit_background(task, payload))

    logger.info("SEO audit started: task=%s url=%s", task_id, url)

    return {
        "task_id": task_id,
        "status": "pending",
        "status_url": f"/api/seo/audit/{task_id}",
    }


@router.get("/audit/{task_id}")
async def get_audit_status(task_id: str):
    """Poll audit task status. Returns result when done."""
    task = _tasks.get(task_id)
    if task is None:
        raise HTTPException(status_code=404, detail=f"Task {task_id} not found")

    response: dict = {
        "task_id": task.task_id,
        "status": task.status,
        "progress": task.progress,
    }

    if task.status == "done" and task.result:
        response["result"] = task.result
    elif task.status == "error":
        response["error"] = task.error

    return response
