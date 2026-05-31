"""Data models for LLM-based CI analysis pipeline."""

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class SeoAuditResult:
    """Basic SEO audit — no paid APIs."""
    url: str
    score: int  # 0-100
    issues: list[str] = field(default_factory=list)
    title: str = ""
    title_length: int = 0
    meta_description: str = ""
    meta_description_length: int = 0
    h1_count: int = 0
    h2_count: int = 0
    h3_count: int = 0
    has_viewport: bool = False
    has_ssl: bool = False
    has_canonical: bool = False
    has_robots_txt: bool = False
    has_sitemap: bool = False
    has_og_tags: bool = False
    load_time_ms: int = 0
    pages_scraped: int = 0
    broken_links: list[str] = field(default_factory=list)
    error: str = ""


@dataclass
class SocialProfile:
    """Single social media profile data."""
    platform: str  # "instagram" | "telegram" | "vk" | "tiktok"
    handle: str
    url: str = ""
    exists: bool = False
    subscribers: int = 0
    posts_last_month: int = 0
    avg_likes: int = 0
    avg_comments: int = 0
    top_topics: list[str] = field(default_factory=list)
    content_formats: dict[str, int] = field(default_factory=dict)  # {"photo": 5, "video": 3, "text": 2}
    last_post_date: str = ""
    error: str = ""


@dataclass
class SocialScanResult:
    """Full social media scan for one competitor."""
    company_name: str
    instagram: Optional[SocialProfile] = None
    telegram: Optional[SocialProfile] = None
    vk: Optional[SocialProfile] = None
    tiktok: Optional[SocialProfile] = None
    total_platforms_found: int = 0
    error: str = ""

    def as_dict(self) -> dict:
        result = {}
        for plat in ("instagram", "telegram", "vk", "tiktok"):
            profile = getattr(self, plat)
            if profile is None:
                result[plat] = {"exists": False}
            else:
                result[plat] = {
                    "handle": profile.handle,
                    "exists": profile.exists,
                    "posts_month": profile.posts_last_month,
                    "avg_likes": profile.avg_likes,
                    "topics": profile.top_topics,
                }
        return result


@dataclass
class ArticleInfo:
    """Single journal article or publication."""
    title: str
    authors: list[str] = field(default_factory=list)
    journal: str = ""
    year: int = 0
    doi: str = ""
    url: str = ""
    citations: int = 0
    source: str = ""  # "elibrary" | "cyberleninka" | "pubmed" | "scholar"
    abstract: str = ""


@dataclass
class ArticleSearchResult:
    """Article search results for one person/clinic."""
    query_name: str
    total_found: int = 0
    articles: list[ArticleInfo] = field(default_factory=list)
    sources_searched: list[str] = field(default_factory=list)
    error: str = ""


@dataclass
class DoctorSocialResult:
    """Social media profiles for one doctor."""
    doctor_name: str
    profiles: list[SocialProfile] = field(default_factory=list)
    platforms_found: int = 0
    error: str = ""


@dataclass
class DoctorInfo:
    """Comprehensive profile of a doctor at a competitor clinic.

    Combines social media presence, publications, ProDoctorov ratings,
    and review mentions into a single influence_score (0-100).
    """
    name: str
    specialty: str = ""
    photo_url: str = ""
    bio_url: str = ""
    social: Optional[DoctorSocialResult] = None
    articles: Optional[ArticleSearchResult] = None
    prodoctorov_rating: float = 0.0
    prodoctorov_reviews: int = 0
    review_mentions: int = 0
    influence_score: float = 0.0  # 0-100
    is_leader: bool = False


@dataclass
class CompetitorFull:
    """All collected data for one competitor."""
    name: str
    url: str
    inn: str = ""
    financials: dict = field(default_factory=dict)  # revenue, profit, trend
    seo: Optional[SeoAuditResult] = None
    social: Optional[SocialScanResult] = None
    website_features: list[str] = field(default_factory=list)  # ["booking", "chat", "price_list"]
    website_missing: list[str] = field(default_factory=list)  # ["calculator", "reviews"]
    doctors_count: int = 0
    directions_claimed: int = 0
    pricing_visible: bool = False
    positioning: str = ""
    gm_rating: float = 0.0
    gm_reviews_count: int = 0
    yandex_rating: float = 0.0
    yandex_reviews_count: int = 0
    prodoctorov_rating: float = 0.0
    prodoctorov_reviews_count: int = 0
    scraped_at: str = ""
    doctors: list[DoctorInfo] = field(default_factory=list)


@dataclass
class ComparisonMatrix:
    """Compact matrix for LLM context (~5000 tokens)."""
    client: dict = field(default_factory=dict)
    competitors: list[dict] = field(default_factory=list)
    generated_at: str = ""


@dataclass
class WowMetrics:
    """Estimated practice metrics (patients/month, time-to-result, cost-per-patient).

    Used by WowEstimator in wow_estimator.py to provide ballpark numbers
    for competitive comparison when real data is unavailable.
    """
    patients_per_month: Optional[int] = None
    time_to_result_weeks: Optional[int] = None
    cost_per_patient_rub: Optional[int] = None
    is_estimated: bool = False
    source: str = ""

@dataclass
class PipelineProgress:
    """Progress update emitted during collection."""
    stage: str  # "searching" | "collecting" | "financials" | "seo" | "social" | "scraping" | "matrix" | "done"
    message: str
    competitor_name: str = ""
    details: dict = field(default_factory=dict)


@dataclass
class SwotQuadrant:
    """SWOT analysis quadrant result — strength/weakness/opportunity/threat lists."""
    strengths: list[str] = field(default_factory=list)
    weaknesses: list[str] = field(default_factory=list)
    opportunities: list[str] = field(default_factory=list)
    threats: list[str] = field(default_factory=list)


@dataclass
class StealWorthyTactic:
    """A tactic worth stealing from a competitor — the source, the tactic, and why."""
    source_competitor: str
    tactic_description: str
    why_it_works: str = ""
    how_to_implement: str = ""
    estimated_effort: str = "Medium"  # "Low" | "Medium" | "High"
    expected_impact: str = "Medium"   # "Low" | "Medium" | "High"


@dataclass
class UnifiedCiResult:
    """Phase 21 — unified result type that spans quick/deep/full tiers.

    Replaces the three separate result types from the old Path 1/2/3 architecture
    with a single dataclass that adapts behaviour based on tier.
    """
    tier: str = "quick"  # "quick" | "deep" | "full"
    chat_summary: str = ""
    feature_matrix: dict = field(default_factory=dict)
    aggregate_swot: Optional[SwotQuadrant] = None
    steal_worthy_tactics: list[StealWorthyTactic] = field(default_factory=list)
    top_recommendation: str = ""
    wow: dict = field(default_factory=dict)
    error: str = ""
    analysis_duration_seconds: float = 0.0
    # Phase 21 tier-spanning fields
    findings: dict = field(default_factory=dict)
    phases_executed: list[int] = field(default_factory=list)
    competitors_analyzed: int = 0
    quality_score: dict = field(default_factory=dict)

    @property
    def is_quick(self) -> bool:
        return self.tier == "quick"

    def to_dict(self) -> dict:
        """Serialize to dict for JSON output."""
        result = {
            "tier": self.tier,
            "chat_summary": self.chat_summary,
            "feature_matrix": self.feature_matrix,
            "top_recommendation": self.top_recommendation,
            "wow": self.wow,
            "error": self.error,
            "analysis_duration_seconds": self.analysis_duration_seconds,
            "findings": self.findings,
            "phases_executed": self.phases_executed,
            "competitors_analyzed": self.competitors_analyzed,
            "quality_score": self.quality_score,
        }
        if self.aggregate_swot is not None:
            result["aggregate_swot"] = {
                "strengths": self.aggregate_swot.strengths,
                "weaknesses": self.aggregate_swot.weaknesses,
                "opportunities": self.aggregate_swot.opportunities,
                "threats": self.aggregate_swot.threats,
            }
        if self.steal_worthy_tactics:
            result["steal_worthy_tactics"] = [
                {
                    "tactic": t.tactic_description,
                    "source": t.source_competitor,
                    "why": t.why_it_works,
                    "how": t.how_to_implement,
                    "effort": t.estimated_effort,
                    "impact": t.expected_impact,
                }
                for t in self.steal_worthy_tactics
            ]
        return result
