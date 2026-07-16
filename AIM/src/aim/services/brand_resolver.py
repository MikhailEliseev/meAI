"""Brand → INN resolver via bo.nalog.gov.ru.

Takes a brand name (e.g. "Seline", "Клазко", "GMTClinic") and resolves it
to a real legal entity (ИНН) using ФНС registry search, filtered by medical
OKVED codes and ranked by revenue.

This replaces the broken rusprofile-based _enrich_gm_via_inn (0/48 hit rate)
with a reliable bo.nalog.gov.ru lookup (validated on Фрау Клиник, Клазко, GMT).
"""

import asyncio
import logging
import os
import re
from dataclasses import dataclass, field
from typing import Optional

from src.aim.services.nalog import BfoNalogClient, get_nalog_client

logger = logging.getLogger(__name__)

# Medical OKVED prefixes — only return companies in healthcare
MEDICAL_OKVED_PREFIXES = ("86.",)

# Minimum INN length for a valid legal entity
_MIN_INN_LEN = 10

# ── Brand normalization ────────────────────────────────────────────────
# Regex patterns for geo-attachments and address suffixes to strip from
# brand names before resolving. Applied in order.
_GEO_STRIP_PATTERNS = [
    # "на Ленинском проспекте" / "на Тверской улице" / "на Кутузовском шоссе"
    re.compile(r"\s+на\s+[\w\s-]*(?:проспект[е]?|улиц[ае]?|шоссе|набережной|площади)\s*$", re.I),
    # "в Орловском переулке" / "в Столовом переулке"
    re.compile(r"\s+в\s+[\w\s-]*(?:переулке|проезде|тупике|аллее)\s*$", re.I),
    # "метро Таганская" / "м. Тверская"
    re.compile(r"\s+(?:метро|m\.?)\s+[\w-]+\s*$", re.I),
    # "г. Москва" / "город Москва"
    re.compile(r",?\s*(?:г\.|город)\s+[\w\s-]+\s*$", re.I),
    # "№ 5" / "№5"
    re.compile(r"\s+№\s*\d+\s*$", re.I),
    # "на Соколе" / "на Арбате" (short metro/area names — 1-2 words after "на")
    re.compile(r"\s+на\s+[\w]+\s*$", re.I),
]


def normalize_brand_name(brand: str) -> str:
    """Strip geo-attachments and address suffixes from a brand name.

    Perplexity and SearXNG sometimes return brand names with location
    qualifiers like "Медиал на Ленинском проспекте" or "ЕМС в Орловском
    переулке". These confuse bo.nalog search (finds small branch entities
    instead of the main legal entity).

    Args:
        brand: Raw brand name potentially containing geo-attachments.

    Returns:
        Cleaned brand name with geo-attachments removed.

    Examples:
        >>> normalize_brand_name("Медиал на Ленинском проспекте")
        'Медиал'
        >>> normalize_brand_name("ЕМС в Орловском переулке")
        'ЕМС'
        >>> normalize_brand_name("ОН Клиник на Таганке")
        'ОН Клиник'
        >>> normalize_brand_name("Клазко")
        'Клазко'
    """
    if not brand:
        return brand
    result = brand.strip()
    for pattern in _GEO_STRIP_PATTERNS:
        result = pattern.sub("", result).strip()
    return result if result else brand.strip()


@dataclass
class ResolvedBrand:
    """A brand resolved to a real legal entity in ФНС."""

    brand_query: str  # cleaned brand name (after normalization)
    inn: str
    org_id: int  # bo.nalog numeric ID for financials lookup
    legal_name: str
    okved: str
    latest_revenue: Optional[int]  # RUB (gainSum × 1000)
    status: str = ""
    address: str = ""
    brand_original: str = ""  # original brand before normalization (for logging)

    @property
    def is_medical(self) -> bool:
        return any(self.okved.startswith(p) for p in MEDICAL_OKVED_PREFIXES)


def _resolve_sync(
    nalog: BfoNalogClient,
    brand_name: str,
    okved_prefix: str,
    brand_original: str = "",
) -> Optional[ResolvedBrand]:
    """Synchronous resolution — called via asyncio.to_thread."""
    results = nalog.search(brand_name)
    if not results:
        return None

    # Filter by OKVED prefix (medical) if any match
    medical = [r for r in results if r.okved2 and r.okved2.startswith(okved_prefix)]
    pool = medical if medical else results

    # Score each candidate: name similarity to brand + revenue bonus.
    # This fixes "ЛАНЦЕТЪ" → wrong "ДЕЛАЙТ-ЛАНЦЕТЪ" (higher revenue but
    # different brand) and "СМ-Клиника" → correct ООО КЛИНИКА ЛК.
    brand_lower = brand_name.lower().strip()
    brand_words = set(brand_lower.split())

    def _score(r):
        name_lower = r.short_name.lower()
        # Exact match = highest priority
        if brand_lower in name_lower:
            return (3, r.latest_revenue or 0)
        # Word overlap (brand words in legal name)
        name_words = set(name_lower.split())
        overlap = len(brand_words & name_words)
        return (overlap, r.latest_revenue or 0)

    pool.sort(key=_score, reverse=True)

    best = pool[0]
    if not best.inn or len(best.inn) < _MIN_INN_LEN:
        return None

    # gainSum from bo.nalog is in thousands of rubles
    revenue_rub = best.latest_revenue * 1000 if best.latest_revenue else None

    return ResolvedBrand(
        brand_query=brand_name,
        inn=best.inn,
        org_id=best.id,
        legal_name=best.short_name,
        okved=best.okved2,
        latest_revenue=revenue_rub,
        status=best.status,
        address=best.address,
        brand_original=brand_original or brand_name,
    )


async def _resolve_bo_nalog_only(
    brand_name: str,
    okved_prefix: str = "86.",
    nalog: Optional[BfoNalogClient] = None,
) -> Optional[ResolvedBrand]:
    """Level 1 only: bo.nalog search по названию. Быстро, дёшево."""
    brand_original = brand_name
    brand_name = normalize_brand_name(brand_name)
    client = nalog or get_nalog_client()
    result = await asyncio.to_thread(_resolve_sync, client, brand_name, okved_prefix, brand_original)
    if result:
        logger.info("brand_resolved: brand=%s → inn=%s", brand_name, result.inn)
    return result


async def _resolve_with_fallbacks(
    brand_name: str,
    okved_prefix: str = "86.",
    nalog: Optional[BfoNalogClient] = None,
) -> Optional[ResolvedBrand]:
    """Level 2 + 3: website scrape + Perplexity. Медленно, дорого."""
    brand_original = brand_name
    brand_name = normalize_brand_name(brand_name)
    client = nalog or get_nalog_client()

    # Level 2: Firecrawl scrape сайта → ИНН
    result = await _resolve_via_website_scrape(brand_name, okved_prefix, client, brand_original)
    if result:
        logger.info("brand_resolved_website: brand=%s → inn=%s", brand_name, result.inn)
        return result

    # Level 3: Perplexity → ИНН
    result = await _resolve_via_perplexity(brand_name, okved_prefix, client, brand_original)
    if result:
        logger.info("brand_resolved_perplexity: brand=%s → inn=%s", brand_name, result.inn)
        return result

    logger.info("brand_not_found_in_fns: brand=%s", brand_name)
    return None


async def resolve_brand_to_inn(
    brand_name: str,
    okved_prefix: str = "86.",
    nalog: Optional[BfoNalogClient] = None,
    skip_normalize: bool = False,
) -> Optional[ResolvedBrand]:
    """Resolve a brand name to a legal entity (ИНН) via multi-level fallback.

    Pipeline:
      Level 0: Normalize brand name (strip geo-attachments)
      Level 1: bo.nalog search by brand name (exact match)
      Level 2: Firecrawl scrape website → ИНН from footer/policy → ФНС validate
      Level 3: Perplexity → ИНН → ФНС validate (last resort)

    Anti-hallucination: every level validates through ФНС. A brand that
    doesn't exist in ФНС returns None — filters out fabricated competitors.

    Args:
        brand_name: Brand name to resolve (e.g. "Клазко", "GMTClinic").
        okved_prefix: OKVED prefix to filter (default: "86." for medical).
        nalog: Optional BfoNalogClient instance (creates one if not provided).
        skip_normalize: If True, skip geo-attachment normalization.

    Returns:
        ResolvedBrand with INN and org_id, or None if not found in ФНС.
    """
    brand_original = brand_name
    if not skip_normalize:
        brand_name = normalize_brand_name(brand_name)
        if brand_name != brand_original:
            logger.info("brand_normalized: \"%s\" → \"%s\"", brand_original, brand_name)

    # Always use singleton — never close it (cache survives between requests)
    client = nalog or get_nalog_client()
    result = await asyncio.to_thread(_resolve_sync, client, brand_name, okved_prefix, brand_original)
    if result:
        logger.info(
            "brand_resolved: brand=%s → inn=%s okved=%s revenue=%s",
            brand_name, result.inn, result.okved,
            f"{result.latest_revenue:,}" if result.latest_revenue else "N/A",
        )
        return result

    # ── Level 2: Firecrawl scrape сайта → ИНН из подвала/политики ──
    result = await _resolve_via_website_scrape(brand_name, okved_prefix, client, brand_original)
    if result:
        logger.info(
            "brand_resolved_website: brand=%s → inn=%s okved=%s revenue=%s",
            brand_name, result.inn, result.okved,
            f"{result.latest_revenue:,}" if result.latest_revenue else "N/A",
        )
        return result

    # ── Level 3: Perplexity fallback (последний шанс) ──
    result = await _resolve_via_perplexity(brand_name, okved_prefix, client, brand_original)
    if result:
        logger.info(
            "brand_resolved_perplexity: brand=%s → inn=%s okved=%s revenue=%s",
            brand_name, result.inn, result.okved,
            f"{result.latest_revenue:,}" if result.latest_revenue else "N/A",
        )
        return result

    logger.info("brand_not_found_in_fns: brand=%s", brand_name)
    return None


async def _resolve_via_website_scrape(
    brand_name: str,
    okved_prefix: str,
    client: "BfoNalogClient",
    brand_original: str,
) -> Optional[ResolvedBrand]:
    """Firecrawl scrape сайта клиники → извлечение ИНН → ФНС валидация.

    ИНН на сайтах клиник находится:
    - В подвале (footer) главной страницы
    - В политике конфиденциальности (152-ФЗ требует)
    - В странице "Контакты" / "Реквизиты"

    Args:
        brand_name: Название бренда (для построения URL).
    Returns:
        ResolvedBrand или None.
    """
    # Шаг 1: найти URL сайта через Perplexity (быстрый поиск)
    website_url = await _find_brand_website(brand_name)
    if not website_url:
        return None

    # Шаг 2: скрапить сайт → найти ИНН (с aggregate timeout 20s)
    try:
        inn = await asyncio.wait_for(_scrape_inn_from_website(website_url), timeout=20)
    except asyncio.TimeoutError:
        logger.debug("Website INN scrape timed out for %s", website_url[:40])
        return None
    if not inn:
        return None

    # Шаг 3: валидация через ФНС
    return await _validate_inn_in_fns(inn, okved_prefix, client, brand_original)


async def _find_brand_website(brand_name: str) -> Optional[str]:
    """Находит сайт клиники через Perplexity."""
    try:
        from src.aim.services.lib.perplexity_client import perplexity_chat, is_configured as perplexity_configured
    except ImportError:
        return None
    if not perplexity_configured():
        return None
    try:
        raw = await perplexity_chat(
            [{"role": "user", "content": f"Официальный сайт клиники \"{brand_name}\" Москва. Верни ТОЛЬКО URL."}],
            temperature=0.0,
        )
        # Extract URL
        url_match = re.search(r"https?://[^\s<>\"]+", raw.strip())
        if url_match:
            url = url_match.group(0).rstrip(".,;)")
            # Базовый домен (без пути)
            from urllib.parse import urlparse
            parsed = urlparse(url)
            return f"{parsed.scheme}://{parsed.netloc}"
    except Exception:
        pass
    return None


async def _scrape_inn_from_website(website_url: str) -> Optional[str]:
    """Скрапит сайт → находит ИНН в подвале или политике конфиденциальности.

    Алгоритм:
    1. Скрапить главную → regex ИНН
    2. Если нет → найти ссылку на политику → скрапить её
    3. Если нет → попробовать /policy, /privacy, /kontakty, /o-klinike
    """
    import httpx  # lazy import

    # Загружаем Firecrawl ключи
    fc_key = _get_firecrawl_key()
    if not fc_key:
        return None

    inn_patterns = [
        re.compile(r"[Ии][Нн][Нн][^0-9]*?(\d{10})"),  # ИНН 1234567890
        re.compile(r"INN[^0-9]*?(\d{10})", re.I),       # INN: 1234567890
    ]

    async with httpx.AsyncClient(timeout=15) as http:  # 15s per-request, 20s aggregate
        # Стратегические URL для проверки
        candidate_urls = [website_url]  # главная

        # Шаг 1: скрапить главную, найти ссылки на политику/реквизиты
        try:
            r = await http.post("https://api.firecrawl.dev/v1/scrape",
                headers={"Authorization": f"Bearer {fc_key}", "Content-Type": "application/json"},
                json={"url": website_url, "formats": ["markdown"], "onlyMainContent": False, "waitFor": 3000})
            if r.status_code == 200:
                md = r.json().get("data", {}).get("markdown", "")
                # ИНН на главной?
                for pat in inn_patterns:
                    m = pat.search(md)
                    if m:
                        return m.group(1)

                # Найти ссылки на политику/реквизиты
                from urllib.parse import urljoin
                md_links = re.findall(r'\[([^\]]+)\]\(([^)]+)\)', md)
                policy_keywords = ["политик", "policy", "privacy", "konfidenc",
                                   "соглаш", "лиценз", "licens", "rekviz", "контакт",
                                   "контакты", "about", "о клинике", "о нас"]
                for text, href in md_links:
                    if any(k in (text + href).lower() for k in policy_keywords):
                        full_url = urljoin(website_url, href)
                        if full_url not in candidate_urls:
                            candidate_urls.append(full_url)
        except Exception:
            pass

        # Стандартные пути если не нашли ссылки
        for path in ["/policy", "/privacy", "/kontakty", "/o-klinike", "/about", "/requisites"]:
            candidate_urls.append(website_url.rstrip("/") + path)

        # Шаг 2: скрапить каждую кандидатную страницу (максимум 3 — экономия ключей)
        for curl in candidate_urls[1:4]:  # пропускаем главную (уже проверили)
            try:
                r = await http.post("https://api.firecrawl.dev/v1/scrape",
                    headers={"Authorization": f"Bearer {fc_key}", "Content-Type": "application/json"},
                    json={"url": curl, "formats": ["markdown"], "onlyMainContent": False})
                if r.status_code == 200:
                    md = r.json().get("data", {}).get("markdown", "")
                    for pat in inn_patterns:
                        m = pat.search(md)
                        if m:
                            return m.group(1)
            except Exception:
                continue

    return None


def _get_firecrawl_key() -> Optional[str]:
    """Возвращает первый доступный Firecrawl ключ."""
    for prefix in ("FIRECRAWL_API_KEY_", "FIRECRAWL_KEY_"):
        for i in range(1, 21):
            k = os.getenv(f"{prefix}{i:02d}", "") or os.getenv(f"{prefix}{i}", "")
            if k:
                return k
    k = os.getenv("FIRECRAWL_API_KEY", "")
    return k if k else None


async def _validate_inn_in_fns(
    inn: str,
    okved_prefix: str,
    client: "BfoNalogClient",
    brand_original: str,
) -> Optional[ResolvedBrand]:
    """Валидирует ИНН через bo.nalog → ResolvedBrand если ОК."""
    try:
        search_results = await asyncio.to_thread(client.search, inn)
        if not search_results:
            return None
        org = search_results[0]
        if okved_prefix and okved_prefix not in (org.okved2 or ""):
            return None
        statements = await asyncio.to_thread(client.get_financials, org.id)
        latest_rev = statements[0].revenue_rub if statements else None
        return ResolvedBrand(
            inn=org.inn, org_id=org.id, legal_name=org.short_name,
            brand_query=brand_original, okved=org.okved2,
            latest_revenue=latest_rev, status="resolved_website",
            address=org.address,
        )
    except Exception:
        return None


async def _resolve_via_perplexity(
    brand_name: str,
    okved_prefix: str,
    client: "BfoNalogClient",
    brand_original: str,
) -> Optional[ResolvedBrand]:
    """Perplexity fallback для brand resolution."""
    try:
        from src.aim.services.lib.perplexity_client import perplexity_chat, is_configured as perplexity_configured
    except ImportError:
        return None

    if not perplexity_configured():
        return None

    try:
        prompt = (
            f"Найди ИНН медицинской клиники: \"{brand_name}\". "
            "Верни ТОЛЬКО число (10 цифр). Без пояснений."
        )
        raw = await perplexity_chat(
            [{"role": "user", "content": prompt}],
            temperature=0.0,
        )
        # Извлекаем ИНН (10 цифр)
        inn_match = re.findall(r"\b(\d{10})\b", raw.strip())
        if not inn_match:
            return None

        inn = inn_match[0]

        # Валидация: ищем этот ИНН в bo.nalog
        search_results = await asyncio.to_thread(client.search, inn)
        if not search_results:
            return None

        org = search_results[0]
        # Проверка ОКВЭД
        if okved_prefix and okved_prefix not in (org.okved2 or ""):
            return None

        # Получаем финансы
        statements = await asyncio.to_thread(client.get_financials, org.id)
        latest_rev = statements[0].revenue_rub if statements else None

        return ResolvedBrand(
            inn=org.inn,
            org_id=org.id,
            legal_name=org.short_name,
            brand_query=brand_original,
            okved=org.okved2,
            latest_revenue=latest_rev,
            status="resolved_perplexity",
            address=org.address,
        )
    except Exception as e:
        logger.debug("Perplexity brand resolution failed for %s: %s", brand_name, str(e)[:80])
        return None


async def resolve_brands_batch(
    brand_names: list[str],
    okved_prefix: str = "86.",
    max_concurrent: int = 5,  # deprecated, now hardcoded to 15
    max_brands: int = 40,  # NEW: only resolve first N brands
) -> list[Optional[ResolvedBrand]]:
    """Resolve multiple brands to INNs concurrently.

    Each brand is normalized (geo-attachments stripped) before resolving.
    Uses a single shared BfoNalogClient (its internal rate limiter handles
    concurrency at 5 req/s). Results are in the same order as input.

    Args:
        brand_names: List of brand names to resolve.
        okved_prefix: OKVED prefix filter.
        max_concurrent: DEPRECATED — ignored, semaphore=15 hardcoded.
        max_brands: Maximum brands to resolve (truncates list).

    Returns:
        List of ResolvedBrand or None, same order as input (truncated to max_brands).
    """
    # Truncate to max_brands budget
    brand_names = brand_names[:max_brands]
    
    nalog = get_nalog_client()  # singleton — cache survives, do NOT close
    semaphore = asyncio.Semaphore(15)  # Increased from 5 — bo.nalog can handle higher concurrency
    website_scrape_budget = 5  # максимум брендов для Level 2 (Firecrawl scrape)
    website_scrape_used = 0

    async def _semaphored(brand: str) -> Optional[ResolvedBrand]:
        nonlocal website_scrape_used
        async with semaphore:
            # Level 1: bo.nalog (быстро, дёшево)
            result = await _resolve_bo_nalog_only(brand, okved_prefix, nalog)
            if result:
                return result
            # Level 2 + 3 только если бюджет позволяет
            if website_scrape_used >= website_scrape_budget:
                logger.debug("brand_resolver: website scrape budget exhausted, skipping %s", brand[:25])
                return None
            website_scrape_used += 1
            return await _resolve_with_fallbacks(brand, okved_prefix, nalog)

    results = await asyncio.gather(
        *[_semaphored(b) for b in brand_names],
        return_exceptions=True,
    )

    # Convert exceptions to None
    return [r if isinstance(r, ResolvedBrand) else None for r in results]

