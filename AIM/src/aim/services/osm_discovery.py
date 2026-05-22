"""OpenStreetMap competitor discovery via Overpass API.

Finds medical organizations by amenity type (dentist/clinic/doctors),
not by legal name. Catches brand-named clinics like "Никор-Мед" that
DaData prefix search misses.

Free, no API key required. Data from OpenStreetMap contributors.
"""

import logging
import traceback
from typing import Optional

import httpx

logger = logging.getLogger(__name__)

NOMINATIM_URL = "https://nominatim.openstreetmap.org/search"
OVERPASS_URL = "https://overpass.kumi.systems/api/interpreter"
REQUEST_TIMEOUT = 30.0
USER_AGENT = "AIM-CompetitorMatcher/1.0 (me@iamaim.ru)"

# Medical amenities we care about
MEDICAL_AMENITIES = {
    "dentist": "стоматология",
    "clinic": "клиника",
    "doctors": "врачи",
}

# Radius around city center to search (meters)
SEARCH_RADIUS = 15000


class OSMDiscovery:
    """Find medical organizations in a city via OpenStreetMap."""

    def __init__(self):
        self._http: httpx.AsyncClient | None = None

    async def _get_client(self) -> httpx.AsyncClient:
        if self._http is None:
            self._http = httpx.AsyncClient(
                timeout=REQUEST_TIMEOUT,
                headers={"User-Agent": USER_AGENT},
            )
        return self._http

    async def close(self):
        if self._http:
            await self._http.aclose()
            self._http = None

    async def geocode(self, city: str) -> tuple[float, float] | None:
        """Get coordinates for a city name via Nominatim."""
        client = await self._get_client()
        try:
            resp = await client.get(NOMINATIM_URL, params={
                "q": f"{city}, Россия",
                "format": "json",
                "limit": 3,
            })
            resp.raise_for_status()
            data = resp.json()
            if data:
                return float(data[0]["lat"]), float(data[0]["lon"])
        except Exception as e:
            logger.error(
                "Nominatim geocoding failed for %s: %s %s",
                city, type(e).__name__, e,
            )
            logger.debug("Full traceback:", exc_info=True)
        return None

    async def find_medical_places(
        self,
        city: str,
        lat: float | None = None,
        lon: float | None = None,
        radius: int = SEARCH_RADIUS,
    ) -> list[dict]:
        """Find medical organizations near a city.

        Returns list of dicts with: name, amenity, lat, lon, website,
        phone, street, housenumber, city (inferred).
        """
        if lat is None or lon is None:
            coords = await self.geocode(city)
            if not coords:
                return []
            lat, lon = coords

        query = _build_overpass_query(lat, lon, radius)

        client = await self._get_client()
        try:
            resp = await client.post(
                OVERPASS_URL,
                data={"data": query},
                timeout=30,
                headers={"Accept": "application/json"},
            )
            resp.raise_for_status()
            data = resp.json()
        except Exception as e:
            logger.error(
                "Overpass query failed for %s: %s %s",
                city, type(e).__name__, e,
            )
            logger.debug("Full traceback:", exc_info=True)
            return []

        results: list[dict] = []
        seen_names: set[str] = set()

        for element in data.get("elements", []):
            tags = element.get("tags", {})
            name = tags.get("name", "").strip()
            if not name or name == "???":
                continue

            amenity = tags.get("amenity", "")
            if amenity not in MEDICAL_AMENITIES:
                continue

            # Deduplicate by name (many clinics have multiple nodes)
            name_key = name.lower()
            if name_key in seen_names:
                continue
            seen_names.add(name_key)

            el_lat = element.get("lat") or (element.get("center", {}).get("lat") if "center" in element else None)
            el_lon = element.get("lon") or (element.get("center", {}).get("lon") if "center" in element else None)

            result = {
                "name": name,
                "amenity": amenity,
                "amenity_label": MEDICAL_AMENITIES.get(amenity, amenity),
                "lat": el_lat,
                "lon": el_lon,
                "website": _normalize_website(tags.get("website", tags.get("contact:website", ""))),
                "phone": tags.get("phone", tags.get("contact:phone", "")),
                "street": tags.get("addr:street", ""),
                "housenumber": tags.get("addr:housenumber", ""),
                "city": city,
            }
            results.append(result)

        logger.info("OSM: found %d medical places in %s", len(results), city)
        return results


def _build_overpass_query(lat: float, lon: float, radius: int) -> str:
    """Build Overpass QL query for medical amenities."""
    parts = []
    for amenity in MEDICAL_AMENITIES:
        parts.append(f'  node["amenity"="{amenity}"](around:{radius},{lat},{lon});')
        parts.append(f'  way["amenity"="{amenity}"](around:{radius},{lat},{lon});')
    return f"""[out:json][timeout:30];
(
{chr(10).join(parts)}
);
out body center;
"""


def _normalize_website(raw: str) -> str:
    """Ensure website URL has https:// prefix."""
    if not raw:
        return ""
    raw = raw.strip()
    if raw.startswith("http://") or raw.startswith("https://"):
        return raw
    return f"https://{raw}"


# Singleton
_osm_discovery: OSMDiscovery | None = None


def get_osm_discovery() -> OSMDiscovery:
    global _osm_discovery
    if _osm_discovery is None:
        _osm_discovery = OSMDiscovery()
    return _osm_discovery
