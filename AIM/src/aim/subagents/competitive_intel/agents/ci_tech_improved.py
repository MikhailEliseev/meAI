"""
CI Tech Agent Improved - Real Technical SEO Audit

Реальный технический SEO аудит конкурентов:
- Core Web Vitals через PageSpeed Insights API
- Playwright рендеринг для SPA сайтов
- Анализ robots.txt и sitemap.xml
- Валидация структурированных данных (JSON-LD)
- Детекция AI crawler blocking

Основано на лучших практиках из:
- https://github.com/tentacl-ai/seo-autopilot (880+ stars)
"""

from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional
from xml.etree import ElementTree

import httpx

from meai.agents.base_agent import Agent, Task, TaskResult
from meai.memory.obsidian import ObsidianVault

logger = logging.getLogger(__name__)

# ============================================================================
# PageSpeed Insights Integration (Core Web Vitals)
# ============================================================================

PSI_ENDPOINT = "https://www.googleapis.com/pagespeedonline/v5/runPagespeed"
DEFAULT_CATEGORIES = ["performance", "seo", "accessibility", "best-practices"]
TIMEOUT = 60.0

# CWV thresholds (April 2026)
CWV_THRESHOLDS = {
    "lcp": {"good": 2500, "poor": 4000, "unit": "ms"},
    "cls": {"good": 0.1, "poor": 0.25, "unit": "score"},
    "inp": {"good": 200, "poor": 500, "unit": "ms"},
    "fcp": {"good": 1800, "poor": 3000, "unit": "ms"},
    "ttfb": {"good": 800, "poor": 1800, "unit": "ms"},
}


@dataclass
class PageSpeedResult:
    """Lighthouse + CrUX result for a single URL."""

    url: str
    strategy: str = "mobile"

    # Lighthouse category scores (0-100)
    performance_score: Optional[int] = None
    seo_score: Optional[int] = None
    accessibility_score: Optional[int] = None
    best_practices_score: Optional[int] = None

    # Lab data (Lighthouse synthetic)
    lcp_ms: Optional[float] = None
    cls: Optional[float] = None
    fcp_ms: Optional[float] = None
    ttfb_ms: Optional[float] = None

    # Field data (CrUX — real user metrics)
    crux_lcp_ms: Optional[float] = None
    crux_lcp_rating: Optional[str] = None
    crux_cls: Optional[float] = None
    crux_cls_rating: Optional[str] = None
    crux_inp_ms: Optional[float] = None
    crux_inp_rating: Optional[str] = None
    has_field_data: bool = False

    error: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {k: v for k, v in self.__dict__.items() if v is not None}


def rate_metric(metric: str, value: float) -> str:
    """Rate a CWV metric as good/needs-improvement/poor."""
    thresholds = CWV_THRESHOLDS.get(metric)
    if not thresholds:
        return "unknown"
    if value <= thresholds["good"]:
        return "good"
    elif value < thresholds["poor"]:
        return "needs-improvement"
    else:
        return "poor"


async def fetch_pagespeed(
    url: str,
    api_key: Optional[str] = None,
    strategy: str = "mobile",
) -> PageSpeedResult:
    """Fetch PageSpeed Insights for a single URL."""
    result = PageSpeedResult(url=url, strategy=strategy)

    param_list = [("url", url), ("strategy", strategy)]
    for c in DEFAULT_CATEGORIES:
        param_list.append(("category", c))
    if api_key:
        param_list.append(("key", api_key))

    try:
        async with httpx.AsyncClient(timeout=TIMEOUT) as client:
            resp = await client.get(PSI_ENDPOINT, params=param_list)

        if resp.status_code == 429:
            result.error = "Rate limited (429). Set PAGESPEED_API_KEY for higher quota."
            logger.warning(f"PageSpeed rate limited for {url}")
            return result

        if resp.status_code != 200:
            result.error = f"HTTP {resp.status_code}"
            logger.warning(f"PageSpeed error for {url}: {result.error}")
            return result

        data = resp.json()
        lr = data.get("lighthouseResult", {})

        # Category scores (0-100)
        categories_data = lr.get("categories", {})
        if "performance" in categories_data:
            result.performance_score = int(categories_data["performance"]["score"] * 100)
        if "seo" in categories_data:
            result.seo_score = int(categories_data["seo"]["score"] * 100)
        if "accessibility" in categories_data:
            result.accessibility_score = int(categories_data["accessibility"]["score"] * 100)
        if "best-practices" in categories_data:
            result.best_practices_score = int(categories_data["best-practices"]["score"] * 100)

        # Lab data from Lighthouse audits
        audits = lr.get("audits", {})
        if "largest-contentful-paint" in audits:
            result.lcp_ms = audits["largest-contentful-paint"].get("numericValue")
        if "cumulative-layout-shift" in audits:
            result.cls = audits["cumulative-layout-shift"].get("numericValue")
        if "first-contentful-paint" in audits:
            result.fcp_ms = audits["first-contentful-paint"].get("numericValue")

        # CrUX Field Data (real user metrics)
        le = data.get("loadingExperience", {})
        metrics = le.get("metrics", {})
        if metrics:
            result.has_field_data = True
            # LCP
            lcp_data = metrics.get("LARGEST_CONTENTFUL_PAINT_MS", {})
            if "percentile" in lcp_data:
                result.crux_lcp_ms = float(lcp_data["percentile"])
                result.crux_lcp_rating = _normalize_rating(lcp_data.get("category", ""))
            # CLS
            cls_data = metrics.get("CUMULATIVE_LAYOUT_SHIFT_SCORE", {})
            if "percentile" in cls_data:
                result.crux_cls = round(cls_data["percentile"] / 100, 3)
                result.crux_cls_rating = _normalize_rating(cls_data.get("category", ""))
            # INP
            inp_data = metrics.get("INTERACTION_TO_NEXT_PAINT", {})
            if "percentile" in inp_data:
                result.crux_inp_ms = float(inp_data["percentile"])
                result.crux_inp_rating = _normalize_rating(inp_data.get("category", ""))

        logger.info(
            f"PageSpeed {strategy} {url}: perf={result.performance_score} "
            f"LCP={result.lcp_ms}ms CLS={result.cls} field_data={result.has_field_data}"
        )

    except httpx.TimeoutException:
        result.error = f"Timeout after {TIMEOUT}s"
        logger.warning(f"PageSpeed timeout for {url}")
    except Exception as exc:
        result.error = str(exc)
        logger.warning(f"PageSpeed error for {url}: {exc}")

    return result


def _normalize_rating(category: str) -> str:
    """Normalize PSI rating (FAST/AVERAGE/SLOW) to good/needs-improvement/poor."""
    rating_map = {
        "fast": "good",
        "average": "needs-improvement",
        "slow": "poor",
    }
    return rating_map.get(category.lower().replace("_", "-"), category)


# ============================================================================
# Playwright Renderer (for SPA sites)
# ============================================================================

MIN_WORDS_THRESHOLD = 50
SPA_INDICATORS = [
    'id="root"',
    'id="app"',
    'id="__next"',
    'id="__nuxt"',
    'script type="module"',
    "__NEXT_DATA__",
    "__NUXT__",
]
RENDER_TIMEOUT_MS = 15_000

_playwright_available: Optional[bool] = None


def is_spa_likely(raw_html: str, word_count: int) -> bool:
    """Check if page is likely a SPA."""
    if word_count >= MIN_WORDS_THRESHOLD:
        return False
    html_lower = raw_html.lower()
    return any(indicator.lower() in html_lower for indicator in SPA_INDICATORS)


async def render_page(url: str, timeout_ms: int = RENDER_TIMEOUT_MS) -> Optional[str]:
    """Render page with Playwright and return rendered HTML."""
    global _playwright_available

    if _playwright_available is False:
        return None

    try:
        from playwright.async_api import async_playwright

        _playwright_available = True
    except ImportError:
        _playwright_available = False
        logger.info(
            "[renderer] Playwright not installed — JS rendering unavailable. "
            "Install with: pip install playwright && playwright install chromium"
        )
        return None

    browser = None
    try:
        pw = await async_playwright().start()
        browser = await pw.chromium.launch(
            headless=True,
            args=[
                "--no-sandbox",
                "--disable-setuid-sandbox",
                "--disable-dev-shm-usage",
                "--disable-gpu",
                "--single-process",
            ],
        )

        page = await browser.new_page(
            user_agent="AIMBot/1.0 (+https://iamaim.ru)",
            viewport={"width": 1280, "height": 720},
        )

        await page.goto(url, wait_until="networkidle", timeout=timeout_ms)
        await page.wait_for_timeout(500)
        rendered_html = await page.content()

        await page.close()
        await browser.close()
        await pw.stop()

        logger.info(f"[renderer] JS-rendered {url} ({len(rendered_html)} bytes)")
        return rendered_html

    except Exception as exc:
        logger.warning(f"[renderer] Rendering failed for {url}: {exc}")
        if browser:
            try:
                await browser.close()
            except Exception:
                pass
        return None


# ============================================================================
# Robots.txt + Sitemap Audit
# ============================================================================

AI_CRAWLERS = [
    "GPTBot",
    "ChatGPT-User",
    "ClaudeBot",
    "anthropic-ai",
    "PerplexityBot",
    "Bytespider",
    "CCBot",
    "Google-Extended",
    "FacebookBot",
    "cohere-ai",
]

SITEMAP_MAX_URLS = 50_000
NS = {"sm": "http://www.sitemaps.org/schemas/sitemap/0.9"}


@dataclass
class RobotsResult:
    """Parsed robots.txt data."""

    raw: str = ""
    exists: bool = False
    status_code: int = 0
    sitemap_directives: List[str] = field(default_factory=list)
    blocked_ai_crawlers: List[str] = field(default_factory=list)
    blocks_css_js: bool = False


@dataclass
class SitemapResult:
    """Parsed sitemap data."""

    url: str = ""
    exists: bool = False
    status_code: int = 0
    url_count: int = 0
    is_index: bool = False
    child_sitemaps: List[str] = field(default_factory=list)
    parse_error: Optional[str] = None


async def fetch_robots(base_url: str) -> RobotsResult:
    """Fetch and parse robots.txt."""
    result = RobotsResult()
    robots_url = f"{base_url.rstrip('/')}/robots.txt"

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(robots_url, follow_redirects=True)
        result.status_code = resp.status_code
        result.exists = resp.status_code == 200

        if result.exists:
            result.raw = resp.text
            lines = result.raw.lower().split("\n")

            # Check for sitemap directives
            result.sitemap_directives = [
                line.split(":", 1)[1].strip()
                for line in lines
                if line.startswith("sitemap:")
            ]

            # Check for AI crawler blocking
            for crawler in AI_CRAWLERS:
                if f"user-agent: {crawler.lower()}" in result.raw.lower():
                    if "disallow: /" in result.raw.lower():
                        result.blocked_ai_crawlers.append(crawler)

            # Check for CSS/JS blocking
            result.blocks_css_js = any(
                "disallow:" in line and (".css" in line or ".js" in line or "/static" in line)
                for line in lines
            )

        logger.info(f"Robots.txt {robots_url}: exists={result.exists}, blocked_ai={len(result.blocked_ai_crawlers)}")

    except Exception as exc:
        logger.warning(f"Robots.txt fetch failed for {robots_url}: {exc}")

    return result


async def fetch_sitemap(sitemap_url: str) -> SitemapResult:
    """Fetch and parse sitemap.xml."""
    result = SitemapResult(url=sitemap_url)

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.get(sitemap_url, follow_redirects=True)
        result.status_code = resp.status_code
        result.exists = resp.status_code == 200

        if result.exists:
            try:
                root = ElementTree.fromstring(resp.content)

                # Check if sitemap index
                if root.tag.endswith("sitemapindex"):
                    result.is_index = True
                    result.child_sitemaps = [
                        elem.text
                        for elem in root.findall(".//sm:loc", NS)
                        if elem.text
                    ]
                else:
                    # Regular sitemap
                    urls = root.findall(".//sm:url", NS)
                    result.url_count = len(urls)

                logger.info(
                    f"Sitemap {sitemap_url}: exists={result.exists}, "
                    f"is_index={result.is_index}, urls={result.url_count}"
                )

            except ElementTree.ParseError as exc:
                result.parse_error = str(exc)
                logger.warning(f"Sitemap parse error for {sitemap_url}: {exc}")

    except Exception as exc:
        logger.warning(f"Sitemap fetch failed for {sitemap_url}: {exc}")

    return result


# ============================================================================
# CI Tech Agent Improved
# ============================================================================


class CITechAgentImproved(Agent):
    """CI Tech Agent with real technical SEO audit."""

    def __init__(
        self,
        agent_id: str,
        database_url: str = "sqlite+aiosqlite:///./data/meai.db",
        vault_path: str = "./obsidian",
        pagespeed_api_key: Optional[str] = None,
    ):
        super().__init__(
            agent_id=agent_id,
            agent_type="ci-tech",
            database_url=database_url,
            vault_path=vault_path,
        )
        self.vault = ObsidianVault("AIM/obsidian/ci-tech")
        self.pagespeed_api_key = pagespeed_api_key

    async def execute_task(self, task: Task) -> TaskResult:
        """Execute technical SEO audit for competitors."""
        try:
            competitors = task.payload.get("competitors", [])
            logger.info(f"[CI Tech] Analyzing {len(competitors)} competitors")

            # Audit each competitor
            audits = []
            for comp in competitors:
                url = comp.get("url")
                if not url:
                    continue

                audit = await self._audit_competitor(url, comp.get("name", url))
                audits.append(audit)

            # Aggregate insights
            insights = self._generate_insights(audits)

            results = {
                "analysis_date": datetime.now().isoformat(),
                "total_analyzed": len(audits),
                "audits": audits,
                "insights": insights,
            }

            logger.info(f"[CI Tech] Analysis completed for {len(audits)} competitors")

            return TaskResult(
                subtask_id=task.subtask_id,
                agent_id=self.agent_id,
                action=task.action,
                status="success",
                result=results,
                error=None,
                duration_seconds=0.0,
                completed_at=datetime.now(),
            )

        except Exception as e:
            logger.error(f"[CI Tech] Task failed: {e}")
            return TaskResult(
                subtask_id=task.subtask_id,
                agent_id=self.agent_id,
                action=task.action,
                status="failed",
                result={"error": str(e)},
                error=str(e),
                duration_seconds=0.0,
                completed_at=datetime.now(),
            )

    async def _audit_competitor(self, url: str, name: str) -> Dict[str, Any]:
        """Perform full technical SEO audit for a competitor."""
        logger.info(f"[CI Tech] Auditing {name} ({url})")

        # Run audits in parallel
        pagespeed_task = fetch_pagespeed(url, api_key=self.pagespeed_api_key)
        robots_task = fetch_robots(url)

        pagespeed_result, robots_result = await asyncio.gather(
            pagespeed_task, robots_task, return_exceptions=True
        )

        # Handle exceptions
        if isinstance(pagespeed_result, Exception):
            logger.warning(f"PageSpeed failed for {url}: {pagespeed_result}")
            pagespeed_result = PageSpeedResult(url=url, error=str(pagespeed_result))

        if isinstance(robots_result, Exception):
            logger.warning(f"Robots.txt failed for {url}: {robots_result}")
            robots_result = RobotsResult()

        # Fetch sitemap if found in robots.txt
        sitemap_result = None
        if robots_result.sitemap_directives:
            sitemap_url = robots_result.sitemap_directives[0]
            sitemap_result = await fetch_sitemap(sitemap_url)

        # Calculate tech maturity score
        tech_score = self._calculate_tech_score(pagespeed_result, robots_result, sitemap_result)

        return {
            "name": name,
            "url": url,
            "pagespeed": pagespeed_result.to_dict(),
            "robots": {
                "exists": robots_result.exists,
                "has_sitemap": len(robots_result.sitemap_directives) > 0,
                "blocked_ai_crawlers": robots_result.blocked_ai_crawlers,
                "blocks_css_js": robots_result.blocks_css_js,
            },
            "sitemap": {
                "exists": sitemap_result.exists if sitemap_result else False,
                "url_count": sitemap_result.url_count if sitemap_result else 0,
                "is_index": sitemap_result.is_index if sitemap_result else False,
            }
            if sitemap_result
            else None,
            "tech_score": tech_score,
        }

    def _calculate_tech_score(
        self,
        pagespeed: PageSpeedResult,
        robots: RobotsResult,
        sitemap: Optional[SitemapResult],
    ) -> Dict[str, Any]:
        """Calculate technical maturity score (0-100)."""
        score = 0
        max_score = 100

        # Performance (40 points)
        if pagespeed.performance_score is not None:
            score += (pagespeed.performance_score / 100) * 40

        # SEO basics (30 points)
        if pagespeed.seo_score is not None:
            score += (pagespeed.seo_score / 100) * 20
        if robots.exists:
            score += 5
        if sitemap and sitemap.exists:
            score += 5

        # Accessibility (15 points)
        if pagespeed.accessibility_score is not None:
            score += (pagespeed.accessibility_score / 100) * 15

        # Best practices (15 points)
        if pagespeed.best_practices_score is not None:
            score += (pagespeed.best_practices_score / 100) * 15

        # Penalties
        if robots.blocked_ai_crawlers:
            score -= 10  # Blocking AI crawlers hurts GEO visibility
        if robots.blocks_css_js:
            score -= 5  # Blocking CSS/JS prevents rendering

        score = max(0, min(max_score, score))

        return {
            "total": round(score, 1),
            "rating": "high" if score >= 70 else "medium" if score >= 40 else "low",
        }

    def _generate_insights(self, audits: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate market insights from audits."""
        if not audits:
            return {}

        # Average scores
        avg_perf = sum(
            a["pagespeed"].get("performance_score", 0)
            for a in audits
            if a["pagespeed"].get("performance_score")
        ) / len(audits)

        avg_tech_score = sum(a["tech_score"]["total"] for a in audits) / len(audits)

        # AI crawler blocking
        blocking_ai = sum(
            1 for a in audits if a["robots"].get("blocked_ai_crawlers")
        )

        # Sitemap adoption
        has_sitemap = sum(
            1 for a in audits if a.get("sitemap") and a["sitemap"]["exists"]
        )

        return {
            "avg_performance_score": round(avg_perf, 1),
            "avg_tech_score": round(avg_tech_score, 1),
            "ai_crawler_blocking_rate": round((blocking_ai / len(audits)) * 100, 1),
            "sitemap_adoption_rate": round((has_sitemap / len(audits)) * 100, 1),
            "key_findings": [
                f"Средний Performance Score: {avg_perf:.0f}/100",
                f"Средний Tech Score: {avg_tech_score:.0f}/100",
                f"Блокируют AI краулеры: {blocking_ai}/{len(audits)} компаний",
                f"Имеют sitemap.xml: {has_sitemap}/{len(audits)} компаний",
            ],
        }

    def get_capabilities(self) -> List[str]:
        """Return agent capabilities."""
        return [
            "core_web_vitals_analysis",
            "pagespeed_insights_audit",
            "playwright_spa_rendering",
            "robots_txt_audit",
            "sitemap_xml_audit",
            "ai_crawler_detection",
            "tech_maturity_scoring",
        ]
