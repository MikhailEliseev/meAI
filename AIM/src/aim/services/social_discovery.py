"""Social media link discovery for competitor websites.

Reusable social link extraction — used by both CI marketing analysis
and competitor discovery pipeline.

Usage:
    from aim.services.social_discovery import extract_social_links, SocialDiscoveryClient

    # Reusable function (used by ci_marketing_analysis.py)
    links = extract_social_links(html, base_url)

    # Async client for competitor pipeline
    client = SocialDiscoveryClient()
    socials = await client.discover("https://clinic.ru")
"""

import logging
import re
from urllib.parse import urlparse

import httpx
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

SOCIAL_DOMAINS = {
    "vk.com": "vk",
    "instagram.com": "instagram",
    "youtube.com": "youtube",
    "t.me": "telegram",
    "telegram.me": "telegram",
    "whatsapp.com": "whatsapp",
    "wa.me": "whatsapp",
    "dzen.ru": "dzen",
    "zen.yandex.ru": "dzen",
}


def extract_social_links(html: str, base_url: str = "") -> dict[str, str]:
    """Extract social media links from HTML content.

    Returns a dict mapping platform name → URL, e.g.:
        {"vk": "https://vk.com/clinic123", "telegram": "https://t.me/clinic123"}
    """
    soup = BeautifulSoup(html, "html.parser")
    found: dict[str, str] = {}

    def _check_url(href: str) -> str | None:
        """Check if href is a social URL. Returns normalized URL or None."""
        if not href or len(href) < 4:
            return None
        href_lower = href.strip().lower()
        for domain, platform in SOCIAL_DOMAINS.items():
            if platform in found:
                continue
            if domain in href_lower:
                href = href.strip()
                if href.startswith("//"):
                    href = "https:" + href
                elif href.startswith("/"):
                    if base_url:
                        parsed = urlparse(base_url)
                        href = f"{parsed.scheme}://{parsed.netloc}{href}"
                    else:
                        return None
                elif not href.startswith("http"):
                    href = "https://" + href
                return platform, href
        return None

    # Strategy 1: <a href="..."> tags (most common)
    for a in soup.find_all("a", href=True):
        href = a["href"].strip()
        if not href:
            continue
        result = _check_url(href)
        if result:
            platform, url = result
            if platform not in found:
                found[platform] = url

    # Strategy 2: data-url attributes on any element
    # Some sites use <span data-url="https://vk.com/..."> instead of <a href="...">
    for el in soup.find_all(attrs={"data-url": True}):
        data_url = el["data-url"].strip()
        if not data_url:
            continue
        result = _check_url(data_url)
        if result:
            platform, url = result
            if platform not in found:
                found[platform] = url

    # Strategy 3: onclick attributes containing social URLs
    # Pattern: onclick="window.open('https://vk.com/...')"
    onclick_re = re.compile(
        r"""(?:window\.open\(|location\.href\s*=\s*)(['"])(https?://[^'"]+)\1""",
        re.IGNORECASE,
    )
    for el in soup.find_all(attrs={"onclick": True}):
        onclick = el.get("onclick", "")
        if not onclick:
            continue
        match = onclick_re.search(onclick)
        if match:
            url_candidate = match.group(2)
            result = _check_url(url_candidate)
            if result:
                platform, url = result
                if platform not in found:
                    found[platform] = url

    return found


class SocialDiscoveryClient:
    """Async client that fetches a competitor website and extracts social links.

    Lightweight — single-page fetch with httpx, no headless browser.
    """

    def __init__(self, timeout: float = 10.0):
        self.timeout = timeout

    async def discover(self, website: str) -> dict[str, str]:
        """Fetch a website and extract social media links.

        Returns dict of platform → URL. Empty dict if the site is unreachable
        or has no social links.
        """
        if not website:
            return {}

        url = website if website.startswith("http") else f"https://{website}"

        try:
            async with httpx.AsyncClient(
                timeout=self.timeout, follow_redirects=True,
            ) as client:
                resp = await client.get(url, headers={
                    "User-Agent": (
                        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
                    ),
                    "Accept": "text/html,application/xhtml+xml",
                    "Accept-Language": "ru-RU,ru;q=0.9",
                })
                html = resp.text
        except Exception as e:
            logger.debug("SocialDiscovery: failed to fetch %s: %s", url, e)
            return {}

        links = extract_social_links(html, url)
        if links:
            logger.debug("SocialDiscovery: found %s for %s", list(links.keys()), url)
        return links


# ── Singleton ────────────────────────────────────────────────────────

_social_discovery: SocialDiscoveryClient | None = None


def get_social_discovery_client() -> SocialDiscoveryClient:
    global _social_discovery
    if _social_discovery is None:
        _social_discovery = SocialDiscoveryClient()
    return _social_discovery
