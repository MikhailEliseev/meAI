"""
show_all_leads — Hermes tool: Show All Leads (ADMIN only)

GET http://aim-app:8000/api/leads?period={period}&status={status}
Shows all leads captured by the AIM agency. Lists lead details including
source, status, contact info, website, and current pipeline stage.
Intended for ADMIN mode (Mikhail). Access control enforced at AIM API layer.

Registered in Hermes internal registry under toolset "aim-operations".
"""

import json
import logging

import httpx

from tools.registry import registry

logger = logging.getLogger(__name__)

AIM_API_BASE = "http://aim-app:8000"
REQUEST_TIMEOUT = 30.0  # seconds


async def handle_show_all_leads(period: str = "week", status: str = "all", **kwargs) -> str:
    """Show all leads captured by the AIM agency.

    Lists lead details including source, status, contact info, website,
    and current pipeline stage. Access control is enforced at the AIM API
    layer — non-admin requests will be rejected by the API.

    Args:
        period: Filter period: "today", "week", "month", or "all"
        status: Filter status: "new", "qualified", "audited", "contacted",
                "active", "completed", "closed", or "all"

    Returns:
        JSON string with list of leads matching filters.
    """
    logger.info("Fetching leads: period=%s status=%s", period, status)
    try:
        async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT) as client:
            response = await client.get(
                f"{AIM_API_BASE}/api/leads",
                params={"period": period, "status": status},
            )
            response.raise_for_status()
            data = response.json()
            lead_count = len(data) if isinstance(data, list) else "unknown"
            logger.info("Leads fetched: count=%s", lead_count)
            return json.dumps(data, ensure_ascii=False, indent=2)
    except httpx.HTTPStatusError as e:
        logger.error("AIM API returned error for leads listing: %s", e)
        return json.dumps({
            "error": "AIM API returned an error",
            "status": e.response.status_code,
            "detail": str(e),
        })
    except httpx.RequestError as e:
        logger.error("Cannot reach AIM API for leads listing: %s", e)
        return json.dumps({
            "error": "Cannot reach AIM API",
            "detail": str(e),
        })
    except Exception as e:
        logger.exception("Unexpected error in leads listing handler")
        return json.dumps({
            "error": "Unexpected error in tool handler",
            "detail": str(e),
        })


registry.register(
    name="show_all_leads",
    toolset="aim-operations",
    schema={
        "type": "function",
        "function": {
            "name": "show_all_leads",
            "description": (
                "Show all leads captured by the AIM agency. Lists lead details "
                "including source, status, contact info, website, and current "
                "pipeline stage. Intended for ADMIN mode (Mikhail)."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "period": {
                        "type": "string",
                        "description": "Filter period: today, week, month, all",
                        "enum": ["today", "week", "month", "all"],
                    },
                    "status": {
                        "type": "string",
                        "description": "Filter status: new, qualified, audited, contacted, active, completed, closed, all",
                        "enum": [
                            "new", "qualified", "audited", "contacted",
                            "active", "completed", "closed", "all",
                        ],
                    },
                },
            },
        },
    },
    handler=handle_show_all_leads,
    check_fn=lambda: True,
    is_async=True,
    description="Show all leads captured by AIM agency with optional period/status filters (ADMIN mode)",
    emoji="👥",
)
