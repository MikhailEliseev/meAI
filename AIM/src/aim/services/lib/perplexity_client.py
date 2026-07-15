"""Perplexity API client for aim-app.

Uses Perplexity's sonar model with built-in web search for market
research and competitor discovery. Mirrors the pattern from
hermes-v2/app/lib/perplexity.py.
"""

import logging
import os

import httpx

logger = logging.getLogger(__name__)

PERPLEXITY_API_KEY = os.getenv("PERPLEXITY_API_KEY", "")
PERPLEXITY_BASE_URL = "https://api.perplexity.ai"
PERPLEXITY_MODEL = os.getenv("PERPLEXITY_MODEL", "sonar")
PERPLEXITY_TIMEOUT = 60.0


async def perplexity_chat(
    messages: list[dict],
    model: str | None = None,
    temperature: float = 0.2,
) -> str:
    """Send a chat completion request to Perplexity.

    Args:
        messages: List of {"role": "user"|"system", "content": "..."} dicts.
        model: Override model (default: sonar).
        temperature: Sampling temperature.

    Returns:
        The response content string.

    Raises:
        RuntimeError: If PERPLEXITY_API_KEY is not configured.
        httpx.HTTPStatusError: On API errors.
    """
    if not PERPLEXITY_API_KEY:
        raise RuntimeError("PERPLEXITY_API_KEY not configured in aim-app")

    used_model = model or PERPLEXITY_MODEL

    async with httpx.AsyncClient(timeout=PERPLEXITY_TIMEOUT) as client:
        resp = await client.post(
            f"{PERPLEXITY_BASE_URL}/chat/completions",
            headers={
                "Authorization": f"Bearer {PERPLEXITY_API_KEY}",
                "Content-Type": "application/json",
            },
            json={
                "model": used_model,
                "messages": messages,
                "temperature": temperature,
            },
        )
        resp.raise_for_status()
        data = resp.json()

    content = data["choices"][0]["message"]["content"]
    logger.debug("perplexity_chat: model=%s response_len=%d", used_model, len(content))
    return content


def is_configured() -> bool:
    """Check if Perplexity API key is available."""
    return bool(PERPLEXITY_API_KEY)
