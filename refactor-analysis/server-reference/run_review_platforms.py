"""
run_review_platforms — Hermes tool: Review Platforms Scanner

Ищет отзывы клиники через DuckDuckGo по платформам:
ProDoctorov, Яндекс.Карты, 2ГИС, Google Maps, otzovik.com, irecommend.ru, zoon.ru.
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

REVIEW_PLATFORMS = {
    "prodoctorov": {
        "name": "ПроДокторов",
        "search": "site:prodoctorov.ru",
        "weight": 0.25,
    },
    "yandex_maps": {
        "name": "Яндекс.Карты",
        "search": "site:yandex.ru/maps",
        "weight": 0.20,
    },
    "2gis": {
        "name": "2ГИС",
        "search": "site:2gis.ru",
        "weight": 0.20,
    },
    "google_maps": {
        "name": "Google Maps",
        "search": "site:google.com/maps",
        "weight": 0.10,
    },
    "otzovik": {
        "name": "Отзовик",
        "search": "site:otzovik.com",
        "weight": 0.10,
    },
    "irecommend": {
        "name": "IRecommend",
        "search": "site:irecommend.ru",
        "weight": 0.10,
    },
    "zoon": {
        "name": "Zoon",
        "search": "site:zoon.ru",
        "weight": 0.05,
    },
}


def _normalize_args(first_param, defaults):
    if isinstance(first_param, dict):
        return {k: first_param.get(k, defaults[k]) for k in defaults}
    return None


async def handle_run_review_platforms(url=None, company_name="", city="", **kwargs) -> str:
    """Scan review platforms for a clinic using DuckDuckGo.

    Args:
        url: Website URL to search reviews for.
        company_name: Clinic name (used as search target if url not provided).
        city: City for geo-targeted review search.

    Returns:
        JSON with discovered reviews, ratings, platform links.
    """
    unpacked = _normalize_args(url, {"url": ""})
    if unpacked:
        url = unpacked["url"]
        company_name = unpacked.get("company_name", company_name)
        city = unpacked.get("city", city)

    cn = kwargs.get("company_name", "")
    if cn and not company_name:
        company_name = cn
    ct = kwargs.get("city", "")
    if ct and not city:
        city = ct

    search_target = url or company_name or ""
    if search_target and not search_target.startswith("http"):
        pass
    elif search_target and search_target.startswith("http"):
        from urllib.parse import urlparse
        parsed = urlparse(search_target)
        domain = parsed.netloc.replace("www.", "")
        company_name = company_name or domain

    if not search_target and not company_name:
        return json.dumps({"error": "URL or clinic name is required"})

    query_name = company_name or search_target
    if city:
        query_name = f"{query_name} {city}"

    cache_key = f"reviews_{query_name}"
    cached = _cache.get(cache_key)
    if cached is not None:
        cached_ts, cached_result = cached
        if time.time() - cached_ts < _CACHE_TTL:
            return cached_result
        del _cache[cache_key]

    logger.info("Scanning review platforms for: %s", query_name)

    try:
        from app.main import push_tool_progress
        from app.tools._search_fallback import search as fallback_search

        push_tool_progress("reviews", f"⭐ Ищу отзывы для {query_name}…")

        platform_results: dict[str, dict] = {}
        all_links: list[dict] = []

        # Параллельный поиск по всем платформам
        platform_keys = list(REVIEW_PLATFORMS.keys())
        coros = [
            fallback_search(f'"{query_name}" отзывы {REVIEW_PLATFORMS[k]["search"]}', max_results=3)
            for k in platform_keys
        ]
        raw_results = await asyncio.gather(*coros, return_exceptions=True)
        # Unpack (results, provider) tuples
        search_results = []
        for item in raw_results:
            if isinstance(item, Exception):
                search_results.append(item)
            elif isinstance(item, tuple) and len(item) == 2:
                search_results.append(item[0])  # just the results list
            else:
                search_results.append(item)

        for key, results in zip(platform_keys, search_results):
            plat = REVIEW_PLATFORMS[key]
            if isinstance(results, Exception):
                logger.warning("Review search exception for %s: %s", key, results)
                platform_results[key] = {"platform": plat["name"], "found": 0, "links": []}
                continue
            if results:
                links = []
                for r in results:
                    link = {
                        "title": r.get("title", ""),
                        "url": r.get("url", ""),
                        "description": (r.get("description", "") or "")[:200],
                    }
                    links.append(link)
                    all_links.append(link)
                platform_results[key] = {
                    "platform": plat["name"],
                    "found": len(links),
                    "links": links,
                }
            else:
                platform_results[key] = {
                    "platform": plat["name"],
                    "found": 0,
                    "links": [],
                }

        total_found = sum(p["found"] for p in platform_results.values())
        covered_platforms = sum(1 for p in platform_results.values() if p["found"] > 0)

        result = {
            "search_term": query_name,
            "total_mentions": total_found,
            "platforms_with_results": covered_platforms,
            "platforms_total": len(REVIEW_PLATFORMS),
            "platforms": platform_results,
            "top_links": all_links[:10],
            "source": "DuckDuckGo",
        }

        push_tool_progress("reviews", f"✅ Найдено упоминаний: {total_found} на {covered_platforms} платформах")
        result_json = json.dumps(result, ensure_ascii=False, indent=2)
        _cache[cache_key] = (time.time(), result_json)
        return result_json

    except Exception as e:
        logger.exception("Review scan error")
        return json.dumps({"error": "Unexpected error", "detail": str(e)})


registry.register(
    name="run_review_platforms",
    toolset="aim-operations",
    schema={
        "type": "function",
        "function": {
            "name": "run_review_platforms",
            "description": "Scan all review platforms (ProDoctorov, Yandex Maps, 2GIS, Google Maps, otzovik, irecommend, zoon.ru) for clinic ratings and patient reviews.",
            "parameters": {
                "type": "object",
                "properties": {
                    "url": {"type": "string", "description": "Website URL or clinic name to search reviews for"},
                },
                "required": ["url"],
            },
        },
    },
    handler=handle_run_review_platforms,
    check_fn=lambda: True,
    is_async=True,
    description="Scan review platforms for clinic ratings and patient reviews",
    emoji="⭐",
)
