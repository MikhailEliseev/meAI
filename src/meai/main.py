"""FastAPI application entry point."""

from datetime import datetime, timezone
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from meai.monitoring import HealthChecker

app = FastAPI(
    title="meAI Assistant",
    description="Personal AI assistant for building AIM agency",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize components
health_checker = HealthChecker()
start_time = datetime.now(timezone.utc)


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "status": "ok",
        "name": "meAI Assistant",
        "version": "0.1.0",
    }


@app.get("/health")
async def health():
    """Health check endpoint."""
    health_status = await health_checker.check_health()
    return health_status


@app.get("/metrics")
async def metrics():
    """Metrics endpoint."""
    return {
        "metrics": [],
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@app.get("/status")
async def status():
    """Status endpoint."""
    uptime = (datetime.now(timezone.utc) - start_time).total_seconds()
    return {
        "uptime": uptime,
        "components": {
            "api": "healthy",
            "database": "healthy",
        },
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }

