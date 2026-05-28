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
import urllib.parse
from datetime import timedelta
from typing import Optional

import httpx
from bs4 import BeautifulSoup

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
                # Also catch wall<NUMBERS>_<NUMBERS> (numeric wall posts)
                if re.match(r"wall\d+_\d+", handle_part):
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

        # ---- Enrich profiles with actual subscriber counts ----
        await self._enrich_subscriber_counts(results)

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

    async def _enrich_subscriber_counts(
        self, results: dict[str, DoctorSocialResult]
    ) -> None:
        """Enrich Apify-found profiles with actual subscriber/follower counts.

        Apify Google Search returns profile URLs but no stats. This method
        scrapes each profile page to extract real subscriber counts.

        Runs Instagram and VK enrichment in parallel per doctor.
        """
        # Collect all profiles that need enrichment
        instagram_handles: list[tuple[str, str]] = []  # (doctor_name, handle)
        vk_urls: list[tuple[str, str]] = []  # (doctor_name, url)

        for name, dr in results.items():
            for p in dr.profiles:
                if not p.exists or p.subscribers > 0:
                    continue
                if p.platform == "instagram" and p.handle:
                    instagram_handles.append((name, p.handle.lstrip("@")))
                elif p.platform == "vk" and p.url:
                    vk_urls.append((name, p.url))

        if not instagram_handles and not vk_urls:
            return

        async with httpx.AsyncClient(
            timeout=httpx.Timeout(8.0),
            headers={
                "User-Agent": (
                    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/148.0.0.0 Safari/537.36"
                ),
                "Accept-Language": "ru-RU,ru;q=0.9",
            },
            follow_redirects=True,
        ) as client:
            # Enrich Instagram profiles via topsearch API (parallel)
            if instagram_handles:
                ig_tasks = [
                    self._enrich_instagram(client, name, handle)
                    for name, handle in instagram_handles
                ]
                ig_results = await asyncio.gather(*ig_tasks, return_exceptions=True)
                for (name, handle), result in zip(instagram_handles, ig_results):
                    if isinstance(result, Exception):
                        logger.debug("IG enrich failed for @%s: %s", handle, result)
                        continue
                    if result:
                        dr = results[name]
                        for p in dr.profiles:
                            if p.platform == "instagram" and p.handle.lstrip("@") == handle:
                                p.subscribers = result.get("subscribers", 0)
                                p.posts_last_month = result.get("posts_last_month", 0)
                                p.top_topics = result.get("top_topics", [])
                                break

            # Enrich VK profiles via page scraping (parallel)
            if vk_urls:
                vk_tasks = [
                    self._enrich_vk(client, name, url)
                    for name, url in vk_urls
                ]
                vk_results = await asyncio.gather(*vk_tasks, return_exceptions=True)
                for (name, url), result in zip(vk_urls, vk_results):
                    if isinstance(result, Exception):
                        logger.debug("VK enrich failed for %s: %s", url, result)
                        continue
                    if result and result.get("subscribers", 0) > 0:
                        dr = results[name]
                        for p in dr.profiles:
                            if p.platform == "vk" and p.url == url:
                                p.subscribers = result.get("subscribers", 0)
                                if result.get("topics"):
                                    p.top_topics = result["topics"]
                                break

    @staticmethod
    async def _enrich_instagram(
        client: httpx.AsyncClient, name: str, handle: str
    ) -> dict | None:
        """Fetch Instagram profile stats via topsearch API."""
        try:
            encoded = urllib.parse.quote(handle)
            resp = await client.get(
                f"https://www.instagram.com/web/search/topsearch/?query={encoded}",
                headers={"X-Requested-With": "XMLHttpRequest"},
            )
            if resp.status_code != 200:
                return None

            data = resp.json()
            users = data.get("users", [])
            for user in users[:5]:
                user_info = user.get("user", {})
                username = user_info.get("username", "")
                if username.lower() != handle.lower():
                    continue

                followers = user_info.get("follower_count", 0) or 0
                media_count = user_info.get("media_count", 0) or 0
                biography = user_info.get("biography", "") or ""

                topics: list[str] = []
                if biography:
                    # Extract medical/cosmetology topics from bio
                    topic_keywords = [
                        "косметолог", "дерматолог", "врач", "доктор", "клиник",
                        "cosmetolog", "dermatolog", "doctor", "clinic",
                        "эстетист", "antiage", "омоложен", "ботулотоксин",
                        "филлер", "filler", "botox", "пластическ",
                    ]
                    bio_lower = biography.lower()
                    for kw in topic_keywords:
                        if kw in bio_lower:
                            topics.append(kw)

                return {
                    "subscribers": int(followers),
                    "posts_last_month": min(int(media_count), 9999),
                    "top_topics": topics[:5],
                }

            return None
        except Exception as e:
            logger.debug("IG enrich error for @%s: %s", handle, e)
            return None

    @staticmethod
    async def _enrich_vk(
        client: httpx.AsyncClient, name: str, url: str
    ) -> dict | None:
        """Scrape VK profile page for subscriber counts."""
        try:
            resp = await client.get(
                url, headers={"Accept-Language": "ru-RU,ru;q=0.9"}
            )
            if resp.status_code != 200:
                return None

            soup = BeautifulSoup(resp.text, "html.parser")

            result: dict = {"subscribers": 0}

            # Strategy 1: og:description meta
            meta_desc = soup.select_one('meta[property="og:description"]')
            if meta_desc:
                desc = meta_desc.get("content", "")
                patterns = [
                    (r"([\d\s]+)\s*подписчик", "subscribers"),
                    (r"([\d\s]+)\s*участник", "subscribers"),
                    (r"([\d\s]+)\s*друг", "friends"),
                    (r"([\d\s]+)\s*follower", "subscribers"),
                    (r"([\d\s]+)\s*member", "subscribers"),
                ]
                for pattern, key in patterns:
                    match = re.search(pattern, desc, re.IGNORECASE)
                    if match:
                        raw = match.group(1).replace(" ", "").replace(",", ".")
                        try:
                            count = int(float(raw))
                        except ValueError:
                            count = 0
                        if count > 0:
                            result["subscribers"] = count
                            break

            # Strategy 2: inline JSON with members_count/followers_count
            if not result.get("subscribers"):
                for script in soup.select("script"):
                    text = script.string or ""
                    if '"members_count"' in text or '"followers_count"' in text:
                        members_m = re.search(r'"members_count":(\d+)', text)
                        followers_m = re.search(r'"followers_count":(\d+)', text)
                        if members_m:
                            result["subscribers"] = int(members_m.group(1))
                        elif followers_m:
                            result["subscribers"] = int(followers_m.group(1))
                        break

            # Strategy 3: CSS counter selectors
            if not result.get("subscribers"):
                for selector in (
                    ".page_members_count", ".group_members_count",
                    ".profile_friends_count", ".header_subscribers_count",
                ):
                    el = soup.select_one(selector)
                    if el:
                        text = el.get_text(strip=True)
                        digits = re.sub(r"[^\d]", "", text)
                        if digits:
                            result["subscribers"] = int(digits)
                            break

            return result if result.get("subscribers", 0) > 0 else None
        except Exception as e:
            logger.debug("VK enrich error for %s: %s", url, e)
            return None

    async def find_doctor(self, name: str) -> DoctorSocialResult:
        """Search for a single doctor's social profiles."""
        batch = await self.find_doctors([name])
        return batch.get(name, DoctorSocialResult(doctor_name=name))
