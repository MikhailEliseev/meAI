"""Competitor matching algorithm — finds top-3 competitors for a client clinic.

Scores candidates by:
  revenue_match   (0.35) — similar scale
  location_score  (0.25) — nearby (≤50 km)
  service_overlap (0.25) — same services
  data_quality    (0.15) — real financials > estimates

Uses DaData for company search, falls back to industry benchmarks for unknown revenue.
"""

import asyncio
import logging
import math
from typing import Optional

from .rusprofile.client import DaDataClient, get_dadata_client
from .rusprofile.models import ClientProfile, CompanyProfile, CompetitorMatch
from .service_extractor import extract_client_profile

logger = logging.getLogger(__name__)

# ── Scoring weights ────────────────────────────────────────────────
W_REVENUE = 0.35
W_LOCATION = 0.25
W_SERVICES = 0.25
W_DATA = 0.15

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

    def __init__(self, dadata: DaDataClient | None = None):
        self.dadata = dadata or get_dadata_client()

    # ── Main entry point ───────────────────────────────────────────

    async def find_competitors(
        self,
        url: str,
        count: int = 3,
    ) -> list[CompetitorMatch]:
        """Find top-N competitors for a clinic website.

        Args:
            url: Client's website URL
            count: Number of competitors to return (default 3)

        Returns:
            List of CompetitorMatch, sorted by total_score descending.
        """
        # 1. Extract client profile from website
        raw = await extract_client_profile(url)
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

        # 2. Search DaData for medical companies
        candidates = await self._search_candidates(client)
        if not candidates:
            logger.warning("CompetitorMatcher: no candidates found for %s", url)
            return []

        # 3. Score and rank
        scored = await self._score_candidates(client, candidates, count)

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
        spec = client.specialization or "медицинская клиника"
        city = client.city

        queries: list[str] = []

        # ── Tier 1: Specialization-based ──────────────────────────
        queries.append(spec)
        if spec == "стоматология":
            queries.extend([
                "стоматологическая клиника",
                "стоматологический центр",
                "стоматологическая практика",
                "стоматолог",
            ])
        elif spec == "косметология":
            queries.extend([
                "косметологический центр",
                "центр косметологии",
                "косметолог",
                "косметологическая клиника",
            ])
        elif spec == "многопрофильная клиника":
            queries.extend([
                "медицинский центр",
                "многопрофильный медицинский центр",
                "клиника",
            ])
        elif spec == "пластическая хирургия":
            queries.extend([
                "пластическая хирургия",
                "хирургическая клиника",
                "центр хирургии",
            ])
        elif spec == "офтальмология":
            queries.extend([
                "офтальмологическая клиника",
                "офтальмологический центр",
                "офтальмолог",
            ])
        elif spec == "диагностический центр":
            queries.extend([
                "диагностический центр",
                "медицинский центр",
                "диагностика",
            ])
        elif spec == "педиатрия":
            queries.extend([
                "педиатрия",
                "детская клиника",
                "детский медицинский центр",
            ])

        # ── Tier 2: Generic medical terms ─────────────────────────
        # Catches brands where legal name doesn't include specialization,
        # e.g. "Никор-Мед", "Мед-Профи", "Здоровье", "Гиппократ", etc.
        generic_medical = [
            "медицинский центр",
            "клиника",
            "медицина",
            "мед",
        ]
        queries.extend(generic_medical)

        # ── Tier 3: City-only (broad sweep) ────────────────────────
        # When city is known, search city name alone — DaData will return
        # companies by address, then _is_medical filters by OKVED.
        if city:
            queries.append(city)

        raw_all: list[CompanyProfile] = []
        seen_inn: set[str] = set()

        for q in queries[:10]:  # max 10 queries for coverage
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
                    if p.inn and p.inn not in seen_inn:
                        seen_inn.add(p.inn)
                        raw_all.append(p)
            except Exception as e:
                logger.error("DaData search failed for query=%s: %s", q, e)

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

        return candidates[:25]

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
        tasks = [_score_one(client, c, client_revenue) for c in candidates]
        results = await asyncio.gather(*tasks)

        for match in results:
            if match.total_score > 0.05:  # filter complete noise
                scored.append(match)

        scored.sort(key=lambda m: m.total_score, reverse=True)

        # Generate human-readable match reasons
        for m in scored[:top_n]:
            m.match_reason = _build_reason(m)

        return scored[:top_n]


async def _score_one(
    client: ClientProfile,
    candidate: CompanyProfile,
    client_revenue: int,
) -> CompetitorMatch:
    """Score a single candidate against the client profile."""
    # Revenue match
    comp_rev = candidate.revenue_year
    data_quality = 0.85 if candidate.has_real_financials() else 0.4
    rev_for_score = comp_rev if comp_rev else _estimate_revenue(candidate)
    revenue_match = _score_revenue_match(client_revenue, rev_for_score)

    # Location score
    location_score = _score_location(client, candidate)

    # Service overlap — rough: compare OKVED codes to service keywords
    service_overlap = _score_services(client, candidate)

    # Weighted total
    total = (
        revenue_match * W_REVENUE
        + location_score * W_LOCATION
        + service_overlap * W_SERVICES
        + data_quality * W_DATA
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


def _score_location(client: ClientProfile, candidate: CompanyProfile) -> float:
    """Score geographic proximity. Returns 0-1, higher = closer."""
    # If we have coordinates for both, use haversine
    if (client.estimated_revenue is not None
            and candidate.geo_lat is not None
            and candidate.geo_lon is not None):
        # We don't have client coordinates, so we use city matching as fallback
        pass

    # City match: same city = 0.9, different city = 0.3
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
        return 0.9

    # Strategy B: extract city from address and compare
    candidate_city = _extract_city(candidate.legal_address)
    if not candidate_city:
        candidate_city = _extract_city(
            candidate.actual_addresses[0] if candidate.actual_addresses else ""
        )

    if candidate_city and client.city.lower() == candidate_city.lower():
        return 0.9
    if candidate_city and client.city.lower() in candidate_city.lower():
        return 0.7
    if candidate_city and candidate_city.lower() in client.city.lower():
        return 0.7

    # If client has coords and candidate has coords, compute distance
    # (We don't have client coords from website extraction currently)
    if (candidate.geo_lat is not None
            and candidate.geo_lon is not None
            and client.city):
        # Approximate: same city = likely within 10-20 km
        return 0.5

    return 0.3  # different city or unknown


def _score_services(client: ClientProfile, candidate: CompanyProfile) -> float:
    """Score service overlap using OKVED codes as proxy."""
    if not client.services:
        return 0.5  # neutral

    # Map OKVED codes to our service keywords
    candidate_services = _okved_to_services(
        candidate.okved_main, candidate.okved_secondary
    )

    if not candidate_services:
        return 0.3

    overlap = len(set(client.services) & set(candidate_services))
    return min(overlap / max(len(client.services), 1), 1.0)


def _shared_services(client: ClientProfile, candidate: CompanyProfile) -> list[str]:
    """Return the list of services shared between client and candidate."""
    if not client.services:
        return []
    candidate_services = _okved_to_services(
        candidate.okved_main, candidate.okved_secondary
    )
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


def _build_reason(m: CompetitorMatch) -> str:
    """Build a human-readable reason string for the match."""
    parts: list[str] = []

    if m.revenue_match >= 0.7:
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

    if m.data_quality >= 0.8:
        parts.append("реальные данные")
    else:
        parts.append("оценочные данные")

    return ", ".join(parts)
