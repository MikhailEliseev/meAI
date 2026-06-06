"""
Content Analysis API Endpoint

POST /api/content/analyze — Content quality analysis via CI Content agent.
Wires Hermes tool run_content_analysis → CI pipeline.
"""

import logging
import os
import asyncio
import time

from fastapi import APIRouter, HTTPException

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/content", tags=["content"])


@router.post("/analyze")
async def run_content_analysis(payload: dict):
    """Analyze content quality on a medical clinic website.

    Request body:
        {
            "url": "https://clinic.ru",
            "content_type": "all"       // all, blog, services, landing
        }

    Evaluates medical accuracy, SEO optimization, readability,
    and conversion effectiveness per page type.
    """
    url = payload.get("url", "").strip()
    if not url:
        raise HTTPException(status_code=400, detail="url is required")

    content_type = payload.get("content_type", "all")

    # Use ci_content agent via CIOrchestrator for consistent pipeline
    try:
        from meai.events.event_bus import EventBus
        from src.aim.subagents.competitive_intel.orchestrator.ci_orchestrator import CIOrchestrator

        database_url = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./AIM/data/aim.db")
        event_bus = EventBus()
        await event_bus.initialize()

        orchestrator = CIOrchestrator(
            agent_id="hermes-content-api",
            event_bus=event_bus,
            database_url=database_url,
            vault_path="AIM/obsidian/ci-orchestrator",
        )

        result = await orchestrator.execute_ci_analysis(
            task_data={
                "task_id": f"content-analysis-{int(time.time())}",
                "niche": "medical",
                "geo": "ru",
                "tier": "quick",  # Quick tier for content-only
                "competitors": [url],
                "content_type": content_type,
            }
        )

        logger.info("Content analysis completed for: %s (type: %s)", url, content_type)
        return result

    except Exception as e:
        logger.exception("Content analysis failed")
        raise HTTPException(status_code=500, detail=f"Content analysis failed: {str(e)}")
