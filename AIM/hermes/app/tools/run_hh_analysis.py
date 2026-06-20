"""
run_hh_analysis — Hermes tool: HeadHunter Vacancy Analysis

Анализирует вакансии клиники на hh.ru: количество, позиции, зарплаты, требования.
Используется для оценки кадровой ситуации клиники (рост/сжатие/стабильность).
"""

import asyncio
import json
import logging
import time

import httpx

from tools.registry import registry

logger = logging.getLogger(__name__)

AIM_API_BASE = "http://aim-app:8000"
REQUEST_TIMEOUT = 120.0
POLL_INTERVAL = 2.0

_cache: dict[str, tuple[float, str]] = {}
_CACHE_TTL = 600


def _normalize_args(first_param, defaults):
    if isinstance(first_param, dict):
        return {k: first_param.get(k, defaults[k]) for k in defaults}
    return None


async def handle_run_hh_analysis(url=None, company_name="", **kwargs) -> str:
    """Analyze HeadHunter vacancies for a clinic.

    Args:
        url: Website URL or company name to search HH vacancies for.
        company_name: Optional company name for more precise search.

    Returns:
        JSON with vacancy count, positions, salary ranges, requirements.
    """
    unpacked = _normalize_args(url, {"url": "", "company_name": ""})
    if unpacked:
        url = unpacked["url"]
        company_name = unpacked.get("company_name", company_name)

    if url and not url.startswith(("http://", "https://")):
        url = "https://" + url

    search_term = company_name or url or ""
    if not search_term:
        return json.dumps({"error": "URL or company name is required"})

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

        async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT) as client:
            resp = await client.post(
                f"{AIM_API_BASE}/api/hh/analyze",
                json={"query": search_term, "url": url},
            )
            resp.raise_for_status()
            data = resp.json()

            task_id = data.get("task_id")
            if not task_id:
                push_tool_progress("hh", "✅ Анализ вакансий готов!")
                result_json = json.dumps(data, ensure_ascii=False, indent=2)
                _cache[cache_key] = (time.time(), result_json)
                return result_json

            status_url = f"{AIM_API_BASE}/api/hh/analyze/{task_id}"
            poll_count = 0

            while True:
                await asyncio.sleep(POLL_INTERVAL)
                poll_count += 1
                status_resp = await client.get(status_url)
                status_resp.raise_for_status()
                status_data = status_resp.json()

                st = status_data.get("status", "unknown")
                if st == "done":
                    push_tool_progress("hh", "✅ Анализ вакансий готов!")
                    result = status_data.get("result", {})
                    result_json = json.dumps(result, ensure_ascii=False, indent=2)
                    _cache[cache_key] = (time.time(), result_json)
                    return result_json
                if st == "error":
                    return json.dumps({"error": "HH analysis failed", "detail": status_data.get("error", "Unknown")})

    except httpx.HTTPStatusError as e:
        logger.error("AIM API error for HH: %s", e)
        return json.dumps({"error": "AIM API error", "status": e.response.status_code, "detail": str(e)})
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
