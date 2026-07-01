"""
get_lead_pipeline — Hermes tool: Get Sales Pipeline Overview

GET http://aim-app:8000/api/sales/pipeline
Returns the sales pipeline — conversations by status and qualification tier.
Used by the SALES_ADMIN and ADMIN modes to view the state of the funnel.

Registered in Hermes internal registry under toolset "aim-operations".
"""

import json
import logging

import httpx

from tools.registry import registry

logger = logging.getLogger(__name__)

AIM_API_BASE = "http://aim-app:8000"
REQUEST_TIMEOUT = 15.0


async def handle_get_lead_pipeline(project_id=None, **kwargs) -> str:
    """Get the sales pipeline overview.

    Returns total conversation count, breakdown by status (active, escalated,
    closed), and breakdown by qualification tier (hot, warm, cold).

    Args:
        project_id: Optional project ID to filter by.

    Returns:
        JSON string with pipeline statistics.
    """
    if isinstance(project_id, dict):
        project_id = project_id.get("project_id", None)

    params = {}
    if project_id:
        params["project_id"] = project_id

    logger.info("Fetching pipeline: project=%s", project_id or "all")
    try:
        async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT) as client:
            response = await client.get(
                f"{AIM_API_BASE}/api/sales/pipeline",
                params=params,
            )
            response.raise_for_status()
            data = response.json()
            logger.info("Pipeline fetched: total=%s", data.get("total", 0))
            return json.dumps(data, ensure_ascii=False, indent=2)
    except httpx.HTTPStatusError as e:
        logger.error("AIM API returned error for pipeline: %s", e)
        return json.dumps({
            "error": "AIM API returned an error",
            "status": e.response.status_code,
            "detail": str(e),
        })
    except httpx.RequestError as e:
        logger.error("Cannot reach AIM API for pipeline: %s", e)
        return json.dumps({"error": "Cannot reach AIM API", "detail": str(e)})
    except Exception as e:
        logger.exception("Unexpected error in get_lead_pipeline handler")
        return json.dumps({"error": "Unexpected error", "detail": str(e)})


registry.register(
    name="get_lead_pipeline",
    toolset="aim-operations",
    schema={
        "type": "function",
        "function": {
            "name": "get_lead_pipeline",
            "description": (
                "Get the sales pipeline overview — total conversations, "
                "breakdown by status (active, escalated, closed) and "
                "by qualification tier (hot, warm, cold)."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "project_id": {
                        "type": "string",
                        "description": "Optional project ID to filter by",
                    },
                },
                "required": [],
            },
        },
    },
    handler=handle_get_lead_pipeline,
    check_fn=lambda: True,
    is_async=True,
    description="Get sales pipeline overview with status and tier breakdowns",
    emoji="📊",
)
