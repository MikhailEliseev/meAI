"""
send_telegram_file — Hermes tool: send files (images, documents) to Telegram chats.

Uses Bot API sendDocument/sendPhoto with multipart/form-data.
Files are sent from disk (e.g., screenshots from browser_screenshot).

Part of toolset "aim-operations". Requires TELEGRAM_BOT_TOKEN in env.
"""

import json
import logging
import os
import mimetypes
from pathlib import Path

import httpx
from tools.registry import registry

logger = logging.getLogger(__name__)

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_ADMIN_CHAT_ID = int(os.getenv("TELEGRAM_ADMIN_CHAT_ID", "0"))
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


def _guess_file_type(file_path: str) -> str:
    """Guess whether to use sendPhoto or sendDocument based on extension."""
    mime, _ = mimetypes.guess_type(file_path)
    if mime and mime.startswith("image/"):
        return "photo"
    return "document"


def _send_file_sync(chat_id: int, file_path: str, caption: str = "") -> dict:
    """Send a file via Telegram Bot API — synchronous with retry.

    Uses sendPhoto for images, sendDocument for everything else.
    Routes through the OmniRoute proxy (same as telegram_gateway).
    """
    if not TELEGRAM_BOT_TOKEN:
        return {"error": "TELEGRAM_BOT_TOKEN not configured"}

    path = Path(file_path)
    if not path.exists():
        return {"error": f"File not found: {file_path}"}
    if not path.is_file():
        return {"error": f"Not a file: {file_path}"}

    file_type = _guess_file_type(file_path)
    if file_type == "photo":
        method = "sendPhoto"
        file_param = "photo"
    else:
        method = "sendDocument"
        file_param = "document"

    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/{method}"
    proxy = _get_proxy_url()

    file_size = path.stat().st_size
    logger.info("send_telegram_file: %s -> chat %d (%s, %d bytes)",
                path.name, chat_id, method, file_size)

    last_error = None
    for attempt in range(3):
        try:
            with open(file_path, "rb") as f:
                files = {file_param: (path.name, f, mimetypes.guess_type(file_path)[0] or "application/octet-stream")}
                data = {"chat_id": str(chat_id)}
                if caption:
                    data["caption"] = caption

                with httpx.Client(timeout=30.0, proxy=proxy) as client:
                    resp = client.post(url, data=data, files=files)

            if resp.status_code == 200:
                result = resp.json()
                if result.get("ok"):
                    logger.info("send_telegram_file: sent %s to chat %d", path.name, chat_id)
                    return {
                        "status": "sent",
                        "chat_id": chat_id,
                        "file_name": path.name,
                        "file_size_bytes": file_size,
                        "method": method,
                        "message_id": result.get("result", {}).get("message_id"),
                    }
                else:
                    last_error = f"API error: {result.get('description', 'unknown')}"
            else:
                last_error = f"HTTP {resp.status_code}: {resp.text[:300]}"

        except Exception as e:
            last_error = str(e)

        if attempt < 2:
            backoff = (attempt + 1) * 2
            logger.warning("send_telegram_file attempt %d failed: %s, retrying in %ds",
                           attempt + 1, last_error, backoff)
            import time
            time.sleep(backoff)

    logger.error("send_telegram_file failed after 3 attempts: %s", last_error)
    return {"error": f"Failed after 3 attempts: {last_error}"}


async def handle_send_telegram_file(
    file_path: str = None,
    chat_id: int = None,
    caption: str = None,
    **kwargs,
) -> str:
    """Send a file to a Telegram chat via Bot API.

    Args:
        file_path: Absolute path to the file on disk (e.g., /tmp/screenshot_123.png)
        chat_id: Telegram chat ID to send to. Defaults to TELEGRAM_ADMIN_CHAT_ID
                 (Mikhail) if not specified. Use this to send files to clients.
        caption: Optional caption text for the file.

    Returns:
        JSON with status, chat_id, file_name, message_id, or error.
    """
    # Hermes-agent may pass all args as a single dict
    if isinstance(file_path, dict):
        d = file_path
        file_path = d.get("file_path", "")
        chat_id = d.get("chat_id", chat_id)
        caption = d.get("caption", caption)

    if not file_path or not isinstance(file_path, str):
        return json.dumps({"error": "file_path is required (string)"})

    # Resolve chat_id: explicit param > telegram_context > admin env
    target_chat_id = chat_id
    if not target_chat_id:
        try:
            from app.telegram_context import get_current_chat_id
            target_chat_id = get_current_chat_id()
        except ImportError:
            pass
    if not target_chat_id:
        target_chat_id = TELEGRAM_ADMIN_CHAT_ID
    if not target_chat_id:
        return json.dumps({"error": "No chat_id provided and TELEGRAM_ADMIN_CHAT_ID not configured"})

    # Ensure file_path is within allowed directories
    allowed_prefixes = ["/tmp/", "/opt/hermes/", "/opt/data/"]
    if not any(file_path.startswith(p) for p in allowed_prefixes):
        return json.dumps({
            "error": f"file_path must be in: {', '.join(allowed_prefixes)}",
            "requested": file_path,
        })

    # Send synchronously (file I/O + HTTP) — run in executor to avoid blocking
    import asyncio
    loop = asyncio.get_running_loop()
    result = await loop.run_in_executor(
        None,
        lambda: _send_file_sync(int(target_chat_id), file_path, caption or ""),
    )

    return json.dumps(result, ensure_ascii=False)


# ── Register tool ───────────────────────────────────────────────────

registry.register(
    name="send_telegram_file",
    toolset="aim-operations",
    schema={
        "type": "function",
        "function": {
            "name": "send_telegram_file",
            "description": (
                "Send a file (image, document, screenshot) to a Telegram chat. "
                "Uses Bot API sendDocument/sendPhoto. "
                "Use after browser_screenshot to send the screenshot to the user. "
                "Defaults to sending to Mikhail (admin) if no chat_id specified."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "file_path": {
                        "type": "string",
                        "description": "Absolute path to the file on disk (e.g., /tmp/screenshot_123.png)",
                    },
                    "chat_id": {
                        "type": "integer",
                        "description": "Telegram chat ID to send to. Defaults to admin chat if omitted.",
                    },
                    "caption": {
                        "type": "string",
                        "description": "Optional caption text for the file.",
                    },
                },
                "required": ["file_path"],
            },
        },
    },
    handler=handle_send_telegram_file,
    is_async=True,
    description="Send files (screenshots, documents) to Telegram chats via Bot API",
)
