"""Pydantic schemas for content gap analysis."""

from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class GapType(str, Enum):
    """Type of content gap."""

    MISSING_TOPIC = "missing_topic"
    MISSING_URL = "missing_url"
    MISSING_KEYWORD = "missing_keyword"
    UNDERREPRESENTED = "underrepresented"


class GapSeverity(str, Enum):
    """Severity of content gap."""

    HIGH = "high"  # Missing completely (0 pages)
    MEDIUM = "medium"  # Underrepresented (1-2 pages vs 5+)
    LOW = "low"  # Comparable coverage


class ContentGap(BaseModel):
    """Content gap detected between client and competitors."""

    model_config = ConfigDict(use_enum_values=True)

    topic: str = Field(..., description="Topic or keyword of the gap")
    gap_type: GapType = Field(..., description="Type of gap")
    severity: GapSeverity = Field(..., description="Severity of gap")
    opportunity_score: float = Field(
        ..., ge=0.0, le=100.0, description="Opportunity score (0-100)"
    )
    priority: str = Field(..., description="Priority tier (P0-P3)")
    competitor_coverage: list[dict[str, Any]] = Field(
        default_factory=list,
        description="Competitor pages covering this topic",
    )
    recommended_actions: list[str] = Field(
        default_factory=list,
        description="Recommended actions to close the gap",
    )
    target_keywords: list[str] = Field(
        default_factory=list,
        description="Target keywords for this gap",
    )
    recommended_content_type: str = Field(
        default="blog_post",
        description="Recommended content type",
    )
    estimated_traffic_potential: int = Field(
        default=0,
        ge=0,
        description="Estimated traffic potential",
    )
    detected_at: datetime = Field(
        default_factory=lambda: datetime.now(),
        description="When gap was detected",
    )


class GapAnalysisResult(BaseModel):
    """Result of gap analysis."""

    model_config = ConfigDict(use_enum_values=True)

    gaps: list[ContentGap] = Field(
        default_factory=list,
        description="Detected content gaps",
    )
    client_pages_analyzed: int = Field(
        default=0,
        ge=0,
        description="Number of client pages analyzed",
    )
    competitor_pages_analyzed: int = Field(
        default=0,
        ge=0,
        description="Number of competitor pages analyzed",
    )
    topics_discovered: int = Field(
        default=0,
        ge=0,
        description="Number of topics discovered",
    )
    cluster_quality: str = Field(
        default="unknown",
        description="Cluster quality classification",
    )
    analysis_time_seconds: float = Field(
        default=0.0,
        ge=0.0,
        description="Analysis time in seconds",
    )
    cost_usd: float = Field(
        default=0.0,
        ge=0.0,
        description="Total cost in USD",
    )
    topic_clusters: list[dict[str, Any]] = Field(
        default_factory=list,
        description="Topic clusters with coverage",
    )
    quality_comparison: dict[str, Any] = Field(
        default_factory=dict,
        description="Quality comparison between client and competitors",
    )
    summary: dict[str, Any] = Field(
        default_factory=dict,
        description="Summary metrics",
    )
    analyzed_at: datetime = Field(
        default_factory=lambda: datetime.now(),
        description="When analysis was performed",
    )
