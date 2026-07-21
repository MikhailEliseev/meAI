"""2ГИС reviews через Apify actor (m_mamaev/2gis-places-scraper).

Прямой скрапинг рейтингов с 2ГИС — часть гибридного подхода для блока отзывов.
Аналогичен yandex_reviews.py, но проще: 2ГИС actor возвращает place data
(рейтинг + кол-во отзывов), без глубокого парсинга текстов отзывов.

Ротация ключей через UnifiedKeyPool (14 ключей).
"""
import asyncio
import logging

import httpx

from app.lib.apify_client import APIFY_BASE, REQUEST_TIMEOUT

logger = logging.getLogger(__name__)

# m_mamaev/2gis-places-scraper — структурированные данные заведений 2ГИС
GIS2_ACTOR_ID = "m_mamaev~2gis-places-scraper"

_POLL_ATTEMPTS = 12
_POLL_INTERVAL = 5


async def _run_actor(api_key: str, search_query: str) -> dict | None:
    """Запустить Apify actor для 2ГИС → дождаться → вернуть первый item."""
    async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT) as client:
        run_input = {"search": search_query, "limit": 1}
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


def _normalize(raw: dict, search_query: str) -> dict | None:
    """Привести ответ 2ГИС к единому формату."""
    if not raw:
        return None

    rating = raw.get("rating") or raw.get("rating_value")
    if rating is None:
        return None

    try:
        rating = float(rating)
    except (TypeError, ValueError):
        return None

    reviews_count = raw.get("reviews_count") or raw.get("reviewsCount") or 0
    try:
        reviews_count = int(reviews_count)
    except (TypeError, ValueError):
        reviews_count = 0

    return {
        "rating": rating,
        "reviews": reviews_count,
        "review_texts": [],  # 2ГИС actor не отдаёт тексты отзывов
        "address": raw.get("address") or raw.get("full_address") or "",
        "categories": raw.get("categories") or [],
        "name": raw.get("name") or search_query,
        "source": "2gis",
    }


async def search(company_name: str, city: str, url: str | None = None) -> dict | None:
    """Найти клинику на 2ГИС → точный рейтинг + кол-во отзывов.

    Returns:
        {rating, reviews, review_texts: [], address, categories, name, source}
        или None если не найдено.
    """
    if not company_name and not url:
        return None

    from app.lib.apify_client import get_apify_pool
    pool = get_apify_pool()

    location = f", {city}" if city else ""
    search_query = f"{company_name}{location}" if company_name else url or ""

    last_error = None
    for attempt in range(5):
        try:
            key = await pool.get_next_key()
        except RuntimeError:
            logger.error("gis2_reviews: all Apify keys exhausted")
            return None
        try:
            raw = await _run_actor(key, search_query)
            if raw:
                normalized = _normalize(raw, search_query)
                if normalized:
                    logger.info(
                        "gis2_reviews OK: %s — rating=%s reviews=%d",
                        search_query, normalized["rating"], normalized["reviews"],
                    )
                    return normalized
                return None
            logger.info("gis2: not found: %s", search_query)
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
            last_error = str(e)
            logger.warning("gis2: key %s… failed: %s", key[:20], e)
        except Exception as e:
            last_error = str(e)
            logger.warning("gis2: key %s… failed: %s", key[:20], e)

    logger.error("gis2_reviews: all attempts failed: %s — %s", search_query, last_error)
    return None
