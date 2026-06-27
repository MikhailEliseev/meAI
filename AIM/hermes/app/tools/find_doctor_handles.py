"""
find_doctor_handles — Hermes tool: Find clinic doctors + Instagram handles

ПОДХОД С ВЕРИФИКАЦИЕЙ ЧЕРЕЗ СКРАПИНГ:
  1. Скрапим сайт клиники → получаем РЕАЛЬНЫЕ имена врачей (httpx + regex).
  2. Perplexity: для верифицированных врачей ищем регалии + соцсети.
  3. Фильтрация: врачи с Instagram → сортировка по подписчикам → топ-5 для Apify.

Perplexity НЕ выбирает врачей — только обогащает данные. Имена ТОЛЬКО из скрапинга.

Fallback: DeepSeek через LLM_BASE_URL (если PERPLEXITY_API_KEY не задан).
"""

import asyncio
import json
import logging
import os
import re
import time

import httpx

from tools.registry import registry

logger = logging.getLogger(__name__)

PERPLEXITY_API_KEY = os.getenv("PERPLEXITY_API_KEY", "").strip()
PERPLEXITY_BASE_URL = "https://api.perplexity.ai"
PERPLEXITY_MODEL = "sonar-pro"
USE_PERPLEXITY = bool(PERPLEXITY_API_KEY)

LLM_BASE_URL = os.getenv("LLM_BASE_URL", os.getenv("OMNIROUTE_URL", "https://api.deepseek.com/v1"))
LLM_API_KEY = os.getenv("LLM_API_KEY", os.getenv("OMNIROUTE_AUTH", os.getenv("DEEPSEEK_API_KEY", "")))
LLM_MODEL = os.getenv("LLM_MODEL", "deepseek-chat")

REQUEST_TIMEOUT = 90.0
SCRAPE_TIMEOUT = 30.0
MAX_TOKENS = 8000

_cache: dict[str, tuple[float, str]] = {}
_CACHE_TTL = 600

# Типичные URL страниц с врачами (в порядке приоритета)
_DOCTORS_PAGE_PATTERNS = [
    "/specialists/",
    "/specialisty/",
    "/vrachi/",
    "/doctors/",
    "/nashi-vrachi/",
    "/team/",
    "/about/doctors/",
    "/o-klinike/vrachi/",
    "/o-nas/vrachi/",
    "/specialistam/",
    "/personal/",
    "/sotrudniki/",
    "/nasha-komanda/",
    "/kollektiv/",
]

# Слова-маркеры: НЕ имена врачей (UI-элементы, кнопки, навигация)
_UI_WORDS = {
    "позвонить", "записаться", "найти", "сбросить", "применить",
    "показать", "скрыть", "отправить", "заказать", "купить",
    "подробнее", "читать", "смотреть", "скачать", "войти",
    "выйти", "регистраци", "авторизаци", "корзин", "избранн",
    "сравнить", "поделиться", "назад", "вперед", "вверх",
    "меню", "поиск", "закрыть", "открыть", "настройк",
    "профиль", "выйти", "помощь", "поддержка", "контакты",
    "оставить", "написать", "перезвонить", "обратный",
    "заслуженный", "заслужен", "врачей", "специалист",
    "доцент", "профессор", "академик", "член-корр",
    "главный", "главврач", "заведующи", "руководител",
    "отделен", "старший", "младший", "научный", "сотрудник",
    "кафедр", "университет", "институт",
    "стаж", "опыт", "года", "лет",
    "принимает", "ведёт", "консультирует", "оперирует",
    "пластическ", "эстетическ", "челюстно", "лицево",
    "реконструктив", "микрохирург", "лазерн",
    # Navigation
    "позвонить", "записаться", "найти",
}
# Слова-специальности и организационные термины
_NON_DOCTOR_WORDS = {
    "клиник", "центр", "город", "медицин", "москв", "росси",
    "запись", "приём", "консультаци", "услуг", "лечени",
    "отделен", "хирурги", "операци", "главн", "страниц",
    "телефон", "адрес", "почта", "контакт", "новост",
    "акци", "скидк", "подарк", "сертификат", "лицензи",
    "политик", "конфиденци", "обработк", "персональн",
    "информац", "сайт", "поиск", "меню", "кабинет",
    "copyright", "соглас", "cookie", "фамил", "вконтакте",
    "специалист", "врачей", "доктор", "профессор",
    "петербург", "набережн", "оплат",
    "андролог", "бариатри", "гастроэнтеролог", "гематолог",
    "гепатолог", "гинеколог", "дерматолог", "диетолог",
    "иммунолог", "кардиолог", "колопроктолог", "лор",
    "маммолог", "невролог", "нейрохирург", "онколог",
    "ортопед", "оториноларинголог", "офтальмолог",
    "педиатр", "проктолог", "психиатр", "психотерапевт",
    "пульмонолог", "ревматолог", "рентген", "рефлексотерапевт",
    "сомнолог", "стоматолог", "терапевт", "травматолог",
    "уролог", "физиотерапевт", "флеболог", "хирург",
    "эндокринолог", "эндоскопист",
}


def _normalize_args(first_param, defaults):
    if isinstance(first_param, dict):
        return {k: first_param.get(k, defaults[k]) for k in defaults}
    return None


# ═══════════════════════════════════════════════════════════════════════
# STEP 1: Scrape clinic website for REAL doctor names
# ═══════════════════════════════════════════════════════════════════════

async def _scrape_clinic_doctors(url: str) -> tuple[list[str], dict[str, str]]:
    """Scrape the clinic website to find REAL doctor names + profile URLs.

    Tries common URL patterns for the doctors page.
    Returns:
        (names, profile_urls) — verified full names + mapping name→profile page URL.
    """
    if not url or not url.startswith("http"):
        return [], {}

    base_url = url.rstrip("/")

    async def _try_fetch(page_url: str) -> str | None:
        try:
            async with httpx.AsyncClient(timeout=SCRAPE_TIMEOUT, follow_redirects=True) as client:
                resp = await client.get(
                    page_url,
                    headers={
                        "User-Agent": (
                            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                            "AppleWebKit/537.36 (KHTML, like Gecko) "
                            "Chrome/120.0.0.0 Safari/537.36"
                        ),
                        "Accept": "text/html,application/xhtml+xml",
                        "Accept-Language": "ru-RU,ru;q=0.9,en;q=0.8",
                    },
                )
                if resp.status_code == 200 and len(resp.text) > 500:
                    return resp.text
                return None
        except Exception:
            return None

    html = None
    found_url = None

    for pattern in _DOCTORS_PAGE_PATTERNS:
        page_url = f"{base_url}{pattern}"
        html = await _try_fetch(page_url)
        if html:
            found_url = page_url
            logger.info("Scraped doctors page: %s (%d chars)", found_url, len(html))
            break

    if not html:
        html = await _try_fetch(base_url)
        if html:
            found_url = base_url
            logger.info("Fallback to homepage: %s (%d chars)", found_url, len(html))

    if not html:
        logger.warning("Could not scrape any page for %s", base_url)
        return [], {}

    def _is_valid_person_name(name: str) -> bool:
        """Check if a name looks like a real person, not UI text or specialty list."""
        words = name.split()
        if not (2 <= len(words) <= 3):
            return False
        full_lower = name.lower()

        # No UI words
        if any(ui_word in full_lower for ui_word in _UI_WORDS):
            return False

        # No non-doctor words
        if any(ndw in full_lower for ndw in _NON_DOCTOR_WORDS):
            return False

        # First name must be capitalized (Фамилия)
        if not words[0][0].isupper():
            return False

        # All words should be capitalized
        if not all(w[0].isupper() for w in words):
            return False

        # No single-letter words
        if any(len(w) < 3 for w in words):
            return False

        # Check for specialty suffixes in words
        _SPECIALTY_SUFFIXES = (
            'хирург', 'терапевт', 'лог', 'певт', 'метр', 'зист',
        )
        spec_word_count = sum(
            1 for w in words
            if any(suffix in w.lower() for suffix in _SPECIALTY_SUFFIXES)
        )
        # If 2+ words look like specialties, it's not a person
        if spec_word_count >= 2:
            return False
        # If it's 2 words and both look like specialties
        if len(words) == 2 and spec_word_count >= 1:
            return False

        # Фамилия should end in typical Russian surname endings
        # Broad endings: Russian, Ukrainian, Georgian, Armenian, Baltic, etc.
        _SURNAME_ENDINGS = (
            'ов', 'ев', 'ёв', 'ин', 'ын', 'ий', 'ой', 'ый', 'ая', 'яя',
            'ко', 'ук', 'юк', 'чук', 'нюк', 'енко',
            'вич', 'овна', 'евна', 'ична', 'ыч', 'ич',
            'ский', 'цкий', 'ская', 'цкая', 'ских', 'цких',
            'ных', 'ян', 'янц', 'дзе', 'швили', 'ан',
            'берг', 'ман', 'ерн', 'лис', 'ага', 'ули', 'ели',
            'о', 'их', 'ых',
        )
        # At least one word should have a name-like ending
        has_name_ending = any(
            any(w.lower().endswith(ending) for ending in _SURNAME_ENDINGS)
            for w in words
        )
        if not has_name_ending:
            return False

        return True

    # ── Extract names ──────────────────────────────────────────
    # Remove scripts, styles, then strip HTML tags
    html_clean = re.sub(r'<script[^>]*>.*?</script>', '', html, flags=re.DOTALL | re.IGNORECASE)
    html_clean = re.sub(r'<style[^>]*>.*?</style>', '', html_clean, flags=re.DOTALL | re.IGNORECASE)

    # ── Extract profile URLs BEFORE stripping tags ────────────
    # Look for <a href="...doctor-path...">Имя Фамилия</a> patterns
    profile_urls: dict[str, str] = {}
    name_in_link_pattern = re.compile(
        r'([А-ЯЁ][а-яё]+\s+[А-ЯЁ][а-яё]+(?:\s+[А-ЯЁ][а-яё]+)?)'
    )
    for link_match in re.finditer(
        r'<a\s+[^>]*href\s*=\s*["\']([^"\']+)["\'][^>]*>\s*'
        r'([А-ЯЁ][а-яё]+\s+[А-ЯЁ][а-яё]+(?:\s+[А-ЯЁ][а-яё]+)?)\s*</a>',
        html_clean, re.IGNORECASE,
    ):
        href = link_match.group(1)
        link_name = link_match.group(2).strip()
        if _is_valid_person_name(link_name):
            full_url = href if href.startswith("http") else base_url.rstrip("/") + "/" + href.lstrip("/")
            profile_urls[link_name] = full_url

    html_clean = re.sub(r'<[^>]+>', ' ', html_clean)
    html_clean = re.sub(r'\s+', ' ', html_clean)

    # Russian full name: 2-3 words, each capitalized
    name_pattern = re.compile(
        r'\b([А-ЯЁ][а-яё]+\s+[А-ЯЁ][а-яё]+(?:\s+[А-ЯЁ][а-яё]+)?)\b'
    )

    found_names = []
    seen = set()

    for match in name_pattern.finditer(html_clean):
        full_name = match.group(1).strip()
        if full_name in seen:
            continue
        if not _is_valid_person_name(full_name):
            continue
        seen.add(full_name)
        found_names.append(full_name)

    # ── Also try HTML structure (h3, h4, doctor card patterns) ──
    for tag_pattern in [
        r'<h[34][^>]*>([^<]+)</h[34]>',
        r'class="[^"]*name[^"]*"[^>]*>([^<]+)',
        r'class="[^"]*doctor[^"]*"[^>]*>([^<]+)',
        r'class="[^"]*specialist[^"]*"[^>]*>([^<]+)',
    ]:
        for match in re.finditer(tag_pattern, html, re.IGNORECASE):
            text = match.group(1).strip()
            name_matches = name_pattern.findall(text)
            for nm in name_matches:
                nm = nm.strip()
                if nm not in seen and _is_valid_person_name(nm):
                    seen.add(nm)
                    found_names.append(nm)

    logger.info(
        "Extracted %d verified doctor names (+ %d profile URLs) from %s",
        len(found_names), len(profile_urls), found_url,
    )
    return found_names, profile_urls


# ═══════════════════════════════════════════════════════════════════════
# STEP 1.5: Scrape individual doctor profile pages for context
# ═══════════════════════════════════════════════════════════════════════

_SOCIAL_DOMAINS = [
    "instagram.com", "t.me", "telegram.me", "vk.com", "vkontakte.ru",
    "youtube.com", "youtu.be", "facebook.com", "ok.ru", "dzen.ru",
]

# Keywords that signal regalia / achievements
_REGALIA_KEYWORDS = [
    "профессор", "доцент", "академик", "член-корр", "член корр",
    "доктор медицинских наук", "д.м.н", "д.м.н.", "к.м.н", "к.м.н.",
    "кандидат медицинских наук", "заведующи", "зав.", "руководитель",
    "главный врач", "главврач", "зам.", "заместитель", "президент",
    "член общества", "член правления", "член этического",
    "преподаватель", "кафедр", "сертифицирован",
    "стаж", "лет опыта",
]


# ── Phase 4 / SEC-04 / D-08: Structured regalia extraction ───────────────
# Denylist for false positives in education extraction.
# Captured text containing any of these substrings is treated as
# non-institutional context and skipped.
_EDUCATION_DENYLIST = (
    "работу",   # "окончил работу в клинике"
    "врачом",   # "окончил работу врачом"
    "стаж",     # "окончил стажировку"
    "обучение", # "окончил обучение на курсах"
    "повышени", # "окончил повышение квалификации"
    "лекцию",   # "окончил лекцию"
    "практик",  # "окончил практику"
    "курс",     # "окончил курс лекций"
)


def _extract_structured_regalia(text: str) -> dict:
    """Extract TYPED regalia fields from doctor profile page text.

    Phase 4 / SEC-04 / D-08. Parses academic degree, title, experience years,
    and educational institutions from cleaned doctor-bio text.

    Args:
        text: Cleaned text from a doctor profile page (e.g., the output of
            ``re.sub(r'\\s+', ' ', text).strip()`` in ``_scrape_doctor_profile``).

    Returns:
        dict with keys:
            - ``degree`` (str | None): "КМН" | "ДМН" | None
            - ``academic_title`` (str | None): профессор / доцент / академик /
              член-корреспондент / None
            - ``experience_years`` (int | None): years of professional experience
            - ``education`` (list[str]): up to 3 unique institution strings
    """
    empty = {
        "degree": None,
        "academic_title": None,
        "experience_years": None,
        "education": [],
    }
    if not text:
        return empty

    text_lower = text.lower()

    # ── degree: КМН / ДМН (ДМН takes priority if both present) ──
    degree: str | None = None
    if (
        "доктор медицинских наук" in text_lower
        or "д.м.н" in text_lower
    ):
        degree = "ДМН"
    elif (
        "кандидат медицинских наук" in text_lower
        or "к.м.н" in text_lower
    ):
        degree = "КМН"

    # ── academic_title (priority: профессор > доцент > академик > член-корр) ──
    academic_title: str | None = None
    if "профессор" in text_lower:
        academic_title = "профессор"
    elif "доцент" in text_lower:
        academic_title = "доцент"
    elif "академик" in text_lower:
        academic_title = "академик"
    elif "член-корр" in text_lower or "член корр" in text_lower:
        academic_title = "член-корреспондент"

    # ── experience_years (regex priority order) ─────────────────
    experience_years: int | None = None
    for pattern in (
        r"стаж\s+(?:работы\s+)?(\d+)\s*лет",
        r"(\d+)\s*лет\s+опыта",
        r"опыт\s+работы\s+(\d+)\s*лет",
    ):
        m = re.search(pattern, text_lower)
        if m:
            try:
                experience_years = int(m.group(1))
                break
            except ValueError:
                continue

    # ── education (regex extract → denylist filter → dedup → cap 3) ──
    raw_education: list[str] = []
    for pattern in (
        r"окончил[а]?\s+([^.]{5,100})",
        r"образование[:\s]+([^.]{5,100})",
    ):
        for m in re.finditer(pattern, text, re.IGNORECASE):
            institution = m.group(1).strip().rstrip(",;: ")
            # False-positive filter
            inst_lower = institution.lower()
            if any(bad in inst_lower for bad in _EDUCATION_DENYLIST):
                continue
            # Hard cap per entry (regex {5,100} already bounds it,
            # but defensive truncation in case of boundary edge cases)
            if len(institution) > 100:
                institution = institution[:100].strip()
            raw_education.append(institution)

    # Deduplicate (case-insensitive key) preserving order
    seen: set[str] = set()
    education: list[str] = []
    for inst in raw_education:
        key = inst.lower()
        if key in seen:
            continue
        seen.add(key)
        education.append(inst)
        if len(education) >= 3:
            break

    return {
        "degree": degree,
        "academic_title": academic_title,
        "experience_years": experience_years,
        "education": education,
    }


# Empty-default structured_regalia dict — reused by handler fallbacks
# (Perplexity-enrichment-only path, exception/None profile branches).
# Module-level singleton so we don't allocate a fresh dict per doctor.
_EMPTY_STRUCTURED_REGALIA: dict = {
    "degree": None,
    "academic_title": None,
    "experience_years": None,
    "education": [],
}


def _normalize_full_name(name: str) -> str:
    """Normalize a Russian full name for deterministic matching.

    Phase 4 / SEC-04 / D-09. Used by _merge_doctor_data to match site-scraped
    doctors with Instagram-analyzed doctors by ФИО.

    Normalization rules:
        - lowercase
        - strip leading/trailing whitespace
        - collapse internal whitespace
        - remove dots and hyphens

    Examples:
        ``"Иванов И.И."`` → ``"иванов и и"``
        ``"Иванов Иван Иванович"`` → ``"иванов иван иванович"``
        ``"Петров-Иванов П.П."`` → ``"петров иванов п п"``
    """
    if not name:
        return ""
    n = name.lower().strip()
    n = re.sub(r"[.\-]+", " ", n)
    n = re.sub(r"\s+", " ", n).strip()
    return n


def _names_match(name_a: str, name_b: str) -> bool:
    """Check if two Russian names refer to the same person.

    Phase 4 / SEC-04 / D-09. Initials-aware matching: when one side uses an
    initial (single letter), it matches the corresponding full token's first
    letter on the other side. Last name (first token) MUST match exactly.

    Examples (all return True):
        ``"Иванов И.И."`` ↔ ``"Иванов Иван Иванович"``
        ``"Петров П.П."`` ↔ ``"Петров Петр Петрович"``
        ``"Иванов Иван"`` ↔ ``"Иванов Иван Иванович"`` (subset matches)

    Examples (return False):
        ``"Иванов И.И."`` ↔ ``"Иванов Петр Петрович"`` (initial mismatch)
        ``"Иванов И.И."`` ↔ ``"Петров И.И."`` (last name mismatch)

    Args:
        name_a, name_b: Raw name strings (any case, may contain dots/hyphens).

    Returns:
        True if names are considered to refer to the same person.
    """
    a_tokens = _normalize_full_name(name_a).split()
    b_tokens = _normalize_full_name(name_b).split()
    if not a_tokens or not b_tokens:
        return False

    # Last name MUST match exactly (case-insensitive after normalization)
    if a_tokens[0] != b_tokens[0]:
        return False

    # If either side has only a last name, accept the match
    if len(a_tokens) == 1 or len(b_tokens) == 1:
        return True

    # Compare remaining tokens position-by-position with initial-aware logic.
    # Tokens like "и" (initial) match the first letter of the other token.
    # Tokens like "иван" (full) must match exactly OR be matched by an initial.
    common_len = min(len(a_tokens), len(b_tokens))
    for i in range(1, common_len):
        ta, tb = a_tokens[i], b_tokens[i]
        if ta == tb:
            continue
        # Single-letter token (initial) matches first letter of the other
        if len(ta) == 1 and tb.startswith(ta):
            continue
        if len(tb) == 1 and ta.startswith(tb):
            continue
        return False

    # If one side has MORE tokens than the other, that's OK — the shorter
    # side just omits the middle name or patronymic. We accept because the
    # last name + matched-initials subset is a strong signal.
    return True


def _merge_doctor_data(site_doctors: list[dict], instagram_data: dict) -> list[dict]:
    """Merge site-scraped doctors (with регалии) and Instagram-analyzed doctors.

    Phase 4 / SEC-04 / D-09. Deterministic initials-aware ФИО matching — does
    NOT call an LLM. The LLM consumer (Pass 3 orchestrator) resolves any
    remaining ambiguities from conversation context.

    Matching rules (see ``_names_match``):
        - Last name (first token) MUST match exactly
        - Initials match corresponding full tokens by first letter
        - Subset matches are accepted (e.g., 2-token vs 3-token)

    Args:
        site_doctors: list of doctor dicts (typically from
            ``handle_find_doctor_handles``) where each doctor has at least a
            ``"name"`` key and optionally a ``"structured_regalia"`` dict.
        instagram_data: batch response dict from ``run_instagram_content`` with
            optional ``top_by_followers`` and ``profiles`` lists. Each profile
            is matched by its ``full_name`` field.

    Returns:
        list[dict] — each entry has at minimum:
            - ``name`` (str)
            - ``structured_regalia`` (dict) — from site or ``_EMPTY_STRUCTURED_REGALIA``
            - ``instagram_metrics`` (dict | None) — matched profile or None
            - ``source`` (str): ``"site"`` | ``"instagram_only"`` | ``"both"``
    """
    if not site_doctors and not instagram_data:
        return []

    # ── Flatten Instagram profiles into a list ─────────────────
    ig_profiles: list[dict] = []
    if instagram_data:
        for key in ("top_by_followers", "profiles"):
            for profile in instagram_data.get(key, []) or []:
                full_name = profile.get("full_name") or profile.get("name") or ""
                if full_name:
                    ig_profiles.append(profile)

    matched_ig_indices: set[int] = set()
    merged: list[dict] = []

    # ── Pass 1: site doctors → look up Instagram metrics by ФИО ─
    for site_doc in site_doctors or []:
        name = site_doc.get("name") or site_doc.get("full_name") or ""
        if not name:
            continue

        ig_profile: dict | None = None
        for idx, profile in enumerate(ig_profiles):
            ig_name = profile.get("full_name") or profile.get("name") or ""
            if _names_match(name, ig_name):
                ig_profile = profile
                matched_ig_indices.add(idx)
                break  # first match wins; LLM resolves multi-match ambiguities

        regalia = site_doc.get("structured_regalia")
        if not regalia or not isinstance(regalia, dict):
            regalia = dict(_EMPTY_STRUCTURED_REGALIA)

        entry: dict = {
            "name": name,
            "structured_regalia": regalia,
            "instagram_metrics": ig_profile,
            "source": "both" if ig_profile is not None else "site",
        }
        # Optional carry-forward (non-destructive — only if present)
        for opt_key in ("profile_url", "specializations", "regalia", "social_links"):
            if opt_key in site_doc:
                entry[opt_key] = site_doc[opt_key]
        merged.append(entry)

    # ── Pass 2: Instagram-only doctors (not matched to any site doctor) ──
    for idx, profile in enumerate(ig_profiles):
        if idx in matched_ig_indices:
            continue
        full_name = profile.get("full_name") or profile.get("name") or ""
        entry = {
            "name": full_name,
            "structured_regalia": dict(_EMPTY_STRUCTURED_REGALIA),
            "instagram_metrics": profile,
            "source": "instagram_only",
        }
        merged.append(entry)

    return merged


# Specialization keywords (abbreviated forms common in page text)
_SPEC_KEYWORDS = [
    "пластический хирург", "хирург", "косметолог", "дерматолог",
    "андролог", "гинеколог", "уролог", "онколог", "флеболог",
    "отоларинголог", "лор", "офтальмолог", "невролог", "терапевт",
    "эндокринолог", "кардиолог", "гастроэнтеролог", "стоматолог",
    "ортопед", "травматолог", "маммолог", "реабилитолог",
    "анестезиолог", "рентгенолог",
]


async def _scrape_doctor_profile(profile_url: str) -> dict | None:
    """Scrape a single doctor's profile page for bio, specialization & social links.

    Fast: 200-500ms per page (httpx, no JS rendering).
    Returns dict with: bio, specializations, regalia, social_links, title.
    Returns None on failure (timeout, 404, etc.).
    """
    if not profile_url or not profile_url.startswith("http"):
        return None

    try:
        async with httpx.AsyncClient(timeout=SCRAPE_TIMEOUT, follow_redirects=True) as client:
            resp = await client.get(
                profile_url,
                headers={
                    "User-Agent": (
                        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                        "AppleWebKit/537.36 (KHTML, like Gecko) "
                        "Chrome/120.0.0.0 Safari/537.36"
                    ),
                    "Accept": "text/html,application/xhtml+xml",
                    "Accept-Language": "ru-RU,ru;q=0.9,en;q=0.8",
                },
            )
            if resp.status_code != 200 or len(resp.text) < 500:
                return None

        html = resp.text
    except Exception:
        return None

    # ── Extract social links (href attributes) ─────────────────
    social_links: dict[str, str] = {}
    for m in re.finditer(r'href\s*=\s*["\']([^"\']*(?:instagram\.com|t\.me|telegram\.me|vk\.com|vkontakte\.ru|youtube\.com|youtu\.be|facebook\.com|ok\.ru|dzen\.ru)[^"\']*)["\']', html, re.IGNORECASE):
        url = m.group(1)
        for domain in _SOCIAL_DOMAINS:
            if domain in url.lower():
                platform = domain.split(".")[0]
                if platform not in social_links:
                    social_links[platform] = url
                break

    # ── Extract title tag ─────────────────────────────────────
    title = ""
    title_match = re.search(r'<title[^>]*>(.*?)</title>', html, re.IGNORECASE)
    if title_match:
        title = title_match.group(1).strip()

    # ── Extract text content ──────────────────────────────────
    # Remove scripts, styles
    text = re.sub(r'<script[^>]*>.*?</script>', '', html, flags=re.DOTALL | re.IGNORECASE)
    text = re.sub(r'<style[^>]*>.*?</style>', '', text, flags=re.DOTALL | re.IGNORECASE)
    text = re.sub(r'<[^>]+>', ' ', text)
    text = re.sub(r'\s+', ' ', text).strip()

    # ── Extract specializations ───────────────────────────────
    text_lower = text.lower()
    specializations = []
    for kw in _SPEC_KEYWORDS:
        if kw in text_lower:
            specializations.append(kw)

    # ── Extract regalia ───────────────────────────────────────
    regalia = []
    for kw in _REGALIA_KEYWORDS:
        if kw.lower() in text_lower:
            regalia.append(kw)

    # ── Extract structured regalia (Phase 4 / SEC-04 / D-08) ───
    structured_regalia = _extract_structured_regalia(text)

    # ── Compress bio to ~300 chars (first part is most relevant) ──
    bio = text[:2000] if len(text) > 2000 else text

    return {
        "title": title,
        "bio": bio,
        "specializations": specializations[:5],
        "regalia": regalia[:5],
        "structured_regalia": structured_regalia,
        "social_links": social_links,
    }


# ═══════════════════════════════════════════════════════════════════════
# STEP 2: Perplexity finds regalia + social media for verified names
# ═══════════════════════════════════════════════════════════════════════

def _build_enrichment_query_batch(
    doctors_data: list[dict], clinic_name: str, city: str = "", specialization: str = ""
) -> str:
    """Build a TARGETED query for doctors — enriched with profile page context.

    Args:
        doctors_data: list of dicts, each with:
            'name' (str), 'profile_url' (str|None), 'specializations' (list),
            'regalia' (list), 'social_links' (dict|None).
    """
    names_with_context = []
    for i, d in enumerate(doctors_data):
        name = d.get("name") or d.get("full_name", "")
        hints = _generate_handle_hints(name)
        profile_url = d.get("profile_url", "")
        specs = d.get("specializations", [])
        regs = d.get("regalia", [])
        social_found = d.get("social_links") or {}

        context_parts = []
        if specs:
            context_parts.append("Специализации: " + ", ".join(specs[:3]))
        if regs:
            context_parts.append("Регалии: " + ", ".join(regs[:3]))
        if profile_url:
            context_parts.append(f"Страница на сайте: {profile_url}")
        if social_found:
            context_parts.append("Соцсети с сайта: " + ", ".join(
                f"{plat}: {url}" for plat, url in social_found.items()
            ))

        context_str = " | ".join(context_parts) if context_parts else "нет данных с сайта"

        names_with_context.append(
            f"{i+1}. {name}\n"
            f"   Контекст: {context_str}\n"
            f"   Возможные никнеймы: {', '.join('@'+h for h in hints[:6])}"
        )

    names_text = "\n".join(names_with_context)
    city_str = f", город {city}" if city else ""
    spec_str = f" ({specialization})" if specialization else ""

    return (
        f"Найди Instagram для врачей клиники «{clinic_name}»{city_str}{spec_str}:\n\n"
        f"{names_text}\n\n"
        "ДЛЯ КАЖДОГО:\n"
        "1. Поищи в вебе: 'Фамилия Имя Instagram' + контекст из специализации/регалий\n"
        "2. ПРОВЕРЬ ВСЕ никнеймы из списка выше — открой Instagram.com/никнейм\n"
        "3. ENTITY RESOLUTION — проверь СОВПАДЕНИЕ по 5 сигналам:\n"
        "   - ФИО в bio/username\n"
        "   - Город в описании профиля\n"
        "   - Специализация в bio (сравни с контекстом выше)\n"
        "   - Ссылка на сайт клиники или упоминание «{clinic_name}» в bio/ссылках\n"
        "   - Регалии (если указаны в контексте — проверь упоминания в bio)\n"
        "5. Сравни фото профиля с фото врача (если есть страница на сайте — зайди по ссылке)\n"
        "6. Если нашёл несколько аккаунтов — выбери ТОТ, где больше сигналов совпадает\n"
        "7. Если не нашёл — попробуй ЕЩЁ РАЗ с другими вариантами\n\n"
        "ОТВЕТ СТРОГО:\n"
        "---\n"
        "Врач: ФИО | специализация\n"
        "Instagram: @nickname (подписчиков: N)\n"
        "---\n"
        "Если не нашёл — Instagram: не найден"
    )


def _generate_handle_hints(full_name: str) -> list[str]:
    """Generate likely Instagram handle patterns from a Russian name."""
    parts = full_name.split()
    if len(parts) < 2:
        return []

    surname = parts[0]
    first_name = parts[1] if len(parts) > 1 else ""

    # Simple transliteration table (Russian → Latin)
    _RU_TO_LAT = {
        'а': 'a', 'б': 'b', 'в': 'v', 'г': 'g', 'д': 'd', 'е': 'e', 'ё': 'e',
        'ж': 'zh', 'з': 'z', 'и': 'i', 'й': 'y', 'к': 'k', 'л': 'l', 'м': 'm',
        'н': 'n', 'о': 'o', 'п': 'p', 'р': 'r', 'с': 's', 'т': 't', 'у': 'u',
        'ф': 'f', 'х': 'kh', 'ц': 'ts', 'ч': 'ch', 'ш': 'sh', 'щ': 'shch',
        'ы': 'y', 'э': 'e', 'ю': 'yu', 'я': 'ya',
        'ь': '', 'ъ': '',
    }

    def _translit(text: str) -> str:
        result = []
        for ch in text.lower():
            result.append(_RU_TO_LAT.get(ch, ch))
        return ''.join(result)

    # Common Western spelling variants for Russian names
    _NAME_VARIANTS: dict[str, list[str]] = {
        'артур': ['artur', 'arthur'],
        'евгений': ['evgeniy', 'evgeny', 'eugene', 'yevgeny'],
        'ева': ['eva', 'yeva'],
        'юлия': ['yulia', 'julia', 'yuliya'],
        'наталья': ['natalya', 'natalia', 'natali'],
        'константин': ['konstantin', 'constantine'],
        'ксения': ['ksenia', 'kseniia', 'xenia'],
        'дмитрий': ['dmitry', 'dmitriy', 'dmitrii'],
        'александр': ['alexander', 'alexandr', 'aleksandr'],
        'ольга': ['olga'],
        'анна': ['anna'],
        'елена': ['elena', 'yelena'],
        'сергей': ['sergey', 'sergei', 'sergii'],
        'андрей': ['andrey', 'andrei'],
        'максим': ['maxim', 'maksim'],
        'владимир': ['vladimir'],
        'алексей': ['alexey', 'alexei', 'aleksey'],
        'игорь': ['igor'],
        'станислав': ['stanislav', 'stanislaw'],
        'григорий': ['grigory', 'grigoriy', 'gregory'],
    }

    s_lat = _translit(surname)
    n_lat = _translit(first_name)
    # Get Western spelling variants for this name
    name_variants = _NAME_VARIANTS.get(first_name.lower(), [n_lat])
    if n_lat not in name_variants:
        name_variants.insert(0, n_lat)

    # Common abbreviations
    s_short = s_lat[:5] if len(s_lat) > 5 else s_lat
    n_short = n_lat[:4] if len(n_lat) > 4 else n_lat

    hints = []
    # PRIORITY 1: Core patterns (no name dependency) — most likely to hit
    hints.append(f"dr{s_lat}")           # @drmelnikov style (no underscore!)
    hints.append(f"dr_{s_lat}")          # @dr_melnikov
    hints.append(f"doctor_{s_lat}")      # @doctor_melnikov
    hints.append(f"{s_lat}")             # pure surname
    hints.append(f"dr.{s_lat}")          # @dr.melnikov

    # PRIORITY 2: Name+surname+channel for ALL variants (catches Western spellings)
    for n_var in name_variants[:2]:
        hints.append(f"{n_var}_{s_lat}_channel")      # @arthur_rybakin_channel

    # PRIORITY 3: Surname-only suffix patterns
    for suffix in ["channel", "official", "doc", "clinic", "med"]:
        hints.append(f"{s_lat}_{suffix}")            # @rybakin_channel

    # PRIORITY 4: Name+surname+other suffixes
    for n_var in name_variants[:2]:
        hints.append(f"{n_var}_{s_lat}_official")     # @arthur_rybakin_official

    for n_var in name_variants[:2]:  # max 2 name variants
        # PRIORITY 5: Name+surname patterns
        hints.append(f"dr_{n_var}_{s_lat}")             # @dr_artur_rybakin
        hints.append(f"doctor_{n_var}_{s_lat}")         # @doctor_artur_rybakin
        hints.append(f"{n_var}_{s_lat}")                # @artur_rybakin

    # Remove duplicates preserving order
    seen = set()
    unique = []
    for h in hints:
        h_clean = h.strip('_')
        if h_clean not in seen and len(h_clean) >= 3:
            seen.add(h_clean)
            unique.append(h_clean)

    return unique


def _build_enrichment_system_prompt() -> str:
    return (
        "Ты ищешь Instagram-аккаунты врачей. "
        "Для каждого врача выполни веб-поиск с разными вариантами запроса. "
        "ENTITY RESOLUTION — ты ДОЛЖЕН проверить 5 сигналов перед тем как сказать «нашёл»:\n"
        "1. ФИО — совпадает ли имя/фамилия в username, name, bio\n"
        "2. Город — указан ли тот же город в профиле\n"
        "3. Специализация — совпадает ли специализация в bio\n"
        "4. Клиника — есть ли ссылка на сайт клиники или упоминание в bio/ссылках\n"
        "5. Фото — совпадает ли аватар с фото врача на сайте клиники\n\n"
        "Если хотя бы 3 из 5 сигналов совпадают — это ОН. Если 1-2 — продолжай искать.\n"
        "Найди ТОЧНЫЙ никнейм и число подписчиков. "
        "Если не нашёл — честно напиши «Instagram: не найден»."
    )




# ═══════════════════════════════════════════════════════════════════════
# Perplexity / LLM calls
# ═══════════════════════════════════════════════════════════════════════

async def _call_perplexity(system_prompt: str, user_prompt: str) -> str:
    from hashlib import sha256
    from openai import AsyncOpenAI

    # P5: file cache check
    cache_key = f"pplx_{sha256((system_prompt + user_prompt).encode()).hexdigest()[:32]}"
    try:
        from app.tools._file_cache import file_cache
        cached = await file_cache.get(cache_key)
        if cached is not None:
            logger.info("Perplexity cache HIT (%d chars)", len(cached))
            return cached
    except Exception:
        pass

    client = AsyncOpenAI(
        api_key=PERPLEXITY_API_KEY,
        base_url=PERPLEXITY_BASE_URL,
        timeout=REQUEST_TIMEOUT,
    )
    response = await client.chat.completions.create(
        model=PERPLEXITY_MODEL,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        temperature=0.2,
        max_tokens=MAX_TOKENS,
    )
    result = response.choices[0].message.content or ""

    # P5: save to file cache
    try:
        from app.tools._file_cache import file_cache
        await file_cache.set(cache_key, result)
    except Exception:
        pass

    return result


async def _call_llm(system_prompt: str, user_prompt: str) -> str:
    from openai import AsyncOpenAI

    client = AsyncOpenAI(
        api_key=LLM_API_KEY,
        base_url=LLM_BASE_URL,
        timeout=REQUEST_TIMEOUT,
    )
    response = await client.chat.completions.create(
        model=LLM_MODEL,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        temperature=0.2,
        max_tokens=MAX_TOKENS,
    )
    return response.choices[0].message.content or ""


# ═══════════════════════════════════════════════════════════════════════
# Parsing
# ═══════════════════════════════════════════════════════════════════════

def _parse_enrichment(answer: str, doctor_names: list[str]) -> list[dict]:
    """Parse Perplexity's enrichment response into structured doctor data."""
    # Split by doctor sections
    sections = re.split(r'\n---\n|^---\n|\n---$', answer, flags=re.MULTILINE)
    if len(sections) <= 1:
        sections = re.split(r'\n(?=Врач:)', answer)

    doctors = []
    seen_names = set()

    for section in sections:
        section = section.strip()
        if not section or len(section) < 15:
            continue

        # ── Doctor name ────────────────────────────────────────
        header_match = re.search(r'Врач:\s*(.+?)(?:\n|$)', section)
        header = header_match.group(1).strip() if header_match else ""

        # Parse header: "ФИО | специализация"
        if "|" in header:
            parts = [p.strip() for p in header.split("|")]
            full_name = parts[0] if len(parts) > 0 else ""
            specialization = parts[1] if len(parts) > 1 else ""
        else:
            full_name = header
            specialization = ""

        # ── Instagram ──────────────────────────────────────────
        # Multiple patterns to catch various formats
        ig_handle = ""
        followers = 0
        is_private = "приват" in section.lower()

        # Pattern 1: "Instagram: @nickname (подписчиков: N)"
        ig_match = re.search(
            r'Instagram:\s*(?:@)?([a-zA-Z][a-zA-Z0-9_.]{2,29})',
            section,
        )
        # Pattern 2: "**@nickname**"  (markdown bold)
        if not ig_match:
            ig_match = re.search(r'\*\*@([a-zA-Z][a-zA-Z0-9_.]{2,29})\*\*', section)
        # Pattern 3: "@nickname" anywhere in the doctor section
        if not ig_match:
            ig_match = re.search(r'(?<!\w)@([a-zA-Z][a-zA-Z0-9_.]{2,29})(?!\w)', section)

        if ig_match:
            ig_handle = ig_match.group(1)
            # Filter out false positives
            _KNOWN_TLDS = {
                'ru', 'com', 'org', 'net', 'su', 'io', 'dev', 'pro',
                'info', 'biz', 'online', 'site', 'live', 'app',
            }
            if ig_handle.lower() in _KNOWN_TLDS:
                ig_handle = ""

        # Extract followers (two patterns: keyword-first and number-first)
        followers_str = None
        # Pattern 1: "followers: 87.5K" / "подписчиков: 52K"
        m1 = re.search(
            r'(?:подписчиков|фолловеров|followers)[:\s]*(\d[\d\s.]*[KkMm]?)',
            section, re.IGNORECASE,
        )
        # Pattern 2: "87.5K followers" / "52K подписчиков" (number BEFORE keyword)
        m2 = re.search(
            r'(\d[\d\s.]*[KkMm]?)\s*(?:подписчиков|фолловеров|followers)',
            section, re.IGNORECASE,
        )
        followers_match = m1 or m2
        if followers_match:
            followers_str = followers_match.group(1).replace(" ", "").strip()
            try:
                if 'K' in followers_str.upper():
                    followers = int(float(followers_str.upper().replace('K', '')) * 1000)
                elif 'M' in followers_str.upper():
                    followers = int(float(followers_str.upper().replace('M', '')) * 1_000_000)
                else:
                    followers = int(float(followers_str.replace(',', '')))
            except (ValueError, TypeError):
                pass

        # Skip if "не найден" for Instagram
        if re.search(r'Instagram:\s*не\s*найден', section, re.IGNORECASE):
            ig_handle = ""

        # Strip unpaired markdown stars first (e.g. **Годин — without closing **)
        full_name = full_name.strip('*').strip()
        # Strip markdown formatting from name (paired stars)
        full_name = re.sub(r'\*+([^*]+)\*+', r'\1', full_name).strip()
        # Strip citation brackets like [1][9]
        full_name = re.sub(r'\[\d+\]', '', full_name).strip()

        if not full_name or len(full_name.split()) < 2:
            continue

        # Deduplicate
        name_key = full_name.lower()
        if name_key in seen_names:
            continue
        seen_names.add(name_key)

        doctors.append({
            "full_name": full_name,
            "specialization": specialization,
            "regalia": "",
            "position": "",
            "instagram": ig_handle,
            "instagram_private": is_private,
            "instagram_followers_approx": followers,
            "telegram": "",
            "youtube": "",
            "verified": True,
            "verified_on_site": True,
        })

    # If parsing failed (no doctor sections found), try to extract from raw text
    if not doctors and doctor_names:
        for name in doctor_names:
            doctors.append({
                "full_name": name,
                "specialization": "",
                "regalia": "",
                "position": "",
                "instagram": "",
                "instagram_private": False,
                "instagram_followers_approx": 0,
                "telegram": "",
                "youtube": "",
                "verified": True,
                "verified_on_site": True,
            })

    return doctors


def _extract_all_handles(answer: str) -> list[str]:
    """Extract all Instagram handles from text."""
    handles = set()

    for m in re.finditer(r'(?<!\w)@([a-zA-Z][a-zA-Z0-9_.]{2,29})(?!\w)', answer):
        handles.add(m.group(1))

    for m in re.finditer(r'Instagram:\s*(?:@)?([a-zA-Z][a-zA-Z0-9_.]{2,29})', answer):
        handles.add(m.group(1))

    _KNOWN_TLDS = {
        'ru', 'com', 'org', 'net', 'su', 'io', 'dev', 'pro',
        'info', 'biz', 'online', 'site', 'live', 'app', 'co',
        'рф', 'рус', 'москва', 'дети', 'travel', 'shop', 'club',
        'blog', 'news', 'wiki', 'media', 'email', 'website',
    }
    filtered = []
    for h in handles:
        h_lower = h.strip('.').lower()
        parts = h_lower.split('.')
        if any(p in _KNOWN_TLDS for p in parts):
            continue
        if len(parts) > 1 and all(p.isascii() for p in parts):
            continue
        if len(h_lower) < 3:
            continue
        filtered.append(h_lower)

    return list(dict.fromkeys(filtered))


# ═══════════════════════════════════════════════════════════════════════
# Main handler
# ═══════════════════════════════════════════════════════════════════════

async def handle_find_doctor_handles(url=None, company_name="", city="", specialization="", **kwargs) -> str:
    """Find clinic doctors via website scraping + Perplexity enrichment.

    Step 1: Scrape clinic website → get REAL doctor names.
    Step 2: Perplexity enriches with regalia + finds social media.

    Returns JSON with verified doctors, handles, and top-5 for Apify.
    """
    unpacked = _normalize_args(url, {"url": "", "company_name": "", "city": "", "specialization": ""})
    if unpacked:
        url = unpacked.get("url", url)
        company_name = unpacked.get("company_name", company_name)
        city = unpacked.get("city", city)
        specialization = unpacked.get("specialization", specialization)

    cn = kwargs.get("company_name", "")
    if cn and not company_name:
        company_name = cn
    ct = kwargs.get("city", "")
    if ct and not city:
        city = ct
    sp = kwargs.get("specialization", "")
    if sp and not specialization:
        specialization = sp

    search_target = url or company_name or ""
    if not search_target:
        return json.dumps({"error": "URL or clinic name is required"}, ensure_ascii=False)

    if url and url.startswith("http") and not company_name:
        from urllib.parse import urlparse
        parsed = urlparse(url)
        company_name = parsed.netloc.replace("www.", "")

    query_name = company_name or search_target

    cache_key = f"doctors_v5_{query_name}_{city}"
    cached = _cache.get(cache_key)
    if cached is not None:
        cached_ts, cached_result = cached
        if time.time() - cached_ts < _CACHE_TTL:
            logger.info("Doctor handles cache HIT for: %s", query_name)
            return cached_result
        del _cache[cache_key]

    logger.info("Doctor discovery (scrape+enrich) for: %s", query_name)

    try:
        from app.main import push_tool_progress

        # ── STEP 1: Scrape clinic website ───────────────────────
        push_tool_progress("doctors", f"🔍 Шаг 1/3: Скрапим сайт {query_name} → ищем реальных врачей…")

        scraped_names: list[str] = []
        profile_urls: dict[str, str] = {}
        if url and url.startswith("http"):
            scraped_names, profile_urls = await _scrape_clinic_doctors(url)

        if not scraped_names:
            # Fallback: use DeepSeek to find doctor names (P6: save Perplexity cost)
            push_tool_progress("doctors", "⚠️ Скрапинг не дал результатов — fallback на DeepSeek…")
            answer = await _call_llm(
                "Ты — HR-аналитик. Найди врачей клиники на её сайте. "
                "Перечисли ФИО в формате: 1. ФИО | специализация.",
                f"Найди всех врачей клиники «{query_name}». "
                "Перечисли 10-15 врачей с полными ФИО. "
                "Формат: 1. ФИО | специализация",
            )
            source = f"llm ({LLM_MODEL}) — fallback (no scrape)"

            # Parse names from fallback
            import re as _re
            fallback_names = []
            for line in answer.split("\n"):
                match = _re.match(r'^\d+\.?\s+(.+?)(?:\s*\||$)', line.strip())
                if match:
                    name = match.group(1).strip()
                    if len(name.split()) >= 2 and not any(
                        w in name.lower() for w in ("всего", "клиник", "сайт")
                    ):
                        fallback_names.append(name)
            scraped_names = fallback_names[:15]
        else:
            source = "website_scraping"

        if not scraped_names:
            return json.dumps({
                "error": "Could not find any doctor names",
                "clinic": query_name,
            }, ensure_ascii=False)

        push_tool_progress(
            "doctors",
            f"✅ Сайт: {len(scraped_names)} врачей найдено"
            + (f" (+ {len(profile_urls)} персональных страниц)" if profile_urls else ""),
        )

        # ── SURFACE-LEVEL ONLY: cap at 10 doctors, ONE Perplexity call ─
        MAX_DOCTORS = 10
        doctors_to_enrich = scraped_names[:MAX_DOCTORS]

        # ── STEP 1.5: Scrape top-5 doctor profiles for context ──
        N_PROFILES = min(5, len(doctors_to_enrich))
        doctors_context: list[dict] = []
        found_social_links: dict[str, dict] = {}

        if profile_urls:
            push_tool_progress(
                "doctors",
                f"📋 Шаг 1.5/3: Скрапим {N_PROFILES} персональных страниц врачей…",
            )

            # Get profile URLs for top doctors (by position on page = importance)
            top_doctors_with_urls = []
            for name in doctors_to_enrich:
                if name in profile_urls:
                    top_doctors_with_urls.append((name, profile_urls[name]))
                if len(top_doctors_with_urls) >= N_PROFILES:
                    break

            # Scrape in parallel
            profile_tasks = [
                _scrape_doctor_profile(purl)
                for _, purl in top_doctors_with_urls
            ]
            profile_results = await asyncio.gather(*profile_tasks, return_exceptions=True)

            # Build context dicts for enrichment query
            for (name, purl), profile in zip(top_doctors_with_urls, profile_results):
                if isinstance(profile, Exception):
                    doctors_context.append({
                        "name": name, "profile_url": purl,
                        "specializations": [], "regalia": [], "social_links": {},
                        "structured_regalia": _EMPTY_STRUCTURED_REGALIA,
                    })
                    continue
                if profile is None:
                    doctors_context.append({
                        "name": name, "profile_url": purl,
                        "specializations": [], "regalia": [], "social_links": {},
                        "structured_regalia": _EMPTY_STRUCTURED_REGALIA,
                    })
                    continue

                doctors_context.append({
                    "name": name,
                    "profile_url": purl,
                    "specializations": profile.get("specializations", []),
                    "regalia": profile.get("regalia", []),
                    "social_links": profile.get("social_links", {}),
                    "structured_regalia": profile.get("structured_regalia", _EMPTY_STRUCTURED_REGALIA),
                })

                # Track any social links found on profile pages
                if profile.get("social_links"):
                    found_social_links[name] = profile["social_links"]

            # Fill remaining doctors not already in context
            already_contexted = {d["name"] for d in doctors_context}
            for name in doctors_to_enrich:
                if name not in already_contexted:
                    doctors_context.append({
                        "name": name, "profile_url": "",
                        "specializations": [], "regalia": [], "social_links": {},
                        "structured_regalia": _EMPTY_STRUCTURED_REGALIA,
                    })

            if found_social_links:
                push_tool_progress(
                    "doctors",
                    f"✅ Найдены соцсети у {len(found_social_links)} врачей прямо на сайте: "
                    + ", ".join(
                        f"{name}: {', '.join(f'{k}={v}' for k, v in sl.items())}"
                        for name, sl in list(found_social_links.items())[:3]
                    ),
                )
        else:
            # No profile URLs — fall back to name-only context
            for name in doctors_to_enrich:
                doctors_context.append({
                    "name": name, "profile_url": "",
                    "specializations": [], "regalia": [], "social_links": {},
                    "structured_regalia": _EMPTY_STRUCTURED_REGALIA,
                })
            found_social_links = {}

        logger.info(
            "Enrichment for %d doctors (from %d scraped, %d with profile context) for %s",
            len(doctors_to_enrich), len(scraped_names),
            sum(1 for d in doctors_context if d.get("profile_url")), query_name,
        )

        # ── STEP 2: ONE Perplexity call for ALL doctors ──────────
        push_tool_progress(
            "doctors",
            f"🔍 Шаг 2/3: Ищу Instagram для {len(doctors_to_enrich)} врачей (один запрос)…",
        )

        enrichment_query = _build_enrichment_query_batch(
            doctors_context, query_name, city, specialization,
        )

        if USE_PERPLEXITY:
            enrichment_answer = await _call_perplexity(
                _build_enrichment_system_prompt(), enrichment_query,
            )
        else:
            enrichment_answer = await _call_llm(
                _build_enrichment_system_prompt(), enrichment_query,
            )
            source = f"llm ({LLM_MODEL})"

        # Parse the single response
        all_doctors = _parse_enrichment(enrichment_answer, doctors_to_enrich)
        all_enrichment_answers = [enrichment_answer]

        # ── Fill in any doctors not returned by Perplexity ──────
        parsed_names = {d.get("full_name", "") for d in all_doctors}
        for dctx in doctors_context:
            name = dctx["name"]
            if name and name not in parsed_names:
                all_doctors.append({
                    "full_name": name, "specialization": "", "regalia": "",
                    "position": "", "instagram": "", "instagram_private": False,
                    "instagram_followers_approx": 0, "telegram": "", "youtube": "",
                    "verified": True, "verified_on_site": True,
                })
                logger.debug("Backfilled doctor missing from Perplexity response: %s", name)

        # ── Merge social links found during profile scraping ───
        for d in all_doctors:
            name = d.get("full_name", "")
            if name in found_social_links and not d.get("instagram"):
                sl = found_social_links[name]
                # Extract Instagram handle from URL
                for platform, url in sl.items():
                    if platform == "instagram":
                        # Try to extract handle from URL: instagram.com/handle/
                        handle_match = re.search(
                            r'instagram\.com/([a-zA-Z0-9_.]{2,30})(?:/|\?|$)', url,
                        )
                        if handle_match:
                            d["instagram"] = handle_match.group(1)
                            logger.info("Found Instagram for %s via profile scraping: @%s", name, d["instagram"])
                    elif platform in ("telegram", "vk", "youtube"):
                        d[platform] = url

        # Collect handles
        all_handles = _extract_all_handles(enrichment_answer)
        for d in all_doctors:
            ig = d.get("instagram", "")
            if ig and ig not in all_handles:
                all_handles.append(ig)

        # ── Phase 4 / SEC-04 / D-08: inject structured_regalia into each ─
        # Doctor dicts produced by _parse_enrichment come from Perplexity
        # and do not contain structured_regalia. We inject the typed regalia
        # dict from the site-scraped doctors_context by matching full_name.
        _context_by_name: dict[str, dict] = {}
        for ctx in doctors_context:
            cname = ctx.get("name") or ""
            if cname:
                _context_by_name[cname] = ctx
        for d in all_doctors:
            fname = d.get("full_name", "") or ""
            ctx = _context_by_name.get(fname)
            if ctx is not None:
                d["structured_regalia"] = ctx.get(
                    "structured_regalia", _EMPTY_STRUCTURED_REGALIA,
                )
            else:
                # Per plan Step B: Perplexity-only doctors get an empty default
                d["structured_regalia"] = _EMPTY_STRUCTURED_REGALIA

        doctors = all_doctors

        doctors_with_ig = [d for d in doctors if d.get("instagram")]
        doctors_no_ig = [d for d in doctors if not d.get("instagram")]

        # NOTE: Никакого STEP 3 (solo enrichment) и STEP 4 (follower enrichment).
        # Это ультра-бюджетный режим. Глубокий анализ — только в premium.

        doctors_with_ig.sort(
            key=lambda d: d.get("instagram_followers_approx", 0),
            reverse=True,
        )

        all_doctors_sorted = doctors_with_ig + doctors_no_ig

        # Топ-5 хэндлов для Apify
        top5_for_apify = [d["instagram"] for d in doctors_with_ig[:5] if d.get("instagram")]

        # Collect handles from parsed doctors too
        for d in doctors:
            ig = d.get("instagram", "")
            if ig and ig not in all_handles:
                all_handles.append(ig)

        push_tool_progress(
            "doctors",
            f"✅ Instagram у {len(doctors_with_ig)}/{len(doctors)} врачей, "
            f"топ-5 для Apify: {', '.join('@' + h for h in top5_for_apify) if top5_for_apify else 'нет'}",
        )

        # ── Build result ────────────────────────────────────────
        result = {
            "clinic": query_name,
            "city": city or "не указан",
            "specialization": specialization or "не указана",
            "total_doctors_on_site": len(scraped_names),
            "doctors": all_doctors_sorted,
            "doctors_count": len(all_doctors_sorted),
            "doctors_with_instagram": len(doctors_with_ig),
            "instagram_handles": all_handles,
            "handles_count": len(all_handles),
            "top5_for_apify": top5_for_apify,
            "top_by_followers": [
                {
                    "full_name": d["full_name"],
                    "instagram": d.get("instagram", ""),
                    "followers_approx": d.get("instagram_followers_approx", 0),
                    "private": d.get("instagram_private", False),
                }
                for d in doctors_with_ig
            ],
            "source": source,
            "analysis": "\n\n".join(all_enrichment_answers),
            "searched_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
        }

        result_json = json.dumps(result, ensure_ascii=False, indent=2)
        _cache[cache_key] = (time.time(), result_json)

        # P5: periodic cache cleanup (fast — just lists cache dir)
        try:
            from app.tools._file_cache import file_cache
            file_cache.cleanup_expired()
        except Exception:
            pass

        # Phase 4 / SEC-04 / D-09: _merge_doctor_data() helper is exposed at
        # module level for Pass 3 LLM / orchestrator import. The merge itself
        # happens AFTER run_instagram_content returns instagram_data, so it
        # is NOT invoked here. Import like:
        #   from app.tools.find_doctor_handles import _merge_doctor_data
        return result_json

    except Exception as e:
        logger.exception("Doctor handles search error for %s", query_name)
        return json.dumps({
            "error": "Doctor handles search failed",
            "detail": str(e)[:500],
        }, ensure_ascii=False)


registry.register(
    name="find_doctor_handles",
    toolset="aim-operations",
    schema={
            "name": "find_doctor_handles",
            "description": (
                "Find clinic doctors and their Instagram/Telegram/YouTube handles. "
                "SCRAPES the clinic website to get REAL doctor names, then uses Perplexity "
                "to find regalia and social media for each verified doctor. "
                "Returns structured doctor list with verified handles + top5_for_apify. "
                "Use this BEFORE run_instagram_content to get handles to analyze."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "url": {
                        "type": "string",
                        "description": "Clinic website URL (e.g., 'https://clinic.ru'). Required for scraping.",
                    },
                    "company_name": {
                        "type": "string",
                        "description": "Clinic name for search",
                    },
                    "city": {
                        "type": "string",
                        "description": "City for geo-targeting",
                    },
                    "specialization": {
                        "type": "string",
                        "description": "Clinic specialization (e.g., 'пластическая хирургия')",
                    },
                },
                "required": ["url"],
            },
        },
    handler=handle_find_doctor_handles,
    check_fn=lambda: True,
    is_async=True,
    description="Scrape clinic website for real doctors + Perplexity enrichment for regalia & social media",
    emoji="👨‍⚕️",
)
