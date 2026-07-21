"""run_review_platforms — Hermes-v2 tool: отзывы клиники по площадкам.

Гибридный подход (замена Perplexity):
- Яндекс.Карты → Apify zen-studio/yandex-maps-reviews-scraper (точные рейтинги + тексты)
- 2ГИС → Apify m_mamaev/2gis-places-scraper (точные рейтинги)
- ПроДокторов → пропускаем (нет готового Apify actor)

Perplexity раньше галлюцинировал рейтинги (4.9 вместо 4.2, выдуманные кол-ва
отзывов). Apify берёт данные напрямую с площадок — точные цифры.

Возвращает JSON в ТОМ ЖЕ формате, что и старая версия (обратная совместимость
с _format_reviews_block в llm.py): {platforms, praise_summary, criticism_summary,
reputation_summary}.
"""
import asyncio
import json
import logging
import time

from app.tools.registry import register

logger = logging.getLogger(__name__)

_cache: dict[str, tuple[float, str]] = {}
_CACHE_TTL = 600  # 10 минут


def _normalize_args(**kwargs) -> tuple[str, str, str]:
    """Привести url/company_name/city к строкам (могут прийти dict из LLM)."""
    def _str(v):
        if isinstance(v, dict):
            # берём первое строковое значение (url/company_name/city)
            return str(next(iter(v.values()), ""))
        return str(v or "").strip()

    return _str(kwargs.get("url")), _str(kwargs.get("company_name")), _str(kwargs.get("city"))


def _extract_themes(review_texts: list[str]) -> tuple[list[str], list[str]]:
    """Грубое извлечение тем «хвалят/критикуют» из реальных текстов отзывов.

    Не заменяет LLM-анализ, но даёт конкретику из настоящих отзывов —
    лучше выдуманных Perplexity тем. Простая эвристика по позитивным/
    негативным маркерам.
    """
    if not review_texts:
        return [], []

    positive_markers = [
        "спасибо", "отлично", "профессионал", "внимательн", "рекомендую",
        "довольн", "помогл", "вежлив", "чисто", "удобно", "быстро",
        "вылечил", "спас", "лучший", "добрый", "забот",
    ]
    negative_markers = [
        "ужас", "больше не", "не рекомендую", "дорог", "очередь",
        "груб", "хам", "некомпетент", "гряз", "обман", "развод",
        "деньги впустую", "не помог", "халатн", "бестолков",
    ]

    praise: list[str] = []
    criticism: list[str] = []

    for text in review_texts:
        text_lower = text.lower()
        for marker in positive_markers:
            if marker in text_lower and len(praise) < 6:
                # вырезаем предложение с маркером (до 120 символов)
                idx = text_lower.find(marker)
                start = text_lower.rfind(". ", 0, idx) + 2 if idx > 0 else 0
                snippet = text[start:idx + 100].strip().rstrip(".")[:120]
                if snippet and snippet not in praise:
                    praise.append(snippet)
                break
        for marker in negative_markers:
            if marker in text_lower and len(criticism) < 6:
                idx = text_lower.find(marker)
                start = text_lower.rfind(". ", 0, idx) + 2 if idx > 0 else 0
                snippet = text[start:idx + 100].strip().rstrip(".")[:120]
                if snippet and snippet not in criticism:
                    criticism.append(snippet)
                break

    return praise, criticism


def _build_summary(yandex: dict | None, gis2: dict | None, company_name: str) -> str:
    """Короткая текстовая сводка репутации из точных данных."""
    parts = []
    if yandex and yandex.get("rating"):
        rating = yandex["rating"]
        tone = "сильная" if rating >= 4.5 else ("средняя" if rating >= 3.8 else "слабая")
        parts.append(f"Яндекс.Карты: {rating}★ ({yandex['reviews']} отз.) — репутация {tone}")
    if gis2 and gis2.get("rating"):
        parts.append(f"2ГИС: {gis2['rating']}★ ({gis2['reviews']} отз.)")
    if not parts:
        return f"Отзывы для «{company_name}» временно недоступны — площадки отзывов не отвечают."
    return " · ".join(parts) + "."


async def handle_run_review_platforms(url: str = "", company_name: str = "", city: str = "", **kwargs) -> str:
    """Сбор отзывов клиники с Яндекс.Карт и 2ГИС через Apify actors.

    Вызывает 2 actor'а параллельно через asyncio.gather. Возвращает JSON
    в формате, совместимом с _format_reviews_block (llm.py).
    """
    url, company_name, city = _normalize_args(url=url, company_name=company_name, city=city)

    cache_key = f"{company_name or url}:{city}"
    cached = _cache.get(cache_key)
    if cached and time.time() - cached[0] < _CACHE_TTL:
        logger.info("review_platforms cache hit: %s", cache_key[:40])
        return cached[1]

    # Периодическая чистка кэша (предотвращает безлимитный рост)
    if len(_cache) > 50:
        now = time.time()
        expired = [k for k, (ts, _) in _cache.items() if now - ts > _CACHE_TTL]
        for k in expired:
            del _cache[k]

    from app.lib import gis2_reviews, yandex_reviews

    # Параллельный вызов 2 площадок (return_exceptions чтобы одна не роняла вторую)
    yandex_result, gis2_result = await asyncio.gather(
        yandex_reviews.search(company_name, city, url or None),
        gis2_reviews.search(company_name, city, url or None),
        return_exceptions=True,
    )

    # Обработка исключений из gather
    if isinstance(yandex_result, Exception):
        logger.error("yandex_reviews raised: %s", yandex_result)
        yandex_result = None
    if isinstance(gis2_result, Exception):
        logger.error("gis2_reviews raised: %s", gis2_result)
        gis2_result = None

    # Сборка в формат, совместимый с _format_reviews_block
    platforms: dict[str, dict] = {
        "yandex": {},
        "twogis": {},
        "prodoctorov": {},  # пропускаем — нет готового Apify actor
    }

    if yandex_result:
        platforms["yandex"] = {
            "rating": yandex_result.get("rating"),
            "reviews": yandex_result.get("reviews", 0),
        }
    if gis2_result:
        platforms["twogis"] = {
            "rating": gis2_result.get("rating"),
            "reviews": gis2_result.get("reviews", 0),
        }

    # Темы отзывов: приоритет — структурированные аспекты Яндекса (точные),
    # fallback — извлечение из текстов отзывов через эвристику
    praise: list[str] = []
    criticism: list[str] = []

    # Яндекс отдаёт структурированные аспекты: [{name: "Персонал", count: 294}]
    if yandex_result and yandex_result.get("aspects"):
        for aspect in yandex_result["aspects"][:6]:
            name = aspect.get("name", "")
            count = aspect.get("count", 0)
            if name and count > 0:
                praise.append(f"{name} ({count} упоминаний)")

    # Fallback: эвристика по текстам отзывов (если аспектов нет)
    if not praise:
        all_reviews = []
        if yandex_result and yandex_result.get("review_texts"):
            all_reviews.extend(yandex_result["review_texts"])
        if gis2_result and gis2_result.get("review_texts"):
            all_reviews.extend(gis2_result["review_texts"])
        praise, criticism = _extract_themes(all_reviews)

    # Нейросводка Яндекса (AI-резюме отзывов от самой площадки)
    neuro_summary = yandex_result.get("neuro_summary", "") if yandex_result else ""

    result = {
        "clinic": company_name or url,
        "platforms": platforms,
        "praise_summary": " | ".join(praise) if praise else "",
        "criticism_summary": " | ".join(criticism) if criticism else "",
        "reputation_summary": _build_summary(yandex_result, gis2_result, company_name or url),
        "neuro_summary": neuro_summary,
        "source": "apify",
        "searched_at": time.strftime("%Y-%m-%d %H:%M"),
    }

    result_json = json.dumps(result, ensure_ascii=False, indent=2)
    _cache[cache_key] = (time.time(), result_json)

    platforms_found = sum(1 for p in result["platforms"].values() if p.get("rating"))
    logger.info(
        "review_platforms OK: %s — %d platforms (yandex=%s gis2=%s)",
        company_name or url,
        platforms_found,
        yandex_result.get("rating") if yandex_result else None,
        gis2_result.get("rating") if gis2_result else None,
    )
    return result_json


register(
    name="run_review_platforms",
    schema={
        "type": "function",
        "function": {
            "name": "run_review_platforms",
            "description": (
                "Собрать отзывы и рейтинги клиники с Яндекс.Карт и 2ГИС (через Apify). "
                "Возвращает ТОЧНЫЕ рейтинги с площадок и темы: за что хвалят, за что критикуют "
                "(извлечённые из реальных текстов отзывов). "
                "ВЫЗЫВАЙ когда клиент прислал URL сайта (параллельно с конкурентами)."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "url": {"type": "string", "description": "URL сайта клиники"},
                    "company_name": {"type": "string", "description": "Название клиники"},
                    "city": {"type": "string", "description": "Город клиники"},
                },
                "required": ["url"],
            },
        },
    },
    handler=handle_run_review_platforms,
)
