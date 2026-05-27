"""SocialScanner — find competitor social media presence.

Searches Instagram, Telegram, VK, TikTok by company name AND individual doctor names.
Extracts basic stats: followers, posting frequency, top topics.
Uses httpx (no Playwright needed — profile pages are mostly static HTML).

TTL: 24 hours (social activity changes daily).
"""

import html as _html_module
import json
import logging
import re
import time
import urllib.parse
from typing import Optional

import httpx
from bs4 import BeautifulSoup

from .models import DoctorSocialResult, SocialProfile, SocialScanResult

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
        self._last_request_ts: float = 0.0

    def _rate_limit(self, min_delay: float = 1.5) -> None:
        """Ensure minimum delay between requests to avoid rate limiting."""
        elapsed = time.monotonic() - self._last_request_ts
        if elapsed < min_delay:
            time.sleep(min_delay - elapsed)
        self._last_request_ts = time.monotonic()

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

    def scan_doctor(self, doctor_name: str) -> DoctorSocialResult:
        """Scan social media for an individual doctor (brand ambassador)."""
        cached = self._cache_get(f"doctor:{doctor_name}")
        if cached is not None:
            if isinstance(cached, DoctorSocialResult):
                return cached

        result = DoctorSocialResult(doctor_name=doctor_name)

        # Strategy 1: Direct platform search (by transliterated handle)
        result.profiles.append(self._find_doctor_instagram(doctor_name))
        result.profiles.append(self._find_doctor_vk(doctor_name))
        result.profiles.append(self._find_doctor_telegram(doctor_name))

        # Strategy 2: Search-based discovery (Google/Yandex via Playwright)
        # DISABLED: Google returns 429, Yandex shows captcha for all HTTP
        # requests from Russia. Re-enable when Playwright-based search is added.
        # google_profiles = self._find_doctor_social_via_search(doctor_name)
        # result.profiles.extend(google_profiles)

        # Merge: keep best profile per platform
        result.profiles = [p for p in result.profiles if p is not None]
        best_per_platform: dict[str, SocialProfile] = {}
        for p in result.profiles:
            existing = best_per_platform.get(p.platform)
            if existing is None or (p.exists and not existing.exists):
                best_per_platform[p.platform] = p
        result.profiles = list(best_per_platform.values())
        result.platforms_found = sum(1 for p in result.profiles if p.exists)

        self._cache_set(f"doctor:{doctor_name}", result)
        return result

    def scan_doctors(self, doctor_names: list[str]) -> list[DoctorSocialResult]:
        """Scan social media for multiple doctors, returning results in order."""
        return [self.scan_doctor(name) for name in doctor_names]

    # ------------------------------------------------------------------
    # Platform finders (company)
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
                    # Extract follower count, media count, and bio
                    followers = user_info.get("follower_count", 0) or 0
                    media_count = user_info.get("media_count", 0) or 0
                    biography = user_info.get("biography", "") or ""

                    # Derive topics from biography
                    topics: list[str] = []
                    if biography:
                        topics = self._extract_bio_topics(biography)

                    return SocialProfile(
                        platform="instagram",
                        handle=f"@{username}",
                        url=f"https://instagram.com/{username}",
                        exists=True,
                        subscribers=int(followers),
                        posts_last_month=min(int(media_count), 9999),
                        top_topics=topics,
                    )

            return SocialProfile(platform="instagram", handle="", exists=False)

        except Exception as e:
            logger.warning("Instagram search failed for '%s': %s", name, e)
            return SocialProfile(
                platform="instagram", handle="", exists=False, error=str(e)
            )

    def _find_telegram(self, name: str) -> Optional[SocialProfile]:
        """Search Telegram channels by company name.

        Note: Telegram handles only support Latin characters (a-z, 0-9, _).
        Russian/cyrillic company names will NOT match via direct handle lookup.
        This is a known platform limitation — Telegram does not offer cyrillic handles.
        """
        try:
            encoded = urllib.parse.quote(name)
            resp = self._client.get(f"https://t.me/s/{encoded}")
            if resp.status_code == 200 and len(resp.text) > 500:
                soup = BeautifulSoup(resp.text, "html.parser")

                # Check for "not found" indicators to avoid false positives
                if soup.select_one(".tgme_page_not_found"):
                    return SocialProfile(platform="telegram", handle="", exists=False)
                body_text = soup.get_text().lower()
                if any(
                    indicator in body_text
                    for indicator in (
                        "page not found",
                        "канал не найден",
                        "channel not found",
                        "user not found",
                    )
                ):
                    return SocialProfile(platform="telegram", handle="", exists=False)

                # MUST have either tgme_page_title or message posts to be valid
                has_title = soup.select_one(".tgme_page_title")
                has_posts = soup.select(".tgme_widget_message_wrap")
                if not has_title and not has_posts:
                    return SocialProfile(platform="telegram", handle="", exists=False)

                posts = has_posts
                topics = []
                for post in posts[:10]:
                    text_el = post.select_one(".tgme_widget_message_text")
                    if text_el:
                        topics.append(text_el.get_text(strip=True)[:100])

                # Try to extract subscriber count from tgme_page_extra
                subscribers = self._parse_tg_subscribers(soup)

                return SocialProfile(
                    platform="telegram",
                    handle=f"@{name}",
                    url=f"https://t.me/{encoded}",
                    exists=True,
                    subscribers=subscribers,
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
                )
                if link:
                    href = link.get("href", "")
                    group_name = link.get_text(strip=True)
                    if name.lower()[:5] in group_name.lower():
                        # Try to extract member count
                        subscribers = self._parse_vk_subscribers(group)

                        # Try to extract group description for topics
                        desc_el = group.select_one(".labeled_desc, .search_row_info")
                        top_topics: list[str] = []
                        if desc_el:
                            top_topics = self._extract_bio_topics(desc_el.get_text(strip=True))

                        return SocialProfile(
                            platform="vk",
                            handle=href.replace("/", ""),
                            url=f"https://vk.com{href}" if href.startswith("/") else href,
                            exists=True,
                            subscribers=subscribers,
                            top_topics=top_topics,
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

                    # Try to extract follower count
                    followers = 0
                    follower_match = re.search(r'"followerCount":(\d+)', resp.text)
                    if follower_match:
                        followers = int(follower_match.group(1))

                    return SocialProfile(
                        platform="tiktok",
                        handle=f"@{username}",
                        url=f"https://tiktok.com/@{username}",
                        exists=True,
                        subscribers=followers,
                    )

            return SocialProfile(platform="tiktok", handle="", exists=False)

        except Exception as e:
            logger.warning("TikTok search failed for '%s': %s", name, e)
            return SocialProfile(
                platform="tiktok", handle="", exists=False, error=str(e)
            )

    # ------------------------------------------------------------------
    # Doctor-specific platform finders
    # ------------------------------------------------------------------

    def _find_doctor_instagram(self, name: str) -> Optional[SocialProfile]:
        """Find a doctor's personal Instagram by full name."""
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
            for user in users[:5]:
                user_info = user.get("user", {})
                username = user_info.get("username", "")
                full_name = user_info.get("full_name", "")
                is_private = user_info.get("is_private", False)
                is_business = user_info.get("is_business", False)

                if is_business:
                    continue

                name_lower = name.lower()
                if name_lower in full_name.lower() or name_lower in username.lower():
                    followers = user_info.get("follower_count", 0) or 0
                    media_count = user_info.get("media_count", 0) or 0
                    biography = user_info.get("biography", "") or ""

                    topics: list[str] = []
                    if biography:
                        topics = self._extract_bio_topics(biography)

                    return SocialProfile(
                        platform="instagram",
                        handle=f"@{username}",
                        url=f"https://instagram.com/{username}",
                        exists=True,
                        subscribers=int(followers),
                        posts_last_month=min(int(media_count), 9999),
                        top_topics=topics,
                    )

            return SocialProfile(platform="instagram", handle="", exists=False)

        except Exception as e:
            logger.warning("Doctor Instagram search failed for '%s': %s", name, e)
            return SocialProfile(
                platform="instagram", handle="", exists=False, error=str(e)
            )

    def _find_doctor_telegram(self, name: str) -> Optional[SocialProfile]:
        """Find a doctor's personal Telegram channel by name."""
        try:
            latin_name = self._transliterate(name)
            handles_to_try = [
                latin_name.lower().replace(" ", "_"),
                latin_name.lower().replace(" ", ""),
                name.lower().replace(" ", "_"),
            ]

            for handle in handles_to_try:
                resp = self._client.get(f"https://t.me/s/{handle}")
                if resp.status_code == 200 and len(resp.text) > 500:
                    soup = BeautifulSoup(resp.text, "html.parser")
                    if soup.select_one(".tgme_page_not_found"):
                        continue
                    body_text = soup.get_text().lower()
                    if any(
                        indicator in body_text
                        for indicator in (
                            "page not found",
                            "канал не найден",
                            "channel not found",
                            "user not found",
                        )
                    ):
                        continue

                    # MUST have page title or posts — otherwise it's a redirect stub
                    has_title = soup.select_one(".tgme_page_title")
                    has_posts = soup.select(".tgme_widget_message_wrap")
                    if not has_title and not has_posts:
                        continue

                    profile_name_el = has_title
                    profile_name = profile_name_el.get_text(strip=True) if profile_name_el else ""
                    if name.lower() not in profile_name.lower() and profile_name.lower() not in name.lower():
                        continue

                    posts = has_posts
                    subscribers = self._parse_tg_subscribers(soup)
                    topics = []
                    for post in posts[:5]:
                        text_el = post.select_one(".tgme_widget_message_text")
                        if text_el:
                            topics.append(text_el.get_text(strip=True)[:100])

                    return SocialProfile(
                        platform="telegram",
                        handle=f"@{handle}",
                        url=f"https://t.me/{handle}",
                        exists=True,
                        subscribers=subscribers,
                        posts_last_month=len(posts),
                        top_topics=self._extract_topics(topics),
                    )

            return SocialProfile(platform="telegram", handle="", exists=False)

        except Exception as e:
            logger.warning("Doctor Telegram search failed for '%s': %s", name, e)
            return SocialProfile(
                platform="telegram", handle="", exists=False, error=str(e)
            )

    def _find_doctor_vk(self, name: str) -> Optional[SocialProfile]:
        """Find a doctor's personal VK profile by name and scrape stats."""
        try:
            encoded = urllib.parse.quote(name)
            resp = self._client.get(
                f"https://vk.com/search?c%5Bper_page%5D=5&c%5Bq%5D={encoded}&c%5Bsection%5D=people",
            )
            if resp.status_code != 200:
                return SocialProfile(
                    platform="vk",
                    handle="",
                    exists=False,
                    error=f"VK search returned {resp.status_code}",
                )

            soup = BeautifulSoup(resp.text, "html.parser")
            people = soup.select(".labeled_title, .search_row")
            for person in people[:3]:
                link = person.select_one("a[href*='id']")
                if not link:
                    continue
                href = link.get("href", "")
                person_name = link.get_text(strip=True)
                if name.lower()[:5] in person_name.lower():
                    url = f"https://vk.com{href}" if href.startswith("/") else href
                    handle = href.replace("/", "")

                    # Try to extract friend/subscriber count from search snippet
                    subscribers = self._parse_vk_subscribers(person)

                    # Fetch the actual profile page for more stats
                    profile_stats = self._scrape_vk_profile(url)
                    if profile_stats:
                        subscribers = profile_stats.get("subscribers", subscribers)
                        return SocialProfile(
                            platform="vk",
                            handle=handle,
                            url=url,
                            exists=True,
                            subscribers=subscribers,
                            posts_last_month=profile_stats.get("posts_count", 0),
                            top_topics=profile_stats.get("topics", []),
                        )

                    return SocialProfile(
                        platform="vk",
                        handle=handle,
                        url=url,
                        exists=True,
                        subscribers=subscribers,
                    )

            return SocialProfile(platform="vk", handle="", exists=False)

        except Exception as e:
            logger.warning("Doctor VK search failed for '%s': %s", name, e)
            return SocialProfile(
                platform="vk", handle="", exists=False, error=str(e)
            )

    @staticmethod
    def _transliterate(cyrillic: str) -> str:
        """Simple cyrillic-to-latin transliteration for username guessing."""
        mapping = {
            "а": "a", "б": "b", "в": "v", "г": "g", "д": "d", "е": "e",
            "ё": "yo", "ж": "zh", "з": "z", "и": "i", "й": "y", "к": "k",
            "л": "l", "м": "m", "н": "n", "о": "o", "п": "p", "р": "r",
            "с": "s", "т": "t", "у": "u", "ф": "f", "х": "kh", "ц": "ts",
            "ч": "ch", "ш": "sh", "щ": "sch", "ъ": "", "ы": "y", "ь": "",
            "э": "e", "ю": "yu", "я": "ya",
            "А": "a", "Б": "b", "В": "v", "Г": "g", "Д": "d", "Е": "e",
            "Ё": "yo", "Ж": "zh", "З": "z", "И": "i", "Й": "y", "К": "k",
            "Л": "l", "М": "m", "Н": "n", "О": "o", "П": "p", "Р": "r",
            "С": "s", "Т": "t", "У": "u", "Ф": "f", "Х": "kh", "Ц": "ts",
            "Ч": "ch", "Ш": "sh", "Щ": "sch", "Ъ": "", "Ы": "y", "Ь": "",
            "Э": "e", "Ю": "yu", "Я": "ya",
        }
        return "".join(mapping.get(c, c) for c in cyrillic)

    # ------------------------------------------------------------------
    # Google search for doctor social profiles
    # ------------------------------------------------------------------

    def _find_doctor_social_via_search(self, name: str) -> list[SocialProfile]:
        """Search for a doctor's social media profiles via Yandex + Google.

        Most Russian doctors don't have transliterated handles matching
        their names — search engines find the actual profile URLs.
        Tries Yandex first (more relevant for Russian content), then Google.
        Adds a short delay between requests to avoid rate limiting.
        """
        profiles: list[SocialProfile] = []

        # Try Yandex first (better for Russian-language content)
        yandex_urls = self._search_yandex_social(name)
        for url in yandex_urls:
            profile = self._classify_social_url(url, name)
            if profile is not None:
                profiles.append(profile)

        # Small delay before hitting Google
        time.sleep(1.5)

        # Try Google as fallback
        google_urls = self._search_google_social(name)
        for url in google_urls:
            profile = self._classify_social_url(url, name)
            if profile is not None:
                profiles.append(profile)

        return profiles

    def _search_yandex_social(self, name: str) -> set[str]:
        """Search Yandex for social media profile URLs."""
        urls: set[str] = set()
        try:
            self._rate_limit()
            query = f'"{name}" (telegram OR instagram OR vk.com)'
            encoded = urllib.parse.quote(query)
            url = f"https://yandex.ru/search/?text={encoded}&lr=213"
            resp = self._client.get(url)
            if resp.status_code != 200:
                logger.warning("Yandex search for '%s' returned %d", name, resp.status_code)
                return urls

            soup = BeautifulSoup(resp.text, "html.parser")

            # Yandex search result links
            for link in soup.select("a[href]"):
                href = link.get("href", "")
                if any(domain in href for domain in ("t.me/", "telegram.me/", "instagram.com/", "vk.com/", "vk.ru/")):
                    urls.add(href)

        except Exception as e:
            logger.warning("Yandex social search failed for '%s': %s", name, e)

        return urls

    def _search_google_social(self, name: str) -> set[str]:
        """Search Google for social media profile URLs."""
        urls: set[str] = set()
        try:
            self._rate_limit(min_delay=2.0)
            query = f'"{name}" (telegram OR instagram OR vk OR vk.com)'
            encoded = urllib.parse.quote(query)
            url = f"https://www.google.com/search?q={encoded}&hl=ru&num=10"
            resp = self._client.get(url)
            if resp.status_code != 200:
                logger.warning("Google search for '%s' returned %d", name, resp.status_code)
                return urls

            soup = BeautifulSoup(resp.text, "html.parser")

            # Extract URLs from search result citations
            for cite in soup.select("cite"):
                text = cite.get_text(strip=True)
                if text and any(d in text for d in ("t.me/", "instagram.com/", "vk.com/")):
                    urls.add(text)

            # Also check link hrefs (Google wraps as /url?q=REAL_URL&...)
            for link in soup.select("a[href]"):
                href = link.get("href", "")
                if href.startswith("/url?") or href.startswith("http"):
                    if "/url?" in href:
                        from urllib.parse import parse_qs, urlparse
                        parsed = urlparse(href)
                        qs = parse_qs(parsed.query)
                        real = qs.get("q", [""])[0]
                        if real.startswith("http") and "google" not in real:
                            urls.add(real)
                    elif href.startswith("http") and "google" not in href:
                        urls.add(href)

        except Exception as e:
            logger.warning("Google social search failed for '%s': %s", name, e)

        return urls

    def _classify_social_url(self, url: str, doctor_name: str) -> Optional[SocialProfile]:
        """Parse a URL found via search and create a SocialProfile if it's a known platform."""
        url_lower = url.lower()

        if "t.me/" in url_lower or "telegram.me/" in url_lower or "telegram.org/" in url_lower:
            return self._parse_telegram_from_url(url, doctor_name)

        if "instagram.com/" in url_lower:
            return self._parse_instagram_from_url(url)

        if "vk.com/" in url_lower or "vk.ru/" in url_lower:
            return self._parse_vk_from_url(url, doctor_name)

        return None

    def _parse_telegram_from_url(self, url: str, doctor_name: str) -> Optional[SocialProfile]:
        """Extract handle from Telegram URL and fetch channel stats."""
        try:
            match = re.search(r"t\.me/([^/?\s]+)", url)
            if not match:
                return None
            handle = match.group(1)
            if handle in ("share", "login", "joinchat", "addstickers", "proxy", "setlanguage"):
                return None

            # Fetch channel preview page for stats
            resp = self._client.get(f"https://t.me/s/{handle}")
            if resp.status_code != 200:
                return SocialProfile(
                    platform="telegram", handle=f"@{handle}", url=f"https://t.me/{handle}", exists=True
                )

            soup = BeautifulSoup(resp.text, "html.parser")
            if soup.select_one(".tgme_page_not_found"):
                return None

            has_title = soup.select_one(".tgme_page_title")
            has_posts = soup.select(".tgme_widget_message_wrap")
            if not has_title and not has_posts:
                return None

            profile_name = has_title.get_text(strip=True) if has_title else ""
            subscribers = self._parse_tg_subscribers(soup)

            topics: list[str] = []
            for post in has_posts[:5]:
                text_el = post.select_one(".tgme_widget_message_text")
                if text_el:
                    topics.append(text_el.get_text(strip=True)[:100])

            return SocialProfile(
                platform="telegram",
                handle=f"@{handle}",
                url=f"https://t.me/{handle}",
                exists=True,
                subscribers=subscribers,
                posts_last_month=len(has_posts),
                top_topics=self._extract_topics(topics),
            )

        except Exception as e:
            logger.warning("Failed to parse Telegram from URL '%s': %s", url, e)
            return None

    def _parse_instagram_from_url(self, url: str) -> Optional[SocialProfile]:
        """Extract Instagram username from URL."""
        match = re.search(r"instagram\.com/([^/?\s]+)", url)
        if not match:
            return None
        username = match.group(1)
        if username in ("p", "reel", "stories", "explore", "accounts"):
            return None

        return SocialProfile(
            platform="instagram",
            handle=f"@{username}",
            url=f"https://instagram.com/{username}",
            exists=True,
        )

    def _parse_vk_from_url(self, url: str, doctor_name: str) -> Optional[SocialProfile]:
        """Extract VK handle from URL and scrape profile stats."""
        match = re.search(r"vk\.(?:com|ru)/([^/?\s]+)", url)
        if not match:
            return None
        handle = match.group(1)
        if handle in ("search", "feed", "im", "friends", "groups", "video", "music", "apps", "market"):
            return None

        profile_url = f"https://vk.com/{handle}"
        profile_stats = self._scrape_vk_profile(profile_url)

        if profile_stats:
            return SocialProfile(
                platform="vk",
                handle=handle,
                url=profile_url,
                exists=True,
                subscribers=profile_stats.get("subscribers", 0),
                posts_last_month=profile_stats.get("posts_count", 0),
                top_topics=profile_stats.get("topics", []),
            )

        return SocialProfile(
            platform="vk",
            handle=handle,
            url=profile_url,
            exists=True,
        )

    # ------------------------------------------------------------------
    # ProDoctorov per-doctor search
    # ------------------------------------------------------------------

    def search_prodoctorov_doctor(self, name: str) -> tuple[float, int]:
        """Search ProDoctorov for a specific doctor's rating and review count.

        Uses ProDoctorov's own search API (POST /api/search/) to find the doctor
        profile URL, then extracts rating/reviews from Vue.js SSR data embedded
        in the profile page HTML.

        Returns (rating_0_to_5, reviews_count).
        """
        try:
            doctor_link = self._search_prodoctorov_api(name)
            if not doctor_link:
                return 0.0, 0

            rating, reviews = self._fetch_prodoctorov_profile(doctor_link)
            return rating, reviews

        except Exception as e:
            logger.warning("ProDoctorov doctor search failed for '%s': %s", name, e)
            return 0.0, 0

    def _search_prodoctorov_api(self, name: str) -> Optional[str]:
        """Search ProDoctorov's /api/search/ endpoint for a doctor by name.

        POSTs a JSON query and filters results for category=DOCTOR with name match.
        Returns the relative profile link (e.g. /spb/vrach/982455-ivanov/).
        """
        try:
            resp = self._client.post(
                "https://prodoctorov.ru/api/search/",
                json={"query": name, "town": "spb"},
                headers={
                    "x-requested-with": "XMLHttpRequest",
                    "Referer": "https://prodoctorov.ru/",
                },
            )
            if resp.status_code != 200:
                logger.debug("ProDoctorov search API returned %d for '%s'", resp.status_code, name)
                return None

            data = resp.json()
            for section in data:
                if section.get("title") == "Врачи":
                    for doctor in section.get("results", []):
                        if doctor.get("category") == "DOCTOR":
                            result_name = doctor.get("title", "")
                            if self._names_match(name, result_name):
                                return doctor.get("link", "")
                    break

        except Exception as e:
            logger.warning("ProDoctorov search API failed for '%s': %s", name, e)

        return None

    @staticmethod
    def _names_match(query: str, result: str) -> bool:
        """Check if all significant parts of query appear in the result name."""
        query_parts = [p for p in query.lower().split() if len(p) >= 2]
        result_lower = result.lower()
        return all(part in result_lower for part in query_parts)

    def _fetch_prodoctorov_profile(self, link: str) -> tuple[float, int]:
        """Fetch a ProDoctorov doctor profile page and extract rating/reviews.

        ProDoctorov embeds all doctor data as a Vue.js prop in SSR HTML:
        :doctor="{&quot;stars&quot;: 5.0, &quot;rates&quot;: 90, ...}"
        """
        try:
            url = f"https://prodoctorov.ru{link}" if link.startswith("/") else link
            resp = self._client.get(url)
            if resp.status_code != 200:
                return 0.0, 0

            match = re.search(r':doctor="({[^"]+})"', resp.text)
            if not match:
                logger.debug("No :doctor SSR data found on %s", url)
                return 0.0, 0

            doctor_json = _html_module.unescape(match.group(1))
            doctor_data = json.loads(doctor_json)

            stars = float(doctor_data.get("stars", 0))
            rates = int(doctor_data.get("rates", 0))
            return stars, rates

        except Exception as e:
            logger.warning("Failed to fetch ProDoctorov profile %s: %s", link, e)
            return 0.0, 0

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _parse_tg_subscribers(soup: BeautifulSoup) -> int:
        """Extract subscriber count from Telegram channel page.

        Looks for tgme_page_extra div which contains text like
        '1 234 subscribers' or '56.7K subscribers'.
        """
        try:
            extra = soup.select_one(".tgme_page_extra")
            if extra:
                text = extra.get_text(strip=True)
                # Parse "1 234 subscribers" or "56.7K subscribers"
                match = re.search(r"([\d\s.,]+[KkMm]?)\s*subscriber", text)
                if match:
                    raw = match.group(1).replace(",", ".").replace(" ", "")
                    return SocialScanner._parse_abbreviated_count(raw)
        except Exception:
            pass
        return 0

    @staticmethod
    def _parse_vk_subscribers(group_tag) -> int:
        """Extract member/subscriber count from VK search result group element.

        Looks for text patterns like '1 234 подписчика' or '56.7K участников'
        in sibling elements or the group description.
        """
        try:
            text = group_tag.get_text(" ", strip=True)
            # VK shows: "12 345 подписчиков", "1.2K участников", "1 234 члена"
            match = re.search(
                r"([\d\s.,]+[KkМ]?)\s*(?:подписчик|участник|член|subscriber|member)",
                text,
            )
            if match:
                raw = match.group(1).replace(",", ".").replace(" ", "")
                return SocialScanner._parse_abbreviated_count(raw)
        except Exception:
            pass
        return 0

    def _scrape_vk_profile(self, url: str) -> dict:
        """Fetch a VK profile/page and extract subscriber/friend counts and bio.

        VK is heavily JS-rendered, but the initial HTML often contains:
        - Meta og:description with follower count
        - Inline JSON blobs with page info
        - Static counter elements for public pages

        Returns dict with keys: subscribers, posts_count, topics.
        Empty dict if nothing could be extracted.
        """
        try:
            self._rate_limit(min_delay=1.0)
            resp = self._client.get(url, headers={"Accept-Language": "ru-RU,ru;q=0.9"})
            if resp.status_code != 200:
                return {}

            soup = BeautifulSoup(resp.text, "html.parser")

            result: dict = {}

            # Strategy 1: Look for subscriber count in meta tags
            meta_desc = soup.select_one('meta[property="og:description"]')
            if meta_desc:
                desc = meta_desc.get("content", "")
                # VK og:description for profiles often contains:
                # "Имя Фамилия. 123 друга. 45 подписчиков."
                # or "Название. 1 234 участника."
                patterns = [
                    (r"([\d\s]+)\s*подписчик", "subscribers"),
                    (r"([\d\s]+)\s*участник", "subscribers"),
                    (r"([\d\s]+)\s*друг", "friends"),
                    (r"([\d\s]+)\s*friend", "friends"),
                    (r"([\d\s]+)\s*follower", "subscribers"),
                    (r"([\d\s]+)\s*member", "subscribers"),
                ]
                for pattern, key in patterns:
                    match = re.search(pattern, desc, re.IGNORECASE)
                    if match:
                        raw = match.group(1).replace(",", ".").replace(" ", "")
                        count = self._parse_abbreviated_count(raw)
                        if count > 0:
                            if key == "friends":
                                # Friends ≈ subscribers for personal profiles
                                result["subscribers"] = count
                            else:
                                result["subscribers"] = count
                            break

            # Strategy 2: Look for inline data in scripts
            for script in soup.select("script"):
                text = script.string or ""
                # VK often embeds page info as JSON in inline scripts
                if '"members_count"' in text or '"followers_count"' in text:
                    try:
                        # Extract the JSON object containing these fields
                        members_m = re.search(r'"members_count":(\d+)', text)
                        followers_m = re.search(r'"followers_count":(\d+)', text)
                        if members_m:
                            result["subscribers"] = int(members_m.group(1))
                        elif followers_m:
                            result["subscribers"] = int(followers_m.group(1))
                    except Exception:
                        pass

            # Strategy 3: Look for visible counters (public pages)
            counter_selectors = [
                ".page_members_count",
                ".group_members_count",
                ".profile_friends_count",
                ".header_subscribers_count",
            ]
            for selector in counter_selectors:
                el = soup.select_one(selector)
                if el:
                    text = el.get_text(strip=True)
                    digits = re.sub(r"[^\d]", "", text)
                    if digits:
                        result["subscribers"] = int(digits)
                        break

            # Try to extract bio/description for topics
            bio_el = (
                soup.select_one(".profile_short_desc")
                or soup.select_one(".page_current_info")
                or soup.select_one(".group_description")
            )
            if bio_el:
                bio_text = bio_el.get_text(strip=True)
                if bio_text and len(bio_text) > 15:
                    result["topics"] = self._extract_bio_topics(bio_text)

            return result

        except Exception as e:
            logger.debug("VK profile scrape failed for '%s': %s", url, e)
            return {}

    @staticmethod
    def _parse_abbreviated_count(raw: str) -> int:
        """Parse abbreviated count strings like '1.2K', '56M', '1234' into int."""
        raw = raw.upper().replace("М", "M").replace("К", "K")
        try:
            if raw.endswith("K"):
                return int(float(raw[:-1]) * 1_000)
            elif raw.endswith("M"):
                return int(float(raw[:-1]) * 1_000_000)
            else:
                return int(raw)
        except (ValueError, TypeError):
            return 0

    @staticmethod
    def _extract_bio_topics(bio_text: str, max_topics: int = 5) -> list[str]:
        """Extract short topic phrases from a bio/description text.

        Splits on punctuation and newlines, filters very short fragments,
        returns at most max_topics items.
        """
        if not bio_text:
            return []
        topics: list[str] = []
        # Split on common delimiters: period, comma, newline, emoji separators
        fragments = re.split(r"[.,\n;|•·•●■♦▪▸►▶]|\s{2,}", bio_text)
        for fragment in fragments:
            clean = fragment.strip()
            if 15 <= len(clean) <= 100:
                topics.append(clean)
                if len(topics) >= max_topics:
                    break
        return topics

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
