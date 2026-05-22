"""Yandex Maps organization search — Tier 3 competitor discovery.

Two search methods:
  1. Playwright headless browser (PRIMARY) — navigates Yandex Maps web search,
     extracts business cards via JavaScript. No API key needed.
  2. Organization Search API (FALLBACK) — search-maps.yandex.ru/v1 with type=biz.
     Only works with a key that has the Organization Search product enabled.

Also uses Yandex Geocoder API (geocode-maps.yandex.ru/v1) to get
city center coordinates for spatial filtering.

API key: developer.tech.yandex.ru → "JavaScript API и HTTP Геокодер"
Free tier: 25,000 requests/day for Geocoder, 1,000 requests/day for Search.
"""

import logging
import os
from typing import Optional

import httpx
from bs4 import BeautifulSoup

from .yandex_maps_search import YandexMapsSearchClient, get_yandex_search_client

logger = logging.getLogger(__name__)

GEOCODER_URL = "https://geocode-maps.yandex.ru/v1"
ORG_SEARCH_URL = "https://search-maps.yandex.ru/v1"
REQUEST_TIMEOUT = 15.0

YANDEX_MAPS_KEY = os.getenv("YANDEX_MAPS_API_KEY", "")

# Medical categories for Yandex organization search
MEDICAL_SEARCH_TERMS = {
    "стоматология": [
        "стоматология",
        "стоматологическая клиника",
        "стоматологический центр",
    ],
    "косметология": [
        "косметология",
        "косметологический центр",
        "косметологическая клиника",
    ],
    "многопрофильная клиника": [
        "медицинский центр",
        "многопрофильная клиника",
    ],
    "пластическая хирургия": [
        "пластическая хирургия",
        "хирургическая клиника",
    ],
    "офтальмология": [
        "офтальмологическая клиника",
        "офтальмологический центр",
    ],
    "диагностический центр": [
        "диагностический центр",
    ],
    "педиатрия": [
        "детская клиника",
        "педиатрия",
        "детский медицинский центр",
    ],
}


class YandexMapsClient:
    """Async client for Yandex Maps organization search.

    Uses Playwright web search as primary method (no API key needed),
    with HTTP Organization Search API as fallback.
    """

    def __init__(
        self,
        api_key: str | None = None,
        search_client: YandexMapsSearchClient | None = None,
    ):
        self.api_key = api_key or YANDEX_MAPS_KEY
        self._client: httpx.AsyncClient | None = None
        self._search = search_client or get_yandex_search_client()

    @property
    def configured(self) -> bool:
        # Playwright search always works — no API key needed.
        # The API key is only needed for Geocoder (which works)
        # and Organization Search (which requires a specific product key).
        return True

    async def _get_client(self) -> httpx.AsyncClient:
        if self._client is None:
            self._client = httpx.AsyncClient(timeout=REQUEST_TIMEOUT)
        return self._client

    async def close(self):
        if self._client:
            await self._client.aclose()
            self._client = None
        if self._search:
            await self._search.close()

    async def geocode(self, query: str) -> tuple[float, float] | None:
        """Geocode an address or city name to coordinates.

        Uses Yandex Geocoder API v1. Returns (lat, lon) or None.
        """
        if not self.configured:
            return None

        try:
            client = await self._get_client()
            resp = await client.get(GEOCODER_URL, params={
                "apikey": self.api_key,
                "geocode": query,
                "lang": "ru_RU",
                "format": "json",
                "results": 1,
            })
            resp.raise_for_status()
            data = resp.json()
        except Exception as e:
            logger.error("Yandex Geocoder v1 failed for query=%s: %s", query, e)
            return None

        features = _extract_features(data)
        if not features:
            return None

        geo_object = features[0].get("GeoObject", {})
        pos = geo_object.get("Point", {}).get("pos", "")
        if pos:
            parts = pos.split()
            if len(parts) == 2:
                return float(parts[1]), float(parts[0])  # lat, lon

        return None

    async def find_organizations(
        self,
        query: str,
        city: str = "",
        results: int = 50,
    ) -> list[dict]:
        """Find organizations via Yandex Maps web search (Playwright).

        Primary method: Playwright headless browser → Yandex Maps search page
        → JavaScript extraction of business cards. No API key needed.

        Fallback: HTTP Organization Search API (only if Playwright is
        unavailable AND a valid Organization Search key is configured).

        Returns list of dicts with: name, address, lat, lon, yandex_url,
        rating, reviews_count, phone, categories.
        """
        # ── Primary: Playwright web search ─────────────────────────
        try:
            web_orgs = await self._search.search_organizations(
                query=query,
                city=city,
                results=results,
            )
            if web_orgs:
                orgs = [_convert_web_result(o) for o in web_orgs]
                logger.info(
                    "Yandex Maps (Playwright): found %d orgs for '%s' in %s",
                    len(orgs), query, city,
                )
                return orgs
        except Exception as e:
            logger.warning("Yandex Maps Playwright search failed: %s", e)

        # ── Fallback: HTTP API ─────────────────────────────────────
        return await self._find_organizations_api(query, city, results)

    async def _find_organizations_api(
        self,
        query: str,
        city: str = "",
        results: int = 50,
    ) -> list[dict]:
        """Fallback: Yandex Organization Search API (search-maps.yandex.ru/v1).

        Only works with an API key that has the Organization Search product
        enabled. The standard Geocoder key returns HTTP 403.
        """
        if not self.api_key or len(self.api_key) < 10:
            logger.warning("Yandex Maps API key not configured — skipping API search")
            return []

        full_query = f"{query}, {city}" if city else query

        try:
            client = await self._get_client()
            resp = await client.get(ORG_SEARCH_URL, params={
                "apikey": self.api_key,
                "text": full_query,
                "type": "biz",
                "lang": "ru_RU",
                "results": results,
            })
            resp.raise_for_status()
            data = resp.json()
        except Exception as e:
            logger.error("Yandex Org Search API failed for query=%s: %s", full_query, e)
            return []

        orgs: list[dict] = []
        seen_names: set[str] = set()

        for feature in data.get("features", []):
            props = feature.get("properties", {})
            company_meta = props.get("CompanyMetaData", {})

            name = company_meta.get("name", "").strip()
            if not name or len(name) < 2:
                continue

            name_key = name.lower()
            if name_key in seen_names:
                continue
            seen_names.add(name_key)

            geometry = feature.get("geometry", {})
            coords = geometry.get("coordinates", [])
            lon, lat = None, None
            if len(coords) == 2:
                lon, lat = float(coords[0]), float(coords[1])

            address = company_meta.get("address", "")

            phones = company_meta.get("Phones", [])
            phone = phones[0].get("formatted", "") if phones else ""

            categories = [
                c.get("name", "") for c in company_meta.get("Categories", [])
            ]

            yandex_url = ""
            if lat and lon:
                slug = name.lower().replace(" ", "_").replace('"', '').replace("'", "")
                yandex_url = f"https://yandex.ru/maps/org/{slug}/{lon},{lat}"

            orgs.append({
                "name": name,
                "address": address,
                "lat": lat,
                "lon": lon,
                "phone": phone,
                "categories": categories,
                "yandex_url": yandex_url,
                "source": "yandex_maps_api",
            })

        logger.info("Yandex Maps API: found %d orgs for '%s' in %s", len(orgs), query, city)
        return orgs

    async def find_medical_orgs(
        self,
        specialization: str,
        city: str,
    ) -> list[dict]:
        """Find medical organizations for a given specialization and city.

        Uses multiple search terms for broader coverage.
        """
        terms = MEDICAL_SEARCH_TERMS.get(specialization, ["медицинский центр"])

        all_orgs: list[dict] = []
        seen: set[str] = set()

        for term in terms[:3]:  # max 3 queries for coverage
            try:
                batch = await self.find_organizations(query=term, city=city, results=30)
                for org in batch:
                    key = org["name"].lower()
                    if key not in seen:
                        seen.add(key)
                        all_orgs.append(org)
            except Exception as e:
                logger.error("Yandex search failed for term=%s: %s", term, e)

        return all_orgs

    async def enrich_with_ratings(self, org: dict) -> dict:
        """Try to scrape rating and review count from Yandex Maps org page.

        Playwright results already include rating and reviews_count, so this
        is only needed for API-sourced results. Skips if ratings already present.
        """
        # Already have ratings from Playwright search — skip
        if org.get("rating") and org.get("reviews_count"):
            return org

        url = org.get("yandex_url") or org.get("url", "")
        if not url:
            return org

        try:
            client = await self._get_client()
            resp = await client.get(url, follow_redirects=True)
            if resp.status_code != 200:
                return org

            soup = BeautifulSoup(resp.text, "html.parser")

            rating_el = soup.select_one('[itemprop="ratingValue"]')
            if rating_el and rating_el.get("content"):
                org["rating"] = float(rating_el["content"])

            reviews_el = soup.select_one('[itemprop="reviewCount"]')
            if reviews_el and reviews_el.get("content"):
                org["reviews_count"] = int(reviews_el["content"])

        except Exception:
            pass  # ratings are optional enrichment

        return org


def _convert_web_result(web: dict) -> dict:
    """Convert Playwright web search result to the standard org dict format.

    Playwright format:  name, rating, ratings_count, address, category,
                        working_status, url, lat, lon, source
    Standard format:    name, address, lat, lon, yandex_url, rating,
                        reviews_count, phone, categories, source
    """
    return {
        "name": web.get("name", ""),
        "address": web.get("address", ""),
        "lat": web.get("lat"),
        "lon": web.get("lon"),
        "yandex_url": web.get("url", ""),
        "rating": web.get("rating"),
        "reviews_count": web.get("ratings_count"),
        "phone": "",
        "categories": [web.get("category", "")] if web.get("category") else [],
        "source": "yandex_maps_web",
    }


def _extract_features(data: dict) -> list[dict]:
    """Extract GeoObject features from Geocoder response."""
    try:
        return (
            data.get("response", {})
            .get("GeoObjectCollection", {})
            .get("featureMember", [])
        )
    except Exception:
        return []


# ── Singleton ──────────────────────────────────────────────────────

_yandex_maps: YandexMapsClient | None = None


def get_yandex_maps_client() -> YandexMapsClient:
    global _yandex_maps
    if _yandex_maps is None:
        _yandex_maps = YandexMapsClient()
    return _yandex_maps
