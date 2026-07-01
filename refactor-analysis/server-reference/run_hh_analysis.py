"""
run_hh_analysis — Hermes tool: HeadHunter Vacancy Analysis

Анализирует вакансии клиники на hh.ru:
- Прямой поиск через hh.ru public API (employers → vacancies)
- DuckDuckGo fallback для случаев когда компания не найдена через API

Используется для оценки кадровой ситуации клиники (рост/сжатие/стабильность).
"""

import asyncio
import json
import logging
import time

import httpx

from tools.registry import registry

logger = logging.getLogger(__name__)

REQUEST_TIMEOUT = 60.0

_cache: dict[str, tuple[float, str]] = {}
_CACHE_TTL = 600


def _normalize_args(first_param, defaults):
    if isinstance(first_param, dict):
        return {k: first_param.get(k, defaults[k]) for k in defaults}
    return None


async def _search_hh_api(client: httpx.AsyncClient, company_name: str) -> dict | None:
    """Search for employer on hh.ru public API."""
    # Step 1: find employer
    emp_url = "https://api.hh.ru/employers"
    emp_resp = await client.get(emp_url, params={
        "text": company_name,
        "area": 113,  # Russia
        "per_page": 5,
        "only_with_vacancies": True,
    })
    emp_resp.raise_for_status()
    employers = emp_resp.json().get("items", [])

    if not employers:
        return None

    # Pick best match
    employer = employers[0]
    employer_id = employer["id"]
    employer_name = employer["name"]

    # Step 2: get vacancies
    vac_url = f"https://api.hh.ru/vacancies"
    vac_resp = await client.get(vac_url, params={
        "employer_id": employer_id,
        "per_page": 50,
        "area": 113,
    })
    vac_resp.raise_for_status()
    vac_data = vac_resp.json()

    vacancies = []
    for v in vac_data.get("items", []):
        salary = v.get("salary") or {}
        vacancies.append({
            "name": v.get("name", ""),
            "area": (v.get("area") or {}).get("name", ""),
            "salary_from": salary.get("from"),
            "salary_to": salary.get("to"),
            "salary_currency": salary.get("currency"),
            "published_at": v.get("published_at", ""),
            "url": v.get("alternate_url", ""),
        })

    # Category analysis
    categories: dict[str, int] = {}
    for v in vacancies:
        cat = v["name"].split("(")[0].strip()
        categories[cat] = categories.get(cat, 0) + 1

    return {
        "source": "hh.ru API",
        "employer_name": employer_name,
        "employer_id": employer_id,
        "employer_url": f"https://hh.ru/employer/{employer_id}",
        "open_vacancies": employer.get("open_vacancies", len(vacancies)),
        "vacancies": vacancies[:20],
        "top_categories": dict(sorted(categories.items(), key=lambda x: x[1], reverse=True)[:5]),
    }


async def _search_via_ddg(company_name: str) -> dict | None:
    """Search for HH vacancies via search fallback (DDG → Crawlee → Firecrawl)."""
    try:
        from app.tools._search_fallback import search as fallback_search
    except ImportError:
        return None

    query = f'"{company_name}" вакансии site:hh.ru'
    results, provider = await fallback_search(query, max_results=10)

    links = []
    for r in results:
        links.append({
            "title": r.get("title", ""),
            "url": r.get("url", ""),
            "description": r.get("description", ""),
        })

    return {
        "source": provider,
        "query": query,
        "search_results": links,
    } if links else None


async def handle_run_hh_analysis(url=None, company_name="", **kwargs) -> str:
    """Analyze HeadHunter vacancies for a clinic.

    Searches hh.ru public API directly, then falls back to DuckDuckGo.

    Args:
        url: Website URL or company name to search HH vacancies for.
        company_name: Optional company name for more precise search.

    Returns:
        JSON with vacancy count, positions, salary ranges, requirements.
    """
    unpacked = _normalize_args(url, {"url": "", "company_name": ""})
    if unpacked:
        url = unpacked.get("url", url)
        company_name = unpacked.get("company_name", company_name)

    # Also extract from kwargs
    cn = kwargs.get("company_name", "")
    if cn and not company_name:
        company_name = cn

    search_term = company_name or url or ""
    if not search_term:
        return json.dumps({"error": "URL or company name is required"})

    # Clean search term: remove protocol and www
    if search_term.startswith("http"):
        from urllib.parse import urlparse
        parsed = urlparse(search_term)
        search_term = parsed.netloc.replace("www.", "") or search_term

    cache_key = f"hh_{search_term}"
    cached = _cache.get(cache_key)
    if cached is not None:
        cached_ts, cached_result = cached
        if time.time() - cached_ts < _CACHE_TTL:
            return cached_result
        del _cache[cache_key]

    logger.info("Analyzing HH vacancies for: %s", search_term)

    try:
        from app.main import push_tool_progress
        push_tool_progress("hh", f"💼 Анализирую вакансии для {search_term}…")

        result: dict = {"search_term": search_term}

        async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT) as client:
            # Try hh.ru API first
            try:
                api_result = await _search_hh_api(client, search_term)
                if api_result:
                    result.update(api_result)
                    push_tool_progress("hh", f"✅ Найдено {api_result.get('open_vacancies', 0)} вакансий на hh.ru!")
            except Exception as e:
                logger.warning("hh.ru API search failed: %s", str(e)[:150])

            # DDG fallback for additional context
            if not result.get("vacancies"):
                try:
                    ddg_result = await _search_via_ddg(search_term)
                    if ddg_result:
                        result.update(ddg_result)
                except Exception as e:
                    logger.warning("DDG HH search failed: %s", str(e)[:150])

        if not result.get("vacancies") and not result.get("search_results"):
            result["note"] = "No vacancies found on hh.ru for this clinic"

        push_tool_progress("hh", "✅ Анализ вакансий готов!")
        result_json = json.dumps(result, ensure_ascii=False, indent=2)
        _cache[cache_key] = (time.time(), result_json)
        return result_json

    except Exception as e:
        logger.exception("HH analysis error")
        return json.dumps({"error": "Unexpected error", "detail": str(e)})


registry.register(
    name="run_hh_analysis",
    toolset="aim-operations",
    schema={
        "type": "function",
        "function": {
            "name": "run_hh_analysis",
            "description": "Analyze HeadHunter.ru vacancies for a clinic: open positions, salary ranges, requirements. Shows hiring activity as growth/contraction indicator.",
            "parameters": {
                "type": "object",
                "properties": {
                    "url": {"type": "string", "description": "Website URL or company name to search HH vacancies for"},
                    "company_name": {"type": "string", "description": "Optional: exact company name for more precise search"},
                },
                "required": ["url"],
            },
        },
    },
    handler=handle_run_hh_analysis,
    check_fn=lambda: True,
    is_async=True,
    description="Analyze HeadHunter.ru vacancies for hiring activity insights",
    emoji="💼",
)
