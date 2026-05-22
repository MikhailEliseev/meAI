"""
Company Financials API Endpoint

GET /api/companies/financials — Real financial data from rusprofile.ru by INN/OGRN.
Wraps RusprofileParser (Python port of RomanHuBoss/RusprofileParser VBScript).
"""

import logging

from fastapi import APIRouter, HTTPException, Query

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/companies", tags=["companies"])


@router.get("/financials")
async def get_company_financials(
    inn: str = Query("", description="Company INN (10-12 digits)"),
    ogrn: str = Query("", description="Company OGRN (13-15 digits)"),
):
    """Get real financial data for a Russian company from rusprofile.ru.

    Fetches tax-filed revenue, profit, and company value by year.
    Also returns company metadata: name, director, registration date,
    tax regime, OKVED, MSP category.

    Args:
        inn: Company INN (taxpayer ID, 10-12 digits)
        ogrn: Company OGRN (state registration number, 13-15 digits)

    Returns:
        {
            "success": true,
            "company": {
                "inn": "...",
                "ogrn": "...",
                "short_name": "...",
                "full_name": "...",
                "director": "...",
                "registration_date": "...",
                "status": "Действующее",
                "revenue": {2024: 242000000, 2023: 198000000},
                "profit": {2024: 21000000, 2023: 15000000},
                "value": {2024: 180000000, 2023: 160000000},
                "tax_regime": "УСН",
                "msp_category": "Малое предприятие",
                "okved_main": "86.23",
                "license_count": 3,
                "trademark_count": 1
            }
        }
    """
    if not inn and not ogrn:
        raise HTTPException(status_code=400, detail="Either inn or ogrn is required")

    identifier = inn or ogrn
    logger.info("Fetching financials for: %s", identifier)

    try:
        from aim.services.rusprofile.parser import get_rusprofile_client

        client = get_rusprofile_client()
        if inn:
            company = await client.get_by_inn(inn)
        else:
            company = await client.get_by_ogrn(ogrn)

        if company is None:
            return {
                "success": False,
                "error": f"Company not found for {'INN' if inn else 'OGRN'}: {identifier}",
                "company": None,
            }

        return {
            "success": True,
            "company": {
                "inn": company.inn,
                "ogrn": company.ogrn,
                "kpp": company.kpp,
                "short_name": company.short_name,
                "full_name": company.full_name,
                "legal_address": company.legal_address,
                "director": company.director,
                "registration_date": company.registration_date,
                "status": company.status,
                "revenue": {str(k): v for k, v in sorted(company.revenue.items(), reverse=True)},
                "profit": {str(k): v for k, v in sorted(company.profit.items(), reverse=True)},
                "value": {str(k): v for k, v in sorted(company.value.items(), reverse=True)},
                "tax_regime": company.tax_regime,
                "msp_category": company.msp_category,
                "okved_main": company.okved_main,
                "okved_secondary": company.okved_secondary,
                "license_count": company.license_count,
                "trademark_count": company.trademark_count,
                "founder_name": company.founder_name,
                "founder_share": company.founder_share,
                "rusprofile_id": company.rusprofile_id,
            },
        }

    except Exception as e:
        logger.exception("Failed to fetch financials for %s", identifier)
        return {
            "success": False,
            "error": f"Failed to fetch financials: {str(e)}",
            "company": None,
        }
