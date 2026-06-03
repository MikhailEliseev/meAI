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
# Patterns include common declensions (genitive, accusative) because
# Russian clinic websites almost never use the nominative form.
# E.g. "клиника пластической хирургии" (genitive) vs "пластическая хирургия" (nominative).
_SPECIALIZATIONS: dict[str, list[str]] = {
    "стоматология": [
        "стоматолог", "стоматологи", "стоматологии", "стоматологию",
        "зубной", "зубов", "дантист", "dental",
    ],
    "косметология": [
        "косметолог", "косметологи", "косметологии", "косметологию",
        "косметология", "эстетическ",
    ],
    "многопрофильная клиника": [
        "многопрофильн", "медицинский центр", "клиника",
        "многопрофильной", "многопрофильную",
        # Genitive/plural forms — catch "сеть клиник", "клиник и центров"
        "клиник", "медицинских центр",
        # "Сеть" + medical context = large multidisciplinary network
        "сеть клиник", "сеть медицинских",
    ],
    "пластическая хирургия": [
        "пластическая хирургия", "пластической хирургии", "пластическую хирургию",
        "пластический хирург", "пластического хирурга",
    ],
    "диагностический центр": [
        "диагностический центр", "диагностического центра",
        "мрт", "кт", "томограф",
    ],
    "офтальмология": [
        "офтальмолог", "офтальмологи", "офтальмологии",
        "глазн", "коррекция зрения", "офтальмологическ",
    ],
    "педиатрия": [
        "педиатр", "педиатры", "педиатрии", "педиатрию",
        "детск",
    ],
    "психология": [
        "психолог", "психологи", "психологии", "психологию",
        "психотерап", "психотерапии", "психотерапию",
        "семейная психология", "семейной психологии",
        "перинатальн",
    ],
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

# Moscow administrative districts that should normalize to Москва
_CITY_CANONICAL: dict[str, str] = {
    "Зеленоград": "Москва",
}

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
        city (str), company_name (str|None), site_structure (dict|None)
    """
    html = await _fetch_page(url)
    if not html:
        return {
            "services": [],
            "specialization": "",
            "city": _extract_city_from_url(url),
            "company_name": None,
            "site_structure": None,
        }

    text = _extract_text(html)
    text_lower = text.lower()

    services = _detect_services(text_lower)
    site_structure = _analyze_site_structure(html)
    specialization = _detect_specialization(text_lower, url, html, site_structure)
    city = _extract_city_from_schema(html) or _detect_city(text) or _extract_city_from_url(url)
    city = _CITY_CANONICAL.get(city, city)  # normalize districts → city
    company_name = _extract_company_name(html)
    inn = _extract_inn(html)

    logger.info(
        "Service extraction: url=%s services=%s specialization=%s city=%s structure_departments=%s",
        url, services, specialization, city,
        len(site_structure.get("departments", [])) if site_structure else 0,
    )

    return {
        "services": services,
        "specialization": specialization,
        "city": city,
        "company_name": company_name,
        "inn": inn,
        "site_structure": site_structure,
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


# Weights for different signal zones
_TITLE_WEIGHT = 5
_DOMAIN_WEIGHT = 3
_BODY_WEIGHT = 1

# Specializations where the primary niche is often drowned out by
# secondary service mentions. If the dominant_spec appears in title/H1,
# it overrides the noisy_spec even when noisy_spec has a higher body count.
_PRIORITY_OVERRIDES: dict[str, str] = {
    # пластическая хирургия > косметология (хирургические клиники всегда
    # предлагают косметологию, но позиционируются как хирургия)
    "пластическая хирургия": "косметология",
    # стоматология > многопрофильная клиника (клиники с dental в названии
    # часто имеют много общемедицинских услуг в теле страницы)
    "стоматология": "многопрофильная клиника",
    # психология > многопрофильная клиника (психологические центры часто
    # используют слово "клиника", но это психология)
    "психология": "многопрофильная клиника",
}


def _extract_domain_keywords(url: str) -> list[str]:
    """Extract potential niche-bearing tokens from domain name."""
    parsed = urlparse(url)
    domain = parsed.netloc.lower()
    domain = re.sub(r"\.(ru|com|org|net|рф|su|io|co|msk|spb|xn--[a-z0-9]+)$", "", domain)
    domain = re.sub(r"^(www|m|online|portal)\\.", "", domain)
    return [p for p in re.split(r"[-_.]", domain) if len(p) >= 3]


def _extract_title_h1_meta(html: str) -> str:
    """Extract concatenated lowercased text from title, H1, and meta description."""
    try:
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(html, "html.parser")
        parts: list[str] = []

        title_tag = soup.find("title")
        if title_tag:
            parts.append(title_tag.get_text())

        h1_tag = soup.find("h1")
        if h1_tag:
            parts.append(h1_tag.get_text())

        meta = soup.find("meta", attrs={"name": "description"})
        if meta and meta.get("content"):
            parts.append(meta["content"])

        return " ".join(parts).lower()
    except Exception:
        return ""


def _analyze_site_structure(html: str) -> dict:
    """Parse navigation structure from HTML to detect site specialisation profile.

    Extracts menu/nav links, groups them by matched specialisation category,
    and determines whether the site structure reflects a specialised clinic
    or a truly multidisciplinary one.

    Returns:
        dict with:
        - departments: list of {"label": str, "href": str, "specializations": [str]}
        - nav_specializations: dict[spec_name → count] (how many nav items per spec)
        - total_nav_items: int
        - is_multidisciplinary: bool (true if 3+ specialisations each have ≥15% of nav)
    """
    try:
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(html, "html.parser")
    except Exception:
        return _empty_structure()

    nav_items: list[dict] = []

    # Collect navigation links from: <nav>, header, elements with menu/nav classes
    selectors = [
        soup.find_all("nav"),
        soup.find_all("header"),
        soup.find_all(class_=lambda c: c and any(
            kw in c.lower() for kw in ["menu", "nav", "navigation", "sidebar"]
        ) if c else False),
        soup.find_all(id=lambda i: i and any(
            kw in i.lower() for kw in ["menu", "nav", "navigation", "sidebar"]
        ) if i else False),
    ]

    seen_hrefs: set[str] = set()
    for group in selectors:
        for container in group:
            for link in container.find_all("a", href=True):
                href = link.get("href", "").strip()
                label = link.get_text(strip=True)
                if not label or len(label) < 2:
                    continue
                # Skip non-navigation links (phone, email, social, etc.)
                if any(kw in href.lower() for kw in ["tel:", "mailto:", "javascript:", "#"]):
                    if not href.startswith("#") or len(href) <= 2:
                        continue
                # Deduplicate by href+label
                key = f"{href}|{label}"
                if key in seen_hrefs:
                    continue
                seen_hrefs.add(key)
                nav_items.append({"label": label, "href": href})

    if not nav_items:
        # Fallback: grab all links from body (less reliable but better than nothing)
        body = soup.find("body")
        if body:
            for link in body.find_all("a", href=True)[:80]:
                label = link.get_text(strip=True)
                href = link.get("href", "").strip()
                if label and len(label) >= 2:
                    key = f"{href}|{label}"
                    if key not in seen_hrefs:
                        seen_hrefs.add(key)
                        nav_items.append({"label": label, "href": href})

    # Match each nav item against specialisation patterns
    label_lower_all = " | ".join(item["label"].lower() for item in nav_items)
    spec_counts: dict[str, int] = {spec: 0 for spec in _SPECIALIZATIONS}
    departments: list[dict] = []

    for item in nav_items:
        label_lower = item["label"].lower()
        matched_specs: list[str] = []
        for spec, patterns in _SPECIALIZATIONS.items():
            for p in patterns:
                if p in label_lower:
                    matched_specs.append(spec)
                    break
        item_specs = list(set(matched_specs))
        for s in item_specs:
            spec_counts[s] = spec_counts.get(s, 0) + 1
        departments.append({
            "label": item["label"],
            "href": item["href"],
            "specializations": item_specs,
        })

    total = len(nav_items)
    # A site is multidisciplinary if 3+ specializations each have ≥15% of nav items
    threshold = max(1, total * 0.15)
    significant_specs = [
        spec for spec, count in spec_counts.items()
        if count >= threshold and spec != "многопрофильная клиника"
    ]
    is_multidisciplinary = len(significant_specs) >= 3

    return {
        "departments": departments,
        "nav_specializations": {k: v for k, v in spec_counts.items() if v > 0},
        "total_nav_items": total,
        "is_multidisciplinary": is_multidisciplinary,
    }


def _empty_structure() -> dict:
    return {
        "departments": [],
        "nav_specializations": {},
        "total_nav_items": 0,
        "is_multidisciplinary": False,
    }


def _detect_specialization(
    text_lower: str, url: str, html: str = "",
    site_structure: dict | None = None,
) -> str:
    """Detect clinic specialization with position-weighted scoring + site structure.

    Title/H1/meta keywords carry 5× weight over body text. This prevents
    secondary niches (e.g. косметология mentioned in 20 service listings)
    from outscoring the primary specialization (e.g. пластическая хирургия
    in the page title).

    Site structure analysis provides an additional signal: if the navigation
    menu is overwhelmingly focused on one specialization (≥60% of nav items),
    the site is specialised regardless of body-text scores.
    """
    high_signal = _extract_title_h1_meta(html) if html else ""
    domain_keywords = _extract_domain_keywords(url)

    scores: dict[str, float] = {}
    for spec, patterns in _SPECIALIZATIONS.items():
        score = 0.0
        score += sum(_TITLE_WEIGHT for p in patterns if p in high_signal)
        score += sum(_BODY_WEIGHT for p in patterns if p in text_lower)
        for dk in domain_keywords:
            if any(dk in p or p in dk for p in patterns):
                score += _DOMAIN_WEIGHT
        if score > 0:
            scores[spec] = score

    if not scores:
        return _detect_specialization_from_url(url)

    # ── Site structure signal ──────────────────────────────────────
    # If 60%+ of navigation items fall under one specialisation,
    # the site is functionally specialised — override multiprofile.
    if site_structure and site_structure.get("nav_specializations"):
        nav_specs = site_structure["nav_specializations"]
        total_nav = site_structure.get("total_nav_items", 1)
        for spec, nav_count in nav_specs.items():
            if spec == "многопрофильная клиника":
                continue
            if nav_count >= total_nav * 0.6:
                # Strong nav signal: boost this spec's score
                scores[spec] = scores.get(spec, 0) + _TITLE_WEIGHT * 2
                logger.info(
                    "Site structure boost: %s (nav items=%d/%d, %.0f%%)",
                    spec, nav_count, total_nav, nav_count / total_nav * 100,
                )

    best = max(scores, key=scores.get)

    # Priority overrides: if dominant_spec appears in title/H1 and noisy_spec
    # is leading only because of body-text volume, promote dominant_spec.
    # BUT: only override when dominant appears FIRST in the title OR it has
    # strong body presence (≥60% of noisy score). Prevents false overrides
    # where a secondary specialisation is merely listed among many in a title.
    for dominant, noisy in _PRIORITY_OVERRIDES.items():
        if best == noisy and dominant in scores:
            dominant_patterns = _SPECIALIZATIONS.get(dominant, [])
            if any(p in high_signal for p in dominant_patterns):
                # Check which specialisation appears first in the title/H1
                noisy_patterns = _SPECIALIZATIONS.get(noisy, [])
                dominant_first_pos = min(
                    (high_signal.find(p) for p in dominant_patterns if p in high_signal),
                    default=9999,
                )
                noisy_first_pos = min(
                    (high_signal.find(p) for p in noisy_patterns if p in high_signal),
                    default=9999,
                )
                # If noisy appears first in title, dominant is secondary —
                # require stronger evidence (≥60% of noisy score)
                if noisy_first_pos < dominant_first_pos:
                    threshold = 0.6
                else:
                    # Dominant appears first — this is likely the primary niche
                    threshold = 0.3
                if scores[dominant] >= scores[noisy] * threshold:
                    logger.info(
                        "Priority override: %s → %s (scores: %.1f vs %.1f, threshold=%.1f, "
                        "dominant_pos=%d, noisy_pos=%d)",
                        noisy, dominant, scores[dominant], scores[noisy],
                        threshold, dominant_first_pos, noisy_first_pos,
                    )
                    return dominant

    # "Многопрофильная клиника" — особый случай. Паттерн "клиника"
    # матчится на ЛЮБОМ сайте, создавая ложное преимущество.
    # Реальный сигнал — только "многопрофильн".
    # Если "многопрофильн" НЕ в title/H1 → ищем специализацию-лидера.
    if best == "многопрофильная клиника":
        mnogo_in_title = "многопрофильн" in high_signal
        mnogo_in_structure = (
            site_structure
            and site_structure.get("is_multidisciplinary")
        ) if site_structure else False

        # If the navigation structure confirms it's truly multidisciplinary,
        # and the title says so too — keep "многопрофильная клиника"
        if mnogo_in_title and mnogo_in_structure:
            return best

        # If neither title nor structure confirms multiprofile → find leader
        if not mnogo_in_title:
            candidates = [
                (spec, sc) for spec, sc in scores.items()
                if spec != "многопрофильная клиника"
                and sc >= scores["многопрофильная клиника"] * 0.4
                and any(p in high_signal for p in _SPECIALIZATIONS.get(spec, []))
            ]
            if candidates:
                return max(candidates, key=lambda x: x[1])[0]

    return best


def _detect_specialization_from_url(url: str) -> str:
    """Fallback niche detection from URL when page text yields nothing."""
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


def _extract_inn(html: str) -> Optional[str]:
    """Extract INN (10 or 12 digits) from website HTML.

    Looks in: footer sections, schema.org markup, text near "ИНН" label.
    Returns the first valid INN found, or None.
    """
    try:
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(html, "html.parser")

        # 1. Look for text "ИНН" followed by digits (footer, requisites)
        text = soup.get_text()
        inn_match = re.search(r"ИНН\s*[:/\s]*\s*(\d{10}|\d{12})", text)
        if inn_match:
            return inn_match.group(1)

        # 2. Look in schema.org Organization markup
        for script in soup.find_all("script", type="application/ld+json"):
            try:
                import json
                data = json.loads(script.string or "")
                if isinstance(data, dict):
                    tax_id = data.get("taxID") or ""
                    if re.match(r"^\d{10}$|^\d{12}$", tax_id):
                        return tax_id
            except (json.JSONDecodeError, TypeError):
                pass

        # 3. Look for elements with class/id containing "inn" or "реквизит"
        for el in soup.find_all(
            class_=lambda c: c and any(
                kw in c.lower() for kw in ["inn", "реквизит", "requisite", "footer"]
            ) if c else False
        ):
            el_text = el.get_text()
            m = re.search(r"(\d{10}|\d{12})", el_text)
            if m:
                digits = m.group(1)
                # Validate: skip phone numbers (start with 7 or 8)
                if digits[0] not in ("7", "8"):
                    return digits

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
