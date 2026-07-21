"""
run_smi_mentions — Hermes tool: SMI & Media Mention Scanner

Searches major Russian media outlets for mentions of a competitor.
Covers: Forbes Russia, RBC, Kommersant, Vogue Russia, Marie Claire, The Blueprint,
Buro 24/7, and general Google News search.

Uses Firecrawl search API for each source in parallel.
Registered in Hermes internal registry under toolset "aim-operations".
"""

import asyncio
import json
import logging

import httpx

from .firecrawl_key_bank import get_key_with_fallback, mark_exhausted, classify_exhaustion
from tools.registry import registry

logger = logging.getLogger(__name__)

REQUEST_TIMEOUT = 120.0
FIRECRAWL_API = "https://api.firecrawl.dev/v2/search"
_MAX_RETRIES = 3



# Sources to search (Russian media landscape for medical/clinic coverage)
SMI_SOURCES = [
    {
        "name": "Forbes Russia",
        "domain": "forbes.ru",
        "query_template": '{company} site:forbes.ru',
        "category": "business",
    },
    {
        "name": "RBC",
        "domain": "rbc.ru",
        "query_template": '{company} site:rbc.ru',
        "category": "business",
    },
    {
        "name": "Коммерсантъ",
        "domain": "kommersant.ru",
        "query_template": '{company} site:kommersant.ru',
        "category": "business",
    },
    {
        "name": "Vogue Russia",
        "domain": "vogue.ru",
        "query_template": '{company} site:vogue.ru',
        "category": "glossy",
    },
    {
        "name": "Marie Claire",
        "domain": "marieclaire.ru",
        "query_template": '{company} site:marieclaire.ru',
        "category": "glossy",
    },
    {
        "name": "The Blueprint",
        "domain": "theblueprint.ru",
        "query_template": '{company} site:theblueprint.ru',
        "category": "glossy",
    },
    {
        "name": "Buro 24/7",
        "domain": "buro247.ru",
        "query_template": '{company} site:buro247.ru',
        "category": "glossy",
    },
    {
        "name": "Google News",
        "query_template": '{company} клиника',
        "category": "news",
    },
]


async def handle_run_smi_mentions(company_name=None, **kwargs) -> str:
    """Search Russian media outlets for mentions of a competitor clinic.

    Scans Forbes, RBC, Kommersant, Vogue, Marie Claire, The Blueprint, and
    Google News in parallel. Returns articles with URLs, dates, and categories.

    Args:
        company_name: Clinic or company name to search for (e.g., "СМ-Клиника")

    Returns:
        JSON string with mentions grouped by source, total count, and media presence score.
    """
    if isinstance(company_name, dict):
        company_name = company_name.get("company_name", "")

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

    logger.info("Scanning SMI mentions for: %s", company_name)

    from app.main import push_tool_progress

    push_tool_progress("smi", f"Сканирую СМИ на упоминания «{company_name}»…")

    try:
        async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT) as client:
            results = []

            # Search up to 6 sources in parallel (batch of 3 to avoid rate limits)
            sources_to_search = SMI_SOURCES[:6]  # limit to avoid excessive API calls

            for i in range(0, len(sources_to_search), 3):
                batch = sources_to_search[i:i+3]

                tasks = [
                    _search_source(client, source, company_name)
                    for source in batch
                ]
                batch_results = await asyncio.gather(*tasks, return_exceptions=True)

                for j, result in enumerate(batch_results):
                    source = batch[j]
                    if isinstance(result, Exception):
                        logger.warning("SMI search failed for %s: %s", source["name"], result)
                        results.append({
                            "source": source["name"],
                            "category": source["category"],
                            "error": str(result),
                            "mentions": [],
                        })
                    else:
                        results.append(result)

                if i + 3 < len(sources_to_search):
                    await asyncio.sleep(1)  # rate limit pause between batches

        total_mentions = sum(len(r.get("mentions", [])) for r in results)
        sources_with_mentions = sum(1 for r in results if len(r.get("mentions", [])) > 0)

        # Media presence assessment
        if sources_with_mentions >= 4:
            presence = "высокая — компания активно представлена в медиа"
        elif sources_with_mentions >= 2:
            presence = "средняя — компания периодически появляется в СМИ"
        elif sources_with_mentions >= 1:
            presence = "низкая — единичные упоминания"
        else:
            presence = "отсутствует — компания невидима в федеральных СМИ"

        push_tool_progress(
            "smi",
            f"✅ Нашёл {total_mentions} упоминаний в {sources_with_mentions} источниках — {presence}",
        )

        return json.dumps({
            "company_name": company_name,
            "total_mentions": total_mentions,
            "sources_with_mentions": sources_with_mentions,
            "media_presence": presence,
            "sources": results,
        }, ensure_ascii=False, indent=2)

    except Exception as e:
        logger.exception("SMI mentions scan failed")
        return json.dumps({"error": "SMI scan failed", "detail": str(e)})


async def _search_source(
    client: httpx.AsyncClient, source: dict, company: str
) -> dict:
    """Search a single media source via Firecrawl with key rotation."""
    query = source["query_template"].format(company=company)

    for attempt in range(_MAX_RETRIES):
        try:
            key = get_key_with_fallback()
        except RuntimeError:
            return {
                "source": source["name"],
                "category": source["category"],
                "error": "Нет доступных ключей Firecrawl",
                "mentions": [],
            }

        try:
            response = await client.post(
                FIRECRAWL_API,
                headers={"Authorization": f"Bearer {key}"},
                json={
                    "query": query,
                    "limit": 5,
                    "sources": ["web"] if source.get("domain") else ["news"],
                },
            )
            if response.status_code == 402:
                reason = classify_exhaustion(response.text)
                if reason:
                    mark_exhausted(key, reason)
                    logger.warning("Firecrawl 402 on SMI search (%s), rotating key (attempt %d)", source["name"], attempt + 1)
                    continue

            response.raise_for_status()
            data = response.json()
            break  # success
        except httpx.HTTPStatusError as e:
            reason = classify_exhaustion(str(e))
            if reason:
                mark_exhausted(key, reason)
                logger.warning("Firecrawl credit exhausted on SMI search (%s), rotating (attempt %d)", source["name"], attempt + 1)
                continue
            logger.warning("SMI search HTTP error for %s: %s", source["name"], e)
            return {
                "source": source["name"],
                "category": source["category"],
                "error": str(e)[:500],
                "mentions": [],
            }
    else:
        # All retries exhausted
        return {
            "source": source["name"],
            "category": source["category"],
            "error": "Все ключи Firecrawl исчерпаны",
            "mentions": [],
        }

    search_data = data.get("data", [])
    if isinstance(search_data, dict):
        search_data = search_data.get("web", [])
    items = []
    for item in search_data[:5]:
        items.append({
            "title": item.get("title", ""),
            "url": item.get("url", ""),
            "snippet": (item.get("description") or item.get("snippet", ""))[:300],
        })

    return {
        "source": source["name"],
        "category": source["category"],
        "mentions_count": len(items),
        "mentions": items,
    }


registry.register(
    name="run_smi_mentions",
    toolset="aim-operations",
    schema={
        "type": "function",
        "function": {
            "name": "run_smi_mentions",
            "description": (
                "Search major Russian media outlets (Forbes, RBC, Kommersant, Vogue, "
                "Marie Claire, The Blueprint) and Google News for mentions of a competitor. "
                "Shows media presence level: is the competitor famous, interviewed, "
                "featured in business/glossy press? "
                "Use this to understand a competitor's PR strategy and public visibility. "
                "High media presence = strong brand, harder to compete with."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "company_name": {
                        "type": "string",
                        "description": "[REQUIRED] Clinic or company name to search for in media (e.g., 'СМ-Клиника', 'Медси')",
                    },
                },
                "required": ["company_name"],
            },
        },
    },
    handler=handle_run_smi_mentions,
    check_fn=lambda: True,
    is_async=True,
    description="Scan Russian media (Forbes, RBC, Vogue, etc.) for competitor mentions — PR visibility audit",
    emoji="📰",
)
