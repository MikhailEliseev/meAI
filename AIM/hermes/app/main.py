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

import asyncio
import json
import re

from fastapi import FastAPI, Depends, HTTPException, Request
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import BaseModel

try:
    from meai.events.event_bus import EventBus
    _event_bus_available = True
except ImportError:
    EventBus = None
    _event_bus_available = False

from knowledge.vault import HermesKnowledgeVault

from .auth import verify_api_key
from .agent_wrapper import run_agent
from .telegram_gateway import router as telegram_router, start_polling, stop_polling
from .knowledge_router import router as knowledge_router

# ── Tool progress queue (thread-safe, for real-time SSE streaming) ──
# Tool handlers push progress events here. The SSE generator reads them
# concurrently while the agent runs in a background task.
_tool_progress_queue: asyncio.Queue | None = None
_main_event_loop: asyncio.AbstractEventLoop | None = None


def set_tool_progress_queue(q: asyncio.Queue) -> None:
    """Set the active progress queue for the current SSE request."""
    global _tool_progress_queue
    _tool_progress_queue = q


def clear_tool_progress_queue() -> None:
    """Clear the active progress queue after the SSE request completes."""
    global _tool_progress_queue
    _tool_progress_queue = None


def push_tool_progress(stage: str, message: str, competitor: str = "") -> None:
    """Push a progress event from any thread (thread-safe).

    Tool handlers call this during long-running operations.
    Uses call_soon_threadsafe to safely cross from tool thread to event loop.
    Falls back to logging if no active queue or loop.
    """
    q = _tool_progress_queue
    if q is None:
        logger.info("[tool-progress] %s: %s", stage, message)
        return
    event = {"type": "tool-progress", "stage": stage, "message": message, "competitor": competitor}
    loop = _main_event_loop
    if loop is None:
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            logger.info("[tool-progress] %s: %s (no event loop)", stage, message)
            return
    loop.call_soon_threadsafe(q.put_nowait, event)


# ── Metrics ──────────────────────────────────────────────────────────
_metrics = {
    "requests_total": 0,
    "errors_total": 0,
    "latencies": [],  # ring buffer, last 100
    "request_start_time": {},  # request_id -> timestamp
    # Chat metrics
    "chat_sessions_active": 0,
    "chat_messages_total": 0,
    "chat_leads_total": 0,
    "chat_token_cost_total": 0.0,
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
    from app.tools import register_all_tools, register_debug_tools
    register_all_tools()
    register_debug_tools()
    logger.info("Hermes FastAPI started — tools registered")

    vault = HermesKnowledgeVault()

    # Teacher → Hermes knowledge sync (non-blocking, best-effort)
    try:
        from knowledge.teacher_sync import TeacherSync
        sync = TeacherSync(vault, teacher_agent=None)
        results = await sync.sync_all_domains()
        total = sum(results.values())
        logger.info(f"[Hermes] TeacherSync: {total} learnings synced across {len(results)} domains")
    except Exception as e:
        logger.info(f"[Hermes] TeacherSync skipped (no teacher agent available): {e}")

    # EventBus listener: subscribe to CI execution events (only if meai available)
    if _event_bus_available:
        try:
            database_url = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./data/hermes.db")
            event_bus = EventBus(database_url=database_url)
            await event_bus.initialize()

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
        webhook_url = os.getenv("TELEGRAM_WEBHOOK_URL", "")
        if webhook_url:
            logger.info("Telegram webhook configured (%s), skipping getUpdates polling", webhook_url)
        else:
            start_polling()
            logger.info("Telegram polling started (lazy init on first /health)")
        _polling_started = True

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
        "# HELP aim_chat_sessions_active Active SSE chat sessions",
        "# TYPE aim_chat_sessions_active gauge",
        f"aim_chat_sessions_active {_metrics['chat_sessions_active']}",
        "# HELP aim_chat_messages_total Total chat messages",
        "# TYPE aim_chat_messages_total counter",
        f"aim_chat_messages_total {_metrics['chat_messages_total']}",
        "# HELP aim_chat_leads_total Total leads collected via chat",
        "# TYPE aim_chat_leads_total counter",
        f"aim_chat_leads_total {_metrics['chat_leads_total']}",
        "# HELP aim_chat_token_cost_total Total token cost in USD",
        "# TYPE aim_chat_token_cost_total counter",
        f"aim_chat_token_cost_total {_metrics['chat_token_cost_total']:.4f}",
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


# ── Chat (SSE streaming) ──────────────────────────────────────────────
@app.post("/api/chat/stream")
async def chat_stream(
    body: ChatRequest,
    _token: str = Depends(verify_api_key),
):
    """SSE streaming chat endpoint for the frontend full-page chat.

    Runs the AI agent in a background task. While the agent works, tool handlers
    push progress events via push_tool_progress(), which are streamed as
    "tool-progress" SSE events in real-time.

    Emits events:
      - tool-progress: real-time progress during tool execution (stage, message, competitor)
      - step-start / step-end: tool call lifecycle
      - text-delta: word-by-word reply
      - finish: session_id + completion signal
    """
    mode = body.mode
    if mode == "ADMIN":
        logger.warning("ADMIN mode SSE chat request received — audit this access")

    _metrics["requests_total"] += 1
    _metrics["chat_messages_total"] += 1
    _metrics["chat_sessions_active"] += 1
    t0 = time.time()

    async def generate():
        global _main_event_loop
        _main_event_loop = asyncio.get_running_loop()

        # Create a progress queue for this request
        queue: asyncio.Queue = asyncio.Queue()
        set_tool_progress_queue(queue)

        agent_result: dict = {}
        tool_names_seen: list[str] = []  # track unique tool stages from progress events

        try:
            # Start agent in background task
            async def run_agent_task():
                nonlocal agent_result
                agent_result = await run_agent(
                    message=body.message,
                    session_id=body.session_id,
                    mode=mode,
                )

            agent_task = asyncio.create_task(run_agent_task())

            # Hard deadline for the entire agent run (5 min).
            # hermes-agent hardcodes stream=True; OmniRoute's DeepSeek
            # sometimes never sends the first token → hangs without timeout.
            _SSE_DEADLINE = time.time() + 300

            # Phase A — Yield progress events while agent runs.
            # Also collect unique tool stage names so we can emit
            # step-start / step-end lifecycle markers in Phase C.
            while not agent_task.done():
                if time.time() > _SSE_DEADLINE:
                    logger.error("SSE agent deadline exceeded — cancelling task")
                    agent_task.cancel()
                    yield f"data: {json.dumps({'type': 'error', 'message': 'Превышено время ожидания. Попробуй ещё раз.'}, ensure_ascii=False)}\n\n"
                    break
                try:
                    event = await asyncio.wait_for(queue.get(), timeout=0.1)
                    yield f"data: {json.dumps(event, ensure_ascii=False)}\n\n"
                    # Track tool names from progress events
                    if event.get("type") == "tool-progress":
                        stage = event.get("stage", "")
                        if stage and stage not in tool_names_seen:
                            tool_names_seen.append(stage)
                except asyncio.TimeoutError:
                    continue

            # If deadline killed the task, skip Phase B/C — bail out
            if agent_task.cancelled():
                clear_tool_progress_queue()
                _metrics["chat_sessions_active"] = max(0, _metrics["chat_sessions_active"] - 1)
                return

            # Phase B — Drain remaining queue events
            while not queue.empty():
                try:
                    event = queue.get_nowait()
                    yield f"data: {json.dumps(event, ensure_ascii=False)}\n\n"
                    if event.get("type") == "tool-progress":
                        stage = event.get("stage", "")
                        if stage and stage not in tool_names_seen:
                            tool_names_seen.append(stage)
                except asyncio.QueueEmpty:
                    break

            reply = agent_result.get("reply", "")
            if isinstance(reply, dict):
                reply = reply.get("response", reply.get("content", str(reply)))
            reply = str(reply)

            # Phase C — Emit tool lifecycle events (from observed progress stages).
            # Falls back to agent_result["tool_calls"] if no progress events were seen.
            step_names = tool_names_seen or [
                tc.get("name", tc.get("function", {}).get("name", "unknown"))
                for tc in agent_result.get("tool_calls", [])
            ]
            for tc_name in step_names:
                yield f"data: {json.dumps({'type': 'step-start', 'step': tc_name}, ensure_ascii=False)}\n\n"
                await asyncio.sleep(0.15)
                yield f"data: {json.dumps({'type': 'step-end', 'step': tc_name}, ensure_ascii=False)}\n\n"

            # Stream reply token-by-token, preserving paragraph/line breaks
            tokens = re.split(r'( +|\t+|\n+)', reply)
            for token in tokens:
                if not token:
                    continue
                if token.startswith('\n'):
                    yield f"data: {json.dumps({'type': 'text-delta', 'textDelta': token}, ensure_ascii=False)}\n\n"
                else:
                    yield f"data: {json.dumps({'type': 'text-delta', 'textDelta': token}, ensure_ascii=False)}\n\n"
                await asyncio.sleep(0.02)

            # Finish signal
            yield f"data: {json.dumps({'type': 'finish', 'session_id': agent_result.get('session_id')}, ensure_ascii=False)}\n\n"

        except Exception as e:
            _metrics["errors_total"] += 1
            logger.exception("SSE chat stream failed")
            yield f"data: {json.dumps({'type': 'error', 'message': str(e)}, ensure_ascii=False)}\n\n"

        finally:
            clear_tool_progress_queue()
            _metrics["chat_sessions_active"] = max(0, _metrics["chat_sessions_active"] - 1)

    elapsed = time.time() - t0
    _metrics["latencies"].append(elapsed)
    if len(_metrics["latencies"]) > MAX_LATENCY_SAMPLES:
        _metrics["latencies"].pop(0)

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


# ── Error handlers ────────────────────────────────────────────────────
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": str(exc.detail)},
    )
