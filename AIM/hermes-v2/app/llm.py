"""LLM-клиент Гермеса v2 — deepseek-chat через Z.AI-шлюз.

Сырой openai SDK (нативный streaming). Z.AI-шлюз OpenAI-совместимый.
Системный промпт подставляется автоматически как messages[0] (DIALOG-03).
"""
import logging

import openai

from app.config import LLM_MODEL, OMNIROUTE_AUTH, OMNIROUTE_URL
from app.prompts.dialogue import SYSTEM_PROMPT

logger = logging.getLogger(__name__)

# Ленивая инициализация: client создаётся при первом вызове, когда env уже
# загружен. На import OMNIROUTE_AUTH может быть пустым (тесты) — тогда
# client всё равно создастся с dummy, реальный вызов вскроет проблему.
_client: openai.AsyncClient | None = None


def get_client() -> openai.AsyncClient:
    """Возвращает (или создаёт при первом обращении) openai.AsyncClient."""
    global _client
    if _client is None:
        # dummy-ключ если env пуст — client создастся, ошибка всплывёт
        # при реальном вызове с понятным сообщением.
        key = OMNIROUTE_AUTH or "dummy-not-set"
        _client = openai.AsyncClient(base_url=OMNIROUTE_URL, api_key=key)
        logger.info("LLM client init: base_url=%s model=%s", OMNIROUTE_URL, LLM_MODEL)
    return _client


async def stream_chat(history: list[dict]):
    """Стримит токены ответа модели.

    Args:
        history: [{"role":"user"/"assistant","content":"..."}, ...]
                 БЕЗ системного промпта — он подставляется здесь (DIALOG-03).

    Yields:
        str — токены (delta.content). None/empty delta пропускаются.
    """
    messages = [{"role": "system", "content": SYSTEM_PROMPT}] + history
    logger.info("stream_chat: model=%s messages=%d", LLM_MODEL, len(messages))

    client = get_client()
    stream = await client.chat.completions.create(
        model=LLM_MODEL,
        messages=messages,
        stream=True,
    )
    async for chunk in stream:
        delta = chunk.choices[0].delta.content
        if delta:
            yield delta
