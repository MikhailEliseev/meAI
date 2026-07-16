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
_fc_exhausted: dict[str, float] = {}  # key → expiry timestamp
_EXHAUSTED_TTL = 3600  # 1 hour
_fc_lock = __import__("threading").Lock()


import time as _time


def _load_firecrawl_keys() -> list[str]:
    """Загружает Firecrawl ключи из env или JSON пула."""
    global _fc_keys
    if _fc_keys:
        return _fc_keys

    keys = set()
    for prefix in ("FIRECRAWL_API_KEY_", "FIRECRAWL_KEY_"):
        for i in range(1, 21):
            k = os.getenv(f"{prefix}{i:02d}", "") or os.getenv(f"{prefix}{i}", "")
            if k:
                keys.add(k)
    single = os.getenv("FIRECRAWL_API_KEY", "")
    if single:
        keys.add(single)

    pool_path = os.getenv("FIRECRAWL_KEYS_FILE", "/opt/keys/firecrawl.json")
    try:
        import json
        if os.path.exists(pool_path):
            with open(pool_path) as f:
                data = json.load(f)
            for entry in data.get("keys", []):
                if entry.get("status") == "active":
                    keys.add(entry.get("token", ""))
    except Exception:
        pass

    _fc_keys = [k for k in keys if k]
    logger.info("Firecrawl enricher: %d keys loaded", len(_fc_keys))
    return _fc_keys


def _get_next_key() -> Optional[str]:
    """Round-robin по активным ключам (исключая exhausted с TTL)."""
    global _fc_idx
    with _fc_lock:
        now = _time.time()
        # Clear expired exhaustion entries
        expired = [k for k, t in _fc_exhausted.items() if t < now]
        for k in expired:
            del _fc_exhausted[k]
        keys = [k for k in _load_firecrawl_keys() if k not in _fc_exhausted]
        if not keys:
            return None
        key = keys[_fc_idx % len(keys)]
        _fc_idx += 1
        return key


def _mark_key_exhausted(key: str):
    """Помечает ключ исчерпанным на _EXHAUSTED_TTL секунд."""
    with _fc_lock:
        _fc_exhausted[key] = _time.time() + _EXHAUSTED_TTL
    logger.warning("Firecrawl key exhausted …%s (TTL %ds, total: %d)",
                   key[-4:], _EXHAUSTED_TTL, len(_fc_exhausted))


async def _firecrawl_request(endpoint: str, payload: dict, max_retries: int = 3) -> Optional[dict]:
    """Вызывает Firecrawl API с ротацией ключей."""
    async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT) as client:
        for attempt in range(max_retries):
            key = _get_next_key()
            if not key:
                logger.warning("Firecrawl: no active keys available")
                return None
            try:
                resp = await client.post(
                    endpoint,
                    headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
                    json=payload,
                )
                if resp.status_code == 402:
                    _mark_key_exhausted(key)
                    logger.warning("Firecrawl key exhausted 402 (attempt %d)", attempt + 1)
                    continue
                if resp.status_code == 429:
                    # Transient rate limit — НЕ убиваем ключ, просто retry
                    logger.warning("Firecrawl rate limited 429 (attempt %d) — retrying", attempt + 1)
                    continue
                resp.raise_for_status()
                return resp.json()
            except httpx.HTTPError as e:
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
    """Скрапит сайт → CMS, размер, ссылки, соцсети.

    Returns:
        {"cms": str|None, "page_size_kb": float|None, "title": str|None,
         "links": int|None, "socials": dict|None}
    """
    result = {"cms": None, "page_size_kb": None, "title": None, "links": None, "socials": None}

    data = await _firecrawl_request(FIRECRAWL_SCRAPE, {
        "url": url,
        "formats": ["markdown", "html"],
        "onlyMainContent": False,
        "waitFor": 3000,
    })
    if not data or not data.get("success", True):
        return result

    page_data = data.get("data", {})
    html_content = page_data.get("markdown", "") or page_data.get("html", "")
    raw_html = page_data.get("html", "") or ""

    # Размер
    if html_content:
        result["page_size_kb"] = round(len(html_content.encode("utf-8")) / 1024, 1)

    # Количество внутренних ссылок (считаем из metadata если есть)
    links = page_data.get("links", [])
    if links:
        result["links"] = len(links)
    elif raw_html:
        # Считаем <a href> на главной странице как approximation
        internal_links = re.findall(r'href=["\'](/[a-z])', raw_html, re.I)
        result["links"] = len(set(internal_links))

    # CMS detection
    html_lower = (html_content + " " + raw_html).lower()
    for cms, patterns in _CMS_PATTERNS.items():
        if any(p in html_lower for p in patterns):
            result["cms"] = cms
            break

    # <meta generator>
    gen_match = re.search(r'<meta[^>]+name=["\']generator["\'][^>]+content=["\']([^"\']+)', raw_html, re.I)
    if gen_match and not result["cms"]:
        gen = gen_match.group(1).strip()
        for cms, patterns in _CMS_PATTERNS.items():
            if cms.lower() in gen.lower():
                result["cms"] = cms
                break
        if not result["cms"]:
            result["cms"] = gen[:30]

    # Title
    title_match = re.search(r"<title[^>]*>([^<]+)", raw_html, re.I)
    if title_match:
        result["title"] = title_match.group(1).strip()[:100]

    # Соцсети из HTML (реальные href ссылки, не Perplexity-текст)
    socials = _extract_socials_from_html(raw_html)
    if socials:
        result["socials"] = socials

    return result


def _extract_socials_from_html(html: str) -> dict:
    """Извлекает реальные ссылки на соцсети из HTML.

    Ищет href ссылки на instagram.com, vk.com, t.me, youtube.com.
    Возвращает {platform: url} или пустой dict.
    """
    socials = {}
    patterns = [
        ("instagram", r'href=["\']([^"\']*instagram\.com/[^"\'/?#]+)'),
        ("vk", r'href=["\']([^"\']*vk\.com/[^"\'/?#]+)'),
        ("telegram", r'href=["\']([^"\']*(?:t\.me|telegram\.me)/[^"\'/?#]+)'),
        ("youtube", r'href=["\']([^"\']*youtube\.com/[^"\'/?#@]+)'),
    ]
    for platform, pattern in patterns:
        matches = re.findall(pattern, html, re.I)
        if matches:
            # Берём первую не-мусорную ссылку
            for url in matches:
                handle = url.split("/")[-1].lower()
                if handle not in ("p", "reel", "explore", "accounts", "stories",
                                  "watch", "feed", "channel", "share"):
                    socials[platform] = url
                    break
    return socials


# ── Количество страниц (/map) ───────────────────────────────────────

async def map_website(url: str) -> int:
    """Возвращает количество страниц сайта через Firecrawl /map."""
    data = await _firecrawl_request(FIRECRAWL_MAP, {"url": url, "limit": 200})
    if not data or not data.get("success", True):
        return 0
    links = data.get("data", {}).get("links", [])
    return len(links) if links else 0


# ── Врачи (скрап /vrachi или /team) ──────────────────────────────────

_DOCTOR_URL_PATTERNS = [
    "/vrachi", "/doctors", "/team", "/specialists", "/staff",
    "/about/doctors", "/o-klinike/vrachi",
    "/specialisty", "/our-team", "/kollektiv",  # русские варианты
    "/klinika/komanda", "/klinik/vrachi", "/klinika/vrachi",
    "/o-nas/komanda", "/o-nas/vrachi", "/nashi-spetsialisty",
]


async def scrape_doctors(url: str, brand_name: str = "") -> Optional[int]:
    """Скрапит страницу врачей → считает количество карточек.

    Алгоритм:
    1. Скрапить главную → найти ссылки на страницу врачей
    2. Если найдена → скрапить её, посчитать врачей
    3. Если не найдена → пробовать стандартные паттерны

    Returns:
        Количество врачей (int) или None если страница не найдена.
    """
    base_url = url.rstrip("/")

    # Шаг 0: Найти URL страницы врачей из главной
    doctor_page_urls = []
    try:
        homepage_data = await _firecrawl_request(FIRECRAWL_SCRAPE, {
            "url": url, "formats": ["markdown"], "onlyMainContent": False, "waitFor": 3000,
        })
        if homepage_data and homepage_data.get("success", True):
            md = homepage_data.get("data", {}).get("markdown", "")
            from urllib.parse import urljoin
            md_links = re.findall(r'\[([^\]]+)\]\(([^)]+)\)', md)
            for text, href in md_links:
                if any(k in (text + href).lower() for k in
                       ["врач", "doctor", "специалист", "specialist", "team", "команда",
                        "staff", "сотрудник", "personal"]):
                    full_url = urljoin(url, href)
                    if full_url not in doctor_page_urls and "mailto:" not in full_url:
                        doctor_page_urls.append(full_url)
    except Exception:
        pass

    # Шаг 1: Скрапить найденные страницы врачей (максимум 2)
    for doc_url in doctor_page_urls[:2]:
        count = await _count_doctors_on_page(doc_url)
        if count:
            return count

    # Шаг 2: Пробовать стандартные паттерны
    for pattern in _DOCTOR_URL_PATTERNS:
        doc_url = base_url + pattern
        count = await _count_doctors_on_page(doc_url)
        if count:
            return count

    return None


async def _count_doctors_on_page(url: str) -> Optional[int]:
    """Скрапит страницу → считает врачей. Возвращает None если 0."""
    data = await _firecrawl_request(FIRECRAWL_SCRAPE, {
        "url": url,
        "formats": ["markdown"],
        "onlyMainContent": True,
        "waitFor": 3000,
    })
    if not data or not data.get("success", True):
        return None

    markdown = data.get("data", {}).get("markdown", "")
    if not markdown or len(markdown) < 200:
        return None

    # Считаем карточки врачей по паттернам
    # Паттерн 1: списки с именами «Иванов И.И.»
    doctor_names = re.findall(
        r"(?:^|\n)[-•*]\s*([А-ЯЁ][а-яё]+\s+[А-ЯЁ]\.\s*[А-ЯЁ]\.)",
        markdown,
    )
    if len(doctor_names) >= 2:
        return len(doctor_names)

    # Паттерн 2: заголовки карточек <h3>/<h4> — только имя + инициалы
    headings = re.findall(r"^#{3,4}\s+([А-ЯЁ][а-яё]+ [А-ЯЁ]\.?\s*[А-ЯЁ]\.?[^#\n]{0,50})", markdown, re.MULTILINE)
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

    Если website неизвестен — ищет через Firecrawl search по названию бренда.
    Modifies competitors in place.
    """
    sem = asyncio.Semaphore(3)

    async def _enrich_single(comp):
        async with sem:
            brand = ""
            if hasattr(comp, "profile"):
                brand = comp.profile.brand_name or comp.profile.legal_name or ""
            if not brand:
                return

            # Шаг 1: найти website (если не задан)
            website = None
            if hasattr(comp, "website") and comp.website:
                website = comp.website
            elif hasattr(comp, "profile") and comp.profile.website:
                website = comp.profile.website

            if not website:
                # Поиск сайта через Firecrawl search
                website = await _find_clinic_website(brand)
                if website:
                    if hasattr(comp, "profile"):
                        comp.profile.website = website
                    if hasattr(comp, "website"):
                        comp.website = website

            if not website:
                logger.debug("Firecrawl enrich: no website for %s", brand[:30])
                return

            try:
                # Шаг 2: CMS + размер + ссылки + соцсети + schema
                site_data = await scrape_website(website)
                if site_data.get("cms"):
                    comp.profile.social_links["website_cms"] = site_data["cms"]
                if site_data.get("page_size_kb"):
                    comp.profile.social_links["website_size_kb"] = str(site_data["page_size_kb"])
                if site_data.get("links"):
                    comp.profile.social_links["website_pages"] = str(site_data["links"])
                if site_data.get("socials"):
                    for platform, url in site_data["socials"].items():
                        if platform == "instagram" and not comp.profile.social_links.get("instagram"):
                            comp.profile.social_links["instagram"] = f"@{url.split('/')[-1]}"
                        elif platform == "vk":
                            comp.profile.social_links["vk"] = url
                        elif platform == "telegram":
                            comp.profile.social_links["telegram"] = url

                # Шаг 3: Врачи (если СЧЛ неизвестен)
                if not comp.profile.employee_count:
                    doctors = await scrape_doctors(website, brand)
                    if doctors:
                        comp.profile.employee_count = doctors

            except Exception as e:
                logger.warning("Firecrawl enrich failed for %s: %s", website[:50], str(e)[:100])

    tasks = [_enrich_single(c) for c in competitors[:max_count]]
    await asyncio.gather(*tasks, return_exceptions=True)
    logger.info("Firecrawl enrich: %d competitors processed", len(competitors[:max_count]))


async def _find_clinic_website(brand_name: str) -> Optional[str]:
    """Находит сайт клиники через Firecrawl search."""
    query = f"сайт клиники {brand_name}"
    data = await _firecrawl_request(FIRECRAWL_SEARCH, {"query": query, "limit": 5})
    if not data:
        return None

    results = data.get("data", data.get("results", []))
    for res in results:
        url = res.get("url", "") if isinstance(res, dict) else ""
        # Фильтр: только сайты клиник (не агрегаторы)
        if not url:
            continue
        skip = ("instagram.com", "vk.com", "youtube.com", "facebook.com",
                "prodoctorov.ru", "yandex.ru", "2gis.ru", "docdoc.ru",
                "zoon.ru", "nashe-tagil.ru", "avito.ru")
        if any(s in url.lower() for s in skip):
            continue
        # Возвращаем первый подходящий URL
        return url

    return None
