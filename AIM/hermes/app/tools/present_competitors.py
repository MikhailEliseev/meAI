"""
present_competitors — Hermes tool: Save Competitor Selection

POST http://app:8000/api/competitors/save
Saves the final competitor selection to the lead's pre-sale/ folder.
Handles both "client approved system suggestions" and "client suggested own URLs".

Registered in Hermes internal registry under toolset "aim-operations".
"""

import json
import logging

import httpx

from tools.registry import registry

logger = logging.getLogger(__name__)


def _normalize_args(first_param, defaults):
    if isinstance(first_param, dict):
        return {k: first_param.get(k, defaults[k]) for k in defaults}
    return None


AIM_API_BASE = "http://app:8000"
REQUEST_TIMEOUT = 30.0


async def handle_present_competitors(lead_id=None, status=None, competitors=None, client_urls=None, **kwargs) -> str:
    """Save the final competitor selection to the lead's pre-sale/ folder.

    Handles two flows:
    - status="approved": client accepted the AI-suggested competitors.
      Pass the competitors list (with inn, legal_name, scores).
    - status="client_suggested": client provided their own competitor URLs.
      Pass client_urls list.

    Args:
        lead_id: The lead ID from collect_contact
        status: "approved" or "client_suggested"
        competitors: List of competitor objects (for approved status)
        client_urls: List of URL strings (for client_suggested status)

    Returns:
        JSON string with save confirmation.
    """
    unpacked = _normalize_args(lead_id, {
        "lead_id": "", "status": "approved", "competitors": [], "client_urls": []
    })
    if unpacked:
        lead_id = unpacked["lead_id"]
        status = unpacked["status"]
        competitors = unpacked["competitors"]
        client_urls = unpacked["client_urls"]

    if not lead_id:
        return json.dumps({"error": "lead_id is required"})

    if status not in ("approved", "client_suggested"):
        return json.dumps({"error": "status must be 'approved' or 'client_suggested'"})

    logger.info("Saving competitors for lead=%s status=%s", lead_id, status)

    try:
        body = {
            "lead_id": lead_id,
            "status": status,
            "competitors": competitors if isinstance(competitors, list) else [],
            "client_urls": client_urls if isinstance(client_urls, list) else [],
        }

        async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT) as client:
            response = await client.post(
                f"{AIM_API_BASE}/api/competitors/save",
                json=body,
            )
            response.raise_for_status()
            data = response.json()
            logger.info("Competitors saved: lead=%s count=%s", lead_id, data.get("count", 0))
            return json.dumps(data, ensure_ascii=False, indent=2)

    except httpx.HTTPStatusError as e:
        logger.error("AIM API returned error for present_competitors: %s", e)
        return json.dumps({
            "error": "AIM API returned an error",
            "status": e.response.status_code,
            "detail": str(e),
        })
    except httpx.RequestError as e:
        logger.error("Cannot reach AIM API for present_competitors: %s", e)
        return json.dumps({
            "error": "Cannot reach AIM API",
            "detail": str(e),
        })
    except Exception as e:
        logger.exception("Unexpected error in present_competitors handler")
        return json.dumps({
            "error": "Unexpected error in tool handler",
            "detail": str(e),
        })


registry.register(
    name="present_competitors",
    toolset="aim-operations",
    schema={
        "type": "function",
        "function": {
            "name": "present_competitors",
            "description": (
                "Save the final competitor selection to the lead's pre-sale/ folder. "
                "Call after the client approves AI-suggested competitors (status='approved') "
                "or provides their own competitor URLs (status='client_suggested'). "
                "For 'approved', pass the competitors list from find_competitors result. "
                "For 'client_suggested', pass client_urls list with competitor website URLs."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "lead_id": {
                        "type": "string",
                        "description": "Lead ID from collect_contact result",
                    },
                    "status": {
                        "type": "string",
                        "description": "'approved' if client accepted suggestions, 'client_suggested' if they provided their own URLs",
                        "enum": ["approved", "client_suggested"],
                    },
                    "competitors": {
                        "type": "array",
                        "description": "List of competitor objects (from find_competitors result), only for status='approved'",
                        "items": {"type": "object"},
                    },
                    "client_urls": {
                        "type": "array",
                        "description": "List of competitor website URLs, only for status='client_suggested'",
                        "items": {"type": "string"},
                    },
                },
                "required": ["lead_id", "status"],
            },
        },
    },
    handler=handle_present_competitors,
    check_fn=lambda: True,
    is_async=True,
    description="Save final competitor selection to lead's pre-sale/ folder",
    emoji="✅",
)
