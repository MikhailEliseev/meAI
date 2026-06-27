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

            # New structured blocks (Plan 04-01) — additive, do not affect
            # existing output fields. revenue_dynamics applies the strict
            # <3-year gate (D-13). clinic_metrics structures data for the
            # About section; OKVED descriptions are left empty for the LLM
            # to translate in Pass 3 (D-21).
            revenue_dynamics = _format_revenue_dynamics(revenue)
            clinic_metrics = _format_clinic_metrics(company)

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
                    "revenue_dynamics": revenue_dynamics,
                    "clinic_metrics": clinic_metrics,
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


def _fmt_revenue_short(val) -> str:
    """Format revenue as human-readable Russian string.

    Replicates the logic from generate_html_report._fmt_revenue_short so the
    dynamics summary_text is self-contained without cross-module imports
    (which would create a circular dependency with the HTML reporter).
    """
    if val is None:
        return "—"
    if not isinstance(val, (int, float)):
        return str(val)
    if val >= 1_000_000_000:
        return f"{val / 1_000_000_000:.1f} млрд"
    if val >= 1_000_000:
        return f"{val / 1_000_000:.0f} млн"
    if val >= 1_000:
        return f"{val / 1_000:.0f} тыс"
    return f"{int(val)}"


def _format_revenue_dynamics(revenue_by_year: dict) -> dict:
    """Build a 3-year revenue dynamics block per DAT-01, D-12..14.

    Strict <3-year gate (D-13): if fewer than 3 years are available, returns
    dynamics_available=False with an honest Russian reason. NO partial-data
    table is rendered — this prevents misleading trend claims from sparse data.

    Args:
        revenue_by_year: dict mapping year-string → amount-int (rubles).
            Example: {"2023": 4300000000, "2022": 3400000000, "2021": 2400000000}

    Returns:
        dict with shape:
        - dynamics_available=True:
            {
                "dynamics_available": True,
                "years": [{"year": "2023", "revenue": int, "yoy_pct": float|None}, ...],
                "total_growth_pct": float,
                "summary_text": str  # Russian, for LLM blockquote (D-14)
            }
        - dynamics_available=False:
            {"dynamics_available": False, "reason": str}
    """
    # Guard: empty/None/non-dict input
    if not revenue_by_year or not isinstance(revenue_by_year, dict):
        return {"dynamics_available": False, "reason": "нет данных о выручке"}

    # Filter to numeric values only (defensive — backend may include stray keys)
    numeric = {
        str(y): v
        for y, v in revenue_by_year.items()
        if isinstance(v, (int, float)) and not isinstance(v, bool)
    }
    if not numeric:
        return {"dynamics_available": False, "reason": "нет данных о выручке"}

    # Sort years descending and take the latest 3
    sorted_years = sorted(numeric.keys(), reverse=True)
    latest_3 = sorted_years[:3]

    # STRICT 3-YEAR GATE (D-13)
    if len(latest_3) < 3:
        return {
            "dynamics_available": False,
            "reason": f"доступно {len(latest_3)} год(а) — нужно минимум 3 для динамики",
        }

    # Build per-year records with YoY %
    years_list = []
    for i, year in enumerate(latest_3):
        revenue = int(numeric[year])
        if i < len(latest_3) - 1:
            prior_revenue = numeric[latest_3[i + 1]]
            if prior_revenue and prior_revenue != 0:
                yoy = round(((revenue - prior_revenue) / prior_revenue) * 100, 1)
            else:
                yoy = None
        else:
            yoy = None  # oldest year in the 3-year window has no prior
        years_list.append({"year": year, "revenue": revenue, "yoy_pct": yoy})

    # Compute total growth (latest vs oldest in window)
    oldest_revenue = numeric[latest_3[-1]]
    latest_revenue = numeric[latest_3[0]]
    if oldest_revenue and oldest_revenue != 0:
        total_growth_pct = round(
            ((latest_revenue - oldest_revenue) / oldest_revenue) * 100, 1
        )
    else:
        total_growth_pct = 0.0

    # Build summary_text (D-14) — suggestion for the LLM, not final rendering
    # Year order in the summary is oldest → latest (chronological narrative)
    oldest_year = latest_3[-1]
    middle_year = latest_3[1]
    latest_year_str = latest_3[0]
    oldest_str = _fmt_revenue_short(numeric[oldest_year])
    middle_str = _fmt_revenue_short(numeric[middle_year])
    latest_str = _fmt_revenue_short(numeric[latest_year_str])
    progression = f"{oldest_str} → {middle_str} → {latest_str}"

    if total_growth_pct >= 0:
        summary_text = (
            f"Выручка выросла на {total_growth_pct}% за 3 года ({progression})"
        )
    else:
        summary_text = (
            f"Выручка снизилась на {abs(total_growth_pct)}% за 3 года ({progression})"
        )

    return {
        "dynamics_available": True,
        "years": years_list,
        "total_growth_pct": total_growth_pct,
        "summary_text": summary_text,
    }


def _format_clinic_metrics(company: dict) -> dict:
    """Structure clinic metadata for the About section per DAT-04, D-21.

    The Pass 3 LLM consumes this block to render the About section. The
    okved_codes[].description field is intentionally empty here — the LLM
    is responsible for translating the OKVED code to a human-readable
    specialization in Pass 3 (per Plan 04-05 prompt work). This keeps the
    tool deterministic and avoids a hardcoded mapping that goes stale.

    Licenses are also an empty list: the AIM backend (nalog.ru source) does
    not carry license data — licenses are merged in from run_prescan site
    scrapes by the HTML reporter.

    Args:
        company: company dict from AIM backend API response.

    Returns:
        dict with: revenue_latest, profit_latest, employees, okved_codes,
        licenses, status, legal_address.
    """
    if not isinstance(company, dict):
        company = {}

    # Revenue: prefer pre-computed latest_revenue, fall back to _latest_value
    revenue_latest = company.get("latest_revenue")
    if revenue_latest is None:
        revenue_latest = _latest_value(company.get("revenue", {}))

    # Profit: same pattern
    profit_latest = company.get("latest_profit")
    if profit_latest is None:
        profit_latest = _latest_value(company.get("profit", {}))

    # Employees: backend may not return this — default to None
    employees = company.get("employees")

    # OKVED codes: primary code only (description deferred to LLM per D-21)
    okved_codes = []
    okved_main = company.get("okved_main")
    if okved_main:
        okved_codes.append({"code": okved_main, "description": ""})

    return {
        "revenue_latest": revenue_latest,
        "profit_latest": profit_latest,
        "employees": employees,
        "okved_codes": okved_codes,
        "licenses": [],  # merged from run_prescan at the HTML reporter layer
        "status": company.get("status"),
        "legal_address": company.get("legal_address"),
    }


registry.register(
    name="find_company_financials",
    toolset="aim-operations",
    schema={
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
    handler=handle_find_company_financials,
    check_fn=lambda: True,
    is_async=True,
    description="Get real tax-filed financial data (revenue, profit, P&L) from bo.nalog.gov.ru by INN",
    emoji="💰",
)
