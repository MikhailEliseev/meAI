"""Configuration management for meAI"""

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""

    # Required
    anthropic_api_key: str = Field(
        ...,
        min_length=1,
        description="Anthropic API key for Claude"
    )

    # Database
    database_url: str = Field(
        default="sqlite+aiosqlite:///./data/meai.db",
        description="Database connection URL"
    )

    # Obsidian
    obsidian_vault_path: str = Field(
        default="./obsidian",
        description="Path to Obsidian vault"
    )

    # Logging
    log_level: str = Field(
        default="INFO",
        description="Logging level (DEBUG, INFO, WARNING, ERROR)"
    )

    # Claude API
    claude_api_rate_limit: int = Field(
        default=50,
        description="Claude API rate limit (requests per minute)"
    )

    claude_api_budget_monthly: float = Field(
        default=100.0,
        description="Monthly budget for Claude API (USD)"
    )

    # Telegram (optional)
    telegram_bot_token: str | None = Field(
        default=None,
        description="Telegram bot token for alerts (optional)"
    )

    telegram_chat_id: str | None = Field(
        default=None,
        description="Telegram chat ID for alerts (optional)"
    )

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )
