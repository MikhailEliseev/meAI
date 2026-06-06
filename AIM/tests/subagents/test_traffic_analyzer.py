"""Tests for Traffic Analyzer."""

import pytest
from datetime import datetime, timedelta

from src.aim.subagents.analytics.traffic_analyzer import (
    TrafficAnalyzer,
    TrafficReport,
    TrafficSource,
    UserBehavior,
    ConversionFunnel,
    BounceAnalysis,
    SessionAnalysis,
)


@pytest.fixture
def analyzer():
    """Create Traffic Analyzer instance."""
    return TrafficAnalyzer(
        ga4_property_id="123456789",
        yandex_counter_id="987654321",
    )


@pytest.fixture
def date_range():
    """Create date range for testing."""
    end_date = datetime.now().date()
    start_date = end_date - timedelta(days=30)
    return start_date.isoformat(), end_date.isoformat()


@pytest.mark.asyncio
async def test_analyze_complete_report(analyzer, date_range):
    """Test complete traffic analysis."""
    start_date, end_date = date_range

    report = await analyzer.analyze(
        start_date=start_date,
        end_date=end_date,
        source="ga4",
    )

    assert isinstance(report, TrafficReport)
    assert report.start_date == start_date
    assert report.end_date == end_date
    assert report.total_sessions > 0
    assert report.total_users > 0
    assert report.total_pageviews > 0
    assert len(report.traffic_sources) > 0
    assert isinstance(report.user_behavior, UserBehavior)
    assert len(report.conversion_funnel) > 0
    assert isinstance(report.bounce_analysis, BounceAnalysis)
    assert isinstance(report.session_analysis, SessionAnalysis)
    assert len(report.insights) > 0


@pytest.mark.asyncio
async def test_fetch_traffic_sources(analyzer, date_range):
    """Test traffic sources fetching."""
    start_date, end_date = date_range

    sources = await analyzer._fetch_traffic_sources(start_date, end_date, "ga4")

    assert len(sources) > 0
    assert all(isinstance(s, TrafficSource) for s in sources)
    assert any(s.source == "google" for s in sources)
    assert any(s.source == "yandex" for s in sources)
    assert any(s.source == "direct" for s in sources)
    assert all(s.sessions > 0 for s in sources)
    assert all(s.users > 0 for s in sources)
    assert all(0 <= s.bounce_rate <= 100 for s in sources)


@pytest.mark.asyncio
async def test_analyze_user_behavior(analyzer, date_range):
    """Test user behavior analysis."""
    start_date, end_date = date_range

    behavior = await analyzer._analyze_user_behavior(start_date, end_date, "ga4")

    assert isinstance(behavior, UserBehavior)
    assert behavior.new_users > 0
    assert behavior.returning_users > 0
    assert behavior.total_users == behavior.new_users + behavior.returning_users
    assert 0 <= behavior.new_user_rate <= 100
    assert behavior.pages_per_session > 0
    assert behavior.avg_session_duration > 0


@pytest.mark.asyncio
async def test_analyze_conversion_funnel(analyzer, date_range):
    """Test conversion funnel analysis."""
    start_date, end_date = date_range

    funnel = await analyzer._analyze_conversion_funnel(start_date, end_date, "ga4")

    assert len(funnel) > 0
    assert all(isinstance(step, ConversionFunnel) for step in funnel)
    assert funnel[0].step_number == 1
    assert funnel[0].conversion_rate == 100.0
    assert funnel[0].drop_off_rate == 0.0

    # Check funnel progression
    for i in range(1, len(funnel)):
        assert funnel[i].users <= funnel[i - 1].users
        assert 0 <= funnel[i].conversion_rate <= 100
        assert 0 <= funnel[i].drop_off_rate <= 100


@pytest.mark.asyncio
async def test_analyze_bounce_rate(analyzer, date_range):
    """Test bounce rate analysis."""
    start_date, end_date = date_range

    bounce = await analyzer._analyze_bounce_rate(start_date, end_date, "ga4")

    assert isinstance(bounce, BounceAnalysis)
    assert 0 <= bounce.overall_bounce_rate <= 100
    assert len(bounce.bounce_by_source) > 0
    assert all(0 <= rate <= 100 for rate in bounce.bounce_by_source.values())
    assert len(bounce.high_bounce_pages) > 0
    assert len(bounce.low_bounce_pages) > 0


@pytest.mark.asyncio
async def test_analyze_session_duration(analyzer, date_range):
    """Test session duration analysis."""
    start_date, end_date = date_range

    session = await analyzer._analyze_session_duration(start_date, end_date, "ga4")

    assert isinstance(session, SessionAnalysis)
    assert session.avg_duration > 0
    assert session.median_duration > 0
    assert len(session.duration_by_source) > 0
    assert all(duration > 0 for duration in session.duration_by_source.values())
    assert session.short_sessions >= 0
    assert session.medium_sessions >= 0
    assert session.long_sessions >= 0


@pytest.mark.asyncio
async def test_overall_conversion_rate_calculation(analyzer, date_range):
    """Test overall conversion rate calculation."""
    start_date, end_date = date_range

    report = await analyzer.analyze(start_date, end_date, "ga4")

    # Conversion rate should be (last step users / first step users) * 100
    first_step = report.conversion_funnel[0]
    last_step = report.conversion_funnel[-1]
    expected_rate = (last_step.users / first_step.users) * 100

    assert abs(report.overall_conversion_rate - expected_rate) < 0.1


def test_generate_insights_top_source(analyzer):
    """Test insights generation for top traffic source."""
    sources = [
        TrafficSource("google", 5000, 4000, 15000, 45.0, 180.0),
        TrafficSource("yandex", 3000, 2500, 9000, 50.0, 150.0),
    ]
    behavior = UserBehavior(7000, 2850, 9850, 71.1, 3.2, 165.0)
    bounce = BounceAnalysis(47.5, {}, [], [])
    session = SessionAnalysis(165.0, 120.0, {}, 3000, 5000, 2500)

    insights = analyzer._generate_insights(sources, behavior, bounce, session)

    assert len(insights) > 0
    assert any("google" in insight.lower() for insight in insights)


def test_generate_insights_high_new_users(analyzer):
    """Test insights for high new user rate."""
    sources = [TrafficSource("google", 5000, 4000, 15000, 45.0, 180.0)]
    behavior = UserBehavior(8000, 1000, 9000, 88.9, 3.2, 165.0)  # 88.9% new users
    bounce = BounceAnalysis(47.5, {}, [], [])
    session = SessionAnalysis(165.0, 120.0, {}, 3000, 5000, 2500)

    insights = analyzer._generate_insights(sources, behavior, bounce, session)

    assert any("новых пользователей" in insight.lower() for insight in insights)
    assert any("удержание" in insight.lower() for insight in insights)


def test_generate_insights_high_bounce(analyzer):
    """Test insights for high bounce rate."""
    sources = [TrafficSource("google", 5000, 4000, 15000, 45.0, 180.0)]
    behavior = UserBehavior(7000, 2850, 9850, 71.1, 3.2, 165.0)
    bounce = BounceAnalysis(65.0, {}, [], [])  # High bounce rate
    session = SessionAnalysis(165.0, 120.0, {}, 3000, 5000, 2500)

    insights = analyzer._generate_insights(sources, behavior, bounce, session)

    assert any("отказов" in insight.lower() for insight in insights)


def test_generate_insights_short_sessions(analyzer):
    """Test insights for short session duration."""
    sources = [TrafficSource("google", 5000, 4000, 15000, 45.0, 180.0)]
    behavior = UserBehavior(7000, 2850, 9850, 71.1, 3.2, 165.0)
    bounce = BounceAnalysis(47.5, {}, [], [])
    session = SessionAnalysis(45.0, 30.0, {}, 8000, 1000, 500)  # Short sessions

    insights = analyzer._generate_insights(sources, behavior, bounce, session)

    assert any("длительность" in insight.lower() for insight in insights)


def test_traffic_source_metrics(analyzer):
    """Test traffic source metrics validation."""
    source = TrafficSource(
        source="google",
        sessions=5000,
        users=4200,
        pageviews=15000,
        bounce_rate=45.5,
        avg_session_duration=180.0,
    )

    assert source.sessions > 0
    assert source.users > 0
    assert source.pageviews > 0
    assert 0 <= source.bounce_rate <= 100
    assert source.avg_session_duration > 0
    assert source.pageviews >= source.sessions  # At least 1 page per session
