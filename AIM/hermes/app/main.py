"""Hermes FastAPI wrapper — HTTP API for Next.js chat proxy.

Per D-10: FastAPI wraps Hermes AIAgent programmatically (not subprocess).
Per D-11: Hermes is the sole LLM gateway — Next.js proxies all chat here.
Per D-29: GET /health returns status (Prometheus scrapes this).
Per D-30: Standard RED metrics (Rate, Errors, Duration) via prometheus-client.
"""

import logging
import os
import time
from contextlib import asynccontextmanager

from fastapi import FastAPI, Depends, HTTPException, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from .auth import verify_api_key
from .agent_wrapper import run_agent
from .telegram_gateway import router as telegram_router

logger = logging.getLogger(__name__)

# ── Metrics ──────────────────────────────────────────────────────────
_metrics = {
    "requests_total": 0,
    "errors_total": 0,
    "latencies": [],  # ring buffer, last 100
    "request_start_time": {},  # request_id -> timestamp
}
MAX_LATENCY_SAMPLES = 100


# ── Lifespan ──────────────────────────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Register AIM tools at startup."""
    from app.tools import register_all_tools
    register_all_tools()
    logger.info("Hermes FastAPI started — tools registered")
    yield
    logger.info("Hermes FastAPI shutting down")


app = FastAPI(
    title="Hermes AIM Operator",
    version="0.1.0",
    lifespan=lifespan,
)

app.include_router(telegram_router)


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


# ── Health ────────────────────────────────────────────────────────────
_start_time = time.time()


@app.get("/health", response_model=HealthResponse)
async def health():
    """Health check endpoint (D-29). Prometheus scrapes this."""
    return HealthResponse(
        status="ok",
        hermes="healthy",
        uptime_seconds=round(time.time() - _start_time, 1),
        requests_total=_metrics["requests_total"],
        errors_total=_metrics["errors_total"],
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
    request: Request,
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
