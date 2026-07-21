"""Yandex Maps reviews через Apify actor (zen-studio/yandex-maps-reviews-scraper).

Прямой скрапинг рейтингов/отзывов с Яндекс.Карт — замена галлюцинирующему
Perplexity для блока «04 — ОТЗЫВЫ». Возвращает точные цифры с самой площадки.

Ротация ключей через UnifiedKeyPool (14 ключей в /opt/aim-keys/apify.json).
"""
import asyncio
import logging

import httpx

from app.lib.apify_client import APIFY_BASE, REQUEST_TIMEOUT

logger = logging.getLogger(__name__)

# zen-studio/yandex-maps-reviews-scraper — тянет рейтинги + тексты отзывов
YANDEX_ACTOR_ID = "zen-studio~yandex-maps-reviews-scraper"

# Сколько топ-отзывов тащить (для извлечения тем «хвалят/критикуют»)
_MAX_REVIEWS = 20
# Лимит попыток polling (12 × 5с = 60с max)
_POLL_ATTEMPTS = 12
_POLL_INTERVAL = 5


async def _run_actor(api_key: str, search_query: str, url: str | None) -> dict | None:
    """Запустить Apify actor → дождаться → вернуть первый item из dataset.

    Сначала ищем по searchStrings (название + город), при провале — пробуем
    startUrls с доменом клиники (если домен совпадает с yandex URL).
    """
    async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT) as client:
        # Попытка 1: поиск по строке
        run_input = {
            "searchStrings": [search_query],
            "maxReviews": _MAX_REVIEWS,
            "lang": "ru",
        }
        item = await _start_poll_get(client, api_key, run_input)
        if item:
            return item

        # Попытка 2 (fallback): startUrls с доменом клиники
        if url:
            clean_url = url if url.startswith("http") else f"https://{url}"
            logger.info("yandex: fallback to startUrls for %s", clean_url)
            run_input = {
                "startUrls": [clean_url],
                "maxReviews": _MAX_REVIEWS,
                "lang": "ru",
            }
            return await _start_poll_get(client, api_key, run_input)
    return None


async def _start_poll_get(client: httpx.AsyncClient, api_key: str, run_input: dict) -> dict | None:
    """Start run → poll до SUCCEEDED → получить items из dataset."""
    start_url = f"{APIFY_BASE}/acts/{YANDEX_ACTOR_ID}/runs?token={api_key}"
    try:
        start_resp = await client.post(start_url, json=run_input)
        start_resp.raise_for_status()
    except httpx.HTTPStatusError:
        raise  # ротация ключей обрабатывается выше
    except Exception as e:
        logger.warning("yandex: start run failed: %s", e)
        return None

    run_id = start_resp.json().get("data", {}).get("id")
    if not run_id:
        logger.warning("yandex: no run_id in response")
        return None
    logger.info("yandex run started: %s", run_id)

    poll_data = None
    for _ in range(_POLL_ATTEMPTS):
        await asyncio.sleep(_POLL_INTERVAL)
        poll_resp = await client.get(
            f"{APIFY_BASE}/acts/{YANDEX_ACTOR_ID}/runs/{run_id}?token={api_key}"
        )
        poll_resp.raise_for_status()
        poll_data = poll_resp.json()
        status = poll_data.get("data", {}).get("status")
        if status == "SUCCEEDED":
            break
        if status in ("FAILED", "ABORTED", "TIMED-OUT"):
            logger.warning("yandex run %s ended with status %s", run_id, status)
            return None
    else:
        logger.warning("yandex run %s timed out after polling", run_id)
        return None

    dataset_id = poll_data["data"]["defaultDatasetId"]
    items = (
        await client.get(f"{APIFY_BASE}/datasets/{dataset_id}/items?token={api_key}")
    ).json()
    return items[0] if items else None


def _normalize(raw: dict, search_query: str) -> dict | None:
    """Привести ответ Apify к единому формату.

    Actor возвращает поля с разными именами в разных версиях — проверяем
    несколько вариантов (rating/ratingValue, reviewsCount/reviewsCount и т.д.).
    """
    if not raw:
        return None

    # Рейтинг — пробуем несколько ключей
    rating = (
        raw.get("rating")
        or raw.get("ratingValue")
        or raw.get("averageRating")
    )
    if rating is None:
        return None  # без рейтинга отзыв бесполезен

    try:
        rating = float(rating)
    except (TypeError, ValueError):
        return None

    # Кол-во отзывов
    reviews_count = (
        raw.get("reviewsCount")
        or raw.get("reviewsCount")
        or raw.get("numberOfReviews")
        or 0
    )
    try:
        reviews_count = int(reviews_count)
    except (TypeError, ValueError):
        reviews_count = 0

    # Тексты отзывов для извлечения тем
    raw_reviews = raw.get("reviews") or raw.get("review") or []
    review_texts = []
    for r in raw_reviews[:_MAX_REVIEWS]:
        if isinstance(r, dict):
            text = r.get("text") or r.get("comment") or r.get("reviewText") or ""
        else:
            text = str(r)
        if text:
            review_texts.append(text.strip()[:500])

    return {
        "rating": rating,
        "reviews": reviews_count,
        "review_texts": review_texts,
        "address": raw.get("address") or raw.get("location") or "",
        "categories": raw.get("categories") or raw.get("category") or [],
        "name": raw.get("title") or raw.get("name") or search_query,
        "source": "yandex_maps",
    }


async def search(company_name: str, city: str, url: str | None = None) -> dict | None:
    """Найти клинику на Яндекс.Картах → точный рейтинг + отзывы.

    Returns:
        {rating, reviews, review_texts, address, categories, name, source}
        или None если не найдено / все ключи исчерпаны.
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
            logger.error("yandex_reviews: all Apify keys exhausted")
            return None
        try:
            raw = await _run_actor(key, search_query, url)
            if raw:
                normalized = _normalize(raw, search_query)
                if normalized:
                    logger.info(
                        "yandex_reviews OK: %s — rating=%s reviews=%d",
                        search_query, normalized["rating"], normalized["reviews"],
                    )
                    return normalized
                logger.info("yandex: item found but no rating: %s", search_query)
                # если найдено, но без рейтинга — клиника всё-таки есть,
                # нет смысла крутить другие ключи
                return None
            # пустой результат — actor отработал, клиники нет в Яндексе
            logger.info("yandex: not found: %s", search_query)
            return None
        except httpx.HTTPStatusError as e:
            if e.response.status_code in (402, 429):
                reason = "insufficient_credits" if e.response.status_code == 402 else "rate_limited"
                await pool.mark_exhausted(key, reason)
                logger.warning(
                    "yandex: key %s… exhausted (%d, attempt %d)",
                    key[:20], e.response.status_code, attempt + 1,
                )
                continue
            last_error = str(e)
            logger.warning("yandex: key %s… failed: %s", key[:20], e)
        except Exception as e:
            last_error = str(e)
            logger.warning("yandex: key %s… failed: %s", key[:20], e)

    logger.error("yandex_reviews: all attempts failed: %s — %s", search_query, last_error)
    return None
