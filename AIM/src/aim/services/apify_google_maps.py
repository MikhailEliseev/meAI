"""Apify Google Maps Scraper integration — primary competitor discovery.

Replaces the broken Yandex Maps + OSM + DomainGuess pipeline with a single
reliable Google Maps API that returns competitors with website, rating,
reviews, coordinates, and social links — all in one call.
"""

import logging
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
            "proxyConfig": {"useApifyProxy": True},
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

        profile = CompanyProfile(
            inn="",  # will be filled by DaData enrichment
            legal_name=title,
            brand_name=title,
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
