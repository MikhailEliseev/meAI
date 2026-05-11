"""Result Schemas

Models for keyword analysis results and research reports.
"""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field

from AIM.src.aim.subagents.schemas.api_responses import KeywordDataUnified
from AIM.src.aim.subagents.schemas.compliance import ComplianceResult
from AIM.src.aim.subagents.schemas.prioritization import (
    FeedbackSummary,
    KeywordPriority,
    PriorityTier,
)


class KeywordAnalysisResult(BaseModel):
    """Complete analysis result for a single keyword

    Combines API data, compliance check, and priority calculation.
    """

    # Source data
    keyword_data: KeywordDataUnified = Field(..., description="Unified keyword data from API")

    # Analysis results
    compliance: ComplianceResult = Field(..., description="Compliance check result")
    priority: KeywordPriority = Field(..., description="Priority calculation result")

    # Metadata
    analyzed_at: datetime = Field(default_factory=datetime.utcnow)
    analysis_duration_ms: float = Field(..., ge=0, description="Analysis duration in milliseconds")
    cost_usd: float = Field(..., ge=0, description="API cost for this keyword")


class RecommendationType(str, Enum):
    """Recommendation type"""

    CONTENT = "content"  # Content creation recommendation
    OPTIMIZATION = "optimization"  # Existing content optimization
    TECHNICAL = "technical"  # Technical SEO recommendation
    COMPLIANCE = "compliance"  # Compliance-related recommendation
    MONITORING = "monitoring"  # Monitoring/tracking recommendation


class Recommendation(BaseModel):
    """Actionable recommendation based on keyword analysis"""

    type: RecommendationType = Field(..., description="Recommendation type")
    priority: PriorityTier = Field(..., description="Recommendation priority")
    title: str = Field(..., description="Short recommendation title")
    description: str = Field(..., description="Detailed recommendation")
    keywords: list[str] = Field(..., description="Keywords this applies to")
    estimated_impact: str = Field(..., description="Expected impact (e.g., '+20% traffic')")
    effort: str = Field(..., description="Effort required (e.g., '2-4 hours')")


class KeywordResearchReport(BaseModel):
    """Complete keyword research report with recommendations

    Final output of the Keyword Research Agent.
    """

    # Request context
    seed_keyword: str = Field(..., description="Original seed keyword")
    requested_at: datetime = Field(..., description="When research was requested")
    completed_at: datetime = Field(default_factory=datetime.utcnow)

    # Results
    keywords: list[KeywordAnalysisResult] = Field(..., description="All analyzed keywords")
    total_keywords: int = Field(..., ge=0, description="Total keywords analyzed")

    # Breakdown by priority
    p0_count: int = Field(..., ge=0, description="P0 keywords count")
    p1_count: int = Field(..., ge=0, description="P1 keywords count")
    p2_count: int = Field(..., ge=0, description="P2 keywords count")
    p3_count: int = Field(..., ge=0, description="P3 keywords count")

    # Compliance breakdown
    blocked_count: int = Field(..., ge=0, description="Keywords blocked by compliance")
    reduced_count: int = Field(..., ge=0, description="Keywords with reduced priority")
    passed_count: int = Field(..., ge=0, description="Keywords that passed compliance")

    # Recommendations
    recommendations: list[Recommendation] = Field(
        default_factory=list, description="Actionable recommendations"
    )

    # Cost tracking
    total_cost_usd: float = Field(..., ge=0, description="Total API cost")
    api_calls: int = Field(..., ge=0, description="Total API calls made")

    # Quality metrics
    average_priority_score: float = Field(..., ge=0, le=100, description="Average priority score")
    confidence: float = Field(default=1.0, ge=0, le=1, description="Overall confidence")

    # Feedback (if available)
    feedback_summary: Optional[FeedbackSummary] = Field(
        None, description="User feedback summary"
    )

    # Metadata
    analysis_duration_seconds: float = Field(..., ge=0, description="Total analysis duration")
    agent_version: str = Field(default="1.0.0", description="Agent version")


from enum import Enum  # noqa: E402 - import after usage for proper ordering
