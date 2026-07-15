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
from src.aim.services.lib.instagram_enricher import enrich_instagram_batch
from src.aim.services.nalog import BfoNalogClient, get_nalog_client
from src.aim.services.rusprofile.models import CompanyProfile, CompetitorMatch
from src.aim.services.service_extractor import extract_client_profile

logger = logging.getLogger(__name__)

# Revenue corridor: competitors between 0.1× and 10× of client revenue
# Wide corridor to ensure we get enough competitors even for very large clients
_REVENUE_CORRIDOR_MIN = 0.1
_REVENUE_CORRIDOR_MAX = 10.0

# Wider corridor fallback (used when too few competitors in the main corridor)
_CORRIDOR_WIDE_MIN = 0.05
_CORRIDOR_WIDE_MAX = 20.0

# If fewer than this many competitors in the corridor, return all with revenue
_CORRIDOR_WIDEN_THRESHOLD = 3

# Revenue trend → human-readable Russian (for match_reason)
_TREND_RU = {
    "growing": "растёт",
    "stable": "стабилен",
    "declining": "снижается",
}


# ── Prompts ────────────────────────────────────────────────────────────

COMPETITOR_DISCOVERY_PROMPT = """Ты эксперт по рынку медицинских клиник России.
Клиника: {clinic_name} — специализация: {specialization}, город: {city}, выручка ~{revenue_desc}.

Назови 12 ПРЯМЫХ КОНКУРЕНТОВ этой клиники по принципам:
1. Схожесть услуг (та же специализация: {specialization})
2. Сопоставимый масштаб бизнеса (выручка от 30%% до 300%% от клиента)
3. Тот же город/регион: {city}

Для каждого конкурента:
- brand: брендовое название как оно известно на рынке
- doctors_estimate: примерное число врачей/специалистов (целое число)

ВАЖНО:
- НЕ выдумывай ИНН — только брендовые названия
- Называй реальные клиники, которые существуют на рынке
- Если не уверен в числе врачей — поставь примерную оценку

Верни ТОЛЬКО JSON массив, без markdown:
[{{"brand": "название", "doctors_estimate": 10}}]"""

SIMPLE_DISCOVERY_PROMPT = """Назови 12 самых известных клиник {specialization} в {city}.
Только названия, по одному на строку. Без нумерации, без объяснений."""

BRAND_EXTRACTION_PROMPT = """Ниже — результаты поиска о клиниках {specialization} в {city}.
Извлеки из них названия ВСЕХ клиник/центров, которые упоминаются.

РЕЗУЛЬТАТЫ ПОИСКА:
{snippets}

Верни ТОЛЬКО JSON массив названий клиник (строк). Без markdown, без объяснений.
Пример: ["Он Клиник", "Фрау Клиник"]"""


# ── Helpers ────────────────────────────────────────────────────────────

_html_tag_re = re.compile(r"<[^>]+>")


def _strip_html_tags(text: str) -> str:
    """Strip HTML tags from bo.nalog API response (shortName contains <strong>)."""
    return _html_tag_re.sub("", text).strip()


def _build_org_address(item: dict) -> str:
    """Build address from bo.nalog org dict."""
    parts = [
        item.get("index"),
        item.get("region"),
        item.get("city"),
        item.get("street"),
        item.get("house"),
    ]
    return ", ".join(p for p in parts if p)


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
        self.nalog = get_nalog_client()  # singleton — cache survives between requests
        self.last_is_megalopolis = False

    async def close(self):
        """Cleanup resources. Note: nalog client is a singleton, NOT closed here."""
        pass

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

        # Resolve client INN with multi-level fallback
        if not client_inn:
            client_inn, inn_source = await self._resolve_client_inn(
                company_name, city, url, specialization
            )
            logger.info(
                "Client INN resolution: source=%s inn=%s",
                inn_source, client_inn or "None",
            )

        # Get real client revenue from ФНС
        client_revenue_real = await self._get_revenue_by_inn(client_inn)
        effective_revenue = (
            client_revenue_real
            or client_revenue
            or client_profile.get("estimated_revenue")
        )
        logger.info(
            "Client revenue: real=%s effective=%s source=%s",
            f"{client_revenue_real:,}" if client_revenue_real else "None",
            f"{effective_revenue:,}" if effective_revenue else "None",
            "ФНС" if client_revenue_real else "estimate",
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

        # ── STAGE 3.5a: Backfill from ОКВЭД registry if not enough competitors ─
        # If Perplexity+SearXNG gave fewer than requested, top up from
        # bo.nalog registry: top medical companies by revenue in the corridor.
        if len(result) < count:
            needed = count - len(result)
            existing_inns = {r.profile.inn for r in result if r.profile.inn}
            backfill = await self._backfill_from_okved_registry(
                specialization, city, effective_revenue, needed, existing_inns
            )
            result.extend(backfill)
            logger.info("backfill_from_okved: added %d competitors (total now %d)", len(backfill), len(result))

        # ── STAGE 3.5b: Post-selection enrichment (doctors + Instagram + website) ─
        # Only for the final top-N to keep it fast
        if result:
            from src.aim.services.lib.firecrawl_enricher import enrich_websites_batch
            await asyncio.gather(
                self._enrich_doctors_batch(result, city, count),
                enrich_instagram_batch(result, count, city),
                enrich_websites_batch(result, count),
                return_exceptions=True,
            )

        elapsed = time.monotonic() - t0
        surgeons_filled = sum(1 for r in result if r.profile.employee_count)
        ig_filled = sum(1 for r in result if r.profile.social_links.get("instagram"))
        logger.info(
            "CompetitorMatcherV2 done: url=%s competitors=%d elapsed=%.1fs "
            "client_revenue=%s surgeons_filled=%d instagram_filled=%d",
            url, len(result), elapsed,
            f"{effective_revenue:,}" if effective_revenue else "None",
            surgeons_filled, ig_filled,
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

    async def _resolve_client_inn(
        self,
        company_name: Optional[str],
        city: str,
        url: str,
        specialization: str,
    ) -> tuple[str, str]:
        """Resolve client INN with multi-level fallback.

        Tries in order:
          1. bo.nalog search by company_name (from site scrape)
          2. Perplexity: "какой ИНН у клиники X" → bo.nalog validation
          3. Gives up (returns empty)

        Returns:
            Tuple of (inn, source) where source ∈ {"bo_nalog", "perplexity", "failed"}.
        """
        # Level 1: bo.nalog search by company name
        if company_name:
            resolved = await resolve_brand_to_inn(company_name, nalog=self.nalog)
            if resolved and resolved.inn:
                return resolved.inn, "bo_nalog"

        # Level 2: Perplexity → extract INN → bo.nalog validate
        if perplexity_configured():
            query_name = company_name or specialization or url
            prompt = (
                f"Найди ИНН медицинской организации: {query_name}"
                f"{', ' + city if city else ''}. "
                f"Сайт: {url}\n"
                "Верни ТОЛЬКО число (10 или 12 цифр) или null. Без пояснений."
            )
            try:
                raw = await perplexity_chat(
                    [{"role": "user", "content": prompt}],
                    temperature=0.0,
                )
                # Extract digits from response
                inn_match = re.findall(r"\b(\d{10}|\d{12})\b", raw.strip())
                if inn_match:
                    candidate_inn = inn_match[0]
                    # Validate: does this INN exist in ФНС?
                    validated = await self._get_revenue_by_inn(candidate_inn)
                    if validated and validated > 0:
                        logger.info(
                            "Client INN via Perplexity: %s (revenue=%s)",
                            candidate_inn, f"{validated:,}",
                        )
                        return candidate_inn, "perplexity"
                    logger.warning(
                        "Perplexity INN %s not validated in ФНС", candidate_inn,
                    )
            except Exception as e:
                logger.warning("Perplexity INN resolution failed: %s", e)

        return "", "failed"

    # ── Stage 1: Discovery channels ──────────────────────────────────

    async def _discover_via_perplexity(
        self,
        company_name: Optional[str],
        specialization: str,
        city: str,
        revenue: Optional[int],
    ) -> list[str]:
        """Discover competitor brands via Perplexity with retry on empty results.

        Strategy:
          Attempt 1: rich JSON prompt (COMPETITOR_DISCOVERY_PROMPT)
          Attempt 2: simple line-by-line prompt (SIMPLE_DISCOVERY_PROMPT)
          Attempt 3: last chance with bare specialization+city
        If all attempts return 0 brands → empty list (SearXNG-only fallback).
        """
        if not perplexity_configured():
            logger.warning("Perplexity not configured — skipping discovery channel")
            return []

        revenue_desc = _format_revenue(revenue)
        spec = specialization or "медицина"
        ci = city or "Москва"

        self._perplexity_estimates = {}

        # ── Attempt 1: rich JSON prompt ──────────────────────────────
        prompt1 = COMPETITOR_DISCOVERY_PROMPT.format(
            clinic_name=company_name or "клиника",
            specialization=spec,
            city=ci,
            revenue_desc=revenue_desc,
        )
        brands = await self._try_perplexity_json(prompt1)
        if brands:
            logger.info("perplexity_attempt: n=1 brands=%d", len(brands))
            return brands

        # ── Attempt 2: simple line-by-line prompt ────────────────────
        logger.info("perplexity_retry: attempt=2 reason=empty_result")
        prompt2 = SIMPLE_DISCOVERY_PROMPT.format(specialization=spec, city=ci)
        brands = await self._try_perplexity_simple(prompt2)
        if brands:
            logger.info("perplexity_attempt: n=2 brands=%d", len(brands))
            return brands

        # ── Attempt 3: last chance — bare query ──────────────────────
        logger.info("perplexity_retry: attempt=3 reason=empty_result")
        prompt3 = f"Перечисли известные клиники {spec} в {ci}. Только названия."
        brands = await self._try_perplexity_simple(prompt3)
        if brands:
            logger.info("perplexity_attempt: n=3 brands=%d", len(brands))
        else:
            logger.warning("perplexity_all_attempts_empty: falling back to SearXNG-only")
        return brands

    async def _try_perplexity_json(self, prompt: str) -> list[str]:
        """Try Perplexity with JSON parsing. Returns brands or empty list."""
        try:
            raw = await perplexity_chat(
                [{"role": "user", "content": prompt}],
                temperature=0.1,
            )
            cleaned = _strip_markdown(raw)
            data = json.loads(cleaned)
            brands = [item.get("brand", "").strip() for item in data if isinstance(item, dict)]
            # Store doctors estimates for later enrichment
            self._perplexity_estimates = {
                item.get("brand", "").strip().lower(): item.get("doctors_estimate")
                for item in data if isinstance(item, dict)
            }
            return [b for b in brands if b]
        except (json.JSONDecodeError, KeyError, TypeError) as e:
            logger.debug("Perplexity JSON parse failed: %s", e)
            return []
        except Exception as e:
            logger.warning("Perplexity JSON call failed: %s", e)
            return []

    async def _try_perplexity_simple(self, prompt: str) -> list[str]:
        """Try Perplexity with plain-text line parsing. Returns brands or empty."""
        try:
            raw = await perplexity_chat(
                [{"role": "user", "content": prompt}],
                temperature=0.1,
            )
            # Parse line-by-line, skip empty and numbered lines
            brands = []
            for line in raw.strip().split("\n"):
                line = line.strip()
                # Strip leading numbers/bullets: "1. Clinic" → "Clinic"
                line = re.sub(r"^\d+[\.\)]\s*", "", line)
                line = line.lstrip("-•* ")
                if line and len(line) > 2:
                    brands.append(line)
            return brands
        except Exception as e:
            logger.warning("Perplexity simple call failed: %s", e)
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
        # Логируем исключения (не блокирующие)
        for i, e in enumerate(enriched):
            if isinstance(e, Exception):
                logger.warning("_enrich_one failed for brand=%s: %s: %s",
                    resolved[i].brand_query[:25] if i < len(resolved) else "?",
                    type(e).__name__, str(e)[:100])
        return [e for e in enriched if isinstance(e, CompetitorMatch)]

    async def _enrich_one(self, resolved: ResolvedBrand) -> CompetitorMatch:
        """Enrich a single resolved brand with ФНС financials + deep org data."""
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

        # ── Deep org data: registration_date + СЧЛ ──
        registration_date = None
        scl_count = None  # среднесписочная численность (все сотрудники)
        try:
            org_raw = await asyncio.to_thread(
                self.nalog.get_organization, resolved.org_id
            )
            if org_raw and isinstance(org_raw, dict):
                # bo.nalog.gov.ru: registrationDate (подтверждено из raw dict)
                registration_date = (
                    org_raw.get("registrationDate")
                    or org_raw.get("dtRegister")
                    or org_raw.get("regDate")
                )
                # СЧЛ: нет в get_organization, проверяем bfo/msp категории
                scl_count = (
                    org_raw.get("sclCount")
                    or org_raw.get("averageEmployees")
                    or org_raw.get("employeeCount")
                )
                if scl_count is not None:
                    try:
                        scl_count = int(scl_count)
                    except (ValueError, TypeError):
                        scl_count = None
        except Exception as e:
            logger.debug("get_organization failed for org_id=%s: %s", resolved.org_id, e)

        # ── Multi-year revenue dynamics ──
        from src.aim.services.nalog.models import compute_revenue_dynamics
        dynamics = compute_revenue_dynamics(statements) if statements else {"change_3yr_pct": None, "history": []}

        # Lookup doctors estimate from Perplexity discovery (if available)
        doctors = None
        if hasattr(self, "_perplexity_estimates"):
            doctors = self._perplexity_estimates.get(resolved.brand_query.lower())

        # СЧЛ приоритетнее Perplexity-оценки (реальные данные ФНС)
        employee_count = scl_count or doctors

        # Build match_reason
        reason_parts = []
        reason_parts.append(resolved.legal_name)
        if revenue:
            reason_parts.append(f"выручка {_format_revenue(revenue)}")
        if trend and trend in _TREND_RU:
            reason_parts.append(f"тренд: {_TREND_RU[trend]}")
        if dynamics.get("change_3yr_pct") is not None:
            reason_parts.append(f"динамика 3г: {dynamics['change_3yr_pct']:+.0f}%")
        if resolved.okved:
            reason_parts.append(f"ОКВЭД: {resolved.okved}")
        if scl_count:
            reason_parts.append(f"СЧЛ: {scl_count}")
        elif doctors:
            reason_parts.append(f"~{doctors} врачей")

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
            employee_count=employee_count,
            registration_date=registration_date,
            data_source="bo_nalog_v2",
            confidence=0.95 if latest else 0.7,
        )

        # Сохраняем dynamics в profile для последующей сериализации
        profile.scraped_services = dynamics.get("history", [])  # временный hack: храним в scraped_services

        return CompetitorMatch(
            profile=profile,
            match_reason=", ".join(reason_parts),
            data_quality=0.95 if latest else 0.6,
            total_score=1.0 if latest else 0.5,  # placeholder; revenue_proximity used for sorting
        )

    async def _enrich_doctors_batch(
        self,
        competitors: list[CompetitorMatch],
        city: str,
        max_count: int = 5,
    ) -> None:
        """Fill missing doctor counts via Perplexity for top-N competitors.

        Only enriches competitors where employee_count (doctors) is None.
        Uses Perplexity to estimate the number of doctors/specialists.
        Works for any specialization (surgeons, dentists, narcologists, etc).
        Modifies competitors in place.
        """
        if not perplexity_configured():
            return

        targets = [
            c for c in competitors[:max_count]
            if c.profile.employee_count is None
        ]
        if not targets:
            return

        semaphore = asyncio.Semaphore(3)  # Perplexity rate limit

        async def _ask_doctors(comp: CompetitorMatch) -> None:
            async with semaphore:
                brand = comp.profile.brand_name or comp.profile.legal_name or ""
                prompt = (
                    f"Сколько врачей работает в клинике \"{brand}\""
                    f"{', ' + city if city else ''}? "
                    "Верни ТОЛЬКО целое число (примерная оценка) или null."
                )
                try:
                    raw = await perplexity_chat(
                        [{"role": "user", "content": prompt}],
                        temperature=0.0,
                    )
                    # Parse number from response
                    numbers = re.findall(r"\b(\d+)\b", raw.strip())
                    if numbers:
                        count = int(numbers[0])
                        if 1 <= count <= 300:  # sanity check: 1-300 surgeons
                            comp.profile.employee_count = count
                            comp.match_reason += f", ~{count} врачей"
                            logger.info("doctors_estimate: %s → %d", brand, count)
                except Exception as e:
                    logger.debug("doctors_estimate failed for %s: %s", brand, e)

        await asyncio.gather(
            *[_ask_doctors(c) for c in targets],
            return_exceptions=True,
        )

    # ── Stage 3: Filtering ───────────────────────────────────────────

    async def _backfill_from_okved_registry(
        self,
        specialization: str,
        city: str,
        client_revenue: Optional[int],
        needed: int,
        exclude_inns: set[str],
    ) -> list[CompetitorMatch]:
        """Backfill competitors from bo.nalog ОКВЭД registry.

        When Perplexity+SearXNG don't yield enough, query bo.nalog with
        broad specialization terms + ОКВЭД 86.xx filter, sort by revenue
        in the client's corridor, and add the top-N not already in the list.

        These are legal entities (not brands) — we use their short_name as
        both brand and legal name, and flag data_source='okved_registry'.
        """
        if needed <= 0:
            return []

        # Broad query terms based on specialization
        spec = specialization or "медицина"
        # Map specializations to search terms
        search_terms_map = {
            "пластическая хирургия": ["пластик", "хирург", "косметолог", "эстет"],
            "косметология": ["косметолог", "эстет", "клиник"],
            "стоматология": ["стоматолог", "дент", "зуб"],
            "наркология": ["нарколог", "наркот"],
            "гинекология": ["гинеколог", "женск"],
        }
        terms = search_terms_map.get(spec.lower(), ["клиник", "медиц"])

        # Region code (77=Москва, 78=СПб, etc.)
        region_map = {"москва": "77", "санкт-петербург": "78", "спб": "78"}
        region = region_map.get((city or "").lower(), "77")

        # Collect orgs from multiple broad queries
        all_orgs: dict[str, dict] = {}  # inn → org dict (dedup by INN)
        from urllib.parse import quote_plus

        for term in terms:
            try:
                path = (
                    f"/advanced-search/organizations/search?"
                    f"query={quote_plus(term)}&okved=86.&region={region}"
                    f"&page=0&size=20"
                )
                data = await asyncio.to_thread(self.nalog._get, path)
                for org in data.get("content", []):
                    inn = org.get("inn", "").strip()
                    if inn and inn not in exclude_inns and inn not in all_orgs:
                        bfo = org.get("bfo") or {}
                        gain = bfo.get("gainSum") or 0
                        if gain > 0:  # only companies with actual revenue
                            all_orgs[inn] = {
                                "inn": inn,
                                "org_id": org.get("id"),
                                "name": _strip_html_tags(org.get("shortName", "")),
                                "okved": org.get("okved2", ""),
                                "gain": gain,  # тыс.руб
                                "address": _build_org_address(org),
                            }
            except Exception as e:
                logger.warning("okved_registry query failed for '%s': %s", term, e)

        if not all_orgs:
            logger.info("backfill_from_okved: no companies found")
            return []

        # Sort by revenue desc, filter to corridor
        sorted_orgs = sorted(all_orgs.values(), key=lambda o: o["gain"], reverse=True)

        # Corridor: same 0.1×-10× as main pipeline
        if client_revenue and client_revenue > 0:
            min_gain = (client_revenue * _REVENUE_CORRIDOR_MIN) / 1000  # RUB → тыс.руб
            max_gain = (client_revenue * _REVENUE_CORRIDOR_MAX) / 1000
            in_corridor = [o for o in sorted_orgs if min_gain <= o["gain"] <= max_gain]
            if len(in_corridor) >= 2:
                sorted_orgs = in_corridor
            # else: keep all sorted (corridor too narrow)

        # Take top-N needed
        selected = sorted_orgs[:needed]
        logger.info(
            "backfill_from_okved: %d candidates found, %d in corridor, selecting %d",
            len(all_orgs), len(sorted_orgs), len(selected),
        )

        # Convert to CompetitorMatch
        result: list[CompetitorMatch] = []
        for org in selected:
            revenue_rub = org["gain"] * 1000  # тыс.руб → RUB
            profile = CompanyProfile(
                inn=org["inn"],
                legal_name=org["name"],
                brand_name=org["name"],  # legal name as brand
                okved_main=org["okved"],
                revenue_year=revenue_rub,
                revenue_source="estimated",  # gainSum is approximate
                legal_address=org["address"],
                data_source="okved_registry",
                confidence=0.7,
            )
            result.append(CompetitorMatch(
                profile=profile,
                match_reason=f"{org['name']}, выручка {_format_revenue(revenue_rub)} (реестр ФНС)",
                data_quality=0.6,
                total_score=0.5,
            ))

        return result

    def _dedup_by_inn(self, competitors: list[CompetitorMatch]) -> list[CompetitorMatch]:
        """Confident-resolve dedup: one brand per ИНН.

        When multiple brands resolve to the same ИНН, keep only the one whose
        brand name best matches the legal entity name. Others are likely
        incorrect resolutions (bo.nalog fallback picked the wrong entity).

        Example: СМ-Клиника, ЛАНЦЕТЪ, Возрождение all → ИНН 2367011265 (КЛИНИКА ЛК).
        "СМ-Клиника" shares "клиник" with "КЛИНИКА ЛК" → confident match.
        "ЛАНЦЕТЪ" and "Возрождение" have no word overlap → dropped as uncertain.
        """
        # Group by ИНН
        by_inn: dict[str, list[CompetitorMatch]] = {}
        no_inn: list[CompetitorMatch] = []
        for c in competitors:
            inn = c.profile.inn.strip()
            if not inn:
                no_inn.append(c)
            else:
                by_inn.setdefault(inn, []).append(c)

        result: list[CompetitorMatch] = []
        for inn, group in by_inn.items():
            if len(group) == 1:
                # Only one brand for this ИНН → confident, keep it
                result.append(group[0])
                continue

            # Multiple brands → one ИНН: pick the most confident match
            brands = [c.profile.brand_name or c.profile.legal_name or "?" for c in group]
            logger.info("dedup_conflict: inn=%s brands=%s", inn, brands)

            def _name_overlap(c: CompetitorMatch) -> int:
                """Count overlapping word roots between brand and legal name."""
                brand = (c.profile.brand_name or "").lower()
                legal = (c.profile.legal_name or "").lower()
                # Remove common generic words
                generic = {"клиника", "клиник", "клинике", "ооо", "ао", "центр", "медицинский", "и"}
                brand_words = {w for w in brand.split() if w not in generic and len(w) > 2}
                legal_words = {w for w in legal.split() if len(w) > 2}
                return len(brand_words & legal_words)

            # Sort by name overlap descending (most confident first)
            group.sort(key=_name_overlap, reverse=True)
            winner = group[0]
            overlap = _name_overlap(winner)
            dropped = [c.profile.brand_name for c in group[1:]]

            if overlap > 0:
                # Winner has real name overlap → confident, keep it
                logger.info(
                    "dedup_resolved: inn=%s winner='%s' overlap=%d dropped=%s",
                    inn, winner.profile.brand_name, overlap, dropped,
                )
                result.append(winner)
            else:
                # No overlap for ANY brand → uncertain, keep first but warn
                logger.warning(
                    "dedup_uncertain: inn=%s no name overlap for any brand, keeping first: %s",
                    inn, winner.profile.brand_name,
                )
                result.append(winner)

        return result + no_inn

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
