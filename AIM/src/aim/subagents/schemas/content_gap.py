"""Pydantic schemas for content gap analysis."""

from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator


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

    client_url: str = Field(..., description="Client website URL")
    competitor_urls: list[str] = Field(
        default_factory=list, description="Competitor URLs analyzed"
    )
    niche: str = Field(..., description="Target niche/topic")
    gaps: list[ContentGap] = Field(
        default_factory=list,
        description="Detected content gaps",
    )
    clusters: list[ContentCluster] = Field(
        default_factory=list,
        description="Keyword clusters from SERP overlap analysis",
    )
    architecture: dict[str, Any] = Field(
        default_factory=dict,
        description="Hub-and-spoke content architecture",
    )
    briefs: list[dict[str, Any]] = Field(
        default_factory=list,
        description="Content briefs for top gaps",
    )
    summary: dict[str, Any] = Field(
        default_factory=dict,
        description="Summary metrics",
    )
    analyzed_at: datetime = Field(
        default_factory=lambda: datetime.now(),
        description="When analysis was performed",
    )


class SERPResult(BaseModel):
    """Single SERP result for a keyword."""

    keyword: str = Field(..., description="Search keyword")
    url: str = Field(..., description="Ranking URL")
    position: int = Field(..., ge=1, le=100, description="SERP position (1-100)")
    title: str = Field(..., description="Page title")
    intent: IntentType = Field(default=IntentType.INFORMATIONAL, description="Search intent")

    @field_validator("url")
    @classmethod
    def validate_url(cls, v: str) -> str:
        """Validate URL format."""
        if not v.startswith(("http://", "https://")):
            raise ValueError(f"Invalid URL: {v}")
        return v


class KeywordSERPData(BaseModel):
    """SERP data for a single keyword."""

    keyword: str = Field(..., description="Search keyword")
    serp_results: list[SERPResult] = Field(
        default_factory=list, description="Top 30 SERP results"
    )
    search_volume: int = Field(default=0, ge=0, description="Monthly search volume")
    intent: IntentType = Field(default=IntentType.INFORMATIONAL, description="Primary intent")

    @field_validator("serp_results")
    @classmethod
    def validate_serp_results(cls, v: list[SERPResult]) -> list[SERPResult]:
        """Validate SERP results count."""
        if len(v) > 100:
            raise ValueError(f"Too many SERP results: {len(v)} (max 100)")
        return v
