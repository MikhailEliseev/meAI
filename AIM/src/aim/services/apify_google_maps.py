"""Apify Google Maps Scraper integration — primary competitor discovery.

Replaces the broken Yandex Maps + OSM + DomainGuess pipeline with a single
reliable Google Maps API that returns competitors with website, rating,
reviews, coordinates, and social links — all in one call.

Two actors supported with automatic fallback:
  1. compass/crawler-google-places (primary — more features, social media)
  2. solidcode/google-maps-scraper-2-5-per-1-000-results (fallback — $2.50/1K results)
"""

import json
import logging
import re
import time
from datetime import timedelta

from .apify_client import ApifyClient
from .rusprofile.models import CompanyProfile

logger = logging.getLogger(__name__)

_ACTOR_ID = "compass/crawler-google-places"
_ALT_ACTOR_ID = "solidcode/google-maps-scraper-2-5-per-1-000-results"
_DEFAULT_COUNT = 60
_DEFAULT_TIMEOUT = timedelta(minutes=10)

# Multi-search queries — alternative search strings per specialization to
# catch different tiers of competitors (premium, mid, niche). GM ranks places
# by relevance, so a generic "косметология" query tends to surface smaller
# high-volume clinics, not the big 300M+ medical centers.
_MULTI_SEARCH_QUERIES: dict[str, list[str]] = {
    "косметология": [
        "центр эстетической медицины",
        "лазерная косметология",
        "аппаратная косметология",
    ],
    "стоматология": [
        "стоматологическая клиника",
        "имплантация зубов",
        "эстетическая стоматология",
    ],
    "пластическая хирургия": [
        "клиника пластической хирургии",
        "эстетическая хирургия",
        "реконструктивная хирургия",
    ],
    "дерматология": [
        "центр дерматологии",
        "лазерная дерматология",
        "эстетическая дерматология",
    ],
    "гинекология": [
        "центр гинекологии",
        "репродуктивная медицина",
        "эстетическая гинекология",
    ],
}


def _build_search_queries(specialization: str, city: str) -> list[str]:
    """Generate multiple search queries to catch competitors at different tiers.

    Always includes the base query (specialization + city). Adds alternative
    queries from _MULTI_SEARCH_QUERIES if the specialization is known.
    All queries get city appended unless already present.
    """
    base = specialization
    if city and city.lower() not in specialization.lower():
        base = f"{specialization} {city}"

    queries = [base]
    alt_phrases = _MULTI_SEARCH_QUERIES.get(specialization.lower(), [])
    for phrase in alt_phrases:
        if city and city.lower() not in phrase.lower():
            queries.append(f"{phrase} {city}")
        else:
            queries.append(phrase)

    return queries

# Large-area GeoJSON polygons for major Russian cities.
# Default city polygons in Apify are often too small (no agglomeration).
# These polygons cover the city + suburbs/agglomeration (50-100 km radius).
# Format: [longitude, latitude] pairs — GeoJSON spec.
_CITY_POLYGONS: dict[str, list[list[tuple[float, float]]]] = {
    "Москва": [[
        [36.3, 56.35],   # NW — Зеленоград / Солнечногорск
        [38.8, 56.35],   # NE — Ногинск / Черноголовка
        [38.8, 55.15],   # SE — Подольск / Домодедово / Чехов
        [36.3, 55.15],   # SW — Наро-Фоминск / Обнинск
        [36.3, 56.35],   # close polygon
    ]],
    "Санкт-Петербург": [[
        [29.5, 60.3],    # NW — Выборгское шоссе
        [30.9, 60.3],    # NE — Всеволожск
        [30.9, 59.65],   # SE — Пушкин / Колпино
        [29.5, 59.65],   # SW — Петергоф / Стрельна
        [29.5, 60.3],
    ]],
    "Казань": [[
        [48.5, 56.0],    # NW
        [49.7, 56.0],    # NE
        [49.7, 55.5],    # SE
        [48.5, 55.5],    # SW
        [48.5, 56.0],
    ]],
    "Екатеринбург": [[
        [60.0, 57.1],    # NW
        [61.2, 57.1],    # NE
        [61.2, 56.5],    # SE
        [60.0, 56.5],    # SW
        [60.0, 57.1],
    ]],
    "Новосибирск": [[
        [82.3, 55.3],    # NW
        [83.5, 55.3],    # NE
        [83.5, 54.7],    # SE
        [82.3, 54.7],    # SW
        [82.3, 55.3],
    ]],
    "Краснодар": [[
        [38.5, 45.25],   # NW
        [39.3, 45.25],   # NE
        [39.3, 44.85],   # SE
        [38.5, 44.85],   # SW
        [38.5, 45.25],
    ]],
    "Нижний Новгород": [[
        [43.5, 56.5],    # NW
        [44.3, 56.5],    # NE
        [44.3, 56.1],    # SE
        [43.5, 56.1],    # SW
        [43.5, 56.5],
    ]],
    "Ростов-на-Дону": [[
        [39.3, 47.45],   # NW
        [40.1, 47.45],   # NE
        [40.1, 47.05],   # SE
        [39.3, 47.05],   # SW
        [39.3, 47.45],
    ]],
}


def _build_city_geolocation(city: str) -> dict | None:
    """Build a customGeolocation GeoJSON dict for a city, or None if not found.

    Tries exact match first, then prefix match (e.g. "Москва" matches "Москва, Россия").
    """
    if city in _CITY_POLYGONS:
        coords = _CITY_POLYGONS[city]
    else:
        for key in _CITY_POLYGONS:
            if key.lower() in city.lower() or city.lower() in key.lower():
                coords = _CITY_POLYGONS[key]
                break
        else:
            return None

    return {
        "type": "Polygon",
        "coordinates": coords,
    }


async def discover_competitors_google_maps(
    specialization: str,
    city: str,
    count: int = _DEFAULT_COUNT,
    client: ApifyClient | None = None,
) -> list[CompanyProfile]:
    """Find competitors via Apify Google Maps Scraper.

    Tries primary actor (compass/crawler-google-places) first,
    falls back to solidcode/google-maps-scraper on failure.

    Args:
        specialization: e.g. "стоматология", "косметология"
        city: e.g. "Казань" (will append ", Россия" for geolocation)
        count: max results (default 50)
        client: ApifyClient instance (required — no default singleton).

    Returns:
        List of CompanyProfile objects with website, rating, reviews, coords.
    """
    if client is None:
        raise ValueError("ApifyClient is required — create via get_apify_client() from src.aim.services")

    # Multi-search (>1 query) → SolidCode first (fast, handles multi-query well)
    # Single search → Compass first (slower but returns social media data)
    queries = _build_search_queries(specialization, city)
    use_multi = len(queries) > 1

    if use_multi:
        # SolidCode primary for multi-search (Compass polygon is too slow)
        try:
            profiles = await _discover_via_solidcode(client, specialization, city, count)
            if profiles:
                return profiles
            logger.warning("SolidCode returned 0 results, trying Compass fallback...")
        except Exception as e:
            logger.warning("SolidCode failed: %s — trying Compass fallback...", e)

        try:
            profiles = await _discover_via_compass(client, specialization, city, count)
            if profiles:
                return profiles
            logger.warning("Compass fallback also returned 0 results")
        except Exception as e:
            logger.error("Compass fallback also failed: %s", e)
    else:
        # Compass primary for single search (social media + polygon)
        try:
            profiles = await _discover_via_compass(client, specialization, city, count)
            if profiles:
                return profiles
            logger.warning("Compass returned 0 results, trying SolidCode fallback...")
        except Exception as e:
            logger.warning("Compass failed: %s — trying SolidCode fallback...", e)

        try:
            profiles = await _discover_via_solidcode(client, specialization, city, count)
            if profiles:
                return profiles
            logger.warning("SolidCode fallback also returned 0 results")
        except Exception as e:
            logger.error("SolidCode fallback also failed: %s", e)

    return []


async def _discover_via_compass(
    apify: ApifyClient,
    specialization: str,
    city: str,
    count: int,
) -> list[CompanyProfile]:
    """Primary actor: compass/crawler-google-places (social media included).

    Uses custom geolocation polygons for major Russian cities to expand
    search radius beyond the default (often too narrow) city boundaries.
    Falls back to free-text location for unsupported cities.
    """
    location = f"{city}, Россия" if city and "росси" not in city.lower() else city
    search_queries = _build_search_queries(specialization, city)

    t0 = time.monotonic()

    # Build run input with expanded search area for supported cities
    custom_geo_raw = _build_city_geolocation(city)

    # Distribute result limit across search queries — multi-search multiplies
    # the crawl volume, so we reduce per-query limits to keep total manageable.
    per_query = max(count // len(search_queries), 8)

    run_input: dict = {
        "searchStringsArray": search_queries,
        "maxResults": count,
        "maxCrawledPlacesPerSearch": per_query,
        "language": "ru",
        "includeSocialMedia": True,
        "includeReviews": False,
        "proxyConfig": {"useApifyProxy": True, "apifyProxyGroups": ["RESIDENTIAL"]},
    }

    if custom_geo_raw:
        run_input["customGeolocation"] = custom_geo_raw
        logger.info(
            "Compass GM: using custom polygon for %s (%.1f×%.1f km)",
            city,
            (custom_geo_raw["coordinates"][0][1][0] - custom_geo_raw["coordinates"][0][0][0]) * 111,
            (custom_geo_raw["coordinates"][0][0][1] - custom_geo_raw["coordinates"][0][2][1]) * 111,
        )
    else:
        run_input["locationQuery"] = location
        logger.info("Compass GM: using free-text location '%s'", location)

    run = await apify.call_actor(
        actor_id=_ACTOR_ID,
        run_input=run_input,
        run_timeout=_DEFAULT_TIMEOUT,
        memory_mbytes=2048,
    )

    if run.status != "SUCCEEDED":
        logger.error(
            "Compass GM run %s failed: status=%s", run.id, run.status,
        )
        return []

    if not run.default_dataset_id:
        logger.warning("Compass GM run %s returned no dataset", run.id)
        return []

    items = await apify.get_dataset_items(run.default_dataset_id)
    elapsed = time.monotonic() - t0
    logger.info(
        "Compass GM: %d results for %d queries (%s) in %s (%.1fs)",
        len(items), len(search_queries), search_queries[0], location, elapsed,
    )

    profiles: list[CompanyProfile] = []
    for item in items:
        title = item.get("title", "")
        if not title:
            continue
        if item.get("permanentlyClosed"):
            continue

        website = item.get("website")
        location_data = item.get("location") or {}
        social_media = item.get("socialMedia") or {}

        clean_brand = _clean_gm_title(title)
        clean_full = _clean_gm_title_full(title)

        profile = CompanyProfile(
            inn="",
            legal_name=clean_full,
            brand_name=clean_brand,
            website=website,
            social_links=social_media if social_media else None,
            geo_lat=location_data.get("lat"),
            geo_lon=location_data.get("lng"),
            rating=item.get("totalScore"),
            reviews_count=item.get("reviewsCount"),
            legal_address=item.get("address") or "",
            actual_addresses=[item.get("address")] if item.get("address") else [],
            source_specialization=specialization,
            data_source="apify_google_maps",
            confidence=0.75,
        )
        profiles.append(profile)

    return profiles


async def _discover_via_solidcode(
    apify: ApifyClient,
    specialization: str,
    city: str,
    count: int,
) -> list[CompanyProfile]:
    """Fallback actor: solidcode/google-maps-scraper-2-5-per-1-000-results.

    $2.50 per 1000 results. Different field names than Compass actor.
    No social media field — that's the main tradeoff.
    """
    location = f"{city}, Россия" if city and "росси" not in city.lower() else city
    search_queries = _build_search_queries(specialization, city)

    t0 = time.monotonic()

    run = await apify.call_actor(
        actor_id=_ALT_ACTOR_ID,
        run_input={
            "searchQueries": search_queries,
            "locationName": location,
            "maxResults": count,
            "language": "ru",
            "countryCode": "RU",
        },
        run_timeout=_DEFAULT_TIMEOUT,
        memory_mbytes=1024,
    )

    if run.status != "SUCCEEDED":
        logger.error(
            "SolidCode GM run %s failed: status=%s", run.id, run.status,
        )
        return []

    if not run.default_dataset_id:
        logger.warning("SolidCode GM run %s returned no dataset", run.id)
        return []

    items = await apify.get_dataset_items(run.default_dataset_id)
    elapsed = time.monotonic() - t0
    logger.info(
        "SolidCode GM: %d results for %d queries (%s) in %s (%.1fs)",
        len(items), len(search_queries), search_queries[0], location, elapsed,
    )

    profiles: list[CompanyProfile] = []
    for item in items:
        # SolidCode uses "name" instead of "title"
        title = item.get("name") or item.get("title", "")
        if not title:
            continue

        if item.get("permanentlyClosed") or item.get("temporarilyClosed"):
            continue

        clean_brand = _clean_gm_title(title)
        clean_full = _clean_gm_title_full(title)

        profile = CompanyProfile(
            inn="",
            legal_name=clean_full,
            brand_name=clean_brand,
            website=item.get("website"),
            social_links=None,  # SolidCode actor doesn't provide social media
            geo_lat=item.get("latitude"),
            geo_lon=item.get("longitude"),
            rating=item.get("totalScore"),
            reviews_count=item.get("reviewsCount"),
            legal_address=item.get("address") or "",
            actual_addresses=[item.get("address")] if item.get("address") else [],
            source_specialization=specialization,
            data_source="apify_google_maps",
            confidence=0.70,  # slightly lower — no social media
        )
        profiles.append(profile)

    return profiles


# ── Google Maps title cleaning ────────────────────────────────────────
# GM titles are noisy: "Darmed | Косметология Фрунзенская | Лазерная эпиляция, масса"
# We extract a clean short brand name and a clean full name for DaData matching.

_ADDR_MARKERS = [
    "ул.", "улица", "пр-т", "проспект", "пр-д", "проезд",
    "д.", "дом", "г.", "город", "мкр.", "микрорайон",
    "шоссе", "ш.", "наб.", "набережная", "пер.", "переулок",
    "б-р", "бульвар", "пл.", "площадь", "стр.", "строение",
    "корп.", "корпус", "оф.", "офис", "пом.", "помещение",
    "кв.", "квартира", "эт.", "этаж",
]

_SEPARATORS = (" | ", " · ", " • ", " — ", " – ", " - ", " / ", ". ")

# Patterns that indicate a location suffix (city, district, street reference)
_LOCATION_SUFFIX_RE = re.compile(
    r'\s+(?:в|на|по)\s+\S+'  # "в Москве", "на Тенишевой", "по Ленинскому"
    r'(?:\s+(?:проспекту|шоссе|улице|переулку|бульвару|набережной|проезду))?'
    r'(?:\s+\S+)?'  # optional one more word
    r'$',
    re.IGNORECASE,
)


def _strip_address_suffix(text: str) -> str:
    """Strip address markers and location suffixes from the end of brand text.

    "Стоматология Миллидент ул. М. Салимжанова 15/8в" → "Стоматология Миллидент"
    "Косметологическая клиника Дар-Ян в Москве" → "Косметологическая клиника Дар-Ян"
    "NSVS Новый Стандарт на Тенишевой" → "NSVS Новый Стандарт"
    """
    text = text.strip()
    if len(text) < 5:
        return text

    # Strip address markers (ул., д., пр-т, etc.)
    for marker in _ADDR_MARKERS:
        idx = text.lower().find(marker)
        if idx > 3:
            text = text[:idx].rstrip(", ")
            break

    # Strip location suffixes (в Москве, на Тенишевой, по Ленинскому проспекту)
    m = _LOCATION_SUFFIX_RE.search(text)
    if m and m.start() > 3:
        text = text[:m.start()].rstrip(", ")

    return text.strip()


def _looks_like_address(text: str) -> bool:
    """Check if text is primarily an address, not a brand name.

    "Москва, ул. Тверская, д. 5" → True (pure address)
    "Стоматология Миллидент ул. Салимжанова 15" → False (brand + address)
    """
    text_lower = text.lower()

    # If text is very short (< 15 chars) and has no brand-like words, it's an address
    if len(text) < 15:
        # Check if it starts with a city prefix
        if text_lower.startswith(("г.", "г ", "город")):
            return True
        # Check if first word is a street marker
        first_word = text_lower.split()[0] if text.split() else ""
        if first_word in ("ул.", "улица", "пр-т", "проспект", "пер.", "переулок",
                          "наб.", "набережная", "б-р", "бульвар", "пл.", "площадь",
                          "шоссе", "ш.", "мкр.", "микрорайон"):
            return True
        # Single address marker with number → likely address
        import re
        for marker in _ADDR_MARKERS:
            if marker in text_lower:
                # If there's a number near the marker, it's an address
                if re.search(r'\d', text):
                    # But only if the text is short (brand names are longer)
                    return True
                return False
        return False

    # For longer text: check if address markers dominate
    # Count characters before first address marker
    first_addr_idx = len(text)
    for marker in _ADDR_MARKERS:
        idx = text_lower.find(marker)
        if idx >= 0 and idx < first_addr_idx:
            first_addr_idx = idx

    if first_addr_idx < len(text):
        prefix = text[:first_addr_idx]
        # If the meaningful prefix (before address) has < 2 words, it's likely
        # an address. 2+ meaningful words = brand + address (not pure address).
        prefix_words = [w for w in prefix.split() if len(w.strip('«»"\'.,;:!?')) >= 2]
        if len(prefix_words) < 2:
            return True

    return False


def _clean_gm_title(title: str) -> str:
    """Extract a short clean brand name from a Google Maps title.

    "Darmed | Косметология Фрунзенская | Лазерная эпиляция, масса"
    → "Darmed"

    "Клиника 360 Косметология в Хамовниках"
    → "Клиника 360"

    "Стоматология Миллидент ул. М. Салимжанова 15/8в | Имплантаци"
    → "Стоматология Миллидент"

    "НОВОКЛИНИК, центр эстетической медицины и косметологии"
    → "НОВОКЛИНИК"

    "Косметологическая клиника Дар-Ян в Москве"
    → "Косметологическая клиника Дар-Ян"
    """
    if not title:
        return ""

    # Split on separators (pipe, dash, slash etc.)
    for sep in _SEPARATORS:
        if sep in title:
            parts = [p.strip() for p in title.split(sep)]
            for part in parts:
                if not _looks_like_address(part) and len(part) >= 2:
                    return _strip_address_suffix(part)
            return _strip_address_suffix(parts[0])

    # No pipe-style separator — try comma-splitting for "BRAND, description" patterns
    if ", " in title:
        parts = [p.strip() for p in title.split(", ")]
        for part in parts:
            if not _looks_like_address(part) and len(part) >= 2:
                return _strip_address_suffix(part)
        return _strip_address_suffix(parts[0])

    # Single-part title — strip address suffix
    return _strip_address_suffix(title.strip())


def _clean_gm_title_full(title: str) -> str:
    """Extract a clean full name — brand part without separators/addresses.

    "Darmed | Косметология Фрунзенская | Лазерная эпиляция, масса"
    → "Darmed"

    "Стоматология Миллидент ул. М. Салимжанова 15/8в | Имплантаци"
    → "Стоматология Миллидент"

    "НОВОКЛИНИК, центр эстетической медицины и косметологии"
    → "НОВОКЛИНИК"

    "Косметологическая клиника Дар-Ян в Москве"
    → "Косметологическая клиника Дар-Ян"
    """
    if not title:
        return ""

    # Try separator split first
    for sep in _SEPARATORS:
        if sep in title:
            parts = [p.strip() for p in title.split(sep)]
            meaningful = [p for p in parts if not _looks_like_address(p) and len(p) >= 2]
            if meaningful:
                return _strip_address_suffix(meaningful[0])
            return _strip_address_suffix(parts[0])

    # Try comma-splitting for "BRAND, description" patterns
    if ", " in title:
        parts = [p.strip() for p in title.split(", ")]
        meaningful = [p for p in parts if not _looks_like_address(p) and len(p) >= 2]
        if meaningful:
            return _strip_address_suffix(meaningful[0])
        return _strip_address_suffix(parts[0])

    # No separator — strip address suffix
    return _strip_address_suffix(title.strip())
