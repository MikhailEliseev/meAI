"""
run_ads_intelligence — Hermes tool: Advertising Intelligence (Facebook + Telegram)

Analyses a competitor's active advertising campaigns:
- Facebook/Instagram Ad Library (public, no auth)
- Telegram Ads presence (search-based)
- Ad formats, messages, CTAs, landing pages, estimated budget level

Uses Firecrawl with JS rendering for Facebook Ad Library.
Registered in Hermes internal registry under toolset "aim-operations".
"""

import asyncio
import json
import logging
import os
import re
from pathlib import Path

import httpx

from app.key_bank import key_bank
from .firecrawl_key_bank import classify_exhaustion
from tools.registry import registry

logger = logging.getLogger(__name__)

REQUEST_TIMEOUT = 180.0
FIRECRAWL_SCRAPE = "https://api.firecrawl.dev/v2/scrape"
_MAX_RETRIES = 3


async def handle_run_ads_intelligence(company_name=None, website=None, **kwargs) -> str:
    """Scan competitor advertising across Facebook/Instagram and Telegram.

    Searches Facebook Ad Library for active ads, analyses ad creatives,
    and checks Telegram channels for ad placements.

    Args:
        company_name: Company name to search in ad libraries
        website: Company website (helps find landing pages in ads)

    Returns:
        JSON with active ads count, platforms, formats, top messages, CTAs, landing pages.
    """
    if isinstance(company_name, dict):
        d = company_name
        company_name = d.get("company_name", "")
        if website is None:
            website = d.get("website", "")

    if not company_name:
        try:
            cached = Path("/tmp/hermes_last_company.txt").read_text().strip()
            if cached:
                logger.info("Using cached company name: %s", cached)
                company_name = cached
        except Exception:
            pass

    if not company_name:
        return json.dumps({"error": "company_name is required"})

    # Fallback: if LLM forgot the website, try the cache from run_prescan
    if not website:
        try:
            cached = Path("/tmp/hermes_last_url.txt").read_text().strip()
            if cached:
                logger.info("Using cached URL from prescan: %s", cached)
                website = cached
        except Exception:
            pass

    logger.info("Scanning ads for: %s (website: %s)", company_name, website)

    from app.main import push_tool_progress

    facebook_result = {"error": "not_searched"}
    telegram_result = {"error": "not_searched"}

    push_tool_progress("ads", f"Сканирую рекламу «{company_name}» в Facebook Ad Library…")

    try:
        async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT) as client:
            # Run Facebook and Telegram searches in parallel (each handles own key rotation)
            fb_task = _search_facebook_ads(client, company_name, website)
            tg_task = _search_telegram_ads(client, company_name)

            facebook_result, telegram_result = await asyncio.gather(
                fb_task, tg_task, return_exceptions=True,
            )

            if isinstance(facebook_result, Exception):
                logger.warning("Facebook ad search failed: %s", facebook_result)
                facebook_result = {"error": str(facebook_result), "active_ads_count": 0, "ads": []}
            if isinstance(telegram_result, Exception):
                logger.warning("Telegram ad search failed: %s", telegram_result)
                telegram_result = {"error": str(telegram_result), "active_ads_count": 0, "channels": []}

        # Merge insights
        fb_count = facebook_result.get("active_ads_count", 0)
        tg_count = telegram_result.get("active_ads_count", 0)
        total = fb_count + tg_count

        if total >= 20:
            intensity = "агрессивная — компания активно закупает трафик"
        elif total >= 5:
            intensity = "заметная — компания регулярно рекламируется"
        elif total >= 1:
            intensity = "низкая — единичные рекламные кампании"
        else:
            intensity = "отсутствует — компания не использует платную рекламу в этих каналах"

        push_tool_progress(
            "ads",
            f"✅ Рекламная разведка: {total} активных объявлений — {intensity}",
        )

        return json.dumps({
            "company_name": company_name,
            "total_active_ads": total,
            "ad_intensity": intensity,
            "facebook": facebook_result,
            "telegram": telegram_result,
        }, ensure_ascii=False, indent=2)

    except Exception as e:
        logger.exception("Ad intelligence scan failed")
        return json.dumps({"error": "Ad intelligence failed", "detail": str(e)})


async def _search_facebook_ads(
    client: httpx.AsyncClient, company: str, website: str
) -> dict:
    """Search Facebook Ad Library for active ads. Uses key bank with rotation."""
    fb_url = (
        f"https://www.facebook.com/ads/library/"
        f"?active_status=active&ad_type=all&country=RU&q={company}"
    )

    for attempt in range(_MAX_RETRIES):
        try:
            key = key_bank.get_firecrawl_key()
        except RuntimeError:
            return {
                "platforms": ["facebook", "instagram"],
                "active_ads_count": 0, "ads": [],
                "note": "Нет доступных ключей Firecrawl",
            }
        if not key:
            return {
                "platforms": ["facebook", "instagram"],
                "active_ads_count": 0, "ads": [],
                "note": "Нет доступных ключей Firecrawl",
            }

        try:
            response = await client.post(
                FIRECRAWL_SCRAPE,
                headers={"Authorization": f"Bearer {key}"},
                json={
                    "url": fb_url,
                    "formats": ["markdown"],
                    "waitFor": 8000,
                    "onlyMainContent": True,
                },
            )
            if response.status_code == 402:
                reason = classify_exhaustion(response.text)
                if reason:
                    key_bank.mark_firecrawl_exhausted(key)
                    logger.warning("Firecrawl 402 on FB ads, rotating key (attempt %d)", attempt + 1)
                    continue

            response.raise_for_status()
            data = response.json()
            break  # success — exit retry loop
        except httpx.HTTPStatusError:
            logger.warning("Facebook Ad Library scrape returned non-200")
            return {
                "platforms": ["facebook", "instagram"],
                "active_ads_count": 0, "ads": [],
                "note": "Facebook Ad Library недоступен (возможно, геоблокировка)",
            }
    else:
        # All retries exhausted
        return {
            "platforms": ["facebook", "instagram"],
            "active_ads_count": 0, "ads": [],
            "note": "Все ключи Firecrawl исчерпаны",
        }

    markdown = data.get("data", {}).get("markdown", "")

    # Parse ad count from markdown
    ad_count = 0
    count_match = re.search(r'(\d[\d\s]*)\s*(?:result|результат|объявл|ad)', markdown, re.IGNORECASE)
    if count_match:
        try:
            ad_count = int(count_match.group(1).replace(" ", ""))
        except ValueError:
            pass

    # Try to extract ad messages from the markdown
    ad_messages = []
    cta_patterns = set()
    landing_pages = set()

    # Common CTAs in Russian medical ads
    cta_keywords = {
        "записаться": "Записаться на консультацию",
        "консультация": "Получить консультацию",
        "цена": "Узнать цену",
        "стоимость": "Узнать стоимость",
        "акция": "Акция / Скидка",
        "заказать": "Заказать",
        "звонок": "Заказать звонок",
        "рассрочка": "Рассрочка",
        "подарок": "Подарок при записи",
    }

    for line in markdown.split("\n"):
        line_lower = line.lower()
        for keyword, cta in cta_keywords.items():
            if keyword in line_lower:
                cta_patterns.add(cta)
                if len(line) > 20:
                    ad_messages.append(line.strip()[:200])

    # Extract landing page URLs
    url_matches = re.findall(r'https?://[^\s\)\]>"]+', markdown)
    for u in url_matches:
        if "facebook.com" not in u and "fb.com" not in u:
            landing_pages.add(u)

    return {
        "platforms": ["facebook", "instagram"],
        "active_ads_count": ad_count,
        "ads_found_text": bool(ad_messages),
        "top_messages": list(set(m[:150] for m in ad_messages[:10])),
        "cta_patterns": list(cta_patterns),
        "landing_pages": list(landing_pages)[:5],
        "raw_excerpt": markdown[:800],
    }


async def _search_telegram_ads(
    client: httpx.AsyncClient, company: str
) -> dict:
    """Search for Telegram ad placements using unified search fallback."""
    from app.tools._search_fallback import search as fallback_search

    results, provider = await fallback_search(f'{company} реклама site:t.me', max_results=10)

    channels = []
    for item in results:
        url = item.get("url", "")
        if "t.me" in url:
            channels.append({
                "channel_url": url,
                "title": item.get("title", ""),
                "snippet": (item.get("description", ""))[:200],
            })

    return {
        "active_ads_count": len(channels),
        "channels": channels,
        "source": provider,
    }


registry.register(
    name="run_ads_intelligence",
    toolset="aim-operations",
    schema={
        "type": "function",
        "function": {
            "name": "run_ads_intelligence",
            "description": (
                "Analyse a competitor's advertising strategy across Facebook/Instagram "
                "and Telegram. Scans Facebook Ad Library for active ads, identifies "
                "ad formats, key marketing messages, CTAs (call-to-actions), and landing pages. "
                "Also checks Telegram channels for ad placements. "
                "Use this to understand HOW a competitor attracts clients: their hooks, "
                "offers, and conversion tactics. Reveals budget level (aggressive/noticeable/low). "
                "Critical for competitive positioning — if they spend heavily on ads, "
                "you need a differentiated strategy."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "company_name": {
                        "type": "string",
                        "description": "[REQUIRED] Company name to search in ad libraries (e.g., 'СМ-Клиника')",
                    },
                    "website": {
                        "type": "string",
                        "description": "Company website — helps identify landing pages used in ads",
                    },
                },
                "required": ["company_name"],
            },
        },
    },
    handler=handle_run_ads_intelligence,
    check_fn=lambda: True,
    is_async=True,
    description="Analyse competitor ads on Facebook/Instagram + Telegram: active campaigns, messages, CTAs, budget level",
    emoji="📢",
)
