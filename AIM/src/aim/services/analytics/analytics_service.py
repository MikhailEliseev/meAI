"""Analytics Service

Aggregates and calculates metrics for leads, emails, and conversions.

Part of: Phase 11 Sprint 2 - Task 2.5
"""

import logging
from datetime import datetime, timedelta, timezone
from typing import Optional

from sqlalchemy import func, select, and_, case
from sqlalchemy.ext.asyncio import AsyncSession

from src.aim.models import (
    Lead,
    EmailWorkflow,
    ScheduledEmail,
    EmailEvent,
    LinearTask,
)
from src.aim.schemas.analytics import (
    LeadMetrics,
    EmailMetrics,
    ConversionFunnel,
    RealTimeStats,
    TimeSeriesPoint,
)

logger = logging.getLogger(__name__)


class AnalyticsService:
    """Service for calculating analytics metrics.

    Responsibilities:
    - Aggregate lead metrics (capture, scoring, tiers)
    - Calculate email metrics (engagement, delivery)
    - Generate conversion funnel
    - Provide real-time statistics
    - Generate time-series data

    Example:
        service = AnalyticsService(db_session)

        # Get lead metrics
        lead_metrics = await service.get_lead_metrics(
            start_date=datetime(2026, 5, 1),
            end_date=datetime(2026, 5, 16),
            tier="hot",
        )

        # Get email metrics
        email_metrics = await service.get_email_metrics(
            start_date=datetime(2026, 5, 1),
            end_date=datetime(2026, 5, 16),
        )

        # Get conversion funnel
        funnel = await service.get_conversion_funnel(
            start_date=datetime(2026, 5, 1),
            end_date=datetime(2026, 5, 16),
        )

        # Get real-time stats
        stats = await service.get_real_time_stats()
    """

    def __init__(self, db: AsyncSession):
        """Initialize analytics service.

        Args:
            db: Database session
        """
        self.db = db

    async def get_lead_metrics(
        self,
        start_date: datetime,
        end_date: datetime,
        tier: Optional[str] = None,
    ) -> LeadMetrics:
        """Get lead acquisition and scoring metrics.

        Args:
            start_date: Start date for metrics
            end_date: End date for metrics
            tier: Optional tier filter (hot/warm/cold)

        Returns:
            LeadMetrics with aggregated data
        """
        # Base query
        query = select(Lead).where(
            and_(
                Lead.created_at >= start_date,
                Lead.created_at <= end_date,
            )
        )

        if tier:
            query = query.where(Lead.tier == tier)

        result = await self.db.execute(query)
        leads = result.scalars().all()

        # Total leads
        total_leads = len(leads)

        # Leads by tier
        leads_by_tier = {}
        for lead in leads:
            tier_key = lead.tier or "unknown"
            leads_by_tier[tier_key] = leads_by_tier.get(tier_key, 0) + 1

        # Leads by source
        leads_by_source = {}
        for lead in leads:
            source_key = lead.source or "unknown"
            leads_by_source[source_key] = leads_by_source.get(source_key, 0) + 1

        # Leads by specialty
        leads_by_specialty = {}
        for lead in leads:
            specialty_key = lead.specialty or "unknown"
            leads_by_specialty[specialty_key] = (
                leads_by_specialty.get(specialty_key, 0) + 1
            )

        # Average score
        scores = [lead.score for lead in leads if lead.score is not None]
        average_score = sum(scores) / len(scores) if scores else 0.0

        # Capture rate (leads per day)
        days = (end_date - start_date).days + 1
        capture_rate = total_leads / days if days > 0 else 0.0

        # Duplicate rate
        # Count leads with same email hash
        email_hashes = [lead.email_hash for lead in leads]
        unique_hashes = len(set(email_hashes))
        duplicate_count = total_leads - unique_hashes
        duplicate_rate = (
            (duplicate_count / total_leads * 100) if total_leads > 0 else 0.0
        )

        # Time series (leads per day)
        time_series = await self._calculate_lead_time_series(
            start_date, end_date, tier
        )

        return LeadMetrics(
            total_leads=total_leads,
            leads_by_tier=leads_by_tier,
            leads_by_source=leads_by_source,
            leads_by_specialty=leads_by_specialty,
            average_score=average_score,
            capture_rate=capture_rate,
            duplicate_rate=duplicate_rate,
            time_series=time_series,
            start_date=start_date,
            end_date=end_date,
        )

    async def get_email_metrics(
        self,
        start_date: datetime,
        end_date: datetime,
        tier: Optional[str] = None,
    ) -> EmailMetrics:
        """Get email campaign performance metrics.

        Args:
            start_date: Start date for metrics
            end_date: End date for metrics
            tier: Optional workflow tier filter (hot/warm/cold)

        Returns:
            EmailMetrics with engagement data
        """
        # Query scheduled emails
        query = select(ScheduledEmail).where(
            and_(
                ScheduledEmail.scheduled_at >= start_date,
                ScheduledEmail.scheduled_at <= end_date,
            )
        )

        if tier:
            # Join with workflow to filter by tier
            query = query.join(EmailWorkflow).where(EmailWorkflow.tier == tier)

        result = await self.db.execute(query)
        emails = result.scalars().all()

        # Total counts
        total_sent = sum(1 for e in emails if e.status == "sent")
        total_scheduled = sum(1 for e in emails if e.status == "pending")
        total_failed = sum(1 for e in emails if e.status == "failed")

        # Query email events
        email_ids = [e.id for e in emails if e.status == "sent"]

        if email_ids:
            events_query = select(EmailEvent).where(
                EmailEvent.email_id.in_(email_ids)
            )
            events_result = await self.db.execute(events_query)
            events = events_result.scalars().all()
        else:
            events = []

        # Count events by type
        total_delivered = sum(1 for e in events if e.event_type == "delivered")
        total_opened = sum(1 for e in events if e.event_type == "opened")
        total_clicked = sum(1 for e in events if e.event_type == "clicked")
        total_bounced = sum(1 for e in events if e.event_type == "bounced")
        total_complained = sum(1 for e in events if e.event_type == "complained")
        total_unsubscribed = sum(
            1 for e in events if e.event_type == "unsubscribed"
        )

        # Calculate rates
        delivery_rate = (
            (total_delivered / total_sent * 100) if total_sent > 0 else 0.0
        )
        open_rate = (
            (total_opened / total_delivered * 100) if total_delivered > 0 else 0.0
        )
        click_rate = (
            (total_clicked / total_opened * 100) if total_opened > 0 else 0.0
        )
        bounce_rate = (
            (total_bounced / total_sent * 100) if total_sent > 0 else 0.0
        )
        complaint_rate = (
            (total_complained / total_sent * 100) if total_sent > 0 else 0.0
        )
        unsubscribe_rate = (
            (total_unsubscribed / total_sent * 100) if total_sent > 0 else 0.0
        )

        # Emails by tier
        emails_by_tier = {}
        for email in emails:
            # Get workflow tier
            workflow_query = select(EmailWorkflow).where(
                EmailWorkflow.id == email.workflow_id
            )
            workflow_result = await self.db.execute(workflow_query)
            workflow = workflow_result.scalar_one_or_none()

            if workflow:
                tier_key = workflow.tier or "unknown"
                emails_by_tier[tier_key] = emails_by_tier.get(tier_key, 0) + 1

        # Average time to open/click
        avg_time_to_open = await self._calculate_avg_time_to_event(
            emails, events, "opened"
        )
        avg_time_to_click = await self._calculate_avg_time_to_event(
            emails, events, "clicked"
        )

        # Time series (emails sent per day)
        time_series = await self._calculate_email_time_series(
            start_date, end_date, tier
        )

        return EmailMetrics(
            total_sent=total_sent,
            total_scheduled=total_scheduled,
            total_failed=total_failed,
            total_delivered=total_delivered,
            total_opened=total_opened,
            total_clicked=total_clicked,
            total_bounced=total_bounced,
            total_complained=total_complained,
            total_unsubscribed=total_unsubscribed,
            delivery_rate=delivery_rate,
            open_rate=open_rate,
            click_rate=click_rate,
            bounce_rate=bounce_rate,
            complaint_rate=complaint_rate,
            unsubscribe_rate=unsubscribe_rate,
            emails_by_tier=emails_by_tier,
            avg_time_to_open=avg_time_to_open,
            avg_time_to_click=avg_time_to_click,
            time_series=time_series,
            start_date=start_date,
            end_date=end_date,
        )

    async def get_conversion_funnel(
        self,
        start_date: datetime,
        end_date: datetime,
    ) -> ConversionFunnel:
        """Get lead conversion funnel metrics.

        Args:
            start_date: Start date for metrics
            end_date: End date for metrics

        Returns:
            ConversionFunnel with stage counts and conversion rates
        """
        # Query leads
        leads_query = select(Lead).where(
            and_(
                Lead.created_at >= start_date,
                Lead.created_at <= end_date,
            )
        )
        leads_result = await self.db.execute(leads_query)
        leads = leads_result.scalars().all()
        lead_ids = [lead.id for lead in leads]

        # Stage 1: Leads captured
        leads_captured = len(leads)

        # Stage 2: Leads scored
        leads_scored = sum(1 for lead in leads if lead.score is not None)

        # Stage 3: Tasks created
        if lead_ids:
            tasks_query = select(func.count(LinearTask.id)).where(
                LinearTask.lead_id.in_(lead_ids)
            )
            tasks_result = await self.db.execute(tasks_query)
            tasks_created = tasks_result.scalar() or 0
        else:
            tasks_created = 0

        # Stage 4: Workflows triggered
        if lead_ids:
            workflows_query = select(func.count(EmailWorkflow.id)).where(
                EmailWorkflow.lead_id.in_(lead_ids)
            )
            workflows_result = await self.db.execute(workflows_query)
            workflows_triggered = workflows_result.scalar() or 0
        else:
            workflows_triggered = 0

        # Stage 5: Emails sent
        if lead_ids:
            emails_query = (
                select(func.count(ScheduledEmail.id))
                .join(EmailWorkflow)
                .where(
                    and_(
                        EmailWorkflow.lead_id.in_(lead_ids),
                        ScheduledEmail.status == "sent",
                    )
                )
            )
            emails_result = await self.db.execute(emails_query)
            emails_sent = emails_result.scalar() or 0
        else:
            emails_sent = 0

        # Stage 6: Emails delivered
        if lead_ids:
            delivered_query = (
                select(func.count(func.distinct(EmailEvent.email_id)))
                .join(ScheduledEmail)
                .join(EmailWorkflow)
                .where(
                    and_(
                        EmailWorkflow.lead_id.in_(lead_ids),
                        EmailEvent.event_type == "delivered",
                    )
                )
            )
            delivered_result = await self.db.execute(delivered_query)
            emails_delivered = delivered_result.scalar() or 0
        else:
            emails_delivered = 0

        # Stage 7: Emails opened
        if lead_ids:
            opened_query = (
                select(func.count(func.distinct(EmailEvent.email_id)))
                .join(ScheduledEmail)
                .join(EmailWorkflow)
                .where(
                    and_(
                        EmailWorkflow.lead_id.in_(lead_ids),
                        EmailEvent.event_type == "opened",
                    )
                )
            )
            opened_result = await self.db.execute(opened_query)
            emails_opened = opened_result.scalar() or 0
        else:
            emails_opened = 0

        # Stage 8: Emails clicked
        if lead_ids:
            clicked_query = (
                select(func.count(func.distinct(EmailEvent.email_id)))
                .join(ScheduledEmail)
                .join(EmailWorkflow)
                .where(
                    and_(
                        EmailWorkflow.lead_id.in_(lead_ids),
                        EmailEvent.event_type == "clicked",
                    )
                )
            )
            clicked_result = await self.db.execute(clicked_query)
            emails_clicked = clicked_result.scalar() or 0
        else:
            emails_clicked = 0

        # Calculate conversion rates
        conversion_rates = {
            "capture_to_score": (
                (leads_scored / leads_captured * 100)
                if leads_captured > 0
                else 0.0
            ),
            "score_to_task": (
                (tasks_created / leads_scored * 100) if leads_scored > 0 else 0.0
            ),
            "task_to_workflow": (
                (workflows_triggered / tasks_created * 100)
                if tasks_created > 0
                else 0.0
            ),
            "workflow_to_sent": (
                (emails_sent / workflows_triggered * 100)
                if workflows_triggered > 0
                else 0.0
            ),
            "sent_to_delivered": (
                (emails_delivered / emails_sent * 100) if emails_sent > 0 else 0.0
            ),
            "delivered_to_opened": (
                (emails_opened / emails_delivered * 100)
                if emails_delivered > 0
                else 0.0
            ),
            "opened_to_clicked": (
                (emails_clicked / emails_opened * 100)
                if emails_opened > 0
                else 0.0
            ),
        }

        return ConversionFunnel(
            leads_captured=leads_captured,
            leads_scored=leads_scored,
            tasks_created=tasks_created,
            workflows_triggered=workflows_triggered,
            emails_sent=emails_sent,
            emails_delivered=emails_delivered,
            emails_opened=emails_opened,
            emails_clicked=emails_clicked,
            conversion_rates=conversion_rates,
            start_date=start_date,
            end_date=end_date,
        )

    async def get_real_time_stats(self) -> RealTimeStats:
        """Get real-time statistics for current day.

        Returns:
            RealTimeStats with today's counts
        """
        # Today's date range
        today_start = datetime.now(timezone.utc).replace(
            hour=0, minute=0, second=0, microsecond=0
        )
        today_end = datetime.now(timezone.utc)

        # Leads today
        leads_today_query = select(func.count(Lead.id)).where(
            Lead.created_at >= today_start
        )
        leads_today_result = await self.db.execute(leads_today_query)
        leads_today = leads_today_result.scalar() or 0

        # Emails sent today
        emails_sent_today_query = select(func.count(ScheduledEmail.id)).where(
            and_(
                ScheduledEmail.sent_at >= today_start,
                ScheduledEmail.status == "sent",
            )
        )
        emails_sent_today_result = await self.db.execute(emails_sent_today_query)
        emails_sent_today = emails_sent_today_result.scalar() or 0

        # Emails opened today
        emails_opened_today_query = select(
            func.count(func.distinct(EmailEvent.email_id))
        ).where(
            and_(
                EmailEvent.occurred_at >= today_start,
                EmailEvent.event_type == "opened",
            )
        )
        emails_opened_today_result = await self.db.execute(
            emails_opened_today_query
        )
        emails_opened_today = emails_opened_today_result.scalar() or 0

        # Emails clicked today
        emails_clicked_today_query = select(
            func.count(func.distinct(EmailEvent.email_id))
        ).where(
            and_(
                EmailEvent.occurred_at >= today_start,
                EmailEvent.event_type == "clicked",
            )
        )
        emails_clicked_today_result = await self.db.execute(
            emails_clicked_today_query
        )
        emails_clicked_today = emails_clicked_today_result.scalar() or 0

        # Active workflows
        active_workflows_query = select(func.count(EmailWorkflow.id)).where(
            EmailWorkflow.status == "active"
        )
        active_workflows_result = await self.db.execute(active_workflows_query)
        active_workflows = active_workflows_result.scalar() or 0

        # Pending emails
        pending_emails_query = select(func.count(ScheduledEmail.id)).where(
            ScheduledEmail.status == "pending"
        )
        pending_emails_result = await self.db.execute(pending_emails_query)
        pending_emails = pending_emails_result.scalar() or 0

        # Hot leads (score >= 80)
        hot_leads_query = select(func.count(Lead.id)).where(Lead.tier == "hot")
        hot_leads_result = await self.db.execute(hot_leads_query)
        hot_leads_count = hot_leads_result.scalar() or 0

        # Hot leads today
        hot_leads_today_query = select(func.count(Lead.id)).where(
            and_(
                Lead.created_at >= today_start,
                Lead.tier == "hot",
            )
        )
        hot_leads_today_result = await self.db.execute(hot_leads_today_query)
        hot_leads_today = hot_leads_today_result.scalar() or 0

        return RealTimeStats(
            leads_today=leads_today,
            emails_sent_today=emails_sent_today,
            emails_opened_today=emails_opened_today,
            emails_clicked_today=emails_clicked_today,
            active_workflows=active_workflows,
            pending_emails=pending_emails,
            hot_leads_count=hot_leads_count,
            hot_leads_today=hot_leads_today,
        )

    async def _calculate_lead_time_series(
        self,
        start_date: datetime,
        end_date: datetime,
        tier: Optional[str] = None,
    ) -> list[TimeSeriesPoint]:
        """Calculate time series for lead capture.

        Args:
            start_date: Start date
            end_date: End date
            tier: Optional tier filter

        Returns:
            List of TimeSeriesPoint with daily lead counts
        """
        # Query leads grouped by date
        query = (
            select(
                func.date(Lead.created_at).label("date"),
                func.count(Lead.id).label("count"),
            )
            .where(
                and_(
                    Lead.created_at >= start_date,
                    Lead.created_at <= end_date,
                )
            )
            .group_by(func.date(Lead.created_at))
            .order_by(func.date(Lead.created_at))
        )

        if tier:
            query = query.where(Lead.tier == tier)

        result = await self.db.execute(query)
        rows = result.all()

        # Convert to TimeSeriesPoint
        time_series = []
        for row in rows:
            date_obj = row.date
            if isinstance(date_obj, str):
                date_obj = datetime.strptime(date_obj, "%Y-%m-%d")

            time_series.append(
                TimeSeriesPoint(
                    timestamp=date_obj,
                    value=float(row.count),
                    label=date_obj.strftime("%Y-%m-%d"),
                )
            )

        return time_series

    async def _calculate_email_time_series(
        self,
        start_date: datetime,
        end_date: datetime,
        tier: Optional[str] = None,
    ) -> list[TimeSeriesPoint]:
        """Calculate time series for email sends.

        Args:
            start_date: Start date
            end_date: End date
            tier: Optional tier filter

        Returns:
            List of TimeSeriesPoint with daily email counts
        """
        # Query emails grouped by date
        query = (
            select(
                func.date(ScheduledEmail.sent_at).label("date"),
                func.count(ScheduledEmail.id).label("count"),
            )
            .where(
                and_(
                    ScheduledEmail.sent_at >= start_date,
                    ScheduledEmail.sent_at <= end_date,
                    ScheduledEmail.status == "sent",
                )
            )
            .group_by(func.date(ScheduledEmail.sent_at))
            .order_by(func.date(ScheduledEmail.sent_at))
        )

        if tier:
            query = query.join(EmailWorkflow).where(EmailWorkflow.tier == tier)

        result = await self.db.execute(query)
        rows = result.all()

        # Convert to TimeSeriesPoint
        time_series = []
        for row in rows:
            date_obj = row.date
            if isinstance(date_obj, str):
                date_obj = datetime.strptime(date_obj, "%Y-%m-%d")

            time_series.append(
                TimeSeriesPoint(
                    timestamp=date_obj,
                    value=float(row.count),
                    label=date_obj.strftime("%Y-%m-%d"),
                )
            )

        return time_series

    async def _calculate_avg_time_to_event(
        self,
        emails: list[ScheduledEmail],
        events: list[EmailEvent],
        event_type: str,
    ) -> Optional[float]:
        """Calculate average time from send to event.

        Args:
            emails: List of scheduled emails
            events: List of email events
            event_type: Event type to calculate (opened/clicked)

        Returns:
            Average time in minutes, or None if no events
        """
        times = []

        for email in emails:
            if not email.sent_at:
                continue

            # Find first event of this type for this email
            email_events = [
                e for e in events
                if e.email_id == email.id and e.event_type == event_type
            ]

            if email_events:
                # Sort by occurred_at
                email_events.sort(key=lambda e: e.occurred_at)
                first_event = email_events[0]

                # Calculate time difference
                time_diff = (first_event.occurred_at - email.sent_at).total_seconds() / 60
                times.append(time_diff)

        return sum(times) / len(times) if times else None
