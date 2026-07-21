"""2ГИС places через Apify actor (m_mamaev/2gis-places-scraper).

Прямой скрапинг рейтингов + отзывов с 2ГИС — часть гибридного подхода для
блока отзывов. Этот actor сам отдаёт тексты отзывов через maxReviewsPerPlace.

Input schema (проверено 21 июля 2026 через API):
  - query: array — поисковые запросы
  - locationQuery: string — город
  - maxItems: int — лимит результатов
  - maxReviewsPerPlace: int — сколько отзывов тянуть ($)

Ротация ключей через UnifiedKeyPool (14 ключей).
"""
import asyncio
import logging

import httpx

from app.lib.apify_client import APIFY_BASE, REQUEST_TIMEOUT

logger = logging.getLogger(__name__)

# m_mamaev/2gis-places-scraper — структурированные данные + отзывы 2ГИС
GIS2_ACTOR_ID = "m_mamaev~2gis-places-scraper"

_POLL_ATTEMPTS = 24
_POLL_INTERVAL = 5


async def _run_actor(api_key: str, query: str, location: str) -> dict | None:
    """Запустить Apify actor для 2ГИС → дождаться → вернуть первый item."""
    async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT) as client:
        run_input = {
            "query": [query],
            "locationQuery": location or "Москва",
            "maxItems": 1,
            "maxReviewsPerPlace": 20,  # тащим до 20 отзывов для тем
        }
        start_url = f"{APIFY_BASE}/acts/{GIS2_ACTOR_ID}/runs?token={api_key}"
        try:
            start_resp = await client.post(start_url, json=run_input)
            start_resp.raise_for_status()
        except httpx.HTTPStatusError:
            raise
        except Exception as e:
            logger.warning("gis2: start run failed: %s", e)
            return None

        run_id = start_resp.json().get("data", {}).get("id")
        if not run_id:
            return None
        logger.info("gis2 run started: %s", run_id)

        poll_data = None
        for _ in range(_POLL_ATTEMPTS):
            await asyncio.sleep(_POLL_INTERVAL)
            poll_resp = await client.get(
                f"{APIFY_BASE}/acts/{GIS2_ACTOR_ID}/runs/{run_id}?token={api_key}"
            )
            poll_resp.raise_for_status()
            poll_data = poll_resp.json()
            status = poll_data.get("data", {}).get("status")
            if status == "SUCCEEDED":
                break
            if status in ("FAILED", "ABORTED", "TIMED-OUT"):
                logger.warning("gis2 run %s ended %s", run_id, status)
                return None
        else:
            logger.warning("gis2 run %s timed out polling", run_id)
            return None

        dataset_id = poll_data["data"]["defaultDatasetId"]
        items = (
            await client.get(f"{APIFY_BASE}/datasets/{dataset_id}/items?token={api_key}")
        ).json()
        return items[0] if items else None


def _normalize(raw: dict, query: str) -> dict | None:
    """Привести ответ 2ГИС к единому формату."""
    if not raw:
        return None

    rating = raw.get("rating") or raw.get("totalScore")
    if rating is None:
        return None

    try:
        rating = float(rating)
    except (TypeError, ValueError):
        return None

    reviews_count = raw.get("reviewCount") or raw.get("ratingCount") or raw.get("reviewsCount") or 0
    try:
        reviews_count = int(reviews_count)
    except (TypeError, ValueError):
        reviews_count = 0

    # 2ГИС actor отдаёт тексты отзывов через reviews
    raw_reviews = raw.get("reviews") or []
    review_texts = []
    for r in raw_reviews[:20]:
        if isinstance(r, dict):
            text = r.get("text") or r.get("comment") or ""
        else:
            text = str(r)
        if text:
            review_texts.append(text.strip()[:500])

    return {
        "rating": rating,
        "reviews": reviews_count,
        "review_texts": review_texts,
        "address": raw.get("address") or raw.get("fullAddress") or "",
        "categories": raw.get("rubrics") or raw.get("categories") or [],
        "name": raw.get("name") or raw.get("title") or query,
        "source": "2gis",
    }


async def search(company_name: str, city: str, url: str | None = None) -> dict | None:
    """Найти клинику на 2ГИС → точный рейтинг + отзывы.

    Args:
        company_name: название клиники
        city: город
        url: (не используется, для совместимости)

    Returns:
        {rating, reviews, review_texts, address, name, source} или None.
    """
    if not company_name and not url:
        return None

    from app.lib.apify_client import get_apify_pool
    pool = get_apify_pool()

    query = company_name or url or ""
    location = city or "Москва"

    last_error = None
    for attempt in range(5):
        try:
            key = await pool.get_next_key()
        except RuntimeError:
            logger.error("gis2_reviews: all Apify keys exhausted")
            return None
        try:
            raw = await _run_actor(key, query, location)
            if raw:
                normalized = _normalize(raw, query)
                if normalized:
                    logger.info(
                        "gis2_reviews OK: %s — rating=%s reviews=%d texts=%d",
                        query, normalized["rating"], normalized["reviews"],
                        len(normalized["review_texts"]),
                    )
                    return normalized
                return None
            logger.info("gis2: not found: %s", query)
            return None
        except httpx.HTTPStatusError as e:
            if e.response.status_code in (402, 429):
                reason = "insufficient_credits" if e.response.status_code == 402 else "rate_limited"
                await pool.mark_exhausted(key, reason)
                logger.warning(
                    "gis2: key %s… exhausted (%d, attempt %d)",
                    key[:20], e.response.status_code, attempt + 1,
                )
                continue
            last_error = f"{e.response.status_code}: {e.response.text[:200]}"
            logger.warning("gis2: key %s… failed: %s", key[:20], last_error)
        except Exception as e:
            last_error = str(e)
            logger.warning("gis2: key %s… failed: %s", key[:20], e)

    logger.error("gis2_reviews: all attempts failed: %s — %s", query, last_error)
    return None
