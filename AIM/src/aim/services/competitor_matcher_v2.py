"""CompetitorMatcherV2 — hybrid competitor discovery pipeline.

Replaces Google Maps as the sole discovery source with a two-channel
approach: Perplexity (market knowledge) + SearXNG (real rankings),
then resolves brands → ИНН via bo.nalog.gov.ru, and enriches with
real ФНС financials.

Pipeline:
  Stage 0: Extract client profile + resolve client ИНН + real revenue
  Stage 1: Discover competitor brands (Perplexity + SearXNG in parallel)
  Stage 2: Resolve each brand → legal entity ИНН (bo.nalog, anti-hallucination)
  Stage 3: Enrich with ФНС financials + revenue corridor filter + top-N

Fixes all 8 logged errors from the IPHK test case:
  1. Client INN None → bo.nalog search by name
  2. rusprofile 0/48 → replaced by bo.nalog
  3. Revenue 80M instead of 4.3B → real ФНС gainSum
  4. OKVED None → bo.nalog returns okved2
  5. Service scraping 7/8 → OKVED + Perplexity specialization
  6. Geo center wrong → fixed; geo is secondary
  7. Competitor INN "" → bo.nalog brand→INN
  8. revenue_source none → auto-fixed after INN resolution
"""

import asyncio
import json
import logging
import re
import time
from typing import Optional

from src.aim.services.brand_resolver import ResolvedBrand, resolve_brand_to_inn, resolve_brands_batch
from src.aim.services.lib.perplexity_client import perplexity_chat, is_configured as perplexity_configured
from src.aim.services.lib.searxng_client import searxng_search
from src.aim.services.nalog import BfoNalogClient
from src.aim.services.rusprofile.models import CompanyProfile, CompetitorMatch
from src.aim.services.service_extractor import extract_client_profile

logger = logging.getLogger(__name__)

# Revenue corridor: competitors between 0.3× and 3.0× of client revenue
_REVENUE_CORRIDOR_MIN = 0.3
_REVENUE_CORRIDOR_MAX = 3.0

# If fewer than this many competitors in the corridor, widen to 0.1× – 10×
_CORRIDOR_WIDEN_THRESHOLD = 3
_CORRIDOR_WIDE_MIN = 0.1
_CORRIDOR_WIDE_MAX = 10.0

# Revenue trend → human-readable Russian (for match_reason)
_TREND_RU = {
    "growing": "растёт",
    "stable": "стабилен",
    "declining": "снижается",
}


# ── Prompts ────────────────────────────────────────────────────────────

COMPETITOR_DISCOVERY_PROMPT = """Ты эксперт по рынку медицинских клиник России.
Клиника: {clinic_name} — специализация: {specialization}, город: {city}, выручка ~{revenue_desc}.

Назови 10 ПРЯМЫХ КОНКУРЕНТОВ этой клиники по принципам:
1. Схожесть услуг (та же специализация: {specialization})
2. Сопоставимый масштаб бизнеса (выручка от 30%% до 300%% от клиента)
3. Тот же город/регион: {city}

Для каждого конкурента:
- brand: брендовое название как оно известно на рынке
- surgeons_estimate: примерное число врачей/хирургов (целое число)

ВАЖНО:
- НЕ выдумывай ИНН — только брендовые названия
- Называй реальные клиники, которые существуют на рынке
- Если не уверен в числе хирургов — поставь примерную оценку

Верни ТОЛЬКО JSON массив, без markdown:
[{{"brand": "название", "surgeons_estimate": 10}}]"""

BRAND_EXTRACTION_PROMPT = """Ниже — результаты поиска о клиниках {specialization} в {city}.
Извлеки из них названия ВСЕХ клиник/центров, которые упоминаются.

РЕЗУЛЬТАТЫ ПОИСКА:
{snippets}

Верни ТОЛЬКО JSON массив названий клиник (строк). Без markdown, без объяснений.
Пример: ["Он Клиник", "Фрау Клиник"]"""


# ── Helpers ────────────────────────────────────────────────────────────

def _strip_markdown(text: str) -> str:
    """Strip markdown code fences from LLM response."""
    text = text.strip()
    if text.startswith("```"):
        # Remove first line (```json or ```)
        text = text.split("\n", 1)[1] if "\n" in text else text[3:]
        # Remove trailing ```
        if text.rstrip().endswith("```"):
            text = text.rstrip()[:-3]
    return text.strip()


def _format_revenue(revenue: Optional[int]) -> str:
    """Format revenue for prompt context."""
    if not revenue:
        return "неизвестна"
    if revenue >= 1_000_000_000:
        return f"{revenue / 1_000_000_000:.1f} млрд руб"
    if revenue >= 1_000_000:
        return f"{revenue / 1_000_000:.0f} млн руб"
    return f"{revenue:,} руб"


def _dedup_brands(brands: list[str]) -> list[str]:
    """Deduplicate brand names case-insensitively, preserving order."""
    seen = set()
    result = []
    for b in brands:
        key = b.lower().strip()
        if key and key not in seen:
            seen.add(key)
            result.append(b.strip())
    return result


# ── Main class ─────────────────────────────────────────────────────────

class CompetitorMatcherV2:
    """Hybrid competitor matcher: Perplexity + SearXNG → bo.nalog → ФНС."""

    def __init__(self):
        self.nalog = BfoNalogClient()
        self.last_is_megalopolis = False

    async def close(self):
        """Cleanup resources."""
        self.nalog.close()

    async def find_competitors(
        self,
        url: str,
        count: int = 5,
        named_competitors: Optional[list[str]] = None,
        client_revenue: Optional[int] = None,
    ) -> list[CompetitorMatch]:
        """Find competitors for a clinic URL using the hybrid pipeline.

        Args:
            url: Client clinic website URL.
            count: Number of competitors to return.
            named_competitors: Optional list of brand names to include.
            client_revenue: Optional client revenue override (RUB).

        Returns:
            List of CompetitorMatch sorted by revenue proximity to client.
        """
        t0 = time.monotonic()

        # ── STAGE 0: Client profile + INN + revenue ───────────────────
        client_profile = await extract_client_profile(url)
        specialization = client_profile.get("specialization", "")
        city = client_profile.get("city", "")
        company_name = client_profile.get("company_name")
        client_inn = client_profile.get("inn", "")

        logger.info(
            "CompetitorMatcherV2 stage 0: url=%s spec=%s city=%s company=%s inn=%s",
            url, specialization, city, company_name, client_inn or "None",
        )

        # If INN not on site → resolve via bo.nalog by company name
        if not client_inn and company_name:
            resolved_client = await resolve_brand_to_inn(company_name, nalog=self.nalog)
            if resolved_client:
                client_inn = resolved_client.inn
                logger.info("Client INN resolved via ФНС: %s → %s", company_name, client_inn)

        # Get real client revenue from ФНС
        client_revenue_real = await self._get_revenue_by_inn(client_inn)
        effective_revenue = (
            client_revenue_real
            or client_revenue
            or client_profile.get("estimated_revenue")
        )
        logger.info(
            "Client revenue: real=%s effective=%s",
            f"{client_revenue_real:,}" if client_revenue_real else "None",
            f"{effective_revenue:,}" if effective_revenue else "None",
        )

        # ── STAGE 1: Discover brands (2 channels parallel) ───────────
        perplexity_task = self._discover_via_perplexity(
            company_name, specialization, city, effective_revenue
        )
        searxng_task = self._discover_via_searxng(specialization, city)

        perplexity_brands, searxng_brands = await asyncio.gather(
            perplexity_task, searxng_task, return_exceptions=True,
        )

        # Handle exceptions gracefully
        if isinstance(perplexity_brands, Exception):
            logger.warning("Perplexity discovery failed: %s", perplexity_brands)
            perplexity_brands = []
        if isinstance(searxng_brands, Exception):
            logger.warning("SearXNG discovery failed: %s", searxng_brands)
            searxng_brands = []

        # Merge + dedup
        all_brands = _dedup_brands(
            list(perplexity_brands) + list(searxng_brands) + (named_competitors or [])
        )
        logger.info(
            "Stage 1: perplexity=%d searxng=%d merged=%d unique brands",
            len(perplexity_brands), len(searxng_brands), len(all_brands),
        )

        if not all_brands:
            logger.warning("No brands discovered for %s", url)
            return []

        # ── STAGE 2: Resolve brands → ИНН (bo.nalog) ──────────────────
        resolved = await resolve_brands_batch(all_brands)
        valid = [r for r in resolved if r is not None]
        rejected = len(all_brands) - len(valid)
        logger.info(
            "Stage 2: resolved %d/%d brands (%d rejected — not in ФНС)",
            len(valid), len(all_brands), rejected,
        )

        if not valid:
            logger.warning("No brands resolved to legal entities for %s", url)
            return []

        # ── STAGE 3: Enrich with ФНС financials + filter + sort ───────
        enriched = await self._enrich_all(valid, perplexity_brands)

        # Dedup by ИНН — multiple brand variants may resolve to the same legal entity
        # (e.g. "СМ-Клиника Волгоградский" and "СМ-Клиника Сенежская" → same ИНН)
        enriched = self._dedup_by_inn(enriched)

        # Revenue corridor filter
        filtered = self._filter_by_revenue_corridor(enriched, effective_revenue)

        # Sort: if client revenue known → by proximity; otherwise → by revenue desc
        if effective_revenue and effective_revenue > 0:
            filtered.sort(key=lambda m: abs((m.profile.revenue_year or 0) - effective_revenue))
        else:
            filtered.sort(key=lambda m: m.profile.revenue_year or 0, reverse=True)

        result = filtered[:count]

        elapsed = time.monotonic() - t0
        logger.info(
            "CompetitorMatcherV2 done: url=%s competitors=%d elapsed=%.1fs",
            url, len(result), elapsed,
        )
        return result

    # ── Stage 0 helpers ──────────────────────────────────────────────

    async def _get_revenue_by_inn(self, inn: str) -> Optional[int]:
        """Get real revenue from ФНС by INN."""
        if not inn or len(inn) < 10:
            return None
        try:
            results = await asyncio.to_thread(self.nalog.search, inn)
            if not results:
                return None
            org = results[0]
            if org.latest_revenue:
                return org.latest_revenue * 1000  # тыс.руб → RUB
        except Exception as e:
            logger.warning("Failed to get client revenue for inn=%s: %s", inn, e)
        return None

    # ── Stage 1: Discovery channels ──────────────────────────────────

    async def _discover_via_perplexity(
        self,
        company_name: Optional[str],
        specialization: str,
        city: str,
        revenue: Optional[int],
    ) -> list[str]:
        """Discover competitor brands via Perplexity (market knowledge)."""
        if not perplexity_configured():
            logger.warning("Perplexity not configured — skipping discovery channel")
            return []

        revenue_desc = _format_revenue(revenue)
        prompt = COMPETITOR_DISCOVERY_PROMPT.format(
            clinic_name=company_name or "клиника",
            specialization=specialization or "медицина",
            city=city or "Москва",
            revenue_desc=revenue_desc,
        )

        raw = await perplexity_chat(
            [{"role": "user", "content": prompt}],
            temperature=0.1,
        )
        cleaned = _strip_markdown(raw)

        try:
            data = json.loads(cleaned)
            brands = [item.get("brand", "").strip() for item in data if isinstance(item, dict)]
            # Store surgeons estimates for later enrichment
            self._perplexity_estimates = {
                item.get("brand", "").strip().lower(): item.get("surgeons_estimate")
                for item in data if isinstance(item, dict)
            }
            return [b for b in brands if b]
        except json.JSONDecodeError as e:
            logger.warning("Perplexity returned non-JSON: %s", e)
            return []

    async def _discover_via_searxng(
        self,
        specialization: str,
        city: str,
    ) -> list[str]:
        """Discover competitor brands via SearXNG + LLM extraction."""
        query = f"рейтинг топ лучших клиник {specialization or 'пластической хирургии'} {city or 'Москва'}"
        results = await searxng_search(query, limit=15)

        if not results:
            return []

        # Build snippets for LLM extraction
        snippets = []
        for r in results[:10]:
            title = r.get("title", "")[:100]
            content = (r.get("content", "") or "")[:120]
            snippets.append(f"- {title}: {content}")

        prompt = BRAND_EXTRACTION_PROMPT.format(
            specialization=specialization or "медицина",
            city=city or "Москва",
            snippets="\n".join(snippets),
        )

        # Use Perplexity for extraction (it's the LLM we have configured)
        if not perplexity_configured():
            # Fallback: extract brand-like patterns from titles
            return self._extract_brands_heuristic(results)

        raw = await perplexity_chat(
            [{"role": "user", "content": prompt}],
            temperature=0.1,
        )
        cleaned = _strip_markdown(raw)

        try:
            brands = json.loads(cleaned)
            if isinstance(brands, list):
                return [str(b).strip() for b in brands if b]
        except json.JSONDecodeError:
            pass

        return self._extract_brands_heuristic(results)

    def _extract_brands_heuristic(self, results: list[dict]) -> list[str]:
        """Fallback: extract clinic names from search result titles."""
        brands = []
        for r in results:
            title = r.get("title", "")
            # Look for patterns like "Клиника X", "Центр Y"
            match = re.search(r"(?:клиник[аы]|центр)\s+([«""]?[\w\s-]+[»""]?)", title, re.I)
            if match:
                brands.append(match.group(1).strip(" «»\""))
        return brands

    # ── Stage 3: Enrichment ──────────────────────────────────────────

    async def _enrich_all(
        self,
        resolved: list[ResolvedBrand],
        perplexity_brands: list[str],
    ) -> list[CompetitorMatch]:
        """Enrich all resolved brands with ФНС financials."""
        enriched = await asyncio.gather(
            *[self._enrich_one(r) for r in resolved],
            return_exceptions=True,
        )
        return [e for e in enriched if isinstance(e, CompetitorMatch)]

    async def _enrich_one(self, resolved: ResolvedBrand) -> CompetitorMatch:
        """Enrich a single resolved brand with ФНС financials."""
        # Get financial statements (sync → thread)
        try:
            statements = await asyncio.to_thread(
                self.nalog.get_financials, resolved.org_id
            )
        except Exception as e:
            logger.warning("Financials fetch failed for org_id=%s: %s", resolved.org_id, e)
            statements = []

        latest = statements[0] if statements else None
        revenue = latest.revenue_rub if latest else resolved.latest_revenue
        trend = latest.revenue_trend if latest else ""
        profit = latest.net_profit_rub if latest else None

        # Lookup surgeons estimate from Perplexity (if available)
        surgeons = None
        if hasattr(self, "_perplexity_estimates"):
            surgeons = self._perplexity_estimates.get(resolved.brand_query.lower())

        # Build match_reason
        reason_parts = []
        reason_parts.append(resolved.legal_name)
        if revenue:
            reason_parts.append(f"выручка {_format_revenue(revenue)}")
        if trend and trend in _TREND_RU:
            reason_parts.append(f"тренд: {_TREND_RU[trend]}")
        if resolved.okved:
            reason_parts.append(f"ОКВЭД: {resolved.okved}")
        if surgeons:
            reason_parts.append(f"~{surgeons} врачей")

        profile = CompanyProfile(
            inn=resolved.inn,
            legal_name=resolved.legal_name,
            brand_name=resolved.brand_query,
            okved_main=resolved.okved,
            revenue_year=revenue,
            profit_year=profit,
            revenue_trend=trend if trend else None,
            financial_year=int(latest.period) if latest else None,
            revenue_source="tax_filed" if latest else ("estimated" if resolved.latest_revenue else "none"),
            legal_address=resolved.address,
            employee_count=surgeons,
            data_source="bo_nalog_v2",
            confidence=0.95 if latest else 0.7,
        )

        return CompetitorMatch(
            profile=profile,
            match_reason=", ".join(reason_parts),
            data_quality=0.95 if latest else 0.6,
            total_score=1.0 if latest else 0.5,  # placeholder; revenue_proximity used for sorting
        )

    # ── Stage 3: Filtering ───────────────────────────────────────────

    def _dedup_by_inn(self, competitors: list[CompetitorMatch]) -> list[CompetitorMatch]:
        """Remove duplicates by ИНН — keep the one with the best brand name.

        Multiple brand queries (e.g. "СМ-Клиника Волгоградский",
        "СМ-Клиника Сенежская") may resolve to the same legal entity (same ИНН).
        We keep the first occurrence (most specific brand name) per ИНН.
        """
        seen_inns: dict[str, CompetitorMatch] = {}
        no_inn: list[CompetitorMatch] = []
        for c in competitors:
            inn = c.profile.inn.strip()
            if not inn:
                no_inn.append(c)
            elif inn not in seen_inns:
                seen_inns[inn] = c
        return list(seen_inns.values()) + no_inn

    def _filter_by_revenue_corridor(
        self,
        competitors: list[CompetitorMatch],
        client_revenue: Optional[int],
    ) -> list[CompetitorMatch]:
        """Filter competitors by revenue corridor relative to client.

        If client revenue is unknown, return all.
        Otherwise keep competitors within 0.3× – 3.0× of client revenue.
        Widen to 0.1× – 10× if too few remain.
        """
        if not client_revenue or client_revenue <= 0:
            return competitors

        has_rev = [c for c in competitors if c.profile.revenue_year and c.profile.revenue_year > 0]
        no_rev = [c for c in competitors if not c.profile.revenue_year]

        min_r = client_revenue * _REVENUE_CORRIDOR_MIN
        max_r = client_revenue * _REVENUE_CORRIDOR_MAX

        in_corridor = [c for c in has_rev if min_r <= c.profile.revenue_year <= max_r]

        if len(in_corridor) < _CORRIDOR_WIDEN_THRESHOLD:
            # Widen the corridor
            min_wide = client_revenue * _CORRIDOR_WIDE_MIN
            max_wide = client_revenue * _CORRIDOR_WIDE_MAX
            in_corridor = [c for c in has_rev if min_wide <= c.profile.revenue_year <= max_wide]

        # If still empty, use all with revenue
        if not in_corridor:
            in_corridor = has_rev

        # Append those without revenue at the end
        return in_corridor + no_rev
