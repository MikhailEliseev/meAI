"""Direct OmniRoute client — bypasses AIAgent streaming for fast responses.

AIAgent hardcodes `stream: True` in _call_chat_completions() which cannot
be overridden via request_overrides.  OmniRoute's DeepSeek V4 provider
times out on streamed responses (>30s for first token).  Non-streaming
requests complete in <1s.

This module provides a direct OpenAI SDK wrapper used by the Telegram
gateway for fast, reliable responses.
"""

import logging
import os
from typing import Optional

from openai import OpenAI

logger = logging.getLogger(__name__)

OMNIROUTE_URL = os.getenv("OMNIROUTE_URL", "https://api.deepseek.com")
OMNIROUTE_AUTH = os.getenv("OMNIROUTE_AUTH", "sk-placeholder")
DEFAULT_MODEL = os.getenv("HERMES_MODEL", "deepseek-chat")

_client: Optional[OpenAI] = None


def _get_client() -> OpenAI:
    global _client
    if _client is None:
        _client = OpenAI(
            base_url=OMNIROUTE_URL,
            api_key=OMNIROUTE_AUTH,
            max_retries=1,
            timeout=60.0,
        )
    return _client


def chat(messages: list[dict], model: str | None = None) -> str:
    """Send chat completion to OmniRoute and return text response.

    Non-streaming, fast, reliable.  Returns the assistant's text or
    a fallback error message.
    """
    client = _get_client()
    try:
        response = client.chat.completions.create(
            model=model or DEFAULT_MODEL,
            messages=messages,
            max_tokens=2048,
            stream=False,
            extra_body={"thinking": {"type": "disabled"}},
        )
        content = response.choices[0].message.content
        return content.strip() if content else "…"
    except Exception as e:
        logger.exception("Direct OmniRoute call failed")
        return f"Извините, произошла ошибка. Попробуйте позже. [{type(e).__name__}]"
