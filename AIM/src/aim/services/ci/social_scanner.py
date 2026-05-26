"""SocialScanner — find competitor social media presence.

Searches Instagram, Telegram, VK, TikTok by company name.
Extracts basic stats: followers, posting frequency, top topics.
Uses httpx (no Playwright needed — profile pages are mostly static HTML).

TTL: 24 hours (social activity changes daily).
"""

import logging
import re
import time
import urllib.parse
from typing import Optional

import httpx
from bs4 import BeautifulSoup

from .models import SocialScanResult, SocialProfile

logger = logging.getLogger(__name__)

USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/148.0.0.0 Safari/537.36"
)


class SocialScanner:
    """Scans social media platforms for competitor profiles."""

    def __init__(self, timeout: float = 8.0, cache_ttl: int = 86400) -> None:
        self._client = httpx.Client(
            timeout=httpx.Timeout(timeout),
            headers={"User-Agent": USER_AGENT, "Accept": "text/html,application/json"},
            follow_redirects=True,
        )
        self._cache: dict[str, tuple[float, SocialScanResult]] = {}
        self._cache_ttl = cache_ttl

    def close(self) -> None:
        self._client.close()

    def scan(self, company_name: str) -> SocialScanResult:
        cached = self._cache_get(company_name)
        if cached is not None:
            return cached

        result = SocialScanResult(company_name=company_name)

        # Try each platform
        result.instagram = self._find_instagram(company_name)
        result.telegram = self._find_telegram(company_name)
        result.vk = self._find_vk(company_name)
        result.tiktok = self._find_tiktok(company_name)

        result.total_platforms_found = sum(
            1
            for p in [result.instagram, result.telegram, result.vk, result.tiktok]
            if p and p.exists
        )

        self._cache_set(company_name, result)
        return result

    # ------------------------------------------------------------------
    # Platform finders
    # ------------------------------------------------------------------

    def _find_instagram(self, name: str) -> Optional[SocialProfile]:
        """Search Instagram by company name (limited — Instagram blocks heavily)."""
        try:
            encoded = urllib.parse.quote(name)
            resp = self._client.get(
                f"https://www.instagram.com/web/search/topsearch/?query={encoded}",
                headers={"X-Requested-With": "XMLHttpRequest"},
            )
            if resp.status_code != 200:
                return SocialProfile(
                    platform="instagram",
                    handle="",
                    exists=False,
                    error=f"Instagram search returned {resp.status_code}",
                )

            data = resp.json()
            users = data.get("users", [])
            for user in users[:3]:
                user_info = user.get("user", {})
                username = user_info.get("username", "")
                full_name = user_info.get("full_name", "")
                if name.lower() in full_name.lower() or name.lower() in username.lower():
                    return SocialProfile(
                        platform="instagram",
                        handle=f"@{username}",
                        url=f"https://instagram.com/{username}",
                        exists=True,
                    )

            return SocialProfile(platform="instagram", handle="", exists=False)

        except Exception as e:
            logger.warning("Instagram search failed for '%s': %s", name, e)
            return SocialProfile(
                platform="instagram", handle="", exists=False, error=str(e)
            )

    def _find_telegram(self, name: str) -> Optional[SocialProfile]:
        """Search Telegram channels by company name."""
        try:
            encoded = urllib.parse.quote(name)
            resp = self._client.get(f"https://t.me/s/{encoded}")
            if resp.status_code == 200 and len(resp.text) > 500:
                soup = BeautifulSoup(resp.text, "html.parser")
                posts = soup.select(".tgme_widget_message_wrap")
                topics = []
                for post in posts[:10]:
                    text_el = post.select_one(".tgme_widget_message_text")
                    if text_el:
                        topics.append(text_el.get_text(strip=True)[:100])

                return SocialProfile(
                    platform="telegram",
                    handle=f"@{encoded}",
                    url=f"https://t.me/{encoded}",
                    exists=True,
                    posts_last_month=len(posts),
                    top_topics=self._extract_topics(topics),
                )

            return SocialProfile(platform="telegram", handle="", exists=False)

        except Exception as e:
            logger.warning("Telegram search failed for '%s': %s", name, e)
            return SocialProfile(
                platform="telegram", handle="", exists=False, error=str(e)
            )

    def _find_vk(self, name: str) -> Optional[SocialProfile]:
        """Search VK communities by company name."""
        try:
            encoded = urllib.parse.quote(name)
            resp = self._client.get(
                f"https://vk.com/search?c%5Bper_page%5D=5&c%5Bq%5D={encoded}&c%5Bsection%5D=communities",
            )
            if resp.status_code != 200:
                return SocialProfile(
                    platform="vk",
                    handle="",
                    exists=False,
                    error=f"VK search returned {resp.status_code}",
                )

            soup = BeautifulSoup(resp.text, "html.parser")
            groups = soup.select(".labeled_title, .search_row")
            for group in groups[:3]:
                link = (
                    group.select_one("a[href*='public']")
                    or group.select_one("a[href*='club']")
                    or group.select_one("a[href*='/']")
                )
                if link:
                    href = link.get("href", "")
                    group_name = link.get_text(strip=True)
                    if name.lower()[:5] in group_name.lower():
                        return SocialProfile(
                            platform="vk",
                            handle=href.replace("/", ""),
                            url=f"https://vk.com{href}" if href.startswith("/") else href,
                            exists=True,
                        )

            return SocialProfile(platform="vk", handle="", exists=False)

        except Exception as e:
            logger.warning("VK search failed for '%s': %s", name, e)
            return SocialProfile(
                platform="vk", handle="", exists=False, error=str(e)
            )

    def _find_tiktok(self, name: str) -> Optional[SocialProfile]:
        """Search TikTok by company name."""
        try:
            encoded = urllib.parse.quote(name)
            resp = self._client.get(
                f"https://www.tiktok.com/search/user?q={encoded}",
            )
            if resp.status_code == 200 and len(resp.text) > 500:
                username_match = re.search(r'"uniqueId":"([^"]+)"', resp.text)
                if username_match:
                    username = username_match.group(1)
                    return SocialProfile(
                        platform="tiktok",
                        handle=f"@{username}",
                        url=f"https://tiktok.com/@{username}",
                        exists=True,
                    )

            return SocialProfile(platform="tiktok", handle="", exists=False)

        except Exception as e:
            logger.warning("TikTok search failed for '%s': %s", name, e)
            return SocialProfile(
                platform="tiktok", handle="", exists=False, error=str(e)
            )

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _extract_topics(self, texts: list[str], max_topics: int = 5) -> list[str]:
        """Extract common topics from post texts (simple keyword extraction)."""
        if not texts:
            return []
        seen: set[str] = set()
        topics: list[str] = []
        for text in texts:
            key = text[:50].lower()
            if key not in seen and len(text) > 20:
                seen.add(key)
                topics.append(text[:80])
            if len(topics) >= max_topics:
                break
        return topics

    def _cache_get(self, key: str) -> Optional[SocialScanResult]:
        entry = self._cache.get(key)
        if entry is None:
            return None
        ts, value = entry
        if time.monotonic() - ts > self._cache_ttl:
            del self._cache[key]
            return None
        return value

    def _cache_set(self, key: str, value: SocialScanResult) -> None:
        self._cache[key] = (time.monotonic(), value)
