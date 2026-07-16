"""
Data models for competitor content analysis.

Pydantic schemas for request/response validation.
"""

from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field, HttpUrl, field_validator


class AnalysisMode(str, Enum):
    """Analysis depth mode."""

    QUICK = "quick"  # Basic analysis (keyword density, meta tags)
    STANDARD = "standard"  # + AI detection, E-E-A-T scoring
    DEEP = "deep"  # + Technical SEO, full content structure


class TargetMarket(str, Enum):
    """Target search engine market."""

    YANDEX = "yandex"  # Russian market (2-3% keyword density)
    GOOGLE = "google"  # Global market (0.5-1.5% keyword density)
    BOTH = "both"  # Optimize for both markets


class CompetitorAnalysisRequest(BaseModel):
    """Request for competitor content analysis."""

    client_url: HttpUrl = Field(..., description="Client's page URL")
    competitor_urls: list[HttpUrl] = Field(
        ..., min_length=1, max_length=10, description="Competitor page URLs (1-10)"
    )
    target_keyword: str = Field(
        ..., min_length=2, max_length=100, description="Target keyword to analyze"
    )
    analysis_mode: AnalysisMode = Field(
        default=AnalysisMode.STANDARD, description="Analysis depth"
    )
    target_market: TargetMarket = Field(
        default=TargetMarket.GOOGLE, description="Target market"
    )
    include_technical_seo: bool = Field(
        default=True, description="Include technical SEO analysis"
    )

    @field_validator("target_keyword")
    @classmethod
    def validate_keyword(cls, v: str) -> str:
        """Validate keyword is not empty after stripping."""
        cleaned = v.strip()
        if not cleaned:
            raise ValueError("Keyword cannot be empty")
        return cleaned


class KeywordAnalysisResult(BaseModel):
    """Keyword analysis results."""

    keyword: str
    count: int
    density: float
    status: str  # "optimal", "too_low", "too_high", "missing"
    recommendation: str
    market: str
    target_range: str

    # Placement analysis
    placements: dict[str, bool] = Field(default_factory=dict)
    placement_score: float = Field(default=0.0)

    # LSI keywords
    lsi_keywords: list[dict] = Field(default_factory=list)
    lsi_count: int = Field(default=0)
    lsi_per_1000_words: float = Field(default=0.0)
    lsi_status: str = Field(default="unknown")

    # Overall optimization
    overall_score: float = Field(default=0.0)
    density_score: float = Field(default=0.0)


class AIDetectionResult(BaseModel):
    """AI content detection results."""

    is_ai_generated: bool
    confidence: float = Field(ge=0.0, le=1.0)
    signals: dict[str, float] = Field(default_factory=dict)
    explanation: str


class EEATScore(BaseModel):
    """E-E-A-T scoring results."""

    experience_score: float = Field(ge=0.0, le=100.0)
    expertise_score: float = Field(ge=0.0, le=100.0)
    authoritativeness_score: float = Field(ge=0.0, le=100.0)
    trustworthiness_score: float = Field(ge=0.0, le=100.0)
    overall_score: float = Field(ge=0.0, le=100.0)

    # Component details
    experience_signals: list[str] = Field(default_factory=list)
    expertise_signals: list[str] = Field(default_factory=list)
    authoritativeness_signals: list[str] = Field(default_factory=list)
    trustworthiness_signals: list[str] = Field(default_factory=list)

    # Medical YMYL specific
    has_qualified_reviewer: bool = Field(default=False)
    last_updated: Optional[datetime] = None
    update_frequency_days: Optional[int] = None


class ContentStructure(BaseModel):
    """Content structure analysis."""

    word_count: int
    paragraph_count: int
    sentence_count: int
    avg_sentence_length: float

    # Headings
    h1_count: int = Field(default=0)
    h2_count: int = Field(default=0)
    h3_count: int = Field(default=0)
    h4_count: int = Field(default=0)
    h5_count: int = Field(default=0)
    h6_count: int = Field(default=0)
    heading_hierarchy_valid: bool = Field(default=True)

    # Formatting
    list_count: int = Field(default=0)
    bold_count: int = Field(default=0)
    image_count: int = Field(default=0)
    link_count: int = Field(default=0)

    # Readability
    flesch_reading_ease: Optional[float] = None
    flesch_kincaid_grade: Optional[float] = None


class TechnicalSEOResult(BaseModel):
    """Technical SEO analysis results."""

    # Core Web Vitals
    lcp: Optional[float] = Field(None, description="Largest Contentful Paint (ms)")
    inp: Optional[float] = Field(None, description="Interaction to Next Paint (ms)")
    cls: Optional[float] = Field(None, description="Cumulative Layout Shift")

    # Mobile optimization
    mobile_friendly: bool = Field(default=False)
    viewport_configured: bool = Field(default=False)

    # Page speed
    page_load_time: Optional[float] = Field(None, description="Page load time (ms)")
    time_to_interactive: Optional[float] = Field(
        None, description="Time to Interactive (ms)"
    )

    # Schema markup
    has_schema: bool = Field(default=False)
    schema_types: list[str] = Field(default_factory=list)

    # Overall score
    technical_score: float = Field(default=0.0, ge=0.0, le=100.0)


class CompetitorAnalysisResult(BaseModel):
    """Complete competitor analysis results."""

    # Request info
    client_url: str
    competitor_url: str
    target_keyword: str
    analysis_mode: AnalysisMode
    target_market: TargetMarket
    analyzed_at: datetime = Field(default_factory=datetime.utcnow)

    # Analysis results
    keyword_analysis: KeywordAnalysisResult
    ai_detection: Optional[AIDetectionResult] = None
    eeat_score: Optional[EEATScore] = None
    content_structure: ContentStructure
    technical_seo: Optional[TechnicalSEOResult] = None

    # Comparison with client
    client_keyword_analysis: Optional[KeywordAnalysisResult] = None
    client_content_structure: Optional[ContentStructure] = None

    # Recommendations
    priority_actions: list[str] = Field(default_factory=list)
    quick_wins: list[str] = Field(default_factory=list)
    long_term_improvements: list[str] = Field(default_factory=list)

    # Overall assessment
    competitor_strength: str = Field(
        default="unknown"
    )  # "weak", "moderate", "strong"
    gap_analysis: dict[str, str] = Field(default_factory=dict)


class CompetitorComparisonReport(BaseModel):
    """Comparison report across multiple competitors."""

    client_url: str
    target_keyword: str
    target_market: TargetMarket
    analyzed_at: datetime = Field(default_factory=datetime.utcnow)

    # Individual analyses
    competitor_analyses: list[CompetitorAnalysisResult]

    # Aggregate insights
    avg_competitor_keyword_density: float
    avg_competitor_word_count: int
    avg_competitor_eeat_score: Optional[float] = None
    avg_competitor_technical_score: Optional[float] = None

    # Client position
    client_keyword_density: float
    client_word_count: int
    client_eeat_score: Optional[float] = None
    client_technical_score: Optional[float] = None

    # Strategic recommendations
    top_priority_actions: list[str] = Field(default_factory=list)
    competitive_advantages: list[str] = Field(default_factory=list)
    competitive_gaps: list[str] = Field(default_factory=list)

    # Market-specific insights
    market_insights: dict[str, str] = Field(default_factory=dict)
