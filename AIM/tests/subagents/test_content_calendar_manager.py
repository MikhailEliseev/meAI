"""Tests for Content Calendar Manager."""

import pytest
from datetime import datetime, timedelta

from AIM.src.aim.subagents.content.content_calendar_manager import (
    ContentCalendarManager,
    ContentCalendarReport,
    ContentItem,
    ChannelSchedule,
    ContentGap,
    DeadlineAlert,
    CalendarMetrics,
)


@pytest.fixture
def manager():
    """Create Content Calendar Manager instance."""
    return ContentCalendarManager()


@pytest.fixture
def sample_data():
    """Sample calendar data for testing."""
    return {
        "items": [
            {
                "content_id": "content_001",
                "title": "Dental Implants Guide",
                "content_type": "blog",
                "status": "scheduled",
                "author": "Dr. Smith",
                "target_keyword": "dental implants",
                "scheduled_date": "2026-05-15T09:00:00",
                "publish_channel": "blog",
                "priority": "high",
                "word_count": 2000,
                "estimated_hours": 8.0,
            },
            {
                "content_id": "content_002",
                "title": "Patient Story",
                "content_type": "social",
                "status": "draft",
                "author": "Marketing Team",
                "target_keyword": None,
                "scheduled_date": "2026-05-16T14:00:00",
                "publish_channel": "instagram",
                "priority": "medium",
                "word_count": 150,
                "estimated_hours": 2.0,
            },
            {
                "content_id": "content_003",
                "title": "Newsletter",
                "content_type": "email",
                "status": "published",
                "author": "Content Team",
                "target_keyword": None,
                "scheduled_date": "2026-05-10T10:00:00",
                "publish_channel": "email",
                "priority": "high",
                "word_count": 800,
                "estimated_hours": 4.0,
            },
        ],
        "channels": {
            "blog": {"frequency": "weekly", "optimal_times": ["09:00", "14:00"]},
            "instagram": {"frequency": "daily", "optimal_times": ["12:00", "18:00"]},
            "email": {"frequency": "monthly", "optimal_times": ["10:00"]},
        },
        "target_keywords": ["dental implants", "teeth whitening", "orthodontics"],
    }


@pytest.mark.asyncio
async def test_get_calendar_complete(manager, sample_data):
    """Test complete calendar retrieval."""
    report = await manager.get_calendar(
        period="2026-05-01 to 2026-05-31",
        data=sample_data,
    )

    assert isinstance(report, ContentCalendarReport)
    assert report.period == "2026-05-01 to 2026-05-31"
    assert isinstance(report.calendar_items, list)
    assert isinstance(report.channel_schedules, list)
    assert isinstance(report.content_gaps, list)
    assert isinstance(report.deadline_alerts, list)
    assert isinstance(report.metrics, CalendarMetrics)
    assert isinstance(report.recommendations, list)


@pytest.mark.asyncio
async def test_get_calendar_items(manager, sample_data):
    """Test calendar items retrieval."""
    items = await manager._get_calendar_items(sample_data)

    assert isinstance(items, list)
    assert len(items) == 3
    assert all(isinstance(item, ContentItem) for item in items)

    # Check first item
    item = items[0]
    assert item.content_id == "content_003"  # Sorted by date (earliest first)
    assert item.title == "Newsletter"
    assert item.content_type == "email"
    assert item.status == "published"


@pytest.mark.asyncio
async def test_schedule_content(manager):
    """Test content scheduling."""
    item = await manager.schedule_content(
        title="New Blog Post",
        content_type="blog",
        author="John Doe",
        target_date="2026-05-20T09:00:00",
        channel="blog",
        priority="high",
        target_keyword="dental care",
    )

    assert isinstance(item, ContentItem)
    assert item.title == "New Blog Post"
    assert item.content_type == "blog"
    assert item.status == "draft"
    assert item.author == "John Doe"
    assert item.target_keyword == "dental care"
    assert item.scheduled_date == "2026-05-20T09:00:00"
    assert item.publish_channel == "blog"
    assert item.priority == "high"
    assert item.estimated_hours == 8.0  # Blog estimate


@pytest.mark.asyncio
async def test_get_channel_schedules(manager, sample_data):
    """Test channel schedules retrieval."""
    items = await manager._get_calendar_items(sample_data)
    schedules = await manager._get_channel_schedules(sample_data, items)

    assert isinstance(schedules, list)
    assert len(schedules) == 3
    assert all(isinstance(s, ChannelSchedule) for s in schedules)

    # Check blog schedule
    blog_schedule = next(s for s in schedules if s.channel == "blog")
    assert blog_schedule.frequency == "weekly"
    assert blog_schedule.capacity == 4  # Weekly = 4 posts per month
    assert blog_schedule.current_load == 1  # 1 scheduled blog post


@pytest.mark.asyncio
async def test_get_channel_schedules_capacity(manager):
    """Test channel capacity calculation."""
    data = {
        "items": [],
        "channels": {
            "daily": {"frequency": "daily", "optimal_times": ["09:00"]},
            "weekly": {"frequency": "weekly", "optimal_times": ["09:00"]},
            "biweekly": {"frequency": "biweekly", "optimal_times": ["09:00"]},
            "monthly": {"frequency": "monthly", "optimal_times": ["09:00"]},
        },
    }
    items = await manager._get_calendar_items(data)
    schedules = await manager._get_channel_schedules(data, items)

    daily = next(s for s in schedules if s.channel == "daily")
    weekly = next(s for s in schedules if s.channel == "weekly")
    biweekly = next(s for s in schedules if s.channel == "biweekly")
    monthly = next(s for s in schedules if s.channel == "monthly")

    assert daily.capacity == 30
    assert weekly.capacity == 4
    assert biweekly.capacity == 2
    assert monthly.capacity == 1


@pytest.mark.asyncio
async def test_identify_content_gaps(manager, sample_data):
    """Test content gap identification."""
    items = await manager._get_calendar_items(sample_data)
    gaps = await manager._identify_content_gaps(sample_data, items)

    assert isinstance(gaps, list)
    assert len(gaps) == 2  # teeth whitening, orthodontics (dental implants is covered)
    assert all(isinstance(g, ContentGap) for g in gaps)

    # Check gap structure
    gap = gaps[0]
    assert gap.priority in ["high", "medium", "low"]
    assert len(gap.keyword) > 0
    assert len(gap.reason) > 0


@pytest.mark.asyncio
async def test_identify_content_gaps_all_covered(manager):
    """Test when all keywords are covered."""
    data = {
        "items": [
            {
                "content_id": "content_001",
                "title": "Post 1",
                "content_type": "blog",
                "status": "scheduled",
                "author": "Author",
                "target_keyword": "keyword1",
                "scheduled_date": "2026-05-15T09:00:00",
                "publish_channel": "blog",
                "priority": "high",
                "word_count": 2000,
                "estimated_hours": 8.0,
            },
        ],
        "target_keywords": ["keyword1"],
    }
    items = await manager._get_calendar_items(data)
    gaps = await manager._identify_content_gaps(data, items)

    assert len(gaps) == 0  # All keywords covered


@pytest.mark.asyncio
async def test_generate_deadline_alerts(manager):
    """Test deadline alerts generation."""
    # Create items with different deadlines
    now = datetime.now()
    items = [
        ContentItem(
            content_id="urgent",
            title="Urgent Post",
            content_type="blog",
            status="draft",
            author="Author",
            target_keyword=None,
            scheduled_date=(now + timedelta(hours=12)).isoformat(),  # < 1 day
            publish_channel="blog",
            priority="high",
            word_count=None,
            estimated_hours=8.0,
        ),
        ContentItem(
            content_id="soon",
            title="Soon Post",
            content_type="blog",
            status="review",
            author="Author",
            target_keyword=None,
            scheduled_date=(now + timedelta(days=5)).isoformat(),  # 5 days
            publish_channel="blog",
            priority="high",
            word_count=None,
            estimated_hours=8.0,
        ),
        ContentItem(
            content_id="later",
            title="Later Post",
            content_type="blog",
            status="draft",
            author="Author",
            target_keyword=None,
            scheduled_date=(now + timedelta(days=10)).isoformat(),  # 10 days
            publish_channel="blog",
            priority="high",
            word_count=None,
            estimated_hours=8.0,
        ),
    ]

    alerts = await manager._generate_deadline_alerts(items)

    assert isinstance(alerts, list)
    assert len(alerts) == 2  # Only items within 7 days
    assert all(isinstance(a, DeadlineAlert) for a in alerts)

    # Check urgency levels (sorted by urgency)
    assert alerts[0].urgency in ["critical", "high"]  # Most urgent first
    assert all(a.urgency in ["critical", "high", "medium"] for a in alerts)


@pytest.mark.asyncio
async def test_generate_deadline_alerts_no_alerts(manager):
    """Test when no deadline alerts needed."""
    now = datetime.now()
    items = [
        ContentItem(
            content_id="published",
            title="Published Post",
            content_type="blog",
            status="published",  # Published items don't need alerts
            author="Author",
            target_keyword=None,
            scheduled_date=(now + timedelta(days=1)).isoformat(),
            publish_channel="blog",
            priority="high",
            word_count=None,
            estimated_hours=8.0,
        ),
    ]

    alerts = await manager._generate_deadline_alerts(items)

    assert len(alerts) == 0


@pytest.mark.asyncio
async def test_calculate_metrics(manager, sample_data):
    """Test metrics calculation."""
    items = await manager._get_calendar_items(sample_data)
    metrics = await manager._calculate_metrics(items)

    assert isinstance(metrics, CalendarMetrics)
    assert metrics.total_items == 3
    assert metrics.published_count == 1
    assert metrics.scheduled_count == 1
    assert metrics.draft_count == 1
    assert 0 <= metrics.completion_rate <= 100
    assert metrics.avg_production_time > 0
    assert isinstance(metrics.channel_distribution, dict)


@pytest.mark.asyncio
async def test_calculate_metrics_completion_rate(manager):
    """Test completion rate calculation."""
    items = [
        ContentItem(
            content_id="pub1",
            title="Published 1",
            content_type="blog",
            status="published",
            author="Author",
            target_keyword=None,
            scheduled_date="2026-05-15T09:00:00",
            publish_channel="blog",
            priority="high",
            word_count=None,
            estimated_hours=8.0,
        ),
        ContentItem(
            content_id="pub2",
            title="Published 2",
            content_type="blog",
            status="published",
            author="Author",
            target_keyword=None,
            scheduled_date="2026-05-16T09:00:00",
            publish_channel="blog",
            priority="high",
            word_count=None,
            estimated_hours=8.0,
        ),
        ContentItem(
            content_id="draft1",
            title="Draft 1",
            content_type="blog",
            status="draft",
            author="Author",
            target_keyword=None,
            scheduled_date="2026-05-17T09:00:00",
            publish_channel="blog",
            priority="high",
            word_count=None,
            estimated_hours=8.0,
        ),
    ]

    metrics = await manager._calculate_metrics(items)

    assert metrics.completion_rate == 66.67  # 2/3 * 100


@pytest.mark.asyncio
async def test_generate_recommendations(manager, sample_data):
    """Test recommendations generation."""
    items = await manager._get_calendar_items(sample_data)
    schedules = await manager._get_channel_schedules(sample_data, items)
    gaps = await manager._identify_content_gaps(sample_data, items)
    alerts = await manager._generate_deadline_alerts(items)

    recommendations = await manager._generate_recommendations(
        items, schedules, gaps, alerts
    )

    assert isinstance(recommendations, list)
    # Should have recommendations for content gaps
    assert any("gap" in rec.lower() for rec in recommendations)


@pytest.mark.asyncio
async def test_generate_recommendations_critical_alerts(manager):
    """Test recommendations with critical alerts."""
    now = datetime.now()
    items = [
        ContentItem(
            content_id="urgent",
            title="Urgent",
            content_type="blog",
            status="draft",
            author="Author",
            target_keyword=None,
            scheduled_date=(now + timedelta(hours=12)).isoformat(),
            publish_channel="blog",
            priority="high",
            word_count=None,
            estimated_hours=8.0,
        ),
    ]
    schedules = []
    gaps = []
    alerts = await manager._generate_deadline_alerts(items)

    recommendations = await manager._generate_recommendations(
        items, schedules, gaps, alerts
    )

    assert any("urgent" in rec.lower() for rec in recommendations)


def test_estimate_production_time(manager):
    """Test production time estimation."""
    assert manager._estimate_production_time("blog") == 8.0
    assert manager._estimate_production_time("social") == 2.0
    assert manager._estimate_production_time("email") == 4.0
    assert manager._estimate_production_time("video") == 16.0
    assert manager._estimate_production_time("infographic") == 12.0
    assert manager._estimate_production_time("unknown") == 4.0  # Default
