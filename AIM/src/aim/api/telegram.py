"""Telegram Bot Webhook Handler

Receives updates from Telegram Bot API and routes them to appropriate handlers.
Set webhook: POST https://api.telegram.org/bot<TOKEN>/setWebhook with body
{"url": "https://iamaim.ru/telegram/webhook"}

Part of: Production infrastructure — alerting + bot communication channel
"""

import logging
import os

from fastapi import APIRouter, HTTPException, Request, status

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/telegram", tags=["telegram"])


def _is_authorized(request: Request) -> bool:
    """Lightweight auth: check X-Telegram-Bot-Api-Secret header if configured."""
    expected = os.getenv("TELEGRAM_WEBHOOK_SECRET", "")
    if not expected:
        return True  # No secret configured — accept all (dev/test mode)
    actual = request.headers.get("X-Telegram-Bot-Api-Secret", "")
    return actual == expected


@router.get("/webhook", status_code=status.HTTP_200_OK)
async def telegram_webhook_info():
    """Return webhook status — helps debugging webhook setup."""
    bot_token = os.getenv("TELEGRAM_BOT_TOKEN", "")
    webhook_url = os.getenv("TELEGRAM_WEBHOOK_URL", "https://iamaim.ru/telegram/webhook")
    return {
        "endpoint": "/telegram/webhook",
        "method": "POST",
        "bot_configured": bool(bot_token),
        "webhook_url": webhook_url,
    }


@router.post("/webhook", status_code=status.HTTP_200_OK)
async def telegram_webhook(request: Request):
    """Handle incoming Telegram bot update.

    Telegram sends Update objects:
    https://core.telegram.org/bots/api#update

    Responds 200 immediately — Telegram retries if no 200 within ~10s.
    Heavy processing should be offloaded to background tasks.
    """
    if not _is_authorized(request):
        logger.warning("telegram_webhook_unauthorized")
        raise HTTPException(status_code=403, detail="Forbidden")

    update = await request.json()
    update_id = update.get("update_id", "unknown")

    logger.debug("telegram_update_received", extra={"update_id": update_id})

    # Route by update type
    if "message" in update:
        await _handle_message(update["message"])
    elif "callback_query" in update:
        await _handle_callback(update["callback_query"])
    elif "edited_message" in update:
        await _handle_message(update["edited_message"], edited=True)

    return {"status": "ok"}


async def _handle_message(message: dict, edited: bool = False) -> None:
    """Handle incoming text messages and commands."""
    chat_id = message.get("chat", {}).get("id")
    text = message.get("text", "")
    admin_chat_id = os.getenv("TELEGRAM_ADMIN_CHAT_ID", "")

    logger.info(
        "telegram_message",
        extra={
            "chat_id": str(chat_id),
            "text": text[:100] if text else "",
            "edited": edited,
        },
    )

    # Only respond to admin chat for now
    if str(chat_id) != admin_chat_id:
        logger.debug("telegram_ignored_non_admin", extra={"chat_id": str(chat_id)})
        return

    # Command routing — extend as needed
    if text.startswith("/"):
        await _handle_command(chat_id, text)


async def _handle_command(chat_id: int, text: str) -> None:
    """Route bot commands to appropriate handlers."""
    parts = text.split()
    command = parts[0].lower()

    if command == "/start":
        await _send_telegram_message(chat_id, "🤖 AIM Agency Bot online. Use /help for commands.")
    elif command == "/help":
        await _send_telegram_message(
            chat_id,
            "/status — system health\n/help — this message",
        )
    elif command == "/status":
        await _send_telegram_message(chat_id, "✅ AIM Agency operational — iamaim.ru")
    else:
        await _send_telegram_message(chat_id, f"Unknown command: {command}. Use /help.")


async def _handle_callback(callback_query: dict) -> None:
    """Handle inline keyboard callbacks."""
    logger.info("telegram_callback", extra={"callback_query": str(callback_query)[:200]})
    # Future: route callbacks for interactive workflows


async def _send_telegram_message(chat_id: int, text: str) -> None:
    """Send a message via Telegram Bot API."""
    bot_token = os.getenv("TELEGRAM_BOT_TOKEN", "")
    if not bot_token:
        logger.warning("telegram_send_skipped_no_token")
        return

    import httpx

    try:
        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.post(
                f"https://api.telegram.org/bot{bot_token}/sendMessage",
                json={
                    "chat_id": chat_id,
                    "text": text,
                    "parse_mode": "HTML",
                },
            )
            response.raise_for_status()
    except Exception as e:
        logger.error("telegram_send_failed", extra={"error": str(e)})
