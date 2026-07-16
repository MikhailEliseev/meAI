"""Общий Perplexity-клиент (замена дублирования в 4 тулах старого hermes).

Perplexity — OpenAI-совместимый. base_url: https://api.perplexity.ai.
Модель по умолчанию: sonar-pro.
"""
import logging
import os

from openai import AsyncOpenAI

logger = logging.getLogger(__name__)

PERPLEXITY_API_KEY = os.getenv("PERPLEXITY_API_KEY", "").strip()
PERPLEXITY_BASE_URL = "https://api.perplexity.ai"
PERPLEXITY_MODEL = "sonar-pro"

USE_PERPLEXITY = bool(PERPLEXITY_API_KEY)


def get_client() -> AsyncOpenAI | None:
    """Возвращает Perplexity-клиент или None если ключ не задан."""
    if not USE_PERPLEXITY:
        return None
    return AsyncOpenAI(api_key=PERPLEXITY_API_KEY, base_url=PERPLEXITY_BASE_URL)


async def perplexity_chat(messages: list[dict], model: str | None = None) -> str:
    """Вызывает Perplexity chat completion, возвращает текст ответа.

    Args:
        messages: [{"role":"system"/"user","content":"..."}]
        model: переопределение модели (sonar-pro, sonar, sonar-reasoning)

    Raises:
        RuntimeError: если PERPLEXITY_API_KEY не задан или API-ошибка.
    """
    if not USE_PERPLEXITY:
        raise RuntimeError("PERPLEXITY_API_KEY not configured")
    client = get_client()
    response = await client.chat.completions.create(
        model=model or PERPLEXITY_MODEL,
        messages=messages,
    )
    return response.choices[0].message.content or ""
