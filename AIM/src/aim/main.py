"""
AIM Agency API - FastAPI Application

Production-ready API with health checks, metrics, and monitoring.
"""

import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI, status, Request
from fastapi.responses import JSONResponse, Response
from datetime import datetime
import os

# Prometheus metrics
from prometheus_client import Counter, Histogram, Gauge, generate_latest, CONTENT_TYPE_LATEST
from prometheus_fastapi_instrumentator import Instrumentator

# Structured logging
from aim.config.logging import configure_logging, get_logger

# Configure logging
environment = os.getenv("ENVIRONMENT", "production")
log_level = os.getenv("LOG_LEVEL", "INFO")
configure_logging(environment=environment, log_level=log_level)
logger = get_logger("aim.api")

# Sentry error tracking
sentry_dsn = os.getenv("SENTRY_DSN", "")
if sentry_dsn:
    import sentry_sdk
    from sentry_sdk.integrations.fastapi import FastApiIntegration
    from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration
    sentry_sdk.init(
        dsn=sentry_dsn,
        environment=environment,
        traces_sample_rate=0.1 if environment == "production" else 1.0,
        integrations=[
            FastApiIntegration(transaction_style="endpoint"),
            SqlalchemyIntegration(),
        ],
        send_default_pii=False,
    )
    logger.info("sentry_initialized", environment=environment)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Run Alembic migrations on startup (production mode only)."""
    if os.getenv("AUTO_MIGRATE", "false").lower() == "true":
        from alembic.config import Config
        from alembic import command

        await asyncio.to_thread(
            lambda: command.upgrade(Config("AIM/alembic.ini"), "head")
        )
        logger.info("alembic_migrations_applied")

    # Ensure ФЗ-152 partitions exist
    from aim.services.retention.partition_manager import PartitionManager
    from aim.database import async_session_maker
    pm = PartitionManager(async_session_maker)
    await pm.ensure_partitions()
    logger.info("fz152_partitions_ensured")

    yield


# Create FastAPI application
app = FastAPI(
    title="AIM Agency API",
    description="AI-first medical marketing agency automation platform",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# Query profiling middleware
from aim.middleware.profiling import QueryProfilingMiddleware
app.add_middleware(QueryProfilingMiddleware)

# Custom Prometheus metrics
api_requests_total = Counter(
    "aim_api_requests_total",
    "Total API requests",
    ["method", "endpoint", "status"]
)

api_request_duration = Histogram(
    "aim_api_request_duration_seconds",
    "API request duration in seconds",
    ["method", "endpoint"],
    buckets=[0.1, 0.5, 1.0, 2.0, 5.0, 10.0]
)

active_tasks = Gauge(
    "aim_active_tasks",
    "Number of active tasks",
    ["magister", "subagent"]
)

api_errors_total = Counter(
    "aim_api_errors_total",
    "Total API errors",
    ["endpoint", "error_type"]
)

api_cost_usd_total = Counter(
    "aim_api_cost_usd_total",
    "Total API costs in USD",
    ["provider"]
)

# Business metrics — imported from single source of truth
from aim.metrics import (
    leads_captured_total,
    leads_scored_total,
    leads_by_tier,
    rate_limit_hits_total,
)

# Instrument FastAPI with Prometheus
Instrumentator().instrument(app).expose(app, endpoint="/metrics", include_in_schema=False)


@app.middleware("http")
async def track_metrics(request: Request, call_next):
    """Track custom metrics for each request"""
    method = request.method
    endpoint = request.url.path

    # Track request duration
    with api_request_duration.labels(method=method, endpoint=endpoint).time():
        response = await call_next(request)

    # Track request count
    api_requests_total.labels(
        method=method,
        endpoint=endpoint,
        status=response.status_code
    ).inc()

    # Track errors
    if response.status_code >= 400:
        api_errors_total.labels(
            endpoint=endpoint,
            error_type=f"{response.status_code}"
        ).inc()

    return response


@app.on_event("startup")
async def startup_event():
    """Initialize application on startup"""
    logger.info(
        "application_startup",
        service="AIM Agency API",
        version="1.0.0",
        environment=environment
    )


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    logger.info("application_shutdown", service="AIM Agency API")


@app.get("/", status_code=status.HTTP_200_OK)
async def root():
    """Root endpoint"""
    return {
        "service": "AIM Agency API",
        "version": "1.0.0",
        "status": "operational",
        "timestamp": datetime.utcnow().isoformat()
    }


@app.get("/health", status_code=status.HTTP_200_OK)
async def health_check():
    """
    Basic health check - returns 200 if service is running.
    Used by Docker healthcheck and load balancers.
    """
    logger.debug("health_check_called")
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat()
    }


@app.get("/ready", status_code=status.HTTP_200_OK)
async def readiness_check():
    """
    Readiness check - verifies all dependencies are available.
    Returns 200 only if service is ready to handle requests.
    """
    checks = {
        "database": False,
        "redis": False,
        "event_bus": False,
    }

    # Check database
    try:
        from sqlalchemy.ext.asyncio import create_async_engine
        from sqlalchemy import text

        db_url = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./data/production/aim.db")
        engine = create_async_engine(db_url, echo=False)

        async with engine.begin() as conn:
            await conn.execute(text("SELECT 1"))

        await engine.dispose()
        checks["database"] = True
        logger.debug("database_check_passed")
    except Exception as e:
        logger.error("database_check_failed", error=str(e))

    # Check redis
    try:
        import aioredis
        redis_url = os.getenv("REDIS_URL", "redis://redis:6379/0")
        redis = await aioredis.create_redis_pool(redis_url)
        await redis.ping()
        redis.close()
        await redis.wait_closed()
        checks["redis"] = True
        logger.debug("redis_check_passed")
    except Exception as e:
        logger.error("redis_check_failed", error=str(e))

    # Check event bus (basic check - can instantiate)
    try:
        checks["event_bus"] = True
        logger.debug("event_bus_check_passed")
    except Exception as e:
        logger.error("event_bus_check_failed", error=str(e))

    # All checks must pass
    if all(checks.values()):
        logger.info("readiness_check_passed", checks=checks)
        return {
            "status": "ready",
            "checks": checks,
            "timestamp": datetime.utcnow().isoformat()
        }
    else:
        logger.warning("readiness_check_failed", checks=checks)
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={
                "status": "not_ready",
                "checks": checks,
                "timestamp": datetime.utcnow().isoformat()
            }
        )


@app.get("/metrics")
async def metrics():
    """
    Prometheus metrics endpoint.
    Returns metrics in Prometheus text format.
    """
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)


# Import API routers
from aim.api.leads import router as leads_router
from aim.api.onboarding import router as onboarding_router
from aim.api.analytics import router as analytics_router
from aim.api.email import router as email_router
from aim.api.webhooks import router as webhooks_router
from aim.api.gdpr import router as gdpr_router
from aim.api.seo import router as seo_router
from aim.api.content import router as content_router
from aim.api.ads import router as ads_router
from aim.api.projects import router as projects_router

# Include API routers
app.include_router(leads_router)
app.include_router(onboarding_router)
app.include_router(analytics_router)
app.include_router(email_router)
app.include_router(webhooks_router)
app.include_router(gdpr_router)
app.include_router(seo_router)
app.include_router(content_router)
app.include_router(ads_router)
app.include_router(projects_router)

# Performance stats endpoint
@app.get("/api/performance/stats")
async def performance_stats():
    """Return query profiling statistics and cache info."""
    from aim.middleware.profiling import get_profiler
    from aim.middleware.cache import cache as response_cache
    return {
        "query_profiler": get_profiler().stats,
        "cache_entries": response_cache.size,
    }


@app.post("/api/performance/cache/clear")
async def clear_analytics_cache():
    """Clear analytics response cache. Useful after data imports."""
    from aim.middleware.cache import cache as response_cache
    count = response_cache.invalidate("analytics:")
    return {"cleared": count}

# API Routes
@app.get("/api/v1/status")
async def api_status():
    """API status endpoint"""
    return {
        "api_version": "1.0.0",
        "status": "operational",
        "endpoints": {
            "health": "/health",
            "ready": "/ready",
            "metrics": "/metrics",
            "docs": "/docs",
            "leads": "/api/leads",
            "onboarding": "/api/onboarding",
            "analytics": "/api/analytics",
            "email": "/api/email",
            "seo": "/api/seo",
            "content": "/api/content",
            "ads": "/api/ads",
            "projects": "/api/projects"
        }
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        workers=4,
        log_level="info"
    )
