"""Competitor matching algorithm — finds top-3 competitors for a client clinic.

CRITICAL: We work ONLY in commercial medicine. Municipal, state, and
budgetary healthcare institutions (ГАУЗ, ГБУЗ, городские поликлиники,
районные больницы, etc.) are filtered out at discovery time.

Scores candidates by:
  service_overlap     (0.12) — same services (Jaccard)
  specialization_purity (0.15) — mono vs multi-profile matching
  popularity          (0.18) — ratings + reviews (real-world presence)
  location_score      (0.15) — nearby (≤50 km)
  revenue_match       (0.10) — similar scale
  visibility          (0.12) — search presence + maps listing
  data_quality        (0.18) — real financials > estimates

Discovery pipeline (Apify-first):
  1. Apify Google Maps — finds competitors by specialization + city
     Returns: name, website, rating, reviews, coordinates, social links
  2. DaData — enriches Google Maps results with INN + financial estimates
     (NO LONGER used for primary competitor discovery)
  3. rusprofile — real tax-filed financials for INN-carrying competitors
  4. Direct scraping — extracts real services from competitor websites
"""

import asyncio
import logging
import math
import os
import re
import time
from typing import Optional

import httpx

from .apify_google_maps import discover_competitors_google_maps
from . import get_apify_client
from .rusprofile.client import DaDataClient, get_dadata_client
from .rusprofile.models import ClientProfile, CompanyProfile, CompetitorMatch
from .scraping_service import scrape_services_batch
from .service_extractor import extract_client_profile

logger = logging.getLogger(__name__)

# ── Megalopolis cities ──────────────────────────────────────────────
# Auto-discovery (OSM Overpass + Yandex Maps) is unreliable for these cities
# because the 15km radius contains too many datapoints. Skip open-data
# discovery and ask the user for named competitors instead.

MEGAPOLIS_CITIES: set[str] = {
    "Москва", "Санкт-Петербург", "СПб",
}


def is_megalopolis(city: str) -> bool:
    """Check if city is too large for reliable open-data competitor discovery."""
    if not city:
        return False
    city_clean = city.strip().removeprefix("г ").removeprefix("г. ")
    for mc in MEGAPOLIS_CITIES:
        if mc.lower() in city_clean.lower():
            return True
    return False


# ── Blacklist ───────────────────────────────────────────────────────
# Comma-separated company names that should NEVER appear as competitors.
# These are typically the user's own projects/clients.
_BLACKLIST_NAMES: set[str] = set()
_bl = os.environ.get("COMPETITOR_BLACKLIST_NAMES", "")
if _bl:
    _BLACKLIST_NAMES = {n.strip().lower() for n in _bl.split(",") if n.strip()}
    logger.info("Competitor blacklist loaded: %d names", len(_BLACKLIST_NAMES))

# ── Scoring weights ────────────────────────────────────────────────
# Location is dominant for medical clinics — patients don't travel far.
# MAX_DISTANCE_KM = 7 km: beyond this, location_score drops to 0.
# For dental/cosmetic clinics, patients rarely go beyond their district.
W_REVENUE = 0.10
W_LOCATION = 0.15
W_SERVICES = 0.12
W_SPECIALIZATION = 0.15
W_DATA = 0.18
W_POPULARITY = 0.18
W_VISIBILITY = 0.12

MAX_DISTANCE_KM = 7.0  # beyond this, location_score = 0

# Revenue fallback by specialization (RUB/year), used when both DaData
# and client website lack financial data.
SPECIALIZATION_REVENUE = {
    "стоматология": 30_000_000,
    "косметология": 20_000_000,
    "многопрофильная клиника": 60_000_000,
    "пластическая хирургия": 80_000_000,
    "диагностический центр": 100_000_000,
    "офтальмология": 40_000_000,
    "педиатрия": 25_000_000,
}


def _searchable_name(profile: CompanyProfile) -> str:
    """Return the best name for web search — short brand name, not legal entity.

    "ОБЩЕСТВО С ОГРАНИЧЕННОЙ ОТВЕТСТВЕННОСТЬЮ СТОМАТОЛОГИЯ" → "Стоматология"
    "ООО СТОМАТОЛОГИЯ Н ДЕНТ" → "Стоматология Н Дент"
    """
    # Prefer brand_name if it's meaningfully different from legal_name
    name = profile.legal_name or ""
    if profile.brand_name and len(profile.brand_name) >= 3:
        name = profile.brand_name

    # Strip legal-form prefixes
    for prefix in (
        "общество с ограниченной ответственностью",
        "obschestvo s ogranichennoy otvetstvennostyu",
        "публичное акционерное общество",
        "непубличное акционерное общество",
        "акционерное общество",
        "индивидуальный предприниматель",
        "ооо", "ooo", "ао", "ao", "зао", "zao", "ип", "ip",
        "пао", "pao", "нао", "nao",
    ):
        if name.lower().startswith(prefix):
            name = name[len(prefix):]
            break

    # Clean up: remove leading/trailing quotes, whitespace, punctuation
    name = name.strip().strip('«»"\'')
    return name.strip() or profile.legal_name


class CompetitorMatcher:
    """Find and score competitors for a client clinic."""

    def __init__(self, dadata: DaDataClient | None = None):
        self.dadata = dadata or get_dadata_client()
        self._inn_browser = None
        self._inn_playwright = None
        self._inn_lock = None
        self.last_is_megalopolis = False

    async def close(self):
        """Clean up Playwright browser and other resources."""
        if self._inn_browser:
            try:
                await self._inn_browser.close()
            except Exception:
                pass
            self._inn_browser = None
        if self._inn_playwright:
            try:
                await self._inn_playwright.stop()
            except Exception:
                pass
            self._inn_playwright = None

    # ── Main entry point ───────────────────────────────────────────

    async def find_competitors(
        self,
        url: str,
        count: int = 3,
        named_competitors: Optional[list[str]] = None,
    ) -> list[CompetitorMatch]:
        """Find top-N competitors for a clinic website.

        Apify-first pipeline:
          1. Extract client profile (specialization, city, services)
          2. Apify Google Maps → discover competitors (name, website, rating, coords)
          3. Geocode client city center
          4. DaData enrichment → INN + legal data for Google Maps candidates
          5. Scrape real services from competitor websites
          6. rusprofile → real tax-filed financials
          7. Score and return top-N
        """
        t0 = time.monotonic()

        # 1. Extract client profile from website
        raw = await extract_client_profile(url)
        t_extract = time.monotonic()
        client = ClientProfile(
            url=url,
            specialization=raw["specialization"],
            city=raw["city"],
            services=raw["services"],
            company_name=raw.get("company_name"),
            estimated_revenue=SPECIALIZATION_REVENUE.get(
                raw["specialization"], 30_000_000
            ),
        )
        logger.info("CompetitorMatcher: client profile — %s", client)

        # Geocode client city center
        if client.city:
            coords = await self._geocode_city(client.city)
            if coords:
                client.city_lat, client.city_lon = coords
                logger.info(
                    "CompetitorMatcher: city center %s = (%.4f, %.4f)",
                    client.city, client.city_lat, client.city_lon,
                )

        t_geocode = time.monotonic()
        logger.info(
            "CompetitorMatcher: extract_profile=%.1fs, geocode=%.1fs",
            t_extract - t0, t_geocode - t_extract,
        )

        if not client.specialization or not client.city:
            logger.error("CompetitorMatcher: missing specialization or city — cannot search")
            return []

        # 2. Apify Google Maps — primary competitor discovery
        self.last_is_megalopolis = is_megalopolis(client.city or "")
        gm_candidates = await discover_competitors_google_maps(
            specialization=client.specialization,
            city=client.city,
            count=50,
            client=get_apify_client(),
        )
        t_discovery = time.monotonic()
        logger.info(
            "CompetitorMatcher: google_maps=%.1fs (%d candidates)",
            t_discovery - t_geocode, len(gm_candidates),
        )

        # Filter out client's own company
        gm_candidates = [
            c for c in gm_candidates
            if not (client.company_name and client.company_name.lower() in c.legal_name.lower())
        ]

        # 3. Enrich Google Maps candidates with DaData (INN + financials)
        if gm_candidates:
            gm_candidates = await self._enrich_gm_with_dadata(gm_candidates, client)
        t_dadata = time.monotonic()
        logger.info(
            "CompetitorMatcher: dadata_enrich=%.1fs",
            t_dadata - t_discovery,
        )

        # 3.5. Merge named competitors
        if named_competitors:
            named_profiles = await self._lookup_named_competitors(named_competitors, client)
            gm_candidates = gm_candidates + named_profiles

        # 4. Merge duplicates (same name/INN)
        candidates = self._dedup_candidates(gm_candidates)

        # 5. Filter state healthcare
        candidates = [c for c in candidates if not _is_state_healthcare(c.legal_name)]
        if _BLACKLIST_NAMES:
            candidates = [
                c for c in candidates
                if c.legal_name.lower() not in _BLACKLIST_NAMES
            ]

        # 6. Hard distance filter
        HARD_DISTANCE_KM = 15.0
        if client.city_lat and client.city_lon:
            filtered: list[CompanyProfile] = []
            for c in candidates:
                if c.geo_lat is not None and c.geo_lon is not None:
                    d = _haversine(client.city_lat, client.city_lon, c.geo_lat, c.geo_lon)
                    if d > HARD_DISTANCE_KM:
                        continue
                filtered.append(c)
            removed = len(candidates) - len(filtered)
            if removed:
                logger.info("CompetitorMatcher: distance filter removed %d candidates > %.0f km", removed, HARD_DISTANCE_KM)
            candidates = filtered

        if not candidates:
            logger.warning("CompetitorMatcher: no candidates found for %s", url)
            return []

        # 7. Scrape real services from competitor websites
        websites = [c.website for c in candidates if c.website and not c.scraped_services]
        if websites:
            t_scrape_start = time.monotonic()
            scraped = await scrape_services_batch(websites[:8], max_concurrent=5)
            for c in candidates:
                if c.website and c.website in scraped:
                    c.scraped_services = scraped[c.website]
            t_scrape = time.monotonic()
            hits = sum(1 for c in candidates if c.scraped_services)
            if hits:
                logger.info("CompetitorMatcher: scraped services for %d/%d candidates in %.1fs", hits, len(websites[:8]), t_scrape - t_scrape_start)

        # 8. Extract INN from competitor websites
        no_inn = [c for c in candidates if c.website and not (c.inn and c.inn.isdigit())]
        if no_inn:
            t_inn_start = time.monotonic()
            inn_extracted = await self._extract_inn_from_websites(no_inn)
            if inn_extracted:
                logger.info("CompetitorMatcher: extracted INN from %d websites in %.1fs", inn_extracted, time.monotonic() - t_inn_start)

        # 9. rusprofile enrichment
        inn_batch = [c for c in candidates if c.inn and c.inn.isdigit()][:10]
        if inn_batch:
            t_enrich_start = time.monotonic()
            enriched_count = await self._enrich_with_rusprofile(inn_batch)
            if enriched_count:
                logger.info("CompetitorMatcher: rusprofile enriched %d/%d in %.1fs", enriched_count, len(inn_batch), time.monotonic() - t_enrich_start)

        # 10. Score and rank
        scored = await self._score_candidates(client, candidates, count)

        # 11. Source diversity — ensure INN and real financials in top-N
        top = scored[:count]
        has_inn = any(m.profile.inn and m.profile.inn.strip() for m in top)
        if not has_inn:
            inn_candidates = [
                m for m in scored
                if m.profile.inn and m.profile.inn.strip() and m not in top
            ]
            if inn_candidates:
                inn_best = max(inn_candidates, key=lambda m: m.total_score)
                weakest = min(top, key=lambda m: (1 if m.website else 0, m.total_score))
                top.remove(weakest)
                top.append(inn_best)
                top.sort(key=lambda m: m.total_score, reverse=True)
                logger.info("CompetitorMatcher: diversity swap (INN) — replaced %s with %s", weakest.profile.legal_name[:30], inn_best.profile.legal_name[:30])

        has_real_fin = any(
            m.profile.has_real_financials() and m.profile.data_source == "rusprofile"
            for m in top
        )
        if not has_real_fin:
            rp_candidates = [
                m for m in scored
                if m.profile.has_real_financials()
                and m.profile.data_source == "rusprofile"
                and m not in top
            ]
            if rp_candidates:
                rp_best = max(rp_candidates, key=lambda m: m.total_score)
                weakest = min(top, key=lambda m: (
                    m.total_score - 0.1 * bool(not m.profile.inn) - 0.05 * bool(not m.profile.has_real_financials())
                ))
                top.remove(weakest)
                top.append(rp_best)
                top.sort(key=lambda m: m.total_score, reverse=True)
                logger.info("CompetitorMatcher: diversity swap (rusprofile) — replaced %s with %s", weakest.profile.legal_name[:30], rp_best.profile.legal_name[:30])
        scored = top

        t_total = time.monotonic()
        logger.info("CompetitorMatcher: total=%.1fs (extract=%.1fs geocode=%.1fs gm=%.1fs dadata=%.1fs)", t_total - t0, t_extract - t0, t_geocode - t_extract, t_discovery - t_geocode, t_dadata - t_discovery)

        return scored

    # ── Candidate discovery ────────────────────────────────────────

    async def _geocode_city(self, city: str) -> tuple[float, float] | None:
        """Geocode city name to coordinates via Nominatim."""
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.get(
                    self._NOMINATIM_URL,
                    params={"q": f"{city}, Россия", "format": "json", "limit": 1},
                    headers={"User-Agent": "AIM-CompetitorDiscovery/2.0 (me@iamaim.ru)"},
                )
                resp.raise_for_status()
                data = resp.json()
                if data:
                    return float(data[0]["lat"]), float(data[0]["lon"])
        except Exception as e:
            logger.warning("Geocode failed for city %s: %s", city, e)
        return None

    async def _enrich_gm_with_dadata(
        self, gm_candidates: list[CompanyProfile], client: ClientProfile
    ) -> list[CompanyProfile]:
        """Enrich Google Maps candidates with DaData (INN + legal data + financials).

        Matches Google Maps names to DaData legal entities by name similarity.
        DaData is used ONLY for enrichment here — not for primary discovery.
        """
        enriched: list[CompanyProfile] = []

        async def _enrich_one(c: CompanyProfile) -> CompanyProfile:
            name = c.legal_name
            if not name:
                return c

            # Extract first 1-2 words as brand core for DaData search
            words = name.split()
            brand_core = " ".join(words[:2]) if len(words) >= 2 else words[0]

            try:
                results = await self.dadata.find_medical_companies(
                    query=brand_core,
                    city=client.city,
                    count=3,
                )
            except Exception as e:
                logger.debug("DaData lookup failed for %s: %s", brand_core, e)
                return c

            for r in results:
                if _name_similarity(name, r.legal_name) > 0.3:
                    # Transfer DaData enrichment to Google Maps profile
                    if not c.inn and r.inn:
                        c.inn = r.inn
                    if not c.ogrn and r.ogrn:
                        c.ogrn = r.ogrn
                    if not c.okved_main and r.okved_main:
                        c.okved_main = r.okved_main
                    if not c.okved_secondary and r.okved_secondary:
                        c.okved_secondary = r.okved_secondary
                    if not c.legal_address and r.legal_address:
                        c.legal_address = r.legal_address
                    if not c.employee_count and r.employee_count:
                        c.employee_count = r.employee_count
                    if not c.revenue_year and r.revenue_year:
                        c.revenue_year = r.revenue_year
                        c.profit_year = r.profit_year
                        c.financial_year = r.financial_year
                    # Keep Google Maps digital presence (website, social, rating)
                    c.website = c.website or r.website
                    if not c.social_links and r.social_links:
                        c.social_links = r.social_links
                    # Tag as enriched
                    c.data_source = "apify_google_maps+dadata"
                    c.source_specialization = client.specialization
                    break

            return c

        # DaData lookup in parallel (was sequential)
        tasks = [_enrich_one(c) for c in gm_candidates[:30]]
        enriched = await asyncio.gather(*tasks)

        # Tag remaining (non-enriched) with specialization
        for c in enriched:
            if not c.source_specialization:
                c.source_specialization = client.specialization

        return list(enriched)

    async def _lookup_named_competitors(
        self, named_competitors: list[str], client: ClientProfile
    ) -> list[CompanyProfile]:
        """Look up named competitors via DaData by name or URL."""
        named_profiles: list[CompanyProfile] = []
        for name in named_competitors:
            raw_input = name.strip()
            is_url = raw_input.startswith("http")
            if is_url:
                clean_name = raw_input.split("//")[-1].split("/")[0]
                clean_name = clean_name.removeprefix("www.")
            else:
                clean_name = raw_input

            profiles = await self.dadata.search_company(clean_name, count=3)
            if profiles:
                for p in profiles:
                    p._named_competitor = True
                    if is_url:
                        p.website = p.website or raw_input
                    p.source_specialization = client.specialization
                named_profiles.extend(profiles)
                logger.info("CompetitorMatcher: named '%s' → %d DaData matches", clean_name, len(profiles))
        return named_profiles

    @staticmethod
    def _dedup_candidates(candidates: list[CompanyProfile]) -> list[CompanyProfile]:
        """Deduplicate candidates by INN first, then name similarity."""
        merged: dict[str, CompanyProfile] = {}
        for p in candidates:
            key = p.inn if p.inn else p.legal_name.lower()
            if key in merged:
                existing = merged[key]
                # Merge: keep best of each field
                existing.website = existing.website or p.website
                if not existing.social_links and p.social_links:
                    existing.social_links = p.social_links
                if existing.rating is None and p.rating is not None:
                    existing.rating = p.rating
                if existing.reviews_count is None and p.reviews_count is not None:
                    existing.reviews_count = p.reviews_count
                if not existing.inn and p.inn:
                    existing.inn = p.inn
                if not existing.revenue_year and p.revenue_year:
                    existing.revenue_year = p.revenue_year
                existing.confidence = max(existing.confidence, p.confidence)
                continue
            merged[key] = p
        return list(merged.values())

    # ── Geocoding ──────────────────────────────────────────────────

    _NOMINATIM_URL = "https://nominatim.openstreetmap.org/search"

    @staticmethod
    def _normalize_address_for_nominatim(addr: str) -> str:
        """Strip Russian address abbreviations that Nominatim doesn't parse.

        "г Москва, ул Раевского, д 3, стр 1, кв 85" → "Москва, Раевского, 3"
        """
        import re as _re_addr

        # Remove city prefix: "г Москва" → "Москва"
        addr = _re_addr.sub(r"^г\.?\s+", "", addr)

        # Remove district/subcity prefixes that Nominatim chokes on
        addr = _re_addr.sub(r",?\s*р-н\s+\S+", "", addr)

        # Remove street-type words: "ул Раевского" → "Раевского"
        addr = _re_addr.sub(
            r"(?:улица|ул|проспект|пр-т|проезд|пр-д|переулок|пер|"
            r"площадь|пл|набережная|наб|бульвар|бул|б-р|шоссе|ш|"
            r"микрорайон|мкр)\.?\s+",
            "", addr,
        )

        # Remove "д N" (house marker) — keep just the number
        addr = _re_addr.sub(r"д\.?\s*", "", addr)

        # Remove everything after house number that's not useful for geocoding:
        # "стр N", "к N", "корп N", "кв N", "оф N", "пом N"
        addr = _re_addr.sub(
            r",?\s*(?:стр|с|корп|к|кв|оф|офис|пом|помещение)\.?\s*\d+[а-яА-Я]?",
            "", addr,
        )

        # Clean up: collapse multiple commas/spaces
        addr = _re_addr.sub(r"\s*,\s*", ", ", addr)
        addr = _re_addr.sub(r"\s+", " ", addr).strip(", ")
        return addr

    # ── INN extraction from websites ──────────────────────────────────

    _INN_RE = re.compile(
        r'(?:ИНН|INN|инн|inn)\s*[:;]?\s*(\d{10,12})',
        re.IGNORECASE,
    )
    # Pages likely to contain INN
    _INN_PATHS = [
        "", "/about", "/contacts", "/kontakty", "/kontakti",
        "/about-us", "/o-klinike", "/o-nas", "/license", "/licenses",
        "/docs", "/documents", "/rekvizity", "/requisites",
    ]

    async def _extract_inn_from_websites(
        self, candidates: list[CompanyProfile]
    ) -> int:
        """Try to extract INN from competitor websites.

        Russian medical organizations are legally required to display ИНН
        on their websites (footer, contacts, or about page).

        Two-tier approach:
          1. Static HTTP GET (fast — works for server-rendered sites)
          2. Playwright headless browser (slow — for JS-rendered sites)
        """
        extracted = 0
        still_missing: list[CompanyProfile] = []

        # ── Tier 1: Static HTTP (fast path) ────────────────────────
        async with httpx.AsyncClient(
            timeout=httpx.Timeout(8.0),
            follow_redirects=True,
            verify=False,
        ) as client:
            for c in candidates:
                if c.inn and c.inn.isdigit():
                    continue
                try:
                    inn = await self._extract_inn_from_one_site(client, c.website)
                    if inn:
                        c.inn = inn
                        extracted += 1
                        logger.debug("INN extracted (static): %s from %s", inn, c.website)
                    else:
                        still_missing.append(c)
                except Exception:
                    still_missing.append(c)

        # ── Tier 2: Playwright for JS-rendered sites ───────────────
        if still_missing:
            # Limit Playwright to 3 candidates (headless browser is expensive)
            pw_batch = still_missing[:3]
            try:
                browser = await self._ensure_inn_browser()
                for c in pw_batch:
                    try:
                        inn = await self._extract_inn_with_playwright(browser, c.website)
                        if inn:
                            c.inn = inn
                            extracted += 1
                            logger.debug("INN extracted (playwright): %s from %s", inn, c.website)
                    except Exception:
                        continue
            except Exception as e:
                logger.warning("INN Playwright extraction failed: %s", e)

        return extracted

    async def _ensure_inn_browser(self):
        """Lazily start Playwright browser for INN extraction."""
        if self._inn_browser is not None:
            return self._inn_browser

        if self._inn_lock is None:
            self._inn_lock = asyncio.Lock()

        async with self._inn_lock:
            if self._inn_browser is not None:
                return self._inn_browser

            from playwright.async_api import async_playwright

            self._inn_playwright = await async_playwright().start()
            self._inn_browser = await self._inn_playwright.chromium.launch(
                headless=True,
                args=[
                    "--no-sandbox",
                    "--disable-setuid-sandbox",
                    "--disable-dev-shm-usage",
                    "--disable-gpu",
                    "--disable-blink-features=AutomationControlled",
                ],
            )
            logger.info("CompetitorMatcher: Playwright browser started for INN extraction")
            return self._inn_browser

    async def _extract_inn_with_playwright(self, browser, base_url: str) -> Optional[str]:
        """Extract INN from a JS-rendered website using Playwright.

        Loads the homepage and checks for INN in the rendered DOM text.
        Also tries /contacts and /about pages if homepage yields nothing.
        """
        from urllib.parse import urljoin

        context = await browser.new_context(
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/131.0.0.0 Safari/537.36"
            ),
            locale="ru-RU",
        )

        try:
            for path in self._INN_PATHS[:3]:  # homepage, /contacts, /about
                url = urljoin(base_url, path)
                page = await context.new_page()
                try:
                    await page.goto(url, wait_until="domcontentloaded", timeout=15000)
                    # Wait a moment for JS to render
                    try:
                        await page.wait_for_timeout(2000)
                    except Exception:
                        pass

                    text = await page.inner_text("body")
                    for m in self._INN_RE.finditer(text):
                        raw_inn = m.group(1)
                        if self._is_valid_inn(raw_inn):
                            return raw_inn

                except Exception:
                    if path == "":
                        return None
                    continue
                finally:
                    await page.close()

        finally:
            await context.close()

        return None

    async def _extract_inn_from_one_site(
        self, client: httpx.AsyncClient, base_url: str
    ) -> Optional[str]:
        """Try multiple paths on a site until INN is found (static HTTP)."""
        from urllib.parse import urljoin

        for path in self._INN_PATHS[:4]:  # only first 4 paths (incl. homepage)
            url = urljoin(base_url, path)
            try:
                resp = await client.get(url)
                if resp.status_code >= 400:
                    if path == "":
                        return None
                    continue

                html = resp.text

                # Search for INN near labels
                for m in self._INN_RE.finditer(html):
                    raw_inn = m.group(1)
                    if self._is_valid_inn(raw_inn):
                        return raw_inn

                # Also try in visible text (strip HTML)
                if not path:
                    text = re.sub(r"<[^>]+>", " ", html)
                    text = re.sub(r"&[a-z]+;", " ", text)
                    text = re.sub(r"\s+", " ", text)
                    for m in self._INN_RE.finditer(text):
                        raw_inn = m.group(1)
                        if self._is_valid_inn(raw_inn):
                            return raw_inn

            except Exception:
                if path == "":
                    return None
                continue

        return None

    @staticmethod
    def _is_valid_inn(inn: str) -> bool:
        """Basic INN validation: length + checksum."""
        if len(inn) == 10:
            # Legal entity: checksum via weights [2,4,10,3,5,9,4,6,8,0]
            weights = [2, 4, 10, 3, 5, 9, 4, 6, 8, 0]
            try:
                digits = [int(d) for d in inn]
                checksum = sum(d * w for d, w in zip(digits, weights)) % 11 % 10
                return checksum == digits[-1]
            except (ValueError, IndexError):
                return False
        elif len(inn) == 12:
            # Sole proprietor: double checksum
            weights1 = [7, 2, 4, 10, 3, 5, 9, 4, 6, 8, 0]
            weights2 = [3, 7, 2, 4, 10, 3, 5, 9, 4, 6, 8, 0]
            try:
                digits = [int(d) for d in inn]
                cs1 = sum(d * w for d, w in zip(digits[:11], weights1)) % 11 % 10
                cs2 = sum(d * w for d, w in zip(digits[:12], weights2)) % 11 % 10
                return cs1 == digits[10] and cs2 == digits[11]
            except (ValueError, IndexError):
                return False
        return False

    # ── Rusprofile enrichment ────────────────────────────────────────

    async def _enrich_with_rusprofile(
        self, candidates: list[CompanyProfile]
    ) -> int:
        """Fetch real tax-filed financials from rusprofile.ru for candidates with INN.

        Updates CompanyProfile.revenue_year and CompanyProfile.financial_year
        in-place. Returns count of successfully enriched candidates.

        Real rusprofile data is preferred over DaData estimates because it's
        tax-filed — the revenue numbers companies report to ФНС.
        """
        enriched = 0
        inn_candidates = [c for c in candidates if c.inn and c.inn.isdigit()]
        if not inn_candidates:
            logger.info(
                "rusprofile: no candidates with valid INN among %d (names: %s)",
                len(candidates),
                [(c.legal_name[:30], c.data_source) for c in candidates[:5]],
            )
            return 0

        logger.info("rusprofile: checking %d candidates with INN", len(inn_candidates))
        for c in inn_candidates:
            if c.has_real_financials() and c.revenue_year and c.revenue_year > 0:
                continue  # already has real financial data

            try:
                from aim.services.rusprofile.parser import get_rusprofile_client

                rp = get_rusprofile_client()
                company = await rp.get_by_inn(c.inn)
                if company is None:
                    logger.debug(
                        "rusprofile: no data for INN %s (%s)",
                        c.inn, c.legal_name[:40],
                    )
                    continue

                # Extract latest revenue and profit
                latest_year = None
                latest_revenue = None
                latest_profit = None
                for year in sorted(company.revenue.keys(), reverse=True):
                    rev = company.revenue.get(year)
                    if rev and rev > 0:
                        latest_year = year
                        latest_revenue = rev
                        break
                for year in sorted(company.profit.keys(), reverse=True):
                    prf = company.profit.get(year)
                    if prf is not None:
                        latest_profit = prf
                        break

                if latest_revenue is not None and latest_revenue > 0:
                    c.revenue_year = latest_revenue
                    c.financial_year = latest_year
                    c.profit_year = latest_profit
                    c.data_source = "rusprofile"
                    enriched += 1
                    logger.debug(
                        "rusprofile: %s (INN %s) — revenue=%d RUB (%d)",
                        company.short_name or c.legal_name[:40],
                        c.inn,
                        latest_revenue,
                        latest_year,
                    )

            except Exception as e:
                logger.warning(
                    "rusprofile enrichment failed for INN %s: %s",
                    c.inn, e,
                )

        return enriched

    async def _geocode_dadata_candidates(
        self, candidates: list[CompanyProfile]
    ) -> None:
        """Geocode DaData candidates that lack coordinates via Nominatim.

        DaData returns legal_addresses but no geo_lat/geo_lon. Without
        coordinates, location scores are flat (0.7 for same city). Geocoding
        gives us actual distances, differentiating competitors within the city.

        Uses Nominatim (free, no API key) with 1 req/s rate limit.
        """
        if not candidates:
            return

        # Collect unique addresses that need geocoding
        needs_geo: list[tuple[int, str, str]] = []  # (index, raw_addr, clean_addr)
        seen_clean: set[str] = set()
        for i, c in enumerate(candidates):
            if c.geo_lat is not None and c.geo_lon is not None:
                continue
            addr = c.legal_address
            if not addr:
                continue
            clean = self._normalize_address_for_nominatim(addr)
            if not clean or clean in seen_clean:
                continue
            seen_clean.add(clean)
            needs_geo.append((i, addr, clean))

        if not needs_geo:
            return

        # Build clean_addr → coordinates cache for dedup
        addr_cache: dict[str, tuple[float, float]] = {}

        async with httpx.AsyncClient(timeout=10.0) as client:
            for idx, raw_addr, clean_addr in needs_geo:
                if clean_addr in addr_cache:
                    candidates[idx].geo_lat, candidates[idx].geo_lon = addr_cache[clean_addr]
                    continue

                try:
                    resp = await client.get(
                        self._NOMINATIM_URL,
                        params={
                            "q": clean_addr,
                            "format": "json",
                            "limit": 1,
                        },
                        headers={
                            "User-Agent": "AIM-CompetitorDiscovery/1.0 (me@iamaim.ru)",
                        },
                    )
                    resp.raise_for_status()
                    data = resp.json()
                    if data:
                        lat = float(data[0]["lat"])
                        lon = float(data[0]["lon"])
                        addr_cache[clean_addr] = (lat, lon)
                        candidates[idx].geo_lat = lat
                        candidates[idx].geo_lon = lon
                        logger.debug(
                            "Geocoded: %s → (%.4f, %.4f)", raw_addr[:50], lat, lon
                        )

                    # Rate limit: 1 req/s for Nominatim
                    await asyncio.sleep(1.1)
                except Exception as e:
                    logger.warning(
                        "Nominatim geocoding failed for %s: %s", raw_addr[:50], e
                    )
                    await asyncio.sleep(1.1)

        geocoded = sum(
            1 for c in candidates if c.geo_lat is not None and c.geo_lon is not None
        )
        logger.info(
            "Geocoded %d/%d DaData candidates via Nominatim",
            geocoded, len(candidates),
        )

    # (Discovery methods removed — replaced by Apify Google Maps pipeline)

    # ── Scoring ────────────────────────────────────────────────────

    async def _score_candidates(
        self,
        client: ClientProfile,
        candidates: list[CompanyProfile],
        top_n: int,
    ) -> list[CompetitorMatch]:
        """Score each candidate and return top-N matches."""
        scored: list[CompetitorMatch] = []
        client_revenue = client.estimated_revenue or 30_000_000

        # Run scoring concurrently (all independent)
        tasks = [
            _score_one(client, c, client_revenue, client.city_lat, client.city_lon)
            for c in candidates
        ]
        results = await asyncio.gather(*tasks)

        for match in results:
            if match.total_score > 0.05:  # filter complete noise
                scored.append(match)

        scored.sort(key=lambda m: m.total_score, reverse=True)

        # Log top candidates for debugging
        for i, m in enumerate(scored[:10]):
            logger.info(
                "Score #%d: %s | total=%.4f rev=%.2f loc=%.2f svc=%.2f spec=%.2f data=%.2f pop=%.2f vis=%.2f "
                "src=%s spec=%s okved=%s fin=%s",
                i + 1,
                m.profile.legal_name[:60],
                m.total_score,
                m.revenue_match,
                m.location_score,
                m.service_overlap,
                m.specialization_purity,
                m.data_quality,
                _score_popularity(m.profile),
                _score_visibility(m.profile),
                m.profile.data_source,
                m.profile.source_specialization,
                m.profile.okved_main,
                m.profile.has_real_financials(),
            )

        # Generate human-readable match reasons for top candidates
        for m in scored[:max(top_n, 10)]:
            m.match_reason = _build_reason(m, client_revenue)

        return scored  # return ALL — caller handles top-N slicing + diversity


async def _score_one(
    client: ClientProfile,
    candidate: CompanyProfile,
    client_revenue: int,
    city_lat: float | None = None,
    city_lon: float | None = None,
) -> CompetitorMatch:
    """Score a single candidate against the client profile."""
    # Revenue match
    comp_rev = candidate.revenue_year
    # rusprofile data is tax-filed → highest quality (0.95)
    # DaData financials are estimates → medium (0.85)
    # No financial data → low (0.4)
    if candidate.data_source == "rusprofile":
        data_quality = 0.95
    elif candidate.has_real_financials():
        data_quality = 0.85
    else:
        data_quality = 0.4
    rev_for_score = comp_rev if comp_rev else _estimate_revenue(candidate)
    revenue_match = _score_revenue_match(client_revenue, rev_for_score)

    # Location score — uses actual distance when coordinates available
    location_score = _score_location(client, candidate, city_lat, city_lon)

    # Service overlap — rough: compare OKVED codes to service keywords
    service_overlap = _score_services(client, candidate)

    # Specialization purity: mono vs multi-profile matching
    specialization_purity = _score_specialization_purity(client, candidate)

    # Popularity: ratings + reviews from Yandex Maps / 2GIS / OSM
    popularity_score = _score_popularity(candidate)

    # Visibility: search presence + maps listing
    visibility_score = _score_visibility(candidate)

    # ── Location penalty for popularity & visibility ─────────────────
    # When a candidate is clearly in a different city (loc ≤ 0.15),
    # their Yandex ratings and website are irrelevant — patients
    # don't travel across Moscow for routine dental care.
    # Scale popularity & visibility by (loc / 0.3), clamped to [0, 1].
    if location_score < 0.3:
        loc_scale = location_score / 0.3  # 0.10 → 0.33, 0.15 → 0.50
        popularity_score *= loc_scale
        visibility_score *= loc_scale

    # Weighted total
    total = (
        revenue_match * W_REVENUE
        + location_score * W_LOCATION
        + service_overlap * W_SERVICES
        + specialization_purity * W_SPECIALIZATION
        + data_quality * W_DATA
        + popularity_score * W_POPULARITY
        + visibility_score * W_VISIBILITY
    )
    total = round(min(total, 1.0), 4)

    # Determine shared services for reporting
    shared = _shared_services(client, candidate)

    return CompetitorMatch(
        profile=candidate,
        website=candidate.website,
        social_links=candidate.social_links,
        services=shared,
        revenue_match=round(revenue_match, 4),
        location_score=round(location_score, 4),
        service_overlap=round(service_overlap, 4),
        specialization_purity=round(specialization_purity, 4),
        popularity_score=round(popularity_score, 4),
        visibility_score=round(visibility_score, 4),
        data_quality=round(data_quality, 4),
        total_score=total,
        match_reason="",
    )


# ── Scoring components ─────────────────────────────────────────────

def _score_revenue_match(client_rev: int, comp_rev: int) -> float:
    """Score how close the competitor's revenue is to the client's.

    Returns 1.0 when identical, 0.0 when difference >= 100%.
    """
    if client_rev <= 0:
        return 0.5  # unknown = neutral
    diff = abs(client_rev - comp_rev) / client_rev
    return max(0.0, 1.0 - min(diff, 1.0))


def _score_location(
    client: ClientProfile,
    candidate: CompanyProfile,
    city_lat: float | None = None,
    city_lon: float | None = None,
) -> float:
    """Score geographic proximity. Returns 0-1, higher = closer.

    CRITICAL: Address check comes FIRST — coordinates from Yandex/OSM
    can be wrong (search center, not actual address). We verify the
    candidate's address mentions the client's city before trusting coords.
    """
    import re as _re

    # ── Step 1: Address-based city verification ─────────────────────
    # This catches cases where Yandex returns a central-Moscow clinic
    # with coordinates shifted to the search center (e.g. Zelenograd).
    if client.city:
        _city_word = _re.compile(
            r"\b" + _re.escape(client.city) + r"\b",
            _re.IGNORECASE,
        )
        full_address = candidate.legal_address or ""

        # Does the address contain the client's city?
        addr_has_city = bool(full_address and _city_word.search(full_address))

        if not addr_has_city:
            # Try actual_addresses as well
            for act_addr in (candidate.actual_addresses or []):
                if _city_word.search(act_addr):
                    addr_has_city = True
                    break

        if not addr_has_city:
            # Try extracting city from address
            candidate_city = _extract_city(full_address)
            if not candidate_city and candidate.actual_addresses:
                candidate_city = _extract_city(candidate.actual_addresses[0])

            if candidate_city:
                client_city_lower = client.city.lower()
                if client_city_lower == candidate_city.lower():
                    addr_has_city = True
                elif client_city_lower in candidate_city.lower():
                    addr_has_city = True

        # If address clearly does NOT contain client city
        if not addr_has_city and full_address:
            # Special case: Зеленоград — must explicitly mention it
            if client.city.lower() in ("зеленоград",):
                _moscow_central_markers = [
                    "цветной бульвар", "трубная", "сухаревская", "арбат",
                    "тверск", "краснопресненск", "таганск", "басман",
                    "замосквореч", "якиманк", "хамовник", "пресненск",
                    "мещанск", "красносельск",
                ]
                addr_lower = full_address.lower()
                if any(m in addr_lower for m in _moscow_central_markers):
                    return 0.1  # clearly wrong location
                if _re.search(r'\bмосква\b', addr_lower) and 'зеленоград' not in addr_lower:
                    return 0.05  # different city — Moscow ≠ Zelenograd

            # Fall through to coords check — address alone may misclassify
            # nearby satellite cities (Химки, Мытищи for Москва; Пушкин for СПб).
            # Let coordinates provide a partial score if they're available.

    # ── Step 2: Coordinate-based distance ──────────────────────────
    if (candidate.geo_lat is not None
            and candidate.geo_lon is not None
            and city_lat is not None
            and city_lon is not None):
        distance_km = _haversine(city_lat, city_lon, candidate.geo_lat, candidate.geo_lon)
        base_score = max(0.0, 1.0 - min(distance_km / MAX_DISTANCE_KM, 1.0))
        if not addr_has_city and full_address:
            # Wrong city by address → cap the coordinate-based score
            # Nearby (within 50km) gets 0.4, further gets proportional penalty
            if distance_km < 50:
                base_score = max(base_score, 0.4)
            else:
                base_score = min(base_score, 0.1)
        return round(base_score, 4)

    # ── Step 3: Fallback scoring ────────────────────────────────────
    if not client.city:
        return 0.5  # neutral

    if addr_has_city:
        return 0.7  # same city by address, no coords

    return 0.3  # different city or unknown


def _score_services(client: ClientProfile, candidate: CompanyProfile) -> float:
    """Score service overlap using pure Jaccard similarity.

    Pure Jaccard is chosen over TF-IDF because candidate services are
    short constructed strings (5-10 words), not document-length text.
    TF-IDF on tiny strings degrades to keyword overlap with extra math.
    """
    if not client.services:
        return 0.5  # neutral

    candidate_services = _candidate_services(client, candidate)
    if not candidate_services:
        return 0.1

    client_set = set(client.services)
    cand_set = set(candidate_services)
    jaccard = len(client_set & cand_set) / max(len(client_set | cand_set), 1)

    return round(jaccard, 4)


def _candidate_services(client: ClientProfile, candidate: CompanyProfile) -> list[str]:
    """Build candidate services from all available signals.

    Priority:
      1. Scraped services (real services from competitor's website)
      2. Source specialization + OKVED (from search query + registry data)
      3. Name analysis (keyword matching in company name)
    """
    # 1. Real scraped services — highest quality signal
    if candidate.scraped_services:
        return candidate.scraped_services

    services: set[str] = set()

    # 2. Source specialization — the search query that found this candidate
    if candidate.source_specialization:
        spec = candidate.source_specialization
        services.add(spec)
        _SPEC_RELATED: dict[str, list[str]] = {
            "косметология": [
                "косметология", "дерматология", "лазерная эпиляция",
                "инъекционная косметология", "аппаратная косметология",
                "уход за кожей", "эстетическая медицина",
            ],
            "стоматология": [
                "стоматология", "терапия", "хирургия", "ортопедия",
                "ортодонтия", "имплантация", "гигиена",
            ],
            "пластическая хирургия": [
                "пластическая хирургия", "хирургия", "косметология",
                "дерматология", "реабилитация",
            ],
            "офтальмология": [
                "офтальмология", "диагностика", "хирургия",
            ],
            "педиатрия": [
                "педиатрия", "терапия", "диагностика",
            ],
            "диагностический центр": [
                "диагностика", "терапия",
            ],
            "многопрофильная клиника": [
                "терапия", "хирургия", "диагностика", "гинекология",
                "дерматология", "косметология", "педиатрия",
            ],
        }
        for related in _SPEC_RELATED.get(spec, [spec]):
            services.add(related)

    # 2. OKVED codes
    okved_services = _okved_to_services(
        candidate.okved_main, candidate.okved_secondary
    )
    services.update(okved_services)

    # 3. Name analysis — specialization keywords in the company name
    name = candidate.legal_name.lower()
    _NAME_SPEC_KEYWORDS: dict[str, list[str]] = {
        "косметология": ["косметологи", "косметолог", "космет", "эстети", "beauty", "лазерн"],
        "стоматология": ["стоматологи", "стоматолог", "дентал", "dental", "дент"],
        "пластическая хирургия": ["пластическ", "хирург"],
        "офтальмология": ["офтальмологи", "офтальмолог", "глаз", "зрение"],
        "педиатрия": ["педиатри", "педиатр", "детск"],
        "диагностический центр": ["диагност", "мрт", "кт", "узи"],
    }
    for spec, keywords in _NAME_SPEC_KEYWORDS.items():
        for kw in keywords:
            if kw in name:
                services.add(spec)
                break

    return list(services)


def _score_popularity(candidate: CompanyProfile) -> float:
    """Score competitor popularity from ratings + review counts.

    rating_score:  3.0 → 0.0, 5.0 → 1.0 (linear)
    review_score:  log-scale, maxes out at 200 reviews

    Returns 0.5 (neutral) when no popularity data is available.
    """
    rating = candidate.rating
    reviews = candidate.reviews_count or 0

    if rating is None and reviews == 0:
        return 0.15  # no popularity data = negative signal, real businesses have reviews

    # Rating component (0.6 weight)
    if rating is not None and rating > 0:
        rating_score = max(0.0, (rating - 3.0) / 2.0)
    else:
        rating_score = 0.5  # neutral

    # Review count component (0.4 weight) — log scale
    if reviews > 0:
        review_score = min(math.log(reviews + 1) / math.log(200), 1.0)
    else:
        review_score = 0.0

    return round(0.6 * rating_score + 0.4 * review_score, 4)


def _score_visibility(candidate: CompanyProfile) -> float:
    """Score competitor's search visibility and maps presence.

    Uses data_source as a proxy signal:
      - "apify_google_maps+dadata" → Google Maps + DaData enrichment (best)
      - "apify_google_maps" → Google Maps listing with website/socials
      - "dadata" → legal-only, no consumer-facing presence

    Returns 0-1 scale.
    """
    ds = candidate.data_source
    if ds == "apify_google_maps+dadata":
        return 0.95  # Google Maps + full legal enrichment
    elif ds == "apify_google_maps":
        return 0.85  # Google Maps — real consumer presence, website, reviews
    elif ds == "dadata":
        return 0.3   # legal-only, no consumer-facing presence
    return 0.3


def _specialization_to_okved(specialization: str) -> str:
    """Map client specialization to the closest OKVED code."""
    mapping = {
        "стоматология": "86.23",
        "косметология": "96.02",
        "многопрофильная клиника": "86.21",
        "пластическая хирургия": "86.22",
        "офтальмология": "86.21",
        "диагностический центр": "86.90",
        "педиатрия": "86.21",
    }
    return mapping.get(specialization, "86.90")


def _shared_services(client: ClientProfile, candidate: CompanyProfile) -> list[str]:
    """Return the list of services shared between client and candidate."""
    if not client.services:
        return []
    candidate_services = _candidate_services(client, candidate)
    return list(set(client.services) & set(candidate_services))


# ── OKVED → service mapping ────────────────────────────────────────

# OKVED → service keywords. Some codes expand to multiple services
# because the OKVED category inherently covers them.
# e.g. 86.23 "Стоматологическая практика" = therapy + surgery + hygiene
_OKVED_SERVICE_MAP: dict[str, list[str]] = {
    "86.10": ["стационар"],
    "86.21": ["терапия"],
    "86.22": ["хирургия"],
    "86.23": ["стоматология", "терапия", "хирургия", "гигиена"],
    "86.90": ["диагностика"],
    "86.90.9": ["диагностика"],
    "86.90.1": ["косметология"],
    "86.90.2": ["косметология"],
    "86.90.3": ["дерматология"],
    "86.90.4": ["массаж"],
    "86.90.5": ["физиотерапия"],
    "86.90.6": ["реабилитация"],
    "86.90.7": ["психотерапия"],
    "96.02": ["косметология"],
    "96.04": ["массаж"],
}


def _okved_to_services(okved_main: str | None, okved_secondary: list[str]) -> list[str]:
    """Map OKVED codes to our service keywords."""
    services: set[str] = set()
    for code in [okved_main] + okved_secondary:
        if not code:
            continue
        svc_list = _OKVED_SERVICE_MAP.get(code) or _OKVED_SERVICE_MAP.get(code[:5])
        if svc_list:
            services.update(svc_list)
        elif code.startswith("86."):
            services.add("терапия")
    return list(services)


# ── Helpers ────────────────────────────────────────────────────────

def _estimate_revenue(profile: CompanyProfile) -> int:
    """Estimate revenue from employee count or OKVED benchmarks."""
    if profile.employee_count and profile.employee_count > 0:
        return profile.employee_count * 3_500_000  # mid-market rev/emp

    # Fallback by OKVED
    for code in [profile.okved_main] + profile.okved_secondary:
        if code and code.startswith("86.23"):
            return 25_000_000  # dentistry
        if code and code.startswith("86.22"):
            return 30_000_000  # surgery
        if code and code.startswith("86.90"):
            return 20_000_000  # other medical

    return 25_000_000  # generic medical


def _extract_city(address: str | None) -> str:
    """Extract the most specific city from an address string.

    For "г Москва, г Зеленоград, к 829" returns "Зеленоград".
    For "Калининградская обл, г Зеленоградск" returns "Зеленоградск".
    """
    if not address:
        return ""
    import re
    # Find all "г. CityName" patterns — take the last (most specific)
    city_markers = re.findall(
        r"\bг\.?\s+([А-ЯЁ][а-яё]+(?:[\s-][А-ЯЁ][а-яё]+)?)\b",
        address,
    )
    if city_markers:
        return city_markers[-1]
    # Fallback: first capitalized word that looks like a city
    m = re.match(r"([А-ЯЁ][а-яё]+(?:[\s-][А-ЯЁ][а-яё]+)?)", address)
    if m:
        return m.group(1)
    return ""


def _haversine(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Haversine distance in kilometres."""
    R = 6371.0
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = (math.sin(dlat / 2) ** 2
         + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2))
         * math.sin(dlon / 2) ** 2)
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def _name_similarity(a: str, b: str) -> float:
    """Crude name similarity: ratio of shared words."""
    wa = set(a.lower().split())
    wb = set(b.lower().split())
    if not wa or not wb:
        return 0.0
    return len(wa & wb) / max(len(wa), len(wb))


_STATE_HEALTHCARE_PATTERNS: dict[str, str] = {
    # State legal-form prefixes (the strongest signal)
    "ГАУЗ": "Государственное автономное учреждение здравоохранения",
    "ГБУЗ": "Государственное бюджетное учреждение здравоохранения",
    "ГУЗ": "Государственное учреждение здравоохранения",
    "МУЗ": "Муниципальное учреждение здравоохранения",
    "МБУЗ": "Муниципальное бюджетное учреждение здравоохранения",
    "ФГБУ": "Федеральное государственное бюджетное учреждение",
    "ФГАУ": "Федеральное государственное автономное учреждение",
    "ФКУЗ": "Федеральное казённое учреждение здравоохранения",
    "ГКУЗ": "Государственное казённое учреждение здравоохранения",
}

# Substrings that strongly indicate state/municipal healthcare,
# checked case-insensitively against the full name.
_STATE_NAME_MARKERS: list[str] = [
    "городская поликлиника",
    "городская больница",
    "городская стоматологическая поликлиника",
    "городская стоматология",
    "муниципальная поликлиника",
    "муниципальная больница",
    "детская городская поликлиника",
    "детская городская больница",
    "детская стоматологическая поликлиника",
    "детская поликлиника",           # e.g. "Детская поликлиника 111"
    "детская больница",              # e.g. "Детская больница № 5"
    "центральная районная больница",
    "районная больница",
    "районная поликлиника",
    "областная больница",
    "областная клиническая больница",
    "областная поликлиника",
    "краевая больница",
    "краевая клиническая больница",
    "республиканская больница",
    "республиканская клиническая больница",
    "женская консультация",
    "кожно-венерологический диспансер",
    "противотуберкулёзный диспансер",
    "противотуберкулезный диспансер",
    "психоневрологический диспансер",
    "наркологический диспансер",
    "онкологический диспансер",
    "врачебно-физкультурный диспансер",
    "психиатрическая больница",      # state psychiatric hospitals
    "инфекционная больница",
    "туберкулёзная больница",
    "туберкулезная больница",
    "центр гигиены и эпидемиологии",
    "станция скорой медицинской помощи",
    "бюро судебно-медицинской экспертизы",
    "дом ребёнка",
]


def _is_state_healthcare(name: str) -> bool:
    """Check if an organization is a state/municipal healthcare institution.

    We work ONLY in commercial medicine. This filter removes:
      - ГАУЗ/ГБУЗ/ГУЗ/МУЗ/МБУЗ — state/municipal healthcare institutions
      - городская/районная/областная поликлиника/больница
      - Numbered polyclinics: «Городская поликлиника № 12»
      - State dispensaries (туберкулёзный, психоневрологический, etc.)
      - ЦРБ, женские консультации, станции скорой помощи

    Does NOT filter:
      - ООО, АО, ЗАО, ИП with «клиника», «стоматология», «медицинский центр»
      - Commercial brands that happen to contain «город» in address context
    """
    if not name:
        return False

    upper = name.upper()

    # ── 1. State legal-form prefix (the strongest signal) ──────────
    for prefix in _STATE_HEALTHCARE_PATTERNS:
        if upper.startswith(prefix) or f'"{prefix}' in upper or f'«{prefix}' in upper:
            return True

    # ── 2. Commercial legal form — if present, it overrides markers ─
    # ООО, АО, ЗАО, ИП are commercial legal forms. Even if the name
    # contains "городская" (as part of address, not ownership), it's commercial.
    _COMMERCIAL_FORMS = ("ООО", "АО ", "АО\"", "ЗАО", "ИП ", "ПАО", "ОАО")
    has_commercial_form = any(
        upper.startswith(cf) or f'"{cf}' in upper or f'«{cf}' in upper
        for cf in _COMMERCIAL_FORMS
    )

    # ── 3. Name-based markers ──────────────────────────────────────
    lower = name.lower()
    for marker in _STATE_NAME_MARKERS:
        if marker in lower:
            # If the org has a commercial form AND the marker word,
            # it's probably a commercial clinic near a landmark or
            # a former state clinic now privatized — let it through.
            # Only filter if NO commercial form is present.
            if not has_commercial_form:
                return True

    # ── 4. Numbered polyclinics & hospitals ───────────────────────
    # «Городская поликлиника № 12», «Стоматологическая поликлиника № 3»,
    # «Поликлиника 52 филиал 2», «Детская поликлиника 111»,
    # «Психиатрическая больница № 14»
    # These are МУЗ/ГБУЗ even without the explicit legal-form prefix.
    import re as _re_state
    if _re_state.search(r"поликлиника\s+(?:№\s*)?\d+", lower):
        if not has_commercial_form:
            return True
    if _re_state.search(r"больница\s+(?:№\s*)?\d+", lower):
        if not has_commercial_form:
            return True

    return False


def _score_specialization_purity(
    client: ClientProfile, candidate: CompanyProfile
) -> float:
    """Score how well the candidate's profile breadth matches the client's.

    Key insight: a mono-profile clinic (only cosmetology) competes with other
    mono cosmetology clinics, NOT with multi-profile medical centers. Similarly,
    a multi-profile clinic competes with other multi-profile clinics that offer
    a similar range of services.

    Returns 1.0 for perfect match, 0.0 for complete mismatch.
    """
    # Determine client's profile type
    client_is_multi = _is_multi_profile_client(client)
    client_specs = _client_specializations(client)

    # Determine candidate's profile type
    candidate_is_multi = _is_multi_profile_candidate(candidate)
    candidate_specs = _candidate_specializations(candidate)

    if not client_specs:
        return 0.5  # unknown — neutral

    # Count overlapping specializations
    overlap = len(client_specs & candidate_specs)
    jaccard = overlap / max(len(client_specs | candidate_specs), 1)

    if client_is_multi and candidate_is_multi:
        # Both multi-profile: reward specialization overlap
        return round(0.6 + 0.4 * jaccard, 4)

    if not client_is_multi and not candidate_is_multi:
        # Both mono-profile: high score if same spec, low if different
        if overlap > 0:
            return round(0.8 + 0.2 * jaccard, 4)
        else:
            return 0.15  # mono but different fields — weak match

    # Mixed: mono vs multi — significant penalty
    if client_is_multi and not candidate_is_multi:
        # Multi client, mono candidate: candidate is narrower
        # Score by whether candidate's spec is one of client's areas
        if overlap > 0:
            return round(0.3 + 0.2 * jaccard, 4)
        return 0.1

    # Mono client, multi candidate: candidate is broader
    if overlap > 0:
        return round(0.25 + 0.2 * jaccard, 4)
    return 0.1


# Specializations that indicate a multi-profile clinic when combined
_MULTI_SPEC_SIGNALS: dict[str, set[str]] = {
    "стоматология": {"стоматология"},
    "косметология": {"косметология", "дерматология"},
    "пластическая хирургия": {"пластическая хирургия", "хирургия"},
    "офтальмология": {"офтальмология"},
    "педиатрия": {"педиатрия"},
    "гинекология": {"гинекология"},
    "диагностика": {"диагностика", "мрт", "кт", "узи"},
    "терапия": {"терапия"},
    "хирургия": {"хирургия"},
    "реабилитация": {"реабилитация"},
    "неврология": {"неврология"},
    "кардиология": {"кардиология"},
    "урология": {"урология"},
    "эндокринология": {"эндокринология"},
    "дерматология": {"дерматология", "косметология"},
}


def _is_multi_profile_client(client: ClientProfile) -> bool:
    """Check if the client is a multi-profile clinic."""
    if client.specialization == "многопрофильная клиника":
        return True
    if not client.services:
        return False

    # Map services to specialization buckets
    matched_specs: set[str] = set()
    for svc in client.services:
        for spec, keywords in _MULTI_SPEC_SIGNALS.items():
            if svc.lower() in keywords or any(kw in svc.lower() for kw in keywords):
                matched_specs.add(spec)
                break

    # 2+ distinct specializations → multi-profile
    return len(matched_specs) >= 2


def _is_multi_profile_candidate(candidate: CompanyProfile) -> bool:
    """Check if the candidate is a multi-profile clinic."""
    # Explicit "многопрофильная" tag
    if candidate.source_specialization == "многопрофильная клиника":
        return True

    name_lower = candidate.legal_name.lower()
    if "многопрофильн" in name_lower:
        return True

    # Check OKVED codes: multiple distinct medical categories
    all_codes = [candidate.okved_main] + candidate.okved_secondary
    all_codes = [c for c in all_codes if c]
    if not all_codes:
        return False

    distinct_categories: set[str] = set()
    for code in all_codes:
        code_prefix = code[:4] if len(code) >= 4 else code
        distinct_categories.add(code_prefix)

    return len(distinct_categories) >= 2


def _client_specializations(client: ClientProfile) -> set[str]:
    """Extract the set of specializations from the client profile."""
    specs: set[str] = set()
    if client.specialization:
        specs.add(client.specialization)
    if not client.services:
        return specs
    for svc in client.services:
        for spec, keywords in _MULTI_SPEC_SIGNALS.items():
            if svc.lower() in keywords or any(kw in svc.lower() for kw in keywords):
                specs.add(spec)
                break
    return specs


def _candidate_specializations(candidate: CompanyProfile) -> set[str]:
    """Extract the set of specializations from a candidate profile.

    CRITICAL: source_specialization is the search query that FOUND this
    candidate — it's what we were LOOKING FOR, not what the candidate IS.
    We only trust it when confirmed by OKVED codes or name keywords.
    Otherwise a neurology center found by broad OSM search gets wrongly
    tagged as "стоматология" just because that's what we searched for.
    """
    specs: set[str] = set()

    # OKVED-based (strongest objective signal)
    all_codes = [candidate.okved_main] + candidate.okved_secondary
    for code in all_codes:
        if not code:
            continue
        okved_services = _okved_to_services(code, [])
        for svc in okved_services:
            for spec, keywords in _MULTI_SPEC_SIGNALS.items():
                if svc in keywords:
                    specs.add(spec)
                    break

    # Name-based
    name = candidate.legal_name.lower()
    _NAME_SPEC: dict[str, list[str]] = {
        "косметология": ["косметолог", "космет", "эстети", "beauty", "лазерн"],
        "стоматология": ["стоматолог", "дентал", "dental", "дент"],
        "пластическая хирургия": ["пластическ", "хирург"],
        "офтальмология": ["офтальмолог", "глаз", "зрение"],
        "педиатрия": ["педиатр", "детск"],
        "диагностика": ["диагност", "мрт", "кт", "узи"],
    }
    for spec, keywords in _NAME_SPEC.items():
        for kw in keywords:
            if kw in name:
                specs.add(spec)
                break

    # Source specialization: only trust if confirmed by OKVED or name
    if candidate.source_specialization:
        if not specs:
            # No OKVED/name signals — source_specialization is our only hint
            # but we treat it with lower confidence (it'll be scored lower in purity)
            specs.add(candidate.source_specialization)
        elif candidate.source_specialization in specs:
            # Confirmed by other signals — reinforce
            pass
        else:
            # source_specialization conflicts with OKVED/name — trust OKVED/name
            pass

    return specs


def _build_reason(m: CompetitorMatch, client_revenue: int = 0) -> str:
    """Build a human-readable reason string for the match.

    When competitor has real financial data and is bigger, flags as aspirational:
    "крупнее вас — посмотрите что они делают чтобы зарабатывать больше"
    """
    parts: list[str] = []
    c = m.profile

    # Revenue comparison — prefer real (rusprofile) data
    comp_rev = c.revenue_year
    if comp_rev and comp_rev > 0 and client_revenue > 0:
        if comp_rev > client_revenue * 1.5:
            multiple = comp_rev / client_revenue
            if multiple >= 5:
                parts.append(f"крупнее в {multiple:.0f}× — вот кто задаёт рынок")
            elif multiple >= 3:
                parts.append(f"крупнее в {multiple:.0f}× — ориентир для роста")
            else:
                parts.append(f"крупнее в {multiple:.1f}× — посмотрите их тактики")
        elif comp_rev > client_revenue * 1.1:
            parts.append("чуть крупнее вас")
        elif comp_rev > client_revenue * 0.9:
            parts.append("схожий масштаб")
        elif comp_rev > client_revenue * 0.5:
            parts.append("меньше вас")
        else:
            parts.append("значительно меньше")
    elif m.revenue_match >= 0.7:
        parts.append("схожий масштаб")
    elif m.revenue_match >= 0.4:
        parts.append("сравнимый масштаб")
    else:
        parts.append("масштаб отличается")

    if m.location_score >= 0.9:
        parts.append("тот же город")
    elif m.location_score >= 0.7:
        parts.append("рядом")

    if m.service_overlap >= 0.7:
        parts.append("те же услуги")
    elif m.service_overlap >= 0.4:
        parts.append("похожие услуги")
    else:
        parts.append("услуги отличаются")

    if c.data_source == "rusprofile":
        parts.append("данные из ФНС")
    elif m.data_quality >= 0.8:
        parts.append("реальные данные")
    else:
        parts.append("оценочные данные")

    # Popularity signals
    profile = m.profile
    if profile.rating and profile.rating >= 4.0:
        parts.append(f"рейтинг {profile.rating:.1f}")
    if profile.reviews_count and profile.reviews_count >= 100:
        parts.append(f"{profile.reviews_count}+ отзывов")
    elif profile.reviews_count and profile.reviews_count >= 20:
        parts.append(f"{profile.reviews_count} отзыва")

    return ", ".join(parts)


