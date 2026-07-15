"""Instagram enrichment for competitor pipeline.

Finds Instagram handles from competitor websites and fetches follower
counts via Apify instagram-profile-scraper. Used for the "Instagram"
column in the competitor table.

Pattern adapted from hermes-v2/app/tools/run_instagram_content.py.
"""

import asyncio
import json
import logging
import os
import re
from typing import Optional

import httpx
from bs4 import BeautifulSoup

from src.aim.services.rusprofile.models import CompetitorMatch

logger = logging.getLogger(__name__)

APIFY_BASE = "https://api.apify.com/v2"
ACTOR_ID = "apify~instagram-profile-scraper"
APIFY_KEYS_PATH = os.getenv("APIFY_KEYS_PATH", "/opt/data/apify_keys.json")
APIFY_TIMEOUT = 120.0
SITE_SCRAPE_TIMEOUT = 10.0

_IG_URL_PATTERN = re.compile(
    r"instagram\.com/([a-zA-Z0-9_.]+)/?", re.I
)


def _load_apify_keys() -> list[str]:
    """Load active Apify API tokens from the key bank."""
    try:
        with open(APIFY_KEYS_PATH) as f:
            data = json.load(f)
        keys = data.get("keys", [])
        active = [k["token"] for k in keys if k.get("status") == "active"]
        if not active:
            logger.warning("apify: no active keys in %s", APIFY_KEYS_PATH)
        return active
    except FileNotFoundError:
        logger.warning("apify: keys file not found: %s", APIFY_KEYS_PATH)
        return []
    except Exception as e:
        logger.warning("apify: cannot load keys: %s", e)
        return []


async def find_instagram_handle(website: str, brand_name: str) -> Optional[str]:
    """Find an Instagram handle from a clinic's website.

    Scrapes the homepage and looks for instagram.com/<handle> links.
    Returns the handle (without @) or None if not found.
    """
    if not website:
        return None

    # Ensure URL has protocol
    url = website
    if not url.startswith("http"):
        url = f"https://{url}"

    try:
        async with httpx.AsyncClient(timeout=SITE_SCRAPE_TIMEOUT) as client:
            resp = await client.get(url, follow_redirects=True)
            resp.raise_for_status()
            html = resp.text

        soup = BeautifulSoup(html, "html.parser")

        # Search all <a> tags for instagram links
        for a_tag in soup.find_all("a", href=True):
            match = _IG_URL_PATTERN.search(a_tag["href"])
            if match:
                handle = match.group(1).lower()
                # Skip generic/explore pages
                if handle not in ("explore", "p", "reel", "accounts"):
                    return handle

        # Fallback: search raw HTML for instagram URLs
        match = _IG_URL_PATTERN.search(html)
        if match:
            handle = match.group(1).lower()
            if handle not in ("explore", "p", "reel", "accounts"):
                return handle

    except Exception as e:
        logger.debug("find_instagram_handle: website=%s error=%s", website, e)

    return None


async def _fetch_followers_via_apify(api_key: str, handle: str) -> Optional[int]:
    """Fetch follower count from Apify instagram-profile-scraper."""
    async with httpx.AsyncClient(timeout=APIFY_TIMEOUT) as client:
        # Start run
        start_url = f"{APIFY_BASE}/acts/{ACTOR_ID}/runs?token={api_key}"
        start_resp = await client.post(
            start_url,
            json={"usernames": [handle], "maxPosts": 0},
        )
        start_resp.raise_for_status()
        run_id = start_resp.json()["data"]["id"]

        # Poll for completion (20 × 5s = 100s max)
        poll_data = None
        for _ in range(20):
            await asyncio.sleep(5)
            poll_resp = await client.get(
                f"{APIFY_BASE}/acts/{ACTOR_ID}/runs/{run_id}?token={api_key}"
            )
            poll_resp.raise_for_status()
            poll_data = poll_resp.json()
            status = poll_data.get("data", {}).get("status")
            if status == "SUCCEEDED":
                break
            if status in ("FAILED", "ABORTED", "TIMED-OUT"):
                return None
        else:
            return None  # timeout

        # Get dataset
        dataset_id = poll_data["data"]["defaultDatasetId"]
        items = (
            await client.get(f"{APIFY_BASE}/datasets/{dataset_id}/items?token={api_key}")
        ).json()

        if items and isinstance(items, list) and len(items) > 0:
            return items[0].get("followersCount")

    return None


async def get_instagram_followers(handle: str) -> Optional[int]:
    """Get follower count for an Instagram handle via Apify.

    Tries each active Apify key in order until one works.
    Returns follower count or None.
    """
    if not handle:
        return None

    handle = handle.lstrip("@")

    keys = _load_apify_keys()
    if not keys:
        logger.warning("get_instagram_followers: no Apify keys available")
        return None

    for key in keys:
        try:
            followers = await _fetch_followers_via_apify(key, handle)
            if followers is not None:
                logger.info(
                    "instagram_followers: @%s → %s", handle, f"{followers:,}",
                )
                return followers
        except Exception as e:
            logger.warning(
                "instagram_followers: key %s... failed for @%s: %s",
                key[:12], handle, e,
            )
            continue

    logger.info("instagram_followers: @%s → not found (all keys failed)", handle)
    return None


async def enrich_instagram_batch(
    competitors: list[CompetitorMatch],
    max_count: int = 5,
) -> None:
    """Enrich top-N competitors with Instagram follower counts.

    For each competitor (up to max_count):
      1. Find IG handle from their website
      2. Fetch follower count via Apify
      3. Store in profile.social_links["instagram"] and set a flag

    Modifies competitors in place. Non-blocking on failure.
    """
    if not competitors:
        return

    targets = competitors[:max_count]
    semaphore = asyncio.Semaphore(3)  # Don't spam Apify

    async def _enrich_one(comp: CompetitorMatch) -> None:
        async with semaphore:
            website = comp.website or comp.profile.website or ""
            brand = comp.profile.brand_name or comp.profile.legal_name or ""

            handle = await find_instagram_handle(website, brand)
            if not handle:
                logger.debug("instagram: no handle found for %s", brand)
                return

            followers = await get_instagram_followers(handle)
            if followers is not None:
                comp.profile.social_links["instagram"] = f"@{handle}"
                comp.profile.social_links["instagram_followers"] = str(followers)
                comp.match_reason += f", Instagram: {followers:,} подписчиков"
                logger.info("instagram_enriched: %s @%s %s", brand, handle, f"{followers:,}")

    await asyncio.gather(
        *[_enrich_one(c) for c in targets],
        return_exceptions=True,
    )
