"""
escalate_to_manager — Hermes tool: Escalate Lead to Manager

Sends Telegram notification to Mikhail with client contact + summary.

Per D-34: CTA button "Обсудить с менеджером" triggers this tool.
"""

import json
import logging
import os

import httpx

from tools.registry import registry

logger = logging.getLogger(__name__)

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_ADMIN_CHAT_ID = os.getenv("TELEGRAM_ADMIN_CHAT_ID", "")


async def handle_escalate_to_manager(
    lead_info: str,
    clinic_name: str,
    website: str,
    summary: str,
    **kwargs
) -> str:
    """Escalate lead to manager via Telegram notification.

    Args:
        lead_info: Contact info (name, email, phone)
        clinic_name: Clinic name
        website: Clinic URL
        summary: Brief summary of findings + offered services

    Returns:
        JSON with status
    """
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_ADMIN_CHAT_ID:
        logger.error("Telegram credentials missing, cannot escalate")
        return json.dumps({"error": "Telegram not configured"})

    try:
        # Build notification message
        message = f"""🔥 <b>Новый горячий лид!</b>

<b>Клиника:</b> {clinic_name}
<b>Сайт:</b> {website}

<b>Контакт:</b>
{lead_info}

<b>Резюме:</b>
{summary}

<i>Клиент хочет обсудить детали. Свяжись в течение 15 минут!</i>
"""

        # Send to Telegram
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(
                f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage",
                json={
                    "chat_id": TELEGRAM_ADMIN_CHAT_ID,
                    "text": message,
                    "parse_mode": "HTML"
                }
            )
            response.raise_for_status()

            logger.info("Lead escalated to manager: %s", clinic_name)
            return json.dumps({
                "status": "escalated",
                "clinic": clinic_name,
                "message": "Менеджер получил уведомление и свяжется с вами в ближайшее время"
            }, ensure_ascii=False)

    except httpx.HTTPStatusError as e:
        logger.error("Telegram API error: %s", e)
        return json.dumps({"error": "Failed to send notification", "detail": str(e)})
    except Exception as e:
        logger.exception("Escalation failed")
        return json.dumps({"error": str(e)})


registry.register(
    name="escalate_to_manager",
    toolset="aim-operations",
    schema={
        "name": "escalate_to_manager",
        "description": "Escalate lead to manager — sends Telegram notification to Mikhail",
        "parameters": {
            "type": "object",
            "properties": {
                "lead_info": {
                    "type": "string",
                    "description": "Contact info: name, email, phone"
                },
                "clinic_name": {
                    "type": "string",
                    "description": "Clinic name"
                },
                "website": {
                    "type": "string",
                    "description": "Clinic website URL"
                },
                "summary": {
                    "type": "string",
                    "description": "Brief summary: findings + offered services"
                }
            },
            "required": ["lead_info", "clinic_name", "website", "summary"]
        }
    },
    handler=handle_escalate_to_manager,
    check_fn=lambda: True,
    is_async=True,
    description="Escalate lead to manager via Telegram",
    emoji="🔥"
)
