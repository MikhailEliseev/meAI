"""
SEO Audit API Endpoint

POST /api/seo/audit — Full SEO audit via CIOrchestrator.
Wires Hermes tool run_seo_audit → Competitive Intelligence pipeline.
"""

import logging
import os
import asyncio
import time
from typing import Optional

from fastapi import APIRouter, HTTPException

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/seo", tags=["seo"])

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

        database_url = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./AIM/data/aim.db")
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


@router.post("/audit")
async def run_seo_audit(payload: dict):
    """Run full SEO audit via Competitive Intelligence pipeline.

    Request body:
        {
            "url": "https://clinic.ru",
            "competitors": ["https://competitor1.ru", "https://competitor2.ru"],  // optional
            "niche": "стоматология",                                              // optional
            "tier": "deep"                                                         // optional: quick/deep/full
        }

    Returns CI analysis with tech stack, content, SEO metrics, strategy.
    """
    url = payload.get("url", "").strip()
    if not url:
        raise HTTPException(status_code=400, detail="url is required")

    competitors = payload.get("competitors", [])
    niche = payload.get("niche", "medical")
    tier = payload.get("tier", "deep")

    # Ensure client URL is first in competitors list
    all_urls = [url] + [c for c in competitors if c != url]

    try:
        orchestrator = await _get_orchestrator()

        result = await orchestrator.execute_ci_analysis(
            task_data={
                "task_id": f"seo-audit-{int(time.time())}",
                "niche": niche,
                "geo": "ru",
                "tier": tier,
                "competitors": all_urls,
                "target_audience": payload.get("target_audience", ""),
                "price_segment": payload.get("price_segment", "mid"),
            }
        )

        logger.info("SEO audit completed: %d phases, %d competitors",
                     len(result.get("phases_executed", [])),
                     result.get("competitors_analyzed", 0))

        return result

    except Exception as e:
        logger.exception("SEO audit failed")
        raise HTTPException(status_code=500, detail=f"SEO audit failed: {str(e)}")
