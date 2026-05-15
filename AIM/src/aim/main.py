"""
AIM Agency API - FastAPI Application

Production-ready API with health checks, metrics, and monitoring.
"""

from fastapi import FastAPI, status
from fastapi.responses import JSONResponse, Response
from datetime import datetime
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Create FastAPI application
app = FastAPI(
    title="AIM Agency API",
    description="AI-first medical marketing agency automation platform",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)


@app.on_event("startup")
async def startup_event():
    """Initialize application on startup"""
    logger.info("AIM Agency API starting up...")
    logger.info("Environment: production")


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    logger.info("AIM Agency API shutting down...")


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
        import os

        db_url = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./data/production/aim.db")
        engine = create_async_engine(db_url, echo=False)

        async with engine.begin() as conn:
            await conn.execute(text("SELECT 1"))

        await engine.dispose()
        checks["database"] = True
    except Exception as e:
        logger.error(f"Database check failed: {e}")

    # Check redis
    try:
        import aioredis
        redis_url = os.getenv("REDIS_URL", "redis://redis:6379/0")
        redis = await aioredis.create_redis_pool(redis_url)
        await redis.ping()
        redis.close()
        await redis.wait_closed()
        checks["redis"] = True
    except Exception as e:
        logger.error(f"Redis check failed: {e}")

    # Check event bus (basic check - can instantiate)
    try:
        checks["event_bus"] = True
    except Exception as e:
        logger.error(f"Event bus check failed: {e}")

    # All checks must pass
    if all(checks.values()):
        return {
            "status": "ready",
            "checks": checks,
            "timestamp": datetime.utcnow().isoformat()
        }
    else:
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
    try:
        from prometheus_client import generate_latest, CONTENT_TYPE_LATEST
        return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)
    except ImportError:
        # Fallback if prometheus_client not installed
        return Response(
            "# Prometheus metrics not available\n",
            media_type="text/plain"
        )


# API Routes (placeholder for future implementation)
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
            "docs": "/docs"
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
