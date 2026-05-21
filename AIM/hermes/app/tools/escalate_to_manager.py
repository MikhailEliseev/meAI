"""
escalate_to_manager — Hermes tool: Escalate to Human Manager

POST http://app:8000/api/sales/escalate
Escalates a conversation to a human manager. Used when the agent cannot
handle the situation: medical data requests (152-ФЗ), complex questions,
threats, profanity, or explicit human requests.

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
REQUEST_TIMEOUT = 15.0


async def handle_escalate_to_manager(
    conversation_id=None,
    reason=None,
    severity="urgent",
    notes="",
    **kwargs,
) -> str:
    """Escalate a conversation to a human manager.

    Use when: patient asks for medical history (152-ФЗ), complex question
    agent cannot answer, threats or profanity, explicit human request,
    or technical failures.

    Args:
        conversation_id: The conversation ID to escalate.
        reason: Escalation reason: medical_data_request, complex_question,
                inappropriate_behavior, human_request, technical_failure.
        severity: immediate (stop now), urgent (within 5 min), routine (flag for review).
        notes: Additional context for the manager.

    Returns:
        JSON string with status and escalation details.
    """
    unpacked = _normalize_args(conversation_id, {
        "conversation_id": "", "reason": "", "severity": "urgent", "notes": ""
    })
    if unpacked:
        conversation_id = unpacked["conversation_id"]
        reason = unpacked["reason"]
        severity = unpacked.get("severity", "urgent")
        notes = unpacked.get("notes", "")

    if not conversation_id:
        return json.dumps({"error": "conversation_id is required"})

    valid_reasons = [
        "medical_data_request", "complex_question",
        "inappropriate_behavior", "human_request", "technical_failure",
    ]
    if reason not in valid_reasons:
        return json.dumps({
            "error": f"Invalid reason. Must be one of: {', '.join(valid_reasons)}"
        })

    logger.info("Escalating: conv=%s reason=%s severity=%s", conversation_id, reason, severity)
    try:
        async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT) as client:
            response = await client.post(
                f"{AIM_API_BASE}/api/sales/escalate",
                json={
                    "conversation_id": conversation_id,
                    "reason": reason,
                    "severity": severity,
                    "notes": str(notes),
                },
            )
            response.raise_for_status()
            data = response.json()
            logger.info("Escalated: conv=%s", conversation_id)
            return json.dumps(data, ensure_ascii=False, indent=2)
    except httpx.HTTPStatusError as e:
        logger.error("AIM API returned error for escalation: %s", e)
        return json.dumps({
            "error": "AIM API returned an error",
            "status": e.response.status_code,
            "detail": str(e),
        })
    except httpx.RequestError as e:
        logger.error("Cannot reach AIM API for escalation: %s", e)
        return json.dumps({"error": "Cannot reach AIM API", "detail": str(e)})
    except Exception as e:
        logger.exception("Unexpected error in escalate_to_manager handler")
        return json.dumps({"error": "Unexpected error", "detail": str(e)})


registry.register(
    name="escalate_to_manager",
    toolset="aim-operations",
    schema={
        "type": "function",
        "function": {
            "name": "escalate_to_manager",
            "description": (
                "Escalate a conversation to a human manager. "
                "Use when: medical data request (152-ФЗ), complex question, "
                "threats/profanity, explicit human request, or technical failures."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "conversation_id": {
                        "type": "string",
                        "description": "The conversation ID to escalate",
                    },
                    "reason": {
                        "type": "string",
                        "description": "Escalation reason",
                        "enum": [
                            "medical_data_request",
                            "complex_question",
                            "inappropriate_behavior",
                            "human_request",
                            "technical_failure",
                        ],
                    },
                    "severity": {
                        "type": "string",
                        "description": "Escalation severity level",
                        "enum": ["immediate", "urgent", "routine"],
                    },
                    "notes": {
                        "type": "string",
                        "description": "Additional context for the manager",
                    },
                },
                "required": ["conversation_id", "reason"],
            },
        },
    },
    handler=handle_escalate_to_manager,
    check_fn=lambda: True,
    is_async=True,
    description="Escalate a conversation to a human manager",
    emoji="🚨",
)
