"""Yandex Maps organization search — Tier 3 competitor discovery.

Uses Yandex Organization Search API (search-maps.yandex.ru/v1)
with type=biz to find medical organizations by specialization + city.
Returns organizations that people actually see on the map.

Also uses Yandex Geocoder API (geocode-maps.yandex.ru/v1) to get
city center coordinates for spatial filtering.

Ratings enrichment via Yandex Maps organization cards (HTML scraping).

API key: developer.tech.yandex.ru → "JavaScript API и HTTP Геокодер"
Free tier: 25,000 requests/day for Geocoder, 1,000 requests/day for Search.
"""

import logging
import os
from typing import Optional

import httpx
from bs4 import BeautifulSoup

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
    """Async client for Yandex Maps organization search."""

    def __init__(self, api_key: str | None = None):
        self.api_key = api_key or YANDEX_MAPS_KEY
        self._client: httpx.AsyncClient | None = None

    @property
    def configured(self) -> bool:
        return bool(self.api_key) and len(self.api_key) > 10

    async def _get_client(self) -> httpx.AsyncClient:
        if self._client is None:
            self._client = httpx.AsyncClient(timeout=REQUEST_TIMEOUT)
        return self._client

    async def close(self):
        if self._client:
            await self._client.aclose()
            self._client = None

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
        """Find organizations via Yandex Organization Search API (type=biz).

        Returns list of dicts with: name, address, lat, lon, yandex_url.
        """
        if not self.configured:
            logger.warning("Yandex Maps not configured — skipping org search")
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
            logger.error("Yandex Org Search failed for query=%s: %s", full_query, e)
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

            # Extract coordinates (Organization Search uses geometry)
            geometry = feature.get("geometry", {})
            coords = geometry.get("coordinates", [])
            lon, lat = None, None
            if len(coords) == 2:
                lon, lat = float(coords[0]), float(coords[1])

            # Address
            address = company_meta.get("address", "")

            # Phone
            phones = company_meta.get("Phones", [])
            phone = phones[0].get("formatted", "") if phones else ""

            # Categories
            categories = [
                c.get("name", "") for c in company_meta.get("Categories", [])
            ]

            # Build Yandex Maps URL
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
                "source": "yandex_maps",
            })

        logger.info("Yandex Maps: found %d orgs for %s in %s", len(orgs), query, city)
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

        This is a lightweight attempt — returns original org unchanged on failure.
        A full implementation would use the Yandex Maps JavaScript API
        organization card endpoint.
        """
        url = org.get("yandex_url", "")
        if not url:
            return org

        try:
            client = await self._get_client()
            resp = await client.get(url, follow_redirects=True)
            if resp.status_code != 200:
                return org

            soup = BeautifulSoup(resp.text, "html.parser")

            # Try to find rating in structured data or page content
            rating_el = soup.select_one('[itemprop="ratingValue"]')
            if rating_el and rating_el.get("content"):
                org["rating"] = float(rating_el["content"])

            reviews_el = soup.select_one('[itemprop="reviewCount"]')
            if reviews_el and reviews_el.get("content"):
                org["reviews_count"] = int(reviews_el["content"])

        except Exception:
            pass  # ratings are optional enrichment

        return org


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
