"""Apify Google Maps Scraper integration — primary competitor discovery.

Replaces the broken Yandex Maps + OSM + DomainGuess pipeline with a single
reliable Google Maps API that returns competitors with website, rating,
reviews, coordinates, and social links — all in one call.
"""

import logging
import re
import time
from datetime import timedelta

from .apify_client import ApifyClient
from .rusprofile.models import CompanyProfile

logger = logging.getLogger(__name__)

_ACTOR_ID = "compass/crawler-google-places"
_DEFAULT_COUNT = 50
_DEFAULT_TIMEOUT = timedelta(minutes=4)


async def discover_competitors_google_maps(
    specialization: str,
    city: str,
    count: int = _DEFAULT_COUNT,
    client: ApifyClient | None = None,
) -> list[CompanyProfile]:
    """Find competitors via Apify Google Maps Scraper.

    Args:
        specialization: e.g. "стоматология", "косметология"
        city: e.g. "Казань" (will append ", Россия" for geolocation)
        count: max results (default 50)
        client: ApifyClient instance (required — no default singleton).

    Returns:
        List of CompanyProfile objects with website, rating, reviews, coords.
    """
    if client is None:
        raise ValueError("ApifyClient is required — create via get_apify_client() from aim.services")
    apify = client

    # Append country for correct geolocation — Google Maps needs this
    location = f"{city}, Россия" if city and "росси" not in city.lower() else city

    search_query = specialization
    if city and city.lower() not in specialization.lower():
        search_query = f"{specialization} {city}"

    t0 = time.monotonic()

    run = await apify.call_actor(
        actor_id=_ACTOR_ID,
        run_input={
            "searchStringsArray": [search_query],
            "location": location,
            "maxResults": count,
            "language": "ru",
            "includeSocialMedia": True,
            "includeReviews": False,
            "proxyConfig": {"useApifyProxy": True, "apifyProxyGroups": ["RESIDENTIAL"]},
        },
        run_timeout=_DEFAULT_TIMEOUT,
        memory_mbytes=2048,
    )

    if run.status != "SUCCEEDED":
        logger.error(
            "Google Maps run %s failed: status=%s, message=%s",
            run.id, run.status, getattr(run, "status_message", ""),
        )
        return []

    if not run.default_dataset_id:
        logger.warning("Google Maps run %s returned no dataset", run.id)
        return []

    items = await apify.get_dataset_items(run.default_dataset_id)
    elapsed = time.monotonic() - t0
    logger.info(
        "Google Maps: %d results for '%s' in %s (%.1fs, usage=%s)",
        len(items), search_query, location, elapsed, run.usage,
    )

    profiles: list[CompanyProfile] = []
    for item in items:
        title = item.get("title", "")
        if not title:
            continue

        # Filter closed businesses
        if item.get("permanentlyClosed"):
            continue

        website = item.get("website")
        location_data = item.get("location") or {}
        social_media = item.get("socialMedia") or {}

        clean_brand = _clean_gm_title(title)
        clean_full = _clean_gm_title_full(title)

        profile = CompanyProfile(
            inn="",  # will be filled by DaData enrichment
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
    """
    if not title:
        return ""

    # Split on separators (pipe, dash, slash etc.)
    for sep in _SEPARATORS:
        if sep in title:
            parts = [p.strip() for p in title.split(sep)]
            for part in parts:
                if not _looks_like_address(part) and len(part) >= 2:
                    return part
            return parts[0]

    # No pipe-style separator — try comma-splitting for "BRAND, description" patterns
    if ", " in title:
        parts = [p.strip() for p in title.split(", ")]
        for part in parts:
            if not _looks_like_address(part) and len(part) >= 2:
                return part
        return parts[0]

    # Single-part title — return as-is
    return title.strip()


def _clean_gm_title_full(title: str) -> str:
    """Extract a clean full name — brand part without separators/addresses.

    "Darmed | Косметология Фрунзенская | Лазерная эпиляция, масса"
    → "Darmed"

    "Стоматология Миллидент ул. М. Салимжанова 15/8в | Имплантаци"
    → "Стоматология Миллидент"

    "НОВОКЛИНИК, центр эстетической медицины и косметологии"
    → "НОВОКЛИНИК"
    """
    if not title:
        return ""

    # Try separator split first
    for sep in _SEPARATORS:
        if sep in title:
            parts = [p.strip() for p in title.split(sep)]
            meaningful = [p for p in parts if not _looks_like_address(p) and len(p) >= 2]
            if meaningful:
                return meaningful[0]
            return parts[0]

    # Try comma-splitting for "BRAND, description" patterns
    if ", " in title:
        parts = [p.strip() for p in title.split(", ")]
        meaningful = [p for p in parts if not _looks_like_address(p) and len(p) >= 2]
        if meaningful:
            return meaningful[0]
        return parts[0]

    # No separator — strip address suffix
    title = title.strip()
    for marker in _ADDR_MARKERS:
        idx = title.lower().find(marker)
        if idx > 3:
            title = title[:idx].rstrip(", ")
            break

    return title
