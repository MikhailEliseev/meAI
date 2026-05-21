"""
Ads Subagent Configuration Settings.

Manages API credentials, rate limits, and timeouts for advertising platforms.
"""

from typing import Optional
from pydantic_settings import BaseSettings


class AdsSettings(BaseSettings):
    """Configuration for Ads subagent API integrations."""

    # Google Ads API
    google_ads_developer_token: str
    google_ads_client_id: str
    google_ads_client_secret: str
    google_ads_refresh_token: str
    google_ads_customer_id: str
    google_ads_login_customer_id: Optional[str] = None

    # Yandex Direct API
    yandex_direct_token: str
    yandex_direct_client_id: str
    yandex_direct_client_login: Optional[str] = None

    # VK Ads API
    vk_ads_access_token: Optional[str] = None
    vk_ads_account_id: Optional[int] = None

    # Telegram Ads API
    telegram_ads_bot_token: Optional[str] = None

    # Facebook Ads API (optional)
    facebook_ads_access_token: Optional[str] = None
    facebook_ads_app_id: Optional[str] = None
    facebook_ads_app_secret: Optional[str] = None

    # Rate Limiting
    rate_limit_capacity: int = 10  # Max requests in bucket
    rate_limit_refill: float = 1.0  # Requests per second refill rate

    # Timeouts (seconds)
    api_timeout: int = 30
    oauth_timeout: int = 60

    # Circuit Breaker
    circuit_breaker_fail_max: int = 5
    circuit_breaker_reset_timeout: int = 60

    # Retry Configuration
    retry_max_attempts: int = 3
    retry_min_wait: int = 1
    retry_max_wait: int = 30
    retry_multiplier: int = 2

    # Caching
    cache_ttl: int = 3600  # 1 hour
    cache_enabled: bool = True

    # Logging
    log_level: str = "INFO"
    log_api_requests: bool = True
    log_api_responses: bool = False  # Can be verbose

    class Config:
        env_file = ".env"
        env_prefix = "ADS_"
        case_sensitive = False


def get_ads_settings() -> AdsSettings:
    """Get Ads settings singleton."""
    return AdsSettings()
