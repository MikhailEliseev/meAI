"""Tests for Conversion Tracker."""

import pytest

from src.aim.subagents.analytics.conversion_tracker import (
    ConversionTracker,
    ConversionReport,
    Goal,
    Attribution,
    TouchPoint,
    CustomerJourney,
    RevenueMetrics,
    ROIMetrics,
)


@pytest.fixture
def tracker():
    """Create Conversion Tracker instance."""
    return ConversionTracker(
        ga4_property_id="123456789",
        yandex_counter_id="987654321",
    )


@pytest.mark.asyncio
async def test_track_complete_report(tracker):
    """Test complete conversion tracking."""
    report = await tracker.track(
        start_date="2026-04-01",
        end_date="2026-04-30",
        source="ga4",
    )

    assert isinstance(report, ConversionReport)
    assert report.start_date == "2026-04-01"
    assert report.end_date == "2026-04-30"
    assert report.total_conversions > 0
    assert report.overall_conversion_rate >= 0
    assert len(report.goals) > 0
    assert len(report.attributions) > 0
    assert len(report.customer_journeys) > 0
    assert isinstance(report.revenue_metrics, RevenueMetrics)
    assert isinstance(report.roi_metrics, ROIMetrics)
    assert len(report.insights) > 0


@pytest.mark.asyncio
async def test_track_goals(tracker):
    """Test goal tracking."""
    goals = await tracker._track_goals("2026-04-01", "2026-04-30", "ga4")

    assert len(goals) > 0
    assert all(isinstance(g, Goal) for g in goals)
    assert all(g.completions > 0 for g in goals)
    assert all(0 <= g.conversion_rate <= 100 for g in goals)
    assert all(g.value >= 0 for g in goals)
    assert any(g.goal_type == "event" for g in goals)


@pytest.mark.asyncio
async def test_analyze_attribution(tracker):
    """Test attribution analysis."""
    attributions = await tracker._analyze_attribution("2026-04-01", "2026-04-30", "ga4")

    assert len(attributions) > 0
    assert all(isinstance(a, Attribution) for a in attributions)
    assert all(a.conversions > 0 for a in attributions)
    assert all(a.revenue >= 0 for a in attributions)
    assert all(a.cost >= 0 for a in attributions)


@pytest.mark.asyncio
async def test_analyze_customer_journeys(tracker):
    """Test customer journey analysis."""
    journeys = await tracker._analyze_customer_journeys("2026-04-01", "2026-04-30", "ga4")

    assert len(journeys) > 0
    assert all(isinstance(j, CustomerJourney) for j in journeys)
    assert all(len(j.touchpoints) > 0 for j in journeys)
    assert all(j.total_touchpoints == len(j.touchpoints) for j in journeys)
    assert all(j.conversion_value > 0 for j in journeys)
    assert all(j.time_to_conversion > 0 for j in journeys)

    # Check touchpoint attribution weights sum to 1.0
    for journey in journeys:
        total_weight = sum(tp.attribution_weight for tp in journey.touchpoints)
        assert abs(total_weight - 1.0) < 0.01


@pytest.mark.asyncio
async def test_track_revenue(tracker):
    """Test revenue tracking."""
    revenue = await tracker._track_revenue("2026-04-01", "2026-04-30", "ga4")

    assert isinstance(revenue, RevenueMetrics)
    assert revenue.total_revenue > 0
    assert revenue.avg_order_value > 0
    assert revenue.transactions > 0
    assert revenue.revenue_per_session > 0
    assert revenue.revenue_per_user > 0
    assert revenue.avg_order_value == revenue.total_revenue / revenue.transactions


@pytest.mark.asyncio
async def test_calculate_roi(tracker):
    """Test ROI calculation."""
    attributions = [
        Attribution("google", "cpc", "brand", 100, 10000.0, 2000.0, 0.0),
        Attribution("yandex", "cpc", "generic", 50, 5000.0, 1000.0, 0.0),
    ]
    revenue_metrics = RevenueMetrics(15000.0, 50.0, 300, 1.5, 1.875)

    roi = await tracker._calculate_roi(attributions, revenue_metrics)

    assert isinstance(roi, ROIMetrics)
    assert roi.total_cost == 3000.0
    assert roi.total_revenue == 15000.0
    assert roi.total_profit == 12000.0
    assert roi.roi_percent == 400.0  # (12000 / 3000) * 100
    assert roi.roas == 5.0  # 15000 / 3000


@pytest.mark.asyncio
async def test_calculate_roi_zero_cost(tracker):
    """Test ROI calculation with zero cost."""
    attributions = [
        Attribution("direct", "none", "(none)", 100, 10000.0, 0.0, 0.0),
    ]
    revenue_metrics = RevenueMetrics(10000.0, 50.0, 200, 1.0, 1.25)

    roi = await tracker._calculate_roi(attributions, revenue_metrics)

    assert roi.roi_percent == 0.0
    assert roi.roas == 0.0


@pytest.mark.asyncio
async def test_top_converting_source(tracker):
    """Test top converting source identification."""
    report = await tracker.track("2026-04-01", "2026-04-30", "ga4")

    assert report.top_converting_source != ""
    assert "/" in report.top_converting_source  # source/medium format


@pytest.mark.asyncio
async def test_avg_touchpoints_calculation(tracker):
    """Test average touchpoints calculation."""
    report = await tracker.track("2026-04-01", "2026-04-30", "ga4")

    assert report.avg_touchpoints > 0
    # Should be average of all journey touchpoints
    manual_avg = sum(j.total_touchpoints for j in report.customer_journeys) / len(report.customer_journeys)
    assert abs(report.avg_touchpoints - manual_avg) < 0.1


def test_generate_insights_top_goal(tracker):
    """Test insights generation for top goal."""
    goals = [
        Goal("1", "Purchase", "event", 1000, 10.0, 50000.0),
        Goal("2", "Lead", "event", 500, 5.0, 10000.0),
    ]
    attributions = []
    journeys = []
    revenue = RevenueMetrics(50000.0, 50.0, 1000, 5.0, 6.25)
    roi = ROIMetrics(10000.0, 50000.0, 40000.0, 400.0, 5.0)

    insights = tracker._generate_insights(goals, attributions, journeys, revenue, roi)

    assert len(insights) > 0
    assert any("Purchase" in insight for insight in insights)


def test_generate_insights_best_roi(tracker):
    """Test insights for best ROI channel."""
    goals = []
    attributions = [
        Attribution("google", "cpc", "brand", 100, 10000.0, 2000.0, 400.0),
        Attribution("yandex", "cpc", "generic", 50, 5000.0, 3000.0, 66.7),
    ]
    journeys = []
    revenue = RevenueMetrics(15000.0, 50.0, 300, 1.5, 1.875)
    roi = ROIMetrics(5000.0, 15000.0, 10000.0, 200.0, 3.0)

    insights = tracker._generate_insights(goals, attributions, journeys, revenue, roi)

    assert any("google" in insight.lower() for insight in insights)
    assert any("roi" in insight.lower() for insight in insights)


def test_generate_insights_complex_journey(tracker):
    """Test insights for complex customer journey."""
    goals = []
    attributions = []
    journeys = [
        CustomerJourney(
            "user_1",
            [
                TouchPoint(1, "google", "organic", "2026-05-01T10:00:00", 0.25),
                TouchPoint(2, "facebook", "social", "2026-05-02T14:00:00", 0.25),
                TouchPoint(3, "yandex", "cpc", "2026-05-03T12:00:00", 0.25),
                TouchPoint(-1, "direct", "none", "2026-05-04T16:00:00", 0.25),
            ],
            4,
            100.0,
            78.0,
        ),
    ]
    revenue = RevenueMetrics(100.0, 100.0, 1, 0.01, 0.0125)
    roi = ROIMetrics(50.0, 100.0, 50.0, 100.0, 2.0)

    insights = tracker._generate_insights(goals, attributions, journeys, revenue, roi)

    assert any("точек контакта" in insight.lower() for insight in insights)


def test_generate_insights_low_roi(tracker):
    """Test insights for low ROI."""
    goals = []
    attributions = []
    journeys = []
    revenue = RevenueMetrics(10000.0, 50.0, 200, 1.0, 1.25)
    roi = ROIMetrics(15000.0, 10000.0, -5000.0, -33.3, 0.67)

    insights = tracker._generate_insights(goals, attributions, journeys, revenue, roi)

    assert any("roi" in insight.lower() for insight in insights)
    assert any("оптимизируйте" in insight.lower() for insight in insights)


def test_generate_insights_high_roi(tracker):
    """Test insights for high ROI."""
    goals = []
    attributions = []
    journeys = []
    revenue = RevenueMetrics(50000.0, 50.0, 1000, 5.0, 6.25)
    roi = ROIMetrics(10000.0, 50000.0, 40000.0, 400.0, 5.0)

    insights = tracker._generate_insights(goals, attributions, journeys, revenue, roi)

    assert any("roi" in insight.lower() for insight in insights)
    assert any("масштабируйте" in insight.lower() for insight in insights)
