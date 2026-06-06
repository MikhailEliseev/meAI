"""Telegram channel monitor — wraps existing telegram_gateway.py.

When the SalesAdminMagister is active, incoming Telegram messages are routed
through EventBus instead of directly to Hermes. The magister decides whether
to auto-reply (via Hermes) or escalate to a human manager.

Part of Phase 13: AI Sales Admin Agent.
"""

import asyncio
import logging
import os
from datetime import datetime, timezone

import httpx

from src.aim.subagents.sales.channel_monitor_base import BaseChannelMonitor, ChannelMessage

logger = logging.getLogger(__name__)

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_PROXY_URL = os.getenv("TELEGRAM_PROXY_URL", "http://193.111.152.14:7451")
TELEGRAM_PROXY_AUTH = os.getenv("TELEGRAM_PROXY_AUTH", "U9pjtK:hxtlqz")


def _build_proxy_url() -> str | None:
    if TELEGRAM_PROXY_URL and TELEGRAM_PROXY_AUTH:
        from urllib.parse import urlparse
        parsed = urlparse(TELEGRAM_PROXY_URL)
        host = parsed.netloc or parsed.path
        return f"http://{TELEGRAM_PROXY_AUTH}@{host}"
    return None


class TelegramMonitor(BaseChannelMonitor):
    """Monitors Telegram for incoming messages and delivers responses.

    Wraps the existing telegram_gateway.py Bot API helpers.
    Does NOT start its own polling loop — it hooks into the existing
    gateway's message processing.
    """

    def __init__(self, event_bus=None) -> None:
        super().__init__(channel="telegram", event_bus=event_bus)
        self._last_update_id: int = 0
        self._poll_task: asyncio.Task | None = None

    # ── Lifecycle ──────────────────────────────────────────────────────────

    async def start(self) -> None:
        """Start monitoring Telegram via long-polling."""
        if self._running:
            return
        self._running = True
        logger.info("TelegramMonitor started")

    async def stop(self) -> None:
        """Stop monitoring."""
        self._running = False
        if self._poll_task:
            self._poll_task.cancel()
            self._poll_task = None
        logger.info("TelegramMonitor stopped")

    # ── Message delivery ───────────────────────────────────────────────────

    async def send_message(self, channel_user_id: str, text: str) -> bool:
        """Send a message to a Telegram chat.

        Args:
            channel_user_id: Telegram chat_id as string.
            text: Message text (max 4096 chars for Telegram).

        Returns:
            True if the message was sent successfully.
        """
        if not TELEGRAM_BOT_TOKEN:
            logger.error("TELEGRAM_BOT_TOKEN not configured")
            return False

        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        proxy = _build_proxy_url()

        try:
            async with httpx.AsyncClient(timeout=10.0, proxy=proxy) as client:
                response = await client.post(url, json={
                    "chat_id": int(channel_user_id),
                    "text": text[:4096],
                    "parse_mode": "HTML",
                })
                data = response.json()
                ok = data.get("ok", False)
                if not ok:
                    logger.error(f"sendMessage failed: {data}")
                return ok
        except Exception as e:
            logger.error(f"sendMessage error: {e}")
            return False

    # ── Incoming message processing ────────────────────────────────────────

    async def handle_incoming(
        self,
        chat_id: int,
        text: str,
        username: str | None = None,
        message_id: int = 0,
    ) -> str | None:
        """Process an incoming Telegram message.

        Called by telegram_gateway when a non-admin, non-binding message arrives.
        Publishes to EventBus so SalesAdminMagister can decide what to do.

        Returns the EventBus event ID, or None if no EventBus is configured.
        """
        message = ChannelMessage(
            channel="telegram",
            channel_user_id=str(chat_id),
            text=text,
            message_id=str(message_id),
            timestamp=datetime.now(timezone.utc),
            metadata={
                "chat_id": chat_id,
                "username": username,
                "source": "telegram",
            },
        )
        return await self.publish_incoming(message)
