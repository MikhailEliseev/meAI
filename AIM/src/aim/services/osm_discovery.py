"""OpenStreetMap competitor discovery via Overpass API + Nominatim fallback.

Finds medical organizations by amenity type (dentist/clinic/doctors),
not by legal name. Catches brand-named clinics like "Никор-Мед" that
DaData prefix search misses.

Primary: Overpass API (detailed tags — website, phone, amenity type).
Fallback: Nominatim search (broader coverage, less detail, same OSM data).

Free, no API key required. Data from OpenStreetMap contributors.
"""

import logging
from typing import Optional

import httpx

logger = logging.getLogger(__name__)

NOMINATIM_URL = "https://nominatim.openstreetmap.org/search"
NOMINATIM_TIMEOUT = 10.0  # per search-term query
OVERPASS_URLS = [
    "https://overpass.kumi.systems/api/interpreter",
    "https://overpass.osm.rambler.ru/api/interpreter",
    "https://overpass.openstreetmap.ru/api/interpreter",
]
REQUEST_TIMEOUT = 15.0
OVERPASS_TIMEOUT = 10.0  # per-instance — fast fail if unresponsive
USER_AGENT = "AIM-CompetitorMatcher/1.0 (me@iamaim.ru)"

# Medical amenities we care about
MEDICAL_AMENITIES = {
    "dentist": "стоматология",
    "clinic": "клиника",
    "doctors": "врачи",
}

# Russian search terms for Nominatim fallback (maps to amenity key)
NOMINATIM_SEARCH_TERMS = {
    "стоматология": "dentist",
    "стоматологическая клиника": "dentist",
    "клиника": "clinic",
    "медицинский центр": "clinic",
    "врачи": "doctors",
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
        return None

    async def find_medical_places(
        self,
        city: str,
        lat: float | None = None,
        lon: float | None = None,
        radius: int = SEARCH_RADIUS,
    ) -> list[dict]:
        """Find medical organizations near a city.

        Tries Overpass first (rich tags: website, phone, amenity type),
        falls back to Nominatim (name + coordinates).
        """
        if lat is None or lon is None:
            coords = await self.geocode(city)
            if not coords:
                return []
            lat, lon = coords

        # Try Overpass first
        results = await self._find_via_overpass(city, lat, lon, radius)

        # Fallback to Nominatim
        if not results:
            logger.info("OSM Overpass returned 0 results for %s — trying Nominatim", city)
            results = await self._find_via_nominatim(city)

        logger.info("OSM: found %d medical places in %s", len(results), city)
        return results

    async def _find_via_overpass(
        self, city: str, lat: float, lon: float, radius: int,
    ) -> list[dict]:
        """Try Overpass API across multiple public instances."""
        query = _build_overpass_query(lat, lon, radius)
        client = await self._get_client()

        data = None
        last_error = None
        for url in OVERPASS_URLS:
            try:
                resp = await client.post(
                    url,
                    data={"data": query},
                    timeout=OVERPASS_TIMEOUT,
                    headers={"Accept": "application/json"},
                )
                resp.raise_for_status()
                data = resp.json()
                break
            except Exception as e:
                last_error = f"{type(e).__name__}: {e}"
                logger.debug("Overpass %s failed: %s", url, last_error)

        if data is None:
            logger.warning(
                "All Overpass URLs failed for %s (tried %d). Last error: %s",
                city, len(OVERPASS_URLS), last_error,
            )
            return []

        return _parse_overpass_response(data, city)

    async def _find_via_nominatim(self, city: str) -> list[dict]:
        """Fallback: search OSM via Nominatim by medical category + city."""
        client = await self._get_client()
        results: list[dict] = []
        seen_names: set[str] = set()

        for search_term, amenity in NOMINATIM_SEARCH_TERMS.items():
            if len(results) >= 60:
                break
            try:
                resp = await client.get(NOMINATIM_URL, params={
                    "q": f"{search_term}, {city}",
                    "format": "json",
                    "limit": 30,
                    "accept-language": "ru",
                    "addressdetails": 1,
                }, timeout=NOMINATIM_TIMEOUT)
                resp.raise_for_status()
                data = resp.json()
            except Exception as e:
                logger.debug("Nominatim search failed for %s: %s", search_term, e)
                continue

            for place in data:
                name = place.get("display_name", "").split(",")[0].strip()
                if not name or len(name) < 3:
                    continue

                name_key = name.lower()
                if name_key in seen_names:
                    continue
                seen_names.add(name_key)

                addr = place.get("address", {})
                results.append({
                    "name": name,
                    "amenity": amenity,
                    "amenity_label": MEDICAL_AMENITIES.get(amenity, amenity),
                    "lat": float(place["lat"]) if place.get("lat") else None,
                    "lon": float(place["lon"]) if place.get("lon") else None,
                    "website": "",
                    "phone": "",
                    "street": addr.get("road", addr.get("street", "")),
                    "housenumber": addr.get("house_number", ""),
                    "city": city,
                })

        return results


def _parse_overpass_response(data: dict, city: str) -> list[dict]:
    """Parse Overpass API JSON response into competitor dicts."""
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

        name_key = name.lower()
        if name_key in seen_names:
            continue
        seen_names.add(name_key)

        el_lat = element.get("lat") or (
            element.get("center", {}).get("lat") if "center" in element else None
        )
        el_lon = element.get("lon") or (
            element.get("center", {}).get("lon") if "center" in element else None
        )

        results.append({
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
        })

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
