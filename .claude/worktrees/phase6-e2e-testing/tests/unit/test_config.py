"""Tests for configuration management"""

import pytest
from pathlib import Path
from pydantic import ValidationError
from meai.config import Settings


def test_settings_loads_from_env(tmp_path, monkeypatch):
    """Test Settings loads from .env file"""
    # Create temporary .env
    env_file = tmp_path / ".env"
    env_file.write_text("""
ANTHROPIC_API_KEY=sk-ant-test123
DATABASE_URL=sqlite+aiosqlite:///./test.db
OBSIDIAN_VAULT_PATH=./test_vault
LOG_LEVEL=DEBUG
""")

    # Clear any existing env vars to avoid loading real .env
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)

    # Load settings with explicit env file
    settings = Settings(_env_file=str(env_file))

    assert settings.anthropic_api_key == "sk-ant-test123"
    assert settings.database_url == "sqlite+aiosqlite:///./test.db"
    assert settings.obsidian_vault_path == "./test_vault"
    assert settings.log_level == "DEBUG"


def test_settings_requires_api_key():
    """Test Settings requires ANTHROPIC_API_KEY"""
    with pytest.raises(ValidationError) as exc_info:
        Settings(
            anthropic_api_key="",  # Empty key should fail
            database_url="sqlite+aiosqlite:///./test.db",
            obsidian_vault_path="./vault"
        )
    
    assert "anthropic_api_key" in str(exc_info.value)


def test_settings_has_defaults():
    """Test Settings has sensible defaults"""
    settings = Settings(
        anthropic_api_key="sk-ant-test123"
    )
    
    assert settings.database_url == "sqlite+aiosqlite:///./data/meai.db"
    assert settings.obsidian_vault_path == "./obsidian"
    assert settings.log_level == "INFO"
    assert settings.claude_api_rate_limit == 50
    assert settings.claude_api_budget_monthly == 100.0


def test_settings_telegram_optional():
    """Test Telegram settings are optional"""
    settings = Settings(
        anthropic_api_key="sk-ant-test123"
    )
    
    assert settings.telegram_bot_token is None
    assert settings.telegram_chat_id is None
