"""Pipeline Runner — orchestrates parallel data collection with progress."""

import asyncio
import logging
import time
from typing import Callable, Awaitable, Optional

from .models import CompetitorFull, PipelineProgress
from .seo_auditor import SeoAuditor
from .social_scanner import SocialScanner

logger = logging.getLogger(__name__)


class PipelineRunner:
    """Orchestrates parallel data collection for CI analysis."""

    def __init__(
        self,
        on_progress: Optional[Callable[[PipelineProgress], Awaitable[None]]] = None,
        timeout: float = 15.0,
    ) -> None:
        self._on_progress = on_progress
        self._timeout = timeout

    async def run(
        self,
        client_url: str,
        named_competitors: Optional[list[str]] = None,
    ) -> list[CompetitorFull]:
        if not client_url:
            raise ValueError("client_url is required")

        start = time.monotonic()

        # Step 1: Find competitors
        await self._emit("searching", "Ищу конкурентов по вашему сайту...")

        competitors = await self._find_competitors(client_url, named_competitors)

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
                self._collect_seo(full.url),
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

            collected.append(full)

        await self._emit("matrix", "Сравниваю с вашим сайтом...")

        elapsed = int(time.monotonic() - start)
        await self._emit("done", f"Готово! Вот что я нашёл... (заняло {elapsed} сек)")

        return collected

    async def _find_competitors(
        self, client_url: str, named: Optional[list[str]]
    ) -> list[dict]:
        """Find competitors using existing CompetitorMatcher.

        Maps CompetitorMatch objects to plain dicts with:
        name, url, inn, services.
        """
        try:
            from AIM.src.aim.services.competitor_matcher import CompetitorMatcher

            matcher = CompetitorMatcher()
            try:
                matches = await matcher.find_competitors(
                    url=client_url,
                    count=5,
                    named_competitors=named,
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
            finally:
                await matcher.close()
        except Exception as e:
            logger.exception("CompetitorFinder failed: %s", e)
            return []

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

    async def _collect_seo(self, url: str) -> Optional[object]:
        """Run SEO audit on competitor website."""
        if not url:
            return None
        try:
            await self._emit("seo", "Проверяю SEO ошибки на сайте...")

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

    async def _collect_social(self, company_name: str) -> Optional[object]:
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
        """Extract website features from existing scraper data.

        Web scraping is done by CompetitorMatcher during discovery
        (services are already extracted). Here we just count them.
        """
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
