"""Presale API Endpoints

POST /api/presale/prescan — parallel pre-sale intelligence gathering (5 threads)
"""

import logging

from fastapi import APIRouter, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from aim.services.prescan_orchestrator import PrescanOrchestrator

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
