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
    "Севастополь", "Симферополь", "Зеленоград",
]

_CITY_PATTERNS: list[tuple[re.Pattern, str]] = []

# Prepositional case forms for cities with non-trivial declension.
# Key = nominative, Value = list of common forms (prepositional, genitive, etc.)
_CITY_DECLENSIONS: dict[str, list[str]] = {
    "Орёл": ["Орле", "Орла"],
    "Санкт-Петербург": ["Санкт-Петербурге", "Петербурге"],
    "Екатеринбург": ["Екатеринбурге"],
    "Тверь": ["Твери"],
    "Казань": ["Казани"],
    "Астрахань": ["Астрахани"],
    "Рязань": ["Рязани"],
    "Пенза": ["Пензе"],
    "Тула": ["Туле"],
    "Уфа": ["Уфе"],
    "Пермь": ["Перми"],
    "Самара": ["Самаре"],
    "Москва": ["Москве"],
    "Кострома": ["Костроме"],
    "Вологда": ["Вологде"],
    "Калуга": ["Калуге"],
    "Тюмень": ["Тюмени"],
    "Челябинск": ["Челябинске"],
    "Новосибирск": ["Новосибирске"],
    "Красноярск": ["Красноярске"],
    "Хабаровск": ["Хабаровске"],
    "Иркутск": ["Иркутске"],
    "Якутск": ["Якутске"],
    "Мурманск": ["Мурманске"],
    "Архангельск": ["Архангельске"],
    "Смоленск": ["Смоленске"],
    "Брянск": ["Брянске"],
    "Курск": ["Курске"],
    "Псков": ["Пскове"],
    "Томск": ["Томске"],
    "Омск": ["Омске"],
    "Курган": ["Кургане"],
    "Тамбов": ["Тамбове"],
    "Саратов": ["Саратове"],
    "Ростов-на-Дону": ["Ростове-на-Дону"],
    "Нижний Новгород": ["Нижнем Новгороде"],
    "Нижний Тагил": ["Нижнем Тагиле"],
    "Владивосток": ["Владивостоке"],
    "Владикавказ": ["Владикавказе"],
    "Ставрополь": ["Ставрополе"],
    "Севастополь": ["Севастополе"],
    "Симферополь": ["Симферополе"],
    "Калининград": ["Калининграде"],
    "Краснодар": ["Краснодаре"],
    "Волгоград": ["Волгограде"],
    "Белгород": ["Белгороде"],
    "Оренбург": ["Оренбурге"],
    "Сургут": ["Сургуте"],
    "Ярославль": ["Ярославле"],
    "Киров": ["Кирове"],
    "Липецк": ["Липецке"],
    "Ижевск": ["Ижевске"],
    "Барнаул": ["Барнауле"],
    "Ульяновск": ["Ульяновске"],
    "Череповец": ["Череповце"],
    "Кемерово": ["Кемерове"],
    "Новокузнецк": ["Новокузнецке"],
    "Саранск": ["Саранске"],
    "Чебоксары": ["Чебоксарах"],
    "Иваново": ["Иванове"],
    "Сочи": ["Сочи"],
    "Махачкала": ["Махачкале"],
    "Воронеж": ["Воронеже"],
    "Нижневартовск": ["Нижневартовске"],
    "Волжский": ["Волжском"],
    "Зеленоград": ["Зеленограде", "Зеленограда"],
}


def _generate_declined_forms(city: str) -> list[str]:
    """Generate common declined forms for a city using heuristic rules."""
    forms: list[str] = []
    if city in _CITY_DECLENSIONS:
        forms.extend(_CITY_DECLENSIONS[city])

    # Heuristic prepositional case generation
    if city.endswith(("ск", "бург", "град")):
        forms.append(city + "е")
    elif city.endswith("ь"):
        forms.append(city[:-1] + "и")
    elif city.endswith("а"):
        forms.append(city[:-1] + "е")
    elif city.endswith(("ж", "ч", "ш", "щ", "ц", "й", "в", "н", "м", "л", "р", "д", "т", "п", "б", "з", "с", "к", "г", "х")):
        forms.append(city + "е")

    return [f for f in forms if f != city]


def _build_city_patterns():
    """Compile city regex patterns once, including declined forms."""
    if _CITY_PATTERNS:
        return
    for city in sorted(_RUSSIAN_CITIES, key=len, reverse=True):
        _CITY_PATTERNS.append((re.compile(re.escape(city), re.IGNORECASE), city))
        for form in _generate_declined_forms(city):
            _CITY_PATTERNS.append((re.compile(re.escape(form), re.IGNORECASE), city))


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
    city = _extract_city_from_schema(html) or _detect_city(text) or _extract_city_from_url(url)
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
            headers={
                "User-Agent": (
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/125.0.0.0 Safari/537.36"
                ),
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                "Accept-Language": "ru-RU,ru;q=0.9,en;q=0.8",
            },
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


_NEGATION_MARKERS: list[str] = [
    "противопоказани",
    "не используем",
    "не применяем",
    "не проводим",
    "не делаем",
    "отказались от",
    "нельзя",
    "запрещен",
    "не рекомендуется",
    "не показан",
    "не является",
]


def _detect_services(text_lower: str) -> list[str]:
    """Detect medical services from page text, excluding negation contexts."""
    found: list[str] = []
    for service, patterns in _MEDICAL_SERVICES.items():
        service_detected = False
        for pattern in patterns:
            idx = text_lower.find(pattern)
            while idx != -1:
                ctx_start = max(0, idx - 30)
                ctx_end = min(len(text_lower), idx + len(pattern) + 20)
                context = text_lower[ctx_start:ctx_end]

                negated = any(marker in context for marker in _NEGATION_MARKERS)
                if not negated:
                    service_detected = True
                    break

                idx = text_lower.find(pattern, idx + 1)

            if service_detected:
                found.append(service)
                break

    return found


def _detect_specialization(text_lower: str, url: str) -> str:
    """Detect clinic specialization — dominance-based (most keyword matches wins)."""
    match_counts: dict[str, int] = {}
    for spec, patterns in _SPECIALIZATIONS.items():
        count = sum(1 for p in patterns if p in text_lower)
        if count > 0:
            match_counts[spec] = count

    if match_counts:
        return max(match_counts, key=match_counts.get)

    # Fallback: check URL
    url_lower = url.lower()
    if "stomat" in url_lower or "dent" in url_lower:
        return "стоматология"
    if "cosmet" in url_lower or "kosmet" in url_lower:
        return "косметология"
    if "clinic" in url_lower or "med" in url_lower or "клиник" in url_lower:
        return "многопрофильная клиника"

    return ""


def _extract_city_from_schema(html: str) -> str:
    """Extract city from JSON-LD / schema.org markup (addressLocality)."""
    try:
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(html, "html.parser")
        for script in soup.find_all("script", type="application/ld+json"):
            try:
                import json
                data = json.loads(script.string or "")
                if isinstance(data, dict):
                    # @graph pattern: {"@graph": [{...}, {...}]}
                    items = data.get("@graph", [data])
                    if isinstance(items, dict):
                        items = [items]
                    for item in items:
                        addr = _extract_locality_from_ld(item)
                        if addr:
                            return addr
                        # Also check nested @graph
                        for sub in item.get("@graph", []):
                            addr = _extract_locality_from_ld(sub)
                            if addr:
                                return addr
            except (json.JSONDecodeError, TypeError, AttributeError):
                continue
    except Exception:
        pass
    return ""


def _extract_locality_from_ld(data: dict) -> str:
    """Extract addressLocality from a JSON-LD node, resolving parentOrg if needed."""
    addr = data.get("address", {})
    if isinstance(addr, str):
        # Inline address string — try to extract city
        for city in _RUSSIAN_CITIES:
            if city.lower() in addr.lower():
                return city
    if isinstance(addr, dict):
        locality = addr.get("addressLocality", "")
        if isinstance(locality, str) and locality:
            return _match_city_name(locality)
    # Check parentOrganization recursively
    parent = data.get("parentOrganization")
    if isinstance(parent, dict):
        return _extract_locality_from_ld(parent)
    if isinstance(parent, list) and parent:
        return _extract_locality_from_ld(parent[0])
    return ""


def _detect_city(text: str) -> str:
    """Detect city from full page text (no char limit)."""
    # Strategy 1: "в Городе" pattern (common in titles/headers: "стоматология в Орле")
    city_preposition = re.search(
        r"\bв\s+(?:гор\.?\s*)?([А-ЯЁ][а-яё]+(?:[\s-][А-ЯЁ][а-яё]+)?)\b",
        text,
        re.IGNORECASE,
    )
    if city_preposition:
        candidate = city_preposition.group(1)
        for city in _RUSSIAN_CITIES:
            if _city_matches(candidate, city):
                return city

    # Strategy 2: Direct city name match (including declined forms) — full text
    for pattern, city in _CITY_PATTERNS:
        if pattern.search(text):
            return city
    return ""


def _match_city_name(name: str) -> str:
    """Match a schema.org city name against known Russian cities."""
    for city in _RUSSIAN_CITIES:
        if _city_matches(name, city):
            return city
    return ""


def _extract_city_from_url(url: str) -> str:
    """Try to extract city from domain name."""
    parsed = urlparse(url)
    domain = parsed.netloc.lower()

    # Common patterns: msk.clinic.ru, spb.clinic.ru, clinic-msk.ru
    city_prefixes = {
        "msk": "Москва", "spb": "Санкт-Петербург", "nsk": "Новосибирск",
        "ekb": "Екатеринбург", "kzn": "Казань", "kazan": "Казань",
        "nn": "Нижний Новгород", "nn52": "Нижний Новгород",
        "sochi": "Сочи", "krd": "Краснодар", "ufa": "Уфа",
        "samara": "Самара", "nsk": "Новосибирск", "perm": "Пермь",
        "voronezh": "Воронеж", "kemerovo": "Кемерово", "tomsk": "Томск",
        "omsk": "Омск", "irkutsk": "Иркутск", "vladivostok": "Владивосток",
        "kaliningrad": "Калининград", "murmansk": "Мурманск",
        "tyumen": "Тюмень", "yaroslavl": "Ярославль",
        "chelyabinsk": "Челябинск", "novosibirsk": "Новосибирск",
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

        # Fallback to title — truncate at separators
        title = soup.find("title")
        if title:
            t = title.get_text(strip=True)
            for sep in [" — ", " – ", " | ", ": ", " - "]:
                if sep in t:
                    t = t.split(sep)[0]
            # If title looks like an SEO phrase (long, contains "в городе"),
            # it's likely not the company name
            if len(t) > 40 or re.search(r"\bв\s+г(?:ор\.?\s*)?[А-ЯЁ]", t, re.IGNORECASE):
                return None
            return t.strip()
    except Exception:
        pass
    return None


def _norm(s: str) -> str:
    """Normalise Cyrillic string: ё→е, lowercase."""
    return s.replace("ё", "е").replace("Ё", "Е").lower()


def _city_matches(candidate: str, city: str) -> bool:
    """Check if a (possibly declined) candidate matches a nominative city name.

    Handles Russian prepositional case:  "Орле" → "Орёл"
    """
    c = _norm(candidate)
    n = _norm(city)
    if c == n:
        return True
    # Subset: "Петербург" in "Санкт-Петербург"
    if len(c) >= 4 and (c in n or n in c):
        return True
    # Strip common Russian case endings and compare stems
    for ending in ("е", "и", "у", "ю", "ой", "ей", "ом", "ем", "а", "я", "ы"):
        if c.endswith(ending) and len(c) > len(ending) + 1:
            stem = c[:-len(ending)]
            if n.startswith(stem) or stem.startswith(n) or stem in n:
                return True
        if n.endswith(ending) and len(n) > len(ending) + 1:
            stem = n[:-len(ending)]
            if c.startswith(stem) or stem.startswith(c) or stem in c:
                return True
    # ё↔е alternation: "орле" vs "орел" — same chars, different order
    if len(c) <= 6 and set(c) == set(n):
        return True
    return False
