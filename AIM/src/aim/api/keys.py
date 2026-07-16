"""API endpoint для мониторинга статуса API-ключей.

GET /api/keys/health → статус всех провайдеров (total/active/exhausted).
"""
import logging

from fastapi import APIRouter

from src.aim.services import get_apify_key_pool

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/keys", tags=["keys"])


@router.get("/health")
async def keys_health():
    """Возвращает статус всех пулов API-ключей.

    Response:
        {
            "apify": {"total": 14, "active": 14, "exhausted": 0},
            "firecrawl": {"total": 15, "active": 15, "exhausted": 0}
        }
    """
    result = {}

    # Apify
    try:
        pool = get_apify_key_pool()
        result["apify"] = pool.get_stats()
    except Exception as e:
        result["apify"] = {"error": str(e)}

    # Firecrawl (singleton — НЕ создавать новый пул на каждый запрос)
    try:
        from src.aim.services.lib.firecrawl_key_pool import get_firecrawl_pool
        fc_pool = get_firecrawl_pool()
        result["firecrawl"] = fc_pool.get_stats()
    except Exception as e:
        result["firecrawl"] = {"error": str(e)}

    return result
