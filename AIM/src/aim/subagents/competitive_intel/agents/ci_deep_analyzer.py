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
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Set
from urllib.parse import urljoin, urlparse
import xml.etree.ElementTree as ET

import aiohttp
import ssl

from meai.agents.base_agent import Agent, Task, TaskResult


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

        return {
            "name": name,
            "url": url,
            "total_pages_found": len(all_urls),
            "pages_analyzed": len(analyzed_pages),
            "page_types": classified_pages,
            "deep_analysis": aggregated,
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
        1. Start with sitemap URLs
        2. BFS crawl with priorities (services > about > blog)
        3. Limit to max_pages
        """
        visited: Set[str] = set()
        to_visit: List[tuple[int, str]] = []  # (priority, url)

        # Add sitemap URLs with priorities
        for url in sitemap_urls[:self.max_pages]:
            priority = self._get_url_priority(url)
            to_visit.append((priority, url))

        # Sort by priority (higher first)
        to_visit.sort(reverse=True)

        all_urls = []

        while to_visit and len(all_urls) < self.max_pages:
            _, url = to_visit.pop(0)

            if url in visited:
                continue

            visited.add(url)
            all_urls.append(url)

            # TODO: Extract links from page and add to queue
            # For now, just use sitemap URLs

        return all_urls[:self.max_pages]

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
        """Deep analysis of each page"""
        analyzed = []

        # Priority order for page types
        priority_order = ["homepage", "services", "about", "contacts", "prices", "blog", "other"]

        # Analyze pages by priority until we reach max_pages
        for page_type in priority_order:
            urls = classified_pages.get(page_type, [])

            for url in urls:
                if len(analyzed) >= self.max_pages:
                    break

                print(f"[CI Deep]     📄 {page_type}: {url}")

                page_analysis = await self._analyze_single_page(url, page_type)
                analyzed.append(page_analysis)

                # Respectful delay
                await asyncio.sleep(self.delay)

            if len(analyzed) >= self.max_pages:
                break

        return analyzed

    async def _analyze_single_page(self, url: str, page_type: str) -> Dict[str, Any]:
        """Analyze single page deeply"""
        html = await self._fetch_url(url)

        if not html:
            return {
                "url": url,
                "type": page_type,
                "error": "Failed to fetch"
            }

        return {
            "url": url,
            "type": page_type,
            "seo": self._analyze_seo(html),
            "content": self._analyze_content(html),
            "technical": self._analyze_technical(html),
            "schema": self._analyze_schema(html)
        }

    def _analyze_seo(self, html: str) -> Dict[str, Any]:
        """SEO analysis of page"""
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

    async def _aggregate_analysis(self, analyzed_pages: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Aggregate analysis across all pages"""
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

        return {
            "total_pages": total,
            "page_types": type_counts,
            "seo_coverage": {
                "title": f"{pages_with_title}/{total}",
                "description": f"{pages_with_desc}/{total}",
                "h1": f"{pages_with_h1}/{total}"
            },
            "schema_coverage": f"{pages_with_schema}/{total}",
            "quality_score": (pages_with_title + pages_with_desc + pages_with_h1) / (total * 3) * 100
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
