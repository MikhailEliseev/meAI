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
import logging
import os
import time
from concurrent.futures import Future
from typing import Optional

import httpx
from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel

from .voice_transcriber import transcribe_voice

logger = logging.getLogger(__name__)

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_ADMIN_CHAT_ID = int(os.getenv("TELEGRAM_ADMIN_CHAT_ID", "0"))


def _get_mode(chat_id: int, lead_id: str | None) -> str:
    """Determine client mode for Telegram messages.

    Admin chat always gets ADMIN mode with full tool access.
    Active leads get ACTIVE, new chats get PRESALE.
    """
    if TELEGRAM_ADMIN_CHAT_ID and chat_id == TELEGRAM_ADMIN_CHAT_ID:
        return "ADMIN"
    if lead_id:
        return "ACTIVE"
    return "PRESALE"

# Telegram API proxy — hosting in NL blocks Telegram IPs on port 443.
# Old OmniRoute server at 193.111.152.14 acts as HTTP forward proxy.
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
_polling_future: Optional[Future] = None
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

        # Detect voice message — download + transcribe before processing
        voice = update.message.get("voice")
        if chat_id and voice and not text:
            file_id = voice.get("file_id")
            if file_id:
                await _send_telegram_message(chat_id, "🎤 Расшифровываю голосовое сообщение...")
                text = transcribe_voice(file_id)
                if not text:
                    await _send_telegram_message(chat_id, "❌ Не удалось расшифровать голосовое сообщение")
                    return {"status": "transcription_failed"}

        # Process message via Hermes AIAgent with session memory (D-17: unified chat)
        if chat_id and text:
            lead_id = _chat_lead_map.get(chat_id)
            mode = _get_mode(chat_id, lead_id)

            reply = _call_hermes_agent(mode=mode, user_message=text, session_id=f"tg:{chat_id}")
            await _send_telegram_message(chat_id, reply)
            return {"status": "replied"}

    return {"status": "ok"}


# ── Helpers ─────────────────────────────────────────────────────────
async def _send_telegram_message(chat_id: int, text: str) -> dict:
    """Send message via Bot API. Async version for webhook."""
    return _send_telegram_message_sync(chat_id, text)


def _send_telegram_message_sync(chat_id: int, text: str) -> dict:
    """Send message via Bot API — synchronous, for use in thread."""
    if not TELEGRAM_BOT_TOKEN:
        logger.error("TELEGRAM_BOT_TOKEN not configured")
        return {"error": "Bot token not configured"}

    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    proxy = _get_proxy_url()
    try:
        with httpx.Client(timeout=10.0, proxy=proxy) as client:
            response = client.post(url, json={
                "chat_id": chat_id,
                "text": text[:4096],
                "parse_mode": "HTML",
            })
            return response.json()
    except Exception as e:
        logger.error(f"sendMessage failed: {e}")
        return {"error": str(e)}


async def _get_updates(offset: int = 0, timeout: int = 30) -> list[dict]:
    """Fetch pending updates from Telegram via long-polling. Async version for webhook."""
    return _get_updates_sync(offset, timeout)


def _get_updates_sync(offset: int = 0, timeout: int = 30) -> list[dict]:
    """Fetch pending updates from Telegram via long-polling — synchronous, for thread."""
    if not TELEGRAM_BOT_TOKEN:
        return []
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/getUpdates"
    proxy = _get_proxy_url()
    try:
        with httpx.Client(timeout=float(timeout + 10), proxy=proxy) as client:
            response = client.post(url, json={
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


def _process_update_sync(message_data: dict, chat_id: int, text: str):
    """Process update via Hermes AIAgent — session, tools, memory. Polling thread."""
    lead_id = _chat_lead_map.get(chat_id)
    mode = _get_mode(chat_id, lead_id)

    logger.info(f"Processing tg message: chat_id={chat_id} mode={mode} text={text[:80]}")
    reply = _call_hermes_agent(mode=mode, user_message=text, session_id=f"tg:{chat_id}")
    _send_telegram_message_sync(chat_id, reply)


def _call_hermes_agent(mode: str, user_message: str, session_id: str) -> str:
    """Process message via Hermes AIAgent — full session, tools, SOUL.md identity.

    Uses AIAgent (not raw OmniRoute) so each Telegram chat gets:
    - Session memory (SQLite persistence per chat_id)
    - Tool access (run_seo_audit, collect_contact, etc.)
    - Full SOUL.md identity via load_soul_identity
    - Consistent behavior with web chat
    """
    from .agent_wrapper import run_agent_sync

    result = run_agent_sync(
        message=user_message,
        session_id=session_id,
        mode=mode,
    )
    reply = result.get("reply", "")
    if isinstance(reply, dict):
        reply = reply.get("response", reply.get("content", str(reply)))
    return str(reply)


def _polling_loop_sync():
    """Background thread: poll Telegram for updates via getUpdates.

    Runs in a separate OS thread via run_in_executor to avoid
    httpx proxy connections blocking the uvicorn event loop.

    Uses long-polling (timeout=30s) to reduce request count.
    Reconnects on error with 5s backoff.
    """
    global _last_update_id, _polling_stop

    logger.info("Telegram polling started (getUpdates, sync thread)")
    consecutive_errors = 0

    while not _polling_stop:
        try:
            updates = _get_updates_sync(offset=_last_update_id + 1, timeout=30)
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

                # Detect voice message — download + transcribe before processing
                voice = message.get("voice")
                if chat_id and voice and not text:
                    file_id = voice.get("file_id")
                    if file_id:
                        _send_telegram_message_sync(chat_id, "🎤 Расшифровываю голосовое сообщение...")
                        text = transcribe_voice(file_id)
                        if not text:
                            _send_telegram_message_sync(chat_id, "❌ Не удалось расшифровать голосовое сообщение")
                            continue

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
                                _send_telegram_message_sync(
                                    chat_id,
                                    "✅ Ваш чат привязан к аккаунту AIM. Оператор готов ответить на ваши вопросы."
                                )
                                continue

                # Process through Hermes Operator
                _process_update_sync(message, chat_id, text)

        except Exception as e:
            consecutive_errors += 1
            backoff = min(5 * consecutive_errors, 60)
            logger.error(f"Polling error (attempt {consecutive_errors}, backoff {backoff}s): {e}")
            time.sleep(backoff)

    logger.info("Telegram polling stopped")


def start_polling():
    """Start Telegram polling in a separate thread via run_in_executor.

    Called from the first /health request AFTER uvicorn has bound to port 8000.
    Using run_in_executor (separate OS thread) guarantees Telegram API calls
    never block the uvicorn event loop.
    """
    global _polling_future, _polling_stop
    if _polling_future is not None and not _polling_future.done():
        logger.warning("Polling already running, skipping start")
        return
    _polling_stop = False
    loop = asyncio.get_running_loop()
    _polling_future = loop.run_in_executor(None, _polling_loop_sync)


async def stop_polling():
    """Stop the Telegram polling thread. Called from on_event("shutdown")."""
    global _polling_stop, _polling_future
    _polling_stop = True
    if _polling_future:
        _polling_future.cancel()  # no-op for running threads, but marks cancelled
        try:
            await asyncio.get_running_loop().run_in_executor(
                None, lambda: _polling_future.result(timeout=5) if not _polling_future.done() else None
            )
        except Exception:
            pass
        _polling_future = None
