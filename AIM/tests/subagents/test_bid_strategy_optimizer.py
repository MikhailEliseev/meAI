"""Tests for Bid Strategy Optimizer."""

import pytest

from src.aim.subagents.ads.bid_strategy_optimizer import (
    BidStrategyOptimizer,
    BidOptimizationReport,
    PerformanceMetrics,
    BidStrategyAnalysis,
    BudgetAnalysis,
    BidAdjustments,
    CompetitorAnalysis,
)


@pytest.fixture
def optimizer():
    """Create Bid Strategy Optimizer instance."""
    return BidStrategyOptimizer()


@pytest.fixture
def sample_performance_data():
    """Sample performance data for testing."""
    return {
        "impressions": 10000,
        "clicks": 500,
        "conversions": 50,
        "cost": 25000.0,
        "revenue": 150000.0,
        "current_strategy": "manual",
        "daily_budget": 5000.0,
        "spent_today": 4800.0,
        "avg_position": 3.5,
        "impression_share": 65.0,
        "lost_is_rank": 20.0,
        "lost_is_budget": 15.0,
        "device_performance": {
            "desktop": {"clicks": 200, "conversions": 25, "cost": 10000.0},
            "mobile": {"clicks": 250, "conversions": 20, "cost": 12500.0},
            "tablet": {"clicks": 50, "conversions": 5, "cost": 2500.0},
        },
        "location_performance": {
            "moscow": {"clicks": 300, "conversions": 35, "cost": 15000.0},
            "spb": {"clicks": 150, "conversions": 12, "cost": 7500.0},
            "other": {"clicks": 50, "conversions": 3, "cost": 2500.0},
        },
        "time_performance": {
            "9-12": {"clicks": 150, "conversions": 20, "cost": 7500.0},
            "12-15": {"clicks": 200, "conversions": 18, "cost": 10000.0},
            "15-18": {"clicks": 100, "conversions": 8, "cost": 5000.0},
            "18-21": {"clicks": 50, "conversions": 4, "cost": 2500.0},
        },
    }


@pytest.mark.asyncio
async def test_optimize_complete_report(optimizer, sample_performance_data):
    """Test complete bid optimization."""
    report = await optimizer.optimize(
        campaign_id="123",
        campaign_name="Test Campaign",
        platform="yandex",
        performance_data=sample_performance_data,
    )

    assert isinstance(report, BidOptimizationReport)
    assert report.campaign_id == "123"
    assert report.campaign_name == "Test Campaign"
    assert report.platform == "yandex"
    assert isinstance(report.performance, PerformanceMetrics)
    assert isinstance(report.strategy, BidStrategyAnalysis)
    assert isinstance(report.budget, BudgetAnalysis)
    assert isinstance(report.adjustments, BidAdjustments)
    assert isinstance(report.competitors, CompetitorAnalysis)
    assert 0 <= report.optimization_score <= 100


@pytest.mark.asyncio
async def test_analyze_performance(optimizer, sample_performance_data):
    """Test performance metrics analysis."""
    performance = await optimizer._analyze_performance(sample_performance_data)

    assert isinstance(performance, PerformanceMetrics)
    assert performance.impressions == 10000
    assert performance.clicks == 500
    assert performance.conversions == 50
    assert performance.cost == 25000.0
    assert performance.revenue == 150000.0
    assert performance.ctr == 5.0  # 500/10000 * 100
    assert performance.cpc == 50.0  # 25000/500
    assert performance.cpa == 500.0  # 25000/50
    assert performance.roas == 6.0  # 150000/25000
    assert performance.conversion_rate == 10.0  # 50/500 * 100


@pytest.mark.asyncio
async def test_analyze_performance_zero_clicks(optimizer):
    """Test performance with zero clicks."""
    data = {
        "impressions": 1000,
        "clicks": 0,
        "conversions": 0,
        "cost": 0.0,
        "revenue": 0.0,
    }
    performance = await optimizer._analyze_performance(data)

    assert performance.ctr == 0.0
    assert performance.cpc == 0.0
    assert performance.cpa == 0.0
    assert performance.roas == 0.0
    assert performance.conversion_rate == 0.0


@pytest.mark.asyncio
async def test_analyze_strategy(optimizer, sample_performance_data):
    """Test bid strategy analysis."""
    performance = await optimizer._analyze_performance(sample_performance_data)
    strategy = await optimizer._analyze_strategy(sample_performance_data, performance)

    assert isinstance(strategy, BidStrategyAnalysis)
    assert strategy.current_strategy == "manual"
    assert 0 <= strategy.strategy_performance <= 100
    assert isinstance(strategy.is_optimal, bool)
    assert strategy.recommended_strategy in [
        "manual",
        "auto",
        "target_cpa",
        "target_roas",
        "maximize_conversions",
    ]
    assert strategy.expected_improvement >= 0
    assert 0 <= strategy.confidence <= 100


@pytest.mark.asyncio
async def test_analyze_strategy_recommend_auto(optimizer):
    """Test strategy recommendation for auto bidding."""
    data = {
        "impressions": 10000,
        "clicks": 500,
        "conversions": 50,  # >= 30, enough for auto
        "cost": 25000.0,
        "revenue": 150000.0,
        "current_strategy": "manual",
    }
    performance = await optimizer._analyze_performance(data)
    strategy = await optimizer._analyze_strategy(data, performance)

    assert strategy.recommended_strategy == "target_roas"
    assert strategy.expected_improvement > 0


@pytest.mark.asyncio
async def test_analyze_budget(optimizer, sample_performance_data):
    """Test budget analysis."""
    performance = await optimizer._analyze_performance(sample_performance_data)
    budget = await optimizer._analyze_budget(sample_performance_data, performance)

    assert isinstance(budget, BudgetAnalysis)
    assert budget.daily_budget == 5000.0
    assert budget.spent_today == 4800.0
    assert budget.utilization_rate == 96.0  # 4800/5000 * 100
    assert budget.is_limited is True  # >= 95%
    assert budget.recommended_budget > 0
    assert 0 <= budget.budget_efficiency <= 100


@pytest.mark.asyncio
async def test_analyze_budget_limited(optimizer):
    """Test budget limited scenario."""
    data = {
        "impressions": 10000,
        "clicks": 500,
        "conversions": 50,
        "cost": 25000.0,
        "revenue": 150000.0,  # Good ROAS
        "daily_budget": 5000.0,
        "spent_today": 4900.0,  # 98% utilization
    }
    performance = await optimizer._analyze_performance(data)
    budget = await optimizer._analyze_budget(data, performance)

    assert budget.is_limited is True
    assert budget.recommended_budget > budget.daily_budget  # Should increase


@pytest.mark.asyncio
async def test_analyze_budget_low_utilization(optimizer):
    """Test low budget utilization."""
    data = {
        "impressions": 10000,
        "clicks": 500,
        "conversions": 50,
        "cost": 25000.0,
        "revenue": 40000.0,  # Poor ROAS
        "daily_budget": 5000.0,
        "spent_today": 3000.0,  # 60% utilization
    }
    performance = await optimizer._analyze_performance(data)
    budget = await optimizer._analyze_budget(data, performance)

    assert budget.utilization_rate < 70
    assert budget.recommended_budget < budget.daily_budget  # Should decrease


@pytest.mark.asyncio
async def test_calculate_adjustments(optimizer, sample_performance_data):
    """Test bid adjustments calculation."""
    performance = await optimizer._analyze_performance(sample_performance_data)
    adjustments = await optimizer._calculate_adjustments(
        sample_performance_data, performance
    )

    assert isinstance(adjustments, BidAdjustments)
    assert isinstance(adjustments.device_adjustments, dict)
    assert isinstance(adjustments.location_adjustments, dict)
    assert isinstance(adjustments.time_adjustments, dict)
    assert isinstance(adjustments.audience_adjustments, dict)
    assert adjustments.overall_impact >= 0


@pytest.mark.asyncio
async def test_calculate_adjustments_device(optimizer):
    """Test device bid adjustments."""
    data = {
        "impressions": 10000,
        "clicks": 500,
        "conversions": 50,
        "cost": 25000.0,
        "revenue": 150000.0,
        "device_performance": {
            "desktop": {
                "clicks": 200,
                "conversions": 40,
                "cost": 10000.0,
                "revenue": 120000.0,
            },  # High ROAS
            "mobile": {
                "clicks": 300,
                "conversions": 10,
                "cost": 15000.0,
                "revenue": 30000.0,
            },  # Low ROAS
        },
    }
    performance = await optimizer._analyze_performance(data)
    adjustments = await optimizer._calculate_adjustments(data, performance)

    # Desktop should have positive adjustment (high ROAS)
    assert adjustments.device_adjustments.get("desktop", 0) > 0
    # Mobile should have negative adjustment (low ROAS)
    assert adjustments.device_adjustments.get("mobile", 0) < 0


@pytest.mark.asyncio
async def test_analyze_competitors(optimizer, sample_performance_data):
    """Test competitor analysis."""
    competitors = await optimizer._analyze_competitors(sample_performance_data)

    assert isinstance(competitors, CompetitorAnalysis)
    assert competitors.avg_position == 3.5
    assert competitors.impression_share == 65.0
    assert competitors.lost_impression_share_rank == 20.0
    assert competitors.lost_impression_share_budget == 15.0
    assert competitors.competitive_intensity in ["low", "medium", "high"]


@pytest.mark.asyncio
async def test_analyze_competitors_high_intensity(optimizer):
    """Test high competitive intensity."""
    data = {
        "avg_position": 5.0,
        "impression_share": 40.0,
        "lost_is_rank": 35.0,  # > 30, high intensity
        "lost_is_budget": 25.0,
    }
    competitors = await optimizer._analyze_competitors(data)

    assert competitors.competitive_intensity == "high"
    assert len(competitors.recommended_actions) > 0


def test_calculate_optimization_score(optimizer):
    """Test optimization score calculation."""
    strategy = BidStrategyAnalysis(
        current_strategy="manual",
        strategy_performance=80.0,
        is_optimal=True,
        recommended_strategy="manual",
        expected_improvement=0.0,
        confidence=90.0,
        reasons=["Good performance"],
        warnings=[],
    )
    budget = BudgetAnalysis(
        daily_budget=5000.0,
        spent_today=4500.0,
        utilization_rate=90.0,
        is_limited=False,
        recommended_budget=5000.0,
        budget_efficiency=100.0,
        recommendations=[],
    )
    adjustments = BidAdjustments(
        device_adjustments={"desktop": 10.0},
        location_adjustments={"moscow": 15.0},
        time_adjustments={"9-12": 20.0},
        audience_adjustments={"remarketing": 50.0},
        overall_impact=10.0,
    )
    competitors = CompetitorAnalysis(
        avg_position=2.5,
        impression_share=75.0,
        lost_impression_share_rank=10.0,
        lost_impression_share_budget=5.0,
        competitive_intensity="low",
        recommended_actions=[],
    )

    score = optimizer._calculate_optimization_score(
        strategy, budget, adjustments, competitors
    )

    assert 0 <= score <= 100
    assert score > 70  # Should be good


def test_identify_priority_actions(optimizer):
    """Test priority actions identification."""
    strategy = BidStrategyAnalysis(
        current_strategy="manual",
        strategy_performance=50.0,  # Low performance
        is_optimal=False,
        recommended_strategy="target_roas",
        expected_improvement=15.0,
        confidence=80.0,
        reasons=[],
        warnings=[],
    )
    budget = BudgetAnalysis(
        daily_budget=5000.0,
        spent_today=4900.0,
        utilization_rate=98.0,
        is_limited=True,  # Budget limited
        recommended_budget=7500.0,
        budget_efficiency=80.0,
        recommendations=[],
    )
    competitors = CompetitorAnalysis(
        avg_position=5.0,  # Low position
        impression_share=40.0,
        lost_impression_share_rank=35.0,
        lost_impression_share_budget=25.0,
        competitive_intensity="high",
        recommended_actions=[],
    )

    actions = optimizer._identify_priority_actions(strategy, budget, competitors)

    assert len(actions) > 0
    assert any("CRITICAL" in action for action in actions)


def test_identify_quick_wins(optimizer):
    """Test quick wins identification."""
    adjustments = BidAdjustments(
        device_adjustments={"desktop": 25.0, "mobile": -20.0},  # Significant adjustments
        location_adjustments={"moscow": 30.0, "spb": -25.0},
        time_adjustments={"9-12": 20.0},
        audience_adjustments={"remarketing": 50.0},
        overall_impact=10.0,
    )
    budget = BudgetAnalysis(
        daily_budget=5000.0,
        spent_today=3000.0,
        utilization_rate=60.0,  # Low utilization
        is_limited=False,
        recommended_budget=5000.0,
        budget_efficiency=60.0,
        recommendations=[],
    )

    wins = optimizer._identify_quick_wins(adjustments, budget)

    assert len(wins) > 0
    assert any("desktop" in win.lower() or "mobile" in win.lower() for win in wins)
