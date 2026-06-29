"""
find_company_financials — Hermes tool: Real Financial Data from bo.nalog.gov.ru (ГИР БО)

GET http://aim-app:8000/api/companies/financials?inn=...
Fetches official tax-filed P&L (форма 0710002) from ФНС public API —
revenue, net profit, gross profit, operating profit, multi-year history.
No API key needed — official government open data.

Registered in Hermes internal registry under toolset "aim-operations".
"""

import json
import logging

import httpx

from tools.registry import registry

logger = logging.getLogger(__name__)


def _normalize_args(first_param, defaults):
    if isinstance(first_param, dict):
        return {k: first_param.get(k, defaults[k]) for k in defaults}
    return None


AIM_API_BASE = "http://aim-app:8000"
REQUEST_TIMEOUT = 10.0  # nalog API is fast (public JSON endpoint)


async def handle_find_company_financials(inn=None, ogrn=None, **kwargs) -> str:
    """Fetch real tax-filed financial data for a Russian company.

    Retrieves official P&L (форма 0710002) from bo.nalog.gov.ru (ГИР БО)
    — the official ФНС public API. Returns annual revenue, net profit,
    gross profit, operating profit, and multi-year history with trends.

    Args:
        inn: Company INN (10-12 digit taxpayer ID) — preferred
        ogrn: Company OGRN (13-15 digit state registration number) — fallback

    Returns:
        JSON with revenue, profit, gross_profit, operating_profit by year,
        company name, status, OKVED, and revenue trend.
    """
    unpacked = _normalize_args(inn, {"inn": "", "ogrn": ""})
    if unpacked:
        inn = unpacked["inn"]
        ogrn = unpacked.get("ogrn", "")

    identifier = inn or ogrn
    if not identifier:
        return json.dumps({
            "error": "Either inn or ogrn is required",
            "detail": "У тебя нет INN конкурента. Получи INN сначала — через find_competitors (он возвращает inn для каждого конкурента) или спроси клиента. Не вызывай этот tool без INN.",
        })

    logger.info("Fetching financials for: %s", identifier)

    params = {}
    if inn:
        params["inn"] = inn
    if ogrn:
        params["ogrn"] = ogrn

    try:
        async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT) as client:
            response = await client.get(
                f"{AIM_API_BASE}/api/companies/financials",
                params=params,
            )
            response.raise_for_status()
            data = response.json()

            if not data.get("success"):
                logger.warning("find_company_financials failed: %s", data.get("error"))
                return json.dumps({
                    "found": False,
                    "error": data.get("error", "Company not found"),
                })

            company = data.get("company", {})
            logger.info("Financials fetched for: %s (revenue years: %d)",
                         company.get("short_name", identifier),
                         len(company.get("revenue", {})))

            # Compact for LLM — key numbers only
            revenue = company.get("revenue", {})
            latest_revenue = _latest_value(revenue)
            profit = company.get("profit", {})
            latest_profit = _latest_value(profit)

            return json.dumps({
                "found": True,
                "company": {
                    "inn": company.get("inn"),
                    "ogrn": company.get("ogrn"),
                    "name": company.get("short_name") or company.get("full_name"),
                    "full_name": company.get("full_name"),
                    "status": company.get("status"),
                    "okved_main": company.get("okved_main"),
                    "legal_address": company.get("legal_address"),
                    "latest_revenue": latest_revenue,
                    "latest_profit": latest_profit,
                    "revenue_by_year": revenue,
                    "profit_by_year": profit,
                    "gross_profit_by_year": company.get("gross_profit", {}),
                    "operating_profit_by_year": company.get("operating_profit", {}),
                    "revenue_trend": company.get("revenue_trend"),
                    "data_source": company.get("data_source"),
                },
            }, ensure_ascii=False, indent=2)

    except httpx.HTTPStatusError as e:
        logger.error("AIM API returned error for find_company_financials: %s", e)
        return json.dumps({
            "found": False,
            "error": f"AIM API returned {e.response.status_code}",
        })
    except httpx.RequestError as e:
        logger.error("Cannot reach AIM API for find_company_financials: %s", e)
        return json.dumps({
            "found": False,
            "error": "Cannot reach AIM API",
        })
    except Exception as e:
        logger.exception("Unexpected error in find_company_financials")
        return json.dumps({
            "found": False,
            "error": str(e),
        })


def _latest_value(by_year: dict) -> int | None:
    """Extract the most recent year's value from {year: amount} dict."""
    if not by_year:
        return None
    years = sorted(by_year.keys(), reverse=True)
    return by_year[years[0]] if years else None


registry.register(
    name="find_company_financials",
    toolset="aim-operations",
    schema={
        "type": "function",
        "function": {
            "name": "find_company_financials",
            "description": (
                "Get real tax-filed financial data for a Russian company from bo.nalog.gov.ru (ГИР БО). "
                "Returns official P&L: annual revenue, net profit, gross profit, operating profit "
                "by year, plus company metadata (name, status, OKVED). "
                "⚠️ ТРЕБУЕТ INN или ОГРН. Если у тебя нет INN/ОГРН конкурента — НЕ вызывай этот tool. "
                "Сначала найди INN через find_competitors или DaData, потом вызывай. "
                "Без INN tool вернёт ошибку — не трать вызов."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "inn": {
                        "type": "string",
                        "description": "Company INN (10-12 digit taxpayer ID). Preferred identifier.",
                    },
                    "ogrn": {
                        "type": "string",
                        "description": "Company OGRN (13-15 digit state registration number). Fallback if no INN.",
                    },
                },
                "required": [],
            },
        },
    },
    handler=handle_find_company_financials,
    check_fn=lambda: True,
    is_async=True,
    description="Get real tax-filed financial data (revenue, profit, P&L) from bo.nalog.gov.ru by INN",
    emoji="💰",
)
