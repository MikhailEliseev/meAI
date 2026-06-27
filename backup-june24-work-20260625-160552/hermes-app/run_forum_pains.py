"""
run_forum_pains — Hermes tool: Patient Fears Extractor (Phase 4 / SEC-05)

Per D-10: Scrape patient review texts from 4 platforms:
- ПроДокторов (prodoctorov.ru) — doctor/clinic reviews
- Otzovik (otzovik.com) — general reviews
- IRecommend (irecommend.ru) — product/service reviews
- Woman.ru (woman.ru, health section) — forum discussions

Per D-11: LLM extracts top-5 patient fears from review texts.
This tool returns raw texts + Perplexity-extracted fear hints.

Uses Perplexity (sonar-pro) for web search + fear extraction.
Fallback: DeepSeek LLM (no web search) if PERPLEXITY_API_KEY not set.
"""

import json
import logging
import os
import re
import time

from tools.registry import registry

logger = logging.getLogger(__name__)

# ── Perplexity (primary) ────────────────────────────────────────────
PERPLEXITY_API_KEY = os.getenv("PERPLEXITY_API_KEY", "").strip()
PERPLEXITY_BASE_URL = "https://api.perplexity.ai"
PERPLEXITY_MODEL = "sonar-pro"
USE_PERPLEXITY = bool(PERPLEXITY_API_KEY)

# ── LLM fallback (no web search) ───────────────────────────────────
LLM_BASE_URL = os.getenv("LLM_BASE_URL", os.getenv("OMNIROUTE_URL", "https://api.deepseek.com/v1"))
LLM_API_KEY = os.getenv("LLM_API_KEY", os.getenv("OMNIROUTE_AUTH", os.getenv("DEEPSEEK_API_KEY", "")))
LLM_MODEL = os.getenv("LLM_MODEL", "deepseek-chat")

REQUEST_TIMEOUT = 90.0
MAX_TOKENS = 8000

_cache: dict[str, tuple[float, str]] = {}
_CACHE_TTL = 600

# ── Forum sources per D-10 ──────────────────────────────────────────
FORUM_SOURCES = [
    {"name": "ПроДокторов", "domain": "prodoctorov.ru", "weight": 0.35},
    {"name": "Otzovik", "domain": "otzovik.com", "weight": 0.25},
    {"name": "IRecommend", "domain": "irecommend.ru", "weight": 0.20},
    {"name": "Woman.ru", "domain": "woman.ru", "weight": 0.20},
]

# Common medical patient fears — hint list for the LLM
_FEAR_HINTS = [
    "больно", "дорого", "неквалифицированный врач", "долгое ожидание",
    "грубость персонала", "неэффективное лечение", "осложнения",
    "антисанитария", "навязывание услуг", "неправильный диагноз",
    "повторное обращение", "отсутствие результатов",
]


def _normalize_args(first_param, defaults):
    """Accept dict-style first arg (some LMs pass kwargs as dict)."""
    if isinstance(first_param, dict):
        return {k: first_param.get(k, defaults[k]) for k in defaults}
    return None


def _build_query(company_name: str, city: str, url: str) -> str:
    """Build Perplexity query — step-by-step per platform per D-11.

    Asks for top-5 patient fears extracted from review TEXTS (not star
    ratings), with mention counts. Mirrors run_review_platforms._build_query
    step-by-step structure for reliable platform coverage.
    """
    target = company_name or url
    location = f" (г. {city})" if city else ""
    website = f", сайт: {url}" if url and url.startswith("http") else ""

    return (
        f"Найди отзывы пациентов о клинике «{target}»{location}{website} "
        f"на следующих платформах и извлеки ТОП-5 страхов/жалоб.\n\n"
        "ВАЖНО: ищи страхи в ТЕКСТАХ отзывов, а не в звёздных рейтингах. "
        "Один отзыв может упоминать несколько страхов. Подсчитай сколько "
        "отзывов упоминают каждый страх (mention_count).\n\n"
        "## Шаг 1 — ПроДокторов (prodoctorov.ru)\n"
        "Найди страницу клиники на prodoctorov.ru. Прочитай тексты отзывов. "
        "Извлеки жалобы/страхи пациентов. Укажи по каждой жалобе:\n"
        "- Название страха (например: «Больно», «Долгое ожидание»)\n"
        "- Сколько отзывов упоминают этот страх (mention_count)\n"
        "- Сколько всего отзывов прочитано\n"
        "Если клиника не найдена — напиши «Не найден на ПроДокторов».\n\n"
        "## Шаг 2 — Otzovik (otzovik.com)\n"
        "Найди страницу клиники на otzovik.com. То же самое: страхи из "
        "текстов отзывов + mention_count. Если нет — «Не найден».\n\n"
        "## Шаг 3 — IRecommend (irecommend.ru)\n"
        "Проверь irecommend.ru на наличие отзывов о клинике. Извлеки "
        "страхи если есть. Если нет — «Не найден».\n\n"
        "## Шаг 4 — Woman.ru (woman.ru, health section)\n"
        "Проверь форум woman.ru (раздел здоровье) на упоминания клиники. "
        "Извлеки страхи из обсуждений. Если нет — «Не найден».\n\n"
        "## ИТОГ — ТОП-5 страхов пациентов\n"
        "После сбора по 4 платформам, выведи ТОП-5 самых частых страхов "
        "в формате (ОБЯЗАТЕЛЬНО в этом формате):\n"
        "1. {Название страха} — {N} упоминаний из {M} отзывов\n"
        "2. {Название страха} — {N} упоминаний из {M} отзывов\n"
        "...\n"
        "Где N — сколько отзывов упоминают этот страх, M — сколько всего "
        "отзывов прочитано по этой платформе.\n\n"
        "Если по всем 4 платформам отзывов нет — напиши "
        "«Страхи не выявлены: недостаточно отзывов»."
    )


def _build_system_prompt() -> str:
    return (
        "Ты — аналитик пациентского опыта медицинских клиник. "
        "Твоя задача — найти ТОП-5 страхов/жалоб пациентов из текстов "
        "отзывов (не из звёздных рейтингов). Ищи конкретные страхи: "
        f"{', '.join(_FEAR_HINTS[:8])} и подобные. "
        "Подсчитывай упоминания каждого страха. "
        "Если данных нет — честно скажи, не выдумывай цифры."
    )


async def _call_perplexity(prompt: str) -> str:
    """Call Perplexity sonar-pro (web search enabled)."""
    from openai import AsyncOpenAI

    client = AsyncOpenAI(
        api_key=PERPLEXITY_API_KEY,
        base_url=PERPLEXITY_BASE_URL,
        timeout=REQUEST_TIMEOUT,
    )
    response = await client.chat.completions.create(
        model=PERPLEXITY_MODEL,
        messages=[
            {"role": "system", "content": _build_system_prompt()},
            {"role": "user", "content": prompt},
        ],
        temperature=0.2,
        max_tokens=MAX_TOKENS,
    )
    return response.choices[0].message.content or ""


async def _call_llm(prompt: str) -> str:
    """Fallback: LLM via OMNIROUTE (no web search)."""
    from openai import AsyncOpenAI

    client = AsyncOpenAI(
        api_key=LLM_API_KEY,
        base_url=LLM_BASE_URL,
        timeout=REQUEST_TIMEOUT,
    )
    response = await client.chat.completions.create(
        model=LLM_MODEL,
        messages=[
            {
                "role": "system",
                "content": (
                    "Ты — аналитик пациентского опыта медицинских клиник. "
                    "У тебя нет доступа к интернету. Если ты не знаешь "
                    "реальных отзывов о клинике — честно напиши "
                    "«Страхи не выявлены: недостаточно данных». "
                    "Не выдумывай страхи и количества упоминаний."
                ),
            },
            {"role": "user", "content": prompt},
        ],
        temperature=0.2,
        max_tokens=MAX_TOKENS,
    )
    return response.choices[0].message.content or ""


# Regex for "{fear} — {N} упоминаний из {M} отзывов" OR "{fear} — {N} упоминаний"
_FEAR_PATTERN = re.compile(
    r"([А-Яа-яЁё][А-Яа-яЁё\s\-]{2,60}?)\s*[—–-]\s*(\d+)\s*упоминан",
    re.IGNORECASE,
)


def _extract_fears(answer: str) -> list[dict]:
    """Parse Perplexity answer for top-5 fears with mention counts.

    Looks for patterns like:
        «Больно — 47 упоминаний из 120 отзывов»
        «Дорого — 35 упоминаний»

    Returns up to 5 dicts sorted by mention_count desc:
        [{"fear": "Больно", "mention_count": 47, "context": "..."}, ...]
    """
    if not answer:
        return []

    fears: list[dict] = []
    seen: set[str] = set()

    for match in _FEAR_PATTERN.finditer(answer):
        fear_name = match.group(1).strip().rstrip(".,;:!?").strip()
        # Filter out obviously non-fear phrases
        fear_name_lower = fear_name.lower()
        if len(fear_name) < 3 or len(fear_name) > 60:
            continue
        # Skip section headers like «Итог — Топ-5 страхов»
        if "топ" in fear_name_lower and "страх" in fear_name_lower:
            continue
        # Normalize key for dedup (lowercase, collapse spaces)
        key = re.sub(r"\s+", " ", fear_name_lower).strip()
        if key in seen:
            continue
        seen.add(key)

        try:
            mention_count = int(match.group(2))
        except ValueError:
            continue

        # Capture surrounding context (up to ~80 chars after match)
        ctx_end = min(match.end() + 80, len(answer))
        context = answer[match.start():ctx_end].replace("\n", " ").strip()

        fears.append({
            "fear": fear_name,
            "mention_count": mention_count,
            "context": context,
        })

        if len(fears) >= 5:
            break

    # Sort by mention_count descending
    fears.sort(key=lambda f: f["mention_count"], reverse=True)
    return fears[:5]


async def handle_run_forum_pains(url=None, company_name="", city="", **kwargs) -> str:
    """Collect patient fears from 4 review platforms via Perplexity.

    Per D-10..11: scrapes patient review texts (ПроДокторов, Otzovik,
    IRecommend, Woman.ru) and extracts top-5 fears with mention counts.

    Args:
        url: Clinic website URL (used as fallback identifier).
        company_name: Clinic name for search (preferred).
        city: City for geo-targeting.

    Returns:
        JSON: clinic, city, sources_checked, patient_fears_hint (up to 5
        dicts with {fear, mention_count, context}), raw_analysis, source,
        searched_at.
    """
    unpacked = _normalize_args(url, {"url": ""})
    if unpacked:
        url = unpacked["url"]
        company_name = unpacked.get("company_name", company_name)
        city = unpacked.get("city", city)

    # Also check kwargs (LMs sometimes pass everything as kwargs)
    cn = kwargs.get("company_name", "")
    if cn and not company_name:
        company_name = cn
    ct = kwargs.get("city", "")
    if ct and not city:
        city = ct

    search_target = url or company_name or ""
    if not search_target:
        return json.dumps({"error": "URL or clinic name is required"}, ensure_ascii=False)

    # Derive clinic name from URL domain if needed
    if search_target.startswith("http") and not company_name:
        from urllib.parse import urlparse
        parsed = urlparse(search_target)
        company_name = parsed.netloc.replace("www.", "")

    query_name = company_name or search_target

    cache_key = f"forum_pains_{query_name}_{city}"
    cached = _cache.get(cache_key)
    if cached is not None:
        cached_ts, cached_result = cached
        if time.time() - cached_ts < _CACHE_TTL:
            logger.info("Forum pains cache HIT for: %s", query_name)
            return cached_result
        del _cache[cache_key]

    logger.info(
        "Extracting patient fears (Perplexity=%s) for: %s, city=%s",
        "available" if USE_PERPLEXITY else "unavailable", query_name, city,
    )

    try:
        from app.main import push_tool_progress

        push_tool_progress("forum_pains", f"😰 Ищу страхи пациентов на 4 форумах для {query_name}…")

        query = _build_query(query_name, city, url)
        source = ""

        if USE_PERPLEXITY:
            push_tool_progress("forum_pains", "🔍 Perplexity ищет отзывы и извлекает страхи…")
            answer = await _call_perplexity(query)
            source = f"perplexity ({PERPLEXITY_MODEL})"
        else:
            push_tool_progress(
                "forum_pains",
                "⚠️ Perplexity недоступен — fallback на LLM без web search…",
            )
            answer = await _call_llm(query)
            source = f"llm ({LLM_MODEL}) — без веб-поиска"

        fears = _extract_fears(answer)
        push_tool_progress(
            "forum_pains",
            f"✅ Извлечено {len(fears)} страхов из {len(FORUM_SOURCES)} платформ",
        )

        result = {
            "clinic": query_name,
            "city": city or "не указан",
            "sources_checked": len(FORUM_SOURCES),
            "forum_sources": [s["name"] for s in FORUM_SOURCES],
            "patient_fears_hint": fears,  # up to 5 dicts per D-11
            "fears_found": len(fears),
            "raw_analysis": answer,  # full Perplexity text for Pass 3 LLM
            "source": source,
            "searched_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
        }

        result_json = json.dumps(result, ensure_ascii=False, indent=2)
        _cache[cache_key] = (time.time(), result_json)
        return result_json

    except Exception as e:
        logger.exception("Forum pains extraction error for %s", query_name)
        return json.dumps({
            "error": "Forum pains extraction failed",
            "detail": str(e)[:500],
        }, ensure_ascii=False)


registry.register(
    name="run_forum_pains",
    toolset="aim-operations",
    schema={
            "name": "run_forum_pains",
            "description": (
                "Ищет отзывы пациентов на 4 платформах (ПроДокторов, Otzovik, "
                "IRecommend, Woman.ru) и извлекает топ-5 страхов/жалоб из "
                "текстов отзывов. Возвращает страхи с количеством упоминаний. "
                "Pass 3 LLM использует это для секции Content Analysis (04)."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "url": {
                        "type": "string",
                        "description": "Website URL or clinic name to search patient fears for",
                    },
                    "company_name": {
                        "type": "string",
                        "description": "Clinic name (preferred over URL)",
                    },
                    "city": {
                        "type": "string",
                        "description": "City for geo-targeting (optional)",
                    },
                },
                "required": ["url"],
            },
        },
    handler=handle_run_forum_pains,
    check_fn=lambda: True,
    is_async=True,
    description="Extract top-5 patient fears from review platforms (ПроДокторов, Otzovik, IRecommend, Woman.ru) via Perplexity",
    emoji="😰",
)
