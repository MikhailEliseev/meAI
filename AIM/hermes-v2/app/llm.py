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
        "start": "📋 Определяю клинику: адрес, специализация, услуги…",
        "done": "✅ Профиль клиники готов",
    },
    "quick_overview": {
        "start": "🔍 Собираю обзор: врачи, услуги, соцсети…",
        "done": "✅ Обзор готов",
    },
    "find_competitors": {
        "start": "🗺️ Ищу конкурентов через Perplexity и ФНС (это ~1-2 минуты)…",
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

    # Auto-inject: run_review_platforms — fill company_name/city from profile_cache
    if tool_name == "run_review_platforms" and profile_cache:
        if not tool_args.get("company_name") and profile_cache.get("company_name"):
            tool_args["company_name"] = profile_cache["company_name"]
        if not tool_args.get("city") and profile_cache.get("city"):
            tool_args["city"] = profile_cache["city"]

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

    # Сначала парсим competitors — там лежат client_cms, client_socials, client_audit
    competitors_result = collected_results.get("find_competitors")
    client_pipeline_data = {}
    client_rev = None
    client_profit = None
    if competitors_result:
        try:
            comp_data = json.loads(competitors_result) if isinstance(competitors_result, str) else competitors_result
            client_rev = comp_data.get("client_revenue")
            client_profit = comp_data.get("client_profit")
            client_pipeline_data = {
                "client_cms": comp_data.get("client_cms"),
                "client_socials": comp_data.get("client_socials"),
                "client_doctors": comp_data.get("client_doctors"),
                "client_audit": comp_data.get("client_audit"),
                "client_registration_date": comp_data.get("client_registration_date"),
                "client_employee_count": comp_data.get("client_employee_count"),
            }
        except (json.JSONDecodeError, TypeError):
            pass

    # ── Profile block — с override данных из pipeline (CMS, соцсети, врачи) ──
    profile_result = profile_cache.get("_raw_result") or collected_results.get("extract_clinic_profile")
    if profile_result:
        try:
            pdata = json.loads(profile_result) if isinstance(profile_result, str) else profile_result
            # Override CMS из Firecrawl audit (точнее чем Perplexity)
            if client_pipeline_data.get("client_cms"):
                pdata["website_platform"] = client_pipeline_data["client_cms"]
            # Добавить соцсети из Firecrawl
            if client_pipeline_data.get("client_socials"):
                pdata["socials_found"] = client_pipeline_data["client_socials"]
            # Добавить врачей из Firecrawl
            if client_pipeline_data.get("client_doctors"):
                pdata["doctors_count"] = client_pipeline_data["client_doctors"]
            profile_result = json.dumps(pdata, ensure_ascii=False) if isinstance(profile_result, str) else pdata
        except (json.JSONDecodeError, TypeError):
            pass
        profile_md, profile_data = format_profile(profile_result)
        if profile_md:
            blocks.append(profile_md)

    # Overview block — БЕЗ платформы (она в audit блоке)
    overview_result = collected_results.get("quick_overview")
    if overview_result:
        overview_md = format_overview(overview_result)
        if overview_md:
            blocks.append(overview_md)

    # ── Competitors block (ПЕРЕД аудитом — клиент хочет видеть рынок первым) ──
    if competitors_result:
        comp_md = format_competitors(
            competitors_result,
            client_revenue=client_rev,
            client_profit=client_profit,
            client_reg_date=client_pipeline_data.get("client_registration_date"),
            client_scl=client_pipeline_data.get("client_employee_count"),
        )
        if comp_md:
            blocks.append(comp_md)

    # ── Reviews block (отзывы клиента по площадкам) ──
    reviews_result = collected_results.get("run_review_platforms")
    if reviews_result:
        reviews_md = _format_reviews_block(reviews_result)
        if reviews_md:
            blocks.append(reviews_md)

    audit = client_pipeline_data.get("client_audit")
    if audit:
        audit_md = _format_audit_block(audit)
        if audit_md:
            blocks.append(audit_md)

    return blocks


def _format_reviews_block(reviews_raw: str) -> str:
    """Форматирует отзывы с площадок в Markdown блок."""
    try:
        data = json.loads(reviews_raw) if isinstance(reviews_raw, str) else reviews_raw
    except (json.JSONDecodeError, TypeError):
        return ""

    platforms = data.get("platforms", {})
    lines = [":::section-num", "04 — ОТЗЫВЫ ПАЦИЕНТОВ", ":::", ""]

    # Рейтинги по площадкам в stat-cards
    platform_labels = {
        "yandex": "Яндекс.Карты",
        "prodoctorov": "ПроДокторов",
        "twogis": "2ГИС",
    }
    found_any = False
    for key, label in platform_labels.items():
        p = platforms.get(key, {})
        rating = p.get("rating")
        reviews = p.get("reviews")
        if rating:
            found_any = True
            rev_str = f" ({reviews})" if reviews else ""
            lines.append(":::stat-card")
            lines.append(f"**{rating} ★**")
            lines.append(f"{label}{rev_str}")
            lines.append(":::")

    if found_any:
        lines.append("")

    if not found_any:
        return ""

    # Темы: хвалят
    praise = data.get("praise_summary", "")
    if praise:
        lines.append("\n**✅ Хвалят:**\n")
        for topic in praise.split("|")[:4]:
            topic = topic.strip()
            if topic:
                lines.append(f"- {topic[:150]}\n")

    # Темы: критикуют
    criticism = data.get("criticism_summary", "")
    if criticism:
        lines.append("\n**⚠️ Критикуют:**\n")
        for topic in criticism.split("|")[:4]:
            topic = topic.strip()
            if topic:
                lines.append(f"- {topic[:150]}\n")

    # Общий вывод о репутации
    summary = data.get("reputation_summary", "")
    if summary:
        lines.append(f"\n**📋 Репутация:** {summary[:300]}\n")

    return "\n".join(lines)


def _format_audit_block(audit: dict) -> str:
    """Форматирует SEO+GEO аудит — структурированные секции как в эталоне."""
    if not audit:
        return ""

    geo = audit.get("geo_score", 0)
    geo_emoji = "🔴" if geo < 30 else ("🟡" if geo < 60 else "🟢")

    lines = [":::section-num", "03 — ТЕХНИЧЕСКИЙ АУДИТ", ":::", ""]

    # ── GEO Score в stat-card ──
    lines.append(":::stat-card")
    lines.append(f"**{geo}/100**")
    lines.append(f"GEO Score {geo_emoji}")
    lines.append(":::")
    lines.append("")

    # ── AI-готовность + Schema + SEO в surface-block ──
    audit_items = []
    ai = audit.get("ai_crawlers", {})
    open_ = [k for k, v in ai.items() if isinstance(v, dict) and not v.get("blocked")]
    blocked = [k for k, v in ai.items() if isinstance(v, dict) and v.get("blocked")]
    if open_:
        audit_items.append(f"✅ AI-краулеры: {', '.join(open_[:5])}")
    if blocked:
        audit_items.append(f"❌ Заблокированы: {', '.join(blocked[:3])}")
    audit_items.append("✅ llms.txt" if audit.get("llms_txt") else "❌ llms.txt отсутствует")

    schema = audit.get("schema", {})
    med = schema.get("medical", [])
    if med:
        audit_items.append(f"✅ Medical Schema: {', '.join(med[:2])}")
    else:
        audit_items.append("❌ MedicalBusiness Schema отсутствует")

    issues = []
    if not audit.get("h1"):
        issues.append("нет H1")
    if not audit.get("meta_description"):
        issues.append("нет meta description")
    if not audit.get("og_tags"):
        issues.append("нет Open Graph")
    if issues:
        audit_items.append(f"⚠️ SEO: {', '.join(issues)}")

    tech = []
    tech.append("SSR ✅" if audit.get("ssr") else "SSR ❌")
    if audit.get("page_size_kb"):
        tech.append(f"{audit['page_size_kb']:.0f} KB")
    if audit.get("perf_estimate"):
        perf_emoji = {"высокая": "🟢", "средняя": "🟡", "низкая": "🔴"}.get(audit["perf_estimate"], "")
        tech.append(f"{perf_emoji} {audit['perf_estimate']}")
    if tech:
        audit_items.append(f"📊 {' · '.join(tech)}")

    if audit_items:
        lines.append(":::surface-block")
        lines.append("  \n".join(audit_items))
        lines.append(":::")
        lines.append("")

    # ── Репутация в stat-cards ──
    yandex_rating = audit.get("yandex_rating")
    yandex_reviews = audit.get("yandex_reviews")
    if yandex_rating:
        rev_str = f" ({yandex_reviews} отзывов)" if yandex_reviews else ""
        lines.append(":::stat-card")
        lines.append(f"**{yandex_rating} ★**")
        lines.append(f"Яндекс{rev_str}")
        lines.append(":::")

    vk_followers = audit.get("vk_followers")
    if vk_followers:
        lines.append(":::stat-card")
        lines.append(f"**{vk_followers:,}**")
        lines.append("VK подписчиков")
        lines.append(":::")

    media = audit.get("media_mentions", 0)
    if media and media > 0:
        lines.append(":::stat-card")
        lines.append(f"**{media}+**")
        lines.append("СМИ публикаций")
        lines.append(":::")

    if yandex_rating or vk_followers:
        lines.append("")

    lines.append("---")
    return "\n".join(lines)


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
            collected_results = {}  # всегда инициализируем (fix NameError)
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

            # ── AUTO-INJECT: run_review_platforms если LLM не вызовала ──
            # LLM упрямо игнорирует 4-й тул. Запускаем принудительно —
            # отзывы ключевая ценность продукта.
            if "find_competitors" in collected_results and "run_review_platforms" not in collected_results:
                # Получить URL из profile_cache или из сообщений
                review_url = profile_cache.get("url", "")
                if not review_url:
                    # Поискать URL в последнем сообщении пользователя
                    for m in reversed(messages):
                        if m.get("role") == "user" and "http" in (m.get("content") or ""):
                            import re as _re
                            url_match = _re.search(r"https?://[^\s]+", m["content"])
                            if url_match:
                                review_url = url_match.group(0)
                                break
                if review_url:
                    yield ("tool_start", "run_review_platforms",
                           {"url": review_url}, "⭐ Собираю отзывы с площадок…")
                    try:
                        from app.tools.run_review_platforms import handle_run_review_platforms
                        review_result = await handle_run_review_platforms(
                            url=review_url,
                            company_name=profile_cache.get("company_name", ""),
                            city=profile_cache.get("city", ""),
                        )
                        collected_results["run_review_platforms"] = review_result
                        yield ("tool_result", "run_review_platforms", review_result, "✅ Отзывы собраны")
                    except Exception as e:
                        logger.warning("auto run_review_platforms failed: %s", e)

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
                        "Выше показаны ТОЧНЫЕ данные (секции 01-04 уже отображены). "
                        "Твоя задача — ТОЛЬКО аналитический нарратив. "
                        "КАТЕГОРИЧЕСКИ ЗАПРЕЩЕНО:\n"
                        "- Повторять данные из секций выше (ИНН, выручку, адреса, услуги, рейтинги)\n"
                        "- Дублировать таблицу конкурентов или блок отзывов\n"
                        "- Создавать заголовки ## — ты пишешь выводы, не данные\n\n"
                        "Структура ответа (БЕЗ заголовков ##, просто текст):\n\n"
                        "**💡 Позиция:** 1-2 предложения — лидер/середняк/аутсайдер рынка.\n\n"
                        "**✅ Сильные:** 2-3 пункта маркированным списком.\n\n"
                        "**⚠️ Рост:** 2-3 конкретных пробела. НЕ рекомендуй то что уже есть.\n\n"
                        "**🎯 Рекомендации:** 1-2 действия на основе РЕАЛЬНЫХ пробелов.\n\n"
                        "**🗣️ Отзывы:** 2-3 предложения — главные темы из блока 04.\n\n"
                        "[SUGGESTIONS]\n"
                        "📸 Анализ соцсетей конкурентов|run_instagram_content\n"
                        "🔍 Глубокий SEO-аудит сайта|seo_audit\n"
                        "[/SUGGESTIONS]\n\n"
                        "КРИТИЧНО:\n"
                        "- НЕ повторяй НИ ОДНОЙ цифры из секций выше в своём тексте\n"
                        "- НЕ выдумывай цифры\n"
                        "- Сравнивай КОНКРЕТНО: «крупнее в X раз»\n"
                        "- ⚖️ НЕ рекомендуй Instagram/Telegram (148-ФЗ). Можно: VK, RuTube, Дзен"
                    ),
                })

            continue  # следующий раунд

        # Нет tool_calls (или тулов нет) → streaming финального ответа
        stream = await client.chat.completions.create(
            model=LLM_MODEL, messages=messages, stream=True,
        )
        llm_text = []  # накапливаем для пост-проверки (анти-галлюцинация)
        try:
            async for chunk in stream:
                if chunk.choices and chunk.choices[0].delta:
                    delta = chunk.choices[0].delta.content
                    if delta:
                        llm_text.append(delta)
                        yield ("text", delta)
        finally:
            # Корректно закрываем stream (освобождает HTTP connection)
            if hasattr(stream, "close"):
                await stream.close()

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
    try:
        async for chunk in stream:
            if chunk.choices and chunk.choices[0].delta:
                delta = chunk.choices[0].delta.content
                if delta:
                    yield delta
    finally:
        if hasattr(stream, "close"):
            await stream.close()
