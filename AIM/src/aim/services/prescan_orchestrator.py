"""PrescanOrchestrator — parallel pre-sale intelligence gathering.

Launches 5 reconnaissance threads simultaneously for a client website:
  1. Website structure (services, specialization, city, doctors, prices)
  2. Financial data (rusprofile/nalog by INN)
  3. Quick SEO scan (meta tags, mobile viewport, SSL, load speed)
  4. Reviews snapshot (first 20, rating, praise/complaint themes)
  5. Social media (last post date, platform)

Returns an aggregated PrescanResult for Hermes to narrate conversationally.
Total target: 60-90 seconds (dominated by slowest thread — Apify/Playwright).
"""

from __future__ import annotations

import asyncio
import re
import time
from dataclasses import dataclass, field
from typing import Optional
from urllib.parse import urlparse

import httpx

from aim.config.logging import get_logger

logger = get_logger("aim.services.prescan_orchestrator")

# ═══════════════════════════════════════════════════════════════════════════
# Data models
# ═══════════════════════════════════════════════════════════════════════════


@dataclass
class PrescanResult:
    """Aggregated result from all 5 prescan threads."""

    # ── Website structure ──
    specialization: str = ""
    city: str = ""
    services: list[str] = field(default_factory=list)
    doctors: list[dict] = field(default_factory=list)  # [{name, title, order}]
    price_hints: list[dict] = field(default_factory=list)  # [{service, price}]

    # ── Financials ──
    inn: str = ""
    revenue_year: Optional[int] = None
    profit_year: Optional[int] = None
    financial_year: Optional[int] = None

    # ── SEO quick scan ──
    seo_score: int = 0
    seo_issues: list[str] = field(default_factory=list)
    has_mobile_viewport: bool = False
    has_ssl: bool = False
    load_speed_ms: int = 0

    # ── Reviews ──
    rating: Optional[float] = None
    reviews_count: int = 0
    review_praise: list[str] = field(default_factory=list)
    review_complaints: list[str] = field(default_factory=list)

    # ── Social ──
    last_post_date: Optional[str] = None
    last_post_platform: Optional[str] = None
    social_links: dict[str, str] = field(default_factory=dict)

    # ── Errors (non-fatal) ──
    errors: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "specialization": self.specialization,
            "city": self.city,
            "services": self.services,
            "doctors": self.doctors,
            "price_hints": self.price_hints,
            "inn": self.inn,
            "revenue_year": self.revenue_year,
            "profit_year": self.profit_year,
            "financial_year": self.financial_year,
            "seo_score": self.seo_score,
            "seo_issues": self.seo_issues,
            "has_mobile_viewport": self.has_mobile_viewport,
            "has_ssl": self.has_ssl,
            "load_speed_ms": self.load_speed_ms,
            "rating": self.rating,
            "reviews_count": self.reviews_count,
            "review_praise": self.review_praise,
            "review_complaints": self.review_complaints,
            "last_post_date": self.last_post_date,
            "last_post_platform": self.last_post_platform,
            "social_links": self.social_links,
            "errors": self.errors,
        }


# ═══════════════════════════════════════════════════════════════════════════
# Orchestrator
# ═══════════════════════════════════════════════════════════════════════════


class PrescanOrchestrator:
    """Launches 5 parallel reconnaissance threads for a client website.

    Usage::

        orchestrator = PrescanOrchestrator()
        result = await orchestrator.prescan("https://clinic.ru",
                                             progress_callback=my_callback)
        print(result.specialization, result.revenue_year)
        await orchestrator.close()
    """

    def __init__(self) -> None:
        self._http_client: Optional[httpx.AsyncClient] = None

    async def _get_http(self) -> httpx.AsyncClient:
        if self._http_client is None:
            self._http_client = httpx.AsyncClient(
                timeout=httpx.Timeout(15.0),
                follow_redirects=True,
                verify=False,
                headers={
                    "User-Agent": (
                        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                        "AppleWebKit/537.36 (KHTML, like Gecko) "
                        "Chrome/148.0.0.0 Safari/537.36"
                    ),
                },
            )
        return self._http_client

    async def close(self) -> None:
        if self._http_client is not None:
            await self._http_client.aclose()
            self._http_client = None

    async def prescan(
        self,
        url: str,
        progress_callback=None,
    ) -> PrescanResult:
        """Run all 5 prescan threads in parallel and aggregate results.

        Args:
            url: Client clinic website URL.
            progress_callback: Optional async callable(thread_name, status, data).
                               Called as each thread produces results.

        Returns:
            PrescanResult with all gathered intelligence.
        """
        if not url.startswith(("http://", "https://")):
            url = "https://" + url

        result = PrescanResult()
        t0 = time.monotonic()

        async def _emit(thread: str, status: str) -> None:
            if progress_callback:
                try:
                    await progress_callback(thread, status)
                except Exception:
                    pass

        # ── Thread 1: Website structure ─────────────────────────────────
        async def _thread_structure():
            await _emit("structure", "scanning")
            try:
                from aim.services.service_extractor import extract_client_profile

                profile = await extract_client_profile(url)
                if profile:
                    result.specialization = str(profile.get("specialization", ""))
                    result.city = str(profile.get("city", ""))
                    result.services = list(profile.get("services", []) or [])
                    result.doctors = list(profile.get("doctors", []) or [])
                    result.price_hints = list(profile.get("price_hints", []) or [])
                    result.inn = profile.get("inn") or ""
                await _emit("structure", "done")
            except Exception as e:
                logger.warning("Prescan structure thread failed: %s", e)
                result.errors.append(f"structure: {e}")
                await _emit("structure", "failed")

        # ── Thread 2: Financials ────────────────────────────────────────
        async def _thread_financials():
            await _emit("financials", "scanning")
            try:
                # First extract INN if not already from structure
                inn = result.inn
                if not inn:
                    inn = await self._extract_inn_from_site(url)

                # Fallback: search rusprofile by company name
                if not inn:
                    inn = await self._extract_inn_by_name(url)

                if inn:
                    result.inn = inn
                    financials = await self._fetch_nalog_financials(inn)
                    if financials:
                        result.revenue_year = financials.get("revenue_year")
                        result.profit_year = financials.get("profit_year")
                        result.financial_year = financials.get("financial_year")
                await _emit("financials", "done")
            except Exception as e:
                logger.warning("Prescan financials thread failed: %s", e)
                result.errors.append(f"financials: {e}")
                await _emit("financials", "failed")

        # ── Thread 3: SEO quick scan ─────────────────────────────────────
        async def _thread_seo():
            await _emit("seo", "scanning")
            try:
                seo_data = await self._quick_seo_scan(url)
                result.seo_score = seo_data.get("score", 0)
                result.seo_issues = seo_data.get("issues", [])
                result.has_mobile_viewport = seo_data.get("has_mobile_viewport", False)
                result.has_ssl = seo_data.get("has_ssl", False)
                result.load_speed_ms = seo_data.get("load_speed_ms", 0)
                await _emit("seo", "done")
            except Exception as e:
                logger.warning("Prescan SEO thread failed: %s", e)
                result.errors.append(f"seo: {e}")
                await _emit("seo", "failed")

        # ── Thread 4: Reviews ───────────────────────────────────────────
        async def _thread_reviews():
            await _emit("reviews", "scanning")
            try:
                reviews = await self._quick_reviews(url, result.specialization, result.city)
                result.rating = reviews.get("rating")
                result.reviews_count = reviews.get("count", 0)
                result.review_praise = reviews.get("praise", [])
                result.review_complaints = reviews.get("complaints", [])
                await _emit("reviews", "done")
            except Exception as e:
                logger.warning("Prescan reviews thread failed: %s", e)
                result.errors.append(f"reviews: {e}")
                await _emit("reviews", "failed")

        # ── Thread 5: Social ────────────────────────────────────────────
        async def _thread_social():
            await _emit("social", "scanning")
            try:
                social = await self._quick_social_scan(url)
                result.last_post_date = social.get("last_post_date")
                result.last_post_platform = social.get("last_post_platform")
                result.social_links = social.get("links", {})
                await _emit("social", "done")
            except Exception as e:
                logger.warning("Prescan social thread failed: %s", e)
                result.errors.append(f"social: {e}")
                await _emit("social", "failed")

        # Launch all 5 threads in parallel
        await asyncio.gather(
            _thread_structure(),
            _thread_financials(),
            _thread_seo(),
            _thread_reviews(),
            _thread_social(),
        )

        elapsed = time.monotonic() - t0
        logger.info(
            "Prescan complete in %.1fs: specialization=%s city=%s revenue=%s "
            "seo=%s rating=%s reviews=%d errors=%d",
            elapsed,
            result.specialization,
            result.city,
            result.revenue_year,
            result.seo_score,
            result.rating,
            result.reviews_count,
            len(result.errors),
        )

        return result

    # ── Financials helpers ──────────────────────────────────────────────

    async def _extract_inn_from_site(self, url: str) -> str:
        """Extract INN from clinic website (footer, contacts, about pages)."""
        inn_re = re.compile(
            r'(?:ИНН|INN|инн|inn)\s*[:;]?\s*(\d{10,12})',
            re.IGNORECASE,
        )
        paths = ["", "/about", "/contacts", "/kontakty", "/o-klinike", "/rekvizity"]
        http = await self._get_http()

        for path in paths[:4]:
            try:
                target = url.rstrip("/") + (path if path else "")
                r = await http.get(target)
                for m in inn_re.finditer(r.text):
                    raw = m.group(1)
                    if self._is_valid_inn(raw):
                        return raw
            except Exception:
                continue
        return ""

    async def _extract_inn_by_name(self, url: str) -> str:
        """Fallback: find INN via DaData API by company name.

        Used when the website doesn't display INN in footer/contacts.
        Extracts brand name from <title>, searches DaData, returns
        the best-match INN.
        """
        company_name = await self._extract_brand_name(url)
        if not company_name or len(company_name) < 5:
            return ""

        try:
            from aim.services.rusprofile.client import get_dadata_client

            client = get_dadata_client()
            if not client.configured:
                return ""

            profiles = await client.search_company(company_name, count=5)
            if not profiles:
                return ""

            # Pick first result with valid INN
            for profile in profiles:
                inn = profile.inn
                if inn and self._is_valid_inn(inn):
                    logger.info(
                        "Found INN via DaData: '%s' → INN %s (%s)",
                        company_name, inn, profile.legal_name[:60],
                    )
                    return inn
        except Exception as e:
            logger.debug("DaData name search failed for '%s': %s", company_name, e)

        return ""

    @staticmethod
    def _is_valid_inn(inn: str) -> bool:
        """Basic INN checksum validation (Russian taxpayer ID)."""
        if not inn or not inn.isdigit():
            return False
        if len(inn) == 10:  # Legal entity
            coeffs = [2, 4, 10, 3, 5, 9, 4, 6, 8]
            checksum = sum(int(inn[i]) * coeffs[i] for i in range(9)) % 11 % 10
            return checksum == int(inn[9])
        if len(inn) == 12:  # Individual entrepreneur
            coeffs1 = [7, 2, 4, 10, 3, 5, 9, 4, 6, 8]
            checksum1 = sum(int(inn[i]) * coeffs1[i] for i in range(10)) % 11 % 10
            coeffs2 = [3, 7, 2, 4, 10, 3, 5, 9, 4, 6, 8]
            checksum2 = sum(int(inn[i]) * coeffs2[i] for i in range(11)) % 11 % 10
            return checksum1 == int(inn[10]) and checksum2 == int(inn[11])
        return False

    async def _fetch_nalog_financials(self, inn: str) -> dict:
        """Fetch financial data from bo.nalog.gov.ru by INN.

        Note: bo.nalog.gov.ru returns values in thousands of rubles
        (Russian accounting standard). We multiply by 1000 to convert
        to actual RUB for consistency with the rest of the system.
        """
        try:
            from aim.services.nalog.bfo_client import BfoNalogClient

            client = BfoNalogClient(timeout=8.0)
            try:
                orgs = client.search(inn)
                if orgs:
                    org = orgs[0]
                    result = {}
                    if org.latest_revenue:
                        result["revenue_year"] = org.latest_revenue * 1000
                        result["financial_year"] = org.latest_period

                    # Try to get net profit from detailed financials
                    try:
                        fin = client.get_latest_financials(org.id)
                        if fin:
                            result["profit_year"] = fin.net_profit * 1000 if fin.net_profit else None
                            if not result["financial_year"]:
                                result["financial_year"] = fin.period
                    except Exception:
                        pass

                    return result
            finally:
                client.close()
        except Exception as e:
            logger.debug("Nalog fetch failed for INN %s: %s", inn, e)
        return {}

    # ── SEO helpers ─────────────────────────────────────────────────────

    async def _quick_seo_scan(self, url: str) -> dict:
        """Quick SEO analysis: meta tags, mobile, SSL, basic speed."""
        result = {
            "score": 70,
            "issues": [],
            "has_mobile_viewport": False,
            "has_ssl": False,
            "load_speed_ms": 0,
        }

        if url.startswith("https://"):
            result["has_ssl"] = True

        http = await self._get_http()
        try:
            t0 = time.monotonic()
            r = await http.get(url)
            result["load_speed_ms"] = int((time.monotonic() - t0) * 1000)

            html = r.text.lower()

            # Check meta viewport (mobile-friendly)
            if 'meta name="viewport"' in html or "meta name='viewport'" in html:
                result["has_mobile_viewport"] = True
            else:
                result["issues"].append("не адаптирован под мобильные (нет viewport meta)")
                result["score"] -= 15

            # Check for title
            if "<title>" not in html or "<title></title>" in html:
                result["issues"].append("отсутствует title — страница не оптимизирована для поиска")
                result["score"] -= 10

            # Check for description meta
            if 'name="description"' not in html and "name='description'" not in html:
                result["issues"].append("отсутствует meta description")
                result["score"] -= 5

            # Speed check
            if result["load_speed_ms"] > 3000:
                result["issues"].append(f"медленная загрузка ({result['load_speed_ms'] / 1000:.1f} сек)")
                result["score"] -= 10

            # Check for h1
            if "<h1" not in html:
                result["issues"].append("отсутствует H1 заголовок")
                result["score"] -= 5

        except Exception as e:
            logger.debug("SEO quick scan failed for %s: %s", url, e)
            result["issues"].append(f"не удалось просканировать сайт: {e}")
            result["score"] = 0

        result["score"] = max(0, min(100, result["score"]))
        return result

    # ── Reviews helpers ─────────────────────────────────────────────────

    async def _extract_brand_name(self, url: str) -> str:
        """Extract brand name from <title> tag of the website.

        Domain-based names (iphk.ru → "Iphk") fail on Russian review platforms
        that expect Cyrillic names. The <title> tag usually contains the real name,
        e.g. "Институт пластической хирургии и косметологии - официальный сайт".
        """
        try:
            http = await self._get_http()
            r = await http.get(url)
            match = re.search(r'<title>(.+?)</title>', r.text, re.IGNORECASE)
            if match:
                title = match.group(1).strip()
                # Strip common suffixes: separators, "официальный сайт", city, etc.
                for sep in [' — ', ' - ', ' – ', ' | ', ' :: ', ' – ']:
                    if sep in title:
                        title = title.split(sep)[0].strip()
                # Remove common boilerplate
                for suffix in [
                    'официальный сайт', 'Официальный сайт',
                    'клиники в Москве', 'клиники в Санкт-Петербурге',
                    'в Москве', 'в Санкт-Петербурге',
                    'Москва', 'Санкт-Петербург',
                ]:
                    title = re.sub(rf'\s*[—–-]?\s*{re.escape(suffix)}\s*$', '', title)
                if len(title) >= 3 and not title.startswith('http'):
                    logger.debug("Extracted brand name from title: %s", title)
                    return title
        except Exception as e:
            logger.debug("Brand name extraction failed for %s: %s", url, e)
        return ""

    async def _quick_reviews(self, url: str, specialization: str, city: str) -> dict:
        """Quick review snapshot: rating, count.

        Uses the existing ReviewCollector (Playwright) if available,
        with a tight 25-second timeout — just enough for 1-2 platforms.

        Note: praise/complaints are left empty here. Real theme extraction
        requires NLP over individual review texts (future enhancement).
        Hermes uses rating + count + specialization to comment intelligently.
        """
        result = {"rating": None, "count": 0, "praise": [], "complaints": []}

        try:
            from aim.services.ci.review_collector import ReviewCollector, AggregatedReviews

            # Extract the real brand name from <title> tag, not domain.
            # Domain-based names (iphk.ru → "Iphk") fail on Cyrillic platforms.
            company_name = await self._extract_brand_name(url)
            if not company_name:
                domain = urlparse(url).netloc.replace("www.", "")
                company_name = domain.split(".")[0].replace("-", " ").title()

            logger.info("Quick reviews: searching for '%s' in %s", company_name, city or "Москва")

            collector = ReviewCollector()
            try:
                await asyncio.wait_for(collector.start(), timeout=15)
                reviews: AggregatedReviews = await asyncio.wait_for(
                    collector.collect(company_name, city or "Москва"), timeout=25
                )
                if reviews and reviews.platforms:
                    result["rating"] = round(reviews.avg_rating, 1)
                    result["count"] = reviews.total_reviews
                    logger.info("Quick reviews found: rating=%s count=%s platforms=%s",
                                result["rating"], result["count"], len(reviews.platforms))
            finally:
                await collector.close()
        except asyncio.TimeoutError:
            logger.warning("Quick reviews timed out for %s — skipping", url)
        except ImportError:
            logger.warning("ReviewCollector not available — skipping quick reviews")
        except Exception as e:
            logger.warning("Quick reviews failed for %s: %s", url, e)

        return result

    # ── Social helpers ──────────────────────────────────────────────────

    async def _quick_social_scan(self, url: str) -> dict:
        """Extract social links from website and check last post dates."""
        result: dict = {
            "last_post_date": None,
            "last_post_platform": None,
            "links": {},
        }

        try:
            http = await self._get_http()
            r = await http.get(url)
            html = r.text.lower()

            # Extract social links from the page
            social_domains = {
                "vk.com": "vk",
                "t.me": "telegram",
                "telegram.me": "telegram",
                "instagram.com": "instagram",
                "youtube.com": "youtube",
                "ok.ru": "odnoklassniki",
                "dzen.ru": "dzen",
            }

            for domain, platform in social_domains.items():
                pattern = rf'https?://(?:www\.)?{re.escape(domain)}/[^\s"\'<>]+'
                matches = re.findall(pattern, r.text, re.IGNORECASE)
                if matches and platform not in result["links"]:
                    result["links"][platform] = matches[0]

            # Try to find platform links in non-lowercase HTML too
            href_pattern = re.compile(
                r'href=["\'](https?://(?:www\.)?(vk\.com|t\.me|telegram\.me|instagram\.com)[^"\']+)["\']',
                re.IGNORECASE,
            )
            for m in href_pattern.finditer(r.text):
                link = m.group(1)
                domain = m.group(2).lower()
                platform_map = {"vk.com": "vk", "t.me": "telegram",
                                "telegram.me": "telegram", "instagram.com": "instagram"}
                platform = platform_map.get(domain)
                if platform and platform not in result["links"]:
                    result["links"][platform] = link

        except Exception as e:
            logger.debug("Social quick scan failed for %s: %s", url, e)

        # For now, last_post_date requires deeper Instagram/VK API access.
        # We just return the links found — Hermes can note which platforms
        # are present.
        return result
