"""
run_smi_mentions — Hermes tool: SMI (Mass Media) Mentions Search

Ищет упоминания клиники в СМИ через DuckDuckGo:
- Business: forbes.ru, rbc.ru, kommersant.ru, vedomosti.ru
- Medical: vademec.ru, medvestnik.ru
- Regional: fontanka.ru, dp.ru, sobaka.ru
- Telegram-media: t.me (Mash, Baza, 112, SHOT)
"""

import asyncio
import json
import logging
import time

from tools.registry import registry

logger = logging.getLogger(__name__)

REQUEST_TIMEOUT = 30.0

_cache: dict[str, tuple[float, str]] = {}
_CACHE_TTL = 600

# Категории СМИ для поиска
MEDIA_SOURCES = {
    "business": {
        "name": "Деловые СМИ",
        "domains": [
            "forbes.ru", "rbc.ru", "kommersant.ru", "vedomosti.ru",
            "tass.ru", "ria.ru", "interfax.ru",
        ],
        "weight": 0.35,
    },
    "medical": {
        "name": "Медицинские СМИ",
        "domains": [
            "vademec.ru", "medvestnik.ru", "medportal.ru",
            "doctorpiter.ru", "medlinks.ru",
        ],
        "weight": 0.30,
    },
    "regional": {
        "name": "Региональные СМИ",
        "domains": [
            "fontanka.ru", "dp.ru", "sobaka.ru", "mk.ru",
            "kp.ru", "aif.ru", "rg.ru",
        ],
        "weight": 0.20,
    },
    "lifestyle": {
        "name": "Lifestyle / Глянец",
        "domains": [
            "marieclaire.ru", "vogue.ru", "cosmopolitan.ru",
            "tatler.ru", "graziamagazine.ru", "buro247.ru",
        ],
        "weight": 0.15,
    },
}


def _normalize_args(first_param, defaults):
    if isinstance(first_param, dict):
        return {k: first_param.get(k, defaults[k]) for k in defaults}
    return None


async def handle_run_smi_mentions(url=None, company_name="", **kwargs) -> str:
    """Search SMI mentions for a clinic using DuckDuckGo.

    Searches across business, medical, regional, and lifestyle media sources.

    Args:
        url: Website URL to search mentions for.
        company_name: Clinic name (used as search target if url not provided).

    Returns:
        JSON with mentions per category: source, title, url, description.
    """
    unpacked = _normalize_args(url, {"url": ""})
    if unpacked:
        url = unpacked["url"]
        company_name = unpacked.get("company_name", company_name)

    cn = kwargs.get("company_name", "")
    if cn and not company_name:
        company_name = cn

    search_target = url or company_name or ""
    if not search_target:
        return json.dumps({"error": "URL or clinic name is required"})

    if search_target.startswith("http"):
        from urllib.parse import urlparse
        parsed = urlparse(search_target)
        domain = parsed.netloc.replace("www.", "")
        company_name = company_name or domain

    query_name = company_name or search_target

    cache_key = f"smi_{query_name}"
    cached = _cache.get(cache_key)
    if cached is not None:
        cached_ts, cached_result = cached
        if time.time() - cached_ts < _CACHE_TTL:
            return cached_result
        del _cache[cache_key]

    logger.info("Searching SMI mentions for: %s", query_name)

    try:
        from app.main import push_tool_progress
        from app.tools._search_fallback import search as fallback_search

        push_tool_progress("smi", f"📰 Ищу упоминания в СМИ для {query_name}…")

        category_results: dict[str, dict] = {}
        all_mentions: list[dict] = []
        providers_used: set[str] = set()

        # Параллельный поиск по всем категориям
        cat_keys = list(MEDIA_SOURCES.keys())
        coros = []
        for cat_key in cat_keys:
            cat = MEDIA_SOURCES[cat_key]
            site_filter = " OR ".join(f"site:{d}" for d in cat["domains"][:3])
            query = f'"{query_name}" ({site_filter})'
            coros.append(fallback_search(query, max_results=5))
        raw_results = await asyncio.gather(*coros, return_exceptions=True)

        # Unpack (results, provider) tuples from fallback_search
        search_results = []
        for item in raw_results:
            if isinstance(item, Exception):
                search_results.append(item)
            elif isinstance(item, tuple) and len(item) == 2:
                search_results.append(item[0])
                providers_used.add(item[1])
            else:
                search_results.append(item)

        for cat_key, results in zip(cat_keys, search_results):
            cat = MEDIA_SOURCES[cat_key]
            if isinstance(results, Exception):
                logger.warning("SMI search exception for %s: %s", cat_key, results)
                category_results[cat_key] = {
                    "category": cat["name"],
                    "weight": cat["weight"],
                    "mentions_found": 0,
                    "mentions": [],
                }
                continue

            mentions = []
            for r in results:
                mention = {
                    "source": r.get("url", "").split("/")[2] if "/" in r.get("url", "") else "unknown",
                    "title": r.get("title", ""),
                    "url": r.get("url", ""),
                    "description": (r.get("description", "") or "")[:200],
                    "date": r.get("age", ""),
                }
                mentions.append(mention)
                all_mentions.append(mention)

            category_results[cat_key] = {
                "category": cat["name"],
                "weight": cat["weight"],
                "mentions_found": len(mentions),
                "mentions": mentions,
            }

        total = sum(c["mentions_found"] for c in category_results.values())
        categories_with_hits = sum(1 for c in category_results.values() if c["mentions_found"] > 0)

        # Fallback: если site:search дал 0 — широкий запрос через Perplexity
        if total == 0:
            try:
                from app.tools.perplexity_tools import handle_perplexity_search
                broad_q = (
                    f'Найди упоминания клиники "{query_name}" в российских СМИ. '
                    f'Проверь Forbes, РБК, Коммерсантъ, Vademecum, Медвестник, региональную прессу. '
                    f'Также проверь Telegram-каналы (Mash, Baza, 112, SHOT). '
                    f'Для каждого упоминания верни: название издания, заголовок статьи, URL, дата. '
                    f'Если публикаций нет — честно скажи "не найдено в открытых источниках".'
                )
                broad_r = await handle_perplexity_search(question=broad_q, context="")
                broad_d = json.loads(broad_r)
                broad_answer = broad_d.get("answer", "") if isinstance(broad_d, dict) else ""
                if broad_answer and len(broad_answer) > 50:
                    # Простой парсинг: ищем URL'ы в ответе
                    import re as _re
                    urls = _re.findall(r'https?://[^\s)<>"]+', broad_answer)
                    # Каждое упоминание = URL + контекст
                    fallback_mentions = []
                    if urls:
                        # Группируем по домену в категорию
                        for url in urls[:10]:
                            domain = url.split("/")[2] if "/" in url else ""
                            fallback_mentions.append({
                                "source": domain,
                                "title": "",
                                "url": url,
                                "description": "",
                                "date": "",
                            })
                    # Добавляем ответ Perplexity как "broad" категорию
                    category_results["broad_search"] = {
                        "category": "Широкий поиск (Perplexity)",
                        "weight": 0.40,
                        "mentions_found": len(fallback_mentions),
                        "mentions": fallback_mentions,
                        "analysis": broad_answer[:2000],
                    }
                    all_mentions.extend(fallback_mentions)
                    providers_used.add("perplexity")
                    total = sum(c["mentions_found"] for c in category_results.values())
                    categories_with_hits = sum(1 for c in category_results.values() if c["mentions_found"] > 0)
                    logger.info("SMI fallback (broad Perplexity) → %d mentions", len(fallback_mentions))
            except Exception as e:
                logger.warning("SMI broad fallback failed: %s", e)

        result = {
            "search_term": query_name,
            "total_mentions": total,
            "categories_with_mentions": categories_with_hits,
            "categories_total": len(MEDIA_SOURCES),
            "categories": category_results,
            "top_mentions": sorted(all_mentions, key=lambda m: len(m.get("description", "")))[:10],
            "source": ", ".join(sorted(providers_used)) if providers_used else "none",
        }

        push_tool_progress("smi", f"✅ Найдено {total} упоминаний в {categories_with_hits} категориях СМИ")
        result_json = json.dumps(result, ensure_ascii=False, indent=2)
        _cache[cache_key] = (time.time(), result_json)
        return result_json

    except Exception as e:
        logger.exception("SMI search error")
        return json.dumps({"error": "Unexpected error", "detail": str(e)})


registry.register(
    name="run_smi_mentions",
    toolset="aim-operations",
    schema={
            "name": "run_smi_mentions",
            "description": "Search mass media mentions for a clinic across Business (Forbes, RBC), Medical (Vademec), Regional, and Lifestyle sources.",
            "parameters": {
                "type": "object",
                "properties": {
                    "url": {"type": "string", "description": "Website URL or clinic name to search media mentions for"},
                },
                "required": ["url"],
            },
        },
    handler=handle_run_smi_mentions,
    check_fn=lambda: True,
    is_async=True,
    description="Search SMI/media mentions across business, medical, regional, and lifestyle sources",
    emoji="📰",
)
