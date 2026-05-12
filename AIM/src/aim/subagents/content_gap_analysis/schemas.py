"""
Pydantic Schemas for Content Gap Analysis Agent

Data validation and serialization models.
"""

from datetime import datetime
from typing import Optional, List, Dict, Any
from enum import Enum

from pydantic import BaseModel, Field, HttpUrl, field_validator, ConfigDict


class AnalysisDepth(str, Enum):
    """Analysis depth levels"""
    QUICK = "quick"  # 10 pages per site
    STANDARD = "standard"  # 30 pages per site
    DEEP = "deep"  # 50+ pages per site


class ContentType(str, Enum):
    """Content type classification"""
    BLOG_POST = "blog_post"
    SERVICE_PAGE = "service_page"
    FAQ = "faq"
    LANDING_PAGE = "landing_page"
    ABOUT_PAGE = "about_page"
    CONTACT_PAGE = "contact_page"
    OTHER = "other"


class GapType(str, Enum):
    """Content gap type"""
    MISSING_TOPIC = "missing_topic"  # 0 pages on client site
    UNDERREPRESENTED_TOPIC = "underrepresented_topic"  # 1-2 pages vs 5+ on competitors


class Priority(str, Enum):
    """Gap priority tier"""
    P0 = "P0"  # High priority (score 80-100)
    P1 = "P1"  # Medium priority (score 60-79)
    P2 = "P2"  # Low priority (score 40-59)
    P3 = "P3"  # Very low priority (score <40)


class AnalysisStatus(str, Enum):
    """Analysis run status"""
    SUCCESS = "success"
    PARTIAL_SUCCESS = "partial_success"
    FAILURE = "failure"


# Input schemas

class AnalysisRequest(BaseModel):
    """Content gap analysis request"""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "client_url": "https://example-clinic.com",
                "competitor_urls": [
                    "https://competitor1.com",
                    "https://competitor2.com"
                ],
                "niche": "dental implants",
                "analysis_depth": "standard",
                "max_pages_per_site": 30,
                "max_cost_usd": 1.0
            }
        }
    )

    client_url: HttpUrl = Field(..., description="Client site URL")
    competitor_urls: List[HttpUrl] = Field(
        ...,
        min_length=3,
        max_length=10,
        description="Competitor URLs (3-10 sites)"
    )
    niche: str = Field(..., min_length=1, max_length=255, description="Target niche")
    analysis_depth: AnalysisDepth = Field(
        default=AnalysisDepth.STANDARD,
        description="Analysis depth"
    )
    max_pages_per_site: int = Field(
        default=30,
        ge=5,
        le=100,
        description="Max pages per site"
    )
    max_cost_usd: float = Field(
        default=1.0,
        ge=0.0,
        le=10.0,
        description="Max API cost"
    )
    min_content_quality: float = Field(
        default=0.5,
        ge=0.0,
        le=1.0,
        description="Min E-E-A-T score"
    )
    include_keywords: Optional[List[str]] = Field(
        default=None,
        description="Keywords to focus on"
    )


# Content schemas

class EEATScores(BaseModel):
    """E-E-A-T component scores"""

    experience: float = Field(..., ge=0.0, le=1.0, description="Experience score")
    expertise: float = Field(..., ge=0.0, le=1.0, description="Expertise score")
    authoritativeness: float = Field(..., ge=0.0, le=1.0, description="Authoritativeness score")
    trustworthiness: float = Field(..., ge=0.0, le=1.0, description="Trustworthiness score")
    total: float = Field(..., ge=0.0, le=1.0, description="Total E-E-A-T score")


class ScrapedPageData(BaseModel):
    """Scraped page content and metadata"""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "url": "https://example.com/dental-implants",
                "domain": "example.com",
                "is_client": False,
                "title": "Dental Implants Guide",
                "word_count": 2500,
                "is_doctor_authored": True,
                "eeat_score": 0.85
            }
        }
    )

    url: str
    domain: str
    is_client: bool

    # Content
    title: Optional[str] = None
    meta_description: Optional[str] = None
    h1: Optional[str] = None
    h2_list: Optional[List[str]] = None
    h3_list: Optional[List[str]] = None
    body_text: Optional[str] = None
    word_count: Optional[int] = None

    # Content type
    content_type: Optional[ContentType] = None

    # Author
    author_name: Optional[str] = None
    author_credentials: Optional[str] = None
    is_doctor_authored: bool = False

    # Citations
    medical_citations_count: int = 0
    pubmed_links: Optional[List[str]] = None
    journal_references: Optional[List[str]] = None

    # Quality
    readability_score: Optional[float] = None
    eeat_score: Optional[float] = None
    eeat_components: Optional[EEATScores] = None

    # Traffic
    traffic_estimate: Optional[int] = None
    backlinks_count: Optional[int] = None

    # Technical
    has_https: bool = True
    has_contact_info: bool = False
    has_privacy_policy: bool = False

    @field_validator("word_count")
    @classmethod
    def validate_word_count(cls, v: Optional[int]) -> Optional[int]:
        if v is not None and v < 0:
            raise ValueError("word_count must be non-negative")
        return v

    @field_validator("eeat_score")
    @classmethod
    def validate_eeat_score(cls, v: Optional[float]) -> Optional[float]:
        if v is not None and not (0.0 <= v <= 1.0):
            raise ValueError("eeat_score must be between 0.0 and 1.0")
        return v


# Clustering schemas

class TopicClusterData(BaseModel):
    """Topic cluster metadata"""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "cluster_id": 0,
                "cluster_name": "Dental Implants Procedures",
                "topics": ["All-on-4", "Single tooth implant"],
                "client_coverage": 2,
                "competitor_coverage": 8,
                "gap_count": 6
            }
        }
    )

    cluster_id: int
    cluster_name: str
    representative_words: Optional[List[str]] = None
    topics: List[str] = Field(default_factory=list)

    # Coverage
    total_pages: int = 0
    client_pages: int = 0
    competitor_pages: int = 0
    gap_count: int = 0

    # Quality
    avg_eeat_score: Optional[float] = None
    avg_word_count: Optional[int] = None
    silhouette_score: Optional[float] = None


# Gap schemas

class CompetitorCoverage(BaseModel):
    """Competitor coverage for a gap"""

    url: str
    quality_score: float = Field(..., ge=0.0, le=1.0)
    traffic_estimate: Optional[int] = None
    word_count: Optional[int] = None
    doctor_authored: bool = False
    medical_citations: int = 0


class ContentGapData(BaseModel):
    """Content gap with recommendations"""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "topic": "All-on-4 dental implants recovery time",
                "gap_type": "missing_topic",
                "opportunity_score": 85.5,
                "priority": "P0",
                "competitor_coverage": {},
                "recommended_actions": [
                    "Create comprehensive guide (2000+ words)"
                ]
            }
        }
    )

    topic: str
    gap_type: GapType
    opportunity_score: float = Field(..., ge=0.0, le=100.0)
    priority: Priority

    # Competitor coverage
    competitor_coverage: Dict[str, CompetitorCoverage]

    # Recommendations
    recommended_word_count: Optional[int] = None
    recommended_content_type: Optional[ContentType] = None
    recommended_actions: List[str] = Field(default_factory=list)
    target_keywords: Optional[List[str]] = None

    # Score components (for debugging)
    score_components: Optional[Dict[str, float]] = None


# Output schemas

class ContentQualityComparison(BaseModel):
    """Content quality comparison between client and competitors"""

    avg_word_count: int
    avg_eeat_score: float
    doctor_authored_pct: float
    medical_citations_per_page: float


class AnalysisSummary(BaseModel):
    """Analysis summary statistics"""

    total_gaps_found: int
    p0_gaps: int
    p1_gaps: int
    p2_gaps: int
    p3_gaps: int = 0
    total_pages_analyzed: int
    total_cost_usd: float


class AnalysisMetrics(BaseModel):
    """Analysis performance metrics"""

    execution_time_ms: int
    pages_scraped: int
    api_calls: int
    gaps_detected: int
    clusters_created: int


class AnalysisError(BaseModel):
    """Analysis error details"""

    code: str
    message: str
    details: Optional[Dict[str, Any]] = None


class AnalysisResult(BaseModel):
    """Content gap analysis result"""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "status": "success",
                "result": {
                    "gaps": [],
                    "topic_clusters": [],
                    "content_quality_comparison": {
                        "client": {},
                        "competitors_avg": {}
                    },
                    "summary": {}
                },
                "metrics": {},
                "errors": []
            }
        }
    )

    status: AnalysisStatus
    result: Optional[Dict[str, Any]] = None
    metrics: AnalysisMetrics
    errors: List[AnalysisError] = Field(default_factory=list)


class AnalysisReport(BaseModel):
    """Complete analysis report for Obsidian vault"""

    analysis_id: str
    client_url: str
    competitor_urls: List[str]
    niche: str

    gaps: List[ContentGapData]
    topic_clusters: List[TopicClusterData]
    content_quality_comparison: Dict[str, ContentQualityComparison]
    summary: AnalysisSummary

    started_at: datetime
    completed_at: datetime
