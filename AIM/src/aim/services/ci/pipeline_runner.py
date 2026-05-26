"""Pipeline Runner — orchestrates parallel data collection with progress."""

import asyncio
import ipaddress
import logging
import time
from typing import Callable, Awaitable, Optional
from urllib.parse import urlparse

from .models import CompetitorFull, PipelineProgress, SeoAuditResult, SocialScanResult
from .seo_auditor import SeoAuditor
from .social_scanner import SocialScanner

logger = logging.getLogger(__name__)


class PipelineRunner:
    """Orchestrates parallel data collection for CI analysis."""

    def __init__(
        self,
        on_progress: Optional[Callable[[PipelineProgress], Awaitable[None]]] = None,
        timeout: float = 180.0,
    ) -> None:
        self._on_progress = on_progress
        self._timeout = timeout

    @staticmethod
    def _named_urls_to_competitors(urls: list[str]) -> list[dict]:
        """Convert named competitor URLs to competitor dicts directly.

        Extracts domain-based names, skipping URLs that fail validation.
        No DaData/Apify needed — urls are used as-is.
        """
        result: list[dict] = []
        for url in urls:
            try:
                PipelineRunner._validate_public_url(url)
            except ValueError:
                logger.warning("Skipping invalid competitor URL: %s", url)
                continue
            parsed = urlparse(url)
            hostname = parsed.hostname or ""
            # Remove www. prefix and use domain as name fallback
            name = hostname.removeprefix("www.")
            result.append({"name": name, "url": url, "inn": "", "services": []})
        return result

    @staticmethod
    def _validate_public_url(url: str) -> None:
        """Validate URL is public (http/https) and doesn't point to internal IPs.

        Raises ValueError on unsafe URLs to prevent SSRF attacks.
        DNS-based checks use warnings to avoid false positives on ephemeral domains.
        """
        parsed = urlparse(url)

        if parsed.scheme not in ("http", "https"):
            raise ValueError(f"Unsupported URL scheme: {parsed.scheme}")

        hostname = parsed.hostname
        if not hostname:
            raise ValueError(f"Could not extract hostname from URL: {url}")

        # Block IP literals pointing to private/loopback/reserved ranges
        try:
            addr = ipaddress.ip_address(hostname)
        except ValueError:
            # Not an IP literal — hostname. DNS resolution is best-effort.
            import socket

            try:
                resolved = socket.getaddrinfo(hostname, None)
            except socket.gaierror:
                logger.warning(
                    "Cannot resolve hostname %s for SSRF check — "
                    "proceeding (hostname-based, not IP literal)",
                    hostname,
                )
                return

            for family, _, _, _, sockaddr in resolved:
                ip_str = sockaddr[0] if len(sockaddr) >= 2 else None
                if not ip_str:
                    continue
                try:
                    ip = ipaddress.ip_address(ip_str)
                except ValueError:
                    continue
                if ip.is_loopback or ip.is_private or ip.is_reserved:
                    raise ValueError(
                        f"URL resolves to internal IP: {ip} (hostname={hostname})"
                    )
            return

        if addr.is_loopback or addr.is_private or addr.is_reserved:
            raise ValueError(f"URL points to internal IP: {addr}")

    async def run(
        self,
        client_url: str,
        named_competitors: Optional[list[str]] = None,
        client_inn: str = "",
    ) -> list[CompetitorFull]:
        if not client_url:
            raise ValueError("client_url is required")

        self._validate_public_url(client_url)

        return await asyncio.wait_for(
            self._run_inner(client_url, named_competitors, client_inn),
            timeout=self._timeout + 30,
        )

    async def _run_inner(
        self,
        client_url: str,
        named_competitors: Optional[list[str]] = None,
        client_inn: str = "",
    ) -> list[CompetitorFull]:
        start = time.monotonic()

        # Step 1: Find competitors
        await self._emit("searching", "Ищу конкурентов по вашему сайту...")

        # When named_competitors are URLs, use them directly (no DaData needed)
        if named_competitors and any(n.startswith(("http://", "https://")) for n in named_competitors):
            competitors = self._named_urls_to_competitors(named_competitors)
        else:
            competitors = await self._find_competitors(client_url, named_competitors, client_inn)

        if not competitors and named_competitors:
            # CompetitorMatcher failed (no DaData/Apify), use names directly
            logger.info("PipelineRunner: falling back to raw names for %d competitors", len(named_competitors))
            competitors = [{"name": n, "url": n if n.startswith(("http://", "https://")) else "", "inn": "", "services": []} for n in named_competitors]

        if not competitors:
            await self._emit("done", "Не смог найти конкурентов автоматически. Скиньте их сайты вручную.")
            return []

        names = ", ".join(c["name"][:30] for c in competitors[:4])
        await self._emit("collecting", f"Нашёл {len(competitors)} конкурентов: {names}. Собираю данные...")

        # Step 2: Collect data in parallel for each competitor
        collected: list[CompetitorFull] = []
        for comp in competitors:
            full = CompetitorFull(
                name=comp.get("name", ""),
                url=comp.get("url", ""),
                inn=comp.get("inn", ""),
            )

            results = await asyncio.gather(
                self._collect_financials(comp),
                self._collect_seo(full.url, full.name),
                self._collect_social(full.name),
                self._collect_website(comp),
                return_exceptions=True,
            )

            financials, seo, social, website = results

            if isinstance(financials, dict):
                full.financials = financials
            if seo and not isinstance(seo, Exception):
                full.seo = seo
            if social and not isinstance(social, Exception):
                full.social = social
            if website and not isinstance(website, Exception):
                full.website_features = website.get("features", [])
                full.website_missing = website.get("missing", [])
                full.doctors_count = website.get("doctors_count", 0)
                full.directions_claimed = website.get("directions_claimed", 0)
                full.pricing_visible = website.get("pricing_visible", False)
                full.positioning = website.get("positioning", "")

            # Skip competitor when ALL collectors returned nothing useful
            has_data = bool(
                full.financials
                or full.seo
                or full.social
                or full.website_features
                or full.positioning
            )
            if has_data:
                collected.append(full)
            else:
                logger.info("Skipping %s — all collectors empty", full.name)

        await self._emit("matrix", "Сравниваю с вашим сайтом...")

        elapsed = int(time.monotonic() - start)
        await self._emit("done", f"Готово! Вот что я нашёл... (заняло {elapsed} сек)")

        return collected

    async def _find_competitors(
        self, client_url: str, named: Optional[list[str]], client_inn: str = "",
    ) -> list[dict]:
        """Find competitors using existing CompetitorMatcher.

        Maps CompetitorMatch objects to plain dicts with:
        name, url, inn, services.
        """
        try:
            from AIM.src.aim.services.competitor_matcher import CompetitorMatcher
        except ImportError as e:
            logger.error(
                "CompetitorMatcher module not available: %s. "
                "Cannot discover competitors.",
                e,
            )
            raise

        matcher = CompetitorMatcher()
        try:
            matches = await matcher.find_competitors(
                url=client_url,
                count=5,
                named_competitors=named,
                client_inn=client_inn,
            )
            return [
                {
                    "name": m.profile.brand_name or m.profile.legal_name,
                    "url": m.website or m.profile.website or "",
                    "inn": m.profile.inn,
                    "services": list(m.services) if m.services else [],
                }
                for m in matches[:5]
            ]
        except Exception as e:
            logger.exception(
                "CompetitorFinder failed for %s: %s", client_url, e
            )
            return []
        finally:
            try:
                await matcher.close()
            except Exception:
                pass

    async def _collect_financials(self, comp: dict) -> Optional[dict]:
        """Fetch tax-filed financials from bo.nalog.gov.ru."""
        inn = comp.get("inn", "")
        if not inn:
            return None
        try:
            await self._emit(
                "financials",
                f"Смотрю финансовую отчётность {comp['name']}...",
                comp["name"],
            )

            def _sync_fetch():
                from AIM.src.aim.services.nalog.bfo_client import BfoNalogClient

                client = BfoNalogClient()
                try:
                    results = client.search(inn)
                    if not results:
                        return None
                    fs_list = client.get_financials(results[0].id)
                    revenue, profit = {}, {}
                    for fs in fs_list:
                        if fs.revenue_rub is not None:
                            revenue[fs.period] = fs.revenue_rub
                        if fs.net_profit_rub is not None:
                            profit[fs.period] = fs.net_profit_rub
                    # Return None when both revenue AND profit are empty
                    if not revenue and not profit:
                        return None
                    return {
                        "revenue": revenue,
                        "profit": profit,
                        "trend": fs_list[0].revenue_trend if fs_list else "",
                    }
                finally:
                    client.close()

            return await asyncio.to_thread(_sync_fetch)
        except Exception as e:
            logger.warning("Financials failed for %s: %s", comp["name"], e)
            return None

    async def _collect_seo(self, url: str, name: str = "") -> Optional[SeoAuditResult]:
        """Run SEO audit on competitor website."""
        if not url:
            return None
        try:
            self._validate_public_url(url)
        except ValueError:
            return None
        try:
            await self._emit(
                "seo",
                f"Проверяю SEO ошибки на сайте {name}..." if name else "Проверяю SEO ошибки на сайте...",
                name,
            )

            def _sync():
                auditor = SeoAuditor()
                try:
                    return auditor.audit(url)
                finally:
                    auditor.close()

            return await asyncio.to_thread(_sync)
        except Exception as e:
            logger.warning("SEO audit failed for %s: %s", url, e)
            return None

    async def _collect_social(self, company_name: str) -> Optional[SocialScanResult]:
        """Scan social media for competitor."""
        if not company_name:
            return None
        try:
            await self._emit("social", f"Ищу соцсети {company_name}...", company_name)

            def _sync():
                scanner = SocialScanner()
                try:
                    return scanner.scan(company_name)
                finally:
                    scanner.close()

            return await asyncio.to_thread(_sync)
        except Exception as e:
            logger.warning("Social scan failed for %s: %s", company_name, e)
            return None

    async def _collect_website(self, comp: dict) -> Optional[dict]:
        """Scrape competitor website for features, doctors, pricing, positioning.

        Uses httpx + BeautifulSoup for basic page analysis (no Playwright).
        Falls back to CompetitorMatcher services count on failure.
        """
        url = comp.get("url", "")
        if not url:
            return None

        try:
            self._validate_public_url(url)
        except ValueError:
            return None

        try:
            await self._emit(
                "scraping",
                f"Анализирую сайт {comp['name']}...",
                comp["name"],
            )

            def _sync_scrape():
                import httpx
                from bs4 import BeautifulSoup

                client = httpx.Client(
                    timeout=httpx.Timeout(8.0),
                    headers={
                        "User-Agent": (
                            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                            "AppleWebKit/537.36 (KHTML, like Gecko) "
                            "Chrome/148.0.0.0 Safari/537.36"
                        ),
                        "Accept": "text/html",
                    },
                    follow_redirects=True,
                )
                try:
                    resp = client.get(url)
                    soup = BeautifulSoup(resp.text, "html.parser")

                    features = _detect_features(soup)
                    doctors_count = _count_doctors(soup)
                    directions_claimed = _count_directions(soup)
                    pricing_visible = _detect_pricing(soup)
                    positioning = _extract_positioning(soup)

                    return {
                        "features": features,
                        "missing": [],
                        "doctors_count": doctors_count,
                        "directions_claimed": directions_claimed,
                        "pricing_visible": pricing_visible,
                        "positioning": positioning,
                    }
                finally:
                    client.close()

            return await asyncio.to_thread(_sync_scrape)
        except Exception as e:
            logger.warning(
                "Website scraping failed for %s: %s", comp.get("name", ""), e
            )
            # Fall back to services count from CompetitorMatcher
            services = comp.get("services", [])
            return {
                "features": [],
                "missing": [],
                "doctors_count": 0,
                "directions_claimed": len(services) if services else 0,
                "pricing_visible": False,
                "positioning": "",
            }

    async def _collect_financials_async(self, inn: str) -> Optional[dict]:
        """Public test helper — same as _collect_financials but takes INN directly."""
        return await self._collect_financials({"inn": inn, "name": "test"})

    async def _emit(self, stage: str, message: str, competitor_name: str = "") -> None:
        """Emit progress update."""
        progress = PipelineProgress(
            stage=stage, message=message, competitor_name=competitor_name
        )
        logger.info("Pipeline [%s]: %s", stage, message)
        if self._on_progress:
            try:
                await self._on_progress(progress)
            except Exception as e:
                logger.warning("Progress callback failed: %s", e)


# ---------------------------------------------------------------------------
# Website feature detectors (module-level helpers used by _collect_website)
# ---------------------------------------------------------------------------


def _detect_features(soup) -> list[str]:
    """Detect website features from CSS classes, text patterns, and DOM structure.

    Returns list of detected feature labels like ["booking", "chat", "calculator"].
    """
    features = []
    html_lower = str(soup).lower()
    text_lower = soup.get_text().lower()

    # Booking / appointment forms
    booking_keywords = [
        "zapis", "appointment", "booking", "online-booking",
        "zapisatsya", "записаться", "запись на приём", "запись на прием",
    ]
    if any(kw in html_lower or kw in text_lower for kw in booking_keywords):
        features.append("booking")

    # Chat widgets
    chat_keywords = [
        "jivosite", "livechat", "chat-widget", "whatsapp-widget",
        "online-chat", "чат", "онлайн-чат", "обратный звонок",
    ]
    if any(kw in html_lower for kw in chat_keywords):
        features.append("chat")

    # Calculators
    calc_keywords = [
        "calculator", "калькулятор", "расчёт стоимости", "расчет стоимости",
    ]
    if any(kw in html_lower or kw in text_lower for kw in calc_keywords):
        features.append("calculator")

    # Review / testimonial blocks
    review_keywords = [
        "review", "testimonial", "feedback", "rating",
        "отзыв", "оценка", "рейтинг",
    ]
    if any(kw in html_lower or kw in text_lower for kw in review_keywords):
        features.append("reviews")

    # Price lists
    price_keywords = [
        "price-list", "pricelist", "tariff", "tarif",
        "прайс", "цены", "стоимость услуг",
    ]
    if any(kw in html_lower or kw in text_lower for kw in price_keywords):
        features.append("price_list")

    return features


def _count_doctors(soup) -> int:
    """Count unique doctor/staff profile elements by CSS classes and card patterns."""
    doctor_selectors = [
        "doctor", "specialist", "employee", "staff", "vrach",
        "врач", "специалист", "сотрудник", "доктор",
    ]

    seen: set[int] = set()
    for selector in doctor_selectors:
        for el in soup.find_all(
            class_=lambda c, s=selector: (
                c and s in c.lower()
                if isinstance(c, str)
                else False
            )
        ):
            seen.add(id(el))
        for el in soup.find_all(
            attrs={"data-role": lambda v, s=selector: v and s in v.lower()}
        ):
            seen.add(id(el))

    # Fallback: detect repeating card patterns with person-related content
    if not seen:
        cards = soup.find_all("article") or soup.find_all(
            "li", class_=lambda c: (
                c and "card" in c.lower() if c else False
            )
        )
        person_keywords = [
            "врач", "доктор", "специалист",
            "doctor", "specialist",
        ]
        for card in cards:
            text = card.get_text().lower()
            if any(kw in text for kw in person_keywords):
                seen.add(id(card))

    return len(seen)


def _count_directions(soup) -> int:
    """Count service/direction links in navigation and content areas."""
    service_keywords = [
        "service", "direction", "department", "napravlenie",
        "услуг", "направлен", "отделен", "лечени", "диагност",
    ]

    # Find service-related links in navigation-like containers
    nav_elements = soup.find_all(
        ["a", "li", "div"],
        class_=lambda c: (
            c and any(
                kw in c.lower()
                for kw in ["nav", "menu", "service", "direction", "uslugi"]
            )
            if c else False
        ),
    )

    seen_hrefs: set[str] = set()
    for el in (nav_elements if nav_elements else soup.find_all("a", href=True)):
        for a in (el.find_all("a", href=True) if el.name != "a" else [el]):
            href = (a.get("href", "") or "").lower()
            text = a.get_text(strip=True).lower()
            if any(kw in href or kw in text for kw in service_keywords):
                seen_hrefs.add(href)
    return len(seen_hrefs)


def _detect_pricing(soup) -> bool:
    """Detect whether pricing information is visible on the page."""
    # CSS classes hinting at price content
    price_elements = soup.find_all(
        class_=lambda c: (
            c and any(
                kw in c.lower()
                for kw in [
                    "price", "pricing", "tariff", "tarif", "cost",
                    "прайс", "цена", "стоимость",
                ]
            )
            if c else False
        ),
    )
    if price_elements:
        return True

    # Tables containing price-like content
    for table in soup.find_all("table"):
        table_text = table.get_text().lower()
        has_currency = "руб" in table_text or "₽" in table_text or "стоимость" in table_text
        has_number = any(c.isdigit() for c in table_text)
        if has_currency and has_number:
            return True

    return False


def _extract_positioning(soup) -> str:
    """Extract positioning text from meta description, H1, or og:description."""
    # 1. Meta description
    meta_desc = soup.find("meta", attrs={"name": "description"})
    if meta_desc and (content := meta_desc.get("content", "")).strip():
        return content.strip()[:200]

    # 2. H1
    h1 = soup.find("h1")
    if h1 and (text := h1.get_text(strip=True)):
        return text[:200]

    # 3. Open Graph description
    og_desc = soup.find("meta", property="og:description")
    if og_desc and (content := og_desc.get("content", "")).strip():
        return content.strip()[:200]

    return ""
