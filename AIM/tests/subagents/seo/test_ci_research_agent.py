"""
Tests for CI Research Agent
"""

import pytest
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

from src.aim.subagents.seo.ci_research_agent import (
    CIResearchAgent,
    CIResearchInput,
    ClientContext,
    ResearchDepth,
    CompetitorProfile,
    Source,
    GrowthLaw,
    SalesLaw,
    Archetype,
    CopyPattern,
    IgnorePattern,
    SequencingPhase,
    Transferability,
)


# ============================================================================
# Fixtures
# ============================================================================

@pytest.fixture
def mock_event_bus():
    """Mock Event Bus"""
    return AsyncMock()


@pytest.fixture
def mock_obsidian_vault():
    """Mock Obsidian Vault"""
    return MagicMock()


@pytest.fixture
def api_keys():
    """Mock API keys"""
    return {
        "similarweb": "test_key",
        "ahrefs": "test_key",
        "semrush": "test_key",
        "crunchbase": "test_key",
        "healthgrades": "test_key",
        "zocdoc": "test_key",
    }


@pytest.fixture
def ci_agent(mock_event_bus, mock_obsidian_vault, api_keys):
    """CI Research Agent instance"""
    return CIResearchAgent(
        agent_id="ci-research-agent",
        event_bus=mock_event_bus,
        obsidian_vault=mock_obsidian_vault,
        api_keys=api_keys,
        database_url="sqlite+aiosqlite:///:memory:",
    )


@pytest.fixture
def valid_input():
    """Valid input data"""
    return {
        "payload": {
            "industry": "стоматология Москва",
            "client_context": {
                "positioning": "премиум имплантация",
                "budget": 500000,
                "goals": ["увеличить трафик на 50%", "снизить CAC на 30%"],
            },
            "research_depth": "tier2",
            "focus_areas": ["growth", "trust", "local_seo"],
            "max_competitors": 5,
        }
    }


@pytest.fixture
def mock_competitor_profile():
    """Mock competitor profile"""
    profile = CompetitorProfile(
        domain="competitor1.ru",
        name="Competitor 1",
    )

    # Add sources
    profile.sources = [
        Source(
            url="https://competitor1.ru/about",
            title="About Us",
            tier=1,
            content="Founder interview content",
        ),
        Source(
            url="https://news.ru/competitor1",
            title="News Article",
            tier=2,
            content="News content",
        ),
    ]

    # Growth Machine
    profile.initial_wedge = "Премиум имплантация в Москве"
    profile.acquisition_channels = ["SEO", "GMB", "Instagram"]
    profile.conversion_mechanism = "Бесплатная консультация"
    profile.retention_mechanism = "Программа лояльности"
    profile.expansion_mechanism = "Upsell дополнительных услуг"

    # Unit Economics
    profile.acv = 150000.0
    profile.cac = 15000.0
    profile.ltv = 300000.0
    profile.payback_period = 6

    # Competitive Advantage
    profile.core_motion = "Доминируют в локальном SEO через 4.8★ GMB"
    profile.moats = ["Brand reputation", "Review volume"]
    profile.risks = ["Dependency on Google", "Price competition"]

    return profile


# ============================================================================
# Unit Tests: Input Validation
# ============================================================================

def test_validate_input_valid(valid_input):
    """Корректные данные проходят валидацию"""
    input_data = CIResearchInput(**valid_input["payload"])
    assert input_data.industry == "стоматология Москва"
    assert input_data.research_depth == ResearchDepth.TIER2
    assert input_data.max_competitors == 5


def test_validate_input_missing_industry():
    """Ошибка если industry отсутствует"""
    with pytest.raises(ValueError, match="industry"):
        CIResearchInput(
            industry="",
            client_context=ClientContext(
                positioning="test",
                budget=100000,
                goals=["goal1"],
            ),
        )


def test_validate_input_invalid_research_depth():
    """Ошибка если research_depth невалиден"""
    with pytest.raises(ValueError):
        CIResearchInput(
            industry="test",
            client_context=ClientContext(
                positioning="test",
                budget=100000,
                goals=["goal1"],
            ),
            research_depth="invalid_tier",
        )


def test_validate_input_max_competitors_out_of_range():
    """Ошибка если max_competitors < 1 или > 50"""
    with pytest.raises(ValueError):
        CIResearchInput(
            industry="test",
            client_context=ClientContext(
                positioning="test",
                budget=100000,
                goals=["goal1"],
            ),
            max_competitors=0,
        )

    with pytest.raises(ValueError):
        CIResearchInput(
            industry="test",
            client_context=ClientContext(
                positioning="test",
                budget=100000,
                goals=["goal1"],
            ),
            max_competitors=51,
        )


# ============================================================================
# Unit Tests: Evidence Quality Calculation
# ============================================================================

def test_calculate_evidence_quality_all_tier1(ci_agent):
    """Evidence quality = 3.0 если все Tier 1"""
    competitors = [
        CompetitorProfile(
            domain="test.ru",
            name="Test",
            sources=[
                Source(url="url1", title="t1", tier=1, content="c1"),
                Source(url="url2", title="t2", tier=1, content="c2"),
            ],
        )
    ]

    score = ci_agent._calculate_evidence_quality(competitors)
    assert score == 3.0


def test_calculate_evidence_quality_mixed(ci_agent):
    """Evidence quality рассчитывается правильно для mixed tiers"""
    competitors = [
        CompetitorProfile(
            domain="test.ru",
            name="Test",
            sources=[
                Source(url="url1", title="t1", tier=1, content="c1"),  # 3 points
                Source(url="url2", title="t2", tier=2, content="c2"),  # 2 points
                Source(url="url3", title="t3", tier=3, content="c3"),  # 1 point
            ],
        )
    ]

    # (3 + 2 + 1) / 3 = 2.0
    score = ci_agent._calculate_evidence_quality(competitors)
    assert score == 2.0


def test_calculate_evidence_quality_empty(ci_agent):
    """Evidence quality = 0.0 если нет источников"""
    competitors = [CompetitorProfile(domain="test.ru", name="Test")]
    score = ci_agent._calculate_evidence_quality(competitors)
    assert score == 0.0


# ============================================================================
# Unit Tests: API Cost Calculation
# ============================================================================

def test_calculate_api_cost(ci_agent):
    """API cost рассчитывается правильно"""
    # $1.15 per competitor
    assert ci_agent._calculate_api_cost(1) == 1.15
    assert ci_agent._calculate_api_cost(5) == 5.75
    assert ci_agent._calculate_api_cost(10) == 11.50


# ============================================================================
# Unit Tests: ICE Score Calculation
# ============================================================================

def test_ice_score_calculation():
    """ICE score = Impact × Confidence × Ease"""
    pattern = CopyPattern(
        pattern="Test pattern",
        impact=8,
        confidence=9,
        ease=7,
        ice_score=0,  # Will be calculated
        implementation="Test implementation",
    )

    assert pattern.ice_score == 8 * 9 * 7  # 504


# ============================================================================
# Integration Tests: Execute Task
# ============================================================================

@pytest.mark.asyncio
async def test_execute_task_invalid_input(ci_agent):
    """Возвращает failure при невалидных данных"""
    task = {
        "payload": {
            "industry": "",  # Invalid: empty
            "client_context": {
                "positioning": "test",
                "budget": 100000,
                "goals": ["goal1"],
            },
        }
    }

    result = await ci_agent.execute_task(task)

    assert result["status"] == "failure"
    assert result["result"] is None
    assert len(result["errors"]) > 0
    assert result["errors"][0]["code"] == "INVALID_INPUT"


@pytest.mark.asyncio
async def test_execute_task_success_mock(ci_agent, valid_input, mock_competitor_profile):
    """Успешное выполнение с mock данными"""
    # Mock методы
    ci_agent._source_harvest = AsyncMock(return_value=[mock_competitor_profile])
    ci_agent._company_synthesis = AsyncMock(return_value=[mock_competitor_profile])
    ci_agent._meta_synthesis = AsyncMock(return_value={
        "growth_laws": [
            GrowthLaw(
                law="Niche-first wedge",
                prevalence=0.8,
                description="80% начали с ниши",
                transferability=Transferability.COPY,
                preconditions=["clear niche"],
            )
        ],
        "sales_laws": [],
        "archetypes": [],
    })
    ci_agent._application_layer = AsyncMock(return_value={
        "do_copy": [
            CopyPattern(
                pattern="GMB optimization",
                impact=9,
                confidence=10,
                ease=8,
                ice_score=720,
                implementation="Optimize GMB profile",
            )
        ],
        "dont_copy": [],
        "sequencing_roadmap": [],
    })
    ci_agent._save_benchmark_report = AsyncMock(
        return_value="wiki/ci-research/2026-05-15-test"
    )

    result = await ci_agent.execute_task(valid_input)

    assert result["status"] == "success"
    assert result["result"]["competitors_analyzed"] == 1
    assert len(result["result"]["growth_laws"]) == 1
    assert len(result["result"]["do_copy"]) == 1
    assert result["metrics"]["evidence_quality_score"] == 2.5  # (1*3 + 1*2) / 2


# ============================================================================
# Unit Tests: Capabilities
# ============================================================================

def test_get_capabilities(ci_agent):
    """Возвращает список capabilities"""
    capabilities = ci_agent.get_capabilities()

    assert "competitor_intelligence" in capabilities
    assert "reverse_engineering" in capabilities
    assert "growth_machine_analysis" in capabilities
    assert "pattern_extraction" in capabilities
    assert "transferability_analysis" in capabilities
    assert "medical_marketing_ci" in capabilities


# ============================================================================
# Unit Tests: Data Models
# ============================================================================

def test_growth_law_model():
    """GrowthLaw model валидация"""
    law = GrowthLaw(
        law="Test law",
        prevalence=0.8,
        description="Test description",
        transferability=Transferability.COPY,
        preconditions=["precondition1"],
    )

    assert law.law == "Test law"
    assert law.prevalence == 0.8
    assert law.transferability == Transferability.COPY


def test_sales_law_model():
    """SalesLaw model валидация"""
    law = SalesLaw(
        law="Test law",
        prevalence=0.6,
        description="Test description",
        transferability=Transferability.ADAPT,
        preconditions=["precondition1"],
    )

    assert law.law == "Test law"
    assert law.prevalence == 0.6
    assert law.transferability == Transferability.ADAPT


def test_archetype_model():
    """Archetype model валидация"""
    archetype = Archetype(
        name="Test Archetype",
        members=["competitor1.ru", "competitor2.ru"],
        characteristics=["char1", "char2"],
    )

    assert archetype.name == "Test Archetype"
    assert len(archetype.members) == 2
    assert len(archetype.characteristics) == 2


def test_copy_pattern_model():
    """CopyPattern model валидация"""
    pattern = CopyPattern(
        pattern="Test pattern",
        impact=8,
        confidence=9,
        ease=7,
        ice_score=504,
        implementation="Test implementation",
    )

    assert pattern.pattern == "Test pattern"
    assert pattern.ice_score == 504


def test_ignore_pattern_model():
    """IgnorePattern model валидация"""
    pattern = IgnorePattern(
        pattern="Test pattern",
        reason="Test reason",
        alternative="Test alternative",
    )

    assert pattern.pattern == "Test pattern"
    assert pattern.reason == "Test reason"


def test_sequencing_phase_model():
    """SequencingPhase model валидация"""
    phase = SequencingPhase(
        phase=1,
        duration="1-2 weeks",
        patterns=["pattern1", "pattern2"],
        expected_impact="Test impact",
    )

    assert phase.phase == 1
    assert phase.duration == "1-2 weeks"
    assert len(phase.patterns) == 2


# ============================================================================
# Unit Tests: Competitor Profile
# ============================================================================

def test_competitor_profile_creation():
    """CompetitorProfile создаётся правильно"""
    profile = CompetitorProfile(
        domain="test.ru",
        name="Test Competitor",
    )

    assert profile.domain == "test.ru"
    assert profile.name == "Test Competitor"
    assert len(profile.sources) == 0
    assert profile.initial_wedge is None


def test_competitor_profile_with_sources():
    """CompetitorProfile с источниками"""
    profile = CompetitorProfile(
        domain="test.ru",
        name="Test",
    )

    profile.sources.append(
        Source(
            url="https://test.ru",
            title="Test Source",
            tier=1,
            content="Test content",
        )
    )

    assert len(profile.sources) == 1
    assert profile.sources[0].tier == 1


def test_competitor_profile_with_growth_machine():
    """CompetitorProfile с Growth Machine"""
    profile = CompetitorProfile(
        domain="test.ru",
        name="Test",
    )

    profile.initial_wedge = "Test wedge"
    profile.acquisition_channels = ["SEO", "PPC"]
    profile.conversion_mechanism = "Free consultation"

    assert profile.initial_wedge == "Test wedge"
    assert len(profile.acquisition_channels) == 2


def test_competitor_profile_with_unit_economics():
    """CompetitorProfile с Unit Economics"""
    profile = CompetitorProfile(
        domain="test.ru",
        name="Test",
    )

    profile.acv = 100000.0
    profile.cac = 10000.0
    profile.ltv = 200000.0
    profile.payback_period = 6

    assert profile.acv == 100000.0
    assert profile.payback_period == 6


# ============================================================================
# Cleanup
# ============================================================================

@pytest.mark.asyncio
async def test_close(ci_agent):
    """HTTP client закрывается правильно"""
    await ci_agent.close()
    # No assertion needed, just verify no exception
