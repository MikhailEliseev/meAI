"""DoctorExtractor — find and score doctor-leaders from clinic websites.

Extracts doctor names/specialties from HTML, then computes influence scores
based on social following, publications, ProDoctorov ratings, review mentions,
and content activity.
"""

import json
import logging
import math
import re
from typing import Optional

from bs4 import BeautifulSoup

from .models import ArticleSearchResult, DoctorInfo, DoctorSocialResult

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Name extraction
# ---------------------------------------------------------------------------

# Russian name pattern: «Фамилия Имя Отчество» (capitalized, 2-3 words)
_FIO_PATTERN = re.compile(
    r"\b([А-ЯЁ][а-яё]+)\s+([А-ЯЁ][а-яё]+)(?:\s+([А-ЯЁ][а-яё]+))?\b"
)

# Specialty keywords that often appear near doctor names
_SPECIALTY_KEYWORDS = [
    "врач", "доктор", "хирург", "терапевт", "дерматолог", "косметолог",
    "гинеколог", "уролог", "стоматолог", "ортопед", "невролог",
    "кардиолог", "офтальмолог", "лор", "эндокринолог", "гастроэнтеролог",
    "онколог", "психиатр", "психолог", "реабилитолог", "физиотерапевт",
    "массажист", "нутрициолог", "диетолог", "аллерголог", "иммунолог",
    "флеболог", "проктолог", "маммолог", "рентгенолог", "узи",
    "трихолог", "подолог", "пластический хирург", "челюстно-лицевой хирург",
    "акушер", "генетик", "гомеопат", "остеопат", "рефлексотерапевт",
    "doctor", "surgeon", "dermatologist", "cosmetologist", "dentist",
]

# CSS class patterns that indicate doctor/staff cards
_DOCTOR_CARD_CLASSES = [
    "doctor-card", "staff-card", "team-member", "employee-card",
    "врач-карточка", "specialist-card", "person-card", "member-card",
    "doctor-item", "staff-item", "team-item", "employee-item",
    "врач-item", "specialist-item",
]

# CSS class patterns for staff grids/containers
_STAFF_CONTAINER_CLASSES = [
    "staff", "doctors", "team", "employees", "specialists", "persons",
    "врачи", "сотрудники", "команда", "специалисты", "персонал",
    "doctor-list", "staff-list", "team-grid", "employees-grid",
    "doctors-grid", "staff-grid", "team-list",
]


def extract_doctors(soup: BeautifulSoup, base_url: str = "") -> list[dict]:
    """Extract doctor names and metadata from a clinic website page.

    Tries multiple strategies in priority order:
    1. Schema.org JSON-LD microdata (@type: Person / Physician)
    2. CSS class patterns (doctor-card, staff-card, врачи, etc.)
    3. Staff container grids (staff, doctors, team)
    4. Fallback: FIO pattern near specialty keywords

    Returns list of dicts with keys: name, specialty, photo_url, bio_url.
    Capped at 10 doctors.
    """
    doctors: list[dict] = []

    # Strategy 1: JSON-LD structured data
    for script in soup.find_all("script", type="application/ld+json"):
        try:
            data = json.loads(script.string or "")
        except (json.JSONDecodeError, TypeError):
            continue
        items = data if isinstance(data, list) else [data]
        for item in items:
            if isinstance(item, dict) and item.get("@type") in ("Person", "Physician"):
                name = item.get("name", "").strip()
                if name and _looks_like_person_name(name):
                    specialty = item.get("jobTitle", item.get("description", ""))
                    photo = item.get("image", "")
                    if isinstance(photo, dict):
                        photo = photo.get("url", "")
                    url = item.get("url", "")
                    doctors.append({
                        "name": name,
                        "specialty": _clean_specialty(specialty),
                        "photo_url": _abs_url(photo, base_url),
                        "bio_url": _abs_url(url, base_url),
                    })
                    if len(doctors) >= 10:
                        return doctors

    # Strategy 2: Doctor card CSS classes
    for cls in _DOCTOR_CARD_CLASSES:
        for card in soup.find_all(class_=lambda c, cls=cls: c and cls in c.lower() if isinstance(c, str) else False):
            d = _parse_doctor_card(card, base_url)
            if d and d["name"]:
                doctors.append(d)
                if len(doctors) >= 10:
                    return doctors

    if doctors:
        return _deduplicate_doctors(doctors)

    # Strategy 3: Staff container grids
    for cls in _STAFF_CONTAINER_CLASSES:
        for container in soup.find_all(class_=lambda c, cls=cls: c and cls in c.lower() if isinstance(c, str) else False):
            # Direct children that look like cards
            for child in container.find_all(["li", "article", "div"], recursive=False):
                d = _parse_doctor_card(child, base_url)
                if d and d["name"]:
                    doctors.append(d)
                    if len(doctors) >= 10:
                        return doctors
            # Try deeper search
            if not doctors:
                for child in container.find_all(["li", "article", "div"]):
                    d = _parse_doctor_card(child, base_url)
                    if d and d["name"]:
                        doctors.append(d)
                        if len(doctors) >= 10:
                            return doctors

    if doctors:
        return _deduplicate_doctors(doctors)

    # Strategy 4: Fallback — FIO patterns near specialty keywords
    body_text = soup.get_text()
    for match in _FIO_PATTERN.finditer(body_text):
        name = match.group(0).strip()
        if len(name.split()) < 2:
            continue
        if not _looks_like_person_name(name):
            continue
        # Check if near a specialty keyword (within 100 chars)
        start = max(0, match.start() - 100)
        end = min(len(body_text), match.end() + 100)
        context = body_text[start:end].lower()
        specialty = ""
        for kw in _SPECIALTY_KEYWORDS:
            if kw in context:
                specialty = kw
                break
        doctors.append({"name": name, "specialty": specialty, "photo_url": "", "bio_url": ""})
        if len(doctors) >= 10:
            break

    return _deduplicate_doctors(doctors)


def _parse_doctor_card(card, base_url: str = "") -> Optional[dict]:
    """Extract doctor info from a DOM element that looks like a person card.

    Looks for: name in heading/strong, photo in img, specialty in description.
    """
    # Find name: heading, strong, or link text
    name_el = (
        card.find(["h2", "h3", "h4", "h5", "strong"])
        or card.find("a", class_=lambda c: c and "name" in c.lower() if c else False)
        or card.find("span", class_=lambda c: c and "name" in c.lower() if c else False)
    )
    name = name_el.get_text(strip=True) if name_el else ""

    # Clean up button labels that pollute doctor names
    _BTN_JUNK = re.compile(
        r"\b(Записаться|Запись\s+на\s+при[её]м|Подробнее|Узнать\s+цену|Прайс-лист)\b",
        re.IGNORECASE,
    )
    name = _BTN_JUNK.sub("", name).strip()

    # Fallback: first link or prominent text
    if not _looks_like_person_name(name):
        name_el = card.find("a", href=True)
        if name_el:
            name = name_el.get_text(strip=True)
            name = _BTN_JUNK.sub("", name).strip()
    if not _looks_like_person_name(name):
        return None

    # Find photo
    photo = ""
    img = card.find("img")
    if img:
        photo = img.get("src", "") or img.get("data-src", "")
        photo = _abs_url(photo, base_url)

    # Find specialty
    specialty = ""
    desc_el = (
        card.find(class_=lambda c: c and any(
            kw in c.lower() for kw in ("specialty", "position", "role", "title", "desc", "info")
        ) if c else False)
    )
    if desc_el:
        specialty = desc_el.get_text(strip=True)
    if not specialty:
        # Check text near the name for specialty keywords
        card_text = card.get_text().lower()
        for kw in _SPECIALTY_KEYWORDS:
            if kw in card_text:
                specialty = kw
                break

    # Find bio link
    bio_url = ""
    bio_link = card.find("a", href=True)
    if bio_link:
        href = bio_link.get("href", "")
        if href and not href.startswith("#") and not href.startswith("tel:"):
            bio_url = _abs_url(href, base_url)

    return {
        "name": name,
        "specialty": _clean_specialty(specialty),
        "photo_url": photo,
        "bio_url": bio_url,
    }


# ---------------------------------------------------------------------------
# Influence scoring
# ---------------------------------------------------------------------------

def compute_influence_score(doctor: DoctorInfo) -> float:
    """Compute influence score 0-100 for a doctor.

    Weights and formulas:
    - Social following: 30% — log-scale, max at 1M followers
    - Publications: 25% — count (12.5) + citations log-scale (12.5)
    - ProDoctorov: 20% — rating (10) + reviews (10)
    - Review mentions: 15% — linear, max at 5 mentions
    - Content activity: 10% — linear, max at 20 posts/month
    """
    score = 0.0

    # --- Social following (30%) ---
    total_followers = 0
    posts_month = 0
    if doctor.social:
        for p in doctor.social.profiles:
            total_followers += p.subscribers
            posts_month += p.posts_last_month
    social_score = min(30.0, math.log10(total_followers + 1) / math.log10(1_000_000) * 30.0)
    score += social_score

    # --- Publications (25%) ---
    pub_count = 0
    total_cites = 0
    if doctor.articles:
        pub_count = len(doctor.articles.articles)
        total_cites = sum(a.citations for a in doctor.articles.articles)
    pub_score = min(12.5, pub_count * 2.5) + min(12.5, math.log10(total_cites + 1) / math.log10(500) * 12.5)
    score += pub_score

    # --- ProDoctorov (20%) ---
    pd_rating_score = min(10.0, doctor.prodoctorov_rating * 2.0)
    pd_reviews_score = min(10.0, doctor.prodoctorov_reviews / 100.0 * 10.0)
    score += pd_rating_score + pd_reviews_score

    # --- Review mentions (15%) ---
    mentions_score = min(15.0, doctor.review_mentions * 3.0)
    score += mentions_score

    # --- Content activity (10%) ---
    activity_score = min(10.0, posts_month * 0.5)
    score += activity_score

    return round(min(100.0, score), 1)


def identify_leaders(doctors: list[DoctorInfo], count: int = 3) -> list[DoctorInfo]:
    """Sort doctors by influence_score desc, mark top-N as is_leader=True.

    Modifies the list in-place and returns it sorted.
    """
    doctors.sort(key=lambda d: d.influence_score, reverse=True)
    for i, d in enumerate(doctors):
        d.is_leader = i < count
    return doctors


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

# Words that are NOT person names even if they match FIO pattern
_NON_PERSON_WORDS = {
    "центр", "клиника", "отделение", "кабинет", "лаборатория",
    "специалисты", "сотрудники", "персонал", "команда", "врачи",
    "отзывы", "новости", "блог", "вакансии", "контакты", "акции",
    "правовая", "информация", "галерея", "фото", "видео", "скидки",
    "дерматология", "косметология", "гинекология", "стоматология",
    "неврология", "кардиология", "эндокринология", "диетология",
    "офтальмология", "урология", "хирургия", "ортопедия",
    "чекапы", "check-up", "диагностика", "процедуры", "услуги",
    "цены", "прайс", "стоимость", "абонементы", "программы",
    "центры", "направления", "лечение", "терапия", "педиатрия",
    "центр косметологии", "центр здоровья",
    # Legal/administrative
    "российской", "федерации", "российская", "федерация",
    "законом", "постановлением", "правительства", "правительство",
    "государственной", "государственный", "государственная",
    "дума", "думы", "министерство", "министерства",
    "закон", "закона", "кодекс", "кодекса", "статья",
    "яндекс", "метрика", "google", "google.ru",
    "политика", "конфиденциальности", "соглашение",
    "лицензия", "лицензии", "сертификат", "сертификаты",
    "онлайн", "запись", "консультация", "консультации",
    "записаться", "подробнее", "узнать", "прайс-лист",
    "решение", "компетенций",
}

# Common Russian surname suffixes — at least one word should match
_SURNAME_PATTERNS = [
    "ов", "ова", "ев", "ева", "ин", "ина", "ын", "ына",
    "ский", "ская", "цкий", "цкая",
    "енко", "енка", "ук", "юк",
    "ич", "ович", "евич", "овна", "евна",
    "ян", "швили", "дзе", "оглы", "заде",
]


def _looks_like_person_name(text: str) -> bool:
    """Check if text looks like a person's name (2-3 capitalized words, no HTML)."""
    if not text or len(text) < 6 or len(text) > 80:
        return False
    if "<" in text or ">" in text:
        return False
    # Reject text with newlines (multi-line junk from cards)
    if "\n" in text:
        return False
    # Reject if contains known non-person keywords
    text_lower = text.lower()
    for kw in _NON_PERSON_WORDS:
        if kw in text_lower:
            return False
    words = text.split()
    if len(words) < 2 or len(words) > 4:
        return False
    # Russian names: each word starts with a capital letter
    for w in words:
        if not w[0].isupper():
            return False
        if len(w) < 2:
            return False
        # Reject words that look like department/category names
        if w.lower() in _NON_PERSON_WORDS:
            return False
    # At least one word must look like a plausible surname
    has_surname = False
    for w in words:
        w_lower = w.lower()
        for suffix in _SURNAME_PATTERNS:
            if w_lower.endswith(suffix) and len(w_lower) > len(suffix) + 1:
                has_surname = True
                break
        if has_surname:
            break
    if not has_surname:
        # Allow known first names even without surname suffix
        # (some sites list doctors as "Имя Отчество Фамилия")
        pass  # We still require the surname pattern for now

    # Must have at least one Cyrillic capital letter
    has_cyrillic = any("А" <= w[0] <= "Я" or "A" <= w[0] <= "Z" for w in words)
    return has_cyrillic and has_surname


def _clean_specialty(text: str) -> str:
    """Clean and truncate specialty text."""
    if not text:
        return ""
    # Remove HTML tags
    text = re.sub(r"<[^>]+>", "", text)
    # Remove extra whitespace
    text = " ".join(text.split())
    # Cap at 100 chars
    return text[:100].strip()


def _abs_url(url: str, base_url: str) -> str:
    """Convert relative URL to absolute using base_url."""
    if not url:
        return ""
    if url.startswith(("http://", "https://", "//")):
        return url
    if not base_url:
        return url
    if url.startswith("/"):
        # Extract scheme + host from base_url
        from urllib.parse import urlparse
        parsed = urlparse(base_url)
        return f"{parsed.scheme}://{parsed.netloc}{url}"
    return f"{base_url.rstrip('/')}/{url.lstrip('/')}"


def _deduplicate_doctors(doctors: list[dict]) -> list[dict]:
    """Remove duplicate doctors by name (first 30 chars, case-insensitive)."""
    seen: set[str] = set()
    unique: list[dict] = []
    for d in doctors:
        key = d["name"][:30].lower().strip()
        if key and key not in seen:
            seen.add(key)
            unique.append(d)
    return unique[:10]
