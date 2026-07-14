"""LLM-клиент Гермеса v2 — glm-5.2 через Z.AI-шлюз.

Сырой openai SDK (нативный streaming + tool-calling). Z.AI-шлюз OpenAI-совместимый.
Системный промпт подставляется автоматически как messages[0] (DIALOG-03).
"""
import json
import logging

import openai

from app.config import LLM_MODEL, OMNIROUTE_AUTH, OMNIROUTE_URL
from app.prompts.dialogue import SYSTEM_PROMPT
from app.tools.registry import execute, get_openai_tools

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


async def chat_with_tools(history: list[dict]):
    """Диалог с tool-calling. Возвращает генератор событий для SSE.

    События (кортежи):
        ("text", str)            — токен текста
        ("tool_start", name, args) — начало вызова тулза
        ("tool_result", name, result) — результат тулза
        ("finish",)              — конец диалога

    Цикл:
    1. non-streaming вызов с tools= для определения хочет ли модель тул.
    2. Если tool_calls → выполняем → добавляем tool message → повтор.
    3. Если нет tool_calls → streaming финального ответа.
    """
    messages = [{"role": "system", "content": SYSTEM_PROMPT}] + list(history)
    tools = get_openai_tools()
    client = get_client()

    for turn in range(5):  # максимум 5 раундов tool-calling
        logger.info("chat_with_tools turn=%d tools=%d msgs=%d", turn, len(tools), len(messages))

        if tools:
            # non-streaming для разбора tool_calls
            response = await client.chat.completions.create(
                model=LLM_MODEL, messages=messages, tools=tools, stream=False,
            )
            msg = response.choices[0].message
        else:
            # без тулов — сразу streaming
            msg = None

        if msg and msg.tool_calls:
            # Модель хочет вызвать тулзы
            messages.append({
                "role": "assistant",
                "content": msg.content or "",
                "tool_calls": [
                    {"id": tc.id, "type": "function",
                     "function": {"name": tc.function.name, "arguments": tc.function.arguments}}
                    for tc in msg.tool_calls
                ],
            })
            for tc in msg.tool_calls:
                tool_name = tc.function.name
                try:
                    tool_args = json.loads(tc.function.arguments or "{}")
                except json.JSONDecodeError:
                    tool_args = {}
                yield ("tool_start", tool_name, tool_args)

                result = await execute(tool_name, tool_args)
                result_str = result if isinstance(result, str) else json.dumps(result, ensure_ascii=False)
                yield ("tool_result", tool_name, result_str)

                messages.append({"role": "tool", "tool_call_id": tc.id, "content": result_str})
            continue  # следующий раунд

        # Нет tool_calls (или тулов нет) → streaming финального ответа
        stream = await client.chat.completions.create(
            model=LLM_MODEL, messages=messages, stream=True,
        )
        async for chunk in stream:
            delta = chunk.choices[0].delta.content
            if delta:
                yield ("text", delta)
        yield ("finish",)
        return

    # Если вышли по лимиту раундов
    yield ("text", "[достигнут лимит вызовов тулов]")
    yield ("finish",)


async def stream_chat(history: list[dict]):
    """Простой streaming без тулов (обратная совместимость с Phase 2 тестами)."""
    messages = [{"role": "system", "content": SYSTEM_PROMPT}] + history
    client = get_client()
    stream = await client.chat.completions.create(
        model=LLM_MODEL, messages=messages, stream=True,
    )
    async for chunk in stream:
        delta = chunk.choices[0].delta.content
        if delta:
            yield delta
