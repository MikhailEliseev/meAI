"""
find_company_financials — Hermes tool: Real Financial Data from rusprofile.ru

GET http://app:8000/api/companies/financials?inn=...
Fetches tax-filed revenue, profit, and company value from rusprofile.ru
by INN or OGRN. No API key needed — public data scraping.

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


AIM_API_BASE = "http://app:8000"
REQUEST_TIMEOUT = 20.0  # rusprofile pages take a bit longer


async def handle_find_company_financials(inn=None, ogrn=None, **kwargs) -> str:
    """Fetch real tax-filed financial data for a Russian company.

    Retrieves annual revenue, profit, and company value from rusprofile.ru
    public data. Also returns company metadata: name, director, registration
    date, tax regime, OKVED codes, MSP category.

    Args:
        inn: Company INN (10-12 digit taxpayer ID) — preferred
        ogrn: Company OGRN (13-15 digit state registration number) — fallback

    Returns:
        JSON with revenue/profit/value by year, company name, director,
        tax regime, MSP category, and other metadata.
    """
    unpacked = _normalize_args(inn, {"inn": "", "ogrn": ""})
    if unpacked:
        inn = unpacked["inn"]
        ogrn = unpacked.get("ogrn", "")

    identifier = inn or ogrn
    if not identifier:
        return json.dumps({"error": "Either inn or ogrn is required"})

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
                    "director": company.get("director"),
                    "status": company.get("status"),
                    "registration_date": company.get("registration_date"),
                    "latest_revenue": latest_revenue,
                    "latest_profit": latest_profit,
                    "revenue_by_year": revenue,
                    "profit_by_year": profit,
                    "tax_regime": company.get("tax_regime"),
                    "msp_category": company.get("msp_category"),
                    "okved_main": company.get("okved_main"),
                    "license_count": company.get("license_count"),
                    "trademark_count": company.get("trademark_count"),
                    "legal_address": company.get("legal_address"),
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
                "Get real tax-filed financial data for a Russian company from rusprofile.ru. "
                "Returns annual revenue, profit, company value by year, plus metadata: "
                "company name, director, tax regime, OKVED codes, MSP category. "
                "Use this when you need to know a competitor's actual revenue "
                "(tax-filed, not estimated). Requires INN or OGRN."
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
    description="Get real tax-filed financial data (revenue, profit, value) from rusprofile.ru by INN",
    emoji="💰",
)
