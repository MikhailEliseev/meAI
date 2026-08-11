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
# Q4 (Phase 14): temperature для фактического анализа. Дефолт 0.7-1.0 даёт
# разброс и галлюцинации. 0.25 = стабильно, фактологично, детерминированно.
LLM_TEMPERATURE = float(os.getenv("LLM_TEMPERATURE", "0.25"))
SESSIONS_DB_PATH = os.getenv("SESSIONS_DB_PATH", "/opt/data/sessions.db")

# --- Phase 3: ключи внешних сервисов ---
# Perplexity: single key, читается напрямую в perplexity.py
# Apify/Firecrawl: JSON pool files, управляются UnifiedKeyPool
# (нет через env vars — см. APIFY_KEYS_FILE / FIRECRAWL_KEYS_FILE)

# --- Phase 5: WordPress DB для публикации отчётов --------------------------
WP_DB_HOST = os.getenv("WP_DB_HOST", "")
WP_DB_USER = os.getenv("WP_DB_USER", "")
WP_DB_PASSWORD = os.getenv("WP_DB_PASSWORD", "")
WP_DB_NAME = os.getenv("WP_DB_NAME", "")
SESSIONS_ROOT = os.getenv("SESSIONS_ROOT", "/opt/data/sessions-archive")
ARCHIVE_BASE_URL = os.getenv("ARCHIVE_BASE_URL", "")
