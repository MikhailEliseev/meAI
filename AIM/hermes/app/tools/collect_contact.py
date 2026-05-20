"""
collect_contact — Hermes tool: Collect Client Contact

POST http://app:8000/api/leads
Collects client contact information and creates a lead dossier. Saves contact
to the AIM database and creates a Linear task for Mikhail to follow up.

Registered in Hermes internal registry under toolset "aim-operations".
"""

import json
import logging

import httpx

from tools.registry import registry

logger = logging.getLogger(__name__)

AIM_API_BASE = "http://app:8000"
REQUEST_TIMEOUT = 30.0  # seconds

VALID_CONTACT_TYPES = {"telegram", "email", "phone"}


async def handle_collect_contact(
    contact_type: str,
    contact_value: str,
    website: str = "",
    name: str = "",
    source: str = "web_chat",
    **kwargs,
) -> str:
    """Collect client contact information and create a lead dossier.

    Validates contact type (telegram/email/phone only), saves contact
    to the AIM database, and creates a Linear task for Mikhail to follow up.

    Args:
        contact_type: Type of contact: "telegram", "email", or "phone"
        contact_value: Contact value: @username, email@domain.com, +7...
        website: Client's website URL (optional)
        name: Client's name (optional)
        source: Lead source, defaults to "web_chat"

    Returns:
        JSON string with lead_id and status.
    """
    if contact_type not in VALID_CONTACT_TYPES:
        return json.dumps({
            "error": "Invalid contact_type",
            "detail": f"Must be one of: {', '.join(sorted(VALID_CONTACT_TYPES))}. Got: {contact_type}",
        })

    logger.info(
        "Collecting contact: type=%s value=%s website=%s name=%s source=%s",
        contact_type, contact_value, website, name, source,
    )
    try:
        async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT) as client:
            response = await client.post(
                f"{AIM_API_BASE}/api/leads",
                json={
                    "contact_type": contact_type,
                    "contact_value": contact_value,
                    "website": website,
                    "name": name,
                    "source": source,
                },
            )
            response.raise_for_status()
            data = response.json()
            logger.info("Contact collected successfully: lead_id=%s", data.get("lead_id", "unknown"))
            return json.dumps(data, ensure_ascii=False, indent=2)
    except httpx.HTTPStatusError as e:
        logger.error("AIM API returned error for contact collection: %s", e)
        return json.dumps({
            "error": "AIM API returned an error",
            "status": e.response.status_code,
            "detail": str(e),
        })
    except httpx.RequestError as e:
        logger.error("Cannot reach AIM API for contact collection: %s", e)
        return json.dumps({
            "error": "Cannot reach AIM API",
            "detail": str(e),
        })
    except Exception as e:
        logger.exception("Unexpected error in contact collection handler")
        return json.dumps({
            "error": "Unexpected error in tool handler",
            "detail": str(e),
        })


registry.register(
    name="collect_contact",
    toolset="aim-operations",
    schema={
        "type": "function",
        "function": {
            "name": "collect_contact",
            "description": (
                "Collect client contact information and create a lead dossier. "
                "Saves contact to the AIM database and creates a Linear task "
                "for Mikhail to follow up."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "contact_type": {
                        "type": "string",
                        "description": "Type of contact: telegram, email, or phone",
                        "enum": ["telegram", "email", "phone"],
                    },
                    "contact_value": {
                        "type": "string",
                        "description": "Contact value: @username, email@domain.com, +7...",
                    },
                    "website": {
                        "type": "string",
                        "description": "Client's website URL (optional)",
                    },
                    "name": {
                        "type": "string",
                        "description": "Client's name (optional)",
                    },
                    "source": {
                        "type": "string",
                        "description": "Lead source (default: web_chat)",
                    },
                },
                "required": ["contact_type", "contact_value"],
            },
        },
    },
    handler=handle_collect_contact,
    check_fn=lambda: True,
    is_async=True,
    description="Collect client contact info and create lead dossier in AIM database",
    emoji="📇",
)
