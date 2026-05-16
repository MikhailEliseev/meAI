"""Analytics Schemas

Pydantic models for analytics metrics and reports.

Part of: Phase 11 Sprint 2 - Task 2.5
"""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class TimeSeriesPoint(BaseModel):
    """Single point in time series data."""

    timestamp: datetime = Field(..., description="Point timestamp")
    value: float = Field(..., description="Metric value")
    label: str = Field(..., description="Human-readable label (e.g., '2026-05-16', 'Week 20')")


class LeadMetrics(BaseModel):
    """Lead acquisition and scoring metrics."""

    # Totals
    total_leads: int = Field(..., description="Total leads captured")
    leads_by_tier: dict[str, int] = Field(
        ..., description="Leads grouped by tier (hot/warm/cold)"
    )
    leads_by_source: dict[str, int] = Field(
        ..., description="Leads grouped by source (landing_page, referral, etc.)"
    )
    leads_by_specialty: dict[str, int] = Field(
        ..., description="Leads grouped by medical specialty"
    )

    # Averages
    average_score: float = Field(..., description="Average lead score (0-100)")
    capture_rate: float = Field(..., description="Leads captured per day")

    # Rates
    duplicate_rate: float = Field(
        ..., description="Percentage of duplicate submissions"
    )

    # Time series
    time_series: list[TimeSeriesPoint] = Field(
        ..., description="Lead capture over time"
    )

    # Metadata
    start_date: datetime = Field(..., description="Metrics start date")
    end_date: datetime = Field(..., description="Metrics end date")
    generated_at: datetime = Field(
        default_factory=datetime.utcnow, description="When metrics were generated"
    )


class EmailMetrics(BaseModel):
    """Email campaign performance metrics."""

    # Totals
    total_sent: int = Field(..., description="Total emails sent")
    total_scheduled: int = Field(..., description="Total emails scheduled")
    total_failed: int = Field(..., description="Total emails failed")
    total_delivered: int = Field(..., description="Total emails delivered")
    total_opened: int = Field(..., description="Total emails opened")
    total_clicked: int = Field(..., description="Total emails clicked")
    total_bounced: int = Field(..., description="Total emails bounced")
    total_complained: int = Field(..., description="Total spam complaints")
    total_unsubscribed: int = Field(..., description="Total unsubscribes")

    # Rates (percentages)
    delivery_rate: float = Field(..., description="Delivery rate (delivered/sent)")
    open_rate: float = Field(..., description="Open rate (opened/delivered)")
    click_rate: float = Field(..., description="Click rate (clicked/opened)")
    bounce_rate: float = Field(..., description="Bounce rate (bounced/sent)")
    complaint_rate: float = Field(..., description="Complaint rate (complained/sent)")
    unsubscribe_rate: float = Field(
        ..., description="Unsubscribe rate (unsubscribed/sent)"
    )

    # By tier
    emails_by_tier: dict[str, int] = Field(
        ..., description="Emails grouped by workflow tier (hot/warm/cold)"
    )

    # Timing
    avg_time_to_open: Optional[float] = Field(
        None, description="Average time to open (minutes)"
    )
    avg_time_to_click: Optional[float] = Field(
        None, description="Average time to click (minutes)"
    )

    # Time series
    time_series: list[TimeSeriesPoint] = Field(
        ..., description="Email sends over time"
    )

    # Metadata
    start_date: datetime = Field(..., description="Metrics start date")
    end_date: datetime = Field(..., description="Metrics end date")
    generated_at: datetime = Field(
        default_factory=datetime.utcnow, description="When metrics were generated"
    )


class ConversionFunnel(BaseModel):
    """Lead conversion funnel metrics."""

    # Funnel stages
    leads_captured: int = Field(..., description="Total leads captured")
    leads_scored: int = Field(..., description="Leads with score assigned")
    tasks_created: int = Field(..., description="Linear tasks created")
    workflows_triggered: int = Field(..., description="Email workflows triggered")
    emails_sent: int = Field(..., description="Emails sent")
    emails_delivered: int = Field(..., description="Emails delivered")
    emails_opened: int = Field(..., description="Emails opened")
    emails_clicked: int = Field(..., description="Emails clicked")

    # Conversion rates (percentages)
    conversion_rates: dict[str, float] = Field(
        ...,
        description="Conversion rates between stages",
        example={
            "capture_to_score": 95.0,
            "score_to_task": 30.0,
            "task_to_workflow": 100.0,
            "workflow_to_sent": 90.0,
            "sent_to_delivered": 98.0,
            "delivered_to_opened": 25.0,
            "opened_to_clicked": 15.0,
        },
    )

    # Metadata
    start_date: datetime = Field(..., description="Metrics start date")
    end_date: datetime = Field(..., description="Metrics end date")
    generated_at: datetime = Field(
        default_factory=datetime.utcnow, description="When metrics were generated"
    )


class RealTimeStats(BaseModel):
    """Real-time statistics for current day."""

    # Today's counts
    leads_today: int = Field(..., description="Leads captured today")
    emails_sent_today: int = Field(..., description="Emails sent today")
    emails_opened_today: int = Field(..., description="Emails opened today")
    emails_clicked_today: int = Field(..., description="Emails clicked today")

    # Active counts
    active_workflows: int = Field(..., description="Active email workflows")
    pending_emails: int = Field(..., description="Pending scheduled emails")

    # Hot leads
    hot_leads_count: int = Field(..., description="Total hot leads (score >= 80)")
    hot_leads_today: int = Field(..., description="Hot leads captured today")

    # Metadata
    last_updated: datetime = Field(
        default_factory=datetime.utcnow, description="When stats were last updated"
    )


class AnalyticsExportRequest(BaseModel):
    """Request for analytics export."""

    start_date: datetime = Field(..., description="Export start date")
    end_date: datetime = Field(..., description="Export end date")
    format: str = Field(
        "csv",
        description="Export format",
        pattern="^(csv|json|pdf)$",
    )
    include_charts: bool = Field(
        False, description="Include charts in PDF export"
    )


class AnalyticsExportResponse(BaseModel):
    """Response for analytics export."""

    file_path: str = Field(..., description="Path to exported file")
    file_size: int = Field(..., description="File size in bytes")
    format: str = Field(..., description="Export format")
    generated_at: datetime = Field(
        default_factory=datetime.utcnow, description="When export was generated"
    )
