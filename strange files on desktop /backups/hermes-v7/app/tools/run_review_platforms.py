"""
run_review_platforms — Hermes tool: Review Platform Aggregator

Searches for clinic reviews across major Russian platforms:
- 2GIS (maps/ratings)
- Yandex.Maps (maps/ratings)
- Google Maps (maps/ratings)
- ProDoctorov (medical ratings)
- Zoon (business ratings)
- Yell (business ratings)

Uses Firecrawl search API for each platform in parallel.
Registered in Hermes internal registry under toolset "aim-operations".
"""

import asyncio
import json
import logging
import re

import httpx

from .firecrawl_key_bank import get_key_with_fallback, mark_exhausted, classify_exhaustion
from tools.registry import registry

logger = logging.getLogger(__name__)

REQUEST_TIMEOUT = 180.0
FIRECRAWL_SEARCH = "https://api.firecrawl.dev/v2/search"
FIRECRAWL_SCRAPE = "https://api.firecrawl.dev/v2/scrape"
_MAX_RETRIES = 3

REVIEW_PLATFORMS = [
    {
        "name": "2GIS",
        "domain": "2gis.ru",
        "query_template": '{company_name} site:2gis.ru',
        "category": "maps",
        "icon": "🗺️",
    },
    {
        "name": "Яндекс.Карты",
        "domain": "yandex.ru/maps",
        "query_template": '{company_name} отзывы site:yandex.ru/maps',
        "category": "maps",
        "icon": "📍",
    },
    {
        "name": "Google Maps",
        "domain": "google.com/maps",
        "query_template": '{company_name} clinic reviews site:google.com/maps',
        "category": "maps",
        "icon": "🌍",
    },
    {
        "name": "ProDoctorov",
        "domain": "prodoctorov.ru",
        "query_template": '{company_name} site:prodoctorov.ru',
        "category": "medical",
        "icon": "🏥",
    },
    {
        "name": "Zoon",
        "domain": "zoon.ru",
        "query_template": '{company_name} site:zoon.ru',
        "category": "business",
        "icon": "📋",
    },
    {
        "name": "Yell",
        "domain": "yell.ru",
        "query_template": '{company_name} site:yell.ru',
        "category": "business",
        "icon": "📝",
    },
    {
        "name": "Отзовик",
        "domain": "otzovik.com",
        "query_template": '{company_name} site:otzovik.com',
        "category": "reviews",
        "icon": "💬",
    },
    {
        "name": "IRecommend",
        "domain": "irecommend.ru",
        "query_template": '{company_name} site:irecommend.ru',
        "category": "reviews",
        "icon": "👍",
    },
]


async def handle_run_review_platforms(company_name=None, city=None, **kwargs) -> str:
    """Aggregate clinic reviews from all major platforms.

    Searches 2GIS, Yandex.Maps, Google Maps, ProDoctorov, Zoon, Yell,
    Otzovik, and IRecommend for clinic ratings and reviews.
    Returns per-platform stats and an overall reputation score.

    Args:
        company_name: Clinic or company name (e.g., "СМ-Клиника")
        city: Optional city for geo-targeting (e.g., "Санкт-Петербург")

    Returns:
        JSON with per-platform ratings, review counts, sentiment summary,
        and overall reputation score.
    """
    if isinstance(company_name, dict):
        d = company_name
        company_name = d.get("company_name", "")
        if city is None:
            city = d.get("city", "")

    if not company_name:
        try:
            cached = Path("/tmp/hermes_last_company.txt").read_text().strip()
            if cached:
                logger.info("Using cached company name: %s", cached)
                company_name = cached
        except Exception:
            pass

    if not company_name:
        return json.dumps({"error": "company_name is required"})

    logger.info("Review aggregation for: %s (city: %s)", company_name, city)

    from app.main import push_tool_progress

    push_tool_progress(
        "reviews",
        f"Собираю отзывы о «{company_name}» на 8 платформах…",
    )

    search_query = f"{company_name} {city}".strip() if city else company_name

    try:
        async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT) as client:
            results = []

            # Search in batches of 3
            platforms_to_search = REVIEW_PLATFORMS[:8]

            for i in range(0, len(platforms_to_search), 3):
                batch = platforms_to_search[i:i + 3]

                tasks = [
                    _search_platform(client, platform, search_query)
                    for platform in batch
                ]
                batch_results = await asyncio.gather(*tasks, return_exceptions=True)

                for j, result in enumerate(batch_results):
                    platform = batch[j]
                    if isinstance(result, Exception):
                        logger.warning("Review search failed for %s: %s", platform["name"], result)
                        results.append({
                            "platform": platform["name"],
                            "category": platform["category"],
                            "icon": platform["icon"],
                            "found": False,
                            "error": str(result),
                        })
                    else:
                        result["icon"] = platform["icon"]
                        result["category"] = platform["category"]
                        results.append(result)

                if i + 3 < len(platforms_to_search):
                    await asyncio.sleep(1)

        # Aggregate stats
        platforms_found = [r for r in results if r.get("found")]
        total_review_count = sum(r.get("review_count", 0) for r in platforms_found)

        # Average rating across platforms
        ratings = []
        for r in platforms_found:
            if r.get("rating"):
                try:
                    ratings.append(float(r["rating"]))
                except (ValueError, TypeError):
                    pass

        avg_rating = round(sum(ratings) / len(ratings), 1) if ratings else None

        # Reputation verdict
        if avg_rating and avg_rating >= 4.5 and len(ratings) >= 3:
            reputation = "отличная — клиника уверенно лидирует по отзывам"
        elif avg_rating and avg_rating >= 4.0 and len(ratings) >= 2:
            reputation = "хорошая — клиника имеет стабильно положительные оценки"
        elif avg_rating and avg_rating >= 3.0:
            reputation = "средняя — есть над чем работать"
        elif platforms_found:
            reputation = "низкая — мало отзывов или низкие оценки"
        else:
            reputation = "не определена — клиника не найдена на отзывных платформах"

        push_tool_progress(
            "reviews",
            f"✅ Отзывы: {len(platforms_found)} платформ, "
            f"{total_review_count} отзывов, "
            f"ср. рейтинг {avg_rating or '—'} — {reputation}",
        )

        return json.dumps({
            "company_name": company_name,
            "city": city,
            "platforms_with_reviews": len(platforms_found),
            "total_review_count": total_review_count,
            "avg_rating": avg_rating,
            "ratings_count": len(ratings),
            "reputation": reputation,
            "platforms": results,
        }, ensure_ascii=False, indent=2)

    except Exception as e:
        logger.exception("Review aggregation failed")
        return json.dumps({"error": "Review aggregation failed", "detail": str(e)})


async def _search_platform(
    client: httpx.AsyncClient, platform: dict, company: str
) -> dict:
    """Search a single review platform for clinic ratings with key rotation."""
    query = platform["query_template"].format(company_name=company)

    for attempt in range(_MAX_RETRIES):
        try:
            key = get_key_with_fallback()
        except RuntimeError:
            return {
                "platform": platform["name"],
                "found": False,
                "review_count": 0,
                "note": "Нет доступных ключей Firecrawl",
            }

        try:
            response = await client.post(
                FIRECRAWL_SEARCH,
                headers={"Authorization": f"Bearer {key}"},
                json={
                    "query": query,
                    "limit": 8,
                    "sources": ["web"],
                },
            )
            if response.status_code == 402:
                reason = classify_exhaustion(response.text)
                if reason:
                    mark_exhausted(key, reason)
                    logger.warning("Firecrawl 402 on review search (%s), rotating key (attempt %d)", platform["name"], attempt + 1)
                    continue

            response.raise_for_status()
            data = response.json()
            break  # success
        except httpx.HTTPStatusError as e:
            reason = classify_exhaustion(str(e))
            if reason:
                mark_exhausted(key, reason)
                logger.warning("Firecrawl credit exhausted on review search (%s), rotating (attempt %d)", platform["name"], attempt + 1)
                continue
            logger.warning("Review search HTTP error for %s: %s", platform["name"], e)
            return {
                "platform": platform["name"],
                "found": False,
                "review_count": 0,
            }
    else:
        # All retries exhausted
        return {
            "platform": platform["name"],
            "found": False,
            "review_count": 0,
            "note": "Все ключи Firecrawl исчерпаны",
        }

    items = data.get("data", [])
    if isinstance(items, dict):
        items = items.get("web", [])
    if not items:
        return {
            "platform": platform["name"],
            "found": False,
            "review_count": 0,
        }

    # Extract rating from search results
    rating = None
    review_count = 0
    snippet_texts = []

    for item in items[:8]:
        snippet = (item.get("description") or item.get("title", ""))
        snippet_texts.append(snippet[:200])

        # Parse rating: "4.5", "4,5", "4.5/5", "4.5 из 5"
        rating_match = re.search(r'(\d[\.,]\d)\s*(?:/|из)\s*5', snippet)
        if not rating_match:
            rating_match = re.search(r'(\d[\.,]\d)\s*(?:звезд|балл|star)', snippet, re.IGNORECASE)
        if not rating_match:
            rating_match = re.search(r'рейтинг[:\s]*(\d[\.,]\d)', snippet, re.IGNORECASE)
        if rating_match and not rating:
            rating = rating_match.group(1).replace(",", ".")

        # Parse review count: "123 отзыва", "456 reviews"
        count_match = re.search(r'(\d[\d\s]*)\s*(?:отзыв|review|оцен)', snippet, re.IGNORECASE)
        if count_match:
            try:
                cnt = int(count_match.group(1).replace(" ", ""))
                if cnt > review_count:
                    review_count = cnt
            except ValueError:
                pass

    return {
        "platform": platform["name"],
        "found": True,
        "rating": rating,
        "review_count": review_count,
        "items_found": len(items),
        "snippets": snippet_texts[:3],
    }


registry.register(
    name="run_review_platforms",
    toolset="aim-operations",
    schema={
        "type": "function",
        "function": {
            "name": "run_review_platforms",
            "description": (
                "Aggregate clinic reviews from all major Russian platforms: "
                "2GIS, Yandex.Maps, Google Maps (geo/maps platforms), "
                "ProDoctorov (medical ratings), Zoon, Yell (business directories), "
                "Otzovik, IRecommend (review sites). "
                "Returns per-platform ratings, review counts, and overall reputation verdict. "
                "Use this to understand HOW patients perceive the competitor: "
                "what they praise, what they complain about, where the competitor is "
                "vulnerable. Critical for competitive positioning — poor reviews = opportunity."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "company_name": {
                        "type": "string",
                        "description": "[REQUIRED] Clinic or company name (e.g., 'СМ-Клиника', 'Медси')",
                    },
                    "city": {
                        "type": "string",
                        "description": "Optional city for geo-targeting (e.g., 'Санкт-Петербург', 'Москва')",
                    },
                },
                "required": ["company_name"],
            },
        },
    },
    handler=handle_run_review_platforms,
    check_fn=lambda: True,
    is_async=True,
    description="Aggregate clinic reviews from 2GIS/Yandex.Maps/Google/ProDoctorov/Zoon — ratings, counts, reputation verdict",
    emoji="⭐",
)
