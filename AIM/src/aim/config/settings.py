"""Settings for API Clients and Integrations

Environment variable configuration with validation for API keys and defaults.
"""

from typing import Optional

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class APISettings(BaseSettings):
    """API client settings from environment variables

    Attributes:
        semrush_api_key: SEMrush API key (required)
        ahrefs_api_key: Ahrefs API key (optional, fallback)
        max_cost_usd: Maximum API cost per request in USD
        min_keywords: Minimum keywords to return
        min_volume: Minimum search volume filter
        cache_ttl: Cache TTL in seconds
        rate_limit_capacity: Rate limiter bucket capacity
        rate_limit_refill: Rate limiter refill rate (requests/sec)
        upload_dir: Directory for uploaded documents
        serpapi_api_key: SerpAPI key for real-time SERP data
        pagespeed_api_key: Google PageSpeed Insights API key
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # API Keys
    semrush_api_key: Optional[str] = Field(
        default=None,
        description="SEMrush API key (required for production)",
    )
    ahrefs_api_key: Optional[str] = Field(
        None,
        description="Ahrefs API key (optional fallback)",
    )
    dadata_api_key: Optional[str] = Field(
        default=None,
        description="DaData API key for Russian company search (10k req/day free)",
        min_length=10,
    )
    serpapi_api_key: Optional[str] = Field(
        default=None,
        validation_alias="SERPAPI_KEY",
        description="SerpAPI key for real-time SERP and web search (primary)",
        min_length=10,
    )
    serpapi_key_secondary: Optional[str] = Field(
        default=None,
        description="SerpAPI secondary key (old key, recovers after ~1 month of inactivity)",
        min_length=10,
    )
    pagespeed_api_key: Optional[str] = Field(
        default=None,
        description="Google PageSpeed Insights API key (optional, free tier: 25k req/day)",
    )

    # File upload settings
    upload_dir: str = Field(
        default="./uploads",
        description="Directory for uploaded documents",
    )

    # Budget and limits
    max_cost_usd: float = Field(
        default=5.0,
        description="Maximum API cost per request in USD",
        ge=0.1,
        le=100.0,
    )
    min_keywords: int = Field(
        default=100,
        description="Minimum keywords to return",
        ge=1,
        le=1000,
    )
    min_volume: int = Field(
        default=10,
        description="Minimum search volume filter",
        ge=0,
    )

    # Caching and rate limiting
    cache_ttl: int = Field(
        default=3600,
        description="Cache TTL in seconds (1 hour default)",
        ge=60,
        le=86400,
    )
    rate_limit_capacity: int = Field(
        default=10,
        description="Rate limiter bucket capacity",
        ge=1,
        le=100,
    )
    rate_limit_refill: float = Field(
        default=1.0,
        description="Rate limiter refill rate (requests/sec)",
        ge=0.1,
        le=10.0,
    )

    @field_validator("semrush_api_key")
    @classmethod
    def validate_semrush_key(cls, v: Optional[str]) -> Optional[str]:
        """Validate SEMrush API key format"""
        if v is None:
            return None
        if v.strip() == "":
            return None
        if v.startswith("your_") or v == "REPLACE_ME":
            raise ValueError(
                "SEMrush API key not configured. "
                "Set SEMRUSH_API_KEY environment variable."
            )
        return v.strip()

    @field_validator("ahrefs_api_key")
    @classmethod
    def validate_ahrefs_key(cls, v: Optional[str]) -> Optional[str]:
        """Validate Ahrefs API key format"""
        if v is None:
            return None
        if v.strip() == "":
            return None
        if v.startswith("your_") or v == "REPLACE_ME":
            return None
        return v.strip()

    def has_fallback(self) -> bool:
        """Check if Ahrefs fallback is configured

        Returns:
            True if Ahrefs API key is available
        """
        return self.ahrefs_api_key is not None

    def validate_on_startup(self, skip_api_key_check: bool = False) -> None:
        """Validate settings on application startup

        Args:
            skip_api_key_check: Skip API key validation (for tests)

        Raises:
            ValueError: If configuration is invalid
        """
        # Check primary API key (skip in tests)
        if not skip_api_key_check and not self.semrush_api_key:
            raise ValueError(
                "SEMrush API key is required. "
                "Set SEMRUSH_API_KEY environment variable."
            )

        # Warn if no fallback (only if we have primary key)
        if self.semrush_api_key and not self.has_fallback():
            import warnings
            warnings.warn(
                "Ahrefs API key not configured. "
                "No fallback available if SEMrush fails. "
                "Set AHREFS_API_KEY environment variable for redundancy.",
                UserWarning,
            )

        # Validate budget vs keywords
        min_cost_per_keyword = 0.01
        estimated_cost = self.min_keywords * min_cost_per_keyword
        if estimated_cost > self.max_cost_usd:
            raise ValueError(
                f"Budget ${self.max_cost_usd} insufficient for "
                f"{self.min_keywords} keywords (estimated ${estimated_cost:.2f}). "
                f"Increase MAX_COST_USD or reduce MIN_KEYWORDS."
            )


# Global settings instance
_settings: Optional[APISettings] = None


def get_api_settings(skip_validation: bool = False) -> APISettings:
    """Get API settings singleton

    Args:
        skip_validation: Skip API key validation (for tests)

    Returns:
        APISettings instance

    Raises:
        ValueError: If settings validation fails
    """
    global _settings
    if _settings is None:
        if skip_validation:
            # Create settings without validation for testing
            _settings = APISettings.model_construct(
                semrush_api_key="test_key",
                ahrefs_api_key="test_key",
            )
        else:
            _settings = APISettings()
            _settings.validate_on_startup(skip_api_key_check=skip_validation)
    return _settings
