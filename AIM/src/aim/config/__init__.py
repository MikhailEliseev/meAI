"""Configuration for AIM Agency."""

from pathlib import Path

from .competitor_analysis_settings import (
    CompetitorAnalysisSettings,
    get_competitor_analysis_settings,
)

# Paths
AIM_ROOT = Path(__file__).parent.parent.parent
OBSIDIAN_ROOT = AIM_ROOT / "obsidian"
DATA_ROOT = AIM_ROOT / "data"

# Database
DATABASE_URL = f"sqlite+aiosqlite:///{DATA_ROOT}/aim.db"

# Obsidian vaults
OPERATOR_VAULT = OBSIDIAN_ROOT / "operator"
SEO_MAGISTER_VAULT = OBSIDIAN_ROOT / "seo-magister"
CONTENT_MAGISTER_VAULT = OBSIDIAN_ROOT / "content-magister"
ADS_MAGISTER_VAULT = OBSIDIAN_ROOT / "ads-magister"

# Agency settings
AGENCY_NAME = "AIM"
AGENCY_DOMAIN = "iamaim.ru"
AGENCY_FOCUS = "AI-first Medical Marketing"

__all__ = [
    "AIM_ROOT",
    "OBSIDIAN_ROOT",
    "DATA_ROOT",
    "DATABASE_URL",
    "OPERATOR_VAULT",
    "SEO_MAGISTER_VAULT",
    "CONTENT_MAGISTER_VAULT",
    "ADS_MAGISTER_VAULT",
    "AGENCY_NAME",
    "AGENCY_DOMAIN",
    "AGENCY_FOCUS",
    "CompetitorAnalysisSettings",
    "get_competitor_analysis_settings",
]
