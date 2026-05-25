"""Lightweight competitor website scraper — extracts real services from clinic sites.

Uses httpx + BeautifulSoup (no headless browser). Fast (~2-3s per site), free,
and sufficient for Russian clinic websites which are mostly server-rendered.

Replaces the heavy apify/website-content-crawler which OOM-kills on free tier.
"""

import logging
import re
from typing import Optional
from urllib.parse import urljoin, urlparse

import httpx
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/131.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "ru-RU,ru;q=0.9,en;q=0.8",
}

_TIMEOUT = 15.0

# Medical service keywords for Russian clinic websites
_SERVICE_KEYWORDS = [
    # Стоматология
    "лечение зубов", "лечение пульпита", "лечение дёсен", "лечение десен",
    "имплантация", "удаление зуб", "удаление зуба",
    "профессиональная гигиена", "гигиена полости рта",
    "отбеливание", "коронк", "протезирование", "винир",
    "брекет", "исправление прикуса", "ортодонт",
    "хирургическая стоматология", "терапевтическая стоматология",
    "ортопедическая стоматология", "детская стоматология",
    # Косметология
    "косметологи", "чистка лица", "пилинг", "мезотерапия", "биоревитализация",
    "контурная пластика", "увеличение губ", "ботулотоксин", "ботокс",
    "лазерная эпиляция", "эпиляция", "фотоомоложение", "smash-лифтинг",
    "плазмотерапия", "плазмолифтинг", "уход за кожей",
    "аппаратная косметология", "инъекционная косметология",
    "удаление новообразований", "удаление папиллом",
    # Медицинские
    "терапия", "диагностика", "узи", "мрт", "кт",
    "гинекология", "урология", "дерматология", "неврология",
    "кардиология", "эндокринология", "гастроэнтерология",
    "педиатрия", "офтальмология", "отоларингология", "лор",
    "пластическая хирургия", "реабилитация", "физиотерапия",
    "массаж", "анализы", "вакцинация", "прививк",
    # Общие
    "консультация", "приём", "прием", "осмотр",
]


async def scrape_services(url: str) -> list[str]:
    """Extract medical services from a clinic website.

    Fetches the homepage + /uslugi (services) page if it exists,
    then matches visible text against known medical service keywords.

    Args:
        url: Website URL (with or without scheme)

    Returns:
        List of service names found (lowercase, deduplicated).
    """
    if not url:
        return []

    if not url.startswith("http"):
        url = f"https://{url}"

    found_services: set[str] = set()

    async with httpx.AsyncClient(
        timeout=_TIMEOUT,
        follow_redirects=True,
        verify=False,
    ) as client:
        # Fetch homepage
        try:
            resp = await client.get(url, headers=_HEADERS)
            if resp.status_code < 400:
                _extract_from_html(resp.text, found_services)
        except Exception as e:
            logger.debug("scrape_services: homepage failed for %s: %s", url, e)

        # Try /uslugi page
        try:
            uslugi_url = urljoin(url, "/uslugi")
            resp = await client.get(uslugi_url, headers=_HEADERS)
            if resp.status_code < 400:
                _extract_from_html(resp.text, found_services)
        except Exception:
            pass

    result = sorted(found_services)
    if result:
        logger.debug("scrape_services: %d services from %s → %s", len(result), url, result)
    return result


def _extract_from_html(html: str, found: set[str]) -> None:
    """Extract service keywords from HTML content."""
    soup = BeautifulSoup(html, "html.parser")

    # Remove non-content elements
    for tag in soup(["script", "style", "noscript", "nav", "footer"]):
        tag.decompose()

    text = soup.get_text(separator=" ", strip=True).lower()

    for kw in _SERVICE_KEYWORDS:
        if kw in text:
            found.add(kw)


async def scrape_services_batch(
    urls: list[str], max_concurrent: int = 5
) -> dict[str, list[str]]:
    """Scrape services from multiple URLs concurrently.

    Args:
        urls: List of website URLs
        max_concurrent: Max concurrent requests (default 5 to avoid rate limiting)

    Returns:
        Dict mapping URL → list of services found.
    """
    import asyncio

    semaphore = asyncio.Semaphore(max_concurrent)

    async def _scrape_one(u: str) -> tuple[str, list[str]]:
        async with semaphore:
            return u, await scrape_services(u)

    tasks = [_scrape_one(u) for u in urls if u]
    results = await asyncio.gather(*tasks, return_exceptions=True)

    output: dict[str, list[str]] = {}
    for r in results:
        if isinstance(r, Exception):
            logger.warning("scrape_services_batch: %s", r)
        else:
            output[r[0]] = r[1]
    return output


# ── Social media link extraction ─────────────────────────────────────


SOCIAL_DOMAINS: dict[str, str] = {
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

    # Strategy 1: <a href="..."> tags
    for a in soup.find_all("a", href=True):
        href = a["href"].strip()
        if not href:
            continue
        result = _check_url(href)
        if result:
            platform, url = result
            if platform not in found:
                found[platform] = url

    # Strategy 2: data-url attributes
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
