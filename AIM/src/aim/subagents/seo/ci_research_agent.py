"""
CI Research Agent - Competitor Intelligence Research

Проводит глубокий reverse-engineering конкурентов в медицинском маркетинге
используя Industry Benchmark подход.

4-layer methodology:
1. Source Harvest - сбор первичных источников
2. Company Synthesis - reverse-engineering memos
3. Meta-Synthesis - извлечение паттернов (growth laws, sales laws, archetypes)
4. Application Layer - transferability analysis (Copy/Adapt/Ignore)
"""

import asyncio
import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field
from enum import Enum

import httpx
import structlog
from pydantic import BaseModel, Field, field_validator

from meai.agents.base_agent import Agent
from meai.events.event_bus import EventBus, Event
from meai.memory.obsidian import ObsidianVault


logger = structlog.get_logger(__name__)


# ============================================================================
# Data Models
# ============================================================================

class ResearchDepth(str, Enum):
    """Глубина исследования"""
    TIER1 = "tier1"  # 10-20 компаний, глубокий анализ
    TIER2 = "tier2"  # 5-10 компаний, средний анализ


class Transferability(str, Enum):
    """Уровень transferability паттерна"""
    COPY = "copy"      # Копировать как есть
    ADAPT = "adapt"    # Адаптировать под контекст
    IGNORE = "ignore"  # Не копировать


class EvidenceLabel(str, Enum):
    """Метки качества evidence"""
    E = "[E]"   # Sourced evidence (Tier 1)
    I = "[I]"   # Inference from facts
    UV = "[UV]" # Unverified estimate
    OQ = "[OQ]" # Open question
    H = "[H]"   # Hypothesis to test


class ClientContext(BaseModel):
    """Контекст клиента"""
    positioning: str = Field(..., description="Позиционирование клиента")
    budget: int = Field(..., description="Бюджет в рублях")
    goals: List[str] = Field(..., description="Цели клиента")


class CIResearchInput(BaseModel):
    """Входные данные для CI Research Agent"""
    industry: str = Field(..., description="Индустрия клиента")
    client_context: ClientContext
    research_depth: ResearchDepth = Field(default=ResearchDepth.TIER2)
    focus_areas: List[str] = Field(
        default=["growth", "gtm", "trust", "local_seo"],
        description="Приоритеты анализа"
    )
    competitor_list: Optional[List[str]] = Field(
        default=None,
        description="Список конкурентов (если известны)"
    )
    max_competitors: int = Field(default=10, ge=1, le=50)

    @field_validator('industry')
    @classmethod
    def industry_not_empty(cls, v):
        if not v or not v.strip():
            raise ValueError("industry cannot be empty")
        return v


class GrowthLaw(BaseModel):
    """Growth law - паттерн роста"""
    law: str = Field(..., description="Название закона")
    prevalence: float = Field(..., ge=0.0, le=1.0, description="Распространённость (0-1)")
    description: str = Field(..., description="Описание")
    transferability: Transferability
    preconditions: List[str] = Field(..., description="Предусловия для работы")


class SalesLaw(BaseModel):
    """Sales law - паттерн продаж"""
    law: str = Field(..., description="Название закона")
    prevalence: float = Field(..., ge=0.0, le=1.0)
    description: str = Field(..., description="Описание")
    transferability: Transferability
    preconditions: List[str] = Field(..., description="Предусловия")


class Archetype(BaseModel):
    """Архетип конкурента"""
    name: str = Field(..., description="Название архетипа")
    members: List[str] = Field(..., description="Конкуренты в архетипе")
    characteristics: List[str] = Field(..., description="Характеристики")


class CopyPattern(BaseModel):
    """Паттерн для копирования с ICE scoring"""
    pattern: str = Field(..., description="Название паттерна")
    impact: int = Field(..., ge=1, le=10, description="Влияние (1-10)")
    confidence: int = Field(..., ge=1, le=10, description="Уверенность (1-10)")
    ease: int = Field(..., ge=1, le=10, description="Лёгкость (1-10)")
    ice_score: int = Field(..., description="ICE score = Impact × Confidence × Ease")
    implementation: str = Field(..., description="Как внедрить")

    @field_validator('ice_score', mode='before')
    @classmethod
    def calculate_ice_score(cls, v, info):
        data = info.data
        if 'impact' in data and 'confidence' in data and 'ease' in data:
            return data['impact'] * data['confidence'] * data['ease']
        return v


class IgnorePattern(BaseModel):
    """Паттерн для игнорирования"""
    pattern: str = Field(..., description="Название паттерна")
    reason: str = Field(..., description="Почему не копировать")
    alternative: str = Field(..., description="Альтернативный подход")


class SequencingPhase(BaseModel):
    """Фаза внедрения паттернов"""
    phase: int = Field(..., description="Номер фазы")
    duration: str = Field(..., description="Длительность")
    patterns: List[str] = Field(..., description="Паттерны для внедрения")
    expected_impact: str = Field(..., description="Ожидаемый эффект")


class CIResearchResult(BaseModel):
    """Результат CI Research"""
    benchmark_report_path: str = Field(..., description="Путь к отчёту")
    competitors_analyzed: int = Field(..., description="Количество конкурентов")
    growth_laws: List[GrowthLaw] = Field(default_factory=list)
    sales_laws: List[SalesLaw] = Field(default_factory=list)
    archetypes: List[Archetype] = Field(default_factory=list)
    do_copy: List[CopyPattern] = Field(default_factory=list)
    dont_copy: List[IgnorePattern] = Field(default_factory=list)
    sequencing_roadmap: List[SequencingPhase] = Field(default_factory=list)


class CIResearchMetrics(BaseModel):
    """Метрики выполнения"""
    execution_time_ms: int
    competitors_analyzed: int
    sources_collected: int
    evidence_quality_score: float = Field(..., ge=0.0, le=3.0)
    api_cost_usd: float


# ============================================================================
# Source Models
# ============================================================================

@dataclass
class Source:
    """Источник информации о конкуренте"""
    url: str
    title: str
    tier: int  # 1 = primary, 2 = secondary, 3 = tertiary
    content: str
    collected_at: datetime = field(default_factory=datetime.now)
    evidence_labels: List[str] = field(default_factory=list)


@dataclass
class CompetitorProfile:
    """Профиль конкурента"""
    domain: str
    name: str
    sources: List[Source] = field(default_factory=list)

    # Growth Machine (AARRR)
    initial_wedge: Optional[str] = None
    acquisition_channels: List[str] = field(default_factory=list)
    conversion_mechanism: Optional[str] = None
    retention_mechanism: Optional[str] = None
    expansion_mechanism: Optional[str] = None

    # Unit Economics
    acv: Optional[float] = None  # Average Contract Value
    cac: Optional[float] = None  # Customer Acquisition Cost
    ltv: Optional[float] = None  # Lifetime Value
    payback_period: Optional[int] = None  # months

    # Competitive Advantage
    core_motion: Optional[str] = None
    moats: List[str] = field(default_factory=list)
    risks: List[str] = field(default_factory=list)


# ============================================================================
# CI Research Agent
# ============================================================================

class CIResearchAgent(Agent):
    """
    CI Research Agent - Competitor Intelligence Research

    Проводит глубокий reverse-engineering конкурентов используя
    Industry Benchmark подход с 4-layer methodology.
    """

    def __init__(
        self,
        agent_id: str,
        event_bus: EventBus,
        obsidian_vault: ObsidianVault,
        api_keys: Dict[str, str],
        database_url: str = "sqlite+aiosqlite:///./AIM/data/aim.db",
    ):
        super().__init__(
            agent_id=agent_id,
            agent_type="ci_research",
            database_url=database_url,
            vault_path=str(obsidian_vault.vault_path),
        )
        self.api_keys = api_keys
        self.http_client = httpx.AsyncClient(timeout=30.0)

        # Timeouts
        self.source_harvest_timeout = 7200  # 2 hours
        self.company_synthesis_timeout = 14400  # 4 hours
        self.total_timeout = 28800  # 8 hours

        # Quality gates
        self.min_sources_per_competitor = 10
        self.target_evidence_quality = 2.0
        self.min_growth_laws = 3

    async def execute_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """
        Выполнить задачу CI Research

        Args:
            task: Задача с входными данными

        Returns:
            Результат с benchmark report
        """
        start_time = datetime.now()

        try:
            # Валидация входных данных
            input_data = CIResearchInput(**task["payload"])

            logger.info(
                "ci_research_started",
                industry=input_data.industry,
                research_depth=input_data.research_depth,
                max_competitors=input_data.max_competitors,
            )

            # Шаг 1: Source Harvest
            competitors = await self._source_harvest(input_data)

            # Шаг 2: Company Synthesis
            profiles = await self._company_synthesis(competitors, input_data)

            # Шаг 3: Meta-Synthesis
            meta = await self._meta_synthesis(profiles, input_data)

            # Шаг 4: Application Layer
            application = await self._application_layer(meta, input_data)

            # Шаг 5: Сохранить benchmark report
            report_path = await self._save_benchmark_report(
                input_data,
                competitors,
                profiles,
                meta,
                application,
            )

            # Рассчитать метрики
            execution_time = (datetime.now() - start_time).total_seconds() * 1000
            metrics = CIResearchMetrics(
                execution_time_ms=int(execution_time),
                competitors_analyzed=len(competitors),
                sources_collected=sum(len(c.sources) for c in competitors),
                evidence_quality_score=self._calculate_evidence_quality(competitors),
                api_cost_usd=self._calculate_api_cost(len(competitors)),
            )

            # Формировать результат
            result = CIResearchResult(
                benchmark_report_path=report_path,
                competitors_analyzed=len(competitors),
                growth_laws=meta["growth_laws"],
                sales_laws=meta["sales_laws"],
                archetypes=meta["archetypes"],
                do_copy=application["do_copy"],
                dont_copy=application["dont_copy"],
                sequencing_roadmap=application["sequencing_roadmap"],
            )

            logger.info(
                "ci_research_completed",
                competitors=len(competitors),
                growth_laws=len(result.growth_laws),
                sales_laws=len(result.sales_laws),
                archetypes=len(result.archetypes),
                execution_time_ms=metrics.execution_time_ms,
            )

            return {
                "status": "success",
                "result": result.model_dump(),
                "metrics": metrics.model_dump(),
                "errors": [],
            }

        except ValueError as e:
            logger.error("ci_research_validation_error", error=str(e))
            return {
                "status": "failure",
                "result": None,
                "metrics": {
                    "execution_time_ms": int((datetime.now() - start_time).total_seconds() * 1000),
                    "competitors_analyzed": 0,
                    "sources_collected": 0,
                    "evidence_quality_score": 0.0,
                    "api_cost_usd": 0.0,
                },
                "errors": [
                    {
                        "code": "INVALID_INPUT",
                        "message": str(e),
                        "details": {},
                    }
                ],
            }

        except asyncio.TimeoutError:
            logger.error("ci_research_timeout")
            return {
                "status": "partial_success",
                "result": None,
                "metrics": {
                    "execution_time_ms": int((datetime.now() - start_time).total_seconds() * 1000),
                    "competitors_analyzed": 0,
                    "sources_collected": 0,
                    "evidence_quality_score": 0.0,
                    "api_cost_usd": 0.0,
                },
                "errors": [
                    {
                        "code": "TIMEOUT",
                        "message": "Research exceeded timeout",
                        "details": {},
                    }
                ],
            }

        except Exception as e:
            logger.exception("ci_research_internal_error", error=str(e))
            return {
                "status": "failure",
                "result": None,
                "metrics": {
                    "execution_time_ms": int((datetime.now() - start_time).total_seconds() * 1000),
                    "competitors_analyzed": 0,
                    "sources_collected": 0,
                    "evidence_quality_score": 0.0,
                    "api_cost_usd": 0.0,
                },
                "errors": [
                    {
                        "code": "INTERNAL_ERROR",
                        "message": str(e),
                        "details": {},
                    }
                ],
            }

    async def _source_harvest(
        self,
        input_data: CIResearchInput,
    ) -> List[CompetitorProfile]:
        """
        Шаг 1: Source Harvest

        Собирает первичные источники о конкурентах:
        - Tier 1: founder interviews, operator posts, case studies
        - Tier 2: industry reports, news articles
        - Tier 3: Wikipedia, generic blogs
        """
        logger.info("source_harvest_started")

        # Определить список конкурентов
        if input_data.competitor_list:
            competitor_domains = input_data.competitor_list
        else:
            # TODO: Использовать SEMrush Competitor Discovery API
            competitor_domains = await self._discover_competitors(
                input_data.industry,
                input_data.max_competitors,
            )

        # Собрать источники для каждого конкурента
        competitors = []
        for domain in competitor_domains[:input_data.max_competitors]:
            profile = CompetitorProfile(domain=domain, name=domain)

            # Tier 1: Primary sources
            primary_sources = await self._collect_primary_sources(domain)
            profile.sources.extend(primary_sources)

            # Tier 2: Secondary sources
            secondary_sources = await self._collect_secondary_sources(domain)
            profile.sources.extend(secondary_sources)

            # Tier 3: Tertiary sources (опционально)
            if len(profile.sources) < self.min_sources_per_competitor:
                tertiary_sources = await self._collect_tertiary_sources(domain)
                profile.sources.extend(tertiary_sources)

            # API data collection
            await self._collect_api_data(profile)

            competitors.append(profile)

            logger.info(
                "competitor_sources_collected",
                domain=domain,
                sources=len(profile.sources),
            )

        logger.info(
            "source_harvest_completed",
            competitors=len(competitors),
            total_sources=sum(len(c.sources) for c in competitors),
        )

        return competitors

    async def _discover_competitors(
        self,
        industry: str,
        max_competitors: int,
    ) -> List[str]:
        """
        Найти конкурентов через SEMrush Competitor Discovery API

        Стратегия:
        1. Извлечь seed domain из industry query
        2. Использовать SEMrush Domain Competitors API
        3. Фильтровать по релевантности
        """
        logger.info("discovering_competitors", industry=industry, max_competitors=max_competitors)

        # Извлечь seed domain из industry query
        # Например: "стоматология Москва" -> поиск топовых доменов
        seed_domain = await self._find_seed_domain(industry)

        if not seed_domain:
            logger.warning("no_seed_domain_found", industry=industry)
            return []

        # Использовать SEMrush через Omni-Router
        from AIM.src.aim.subagents.api_clients.omni_router import OmniRouter
        from AIM.src.aim.subagents.api_clients.semrush_client import SEMrushClient

        # Инициализировать Omni-Router
        router = OmniRouter()
        router.add_provider(
            name="semrush",
            base_url="https://api.semrush.com",
            api_key=self.api_keys.get("semrush", ""),
            priority=10,
        )
        await router.initialize()

        try:
            # Создать SEMrush клиент
            semrush = SEMrushClient(router)

            # Найти конкурентов
            competitors_data = await semrush.discover_competitors(
                domain=seed_domain,
                database="ru",
                limit=max_competitors * 2,  # Запросить больше для фильтрации
            )

            # Фильтровать по релевантности
            # Берём только с competition_level > 0.3 и organic_traffic > 1000
            filtered = [
                c["domain"]
                for c in competitors_data
                if c["competition_level"] > 0.3 and c["organic_traffic"] > 1000
            ]

            result = filtered[:max_competitors]

            logger.info(
                "competitors_discovered",
                seed_domain=seed_domain,
                found=len(competitors_data),
                filtered=len(result),
            )

            return result

        finally:
            await router.close()

    async def _find_seed_domain(self, industry: str) -> Optional[str]:
        """
        Найти seed domain для industry query

        Использует Google Search для поиска топового домена по запросу
        """
        from AIM.src.aim.subagents.api_clients.web_scraper import WebScraper

        scraper = WebScraper()
        await scraper.initialize()

        try:
            # Поиск в Google
            results = await scraper.search_google(
                query=industry,
                num_results=5,
            )

            if results:
                # Взять первый результат как seed domain
                first_url = results[0]["url"]
                # Извлечь домен из URL
                from urllib.parse import urlparse
                domain = urlparse(first_url).netloc
                # Убрать www.
                domain = domain.replace("www.", "")

                logger.info("seed_domain_found", industry=industry, domain=domain)
                return domain

            return None

        finally:
            await scraper.close()

    async def _collect_primary_sources(self, domain: str) -> List[Source]:
        """
        Собрать Tier 1 sources (founder interviews, operator posts, case studies)

        Tier 1 = Primary/Operator sources:
        - Founder interviews
        - Operator posts (LinkedIn, Twitter)
        - Case studies
        - Product demos
        - Customer testimonials
        """
        sources = []
        from AIM.src.aim.subagents.api_clients.web_scraper import WebScraper

        scraper = WebScraper()
        await scraper.initialize()

        try:
            # 1. Founder interviews через Google Search
            interview_queries = [
                f'"{domain}" founder interview',
                f'"{domain}" CEO interview',
                f'"{domain}" основатель интервью',
            ]

            for query in interview_queries:
                try:
                    results = await scraper.search_google(query, num_results=3)
                    for result in results:
                        # Скрапить страницу
                        page_data = await scraper.scrape_page(result["url"])
                        sources.append(
                            Source(
                                url=result["url"],
                                title=result["title"],
                                tier=1,
                                content=page_data["content"] or result["snippet"],
                            )
                        )
                except Exception as e:
                    logger.warning("failed_to_scrape_interview", url=result.get("url"), error=str(e))
                    continue

            # 2. Case studies через поиск на сайте
            case_study_queries = [
                f'site:{domain} "case study"',
                f'site:{domain} "кейс"',
                f'site:{domain} "отзыв пациента"',
            ]

            for query in case_study_queries:
                try:
                    results = await scraper.search_google(query, num_results=5)
                    for result in results:
                        page_data = await scraper.scrape_page(result["url"])
                        sources.append(
                            Source(
                                url=result["url"],
                                title=result["title"],
                                tier=1,
                                content=page_data["content"] or result["snippet"],
                            )
                        )
                except Exception as e:
                    logger.warning("failed_to_scrape_case_study", url=result.get("url"), error=str(e))
                    continue

            # 3. LinkedIn operator posts
            # TODO: Требует LinkedIn API или авторизацию
            # Пока пропускаем

            # 4. Testimonials с медицинских платформ
            if "healthgrades" in self.api_keys or "zocdoc" in self.api_keys:
                # TODO: Интеграция с HealthGrades/Zocdoc API
                pass

            logger.info("primary_sources_collected", domain=domain, count=len(sources))
            return sources

        finally:
            await scraper.close()

    async def _collect_secondary_sources(self, domain: str) -> List[Source]:
        """
        Собрать Tier 2 sources (industry reports, news articles)

        Tier 2 = Secondary sources:
        - Industry reports
        - News articles
        - Conference talks
        - Press releases
        """
        sources = []
        from AIM.src.aim.subagents.api_clients.web_scraper import WebScraper

        scraper = WebScraper()
        await scraper.initialize()

        try:
            # 1. News articles через Google News
            news_queries = [
                f'"{domain}" новости',
                f'"{domain}" news',
            ]

            for query in news_queries:
                try:
                    results = await scraper.search_google(query, num_results=5)
                    for result in results:
                        # Фильтр: только новостные сайты
                        if any(news_domain in result["url"] for news_domain in ["vc.ru", "forbes.ru", "rbc.ru", "kommersant.ru"]):
                            page_data = await scraper.scrape_page(result["url"])
                            sources.append(
                                Source(
                                    url=result["url"],
                                    title=result["title"],
                                    tier=2,
                                    content=page_data["content"] or result["snippet"],
                                )
                            )
                except Exception as e:
                    logger.warning("failed_to_scrape_news", url=result.get("url"), error=str(e))
                    continue

            # 2. Industry reports через Google Scholar
            # TODO: Требует Google Scholar API
            # Пока используем обычный поиск с фильтром
            report_queries = [
                f'"{domain}" отчет рынок',
                f'"{domain}" market report',
            ]

            for query in report_queries:
                try:
                    results = await scraper.search_google(query, num_results=3)
                    for result in results:
                        # Фильтр: только аналитические сайты
                        if any(analytics_domain in result["url"] for analytics_domain in [".pdf", "research", "analytics", "report"]):
                            page_data = await scraper.scrape_page(result["url"])
                            sources.append(
                                Source(
                                    url=result["url"],
                                    title=result["title"],
                                    tier=2,
                                    content=page_data["content"] or result["snippet"],
                                )
                            )
                except Exception as e:
                    logger.warning("failed_to_scrape_report", url=result.get("url"), error=str(e))
                    continue

            # 3. Conference talks через YouTube
            # TODO: Требует YouTube API
            # Пока пропускаем

            logger.info("secondary_sources_collected", domain=domain, count=len(sources))
            return sources

        finally:
            await scraper.close()

    async def _collect_tertiary_sources(self, domain: str) -> List[Source]:
        """
        Собрать Tier 3 sources (Wikipedia, generic blogs)

        Tier 3 = Tertiary sources (используется только если недостаточно Tier 1-2):
        - Wikipedia
        - Generic blogs
        - Social media mentions
        """
        sources = []
        from AIM.src.aim.subagents.api_clients.web_scraper import WebScraper

        scraper = WebScraper()
        await scraper.initialize()

        try:
            # 1. Wikipedia
            wiki_queries = [
                f'site:ru.wikipedia.org "{domain}"',
                f'site:en.wikipedia.org "{domain}"',
            ]

            for query in wiki_queries:
                try:
                    results = await scraper.search_google(query, num_results=2)
                    for result in results:
                        page_data = await scraper.scrape_page(result["url"])
                        sources.append(
                            Source(
                                url=result["url"],
                                title=result["title"],
                                tier=3,
                                content=page_data["content"] or result["snippet"],
                            )
                        )
                except Exception as e:
                    logger.warning("failed_to_scrape_wikipedia", url=result.get("url"), error=str(e))
                    continue

            # 2. Generic blogs
            blog_queries = [
                f'"{domain}" отзыв',
                f'"{domain}" review',
            ]

            for query in blog_queries:
                try:
                    results = await scraper.search_google(query, num_results=3)
                    for result in results:
                        page_data = await scraper.scrape_page(result["url"])
                        sources.append(
                            Source(
                                url=result["url"],
                                title=result["title"],
                                tier=3,
                                content=page_data["content"] or result["snippet"],
                            )
                        )
                except Exception as e:
                    logger.warning("failed_to_scrape_blog", url=result.get("url"), error=str(e))
                    continue

            logger.info("tertiary_sources_collected", domain=domain, count=len(sources))
            return sources

        finally:
            await scraper.close()

    async def _collect_api_data(self, profile: CompetitorProfile) -> None:
        """
        Собрать данные через API (SEMrush, Ahrefs, SimilarWeb, Crunchbase)

        Обогащает profile метриками:
        - SEO metrics (keywords, traffic, backlinks)
        - Business metrics (funding, team size)
        - Medical ratings (HealthGrades, Zocdoc)
        """
        from AIM.src.aim.subagents.api_clients.omni_router import OmniRouter
        from AIM.src.aim.subagents.api_clients.semrush_client import SEMrushClient

        # Инициализировать Omni-Router
        router = OmniRouter()

        # Добавить доступные провайдеры
        if "semrush" in self.api_keys:
            router.add_provider(
                name="semrush",
                base_url="https://api.semrush.com",
                api_key=self.api_keys["semrush"],
                priority=10,
            )

        if "ahrefs" in self.api_keys:
            router.add_provider(
                name="ahrefs",
                base_url="https://api.ahrefs.com",
                api_key=self.api_keys["ahrefs"],
                priority=5,
            )

        await router.initialize()

        try:
            semrush = SEMrushClient(router)

            # 1. Domain Overview
            try:
                overview = await semrush.get_domain_overview(profile.domain, database="ru")

                # Сохранить в Source для evidence
                profile.sources.append(
                    Source(
                        url=f"https://www.semrush.com/analytics/overview/?q={profile.domain}",
                        title=f"SEMrush Domain Overview: {profile.domain}",
                        tier=1,  # API data = Tier 1
                        content=f"Organic Keywords: {overview['organic_keywords']}, "
                                f"Organic Traffic: {overview['organic_traffic']}, "
                                f"Organic Cost: ${overview['organic_cost']:.2f}",
                    )
                )

                logger.info("domain_overview_collected", domain=profile.domain)
            except Exception as e:
                logger.warning("domain_overview_failed", domain=profile.domain, error=str(e))

            # 2. Organic Keywords (top 20)
            try:
                keywords = await semrush.get_organic_keywords(
                    profile.domain,
                    database="ru",
                    limit=20,
                )

                # Сохранить топ-5 ключевых слов в Source
                top_keywords = keywords[:5]
                keywords_text = ", ".join([f"{k['keyword']} (pos {k['position']})" for k in top_keywords])

                profile.sources.append(
                    Source(
                        url=f"https://www.semrush.com/analytics/organic/positions/?q={profile.domain}",
                        title=f"SEMrush Top Keywords: {profile.domain}",
                        tier=1,
                        content=f"Top Keywords: {keywords_text}",
                    )
                )

                logger.info("organic_keywords_collected", domain=profile.domain, count=len(keywords))
            except Exception as e:
                logger.warning("organic_keywords_failed", domain=profile.domain, error=str(e))

            # 3. Backlinks (top 50)
            try:
                backlinks = await semrush.get_backlinks(profile.domain, limit=50)

                # Сохранить статистику в Source
                profile.sources.append(
                    Source(
                        url=f"https://www.semrush.com/analytics/backlinks/overview/?q={profile.domain}",
                        title=f"SEMrush Backlinks: {profile.domain}",
                        tier=1,
                        content=f"Total Backlinks: {len(backlinks)}",
                    )
                )

                logger.info("backlinks_collected", domain=profile.domain, count=len(backlinks))
            except Exception as e:
                logger.warning("backlinks_failed", domain=profile.domain, error=str(e))

            # 4. Crunchbase data (если доступен API key)
            if "crunchbase" in self.api_keys:
                # TODO: Интеграция с Crunchbase API
                pass

            # 5. Medical ratings (если доступны API keys)
            if "healthgrades" in self.api_keys or "zocdoc" in self.api_keys:
                # TODO: Интеграция с HealthGrades/Zocdoc API
                pass

        finally:
            await router.close()

        logger.debug("tertiary_sources_collected", domain=domain, count=len(sources))
        return sources

    async def _collect_api_data(self, profile: CompetitorProfile) -> None:
        """Собрать данные через API (SimilarWeb, Ahrefs, SEMrush, etc.)"""
        # TODO: Реализовать интеграцию с:
        # - SimilarWeb API: traffic, sources, engagement
        # - Ahrefs API: backlinks, keywords, DR
        # - SEMrush API: paid keywords, ad copy
        # - Crunchbase API: funding, team size
        # - HealthGrades/Zocdoc API: reviews, ratings

        logger.debug("api_data_collected", domain=profile.domain)

    async def _company_synthesis(
        self,
        competitors: List[CompetitorProfile],
        input_data: CIResearchInput,
    ) -> List[CompetitorProfile]:
        """
        Шаг 2: Company Synthesis

        Создаёт reverse-engineering memos для каждого конкурента:
        - Growth Machine (AARRR framework)
        - Unit Economics (ACV, CAC, LTV, payback)
        - Competitive Advantage (core motion, moats, risks)
        """
        logger.info("company_synthesis_started", competitors=len(competitors))

        for profile in competitors:
            # Extract Growth Machine
            await self._extract_growth_machine(profile)

            # Estimate Unit Economics
            await self._estimate_unit_economics(profile)

            # Analyze Competitive Advantage
            await self._analyze_competitive_advantage(profile)

            logger.debug(
                "competitor_synthesized",
                domain=profile.domain,
                initial_wedge=profile.initial_wedge,
                core_motion=profile.core_motion,
            )

        logger.info("company_synthesis_completed")
        return competitors

    async def _extract_growth_machine(self, profile: CompetitorProfile) -> None:
        """
        Извлечь Growth Machine (AARRR framework)

        Использует LLM для анализа собранных источников и извлечения:
        - Initial wedge (с чего начали)
        - Acquisition channels (как привлекают)
        - Conversion mechanism (как конвертируют)
        - Retention mechanism (как удерживают)
        - Expansion mechanism (как масштабируют)
        """
        # Собрать весь контент из источников
        all_content = "\n\n".join([
            f"[{s.tier}] {s.title}\n{s.content[:1000]}"  # Первые 1000 символов
            for s in profile.sources
        ])

        # Промпт для LLM
        prompt = f"""Analyze the following sources about {profile.domain} and extract their Growth Machine:

Sources:
{all_content}

Extract the following in JSON format:
{{
    "initial_wedge": "What was their initial market entry strategy? What niche did they start with?",
    "acquisition_channels": ["List of channels: SEO, PPC, GMB, Instagram, etc."],
    "conversion_mechanism": "How do they convert visitors to customers? (e.g., free consultation, trial)",
    "retention_mechanism": "How do they retain customers? (e.g., loyalty program, subscription)",
    "expansion_mechanism": "How do they expand revenue? (e.g., upsell, cross-sell)"
}}

Focus on EVIDENCE from sources. Mark inferences with [I].
"""

        try:
            # TODO: Вызвать LLM через Omni-Router
            # Пока используем заглушку с базовым извлечением

            # Простая эвристика: ищем ключевые слова в контенте
            if "SEO" in all_content or "поиск" in all_content:
                profile.acquisition_channels.append("SEO")
            if "реклама" in all_content or "ads" in all_content:
                profile.acquisition_channels.append("PPC")
            if "Instagram" in all_content or "соцсети" in all_content:
                profile.acquisition_channels.append("Instagram")
            if "Google My Business" in all_content or "GMB" in all_content:
                profile.acquisition_channels.append("GMB")

            # Initial wedge из первых источников
            if profile.sources:
                first_source = profile.sources[0]
                # Извлечь первое предложение как wedge
                sentences = first_source.content.split(".")
                if sentences:
                    profile.initial_wedge = sentences[0][:200]

            # Conversion mechanism
            if "консультация" in all_content or "consultation" in all_content:
                profile.conversion_mechanism = "Бесплатная консультация"
            elif "запись" in all_content or "booking" in all_content:
                profile.conversion_mechanism = "Онлайн запись"

            # Retention mechanism
            if "программа лояльности" in all_content or "loyalty" in all_content:
                profile.retention_mechanism = "Программа лояльности"
            elif "подписка" in all_content or "subscription" in all_content:
                profile.retention_mechanism = "Подписка"

            # Expansion mechanism
            if "дополнительные услуги" in all_content or "upsell" in all_content:
                profile.expansion_mechanism = "Upsell дополнительных услуг"

            logger.info(
                "growth_machine_extracted",
                domain=profile.domain,
                channels=len(profile.acquisition_channels),
            )

        except Exception as e:
            logger.error("growth_machine_extraction_failed", domain=profile.domain, error=str(e))

    async def _estimate_unit_economics(self, profile: CompetitorProfile) -> None:
        """
        Оценить Unit Economics

        Использует LLM для оценки на основе собранных данных:
        - ACV (Average Contract Value) - из pricing page или inference
        - CAC (Customer Acquisition Cost) - из ad spend estimates
        - LTV (Lifetime Value) - calculated from ACV × retention
        - Payback period - CAC / monthly revenue
        """
        # Собрать контент из источников
        all_content = "\n\n".join([
            f"[{s.tier}] {s.title}\n{s.content[:1000]}"
            for s in profile.sources
        ])

        # Промпт для LLM
        prompt = f"""Analyze the following sources about {profile.domain} and estimate their Unit Economics:

Sources:
{all_content}

Estimate the following in JSON format:
{{
    "acv": <number>,  // Average Contract Value in RUB (e.g., 150000 for dental implant)
    "cac": <number>,  // Customer Acquisition Cost in RUB (estimate from ad spend / conversions)
    "ltv": <number>,  // Lifetime Value in RUB (ACV × average customer lifetime)
    "payback_period": <number>  // Months to recover CAC
}}

Use EVIDENCE where available. Mark estimates with [I] inference.
For medical services, typical ranges:
- Dental implant ACV: 100,000-300,000 RUB
- CAC: 10-20% of ACV
- LTV: 2-3x ACV (repeat visits, referrals)
- Payback: 3-12 months
"""

        try:
            # TODO: Вызвать LLM через Omni-Router
            # Пока используем эвристики

            # Поиск цен в контенте
            import re
            prices = re.findall(r'(\d{1,3}(?:\s?\d{3})*)\s*(?:руб|₽|rub)', all_content.lower())
            if prices:
                # Взять максимальную цену как ACV (обычно это основная услуга)
                prices_int = [int(p.replace(" ", "")) for p in prices]
                profile.acv = float(max(prices_int))
            else:
                # Дефолтная оценка для медицинских услуг
                profile.acv = 150000.0  # [I] inference

            # CAC = 10-15% от ACV (типичная оценка для медицины)
            if profile.acv:
                profile.cac = profile.acv * 0.15  # [I] inference

            # LTV = 2x ACV (пациенты возвращаются, рекомендуют)
            if profile.acv:
                profile.ltv = profile.acv * 2.0  # [I] inference

            # Payback period = CAC / (ACV / 12) месяцев
            if profile.cac and profile.acv:
                monthly_revenue = profile.acv / 12
                profile.payback_period = int(profile.cac / monthly_revenue)

            logger.info(
                "unit_economics_estimated",
                domain=profile.domain,
                acv=profile.acv,
                cac=profile.cac,
                ltv=profile.ltv,
                payback=profile.payback_period,
            )

        except Exception as e:
            logger.error("unit_economics_estimation_failed", domain=profile.domain, error=str(e))

    async def _analyze_competitive_advantage(self, profile: CompetitorProfile) -> None:
        """
        Проанализировать конкурентное преимущество

        Использует LLM для анализа:
        - Core motion (как они выигрывают)
        - Moats (защитные рвы: network effects, switching costs, brand, proprietary tech)
        - Risks (зависимости, конкурентные угрозы, операционные риски)
        """
        # Собрать контент из источников
        all_content = "\n\n".join([
            f"[{s.tier}] {s.title}\n{s.content[:1000]}"
            for s in profile.sources
        ])

        # Промпт для LLM
        prompt = f"""Analyze the following sources about {profile.domain} and identify their competitive advantage:

Sources:
{all_content}

Extract the following in JSON format:
{{
    "core_motion": "How do they win? What's their primary competitive advantage?",
    "moats": [
        "List of defensible advantages:",
        "- Network effects (e.g., review volume, community)",
        "- Switching costs (e.g., patient history, loyalty program)",
        "- Brand (e.g., reputation, trust)",
        "- Proprietary tech (e.g., unique equipment, methodology)"
    ],
    "risks": [
        "List of vulnerabilities:",
        "- Dependencies (e.g., Google algorithm, single channel)",
        "- Competitive threats (e.g., new entrants, price competition)",
        "- Operational risks (e.g., key person dependency, location)"
    ]
}}

Focus on EVIDENCE from sources. Mark inferences with [I].
"""

        try:
            # TODO: Вызвать LLM через Omni-Router
            # Пока используем эвристики

            # Core motion из ключевых фраз
            if "4.8" in all_content or "5.0" in all_content or "рейтинг" in all_content:
                profile.core_motion = "Доминируют через высокий рейтинг и отзывы"
            elif "SEO" in all_content or "первые позиции" in all_content:
                profile.core_motion = "Доминируют в локальном SEO"
            elif "премиум" in all_content or "premium" in all_content:
                profile.core_motion = "Премиум позиционирование и качество"
            else:
                profile.core_motion = "Конкурируют через [I] inference"

            # Moats
            if "отзыв" in all_content or "review" in all_content:
                profile.moats.append("Brand reputation через отзывы")
            if "программа лояльности" in all_content:
                profile.moats.append("Switching costs через loyalty program")
            if "уникальн" in all_content or "unique" in all_content:
                profile.moats.append("Proprietary methodology")
            if "сеть" in all_content or "network" in all_content:
                profile.moats.append("Network effects через филиалы")

            # Risks
            if "Google" in all_content or "SEO" in all_content:
                profile.risks.append("Dependency on Google algorithm")
            if "реклама" in all_content or "ads" in all_content:
                profile.risks.append("Dependency on paid advertising")
            if "цена" in all_content or "price" in all_content:
                profile.risks.append("Price competition risk")
            if "основатель" in all_content or "founder" in all_content:
                profile.risks.append("Key person dependency")

            logger.info(
                "competitive_advantage_analyzed",
                domain=profile.domain,
                moats=len(profile.moats),
                risks=len(profile.risks),
            )

        except Exception as e:
            logger.error("competitive_advantage_analysis_failed", domain=profile.domain, error=str(e))

    async def _meta_synthesis(
        self,
        profiles: List[CompetitorProfile],
        input_data: CIResearchInput,
    ) -> Dict[str, Any]:
        """
        Шаг 3: Meta-Synthesis

        Извлекает cross-company паттерны:
        - Growth Laws (prevalence ≥30%)
        - Sales Laws
        - Archetypes (кластеры конкурентов)
        """
        logger.info("meta_synthesis_started")

        # Extract Growth Laws
        growth_laws = await self._extract_growth_laws(profiles)

        # Extract Sales Laws
        sales_laws = await self._extract_sales_laws(profiles)

        # Define Archetypes
        archetypes = await self._define_archetypes(profiles)

        logger.info(
            "meta_synthesis_completed",
            growth_laws=len(growth_laws),
            sales_laws=len(sales_laws),
            archetypes=len(archetypes),
        )

        return {
            "growth_laws": growth_laws,
            "sales_laws": sales_laws,
            "archetypes": archetypes,
        }

    async def _extract_growth_laws(
        self,
        profiles: List[CompetitorProfile],
    ) -> List[GrowthLaw]:
        """
        Извлечь Growth Laws (prevalence ≥30%)

        Growth Law = паттерн, который повторяется у 30%+ конкурентов
        """
        if not profiles:
            return []

        total_competitors = len(profiles)
        threshold = 0.3  # 30% prevalence

        # Подсчитать prevalence для каждого паттерна
        pattern_counts = {}

        # 1. Acquisition channels
        for profile in profiles:
            for channel in profile.acquisition_channels:
                pattern_counts[f"acquisition:{channel}"] = pattern_counts.get(f"acquisition:{channel}", 0) + 1

        # 2. Conversion mechanisms
        for profile in profiles:
            if profile.conversion_mechanism:
                key = f"conversion:{profile.conversion_mechanism}"
                pattern_counts[key] = pattern_counts.get(key, 0) + 1

        # 3. Retention mechanisms
        for profile in profiles:
            if profile.retention_mechanism:
                key = f"retention:{profile.retention_mechanism}"
                pattern_counts[key] = pattern_counts.get(key, 0) + 1

        # 4. Moats
        for profile in profiles:
            for moat in profile.moats:
                pattern_counts[f"moat:{moat}"] = pattern_counts.get(f"moat:{moat}", 0) + 1

        # Извлечь Growth Laws (prevalence ≥ threshold)
        growth_laws = []
        for pattern, count in pattern_counts.items():
            prevalence = count / total_competitors
            if prevalence >= threshold:
                # Разобрать pattern
                category, description = pattern.split(":", 1)

                # Определить transferability
                transferability = Transferability.COPY
                if "unique" in description.lower() or "proprietary" in description.lower():
                    transferability = Transferability.IGNORE

                # Preconditions
                preconditions = []
                if category == "acquisition" and "SEO" in description:
                    preconditions = ["website with content", "technical SEO setup"]
                elif category == "acquisition" and "GMB" in description:
                    preconditions = ["physical location", "Google Business Profile"]
                elif category == "conversion" and "консультация" in description:
                    preconditions = ["booking system", "staff availability"]

                growth_laws.append(
                    GrowthLaw(
                        law=description,
                        prevalence=prevalence,
                        description=f"{int(prevalence * 100)}% конкурентов используют {description}",
                        transferability=transferability,
                        preconditions=preconditions,
                    )
                )

        # Сортировать по prevalence
        growth_laws.sort(key=lambda x: x.prevalence, reverse=True)

        logger.info("growth_laws_extracted", count=len(growth_laws))
        return growth_laws

    async def _extract_sales_laws(
        self,
        profiles: List[CompetitorProfile],
    ) -> List[SalesLaw]:
        """
        Извлечь Sales Laws

        Sales Law = паттерн продаж, который повторяется у 30%+ конкурентов
        """
        if not profiles:
            return []

        total_competitors = len(profiles)
        threshold = 0.3  # 30% prevalence

        # Подсчитать prevalence для sales patterns
        pattern_counts = {}

        # 1. Conversion mechanisms
        for profile in profiles:
            if profile.conversion_mechanism:
                pattern_counts[profile.conversion_mechanism] = pattern_counts.get(profile.conversion_mechanism, 0) + 1

        # 2. Pricing patterns (из ACV)
        price_ranges = {"low": 0, "medium": 0, "high": 0}
        for profile in profiles:
            if profile.acv:
                if profile.acv < 100000:
                    price_ranges["low"] += 1
                elif profile.acv < 200000:
                    price_ranges["medium"] += 1
                else:
                    price_ranges["high"] += 1

        # Добавить pricing patterns
        for range_name, count in price_ranges.items():
            if count > 0:
                pattern_counts[f"pricing:{range_name}"] = count

        # Извлечь Sales Laws
        sales_laws = []
        for pattern, count in pattern_counts.items():
            prevalence = count / total_competitors
            if prevalence >= threshold:
                # Определить transferability
                transferability = Transferability.COPY

                # Preconditions
                preconditions = []
                if "консультация" in pattern:
                    preconditions = ["booking system", "consultation process"]
                elif "pricing:high" in pattern:
                    preconditions = ["premium positioning", "quality proof"]

                sales_laws.append(
                    SalesLaw(
                        law=pattern,
                        prevalence=prevalence,
                        description=f"{int(prevalence * 100)}% конкурентов используют {pattern}",
                        transferability=transferability,
                        preconditions=preconditions,
                    )
                )

        # Сортировать по prevalence
        sales_laws.sort(key=lambda x: x.prevalence, reverse=True)

        logger.info("sales_laws_extracted", count=len(sales_laws))
        return sales_laws

    async def _define_archetypes(
        self,
        profiles: List[CompetitorProfile],
    ) -> List[Archetype]:
        """
        Определить архетипы конкурентов

        Archetype = кластер конкурентов с похожими growth mechanics
        """
        if not profiles:
            return []

        # Простая кластеризация по core motion
        clusters = {}

        for profile in profiles:
            # Определить кластер по ключевым словам в core_motion
            cluster_key = "Other"

            if profile.core_motion:
                if "SEO" in profile.core_motion or "поиск" in profile.core_motion:
                    cluster_key = "SEO-Driven"
                elif "рейтинг" in profile.core_motion or "отзыв" in profile.core_motion:
                    cluster_key = "Reputation-First"
                elif "премиум" in profile.core_motion or "premium" in profile.core_motion:
                    cluster_key = "Premium-Positioned"
                elif "реклама" in profile.core_motion or "ads" in profile.core_motion:
                    cluster_key = "Paid-Acquisition"

            if cluster_key not in clusters:
                clusters[cluster_key] = []
            clusters[cluster_key].append(profile)

        # Создать архетипы
        archetypes = []
        for name, members in clusters.items():
            if len(members) >= 2:  # Минимум 2 члена для архетипа
                # Извлечь общие характеристики
                characteristics = []

                # Общие acquisition channels
                common_channels = set(members[0].acquisition_channels)
                for member in members[1:]:
                    common_channels &= set(member.acquisition_channels)
                if common_channels:
                    characteristics.append(f"Channels: {', '.join(common_channels)}")

                # Средний ACV
                avg_acv = sum(m.acv for m in members if m.acv) / len([m for m in members if m.acv])
                if avg_acv:
                    characteristics.append(f"Avg ACV: {avg_acv:,.0f} RUB")

                # Общие moats
                all_moats = []
                for member in members:
                    all_moats.extend(member.moats)
                if all_moats:
                    from collections import Counter
                    common_moats = [moat for moat, count in Counter(all_moats).most_common(3)]
                    characteristics.append(f"Moats: {', '.join(common_moats)}")

                archetypes.append(
                    Archetype(
                        name=name,
                        members=[m.domain for m in members],
                        characteristics=characteristics,
                    )
                )

        logger.info("archetypes_defined", count=len(archetypes))
        return archetypes

    async def _application_layer(
        self,
        meta: Dict[str, Any],
        input_data: CIResearchInput,
    ) -> Dict[str, Any]:
        """
        Шаг 4: Application Layer

        Определяет transferability:
        - DO COPY (ICE scoring)
        - DON'T COPY (с обоснованием)
        - Sequencing Roadmap (фазы внедрения)
        """
        logger.info("application_layer_started")

        # Classify patterns (Copy/Adapt/Ignore)
        do_copy = await self._classify_copy_patterns(meta, input_data)
        dont_copy = await self._classify_ignore_patterns(meta, input_data)

        # Create sequencing roadmap
        roadmap = await self._create_sequencing_roadmap(do_copy)

        logger.info(
            "application_layer_completed",
            do_copy=len(do_copy),
            dont_copy=len(dont_copy),
            roadmap_phases=len(roadmap),
        )

        return {
            "do_copy": do_copy,
            "dont_copy": dont_copy,
            "sequencing_roadmap": roadmap,
        }

    async def _classify_copy_patterns(
        self,
        meta: Dict[str, Any],
        input_data: CIResearchInput,
    ) -> List[CopyPattern]:
        """
        Классифицировать паттерны для копирования с ICE scoring

        ICE = Impact × Confidence × Ease
        - Impact: 1-10 (насколько сильно повлияет на бизнес)
        - Confidence: 1-10 (насколько уверены что сработает)
        - Ease: 1-10 (насколько легко внедрить)
        """
        copy_patterns = []

        # Обработать Growth Laws
        for law in meta.get("growth_laws", []):
            if law.transferability == Transferability.COPY:
                # Проверить preconditions против client_context
                preconditions_met = True
                if law.preconditions and input_data.client_context:
                    # Простая проверка: если в goals есть упоминание precondition
                    goals_text = " ".join(input_data.client_context.goals).lower()
                    for precondition in law.preconditions:
                        if precondition.lower() not in goals_text:
                            preconditions_met = False
                            break

                # Рассчитать ICE score
                # Impact: высокий prevalence = высокий impact
                impact = int(law.prevalence * 10)

                # Confidence: высокий prevalence = высокая confidence
                confidence = int(law.prevalence * 10)

                # Ease: зависит от preconditions
                ease = 10 - len(law.preconditions) * 2 if law.preconditions else 10
                ease = max(1, ease)

                ice_score = impact * confidence * ease

                # Implementation guidance
                implementation = f"Внедрить {law.law}. "
                if law.preconditions:
                    implementation += f"Требуется: {', '.join(law.preconditions)}."

                copy_patterns.append(
                    CopyPattern(
                        pattern=law.law,
                        impact=impact,
                        confidence=confidence,
                        ease=ease,
                        ice_score=ice_score,
                        implementation=implementation,
                    )
                )

        # Обработать Sales Laws
        for law in meta.get("sales_laws", []):
            if law.transferability == Transferability.COPY:
                impact = int(law.prevalence * 10)
                confidence = int(law.prevalence * 10)
                ease = 10 - len(law.preconditions) * 2 if law.preconditions else 10
                ease = max(1, ease)
                ice_score = impact * confidence * ease

                implementation = f"Внедрить {law.law}. "
                if law.preconditions:
                    implementation += f"Требуется: {', '.join(law.preconditions)}."

                copy_patterns.append(
                    CopyPattern(
                        pattern=law.law,
                        impact=impact,
                        confidence=confidence,
                        ease=ease,
                        ice_score=ice_score,
                        implementation=implementation,
                    )
                )

        # Сортировать по ICE score
        copy_patterns.sort(key=lambda x: x.ice_score, reverse=True)

        logger.info("copy_patterns_classified", count=len(copy_patterns))
        return copy_patterns

    async def _classify_ignore_patterns(
        self,
        meta: Dict[str, Any],
        input_data: CIResearchInput,
    ) -> List[IgnorePattern]:
        """
        Классифицировать паттерны для игнорирования

        Игнорируем паттерны с:
        - Transferability = IGNORE
        - Unique advantages конкурентов
        """
        ignore_patterns = []

        # Обработать Growth Laws с IGNORE transferability
        for law in meta.get("growth_laws", []):
            if law.transferability == Transferability.IGNORE:
                reason = "Unique advantage конкурента, не переносится"
                alternative = "Найти собственное уникальное преимущество"

                ignore_patterns.append(
                    IgnorePattern(
                        pattern=law.law,
                        reason=reason,
                        alternative=alternative,
                    )
                )

        # Обработать Sales Laws с IGNORE transferability
        for law in meta.get("sales_laws", []):
            if law.transferability == Transferability.IGNORE:
                reason = "Специфично для конкурента"
                alternative = "Адаптировать под свой контекст"

                ignore_patterns.append(
                    IgnorePattern(
                        pattern=law.law,
                        reason=reason,
                        alternative=alternative,
                    )
                )

        logger.info("ignore_patterns_classified", count=len(ignore_patterns))
        return ignore_patterns

    async def _create_sequencing_roadmap(
        self,
        do_copy: List[CopyPattern],
    ) -> List[SequencingPhase]:
        """
        Создать roadmap внедрения паттернов

        Фазы:
        - Phase 1: Quick wins (ICE >400, 1-2 weeks)
        - Phase 2: Medium-term (ICE 200-400, 1-2 months)
        - Phase 3: Long-term (ICE <200, 3-6 months)
        """
        if not do_copy:
            return []

        # Разбить на фазы по ICE score
        phase1 = [p for p in do_copy if p.ice_score > 400]
        phase2 = [p for p in do_copy if 200 <= p.ice_score <= 400]
        phase3 = [p for p in do_copy if p.ice_score < 200]

        roadmap = []

        if phase1:
            roadmap.append(
                SequencingPhase(
                    phase=1,
                    duration="1-2 weeks",
                    patterns=[p.pattern for p in phase1],
                    expected_impact=f"Quick wins: {len(phase1)} паттернов с высоким ROI",
                )
            )

        if phase2:
            roadmap.append(
                SequencingPhase(
                    phase=2,
                    duration="1-2 months",
                    patterns=[p.pattern for p in phase2],
                    expected_impact=f"Medium-term: {len(phase2)} паттернов со средним ROI",
                )
            )

        if phase3:
            roadmap.append(
                SequencingPhase(
                    phase=3,
                    duration="3-6 months",
                    patterns=[p.pattern for p in phase3],
                    expected_impact=f"Long-term: {len(phase3)} паттернов с долгосрочным эффектом",
                )
            )

        logger.info("sequencing_roadmap_created", phases=len(roadmap))
        return roadmap

    async def _save_benchmark_report(
        self,
        input_data: CIResearchInput,
        competitors: List[CompetitorProfile],
        profiles: List[CompetitorProfile],
        meta: Dict[str, Any],
        application: Dict[str, Any],
    ) -> str:
        """
        Сохранить benchmark report в Obsidian vault

        Структура:
        - README.md (executive summary)
        - source-harvest/ (evidence archive)
        - synthesis/ (company memos)
        - meta-synthesis/ (laws, archetypes, matrix)
        - application/ (do-copy, roadmap, priorities)
        """
        # Создать директорию для отчёта
        date_str = datetime.now().strftime("%Y-%m-%d")
        industry_slug = input_data.industry.lower().replace(" ", "-")[:50]
        report_dir = f"wiki/ci-research/{date_str}-{industry_slug}"

        # TODO: Интеграция с Obsidian vault для создания структуры
        # Пока логируем путь

        # Создать executive summary
        summary = f"""# CI Research Report: {input_data.industry}

**Date:** {date_str}
**Competitors Analyzed:** {len(competitors)}
**Research Depth:** {input_data.research_depth}

## Key Findings

### Growth Laws ({len(meta.get('growth_laws', []))})
"""
        for law in meta.get('growth_laws', [])[:5]:
            summary += f"- **{law.law}** ({int(law.prevalence * 100)}% prevalence)\n"

        summary += f"\n### Sales Laws ({len(meta.get('sales_laws', []))})\n"
        for law in meta.get('sales_laws', [])[:5]:
            summary += f"- **{law.law}** ({int(law.prevalence * 100)}% prevalence)\n"

        summary += f"\n### Archetypes ({len(meta.get('archetypes', []))})\n"
        for archetype in meta.get('archetypes', []):
            summary += f"- **{archetype.name}** ({len(archetype.members)} members)\n"

        summary += f"\n## Recommendations\n\n### DO COPY ({len(application.get('do_copy', []))})\n"
        for pattern in application.get('do_copy', [])[:10]:
            summary += f"- **{pattern.pattern}** (ICE: {pattern.ice_score})\n"

        summary += f"\n### DON'T COPY ({len(application.get('dont_copy', []))})\n"
        for pattern in application.get('dont_copy', [])[:5]:
            summary += f"- **{pattern.pattern}** - {pattern.reason}\n"

        summary += f"\n## Implementation Roadmap\n\n"
        for phase in application.get('sequencing_roadmap', []):
            summary += f"### Phase {phase.phase}: {phase.duration}\n"
            summary += f"**Impact:** {phase.expected_impact}\n\n"
            for pattern in phase.patterns[:5]:
                summary += f"- {pattern}\n"
            summary += "\n"

        # Логировать summary (в будущем сохранить в Obsidian)
        logger.info(
            "benchmark_report_created",
            path=report_dir,
            summary_length=len(summary),
        )

        return report_dir

    def _calculate_evidence_quality(
        self,
        competitors: List[CompetitorProfile],
    ) -> float:
        """
        Рассчитать Evidence Quality Score

        Formula: (Tier1 × 3 + Tier2 × 2 + Tier3 × 1) / Total
        Target: >2.0
        """
        tier1_count = 0
        tier2_count = 0
        tier3_count = 0

        for competitor in competitors:
            for source in competitor.sources:
                if source.tier == 1:
                    tier1_count += 1
                elif source.tier == 2:
                    tier2_count += 1
                elif source.tier == 3:
                    tier3_count += 1

        total = tier1_count + tier2_count + tier3_count
        if total == 0:
            return 0.0

        score = (tier1_count * 3 + tier2_count * 2 + tier3_count * 1) / total
        return round(score, 2)

    def _calculate_api_cost(self, competitor_count: int) -> float:
        """
        Рассчитать стоимость API calls

        Cost per competitor:
        - SimilarWeb: $0.25
        - Ahrefs: $0.40
        - SEMrush: $0.25
        - Crunchbase: $0.10
        - HealthGrades/Zocdoc: $0.15
        Total: ~$1.15 per competitor
        """
        cost_per_competitor = 1.15
        return round(competitor_count * cost_per_competitor, 2)

    def get_capabilities(self) -> List[str]:
        """Возвращает список capabilities агента"""
        return [
            "competitor_intelligence",
            "reverse_engineering",
            "growth_machine_analysis",
            "pattern_extraction",
            "transferability_analysis",
            "medical_marketing_ci",
        ]

    async def close(self) -> None:
        """Закрыть HTTP client"""
        await self.http_client.aclose()
