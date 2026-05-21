"""Extract medical services, specialization, and city from a clinic website.

Lightweight — fetches homepage via httpx, parses with BeautifulSoup,
matches against curated keyword lists. No JS rendering.
"""

import logging
import re
from typing import Optional
from urllib.parse import urlparse

import httpx

logger = logging.getLogger(__name__)

REQUEST_TIMEOUT = 15.0

# ── Medical service keywords ───────────────────────────────────────
# Each key is a canonical service name, values are patterns to match.
_MEDICAL_SERVICES: dict[str, list[str]] = {
    "терапия": ["терапия", "терапевт", "лечение зубов", "лечение кариеса"],
    "ортопедия": ["ортопедия", "ортопед", "протезирование", "коронки", "мосты", "виниры", "вкладки"],
    "ортодонтия": ["ортодонтия", "ортодонт", "брекеты", "элайнеры", "исправление прикуса"],
    "имплантация": ["имплантаци", "импланты", "имплант"],
    "хирургия": ["хирурги", "удаление зуб", "удаление зуба", "удаление зубов"],
    "стоматология": ["стоматолог"],
    "гигиена": ["гигиена", "чистка зуб", "отбеливание", "профгигиена"],
    "косметология": ["косметолог", "косметология", "чистка лица", "пилинг", "биоревитализация",
                      "мезотерапия", "ботокс", "филлеры", "контурная пластика"],
    "дерматология": ["дерматолог", "дерматология", "лечение кожи"],
    "гинекология": ["гинеколог", "гинекология"],
    "урология": ["уролог", "урология"],
    "офтальмология": ["офтальмолог", "офтальмология", "зрение", "коррекция зрения"],
    "отоларингология": ["отоларинголог", "лор", "лора", "лор-"],
    "неврология": ["невролог", "неврология"],
    "кардиология": ["кардиолог", "кардиология", "экг", "сердце"],
    "эндокринология": ["эндокринолог", "эндокринология"],
    "гастроэнтерология": ["гастроэнтеролог", "гастроэнтерология"],
    "диагностика": ["диагностик", "узи", "рентген", "кт", "мрт", "томограф", "анализы"],
    "физиотерапия": ["физиотерап", "физиотерапия", "массаж"],
    "пластическая хирургия": ["пластическ", "пластика", "липосакция", "ринопластика",
                               "блефаропластика", "маммопластика"],
    "педиатрия": ["педиатр", "педиатрия", "детск"],
    "психотерапия": ["психотерап", "психолог", "психиатр"],
    "наркология": ["нарколог", "наркология"],
    "проктология": ["проктолог", "проктология"],
    "флебология": ["флеболог", "флебология"],
    "аллергология": ["аллерголог", "аллергология"],
    "реабилитация": ["реабилитац", "восстановление"],
    "лазерная эпиляция": ["лазерн", "эпиляци", "эпиляция"],
    "мануальная терапия": ["мануальн", "остеопат", "остеопатия"],
}


# ── Specialization detection ────────────────────────────────────────
_SPECIALIZATIONS: dict[str, list[str]] = {
    "стоматология": ["стоматолог", "зубной", "зубов", "дантист", "dental"],
    "косметология": ["косметолог", "косметология", "эстетическ"],
    "многопрофильная клиника": ["многопрофильн", "медицинский центр", "клиника"],
    "пластическая хирургия": ["пластическая хирургия", "пластический хирург"],
    "диагностический центр": ["диагностический центр", "мрт", "кт", "томограф"],
    "офтальмология": ["офтальмолог", "глазн", "коррекция зрения", "офтальмологическ"],
    "педиатрия": ["педиатр", "детск"],
}


# ── City detection ──────────────────────────────────────────────────
_RUSSIAN_CITIES: list[str] = [
    "Москва", "Санкт-Петербург", "Новосибирск", "Екатеринбург", "Казань",
    "Нижний Новгород", "Челябинск", "Самара", "Омск", "Ростов-на-Дону",
    "Уфа", "Красноярск", "Воронеж", "Пермь", "Волгоград", "Краснодар",
    "Саратов", "Тюмень", "Тольятти", "Ижевск", "Барнаул", "Ульяновск",
    "Иркутск", "Хабаровск", "Ярославль", "Владивосток", "Махачкала",
    "Томск", "Оренбург", "Кемерово", "Новокузнецк", "Рязань", "Астрахань",
    "Пенза", "Липецк", "Тула", "Киров", "Чебоксары", "Калининград",
    "Брянск", "Курск", "Иваново", "Тверь", "Ставрополь", "Белгород",
    "Сочи", "Смоленск", "Калуга", "Владикавказ", "Волжский", "Череповец",
    "Саранск", "Вологда", "Якутск", "Курган", "Орёл", "Тамбов", "Псков",
    "Сургут", "Нижневартовск", "Нижний Тагил", "Архангельск", "Мурманск",
    "Севастополь", "Симферополь",
]

_CITY_PATTERNS: list[tuple[re.Pattern, str]] = []


def _build_city_patterns():
    """Compile city regex patterns once."""
    if _CITY_PATTERNS:
        return
    for city in sorted(_RUSSIAN_CITIES, key=len, reverse=True):
        _CITY_PATTERNS.append((re.compile(re.escape(city), re.IGNORECASE), city))


_build_city_patterns()


# ── Public API ──────────────────────────────────────────────────────

async def extract_client_profile(url: str) -> dict:
    """Extract services, specialization, and city from a clinic website.

    Args:
        url: Clinic website URL

    Returns:
        dict with keys: services (list[str]), specialization (str),
        city (str), company_name (str|None)
    """
    html = await _fetch_page(url)
    if not html:
        return {
            "services": [],
            "specialization": "",
            "city": _extract_city_from_url(url),
            "company_name": None,
        }

    text = _extract_text(html)
    text_lower = text.lower()

    services = _detect_services(text_lower)
    specialization = _detect_specialization(text_lower, url)
    city = _detect_city(text) or _extract_city_from_url(url)
    company_name = _extract_company_name(html)

    logger.info(
        "Service extraction: url=%s services=%s specialization=%s city=%s",
        url, services, specialization, city,
    )

    return {
        "services": services,
        "specialization": specialization,
        "city": city,
        "company_name": company_name,
    }


# ── Internal helpers ────────────────────────────────────────────────

async def _fetch_page(url: str) -> Optional[str]:
    """Fetch page HTML via httpx."""
    try:
        async with httpx.AsyncClient(
            timeout=REQUEST_TIMEOUT,
            follow_redirects=True,
            headers={"User-Agent": "meAI-Hermes/1.0 (Pre-Sale Bot)"},
        ) as client:
            response = await client.get(url)
            response.raise_for_status()
            return response.text
    except httpx.HTTPError as e:
        logger.warning("Failed to fetch %s: %s", url, e)
        return None


def _extract_text(html: str) -> str:
    """Extract visible text from HTML, removing scripts and styles."""
    try:
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(html, "html.parser")
        for tag in soup(["script", "style", "nav", "footer", "header", "noscript"]):
            tag.decompose()
        return soup.get_text(separator=" ", strip=True)
    except Exception:
        # Fallback: strip HTML tags manually
        clean = re.sub(r"<[^>]+>", " ", html)
        return re.sub(r"\s+", " ", clean)


def _detect_services(text_lower: str) -> list[str]:
    """Detect medical services from page text."""
    found: list[str] = []
    for service, patterns in _MEDICAL_SERVICES.items():
        for pattern in patterns:
            if pattern in text_lower:
                found.append(service)
                break
    return found


def _detect_specialization(text_lower: str, url: str) -> str:
    """Detect clinic specialization from content and URL."""
    # Check content first
    for spec, patterns in _SPECIALIZATIONS.items():
        for pattern in patterns:
            if pattern in text_lower:
                return spec

    # Fallback: check URL
    url_lower = url.lower()
    if "stomat" in url_lower or "dent" in url_lower:
        return "стоматология"
    if "cosmet" in url_lower or "kosmet" in url_lower:
        return "косметология"
    if "clinic" in url_lower or "med" in url_lower or "клиник" in url_lower:
        return "многопрофильная клиника"

    return ""


def _detect_city(text: str) -> str:
    """Detect city from page text."""
    # Heuristic: first city match in the first 5000 chars (header/contact area)
    text_head = text[:5000]
    for pattern, city in _CITY_PATTERNS:
        if pattern.search(text_head):
            return city
    return ""


def _extract_city_from_url(url: str) -> str:
    """Try to extract city from domain name."""
    parsed = urlparse(url)
    domain = parsed.netloc.lower()

    # Common patterns: msk.clinic.ru, spb.clinic.ru, clinic-msk.ru
    city_prefixes = {
        "msk": "Москва", "spb": "Санкт-Петербург", "nsk": "Новосибирск",
        "ekb": "Екатеринбург", "kzn": "Казань", "nn": "Нижний Новгород",
        "sochi": "Сочи", "krd": "Краснодар", "ufa": "Уфа",
    }

    for prefix, city in city_prefixes.items():
        if prefix in domain:
            return city

    return ""


def _extract_company_name(html: str) -> Optional[str]:
    """Extract company name from HTML title tag or og:site_name."""
    try:
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(html, "html.parser")

        # Try og:site_name first
        og = soup.find("meta", property="og:site_name")
        if og and og.get("content"):
            return og["content"].strip()

        # Fallback to title
        title = soup.find("title")
        if title:
            t = title.get_text(strip=True)
            # Truncate at common separators
            for sep in [" — ", " – ", " | ", ": "]:
                if sep in t:
                    t = t.split(sep)[0]
            return t.strip()
    except Exception:
        pass
    return None
