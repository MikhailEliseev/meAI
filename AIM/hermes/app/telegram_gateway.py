"""Telegram Gateway — Bot API webhook (incoming) + getUpdates polling (fallback) + Telethon (outgoing via tools).

Per D-16: Hybrid architecture:
- getUpdates polling: incoming messages FROM clients (primary — server can't receive inbound 443 from Telegram)
- Bot API webhook: fallback when direct connectivity works
- Telethon user-client: outgoing messages AS Mikhail, channel search, monitoring

Per D-17: Unified chat — one Operator serves both web chat and Telegram.
Messages from Telegram flow through the same Hermes AIAgent as web chat.

Per D-18: Session binding via tg:// deep link.
Client clicks button in web chat → opens Telegram with deep link containing
web_session_id → bot receives /start command with web_session_id parameter
→ bot links Telegram chat_id to AIM lead dossier.
"""

import asyncio
import hashlib
import hmac
import logging
import os
from typing import Optional

import httpx
from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel

logger = logging.getLogger(__name__)

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")

# Telegram proxy — separate from AI gateway (OmniRoute /v1 only does LLM API, not proxy)
# Old OmniRoute at 193.111.152.14:7451 still acts as HTTP proxy for outbound 443
# Hosting blocks direct 443 to Telegram IPs, so we proxy via this
TELEGRAM_PROXY_URL = os.getenv("TELEGRAM_PROXY_URL", "http://193.111.152.14:7451")
TELEGRAM_PROXY_AUTH = os.getenv("TELEGRAM_PROXY_AUTH", "U9pjtK:hxtlqz")


def _get_proxy_url() -> str | None:
    """Build Telegram proxy URL. Returns None if not configured."""
    if TELEGRAM_PROXY_URL and TELEGRAM_PROXY_AUTH:
        from urllib.parse import urlparse
        parsed = urlparse(TELEGRAM_PROXY_URL)
        host = parsed.netloc or parsed.path
        return f"http://{TELEGRAM_PROXY_AUTH}@{host}"
    return None

router = APIRouter(prefix="/telegram", tags=["telegram"])

# In-memory session binding store (move to DB later)
# Maps web_session_id -> AIM lead_id
_session_bindings: dict[str, str] = {}

# Maps telegram chat_id -> AIM lead_id
_chat_lead_map: dict[int, str] = {}

# Polling control
_polling_task: Optional[asyncio.Task] = None
_polling_stop = False
_last_update_id: int = 0


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
    """Send message via Bot API (uses OmniRoute as HTTPS proxy)."""
    if not TELEGRAM_BOT_TOKEN:
        logger.error("TELEGRAM_BOT_TOKEN not configured")
        return {"error": "Bot token not configured"}

    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    proxy = _get_proxy_url()
    async with httpx.AsyncClient(timeout=10.0, proxy=proxy) as client:
        response = await client.post(url, json={
            "chat_id": chat_id,
            "text": text[:4096],  # Telegram message limit
            "parse_mode": "HTML",
        })
        return response.json()


async def _get_updates(offset: int = 0, timeout: int = 30) -> list[dict]:
    """Fetch pending updates from Telegram via long-polling (uses OmniRoute as HTTPS proxy)."""
    if not TELEGRAM_BOT_TOKEN:
        return []

    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/getUpdates"
    proxy = _get_proxy_url()
    async with httpx.AsyncClient(timeout=float(timeout + 10), proxy=proxy) as client:
        try:
            response = await client.post(url, json={
                "offset": offset,
                "timeout": timeout,
                "allowed_updates": ["message", "callback_query"],
            })
            data = response.json()
            if data.get("ok"):
                return data.get("result", [])
            logger.error(f"getUpdates error: {data}")
            return []
        except Exception as e:
            logger.error(f"getUpdates failed: {e}")
            return []


async def _process_update(message_data: dict, chat_id: int, text: str):
    """Process a single incoming message through Hermes Operator (D-17)."""
    from .agent_wrapper import run_agent

    lead_id = _chat_lead_map.get(chat_id)
    mode = "ACTIVE" if lead_id else "PRESALE"

    result = await run_agent(
        message=text,
        session_id=f"tg_{chat_id}",
        mode=mode,
    )

    reply = result.get("reply", "")
    if isinstance(reply, dict):
        reply = reply.get("response", reply.get("content", str(reply)))

    await _send_telegram_message(chat_id, str(reply))


async def _polling_loop():
    """Background task: poll Telegram for updates via getUpdates.

    Uses long-polling (timeout=30s) to reduce request count.
    Reconnects on error with 5s backoff.
    """
    global _last_update_id, _polling_stop

    logger.info("Telegram polling started (getUpdates via proxy)")
    consecutive_errors = 0

    while not _polling_stop:
        try:
            updates = await _get_updates(offset=_last_update_id + 1, timeout=30)
            consecutive_errors = 0

            for update in updates:
                update_id = update.get("update_id", 0)
                if update_id > _last_update_id:
                    _last_update_id = update_id

                message = update.get("message")
                if not message:
                    continue

                text = message.get("text", "")
                chat = message.get("chat", {})
                chat_id = chat.get("id")

                if not chat_id or not text:
                    continue

                # Handle /start deep link binding (D-18)
                if text.startswith("/start ") and chat_id:
                    parts = text.split()
                    if len(parts) > 1:
                        param = parts[1]
                        if param.startswith("bind_"):
                            web_session_id = param[5:]
                            lead_id = _session_bindings.pop(web_session_id, None)
                            if lead_id:
                                _chat_lead_map[chat_id] = lead_id
                                logger.info(f"Session bound: chat_id={chat_id} -> lead_id={lead_id}")
                                await _send_telegram_message(
                                    chat_id,
                                    "✅ Ваш чат привязан к аккаунту AIM. Оператор готов ответить на ваши вопросы."
                                )
                                continue

                # Process through Hermes Operator
                await _process_update(message, chat_id, text)

        except Exception as e:
            consecutive_errors += 1
            backoff = min(5 * consecutive_errors, 60)
            logger.error(f"Polling error (attempt {consecutive_errors}, backoff {backoff}s): {e}")
            await asyncio.sleep(backoff)

    logger.info("Telegram polling stopped")


def start_polling():
    """Start the Telegram polling background task. Called from lifespan startup."""
    global _polling_task, _polling_stop
    _polling_stop = False
    _polling_task = asyncio.create_task(_polling_loop())


async def stop_polling():
    """Stop the Telegram polling background task. Called from lifespan shutdown."""
    global _polling_stop, _polling_task
    _polling_stop = True
    if _polling_task:
        _polling_task.cancel()
        try:
            await _polling_task
        except asyncio.CancelledError:
            pass
        _polling_task = None
