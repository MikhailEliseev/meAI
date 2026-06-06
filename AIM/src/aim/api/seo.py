"""
SEO Audit API Endpoint

POST /api/seo/audit — Start async SEO audit (background CI pipeline)
GET  /api/seo/audit/{task_id} — Poll audit status + results

Wires Hermes tool run_seo_audit → Competitive Intelligence pipeline.
"""
import json
import logging
import os
import asyncio
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/seo", tags=["seo"])

# ── Background task store ─────────────────────────────────────────

TASKS_FILE = Path(os.getenv("AIM_DATA_DIR", "AIM/data")) / "seo_audit_tasks.json"
TASK_TTL_SECONDS = 86400  # 24 hours — auto-cleanup completed/errored tasks


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


def _load_tasks() -> None:
    """Restore tasks from JSON file on startup."""
    if not TASKS_FILE.exists():
        return
    try:
        data = json.loads(TASKS_FILE.read_text())
        now = time.time()
        for td in data:
            # Skip expired tasks
            finished = td.get("finished_at", 0)
            if finished and td.get("status") in ("done", "error") and (now - finished) > TASK_TTL_SECONDS:
                continue
            task = AuditTask.from_dict(td)
            _tasks[task.task_id] = task
        logger.info("Loaded %d SEO audit tasks from %s", len(_tasks), TASKS_FILE)
    except Exception:
        logger.exception("Failed to load SEO audit tasks, starting fresh")


def _save_tasks() -> None:
    """Persist current tasks to JSON file."""
    try:
        TASKS_FILE.parent.mkdir(parents=True, exist_ok=True)
        data = [t.to_dict() for t in _tasks.values()]
        TASKS_FILE.write_text(json.dumps(data, ensure_ascii=False, indent=2))
    except Exception:
        logger.exception("Failed to persist SEO audit tasks")


def _cleanup_expired() -> None:
    """Remove expired completed/errored tasks from memory and disk."""
    now = time.time()
    expired = [
        tid for tid, t in _tasks.items()
        if t.status in ("done", "error") and t.finished_at and (now - t.finished_at) > TASK_TTL_SECONDS
    ]
    for tid in expired:
        del _tasks[tid]
    if expired:
        _save_tasks()
        logger.info("Cleaned up %d expired SEO audit tasks", len(expired))


# Load on module import
_load_tasks()

# Lazy-initialized orchestrator
_orchestrator = None
_init_lock = asyncio.Lock()


async def _get_orchestrator():
    """Lazy-init CIOrchestrator with shared EventBus (singleton)."""
    global _orchestrator
    if _orchestrator is not None:
        return _orchestrator

    async with _init_lock:
        if _orchestrator is not None:
            return _orchestrator

        from src.aim.orchestration.shared_event_bus import get_shared_event_bus
        from src.aim.subagents.competitive_intel.orchestrator.ci_orchestrator import CIOrchestrator

        database_url = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./data/aim.db")
        event_bus = await get_shared_event_bus()

        _orchestrator = CIOrchestrator(
            agent_id="hermes-seo-api",
            event_bus=event_bus,
            database_url=database_url,
            vault_path="AIM/obsidian/ci-orchestrator",
        )
        logger.info("CIOrchestrator initialized for SEO API (shared EventBus)")
        return _orchestrator


async def _run_audit_background(task: AuditTask, payload: dict):
    """Execute CI pipeline in background, update task store on completion."""
    try:
        task.status = "running"
        task.started_at = time.time()
        _save_tasks()

        orchestrator = await _get_orchestrator()
        task.progress = "Запускаю анализ конкурентов…"
        _save_tasks()

        url = payload.get("url", "")
        if isinstance(url, dict):
            url = url.get("url", "")
        url = url.strip() if isinstance(url, str) else ""

        competitors = payload.get("competitors", [])
        niche = payload.get("niche", "medical")
        tier = payload.get("tier", "deep")

        # Extract city and specialization from client website
        from src.aim.services.service_extractor import extract_client_profile
        task.progress = "Извлекаю город и специализацию с сайта…"
        profile = await extract_client_profile(url)
        geo = profile.get("city") or "ru"
        if niche == "medical":
            niche = profile.get("specialization") or niche
        logger.info("SEO audit: url=%s city=%s niche=%s", url, geo, niche)

        all_urls = [url] + [c for c in competitors if c != url]

        # Progress labels for each phase
        _PHASE_LABELS = {
            1: "Ищу конкурентов в нише…",
            2: "Анализирую сайты конкурентов…",
            3: "Оцениваю техническое SEO…",
            4: "Анализирую репутацию…",
            5: "Собираю данные: цены, контент, технологии, вакансии…",
            6: "Проверяю данные (fact-check)…",
            7: "Формирую стратегию…",
            8: "Анализирую рыночные возможности…",
            9: "Приоритизирую рекомендации…",
        }

        async def update_progress(phase: int, status: str, message: str):
            label = _PHASE_LABELS.get(phase, message)
            task.progress = f"[Фаза {phase}/9] {label}"
            _save_tasks()

        result = await orchestrator.execute_ci_analysis(
            task_data={
                "task_id": task.task_id,
                "niche": niche,
                "geo": geo,
                "tier": tier,
                "competitors": all_urls,
                "target_audience": payload.get("target_audience", ""),
                "price_segment": payload.get("price_segment", "mid"),
            },
            progress_callback=update_progress,
        )

        task.result = result
        task.result["niche"] = niche
        task.result["geo"] = geo
        task.status = "done"
        task.finished_at = time.time()
        _save_tasks()
        logger.info("SEO audit completed: %d phases, %d competitors (task %s)",
                     len(result.get("phases_executed", [])),
                     result.get("competitors_analyzed", 0),
                     task.task_id)

    except Exception as e:
        logger.exception("SEO audit failed (task %s)", task.task_id)
        task.error = str(e)
        task.status = "error"
        task.finished_at = time.time()
        _save_tasks()


@router.post("/audit")
async def start_seo_audit(payload: dict):
    """Start SEO/CI audit via Competitive Intelligence pipeline.

    Request body:
        {
            "url": "https://clinic.ru",
            "competitors": ["https://competitor1.ru"],
            "niche": "стоматология",
            "tier": "deep"  // "quick" | "deep" | "full"
        }

    tier="quick": Returns AnalyzeCompetitorsResponse-format synchronously.
    tier="deep"/"full": Returns task_id immediately. Poll GET /api/seo/audit/{task_id}.
    """
    tier = payload.get("tier", "deep").lower()

    url = payload.get("url", "")
    if isinstance(url, dict):
        url = url.get("url", "")
    url = url.strip() if isinstance(url, str) else ""
    if not url:
        raise HTTPException(status_code=400, detail="url is required")

    # ── Quick tier: synchronous response ──
    if tier == "quick":
        import time as _time
        start = _time.monotonic()

        competitors = payload.get("competitors", [])
        specialization = payload.get("specialization", payload.get("niche", "medical"))
        city = payload.get("city", payload.get("geo", ""))

        import uuid
        orchestrator = await _get_orchestrator()
        result = await orchestrator.execute_ci_analysis({
            "task_id": f"seo-quick-{uuid.uuid4().hex[:8]}",
            "url": url,
            "competitors": [url] + [c for c in competitors if c != url],
            "niche": specialization,
            "geo": city,
            "tier": "quick",
        })

        return {
            "success": True,
            "chat_summary": result.get("chat_summary", ""),
            "narrative": result.get("narrative", {}),
            "feature_matrix": result.get("feature_matrix", {}),
            "pricing_comparison": result.get("pricing_comparison", {}),
            "positioning_map": result.get("positioning_map", {}),
            "competitive_highlights": result.get("competitive_highlights", []),
            "steal_worthy_tactics": result.get("steal_worthy_tactics", []),
            "top_recommendation": result.get("top_recommendation", ""),
            "wow": result.get("wow"),
            "duration_seconds": _time.monotonic() - start,
            "error": result.get("error"),
        }

    # ── Deep/full tier: async fire-and-forget ──
    task_id = f"seo-audit-{int(time.time())}"
    task = AuditTask(task_id=task_id)
    _tasks[task_id] = task
    _save_tasks()
    _cleanup_expired()

    # Fire and forget — background task updates _tasks dict
    asyncio.create_task(_run_audit_background(task, payload))

    logger.info("SEO audit started: task=%s url=%s tier=%s", task_id, url, tier)

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


@router.post("/audit/stream")
async def start_seo_audit_stream(payload: dict):
    """SSE streaming for quick-tier CI analysis.

    Emits progress events during data collection.
    Final event: {"type": "result", "data": {...}}.

    Only supports tier="quick". Deep tier uses poll-based /audit/{task_id}.
    """
    tier = payload.get("tier", "quick").lower()
    if tier != "quick":
        raise HTTPException(
            status_code=400,
            detail="Streaming only supported for tier=quick. Use POST /api/seo/audit for deep tier.",
        )

    url = payload.get("url", "")
    if isinstance(url, dict):
        url = url.get("url", "")
    url = url.strip() if isinstance(url, str) else ""
    if not url:
        raise HTTPException(status_code=400, detail="url is required")

    competitors = payload.get("competitors", [])

    async def generate():
        queue: asyncio.Queue = asyncio.Queue()

        async def run_analysis():
            try:
                orchestrator = await _get_orchestrator()

                async def sse_progress(phase: int, status: str, message: str):
                    await queue.put({"type": "progress", "phase": phase, "status": status, "message": message})

                result = await orchestrator.execute_ci_analysis({
                    "url": url,
                    "competitors": [url] + [c for c in competitors if c != url],
                    "niche": payload.get("niche", payload.get("specialization", "medical")),
                    "geo": payload.get("geo", payload.get("city", "")),
                    "tier": "quick",
                }, progress_callback=sse_progress)
                await queue.put({"type": "result", "data": result})
            except Exception as e:
                logger.exception("Streaming quick analysis failed")
                await queue.put({"type": "error", "message": str(e)})

        task = asyncio.create_task(run_analysis())

        while True:
            event = await queue.get()
            yield f"data: {json.dumps(event, ensure_ascii=False)}\n\n"
            if event["type"] in ("result", "error"):
                break

        await task

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
