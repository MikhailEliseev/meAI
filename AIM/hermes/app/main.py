"""Hermes FastAPI wrapper — HTTP API for Next.js chat proxy.

Per D-10: FastAPI wraps Hermes AIAgent programmatically (not subprocess).
Per D-11: Hermes is the sole LLM gateway — Next.js proxies all chat here.
Per D-29: GET /health returns status (Prometheus scrapes this).
Per D-30: Standard RED metrics (Rate, Errors, Duration) via prometheus-client.
"""

import logging
import sys
import time

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    stream=sys.stdout,
)
logger = logging.getLogger(__name__)

import os

from fastapi import FastAPI, Depends, HTTPException, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel

try:
    from meai.events.event_bus import EventBus
    _event_bus_available = True
except ImportError:
    EventBus = None
    _event_bus_available = False

from hermes.knowledge.vault import HermesKnowledgeVault

from .auth import verify_api_key
from .agent_wrapper import run_agent
from .telegram_gateway import router as telegram_router, start_polling, stop_polling
from .knowledge_router import router as knowledge_router

# ── Metrics ──────────────────────────────────────────────────────────
_metrics = {
    "requests_total": 0,
    "errors_total": 0,
    "latencies": [],  # ring buffer, last 100
    "request_start_time": {},  # request_id -> timestamp
}
MAX_LATENCY_SAMPLES = 100
_polling_started = False

# ── App ──────────────────────────────────────────────────────────────
# NOTE: app must be created BEFORE @app.on_event("startup") decorator

app = FastAPI(
    title="Hermes AIM Operator",
    version="0.1.0",
)


# ── Lifespan ──────────────────────────────────────────────────────────
@app.on_event("startup")
async def on_startup():
    """Register tools + subscribe to EventBus + start Telegram polling.

    EventBus subscriptions connect Hermes to CI execution events.
    For cross-process communication, CI Orchestrator also sends events
    via HTTP POST /api/knowledge/ingest.
    """
    from app.tools import register_all_tools
    register_all_tools()
    logger.info("Hermes FastAPI started — tools registered")

    # EventBus listener: subscribe to CI execution events (only if meai available)
    if _event_bus_available:
        try:
            database_url = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./data/hermes.db")
            event_bus = EventBus(database_url=database_url)
            await event_bus.initialize()

            vault = HermesKnowledgeVault()

            event_bus.subscribe("ci.execution.started", vault.ingest_execution)
            event_bus.subscribe("ci.agent.completed", vault.ingest_agent_result)
            event_bus.subscribe("ci.execution.completed", vault.ingest_execution)

            logger.info("[Hermes] Subscribed to EventBus: ci.execution.* → Knowledge Vault")
        except Exception as e:
            logger.warning(f"[Hermes] EventBus subscription skipped: {e}")
    else:
        logger.info("[Hermes] EventBus unavailable (meai not installed) — HTTP ingest only")


@app.on_event("shutdown")
async def on_shutdown():
    await stop_polling()
    logger.info("Hermes FastAPI shutting down")

app.include_router(telegram_router)
app.include_router(knowledge_router, prefix="/api/knowledge")


# ── Models ────────────────────────────────────────────────────────────
class ChatRequest(BaseModel):
    message: str
    session_id: str | None = None
    mode: str = "PRESALE"


class ChatResponse(BaseModel):
    reply: str
    session_id: str | None = None
    tool_calls: list = []


class HealthResponse(BaseModel):
    status: str
    hermes: str
    uptime_seconds: float
    requests_total: int
    errors_total: int
    knowledge_loop: dict = {}


# ── Health ────────────────────────────────────────────────────────────
_start_time = time.time()


@app.get("/health", response_model=HealthResponse)
async def health():
    """Health check endpoint (D-29). Prometheus scrapes this.

    Includes knowledge loop status from Hermes Knowledge Vault.
    Starts Telegram polling on first call.
    """
    global _polling_started
    if not _polling_started:
        start_polling()
        _polling_started = True
        logger.info("Telegram polling started (lazy init on first /health)")

    # Knowledge loop status
    try:
        from .knowledge_router import vault
        vault_status = await vault.get_status()
        knowledge_loop = {
            "executions_total": vault_status["executions_count"],
            "patterns_total": vault_status["patterns_count"],
            "learnings_total": vault_status["learnings_count"],
            "rules_total": vault_status["rules_count"],
            "last_ingest": vault_status.get("last_ingest"),
            "loop_health": vault_status["loop_health"],
        }
    except Exception:
        knowledge_loop = {"loop_health": "unavailable"}

    return HealthResponse(
        status="ok",
        hermes="healthy",
        uptime_seconds=round(time.time() - _start_time, 1),
        requests_total=_metrics["requests_total"],
        errors_total=_metrics["errors_total"],
        knowledge_loop=knowledge_loop,
    )


@app.get("/metrics")
async def metrics():
    """Prometheus metrics endpoint — returns plain text."""
    lines = [
        "# HELP aim_hermes_requests_total Total chat requests",
        "# TYPE aim_hermes_requests_total counter",
        f"aim_hermes_requests_total {_metrics['requests_total']}",
        "# HELP aim_hermes_errors_total Total error responses",
        "# TYPE aim_hermes_errors_total counter",
        f"aim_hermes_errors_total {_metrics['errors_total']}",
    ]
    latencies = _metrics["latencies"]
    if latencies:
        avg_lat = sum(latencies) / len(latencies)
        lines.append("# HELP aim_hermes_latency_avg Average request latency (seconds)")
        lines.append("# TYPE aim_hermes_latency_avg gauge")
        lines.append(f"aim_hermes_latency_avg {avg_lat:.3f}")
    return "\n".join(lines) + "\n"


# ── Chat ──────────────────────────────────────────────────────────────
@app.post("/api/chat", response_model=ChatResponse)
async def chat(
    body: ChatRequest,
    _token: str = Depends(verify_api_key),
):
    """Main chat endpoint — routes message through Hermes AIAgent.

    Per D-11: this replaces direct DeepSeek calls.
    Per D-26: Next.js determines mode and passes it.
    Per D-25: Bearer token verified via dependency.
    """
    mode = body.mode
    if mode == "ADMIN":
        logger.warning("ADMIN mode chat request received — audit this access")

    _metrics["requests_total"] += 1
    t0 = time.time()

    try:
        result = await run_agent(
            message=body.message,
            session_id=body.session_id,
            mode=mode,
        )
        elapsed = time.time() - t0
        _metrics["latencies"].append(elapsed)
        if len(_metrics["latencies"]) > MAX_LATENCY_SAMPLES:
            _metrics["latencies"].pop(0)

        reply = result.get("reply", "")
        if isinstance(reply, dict):
            reply = reply.get("response", reply.get("content", str(reply)))

        return ChatResponse(
            reply=str(reply),
            session_id=result.get("session_id"),
            tool_calls=result.get("tool_calls", []),
        )

    except Exception as e:
        _metrics["errors_total"] += 1
        logger.exception("Chat request failed")
        raise HTTPException(
            status_code=502,
            detail={"error": "Hermes agent error", "message": str(e)},
        )


# ── Error handlers ────────────────────────────────────────────────────
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": str(exc.detail)},
    )
