"""Tests for Ads Magister V2."""

import pytest
from datetime import datetime

from AIM.src.aim.magisters.ads_magister_v2 import (
    AdsMagisterV2,
    AdsWorkflowReport,
)
from AIM.src.aim.subagents.ads.ad_copy_generator import (
    AdCopySet,
    AdCopyVariant,
    AdHeadline,
    AdDescription,
    CallToAction,
    ComplianceCheck,
)
from AIM.src.aim.subagents.ads.landing_page_analyzer import (
    LandingPageReport,
    RelevanceAnalysis,
    ConversionOptimization,
    UserExperience,
    MobileOptimization,
    PerformanceAnalysis,
)
from AIM.src.aim.subagents.ads.bid_strategy_optimizer import (
    BidOptimizationReport,
    PerformanceMetrics,
    BidStrategyAnalysis,
    BudgetAnalysis,
    BidAdjustments,
    CompetitorAnalysis,
)


@pytest.fixture
def magister():
    """Create Ads Magister V2 instance."""
    return AdsMagisterV2()


@pytest.fixture
def sample_ad_copy():
    """Sample ad copy set."""
    compliance = ComplianceCheck(
        platform="yandex",
        is_compliant=True,
        violations=[],
        warnings=[],
    )

    variant1 = AdCopyVariant(
        variant_id=1,
        headline="Зубные имплантаты - Установка за 1 день",
        description="Пожизненная гарантия. Безболезненная процедура. Узнайте больше.",
        cta="Заказать сейчас",
        platform="yandex",
        compliance=compliance,
    )

    variant2 = AdCopyVariant(
        variant_id=2,
        headline="Ищете зубные имплантаты?",
        description="Имплантаты Nobel Biocare для зубные имплантаты. Быстрая доставка.",
        cta="Узнать больше",
        platform="yandex",
        compliance=compliance,
    )

    return AdCopySet(
        target_keyword="зубные имплантаты",
        timestamp=datetime.now().isoformat(),
        variants=[variant1, variant2],
        total_variants=2,
        headlines=[
            AdHeadline(
                text="Зубные имплантаты - Установка за 1 день",
                length=40,
                variant_type="benefit",
            )
        ],
        total_headlines=1,
        descriptions=[
            AdDescription(
                text="Пожизненная гарантия. Безболезненная процедура.",
                length=50,
                includes_cta=False,
                cta_text=None,
            )
        ],
        total_descriptions=1,
        ctas=[
            CallToAction(
                text="Заказать сейчас",
                urgency_level="high",
                action_type="buy",
            )
        ],
        total_ctas=1,
        yandex_variants=[variant1, variant2],
        google_variants=[],
    )


@pytest.fixture
def sample_landing_page_report():
    """Sample landing page report."""
    return LandingPageReport(
        url="https://example.com/dental-implants",
        timestamp=datetime.now().isoformat(),
        relevance=RelevanceAnalysis(
            keyword_match_score=80.0,
            headline_relevance=100.0,
            content_relevance=100.0,
            cta_alignment=100.0,
            overall_relevance=90.0,
            issues=[],
            recommendations=[],
        ),
        conversion=ConversionOptimization(
            cta_count=2,
            cta_visibility=100.0,
            form_complexity="simple",
            form_fields_count=2,
            trust_signals=["Security badge", "Certification"],
            urgency_elements=["Act now"],
            social_proof=["Star ratings", "Customer reviews"],
            conversion_score=85.0,
            recommendations=[],
        ),
        ux=UserExperience(
            navigation_clarity=100.0,
            content_readability=85.0,
            visual_hierarchy=100.0,
            distraction_score=0.0,
            ux_score=92.5,
            issues=[],
            recommendations=[],
        ),
        mobile=MobileOptimization(
            is_mobile_friendly=True,
            viewport_configured=True,
            touch_targets_adequate=True,
            text_readable=True,
            mobile_score=100.0,
            issues=[],
            recommendations=[],
        ),
        performance=PerformanceAnalysis(
            load_time=2.5,
            page_size=850.0,
            requests_count=25,
            performance_score=85.0,
            issues=[],
            recommendations=[],
        ),
        overall_quality_score=88.5,
        quality_rating="excellent",
        priority_issues=[],
        quick_wins=["Add second CTA button (5 min)"],
    )


@pytest.fixture
def sample_bid_optimization_report():
    """Sample bid optimization report."""
    return BidOptimizationReport(
        campaign_id="campaign-001",
        campaign_name="Dental Implants Campaign",
        platform="yandex",
        timestamp=datetime.now().isoformat(),
        performance=PerformanceMetrics(
            impressions=10000,
            clicks=500,
            conversions=50,
            cost=25000.0,
            revenue=150000.0,
            ctr=5.0,
            cpc=50.0,
            cpa=500.0,
            roas=6.0,
            conversion_rate=10.0,
        ),
        strategy=BidStrategyAnalysis(
            current_strategy="manual",
            strategy_performance=90.0,
            is_optimal=False,
            recommended_strategy="target_roas",
            expected_improvement=15.0,
            confidence=80.0,
            reasons=["Excellent ROAS: 6.0", "High conversion rate: 10.0%"],
            warnings=[],
        ),
        budget=BudgetAnalysis(
            daily_budget=5000.0,
            spent_today=4800.0,
            utilization_rate=96.0,
            is_limited=True,
            recommended_budget=7500.0,
            budget_efficiency=80.0,
            recommendations=["Budget limited. Increase to 7500 RUB"],
        ),
        adjustments=BidAdjustments(
            device_adjustments={"desktop": 20.0, "mobile": 0.0, "tablet": -20.0},
            location_adjustments={"moscow": 30.0, "spb": 0.0, "other": -30.0},
            time_adjustments={"9-12": 25.0, "12-15": 0.0, "15-18": -25.0},
            audience_adjustments={"remarketing": 50.0, "similar": 20.0, "cold": 0.0},
            overall_impact=10.0,
        ),
        competitors=CompetitorAnalysis(
            avg_position=3.5,
            impression_share=65.0,
            lost_impression_share_rank=20.0,
            lost_impression_share_budget=15.0,
            competitive_intensity="medium",
            recommended_actions=["Improve position from 3.5 to top 3"],
        ),
        optimization_score=82.0,
        priority_actions=[
            "CRITICAL: Switch to target_roas (+15.0% expected)",
            "HIGH: Budget limited. Increase to 7500 RUB",
        ],
        quick_wins=[
            "Adjust desktop bids by +20% (5 min)",
            "Adjust mobile bids by +0% (5 min)",
        ],
    )


@pytest.mark.asyncio
async def test_calculate_overall_score_all_phases(
    magister, sample_ad_copy, sample_landing_page_report, sample_bid_optimization_report
):
    """Test overall score calculation with all phases."""
    score = magister._calculate_overall_score(
        sample_ad_copy,
        sample_landing_page_report,
        sample_bid_optimization_report,
    )

    # Ad copy: 2/2 compliant = 100 (40% weight = 40.0)
    # Landing page: 88.5 (30% weight = 26.55)
    # Bid optimization: 82.0 (30% weight = 24.6)
    # Total: 40.0 + 26.55 + 24.6 = 91.15
    assert 90.0 <= score <= 92.0


@pytest.mark.asyncio
async def test_calculate_overall_score_without_landing_page(
    magister, sample_ad_copy, sample_bid_optimization_report
):
    """Test overall score calculation without landing page."""
    score = magister._calculate_overall_score(
        sample_ad_copy,
        None,
        sample_bid_optimization_report,
    )

    # Ad copy: 100 (60% weight = 60.0)
    # Bid optimization: 82.0 (40% weight = 32.8)
    # Total: 60.0 + 32.8 = 92.8
    assert 92.0 <= score <= 93.0


@pytest.mark.asyncio
async def test_calculate_overall_score_without_bid_optimization(
    magister, sample_ad_copy, sample_landing_page_report
):
    """Test overall score calculation without bid optimization."""
    score = magister._calculate_overall_score(
        sample_ad_copy,
        sample_landing_page_report,
        None,
    )

    # Ad copy: 100 (60% weight = 60.0)
    # Landing page: 88.5 (40% weight = 35.4)
    # Total: 60.0 + 35.4 = 95.4
    assert 95.0 <= score <= 96.0


@pytest.mark.asyncio
async def test_calculate_overall_score_ad_copy_only(magister, sample_ad_copy):
    """Test overall score calculation with ad copy only."""
    score = magister._calculate_overall_score(
        sample_ad_copy,
        None,
        None,
    )

    # Ad copy: 2/2 compliant = 100
    assert score == 100.0


@pytest.mark.asyncio
async def test_generate_priority_actions(
    magister,
    sample_ad_copy,
    sample_landing_page_report,
    sample_bid_optimization_report,
):
    """Test priority actions generation."""
    actions = magister._generate_priority_actions(
        sample_ad_copy,
        sample_landing_page_report,
        sample_bid_optimization_report,
    )

    assert isinstance(actions, list)
    assert len(actions) <= 5
    # Should include bid optimization action
    assert any("target_roas" in action.lower() for action in actions)
    # Should include quick win
    assert any("quick win" in action.lower() for action in actions)


@pytest.mark.asyncio
async def test_estimate_impact_high(magister):
    """Test impact estimation for low score."""
    impact = magister._estimate_impact(40.0, None, None)
    assert impact == "high"


@pytest.mark.asyncio
async def test_estimate_impact_medium(magister):
    """Test impact estimation for medium score."""
    impact = magister._estimate_impact(60.0, None, None)
    assert impact == "medium"


@pytest.mark.asyncio
async def test_estimate_impact_low(magister):
    """Test impact estimation for high score."""
    impact = magister._estimate_impact(85.0, None, None)
    assert impact == "low"


@pytest.mark.asyncio
async def test_estimate_impact_with_strategy_change(
    magister, sample_landing_page_report, sample_bid_optimization_report
):
    """Test impact estimation with strategy change opportunity."""
    # Medium score but high improvement potential from strategy change
    impact = magister._estimate_impact(
        60.0,
        sample_landing_page_report,
        sample_bid_optimization_report,
    )
    # Should upgrade from medium to high due to strategy change
    assert impact == "high"


@pytest.mark.asyncio
async def test_execute_workflow_structure(magister):
    """Test workflow execution returns correct structure."""
    report = await magister.execute_workflow(
        campaign_name="Test Campaign",
        target_keyword="зубные имплантаты",
        product_name="Имплантаты Nobel Biocare",
        benefits=["Пожизненная гарантия", "Установка за 1 день"],
        platform="yandex",
    )

    assert isinstance(report, AdsWorkflowReport)
    assert report.campaign_name == "Test Campaign"
    assert isinstance(report.generated_at, str)
    assert isinstance(report.duration_seconds, float)
    assert isinstance(report.ad_copy, AdCopySet)
    assert report.landing_page is None  # No URL provided
    assert report.bid_optimization is None  # No campaign_id provided
    assert 0 <= report.overall_score <= 100
    assert isinstance(report.priority_actions, list)
    assert report.estimated_impact in ["high", "medium", "low"]
    assert report.workflow_status in ["success", "partial", "failed"]
    assert isinstance(report.errors, list)


@pytest.mark.asyncio
async def test_execute_ad_copy_generation_only(magister):
    """Test executing only ad copy generation phase."""
    ad_copy = await magister.execute_ad_copy_generation_only(
        target_keyword="зубные имплантаты",
        product_name="Имплантаты Nobel Biocare",
        benefits=["Пожизненная гарантия", "Установка за 1 день"],
        platform="yandex",
    )

    assert isinstance(ad_copy, AdCopySet)
    assert ad_copy.target_keyword == "зубные имплантаты"
    assert ad_copy.total_variants > 0


@pytest.mark.asyncio
async def test_execute_landing_page_analysis_only(magister):
    """Test executing only landing page analysis phase."""
    report = await magister.execute_landing_page_analysis_only(
        url="https://example.com/dental-implants",
        ad_keyword="зубные имплантаты",
    )

    assert isinstance(report, LandingPageReport)
    assert report.url == "https://example.com/dental-implants"
    assert 0 <= report.overall_quality_score <= 100


@pytest.mark.asyncio
async def test_execute_bid_optimization_only(magister):
    """Test executing only bid optimization phase."""
    report = await magister.execute_bid_optimization_only(
        campaign_id="campaign-001",
        campaign_name="Test Campaign",
        platform="yandex",
    )

    assert isinstance(report, BidOptimizationReport)
    assert report.campaign_id == "campaign-001"
    assert 0 <= report.optimization_score <= 100


@pytest.mark.asyncio
async def test_workflow_with_errors_partial_status(magister, monkeypatch):
    """Test workflow continues with partial status when one phase fails."""

    # Mock ad copy generator to raise exception
    async def mock_generate(*args, **kwargs):
        raise Exception("API error")

    monkeypatch.setattr(magister.ad_copy_generator, "generate", mock_generate)

    report = await magister.execute_workflow(
        campaign_name="Test Campaign",
        target_keyword="зубные имплантаты",
        product_name="Имплантаты Nobel Biocare",
        benefits=["Пожизненная гарантия"],
        platform="yandex",
    )

    assert report.workflow_status == "partial"
    assert len(report.errors) > 0
    assert any("Ad Copy Generation failed" in error for error in report.errors)


@pytest.mark.asyncio
async def test_workflow_priority_actions_limit(
    magister, sample_ad_copy, sample_landing_page_report, sample_bid_optimization_report
):
    """Test priority actions are limited to top 5."""
    # Create landing page report with many issues
    landing_page_with_many_issues = LandingPageReport(
        url="https://example.com",
        timestamp=datetime.now().isoformat(),
        relevance=sample_landing_page_report.relevance,
        conversion=sample_landing_page_report.conversion,
        ux=sample_landing_page_report.ux,
        mobile=sample_landing_page_report.mobile,
        performance=sample_landing_page_report.performance,
        overall_quality_score=50.0,
        quality_rating="fair",
        priority_issues=[f"Issue {i}" for i in range(10)],  # 10 issues
        quick_wins=[],
    )

    actions = magister._generate_priority_actions(
        sample_ad_copy,
        landing_page_with_many_issues,
        sample_bid_optimization_report,
    )

    assert len(actions) <= 5


@pytest.mark.asyncio
async def test_workflow_with_non_compliant_ad_copy(magister):
    """Test workflow handles non-compliant ad copy."""
    # Create ad copy with violations
    non_compliant = ComplianceCheck(
        platform="yandex",
        is_compliant=False,
        violations=["Запрещённое слово: 'лучший'"],
        warnings=[],
    )

    variant = AdCopyVariant(
        variant_id=1,
        headline="Лучшие зубные имплантаты",
        description="Самые качественные имплантаты",
        cta="Заказать",
        platform="yandex",
        compliance=non_compliant,
    )

    ad_copy = AdCopySet(
        target_keyword="зубные имплантаты",
        timestamp=datetime.now().isoformat(),
        variants=[variant],
        total_variants=1,
        headlines=[],
        total_headlines=0,
        descriptions=[],
        total_descriptions=0,
        ctas=[],
        total_ctas=0,
        yandex_variants=[variant],
        google_variants=[],
    )

    # Calculate score with non-compliant ad copy
    score = magister._calculate_overall_score(ad_copy, None, None)
    assert score == 0.0  # 0/1 compliant

    # Check priority actions include violation fix
    actions = magister._generate_priority_actions(ad_copy, None, None)
    assert any("violations" in action.lower() for action in actions)
