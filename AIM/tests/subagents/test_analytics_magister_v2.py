"""Tests for Analytics Magister V2."""

import pytest
from datetime import datetime

from src.aim.magisters.analytics_magister_v2 import (
    AnalyticsMagisterV2,
    AnalyticsWorkflowReport,
)
from src.aim.subagents.analytics.traffic_analyzer import (
    TrafficReport,
    TrafficSource,
    UserBehavior,
    BounceAnalysis,
    SessionAnalysis,
    ConversionFunnel,
)
from src.aim.subagents.analytics.conversion_tracker import (
    ConversionReport,
    Goal,
    Attribution,
    CustomerJourney,
    TouchPoint,
    RevenueMetrics,
    ROIMetrics,
)
from src.aim.subagents.analytics.report_generator import (
    MarketingReport,
    ReportMetrics,
    ChannelPerformance,
    KeyInsight,
    GoalProgress,
    CompetitorComparison,
    Recommendation,
)


@pytest.fixture
def magister():
    """Create Analytics Magister V2 instance."""
    return AnalyticsMagisterV2()


@pytest.fixture
def sample_traffic_report():
    """Sample traffic report."""
    return TrafficReport(
        start_date="2026-01-01",
        end_date="2026-01-31",
        timestamp=datetime.now().isoformat(),
        traffic_sources=[
            TrafficSource(
                source="organic",
                sessions=5000,
                users=4000,
                pageviews=15000,
                bounce_rate=45.0,
                avg_session_duration=180.0,
            ),
            TrafficSource(
                source="direct",
                sessions=3000,
                users=2500,
                pageviews=9000,
                bounce_rate=50.0,
                avg_session_duration=150.0,
            ),
        ],
        total_sessions=8000,
        total_users=6500,
        total_pageviews=24000,
        user_behavior=UserBehavior(
            new_users=4000,
            returning_users=2500,
            total_users=6500,
            new_user_rate=61.5,
            pages_per_session=3.0,
            avg_session_duration=168.75,
        ),
        conversion_funnel=[
            ConversionFunnel(step_name="Landing", step_number=1, users=6500, conversion_rate=100.0, drop_off_rate=0.0),
            ConversionFunnel(step_name="Product Page", step_number=2, users=4000, conversion_rate=61.5, drop_off_rate=38.5),
            ConversionFunnel(step_name="Cart", step_number=3, users=1500, conversion_rate=23.1, drop_off_rate=76.9),
            ConversionFunnel(step_name="Checkout", step_number=4, users=500, conversion_rate=7.7, drop_off_rate=92.3),
            ConversionFunnel(step_name="Purchase", step_number=5, users=250, conversion_rate=3.8, drop_off_rate=96.2),
        ],
        overall_conversion_rate=3.8,
        bounce_analysis=BounceAnalysis(
            overall_bounce_rate=47.0,
            bounce_by_source={"organic": 45.0, "direct": 50.0},
            high_bounce_pages=["/landing-1", "/landing-2"],
            low_bounce_pages=["/product-1", "/product-2"],
        ),
        session_analysis=SessionAnalysis(
            avg_duration=168.75,
            median_duration=150.0,
            duration_by_source={"organic": 180.0, "direct": 150.0},
            short_sessions=2000,
            medium_sessions=4000,
            long_sessions=2000,
        ),
        insights=[
            "Organic traffic has 45% bounce rate - good quality",
            "Direct traffic has 50% bounce rate - needs improvement",
        ],
    )


@pytest.fixture
def sample_conversion_report():
    """Sample conversion report."""
    return ConversionReport(
        start_date="2026-01-01",
        end_date="2026-01-31",
        timestamp=datetime.now().isoformat(),
        goals=[
            Goal(
                goal_id="goal-1",
                goal_name="Purchase",
                goal_type="event",
                completions=250,
                conversion_rate=3.8,
                value=500000.0,
            ),
            Goal(
                goal_id="goal-2",
                goal_name="Lead Form",
                goal_type="event",
                completions=500,
                conversion_rate=7.7,
                value=100000.0,
            ),
        ],
        total_conversions=750,
        overall_conversion_rate=11.5,
        attributions=[
            Attribution(
                source="organic",
                medium="organic",
                campaign="",
                conversions=400,
                revenue=320000.0,
                cost=80000.0,
                roi=300.0,
            ),
            Attribution(
                source="direct",
                medium="none",
                campaign="",
                conversions=350,
                revenue=280000.0,
                cost=70000.0,
                roi=300.0,
            ),
        ],
        top_converting_source="organic",
        customer_journeys=[
            CustomerJourney(
                user_id="user-1",
                touchpoints=[
                    TouchPoint(
                        position=1,
                        source="organic",
                        medium="organic",
                        timestamp="2026-01-01T10:00:00",
                        attribution_weight=0.3,
                    ),
                    TouchPoint(
                        position=2,
                        source="direct",
                        medium="none",
                        timestamp="2026-01-02T14:00:00",
                        attribution_weight=0.3,
                    ),
                    TouchPoint(
                        position=-1,
                        source="organic",
                        medium="organic",
                        timestamp="2026-01-03T16:00:00",
                        attribution_weight=0.4,
                    ),
                ],
                total_touchpoints=3,
                conversion_value=2000.0,
                time_to_conversion=48.0,
            ),
        ],
        avg_touchpoints=2.5,
        avg_time_to_conversion=36.0,
        revenue_metrics=RevenueMetrics(
            total_revenue=600000.0,
            avg_order_value=2400.0,
            transactions=250,
            revenue_per_session=75.0,
            revenue_per_user=92.3,
        ),
        roi_metrics=ROIMetrics(
            total_cost=150000.0,
            total_revenue=600000.0,
            total_profit=450000.0,
            roi_percent=300.0,
            roas=4.0,
        ),
        insights=[
            "ROI is 300% - excellent performance",
            "Organic is top converting source",
        ],
    )


@pytest.fixture
def sample_marketing_report():
    """Sample marketing report."""
    return MarketingReport(
        report_id="report-001",
        report_name="January Marketing Report",
        period="2026-01-01 to 2026-01-31",
        generated_at=datetime.now().isoformat(),
        executive_summary="Strong performance in January with 300% ROI and 11.5% conversion rate.",
        metrics=ReportMetrics(
            period="2026-01-01 to 2026-01-31",
            total_traffic=8000,
            total_conversions=750,
            total_revenue=600000.0,
            total_cost=150000.0,
            roi=300.0,
            conversion_rate=11.5,
            avg_order_value=2400.0,
        ),
        channel_performance=[
            ChannelPerformance(
                channel="organic",
                traffic=5000,
                conversions=400,
                revenue=320000.0,
                cost=80000.0,
                roi=300.0,
                conversion_rate=8.0,
                trend="up",
            ),
            ChannelPerformance(
                channel="direct",
                traffic=3000,
                conversions=350,
                revenue=280000.0,
                cost=70000.0,
                roi=300.0,
                conversion_rate=11.7,
                trend="stable",
            ),
        ],
        key_insights=[
            KeyInsight(
                title="Excellent ROI",
                description="300% ROI indicates strong campaign performance",
                impact="high",
                metric_change=15.0,
                recommendation="Continue current strategy",
            ),
            KeyInsight(
                title="High Conversion Rate",
                description="11.5% conversion rate is above industry average",
                impact="high",
                metric_change=8.5,
                recommendation="Scale successful channels",
            ),
        ],
        goal_progress=[
            GoalProgress(
                goal_name="Revenue Target",
                target_value=500000.0,
                current_value=600000.0,
                progress_percent=120.0,
                status="on_track",
                days_remaining=0,
            ),
        ],
        competitor_comparison=[
            CompetitorComparison(
                metric="conversion_rate",
                our_value=11.5,
                competitor_avg=8.0,
                difference_percent=43.75,
                position="leading",
            ),
        ],
        recommendations=[
            Recommendation(
                priority="high",
                category="seo",
                title="Scale organic traffic",
                description="Organic has excellent ROI - increase budget",
                expected_impact="15% revenue increase",
                effort="medium",
                timeline="short_term",
            ),
            Recommendation(
                priority="medium",
                category="technical",
                title="Optimize direct traffic",
                description="Direct has 50% bounce rate - improve landing pages",
                expected_impact="10% conversion increase",
                effort="low",
                timeline="immediate",
            ),
        ],
        report_type="monthly",
        audience="manager",
    )


@pytest.mark.asyncio
async def test_calculate_overall_score_all_phases(
    magister, sample_traffic_report, sample_conversion_report, sample_marketing_report
):
    """Test overall score calculation with all phases."""
    score = magister._calculate_overall_score(
        sample_traffic_report,
        sample_conversion_report,
        sample_marketing_report,
    )

    # Traffic: bounce 47% → 53 score, duration 168.75s → 93.75 score → avg 73.375 (30% = 22.0)
    # Conversion: rate 11.5% → 100 score, ROI 300% → 75 score → avg 87.5 (40% = 35.0)
    # Report: 2 insights * 20 + 2 recommendations * 10 = 60 score (30% = 18.0)
    # Total: 22.0 + 35.0 + 18.0 = 75.0
    assert 74.0 <= score <= 76.0


@pytest.mark.asyncio
async def test_calculate_overall_score_without_conversion(
    magister, sample_traffic_report, sample_marketing_report
):
    """Test overall score calculation without conversion tracking."""
    score = magister._calculate_overall_score(
        sample_traffic_report,
        None,
        sample_marketing_report,
    )

    # Traffic: 73.375 (60% = 44.025)
    # Report: 60 (40% = 24.0)
    # Total: 44.025 + 24.0 = 68.025
    assert 67.0 <= score <= 69.0


@pytest.mark.asyncio
async def test_calculate_overall_score_without_report(
    magister, sample_traffic_report, sample_conversion_report
):
    """Test overall score calculation without report generation."""
    score = magister._calculate_overall_score(
        sample_traffic_report,
        sample_conversion_report,
        None,
    )

    # Traffic: 73.375 (60% = 44.025)
    # Conversion: 87.5 (40% = 35.0)
    # Total: 44.025 + 35.0 = 79.025
    assert 78.0 <= score <= 80.0


@pytest.mark.asyncio
async def test_calculate_overall_score_traffic_only(magister, sample_traffic_report):
    """Test overall score calculation with traffic only."""
    score = magister._calculate_overall_score(
        sample_traffic_report,
        None,
        None,
    )

    # Traffic: 73.375
    assert 73.0 <= score <= 74.0


@pytest.mark.asyncio
async def test_generate_priority_actions(
    magister,
    sample_traffic_report,
    sample_conversion_report,
    sample_marketing_report,
):
    """Test priority actions generation."""
    actions = magister._generate_priority_actions(
        sample_traffic_report,
        sample_conversion_report,
        sample_marketing_report,
    )

    assert isinstance(actions, list)
    assert len(actions) <= 5
    # Should include traffic insight
    assert any("traffic" in action.lower() for action in actions)
    # Should include conversion insight
    assert any("roi" in action.lower() or "conversion" in action.lower() for action in actions)
    # Should include recommendations
    assert any("high:" in action.lower() for action in actions)


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
async def test_estimate_impact_with_low_roi(
    magister, sample_traffic_report, sample_conversion_report
):
    """Test impact estimation with low ROI."""
    # Create conversion report with low ROI
    low_roi_conversion = ConversionReport(
        start_date="2026-01-01",
        end_date="2026-01-31",
        timestamp=datetime.now().isoformat(),
        goals=[],
        total_conversions=100,
        overall_conversion_rate=5.0,
        attributions=[],
        top_converting_source="organic",
        customer_journeys=[],
        avg_touchpoints=2.0,
        avg_time_to_conversion=24.0,
        revenue_metrics=RevenueMetrics(
            total_revenue=100000.0,
            avg_order_value=1000.0,
            transactions=100,
            revenue_per_session=50.0,
            revenue_per_user=60.0,
        ),
        roi_metrics=ROIMetrics(
            total_cost=120000.0,
            total_revenue=100000.0,
            total_profit=-20000.0,
            roi_percent=-16.7,
            roas=0.83,
        ),
        insights=[],
    )

    # Medium score but low ROI should upgrade to high impact
    impact = magister._estimate_impact(
        60.0,
        sample_traffic_report,
        low_roi_conversion,
    )
    assert impact == "high"


@pytest.mark.asyncio
async def test_estimate_impact_with_high_bounce(
    magister, sample_conversion_report
):
    """Test impact estimation with high bounce rate."""
    # Create traffic report with high bounce rate
    high_bounce_traffic = TrafficReport(
        start_date="2026-01-01",
        end_date="2026-01-31",
        timestamp=datetime.now().isoformat(),
        traffic_sources=[],
        total_sessions=5000,
        total_users=4000,
        total_pageviews=10000,
        user_behavior=UserBehavior(
            new_users=3000,
            returning_users=1000,
            total_users=4000,
            new_user_rate=75.0,
            pages_per_session=2.0,
            avg_session_duration=60.0,
        ),
        conversion_funnel=[],
        overall_conversion_rate=2.0,
        bounce_analysis=BounceAnalysis(
            overall_bounce_rate=70.0,
            bounce_by_source={},
            high_bounce_pages=[],
            low_bounce_pages=[],
        ),
        session_analysis=SessionAnalysis(
            avg_duration=60.0,
            median_duration=45.0,
            duration_by_source={},
            short_sessions=4000,
            medium_sessions=800,
            long_sessions=200,
        ),
        insights=[],
    )

    # Medium score but high bounce should upgrade to high impact
    impact = magister._estimate_impact(
        60.0,
        high_bounce_traffic,
        sample_conversion_report,
    )
    assert impact == "high"


@pytest.mark.asyncio
async def test_execute_workflow_structure(magister):
    """Test workflow execution returns correct structure."""
    report = await magister.execute_workflow(
        start_date="2026-01-01",
        end_date="2026-01-31",
        report_name="Test Report",
        report_type="monthly",
        audience="manager",
        source="ga4",
    )

    assert isinstance(report, AnalyticsWorkflowReport)
    assert report.period == "2026-01-01 to 2026-01-31"
    assert isinstance(report.generated_at, str)
    assert isinstance(report.duration_seconds, float)
    assert isinstance(report.traffic_analysis, TrafficReport)
    assert isinstance(report.conversion_tracking, ConversionReport)
    assert isinstance(report.marketing_report, MarketingReport)
    assert 0 <= report.overall_score <= 100
    assert isinstance(report.priority_actions, list)
    assert report.estimated_impact in ["high", "medium", "low"]
    assert report.workflow_status in ["success", "partial", "failed"]
    assert isinstance(report.errors, list)


@pytest.mark.asyncio
async def test_execute_traffic_analysis_only(magister):
    """Test executing only traffic analysis phase."""
    traffic_report = await magister.execute_traffic_analysis_only(
        start_date="2026-01-01",
        end_date="2026-01-31",
        source="ga4",
    )

    assert isinstance(traffic_report, TrafficReport)
    assert traffic_report.start_date == "2026-01-01"
    assert traffic_report.end_date == "2026-01-31"


@pytest.mark.asyncio
async def test_execute_conversion_tracking_only(magister):
    """Test executing only conversion tracking phase."""
    conversion_report = await magister.execute_conversion_tracking_only(
        start_date="2026-01-01",
        end_date="2026-01-31",
        source="ga4",
    )

    assert isinstance(conversion_report, ConversionReport)
    assert conversion_report.start_date == "2026-01-01"
    assert conversion_report.end_date == "2026-01-31"


@pytest.mark.asyncio
async def test_execute_report_generation_only(magister):
    """Test executing only report generation phase."""
    marketing_report = await magister.execute_report_generation_only(
        report_name="Test Report",
        period="2026-01-01 to 2026-01-31",
        report_type="monthly",
        audience="manager",
    )

    assert isinstance(marketing_report, MarketingReport)
    assert marketing_report.report_name == "Test Report"
    assert marketing_report.period == "2026-01-01 to 2026-01-31"


@pytest.mark.asyncio
async def test_workflow_with_errors_partial_status(magister, monkeypatch):
    """Test workflow continues with partial status when one phase fails."""

    # Mock traffic analyzer to raise exception
    async def mock_analyze(*args, **kwargs):
        raise Exception("API error")

    monkeypatch.setattr(magister.traffic_analyzer, "analyze", mock_analyze)

    report = await magister.execute_workflow(
        start_date="2026-01-01",
        end_date="2026-01-31",
        report_name="Test Report",
    )

    assert report.workflow_status == "partial"
    assert len(report.errors) > 0
    assert any("Traffic Analysis failed" in error for error in report.errors)


@pytest.mark.asyncio
async def test_workflow_priority_actions_limit(
    magister, sample_traffic_report, sample_conversion_report, sample_marketing_report
):
    """Test priority actions are limited to top 5."""
    # Create marketing report with many recommendations
    marketing_with_many_recs = MarketingReport(
        report_id="report-001",
        report_name="Test Report",
        period="2026-01-01 to 2026-01-31",
        generated_at=datetime.now().isoformat(),
        executive_summary="Test summary",
        metrics=sample_marketing_report.metrics,
        channel_performance=[],
        key_insights=[],
        goal_progress=[],
        competitor_comparison=[],
        recommendations=[
            Recommendation(
                priority="high" if i < 5 else "medium",
                category="seo",
                title=f"Recommendation {i}",
                description=f"Description {i}",
                expected_impact="10%",
                effort="low",
                timeline="immediate",
            )
            for i in range(10)
        ],
        report_type="monthly",
        audience="manager",
    )

    actions = magister._generate_priority_actions(
        sample_traffic_report,
        sample_conversion_report,
        marketing_with_many_recs,
    )

    assert len(actions) <= 5
