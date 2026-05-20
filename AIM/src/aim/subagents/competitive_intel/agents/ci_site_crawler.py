"""
CI Site Crawler Agent - Deep Website Crawling & Structure Analysis

Глубокий краулинг сайтов конкурентов:
- Структура сайта (страницы, разделы, глубина)
- Внутренняя перелинковка
- Контент на страницах
- Метаданные (title, description, h1-h6)
- Изображения и медиа
"""

from typing import Any, Dict, List, Set
from datetime import datetime
from urllib.parse import urljoin, urlparse
import asyncio
import json
import re

import httpx
from bs4 import BeautifulSoup

from meai.agents.base_agent import Agent, Task, TaskResult
from meai.memory.obsidian import ObsidianVault


class CISiteCrawlerAgent(Agent):
    """CI Site Crawler - агент глубокого краулинга сайтов конкурентов."""

    def __init__(
        self,
        agent_id: str,
        database_url: str = "sqlite+aiosqlite:///./data/meai.db",
        vault_path: str = "./obsidian"
    ):
        super().__init__(
            agent_id=agent_id,
            agent_type="ci-site-crawler",
            database_url=database_url,
            vault_path=vault_path
        )
        self.vault = ObsidianVault("AIM/obsidian/ci-site-crawler")

        # Page types
        self.page_types = {
            "homepage": "Главная",
            "services": "Услуги",
            "about": "О компании",
            "contacts": "Контакты",
            "blog": "Блог",
            "portfolio": "Портфолио/Кейсы",
            "prices": "Цены",
            "reviews": "Отзывы",
            "faq": "FAQ",
            "booking": "Онлайн-запись"
        }

    async def execute_task(self, task: Task) -> TaskResult:
        """
        Выполнить глубокий краулинг сайтов конкурентов.

        Args:
            task: Задача с payload:
                - competitors: список конкурентов (обязательно)
                - max_depth: максимальная глубина краулинга (опционально, default=3)

        Returns:
            TaskResult с результатами краулинга
        """
        try:
            competitors = task.payload["competitors"]
            max_depth = task.payload.get("max_depth", 3)

            print(f"[CI Site Crawler] Начало краулинга {len(competitors)} сайтов (depth={max_depth})")

            # Шаг 1: Crawl each competitor site
            crawl_results = []
            for competitor in competitors:
                result = await self._crawl_competitor_site(competitor, max_depth)
                crawl_results.append(result)

            # Шаг 2: Analyze site structures
            structure_analysis = await self._analyze_site_structures(crawl_results)

            # Шаг 3: Identify best practices
            best_practices = await self._identify_best_practices(crawl_results)

            # Шаг 4: Site insights
            insights = await self._generate_site_insights(
                crawl_results, structure_analysis, best_practices
            )

            # Шаг 5: Save results
            results = {
                "analysis_date": datetime.now().isoformat(),
                "total_crawled": len(competitors),
                "max_depth": max_depth,
                "crawl_results": crawl_results,
                "structure_analysis": structure_analysis,
                "best_practices": best_practices,
                "insights": insights
            }

            await self._save_results(results)

            print(f"[CI Site Crawler] Краулинг завершён для {len(competitors)} сайтов")

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
            print(f"[CI Site Crawler] Ошибка: {e}")
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

    async def _crawl_competitor_site(
        self,
        competitor: Dict[str, Any],
        max_depth: int
    ) -> Dict[str, Any]:
        """
        Краулинг одного сайта конкурента через реальный BFS crawl.

        Ограничения: до 30 страниц, задержка 1.5s между запросами.

        Args:
            competitor: данные конкурента
            max_depth: максимальная глубина

        Returns:
            Результаты краулинга
        """
        name = competitor["name"]
        website = competitor.get("website", "")

        print(f"[CI Site Crawler] Краулинг: {name} ({website})")

        if not website:
            return self._empty_crawl_result(name, website, "No website URL provided")

        try:
            result = await self._real_bfs_crawl(name, website, max_depth)
        except Exception as e:
            print(f"[CI Site Crawler] Crawl error for {name}: {e}")
            result = self._empty_crawl_result(name, website, f"Crawl error: {str(e)[:200]}")
            result["data_source"] = "error"

        return result

    def _empty_crawl_result(self, name: str, website: str, note: str) -> dict:
        """Return structured null crawl result."""
        return {
            "name": name,
            "website": website,
            "total_pages": None,
            "pages_by_type": {},
            "site_depth": None,
            "internal_links": None,
            "external_links": None,
            "images_count": None,
            "avg_content_length": None,
            "meta_title_coverage": None,
            "meta_description_coverage": None,
            "has_schema": None,
            "mobile_friendly": None,
            "site_health": "unknown",
            "data_source": "unavailable",
            "note": note,
        }

    async def _real_bfs_crawl(
        self, name: str, start_url: str, max_depth: int
    ) -> Dict[str, Any]:
        """Real BFS crawl with httpx + BeautifulSoup, capped at 30 pages."""
        base_domain = urlparse(start_url).netloc
        visited: Set[str] = set()
        queue: List[tuple[str, int]] = [(start_url, 0)]  # (url, depth)
        pages_data: List[dict] = []
        max_pages = 30
        delay = 1.5

        async with httpx.AsyncClient(
            timeout=httpx.Timeout(15.0), follow_redirects=True
        ) as client:
            while queue and len(visited) < max_pages:
                url, depth = queue.pop(0)
                if url in visited:
                    continue
                if depth > max_depth:
                    continue

                visited.add(url)

                try:
                    resp = await client.get(
                        url, headers={"User-Agent": "AIM-CI/1.0"}
                    )
                    resp.raise_for_status()
                    html = resp.text
                    soup = BeautifulSoup(html, "html.parser")
                    final_url = str(resp.url)

                    # Classify page type from URL
                    page_type = self._classify_page_url(final_url)

                    # Collect page data
                    page_data = self._extract_page_data(soup, html, final_url, page_type)
                    page_data["crawl_url"] = url
                    page_data["crawl_depth"] = depth
                    pages_data.append(page_data)

                    # Enqueue internal links for next depth
                    if depth < max_depth:
                        for link in soup.find_all("a", href=True):
                            href = link.get("href", "")
                            full_url = urljoin(final_url, href)
                            parsed = urlparse(full_url)
                            # Only same domain, skip anchors/js/mailto
                            if (
                                parsed.netloc == base_domain
                                and full_url not in visited
                                and full_url.startswith(("http://", "https://"))
                                and not href.startswith("#")
                                and not href.startswith("javascript:")
                                and not href.startswith("mailto:")
                                and not href.startswith("tel:")
                            ):
                                queue.append((full_url, depth + 1))

                    await asyncio.sleep(delay)

                except Exception as e:
                    print(f"[CI Site Crawler] Page error {url}: {e}")
                    continue

        if not pages_data:
            return self._empty_crawl_result(name, start_url, "No pages crawled")

        return self._aggregate_crawl_results(name, start_url, pages_data)

    def _classify_page_url(self, url: str) -> str:
        """Classify page by URL pattern."""
        url_lower = url.lower()
        if url_lower.rstrip("/").endswith(("/", "/index", "/home")):
            return "homepage"
        if any(p in url_lower for p in ["/uslugi", "/service", "/services", "/napravleni", "/lechenie", "/diagnostik"]):
            return "services"
        if any(p in url_lower for p in ["/price", "/cena", "/ceny", "/prices", "/stoimost"]):
            return "prices"
        if any(p in url_lower for p in ["/about", "/o-nas", "/klinika", "/o-klinike", "/company"]):
            return "about"
        if any(p in url_lower for p in ["/contact", "/kontakt", "/contacts"]):
            return "contacts"
        if any(p in url_lower for p in ["/blog", "/article", "/stati", "/news", "/novosti", "/journal"]):
            return "blog"
        if any(p in url_lower for p in ["/otzyv", "/review", "/reviews", "/testimonials"]):
            return "reviews"
        if any(p in url_lower for p in ["/faq", "/question", "/vopros"]):
            return "faq"
        if any(p in url_lower for p in ["/zapis", "/appointment", "/booking", "/online", "/bron"]):
            return "booking"
        return "other"

    def _extract_page_data(
        self, soup: BeautifulSoup, html: str, url: str, page_type: str
    ) -> dict:
        """Extract real data from a single page."""
        # Meta title
        title_tag = soup.find("title")
        has_title = title_tag is not None and bool(title_tag.get_text().strip())

        # Meta description
        meta_desc = soup.find("meta", attrs={"name": "description"})
        has_desc = meta_desc is not None and bool(meta_desc.get("content", "").strip())

        # Headings
        h1_tags = soup.find_all("h1")
        h2_tags = soup.find_all("h2")

        # Images
        images = soup.find_all("img")
        imgs_with_alt = sum(1 for img in images if img.get("alt"))

        # Content length
        for tag in soup(["script", "style", "nav", "footer", "header"]):
            tag.decompose()
        text = soup.get_text(separator=" ")
        text = re.sub(r"\s+", " ", text).strip()
        word_count = len(text.split())

        # Schema
        schema_tags = soup.find_all("script", type="application/ld+json")
        has_schema = len(schema_tags) > 0

        # Mobile
        viewport = soup.find("meta", attrs={"name": "viewport"})
        mobile_friendly = viewport is not None

        # Internal/external links
        base_domain = urlparse(url).netloc
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

        return {
            "url": url,
            "page_type": page_type,
            "has_title": has_title,
            "has_description": has_desc,
            "h1_count": len(h1_tags),
            "h2_count": len(h2_tags),
            "image_count": len(images),
            "images_with_alt": imgs_with_alt,
            "word_count": word_count,
            "has_schema": has_schema,
            "mobile_friendly": mobile_friendly,
            "internal_links": internal,
            "external_links": external,
        }

    def _aggregate_crawl_results(
        self, name: str, website: str, pages_data: List[dict]
    ) -> dict:
        """Aggregate individual page data into site-level crawl result."""
        total_pages = len(pages_data)

        # Pages by type
        pages_by_type: dict[str, int] = {}
        for p in pages_data:
            pt = p["page_type"]
            pages_by_type[pt] = pages_by_type.get(pt, 0) + 1

        # Max depth reached
        max_depth_reached = max(p["crawl_depth"] for p in pages_data)

        # Total internal/external links (sum across all pages)
        total_internal = sum(p["internal_links"] for p in pages_data)
        total_external = sum(p["external_links"] for p in pages_data)

        # Total images
        total_images = sum(p["image_count"] for p in pages_data)

        # Average content length
        avg_content_length = round(sum(p["word_count"] for p in pages_data) / total_pages) if total_pages > 0 else 0

        # Meta coverage
        pages_with_title = sum(1 for p in pages_data if p["has_title"])
        pages_with_desc = sum(1 for p in pages_data if p["has_description"])
        meta_title_coverage = round(pages_with_title / total_pages * 100, 1) if total_pages > 0 else 0
        meta_description_coverage = round(pages_with_desc / total_pages * 100, 1) if total_pages > 0 else 0

        # Schema
        has_schema = any(p["has_schema"] for p in pages_data)

        # Mobile friendly
        mobile_friendly = any(p["mobile_friendly"] for p in pages_data)

        return {
            "name": name,
            "website": website,
            "total_pages": total_pages,
            "pages_by_type": pages_by_type,
            "site_depth": max_depth_reached,
            "internal_links": total_internal,
            "external_links": total_external,
            "images_count": total_images,
            "avg_content_length": avg_content_length,
            "meta_title_coverage": meta_title_coverage,
            "meta_description_coverage": meta_description_coverage,
            "has_schema": has_schema,
            "mobile_friendly": mobile_friendly,
            "site_health": self._assess_site_health(
                meta_title_coverage / 100 if meta_title_coverage > 0 else 0,
                meta_description_coverage / 100 if meta_description_coverage > 0 else 0,
                has_schema,
                mobile_friendly,
            ),
            "crawled_pages": [
                {
                    "url": p["url"],
                    "page_type": p["page_type"],
                    "word_count": p["word_count"],
                }
                for p in pages_data[:10]
            ],
            "data_source": "httpx_bfs_crawl",
        }

    def _assess_site_health(
        self,
        meta_title: float,
        meta_desc: float,
        has_schema: bool,
        mobile: bool
    ) -> str:
        """Оценить здоровье сайта."""
        score = 0

        # Meta tags
        if meta_title > 0.9:
            score += 2
        elif meta_title > 0.7:
            score += 1

        if meta_desc > 0.8:
            score += 2
        elif meta_desc > 0.6:
            score += 1

        # Schema
        if has_schema:
            score += 2

        # Mobile
        if mobile:
            score += 2

        # Оценка
        if score >= 7:
            return "excellent"
        elif score >= 5:
            return "good"
        elif score >= 3:
            return "fair"
        else:
            return "poor"

    async def _analyze_site_structures(
        self,
        crawl_results: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Проанализировать структуры сайтов.

        Args:
            crawl_results: результаты краулинга

        Returns:
            Анализ структур
        """
        print(f"[CI Site Crawler] Анализ структур сайтов")

        # Средние показатели
        avg_pages = sum(r["total_pages"] for r in crawl_results) / len(crawl_results)
        avg_depth = sum(r["site_depth"] for r in crawl_results) / len(crawl_results)
        avg_content_length = sum(r["avg_content_length"] for r in crawl_results) / len(crawl_results)

        # Покрытие типов страниц
        page_type_coverage = {}
        for page_type in self.page_types.keys():
            count = sum(1 for r in crawl_results if r["pages_by_type"].get(page_type, 0) > 0)
            coverage = (count / len(crawl_results)) * 100
            page_type_coverage[page_type] = round(coverage, 1)

        # Мобильная адаптация
        mobile_adoption = (sum(1 for r in crawl_results if r["mobile_friendly"]) / len(crawl_results)) * 100

        # Schema.org adoption
        schema_adoption = (sum(1 for r in crawl_results if r["has_schema"]) / len(crawl_results)) * 100

        structure_analysis = {
            "avg_pages": round(avg_pages, 1),
            "avg_depth": round(avg_depth, 1),
            "avg_content_length": round(avg_content_length),
            "page_type_coverage": page_type_coverage,
            "mobile_adoption_percent": round(mobile_adoption, 1),
            "schema_adoption_percent": round(schema_adoption, 1)
        }

        return structure_analysis

    async def _identify_best_practices(
        self,
        crawl_results: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Определить лучшие практики.

        Args:
            crawl_results: результаты краулинга

        Returns:
            Лучшие практики
        """
        print(f"[CI Site Crawler] Определение лучших практик")

        best_practices = []

        # Лучшие по здоровью сайта
        excellent_sites = [r for r in crawl_results if r["site_health"] == "excellent"]
        if excellent_sites:
            best_practices.append({
                "category": "site_health",
                "title": "Отличное техническое состояние",
                "examples": [s["name"] for s in excellent_sites[:3]],
                "description": "Полное покрытие meta tags, Schema.org, мобильная адаптация"
            })

        # Лучшие по структуре
        deep_sites = sorted(crawl_results, key=lambda x: x["total_pages"], reverse=True)[:3]
        if deep_sites[0]["total_pages"] > 50:
            best_practices.append({
                "category": "content_volume",
                "title": "Большой объём контента",
                "examples": [s["name"] for s in deep_sites],
                "description": f"Более {deep_sites[0]['total_pages']} страниц контента"
            })

        # Лучшие по контенту
        rich_content = sorted(crawl_results, key=lambda x: x["avg_content_length"], reverse=True)[:3]
        if rich_content[0]["avg_content_length"] > 1000:
            best_practices.append({
                "category": "content_quality",
                "title": "Глубокий контент",
                "examples": [s["name"] for s in rich_content],
                "description": f"Средняя длина страницы: {rich_content[0]['avg_content_length']} слов"
            })

        return best_practices

    async def _generate_site_insights(
        self,
        crawl_results: List[Dict[str, Any]],
        structure_analysis: Dict[str, Any],
        best_practices: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Сгенерировать инсайты по сайтам.

        Args:
            crawl_results: результаты краулинга
            structure_analysis: анализ структур
            best_practices: лучшие практики

        Returns:
            Инсайты
        """
        print(f"[CI Site Crawler] Генерация инсайтов")

        insights = {
            "technical_maturity": "high" if structure_analysis["schema_adoption_percent"] > 50 else "medium" if structure_analysis["schema_adoption_percent"] > 25 else "low",
            "mobile_readiness": "high" if structure_analysis["mobile_adoption_percent"] > 80 else "medium" if structure_analysis["mobile_adoption_percent"] > 50 else "low",
            "content_depth": "high" if structure_analysis["avg_content_length"] > 1000 else "medium" if structure_analysis["avg_content_length"] > 500 else "low",
            "key_findings": []
        }

        # Ключевые находки
        if structure_analysis["mobile_adoption_percent"] < 100:
            insights["key_findings"].append(f"{100 - structure_analysis['mobile_adoption_percent']:.0f}% сайтов не адаптированы под мобильные")

        if structure_analysis["schema_adoption_percent"] < 50:
            insights["key_findings"].append("Менее 50% конкурентов используют Schema.org")

        if len(best_practices) > 0:
            insights["key_findings"].append(f"Обнаружено {len(best_practices)} лучших практик для внедрения")

        return insights

    async def _save_results(self, results: Dict[str, Any]):
        """Сохранить результаты в файл."""
        output_file = "AIM/data/ci-site-crawler.json"

        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)

        print(f"[CI Site Crawler] Результаты сохранены в {output_file}")

    def get_capabilities(self) -> List[str]:
        """Возвращает список возможностей агента."""
        return [
            "site_crawling",
            "structure_analysis",
            "link_analysis",
            "content_extraction",
            "metadata_analysis",
            "mobile_analysis",
            "schema_detection"
        ]
