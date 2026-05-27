"""ApifySocialFinder — find doctor social profiles via Apify Google Search + Telegram native search.

Google Search indexes Instagram and VK well, but Telegram channels are barely
indexed (0 results in tests). For Telegram we use native Telegram search via
Telethon (contacts.SearchRequest), which searches Telegram's internal directory.

Strategy:
  1. Batch all doctor queries for Google: "Name" (site:vk.com OR site:instagram.com)
  2. Run ONE Apify Google Search actor → Instagram + VK profiles
  3. Run Telegram native search per doctor → Telegram channels
  4. Merge results → DoctorSocialResult per doctor
"""

from __future__ import annotations

import asyncio
import logging
import re
from datetime import timedelta
from typing import Optional

from ...services import get_apify_client
from .models import DoctorSocialResult, SocialProfile
from .telegram_channel_finder import TelegramChannelFinder

logger = logging.getLogger(__name__)

_ACTOR_ID = "apify/google-search-scraper"
_DEFAULT_TIMEOUT = timedelta(minutes=3)

# Platform detection from URL
_PLATFORM_RULES: list[tuple[str, str, str]] = [
    # (url pattern, platform name, profile URL prefix)
    ("vk.com/", "vk", "https://vk.com/"),
    ("t.me/", "telegram", "https://t.me/"),
    ("instagram.com/", "instagram", "https://instagram.com/"),
    ("youtube.com/@", "youtube", "https://youtube.com/"),
]

# Reliable Russian doctor communities/blogs — these are NOT personal profiles
# but often appear in search results alongside doctor names.
_EXCLUDE_DOMAINS: tuple[str, ...] = (
    "prodoctorov.ru",
    "napopravku.ru",
    "docdoc.ru",
    "sberhealth.ru",
    "yandex.ru/maps",
    "2gis.ru",
    "google.com/maps",
)


def _extract_platform_and_handle(url: str) -> tuple[str, str] | None:
    """Parse URL to determine platform and extract handle.

    Returns (platform, handle) or None if URL is not a personal profile.
    Filters out posts (/p/, /reel/), videos, and other non-profile URLs.
    """
    url_clean = url.lower().strip("/")
    for pattern, platform, prefix in _PLATFORM_RULES:
        if pattern in url_clean:
            idx = url_clean.find(pattern)
            handle_part = url_clean[idx + len(pattern):].strip("/")
            # Remove query params
            handle_part = handle_part.split("?")[0].split("#")[0]

            # Skip Instagram posts/reels — not personal profiles
            if platform == "instagram":
                if handle_part.startswith("p/") or handle_part.startswith("reel/"):
                    return None
                # Skip story highlights, explore, popular, public collections, etc.
                if handle_part.startswith("stories/") or handle_part in (
                    "explore", "direct", "accounts",
                    "popular", "public",
                ):
                    return None

            # Skip VK videos, wall posts, clips, albums — not profiles
            if platform == "vk":
                if any(handle_part.startswith(p) for p in (
                    "video-", "video@", "clip-", "clip@",
                    "wall-", "wall@", "photo-", "photo@",
                    "topic-", "topic@", "market-", "market@",
                    "album-", "album@", "event-", "event@",
                )):
                    return None
                # Keep only the profile part (e.g. "ortopunkt" from "ortopunkt/wall")
                handle_part = handle_part.split("/")[0]

            # Skip YouTube videos — keep only channels
            if platform == "youtube":
                if "/watch" in url_clean or "/shorts/" in url_clean:
                    return None

            if not handle_part or handle_part in (
                "share", "search", "feed", "explore",
            ):
                return None
            return platform, f"@{handle_part}"
    return None


class ApifySocialFinder:
    """Finds doctor social media profiles using Apify Google Search.

    Batches all doctor queries into a single Apify actor run for efficiency.
    """

    def __init__(self, timeout: timedelta = _DEFAULT_TIMEOUT) -> None:
        self._timeout = timeout
        self._client: Optional[object] = None  # ApifyClient

    async def _get_client(self):
        if self._client is None:
            self._client = get_apify_client()
        return self._client

    async def find_doctors(
        self, doctor_names: list[str]
    ) -> dict[str, DoctorSocialResult]:
        """Batch-search social profiles for multiple doctors.

        Returns dict mapping doctor name → DoctorSocialResult.

        Each doctor query searches for their name across VK, Telegram, Instagram.
        All queries run in a SINGLE Apify actor call.
        """
        if not doctor_names:
            return {}

        results: dict[str, DoctorSocialResult] = {
            name: DoctorSocialResult(doctor_name=name) for name in doctor_names
        }

        # Build search queries — one per doctor, joined as single string
        # NOTE: site:t.me excluded — Telegram channels are barely indexed by Google.
        # We search Telegram natively via Telethon (contacts.SearchRequest) instead.
        queries = "\n".join(
            f'"{name}" (site:vk.com OR site:instagram.com)'
            for name in doctor_names
        )

        try:
            client = await self._get_client()
            run = await client.call_actor(
                actor_id=_ACTOR_ID,
                run_input={
                    "queries": queries,
                    "maxPagesPerQuery": 1,
                    "resultsPerPage": 10,
                    "languageCode": "ru",
                    "countryCode": "ru",
                },
                run_timeout=self._timeout,
                memory_mbytes=1024,
                max_retries=2,
            )

            items = await client.get_dataset_items(run.default_dataset_id)

            # Parse results: group by query (doctor name)
            query_to_name = {
                f'"{name}" (site:vk.com OR site:instagram.com)': name
                for name in doctor_names
            }
            # Also try without quotes (Apify may strip them)
            for name in doctor_names:
                plain = f"{name} (site:vk.com OR site:instagram.com)"
                query_to_name[plain] = name

            for item in items:
                # searchQuery can be str or dict with 'term' key
                sq = item.get("searchQuery", "")
                if isinstance(sq, dict):
                    sq = sq.get("term", "")
                search_query = str(sq) if sq else ""
                doctor_name = query_to_name.get(search_query)
                if not doctor_name:
                    # Try fuzzy match
                    for q, n in query_to_name.items():
                        if n in search_query or search_query in q:
                            doctor_name = n
                            break
                if not doctor_name:
                    continue

                organic = item.get("organicResults", [])
                for r in organic:
                    url = r.get("url", "")
                    if not url:
                        continue

                    # Skip non-profile URLs
                    if any(domain in url.lower() for domain in _EXCLUDE_DOMAINS):
                        continue

                    parsed = _extract_platform_and_handle(url)
                    if parsed is None:
                        continue

                    platform, handle = parsed
                    title = r.get("title", "")

                    # Skip if name not in title (likely wrong person)
                    name_parts = doctor_name.lower().split()
                    title_lower = title.lower()
                    if not any(part in title_lower for part in name_parts if len(part) >= 3):
                        continue

                    dr = results[doctor_name]
                    # Replace placeholder (exists=False) if present;
                    # skip if we already have a real profile for this platform
                    replaced = False
                    already_has = False
                    for i, existing in enumerate(dr.profiles):
                        if existing.platform == platform:
                            if existing.exists:
                                already_has = True
                            else:
                                dr.profiles[i] = SocialProfile(
                                    platform=platform,
                                    handle=handle,
                                    url=url,
                                    exists=True,
                                )
                                replaced = True
                            break
                    if already_has:
                        continue
                    if not replaced:
                        dr.profiles.append(SocialProfile(
                            platform=platform,
                            handle=handle,
                            url=url,
                            exists=True,
                        ))

        except Exception as e:
            logger.warning("Apify social finder batch failed: %s", e)

        # ---- Telegram native search (Google doesn't index Telegram well) ----
        try:
            tg_finder = TelegramChannelFinder()
            for name in doctor_names:
                tg_profiles = await tg_finder.find_doctor_channels(name)
                if tg_profiles:
                    dr = results[name]
                    for tp in tg_profiles:
                        # Replace placeholder or append
                        replaced_tg = False
                        for i, existing in enumerate(dr.profiles):
                            if existing.platform == "telegram":
                                if not existing.exists:
                                    dr.profiles[i] = tp
                                    replaced_tg = True
                                break
                        if not replaced_tg:
                            dr.profiles.append(tp)
                    logger.info(
                        "Telegram native: found %d channel(s) for '%s'",
                        len(tg_profiles), name,
                    )
            await tg_finder.close()
        except Exception as e:
            logger.warning("Telegram native search failed: %s", e)

        # Compute platforms_found for each doctor
        for dr in results.values():
            dr.platforms_found = sum(1 for p in dr.profiles if p.exists)

        return results

    async def find_doctor(self, name: str) -> DoctorSocialResult:
        """Search for a single doctor's social profiles."""
        batch = await self.find_doctors([name])
        return batch.get(name, DoctorSocialResult(doctor_name=name))
