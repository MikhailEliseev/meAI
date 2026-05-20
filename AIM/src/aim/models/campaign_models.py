"""Campaign, AdGroup, and Experiment SQLAlchemy Models.

Part of: Phase 13 — Marketing Campaigns Launch + Analytics
"""

from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from aim.storage.models import Base


class Campaign(Base):
    """Marketing campaign model — tracks ad campaigns across platforms."""

    __tablename__ = "campaigns"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    external_id: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    platform: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="active")
    daily_budget: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    currency: Mapped[str] = mapped_column(String(10), nullable=False, default="RUB")
    total_spent: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    utm_source: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    utm_campaign: Mapped[Optional[str]] = mapped_column(String(100), nullable=True, index=True)
    utm_medium: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    start_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    end_date: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )


class CampaignAttribution(Base):
    """Links campaign clicks to lead conversions via UTM parameters."""

    __tablename__ = "campaign_attributions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    campaign_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("campaigns.id"), nullable=False, index=True
    )
    lead_id: Mapped[str] = mapped_column(
        String(50), ForeignKey("leads.id"), nullable=False, index=True
    )
    utm_source: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    utm_campaign: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    utm_medium: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    attributed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    is_conversion: Mapped[bool] = mapped_column(default=False)
    conversion_revenue: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    conversion_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)


class Experiment(Base):
    """A/B test experiment tracking model."""

    __tablename__ = "experiments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    variant_a_name: Mapped[str] = mapped_column(String(100), nullable=False)
    variant_b_name: Mapped[str] = mapped_column(String(100), nullable=False)
    metric_name: Mapped[str] = mapped_column(String(100), nullable=False)
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="running")
    visitors_a: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    conversions_a: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    visitors_b: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    conversions_b: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    winner: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)
    p_value: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    relative_lift: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
