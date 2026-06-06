"""Hermes Orchestration API — single endpoint for all Hermes→AIM operations.

POST /api/hermes/orchestrate  — route any operation through HermesOrchestrator.

Replaces 16 separate API endpoints that Hermes tools currently call.
Existing endpoints (/api/seo/audit, /api/presale/prescan, etc.) remain
operational for backward compatibility.
"""

from __future__ import annotations

import logging

from fastapi import APIRouter, HTTPException

from src.aim.orchestration.hermes_orchestrator import HermesOrchestrator

logger = logging.getLogger("aim.api.hermes")

router = APIRouter(prefix="/api/hermes", tags=["hermes"])

# Singleton orchestrator — lazily initialized
_orchestrator: HermesOrchestrator | None = None


def _get_orchestrator() -> HermesOrchestrator:
    """Lazy-init the HermesOrchestrator singleton."""
    global _orchestrator
    if _orchestrator is None:
        _orchestrator = HermesOrchestrator()
        logger.info("HermesOrchestrator initialized")
    return _orchestrator


@router.post("/orchestrate")
async def orchestrate(payload: dict):
    """Single orchestration endpoint for all Hermes operations.

    Request body:
        {
            "operation": "prescan",
            "params": {
                "url": "https://clinic.ru",
                ...operation-specific params
            }
        }

    Returns:
        {"status": "success"|"error", "operation": str, "result": {...}}

    Available operations:
        prescan              — 3-stage intelligence gathering
        seo_audit            — SEO analysis via SEOMagister
        content_analysis     — Content quality analysis
        ads_report           — Ads performance report
        competitor_analysis  — CI pipeline (quick/deep/full)
        lead_management      — CRM lead operations
        knowledge_query      — Query AIM knowledge base
    """
    operation = payload.get("operation", "")
    params = payload.get("params", {})

    if not operation:
        raise HTTPException(status_code=400, detail="'operation' is required")

    orchestrator = _get_orchestrator()
    result = await orchestrator.orchestrate(operation=operation, params=params)

    if result["status"] == "error" and "Unknown operation" in str(result.get("error", "")):
        raise HTTPException(status_code=400, detail=result["error"])

    return result
