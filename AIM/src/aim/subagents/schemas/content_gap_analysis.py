"""Pydantic schemas for Content Gap Analysis Agent."""

from datetime import datetime, timezone
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class EEATScores(BaseModel):
    """E-E-A-T quality scores for content."""

    model_config = ConfigDict(use_enum_values=True)

    experience_score: float = Field(..., ge=0.0, le=1.0, description="Experience score (0-1)")
    expertise_score: float = Field(..., ge=0.0, le=1.0, description="Expertise score (0-1)")
    authoritativeness_score: float = Field(..., ge=0.0, le=1.0, description="Authoritativeness score (0-1)")
    trustworthiness_score: float = Field(..., ge=0.0, le=1.0, description="Trustworthiness score (0-1)")
    overall_score: float = Field(..., ge=0.0, le=1.0, description="Overall E-E-A-T score (0-1)")
    quality_tier: str = Field(..., description="Quality tier (excellent/good/fair/poor)")
    recommendations: list[str] = Field(default_factory=list, description="Improvement recommendations")


class ScrapedPageData(BaseModel):
    """Scraped page data with E-E-A-T scores."""

    model_config = ConfigDict(use_enum_values=True)

    url: str = Field(..., description="Page URL")
    title: str = Field(..., description="Page title")
    body_text: str = Field(..., description="Main body text")
    headings: list[str] = Field(default_factory=list, description="H1-H3 headings")
    author_name: Optional[str] = Field(None, description="Author name")
    author_credentials: Optional[str] = Field(None, description="Author credentials")
    is_doctor_authored: bool = Field(False, description="Whether authored by doctor")
    citations: list[str] = Field(default_factory=list, description="Medical citations (PubMed, journals)")
    word_count: int = Field(..., ge=0, description="Word count")
    readability_score: float = Field(..., ge=0.0, description="Flesch-Kincaid readability score")
    content_type: str = Field(..., description="Content type (blog_post, service_page, faq, etc.)")
    has_https: bool = Field(False, description="Whether site uses HTTPS")
    has_contact_info: bool = Field(False, description="Whether page has contact info")
    has_privacy_policy: bool = Field(False, description="Whether site has privacy policy")
    eeat_scores: EEATScores = Field(..., description="E-E-A-T quality scores")
    is_client_content: bool = Field(..., description="Whether this is client content")
    scraped_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="When page was scraped",
    )


class AnalysisRequest(BaseModel):
    """Request for content gap analysis."""

    model_config = ConfigDict(use_enum_values=True)

    client_url: str = Field(..., description="Client site URL")
    competitor_urls: list[str] = Field(..., min_length=1, description="Competitor site URLs")
    niche: str = Field(..., description="Target niche/topic")
    max_pages_per_site: int = Field(30, ge=1, le=100, description="Max pages to scrape per site")
    max_cost_usd: float = Field(1.0, ge=0.0, description="Max budget for API calls")
    min_content_quality: float = Field(0.5, ge=0.0, le=1.0, description="Min E-E-A-T score for analysis")
    include_keywords: list[str] = Field(default_factory=list, description="Keywords to focus on")


class AnalysisResult(BaseModel):
    """Result of content gap analysis."""

    model_config = ConfigDict(use_enum_values=True)

    gaps: list[dict] = Field(default_factory=list, description="Detected content gaps")
    client_pages_analyzed: int = Field(..., ge=0, description="Number of client pages analyzed")
    competitor_pages_analyzed: int = Field(..., ge=0, description="Number of competitor pages analyzed")
    topics_discovered: int = Field(..., ge=0, description="Number of topics discovered")
    cluster_quality: str = Field(..., description="Cluster quality classification")
    analysis_time_seconds: float = Field(..., ge=0.0, description="Analysis time in seconds")
    cost_usd: float = Field(..., ge=0.0, description="Total cost in USD")
    analyzed_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="When analysis was performed",
    )
