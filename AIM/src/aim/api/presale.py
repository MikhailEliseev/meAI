"""Presale API Endpoints

POST /api/presale/prescan        — parallel pre-sale intelligence gathering (5 threads)
POST /api/presale/prescan-staged — 3-stage ultra-deep prescan with progressive results
"""

import logging
import time

from fastapi import APIRouter, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from src.aim.schemas.company_profile import StagedPrescanRequest
from src.aim.services.prescan_orchestrator import PrescanOrchestrator

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/presale", tags=["presale"])


class PrescanRequest(BaseModel):
    url: str = Field(..., description="Client clinic website URL")


@router.post("/prescan", status_code=status.HTTP_200_OK)
async def run_prescan(body: PrescanRequest):
    """Run parallel pre-sale intelligence gathering.

    Launches 5 reconnaissance threads simultaneously:
      1. Website structure (services, specialization, city, doctors, prices)
      2. Financial data (rusprofile/nalog by INN)
      3. Quick SEO scan (meta tags, mobile viewport, SSL, load speed)
      4. Reviews snapshot (first 20, rating, praise/complaint themes)
      5. Social media (last post date, platform)

    Returns aggregated PrescanResult for Hermes to narrate conversationally.
    Target: 60-90 seconds (dominated by slowest thread).
    """
    orchestrator = PrescanOrchestrator()
    try:
        result = await orchestrator.prescan(body.url)
        return JSONResponse(content={
            "success": True,
            "url": body.url,
            "result": result.to_dict(),
        })
    except Exception as e:
        logger.exception("prescan_failed")
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "success": False,
                "url": body.url,
                "error": str(e),
            },
        )
    finally:
        await orchestrator.close()


@router.post("/prescan-staged", status_code=status.HTTP_200_OK)
async def run_prescan_staged(body: StagedPrescanRequest):
    """Run 3-stage ultra-deep prescan with progressive results.

    Stages:
      1. Финансовый хук (20-30s)  — revenue, profit, legal entity
      2. Под капотом (40-60s)     — licenses, founders, deep SEO, reviews, social
      3. Рынок (60-90+s)          — Yandex/Google Maps, competitors, content audit

    Each stage fires a progress callback. Results cached in company_profiles.
    """
    orchestrator = PrescanOrchestrator()
    t0 = time.monotonic()
    stages_completed = []
    cached = False

    async def progress_callback(
        stage_number: int, stage_name: str, summary: dict, is_final: bool
    ) -> None:
        stages_completed.append({
            "stage": stage_number,
            "name": stage_name,
            "summary": summary,
            "is_final": is_final,
            "elapsed": round(time.monotonic() - t0, 1),
        })

    try:
        # Check cache first if not force_refresh
        if not body.force_refresh:
            cached_check = await orchestrator._cache_get(body.url)
            if cached_check:
                cached = True
                elapsed = time.monotonic() - t0
                return JSONResponse(content={
                    "success": True,
                    "url": body.url,
                    "cached": True,
                    "elapsed_seconds": round(elapsed, 1),
                    "stages": [],
                    "profile_data": cached_check,
                    "errors": cached_check.get("_errors", []),
                })

        result = await orchestrator.prescan_staged(
            body.url,
            progress_callback=progress_callback,
            force_refresh=body.force_refresh,
        )
        elapsed = time.monotonic() - t0
        return JSONResponse(content={
            "success": True,
            "url": body.url,
            "cached": cached,
            "elapsed_seconds": round(elapsed, 1),
            "stages": stages_completed,
            "profile_data": result,
            "errors": result.get("_errors", []) if isinstance(result, dict) else [],
        })
    except Exception as e:
        logger.exception("prescan_staged_failed")
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "success": False,
                "url": body.url,
                "error": str(e),
            },
        )
    finally:
        await orchestrator.close()
