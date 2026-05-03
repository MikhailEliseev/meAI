"""Configuration for AIM Agency."""

from pathlib import Path

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
