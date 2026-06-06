"""
Company Financials API Endpoint

GET /api/companies/financials — Real financial data from bo.nalog.gov.ru (ГИР БО).
Uses official ФНС public API — no authentication, no CSRF, direct HTTP GET.
"""

import asyncio
import logging

from fastapi import APIRouter, HTTPException, Query

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/companies", tags=["companies"])


@router.get("/financials")
async def get_company_financials(
    inn: str = Query("", description="Company INN (10-12 digits)"),
    ogrn: str = Query("", description="Company OGRN (13-15 digits)"),
):
    """Get real financial data for a Russian company from bo.nalog.gov.ru (ГИР БО).

    Fetches official tax-filed P&L (форма 0710002) including revenue, net profit,
    gross profit, operating profit, and multi-year history with trends.

    Args:
        inn: Company INN (taxpayer ID, 10-12 digits) — preferred
        ogrn: Company OGRN — fallback (not directly supported by nalog, ignored)

    Returns:
        {
            "success": true,
            "company": {
                "inn": "9717023304",
                "ogrn": "1167746394826",
                "short_name": "ООО КПЮ",
                "full_name": "ООО КЛИНИКА ПРОФЕССОРА ЮЦКОВСКОЙ",
                "legal_address": "...",
                "status": "ACTIVE",
                "okved_main": "86.23",
                "revenue": {"2025": 242176000, "2024": 218962000},
                "profit": {"2025": 20922000, "2024": 21361000},
                "gross_profit": {"2025": ..., "2024": ...},
                "operating_profit": {"2025": ..., "2024": ...},
                "revenue_trend": "growing",
                "data_source": "nalog",
                "latest_revenue": 242176000,
                "latest_profit": 20922000
            }
        }
    """
    if not inn and not ogrn:
        raise HTTPException(status_code=400, detail="Either inn or ogrn is required")

    identifier = inn or ogrn
    logger.info("Fetching nalog financials for: %s", identifier)

    try:
        from src.aim.services.nalog import BfoNalogClient

        # BfoNalogClient is sync — run in thread to not block the event loop
        def _fetch():
            client = BfoNalogClient()
            try:
                # Search by INN
                results = client.search(identifier)
                if not results:
                    return None

                org = results[0]
                fs_list = client.get_financials(org.id)

                return org, fs_list
            finally:
                client.close()

        result = await asyncio.to_thread(_fetch)

        if result is None:
            return {
                "success": False,
                "error": f"Company not found for: {identifier}",
                "company": None,
            }

        org, fs_list = result

        # Map financial statements to year-indexed dicts
        revenue: dict[str, int] = {}
        profit: dict[str, int] = {}
        gross_profit: dict[str, int] = {}
        operating_profit: dict[str, int] = {}
        revenue_trend = ""

        for fs in fs_list:
            year = fs.period
            if fs.revenue_rub is not None:
                revenue[year] = fs.revenue_rub
            if fs.net_profit_rub is not None:
                profit[year] = fs.net_profit_rub
            if fs.gross_profit is not None:
                gross_profit[year] = fs.gross_profit * 1000
            if fs.operating_profit is not None:
                operating_profit[year] = fs.operating_profit * 1000
            if not revenue_trend and fs.revenue_trend:
                revenue_trend = fs.revenue_trend

        latest_revenue = revenue.get(org.latest_period or "") if org.latest_period else None
        latest_profit = profit.get(org.latest_period or "") if org.latest_period else None

        return {
            "success": True,
            "company": {
                "inn": org.inn,
                "ogrn": org.ogrn,
                "short_name": org.short_name,
                "full_name": org.short_name,
                "legal_address": org.address,
                "status": org.status,
                "okved_main": org.okved2,
                "revenue": revenue,
                "profit": profit,
                "gross_profit": gross_profit,
                "operating_profit": operating_profit,
                "revenue_trend": revenue_trend,
                "data_source": "nalog",
                "latest_revenue": latest_revenue,
                "latest_profit": latest_profit,
            },
        }

    except Exception as e:
        logger.exception("Failed to fetch nalog financials for %s", identifier)
        return {
            "success": False,
            "error": f"Failed to fetch financials: {str(e)}",
            "company": None,
        }
