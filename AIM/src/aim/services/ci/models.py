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
    scraped_at: str = ""


@dataclass
class ComparisonMatrix:
    """Compact matrix for LLM context (~5000 tokens)."""
    client: dict = field(default_factory=dict)
    competitors: list[dict] = field(default_factory=list)
    generated_at: str = ""


@dataclass
class PipelineProgress:
    """Progress update emitted during collection."""
    stage: str  # "searching" | "collecting" | "financials" | "seo" | "social" | "scraping" | "matrix" | "done"
    message: str
    competitor_name: str = ""
    details: dict = field(default_factory=dict)
