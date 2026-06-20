"""
qualify_lead — Hermes tool: Qualify Sales Lead

POST http://aim-app:8000/api/sales/qualify
Evaluates lead quality from conversation — sets score, tier, and recommended action.
Used by the SALES_ADMIN mode when Hermes needs to manually qualify a lead.

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


AIM_API_BASE = "http://aim-app:8000"
REQUEST_TIMEOUT = 15.0


async def handle_qualify_lead(
    conversation_id=None,
    score=None,
    tier=None,
    notes="",
    **kwargs,
) -> str:
    """Manually qualify a lead in a sales conversation.

    Sets the qualification score (0-100), tier (hot/warm/cold), and notes
    on a conversation. Used when the agent detects strong buying signals
    or wants to flag a conversation for follow-up.

    Args:
        conversation_id: The conversation ID to qualify.
        score: Qualification score 0-100.
        tier: Lead tier: hot (70+), warm (40-69), cold (<40).
        notes: Optional notes about the qualification.

    Returns:
        JSON string with status and qualification details.
    """
    unpacked = _normalize_args(conversation_id, {
        "conversation_id": "", "score": 0, "tier": "", "notes": ""
    })
    if unpacked:
        conversation_id = unpacked["conversation_id"]
        score = unpacked["score"]
        tier = unpacked["tier"]
        notes = unpacked.get("notes", "")

    if not conversation_id:
        return json.dumps({"error": "conversation_id is required"})
    if tier not in ("hot", "warm", "cold"):
        return json.dumps({"error": "tier must be hot, warm, or cold"})

    logger.info("Qualifying lead: conv=%s score=%s tier=%s", conversation_id, score, tier)
    try:
        async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT) as client:
            response = await client.post(
                f"{AIM_API_BASE}/api/sales/qualify",
                json={
                    "conversation_id": conversation_id,
                    "score": int(score),
                    "tier": tier,
                    "notes": str(notes),
                },
            )
            response.raise_for_status()
            data = response.json()
            logger.info("Lead qualified: conv=%s tier=%s", conversation_id, data.get("tier"))
            return json.dumps(data, ensure_ascii=False, indent=2)
    except httpx.HTTPStatusError as e:
        logger.error("AIM API returned error for qualification: %s", e)
        return json.dumps({
            "error": "AIM API returned an error",
            "status": e.response.status_code,
            "detail": str(e),
        })
    except httpx.RequestError as e:
        logger.error("Cannot reach AIM API for qualification: %s", e)
        return json.dumps({"error": "Cannot reach AIM API", "detail": str(e)})
    except Exception as e:
        logger.exception("Unexpected error in qualify_lead handler")
        return json.dumps({"error": "Unexpected error", "detail": str(e)})


registry.register(
    name="qualify_lead",
    toolset="aim-operations",
    schema={
        "type": "function",
        "function": {
            "name": "qualify_lead",
            "description": (
                "Manually qualify a lead in a sales conversation. "
                "Sets score (0-100), tier (hot/warm/cold), and notes. "
                "Use when you detect strong buying signals or want to flag for follow-up."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "conversation_id": {
                        "type": "string",
                        "description": "The conversation ID to qualify",
                    },
                    "score": {
                        "type": "integer",
                        "description": "Qualification score 0-100 (hot=70+, warm=40-69, cold=<40)",
                        "minimum": 0,
                        "maximum": 100,
                    },
                    "tier": {
                        "type": "string",
                        "description": "Lead tier",
                        "enum": ["hot", "warm", "cold"],
                    },
                    "notes": {
                        "type": "string",
                        "description": "Optional qualification notes",
                    },
                },
                "required": ["conversation_id", "score", "tier"],
            },
        },
    },
    handler=handle_qualify_lead,
    check_fn=lambda: True,
    is_async=True,
    description="Manually qualify a sales lead with score and tier",
    emoji="🏷️",
)
