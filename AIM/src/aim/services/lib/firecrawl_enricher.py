"""Firecrawl enrichment — скрапинг сайтов клиник для точных данных.

Каждый инструмент отвечает за свою цифру:
- scrape_website(url) → CMS/платформа, размер страницы
- map_website(url) → количество страниц
- scrape_doctors(url) → количество врачей (по /vrachi или /team)
- search_instagram_handle(brand, city) → IG handle через поиск

Использует UnifiedKeyPool (через FirecrawlKeyBank) для ротации ключей.
"""

import asyncio
import logging
import os
import re
from typing import Optional

import httpx

logger = logging.getLogger(__name__)

FIRECRAWL_SCRAPE = "https://api.firecrawl.dev/v1/scrape"
FIRECRAWL_SEARCH = "https://api.firecrawl.dev/v1/search"
FIRECRAWL_MAP = "https://api.firecrawl.dev/v1/map"
REQUEST_TIMEOUT = 30.0

# Ключи Firecrawl — UnifiedKeyPool через env
_fc_keys: list[str] = []
_fc_idx = 0


def _load_firecrawl_keys() -> list[str]:
    """Загружает Firecrawl ключи из env или JSON пула."""
    global _fc_keys
    if _fc_keys:
        return _fc_keys

    keys = set()
    # Из env (fallback)
    for prefix in ("FIRECRAWL_API_KEY_", "FIRECRAWL_KEY_"):
        for i in range(1, 21):
            k = os.getenv(f"{prefix}{i:02d}", "") or os.getenv(f"{prefix}{i}", "")
            if k:
                keys.add(k)
    single = os.getenv("FIRECRAWL_API_KEY", "")
    if single:
        keys.add(single)

    # Из JSON пула (приоритет)
    pool_path = os.getenv("FIRECRAWL_KEYS_FILE", "/opt/keys/firecrawl.json")
    try:
        import json
        if os.path.exists(pool_path):
            data = json.load(open(pool_path))
            for entry in data.get("keys", []):
                if entry.get("status") == "active":
                    keys.add(entry.get("token", ""))
    except Exception:
        pass

    _fc_keys = [k for k in keys if k]
    logger.info("Firecrawl enricher: %d keys loaded", len(_fc_keys))
    return _fc_keys


def _get_next_key() -> Optional[str]:
    """Round-robin по ключам Firecrawl."""
    global _fc_idx
    keys = _load_firecrawl_keys()
    if not keys:
        return None
    key = keys[_fc_idx % len(keys)]
    _fc_idx += 1
    return key


async def _firecrawl_request(endpoint: str, payload: dict, max_retries: int = 2) -> Optional[dict]:
    """Вызывает Firecrawl API с ротацией ключей."""
    async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT) as client:
        for attempt in range(max_retries):
            key = _get_next_key()
            if not key:
                logger.warning("Firecrawl: no keys available")
                return None
            try:
                resp = await client.post(
                    endpoint,
                    headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
                    json=payload,
                )
                if resp.status_code in (402, 429):
                    logger.warning("Firecrawl key exhausted (attempt %d): %d", attempt + 1, resp.status_code)
                    continue
                resp.raise_for_status()
                return resp.json()
            except Exception as e:
                logger.warning("Firecrawl request failed (attempt %d): %s", attempt + 1, str(e)[:100])
    return None


# ── CMS / платформа ──────────────────────────────────────────────────

_CMS_PATTERNS = {
    "Tilda": ["tilda", "tildacdn"],
    "1C-Bitrix": ["bitrix", "1c-bitrix", "bx-core"],
    "WordPress": ["wp-content", "wp-includes", "wordpress"],
    "Joomla": ["joomla"],
    "OpenCart": ["opencart", "oc-"],
    "Drupal": ["drupal"],
    "Wix": ["wix.com", "wixstatic"],
    "Shopify": ["shopify", "cdn.shopify"],
    "MODX": ["modx", "manager/"],
    "SiteEdit": ["siteedit"],
}


async def scrape_website(url: str) -> dict:
    """Скрапит сайт → CMS, размер страницы, HTML meta.

    Returns:
        {"cms": "Tilda"|None, "page_size_kb": int|None, "title": str|None}
    """
    result = {"cms": None, "page_size_kb": None, "title": None}

    data = await _firecrawl_request(FIRECRAWL_SCRAPE, {
        "url": url,
        "formats": ["markdown"],
        "onlyMainContent": False,
        "waitFor": 3000,
    })
    if not data or not data.get("success", True):
        return result

    page_data = data.get("data", {})
    html_content = page_data.get("markdown", "") or page_data.get("html", "")

    # Размер
    if html_content:
        result["page_size_kb"] = round(len(html_content.encode("utf-8")) / 1024, 1)

    # CMS detection
    html_lower = html_content.lower()
    for cms, patterns in _CMS_PATTERNS.items():
        if any(p in html_lower for p in patterns):
            result["cms"] = cms
            break

    # <meta generator>
    gen_match = re.search(r'<meta[^>]+name=["\']generator["\'][^>]+content=["\']([^"\']+)', html_content, re.I)
    if gen_match and not result["cms"]:
        gen = gen_match.group(1).strip()
        for cms, patterns in _CMS_PATTERNS.items():
            if cms.lower() in gen.lower():
                result["cms"] = cms
                break
        if not result["cms"]:
            result["cms"] = gen[:30]

    # Title
    title_match = re.search(r"<title[^>]*>([^<]+)", html_content, re.I)
    if title_match:
        result["title"] = title_match.group(1).strip()[:100]

    return result


# ── Количество страниц (/map) ───────────────────────────────────────

async def map_website(url: str) -> int:
    """Возвращает количество страниц сайта через Firecrawl /map."""
    data = await _firecrawl_request(FIRECRAWL_MAP, {"url": url, "limit": 200})
    if not data or not data.get("success", True):
        return 0
    links = data.get("data", {}).get("links", [])
    return len(links) if links else 0


# ── Врачи (скрап /vrachi или /team) ──────────────────────────────────

_DOCTOR_URL_PATTERNS = ["/vrachi", "/doctors", "/team", "/specialists", "/staff", "/about/doctors", "/o-klinike/vrachi"]


async def scrape_doctors(url: str, brand_name: str = "") -> Optional[int]:
    """Скрапит страницу врачей → считает количество карточек.

    Returns:
        Количество врачей (int) или None если страница не найдена.
    """
    base_url = url.rstrip("/")

    # Пробуем разные URL паттерны
    for pattern in _DOCTOR_URL_PATTERNS:
        doc_url = base_url + pattern
        data = await _firecrawl_request(FIRECRAWL_SCRAPE, {
            "url": doc_url,
            "formats": ["markdown"],
            "onlyMainContent": True,
            "waitFor": 3000,
        })
        if not data or not data.get("success", True):
            continue

        markdown = data.get("data", {}).get("markdown", "")
        if not markdown or len(markdown) < 200:
            continue

        # Считаем карточки врачей по паттернам
        # Паттерн 1: списки с именами «Иванов И.И.»
        doctor_names = re.findall(
            r"(?:^|\n)[-•*]\s*([А-ЯЁ][а-яё]+\s+[А-ЯЁ]\.\s*[А-ЯЁ]\.)",
            markdown,
        )
        if len(doctor_names) >= 2:
            return len(doctor_names)

        # Паттерн 2: заголовки карточек <h3> или <h4>
        headings = re.findall(r"^#{3,4}\s+([А-ЯЁ][а-яё]+)", markdown, re.MULTILINE)
        if len(headings) >= 2:
            return len(headings)

        # Паттерн 3: «Записаться к N врачам» или «У нас N специалистов»
        count_match = re.search(
            r"(\d+)\s*(?:врач|специалист|хирург|эксперт)",
            markdown,
            re.I,
        )
        if count_match:
            n = int(count_match.group(1))
            if 1 <= n <= 500:
                return n

    return None


# ── IG handle через Firecrawl search ─────────────────────────────────

async def search_instagram_handle(brand_name: str, city: str = "") -> Optional[str]:
    """Ищет Instagram handle клиники через Firecrawl search.

    Returns:
        IG handle (без @) или None.
    """
    query = f"instagram {brand_name} {city}".strip()
    data = await _firecrawl_request(FIRECRAWL_SEARCH, {"query": query, "limit": 5})
    if not data:
        return None

    results = data.get("data", data.get("results", []))
    for res in results:
        url = res.get("url", "") if isinstance(res, dict) else ""
        # instagram.com/handle
        ig_match = re.match(r"https?://(?:www\.)?instagram\.com/([^/?]+)", url)
        if ig_match:
            handle = ig_match.group(1)
            # Фильтр мусорных handles
            if handle.lower() not in ("p", "reel", "explore", "accounts", "stories"):
                return handle

    return None


# ── Batch enrichment ─────────────────────────────────────────────────

async def enrich_websites_batch(competitors: list, max_count: int = 5) -> None:
    """Обогащает список конкурентов: CMS, страницы, врачи.

    Modifies competitors in-place (добавляет в social_links и website).
    competitors: list[CompetitorMatch] — но импорт круговой, поэтому duck typing.
    """
    sem = asyncio.Semaphore(3)  # максимум 3 параллельных Firecrawl запроса

    async def _enrich_single(comp):
        async with sem:
            website = None
            # website из профиля
            if hasattr(comp, "website") and comp.website:
                website = comp.website
            elif hasattr(comp, "profile") and comp.profile.website:
                website = comp.profile.website
            if not website:
                return

            try:
                # CMS + размер
                site_data = await scrape_website(website)
                if site_data.get("cms"):
                    comp.profile.social_links["website_cms"] = site_data["cms"]
                if site_data.get("page_size_kb"):
                    comp.profile.social_links["website_size_kb"] = str(site_data["page_size_kb"])

                # Количество страниц (опционально, не блокирующее)
                try:
                    pages = await map_website(website)
                    if pages:
                        comp.profile.social_links["website_pages"] = str(pages)
                except Exception:
                    pass

                # Врачи (заменяет Perplexity оценку)
                if not comp.profile.employee_count:
                    doctors = await scrape_doctors(website, comp.profile.brand_name or "")
                    if doctors:
                        comp.profile.employee_count = doctors

            except Exception as e:
                logger.warning("Firecrawl enrich failed for %s: %s", website[:50], str(e)[:100])

    tasks = [_enrich_single(c) for c in competitors[:max_count]]
    await asyncio.gather(*tasks, return_exceptions=True)
    logger.info("Firecrawl enrich: %d competitors processed", len(competitors[:max_count]))
