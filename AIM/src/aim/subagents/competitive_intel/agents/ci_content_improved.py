"""
CI Content Agent - Content Strategy Analysis (Improved with trafilatura)

Анализирует контент-стратегию конкурентов используя реальное извлечение контента:
- Извлечение текста через trafilatura
- Анализ метаданных (title, description, author, date)
- Качество и глубина контента (word count, readability)
- SEO-оптимизация (headings, keywords, structure)
- Контент-маркетинг стратегия

Основано на лучших практиках из python-seo-analyzer:
- https://github.com/sethblack/python-seo-analyzer
"""

from typing import Any, Dict, List, Optional
from datetime import datetime
import json
import hashlib
import re
from collections import Counter
from urllib.parse import urlsplit

import trafilatura
import httpx
from bs4 import BeautifulSoup
import lxml.html as lh

from meai.agents.base_agent import Agent, Task, TaskResult
from meai.memory.obsidian import ObsidianVault


# Regex for tokenization
TOKEN_REGEX = re.compile(r"(?u)\b\w\w+\b")

# Heading tags XPaths
HEADING_TAGS_XPATHS = {
    "h1": "//h1",
    "h2": "//h2",
    "h3": "//h3",
    "h4": "//h4",
    "h5": "//h5",
    "h6": "//h6",
}

# Additional tags XPaths
ADDITIONAL_TAGS_XPATHS = {
    "title": "//title/text()",
    "meta_desc": '//meta[@name="description"]/@content',
    "canonical": '//link[@rel="canonical"]/@href',
    "og_title": '//meta[@property="og:title"]/@content',
    "og_desc": '//meta[@property="og:description"]/@content',
    "og_url": '//meta[@property="og:url"]/@content',
    "og_image": '//meta[@property="og:image"]/@content',
}


class PageAnalyzer:
    """
    Анализатор отдельной страницы.

    Основано на python-seo-analyzer/pyseoanalyzer/page.py
    """

    def __init__(self, url: str, encoding: str = "utf-8"):
        self.url = url
        self.encoding = encoding
        self.parsed_url = urlsplit(url)

        # Extracted data
        self.title: str = ""
        self.author: str = ""
        self.description: str = ""
        self.hostname: str = ""
        self.sitename: str = ""
        self.date: str = ""
        self.content: Optional[Dict[str, Any]] = None
        self.content_hash: str = ""
        self.total_word_count: int = 0
        self.headings: Dict[str, List[str]] = {}
        self.additional_info: Dict[str, Any] = {}
        self.warnings: List[str] = []

    async def analyze(self, raw_html: Optional[str] = None) -> bool:
        """
        Проанализировать страницу.

        Args:
            raw_html: HTML контент (если None, будет загружен)

        Returns:
            True если анализ успешен
        """
        # Fetch HTML if not provided
        if not raw_html:
            raw_html = await self._fetch_html()
            if not raw_html:
                return False

        # Calculate content hash
        self.content_hash = hashlib.sha1(raw_html.encode(self.encoding)).hexdigest()

        # Extract metadata using trafilatura
        metadata = trafilatura.extract_metadata(
            filecontent=raw_html,
            default_url=self.url,
            extensive=True,
        )

        # Get metadata values
        metadata_dict = metadata.as_dict() if metadata else {}
        self.title = self._get_meta_value(metadata_dict, "title")
        self.author = self._get_meta_value(metadata_dict, "author")
        self.description = self._get_meta_value(metadata_dict, "description")
        self.hostname = self._get_meta_value(metadata_dict, "hostname")
        self.sitename = self._get_meta_value(metadata_dict, "sitename")
        self.date = self._get_meta_value(metadata_dict, "date")

        # Extract content using trafilatura
        content_json = trafilatura.extract(
            raw_html,
            include_links=True,
            include_formatting=False,
            include_tables=True,
            include_images=True,
            output_format="json",
        )

        self.content = json.loads(content_json) if content_json else None

        if self.content and "text" in self.content:
            self.total_word_count = len(self.content["text"].split())

        # Parse with BeautifulSoup for additional analysis
        html_without_comments = re.sub(r"<!--.*?-->", r"", raw_html, flags=re.DOTALL)
        soup = BeautifulSoup(html_without_comments, "html.parser")

        # Analyze headings
        self._analyze_heading_tags(soup)

        # Analyze additional tags
        self._analyze_additional_tags(soup)

        return True

    async def _fetch_html(self) -> Optional[str]:
        """Загрузить HTML страницы."""
        try:
            async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
                response = await client.get(self.url)
                response.raise_for_status()

                # Detect encoding
                encoding = self.encoding
                if "content-type" in response.headers:
                    content_type = response.headers["content-type"]
                    if "charset=" in content_type:
                        encoding = content_type.split("charset=")[-1].strip()

                return response.content.decode(encoding, errors="replace")

        except Exception as e:
            self.warnings.append(f"Failed to fetch {self.url}: {e}")
            return None

    def _get_meta_value(self, metadata_dict: Dict[str, Any], key: str) -> str:
        """Получить значение метаданных или пустую строку."""
        value = metadata_dict.get(key)
        return "" if value is None or value == "None" else value

    def _analyze_heading_tags(self, soup: BeautifulSoup):
        """Проанализировать заголовки."""
        try:
            dom = lh.fromstring(str(soup))
            for tag, xpath in HEADING_TAGS_XPATHS.items():
                headings = [h.text_content() for h in dom.xpath(xpath)]
                if headings:
                    self.headings[tag] = headings
        except Exception as e:
            self.warnings.append(f"Failed to analyze headings: {e}")

    def _analyze_additional_tags(self, soup: BeautifulSoup):
        """Проанализировать дополнительные теги."""
        try:
            dom = lh.fromstring(str(soup))
            for tag, xpath in ADDITIONAL_TAGS_XPATHS.items():
                values = dom.xpath(xpath)
                if values:
                    self.additional_info[tag] = values
        except Exception as e:
            self.warnings.append(f"Failed to analyze additional tags: {e}")

    def as_dict(self) -> Dict[str, Any]:
        """Вернуть результаты как словарь."""
        return {
            "url": self.url,
            "title": self.title,
            "description": self.description,
            "author": self.author,
            "hostname": self.hostname,
            "sitename": self.sitename,
            "date": self.date,
            "word_count": self.total_word_count,
            "content_hash": self.content_hash,
            "headings": self.headings,
            "additional_info": self.additional_info,
            "warnings": self.warnings,
        }


class CIContentAgentImproved(Agent):
    """CI Content - агент анализа контент-стратегии конкурентов (улучшенная версия)."""

    def __init__(
        self,
        agent_id: str,
        database_url: str = "sqlite+aiosqlite:///./data/meai.db",
        vault_path: str = "./obsidian"
    ):
        super().__init__(
            agent_id=agent_id,
            agent_type="ci-content",
            database_url=database_url,
            vault_path=vault_path
        )
        self.vault = ObsidianVault("AIM/obsidian/ci-content")

        # Content types
        self.content_types = {
            "blog": "Блог/статьи",
            "video": "Видео",
            "cases": "Кейсы/портфолио",
            "faq": "FAQ/вопросы-ответы",
            "guides": "Гайды/инструкции",
            "news": "Новости",
            "reviews": "Отзывы"
        }

    async def execute_task(self, task: Task) -> TaskResult:
        """
        Выполнить анализ контент-стратегии конкурентов.

        Args:
            task: Задача с data:
                - competitors: список конкурентов с URLs (обязательно)
                - niche: ниша (опционально)

        Returns:
            TaskResult с анализом контента
        """
        try:
            competitors = task.data["competitors"]
            niche = task.data.get("niche", "")

            print(f"[CI Content Improved] Начало анализа контента {len(competitors)} конкурентов")

            # Analyze content for each competitor
            content_profiles = []
            for competitor in competitors:
                profile = await self._analyze_competitor_content(competitor, niche)
                content_profiles.append(profile)

            # Market content analysis
            market_analysis = await self._analyze_market_content(content_profiles)

            # Identify content leaders
            content_leaders = await self._identify_content_leaders(content_profiles)

            # Content gaps analysis
            content_gaps = await self._analyze_content_gaps(content_profiles, niche)

            # Generate insights
            insights = await self._generate_content_insights(
                content_profiles, market_analysis, content_leaders, content_gaps
            )

            # Save results
            results = {
                "analysis_date": datetime.now().isoformat(),
                "total_analyzed": len(competitors),
                "niche": niche,
                "content_profiles": content_profiles,
                "market_analysis": market_analysis,
                "content_leaders": content_leaders,
                "content_gaps": content_gaps,
                "insights": insights
            }

            await self._save_results(results)

            print(f"[CI Content Improved] Анализ контента завершён для {len(competitors)} конкурентов")

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
            print(f"[CI Content Improved] Ошибка: {e}")
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

    async def _analyze_competitor_content(
        self,
        competitor: Dict[str, Any],
        niche: str
    ) -> Dict[str, Any]:
        """
        Проанализировать контент одного конкурента.

        Args:
            competitor: данные конкурента (должен содержать 'url')
            niche: ниша

        Returns:
            Контент-профиль конкурента
        """
        name = competitor["name"]
        url = competitor.get("url", "")

        if not url:
            print(f"[CI Content Improved] Пропуск {name}: нет URL")
            return self._empty_profile(name)

        print(f"[CI Content Improved] Анализ контента: {name} ({url})")

        # Analyze main page
        analyzer = PageAnalyzer(url)
        success = await analyzer.analyze()

        if not success:
            print(f"[CI Content Improved] Не удалось проанализировать {name}")
            return self._empty_profile(name)

        # Calculate quality score based on real data
        quality_score = self._calculate_quality_score(analyzer)

        # Calculate SEO score
        seo_score = self._calculate_seo_score(analyzer)

        # Assess content maturity
        content_maturity = self._assess_content_maturity_from_analysis(analyzer, quality_score)

        profile = {
            "name": name,
            "url": url,
            "title": analyzer.title,
            "description": analyzer.description,
            "word_count": analyzer.total_word_count,
            "headings": analyzer.headings,
            "quality_score": quality_score,
            "seo_score": seo_score,
            "content_maturity": content_maturity,
            "has_content_strategy": quality_score > 60 and seo_score > 60,
            "warnings": analyzer.warnings,
            "analyzed_at": datetime.now().isoformat()
        }

        return profile

    def _empty_profile(self, name: str) -> Dict[str, Any]:
        """Создать пустой профиль для конкурента."""
        return {
            "name": name,
            "url": "",
            "title": "",
            "description": "",
            "word_count": 0,
            "headings": {},
            "quality_score": 0,
            "seo_score": 0,
            "content_maturity": "minimal",
            "has_content_strategy": False,
            "warnings": ["No URL provided"],
            "analyzed_at": datetime.now().isoformat()
        }

    def _calculate_quality_score(self, analyzer: PageAnalyzer) -> int:
        """
        Рассчитать оценку качества контента (0-100).

        Факторы:
        - Word count (больше = лучше)
        - Наличие автора
        - Наличие даты
        - Структура заголовков
        """
        score = 0

        # Word count (0-40 points)
        if analyzer.total_word_count >= 2000:
            score += 40
        elif analyzer.total_word_count >= 1000:
            score += 30
        elif analyzer.total_word_count >= 500:
            score += 20
        elif analyzer.total_word_count >= 200:
            score += 10

        # Author (0-15 points)
        if analyzer.author:
            score += 15

        # Date (0-15 points)
        if analyzer.date:
            score += 15

        # Heading structure (0-30 points)
        if "h1" in analyzer.headings:
            score += 10
        if "h2" in analyzer.headings:
            score += 10
        if "h3" in analyzer.headings:
            score += 10

        return min(score, 100)

    def _calculate_seo_score(self, analyzer: PageAnalyzer) -> int:
        """
        Рассчитать SEO оценку (0-100).

        Факторы:
        - Title tag
        - Meta description
        - Canonical URL
        - OG tags
        - Heading structure
        """
        score = 0

        # Title (0-20 points)
        if analyzer.title:
            score += 20

        # Meta description (0-20 points)
        if analyzer.description:
            score += 20

        # Canonical (0-15 points)
        if "canonical" in analyzer.additional_info:
            score += 15

        # OG tags (0-15 points)
        og_count = sum(1 for k in analyzer.additional_info.keys() if k.startswith("og_"))
        score += min(og_count * 5, 15)

        # Heading structure (0-30 points)
        if "h1" in analyzer.headings and len(analyzer.headings["h1"]) == 1:
            score += 15  # Exactly one H1
        if "h2" in analyzer.headings:
            score += 10
        if "h3" in analyzer.headings:
            score += 5

        return min(score, 100)

    def _assess_content_maturity_from_analysis(
        self,
        analyzer: PageAnalyzer,
        quality_score: int
    ) -> str:
        """Оценить зрелость контента на основе анализа."""
        score = 0

        # Quality
        if quality_score >= 80:
            score += 3
        elif quality_score >= 60:
            score += 2
        elif quality_score >= 40:
            score += 1

        # Word count
        if analyzer.total_word_count >= 2000:
            score += 3
        elif analyzer.total_word_count >= 1000:
            score += 2
        elif analyzer.total_word_count >= 500:
            score += 1

        # Structure
        if len(analyzer.headings) >= 3:
            score += 3
        elif len(analyzer.headings) >= 2:
            score += 2
        elif len(analyzer.headings) >= 1:
            score += 1

        # Final assessment
        if score >= 7:
            return "advanced"
        elif score >= 4:
            return "intermediate"
        elif score >= 2:
            return "basic"
        else:
            return "minimal"

    async def _analyze_market_content(
        self,
        content_profiles: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Проанализировать контент-активность рынка."""
        print(f"[CI Content Improved] Анализ контент-активности рынка")

        # Filter out empty profiles
        valid_profiles = [p for p in content_profiles if p["word_count"] > 0]

        if not valid_profiles:
            return {
                "avg_word_count": 0,
                "avg_quality_score": 0,
                "avg_seo_score": 0,
                "strategy_adoption_percent": 0,
            }

        # Average metrics
        avg_word_count = sum(p["word_count"] for p in valid_profiles) / len(valid_profiles)
        avg_quality = sum(p["quality_score"] for p in valid_profiles) / len(valid_profiles)
        avg_seo = sum(p["seo_score"] for p in valid_profiles) / len(valid_profiles)

        # Strategy adoption
        with_strategy = sum(1 for p in valid_profiles if p["has_content_strategy"])
        strategy_adoption = (with_strategy / len(valid_profiles)) * 100

        return {
            "avg_word_count": round(avg_word_count, 1),
            "avg_quality_score": round(avg_quality, 1),
            "avg_seo_score": round(avg_seo, 1),
            "strategy_adoption_percent": round(strategy_adoption, 1),
        }

    async def _identify_content_leaders(
        self,
        content_profiles: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Определить лидеров по контенту."""
        print(f"[CI Content Improved] Определение контент-лидеров")

        # Filter valid profiles
        valid_profiles = [p for p in content_profiles if p["word_count"] > 0]

        if not valid_profiles:
            return {"quality_leaders": [], "seo_leaders": []}

        # Sort by quality
        sorted_by_quality = sorted(
            valid_profiles,
            key=lambda x: x["quality_score"],
            reverse=True
        )

        # Sort by SEO
        sorted_by_seo = sorted(
            valid_profiles,
            key=lambda x: x["seo_score"],
            reverse=True
        )

        return {
            "quality_leaders": [
                {
                    "name": p["name"],
                    "quality_score": p["quality_score"],
                    "word_count": p["word_count"],
                    "maturity": p["content_maturity"]
                }
                for p in sorted_by_quality[:3]
            ],
            "seo_leaders": [
                {
                    "name": p["name"],
                    "seo_score": p["seo_score"],
                    "title": p["title"],
                    "description": p["description"]
                }
                for p in sorted_by_seo[:3]
            ]
        }

    async def _analyze_content_gaps(
        self,
        content_profiles: List[Dict[str, Any]],
        niche: str
    ) -> List[Dict[str, Any]]:
        """Проанализировать пробелы в контенте."""
        print(f"[CI Content Improved] Анализ пробелов в контенте")

        gaps = []

        valid_profiles = [p for p in content_profiles if p["word_count"] > 0]

        if not valid_profiles:
            return gaps

        # Low quality content
        low_quality_count = sum(1 for p in valid_profiles if p["quality_score"] < 60)
        if low_quality_count > len(valid_profiles) / 2:
            gaps.append({
                "type": "quality_gap",
                "description": "Большинство конкурентов имеют низкое качество контента",
                "opportunity": "high"
            })

        # Low SEO optimization
        low_seo_count = sum(1 for p in valid_profiles if p["seo_score"] < 60)
        if low_seo_count > len(valid_profiles) / 2:
            gaps.append({
                "type": "seo_gap",
                "description": "Большинство конкурентов плохо оптимизируют контент для SEO",
                "opportunity": "high"
            })

        # Short content
        short_content_count = sum(1 for p in valid_profiles if p["word_count"] < 500)
        if short_content_count > len(valid_profiles) / 2:
            gaps.append({
                "type": "depth_gap",
                "description": "Большинство конкурентов публикуют короткий контент (<500 слов)",
                "opportunity": "medium"
            })

        return gaps

    async def _generate_content_insights(
        self,
        content_profiles: List[Dict[str, Any]],
        market_analysis: Dict[str, Any],
        content_leaders: Dict[str, Any],
        content_gaps: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Сгенерировать контент-инсайты."""
        print(f"[CI Content Improved] Генерация контент-инсайтов")

        valid_profiles = [p for p in content_profiles if p["word_count"] > 0]

        insights = {
            "content_maturity_level": self._assess_market_maturity(valid_profiles),
            "content_competition": "high" if market_analysis["avg_word_count"] > 1000 else "medium" if market_analysis["avg_word_count"] > 500 else "low",
            "opportunities_count": len([g for g in content_gaps if g.get("opportunity") == "high"]),
            "key_findings": []
        }

        # Key findings
        if market_analysis["strategy_adoption_percent"] < 50:
            insights["key_findings"].append("Менее 50% конкурентов имеют контент-стратегию")

        if market_analysis["avg_quality_score"] < 70:
            insights["key_findings"].append(f"Средний уровень качества контента: {market_analysis['avg_quality_score']:.0f}/100")

        if len(content_gaps) > 0:
            insights["key_findings"].append(f"Обнаружено {len(content_gaps)} возможностей для дифференциации")

        return insights

    def _assess_market_maturity(self, profiles: List[Dict[str, Any]]) -> str:
        """Оценить зрелость контент-маркетинга на рынке."""
        if not profiles:
            return "minimal"

        maturity_scores = {
            "minimal": 1,
            "basic": 2,
            "intermediate": 3,
            "advanced": 4
        }

        avg_score = sum(maturity_scores.get(p["content_maturity"], 1) for p in profiles) / len(profiles)

        if avg_score >= 3.5:
            return "advanced"
        elif avg_score >= 2.5:
            return "intermediate"
        elif avg_score >= 1.5:
            return "basic"
        else:
            return "minimal"

    async def _save_results(self, results: Dict[str, Any]):
        """Сохранить результаты в файл."""
        output_file = "AIM/data/ci-content-improved.json"

        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)

        print(f"[CI Content Improved] Результаты сохранены в {output_file}")

    def get_capabilities(self) -> List[str]:
        """Возвращает список возможностей агента."""
        return [
            "real_content_extraction",
            "trafilatura_analysis",
            "content_quality_assessment",
            "seo_content_analysis",
            "metadata_extraction",
            "heading_structure_analysis"
        ]
