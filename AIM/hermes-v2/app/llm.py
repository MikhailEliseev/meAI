"""LLM-клиент Гермеса v2 — glm-5.2 через Z.AI-шлюз.

Phase 7: параллельное выполнение tool_calls через asyncio.gather.
Сырой openai SDK (нативный streaming + tool-calling). Z.AI-шлюз OpenAI-совместимый.
Системный промпт подставляется автоматически как messages[0] (DIALOG-03).
"""
import asyncio
import json
import logging
import re

import openai

from app.config import LLM_MODEL, OMNIROUTE_AUTH, OMNIROUTE_URL
from app.prompts.dialogue import SYSTEM_PROMPT
from app.tools.registry import execute, get_openai_tools
from app.formatters.competitors import format_competitors
from app.formatters.profile import format_profile
from app.formatters.overview import format_overview

logger = logging.getLogger(__name__)

# ── Анти-галлюцинация: скрытие raw JSON от LLM ──────────────────────────
# Тулы, чьи результаты показаны пользователю как точные таблицы/факты из кода.
# Их raw JSON скрывается от LLM — LLM не видит галлюцинированные цифры Perplexity
# (выручка, ИНН, визиты), только таблицу из кода + качественный обзор.
# Качественные тулы (quick_overview, perplexity_search) — НЕ скрыты: из них
# LLM берёт врачей, соцсети, услуги.
_FORMATTED_TOOLS = frozenset({"find_competitors", "extract_clinic_profile"})

_TOOL_RESULT_HIDDEN = (
    "[Данные получены и отображены пользователю в виде таблицы выше. "
    "Используй данные из таблицы для выводов. Сырой JSON скрыт для предотвращения галлюцинаций.]"
)


def _filtered_tool_content(tool_name: str, result_str: str) -> str:
    """Возвращает content для role:tool message.

    Для форматированных тулов — заглушка (raw JSON скрыт).
    Для остальных — как есть (качественные данные).
    """
    if tool_name in _FORMATTED_TOOLS:
        return _TOOL_RESULT_HIDDEN
    return result_str


# Паттерны подозрительных формулировок (галлюцинации в выводах LLM)
_HALLUCINATION_PATTERNS = [
    (re.compile(r"[~≈]\s*[\d\s,]+", re.I), "оценочное число (~ или ≈)"),
    (re.compile(r"примерно\s+\d", re.I), "слово «примерно» + число"),
    (re.compile(r"около\s+\d", re.I), "слово «около» + число"),
    (re.compile(r"\d+\s*(?:тыс|млн|млрд)\s*визит", re.I), "оценка визитов"),
    (re.compile(r"\d+\s*(?:тыс|млн|млрд)\s*посетит", re.I), "оценка посетителей"),
]


def _check_hallucinations(llm_text: str, formatted_shown: bool) -> None:
    """Лёгкая пост-проверка ответа LLM на галлюцинации.

    НЕ блокирует (текст уже отправлен) — только логирует warnings
    для подозрительных формулировок. Телеметрия для следующей итерации.
    """
    if not llm_text or not formatted_shown:
        return
    for pattern, label in _HALLUCINATION_PATTERNS:
        matches = pattern.findall(llm_text)
        if matches:
            logger.warning(
                "ANTI-HALLUCINATION: LLM ответ содержит «%s»: %s — "
                "возможная галлюцинация (данных нет в таблицах)",
                label, matches[:3],
            )


# Человекочитаемые сообщения прогресса для каждого тула (для UX)
_TOOL_MESSAGES = {
    "extract_clinic_profile": {
        "start": "📋 Определяю клинику: ИНН, юрлицо, адрес…",
        "done": "✅ Профиль клиники готов",
    },
    "quick_overview": {
        "start": "🔍 Собираю обзор: врачи, услуги, соцсети…",
        "done": "✅ Обзор готов",
    },
    "find_competitors": {
        "start": "🗺️ Ищу конкурентов рядом через Google Maps (это ~1-2 минуты)…",
        "done": "✅ Конкуренты найдены",
    },
    "enrich_competitors": {
        "start": "💰 Получаю выручку конкурентов из ФНС…",
        "done": "✅ Финансовые данные готовы",
    },
    "company_financials": {
        "start": "💰 Запрашиваю финансовые данные из налоговой…",
        "done": "✅ Финансы получены",
    },
    "company_profile": {
        "start": "📄 Загружаю профиль из базы…",
        "done": "✅ Профиль готов",
    },
    "analyze_website": {
        "start": "🔬 Глубокий аудит сайта: SEO, UX, репутация (~30 сек)…",
        "done": "✅ Аудит завершён",
    },
    "seo_audit": {
        "start": "🔎 Анализирую SEO…",
        "done": "✅ SEO-анализ готов",
    },
    "perplexity_search": {
        "start": "🌐 Ищу актуальные данные…",
        "done": "✅ Поиск завершён",
    },
    "run_smi_mentions": {
        "start": "📰 Ищу упоминания в СМИ…",
        "done": "✅ Упоминания собраны",
    },
    "run_review_platforms": {
        "start": "⭐ Собираю отзывы и рейтинги…",
        "done": "✅ Отзывы готовы",
    },
    "run_instagram_content": {
        "start": "📸 Анализирую Instagram…",
        "done": "✅ Instagram проанализирован",
    },
    "run_ads_intelligence": {
        "start": "📢 Проверяю рекламную активность…",
        "done": "✅ Реклама проверена",
    },
}


def _tool_msg(tool_name: str, phase: str) -> str:
    """Возвращает человекочитаемое сообщение для тула или fallback."""
    msgs = _TOOL_MESSAGES.get(tool_name, {})
    return msgs.get(phase, f"⚙️ {tool_name}…")

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


async def _execute_single_tool(tc, profile_cache: dict):
    """Выполняет один tool_call. Возвращает (tool_call, result_str)."""
    tool_name = tc.function.name
    try:
        tool_args = json.loads(tc.function.arguments or "{}")
    except json.JSONDecodeError:
        tool_args = {}

    # Auto-inject: if find_competitors called without client_inn/client_address
    # and extract_clinic_profile was called before, merge its result
    if tool_name == "find_competitors" and profile_cache:
        if not tool_args.get("client_inn") and profile_cache.get("inn"):
            tool_args["client_inn"] = profile_cache["inn"]
            logger.info("auto-inject: client_inn=%s into find_competitors", profile_cache["inn"])
        if not tool_args.get("client_address") and profile_cache.get("address"):
            tool_args["client_address"] = profile_cache["address"]
            logger.info("auto-inject: client_address=%s into find_competitors", profile_cache["address"][:60])

    result = await execute(tool_name, tool_args)
    result_str = result if isinstance(result, str) else json.dumps(result, ensure_ascii=False)

    # Cache extract_clinic_profile result for auto-inject into find_competitors
    if tool_name == "extract_clinic_profile" and isinstance(result, str):
        try:
            profile_cache.update(json.loads(result_str))
            profile_cache["_raw_result"] = result_str  # for formatted blocks
            logger.info("profile cache updated: inn=%s city=%s",
                         profile_cache.get("inn"), profile_cache.get("city"))
        except (json.JSONDecodeError, TypeError):
            pass

    return tc, result_str


def _build_formatted_blocks(
    collected_results: dict[str, str],
    profile_cache: dict,
) -> list[str]:
    """Build formatted Markdown data blocks from tool results.

    Converts raw JSON from find_competitors and extract_clinic_profile
    into precise Markdown tables/facts. These are shown to the user
    BEFORE the LLM generates its answer, so the LLM only needs to
    make conclusions — it cannot hallucinate in the table.

    Returns list of Markdown strings (each is a separate data block).
    """
    blocks = []

    # Profile block (from extract_clinic_profile)
    profile_result = profile_cache.get("_raw_result") or collected_results.get("extract_clinic_profile")
    if profile_result:
        profile_md, profile_data = format_profile(profile_result)
        if profile_md:
            blocks.append(profile_md)

    # Overview block (from quick_overview — врачи, соцсети, платформа)
    overview_result = collected_results.get("quick_overview")
    if overview_result:
        overview_md = format_overview(overview_result)
        if overview_md:
            blocks.append(overview_md)

    # Competitors block (from find_competitors)
    competitors_result = collected_results.get("find_competitors")
    if competitors_result:
        # Get client revenue from profile_cache if available
        client_rev = None
        if profile_data and profile_data.get("inn"):
            # We don't have client revenue here, format_competitors handles None
            pass
        comp_md = format_competitors(competitors_result, client_revenue=client_rev)
        if comp_md:
            blocks.append(comp_md)

    return blocks


async def chat_with_tools(history: list[dict]):
    """Диалог с tool-calling. Возвращает генератор событий для SSE.

    События (кортежи):
        ("text", str)            — токен текста
        ("tool_start", name, args) — начало вызова тулза
        ("tool_result", name, result) — результат тулза
        ("finish",)              — конец диалога

    Цикл:
    1. non-streaming вызов с tools= для определения хочет ли модель тул.
    2. Если tool_calls → выполняем ПАРАЛЛЕЛЬНО через asyncio.gather.
    3. Если нет tool_calls → streaming финального ответа.
    """
    messages = [{"role": "system", "content": SYSTEM_PROMPT}] + list(history)
    tools = get_openai_tools()
    client = get_client()
    profile_cache: dict = {}  # caches extract_clinic_profile result for auto-inject
    formatted_shown = False  # prevent showing data blocks twice across turns

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

            # Phase 7: ПАРАЛЛЕЛЬНОЕ выполнение всех tool_calls
            n_tools = len(msg.tool_calls)
            if n_tools > 1:
                logger.info("parallel execution: %d tools", n_tools)

            # Проблема: extract_clinic_profile должен выполниться ПЕРЕД find_competitors
            # (для auto-inject ИНН), но мы хотим параллельность для остальных.
            # Решение: двухфазная стратегия:
            # Фаза 1: extract_clinic_profile (если есть) → получаем ИНН
            # Фаза 2: все остальные тулы параллельно (с ИНН в profile_cache)

            profile_tc = None
            other_tcs = []
            for tc in msg.tool_calls:
                if tc.function.name == "extract_clinic_profile":
                    profile_tc = tc
                else:
                    other_tcs.append(tc)

            # Фаза 1: extract_clinic_profile (если есть) — сначала, для auto-inject
            if profile_tc:
                tool_name = profile_tc.function.name
                yield ("tool_start", tool_name,
                       json.loads(profile_tc.function.arguments or "{}"),
                       _tool_msg(tool_name, "start"))
                profile_tc, profile_result = await _execute_single_tool(profile_tc, profile_cache)
                yield ("tool_result", tool_name, profile_result,
                       _tool_msg(tool_name, "done"))
                messages.append({
                    "role": "tool", "tool_call_id": profile_tc.id,
                    "content": _filtered_tool_content(tool_name, profile_result),
                })

            # Фаза 2: остальные тулы параллельно
            if other_tcs:
                # Отправляем tool_start события для всех
                for tc in other_tcs:
                    tool_name = tc.function.name
                    try:
                        args = json.loads(tc.function.arguments or "{}")
                    except json.JSONDecodeError:
                        args = {}
                    yield ("tool_start", tool_name, args, _tool_msg(tool_name, "start"))

                # Параллельное выполнение
                results = await asyncio.gather(
                    *[_execute_single_tool(tc, profile_cache) for tc in other_tcs],
                    return_exceptions=True,
                )

                # Обрабатываем результаты (в порядке тулов)
                collected_results = {}  # tool_name → result_str (for formatting)
                for tc, result in zip(other_tcs, results):
                    tool_name = tc.function.name
                    if isinstance(result, Exception):
                        error_str = json.dumps({"error": str(result)}, ensure_ascii=False)
                        yield ("tool_result", tool_name, error_str, _tool_msg(tool_name, "done"))
                        messages.append({
                            "role": "tool", "tool_call_id": tc.id,
                            "content": error_str,
                        })
                    else:
                        _, result_str = result
                        collected_results[tool_name] = result_str
                        yield ("tool_result", tool_name, result_str, _tool_msg(tool_name, "done"))
                        messages.append({
                            "role": "tool", "tool_call_id": tc.id,
                            "content": _filtered_tool_content(tool_name, result_str),
                        })

            # ── FORMAT DATA BLOCKS: точные таблицы из кода, не из LLM ──
            # Формируем готовые Markdown блоки из tool results и показываем
            # пользователю ДО того как LLM начнёт генерировать ответ.
            # LLM получает instruction делать только выводы по этим данным.
            if not formatted_shown:
                formatted_blocks = _build_formatted_blocks(
                    collected_results, profile_cache
                )
                if formatted_blocks:
                    formatted_shown = True
                # Показываем таблицы пользователю (как formatted event —
                # отличается от LLM text, чтобы main.py мог сохранить в историю)
                for block in formatted_blocks:
                    yield ("formatted", block + "\n\n")

                # Instruction для LLM: данные выше — факты, делай только выводы
                messages.append({
                    "role": "system",
                    "content": (
                        "Выше показаны ТОЧНЫЕ данные в виде таблиц (из ФНС, SearXNG). "
                        "Твоя задача — сделать только выводы (3-5 предложений):\n"
                        "1. Позиция клиники относительно конкурентов (по выручке)\n"
                        "2. 1-2 конкретных рекомендации на основе данных\n"
                        "3. [SUGGESTIONS] кнопки\n\n"
                        "КРИТИЧНО:\n"
                        "- НЕ повторяй таблицы — они уже показаны выше\n"
                        "- НЕ выдумывай цифры — используй только из таблиц\n"
                        "- НЕ упоминай отзывы, рейтинг, трафик — этих данных нет\n"
                        "- Если данных нет — не пиши про них"
                    ),
                })

            continue  # следующий раунд

        # Нет tool_calls (или тулов нет) → streaming финального ответа
        stream = await client.chat.completions.create(
            model=LLM_MODEL, messages=messages, stream=True,
        )
        llm_text = []  # накапливаем для пост-проверки (анти-галлюцинация)
        async for chunk in stream:
            delta = chunk.choices[0].delta.content
            if delta:
                llm_text.append(delta)
                yield ("text", delta)

        # ── Пост-проверка (анти-галлюцинация) ──────────────────────────
        # Текст уже отправлен — не блокируем. Но логируем подозрительные
        # числа которых нет в formatted blocks (телеметрия для итерации).
        _check_hallucinations("".join(llm_text), formatted_shown)

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
