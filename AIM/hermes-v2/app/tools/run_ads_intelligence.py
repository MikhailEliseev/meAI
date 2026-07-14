"""Ads intelligence через Firecrawl (перенос из старого hermes, упрощённый).

Скрейпит Facebook Ad Library через Firecrawl, парсит кол-во активных рекламы.
Ротация ключей через firecrawl_key_bank.
"""
import json
import logging
import re

import httpx

from app.lib.firecrawl_key_bank import classify_exhaustion, key_bank as fc_key_bank
from app.tools.registry import register

logger = logging.getLogger(__name__)

FIRECRAWL_SCRAPE = "https://api.firecrawl.dev/v2/scrape"
MAX_RETRIES = 3


def _normalize_company(company) -> str:
    if isinstance(company, dict):
        company = company.get("company") or company.get("name", "")
    return str(company).strip()


async def _search_facebook_ads(client: httpx.AsyncClient, company: str) -> dict:
    """Скрейпит FB Ad Library через Firecrawl с ротацией ключей."""
    fb_url = (
        f"https://www.facebook.com/ads/library/"
        f"?active_status=active&ad_type=all&country=RU&q={company}"
    )

    for attempt in range(MAX_RETRIES):
        key = fc_key_bank.get_key()
        if not key:
            return {"platforms": ["facebook", "instagram"], "active_ads_count": 0,
                    "ads": [], "note": "Нет доступных ключей Firecrawl"}
        try:
            response = await client.post(
                FIRECRAWL_SCRAPE,
                headers={"Authorization": f"Bearer {key}"},
                json={"url": fb_url, "formats": ["markdown"], "waitFor": 8000, "onlyMainContent": True},
            )
            if response.status_code in (402, 429) and classify_exhaustion(response.status_code, response.text):
                fc_key_bank.mark_exhausted(key)
                logger.warning("firecrawl exhausted on FB ads, rotating (attempt %d)", attempt + 1)
                continue
            response.raise_for_status()
            data = response.json()
            break
        except httpx.HTTPStatusError:
            return {"platforms": ["facebook", "instagram"], "active_ads_count": 0,
                    "ads": [], "note": "FB Ad Library недоступен (геоблокировка?)"}
    else:
        return {"platforms": ["facebook", "instagram"], "active_ads_count": 0,
                "ads": [], "note": "Все ключи Firecrawl исчерпаны"}

    markdown = data.get("data", {}).get("markdown", "")
    ad_count = 0
    m = re.search(r'(\d[\d\s]*)\s*(?:result|результат|объявл|ad)', markdown, re.IGNORECASE)
    if m:
        try:
            ad_count = int(m.group(1).replace(" ", ""))
        except ValueError:
            pass

    return {
        "platforms": ["facebook", "instagram"],
        "active_ads_count": ad_count,
        "query": company,
        "note": f"Найдено активных объявлений: {ad_count}" if ad_count else "Активных объявлений не найдено",
    }


async def handle_run_ads_intelligence(company=None, url=None, **kwargs) -> str:
    """Анализ рекламной активности (FB/IG Ad Library) через Firecrawl."""
    company = _normalize_company(company)
    if not company and url:
        company = str(url)
    if not company:
        return json.dumps({"error": "company или url требуется"})

    try:
        async with httpx.AsyncClient(timeout=120.0) as client:
            result = await _search_facebook_ads(client, company)
        logger.info("ads OK: %s — %d ads", company[:40], result.get("active_ads_count", 0))
        return json.dumps(result, ensure_ascii=False, indent=2)
    except Exception as e:
        logger.exception("ads failed: %s", company[:40])
        return json.dumps({"error": str(e)})


register(
    name="run_ads_intelligence",
    schema={
        "type": "function",
        "function": {
            "name": "run_ads_intelligence",
            "description": (
                "Анализ рекламной активности клиники: активные объявления в "
                "Facebook/Instagram Ad Library. Возвращает кол-во активных объявлений. "
                "ВЫЗЫВАЙ когда клиент спросил 'сколько тратят на рекламу' или 'проверить рекламу'."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "company": {"type": "string", "description": "Название клиники для поиска"},
                    "url": {"type": "string", "description": "URL сайта (альтернатива company)"},
                },
            },
        },
    },
    handler=handle_run_ads_intelligence,
)
