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

    # ── Competitors ──
    nearby_competitors: list[dict] = field(default_factory=list)

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
            "nearby_competitors": self.nearby_competitors,
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
        paths = [
            "", "/about", "/contacts", "/kontakty", "/o-klinike", "/rekvizity",
            "/about/legal-information", "/about/rekvizity",
            "/o-kompanii/rekvizity", "/legal",
        ]
        http = await self._get_http()

        for path in paths:
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
        """Extract brand name from <title> and og:site_name meta tags.

        Domain-based names (iphk.ru → "Iphk") fail on Russian review platforms
        that expect Cyrillic names. The <title> tag usually contains the real name,
        e.g. "Институт пластической хирургии и косметологии - официальный сайт".

        Falls back to og:site_name when title-based brand looks like a generic
        locale descriptor rather than a real brand name.
        """
        import re as _re
        try:
            http = await self._get_http()
            r = await http.get(url)
            html = r.text

            # Extract og:site_name as potential fallback
            og_site = None
            og_match = _re.search(
                r'<meta[^>]+property=["\']og:site_name["\'][^>]+content=["\']([^"\']+)["\']',
                html, _re.IGNORECASE,
            )
            if not og_match:
                og_match = _re.search(
                    r'<meta[^>]+content=["\']([^"\']+)["\'][^>]+property=["\']og:site_name["\']',
                    html, _re.IGNORECASE,
                )
            if og_match:
                og_site = og_match.group(1).strip()

            match = _re.search(r'<title>(.+?)</title>', html, _re.IGNORECASE)
            if match:
                title = match.group(1).strip()
                parts = None
                for sep in [' — ', ' - ', ' – ', ' | ', ' :: ', ' – ']:
                    if sep in title:
                        parts = [p.strip() for p in title.split(sep, 1)]
                        break

                if parts and len(parts) == 2:
                    boilerplate_labels = {
                        'коммерческое предложение', 'главная', 'главная страница',
                        'home', 'home page', 'index',
                    }
                    first_lower = parts[0].lower()
                    has_latin = bool(_re.search(r'[a-zA-Z]', parts[0]))
                    if not has_latin and (first_lower in boilerplate_labels or
                        (len(parts[0]) < 25 and len(parts[1]) > len(parts[0]) * 2)):
                        title = parts[1]
                    else:
                        title = parts[0]
                elif parts and len(parts) > 2:
                    meaningful = [p for p in parts if p.lower() not in {
                        'коммерческое предложение', 'главная', 'главная страница',
                        'home', 'home page',
                    }]
                    title = meaningful[0] if meaningful else parts[0]

                # Remove common boilerplate suffixes
                for suffix in [
                    'официальный сайт', 'Официальный сайт',
                    'клиники в Москве', 'клиники в Санкт-Петербурге',
                    'в Москве', 'в Санкт-Петербурге',
                    'Москва', 'Санкт-Петербург',
                ]:
                    title = _re.sub(rf'\s*[—–-]?\s*{_re.escape(suffix)}\s*$', '', title)

                # If title-based brand looks like a generic locale descriptor,
                # prefer og:site_name (which is usually the real brand)
                GENERIC_PATTERNS = [
                    r'^стоматология\s+в\s+\S+',       # "Стоматология в Зеленограде"
                    r'^клиника\s+\S+\s+\S+',          # "Клиника профессора Юцковской"
                    r'^стоматологическая\s+клиника',
                ]
                is_generic = len(title) > 30 or any(
                    _re.search(p, title, _re.IGNORECASE) for p in GENERIC_PATTERNS
                )
                if is_generic and og_site and len(og_site) >= 3:
                    logger.debug("Title brand '%s' looks generic, using og:site_name '%s'",
                                 title, og_site)
                    title = og_site

                if len(title) >= 3 and not title.startswith('http'):
                    logger.debug("Extracted brand name: %s", title)
                    return title

            # No title tag — use og:site_name directly
            if og_site and len(og_site) >= 3:
                return og_site
        except Exception as e:
            logger.debug("Brand name extraction failed for %s: %s", url, e)
        return ""

    async def _extract_city_from_html(self, html: str) -> str:
        """Extract city from page HTML — address patterns, Yandex Maps links, geo meta."""
        import re as _re

        city_patterns = [
            # Schema.org address
            r'"addressLocality"\s*:\s*"([^"]+)"',
            r'<meta[^>]+name=["\']address["\'][^>]+content=["\']([^"\']*?)[,\s]*["\']',
            # Yandex Maps widget — city in coordinates or address
            r'yandex\.ru/maps/.*?/[^/]+/([^/]+)/',
            # Address text: "г. Москва", "Санкт-Петербург", etc.
            r'г\.\s*([А-ЯЁ][а-яё]+(?:\s*[-–]\s*[А-ЯЁ][а-яё]+)?)',
            r'город\s+([А-ЯЁ][а-яё]+(?:\s*[-–]\s*[А-ЯЁ][а-яё]+)?)',
            # "Москва", "Санкт-Петербург" on contact pages
        ]

        russian_cities = [
            'Москва', 'Санкт-Петербург', 'Новосибирск', 'Екатеринбург',
            'Казань', 'Нижний Новгород', 'Челябинск', 'Самара', 'Омск',
            'Ростов-на-Дону', 'Уфа', 'Красноярск', 'Воронеж', 'Пермь',
            'Волгоград', 'Краснодар',
        ]

        # Districts/suburbs that should map to parent cities for Yandex Maps search
        suburb_to_city = {
            'Зеленоград': 'Москва',
            'Троицк': 'Москва',
            'Щербинка': 'Москва',
            'Московский': 'Москва',
            'Пушкин': 'Санкт-Петербург',
            'Петергоф': 'Санкт-Петербург',
            'Колпино': 'Санкт-Петербург',
            'Сестрорецк': 'Санкт-Петербург',
        }

        for pattern in city_patterns:
            m = _re.search(pattern, html, _re.IGNORECASE)
            if m:
                candidate = m.group(1).strip()
                if len(candidate) >= 2:
                    return suburb_to_city.get(candidate, candidate)

        # Fallback: scan for known city names
        body = html[:50000]  # first 50KB is enough
        for city in russian_cities:
            if city in body:
                return city

        return ""

    async def _quick_reviews(self, url: str, specialization: str, city: str) -> dict:
        """Quick review snapshot: rating, count, and per-platform data.

        Uses the existing ReviewCollector (Playwright) if available,
        with a tight 25-second timeout — just enough for 1-2 platforms.

        Returns dict with:
          - rating, count, praise, complaints (aggregated)
          - yandex_maps: {found, rating, reviews, url} (from ReviewCollector)
        """
        result = {
            "rating": None, "count": 0, "praise": [], "complaints": [],
            "yandex_maps": {"found": False, "rating": None, "reviews": None, "url": ""},
            "prodoctorov": {"found": False, "rating": None, "reviews": None, "url": ""},
        }

        try:
            from aim.services.ci.review_collector import ReviewCollector, AggregatedReviews

            # Extract the real brand name from <title> tag, not domain.
            company_name = await self._extract_brand_name(url)
            if not company_name:
                domain = urlparse(url).netloc.replace("www.", "")
                company_name = domain.split(".")[0].replace("-", " ").title()

            # Fix: Extract city from page HTML if not already set.
            # _thread_reviews runs in parallel with _thread_structure which sets
            # result.city — if city is empty, reviews defaults to "Москва" and
            # misses regional clinics (e.g. ARclinic in Санкт-Петербург).
            if not city:
                try:
                    http = await self._get_http()
                    r = await http.get(url)
                    city = await self._extract_city_from_html(r.text)
                except Exception:
                    pass

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

                    # Extract Yandex Maps + ProDoctorov data from platform results
                    for p in reviews.platforms:
                        if p.platform == "yandex_maps" and not p.error:
                            result["yandex_maps"] = {
                                "found": True,
                                "rating": p.rating,
                                "reviews": p.reviews_count,
                                "url": p.url,
                            }
                        elif p.platform == "prodoctorov" and not p.error:
                            result["prodoctorov"] = {
                                "found": True,
                                "rating": p.rating,
                                "reviews": p.reviews_count,
                                "url": p.url,
                            }

                    logger.info("Quick reviews found: rating=%s count=%s yandex=%s platforms=%s",
                                result["rating"], result["count"],
                                result["yandex_maps"]["found"], len(reviews.platforms))
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

    # ═══════════════════════════════════════════════════════════════════════
    # Staged Pipeline (Phase 23)
    # ═══════════════════════════════════════════════════════════════════════

    async def prescan_staged(
        self,
        url: str,
        progress_callback=None,
        force_refresh: bool = False,
    ) -> dict:
        """Run 3-stage ultra-deep prescan with progressive results.

        Stages:
          1. Финансовый хук (20-30s) — revenue, profit, legal entity
          2. Под капотом (40-60s) — licenses, founders, deep SEO, reviews, social
          3. Рынок (60-90+s) — maps, competitors, revenue trends, content audit

        Each stage fires progress_callback(stage_number, stage_name, summary, is_final).
        Results are cached in company_profiles for instant repeat lookups.
        """
        if not url.startswith(("http://", "https://")):
            url = "https://" + url

        t0 = time.monotonic()
        errors: list[str] = []

        # ── Cache check ───────────────────────────────────────────────────
        if not force_refresh:
            cached = await self._cache_get(url)
            if cached:
                logger.info("prescan_staged: cache hit for %s (%.0fms)", url,
                            (time.monotonic() - t0) * 1000)
                return cached

        # ── Stage 1: Финансовый хук ───────────────────────────────────────
        try:
            stage_1_data = await self._stage_1_financials(url)
        except Exception as e:
            stage_1_data = {"_errors": [f"stage_1: {e}"]}
        stage_1_errors = stage_1_data.pop("_errors", [])
        errors.extend(stage_1_errors)
        if progress_callback:
            try:
                await progress_callback(1, "Финансовый хук", stage_1_data, False)
            except Exception:
                pass

        # ── Stage 2: Под капотом ──────────────────────────────────────────
        try:
            stage_2_data = await self._stage_2_deep(url, stage_1_data)
        except Exception as e:
            stage_2_data = {"_errors": [f"stage_2: {e}"]}
        stage_2_errors = stage_2_data.pop("_errors", [])
        errors.extend(stage_2_errors)
        if progress_callback:
            try:
                await progress_callback(2, "Под капотом", stage_2_data, False)
            except Exception:
                pass

        # ── Stage 3: Рынок ────────────────────────────────────────────────
        try:
            stage_3_data = await self._stage_3_market(url, stage_1_data, stage_2_data)
        except Exception as e:
            stage_3_data = {"_errors": [f"stage_3: {e}"]}
        stage_3_errors = stage_3_data.pop("_errors", [])
        errors.extend(stage_3_errors)
        if progress_callback:
            try:
                await progress_callback(3, "Рынок", stage_3_data, True)
            except Exception:
                pass

        # ── Merge & cache ──────────────────────────────────────────────────
        profile_data = {
            "stage_1": stage_1_data,
            "stage_2": stage_2_data,
            "stage_3": stage_3_data,
        }
        if errors:
            profile_data["_errors"] = errors

        inn = stage_1_data.get("legal_entity", {}).get("inn", "")
        await self._cache_put(url, inn, profile_data)

        elapsed = time.monotonic() - t0
        logger.info("prescan_staged complete in %.1fs: %d errors", elapsed, len(errors))
        return profile_data

    # ── Stage 1: Финансовый хук ───────────────────────────────────────────

    async def _stage_1_financials(self, url: str) -> dict:
        """Stage 1: financial hook — revenue, profit, legal entity, structure."""
        errors: list[str] = []
        inn = ""
        legal_entity: dict = {}
        revenue_data: dict = {"latest": None, "by_year": {}, "trend": "unknown"}
        profit_data: dict = {"latest": None, "by_year": {}}
        specialization = ""
        city = ""
        services: list = []
        doctors: list = []

        # ── 1a. Website structure ─────────────────────────────────────────
        try:
            from aim.services.service_extractor import extract_client_profile

            profile = await extract_client_profile(url)
            if profile:
                specialization = str(profile.get("specialization", ""))
                city = str(profile.get("city", ""))
                services = list(profile.get("services", []) or [])
                doctors = list(profile.get("doctors", []) or [])
                inn = profile.get("inn") or ""
        except Exception as e:
            errors.append(f"structure: {e}")

        # ── 1b. INN extraction ────────────────────────────────────────────
        if not inn:
            try:
                inn = await self._extract_inn_from_site(url)
            except Exception as e:
                errors.append(f"inn_site: {e}")

        if not inn:
            try:
                inn = await self._extract_inn_by_name(url)
            except Exception as e:
                errors.append(f"inn_name: {e}")

        # ── 1c. DaData legal entity ───────────────────────────────────────
        if inn:
            try:
                from aim.services.rusprofile.client import get_dadata_client

                client = get_dadata_client()
                if client.configured:
                    profiles = await client.search_company(inn, count=1)
                    if profiles:
                        p = profiles[0]
                        years = 0
                        if p.registration_date:
                            try:
                                from datetime import datetime as dt_mod
                                rd = dt_mod.strptime(p.registration_date, "%Y-%m-%d")
                                years = dt_mod.now().year - rd.year
                            except Exception:
                                pass
                        legal_entity = {
                            "inn": p.inn or inn,
                            "ogrn": p.ogrn or "",
                            "legal_name": p.legal_name or "",
                            "registration_date": p.registration_date or "",
                            "years_on_market": years,
                            "okved_main": p.okved_main or "",
                            "legal_address": p.legal_address or "",
                            "authorized_capital": None,
                        }
            except Exception as e:
                errors.append(f"dadata: {e}")

            # Always store INN even without DaData
            if not legal_entity:
                legal_entity = {"inn": inn}

        # ── 1d. ГИР БО financials ─────────────────────────────────────────
        if inn:
            try:
                fin = await self._fetch_nalog_financials(inn)
                revenue_data["latest"] = fin.get("revenue_year")
                profit_data["latest"] = fin.get("profit_year")
                if fin.get("revenue_year"):
                    revenue_data["by_year"][str(fin.get("financial_year", ""))] = fin["revenue_year"]
                if fin.get("profit_year"):
                    profit_data["by_year"][str(fin.get("financial_year", ""))] = fin["profit_year"]

                # Sanity check: medical clinics rarely exceed 500M RUB/year
                rev = fin.get("revenue_year")
                if rev and rev > 500_000_000:
                    logger.warning(
                        "Revenue sanity check failed: INN=%s revenue=%.0fM RUB — "
                        "likely wrong INN (third-party processor?)",
                        inn, rev / 1_000_000,
                    )
                    errors.append(
                        f"revenue_sanity: выручка {rev/1_000_000:.0f}M RUB "
                        f"для ИНН {inn} — возможно, ошибочный ИНН"
                    )
            except Exception as e:
                errors.append(f"nalog: {e}")

        brand_name = await self._extract_brand_name(url)

        summary: dict = {
            "brand_name": brand_name,
            "revenue": revenue_data,
            "profit": profit_data,
            "legal_entity": legal_entity,
            "specialization": specialization,
            "city": city,
            "services": services,
            "doctors": doctors,
        }
        if errors:
            summary["_errors"] = errors
        return summary

    # ── Stage 2: Под капотом ──────────────────────────────────────────────

    async def _stage_2_deep(self, url: str, stage_1: dict) -> dict:
        """Stage 2: deep analysis — licenses, founders, SEO, reviews, social."""
        errors: list[str] = []
        le = stage_1.get("legal_entity", {})
        inn = le.get("inn", "")
        legal_name = le.get("legal_name", "")
        specialization = str(stage_1.get("specialization", ""))
        city = str(stage_1.get("city", ""))

        # ── 2a. DaData founders/management ────────────────────────────────
        founders: list = []
        general_director: dict = {}
        if inn:
            try:
                from aim.services.rusprofile.client import get_dadata_client
                client = get_dadata_client()
                if client.configured:
                    profiles = await client.search_company(inn, count=1)
                    if profiles:
                        p = profiles[0]
                        if p.management:
                            general_director = {
                                "name": p.management.get("name", ""),
                                "position": p.management.get("post", ""),
                            }
                        if p.founders:
                            founders = p.founders
            except Exception as e:
                errors.append(f"founders: {e}")

        # ── 2b. Roszdravnadzor licenses ───────────────────────────────────
        licenses: list = []
        if legal_name or inn:
            try:
                from aim.services.roszdravnadzor.client import RoszdravnadzorClient
                rzd = RoszdravnadzorClient(timeout=8.0)
                try:
                    licenses = await rzd.search_licenses(legal_name, inn=inn)
                finally:
                    await rzd.close()
            except Exception as e:
                errors.append(f"licenses: {e}")

        # ── 2c. Deep SEO scan ─────────────────────────────────────────────
        seo_data: dict = {
            "score": 70, "issues": [],
            "has_mobile_viewport": False, "has_ssl": url.startswith("https://"),
            "load_speed_ms": 0,
            "has_sitemap": False, "sitemap_urls": None,
            "has_structured_data": False, "structured_data_types": [],
            "h1_count": 0, "meta_description": "",
        }
        try:
            http = await self._get_http()
            t0 = time.monotonic()
            r = await http.get(url)
            seo_data["load_speed_ms"] = int((time.monotonic() - t0) * 1000)
            html = r.text.lower()

            if 'meta name="viewport"' in html or "meta name='viewport'" in html:
                seo_data["has_mobile_viewport"] = True
            else:
                seo_data["issues"].append("не адаптирован под мобильные")
                seo_data["score"] -= 15

            if "<title>" not in html or "<title></title>" in html:
                seo_data["issues"].append("отсутствует title")
                seo_data["score"] -= 10

            import re as _re
            desc_match = _re.search(
                r'<meta[^>]+name=["\']description["\'][^>]+content=["\']([^"\']*)["\']', r.text,
                _re.IGNORECASE,
            )
            if desc_match:
                seo_data["meta_description"] = desc_match.group(1)[:200]
            else:
                seo_data["issues"].append("отсутствует meta description")
                seo_data["score"] -= 5

            seo_data["h1_count"] = len(_re.findall(r'<h1[>\s]', html))
            if seo_data["h1_count"] == 0:
                seo_data["issues"].append("отсутствует H1")
                seo_data["score"] -= 5

            # Sitemap check
            sitemap_r = await http.get(url.rstrip("/") + "/sitemap.xml")
            if sitemap_r.status_code == 200 and "<?xml" in sitemap_r.text.lower():
                seo_data["has_sitemap"] = True
                sitemap_urls = _re.findall(r'<loc>(.+?)</loc>', sitemap_r.text)
                seo_data["sitemap_urls"] = len(sitemap_urls)

            # Structured data
            structured_types = _re.findall(
                r'"(?:@type|@context)"[^}]*"(Medical\w+|Physician|Hospital|LocalBusiness|Organization)"',
                r.text, _re.IGNORECASE,
            )
            if structured_types:
                seo_data["has_structured_data"] = True
                seo_data["structured_data_types"] = list(set(structured_types))

            if seo_data["load_speed_ms"] > 3000:
                seo_data["issues"].append(
                    f"медленная загрузка ({seo_data['load_speed_ms']/1000:.1f}с)"
                )
                seo_data["score"] -= 10

            seo_data["score"] = max(0, min(100, seo_data["score"]))

            # ── Platform detection ──────────────────────────────────────
            platform = "unknown"
            platform_markers = {
                "tilda": ["tilda.ws", "tildacdn", "tilda", "tildafiles"],
                "wordpress": ["wp-content", "wordpress", "wp-json"],
                "1c-bitrix": ["bitrix24", "bitrix", "1c-bitrix", "bx_site"],
                "joomla": ["joomla", "com_content"],
                "wix": ["wix.com", "wixstatic"],
                "drupal": ["drupal", "sites/default/files"],
            }
            for name, markers in platform_markers.items():
                if any(m in html for m in markers):
                    platform = name
                    break
            seo_data["platform"] = platform

            if platform == "tilda":
                seo_data["issues"].append("сайт на конструкторе Tilda")
                seo_data["score"] -= 10
        except Exception as e:
            errors.append(f"seo: {e}")

        # ── 2d. Reviews ───────────────────────────────────────────────────
        reviews = await self._quick_reviews(url, specialization, city)

        # ── 2e. Social media ──────────────────────────────────────────────
        social = await self._quick_social_scan(url)

        summary: dict = {
            "licenses": licenses,
            "founders": founders,
            "general_director": general_director,
            "seo_deep": seo_data,
            "reviews": reviews,
            "social": social,
        }
        if errors:
            summary["_errors"] = errors
        return summary

    # ── Stage 3: Рынок ────────────────────────────────────────────────────

    async def _stage_3_market(self, url: str, stage_1: dict, stage_2: dict) -> dict:
        """Stage 3: market position — revenue trends, maps, competitors, content."""
        errors: list[str] = []
        le = stage_1.get("legal_entity", {})
        inn = le.get("inn", "")
        legal_name = le.get("legal_name", "")
        city = str(stage_1.get("city", ""))
        specialization = str(stage_1.get("specialization", ""))

        # ── 3a. Multi-year revenue trends ─────────────────────────────────
        revenue_multi_year: dict = {}
        if inn:
            try:
                from aim.services.nalog.bfo_client import BfoNalogClient
                client = BfoNalogClient(timeout=8.0)
                try:
                    orgs = client.search(inn)
                    if orgs:
                        fs_list = client.get_financials(orgs[0].id)
                        for fs in fs_list:
                            if fs.period and fs.revenue:
                                revenue_multi_year[str(fs.period)] = fs.revenue * 1000
                finally:
                    client.close()
            except Exception as e:
                errors.append(f"revenue_trends: {e}")

        # ── 3b. Content audit ─────────────────────────────────────────────
        content_audit: dict = {
            "total_pages_estimated": 0, "has_blog": False,
            "thin_content_pages": 0, "avg_title_length": 0,
            "titles_sample": [],
        }
        try:
            http = await self._get_http()
            r = await http.get(url)
            html_lower = r.text.lower()

            # Detect blog
            if any(seg in html_lower for seg in ["/blog", "/news", "/articles", "/stati"]):
                content_audit["has_blog"] = True

            # Estimate total pages from internal links (absolute + relative)
            import re as _re
            base = url.rstrip("/")
            # Absolute links to same domain
            abs_links = _re.findall(
                rf'href=["\']({_re.escape(base)}[^"\']*)["\']', r.text,
                _re.IGNORECASE,
            )
            # Relative links (starting with / but not //)
            rel_links = _re.findall(
                r'href=["\'](/(?![/])[^"\']*)["\']', r.text,
                _re.IGNORECASE,
            )
            # Bare relative links (no leading /, no protocol) — e.g. href="about", href="uslugi"
            bare_rel = _re.findall(
                r'href=["\']([a-zA-Zа-яА-ЯёЁ0-9][a-zA-Zа-яА-ЯёЁ0-9._-]*(?:/[a-zA-Zа-яА-ЯёЁ0-9._-]+)*)["\']',
                r.text, _re.IGNORECASE,
            )
            all_links = (
                set(abs_links)
                | {f"{base}{rl}" for rl in rel_links}
                | {f"{base}/{br}" for br in bare_rel}
            )
            STATIC_EXTS = (
                '.css', '.js', '.png', '.jpg', '.jpeg', '.ico', '.svg',
                '.woff2', '.woff', '.ttf', '.eot', '.webp', '.gif',
                '.mp4', '.pdf', '.xml',
            )
            page_links = set()
            for link in all_links:
                if link.startswith(('mailto:', 'tel:', 'javascript:', '#')):
                    continue
                clean = link.split('?')[0].split('#')[0]
                if clean.endswith(STATIC_EXTS):
                    continue
                page_links.add(link)
            content_audit["total_pages_estimated"] = max(len(page_links), 1)

            # Sitemap fallback — always try if count looks low, prefer sitemap if better
            try:
                sm = await http.get(f"{base}/sitemap.xml")
                if sm.status_code == 200 and "<urlset" in sm.text.lower():
                    sm_urls = _re.findall(r'<loc>(.+?)</loc>', sm.text)
                    if sm_urls and len(sm_urls) > content_audit["total_pages_estimated"]:
                        content_audit["total_pages_estimated"] = len(sm_urls)
            except Exception:
                pass

            # Title samples
            titles = _re.findall(r'<title>(.+?)</title>', r.text, _re.IGNORECASE)
            if titles:
                content_audit["titles_sample"] = titles[:5]
                content_audit["avg_title_length"] = sum(len(t) for t in titles) // len(titles)
        except Exception as e:
            errors.append(f"content_audit: {e}")

        # ── 3c. Yandex/Google Maps — reuse ReviewCollector data from Stage 2 ─
        stage_2_reviews = stage_2.get("reviews", {})
        yandex_from_reviews = stage_2_reviews.get("yandex_maps", {})
        if yandex_from_reviews and yandex_from_reviews.get("found"):
            yandex_maps = {
                "found": True,
                "rating": yandex_from_reviews.get("rating"),
                "reviews": yandex_from_reviews.get("reviews"),
                "address": yandex_from_reviews.get("address", ""),
                "coordinates": yandex_from_reviews.get("coordinates", {}),
                "photos": yandex_from_reviews.get("photos"),
                "working_hours": yandex_from_reviews.get("working_hours", ""),
                "url": yandex_from_reviews.get("url", ""),
            }
        else:
            yandex_maps = {"found": False, "rating": None, "reviews": None,
                            "address": "", "coordinates": {}, "photos": None,
                            "working_hours": ""}
        google_maps: dict = {"found": False, "rating": None, "reviews": None}

        # ── 3d. Nearby competitors ────────────────────────────────────────
        nearby_competitors: list = []
        if city and specialization:
            try:
                from aim.services.competitor_matcher import CompetitorMatcher
                matcher = CompetitorMatcher()
                competitors = await matcher.find_competitors(
                    url=url,
                    count=5,
                )
                for c in competitors:
                    nearby_competitors.append({
                        "name": c.profile.legal_name or c.profile.brand_name or "",
                        "rating": c.profile.rating,
                        "reviews_count": c.profile.reviews_count,
                    })
            except Exception as e:
                errors.append(f"nearby_competitors: {e}")

        summary: dict = {
            "revenue_multi_year": revenue_multi_year,
            "yandex_maps": yandex_maps,
            "google_maps": google_maps,
            "nearby_competitors": nearby_competitors,
            "content_audit": content_audit,
        }
        if errors:
            summary["_errors"] = errors
        return summary

    # ── Cache helpers ─────────────────────────────────────────────────────

    async def _cache_get(self, url: str) -> dict | None:
        """Check company_profiles cache for existing prescan data."""
        try:
            from aim.database import async_session_maker
            from aim.models.company_profile import CompanyProfileModel
            from sqlalchemy import select

            async with async_session_maker() as session:
                stmt = (
                    select(CompanyProfileModel)
                    .where(CompanyProfileModel.url == url)
                    .order_by(CompanyProfileModel.updated_at.desc())
                    .limit(1)
                )
                result = await session.execute(stmt)
                row = result.scalar_one_or_none()
                if row and row.profile_data:
                    logger.info("Cache hit for %s", url)
                    return dict(row.profile_data)
        except Exception as e:
            logger.debug("Cache read error for %s: %s", url, e)
        return None

    async def _cache_put(self, url: str, inn: str, profile_data: dict) -> None:
        """Store prescan results in company_profiles cache."""
        try:
            from datetime import datetime as dt_mod, timezone as tz

            from aim.database import async_session_maker
            from aim.models.company_profile import CompanyProfileModel
            from sqlalchemy import select

            async with async_session_maker() as session:
                stmt = (
                    select(CompanyProfileModel)
                    .where(CompanyProfileModel.url == url, CompanyProfileModel.inn == inn)
                    .limit(1)
                )
                result = await session.execute(stmt)
                row = result.scalar_one_or_none()

                if row:
                    row.profile_data = profile_data
                    row.updated_at = dt_mod.now(tz.utc)
                else:
                    row = CompanyProfileModel(
                        url=url,
                        inn=inn or "",
                        profile_data=profile_data,
                    )
                    session.add(row)

                await session.commit()
                logger.info("Cached prescan for %s (INN=%s)", url, inn or "unknown")
        except Exception as e:
            logger.debug("Cache write error for %s: %s", url, e)
