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

    CRITICAL = "critical"  # P0 - Missing completely, high volume
    HIGH = "high"  # P1 - Missing completely or high priority
    MEDIUM = "medium"  # P2 - Underrepresented (1-2 pages vs 5+)
    LOW = "low"  # P3 - Comparable coverage


class IntentType(str, Enum):
    """Search intent type."""

    INFORMATIONAL = "informational"
    COMMERCIAL = "commercial"
    TRANSACTIONAL = "transactional"
    NAVIGATIONAL = "navigational"


class ContentGap(BaseModel):
    """Content gap detected between client and competitors."""

    model_config = ConfigDict(use_enum_values=True)

    missing_keyword: str = Field(..., description="Missing keyword or topic")
    gap_type: GapType = Field(..., description="Type of gap")
    severity: GapSeverity = Field(..., description="Severity of gap")
    search_volume: int = Field(default=0, ge=0, description="Monthly search volume")
    opportunity_score: float = Field(
        ..., ge=0.0, le=1.0, description="Opportunity score (0.0-1.0)"
    )
    competitor_coverage: dict[str, bool] = Field(
        default_factory=dict,
        description="Competitor coverage map (domain -> has_content)",
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

    # Legacy field for backward compatibility
    @property
    def topic(self) -> str:
        """Alias for missing_keyword."""
        return self.missing_keyword

    @property
    def priority(self) -> str:
        """Priority tier based on severity."""
        severity_to_priority = {
            GapSeverity.CRITICAL: "P0",
            GapSeverity.HIGH: "P1",
            GapSeverity.MEDIUM: "P2",
            GapSeverity.LOW: "P3",
        }
        return severity_to_priority.get(self.severity, "P3")


class ContentCluster(BaseModel):
    """Topic cluster from SERP overlap analysis."""

    model_config = ConfigDict(use_enum_values=True)

    hub_keyword: str = Field(..., description="Hub keyword (cluster center)")
    spoke_keywords: list[str] = Field(
        default_factory=list, description="Spoke keywords (cluster members)"
    )
    keywords: list[str] = Field(
        default_factory=list, description="All keywords in cluster"
    )
    total_search_volume: int = Field(
        default=0, ge=0, description="Total search volume for cluster"
    )
    primary_intent: IntentType = Field(
        default=IntentType.INFORMATIONAL, description="Primary search intent"
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
