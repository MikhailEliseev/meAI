"""Telethon MCP tools for Hermes — outgoing messages + channel search.

Per D-16: Telethon user-client for outgoing messages and channel search.
Per D-19: Telethon integrated as MCP tools in Hermes.
These tools are registered in the Hermes internal tool registry,
NOT as separate services.

Session file: /opt/data/sessions/telethon.session (persisted via Docker volume)
First-time authentication: interactive code entry required.
"""

import json
import logging
import os

from tools.registry import registry

logger = logging.getLogger(__name__)

TELEGRAM_API_ID = int(os.getenv("TELEGRAM_API_ID", "0"))
TELEGRAM_API_HASH = os.getenv("TELEGRAM_API_HASH", "")
TELEGRAM_SESSION_PATH = os.getenv(
    "TELEGRAM_SESSION_PATH", "/opt/data/sessions/telethon.session"
)

# Lazy-initialized Telethon client
_client = None


async def _get_client():
    """Get or create Telethon client. Lazy init to avoid blocking startup."""
    global _client
    if _client is not None:
        return _client

    if not TELEGRAM_API_ID or not TELEGRAM_API_HASH:
        raise RuntimeError("TELEGRAM_API_ID and TELEGRAM_API_HASH must be set")

    from telethon import TelegramClient

    _client = TelegramClient(TELEGRAM_SESSION_PATH, TELEGRAM_API_ID, TELEGRAM_API_HASH)
    await _client.start()
    logger.info("Telethon client started")
    return _client


# ── Tool: search_chats ──────────────────────────────────────────────

async def handle_search_chats(query: str, limit: int = 10, **kwargs) -> str:
    """Search Telegram chats and channels by name."""
    try:
        client = await _get_client()
        results = []
        async for dialog in client.iter_dialogs():
            if query.lower() in dialog.name.lower():
                results.append({
                    "name": dialog.name,
                    "id": dialog.id,
                    "type": str(dialog.entity.__class__.__name__),
                    "unread_count": dialog.unread_count,
                })
                if len(results) >= limit:
                    break
        if not results:
            return json.dumps({"message": f"No chats found matching '{query}'"})
        return json.dumps(results, ensure_ascii=False, indent=2)
    except Exception as e:
        return json.dumps({"error": "Chat search failed", "detail": str(e)})


registry.register(
    name="search_telegram_chats",
    toolset="aim-operations",
    schema={
            "name": "search_telegram_chats",
            "description": "Search Telegram chats and channels by name. Useful for finding client conversations, monitoring industry channels, and checking partner activity.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Search query for chat/channel name"},
                    "limit": {"type": "integer", "description": "Max results (default: 10)"},
                },
                "required": ["query"],
            },
        },
    handler=handle_search_chats,
    is_async=True,
    description="Search Telegram chats and channels by name",
)


# ── Tool: send_message_as_user ──────────────────────────────────────

async def handle_send_message_as_user(peer: str, message: str, **kwargs) -> str:
    """Send a Telegram message as the user (Mikhail), not the bot.

    Args:
        peer: Username (@example), phone number, or chat ID
        message: Text to send
    """
    try:
        client = await _get_client()
        await client.send_message(peer, message)
        return json.dumps({"status": "sent", "peer": peer})
    except Exception as e:
        return json.dumps({"error": "Failed to send message", "detail": str(e)})


registry.register(
    name="send_telegram_message",
    toolset="aim-operations",
    schema={
            "name": "send_telegram_message",
            "description": "Send a Telegram message as Mikhail (the agency founder). Use this to personally reach out to clients, partners, or team members. Requires ADMIN mode.",
            "parameters": {
                "type": "object",
                "properties": {
                    "peer": {"type": "string", "description": "Recipient: @username, phone, or chat ID"},
                    "message": {"type": "string", "description": "Message text to send"},
                },
                "required": ["peer", "message"],
            },
        },
    handler=handle_send_message_as_user,
    is_async=True,
    description="Send Telegram message as Mikhail (user account, not bot)",
)
