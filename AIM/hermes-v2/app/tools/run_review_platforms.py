"""run_review_platforms — Hermes-v2 tool: отзывы клиники по площадкам.

Использует Perplexity (sonar) для поиска реальных рейтингов и ТЕМ отзывов
на Яндекс.Картах, ПроДокторов и 2ГИС. Возвращает структурированный JSON с
темами (хвалят/критикуют) для отображения в блоке «Отзывы».
"""
import json
import logging
import time

from app.lib.perplexity import USE_PERPLEXITY, perplexity_chat
from app.tools.registry import register

logger = logging.getLogger(__name__)

_cache: dict[str, tuple[float, str]] = {}
_CACHE_TTL = 600  # 10 минут


def _build_query(company_name: str, city: str, url: str) -> str:
    """Построить Perplexity-запрос для сбора отзывов по 3 площадкам."""
    target = company_name or url
    location = f" (г. {city})" if city else ""

    return (
        f"Найди отзывы о клинике «{target}»{location} на платформах.\n\n"
        "Для каждой платформы укажи рейтинг, кол-во отзывов и ГЛАВНЫЕ ТЕМЫ.\n\n"
        "## Яндекс.Карты\n"
        "- Рейтинг (звёзды) и кол-во отзывов\n"
        "- За что хвалят (2-3 конкретные темы с примерами)\n"
        "- За что критикуют (2-3 темы)\n\n"
        "## ПроДокторов\n"
        "- Рейтинг и кол-во отзывов\n"
        "- Каких врачей хвалят (по именам)\n"
        "- Жалобы\n\n"
        "## 2ГИС\n"
        "- Рейтинг и кол-во отзывов\n"
        "- Темы положительных и отрицательных\n\n"
        "Формат ответа:\n"
        "ЯНДЕКС: рейтинг X.X, отзывов N\n"
        "Хвалят: тема1, тема2\n"
        "Критикуют: тема1, тема2\n"
        "ПРОДОКТОРОВ: рейтинг X.X, отзывов N\n"
        "Хвалят: ...\n"
        "Критикуют: ...\n"
        "2ГИС: рейтинг X.X, отзывов N\n"
        "Хвалят: ...\n"
        "Критикуют: ...\n"
        "ОБЩИЙ ВЫВОД: 2-3 предложения о репутации клиники"
    )


def _parse_response(raw: str, company_name: str) -> dict:
    """Парсит текстовый ответ Perplexity в структурированный dict."""
    import re

    sections = {"yandex": {}, "prodoctorov": {}, "twogis": {}}
    text = raw.strip()

    # Рейтинги: "ЯНДЕКС: рейтинг 4.9, отзывов 681"
    # Ограничиваем .*? до конца строки рейтинга (не перескакивает через другие секции)
    yandex_match = re.search(r"ЯНДЕКС[^\n]*?рейтинг\s*(\d+[.,]?\d*)[^\n]*?отзывов?\s*(\d+)", text, re.I)
    if yandex_match:
        sections["yandex"]["rating"] = float(yandex_match.group(1).replace(",", "."))
        sections["yandex"]["reviews"] = int(yandex_match.group(2))

    pd_match = re.search(r"ПРОДОКТОРОВ[^\n]*?рейтинг\s*(\d+[.,]?\d*)[^\n]*?отзывов?\s*(\d+)", text, re.I)
    if pd_match:
        sections["prodoctorov"]["rating"] = float(pd_match.group(1).replace(",", "."))
        sections["prodoctorov"]["reviews"] = int(pd_match.group(2))

    twogis_match = re.search(r"2ГИС[^\n]*?рейтинг\s*(\d+[.,]?\d*)[^\n]*?отзывов?\s*(\d+)", text, re.I)
    if twogis_match:
        sections["twogis"]["rating"] = float(twogis_match.group(1).replace(",", "."))
        sections["twogis"]["reviews"] = int(twogis_match.group(2))

    # Темы: "Хвалят: ..." и "Критикуют: ..."
    for platform_key, platform_name in [("yandex", "ЯНДЕКС"), ("prodoctorov", "ПРОДОКТОРОВ"), ("twogis", "2ГИС")]:
        # Найти секцию платформы
        platform_start = text.upper().find(platform_name)
        if platform_start == -1:
            continue
        # Секция заканчивается на начале следующей платформы или "ОБЩИЙ"
        next_sections = []
        for pn in ["ПРОДОКТОРОВ", "2ГИС", "ОБЩИЙ"]:
            pos = text.upper().find(pn, platform_start + len(platform_name))
            if pos != -1:
                next_sections.append(pos)
        platform_end = min(next_sections) if next_sections else len(text)
        section = text[platform_start:platform_end]

        praise_match = re.search(r"Хвалят[:\s]*(.+?)(?:Критикуют|ПРОДОКТОРОВ|2ГИС|ОБЩИЙ|$)", section, re.I | re.S)
        if praise_match:
            sections[platform_key]["praise"] = praise_match.group(1).strip()[:300]

        crit_match = re.search(r"Критикуют[:\s]*(.+?)(?:ПРОДОКТОРОВ|2ГИС|ОБЩИЙ|$)", section, re.I | re.S)
        if crit_match:
            sections[platform_key]["criticism"] = crit_match.group(1).strip()[:300]

    # Общий вывод
    summary_match = re.search(r"ОБЩИЙ ВЫВОД[:\s]*(.+)", text, re.I | re.S)
    summary = summary_match.group(1).strip()[:500] if summary_match else ""

    # Агрегированные темы (объединяем по всем платформам)
    all_praise = [s["praise"] for s in sections.values() if s.get("praise")]
    all_crit = [s["criticism"] for s in sections.values() if s.get("criticism")]

    return {
        "clinic": company_name,
        "platforms": sections,
        "praise_summary": " | ".join(all_praise) if all_praise else "",
        "criticism_summary": " | ".join(all_crit) if all_crit else "",
        "reputation_summary": summary,
        "source": "perplexity",
        "searched_at": time.strftime("%Y-%m-%d %H:%M"),
    }


async def handle_run_review_platforms(url: str = "", company_name: str = "", city: str = "", **kwargs) -> str:
    """Сбор отзывов клиники по площадкам через Perplexity."""
    if not USE_PERPLEXITY:
        return json.dumps({"error": "PERPLEXITY_API_KEY not configured"})

    # Нормализация
    if isinstance(url, dict):
        url = url.get("url", "")
    if isinstance(company_name, dict):
        company_name = company_name.get("company_name", "")
    if isinstance(city, dict):
        city = city.get("city", "")

    cache_key = f"{company_name or url}:{city}"
    cached = _cache.get(cache_key)
    if cached and time.time() - cached[0] < _CACHE_TTL:
        logger.info("review_platforms cache hit: %s", cache_key[:40])
        return cached[1]

    # Periodic cleanup of expired entries (prevents unbounded growth)
    if len(_cache) > 50:
        now = time.time()
        expired = [k for k, (ts, _) in _cache.items() if now - ts > _CACHE_TTL]
        for k in expired:
            del _cache[k]

    try:
        query = _build_query(company_name, city, url)
        raw = await perplexity_chat(
            [{"role": "user", "content": query}],
            model="sonar",  # sonar даёт URL источников
        )
        result = _parse_response(raw, company_name or url)
        result_json = json.dumps(result, ensure_ascii=False, indent=2)
        _cache[cache_key] = (time.time(), result_json)
        platforms_found = sum(1 for p in result["platforms"].values() if p.get("rating"))
        logger.info("review_platforms OK: %s — %d platforms found", company_name or url, platforms_found)
        return result_json
    except Exception as e:
        logger.error("review_platforms failed: %s", e)
        return json.dumps({"error": str(e), "clinic": company_name or url})


register(
    name="run_review_platforms",
    schema={
        "type": "function",
        "function": {
            "name": "run_review_platforms",
            "description": (
                "Собрать отзывы и рейтинги клиники с Яндекс.Карт, ПроДокторов, 2ГИС. "
                "Возвращает темы: за что хвалят, за что критикуют. "
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
