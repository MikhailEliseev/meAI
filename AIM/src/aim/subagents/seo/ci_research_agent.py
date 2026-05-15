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
        """Найти конкурентов через SEMrush Competitor Discovery API"""
        # TODO: Реализовать через SEMrush API
        # Пока возвращаем заглушку
        logger.warning("competitor_discovery_not_implemented", using_mock=True)
        return []

    async def _collect_primary_sources(self, domain: str) -> List[Source]:
        """Собрать Tier 1 sources (founder interviews, operator posts, case studies)"""
        sources = []

        # TODO: Реализовать сбор через:
        # - Google/Yandex search: "founder interview" + domain
        # - LinkedIn API: operator posts
        # - Website scraping: case studies
        # - YouTube API: product demos
        # - HealthGrades/Zocdoc API: testimonials

        logger.debug("primary_sources_collected", domain=domain, count=len(sources))
        return sources

    async def _collect_secondary_sources(self, domain: str) -> List[Source]:
        """Собрать Tier 2 sources (industry reports, news articles)"""
        sources = []

        # TODO: Реализовать сбор через:
        # - Google Scholar API: industry reports
        # - Google News API: news articles
        # - YouTube API: conference talks

        logger.debug("secondary_sources_collected", domain=domain, count=len(sources))
        return sources

    async def _collect_tertiary_sources(self, domain: str) -> List[Source]:
        """Собрать Tier 3 sources (Wikipedia, generic blogs)"""
        sources = []

        # TODO: Реализовать сбор через:
        # - Wikipedia API
        # - Generic blog search

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
        """Извлечь Growth Machine (AARRR framework)"""
        # TODO: Реализовать извлечение через LLM:
        # - Initial wedge (с чего начали)
        # - Acquisition (как привлекают)
        # - Activation (как конвертируют)
        # - Retention (как удерживают)
        # - Revenue (как монетизируют)
        # - Referral (как масштабируют)
        pass

    async def _estimate_unit_economics(self, profile: CompetitorProfile) -> None:
        """Оценить Unit Economics"""
        # TODO: Реализовать оценку через LLM:
        # - ACV (из pricing page или inference)
        # - CAC (из ad spend estimates)
        # - LTV (calculated from ACV × retention)
        # - Payback period (CAC / monthly revenue)
        pass

    async def _analyze_competitive_advantage(self, profile: CompetitorProfile) -> None:
        """Проанализировать конкурентное преимущество"""
        # TODO: Реализовать анализ через LLM:
        # - Core motion (как они выигрывают)
        # - Moats (network effects, switching costs, brand, proprietary tech)
        # - Risks (dependencies, competitive threats, operational risks)
        pass

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
        """Извлечь Growth Laws (prevalence ≥30%)"""
        # TODO: Реализовать извлечение через LLM:
        # - Подсчитать prevalence для каждого паттерна
        # - Если prevalence ≥30% → это Growth Law
        # - Документировать preconditions и boundary conditions
        return []

    async def _extract_sales_laws(
        self,
        profiles: List[CompetitorProfile],
    ) -> List[SalesLaw]:
        """Извлечь Sales Laws"""
        # TODO: Реализовать извлечение через LLM
        return []

    async def _define_archetypes(
        self,
        profiles: List[CompetitorProfile],
    ) -> List[Archetype]:
        """Определить архетипы конкурентов"""
        # TODO: Реализовать кластеризацию через LLM:
        # - Идентифицировать 2-5 distinct clusters
        # - Для каждого archetype: name, members, characteristics
        return []

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
        """Классифицировать паттерны для копирования с ICE scoring"""
        # TODO: Реализовать через LLM:
        # - Проверить preconditions против client_context
        # - Рассчитать ICE score (Impact × Confidence × Ease)
        # - Ранжировать по ICE score
        return []

    async def _classify_ignore_patterns(
        self,
        meta: Dict[str, Any],
        input_data: CIResearchInput,
    ) -> List[IgnorePattern]:
        """Классифицировать паттерны для игнорирования"""
        # TODO: Реализовать через LLM:
        # - Определить паттерны с low transferability
        # - Документировать reason и alternative
        return []

    async def _create_sequencing_roadmap(
        self,
        do_copy: List[CopyPattern],
    ) -> List[SequencingPhase]:
        """Создать roadmap внедрения паттернов"""
        # TODO: Реализовать через LLM:
        # - Phase 1: Quick wins (ICE >150, 1-2 weeks)
        # - Phase 2: Medium-term (ICE 100-150, 1-2 months)
        # - Phase 3: Long-term (ICE <100, 3-6 months)
        return []

    async def _save_benchmark_report(
        self,
        input_data: CIResearchInput,
        competitors: List[CompetitorProfile],
        profiles: List[CompetitorProfile],
        meta: Dict[str, Any],
        application: Dict[str, Any],
    ) -> str:
        """Сохранить benchmark report в Obsidian vault"""
        # Создать директорию для отчёта
        date_str = datetime.now().strftime("%Y-%m-%d")
        industry_slug = input_data.industry.lower().replace(" ", "-")
        report_dir = f"wiki/ci-research/{date_str}-{industry_slug}"

        # TODO: Создать структуру отчёта:
        # - README.md (executive summary)
        # - source-harvest/ (evidence archive)
        # - synthesis/ (company memos)
        # - meta-synthesis/ (laws, archetypes, matrix)
        # - application/ (do-copy, roadmap, priorities)

        logger.info("benchmark_report_saved", path=report_dir)
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
