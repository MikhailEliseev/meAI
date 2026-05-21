"""DaData API client for Russian company search and financial data.

Primary: DaData (dadata.ru) — official REST API, free 10k req/day.
Fallback: SPARK-Interfax (if configured) — richer financials.
"""

import logging
import os
from typing import Optional

import httpx

from .models import CompanyProfile

logger = logging.getLogger(__name__)

DADATA_BASE = "https://suggestions.dadata.ru/suggestions/api/4_1/rs"
DADATA_TOKEN = os.getenv("DADATA_API_KEY", "")
REQUEST_TIMEOUT = 15.0

MEDICAL_OKVED_CODES = {
    "86.10",   # Деятельность больничных организаций
    "86.21",   # Общая врачебная практика
    "86.22",   # Специальная врачебная практика
    "86.23",   # Стоматологическая практика
    "86.90",   # Деятельность в области медицины прочая
    "86.90.9", # Прочая деятельность в области медицины
}

MEDICAL_OKVED_PREFIXES = ("86.",)


def _is_medical(profile: CompanyProfile) -> bool:
    """Check if company operates in medical field by OKVED codes."""
    if profile.okved_main and profile.okved_main in MEDICAL_OKVED_CODES:
        return True
    if profile.okved_main and profile.okved_main.startswith(MEDICAL_OKVED_PREFIXES):
        return True
    for code in profile.okved_secondary:
        if code in MEDICAL_OKVED_CODES or code.startswith(MEDICAL_OKVED_PREFIXES):
            return True
    return False


class DaDataClient:
    """Async client for DaData company search API."""

    def __init__(self, api_key: str | None = None):
        self.api_key = api_key or DADATA_TOKEN
        self._client: httpx.AsyncClient | None = None

    @property
    def configured(self) -> bool:
        return bool(self.api_key) and len(self.api_key) > 10

    async def _get_client(self) -> httpx.AsyncClient:
        if self._client is None:
            self._client = httpx.AsyncClient(
                timeout=REQUEST_TIMEOUT,
                headers={
                    "Authorization": f"Token {self.api_key}",
                    "Content-Type": "application/json",
                    "Accept": "application/json",
                },
            )
        return self._client

    async def close(self):
        if self._client:
            await self._client.aclose()
            self._client = None

    async def _post(self, endpoint: str, json: dict) -> dict:
        client = await self._get_client()
        response = await client.post(f"{DADATA_BASE}/{endpoint}", json=json)
        response.raise_for_status()
        return response.json()

    # ── Company search ──────────────────────────────────────────────

    async def search_company(self, query: str, count: int = 10) -> list[CompanyProfile]:
        """Search companies by name, INN, or address.

        Uses DaData suggest/party endpoint.
        """
        if not self.configured:
            logger.warning("DaData not configured — skipping company search")
            return []

        try:
            data = await self._post("suggest/party", {"query": query, "count": count})
        except httpx.HTTPError as e:
            logger.error(f"DaData search_company failed: {e}")
            return []

        suggestions = data.get("suggestions", [])
        return [_parse_suggestion(s) for s in suggestions]

    async def get_company_by_inn(self, inn: str) -> Optional[CompanyProfile]:
        """Look up a company by its INN (taxpayer ID)."""
        if not self.configured:
            return None

        try:
            data = await self._post("findById/party", {
                "query": inn,
                "branch_type": "MAIN",
            })
        except httpx.HTTPError as e:
            logger.error(f"DaData findById failed for INN {inn}: {e}")
            return None

        suggestions = data.get("suggestions", [])
        if not suggestions:
            return None
        return _parse_suggestion(suggestions[0])

    # ── Competitor search ───────────────────────────────────────────

    async def find_medical_companies(
        self,
        query: str,
        city: str = "",
        count: int = 10,
    ) -> list[CompanyProfile]:
        """Search for medical companies in a city.

        Appends city and medical OKVED filters to the query.
        """
        full_query = query
        if city:
            full_query = f"{query} {city}"
        full_query = f"{full_query} медицинская клиника"

        results = await self.search_company(full_query, count=count)
        return [p for p in results if _is_medical(p)]


def _parse_suggestion(suggestion: dict) -> CompanyProfile:
    """Parse a single DaData suggestion into a CompanyProfile."""
    data = suggestion.get("data", {})

    # Address parsing
    address = data.get("address", {}) or {}
    geo_lat = address.get("geo_lat")
    geo_lon = address.get("geo_lon")
    if geo_lat is not None:
        geo_lat = float(geo_lat)
    if geo_lon is not None:
        geo_lon = float(geo_lon)

    # OKVED
    okved_main = data.get("okved")
    okveds_data = data.get("okveds")
    okved_secondary = []
    if okveds_data:
        okved_secondary = [
            o.get("code") for o in okveds_data
            if o.get("code") and o.get("code") != okved_main
        ]

    # Employee count — DaData sometimes includes this
    employees = None
    emp_data = data.get("employee_count") or data.get("employees")
    if emp_data is not None:
        try:
            employees = int(emp_data)
        except (ValueError, TypeError):
            pass

    # Registration date
    reg_date = data.get("state", {}).get("registration_date") if isinstance(data.get("state"), dict) else None

    return CompanyProfile(
        inn=data.get("inn", ""),
        ogrn=data.get("ogrn"),
        legal_name=data.get("name", {}).get("full_with_opf", data.get("value", "")),
        brand_name=data.get("name", {}).get("short_with_opf"),
        employee_count=employees,
        registration_date=reg_date,
        okved_main=okved_main,
        okved_secondary=okved_secondary,
        legal_address=address.get("value"),
        actual_addresses=[address.get("value")] if address.get("value") else [],
        geo_lat=geo_lat,
        geo_lon=geo_lon,
        data_source="dadata",
        confidence=0.75,
    )


# ── Singleton ──────────────────────────────────────────────────────

_dadata: DaDataClient | None = None


def get_dadata_client() -> DaDataClient:
    global _dadata
    if _dadata is None:
        _dadata = DaDataClient()
    return _dadata
