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

Three-tier discovery:
  Tier 1: DaData — finds companies by legal name (prefix search)
  Tier 2: OpenStreetMap — finds organizations by amenity type (dentist/clinic)
           Catches brand-named clinics like "Никор-Мед" that DaData misses.
  Tier 3: Yandex Maps — finds organizations by what people search for
           Adds ratings, reviews, and real-world popularity signals.
"""

import asyncio
import logging
import math
import os
import time
from typing import Optional

import httpx

from .osm_discovery import OSMDiscovery, get_osm_discovery
from .rusprofile.client import DaDataClient, get_dadata_client
from .rusprofile.models import ClientProfile, CompanyProfile, CompetitorMatch
from .service_extractor import extract_client_profile
from .yandex_maps import YandexMapsClient, get_yandex_maps_client

logger = logging.getLogger(__name__)

# ── Blacklist ───────────────────────────────────────────────────────
# Comma-separated company names that should NEVER appear as competitors.
# These are typically the user's own projects/clients.
_BLACKLIST_NAMES: set[str] = set()
_bl = os.environ.get("COMPETITOR_BLACKLIST_NAMES", "")
if _bl:
    _BLACKLIST_NAMES = {n.strip().lower() for n in _bl.split(",") if n.strip()}
    logger.info("Competitor blacklist loaded: %d names", len(_BLACKLIST_NAMES))

# ── Scoring weights ────────────────────────────────────────────────
W_REVENUE = 0.10
W_LOCATION = 0.15
W_SERVICES = 0.12
W_SPECIALIZATION = 0.15
W_DATA = 0.18
W_POPULARITY = 0.18
W_VISIBILITY = 0.12

MAX_DISTANCE_KM = 50.0  # beyond this, location_score = 0

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


class CompetitorMatcher:
    """Find and score competitors for a client clinic."""

    def __init__(
        self,
        dadata: DaDataClient | None = None,
        osm: OSMDiscovery | None = None,
        yandex: YandexMapsClient | None = None,
    ):
        self.dadata = dadata or get_dadata_client()
        self.osm = osm or get_osm_discovery()
        self.yandex = yandex or get_yandex_maps_client()

    # ── Main entry point ───────────────────────────────────────────

    async def find_competitors(
        self,
        url: str,
        count: int = 3,
        named_competitors: Optional[list[str]] = None,
    ) -> list[CompetitorMatch]:
        """Find top-N competitors for a clinic website.

        Args:
            url: Client's website URL
            count: Number of competitors to return (default 3)
            named_competitors: Optional list of competitor names/URLs to
                look up directly via DaData. When provided, these are enriched
                and scored alongside discovered competitors.

        Returns:
            List of CompetitorMatch, sorted by total_score descending.
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
        logger.info("CompetitorMatcher: client profile built — %s", client)

        if not client.city:
            logger.warning("CompetitorMatcher: no city detected for %s", url)
        else:
            # Geocode city for distance-based scoring
            coords = await self.osm.geocode(client.city)
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

        # 2. Three-tier discovery: DaData + OpenStreetMap + Yandex Maps
        dadata_candidates, osm_candidates, yandex_candidates = await asyncio.gather(
            self._search_candidates(client),
            self._search_osm_candidates(client),
            self._search_yandex_candidates(client),
        )
        t_discovery = time.monotonic()
        logger.info(
            "CompetitorMatcher: tiers=%.1fs (DaData=%d, OSM=%d, Yandex=%d) [after extract=%.1fs + geocode=%.1fs]",
            t_discovery - t_geocode, len(dadata_candidates), len(osm_candidates), len(yandex_candidates),
            t_extract - t0, t_geocode - t_extract,
        )

        # 2.5. Look up named competitors via DaData (by name)
        named_profiles: list[CompanyProfile] = []
        if named_competitors:
            for name in named_competitors:
                # Strip URL prefix if user passed a URL instead of name
                clean_name = name.strip()
                if clean_name.startswith("http"):
                    clean_name = clean_name.split("//")[-1].split("/")[0]  # extract domain
                    # Remove www. prefix
                    if clean_name.startswith("www."):
                        clean_name = clean_name[4:]
                profiles = await self.dadata.search_company(clean_name, count=3)
                if profiles:
                    # Mark as named competitor for traceability
                    for p in profiles:
                        p._named_competitor = True
                    named_profiles.extend(profiles)
                    logger.info(
                        "CompetitorMatcher: named_competitor '%s' => %d DaData matches",
                        clean_name, len(profiles),
                    )
                else:
                    logger.warning(
                        "CompetitorMatcher: named_competitor '%s' not found in DaData",
                        clean_name,
                    )

        # Merge: DaData first, then OSM, then Yandex, then named
        candidates = await self._merge_candidates(
            dadata_candidates, osm_candidates, client
        )
        candidates = await self._merge_candidates(
            candidates, yandex_candidates, client
        )
        if named_profiles:
            candidates = await self._merge_candidates(
                candidates, named_profiles, client
            )

        # Filter out municipal/state healthcare institutions.
        # We work ONLY in commercial medicine.
        commercial: list[CompanyProfile] = []
        filtered_count = 0
        for c in candidates:
            if _is_state_healthcare(c.legal_name):
                filtered_count += 1
                logger.debug("Filtered state/municipal: %s", c.legal_name)
            else:
                commercial.append(c)
        candidates = commercial

        if filtered_count > 0:
            logger.info(
                "CompetitorMatcher: filtered %d state/municipal orgs, %d commercial remain",
                filtered_count, len(candidates),
            )

        # Filter out blacklisted companies (user's own projects/clients)
        if _BLACKLIST_NAMES:
            pre_bl = len(commercial)
            commercial = [
                c for c in commercial
                if c.legal_name.lower() not in _BLACKLIST_NAMES
                and not any(bl in c.legal_name.lower() for bl in _BLACKLIST_NAMES if len(bl) > 5)
            ]
            if len(commercial) < pre_bl:
                logger.info(
                    "CompetitorMatcher: filtered %d blacklisted orgs",
                    pre_bl - len(commercial),
                )

        if not candidates:
            logger.warning("CompetitorMatcher: no candidates found for %s", url)
            return []

        logger.info(
            "CompetitorMatcher: %d total candidates (DaData=%d, OSM=%d, Yandex=%d)",
            len(candidates),
            len(dadata_candidates),
            len(osm_candidates),
            len(yandex_candidates),
        )

        # 2.5. Enrich candidates with real financials from rusprofile.ru
        # Only enrich candidates that have an INN (DaData provides INN, OSM/Yandex may not)
        t_enrich_start = time.monotonic()
        enriched_count = await self._enrich_with_rusprofile(candidates[:10])
        if enriched_count:
            t_enrich = time.monotonic()
            logger.info(
                "CompetitorMatcher: rusprofile enriched %d/%d candidates in %.1fs",
                enriched_count, min(len(candidates), 10), t_enrich - t_enrich_start,
            )

        # 3. Score and rank (first pass — without geocoding DaData)
        scored = await self._score_candidates(client, candidates, count)
        t_score1 = time.monotonic()

        # 4. Geocode top DaData candidates to refine location scores
        # Only geocode top-5 who lack coordinates (saves ~20s vs geocoding all 25)
        top_dadata = [
            m.profile for m in scored[:5]
            if m.profile.data_source == "dadata"
            and m.profile.geo_lat is None
            and m.profile.legal_address
        ]
        if top_dadata:
            await self._geocode_dadata_candidates(top_dadata)
            # Re-score with actual coordinates
            scored = await self._score_candidates(client, candidates, count)

        # 5. Ensure source diversity: at least 1 candidate with INN (→ rusprofile financials)
        top = scored[:count]
        has_inn = any(m.profile.inn and m.profile.inn.strip() for m in top)
        if not has_inn:
            inn_candidates = [
                m for m in scored
                if m.profile.inn and m.profile.inn.strip()
                and m not in top
            ]
            if inn_candidates:
                # Replace the lowest-scoring non-INN candidate
                inn_best = inn_candidates[0]  # already sorted by score desc
                sorted_top = sorted(top, key=lambda m: m.total_score)
                replaced = sorted_top[0]
                top.remove(replaced)
                top.append(inn_best)
                top.sort(key=lambda m: m.total_score, reverse=True)
                logger.info(
                    "CompetitorMatcher: diversity swap — replaced %s (score=%.4f, src=%s) "
                    "with %s (score=%.4f, inn=%s)",
                    replaced.profile.legal_name[:40], replaced.total_score, replaced.profile.data_source,
                    inn_best.profile.legal_name[:40], inn_best.total_score, inn_best.profile.inn,
                )
        scored = top

        t_total = time.monotonic()
        logger.info(
            "CompetitorMatcher: scoring=%.1fs, geocode=%d candidates/%.1fs, total=%.1fs",
            t_score1 - t_discovery, len(top_dadata), t_total - t_score1, t_total - t0,
        )

        return scored

    # ── Candidate search ───────────────────────────────────────────

    async def _search_candidates(self, client: ClientProfile) -> list[CompanyProfile]:
        """Search DaData for potential competitors.

        DaData suggest/party searches by company NAME, not OKVED. Companies
        like "Никор-Мед" or "Мед-Профи" won't appear in "стоматология" queries.
        We use three tiers of queries for coverage:
          1. Specialization-specific (e.g. "стоматология", "стоматологическая клиника")
          2. Generic medical terms (e.g. "медицинский центр", "клиника", "мед")
          3. City-only fallback with medical filter
        """
        t0 = time.monotonic()
        spec = client.specialization or "медицинская клиника"
        city = client.city

        queries: list[str] = []

        # ── Tier 1: Specialization-based ──────────────────────────
        spec_queries: list[str] = []
        spec_queries.append(spec)
        if spec == "стоматология":
            spec_queries.extend([
                "стоматологическая клиника",
                "стоматологический центр",
                "стоматологическая практика",
                "стоматолог",
            ])
        elif spec == "косметология":
            spec_queries.extend([
                "косметологический центр",
                "центр косметологии",
                "косметолог",
                "косметологическая клиника",
            ])
        elif spec == "многопрофильная клиника":
            spec_queries.extend([
                "медицинский центр",
                "многопрофильный медицинский центр",
                "клиника",
            ])
        elif spec == "пластическая хирургия":
            spec_queries.extend([
                "пластическая хирургия",
                "хирургическая клиника",
                "центр хирургии",
            ])
        elif spec == "офтальмология":
            spec_queries.extend([
                "офтальмологическая клиника",
                "офтальмологический центр",
                "офтальмолог",
            ])
        elif spec == "диагностический центр":
            spec_queries.extend([
                "диагностический центр",
                "медицинский центр",
                "диагностика",
            ])
        elif spec == "педиатрия":
            spec_queries.extend([
                "педиатрия",
                "детская клиника",
                "детский медицинский центр",
            ])

        # ── Tier 2: Generic medical terms ─────────────────────────
        # Catches brands where legal name doesn't include specialization,
        # e.g. "Никор-Мед", "Мед-Профи", "Здоровье", "Гиппократ", etc.
        generic_queries = [
            "медицинский центр",
            "клиника",
            "медицина",
            "мед",
        ]

        # ── Tier 3: City-only (broad sweep) ────────────────────────
        city_queries: list[str] = []
        if city:
            city_queries.append(city)

        # Build query list: spec queries first (tagged), then generic + city
        all_queries: list[tuple[str, bool]] = []
        for q in spec_queries:
            all_queries.append((q, True))   # tagged with client specialization
        for q in generic_queries:
            all_queries.append((q, False))  # not specialization-tagged
        for q in city_queries:
            all_queries.append((q, False))

        async def _search_one_query(q: str, is_spec_query: bool) -> list[CompanyProfile]:
            """Run a single DaData query and tag results."""
            q_city = ""
            if city and city.lower() not in q.lower():
                q_city = city
            try:
                batch = await self.dadata.find_medical_companies(
                    query=q,
                    city=q_city,
                    count=20,
                )
                for p in batch:
                    if is_spec_query:
                        p.source_specialization = spec
                return batch
            except Exception as e:
                logger.error("DaData search failed for query=%s: %s", q, e)
                return []

        # Run all queries in parallel (was sequential — 10 queries × ~1-2s = 10-20s)
        tasks = [_search_one_query(q, is_spec) for q, is_spec in all_queries[:10]]
        batches = await asyncio.gather(*tasks)

        raw_all: list[CompanyProfile] = []
        seen_inn: set[str] = set()
        for batch in batches:
            for p in batch:
                if p.inn and p.inn not in seen_inn:
                    seen_inn.add(p.inn)
                    raw_all.append(p)

        # Filter out the client's own company
        candidates = []
        for p in raw_all:
            if client.company_name and client.company_name.lower() in p.legal_name.lower():
                continue
            if p.legal_name and client.company_name and _name_similarity(
                client.company_name, p.legal_name
            ) > 0.9:
                continue
            candidates.append(p)

        logger.info(
            "DaData: %d candidates, %d tagged with specialization='%s' (took %.1fs)",
            len(candidates),
            sum(1 for c in candidates if c.source_specialization == spec),
            spec,
            time.monotonic() - t0,
        )
        return candidates[:25]

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
        for c in candidates:
            if not c.inn or not c.inn.isdigit():
                continue
            if c.has_real_financials() and c.revenue_year and c.revenue_year > 0:
                continue  # already has real financial data

            try:
                from aim.services.rusprofile.parser import get_rusprofile_client

                rp = get_rusprofile_client()
                company = await rp.get_by_inn(c.inn)
                if company is None:
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

    # ── OSM discovery ──────────────────────────────────────────────

    async def _search_osm_candidates(
        self, client: ClientProfile
    ) -> list[CompanyProfile]:
        """Find competitors via OpenStreetMap by amenity type.

        OSM tags organizations by what they DO (amenity=dentist), not by
        legal name. This catches brand-named clinics like "Никор-Мед"
        that DaData prefix search misses.
        """
        t0 = time.monotonic()
        city = client.city
        if not city:
            return []

        try:
            osm_places = await self.osm.find_medical_places(city=city)
        except Exception as e:
            logger.error("OSM discovery failed for %s: %s", city, e)
            return []

        if not osm_places:
            return []

        # Filter to relevant amenity types for this specialization
        spec = client.specialization
        relevant = _filter_osm_by_specialization(osm_places, spec)

        # Enrich OSM places with DaData in parallel (was sequential — 15 lookups × ~1s = 15s)
        async def _enrich_one(place: dict) -> CompanyProfile | None:
            try:
                return await self._lookup_osm_on_dadata(place, spec)
            except Exception as e:
                logger.debug("Failed to enrich OSM place %s: %s", place.get("name"), e)
                return None

        enrich_tasks = [_enrich_one(p) for p in relevant[:15]]
        enrich_results = await asyncio.gather(*enrich_tasks)
        profiles = [p for p in enrich_results if p is not None]

        logger.info("OSM: enriched %d/%d places via DaData (took %.1fs)", len(profiles), len(relevant), time.monotonic() - t0)
        return profiles

    async def _lookup_osm_on_dadata(
        self, place: dict, specialization: str = ""
    ) -> CompanyProfile | None:
        """Try to find an OSM place on DaData for financial data.

        Searches by the first word of the name (brand name) in the city.
        Tags the profile with the client's specialization for service matching.
        """
        name = place.get("name", "")
        city = place.get("city", "")
        if not name:
            return None

        # Search by first 1-2 words of the name (brand core)
        words = name.split()
        brand_core = " ".join(words[:2]) if len(words) >= 2 else words[0]

        try:
            results = await self.dadata.find_medical_companies(
                query=brand_core,
                city=city,
                count=5,
            )
        except Exception:
            return None

        for r in results:
            if _name_similarity(name, r.legal_name) > 0.3:
                # Preserve OSM coordinates if DaData doesn't have them
                if r.geo_lat is None and r.geo_lon is None:
                    r.geo_lat = place.get("lat")
                    r.geo_lon = place.get("lon")
                # Tag as OSM-discovered (even though enriched via DaData)
                if r.data_source == "dadata":
                    r.data_source = "osm+dadata"
                # Tag with client specialization for service matching
                if specialization and not r.source_specialization:
                    r.source_specialization = specialization
                return r

        # No DaData match — build a profile from OSM data alone
        return CompanyProfile(
            inn="",
            legal_name=name,
            brand_name=name,
            employee_count=None,
            okved_main=_osm_amenity_to_okved(place.get("amenity", "")),
            okved_secondary=[],
            legal_address=_format_osm_address(place),
            actual_addresses=[_format_osm_address(place)],
            geo_lat=place.get("lat"),
            geo_lon=place.get("lon"),
            source_specialization=specialization,
            data_source="osm",
            confidence=0.5,
        )

    # ── Yandex Maps discovery ────────────────────────────────────────

    async def _search_yandex_candidates(
        self, client: ClientProfile
    ) -> list[CompanyProfile]:
        """Find competitors via Yandex Maps organization search.

        Yandex Maps returns organizations people actually see and interact
        with on the map — a strong signal of real-world presence.
        """
        t0 = time.monotonic()
        city = client.city
        spec = client.specialization
        if not city or not spec:
            return []

        if not self.yandex.configured:
            logger.debug("Yandex Maps not configured — skipping Tier 3")
            return []

        try:
            yandex_orgs = await self.yandex.find_medical_orgs(
                specialization=spec,
                city=city,
            )
        except Exception as e:
            logger.error("Yandex Maps search failed for %s: %s", city, e)
            return []

        if not yandex_orgs:
            logger.debug("Yandex Maps: 0 orgs found (took %.1fs)", time.monotonic() - t0)
            return []

        # Enrich with ratings (optional — non-blocking)
        enriched_orgs = await asyncio.gather(
            *[self.yandex.enrich_with_ratings(org) for org in yandex_orgs[:15]],
            return_exceptions=True,
        )

        # Enrich Yandex orgs with DaData in parallel (was sequential)
        async def _enrich_yandex_one(result) -> CompanyProfile | None:
            if isinstance(result, Exception):
                logger.debug("Yandex ratings enrichment failed: %s", result)
                return None
            try:
                return await self._lookup_yandex_on_dadata(result, spec)
            except Exception as e:
                logger.debug("Failed to enrich Yandex org %s: %s", result.get("name"), e)
                return None

        enrich_tasks = [_enrich_yandex_one(r) for r in enriched_orgs]
        enrich_results = await asyncio.gather(*enrich_tasks)
        profiles = [p for p in enrich_results if p is not None]

        logger.info("Yandex Maps: enriched %d/%d orgs via DaData (took %.1fs)", len(profiles), len(yandex_orgs), time.monotonic() - t0)
        return profiles

    async def _lookup_yandex_on_dadata(
        self, org: dict, specialization: str = ""
    ) -> CompanyProfile | None:
        """Try to find a Yandex Maps org on DaData for financial data."""
        name = org.get("name", "")
        city = ""
        if not name:
            return None

        # Extract city from address
        address = org.get("address", "")
        import re as _re
        city_match = _re.search(r"г\.?\s+([А-ЯЁ][а-яё]+(?:[\s-][А-ЯЁ][а-яё]+)?)", address)
        if city_match:
            city = city_match.group(1)

        # Search by first 1-2 words of the name
        words = name.split()
        brand_core = " ".join(words[:2]) if len(words) >= 2 else words[0]

        try:
            results = await self.dadata.find_medical_companies(
                query=brand_core,
                city=city,
                count=5,
            )
        except Exception:
            results = []

        for r in results:
            if _name_similarity(name, r.legal_name) > 0.3:
                # Preserve Yandex coordinates if DaData doesn't have them
                if r.geo_lat is None and r.geo_lon is None:
                    r.geo_lat = org.get("lat")
                    r.geo_lon = org.get("lon")
                # Carry Yandex rating/reviews to the profile
                if r.rating is None and org.get("rating"):
                    r.rating = org.get("rating")
                if r.reviews_count is None and org.get("reviews_count"):
                    r.reviews_count = org.get("reviews_count")
                # Tag as Yandex-discovered
                if r.data_source == "dadata":
                    r.data_source = "yandex+dadata"
                return r

        # No DaData match — build profile from Yandex data
        return CompanyProfile(
            inn="",
            legal_name=name,
            brand_name=name,
            employee_count=None,
            okved_main=_specialization_to_okved(specialization),
            okved_secondary=[],
            legal_address=address,
            actual_addresses=[address] if address else [],
            geo_lat=org.get("lat"),
            geo_lon=org.get("lon"),
            rating=org.get("rating"),
            reviews_count=org.get("reviews_count"),
            source_specialization=specialization,
            data_source="yandex",
            confidence=0.55,
        )

    async def _merge_candidates(
        self,
        dadata: list[CompanyProfile],
        osm: list[CompanyProfile],
        client: ClientProfile,
    ) -> list[CompanyProfile]:
        """Merge candidates from different sources, deduplicating by name similarity."""
        merged: dict[str, CompanyProfile] = {}

        # DaData first (higher priority — has financial data)
        for p in dadata:
            if p.inn:
                merged[p.inn] = p
            else:
                merged[p.legal_name.lower()] = p

        # OSM: add if no similar DaData company exists
        for p in osm:
            key = p.inn if p.inn else p.legal_name.lower()
            if key in merged:
                continue
            # Check for name similarity with existing
            is_dup = False
            for existing in merged.values():
                if _name_similarity(p.legal_name, existing.legal_name) > 0.6:
                    is_dup = True
                    break
            if not is_dup:
                merged[key] = p

        return list(merged.values())

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
        website=None,  # to be enriched later if needed
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

    When candidate has coordinates and city center is known, uses actual
    haversine distance — this differentiates competitors within the same city
    instead of giving them all the same score.
    """
    # ── Actual distance when coordinates available ─────────────────
    if (candidate.geo_lat is not None
            and candidate.geo_lon is not None
            and city_lat is not None
            and city_lon is not None):
        distance_km = _haversine(city_lat, city_lon, candidate.geo_lat, candidate.geo_lon)
        # Score decays from 1.0 (0 km) to 0.0 (≥50 km)
        return round(max(0.0, 1.0 - min(distance_km / MAX_DISTANCE_KM, 1.0)), 4)

    # ── Fallback: city-name matching ───────────────────────────────
    if not client.city:
        return 0.5  # neutral

    # Strategy A: does the full address contain the client city as a whole word?
    # Handles "г Москва, г Зеленоград" when client city is "Зеленоград".
    import re as _re
    _city_word = _re.compile(
        r"\b" + _re.escape(client.city) + r"\b",
        _re.IGNORECASE,
    )
    full_address = candidate.legal_address or ""
    if full_address and _city_word.search(full_address):
        return 0.7  # same city by address, but no coords → lower confidence

    # Strategy B: extract city from address and compare
    candidate_city = _extract_city(candidate.legal_address)
    if not candidate_city:
        candidate_city = _extract_city(
            candidate.actual_addresses[0] if candidate.actual_addresses else ""
        )

    if candidate_city and client.city.lower() == candidate_city.lower():
        return 0.7
    if candidate_city and client.city.lower() in candidate_city.lower():
        return 0.5
    if candidate_city and candidate_city.lower() in client.city.lower():
        return 0.5

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
    """Build candidate services from all available signals."""
    services: set[str] = set()

    # 1. Source specialization — the search query that found this candidate
    if candidate.source_specialization:
        spec = candidate.source_specialization
        services.add(spec)
        # Add related services for known specializations
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

    Currently uses data_source as a proxy signal:
      - "yandex+dadata" → strong presence (on Yandex Maps + DaData)
      - "yandex" → maps-only presence
      - "osm+dadata" → OSM listing + DaData enrichment
      - "osm" → OSM-only, basic presence
      - "dadata" → legal-only, no consumer-facing presence

    Returns 0-1 scale.
    """
    ds = candidate.data_source
    if ds == "yandex+dadata":
        return 0.9   # best of both worlds
    elif ds == "yandex":
        return 0.7   # maps presence confirmed
    elif ds == "osm+dadata":
        return 0.6   # OSM + legal enrichment
    elif ds == "osm":
        return 0.2   # OSM-only, weak signal — easy to create entries
    elif ds == "dadata":
        return 0.3   # legal-only
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


# ── OSM helpers ────────────────────────────────────────────────────

# Map OSM amenity types to specialization-based filtering priority.
# For a dental client, we want dentists first, then clinics, then doctors.
_AMENITY_PRIORITY: dict[str, dict[str, int]] = {
    "стоматология": {"dentist": 3, "clinic": 1, "doctors": 0},
    "косметология": {"clinic": 3, "doctors": 1, "dentist": 0},
    "многопрофильная клиника": {"clinic": 3, "doctors": 2, "dentist": 1},
    "пластическая хирургия": {"clinic": 3, "doctors": 2, "dentist": 0},
    "офтальмология": {"clinic": 3, "doctors": 2, "dentist": 0},
    "диагностический центр": {"doctors": 3, "clinic": 2, "dentist": 0},
    "педиатрия": {"clinic": 3, "doctors": 2, "dentist": 0},
}


def _filter_osm_by_specialization(
    places: list[dict], specialization: str
) -> list[dict]:
    """Filter OSM places by relevance to the client's specialization.

    For dentistry: keep all dentists + clinics. For cosmetics: keep clinics.
    """
    priority = _AMENITY_PRIORITY.get(specialization, {})
    if not priority:
        return places  # Unknown spec — keep all

    # Keep places with priority > 0, sort by priority desc
    filtered = [p for p in places if priority.get(p.get("amenity", ""), 0) > 0]
    filtered.sort(key=lambda p: priority.get(p.get("amenity", ""), 0), reverse=True)
    return filtered


# OKVED mapping for OSM amenity types (used when DaData lookup fails)
_AMENITY_OKVED_MAP: dict[str, str] = {
    "dentist": "86.23",   # Стоматологическая практика
    "clinic": "86.21",    # Общая врачебная практика
    "doctors": "86.21",   # Общая врачебная практика
}


def _osm_amenity_to_okved(amenity: str) -> str:
    """Map OSM amenity to nearest OKVED code."""
    return _AMENITY_OKVED_MAP.get(amenity, "86.90")


def _format_osm_address(place: dict) -> str:
    """Format OSM place as a DaData-like address string."""
    parts = []
    city = place.get("city", "")
    if city:
        parts.append(f"г {city}")
    street = place.get("street", "")
    if street:
        parts.append(street)
    housenumber = place.get("housenumber", "")
    if housenumber:
        if street:
            parts[-1] = f"{street} {housenumber}"
        else:
            parts.append(housenumber)
    return ", ".join(parts) if parts else ""
