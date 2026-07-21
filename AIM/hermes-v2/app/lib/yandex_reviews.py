"""Yandex Maps reviews через Apify actor (m_mamaev/yandex-maps-places-scraper).

Прямой скрапинг рейтингов/отзывов с Яндекс.Карт — замена галлюцинирующему
Perplexity для блока «04 — ОТЗЫВЫ». Возвращает точные цифры с самой площадки.

Actor возвращает богатые данные: totalScore, ratingCount, reviewsCount,
neurosummary (AI-сводка отзывов от Яндекса), reviewAspects (структурированные
темы отзывов с количеством упоминаний).

Input schema (проверено 21 июля 2026 через API):
  - query: array of strings — поисковые запросы (название клиники)
  - locations: string — город (enum, но принимает любой)
  - maxItems: int — лимит результатов (1 для конкретной клиники)

Ротация ключей через UnifiedKeyPool (14 ключей в /opt/aim-keys/apify.json).
"""
import asyncio
import logging

import httpx

from app.lib.apify_client import APIFY_BASE, REQUEST_TIMEOUT

logger = logging.getLogger(__name__)

# m_mamaev/yandex-maps-places-scraper — тянет рейтинг + нейросводку + аспекты
YANDEX_ACTOR_ID = "m_mamaev~yandex-maps-places-scraper"

# Лимит попыток polling (12 × 5с = 60с max)
_POLL_ATTEMPTS = 12
_POLL_INTERVAL = 5


async def _run_actor(api_key: str, query: str, location: str) -> dict | None:
    """Запустить Apify actor → дождаться → вернуть первый item из dataset.

    Args:
        query: название клиники (например "ARclinic")
        location: город (например "Санкт-Петербург")
    """
    async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT) as client:
        run_input = {
            "query": [query],
            "locations": location or "None",
            "maxItems": 1,
        }
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


def _normalize(raw: dict, query: str) -> dict | None:
    """Привести ответ Apify к единому формату.

    Actor m_mamaev/yandex-maps-places-scraper возвращает:
      totalScore, ratingCount, reviewsCount, neurosummary, reviewAspects,
      address, categories, url, title
    """
    if not raw:
        return None

    # Рейтинг
    rating = raw.get("totalScore")
    if rating is None:
        rating = raw.get("rating") or raw.get("ratingValue")
    if rating is None:
        return None  # без рейтинга отзыв бесполезен
    try:
        rating = float(rating)
    except (TypeError, ValueError):
        return None

    # Кол-во отзывов (ratingCount = проголосовавших, reviewsCount = текстовых)
    rating_count = raw.get("ratingCount") or raw.get("reviewsCount") or 0
    try:
        rating_count = int(rating_count)
    except (TypeError, ValueError):
        rating_count = 0

    # Аспекты отзывов от Яндекса (структурированные темы с количеством)
    aspects = []
    for a in (raw.get("reviewAspects") or [])[:8]:
        if isinstance(a, dict):
            name = a.get("name", "").strip()
            count = a.get("count", 0)
            if name:
                aspects.append({"name": name, "count": count})

    # Нейросводка Яндекса (AI-резюме отзывов — очень полезно)
    neuro_summary = raw.get("neurosummary") or raw.get("neuroCrop") or ""

    return {
        "rating": rating,
        "reviews": rating_count,
        "review_texts": [],  # этот actor не отдаёт тексты отдельных отзывов
        "aspects": aspects,  # структурированные темы: [{name, count}]
        "neuro_summary": neuro_summary[:500],  # AI-резюме от Яндекса
        "address": raw.get("address") or raw.get("fullAddress") or "",
        "categories": raw.get("categories") or [],
        "name": raw.get("title") or raw.get("shortTitle") or query,
        "yandex_url": raw.get("url", ""),
        "source": "yandex_maps",
    }


async def search(company_name: str, city: str, url: str | None = None) -> dict | None:
    """Найти клинику на Яндекс.Картах → точный рейтинг + отзывы.

    Args:
        company_name: название клиники ("ARclinic")
        city: город ("Санкт-Петербург")
        url: (не используется, для совместимости интерфейса)

    Returns:
        {rating, reviews, aspects, neuro_summary, address, name, yandex_url, source}
        или None если не найдено / все ключи исчерпаны.
    """
    if not company_name and not url:
        return None

    from app.lib.apify_client import get_apify_pool
    pool = get_apify_pool()

    query = company_name or url or ""
    location = city or "None"

    last_error = None
    for attempt in range(5):
        try:
            key = await pool.get_next_key()
        except RuntimeError:
            logger.error("yandex_reviews: all Apify keys exhausted")
            return None
        try:
            raw = await _run_actor(key, query, location)
            if raw:
                normalized = _normalize(raw, query)
                if normalized:
                    logger.info(
                        "yandex_reviews OK: %s — rating=%s reviews=%d aspects=%d",
                        query, normalized["rating"], normalized["reviews"],
                        len(normalized["aspects"]),
                    )
                    return normalized
                logger.info("yandex: item found but no rating: %s", query)
                return None
            # пустой результат — клиники нет в Яндексе
            logger.info("yandex: not found: %s", query)
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
            last_error = f"{e.response.status_code}: {e.response.text[:200]}"
            logger.warning("yandex: key %s… failed: %s", key[:20], last_error)
        except Exception as e:
            last_error = str(e)
            logger.warning("yandex: key %s… failed: %s", key[:20], e)

    logger.error("yandex_reviews: all attempts failed: %s — %s", query, last_error)
    return None
