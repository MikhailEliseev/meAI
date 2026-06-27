"""
update_knowledge — Hermes tool: Update Client Knowledge Vault

POST http://aim-app:8000/api/sales/knowledge/update
Updates a client's knowledge vault file (services, FAQ, tone of voice, etc.).
Used by the ADMIN mode to keep client knowledge up to date.

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


async def handle_update_knowledge(
    client_id=None,
    filename=None,
    content=None,
    **kwargs,
) -> str:
    """Update a client's knowledge vault file.

    Updates one of: services.md, faq.md, tone_of_voice.md,
    escalation_rules.md, or qualification.md for a specific client.

    Args:
        client_id: The client identifier.
        filename: The vault file to update (services, faq, tone_of_voice,
                  escalation_rules, or qualification).
        content: New markdown content for the file.

    Returns:
        JSON string with status and updated file info.
    """
    unpacked = _normalize_args(client_id, {
        "client_id": "", "filename": "", "content": ""
    })
    if unpacked:
        client_id = unpacked["client_id"]
        filename = unpacked["filename"]
        content = unpacked["content"]

    if not client_id:
        return json.dumps({"error": "client_id is required"})

    valid_files = ["services", "faq", "tone_of_voice", "escalation_rules", "qualification"]
    if filename not in valid_files:
        return json.dumps({
            "error": f"Invalid filename. Must be one of: {', '.join(valid_files)}.md"
        })

    if not content:
        return json.dumps({"error": "content is required"})

    filename_with_ext = f"{filename}.md"

    logger.info("Updating knowledge: client=%s file=%s", client_id, filename_with_ext)
    try:
        async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT) as client:
            response = await client.put(
                f"{AIM_API_BASE}/api/sales/knowledge/update",
                json={
                    "client_id": client_id,
                    "filename": filename_with_ext,
                    "content": content,
                },
            )
            response.raise_for_status()
            data = response.json()
            logger.info("Knowledge updated: client=%s file=%s", client_id, filename_with_ext)
            return json.dumps(data, ensure_ascii=False, indent=2)
    except httpx.HTTPStatusError as e:
        logger.error("AIM API returned error for knowledge update: %s", e)
        return json.dumps({
            "error": "AIM API returned an error",
            "status": e.response.status_code,
            "detail": str(e),
        })
    except httpx.RequestError as e:
        logger.error("Cannot reach AIM API for knowledge update: %s", e)
        return json.dumps({"error": "Cannot reach AIM API", "detail": str(e)})
    except Exception as e:
        logger.exception("Unexpected error in update_knowledge handler")
        return json.dumps({"error": "Unexpected error", "detail": str(e)})


registry.register(
    name="update_knowledge",
    toolset="aim-operations",
    schema={
            "name": "update_knowledge",
            "description": (
                "Update a client's knowledge vault file. "
                "Files: services (prices and services), faq (common questions), "
                "tone_of_voice (communication style), escalation_rules (escalation config), "
                "qualification (lead qualification criteria)."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "client_id": {
                        "type": "string",
                        "description": "The client identifier",
                    },
                    "filename": {
                        "type": "string",
                        "description": "Vault file to update (without .md extension)",
                        "enum": [
                            "services", "faq", "tone_of_voice",
                            "escalation_rules", "qualification",
                        ],
                    },
                    "content": {
                        "type": "string",
                        "description": "New markdown content for the file",
                    },
                },
                "required": ["client_id", "filename", "content"],
            },
        },
    handler=handle_update_knowledge,
    check_fn=lambda: True,
    is_async=True,
    description="Update a client's knowledge vault file",
    emoji="📝",
)
