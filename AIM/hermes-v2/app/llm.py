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
        # Передаём выручку/прибыль/trend из profile_cache (от auto-call company_financials)
        # в format_profile — иначе обогащение мёртвым кодом (выручка не доходит до блока 01).
        client_data = {
            k: profile_cache[k]
            for k in ("revenue", "profit", "revenue_trend")
            if profile_cache.get(k)
        }
        profile_md, profile_data = format_profile(profile_result, client_data=client_data or None)
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
    logger.info("=== DEBUG _format_reviews_block INPUT: %d chars ===", len(reviews_raw or ""))
    try:
        data = json.loads(reviews_raw) if isinstance(reviews_raw, str) else reviews_raw
    except (json.JSONDecodeError, TypeError):
        logger.warning("=== DEBUG _format_reviews_block: JSON parse failed ===")
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
        # Fallback: не исчезаем полностью — показываем сообщение
        # (Apify может лежать, или клиники нет на Яндекс.Картах/2ГИС)
        summary = data.get("reputation_summary", "")
        return (
            "\n".join([
                ":::section-num",
                "04 — ОТЗЫВЫ ПАЦИЕНТОВ",
                ":::",
                "",
                summary if summary else "Отзывы временно недоступны.",
                "",
            ])
        )

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

    result_md = "\n".join(lines)
    logger.info(
        "=== DEBUG _format_reviews_block OUTPUT: %d chars, has_newlines=%s ===\n%s",
        len(result_md), "\\n" if "\n" in result_md else "NO",
        result_md[:300].replace("\n", "\\n"),
    )
    return result_md


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


def _extract_url_from_messages(messages: list[dict]) -> str:
    """Ищет URL в сообщениях пользователя. Поддерживает как http(s):// так и
    голые домены (arclinic.ru, mira-med.ru). Возвращает URL с https:// или ''.
    """
    import re as _re
    for m in reversed(messages):
        if m.get("role") != "user":
            continue
        content = m.get("content") or ""
        # Сначала полный URL с протоколом
        url_m = _re.search(r"https?://[^\s]+", content)
        if not url_m:
            # Потом голый домен (.ru, .com, и т.д.)
            url_m = _re.search(r"\b[\w-]+\.(ru|com|org|net|su|рф|io|me|pro)\b", content)
        if url_m:
            url = url_m.group(0)
            if not url.startswith("http"):
                url = "https://" + url
            return url
    return ""


async def _auto_publish_report(
    collected_results: dict,
    profile_cache: dict,
    llm_text: str,
):
    """Сгенерировать и опубликовать HTML-отчёт (Phase 11).

    Вызывается из chat_with_tools() перед завершением стрима, если
    collected_results содержит find_competitors (полный анализ выполнен).

    Yield-ит ("report_ready", url, title) при успехе. При ошибке —
    логирует warning (без raise — вызываетющий код уже обёрнут в try).

    Гвард дубликатов: записывает URL в profile_cache["_report_published_url"].
    """
    from app.report_builder import build_data_dict, build_report_html, publish_report

    # Сборка data dict + HTML
    data = build_data_dict(collected_results, profile_cache, llm_text)
    title = (
        profile_cache.get("company_name")
        or data.get("metadata", {}).get("company_name")
        or "Клиника"
    )
    html = build_report_html(data, title)

    # Публикация (async, MySQL INSERT)
    result = await publish_report(html, title)

    if result.get("url"):
        url = result["url"]
        # Защита от дубликатов в этой сессии
        profile_cache["_report_published_url"] = url
        logger.info("Auto-publish: report ready at %s (title=%r)", url, title)
        yield ("report_ready", url, title)
    elif result.get("status") == "saved_locally":
        logger.info("Auto-publish: saved locally (no DB): %s", result.get("path"))
    else:
        logger.warning(
            "Auto-publish: publish_report returned status=%s err=%s",
            result.get("status"),
            result.get("error", "")[:120],
        )


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
    collected_results: dict = {}  # накапливает результаты тулов ВСЕХ раундов (fix: было reset каждый раунд)
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
            # ВАЖНО: collected_results инициализируется ДО цикла (строка ~487) и
            # накапливает результаты всех раундов. НЕ сбрасываем здесь — иначе
            # auto-calls (financials, reviews) не видят результаты прошлых раундов.
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

                # Обрабатываем результаты (в порядке тулов).
                # ВАЖНО: НЕ делаем collected_results = {} — это уничтожит
                # extract_clinic_profile (из Фазы 1) и результаты прошлых раундов.
                # Только обновляем/добавляем ключи.
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

            # ── AUTO-CALL: company_financials если есть client_inn ──
            # Perplexity (extract_clinic_profile) почти не находит ИНН в response,
            # но может вернуть его в profile_cache. find_competitors (через aim-app)
            # тоже может вернуть client_inn в response. Проверяем оба источника.
            if (
                "find_competitors" in collected_results
                and "company_financials" not in collected_results
            ):
                try:
                    comp_data = json.loads(collected_results["find_competitors"])
                    # ИНН может быть в response find_competitors ИЛИ в profile_cache
                    # (extract_clinic_profile записывает его туда через auto-inject)
                    client_inn = (
                        comp_data.get("client_inn", "")
                        or profile_cache.get("inn", "")
                    )
                    if client_inn and len(client_inn) >= 10:
                        yield ("tool_start", "company_financials",
                               {"inn": client_inn}, "💰 Запрашиваю выручку из ФНС…")
                        from app.tools.aim_app_tools import handle_company_financials
                        fin_result = await handle_company_financials(inn=client_inn)
                        collected_results["company_financials"] = fin_result
                        # Обогатить profile_cache выручкой для блока 01
                        try:
                            fin_data = json.loads(fin_result)
                            if fin_data.get("revenue"):
                                profile_cache["revenue"] = fin_data["revenue"]
                            if fin_data.get("revenue_trend"):
                                profile_cache["revenue_trend"] = fin_data["revenue_trend"]
                            if fin_data.get("profit"):
                                profile_cache["profit"] = fin_data["profit"]
                            if fin_data.get("name") and not profile_cache.get("company_name"):
                                profile_cache["company_name"] = fin_data["name"]
                            logger.info(
                                "auto company_financials OK: inn=%s revenue=%s",
                                client_inn, fin_data.get("revenue"),
                            )
                        except (json.JSONDecodeError, TypeError):
                            pass
                        # Честное сообщение: проверяем что ФНС реально отдала выручку,
                        # иначе при aim-app 404 / ненайденном ИНН лжём про "успех".
                        try:
                            fin_data_check = json.loads(fin_result)
                            has_revenue = bool(fin_data_check.get("revenue"))
                        except (json.JSONDecodeError, TypeError):
                            has_revenue = False
                        yield ("tool_result", "company_financials", fin_result,
                               "✅ Финансы из ФНС получены" if has_revenue
                               else "⚠️ Финансы из ФНС недоступны")
                except Exception as e:
                    logger.warning("auto company_financials failed: %s", e)

            # ── AUTO-INJECT: run_review_platforms если LLM не вызовала ──
            # LLM упрямо игнорирует 4-й тул. Запускаем принудительно —
            # отзывы ключевая ценность продукта.
            if "find_competitors" in collected_results and "run_review_platforms" not in collected_results:
                # Получить URL из profile_cache или из сообщений
                review_url = profile_cache.get("url", "") or _extract_url_from_messages(messages)
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
            if not formatted_shown and (
                # Показываем blocks только когда есть данные для блока 01 (профиль).
                # Раньше показывали после первого find_competitors — блок 01 был пустым.
                "extract_clinic_profile" in collected_results
                or "company_financials" in collected_results
                or profile_cache.get("_raw_result")  # профиль из auto-call
            ):
                formatted_blocks = _build_formatted_blocks(
                    collected_results, profile_cache
                )
                if formatted_blocks:
                    formatted_shown = True
                # Показываем таблицы пользователю (как formatted event —
                # отличается от LLM text, чтобы main.py мог сохранить в историю)
                logger.info(
                    "=== DEBUG FORMATTED BLOCKS: %d blocks ===", len(formatted_blocks)
                )
                for i, block in enumerate(formatted_blocks):
                    # Логируем первые 200 символов + наличие переносов
                    has_newlines = "\\n" if "\n" in block else "NO_NEWLINES"
                    logger.info(
                        "=== DEBUG BLOCK[%d] (%s, %d chars, %s) ===\n%s",
                        i, type(block).__name__, len(block), has_newlines,
                        block[:200].replace("\n", "\\n"),
                    )
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

        # ════════════════════════════════════════════════════════════════════
        # LLM НЕ вызвала тулы → хочет дать финальный ответ (streaming).
        # Но перед этим: выполняем auto-calls (financials, reviews) и
        # показываем formatted blocks, ЕСЛИ find_competitors уже выполнен
        # и блоки ещё не показаны. Это страховка для случая, когда LLM
        # вызвала find_competitors в turn 0, а в turn 1 сразу решила отвечать
        # без вызова extract_clinic_profile / run_review_platforms.
        # ════════════════════════════════════════════════════════════════════
        logger.info(
            "=== PRE-STREAM CHECK: find_competitors=%s collected=%s formatted_shown=%s ===",
            "find_competitors" in collected_results,
            list(collected_results.keys()),
            formatted_shown,
        )
        if "find_competitors" in collected_results and (
            "extract_clinic_profile" not in collected_results
            or "company_financials" not in collected_results
            or "run_review_platforms" not in collected_results
            or not formatted_shown
        ):
            logger.info(
                "=== PRE-STREAM AUTO-CALLS: enter (collected=%s formatted_shown=%s) ===",
                list(collected_results.keys()), formatted_shown,
            )
            # Auto-call extract_clinic_profile если не был вызван (для ИНН/города/профиля)
            if "extract_clinic_profile" not in collected_results:
                user_url = _extract_url_from_messages(messages)
                if user_url:
                    yield ("tool_start", "extract_clinic_profile",
                           {"url": user_url}, "📋 Определяю клинику…")
                    try:
                        from app.tools.perplexity_tools import handle_extract_clinic_profile
                        profile_result = await handle_extract_clinic_profile(url=user_url)
                        collected_results["extract_clinic_profile"] = profile_result
                        try:
                            profile_cache.update(json.loads(profile_result))
                            profile_cache["_raw_result"] = profile_result
                            logger.info("auto extract_clinic_profile OK: inn=%s city=%s",
                                        profile_cache.get("inn"), profile_cache.get("city"))
                        except (json.JSONDecodeError, TypeError):
                            pass
                        yield ("tool_result", "extract_clinic_profile", profile_result,
                               "✅ Профиль клиники готов")
                    except Exception as e:
                        logger.warning("auto extract_clinic_profile (pre-stream) failed: %s", e)

            # Auto-call financials (если ещё не вызван)
            if "company_financials" not in collected_results:
                try:
                    comp_data = json.loads(collected_results["find_competitors"])
                    client_inn = (
                        comp_data.get("client_inn", "")
                        or profile_cache.get("inn", "")
                    )
                    if client_inn and len(client_inn) >= 10:
                        yield ("tool_start", "company_financials",
                               {"inn": client_inn}, "💰 Запрашиваю выручку из ФНС…")
                        from app.tools.aim_app_tools import handle_company_financials
                        fin_result = await handle_company_financials(inn=client_inn)
                        collected_results["company_financials"] = fin_result
                        try:
                            fin_data = json.loads(fin_result)
                            if fin_data.get("revenue"):
                                profile_cache["revenue"] = fin_data["revenue"]
                            if fin_data.get("revenue_trend"):
                                profile_cache["revenue_trend"] = fin_data["revenue_trend"]
                            if fin_data.get("profit"):
                                profile_cache["profit"] = fin_data["profit"]
                            if fin_data.get("name") and not profile_cache.get("company_name"):
                                profile_cache["company_name"] = fin_data["name"]
                            logger.info("auto company_financials OK: inn=%s revenue=%s",
                                        client_inn, fin_data.get("revenue"))
                        except (json.JSONDecodeError, TypeError):
                            pass
                        try:
                            fin_data_check = json.loads(fin_result)
                            has_revenue = bool(fin_data_check.get("revenue"))
                        except (json.JSONDecodeError, TypeError):
                            has_revenue = False
                        yield ("tool_result", "company_financials", fin_result,
                               "✅ Финансы из ФНС получены" if has_revenue
                               else "⚠️ Финансы из ФНС недоступны")
                except Exception as e:
                    logger.warning("auto company_financials (pre-stream) failed: %s", e)

            # Auto-call reviews (если ещё не вызван)
            if "run_review_platforms" not in collected_results:
                review_url = profile_cache.get("url", "") or _extract_url_from_messages(messages)
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
                        logger.warning("auto run_review_platforms (pre-stream) failed: %s", e)

            # Показать formatted blocks (только если ещё не показаны)
            if not formatted_shown:
                formatted_blocks = _build_formatted_blocks(collected_results, profile_cache)
                if formatted_blocks:
                    formatted_shown = True
                for block in formatted_blocks:
                    yield ("formatted", block + "\n\n")
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

        # ── Авто-публикация отчёта (Phase 11) ─────────────────────────
        # Если собран конкурентный анализ — публикуем красивый отчёт на
        # iamaim.ru/{slug} и шлём SSE event report-ready с URL.
        # Гварды: (1) есть find_competitors, (2) ещё не публиковали в сессии.
        if (
            "find_competitors" in collected_results
            and not profile_cache.get("_report_published_url")
        ):
            try:
                async for report_event in _auto_publish_report(
                    collected_results, profile_cache, "".join(llm_text)
                ):
                    yield report_event
            except Exception as e:
                logger.warning("Auto-publish report failed: %s", e)
                # Не блокируем finish при ошибке публикации

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
