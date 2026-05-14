"""Tests for Report Generator."""

import pytest

from AIM.src.aim.subagents.analytics.report_generator import (
    ReportGenerator,
    MarketingReport,
    ReportMetrics,
    ChannelPerformance,
    KeyInsight,
    GoalProgress,
    CompetitorComparison,
    Recommendation,
)


@pytest.fixture
def generator():
    """Create Report Generator instance."""
    return ReportGenerator()


@pytest.fixture
def sample_data():
    """Sample report data for testing."""
    return {
        "period": "2026-05-01 to 2026-05-14",
        "total_traffic": 50000,
        "total_conversions": 500,
        "total_revenue": 2500000.0,
        "total_cost": 500000.0,
        "channels": {
            "seo": {
                "traffic": 20000,
                "conversions": 250,
                "revenue": 1250000.0,
                "cost": 100000.0,
                "prev_traffic": 18000,
            },
            "ads": {
                "traffic": 15000,
                "conversions": 150,
                "revenue": 750000.0,
                "cost": 300000.0,
                "prev_traffic": 16000,
            },
            "social": {
                "traffic": 10000,
                "conversions": 80,
                "revenue": 400000.0,
                "cost": 80000.0,
                "prev_traffic": 9000,
            },
        },
        "goals": [
            {"name": "Monthly Revenue", "target": 3000000.0, "current": 2500000.0},
            {"name": "Conversions", "target": 600, "current": 500},
        ],
        "competitors": {
            "conversion_rate": {"ours": 1.0, "avg": 0.8},
            "avg_order_value": {"ours": 5000.0, "avg": 4500.0},
        },
    }


@pytest.mark.asyncio
async def test_generate_complete_report(generator, sample_data):
    """Test complete report generation."""
    report = await generator.generate(
        report_name="Monthly Marketing Report",
        period="2026-05-01 to 2026-05-14",
        report_type="monthly",
        audience="manager",
        data=sample_data,
    )

    assert isinstance(report, MarketingReport)
    assert report.report_name == "Monthly Marketing Report"
    assert report.period == "2026-05-01 to 2026-05-14"
    assert report.report_type == "monthly"
    assert report.audience == "manager"
    assert isinstance(report.metrics, ReportMetrics)
    assert isinstance(report.channel_performance, list)
    assert isinstance(report.key_insights, list)
    assert isinstance(report.goal_progress, list)
    assert isinstance(report.competitor_comparison, list)
    assert isinstance(report.recommendations, list)
    assert len(report.executive_summary) > 0


@pytest.mark.asyncio
async def test_calculate_metrics(generator, sample_data):
    """Test metrics calculation."""
    metrics = await generator._calculate_metrics(sample_data)

    assert isinstance(metrics, ReportMetrics)
    assert metrics.total_traffic == 50000
    assert metrics.total_conversions == 500
    assert metrics.total_revenue == 2500000.0
    assert metrics.total_cost == 500000.0
    assert metrics.roi == 400.0  # (2500000 - 500000) / 500000 * 100
    assert metrics.conversion_rate == 1.0  # 500 / 50000 * 100
    assert metrics.avg_order_value == 5000.0  # 2500000 / 500


@pytest.mark.asyncio
async def test_calculate_metrics_zero_values(generator):
    """Test metrics with zero values."""
    data = {
        "total_traffic": 0,
        "total_conversions": 0,
        "total_revenue": 0.0,
        "total_cost": 0.0,
    }
    metrics = await generator._calculate_metrics(data)

    assert metrics.roi == 0.0
    assert metrics.conversion_rate == 0.0
    assert metrics.avg_order_value == 0.0


@pytest.mark.asyncio
async def test_analyze_channels(generator, sample_data):
    """Test channel performance analysis."""
    channels = await generator._analyze_channels(sample_data)

    assert isinstance(channels, list)
    assert len(channels) == 3
    assert all(isinstance(ch, ChannelPerformance) for ch in channels)

    # Should be sorted by revenue (descending)
    assert channels[0].channel == "seo"  # Highest revenue
    assert channels[0].revenue == 1250000.0

    # Check calculations
    seo = channels[0]
    assert seo.roi == 1150.0  # (1250000 - 100000) / 100000 * 100
    assert seo.conversion_rate == 1.25  # 250 / 20000 * 100
    assert seo.trend == "up"  # 20000 > 18000 * 1.1


@pytest.mark.asyncio
async def test_analyze_channels_trends(generator):
    """Test channel trend detection."""
    data = {
        "channels": {
            "growing": {
                "traffic": 12000,
                "conversions": 100,
                "revenue": 500000.0,
                "cost": 100000.0,
                "prev_traffic": 10000,  # +20% growth
            },
            "declining": {
                "traffic": 8000,
                "conversions": 80,
                "revenue": 400000.0,
                "cost": 80000.0,
                "prev_traffic": 10000,  # -20% decline
            },
            "stable": {
                "traffic": 10000,
                "conversions": 100,
                "revenue": 500000.0,
                "cost": 100000.0,
                "prev_traffic": 10000,  # No change
            },
        }
    }
    channels = await generator._analyze_channels(data)

    growing = next(ch for ch in channels if ch.channel == "growing")
    declining = next(ch for ch in channels if ch.channel == "declining")
    stable = next(ch for ch in channels if ch.channel == "stable")

    assert growing.trend == "up"
    assert declining.trend == "down"
    assert stable.trend == "stable"


@pytest.mark.asyncio
async def test_extract_insights(generator, sample_data):
    """Test insights extraction."""
    metrics = await generator._calculate_metrics(sample_data)
    channels = await generator._analyze_channels(sample_data)
    insights = await generator._extract_insights(sample_data, metrics, channels)

    assert isinstance(insights, list)
    assert len(insights) > 0
    assert all(isinstance(ins, KeyInsight) for ins in insights)

    # Should have insight about best channel
    assert any("seo" in ins.title.lower() for ins in insights)

    # Check insight structure
    insight = insights[0]
    assert insight.impact in ["high", "medium", "low"]
    assert len(insight.recommendation) > 0


@pytest.mark.asyncio
async def test_extract_insights_low_roi(generator):
    """Test insights with low ROI."""
    data = {
        "total_traffic": 50000,
        "total_conversions": 500,
        "total_revenue": 600000.0,  # Low revenue
        "total_cost": 500000.0,
        "channels": {
            "ads": {
                "traffic": 50000,
                "conversions": 500,
                "revenue": 600000.0,
                "cost": 500000.0,
                "prev_traffic": 50000,
            }
        },
    }
    metrics = await generator._calculate_metrics(data)
    channels = await generator._analyze_channels(data)
    insights = await generator._extract_insights(data, metrics, channels)

    # Should have insight about low ROI
    assert any("roi" in ins.title.lower() for ins in insights)


@pytest.mark.asyncio
async def test_track_goals(generator, sample_data):
    """Test goal progress tracking."""
    goals = await generator._track_goals(sample_data)

    assert isinstance(goals, list)
    assert len(goals) == 2
    assert all(isinstance(g, GoalProgress) for g in goals)

    # Check first goal
    revenue_goal = goals[0]
    assert revenue_goal.goal_name == "Monthly Revenue"
    assert revenue_goal.target_value == 3000000.0
    assert revenue_goal.current_value == 2500000.0
    assert revenue_goal.progress_percent == 83.33  # 2500000 / 3000000 * 100
    assert revenue_goal.status in ["on_track", "at_risk", "behind"]


@pytest.mark.asyncio
async def test_track_goals_status(generator):
    """Test goal status determination."""
    data = {
        "goals": [
            {"name": "On Track", "target": 100.0, "current": 95.0},  # >= 90%
            {"name": "At Risk", "target": 100.0, "current": 75.0},  # 70-90%
            {"name": "Behind", "target": 100.0, "current": 50.0},  # < 70%
        ]
    }
    goals = await generator._track_goals(data)

    assert goals[0].status == "on_track"
    assert goals[1].status == "at_risk"
    assert goals[2].status == "behind"


@pytest.mark.asyncio
async def test_compare_competitors(generator, sample_data):
    """Test competitor comparison."""
    comparisons = await generator._compare_competitors(sample_data)

    assert isinstance(comparisons, list)
    assert len(comparisons) == 2
    assert all(isinstance(c, CompetitorComparison) for c in comparisons)

    # Check conversion rate comparison
    conv_rate = next(c for c in comparisons if "conversion" in c.metric.lower())
    assert conv_rate.our_value == 1.0
    assert conv_rate.competitor_avg == 0.8
    assert conv_rate.difference_percent == 25.0  # (1.0 - 0.8) / 0.8 * 100
    assert conv_rate.position == "leading"  # > 10% difference


@pytest.mark.asyncio
async def test_compare_competitors_positions(generator):
    """Test competitor position determination."""
    data = {
        "competitors": {
            "leading": {"ours": 120.0, "avg": 100.0},  # +20%
            "competitive": {"ours": 105.0, "avg": 100.0},  # +5%
            "behind": {"ours": 80.0, "avg": 100.0},  # -20%
        }
    }
    comparisons = await generator._compare_competitors(data)

    leading = next(c for c in comparisons if c.metric == "Leading")
    competitive = next(c for c in comparisons if c.metric == "Competitive")
    behind = next(c for c in comparisons if c.metric == "Behind")

    assert leading.position == "leading"
    assert competitive.position == "competitive"
    assert behind.position == "behind"


@pytest.mark.asyncio
async def test_generate_recommendations(generator, sample_data):
    """Test recommendations generation."""
    metrics = await generator._calculate_metrics(sample_data)
    channels = await generator._analyze_channels(sample_data)
    insights = await generator._extract_insights(sample_data, metrics, channels)
    goals = await generator._track_goals(sample_data)

    recommendations = await generator._generate_recommendations(
        metrics, channels, insights, goals
    )

    assert isinstance(recommendations, list)
    assert len(recommendations) > 0
    assert all(isinstance(r, Recommendation) for r in recommendations)

    # Check recommendation structure
    rec = recommendations[0]
    assert rec.priority in ["high", "medium", "low"]
    assert rec.effort in ["low", "medium", "high"]
    assert rec.timeline in ["immediate", "short_term", "long_term"]
    assert len(rec.title) > 0
    assert len(rec.description) > 0


@pytest.mark.asyncio
async def test_generate_recommendations_scale_best(generator):
    """Test recommendation to scale best channel."""
    data = {
        "total_traffic": 50000,
        "total_conversions": 500,
        "total_revenue": 2500000.0,
        "total_cost": 500000.0,
        "channels": {
            "seo": {
                "traffic": 50000,
                "conversions": 500,
                "revenue": 2500000.0,
                "cost": 100000.0,  # High ROI
                "prev_traffic": 50000,
            }
        },
        "goals": [],
    }
    metrics = await generator._calculate_metrics(data)
    channels = await generator._analyze_channels(data)
    insights = await generator._extract_insights(data, metrics, channels)
    goals = await generator._track_goals(data)

    recommendations = await generator._generate_recommendations(
        metrics, channels, insights, goals
    )

    # Should recommend scaling SEO
    assert any("seo" in r.title.lower() for r in recommendations)
    assert any(r.priority == "high" for r in recommendations)


@pytest.mark.asyncio
async def test_write_executive_summary_executive(generator, sample_data):
    """Test executive summary for executive audience."""
    metrics = await generator._calculate_metrics(sample_data)
    channels = await generator._analyze_channels(sample_data)
    insights = await generator._extract_insights(sample_data, metrics, channels)

    summary = await generator._write_executive_summary(metrics, insights, "executive")

    assert len(summary) > 0
    assert "2,500,000" in summary or "2500000" in summary  # Revenue
    assert "400" in summary  # ROI
    assert "500" in summary  # Conversions


@pytest.mark.asyncio
async def test_write_executive_summary_manager(generator, sample_data):
    """Test executive summary for manager audience."""
    metrics = await generator._calculate_metrics(sample_data)
    channels = await generator._analyze_channels(sample_data)
    insights = await generator._extract_insights(sample_data, metrics, channels)

    summary = await generator._write_executive_summary(metrics, insights, "manager")

    assert len(summary) > 0
    assert "50,000" in summary or "50000" in summary  # Traffic
    assert "1.0" in summary or "1.00" in summary  # Conversion rate
    assert len(summary) > 100  # More detailed than executive
