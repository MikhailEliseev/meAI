"""
Content Calendar Manager - Content Planning and Scheduling.

Manages content calendar, schedules publications, tracks deadlines,
and optimizes content distribution across channels.

Based on: Content Marketing Best Practices + Editorial Calendar Management
"""

import asyncio
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any

import structlog


@dataclass
class ContentItem:
    """Content item in calendar."""

    content_id: str
    title: str
    content_type: str  # blog, social, email, video, infographic
    status: str  # draft, review, scheduled, published
    author: str
    target_keyword: str | None
    scheduled_date: str  # ISO format
    publish_channel: str  # blog, facebook, instagram, linkedin, email
    priority: str  # high, medium, low
    word_count: int | None
    estimated_hours: float


@dataclass
class ChannelSchedule:
    """Publishing schedule for channel."""

    channel: str
    frequency: str  # daily, weekly, biweekly, monthly
    optimal_times: list[str]  # e.g., ["09:00", "14:00", "18:00"]
    next_slot: str  # ISO format
    capacity: int  # Posts per period
    current_load: int  # Scheduled posts


@dataclass
class ContentGap:
    """Content gap identified."""

    topic: str
    keyword: str
    priority: str  # high, medium, low
    reason: str
    suggested_type: str  # blog, video, infographic
    estimated_traffic: int


@dataclass
class DeadlineAlert:
    """Deadline alert."""

    content_id: str
    title: str
    deadline: str  # ISO format
    days_remaining: int
    status: str  # draft, review
    urgency: str  # critical, high, medium


@dataclass
class CalendarMetrics:
    """Calendar performance metrics."""

    total_items: int
    published_count: int
    scheduled_count: int
    draft_count: int
    overdue_count: int
    completion_rate: float  # %
    avg_production_time: float  # hours
    channel_distribution: dict[str, int]


@dataclass
class ContentCalendarReport:
    """Complete content calendar report."""

    period: str
    generated_at: str

    # Core sections
    calendar_items: list[ContentItem]
    channel_schedules: list[ChannelSchedule]
    content_gaps: list[ContentGap]
    deadline_alerts: list[DeadlineAlert]
    metrics: CalendarMetrics

    # Recommendations
    recommendations: list[str]


class ContentCalendarManager:
    """
    Content Calendar Manager.

    Manages content planning, scheduling, and distribution.
    """

    def __init__(self):
        """Initialize Content Calendar Manager."""
        self.logger = structlog.get_logger()

    async def get_calendar(
        self,
        period: str,
        data: dict[str, Any] | None = None,
    ) -> ContentCalendarReport:
        """
        Get content calendar for period.

        Args:
            period: Period (e.g., "2026-05-01 to 2026-05-31")
            data: Calendar data (if None, will fetch)

        Returns:
            Complete content calendar report
        """
        self.logger.info("calendar_fetch_start", period=period)

        # Fetch data if not provided
        if data is None:
            data = await self._fetch_calendar_data(period)

        # Step 1: Get calendar items
        calendar_items = await self._get_calendar_items(data)

        # Step 2: Get channel schedules
        channel_schedules = await self._get_channel_schedules(data, calendar_items)

        # Step 3: Identify content gaps
        content_gaps = await self._identify_content_gaps(data, calendar_items)

        # Step 4: Generate deadline alerts
        deadline_alerts = await self._generate_deadline_alerts(calendar_items)

        # Step 5: Calculate metrics
        metrics = await self._calculate_metrics(calendar_items)

        # Step 6: Generate recommendations
        recommendations = await self._generate_recommendations(
            calendar_items, channel_schedules, content_gaps, deadline_alerts
        )

        report = ContentCalendarReport(
            period=period,
            generated_at=datetime.now().isoformat(),
            calendar_items=calendar_items,
            channel_schedules=channel_schedules,
            content_gaps=content_gaps,
            deadline_alerts=deadline_alerts,
            metrics=metrics,
            recommendations=recommendations,
        )

        self.logger.info(
            "calendar_fetch_complete",
            items_count=len(calendar_items),
            gaps_count=len(content_gaps),
        )

        return report

    async def schedule_content(
        self,
        title: str,
        content_type: str,
        author: str,
        target_date: str,
        channel: str,
        priority: str = "medium",
        target_keyword: str | None = None,
    ) -> ContentItem:
        """
        Schedule new content item.

        Args:
            title: Content title
            content_type: Content type (blog, social, email, video)
            author: Author name
            target_date: Target publish date (ISO format)
            channel: Publish channel
            priority: Priority (high, medium, low)
            target_keyword: Target keyword (optional)

        Returns:
            Created content item
        """
        self.logger.info("content_schedule", title=title, date=target_date)

        # Estimate production time based on content type
        estimated_hours = self._estimate_production_time(content_type)

        content_item = ContentItem(
            content_id=f"content_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            title=title,
            content_type=content_type,
            status="draft",
            author=author,
            target_keyword=target_keyword,
            scheduled_date=target_date,
            publish_channel=channel,
            priority=priority,
            word_count=None,
            estimated_hours=estimated_hours,
        )

        return content_item

    async def _fetch_calendar_data(self, period: str) -> dict[str, Any]:
        """Fetch calendar data from content management system."""
        # Mock data for now (will integrate with real CMS)
        return {
            "items": [
                {
                    "content_id": "content_001",
                    "title": "Dental Implants Guide 2026",
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
                    "title": "Patient Success Story",
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
                    "title": "Monthly Newsletter",
                    "content_type": "email",
                    "status": "review",
                    "author": "Content Team",
                    "target_keyword": None,
                    "scheduled_date": "2026-05-20T10:00:00",
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

    async def _get_calendar_items(self, data: dict[str, Any]) -> list[ContentItem]:
        """Get calendar items from data."""
        items_data = data.get("items", [])
        items = []

        for item_data in items_data:
            items.append(
                ContentItem(
                    content_id=item_data["content_id"],
                    title=item_data["title"],
                    content_type=item_data["content_type"],
                    status=item_data["status"],
                    author=item_data["author"],
                    target_keyword=item_data.get("target_keyword"),
                    scheduled_date=item_data["scheduled_date"],
                    publish_channel=item_data["publish_channel"],
                    priority=item_data["priority"],
                    word_count=item_data.get("word_count"),
                    estimated_hours=item_data["estimated_hours"],
                )
            )

        # Sort by scheduled date
        items.sort(key=lambda x: x.scheduled_date)

        return items

    async def _get_channel_schedules(
        self, data: dict[str, Any], items: list[ContentItem]
    ) -> list[ChannelSchedule]:
        """Get channel schedules."""
        channels_data = data.get("channels", {})
        schedules = []

        for channel, config in channels_data.items():
            # Count scheduled items for this channel
            scheduled_count = sum(
                1 for item in items if item.publish_channel == channel and item.status == "scheduled"
            )

            # Calculate capacity based on frequency
            frequency = config.get("frequency", "weekly")
            if frequency == "daily":
                capacity = 30
            elif frequency == "weekly":
                capacity = 4
            elif frequency == "biweekly":
                capacity = 2
            else:  # monthly
                capacity = 1

            # Find next available slot
            optimal_times = config.get("optimal_times", ["09:00"])
            next_slot = datetime.now() + timedelta(days=1)
            next_slot = next_slot.replace(
                hour=int(optimal_times[0].split(":")[0]),
                minute=int(optimal_times[0].split(":")[1]),
            )

            schedules.append(
                ChannelSchedule(
                    channel=channel,
                    frequency=frequency,
                    optimal_times=optimal_times,
                    next_slot=next_slot.isoformat(),
                    capacity=capacity,
                    current_load=scheduled_count,
                )
            )

        return schedules

    async def _identify_content_gaps(
        self, data: dict[str, Any], items: list[ContentItem]
    ) -> list[ContentGap]:
        """Identify content gaps."""
        target_keywords = data.get("target_keywords", [])
        gaps = []

        # Check which keywords don't have content
        covered_keywords = {item.target_keyword for item in items if item.target_keyword}

        for keyword in target_keywords:
            if keyword not in covered_keywords:
                gaps.append(
                    ContentGap(
                        topic=keyword.title(),
                        keyword=keyword,
                        priority="high",
                        reason="No content targeting this keyword",
                        suggested_type="blog",
                        estimated_traffic=1000,
                    )
                )

        return gaps

    async def _generate_deadline_alerts(
        self, items: list[ContentItem]
    ) -> list[DeadlineAlert]:
        """Generate deadline alerts."""
        alerts = []
        now = datetime.now()

        for item in items:
            if item.status in ["draft", "review"]:
                scheduled = datetime.fromisoformat(item.scheduled_date)
                days_remaining = (scheduled - now).days

                # Alert if deadline is within 7 days
                if days_remaining <= 7:
                    if days_remaining <= 1:
                        urgency = "critical"
                    elif days_remaining <= 3:
                        urgency = "high"
                    else:
                        urgency = "medium"

                    alerts.append(
                        DeadlineAlert(
                            content_id=item.content_id,
                            title=item.title,
                            deadline=item.scheduled_date,
                            days_remaining=days_remaining,
                            status=item.status,
                            urgency=urgency,
                        )
                    )

        # Sort by urgency and days remaining
        urgency_order = {"critical": 0, "high": 1, "medium": 2}
        alerts.sort(key=lambda x: (urgency_order[x.urgency], x.days_remaining))

        return alerts

    async def _calculate_metrics(self, items: list[ContentItem]) -> CalendarMetrics:
        """Calculate calendar metrics."""
        total_items = len(items)
        published_count = sum(1 for item in items if item.status == "published")
        scheduled_count = sum(1 for item in items if item.status == "scheduled")
        draft_count = sum(1 for item in items if item.status == "draft")

        # Count overdue items
        now = datetime.now()
        overdue_count = sum(
            1
            for item in items
            if item.status in ["draft", "review"]
            and datetime.fromisoformat(item.scheduled_date) < now
        )

        # Completion rate
        completion_rate = (
            (published_count / total_items * 100) if total_items > 0 else 0.0
        )

        # Average production time
        items_with_time = [item for item in items if item.estimated_hours]
        avg_production_time = (
            sum(item.estimated_hours for item in items_with_time) / len(items_with_time)
            if items_with_time
            else 0.0
        )

        # Channel distribution
        channel_distribution = {}
        for item in items:
            channel = item.publish_channel
            channel_distribution[channel] = channel_distribution.get(channel, 0) + 1

        return CalendarMetrics(
            total_items=total_items,
            published_count=published_count,
            scheduled_count=scheduled_count,
            draft_count=draft_count,
            overdue_count=overdue_count,
            completion_rate=round(completion_rate, 2),
            avg_production_time=round(avg_production_time, 2),
            channel_distribution=channel_distribution,
        )

    async def _generate_recommendations(
        self,
        items: list[ContentItem],
        schedules: list[ChannelSchedule],
        gaps: list[ContentGap],
        alerts: list[DeadlineAlert],
    ) -> list[str]:
        """Generate recommendations."""
        recommendations = []

        # Deadline alerts
        critical_alerts = [a for a in alerts if a.urgency == "critical"]
        if critical_alerts:
            recommendations.append(
                f"URGENT: {len(critical_alerts)} content item(s) due within 24 hours"
            )

        # Content gaps
        high_priority_gaps = [g for g in gaps if g.priority == "high"]
        if high_priority_gaps:
            recommendations.append(
                f"Fill {len(high_priority_gaps)} high-priority content gap(s)"
            )

        # Channel capacity
        overloaded_channels = [s for s in schedules if s.current_load > s.capacity * 0.8]
        if overloaded_channels:
            channel_names = ", ".join([s.channel for s in overloaded_channels])
            recommendations.append(
                f"Reduce load on {channel_names} (near capacity)"
            )

        # Underutilized channels
        underutilized = [s for s in schedules if s.current_load < s.capacity * 0.5]
        if underutilized:
            channel_names = ", ".join([s.channel for s in underutilized])
            recommendations.append(
                f"Increase content for {channel_names} (underutilized)"
            )

        return recommendations

    def _estimate_production_time(self, content_type: str) -> float:
        """Estimate production time based on content type."""
        estimates = {
            "blog": 8.0,  # hours
            "social": 2.0,
            "email": 4.0,
            "video": 16.0,
            "infographic": 12.0,
        }
        return estimates.get(content_type, 4.0)
