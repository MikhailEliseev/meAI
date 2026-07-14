"""Конфигурация hermes-v2 через env (без pydantic-settings — меньше зависимостей).

Phase 1 использует только AIM_API_BASE и REQUEST_TIMEOUT. Остальные переменные
заложены пустыми для прямой совместимости с Phase 2-5 (LLM, тулы, отчёты),
чтобы последующие фазы не меняли этот файл.
"""
import os

# --- Phase 1 (используются сейчас) ----------------------------------------
AIM_API_BASE = os.getenv("AIM_API_BASE", "http://aim-app:8000")
REQUEST_TIMEOUT = float(os.getenv("REQUEST_TIMEOUT", "600.0"))

# --- Phase 2: LLM / диалог -------------------------------------------------
OMNIROUTE_URL = os.getenv("OMNIROUTE_URL", "")
# OMNIROUTE_AUTH — отдельный Z.AI токен (из .env.production), НЕ DeepSeek-ключ.
OMNIROUTE_AUTH = os.getenv("OMNIROUTE_AUTH", "")
LLM_MODEL = os.getenv("LLM_MODEL", "glm-5.2")
SESSIONS_DB_PATH = os.getenv("SESSIONS_DB_PATH", "/opt/data/sessions.db")

# --- Phase 3: ключи внешних сервисов (заготовки) ---------------------------
PERPLEXITY_API_KEY = os.getenv("PERPLEXITY_API_KEY", "")
APIFY_API_TOKEN = os.getenv("APIFY_API_TOKEN", "")
FIRECRAWL_API_KEY = os.getenv("FIRECRAWL_API_KEY", "")

# --- Phase 5: WordPress DB для публикации отчётов --------------------------
WP_DB_HOST = os.getenv("WP_DB_HOST", "")
WP_DB_USER = os.getenv("WP_DB_USER", "")
WP_DB_PASSWORD = os.getenv("WP_DB_PASSWORD", "")
WP_DB_NAME = os.getenv("WP_DB_NAME", "")
SESSIONS_ROOT = os.getenv("SESSIONS_ROOT", "/opt/data/sessions-archive")
ARCHIVE_BASE_URL = os.getenv("ARCHIVE_BASE_URL", "")
