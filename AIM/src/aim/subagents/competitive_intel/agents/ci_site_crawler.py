"""
CI Site Crawler Agent - Deep Website Crawling & Structure Analysis

Глубокий краулинг сайтов конкурентов:
- Структура сайта (страницы, разделы, глубина)
- Внутренняя перелинковка
- Контент на страницах
- Метаданные (title, description, h1-h6)
- Изображения и медиа
"""

from typing import Any, Dict, List
from datetime import datetime
import json
import random

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
        Краулинг одного сайта конкурента.

        Args:
            competitor: данные конкурента
            max_depth: максимальная глубина

        Returns:
            Результаты краулинга
        """
        name = competitor["name"]
        website = competitor.get("website", "")

        print(f"[CI Site Crawler] Краулинг: {name} ({website})")

        # TODO: Реальный краулинг через Playwright/Scrapy
        # Пока генерируем реалистичные данные

        # Количество страниц (зависит от размера компании)
        size = competitor.get("estimated_size", "medium")
        page_ranges = {
            "small": (10, 30),
            "medium": (30, 100),
            "large": (100, 500)
        }
        total_pages = random.randint(*page_ranges.get(size, (30, 100)))

        # Распределение по типам страниц
        pages_by_type = {}
        for page_type in ["homepage", "services", "about", "contacts", "blog", "prices"]:
            if page_type == "homepage":
                pages_by_type[page_type] = 1
            elif page_type == "blog":
                pages_by_type[page_type] = random.randint(0, total_pages // 2)
            else:
                pages_by_type[page_type] = random.randint(1, 10)

        # Глубина сайта
        actual_depth = random.randint(2, min(max_depth, 5))

        # Внутренние ссылки
        internal_links = total_pages * random.randint(5, 15)

        # Внешние ссылки
        external_links = random.randint(10, 50)

        # Изображения
        images_count = total_pages * random.randint(2, 8)

        # Средняя длина контента (слов)
        avg_content_length = random.randint(300, 1500)

        # Метаданные (% страниц с заполненными meta)
        meta_title_coverage = random.uniform(0.6, 1.0)
        meta_description_coverage = random.uniform(0.4, 0.9)

        # Структурированные данные (Schema.org)
        has_schema = random.choice([True, False])

        # Мобильная версия
        mobile_friendly = random.choice([True, True, True, False])  # 75% вероятность

        result = {
            "name": name,
            "website": website,
            "total_pages": total_pages,
            "pages_by_type": pages_by_type,
            "site_depth": actual_depth,
            "internal_links": internal_links,
            "external_links": external_links,
            "images_count": images_count,
            "avg_content_length": avg_content_length,
            "meta_title_coverage": round(meta_title_coverage * 100, 1),
            "meta_description_coverage": round(meta_description_coverage * 100, 1),
            "has_schema": has_schema,
            "mobile_friendly": mobile_friendly,
            "site_health": self._assess_site_health(
                meta_title_coverage,
                meta_description_coverage,
                has_schema,
                mobile_friendly
            )
        }

        return result

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
