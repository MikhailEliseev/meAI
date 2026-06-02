"""
CI Auditor Agent - Deep Competitor Website Audit

Проводит глубокий аудит сайтов конкурентов по 4 направлениям:
- Technical (скорость, мобильность, SEO)
- Content (структура, качество, ключевые слова)
- UX/UI (юзабилити, конверсия, CTA)
- Marketing (каналы, воронки, лид-магниты)
"""

import asyncio
import os
import time
from typing import Any, Dict, List, Optional
from datetime import datetime
from urllib.parse import urljoin, urlparse
import json
import re

import httpx
from bs4 import BeautifulSoup

from meai.agents.base_agent import Agent, Task, TaskResult
from meai.events.event_bus import EventBus
from meai.memory.obsidian import ObsidianVault


class CIAuditorAgent(Agent):
    """
    CI Auditor - агент глубокого аудита конкурентов.

    Фаза 2-3 CI pipeline:
    - Технический аудит (PageSpeed, мобильность, Core Web Vitals)
    - Контентный аудит (структура, качество, SEO)
    - UX/UI аудит (юзабилити, конверсия)
    - Маркетинговый аудит (каналы, воронки)
    """

    def __init__(
        self,
        agent_id: str,
        pagespeed_api_key: str | None = None,
        database_url: str = "sqlite+aiosqlite:///./data/meai.db",
        vault_path: str = "./obsidian"
    ):
        super().__init__(
            agent_id=agent_id,
            agent_type="ci-auditor",
            database_url=database_url,
            vault_path=vault_path
        )
        # Переопределяем vault на специфичный для CI Auditor
        self.vault = ObsidianVault("AIM/obsidian/ci-auditor")
        self.pagespeed_api_key = pagespeed_api_key or os.getenv("PAGESPEED_API_KEY")
        self.pagespeed_url = "https://www.googleapis.com/pagespeedonline/v5/runPagespeed"

        # Audit dimensions
        self.audit_dimensions = {
            "technical": {
                "page_speed": "Скорость загрузки (Desktop/Mobile)",
                "core_web_vitals": "LCP, FID, CLS",
                "mobile_friendly": "Мобильная адаптация",
                "https": "HTTPS и безопасность",
                "structured_data": "Schema.org разметка",
                "sitemap": "XML Sitemap",
                "robots_txt": "robots.txt"
            },
            "content": {
                "structure": "Структура сайта (глубина, навигация)",
                "quality": "Качество контента (уникальность, полезность)",
                "keywords": "Ключевые слова (плотность, релевантность)",
                "headings": "Заголовки (H1-H6 структура)",
                "images": "Изображения (alt, размер, оптимизация)",
                "internal_links": "Внутренняя перелинковка",
                "blog": "Блог/статьи (частота, качество)"
            },
            "ux_ui": {
                "usability": "Юзабилити (простота навигации)",
                "conversion": "Конверсионные элементы (формы, CTA)",
                "design": "Дизайн (современность, брендинг)",
                "trust_signals": "Сигналы доверия (отзывы, сертификаты)",
                "contact_forms": "Формы связи (доступность, простота)",
                "online_booking": "Онлайн-запись",
                "chat": "Онлайн-чат"
            },
            "marketing": {
                "channels": "Маркетинговые каналы (SEO, PPC, Social)",
                "funnels": "Воронки продаж",
                "lead_magnets": "Лид-магниты (акции, скидки)",
                "email_capture": "Сбор email",
                "retargeting": "Ретаргетинг (пиксели)",
                "analytics": "Аналитика (GA, Яндекс.Метрика)",
                "crm": "CRM интеграция"
            }
        }

        # Scoring weights
        self.weights = {
            "technical": 0.25,
            "content": 0.30,
            "ux_ui": 0.25,
            "marketing": 0.20
        }

    async def execute_task(self, task: Task) -> TaskResult:
        """
        Выполнить аудит конкурентов.

        Args:
            task: Задача с payload:
                - competitors: список конкурентов для аудита (обязательно)
                - audit_type: тип аудита (quick/deep/full, опционально)

        Returns:
            TaskResult с результатами аудита
        """
        try:
            competitors = task.payload["competitors"]
            audit_type = task.payload.get("audit_type", "deep")

            # Логирование начала
            print(f"[CI Auditor] Начало аудита {len(competitors)} конкурентов (тип: {audit_type})")

            # Шаг 1: Audit each competitor
            audits = []
            for competitor in competitors:
                audit = await self._audit_competitor(competitor, audit_type)
                audits.append(audit)

            # Шаг 2: Calculate scores
            scored_audits = await self._calculate_scores(audits)

            # Шаг 3: Generate insights
            insights = await self._generate_insights(scored_audits)

            # Шаг 4: Identify gaps and opportunities
            gaps = await self._identify_gaps(scored_audits)

            # Шаг 5: Save results
            results = {
                "audit_type": audit_type,
                "audit_date": datetime.now().isoformat(),
                "total_audited": len(audits),
                "audits": scored_audits,
                "insights": insights,
                "gaps": gaps
            }

            await self._save_results(results)

            # Логирование завершения
            print(f"[CI Auditor] Завершён аудит {len(audits)} конкурентов")

            return TaskResult(
                subtask_id=task.subtask_id,
                agent_id=self.agent_id,
                action=task.action,
                status="success",
                result=results,
                error=None,
                duration_seconds=0.0,
                completed_at=datetime.now()
            )

        except Exception as e:
            print(f"[CI Auditor] Ошибка: {e}")
            return TaskResult(
                subtask_id=task.subtask_id,
                agent_id=self.agent_id,
                action=task.action,
                status="failed",
                result={"error": str(e)},
                error=str(e),
                duration_seconds=0.0,
                completed_at=datetime.now()
            )

    async def _audit_competitor(
        self,
        competitor: Dict[str, Any],
        audit_type: str
    ) -> Dict[str, Any]:
        """
        Провести аудит одного конкурента.

        Args:
            competitor: данные конкурента
            audit_type: тип аудита (quick/deep/full)

        Returns:
            Результаты аудита
        """
        name = competitor["name"]
        url = competitor.get("url", "")

        print(f"[CI Auditor] Аудит: {name}")

        # Определить dimensions для аудита
        dimensions = self._get_audit_dimensions(audit_type)

        audit = {
            "name": name,
            "url": url,
            "audit_type": audit_type,
            "dimensions": {}
        }

        # Провести аудит по каждому dimension
        for dimension in dimensions:
            audit["dimensions"][dimension] = await self._audit_dimension(
                url, dimension, audit_type
            )

        return audit

    def _get_audit_dimensions(self, audit_type: str) -> List[str]:
        """Определить dimensions для аудита в зависимости от типа."""
        if audit_type == "quick":
            return ["technical", "content"]
        elif audit_type == "deep":
            return ["technical", "content", "ux_ui"]
        else:  # full
            return ["technical", "content", "ux_ui", "marketing"]

    async def _audit_dimension(
        self,
        url: str,
        dimension: str,
        audit_type: str
    ) -> Dict[str, Any]:
        """
        Провести аудит по одному dimension на основе реальных данных.

        Использует httpx + BeautifulSoup для HTML-анализа и
        Google PageSpeed Insights API для performance-метрик.

        Args:
            url: URL сайта
            dimension: dimension для аудита
            audit_type: тип аудита

        Returns:
            Результаты аудита dimension
        """
        checks = self.audit_dimensions[dimension]
        results: Dict[str, Any] = {}

        if not url:
            for check_key, check_name in checks.items():
                results[check_key] = {
                    "name": check_name,
                    "score": None,
                    "status": "unavailable",
                    "details": "URL not provided",
                }
            return results

        try:
            async with httpx.AsyncClient(timeout=httpx.Timeout(20.0), follow_redirects=True) as client:
                resp = await client.get(url, headers={"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"})
                resp.raise_for_status()
                html = resp.text
                soup = BeautifulSoup(html, "html.parser")
                final_url = str(resp.url)

                pagespeed = None
                if dimension == "technical":
                    pagespeed = await self._fetch_pagespeed(client, url)

                for check_key, check_name in checks.items():
                    try:
                        score, status, details = await self._score_real_check(
                            check_key, url, final_url, html, soup, pagespeed, resp, client
                        )
                        results[check_key] = {
                            "name": check_name,
                            "score": score,
                            "status": status,
                            "details": details,
                        }
                    except Exception as e:
                        results[check_key] = {
                            "name": check_name,
                            "score": None,
                            "status": "error",
                            "details": f"Audit failed: {str(e)[:200]}",
                        }

        except Exception as e:
            for check_key, check_name in checks.items():
                if check_key not in results:
                    results[check_key] = {
                        "name": check_name,
                        "score": None,
                        "status": "error",
                        "details": f"Audit failed: {str(e)[:200]}",
                    }

        return results

    async def _fetch_pagespeed(
        self,
        client: httpx.AsyncClient,
        url: str
    ) -> dict | None:
        """Fetch Google PageSpeed Insights data with rate limiting.

        Google PageSpeed API free tier: 1 QPS, 400 queries/hour.
        We use 8s delay to safely stay under the limit with multiple competitors.
        """
        try:
            # Rate limiting: 8s delay between PageSpeed API calls (safe margin for free tier)
            if not hasattr(self, "_last_pagespeed_call"):
                self._last_pagespeed_call = 0.0
            elapsed = time.time() - self._last_pagespeed_call
            if elapsed < 8.0:
                await asyncio.sleep(8.0 - elapsed)
            self._last_pagespeed_call = time.time()

            params = {
                "url": url,
                "strategy": "mobile",
                "category": ["performance", "accessibility", "best-practices", "seo"],
            }
            if self.pagespeed_api_key:
                params["key"] = self.pagespeed_api_key

            ps_url = self.pagespeed_url
            resp = await client.get(ps_url, params=params, timeout=httpx.Timeout(25.0))
            if resp.status_code == 429:
                print(f"[CI Auditor] PageSpeed 429 — waiting 15s before retry")
                await asyncio.sleep(15.0)
                resp = await client.get(ps_url, params=params, timeout=httpx.Timeout(25.0))
            resp.raise_for_status()
            return resp.json()
        except Exception as e:
            print(f"[CI Auditor] PageSpeed API error: {e}")
            return None

    async def _score_real_check(
        self,
        check_key: str,
        url: str,
        final_url: str,
        html: str,
        soup: BeautifulSoup,
        pagespeed: dict | None,
        response: httpx.Response,
        client: httpx.AsyncClient,
    ) -> tuple[int | None, str, str]:
        """Score a single check based on real data. Returns (score, status, details)."""
        scorer_map = {
            # Technical
            "page_speed": self._score_pagespeed,
            "core_web_vitals": self._score_cwv,
            "mobile_friendly": self._score_mobile_friendly,
            "https": self._score_https,
            "structured_data": self._score_structured_data,
            "sitemap": self._score_sitemap,
            "robots_txt": self._score_robots_txt,
            # Content
            "structure": self._score_structure,
            "quality": self._score_content_quality,
            "keywords": self._score_keywords,
            "headings": self._score_headings,
            "images": self._score_images,
            "internal_links": self._score_internal_links,
            "blog": self._score_blog,
            # UX/UI
            "usability": self._score_usability,
            "conversion": self._score_conversion,
            "design": self._score_design,
            "trust_signals": self._score_trust_signals,
            "contact_forms": self._score_contact_forms,
            "online_booking": self._score_online_booking,
            "chat": self._score_chat,
            # Marketing
            "channels": self._score_channels,
            "funnels": self._score_funnels,
            "lead_magnets": self._score_lead_magnets,
            "email_capture": self._score_email_capture,
            "retargeting": self._score_retargeting,
            "analytics": self._score_analytics,
            "crm": self._score_crm,
        }

        scorer = scorer_map.get(check_key)
        if scorer:
            result = scorer(soup, html, url, final_url, pagespeed, response, client)
            if asyncio.iscoroutine(result):
                return await result
            return result
        return (None, "unavailable", "No scorer implemented")

    # ── Technical scorers ──────────────────────────────────────────

    def _score_pagespeed(self, soup, html, url, final_url, pagespeed, response, client) -> tuple:
        if not pagespeed:
            return (None, "unavailable", "PageSpeed API data not available")
        score = pagespeed.get("lighthouseResult", {}).get("categories", {}).get("performance", {}).get("score")
        if score is not None:
            score = round(score * 100)
            status = "good" if score >= 80 else "medium" if score >= 50 else "poor"
            return (score, status, f"PageSpeed Performance: {score}/100 (mobile)")
        return (None, "unavailable", "No performance score in PageSpeed response")

    def _score_cwv(self, soup, html, url, final_url, pagespeed, response, client) -> tuple:
        if not pagespeed:
            return (None, "unavailable", "PageSpeed API data not available")
        audits = pagespeed.get("lighthouseResult", {}).get("audits", {})
        metrics = {}
        for key in ["largest-contentful-paint", "total-blocking-time", "cumulative-layout-shift"]:
            audit = audits.get(key, {})
            val = audit.get("displayValue", "N/A")
            metrics[key] = val

        lcp_audit = audits.get("largest-contentful-paint", {})
        score = lcp_audit.get("score")
        if score is not None:
            score = round(score * 100)
            status = "good" if score >= 80 else "medium" if score >= 50 else "poor"
            details = f"LCP: {metrics['largest-contentful-paint']}, TBT: {metrics['total-blocking-time']}, CLS: {metrics['cumulative-layout-shift']}"
            return (score, status, details)
        return (None, "unavailable", "CWV metrics not available")

    def _score_mobile_friendly(self, soup, html, url, final_url, pagespeed, response, client) -> tuple:
        viewport = soup.find("meta", attrs={"name": "viewport"})
        has_viewport = viewport is not None
        # Check for responsive indicators
        responsive_classes = bool(soup.select("[class*='mobile'], [class*='responsive'], [class*='adaptive']"))
        media_queries = bool(re.findall(r"@media", html, re.IGNORECASE))

        if has_viewport and (responsive_classes or media_queries):
            return (85, "good", "Viewport meta found, responsive design detected")
        elif has_viewport:
            return (60, "medium", "Viewport meta found, but no responsive patterns detected")
        else:
            return (30, "poor", "No viewport meta tag — likely not mobile-friendly")

    def _score_https(self, soup, html, url, final_url, pagespeed, response, client) -> tuple:
        is_https = final_url.startswith("https://")
        hsts = response.headers.get("strict-transport-security", "")
        if is_https and hsts:
            return (95, "good", f"HTTPS with HSTS: {hsts[:80]}")
        elif is_https:
            return (80, "good", "HTTPS enabled (no HSTS)")
        else:
            return (20, "poor", "No HTTPS — security risk")

    def _score_structured_data(self, soup, html, url, final_url, pagespeed, response, client) -> tuple:
        schemas = soup.find_all("script", type="application/ld+json")
        types_found = []
        for s in schemas:
            try:
                data = json.loads(s.string or "{}")
                if isinstance(data, dict):
                    t = data.get("@type", "Unknown")
                elif isinstance(data, list) and data:
                    t = data[0].get("@type", "Unknown") if isinstance(data[0], dict) else "Unknown"
                else:
                    t = "Unknown"
                types_found.append(t)
            except json.JSONDecodeError:
                continue

        if not types_found:
            # Also check microdata
            microdata = soup.find_all(attrs={"itemtype": True})
            types_found = [m.get("itemtype", "Unknown") for m in microdata]

        count = len(types_found)
        if count >= 3:
            return (90, "good", f"{count} schema types: {', '.join(types_found[:5])}")
        elif count >= 1:
            return (65, "medium", f"{count} schema type(s): {', '.join(types_found)}")
        else:
            return (25, "poor", "No structured data (JSON-LD or Microdata) detected")

    async def _score_sitemap(self, soup, html, url, final_url, pagespeed, response, client) -> tuple:
        sitemap_url = urljoin(final_url, "/sitemap.xml")
        try:
            r = await client.get(sitemap_url, headers={"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"}, timeout=httpx.Timeout(10.0))
            if r.status_code == 200 and "xml" in r.headers.get("content-type", ""):
                return (85, "good", f"Sitemap found at {sitemap_url}")
            return (30, "poor", f"No sitemap at {sitemap_url} (status {r.status_code})")
        except Exception:
            return (30, "poor", f"Could not check sitemap at {sitemap_url}")

    async def _score_robots_txt(self, soup, html, url, final_url, pagespeed, response, client) -> tuple:
        robots_url = urljoin(final_url, "/robots.txt")
        try:
            r = await client.get(robots_url, headers={"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"}, timeout=httpx.Timeout(10.0))
            if r.status_code == 200:
                content = r.text[:500]
                has_sitemap_ref = "sitemap:" in content.lower()
                details = f"robots.txt found ({len(r.text)} bytes)"
                if has_sitemap_ref:
                    details += ", references sitemap"
                return (85, "good", details)
            return (30, "poor", "No robots.txt found")
        except Exception:
            return (30, "poor", "Could not check robots.txt")

    # ── Content scorers ────────────────────────────────────────────

    def _score_structure(self, soup, html, url, final_url, pagespeed, response, client) -> tuple:
        nav_links = len(soup.select("nav a, .nav a, .menu a, header a"))
        has_breadcrumbs = bool(soup.select("[class*='breadcrumb'], [aria-label*='breadcrumb']"))
        depth_indicators = len(soup.select("nav ul ul, .submenu, .dropdown"))

        if nav_links > 30 and has_breadcrumbs:
            return (85, "good", f"Clear navigation ({nav_links} nav links, breadcrumbs, {depth_indicators} sub-menus)")
        elif nav_links > 15:
            return (60, "medium", f"Basic navigation ({nav_links} nav links, no breadcrumbs)")
        else:
            return (35, "poor", f"Minimal navigation ({nav_links} nav links)")

    def _score_content_quality(self, soup, html, url, final_url, pagespeed, response, client) -> tuple:
        # Extract visible text
        for tag in soup(["script", "style", "nav", "footer", "header"]):
            tag.decompose()
        text = soup.get_text(separator=" ")
        text = re.sub(r"\s+", " ", text).strip()
        word_count = len(text.split())

        # Check for thin content indicators
        paragraphs = len(soup.find_all("p"))
        lists = len(soup.find_all(["ul", "ol"]))
        has_headings = len(soup.find_all(["h1", "h2", "h3"]))

        if word_count > 1500 and paragraphs > 10 and has_headings:
            return (85, "good", f"Rich content: ~{word_count} words, {paragraphs} paragraphs, {has_headings} headings")
        elif word_count > 500:
            return (60, "medium", f"Adequate content: ~{word_count} words, {paragraphs} paragraphs")
        else:
            return (30, "poor", f"Thin content: ~{word_count} words")

    def _score_keywords(self, soup, html, url, final_url, pagespeed, response, client) -> tuple:
        title = soup.find("title")
        title_text = title.get_text().strip() if title else ""
        meta_desc = soup.find("meta", attrs={"name": "description"})
        desc_text = meta_desc.get("content", "").strip() if meta_desc else ""
        h1 = soup.find("h1")
        h1_text = h1.get_text().strip() if h1 else ""

        has_title = len(title_text) > 0
        has_desc = len(desc_text) > 50
        has_h1 = len(h1_text) > 0

        score = 0
        if has_title:
            score += 35
        if has_desc:
            score += 30
        if has_h1:
            score += 35

        status = "good" if score >= 70 else "medium" if score >= 40 else "poor"
        details_parts = []
        if title_text:
            details_parts.append(f"Title: '{title_text[:80]}'")
        if desc_text:
            details_parts.append(f"Description: '{desc_text[:80]}'")
        if h1_text:
            details_parts.append(f"H1: '{h1_text[:80]}'")
        details = "; ".join(details_parts) if details_parts else "No title/description/H1 found"

        return (score, status, details)

    def _score_headings(self, soup, html, url, final_url, pagespeed, response, client) -> tuple:
        h1_count = len(soup.find_all("h1"))
        h2_count = len(soup.find_all("h2"))
        h3_count = len(soup.find_all("h3"))
        total = h1_count + h2_count + h3_count

        if h1_count == 1 and h2_count >= 3 and total >= 8:
            return (90, "good", f"Proper hierarchy: 1 H1, {h2_count} H2, {h3_count} H3")
        elif h1_count >= 1 and total >= 3:
            return (60, "medium", f"Weak hierarchy: {h1_count} H1, {h2_count} H2, {h3_count} H3")
        elif total > 0:
            return (35, "poor", f"Poor heading structure: {h1_count} H1(s)")
        else:
            return (10, "poor", "No headings found")

    def _score_images(self, soup, html, url, final_url, pagespeed, response, client) -> tuple:
        images = soup.find_all("img")
        total_imgs = len(images)
        with_alt = sum(1 for img in images if img.get("alt"))
        with_srcset = sum(1 for img in images if img.get("srcset"))
        alt_pct = (with_alt / total_imgs * 100) if total_imgs > 0 else 0

        if total_imgs == 0:
            return (80, "good", "No images (may be text-only landing)")
        if alt_pct >= 90 and with_srcset > 0:
            return (90, "good", f"{total_imgs} images, {with_alt} with alt ({alt_pct:.0f}%), {with_srcset} responsive")
        elif alt_pct >= 70:
            return (60, "medium", f"{total_imgs} images, {with_alt} with alt ({alt_pct:.0f}%)")
        else:
            return (30, "poor", f"{total_imgs} images, only {with_alt} with alt ({alt_pct:.0f}%)")

    def _score_internal_links(self, soup, html, url, final_url, pagespeed, response, client) -> tuple:
        base_domain = urlparse(final_url).netloc
        all_links = soup.find_all("a", href=True)
        internal = 0
        external = 0
        for link in all_links:
            href = link.get("href", "")
            parsed = urlparse(href)
            if not parsed.netloc or parsed.netloc == base_domain:
                internal += 1
            else:
                external += 1

        total = internal + external
        if total == 0:
            return (10, "poor", "No links found")
        ratio = internal / total * 100 if total > 0 else 0

        if internal > 50 and 50 <= ratio <= 95:
            return (85, "good", f"{internal} internal / {external} external links ({ratio:.0f}% internal)")
        elif internal > 20:
            return (60, "medium", f"{internal} internal / {external} external links")
        else:
            return (30, "poor", f"Only {internal} internal links")

    def _score_blog(self, soup, html, url, final_url, pagespeed, response, client) -> tuple:
        blog_indicators = soup.select(
            "a[href*='blog'], a[href*='articles'], a[href*='news'], a[href*='novosti'], "
            "a[href*='stati'], a[href*='/journal/']"
        )
        article_blocks = soup.select("article, .post, .blog-item, .news-item, [class*='article']")

        if len(blog_indicators) >= 3 or len(article_blocks) >= 3:
            return (80, "good", f"Active blog detected ({len(blog_indicators)} links, {len(article_blocks)} articles)")
        elif len(blog_indicators) >= 1:
            return (50, "medium", f"Blog section exists ({len(blog_indicators)} link(s))")
        else:
            return (20, "poor", "No blog section detected")

    # ── UX/UI scorers ──────────────────────────────────────────────

    def _score_usability(self, soup, html, url, final_url, pagespeed, response, client) -> tuple:
        has_search = bool(soup.select("input[type='search'], input[name*='search'], [class*='search']"))
        has_nav = bool(soup.find("nav"))
        has_footer = bool(soup.find("footer"))
        breadcrumb = bool(soup.select("[class*='breadcrumb'], [aria-label*='breadcrumb']"))

        score = 0
        details_parts = []
        for name, present in [("nav", has_nav), ("footer", has_footer), ("search", has_search), ("breadcrumbs", breadcrumb)]:
            if present:
                score += 25
                details_parts.append(name)

        status = "good" if score >= 75 else "medium" if score >= 50 else "poor"
        details = f"Found: {', '.join(details_parts)}" if details_parts else "Missing key navigation elements"
        return (score, status, details)

    def _score_conversion(self, soup, html, url, final_url, pagespeed, response, client) -> tuple:
        forms = soup.find_all("form")
        cta_elements = soup.select(
            "a[class*='btn'], button[class*='btn'], "
            "[class*='cta'], [class*='zapis'], [class*='order'], "
            "a[href*='zapis'], a[href*='order'], a[href*='callback']"
        )
        phone_pattern = r'\+7[\s\(]?\d{3}[\s\)]?\d{3}[\s\-]?\d{2}[\s\-]?\d{2}'
        has_phone = bool(re.search(phone_pattern, html))

        score = 0
        det = []
        if len(forms) > 0:
            score += 35
            det.append(f"{len(forms)} form(s)")
        if len(cta_elements) >= 2:
            score += 35
            det.append(f"{len(cta_elements)} CTA elements")
        if has_phone:
            score += 30
            det.append("phone number visible")

        status = "good" if score >= 70 else "medium" if score >= 40 else "poor"
        details = "; ".join(det) if det else "No conversion elements detected"
        return (score, status, details)

    def _score_design(self, soup, html, url, final_url, pagespeed, response, client) -> tuple:
        viewport = bool(soup.find("meta", attrs={"name": "viewport"}))
        # Detect CSS framework indicators
        bootstrap = bool(soup.select("[class*='bs-'], link[href*='bootstrap']")) or "bootstrap" in html.lower()[:5000]
        tailwind = bool(soup.select("[class*='tw-'], [class*='hover:']")) or "tailwind" in html.lower()[:5000]
        modern_css = bool(re.findall(r"(--[\w-]+:\s*|grid|flex|clamp\(|@container)", html[:10000]))
        has_favicon = bool(soup.find("link", rel=lambda r: r and "icon" in r))

        score = 40  # base — site loads
        if viewport:
            score += 15
        if bootstrap or tailwind:
            score += 15
        if modern_css:
            score += 15
        if has_favicon:
            score += 10

        framework = "Tailwind" if tailwind else "Bootstrap" if bootstrap else "custom"
        status = "good" if score >= 70 else "medium" if score >= 50 else "poor"
        return (score, status, f"Framework: {framework}, viewport: {viewport}, favicon: {has_favicon}")

    def _score_trust_signals(self, soup, html, url, final_url, pagespeed, response, client) -> tuple:
        # Detect reviews, certificates, licenses, guarantees
        trust_indicators = soup.select(
            "[class*='review'], [class*='otzyv'], [class*='certificate'], [class*='license'], "
            "[class*='guarantee'], [class*='award'], [class*='rating'], "
            "[class*='partner'], [class*='accredit']"
        )
        trust_text = html.lower()
        trust_keywords = ["лицензия", "сертификат", "диплом", "награда", "аккредитация",
                          "гарантия", "отзыв", "рейтинг", "стаж"]

        found_keywords = [kw for kw in trust_keywords if kw in trust_text]
        count = len(trust_indicators) + len(found_keywords)

        if count >= 5:
            return (85, "good", f"{len(trust_indicators)} visual + {len(found_keywords)} text signals: {found_keywords[:4]}")
        elif count >= 2:
            return (55, "medium", f"{count} trust signals detected")
        else:
            return (20, "poor", "Few or no trust signals")

    def _score_contact_forms(self, soup, html, url, final_url, pagespeed, response, client) -> tuple:
        forms = soup.find_all("form")
        contact_forms = soup.select(
            "[class*='contact'], [class*='callback'], [class*='feedback'], "
            "[class*='zapis'], [class*='appointment'], [id*='contact']"
        )
        inputs_in_forms = sum(len(form.find_all(["input", "textarea"])) for form in forms)

        if len(contact_forms) >= 2 or inputs_in_forms >= 6:
            return (85, "good", f"{len(contact_forms) or len(forms)} contact form(s), {inputs_in_forms} fields")
        elif len(forms) >= 1:
            return (55, "medium", f"{len(forms)} form(s), {inputs_in_forms} field(s)")
        else:
            return (15, "poor", "No contact forms detected")

    def _score_online_booking(self, soup, html, url, final_url, pagespeed, response, client) -> tuple:
        booking_indicators = soup.select(
            "a[href*='zapis'], a[href*='appointment'], a[href*='booking'], "
            "a[href*='online'], a[href*='bron' ], "
            "[class*='booking'], [class*='appointment'], [class*='zapis']"
        )
        # Check for known booking widget scripts
        booking_scripts = soup.select(
            "script[src*='prodoctorov'], script[src*='medflex'], script[src*='infodoktor'], "
            "script[src*='yclients'], script[src*='dikidi']"
        )

        count = len(booking_indicators) + len(booking_scripts)
        if count >= 2:
            return (85, "good", f"Online booking detected ({count} signals)")
        elif count == 1:
            return (50, "medium", "1 booking signal — may have online booking")
        else:
            return (15, "poor", "No online booking detected")

    def _score_chat(self, soup, html, url, final_url, pagespeed, response, client) -> tuple:
        chat_scripts = soup.select(
            "script[src*='jivosite'], script[src*='jivochat'], script[src*='chatra'], "
            "script[src*='tawk'], script[src*='livechat'], script[src*='intercom'], "
            "script[src*='carrot'], script[src*='zopim'], script[src*='whatsapp']"
        )
        chat_links = soup.select(
            "a[href*='whatsapp'], a[href*='t.me/'], a[href*='telegram'], "
            "a[href*='wa.me'], a[class*='chat']"
        )

        total = len(chat_scripts) + len(chat_links)
        if total >= 2:
            return (85, "good", f"Chat widget detected ({total} signals)")
        elif total == 1:
            return (50, "medium", "1 chat signal — possible chat widget")
        else:
            return (20, "poor", "No chat widget detected")

    # ── Marketing scorers ──────────────────────────────────────────

    def _score_channels(self, soup, html, url, final_url, pagespeed, response, client) -> tuple:
        social_links = soup.select(
            "a[href*='vk.com'], a[href*='t.me/'], a[href*='youtube.com'], "
            "a[href*='instagram.com'], a[href*='ok.ru'], a[href*='dzen.ru'], "
            "a[href*='rutube.ru']"
        )
        channels_found = set()
        for link in social_links:
            href = link.get("href", "")
            for ch in ["vk.com", "t.me", "youtube.com", "instagram.com", "ok.ru", "dzen.ru", "rutube.ru"]:
                if ch in href:
                    channels_found.add(ch)

        count = len(channels_found)
        if count >= 4:
            return (90, "good", f"{count} channels: {', '.join(channels_found)}")
        elif count >= 2:
            return (60, "medium", f"{count} channels: {', '.join(channels_found)}")
        elif count >= 1:
            return (35, "poor", f"Only 1 channel: {channels_found.pop()}")
        else:
            return (10, "poor", "No social channels detected")

    def _score_funnels(self, soup, html, url, final_url, pagespeed, response, client) -> tuple:
        # Hard to detect without tracking — check for funnel indicators
        has_landing = bool(soup.select("[class*='landing'], [class*='promo'], [class*='offer']"))
        has_pricing = bool(soup.select("a[href*='price'], a[href*='cena'], a[href*='service']"))
        has_cta = bool(soup.select("a[class*='btn'], button, [class*='cta']"))

        if has_landing and has_pricing and has_cta:
            return (75, "good", "Landing → pricing → CTA funnel structure detected")
        elif has_pricing and has_cta:
            return (50, "medium", "Pricing + CTA detected (partial funnel)")
        else:
            return (None, "unavailable", "Funnel detection requires analytics data. Only HTML signals available.")

    def _score_lead_magnets(self, soup, html, url, final_url, pagespeed, response, client) -> tuple:
        magnet_keywords = ["акци", "скидк", "спецпредложен", "бесплатн", "подарок",
                           "консультаци", "промокод", "купо"]
        found = [kw for kw in magnet_keywords if kw in html.lower()]
        promo_elements = soup.select(
            "[class*='promo'], [class*='sale'], [class*='discount'], [class*='special'], "
            "[class*='action'], [class*='aktsi']"
        )

        count = len(found) + len(promo_elements)
        if count >= 4:
            return (80, "good", f"Lead magnets detected: {found[:4]}")
        elif count >= 1:
            return (45, "medium", f"Possible lead magnet: {found[:2]}")
        else:
            return (15, "poor", "No lead magnets detected")

    def _score_email_capture(self, soup, html, url, final_url, pagespeed, response, client) -> tuple:
        email_inputs = soup.select("input[type='email'], input[name*='email'], input[name*='mail']")
        subscribe_forms = soup.select(
            "form[class*='subscribe'], [class*='newsletter'], [class*='subscription'], "
            "[class*='mailing']"
        )
        count = len(email_inputs) + len(subscribe_forms)
        if count >= 2:
            return (80, "good", f"Email capture detected ({len(email_inputs)} fields, {len(subscribe_forms)} forms)")
        elif count == 1:
            return (45, "medium", "1 email capture signal")
        else:
            return (15, "poor", "No email capture detected")

    def _score_retargeting(self, soup, html, url, final_url, pagespeed, response, client) -> tuple:
        # Detect retargeting pixels
        pixels = []
        if "facebook.com/tr" in html or "connect.facebook.net/en_US/fbevents.js" in html:
            pixels.append("Facebook Pixel")
        if "vk.com/js/api/openapi.js" in html or "VK.Retargeting" in html:
            pixels.append("VK Pixel")
        if "mc.yandex.ru/metrika/tag.js" in html:
            pixels.append("Yandex.Metrika")
        if "my.target.com" in html:
            pixels.append("myTarget")
        if "google-analytics.com" in html or "googletagmanager.com" in html:
            pixels.append("Google Analytics/Tag Manager")

        count = len(pixels)
        if count >= 3:
            return (90, "good", f"Retargeting: {', '.join(pixels)}")
        elif count >= 1:
            return (55, "medium", f"Retargeting: {', '.join(pixels)}")
        else:
            return (15, "poor", "No retargeting pixels detected")

    def _score_analytics(self, soup, html, url, final_url, pagespeed, response, client) -> tuple:
        has_ga = bool(re.search(r"(google-analytics\.com|googletagmanager\.com)", html))
        has_metrika = bool(re.search(r"mc\.yandex\.ru\/metrika", html))
        has_pixel = bool(re.search(r"facebook\.com\/tr|vk\.com\/rtrg", html))

        found = []
        if has_metrika:
            found.append("Yandex.Metrika")
        if has_ga:
            found.append("Google Analytics")
        if has_pixel:
            found.append("Social Pixel")

        if len(found) >= 2:
            return (90, "good", f"Analytics: {', '.join(found)}")
        elif len(found) == 1:
            return (55, "medium", f"Analytics: {found[0]} only")
        else:
            return (10, "poor", "No analytics detected")

    def _score_crm(self, soup, html, url, final_url, pagespeed, response, client) -> tuple:
        crm_signals = [
            ("amoCRM", "amocrm.ru"),
            ("Bitrix24", "bitrix24"),
            ("Yclients", "yclients.com"),
            ("1C-UMI", "1c-umi"),
            ("MedFlex", "medflex.ru"),
            ("InfoDoctor", "infodoktor.ru"),
        ]
        found = []
        for name, signal in crm_signals:
            if signal in html.lower():
                found.append(name)

        if found:
            return (85, "good", f"CRM detected: {', '.join(found)}")
        return (None, "unavailable", "No CRM integration signals detected (may use custom CRM or none)")

    async def _calculate_scores(
        self,
        audits: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Рассчитать общие оценки для каждого аудита.

        Args:
            audits: список аудитов

        Returns:
            Аудиты с рассчитанными оценками
        """
        scored_audits = []

        for audit in audits:
            dimension_scores = {}

            # Рассчитать средний score для каждого dimension
            for dimension, checks in audit["dimensions"].items():
                scores = [check["score"] for check in checks.values() if check["score"] is not None]
                dimension_scores[dimension] = sum(scores) / len(scores) if scores else 0

            # Рассчитать общий weighted score
            total_score = sum(
                dimension_scores.get(dim, 0) * weight
                for dim, weight in self.weights.items()
            )

            audit["dimension_scores"] = dimension_scores
            audit["total_score"] = round(total_score, 1)

            # Определить grade
            if total_score >= 85:
                audit["grade"] = "A"
            elif total_score >= 70:
                audit["grade"] = "B"
            elif total_score >= 55:
                audit["grade"] = "C"
            else:
                audit["grade"] = "D"

            scored_audits.append(audit)

        print(f"[CI Auditor] Рассчитаны оценки для {len(scored_audits)} конкурентов")

        return scored_audits

    async def _generate_insights(
        self,
        audits: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Сгенерировать инсайты из аудитов.

        Args:
            audits: список аудитов с оценками

        Returns:
            Инсайты о рынке
        """
        # Средние оценки по dimensions
        avg_scores = {}
        for dimension in self.audit_dimensions.keys():
            scores = [
                audit["dimension_scores"].get(dimension, 0)
                for audit in audits
                if dimension in audit["dimension_scores"]
            ]
            avg_scores[dimension] = round(sum(scores) / len(scores), 1) if scores else 0

        # Лучший и худший конкурент
        best = max(audits, key=lambda x: x["total_score"])
        worst = min(audits, key=lambda x: x["total_score"])

        insights = {
            "market_average": round(sum(a["total_score"] for a in audits) / len(audits), 1),
            "dimension_averages": avg_scores,
            "best_competitor": {
                "name": best["name"],
                "score": best["total_score"],
                "grade": best["grade"]
            },
            "worst_competitor": {
                "name": worst["name"],
                "score": worst["total_score"],
                "grade": worst["grade"]
            },
            "strongest_dimension": max(avg_scores.items(), key=lambda x: x[1])[0],
            "weakest_dimension": min(avg_scores.items(), key=lambda x: x[1])[0]
        }

        print(f"[CI Auditor] Средняя оценка рынка: {insights['market_average']}")

        return insights

    async def _identify_gaps(
        self,
        audits: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Определить gaps и возможности.

        Args:
            audits: список аудитов с оценками

        Returns:
            Список gaps и возможностей
        """
        gaps = []

        # Найти общие слабые места
        for dimension in self.audit_dimensions.keys():
            scores = [
                audit["dimension_scores"].get(dimension, 0)
                for audit in audits
                if dimension in audit["dimension_scores"]
            ]

            if scores:
                avg = sum(scores) / len(scores)

                if avg < 70:
                    gaps.append({
                        "type": "market_gap",
                        "dimension": dimension,
                        "avg_score": round(avg, 1),
                        "opportunity": f"Рынок слаб в {dimension} (средняя оценка {round(avg, 1)}). Возможность выделиться.",
                        "priority": "high" if avg < 60 else "medium"
                    })

        # Найти специфичные gaps у лидеров
        best_audits = sorted(audits, key=lambda x: x["total_score"], reverse=True)[:3]

        for audit in best_audits:
            for dimension, score in audit["dimension_scores"].items():
                if score < 70:
                    gaps.append({
                        "type": "competitor_weakness",
                        "competitor": audit["name"],
                        "dimension": dimension,
                        "score": score,
                        "opportunity": f"{audit['name']} слаб в {dimension} ({score}). Можно обойти.",
                        "priority": "medium"
                    })

        print(f"[CI Auditor] Найдено {len(gaps)} gaps и возможностей")

        return gaps

    async def _save_results(self, results: Dict[str, Any]):
        """Сохранить результаты в файл."""
        output_file = "AIM/data/ci-audits.json"

        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)

        print(f"[CI Auditor] Результаты сохранены в {output_file}")

    def get_capabilities(self) -> List[str]:
        """Возвращает список возможностей агента."""
        return [
            "technical_audit",
            "content_audit",
            "ux_ui_audit",
            "marketing_audit",
            "competitor_scoring",
            "gap_analysis"
        ]
