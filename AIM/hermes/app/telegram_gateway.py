"""Telegram Gateway — Bot API webhook (incoming) + Telethon (outgoing via tools).

Per D-16: Hybrid architecture:
- Bot API webhook: incoming messages FROM clients
- Telethon user-client: outgoing messages AS Mikhail, channel search, monitoring

Per D-17: Unified chat — one Operator serves both web chat and Telegram.
Messages from Telegram flow through the same Hermes AIAgent as web chat.

Per D-18: Session binding via tg:// deep link.
Client clicks button in web chat → opens Telegram with deep link containing
web_session_id → bot receives /start command with web_session_id parameter
→ bot links Telegram chat_id to AIM lead dossier.
"""

import hashlib
import hmac
import logging
import os
from typing import Optional

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel

logger = logging.getLogger(__name__)

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")

router = APIRouter(prefix="/telegram", tags=["telegram"])

# In-memory session binding store (move to DB later)
# Maps web_session_id -> AIM lead_id
_session_bindings: dict[str, str] = {}

# Maps telegram chat_id -> AIM lead_id
_chat_lead_map: dict[int, str] = {}


# ── Models ──────────────────────────────────────────────────────────
class TelegramUpdate(BaseModel):
    update_id: int
    message: Optional[dict] = None
    callback_query: Optional[dict] = None


class DeepLinkBindRequest(BaseModel):
    web_session_id: str
    lead_id: str


# ── Deep Link Binding ───────────────────────────────────────────────
# D-18: tg:// deep link from website binds Telegram chat to AIM lead

@router.post("/bind-session")
async def bind_session(body: DeepLinkBindRequest):
    """Called by Next.js when user clicks 'Open in Telegram' button.

    Creates a pending binding: when the Telegram bot receives a /start
    command with matching web_session_id, it links the Telegram chat_id
    to the AIM lead_id.
    """
    _session_bindings[body.web_session_id] = body.lead_id
    logger.info(f"Session binding created: {body.web_session_id} -> {body.lead_id}")
    return {"status": "bound", "web_session_id": body.web_session_id}


# ── Webhook ─────────────────────────────────────────────────────────
# D-16: Bot API webhook receives incoming messages from clients

@router.post("/webhook")
async def telegram_webhook(request: Request):
    """Telegram Bot API webhook endpoint.

    Receives incoming messages from clients via Telegram Bot API.
    Routes them through the same Hermes AIAgent as web chat (D-17).

    Webhook URL: https://iamaim.ru/telegram/webhook
    Set via: curl -X POST https://api.telegram.org/bot<TOKEN>/setWebhook
             -d url=https://iamaim.ru/telegram/webhook
    """
    try:
        body = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON")

    update = TelegramUpdate(**body)

    # Handle /start command with deep link (D-18)
    if update.message:
        text = update.message.get("text", "")
        chat_id = update.message.get("chat", {}).get("id")

        if text.startswith("/start ") and chat_id:
            # Extract web_session_id from deep link
            # Format: /start bind_<web_session_id>
            parts = text.split()
            if len(parts) > 1:
                param = parts[1]
                if param.startswith("bind_"):
                    web_session_id = param[5:]  # Remove "bind_" prefix
                    lead_id = _session_bindings.pop(web_session_id, None)
                    if lead_id:
                        _chat_lead_map[chat_id] = lead_id
                        logger.info(f"Session bound: chat_id={chat_id} -> lead_id={lead_id}")
                        await _send_telegram_message(
                            chat_id,
                            "✅ Ваш чат привязан к аккаунту AIM. Оператор готов ответить на ваши вопросы."
                        )
                        return {"status": "bound", "lead_id": lead_id}

        # Process message through Hermes Operator (D-17: unified chat)
        if chat_id and text:
            from .agent_wrapper import run_agent

            lead_id = _chat_lead_map.get(chat_id)
            mode = "ACTIVE" if lead_id else "PRESALE"

            # Route through the same Operator that handles web chat
            result = await run_agent(
                message=text,
                session_id=f"tg_{chat_id}",
                mode=mode,
            )

            reply = result.get("reply", "")
            if isinstance(reply, dict):
                reply = reply.get("response", reply.get("content", str(reply)))

            await _send_telegram_message(chat_id, str(reply))
            return {"status": "replied"}

    return {"status": "ok"}


# ── Helpers ─────────────────────────────────────────────────────────
async def _send_telegram_message(chat_id: int, text: str) -> dict:
    """Send message via Bot API."""
    import httpx

    if not TELEGRAM_BOT_TOKEN:
        logger.error("TELEGRAM_BOT_TOKEN not configured")
        return {"error": "Bot token not configured"}

    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    async with httpx.AsyncClient(timeout=10.0) as client:
        response = await client.post(url, json={
            "chat_id": chat_id,
            "text": text[:4096],  # Telegram message limit
            "parse_mode": "HTML",
        })
        return response.json()
