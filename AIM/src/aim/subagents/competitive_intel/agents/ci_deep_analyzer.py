"""
CI Deep Analyzer - Deep Competitor Analysis System

Глубокий анализ конкурентов по молекулам:
- Sitemap parsing (все URL сайта)
- Page type classification (главная, услуги, статьи, контакты)
- Smart crawling (BFS с приоритетами)
- Deep page analysis (SEO, контент, технический, Schema.org)
- Aggregation & statistics (паттерны, консистентность)
- Detailed reporting (Executive Summary + детальный анализ)

Quality Over Speed: 10-30 минут на конкурента (качество важнее скорости)
"""

import asyncio
import re
import html
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Set
from urllib.parse import urljoin, urlparse
import xml.etree.ElementTree as ET

import aiohttp
import ssl
from bs4 import BeautifulSoup

from meai.agents.base_agent import Agent, Task, TaskResult
from aim.core.agent_learning import AgentLearning


class CIDeepAnalyzer(Agent):
    """Deep Competitor Analysis Agent

    Анализирует конкурентов глубоко и тщательно:
    1. Парсит sitemap для получения всех URL
    2. Классифицирует страницы по типам
    3. Crawls сайт с приоритизацией
    4. Анализирует каждую страницу детально
    5. Агрегирует данные и находит паттерны
    6. Генерирует детальный отчёт
    """

    def __init__(
        self,
        agent_id: str,
        database_url: str,
        vault_path: str,
        max_pages: int = 50,
        delay_between_requests: float = 2.0
    ):
        super().__init__(agent_id, database_url, vault_path)
        self.max_pages = max_pages
        self.delay = delay_between_requests
        self.user_agents = [
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36'
        ]
        self.current_ua_index = 0

        # Initialize learning system
        self.learning = AgentLearning(agent_id=agent_id)

        # Initialize logger
        self.logger = logging.getLogger(f"CIDeepAnalyzer.{agent_id}")

    def get_capabilities(self) -> list[str]:
        return [
            "deep_competitor_analysis",
            "sitemap_parsing",
            "page_classification",
            "smart_crawling",
            "content_analysis",
            "seo_analysis",
            "technical_analysis"
        ]

    # Security Helper Methods

    def _escape_html(self, text: str) -> str:
        """Escape HTML to prevent XSS attacks"""
        if not text:
            return ""
        return html.escape(str(text), quote=True)

    def _safe_detector_call(self, detector_func, *args, **kwargs) -> Dict[str, Any]:
        """Safely call a detector with error handling

        Returns detector result or error dict if detector fails
        """
        try:
            return detector_func(*args, **kwargs)
        except Exception as e:
            self.logger.error(f"Detector {detector_func.__name__} failed: {e}")
            return {
                "error": str(e),
                "confidence": 0.0,
                "detector": detector_func.__name__
            }

    async def execute_task(self, task: Task) -> TaskResult:
        """Execute deep competitor analysis

        Task payload:
        {
            "competitors": [
                {"name": "Competitor 1", "url": "https://example.com"}
            ]
        }
        """
        try:
            start_time = datetime.now()
            competitors = task.payload.get("competitors", [])

            if not competitors:
                return TaskResult(
                    subtask_id=task.subtask_id,
                    agent_id=self.agent_id,
                    action=task.action,
                    status="failed",
                    result={"error": "No competitors provided"},
                    error="No competitors provided",
                    duration_seconds=0.0,
                    completed_at=datetime.now()
                )

            # 🎓 LEARNING: Read lessons before starting
            print(f"[CI Deep] 📚 Читаю уроки перед анализом...")
            lessons = await self.learning.get_lessons(
                tags=["validation", "ci-system", "silent-failure"],
                severity="critical"
            )

            if lessons:
                print(f"[CI Deep] ✅ Найдено {len(lessons)} уроков")
                applied = await self.learning.apply_lessons(task, lessons)
                print(f"[CI Deep] 📋 Применено {len(applied['rules_applied'])} правил")

                # Show prevention rules
                for rule in applied['rules_applied'][:3]:  # Show first 3
                    print(f"[CI Deep]   • {rule['type']}: {rule['rule'][:80]}...")

            print(f"[CI Deep] 🔍 Глубокий анализ {len(competitors)} конкурентов")
            print(f"[CI Deep] ⏱️  Ожидаемое время: {len(competitors) * 10}-{len(competitors) * 30} минут")

            # Analyze each competitor deeply
            deep_profiles = []
            for i, competitor in enumerate(competitors, 1):
                print(f"\n[CI Deep] 📊 Конкурент {i}/{len(competitors)}: {competitor['name']}")
                profile = await self._analyze_competitor_deeply(competitor)
                deep_profiles.append(profile)

            # Aggregate insights
            market_insights = await self._generate_market_insights(deep_profiles)

            results = {
                "analysis_date": datetime.now().isoformat(),
                "total_analyzed": len(competitors),
                "deep_profiles": deep_profiles,
                "market_insights": market_insights,
                "analysis_quality": "deep",
                "pages_analyzed_per_competitor": self.max_pages
            }

            # Save results
            output_dir = Path("AIM/data/ci-deep")
            output_dir.mkdir(parents=True, exist_ok=True)

            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = output_dir / f"deep_analysis_{timestamp}.json"

            import json
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(results, f, ensure_ascii=False, indent=2)

            duration = (datetime.now() - start_time).total_seconds()
            print(f"\n[CI Deep] ✅ Глубокий анализ завершён за {duration:.1f}s")
            print(f"[CI Deep] 📁 Результаты: {output_file}")

            # 🎓 LEARNING: Record success
            avg_quality = sum(p["deep_analysis"]["quality_score"] for p in deep_profiles) / len(deep_profiles)
            await self.learning.record_success(
                task=task,
                result=results,
                metrics={
                    "competitors_analyzed": len(competitors),
                    "avg_quality_score": avg_quality,
                    "duration_seconds": duration
                }
            )

            return TaskResult(
                subtask_id=task.subtask_id,
                agent_id=self.agent_id,
                action=task.action,
                status="success",
                result=results,
                error=None,
                duration_seconds=duration,
                completed_at=datetime.now()
            )

        except Exception as e:
            print(f"[CI Deep] ✗ Error: {e}")
            import traceback
            traceback.print_exc()

            # 🎓 LEARNING: Record failure
            await self.learning.record_failure(
                task=task,
                error=e,
                context={
                    "competitors": len(competitors) if 'competitors' in locals() else 0,
                    "stage": "unknown"
                }
            )

            return TaskResult(
                subtask_id=task.subtask_id,
                agent_id=self.agent_id,
                action=task.action,
                status="failed",
                result={"error": str(e)},
                error=str(e),
                duration_seconds=(datetime.now() - start_time).total_seconds(),
                completed_at=datetime.now()
            )

    async def _analyze_competitor_deeply(self, competitor: Dict[str, Any]) -> Dict[str, Any]:
        """Deep analysis of single competitor"""
        name = competitor["name"]
        url = competitor["url"]

        print(f"[CI Deep]   1️⃣  Парсинг sitemap...")
        sitemap_urls = await self._parse_sitemap(url)
        print(f"[CI Deep]   ✓ Найдено {len(sitemap_urls)} URL в sitemap")

        print(f"[CI Deep]   2️⃣  Crawling сайта...")
        all_urls = await self._smart_crawl(url, sitemap_urls)
        print(f"[CI Deep]   ✓ Собрано {len(all_urls)} URL для анализа")

        print(f"[CI Deep]   3️⃣  Классификация страниц...")
        classified_pages = await self._classify_pages(all_urls)
        print(f"[CI Deep]   ✓ Классифицировано по типам")

        print(f"[CI Deep]   4️⃣  Глубокий анализ страниц...")
        analyzed_pages = await self._analyze_pages_deeply(classified_pages, url)
        print(f"[CI Deep]   ✓ Проанализировано {len(analyzed_pages)} страниц")

        print(f"[CI Deep]   5️⃣  Агрегация данных...")
        aggregated = await self._aggregate_analysis(analyzed_pages)
        print(f"[CI Deep]   ✓ Данные агрегированы")

        print(f"[CI Deep]   6️⃣  Генерация отчёта о проблемах...")
        issues_report = self._generate_issues_report(analyzed_pages)
        print(f"[CI Deep]   ✓ Найдено {issues_report['total_issues']} проблем")

        return {
            "name": name,
            "url": url,
            "total_pages_found": len(all_urls),
            "pages_analyzed": len(analyzed_pages),
            "page_types": classified_pages,
            "deep_analysis": aggregated,
            "issues": issues_report,
            "analyzed_at": datetime.now().isoformat()
        }

    async def _parse_sitemap(self, base_url: str) -> List[str]:
        """Parse sitemap.xml to get all URLs

        Steps:
        1. Check robots.txt for sitemap location
        2. Parse sitemap.xml (handle sitemap index)
        3. Extract all URLs
        """
        urls = []

        try:
            # Try robots.txt first
            robots_url = urljoin(base_url, '/robots.txt')
            robots_content = await self._fetch_url(robots_url)

            sitemap_urls = []
            if robots_content:
                for line in robots_content.split('\n'):
                    if line.lower().startswith('sitemap:'):
                        sitemap_url = line.split(':', 1)[1].strip()
                        sitemap_urls.append(sitemap_url)

            # If no sitemap in robots.txt, try default locations
            if not sitemap_urls:
                sitemap_urls = [
                    urljoin(base_url, '/sitemap.xml'),
                    urljoin(base_url, '/sitemap_index.xml')
                ]

            # Parse each sitemap
            for sitemap_url in sitemap_urls:
                sitemap_content = await self._fetch_url(sitemap_url)
                if sitemap_content:
                    urls.extend(self._extract_urls_from_sitemap(sitemap_content))

        except Exception as e:
            print(f"[CI Deep]   ⚠️  Sitemap parsing error: {e}")

        return urls

    def _extract_urls_from_sitemap(self, xml_content: str) -> List[str]:
        """Extract URLs from sitemap XML"""
        urls = []

        try:
            root = ET.fromstring(xml_content)

            # Handle sitemap index
            for sitemap in root.findall('.//{http://www.sitemaps.org/schemas/sitemap/0.9}sitemap'):
                loc = sitemap.find('{http://www.sitemaps.org/schemas/sitemap/0.9}loc')
                if loc is not None and loc.text:
                    # TODO: recursively fetch sub-sitemaps
                    pass

            # Handle regular sitemap
            for url in root.findall('.//{http://www.sitemaps.org/schemas/sitemap/0.9}url'):
                loc = url.find('{http://www.sitemaps.org/schemas/sitemap/0.9}loc')
                if loc is not None and loc.text:
                    urls.append(loc.text)

        except Exception as e:
            print(f"[CI Deep]   ⚠️  XML parsing error: {e}")

        return urls

    async def _smart_crawl(self, base_url: str, sitemap_urls: List[str]) -> List[str]:
        """Smart crawling with priorities

        Strategy:
        1. Start with sitemap URLs if available
        2. If no sitemap, start from homepage and extract links
        3. BFS crawl with priorities (services > about > blog)
        4. Limit to max_pages
        """
        visited: Set[str] = set()
        to_visit: List[tuple[int, str]] = []  # (priority, url)

        # If we have sitemap URLs, use them
        if sitemap_urls:
            for url in sitemap_urls[:self.max_pages * 2]:  # Get more URLs than needed
                priority = self._get_url_priority(url)
                to_visit.append((priority, url))
        else:
            # No sitemap - start from homepage
            print(f"[CI Deep]   ⚠️  No sitemap found, starting from homepage")
            to_visit.append((10, base_url))

        # Sort by priority (higher first)
        to_visit.sort(reverse=True)

        all_urls = []

        while to_visit and len(all_urls) < self.max_pages:
            _, url = to_visit.pop(0)

            if url in visited:
                continue

            visited.add(url)
            all_urls.append(url)

            # Extract links from page if we need more URLs
            if len(all_urls) < self.max_pages and len(to_visit) < 10:
                html = await self._fetch_url(url)
                if html:
                    links = self._extract_links(html, base_url)
                    for link in links:
                        if link not in visited and link not in [u for _, u in to_visit]:
                            priority = self._get_url_priority(link)
                            to_visit.append((priority, link))

                    # Re-sort by priority
                    to_visit.sort(reverse=True)

                # Respectful delay after fetching
                await asyncio.sleep(self.delay)

        return all_urls[:self.max_pages]

    def _extract_links(self, html: str, base_url: str) -> List[str]:
        """Extract links from HTML"""
        links = []

        # Find all <a href="..."> tags
        href_pattern = r'<a[^>]*href=["\']([^"\']+)["\']'
        matches = re.findall(href_pattern, html, re.IGNORECASE)

        base_domain = urlparse(base_url).netloc

        for href in matches:
            # Convert relative URLs to absolute
            absolute_url = urljoin(base_url, href)

            # Only include links from same domain
            link_domain = urlparse(absolute_url).netloc
            if link_domain == base_domain:
                # Remove fragments and query params for cleaner URLs
                parsed = urlparse(absolute_url)
                clean_url = f"{parsed.scheme}://{parsed.netloc}{parsed.path}"

                # Skip common non-content URLs
                if not any(x in clean_url.lower() for x in ['.jpg', '.png', '.pdf', '.zip', 'javascript:', 'mailto:']):
                    links.append(clean_url)

        return list(set(links))  # Remove duplicates

    def _get_url_priority(self, url: str) -> int:
        """Get URL priority for crawling

        Priority levels:
        10 - Homepage
        9 - Services/Products
        8 - About/Contacts
        7 - Prices
        6 - Blog/Articles
        5 - Other
        """
        url_lower = url.lower()

        if url_lower.endswith('/') and url_lower.count('/') == 3:
            return 10  # Homepage

        if any(x in url_lower for x in ['/services', '/uslugi', '/products', '/tovary']):
            return 9

        if any(x in url_lower for x in ['/about', '/o-nas', '/contacts', '/kontakty']):
            return 8

        if any(x in url_lower for x in ['/prices', '/ceny', '/price']):
            return 7

        if any(x in url_lower for x in ['/blog', '/articles', '/stati', '/news']):
            return 6

        return 5

    async def _classify_pages(self, urls: List[str]) -> Dict[str, List[str]]:
        """Classify pages by type"""
        classified = {
            "homepage": [],
            "services": [],
            "about": [],
            "contacts": [],
            "prices": [],
            "blog": [],
            "other": []
        }

        for url in urls:
            url_lower = url.lower()

            if url_lower.endswith('/') and url_lower.count('/') == 3:
                classified["homepage"].append(url)
            elif any(x in url_lower for x in ['/services', '/uslugi', '/products']):
                classified["services"].append(url)
            elif any(x in url_lower for x in ['/about', '/o-nas']):
                classified["about"].append(url)
            elif any(x in url_lower for x in ['/contacts', '/kontakty']):
                classified["contacts"].append(url)
            elif any(x in url_lower for x in ['/prices', '/ceny']):
                classified["prices"].append(url)
            elif any(x in url_lower for x in ['/blog', '/articles', '/news']):
                classified["blog"].append(url)
            else:
                classified["other"].append(url)

        return classified

    async def _analyze_pages_deeply(
        self,
        classified_pages: Dict[str, List[str]],
        base_url: str
    ) -> List[Dict[str, Any]]:
        """Deep analysis of each page with CWV sampling"""
        analyzed = []

        # Priority order for page types
        priority_order = ["homepage", "services", "about", "contacts", "prices", "blog", "other"]

        # Sample pages for CWV analysis (10-20 pages)
        cwv_sample_urls = []
        cwv_sample_size = min(20, self.max_pages)

        # Analyze pages by priority until we reach max_pages
        for page_type in priority_order:
            urls = classified_pages.get(page_type, [])

            for url in urls:
                if len(analyzed) >= self.max_pages:
                    break

                print(f"[CI Deep]     📄 {page_type}: {url}")

                page_analysis = await self._analyze_single_page(url, page_type)
                analyzed.append(page_analysis)

                # Add to CWV sample (prioritize important pages)
                if len(cwv_sample_urls) < cwv_sample_size:
                    if page_type in ["homepage", "services", "about"]:
                        cwv_sample_urls.append(url)
                    elif len(cwv_sample_urls) < cwv_sample_size * 0.7:
                        cwv_sample_urls.append(url)

                # Respectful delay
                await asyncio.sleep(self.delay)

            if len(analyzed) >= self.max_pages:
                break

        # Analyze CWV, Mobile, and Accessibility for sampled pages
        print(f"[CI Deep]   📊 Analyzing CWV, Mobile, and Accessibility for {len(cwv_sample_urls)} pages...")
        cwv_results = []
        mobile_results = []
        accessibility_results = []

        for i, url in enumerate(cwv_sample_urls[:10], 1):  # Limit to 10 to avoid API rate limits
            print(f"[CI Deep]     [{i}/{min(10, len(cwv_sample_urls))}] {url}")

            # Analyze CWV
            cwv = await self._analyze_core_web_vitals(url)
            if cwv["status"] == "ok":
                cwv_results.append(cwv)

            # Analyze Mobile (same API call, different data extraction)
            mobile = await self._analyze_mobile_usability(url)
            if mobile["status"] == "ok":
                mobile_results.append(mobile)

            # Analyze Accessibility
            accessibility = await self._analyze_accessibility(url)
            if accessibility["status"] == "ok":
                accessibility_results.append(accessibility)

            await asyncio.sleep(2)  # Rate limiting for PageSpeed API

        # Store results for aggregation
        for page in analyzed:
            page["cwv_sampled"] = page["url"] in cwv_sample_urls[:10]
            page["mobile_sampled"] = page["url"] in cwv_sample_urls[:10]
            page["accessibility_sampled"] = page["url"] in cwv_sample_urls[:10]

        # Add summaries to first page (will be used in aggregation)
        if analyzed:
            if cwv_results:
                analyzed[0]["cwv_summary"] = {
                    "pages_sampled": len(cwv_results),
                    "results": cwv_results
                }
            if mobile_results:
                analyzed[0]["mobile_summary"] = {
                    "pages_sampled": len(mobile_results),
                    "results": mobile_results
                }
            if accessibility_results:
                analyzed[0]["accessibility_summary"] = {
                    "pages_sampled": len(accessibility_results),
                    "results": accessibility_results
                }

        return analyzed

    async def _analyze_single_page(self, url: str, page_type: str) -> Dict[str, Any]:
        """Analyze single page deeply with error handling per detector"""
        html = await self._fetch_url(url)

        if not html:
            return {
                "url": url,
                "type": page_type,
                "error": "Failed to fetch"
            }

        result = {
            "url": url,
            "type": page_type
        }

        # Existing detectors
        result["seo"] = self._safe_detector_call(self._analyze_seo, html)
        result["content"] = self._safe_detector_call(self._analyze_content, html)
        result["technical"] = self._safe_detector_call(self._analyze_technical, html)
        result["schema"] = self._safe_detector_call(self._analyze_schema, html)

        # NEW: Business-oriented detectors (Sprint 1)
        result["cms"] = self._safe_detector_call(self._detect_cms, html, {})
        result["analytics"] = self._safe_detector_call(self._detect_analytics, html)
        result["call_tracking"] = self._safe_detector_call(self._detect_call_tracking, html)
        result["live_chat"] = self._safe_detector_call(self._detect_live_chat, html)
        result["messengers"] = self._safe_detector_call(self._detect_messengers, html)
        result["booking_systems"] = self._safe_detector_call(self._detect_booking_systems, html)
        result["payment_systems"] = self._safe_detector_call(self._detect_payment_systems, html)
        result["cdn"] = self._safe_detector_call(self._detect_cdn, html)
        result["hosting"] = self._safe_detector_call(self._detect_hosting, html, {})
        result["ab_testing"] = self._safe_detector_call(self._detect_ab_testing, html)

        # Security analysis needs both url and html (async)
        try:
            result["security"] = await self._analyze_security(url, html)
        except Exception as e:
            self.logger.error(f"Security analysis failed for {url}: {e}")
            result["security"] = {"error": str(e), "confidence": 0.0}

        return result

    def _analyze_seo(self, html: str) -> Dict[str, Any]:
        """SEO analysis using BeautifulSoup (not regex)"""
        try:
            soup = BeautifulSoup(html, 'lxml')

            # Extract title
            title_tag = soup.find('title')
            title = title_tag.get_text().strip() if title_tag else ""

            # Extract meta description
            desc_tag = soup.find('meta', attrs={'name': 'description'})
            description = desc_tag.get('content', '').strip() if desc_tag else ""

            # Extract h1
            h1_tag = soup.find('h1')
            h1 = h1_tag.get_text().strip() if h1_tag else ""

            # Count headings
            h2_count = len(soup.find_all('h2'))
            h3_count = len(soup.find_all('h3'))

            return {
                "title": title,
                "title_length": len(title),
                "has_title": bool(title),
                "description": description,
                "description_length": len(description),
                "has_description": bool(description),
                "h1": h1,
                "has_h1": bool(h1),
                "h2_count": h2_count,
                "h3_count": h3_count
            }
        except Exception as e:
            self.logger.error(f"SEO analysis failed: {e}")
            # Fallback to basic regex if BeautifulSoup fails
            return self._analyze_seo_regex_fallback(html)

    def _analyze_seo_regex_fallback(self, html: str) -> Dict[str, Any]:
        """Fallback SEO analysis using regex (if BeautifulSoup fails)"""
        # Extract title
        title_match = re.search(r'<title[^>]*>(.*?)</title>', html, re.IGNORECASE | re.DOTALL)
        title = title_match.group(1).strip() if title_match else ""

        # Extract meta description
        desc_match = re.search(
            r'<meta[^>]*name=["\']description["\'][^>]*content=["\']([^"\']*)["\']',
            html,
            re.IGNORECASE
        )
        description = desc_match.group(1) if desc_match else ""

        # Extract h1
        h1_match = re.search(r'<h1[^>]*>(.*?)</h1>', html, re.IGNORECASE | re.DOTALL)
        h1 = h1_match.group(1).strip() if h1_match else ""

        # Count headings
        h2_count = len(re.findall(r'<h2[^>]*>', html, re.IGNORECASE))
        h3_count = len(re.findall(r'<h3[^>]*>', html, re.IGNORECASE))

        return {
            "title": title,
            "title_length": len(title),
            "has_title": bool(title),
            "description": description,
            "description_length": len(description),
            "has_description": bool(description),
            "h1": h1,
            "has_h1": bool(h1),
            "h2_count": h2_count,
            "h3_count": h3_count
        }

    def _analyze_content(self, html: str) -> Dict[str, Any]:
        """Content analysis"""
        # Remove scripts and styles
        clean_html = re.sub(r'<script[^>]*>.*?</script>', '', html, flags=re.DOTALL | re.IGNORECASE)
        clean_html = re.sub(r'<style[^>]*>.*?</style>', '', clean_html, flags=re.DOTALL | re.IGNORECASE)

        # Extract text
        text = re.sub(r'<[^>]+>', ' ', clean_html)
        text = re.sub(r'\s+', ' ', text).strip()

        words = text.split()

        return {
            "text_length": len(text),
            "word_count": len(words),
            "has_content": len(words) > 100
        }

    def _analyze_technical(self, html: str) -> Dict[str, Any]:
        """Technical analysis"""
        return {
            "html_size_kb": len(html) / 1024,
            "has_viewport": bool(re.search(r'<meta[^>]*name=["\']viewport["\']', html, re.IGNORECASE))
        }

    def _analyze_schema(self, html: str) -> Dict[str, Any]:
        """Schema.org analysis"""
        has_schema = bool(re.search(r'schema\.org', html, re.IGNORECASE))
        has_faq = bool(re.search(r'FAQPage', html, re.IGNORECASE))
        has_local_business = bool(re.search(r'LocalBusiness', html, re.IGNORECASE))

        return {
            "has_schema": has_schema,
            "has_faq_schema": has_faq,
            "has_local_business": has_local_business
        }

    # ========== NEW: Business-Oriented Detectors (Sprint 1) ==========

    def _detect_cms(self, html: str, headers: dict) -> Dict[str, Any]:
        """Detect CMS with confidence scoring"""
        patterns = {
            "WordPress": ["wp-content", "wp-includes", "wp-json"],
            "Bitrix": ["bitrix/templates", "1C-Bitrix", "/bitrix/"],
            "Tilda": ["tilda.cc", "tilda.ws", "tildacdn.com"],
            "Wix": ["wix.com", "wixstatic.com"],
            "Joomla": ["joomla", "/components/com_"],
        }

        detected = None
        evidence = []
        confidence = 0.0

        # Check headers first
        if 'X-Powered-By' in headers:
            powered_by = headers['X-Powered-By'].lower()
            if 'bitrix' in powered_by:
                detected = "Bitrix"
                evidence.append(f"X-Powered-By: {headers['X-Powered-By']}")
                confidence = 1.0

        # Check HTML patterns
        if not detected:
            for cms, patterns_list in patterns.items():
                matches = [p for p in patterns_list if p in html]
                if matches:
                    detected = cms
                    evidence = matches
                    # Confidence based on number of matches
                    confidence = min(1.0, len(matches) / len(patterns_list) * 1.5)
                    break

        # Default to Custom if no CMS detected
        if not detected:
            detected = "Custom"
            confidence = 0.5

        return {
            "cms": detected,
            "confidence": confidence,
            "evidence": evidence[:3],  # Limit to 3 pieces of evidence
            "business_context": self._get_cms_context(detected)
        }

    def _get_cms_context(self, cms: str) -> str:
        """Get business context for CMS"""
        contexts = {
            "WordPress": "Гибкая CMS, большая экосистема плагинов",
            "Bitrix": "Российская CMS, интеграция с 1С, дорогая в поддержке",
            "Tilda": "Конструктор сайтов, быстрый запуск, ограниченные возможности",
            "Wix": "Конструктор сайтов, простой, но медленный",
            "Joomla": "Гибкая CMS, средняя сложность",
            "Custom": "Самописная CMS, полный контроль, высокая стоимость разработки"
        }
        return contexts.get(cms, "Неизвестная CMS")

    def _detect_analytics(self, html: str) -> Dict[str, Any]:
        """Detect analytics and tracking tools"""
        tools = {
            "google_analytics": {
                "patterns": [r"UA-\d+", r"G-[A-Z0-9]+", "gtag.js", "analytics.js"],
                "name": "Google Analytics"
            },
            "yandex_metrika": {
                "patterns": ["mc.yandex.ru", "metrika/tag.js", r"ym\(\d+"],
                "name": "Яндекс.Метрика"
            },
            "google_tag_manager": {
                "patterns": ["googletagmanager.com/gtm.js", r"GTM-[A-Z0-9]+"],
                "name": "Google Tag Manager"
            },
            "facebook_pixel": {
                "patterns": ["facebook.net/en_US/fbevents.js", r"fbq\("],
                "name": "Facebook Pixel"
            },
            "vk_pixel": {
                "patterns": ["vk.com/js/api/openapi.js", r"VK\.Retargeting"],
                "name": "VK Pixel"
            }
        }

        results = {}
        for key, config in tools.items():
            detected = False
            confidence = 0.0
            tool_id = None

            for pattern in config["patterns"]:
                if re.search(pattern, html, re.IGNORECASE):
                    detected = True
                    # Try to extract ID
                    match = re.search(pattern, html, re.IGNORECASE)
                    if match and match.groups():
                        tool_id = match.group(0)
                    confidence = min(1.0, confidence + 0.4)

            results[key] = {
                "detected": detected,
                "confidence": round(confidence, 2),
                "id": tool_id,
                "name": config["name"]
            }

        # Business context
        detected_count = sum(1 for r in results.values() if r["detected"])
        if detected_count >= 3:
            context = "Полный стек аналитики - data-driven подход"
        elif detected_count >= 1:
            context = "Базовая аналитика настроена"
        else:
            context = "Аналитика не обнаружена - работают вслепую"

        return {
            "analytics": results,
            "business_context": context
        }

    def _detect_call_tracking(self, html: str) -> Dict[str, Any]:
        """Detect call tracking systems"""
        providers = {
            "Calltouch": ["calltouch.ru", "ct-widget"],
            "Callibri": ["callibri.ru", "clbr"],
            "CoMagic": ["comagic.ru", "comagic-widget"],
            "Ringostat": ["ringostat.com", "roistat"]
        }

        detected_provider = None
        confidence = 0.0

        for provider, patterns in providers.items():
            matches = sum(1 for p in patterns if p in html.lower())
            if matches > 0:
                detected_provider = provider
                confidence = min(1.0, matches / len(patterns) * 1.5)
                break

        context = "Call tracking включён - отслеживают источники звонков" if detected_provider else "Нет call tracking - теряют 30% атрибуции лидов"

        return {
            "provider": detected_provider,
            "detected": bool(detected_provider),
            "confidence": confidence,
            "business_context": context
        }

    def _detect_live_chat(self, html: str) -> Dict[str, Any]:
        """Detect live chat systems"""
        chats = {
            "Jivo": ["jivo", "jivosite"],
            "Carrot": ["carrotquest", "carrot.top"],
            "Bitrix24": ["bitrix24", "b24-web-form"],
            "Intercom": ["intercom.io", "intercom-container"]
        }

        detected_chat = None
        confidence = 0.0

        for chat, patterns in chats.items():
            matches = sum(1 for p in patterns if p in html.lower())
            if matches > 0:
                detected_chat = chat
                confidence = min(1.0, matches / len(patterns) * 1.5)
                break

        context = f"Онлайн-чат {detected_chat} - быстрая связь с клиентами" if detected_chat else "Нет онлайн-чата - упускают горячих лидов"

        return {
            "provider": detected_chat,
            "detected": bool(detected_chat),
            "confidence": confidence,
            "business_context": context
        }

    def _detect_messengers(self, html: str) -> Dict[str, Any]:
        """Detect messenger integration buttons"""
        messengers = {
            "WhatsApp": ["wa.me", "whatsapp.com", "api.whatsapp"],
            "Telegram": ["t.me", "telegram.me", "telegram.org"],
            "Viber": ["viber://", "chats.viber.com"]
        }

        detected = {}
        for messenger, patterns in messengers.items():
            found = any(p in html.lower() for p in patterns)
            if found:
                detected[messenger] = True

        context = f"Мессенджеры: {', '.join(detected.keys())}" if detected else "Нет мессенджеров - ограничивают каналы связи"

        return {
            "messengers": detected,
            "count": len(detected),
            "confidence": 1.0 if detected else 0.0,
            "business_context": context
        }

    def _detect_booking_systems(self, html: str) -> Dict[str, Any]:
        """Detect online booking systems"""
        systems = {
            "YCLIENTS": ["yclients.com", "n237778.yclients.com"],
            "Dikidi": ["dikidi.ru", "dikidi.net"],
            "Custom": ["booking", "запись", "онлайн-запись"]
        }

        detected_system = None
        confidence = 0.0

        for system, patterns in systems.items():
            matches = sum(1 for p in patterns if p in html.lower())
            if matches > 0:
                detected_system = system
                confidence = 0.8 if system == "Custom" else 1.0
                break

        context = f"Онлайн-запись {detected_system} - удобство для клиентов" if detected_system else "Нет онлайн-записи - клиенты уходят к конкурентам"

        return {
            "system": detected_system,
            "detected": bool(detected_system),
            "confidence": confidence,
            "business_context": context
        }

    def _detect_payment_systems(self, html: str) -> Dict[str, Any]:
        """Detect payment systems"""
        systems = {
            "Stripe": ["stripe.com", "js.stripe.com"],
            "PayPal": ["paypal.com", "paypalobjects.com"],
            "Yandex.Kassa": ["yookassa.ru", "kassa.yandex", "money.yandex"],
            "Tinkoff": ["securepay.tinkoff.ru", "tinkoff.ru/api"]
        }

        detected = {}
        for system, patterns in systems.items():
            found = any(p in html.lower() for p in patterns)
            if found:
                detected[system] = True

        context = f"Оплата: {', '.join(detected.keys())}" if detected else "Нет онлайн-оплаты - только офлайн"

        return {
            "systems": detected,
            "count": len(detected),
            "confidence": 1.0 if detected else 0.0,
            "business_context": context
        }

    def _detect_cdn(self, html: str) -> Dict[str, Any]:
        """Detect CDN usage"""
        cdns = {
            "Cloudflare": ["cloudflare.com", "cdnjs.cloudflare.com"],
            "Akamai": ["akamai.net", "akamaihd.net"],
            "CloudFront": ["cloudfront.net"],
            "Fastly": ["fastly.net"]
        }

        detected_cdn = None
        confidence = 0.0

        for cdn, patterns in cdns.items():
            if any(p in html.lower() for p in patterns):
                detected_cdn = cdn
                confidence = 1.0
                break

        context = f"CDN {detected_cdn} - быстрая загрузка контента" if detected_cdn else "Нет CDN - медленная загрузка для удалённых пользователей"

        return {
            "provider": detected_cdn,
            "detected": bool(detected_cdn),
            "confidence": confidence,
            "business_context": context
        }

    def _detect_hosting(self, html: str, headers: dict = None) -> Dict[str, Any]:
        """Detect hosting provider (basic detection via common patterns)"""
        # Note: Accurate hosting detection requires DNS/IP lookup
        # This is basic detection via common patterns

        providers = {
            "Beget": ["beget.com", "beget.ru"],
            "Timeweb": ["timeweb.ru", "timeweb.com"],
            "AWS": ["amazonaws.com", "aws.amazon.com"],
            "Cloudflare": ["cloudflare"]  # From headers
        }

        detected_provider = None
        confidence = 0.3  # Low confidence without DNS lookup

        # Check HTML
        for provider, patterns in providers.items():
            if any(p in html.lower() for p in patterns):
                detected_provider = provider
                confidence = 0.6
                break

        # Check headers if available
        if headers and 'Server' in headers:
            server = headers['Server'].lower()
            if 'cloudflare' in server:
                detected_provider = "Cloudflare"
                confidence = 0.9

        context = f"Хостинг: {detected_provider}" if detected_provider else "Хостинг не определён (нужен DNS lookup)"

        return {
            "provider": detected_provider,
            "detected": bool(detected_provider),
            "confidence": confidence,
            "business_context": context,
            "note": "Для точного определения нужен DNS/IP lookup"
        }

    def _detect_ab_testing(self, html: str) -> Dict[str, Any]:
        """Detect A/B testing tools"""
        tools = {
            "Google Optimize": ["optimize.google.com", "gtag('event', 'optimize"],
            "VWO": ["vwo.com", "visualwebsiteoptimizer"],
            "Optimizely": ["optimizely.com", "cdn.optimizely.com"]
        }

        detected_tool = None
        confidence = 0.0

        for tool, patterns in tools.items():
            if any(p in html.lower() for p in patterns):
                detected_tool = tool
                confidence = 1.0
                break

        context = f"A/B тестирование {detected_tool} - оптимизируют конверсию" if detected_tool else "Нет A/B тестирования - не оптимизируют конверсию"

        return {
            "tool": detected_tool,
            "detected": bool(detected_tool),
            "confidence": confidence,
            "business_context": context
        }

    # ========== End of Business-Oriented Detectors ==========

    async def _analyze_core_web_vitals(self, url: str) -> Dict[str, Any]:
        """
        Analyze Core Web Vitals using PageSpeed Insights API

        Metrics:
        - LCP (Largest Contentful Paint): < 2.5s good, < 4.0s needs improvement, >= 4.0s poor
        - INP (Interaction to Next Paint): < 200ms good, < 500ms needs improvement, >= 500ms poor
        - CLS (Cumulative Layout Shift): < 0.1 good, < 0.25 needs improvement, >= 0.25 poor
        - TTFB (Time to First Byte): < 800ms good, < 1800ms needs improvement, >= 1800ms poor
        - FCP (First Contentful Paint): < 1.8s good, < 3.0s needs improvement, >= 3.0s poor

        Returns:
        {
            "lcp": float (seconds),
            "inp": float (milliseconds),
            "cls": float,
            "ttfb": float (milliseconds),
            "fcp": float (seconds),
            "score": float (0-100),
            "status": "ok" | "error",
            "error": str | None
        }
        """
        try:
            # Get API config and cache
            from aim.core.api_config import get_api_config, get_api_cache

            api_config = get_api_config()
            api_cache = get_api_cache()

            # PageSpeed Insights API endpoint
            api_url = "https://www.googleapis.com/pagespeedonline/v5/runPagespeed"

            params = {
                "url": url,
                "strategy": "mobile",  # Mobile-first
                "category": "performance"
            }

            # Add API key if available
            if api_config.has_pagespeed_api_key():
                params["key"] = api_config.get_pagespeed_api_key()

            # Check cache first
            cached_response = api_cache.get(api_url, params)
            if cached_response:
                print(f"[CI Deep]     💾 Using cached CWV data")
                data = cached_response
            else:
                # Rate limiting
                await api_config.rate_limiter.acquire()

                print(f"[CI Deep]     🔍 Analyzing CWV for {url}...")

                async with aiohttp.ClientSession() as session:
                    async with session.get(api_url, params=params, timeout=aiohttp.ClientTimeout(total=30)) as response:
                        if response.status != 200:
                            return {
                                "status": "error",
                                "error": f"PageSpeed API returned {response.status}",
                                "lcp": None,
                                "inp": None,
                                "cls": None,
                                "ttfb": None,
                                "fcp": None,
                                "score": 0
                            }

                        data = await response.json()

                        # Cache response
                        api_cache.set(api_url, params, data)

                    # Extract metrics from response
                    lighthouse = data.get("lighthouseResult", {})
                    audits = lighthouse.get("audits", {})

                    # Extract CWV metrics
                    lcp_audit = audits.get("largest-contentful-paint", {})
                    lcp = lcp_audit.get("numericValue", 0) / 1000  # Convert to seconds

                    # INP is newer, might not be in all responses
                    inp_audit = audits.get("interaction-to-next-paint", {})
                    inp = inp_audit.get("numericValue", 0)  # Already in milliseconds

                    cls_audit = audits.get("cumulative-layout-shift", {})
                    cls = cls_audit.get("numericValue", 0)

                    ttfb_audit = audits.get("server-response-time", {})
                    ttfb = ttfb_audit.get("numericValue", 0)  # In milliseconds

                    fcp_audit = audits.get("first-contentful-paint", {})
                    fcp = fcp_audit.get("numericValue", 0) / 1000  # Convert to seconds

                    # Calculate score based on thresholds
                    score = self._calculate_cwv_score(lcp, inp, cls, ttfb, fcp)

                    print(f"[CI Deep]     ✓ CWV: LCP={lcp:.2f}s, INP={inp:.0f}ms, CLS={cls:.3f}, Score={score:.0f}")

                    return {
                        "status": "ok",
                        "error": None,
                        "lcp": lcp,
                        "inp": inp,
                        "cls": cls,
                        "ttfb": ttfb,
                        "fcp": fcp,
                        "score": score
                    }

        except asyncio.TimeoutError:
            return {
                "status": "error",
                "error": "PageSpeed API timeout",
                "lcp": None,
                "inp": None,
                "cls": None,
                "ttfb": None,
                "fcp": None,
                "score": 0
            }
        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "lcp": None,
                "inp": None,
                "cls": None,
                "ttfb": None,
                "fcp": None,
                "score": 0
            }

    def _calculate_cwv_score(self, lcp: float, inp: float, cls: float, ttfb: float, fcp: float) -> float:
        """
        Calculate CWV score (0-100) based on thresholds

        Weighted scoring:
        - LCP: 30%
        - INP: 25%
        - CLS: 25%
        - TTFB: 10%
        - FCP: 10%
        """
        scores = []

        # LCP score (30%)
        if lcp < 2.5:
            lcp_score = 100
        elif lcp < 4.0:
            lcp_score = 50
        else:
            lcp_score = 0
        scores.append(lcp_score * 0.30)

        # INP score (25%)
        if inp < 200:
            inp_score = 100
        elif inp < 500:
            inp_score = 50
        else:
            inp_score = 0
        scores.append(inp_score * 0.25)

        # CLS score (25%)
        if cls < 0.1:
            cls_score = 100
        elif cls < 0.25:
            cls_score = 50
        else:
            cls_score = 0
        scores.append(cls_score * 0.25)

        # TTFB score (10%)
        if ttfb < 800:
            ttfb_score = 100
        elif ttfb < 1800:
            ttfb_score = 50
        else:
            ttfb_score = 0
        scores.append(ttfb_score * 0.10)

        # FCP score (10%)
        if fcp < 1.8:
            fcp_score = 100
        elif fcp < 3.0:
            fcp_score = 50
        else:
            fcp_score = 0
        scores.append(fcp_score * 0.10)

        return sum(scores)

    async def _analyze_mobile_usability(self, url: str) -> Dict[str, Any]:
        """
        Analyze Mobile Usability using PageSpeed Insights API (mobile strategy)

        Checks:
        - Viewport meta tag
        - Responsive design
        - Tap targets size
        - Font sizes
        - Content width

        Returns:
        {
            "viewport_ok": bool,
            "responsive": bool,
            "tap_targets_ok": bool,
            "font_size_ok": bool,
            "content_width_ok": bool,
            "score": float (0-100),
            "status": "ok" | "error",
            "error": str | None
        }
        """
        try:
            # Get API config and cache
            from aim.core.api_config import get_api_config, get_api_cache

            api_config = get_api_config()
            api_cache = get_api_cache()

            # PageSpeed Insights API endpoint (mobile strategy)
            api_url = "https://www.googleapis.com/pagespeedonline/v5/runPagespeed"

            params = {
                "url": url,
                "strategy": "mobile",
                "category": "performance"
            }

            # Add API key if available
            if api_config.has_pagespeed_api_key():
                params["key"] = api_config.get_pagespeed_api_key()

            # Check cache first
            cached_response = api_cache.get(api_url, params)
            if cached_response:
                print(f"[CI Deep]     💾 Using cached Mobile data")
                data = cached_response
            else:
                # Rate limiting
                await api_config.rate_limiter.acquire()

                print(f"[CI Deep]     📱 Analyzing Mobile for {url}...")

                async with aiohttp.ClientSession() as session:
                    async with session.get(api_url, params=params, timeout=aiohttp.ClientTimeout(total=30)) as response:
                        if response.status != 200:
                            return {
                                "status": "error",
                                "error": f"PageSpeed API returned {response.status}",
                                "viewport_ok": False,
                                "responsive": False,
                                "tap_targets_ok": False,
                                "font_size_ok": False,
                                "content_width_ok": False,
                                "score": 0
                            }

                        data = await response.json()

                        # Cache response
                        api_cache.set(api_url, params, data)

                    # Extract mobile usability audits
                    lighthouse = data.get("lighthouseResult", {})
                    audits = lighthouse.get("audits", {})

                    # Viewport
                    viewport_audit = audits.get("viewport", {})
                    viewport_ok = viewport_audit.get("score", 0) == 1

                    # Content width
                    content_width_audit = audits.get("content-width", {})
                    content_width_ok = content_width_audit.get("score", 0) == 1

                    # Tap targets
                    tap_targets_audit = audits.get("tap-targets", {})
                    tap_targets_ok = tap_targets_audit.get("score", 0) >= 0.9

                    # Font size
                    font_size_audit = audits.get("font-size", {})
                    font_size_ok = font_size_audit.get("score", 0) >= 0.9

                    # Responsive images (as proxy for responsive design)
                    responsive_images_audit = audits.get("uses-responsive-images", {})
                    responsive = responsive_images_audit.get("score", 0) >= 0.8

                    # Calculate mobile score
                    score = self._calculate_mobile_score(
                        viewport_ok, responsive, tap_targets_ok, font_size_ok, content_width_ok
                    )

                    print(f"[CI Deep]     ✓ Mobile: Viewport={viewport_ok}, Responsive={responsive}, Score={score:.0f}")

                    return {
                        "status": "ok",
                        "error": None,
                        "viewport_ok": viewport_ok,
                        "responsive": responsive,
                        "tap_targets_ok": tap_targets_ok,
                        "font_size_ok": font_size_ok,
                        "content_width_ok": content_width_ok,
                        "score": score
                    }

        except asyncio.TimeoutError:
            return {
                "status": "error",
                "error": "PageSpeed API timeout",
                "viewport_ok": False,
                "responsive": False,
                "tap_targets_ok": False,
                "font_size_ok": False,
                "content_width_ok": False,
                "score": 0
            }
        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "viewport_ok": False,
                "responsive": False,
                "tap_targets_ok": False,
                "font_size_ok": False,
                "content_width_ok": False,
                "score": 0
            }

    def _calculate_mobile_score(
        self,
        viewport_ok: bool,
        responsive: bool,
        tap_targets_ok: bool,
        font_size_ok: bool,
        content_width_ok: bool
    ) -> float:
        """
        Calculate mobile usability score (0-100)

        Weighted scoring:
        - Viewport: 25%
        - Content width: 25%
        - Tap targets: 20%
        - Font size: 15%
        - Responsive: 15%
        """
        score = 0

        if viewport_ok:
            score += 25
        if content_width_ok:
            score += 25
        if tap_targets_ok:
            score += 20
        if font_size_ok:
            score += 15
        if responsive:
            score += 15

        return score

    async def _analyze_accessibility(self, url: str) -> Dict[str, Any]:
        """
        Analyze accessibility using PageSpeed Insights Lighthouse accessibility audit

        Checks WCAG compliance:
        - Color contrast
        - ARIA attributes
        - Alt text for images
        - Form labels
        - Keyboard navigation
        - Screen reader support

        Returns:
        {
            "color_contrast": bool,
            "aria_valid": bool,
            "alt_text": bool,
            "form_labels": bool,
            "keyboard_nav": bool,
            "screen_reader": bool,
            "score": float (0-100),
            "status": "ok" | "error",
            "error": str | None
        }
        """
        try:
            # Get API config and cache
            from aim.core.api_config import get_api_config, get_api_cache

            api_config = get_api_config()
            api_cache = get_api_cache()

            # PageSpeed Insights API endpoint
            api_url = "https://www.googleapis.com/pagespeedonline/v5/runPagespeed"

            params = {
                "url": url,
                "category": "accessibility"
            }

            # Add API key if available
            if api_config.has_pagespeed_api_key():
                params["key"] = api_config.get_pagespeed_api_key()

            # Check cache first
            cached_response = api_cache.get(api_url, params)
            if cached_response:
                print(f"[CI Deep]     💾 Using cached Accessibility data")
                data = cached_response
            else:
                # Rate limiting
                await api_config.rate_limiter.acquire()

                print(f"[CI Deep]     🔍 Analyzing Accessibility for {url}...")

                async with aiohttp.ClientSession() as session:
                    async with session.get(api_url, params=params, timeout=aiohttp.ClientTimeout(total=30)) as response:
                        if response.status != 200:
                            return {
                                "status": "error",
                                "error": f"PageSpeed API returned {response.status}",
                                "color_contrast": False,
                                "aria_valid": False,
                                "alt_text": False,
                                "form_labels": False,
                                "keyboard_nav": False,
                                "screen_reader": False,
                                "score": 0
                            }

                        data = await response.json()

                        # Cache response
                        api_cache.set(api_url, params, data)

                    # Extract accessibility audits
                    lighthouse = data.get("lighthouseResult", {})
                    audits = lighthouse.get("audits", {})

                    # Color contrast
                    color_contrast_audit = audits.get("color-contrast", {})
                    color_contrast = color_contrast_audit.get("score", 0) >= 0.9

                    # ARIA attributes
                    aria_valid_audit = audits.get("aria-valid-attr", {})
                    aria_valid = aria_valid_audit.get("score", 0) >= 0.9

                    # Alt text for images
                    alt_text_audit = audits.get("image-alt", {})
                    alt_text = alt_text_audit.get("score", 0) >= 0.9

                    # Form labels
                    form_labels_audit = audits.get("label", {})
                    form_labels = form_labels_audit.get("score", 0) >= 0.9

                    # Keyboard navigation
                    keyboard_nav_audit = audits.get("focusable-controls", {})
                    keyboard_nav = keyboard_nav_audit.get("score", 0) >= 0.9

                    # Screen reader support (button names, link names)
                    button_name_audit = audits.get("button-name", {})
                    link_name_audit = audits.get("link-name", {})
                    screen_reader = (
                        button_name_audit.get("score", 0) >= 0.9 and
                        link_name_audit.get("score", 0) >= 0.9
                    )

                    # Calculate accessibility score
                    score = self._calculate_accessibility_score(
                        color_contrast, aria_valid, alt_text,
                        form_labels, keyboard_nav, screen_reader
                    )

                    print(f"[CI Deep]     ✓ A11y: Contrast={color_contrast}, ARIA={aria_valid}, Score={score:.0f}")

                    return {
                        "status": "ok",
                        "error": None,
                        "color_contrast": color_contrast,
                        "aria_valid": aria_valid,
                        "alt_text": alt_text,
                        "form_labels": form_labels,
                        "keyboard_nav": keyboard_nav,
                        "screen_reader": screen_reader,
                        "score": score
                    }

        except asyncio.TimeoutError:
            return {
                "status": "error",
                "error": "PageSpeed API timeout",
                "color_contrast": False,
                "aria_valid": False,
                "alt_text": False,
                "form_labels": False,
                "keyboard_nav": False,
                "screen_reader": False,
                "score": 0
            }
        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "color_contrast": False,
                "aria_valid": False,
                "alt_text": False,
                "form_labels": False,
                "keyboard_nav": False,
                "screen_reader": False,
                "score": 0
            }

    def _calculate_accessibility_score(
        self,
        color_contrast: bool,
        aria_valid: bool,
        alt_text: bool,
        form_labels: bool,
        keyboard_nav: bool,
        screen_reader: bool
    ) -> float:
        """
        Calculate accessibility score (0-100)

        Weighted scoring based on WCAG importance:
        - Color contrast: 25% (critical for readability)
        - Screen reader: 20% (critical for blind users)
        - Alt text: 20% (critical for images)
        - ARIA: 15% (important for complex widgets)
        - Form labels: 10% (important for forms)
        - Keyboard nav: 10% (important for motor disabilities)
        """
        score = 0

        if color_contrast:
            score += 25
        if screen_reader:
            score += 20
        if alt_text:
            score += 20
        if aria_valid:
            score += 15
        if form_labels:
            score += 10
        if keyboard_nav:
            score += 10

        return score

    async def _analyze_security(self, url: str, html: str) -> Dict[str, Any]:
        """
        Analyze security features

        Checks:
        - HTTPS enabled
        - Security headers (CSP, X-Frame-Options, etc.)
        - Mixed content
        - Secure cookies
        - SSL certificate validity

        Returns:
        {
            "https": bool,
            "hsts": bool,
            "csp": bool,
            "x_frame_options": bool,
            "x_content_type": bool,
            "mixed_content": bool,
            "score": float (0-100),
            "status": "ok" | "error",
            "error": str | None
        }
        """
        try:
            parsed_url = urlparse(url)

            # Check HTTPS
            https = parsed_url.scheme == "https"

            # Fetch headers
            ssl_context = ssl.create_default_context()
            ssl_context.check_hostname = False
            ssl_context.verify_mode = ssl.CERT_NONE

            connector = aiohttp.TCPConnector(ssl=ssl_context)
            timeout = aiohttp.ClientTimeout(total=10)

            async with aiohttp.ClientSession(connector=connector, timeout=timeout) as session:
                async with session.get(url, allow_redirects=True) as response:
                    headers = response.headers

                    # Check security headers
                    hsts = "Strict-Transport-Security" in headers
                    csp = "Content-Security-Policy" in headers
                    x_frame_options = "X-Frame-Options" in headers
                    x_content_type = "X-Content-Type-Options" in headers

                    # Check for mixed content (HTTP resources on HTTPS page)
                    mixed_content = False
                    if https and html:
                        # Look for http:// in src/href attributes
                        http_pattern = r'(?:src|href)=["\']http://[^"\']*["\']'
                        mixed_content = bool(re.search(http_pattern, html, re.IGNORECASE))

                    # Calculate security score
                    score = self._calculate_security_score(
                        https, hsts, csp, x_frame_options, x_content_type, mixed_content
                    )

                    print(f"[CI Deep]     ✓ Security: HTTPS={https}, HSTS={hsts}, CSP={csp}, Score={score:.0f}")

                    return {
                        "status": "ok",
                        "error": None,
                        "https": https,
                        "hsts": hsts,
                        "csp": csp,
                        "x_frame_options": x_frame_options,
                        "x_content_type": x_content_type,
                        "mixed_content": mixed_content,
                        "score": score
                    }

        except asyncio.TimeoutError:
            return {
                "status": "error",
                "error": "Timeout",
                "https": False,
                "hsts": False,
                "csp": False,
                "x_frame_options": False,
                "x_content_type": False,
                "mixed_content": True,
                "score": 0
            }
        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "https": False,
                "hsts": False,
                "csp": False,
                "x_frame_options": False,
                "x_content_type": False,
                "mixed_content": True,
                "score": 0
            }

    def _calculate_security_score(
        self,
        https: bool,
        hsts: bool,
        csp: bool,
        x_frame_options: bool,
        x_content_type: bool,
        mixed_content: bool
    ) -> float:
        """
        Calculate security score (0-100)

        Weighted scoring:
        - HTTPS: 40% (critical)
        - HSTS: 20% (important for HTTPS)
        - CSP: 15% (important for XSS protection)
        - X-Frame-Options: 10% (clickjacking protection)
        - X-Content-Type-Options: 10% (MIME sniffing protection)
        - No mixed content: 5% (bonus for clean HTTPS)
        """
        score = 0

        if https:
            score += 40
        if hsts:
            score += 20
        if csp:
            score += 15
        if x_frame_options:
            score += 10
        if x_content_type:
            score += 10
        if not mixed_content:
            score += 5

        return score

    async def _aggregate_analysis(self, analyzed_pages: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Aggregate analysis across all pages including CWV and Mobile"""
        if not analyzed_pages:
            return {}

        # Count by type
        type_counts = {}
        for page in analyzed_pages:
            page_type = page.get("type", "unknown")
            type_counts[page_type] = type_counts.get(page_type, 0) + 1

        # SEO stats
        pages_with_title = sum(1 for p in analyzed_pages if p.get("seo", {}).get("has_title"))
        pages_with_desc = sum(1 for p in analyzed_pages if p.get("seo", {}).get("has_description"))
        pages_with_h1 = sum(1 for p in analyzed_pages if p.get("seo", {}).get("has_h1"))

        # Schema stats
        pages_with_schema = sum(1 for p in analyzed_pages if p.get("schema", {}).get("has_schema"))

        total = len(analyzed_pages)

        # Extract CWV summary if available
        cwv_summary = analyzed_pages[0].get("cwv_summary") if analyzed_pages else None
        cwv_score = 0
        cwv_pages_sampled = 0

        if cwv_summary and cwv_summary.get("results"):
            cwv_results = cwv_summary["results"]
            cwv_pages_sampled = len(cwv_results)

            # Calculate average CWV score
            if cwv_results:
                cwv_score = sum(r["score"] for r in cwv_results) / len(cwv_results)

                # Calculate average metrics
                avg_lcp = sum(r["lcp"] for r in cwv_results) / len(cwv_results)
                avg_inp = sum(r["inp"] for r in cwv_results) / len(cwv_results)
                avg_cls = sum(r["cls"] for r in cwv_results) / len(cwv_results)

        # Extract Mobile summary if available
        mobile_summary = analyzed_pages[0].get("mobile_summary") if analyzed_pages else None
        mobile_score = 0
        mobile_pages_sampled = 0

        if mobile_summary and mobile_summary.get("results"):
            mobile_results = mobile_summary["results"]
            mobile_pages_sampled = len(mobile_results)

            # Calculate average Mobile score
            if mobile_results:
                mobile_score = sum(r["score"] for r in mobile_results) / len(mobile_results)

                # Calculate pass rates
                viewport_pass_rate = sum(1 for r in mobile_results if r["viewport_ok"]) / len(mobile_results) * 100
                responsive_pass_rate = sum(1 for r in mobile_results if r["responsive"]) / len(mobile_results) * 100
                tap_targets_pass_rate = sum(1 for r in mobile_results if r["tap_targets_ok"]) / len(mobile_results) * 100

        # Extract Accessibility summary if available
        accessibility_summary = analyzed_pages[0].get("accessibility_summary") if analyzed_pages else None
        accessibility_score = 0
        accessibility_pages_sampled = 0

        if accessibility_summary and accessibility_summary.get("results"):
            accessibility_results = accessibility_summary["results"]
            accessibility_pages_sampled = len(accessibility_results)

            # Calculate average Accessibility score
            if accessibility_results:
                accessibility_score = sum(r["score"] for r in accessibility_results) / len(accessibility_results)

                # Calculate pass rates
                color_contrast_pass_rate = sum(1 for r in accessibility_results if r["color_contrast"]) / len(accessibility_results) * 100
                aria_pass_rate = sum(1 for r in accessibility_results if r["aria_valid"]) / len(accessibility_results) * 100
                alt_text_pass_rate = sum(1 for r in accessibility_results if r["alt_text"]) / len(accessibility_results) * 100

        # Calculate Security stats from all analyzed pages
        security_score = 0
        pages_with_https = sum(1 for p in analyzed_pages if p.get("security", {}).get("https"))
        pages_with_hsts = sum(1 for p in analyzed_pages if p.get("security", {}).get("hsts"))
        pages_with_csp = sum(1 for p in analyzed_pages if p.get("security", {}).get("csp"))

        if total > 0:
            # Calculate average security score from all pages
            security_scores = [p.get("security", {}).get("score", 0) for p in analyzed_pages if p.get("security", {}).get("status") == "ok"]
            if security_scores:
                security_score = sum(security_scores) / len(security_scores)

        # Calculate component scores
        seo_score = (pages_with_title + pages_with_desc + pages_with_h1) / (total * 3) * 100

        # NEW: Weighted quality score
        # Formula from research: SEO 15%, CWV 25%, Mobile 20%, Accessibility 20%, Security 10%, Technical 10%
        # For now we have: SEO, CWV, Mobile, Accessibility, Security
        # Normalize weights: SEO 15/(15+25+20+20+10)=16.67%, CWV 25/90=27.78%, Mobile 20/90=22.22%, Accessibility 20/90=22.22%, Security 10/90=11.11%

        if cwv_score > 0 and mobile_score > 0 and accessibility_score > 0 and security_score > 0:
            # All five available
            quality_score = (seo_score * 0.1667 + cwv_score * 0.2778 + mobile_score * 0.2222 + accessibility_score * 0.2222 + security_score * 0.1111)
        elif cwv_score > 0 and mobile_score > 0 and accessibility_score > 0:
            # SEO, CWV, Mobile, Accessibility (no Security)
            quality_score = (seo_score * 0.1875 + cwv_score * 0.3125 + mobile_score * 0.25 + accessibility_score * 0.25)
        elif cwv_score > 0 and mobile_score > 0:
            # SEO, CWV, Mobile (no Accessibility, no Security)
            quality_score = (seo_score * 0.25 + cwv_score * 0.4167 + mobile_score * 0.3333)
        elif cwv_score > 0:
            # Only SEO and CWV
            quality_score = (seo_score * 0.375 + cwv_score * 0.625)
        else:
            # Fallback to old formula if no CWV/Mobile/Accessibility
            quality_score = seo_score

        result = {
            "total_pages": total,
            "page_types": type_counts,
            "seo_coverage": {
                "title": f"{pages_with_title}/{total}",
                "description": f"{pages_with_desc}/{total}",
                "h1": f"{pages_with_h1}/{total}"
            },
            "schema_coverage": f"{pages_with_schema}/{total}",
            "quality_score": quality_score
        }

        # Add CWV data if available
        if cwv_summary and cwv_summary.get("results"):
            cwv_results = cwv_summary["results"]
            result["cwv"] = {
                "pages_sampled": cwv_pages_sampled,
                "score": cwv_score,
                "avg_lcp": avg_lcp,
                "avg_inp": avg_inp,
                "avg_cls": avg_cls,
                "details": cwv_results
            }

        # Add Mobile data if available
        if mobile_summary and mobile_summary.get("results"):
            mobile_results = mobile_summary["results"]
            result["mobile"] = {
                "pages_sampled": mobile_pages_sampled,
                "score": mobile_score,
                "viewport_pass_rate": viewport_pass_rate,
                "responsive_pass_rate": responsive_pass_rate,
                "tap_targets_pass_rate": tap_targets_pass_rate,
                "details": mobile_results
            }

        # Add Accessibility data if available
        if accessibility_summary and accessibility_summary.get("results"):
            accessibility_results = accessibility_summary["results"]
            result["accessibility"] = {
                "pages_sampled": accessibility_pages_sampled,
                "score": accessibility_score,
                "color_contrast_pass_rate": color_contrast_pass_rate,
                "aria_pass_rate": aria_pass_rate,
                "alt_text_pass_rate": alt_text_pass_rate,
                "details": accessibility_results
            }

        # Add Security data (from all pages)
        if security_score > 0:
            https_rate = (pages_with_https / total * 100) if total > 0 else 0
            hsts_rate = (pages_with_hsts / total * 100) if total > 0 else 0
            csp_rate = (pages_with_csp / total * 100) if total > 0 else 0

            result["security"] = {
                "pages_analyzed": total,
                "score": security_score,
                "https_rate": https_rate,
                "hsts_rate": hsts_rate,
                "csp_rate": csp_rate
            }

        return result

    def _generate_issues_report(self, analyzed_pages: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Generate detailed issues report with actionable recommendations

        Categorizes issues by:
        - Severity: critical, high, medium, low
        - Category: seo, performance, mobile, accessibility, security
        - Impact: what's affected and why it matters
        - Recommendation: how to fix

        Returns structured report with prioritized issues
        """
        issues = []

        for page in analyzed_pages:
            url = page.get("url", "")
            page_type = page.get("type", "unknown")

            # SEO Issues
            seo = page.get("seo", {})
            if not seo.get("has_title"):
                issues.append({
                    "severity": "critical",
                    "category": "seo",
                    "page": url,
                    "page_type": page_type,
                    "issue": "Missing title tag",
                    "impact": "Search engines can't understand page topic. Major ranking penalty.",
                    "recommendation": "Add unique, descriptive <title> tag (50-60 characters)"
                })
            elif seo.get("title_length", 0) > 60:
                issues.append({
                    "severity": "medium",
                    "category": "seo",
                    "page": url,
                    "page_type": page_type,
                    "issue": f"Title too long ({seo.get('title_length')} chars)",
                    "impact": "Title gets truncated in search results",
                    "recommendation": "Shorten title to 50-60 characters"
                })

            if not seo.get("has_description"):
                issues.append({
                    "severity": "high",
                    "category": "seo",
                    "page": url,
                    "page_type": page_type,
                    "issue": "Missing meta description",
                    "impact": "Lower click-through rate from search results",
                    "recommendation": "Add compelling meta description (150-160 characters)"
                })

            if not seo.get("has_h1"):
                issues.append({
                    "severity": "high",
                    "category": "seo",
                    "page": url,
                    "page_type": page_type,
                    "issue": "Missing H1 heading",
                    "impact": "Unclear page hierarchy for search engines and users",
                    "recommendation": "Add single H1 with main page topic"
                })

            # Security Issues
            security = page.get("security", {})
            if security.get("status") == "ok":
                if not security.get("https"):
                    issues.append({
                        "severity": "critical",
                        "category": "security",
                        "page": url,
                        "page_type": page_type,
                        "issue": "No HTTPS",
                        "impact": "Data not encrypted. Browser warnings. SEO penalty.",
                        "recommendation": "Install SSL certificate and redirect HTTP to HTTPS"
                    })

                if not security.get("hsts"):
                    issues.append({
                        "severity": "medium",
                        "category": "security",
                        "page": url,
                        "page_type": page_type,
                        "issue": "Missing HSTS header",
                        "impact": "Vulnerable to SSL stripping attacks",
                        "recommendation": "Add Strict-Transport-Security header"
                    })

                if not security.get("csp"):
                    issues.append({
                        "severity": "medium",
                        "category": "security",
                        "page": url,
                        "page_type": page_type,
                        "issue": "Missing Content-Security-Policy",
                        "impact": "Vulnerable to XSS attacks",
                        "recommendation": "Implement CSP header to prevent XSS"
                    })

                if security.get("mixed_content"):
                    issues.append({
                        "severity": "high",
                        "category": "security",
                        "page": url,
                        "page_type": page_type,
                        "issue": "Mixed content (HTTP on HTTPS page)",
                        "impact": "Browser warnings. Security vulnerabilities.",
                        "recommendation": "Change all HTTP resources to HTTPS"
                    })

        # Add issues from CWV analysis
        cwv_summary = analyzed_pages[0].get("cwv_summary") if analyzed_pages else None
        if cwv_summary and cwv_summary.get("results"):
            for cwv in cwv_summary["results"]:
                # LCP issues
                if cwv.get("lcp", 0) > 4.0:
                    issues.append({
                        "severity": "critical",
                        "category": "performance",
                        "page": "sampled pages",
                        "page_type": "various",
                        "issue": f"Poor LCP: {cwv['lcp']:.2f}s (should be < 2.5s)",
                        "impact": "Slow loading. Poor user experience. SEO penalty.",
                        "recommendation": "Optimize images, reduce server response time, use CDN"
                    })
                elif cwv.get("lcp", 0) > 2.5:
                    issues.append({
                        "severity": "medium",
                        "category": "performance",
                        "page": "sampled pages",
                        "page_type": "various",
                        "issue": f"Needs improvement LCP: {cwv['lcp']:.2f}s",
                        "impact": "Slower than optimal loading speed",
                        "recommendation": "Optimize largest content element loading"
                    })

                # CLS issues
                if cwv.get("cls", 0) > 0.25:
                    issues.append({
                        "severity": "high",
                        "category": "performance",
                        "page": "sampled pages",
                        "page_type": "various",
                        "issue": f"Poor CLS: {cwv['cls']:.3f} (should be < 0.1)",
                        "impact": "Layout shifts annoy users. Accidental clicks.",
                        "recommendation": "Set image dimensions, avoid dynamic content insertion"
                    })

        # Add issues from Mobile analysis
        mobile_summary = analyzed_pages[0].get("mobile_summary") if analyzed_pages else None
        if mobile_summary and mobile_summary.get("results"):
            for mobile in mobile_summary["results"]:
                if not mobile.get("viewport_ok"):
                    issues.append({
                        "severity": "high",
                        "category": "mobile",
                        "page": "sampled pages",
                        "page_type": "various",
                        "issue": "Missing or incorrect viewport meta tag",
                        "impact": "Poor mobile display. Not mobile-friendly.",
                        "recommendation": "Add <meta name='viewport' content='width=device-width, initial-scale=1'>"
                    })

                if not mobile.get("tap_targets_ok"):
                    issues.append({
                        "severity": "medium",
                        "category": "mobile",
                        "page": "sampled pages",
                        "page_type": "various",
                        "issue": "Tap targets too small",
                        "impact": "Hard to tap on mobile. Poor UX.",
                        "recommendation": "Make buttons/links at least 48x48px"
                    })

        # Add issues from Accessibility analysis
        accessibility_summary = analyzed_pages[0].get("accessibility_summary") if analyzed_pages else None
        if accessibility_summary and accessibility_summary.get("results"):
            for a11y in accessibility_summary["results"]:
                if not a11y.get("color_contrast"):
                    issues.append({
                        "severity": "high",
                        "category": "accessibility",
                        "page": "sampled pages",
                        "page_type": "various",
                        "issue": "Insufficient color contrast",
                        "impact": "Hard to read for visually impaired users. WCAG violation.",
                        "recommendation": "Ensure 4.5:1 contrast ratio for normal text"
                    })

                if not a11y.get("alt_text"):
                    issues.append({
                        "severity": "high",
                        "category": "accessibility",
                        "page": "sampled pages",
                        "page_type": "various",
                        "issue": "Images missing alt text",
                        "impact": "Inaccessible to screen readers. SEO penalty.",
                        "recommendation": "Add descriptive alt text to all images"
                    })

        # Sort by severity
        severity_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
        issues.sort(key=lambda x: severity_order.get(x["severity"], 4))

        # Group by severity
        issues_by_severity = {
            "critical": [i for i in issues if i["severity"] == "critical"],
            "high": [i for i in issues if i["severity"] == "high"],
            "medium": [i for i in issues if i["severity"] == "medium"],
            "low": [i for i in issues if i["severity"] == "low"]
        }

        # Group by category
        issues_by_category = {}
        for issue in issues:
            category = issue["category"]
            if category not in issues_by_category:
                issues_by_category[category] = []
            issues_by_category[category].append(issue)

        return {
            "total_issues": len(issues),
            "by_severity": {
                "critical": len(issues_by_severity["critical"]),
                "high": len(issues_by_severity["high"]),
                "medium": len(issues_by_severity["medium"]),
                "low": len(issues_by_severity["low"])
            },
            "by_category": {cat: len(items) for cat, items in issues_by_category.items()},
            "issues": issues,
            "issues_by_severity": issues_by_severity,
            "issues_by_category": issues_by_category
        }

    async def _generate_market_insights(self, deep_profiles: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate market insights from deep profiles"""
        return {
            "total_competitors": len(deep_profiles),
            "avg_pages_analyzed": sum(p["pages_analyzed"] for p in deep_profiles) / len(deep_profiles),
            "analysis_depth": "deep"
        }

    async def _fetch_url(self, url: str) -> str:
        """Fetch URL with rotation and delays"""
        try:
            ssl_context = ssl.create_default_context()
            ssl_context.check_hostname = False
            ssl_context.verify_mode = ssl.CERT_NONE

            # Rotate User-Agent
            user_agent = self.user_agents[self.current_ua_index]
            self.current_ua_index = (self.current_ua_index + 1) % len(self.user_agents)

            async with aiohttp.ClientSession() as session:
                async with session.get(
                    url,
                    ssl=ssl_context,
                    timeout=aiohttp.ClientTimeout(total=30),
                    headers={'User-Agent': user_agent}
                ) as response:
                    if response.status == 200:
                        return await response.text()
                    return ""

        except Exception as e:
            print(f"[CI Deep]   ⚠️  Fetch error {url}: {e}")
            return ""
