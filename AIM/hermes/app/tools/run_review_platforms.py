"""
run_review_platforms — Hermes tool: Review Platforms Scanner (v2)

Использует Perplexity (sonar-pro) для сбора реальных рейтингов и отзывов
клиники по платформам: Яндекс.Карты, Google Maps, ПроДокторов, 2ГИС,
Отзовик, IRecommend, Zoon.

Fallback: DeepSeek через OMNIROUTE (если PERPLEXITY_API_KEY не задан).
"""

import json
import logging
import os
import time

from tools.registry import registry

logger = logging.getLogger(__name__)

PERPLEXITY_API_KEY = os.getenv("PERPLEXITY_API_KEY", "").strip()
PERPLEXITY_BASE_URL = "https://api.perplexity.ai"
PERPLEXITY_MODEL = "sonar-pro"
USE_PERPLEXITY = bool(PERPLEXITY_API_KEY)

# Fallback LLM
LLM_BASE_URL = os.getenv("LLM_BASE_URL", os.getenv("OMNIROUTE_URL", "https://api.deepseek.com/v1"))
LLM_API_KEY = os.getenv("LLM_API_KEY", os.getenv("OMNIROUTE_AUTH", os.getenv("DEEPSEEK_API_KEY", "")))
LLM_MODEL = os.getenv("LLM_MODEL", "deepseek-chat")

REQUEST_TIMEOUT = 90.0
MAX_TOKENS = 8000

_cache: dict[str, tuple[float, str]] = {}
_CACHE_TTL = 600

REVIEW_PLATFORMS = [
    {"name": "Яндекс.Карты", "weight": 0.25},
    {"name": "Google Maps", "weight": 0.15},
    {"name": "ПроДокторов", "weight": 0.25},
    {"name": "2ГИС", "weight": 0.15},
    {"name": "Отзовик", "weight": 0.08},
    {"name": "IRecommend", "weight": 0.07},
    {"name": "Zoon", "weight": 0.05},
]


def _normalize_args(first_param, defaults):
    if isinstance(first_param, dict):
        return {k: first_param.get(k, defaults[k]) for k in defaults}
    return None


def _build_query(company_name: str, city: str, url: str) -> str:
    """Построить Perplexity-запрос для сбора отзывов.

    Использует пошаговый формат — заставляет Perplexity искать каждую
    платформу отдельным шагом, а не поверхностно по всем сразу.
    """
    target = company_name or url
    location = f" (г. {city})" if city else ""
    website = f", сайт: {url}" if url and url.startswith("http") else ""

    return (
        f"Найди актуальные рейтинги и отзывы о клинике «{target}»{location}{website} "
        f"на следующих платформах.\n\n"
        "ВАЖНО: для каждой платформы выполни ОТДЕЛЬНЫЙ поиск. Не пропускай платформы, "
        "даже если кажется что данных нет. Указывай точные цифры из карточки клиники.\n\n"
        "## Шаг 1 — Яндекс.Карты\n"
        "Найди страницу клиники на Яндекс.Картах (yandex.ru/maps). Укажи:\n"
        "- Адрес филиала (если несколько — основные)\n"
        "- Точный рейтинг (звёзды)\n"
        "- Точное количество отзывов\n"
        "- Главные темы положительных отзывов (с примерами)\n"
        "- Главные темы отрицательных отзывов (с примерами)\n"
        "- Отвечает ли клиника на отзывы\n\n"
        "## Шаг 2 — Google Maps\n"
        "Найди страницу клиники на Google Maps (google.com/maps). Укажи:\n"
        "- Точный рейтинг (звёзды)\n"
        "- Количество отзывов\n"
        "- Главные темы положительных и отрицательных отзывов\n"
        "Если клиника не найдена — напиши «Не найден на Google Maps».\n\n"
        "## Шаг 3 — ПроДокторов\n"
        "Найди страницу клиники на prodoctorov.ru. Укажи:\n"
        "- Рейтинг, количество отзывов\n"
        "- Основные темы хвалят/жалуются\n"
        "Если клиника не найдена — напиши «Не найден на ПроДокторов».\n\n"
        "## Шаг 4 — 2ГИС\n"
        "Найди страницу клиники на 2gis.ru. Укажи рейтинг, отзывы, темы.\n"
        "Если нет — напиши «Не найден на 2ГИС».\n\n"
        "## Шаг 5 — Отзовик, IRecommend, Zoon\n"
        "Проверь наличие клиники на otzovik.com, irecommend.ru, zoon.ru.\n"
        "Если найдено — укажи рейтинг и количество отзывов.\n"
        "Если нет — напиши «Не найден».\n\n"
        "В конце дай СВОДКУ:\n"
        "- Суммарный средний рейтинг по всем платформам\n"
        "- Главный репутационный риск (1 предложение)\n"
        "- Главное конкурентное преимущество в глазах пациентов (1 предложение)"
    )


def _build_system_prompt() -> str:
    return (
        "Ты — аналитик репутации медицинских клиник. "
        "Твоя задача — найти актуальные рейтинги и отзывы о клинике на всех платформах. "
        "Ищи фактические данные: звёзды, количество отзывов, тексты отзывов. "
        "Если платформа недоступна или данных нет — честно скажи об этом. "
        "Не выдумывай рейтинги. Каждый факт должен быть из реальной выдачи."
    )


async def _call_perplexity(prompt: str) -> str:
    """Вызвать Perplexity API (sonar-pro, web search)."""
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
    """Fallback: LLM через OMNIROUTE (без web search)."""
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
                    "Ты — аналитик репутации медицинских клиник. "
                    "У тебя нет доступа к интернету, поэтому если ты не знаешь "
                    "точных данных о клинике — честно напиши об этом. "
                    "Не выдумывай рейтинги и цифры."
                ),
            },
            {"role": "user", "content": prompt},
        ],
        temperature=0.2,
        max_tokens=MAX_TOKENS,
    )
    return response.choices[0].message.content or ""


async def handle_run_review_platforms(url=None, company_name="", city="", **kwargs) -> str:
    """Scan review platforms for a clinic using Perplexity web search.

    Uses Perplexity sonar-pro to search for real ratings and reviews
    across all major review platforms. Falls back to LLM if no Perplexity key.

    Args:
        url: Website URL (used if company_name is empty).
        company_name: Clinic name for search.
        city: City for geo-targeting.

    Returns:
        JSON with structured review data: ratings, counts, key themes per platform.
    """
    unpacked = _normalize_args(url, {"url": ""})
    if unpacked:
        url = unpacked["url"]
        company_name = unpacked.get("company_name", company_name)
        city = unpacked.get("city", city)

    # Also check kwargs
    cn = kwargs.get("company_name", "")
    if cn and not company_name:
        company_name = cn
    ct = kwargs.get("city", "")
    if ct and not city:
        city = ct

    search_target = url or company_name or ""
    if not search_target:
        return json.dumps({"error": "URL or clinic name is required"}, ensure_ascii=False)

    # Extract domain as name fallback
    if search_target.startswith("http") and not company_name:
        from urllib.parse import urlparse
        parsed = urlparse(search_target)
        company_name = parsed.netloc.replace("www.", "")

    query_name = company_name or search_target

    cache_key = f"reviews_v2_{query_name}_{city}"
    cached = _cache.get(cache_key)
    if cached is not None:
        cached_ts, cached_result = cached
        if time.time() - cached_ts < _CACHE_TTL:
            logger.info("Review cache HIT for: %s", query_name)
            return cached_result
        del _cache[cache_key]

    logger.info("Scanning reviews (Perplexity=%s) for: %s, city=%s",
                "available" if USE_PERPLEXITY else "unavailable", query_name, city)

    try:
        from app.main import push_tool_progress

        push_tool_progress("reviews", f"⭐ Ищу отзывы о {query_name}…")

        query = _build_query(query_name, city, url)
        source = ""

        if USE_PERPLEXITY:
            push_tool_progress("reviews", "🔍 Perplexity ищет рейтинги по всем платформам…")
            answer = await _call_perplexity(query)
            source = f"perplexity ({PERPLEXITY_MODEL})"
        else:
            push_tool_progress("reviews", "⚠️ Perplexity недоступен, использую LLM (без web search)…")
            answer = await _call_llm(query)
            source = f"llm ({LLM_MODEL}) — без веб-поиска"

        push_tool_progress("reviews", "✅ Данные об отзывах собраны")

        # Estimate review count from the answer (rough heuristic)
        import re
        total_reviews_est = 0
        for m in re.finditer(r'[Оо]тзывов[:\s]*(\d[\d\s]*\d)', answer):
            try:
                total_reviews_est += int(m.group(1).replace(" ", ""))
            except ValueError:
                pass

        platforms_found = len(re.findall(r'##\s+(Яндекс|Google|Продокторов|2ГИС|Отзовик|IRecommend|Zoon)', answer, re.IGNORECASE))

        result = {
            "clinic": query_name,
            "city": city or "не указан",
            "platforms_searched": len(REVIEW_PLATFORMS),
            "platforms_found": platforms_found,
            "total_reviews_estimated": total_reviews_est or None,
            "analysis": answer,
            "source": source,
            "searched_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
        }

        result_json = json.dumps(result, ensure_ascii=False, indent=2)
        _cache[cache_key] = (time.time(), result_json)
        return result_json

    except Exception as e:
        logger.exception("Review scan error for %s", query_name)
        return json.dumps({
            "error": "Review scan failed",
            "detail": str(e)[:500],
        }, ensure_ascii=False)


registry.register(
    name="run_review_platforms",
    toolset="aim-operations",
    schema={
            "name": "run_review_platforms",
            "description": (
                "Scan all review platforms (ProDoctorov, Yandex Maps, 2GIS, Google Maps, "
                "otzovik, irecommend, zoon.ru) for clinic ratings and patient reviews. "
                "Uses Perplexity web search to find real ratings, review counts, "
                "and key patient feedback themes. Returns structured analysis per platform "
                "with praise/complaint themes and reputation summary."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "url": {
                        "type": "string",
                        "description": "Website URL or clinic name to search reviews for",
                    },
                },
                "required": ["url"],
            },
        },
    handler=handle_run_review_platforms,
    check_fn=lambda: True,
    is_async=True,
    description="Scan review platforms (Perplexity): ratings, reviews, patient sentiment per platform",
    emoji="⭐",
)
