"""Roszdravnadzor medical license registry client.

Queries the public license registry for medical organization licenses.
Graceful degradation: returns empty list on any failure, never raises.
"""

from __future__ import annotations

import logging
from typing import Optional

import httpx

logger = logging.getLogger(__name__)

_USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/148.0.0.0 Safari/537.36"
)


class RoszdravnadzorClient:
    """Client for Roszdravnadzor medical license registry.

    Primary approach: search the public registry via HTTP.
    Fallback: return empty list — Roszdravnadzor data is supplementary.
    Never raises — all errors are caught and logged.
    """

    def __init__(self, timeout: float = 10.0) -> None:
        self._timeout = timeout
        self._http: Optional[httpx.AsyncClient] = None

    async def _get_http(self) -> httpx.AsyncClient:
        if self._http is None:
            self._http = httpx.AsyncClient(
                timeout=httpx.Timeout(self._timeout),
                follow_redirects=True,
                verify=False,
                headers={"User-Agent": _USER_AGENT},
            )
        return self._http

    async def search_licenses(
        self, company_name: str, inn: str = ""
    ) -> list[dict]:
        """Search for medical licenses by company name or INN.

        Returns list of license dicts with: number, date_from, date_to,
        services, status. Returns empty list if search fails or no licenses
        found. Never raises.
        """
        try:
            http = await self._get_http()

            # Try the Roszdravnadzor public registry search
            search_url = "https://roszdravnadzor.gov.ru/services/licenses"
            params = {}
            if inn:
                params["inn"] = inn
            else:
                params["name"] = company_name

            r = await http.get(search_url, params=params)
            if r.status_code != 200:
                logger.debug(
                    "Roszdravnadzor returned %d for %s — skipping",
                    r.status_code, company_name,
                )
                return []

            licenses = self._parse_license_table(r.text)
            logger.info(
                "Roszdravnadzor: found %d license(s) for %s",
                len(licenses), company_name,
            )
            return licenses

        except httpx.TimeoutException:
            logger.debug("Roszdravnadzor timed out for %s", company_name)
        except Exception as e:
            logger.debug("Roszdravnadzor search failed for %s: %s", company_name, e)

        return []

    def _parse_license_table(self, html: str) -> list[dict]:
        """Parse license data from Roszdravnadzor HTML table.

        Extracts: license number, validity period, services list.
        Returns empty list if parsing fails.
        """
        import re

        licenses = []
        try:
            # Look for license number patterns: ЛО-XX-XX-XXXXXX
            lo_pattern = re.compile(
                r'(ЛО|ФС)-\d{2}-\d{2}-\d{6,7}',
                re.IGNORECASE,
            )
            found = lo_pattern.findall(html)
            for match in found:
                licenses.append({
                    "number": match,
                    "date_from": "",
                    "date_to": "",
                    "services": [],
                    "status": "active",
                })
        except Exception as e:
            logger.debug("License table parsing failed: %s", e)

        return licenses

    async def close(self) -> None:
        if self._http is not None:
            await self._http.aclose()
            self._http = None
