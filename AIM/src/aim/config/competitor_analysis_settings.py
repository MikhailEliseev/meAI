"""
Configuration settings for Competitor Content Analyzer.

Environment-based configuration with pydantic-settings.
"""

from typing import Optional

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class CompetitorAnalysisSettings(BaseSettings):
    """Settings for competitor content analysis."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Market-specific thresholds
    yandex_min_keyword_density: float = Field(
        default=0.02, description="Yandex minimum keyword density (2%)"
    )
    yandex_max_keyword_density: float = Field(
        default=0.03, description="Yandex maximum keyword density (3%)"
    )
    google_min_keyword_density: float = Field(
        default=0.005, description="Google minimum keyword density (0.5%)"
    )
    google_max_keyword_density: float = Field(
        default=0.015, description="Google maximum keyword density (1.5%)"
    )

    # LSI keywords
    lsi_min_per_1000_words: int = Field(
        default=5, description="Minimum LSI keywords per 1000 words"
    )
    lsi_max_per_1000_words: int = Field(
        default=10, description="Maximum LSI keywords per 1000 words"
    )
    lsi_min_count: int = Field(
        default=2, description="Minimum occurrences to consider as LSI keyword"
    )

    # Content analysis
    min_word_count: int = Field(
        default=300, description="Minimum word count for analysis"
    )
    max_word_count: int = Field(
        default=10000, description="Maximum word count for analysis"
    )

    # AI detection thresholds
    ai_detection_confidence_threshold: float = Field(
        default=0.7, description="Confidence threshold for AI detection (0-1)"
    )

    # E-E-A-T scoring
    eeat_min_score: float = Field(
        default=60.0, description="Minimum acceptable E-E-A-T score"
    )
    eeat_medical_ymyl_required: bool = Field(
        default=True, description="Require medical YMYL checks for medical content"
    )

    # Technical SEO thresholds
    lcp_good_threshold: float = Field(
        default=2500.0, description="Good LCP threshold (ms)"
    )
    lcp_needs_improvement_threshold: float = Field(
        default=4000.0, description="LCP needs improvement threshold (ms)"
    )
    inp_good_threshold: float = Field(
        default=200.0, description="Good INP threshold (ms)"
    )
    inp_needs_improvement_threshold: float = Field(
        default=500.0, description="INP needs improvement threshold (ms)"
    )
    cls_good_threshold: float = Field(
        default=0.1, description="Good CLS threshold"
    )
    cls_needs_improvement_threshold: float = Field(
        default=0.25, description="CLS needs improvement threshold"
    )

    # Timeout and retry settings
    page_load_timeout: int = Field(
        default=30000, description="Page load timeout (ms)"
    )
    analysis_timeout: int = Field(
        default=60000, description="Total analysis timeout (ms)"
    )
    max_retries: int = Field(default=3, description="Maximum retry attempts")
    retry_delay: int = Field(default=1000, description="Retry delay (ms)")

    # Cost control
    max_cost_per_analysis: float = Field(
        default=0.10, description="Maximum cost per analysis (USD)"
    )
    max_competitors_per_request: int = Field(
        default=10, description="Maximum competitors per request"
    )

    # Caching
    cache_ttl: int = Field(
        default=3600, description="Cache TTL for analysis results (seconds)"
    )
    enable_cache: bool = Field(default=True, description="Enable result caching")

    # Playwright settings (for technical SEO)
    playwright_headless: bool = Field(
        default=True, description="Run Playwright in headless mode"
    )
    playwright_timeout: int = Field(
        default=30000, description="Playwright operation timeout (ms)"
    )

    # User agent
    user_agent: str = Field(
        default="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        description="User agent for web requests",
    )

    # API keys (optional, for future integrations)
    semrush_api_key: Optional[str] = Field(
        default=None, description="SEMrush API key (optional)"
    )
    ahrefs_api_key: Optional[str] = Field(
        default=None, description="Ahrefs API key (optional)"
    )


def get_competitor_analysis_settings() -> CompetitorAnalysisSettings:
    """Get competitor analysis settings instance."""
    return CompetitorAnalysisSettings()
