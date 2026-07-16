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


def _same_address(addr1: str, addr2: str) -> bool:
    """Проверяет что два адреса — одно здание (улица + дом совпадают)."""
    if not addr1 or not addr2:
        return False
    # Нормализуем: нижний регистр, убираем лишнее
    import re
    def _norm(a: str) -> str:
        a = a.lower().strip()
        # Извлекаем улицу + дом (грубо: всё до запятой после "ул"/"улица"/"пр")
        a = re.sub(r"[,;]", " ", a)
        a = re.sub(r"\s+", " ", a)
        return a
    n1, n2 = _norm(addr1), _norm(addr2)
    # Проверяем что один содержит ключевые части другого
    # Извлекаем дом (число после "д" или в конце)
    house1 = re.search(r"(?:д\.?\s*|дом\s*)(\d+)", n1)
    house2 = re.search(r"(?:д\.?\s*|дом\s*)(\d+)", n2)
    if house1 and house2:
        return house1.group(1) == house2.group(1) and _street_match(n1, n2)
    # Fallback: проверяем что 80% одного адреса есть в другом
    shorter = n1 if len(n1) < len(n2) else n2
    longer = n2 if len(n1) < len(n2) else n1
    words = [w for w in shorter.split() if len(w) > 3]
    if not words:
        return False
    matches = sum(1 for w in words if w in longer)
    return matches / len(words) >= 0.8


def _street_match(addr1: str, addr2: str) -> bool:
    """Проверяет что улица совпадает (хотя бы 3 буквы корня)."""
    import re
    # Извлекаем название улицы (слово перед "ул"/"улица"/"пр")
    for pattern in [r"([а-яё]{4,})\s*(?:ул|улица|пр|проспект|пер|переулок)", r"(?:ул|улица)\s*([а-яё]{4,})"]:
        m1 = re.search(pattern, addr1)
        m2 = re.search(pattern, addr2)
        if m1 and m2:
            root = min(m1.group(1), m2.group(1), key=len)[:4]
            return root in m1.group(1) and root in m2.group(1)
    return True  # если не определили улицу — не блокируем


# Карта соответствия город → ключевые слова региона в ФНС-адресе.
# bo.nalog отдаёт region как "МОСКВА", "САНКТ-ПЕТЕРБУРГ", "МОСКОВСКАЯ" и т.д.
_CITY_REGION_KEYWORDS: dict[str, list[str]] = {
    "москва": ["МОСКВА", "МОСКОВСКАЯ"],
    "санкт-петербург": ["САНКТ-ПЕТЕРБУРГ", "ЛЕНИНГРАДСКАЯ"],
    "спб": ["САНКТ-ПЕТЕРБУРГ", "ЛЕНИНГРАДСКАЯ"],
    "питер": ["САНКТ-ПЕТЕРБУРГ", "ЛЕНИНГРАДСКАЯ"],
    "новосибирск": ["НОВОСИБИРСК"],
    "екатеринбург": ["СВЕРДЛОВСК", "ЕКАТЕРИНБУРГ"],
    "казань": ["ТАТАРСТАН", "КАЗАНЬ"],
    "нижний новгород": ["НИЖЕГОРОДСК", "НИЖНИЙ НОВГОРОД"],
    "краснодар": ["КРАСНОДАР"],
    "самара": ["САМАРА"],
    "ростов-на-дону": ["РОСТОВСК"],
    "уфа": ["БАШКОРТОСТАН", "УФА"],
    "красноярск": ["КРАСНОЯРСК"],
    "воронеж": ["ВОРОНЕЖ"],
    "пермь": ["ПЕРМСК"],
    "волгоград": ["ВОЛГОГРАД"],
}


def _is_same_city(address: str, city: str) -> bool:
    """Проверяет что ФНС-адрес конкурента в том же городе/регионе, что и клиент.

    address: legal_address из ФНС (например "634029, ТОМСКАЯ, ТОМСК, ГОГОЛЯ, 65")
    city: город клиента (например "Москва")

    Возвращает True если город неизвестен или не в карте (permissive),
    либо если адрес содержит ключевое слово региона города.
    """
    if not address or not city:
        return True  # не можем проверить — пропускаем
    keywords = _CITY_REGION_KEYWORDS.get(city.lower().strip())
    if not keywords:
        return True  # город не в карте — не блокируем (перmissive)
    addr_upper = address.upper()
    return any(kw in addr_upper for kw in keywords)


def _is_related_entity(competitor_name: str, client_name: str) -> bool:
    """Проверяет, является ли конкурент связанным юрлицом клиента.

    Связанные = дочерняя компания, филиал, тот же бренд.
    Эвристика: 3+ значимых слова из названия клиента есть в названии конкурента.
    Пример: IPHK "Институт пластической хирургии" → ЛАНЦЕТЪ "Институт пластической хирургии ЛАНЦЕТЪ" = related.
    """
    if not competitor_name or not client_name:
        return False
    comp_lower = competitor_name.lower()
    _GENERIC_WORDS = {"клиника", "клиник", "центр", "медицинский", "медицина",
                      "институт", "группа", "компания", "общество", "лечебный"}
    client_words = [w for w in client_name.split() if len(w) > 3 and w not in _GENERIC_WORDS]
    if not client_words:
        return False
    matches = sum(1 for w in client_words if w in comp_lower)
    # Если 3+ слова совпадают — почти точно связанное юрлицо
    return matches >= 3 and matches / len(client_words) >= 0.5


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

        # Сохранить для API response
        self.last_client_revenue = effective_revenue
        self.last_client_profit = None
        self.last_client_reg_date = None
        self.last_client_scl = None
        if client_inn and effective_revenue:
            try:
                results = await asyncio.to_thread(self.nalog.search, client_inn)
                if results:
                    org = results[0]
                    fins = await asyncio.to_thread(self.nalog.get_financials, org.id)
                    if fins:
                        self.last_client_profit = fins[0].net_profit_rub
                    # Deep org data для клиента
                    org_raw = await asyncio.to_thread(self.nalog.get_organization, org.id)
                    if org_raw and isinstance(org_raw, dict):
                        self.last_client_reg_date = (
                            org_raw.get("registrationDate")
                            or org_raw.get("dtRegister")
                        )
                        scl = (
                            org_raw.get("sclCount")
                            or org_raw.get("averageEmployees")
                        )
                        if scl:
                            try:
                                self.last_client_scl = int(scl)
                            except (ValueError, TypeError):
                                pass
            except Exception:
                pass

        logger.info(
            "Client revenue: real=%s effective=%s source=%s profit=%s",
            f"{client_revenue_real:,}" if client_revenue_real else "None",
            f"{effective_revenue:,}" if effective_revenue else "None",
            "ФНС" if client_revenue_real else "estimate",
            f"{self.last_client_profit:,}" if self.last_client_profit else "None",
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
        # max_brands=25: each resolved brand costs 2 ФНС API calls in enrichment.
        # Top-25 Perplexity brands is more than enough to pick 10 competitors.
        resolved = await resolve_brands_batch(all_brands, max_brands=25)
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

        # Dedup by ИНН
        enriched = self._dedup_by_inn(enriched)

        # Geo filter: keep only competitors in the client's city/region.
        # brand_resolver may resolve a brand to a company registered elsewhere.
        before_geo = len(enriched)
        enriched = [
            c for c in enriched
            if _is_same_city(c.profile.legal_address or "", city)
        ]
        geo_dropped = before_geo - len(enriched)
        if geo_dropped:
            logger.info(
                "geo_filter: city=%s dropped=%d competitors from other regions",
                city, geo_dropped,
            )

        # Filter out competitors related to client (same INN, same address, or name overlap)
        if client_inn:
            # Собираем имя клиента из всех источников
            client_name_lower = (
                company_name
                or client_profile.get("company_name")
                or client_profile.get("brand_name")
                or ""
            ).lower()
            # Если имени нет — извлекаем из URL домена
            if not client_name_lower and url:
                from urllib.parse import urlparse
                url_parsed = url if "://" in url else "https://" + url
                domain = urlparse(url_parsed).netloc.replace("www.", "").split(".")[0]
                client_name_lower = domain
            before_rel = len(enriched)
            # Также используем legal_name клиента из ФНС (через INN resolution)
            client_legal_name = ""
            try:
                client_results = await asyncio.to_thread(self.nalog.search, client_inn)
                if client_results:
                    client_legal_name = client_results[0].short_name.lower()
            except Exception:
                pass
            enriched = [
                c for c in enriched
                if c.profile.inn != client_inn
                and not (c.profile.legal_address and client_profile.get("address")
                         and _same_address(c.profile.legal_address, client_profile["address"]))
                and not _is_related_entity(c.profile.legal_name, client_name_lower)
                and not (client_legal_name and _is_related_entity(c.profile.legal_name, client_legal_name))
            ]
            removed = before_rel - len(enriched)
            if removed:
                logger.info("related_entity_filter: removed %d related competitors (client_name=%s)", removed, client_name_lower[:30])

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

        # ── STAGE 3.4: Deep ФНС enrichment for final top-N only ──────────
        # Fetch registration_date + scl_count via get_organization. This is a
        # second ФНС call per competitor, so we run it only for the final list
        # (typically 6-10) instead of all resolved brands (up to 25).
        await self._enrich_deep_batch(result)

        # ── STAGE 3.5b: Post-selection enrichment (doctors + Instagram + website) ─
        # Budget: enrich only top-5 to keep Firecrawl scrape volume low (~26% of
        # pipeline time was spent here on 10 competitors). Remaining competitors
        # still have full ФНС financials — just no website/CMS enrichment.
        _ENRICH_BUDGET = min(5, len(result))
        if result:
            from src.aim.services.lib.firecrawl_enricher import enrich_websites_batch
            await asyncio.gather(
                self._enrich_doctors_batch(result, city, _ENRICH_BUDGET),
                enrich_instagram_batch(result, _ENRICH_BUDGET, city),
                enrich_websites_batch(result, _ENRICH_BUDGET),
                return_exceptions=True,
            )

        # ── STAGE 3.5c: CLIENT website enrichment (Firecrawl + SEO audit) ──
        self.last_client_cms = None
        self.last_client_socials = None
        self.last_client_doctors = None
        self.last_client_audit = None
        if url:
            try:
                from src.aim.services.lib.seo_auditor import audit_website
                from src.aim.services.lib.firecrawl_enricher import scrape_website, scrape_doctors

                # Полный аудит (GEO + Schema + robots.txt + llms.txt + CMS)
                audit = await audit_website(url)
                self.last_client_audit = audit
                self.last_client_cms = audit.get("cms")

                # Соцсети + врачи из Firecrawl
                client_site = await scrape_website(url)
                if client_site.get("socials"):
                    self.last_client_socials = client_site["socials"]
                client_doc_count = await scrape_doctors(url, company_name or "")
                if client_doc_count:
                    self.last_client_doctors = client_doc_count

                logger.info(
                    "Client audit: GEO=%d CMS=%s schema_med=%s llms=%s socials=%s",
                    audit.get("geo_score", 0), audit.get("cms"),
                    bool(audit.get("schema", {}).get("medical")),
                    audit.get("llms_txt"),
                    list(self.last_client_socials.keys()) if self.last_client_socials else None,
                )
            except Exception as e:
                logger.warning("Client audit failed: %s", str(e)[:100])

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
          Level 0: extract company name from URL domain
          Level 1: bo.nalog exact search by company_name
          Level 2: Perplexity → extract INN → ФНС validation (precise)
          Level 3: bo.nalog spec search (LAST RESORT — imprecise, first match)

        Returns:
            Tuple of (inn, source) where source ∈ {"bo_nalog", "perplexity", "bo_nalog_spec", "failed"}.
        """
        # Level 0: если нет company_name — извлечь из URL (домен)
        if not company_name and url:
            try:
                from urllib.parse import urlparse
                # urlparse требует схему, иначе netloc пустой
                url_parsed = url if "://" in url else "https://" + url
                domain = urlparse(url_parsed).netloc.replace("www.", "")
                if domain:
                    # Домен → название (gmt-clinic.ru → "gmt clinic")
                    company_name = domain.split(".")[0].replace("-", " ").replace("_", " ")
                    logger.info("Client name from domain: %s → %s", domain, company_name)
            except Exception:
                pass

        # Level 1: bo.nalog search by company name (точное совпадение)
        if company_name:
            resolved = await resolve_brand_to_inn(company_name, nalog=self.nalog)
            if resolved and resolved.inn:
                return resolved.inn, "bo_nalog"

        # Level 2: Perplexity → extract INN → bo.nalog validate (ТОЧНЕЕ чем spec search)
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

        # Level 3 (LAST RESORT): bo.nalog spec search — берёт первую компанию
        # по специализации. Менее точный, но лучше чем ничего.
        if specialization:
            try:
                results = await asyncio.to_thread(self.nalog.search, f"{specialization} {city}")
                if results:
                    for org in results[:5]:
                        if "86" in (org.okved2 or ""):
                            rev = await self._get_revenue_by_inn(org.inn)
                            if rev and rev > 0:
                                logger.info("Client INN via bo.nalog spec search (last resort): %s", org.inn)
                                return org.inn, "bo_nalog_spec"
            except Exception as e:
                logger.debug("bo.nalog spec search failed: %s", e)

        return "", "failed"

    # ── Stage 1: Discovery channels ──────────────────────────────────

    async def _discover_via_perplexity(
        self,
        company_name: Optional[str],
        specialization: str,
        city: str,
        revenue: Optional[int],
    ) -> list[str]:
        """Discover competitor brands via Perplexity — 3 запроса с аккумуляцией.

        Раньше: 3 retry с early return (первый успешный → return).
        Сейчас: 3 разных промпта ПАРАЛЛЕЛЬНО → union всех брендов → дедуп.
        Это компенсирует недетерминированность Perplexity: каждый запрос
        даёт 5-8 брендов, в сумме 10-15 уникальных.
        """
        if not perplexity_configured():
            logger.warning("Perplexity not configured — skipping discovery channel")
            return []

        revenue_desc = _format_revenue(revenue)
        spec = specialization or "медицина"
        ci = city or "Москва"

        self._perplexity_estimates = {}

        # ── 3 разных промпта для максимизации покрытия ───────────────
        prompt1 = COMPETITOR_DISCOVERY_PROMPT.format(
            clinic_name=company_name or "клиника",
            specialization=spec,
            city=ci,
            revenue_desc=revenue_desc,
        )
        prompt2 = SIMPLE_DISCOVERY_PROMPT.format(specialization=spec, city=ci)
        prompt3 = f"Перечисли известные клиники {spec} в {ci}. Только названия, без описаний."

        # ── Параллельный запуск всех 3 промптов ─────────────────────
        results = await asyncio.gather(
            self._try_perplexity_json(prompt1),
            self._try_perplexity_simple(prompt2),
            self._try_perplexity_simple(prompt3),
            return_exceptions=True,
        )

        # ── Аккумуляция: union всех брендов с дедуп ──────────────────
        # Лимит: максимум 20 брендов от каждого промпта (снижает Stage 2 нагрузку)
        _MAX_BRANDS_PER_PROMPT = 20
        
        all_brands: list[str] = []
        seen: set[str] = set()
        for result in results:
            if isinstance(result, list):
                # Truncate to first 20 before accumulation
                for brand in result[:_MAX_BRANDS_PER_PROMPT]:
                    brand_lower = brand.lower().strip()
                    if brand_lower and brand_lower not in seen:
                        seen.add(brand_lower)
                        all_brands.append(brand)

        if all_brands:
            logger.info(
                "perplexity_accumulated: %d unique brands from 3 prompts (raw: %d/%d/%d)",
                len(all_brands),
                len(results[0]) if isinstance(results[0], list) else 0,
                len(results[1]) if isinstance(results[1], list) else 0,
                len(results[2]) if isinstance(results[2], list) else 0,
            )
        else:
            logger.warning("perplexity_all_attempts_empty: falling back to SearXNG-only")

        return all_brands

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

    async def _enrich_deep_batch(
        self, competitors: list[CompetitorMatch]
    ) -> None:
        """Fetch deep ФНС org data (registration_date, scl_count) for top-N.

        Modifies competitors in place. Only calls get_organization for companies
        that don't already have registration_date (e.g. backfill results already
        have it). Uses a semaphore to avoid hammering the ФНС API.
        """
        semaphore = asyncio.Semaphore(10)

        async def _deep_one(comp: CompetitorMatch) -> None:
            # Skip if already enriched or no INN
            if comp.profile.registration_date or not comp.profile.inn:
                return
            async with semaphore:
                try:
                    # Use saved org_id if available (avoids redundant nalog.search)
                    org_id = getattr(comp, "_org_id", None)
                    if not org_id:
                        results = await asyncio.to_thread(self.nalog.search, comp.profile.inn)
                        if not results:
                            return
                        org_id = results[0].id
                    org_raw = await asyncio.to_thread(
                        self.nalog.get_organization, org_id
                    )
                    if org_raw and isinstance(org_raw, dict):
                        reg = (
                            org_raw.get("registrationDate")
                            or org_raw.get("dtRegister")
                            or org_raw.get("regDate")
                        )
                        if reg:
                            comp.profile.registration_date = reg
                        scl = (
                            org_raw.get("sclCount")
                            or org_raw.get("averageEmployees")
                            or org_raw.get("employeeCount")
                        )
                        if scl is not None:
                            try:
                                scl_int = int(scl)
                                if scl_int > 0:
                                    comp.profile.employee_count = (
                                        scl_int or comp.profile.employee_count
                                    )
                            except (ValueError, TypeError):
                                pass
                except Exception as e:
                    logger.debug("deep_enrich failed for inn=%s: %s", comp.profile.inn, e)

        await asyncio.gather(
            *[_deep_one(c) for c in competitors],
            return_exceptions=True,
        )

    async def _enrich_one(self, resolved: ResolvedBrand) -> CompetitorMatch:
        """Enrich a single resolved brand with ФНС financials only (fast phase).

        Deep org data (registration_date, scl_count via get_organization) is
        deferred to _enrich_deep() which runs only for the final top-N after
        corridor + geo filtering. This halves the ФНС API calls for large brand
        lists (e.g. 38 brands → 38 financials instead of 38×2).
        """
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

        # Deep org data deferred to _enrich_deep (top-N only)
        registration_date = None
        scl_count = None

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

        # Сохраняем dynamics в profile
        profile.revenue_history = dynamics.get("history", [])

        match = CompetitorMatch(
            profile=profile,
            match_reason=", ".join(reason_parts),
            data_quality=0.95 if latest else 0.6,
            total_score=1.0 if latest else 0.5,  # placeholder; revenue_proximity used for sorting
        )
        # Save org_id for deep enrichment (avoids redundant nalog.search)
        match._org_id = resolved.org_id  # type: ignore[attr-defined]
        return match

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
            "пластическая хирургия": ["пластик", "хирург", "косметолог", "эстет", "красот", "клиник"],
            "косметология": ["косметолог", "эстет", "клиник", "красот"],
            "стоматология": ["стоматолог", "дент", "зуб"],
            "наркология": ["нарколог", "наркот"],
            "гинекология": ["гинеколог", "женск"],
        }
        terms = search_terms_map.get(spec.lower(), ["клиник", "медиц"])

        # bo.nalog API ignores the region query parameter — it returns companies
        # from all regions. We must filter client-side by the `region` field.
        # Region values for federal cities == city name (МОСКВА, САНКТ-ПЕТЕРБУРГ);
        # for oblast cities the region is the oblast name (МОСКОВСКАЯ, etc.).
        _CITY_REGION_MAP = {
            "москва": ["МОСКВА", "МОСКОВСКАЯ"],
            "санкт-петербург": ["САНКТ-ПЕТЕРБУРГ", "ЛЕНИНГРАДСКАЯ"],
            "спб": ["САНКТ-ПЕТЕРБУРГ", "ЛЕНИНГРАДСКАЯ"],
            "питер": ["САНКТ-ПЕТЕРБУРГ", "ЛЕНИНГРАДСКАЯ"],
            "новосибирск": ["НОВОСИБИРСКАЯ"],
            "екатеринбург": ["СВЕРДЛОВСКАЯ"],
            "казань": ["ТАТАРСТАН"],
            "нижний новгород": ["НИЖЕГОРОДСКАЯ"],
            "краснодар": ["КРАСНОДАРСКИЙ"],
            "самара": ["САМАРСКАЯ"],
            "ростов-на-дону": ["РОСТОВСКАЯ"],
            "уфа": ["БАШКОРТОСТАН"],
            "красноярск": ["КРАСНОЯРСКИЙ"],
            "воронеж": ["ВОРОНЕЖСКАЯ"],
            "пермь": ["ПЕРМСКИЙ"],
            "волгоград": ["ВОЛГОГРАДСКАЯ"],
        }
        city_key = (city or "").lower().strip()
        allowed_regions = _CITY_REGION_MAP.get(city_key)
        # Region code for the API query (best-effort; API often ignores it)
        _region_code_map = {"москва": "77", "санкт-петербург": "78", "спб": "78"}
        region_code = _region_code_map.get(city_key, "77")

        # Collect orgs from multiple broad queries
        all_orgs: dict[str, dict] = {}  # inn → org dict (dedup by INN)
        geo_rejected = 0
        from urllib.parse import quote_plus

        for term in terms:
            try:
                path = (
                    f"/advanced-search/organizations/search?"
                    f"query={quote_plus(term)}&okved=86.&region={region_code}"
                    f"&page=0&size=50"
                )
                data = await asyncio.to_thread(self.nalog._get, path)
                for org in data.get("content", []):
                    inn = org.get("inn", "").strip()
                    if inn and inn not in exclude_inns and inn not in all_orgs:
                        bfo = org.get("bfo") or {}
                        gain = bfo.get("gainSum") or 0
                        if gain > 0:  # only companies with actual revenue
                            # Geo filter: API ignores region param, so verify
                            org_region = (org.get("region") or "").upper().strip()
                            if allowed_regions and not any(
                                org_region.startswith(ar) for ar in allowed_regions
                            ):
                                geo_rejected += 1
                                continue
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

        logger.info(
            "backfill_geo_filter: city=%s allowed_regions=%s kept=%d rejected=%d",
            city, allowed_regions, len(all_orgs), geo_rejected,
        )

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

        # Convert to CompetitorMatch — fetch financials concurrently.
        # Deep org data (registration_date, scl_count) is handled by
        # _enrich_deep_batch() which runs after backfill — avoids duplicate
        # get_organization calls.
        _bf_sem = asyncio.Semaphore(10)

        async def _build_match(org: dict) -> CompetitorMatch:
            org_id = org.get("org_id")
            revenue_rub = org["gain"] * 1000  # тыс.руб → RUB
            profit = None
            trend = ""
            revenue_source = "estimated"

            if org_id:
                async with _bf_sem:
                    try:
                        statements = await asyncio.to_thread(
                            self.nalog.get_financials, org_id
                        )
                        if statements:
                            latest_fin = statements[0]
                            revenue_rub = latest_fin.revenue_rub or revenue_rub
                            profit = latest_fin.net_profit_rub
                            trend = latest_fin.revenue_trend
                            revenue_source = "tax_filed"
                    except Exception as e:
                        logger.debug("backfill get_financials failed org_id=%s: %s", org_id, e)

            profile = CompanyProfile(
                inn=org["inn"],
                legal_name=org["name"],
                brand_name=org["name"],
                okved_main=org["okved"],
                revenue_year=revenue_rub,
                profit_year=profit,
                revenue_trend=trend if trend else None,
                revenue_source=revenue_source,
                legal_address=org["address"],
                employee_count=None,  # filled by _enrich_deep_batch
                registration_date=None,  # filled by _enrich_deep_batch
                data_source="okved_registry",
                confidence=0.85 if revenue_source == "tax_filed" else 0.7,
            )
            reason = f"{org['name']}, выручка {_format_revenue(revenue_rub)} (реестр ФНС)"
            if profit:
                reason += f", прибыль {_format_revenue(profit)}"
            if trend and trend in _TREND_RU:
                reason += f", тренд: {_TREND_RU[trend]}"

            return CompetitorMatch(
                profile=profile,
                match_reason=reason,
                data_quality=0.8 if revenue_source == "tax_filed" else 0.6,
                total_score=0.5,
            )

        result = list(await asyncio.gather(
            *[_build_match(org) for org in selected],
            return_exceptions=True,
        ))
        # Filter out exceptions
        result = [r for r in result if isinstance(r, CompetitorMatch)]

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
            # Нет выручки клиента → топ по выручке (не возвращать мусор)
            has_rev = [c for c in competitors if c.profile.revenue_year and c.profile.revenue_year > 0]
            no_rev = [c for c in competitors if not c.profile.revenue_year]
            sorted_rev = sorted(has_rev, key=lambda c: c.profile.revenue_year, reverse=True)
            return sorted_rev + no_rev

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
