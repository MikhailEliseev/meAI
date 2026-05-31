"""Lightweight competitor website scraper — extracts real services from clinic sites.

Uses httpx + BeautifulSoup (no headless browser). Fast (~2-3s per site), free,
and sufficient for Russian clinic websites which are mostly server-rendered.

Replaces the heavy apify/website-content-crawler which OOM-kills on free tier.
"""

import asyncio
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


# ── INN extraction from website ──────────────────────────────────────
# Russian clinics (ООО, АО, ИП) are required to publish their ИНН on the
# website — usually in the footer, "Правовая информация", or "Контакты".
# We scrape the site, find the INN, then query rusprofile for real revenue.

_INN_RE = re.compile(
    r"ИНН\s*[:\s]*\s*(\d{10}(?:\s*/\s*\d{2,4})?)"  # "ИНН 1234567890" or "ИНН: 1234567890"
    r"|(\d{10})\s*ИНН",                                # "1234567890 ИНН"
    re.IGNORECASE,
)

_INN_PAGES = [
    "/",                    # homepage (footer)
    "/contacts",            # contact page
    "/kontakty",            # Russian variant
    "/about",               # about page
    "/o-kompanii",          # Russian variant
    "/o-nas",               # "about us" Russian variant
    "/o-klinike",           # "about clinic"
    "/policy",              # privacy policy
    "/privacy",             # privacy policy alt
    "/pravovaya-informatsiya",  # legal information
    "/docs",                # documents
    "/rekvizity",           # company details
    "/license",             # license page
    "/licenses",            # license page alt
    "/licenzii",            # Russian variant
]

# Known third-party INNs — these are NOT clinic INNs
_THIRD_PARTY_INNS: set[str] = {
    "7736207543",  # ООО «Яндекс»
    "7703388936",  # ООО «Колтач Солюшнс» (CloudPayments)
    "7707083893",  # ПАО Сбербанк
    "7710140679",  # АО Тинькоff Банк
    "7728168971",  # АО «Альфа-Банк»
    "7702070139",  # Банк ВТБ (ПАО)
}

# Context markers that suggest the INN belongs to a third party
_THIRD_PARTY_MARKERS = [
    "яндекс", "yandex", "сбер", "sber", "тинькофф", "tinkoff",
    "альфа-банк", "alfa-bank", "втб", "vtb",
    "cloudpayments", "колтач", "coltach",
    "веб-студия", "web-студия", "разработка сайта",
    "продвижение сайта", "seo-продвижение",
    "хостинг", "регистратор домен",
    "платёжная система", "платежный сервис", "эквайринг",
]

# Context markers that suggest the INN belongs to the clinic itself
_CLINIC_INN_MARKERS = [
    "огрн", "кпп", "оквэд", "окпо", "окато",
    "лицензия", "медицинск", "клиник", "стоматолог",
    "косметолог", "ooо", "ао", "зао",
]

# ── License extraction ──────────────────────────────────────────────
# Russian medical licenses follow these patterns:
#   Л041-01137-77/00307723  (new format, Moscow)
#   ЛО-77-01-012345         (old format)
#   ЛО-50-01-009876         (Moscow region old format)
#   ФС-77-01-012345         (Federal Service format)

_LICENSE_NUMBER_RE = re.compile(
    r"(?:Лицензи[яи]\s*(?:на\s+(?:осуществление\s+)?медицинскую\s+деятельность\s*)?)?"
    r"(?:[№#]\s*)?"
    r"([ЛФ]0?\d{1,4}[-–—]\d{2,4}[-–—]?\d{2,4}[-–—]?\d{2,4}[-–—/]\d{5,10})",
    re.IGNORECASE,
)

_LICENSE_DATE_RE = re.compile(
    r"(?:от|выдана|дата выдачи)\s*[:\s]*(\d{1,2}[./]\d{1,2}[./]\d{2,4})",
    re.IGNORECASE,
)

_LICENSE_ENTITY_NEAR_RE = re.compile(
    r'(?:ООО|АО|ЗАО|ИП|ПАО)\s*[«"]([^«»""]{3,80})[»""]',
    re.IGNORECASE,
)

_LICENSE_AUTHORITY_RE = re.compile(
    r"(?:выдана?\s*|лицензирующий\s+орган[:\s]*|Департамент[а]?\s+здравоохранения[:\s]*)"
    r"([^.]+?(?:здрав|надзор|Росздравнадзор|Минздрав|лицензирования)[^.]*)",
    re.IGNORECASE,
)


def _extract_licenses_from_html(html: str, page_path: str = "") -> list[dict]:
    """Extract medical license details from HTML content.

    Finds license numbers, dates, legal entity names, INNs, and
    issuing authorities from Russian clinic websites.

    Returns a list of dicts:
        [{number, date, legal_name, inn, authority, page_source}]
    """
    soup = BeautifulSoup(html, "html.parser")
    text = soup.get_text(separator=" ", strip=True)

    # Find all license matches first
    lic_matches = [(m.group(1).strip(), m.start(), m.end()) for m in _LICENSE_NUMBER_RE.finditer(text)]

    licenses: list[dict] = []
    seen_numbers: set[str] = set()

    for i, (lic_number, lic_start, lic_end) in enumerate(lic_matches):
        if lic_number in seen_numbers:
            continue
        seen_numbers.add(lic_number)

        # Context: from license match to next license match (or +400 chars)
        next_start = lic_matches[i + 1][1] if i + 1 < len(lic_matches) else len(text)
        ctx = text[lic_start:min(next_start, lic_end + 400)]

        # Date — look in the text AFTER the license number
        date_match = _LICENSE_DATE_RE.search(ctx)
        lic_date = date_match.group(1) if date_match else ""

        # Legal entity — find the FIRST entity AFTER this license match
        entity_match = _LICENSE_ENTITY_NEAR_RE.search(ctx)
        legal_name = entity_match.group(1) if entity_match else ""

        # INN — find the FIRST INN AFTER this license match
        inn_match = _INN_RE.search(ctx)
        inn = ""
        if inn_match:
            inn_raw = (inn_match.group(1) or inn_match.group(2) or "").strip()
            inn_raw = inn_raw.split("/")[0].strip()
            inn = re.sub(r"\D", "", inn_raw)
            if len(inn) not in (10, 12):
                inn = ""

        # Authority
        auth_match = _LICENSE_AUTHORITY_RE.search(ctx)
        authority = auth_match.group(1).strip() if auth_match else ""

        licenses.append({
            "number": lic_number,
            "date": lic_date,
            "legal_name": legal_name,
            "inn": inn,
            "authority": authority,
            "page_source": page_path,
        })

    if licenses:
        logger.debug(
            "_extract_licenses: %d license(s) from %s: %s",
            len(licenses), page_path,
            [(l["number"], l["legal_name"], l["inn"]) for l in licenses],
        )

    return licenses


async def _fetch_page(client: httpx.AsyncClient, url: str, path: str) -> str | None:
    """Fetch a single page, return text or None on failure."""
    try:
        page_url = urljoin(url, path)
        resp = await client.get(page_url, headers=_HEADERS)
        if resp.status_code < 400:
            return resp.text
    except Exception:
        pass
    return None


def _extract_inn_from_html(html: str, page_path: str = "", min_score: float = -3.0) -> list[str]:
    """Search HTML for INN patterns and return ALL valid candidates.

    Collects ALL INNs found on the page, scores each by context,
    and returns all INNs with score >= min_score, deduplicated,
    sorted by score descending.

    A medical clinic may have multiple legal entities (different INNs)
    listed on the same website — e.g. two licenses under different ООО.

    Scoring:
      - Starts at 5.0 (neutral)
      - +2: Found in <footer> (most reliable location)
      - +1.5: Near clinic markers (ОГРН, КПП, ОКВЭД, клиника, etc.)
      - -3: Near third-party markers (яндекс, сбер, веб-студия)
      - -50: Known third-party INN (Яндекс, Сбер, CloudPayments) — hard reject
      - +2: High-priority page (/about, /contacts, /rekvizity)
      - -2: Low-priority page (/policy, /privacy)
    """
    soup = BeautifulSoup(html, "html.parser")

    # Build search texts with metadata
    search_blocks: list[tuple[str, int, bool]] = []  # (text, priority, is_footer)
    # priority: 0=footer, 1=relevant class, 2=body

    footer = soup.find("footer")
    if footer:
        search_blocks.append((footer.get_text(separator=" ", strip=True), 0, True))

    for el in soup.find_all(["div", "span", "p", "section"], class_=True):
        cls = " ".join(el.get("class", [])).lower()
        if any(kw in cls for kw in ("footer", "inn", "requisites", "rekvizit", "copyright", "legal")):
            search_blocks.append((el.get_text(separator=" ", strip=True), 1, True))

    body = soup.find("body")
    if body:
        search_blocks.append((body.get_text(separator=" ", strip=True), 2, False))

    # Find ALL INN matches across all blocks — collect (inn, score) pairs
    scored: dict[str, float] = {}  # inn → best score seen
    for text, priority, is_footer in search_blocks:
        for m in _INN_RE.finditer(text):
            inn = (m.group(1) or m.group(2) or "").strip()
            inn = inn.split("/")[0].strip()
            inn_digits = re.sub(r"\D", "", inn)
            if len(inn_digits) in (10, 12):
                ctx_start = max(0, m.start() - 150)
                ctx_end = min(len(text), m.end() + 150)
                context = text[ctx_start:ctx_end]
                score = _score_inn_candidate(inn_digits, context, page_path, is_footer, priority)
                # Keep the best score for each INN (same INN may appear in multiple blocks)
                if inn_digits not in scored or score > scored[inn_digits]:
                    scored[inn_digits] = score

    if not scored:
        return []

    # Return all INNs with score >= min_score, sorted by score descending
    valid = [
        inn for inn, score in scored.items()
        if score >= min_score
    ]
    valid.sort(key=lambda inn: scored[inn], reverse=True)

    if not valid:
        logger.debug(
            "_extract_inn_from_html: %d INN(s) found but all below min_score=%.1f (best=%s score=%.1f)",
            len(scored), min_score,
            max(scored, key=scored.get), max(scored.values()),
        )
        return []

    logger.debug(
        "_extract_inn_from_html: %d INN(s) found, %d valid after filtering: %s",
        len(scored), len(valid), [(inn, scored[inn]) for inn in valid],
    )
    return valid


def _extract_primary_inn_from_html(html: str, page_path: str = "") -> str | None:
    """Backward-compatible wrapper: return only the best INN."""
    inns = _extract_inn_from_html(html, page_path)
    return inns[0] if inns else None


def _score_inn_candidate(
    inn: str, context: str, page_path: str = "",
    is_footer: bool = False, priority: int = 2,
) -> float:
    """Score an INN candidate by how likely it belongs to the clinic."""
    score = 5.0
    ctx_lower = context.lower()

    # Hard reject: known third-party INNs
    if inn in _THIRD_PARTY_INNS:
        return -50.0

    # Location bonuses
    if is_footer:
        score += 2.0
    if priority == 0:  # footer
        score += 1.0

    # Clinic markers nearby → strong signal
    clinic_marker_count = sum(1 for m in _CLINIC_INN_MARKERS if m in ctx_lower)
    score += clinic_marker_count * 1.5

    # Third-party markers nearby → penalty
    third_party_count = sum(1 for m in _THIRD_PARTY_MARKERS if m in ctx_lower)
    score -= third_party_count * 3.0

    # Page priority
    _HIGH_PRIORITY_PAGES = ("/about", "/contacts", "/kontakty", "/rekvizity", "/o-kompanii", "/o-klinike", "/o-nas")
    _LOW_PRIORITY_PAGES = ("/policy", "/privacy", "/pravovaya-informatsiya")

    for hp in _HIGH_PRIORITY_PAGES:
        if hp in page_path:
            score += 2.0
            break
    for lp in _LOW_PRIORITY_PAGES:
        if lp in page_path:
            score -= 2.0
            break

    return score


async def extract_inn_from_website(url: str) -> tuple[list[str], list[dict], str | None]:
    """Extract ALL INNs and licenses from a Russian clinic website.

    Fetches homepage + key pages, collects ALL INN candidates and medical
    licenses across all pages. A clinic may have multiple legal entities
    (different INNs) — all are returned.

    Args:
        url: Website URL (with or without scheme)

    Returns:
        (inns, licenses, best_source_url) — all valid INNs, all licenses found,
        and the page URL where the best INN was found.
    """
    if not url:
        return [], [], None

    if not url.startswith("http"):
        url = f"https://{url}"

    # Collect (inn, page_url, score) across all pages
    inn_candidates: list[tuple[str, str, float]] = []
    all_licenses: list[dict] = []

    async with httpx.AsyncClient(
        timeout=_TIMEOUT,
        follow_redirects=True,
        verify=False,
    ) as client:
        # Check homepage first
        html = await _fetch_page(client, url, "/")
        if html:
            inns = _extract_inn_from_html(html, page_path="/")
            for inn in inns:
                inn_candidates.append((inn, url, 10.0))
                logger.debug("extract_inn: found INN=%s on %s (homepage)", inn, url)
            all_licenses.extend(_extract_licenses_from_html(html, page_path="/"))

            # If homepage found good INNs with clinic markers, proceed quickly
            if any(score > 7.0 for _, _, score in inn_candidates):
                # Still scan other pages for licenses and additional INNs
                pass

        # Try additional pages in parallel
        tasks = [_fetch_page(client, url, path) for path in _INN_PAGES[1:]]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        for i, html in enumerate(results):
            if isinstance(html, Exception) or not html:
                continue
            path = _INN_PAGES[i + 1]
            page_url = urljoin(url, path)

            inns = _extract_inn_from_html(html, page_path=path)
            for inn in inns:
                score = _score_inn_for_page(inn, html, path)
                inn_candidates.append((inn, page_url, score))
                logger.debug("extract_inn: candidate INN=%s score=%.1f on %s", inn, score, page_url)

            # Extract licenses from each page
            licenses = _extract_licenses_from_html(html, page_path=path)
            all_licenses.extend(licenses)

    if not inn_candidates:
        logger.debug("extract_inn: no INN found on %s", url)
        return [], [], None

    # Deduplicate INNs — keep best score per INN
    best_scores: dict[str, tuple[str, float]] = {}  # inn → (source_url, score)
    for inn, page_url, score in inn_candidates:
        if inn not in best_scores or score > best_scores[inn][1]:
            best_scores[inn] = (page_url, score)

    # Filter out third-party INNs (score < -3.0)
    valid_inns = {
        inn: (url, score)
        for inn, (url, score) in best_scores.items()
        if score >= -3.0
    }

    if not valid_inns:
        logger.debug("extract_inn: all INN candidates scored < -3 on %s, rejecting", url)
        return [], [], None

    # Sort by score descending
    sorted_inns = sorted(valid_inns.items(), key=lambda x: x[1][1], reverse=True)
    all_inns = [inn for inn, _ in sorted_inns]
    best_url = sorted_inns[0][1][0]

    # Deduplicate licenses by number
    seen_lic: set[str] = set()
    unique_licenses: list[dict] = []
    for lic in all_licenses:
        if lic["number"] not in seen_lic:
            seen_lic.add(lic["number"])
            unique_licenses.append(lic)

    logger.debug(
        "extract_inn: %d INN(s) + %d license(s) from %s → INNs=%s",
        len(all_inns), len(unique_licenses), url, all_inns,
    )
    return all_inns, unique_licenses, best_url


def _score_inn_for_page(inn: str, html: str, page_path: str) -> float:
    """Quick score for an INN candidate based on page context.

    Used by extract_inn_from_website to pick the best INN across multiple pages.
    """
    soup = BeautifulSoup(html, "html.parser")
    text = soup.get_text(separator=" ", strip=True).lower()

    score = 5.0

    # Hard reject: known third-party INNs
    if inn in _THIRD_PARTY_INNS:
        return -50.0

    # Count clinic markers in entire page text
    clinic_hits = sum(1 for m in _CLINIC_INN_MARKERS if m in text)
    score += clinic_hits * 1.5

    # Count third-party markers in entire page text
    third_hits = sum(1 for m in _THIRD_PARTY_MARKERS if m in text)
    score -= third_hits * 3.0

    # Page priority
    _HIGH = ("/about", "/contacts", "/kontakty", "/rekvizity", "/o-kompanii", "/o-klinike", "/o-nas")
    _LOW = ("/policy", "/privacy", "/pravovaya-informatsiya")

    for hp in _HIGH:
        if hp in page_path:
            score += 2.0
            break
    for lp in _LOW:
        if lp in page_path:
            score -= 2.0
            break

    # Bonus if found in footer
    soup = BeautifulSoup(html, "html.parser")
    footer = soup.find("footer")
    if footer and inn in footer.get_text():
        score += 2.0

    return score


async def extract_inn_batch(
    urls: list[str], max_concurrent: int = 10
) -> dict[str, tuple[list[str], list[dict], str | None]]:
    """Extract INNs and licenses from multiple websites concurrently.

    Returns:
        Dict mapping URL → (inns, licenses, best_source_url).
    """
    semaphore = asyncio.Semaphore(max_concurrent)

    async def _extract_one(u: str) -> tuple[str, tuple[list[str], list[dict], str | None]]:
        async with semaphore:
            return u, await extract_inn_from_website(u)

    tasks = [_extract_one(u) for u in urls if u]
    results = await asyncio.gather(*tasks, return_exceptions=True)

    output: dict[str, tuple[list[str], list[dict], str | None]] = {}
    for r in results:
        if isinstance(r, Exception):
            logger.warning("extract_inn_batch: %s", r)
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
