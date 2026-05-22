"""Rusprofile.ru parser — Python port of RomanHuBoss/RusprofileParser VBScript.

Fetches company financial data from rusprofile.ru by INN or OGRN.
Uses the print-friendly page (?print=1) for easy HTML parsing.
No API key needed — public data scraping.

Source: https://github.com/RomanHuBoss/RusprofileParser (VBScript → Python port)
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field
from typing import Optional

import httpx

logger = logging.getLogger(__name__)

REQUEST_TIMEOUT = 15.0
USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
)
RUSPROFILE_SEARCH = "https://www.rusprofile.ru/search?query={}"


@dataclass
class RusprofileCompany:
    """Parsed company data from rusprofile.ru."""

    inn: str = ""
    ogrn: str = ""
    kpp: str = ""
    short_name: str = ""
    full_name: str = ""
    legal_address: str = ""
    director: str = ""
    registration_date: str = ""
    status: str = "Действующее"

    # Financials (RUB)
    revenue: dict[int, int] = field(default_factory=dict)  # year → rubles
    profit: dict[int, int] = field(default_factory=dict)   # year → rubles
    value: dict[int, int] = field(default_factory=dict)     # year → rubles

    # Classification
    okved_main: str = ""
    okved_secondary: list[str] = field(default_factory=list)
    tax_regime: str = ""  # УСН, ОСН, etc.
    msp_category: str = ""  # Малое/Среднее/Микро предприятие

    # Relations
    founder_name: str = ""
    founder_share: str = ""
    founder_inn: str = ""

    # Misc
    license_count: int = 0
    trademark_count: int = 0
    arbitration_cases: int = 0
    gov_procurements: bool = False

    # Metadata
    rusprofile_id: str = ""
    fetched_at: str = ""


class RusprofileClient:
    """Async client for rusprofile.ru company data scraping."""

    def __init__(self):
        self._client: httpx.AsyncClient | None = None

    async def _get_client(self) -> httpx.AsyncClient:
        if self._client is None:
            self._client = httpx.AsyncClient(
                timeout=REQUEST_TIMEOUT,
                headers={
                    "User-Agent": USER_AGENT,
                    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                    "Accept-Language": "ru-RU,ru;q=0.8,en-US;q=0.5,en;q=0.3",
                },
                follow_redirects=True,
            )
        return self._client

    async def close(self):
        if self._client:
            await self._client.aclose()
            self._client = None

    # ── Public API ────────────────────────────────────────────────────

    async def get_by_inn(self, inn: str) -> Optional[RusprofileCompany]:
        """Fetch company data by INN."""
        return await self._fetch(inn=inn)

    async def get_by_ogrn(self, ogrn: str) -> Optional[RusprofileCompany]:
        """Fetch company data by OGRN."""
        return await self._fetch(ogrn=ogrn)

    async def search(self, query: str) -> list[dict]:
        """Search rusprofile.ru for companies matching query.

        Returns list of {name, inn, ogrn, address, rusprofile_id}.
        Used to find INN/OGRN when only the company name is known.
        """
        client = await self._get_client()
        url = RUSPROFILE_SEARCH.format(query)
        try:
            response = await client.get(url)
            response.raise_for_status()
        except httpx.HTTPError as e:
            logger.error("rusprofile search failed: %s", e)
            return []

        return _parse_search_results(response.text)

    # ── Internal ──────────────────────────────────────────────────────

    async def _fetch(
        self, inn: str = "", ogrn: str = ""
    ) -> Optional[RusprofileCompany]:
        """Fetch and parse company data from rusprofile.ru."""
        identifier = inn or ogrn
        if not identifier:
            return None

        client = await self._get_client()
        search_url = RUSPROFILE_SEARCH.format(identifier)

        # Step 1: Search by INN/OGRN to get canonical URL
        try:
            response = await client.get(search_url)
            response.raise_for_status()
        except httpx.HTTPError as e:
            logger.error("rusprofile fetch failed for %s: %s", identifier, e)
            return None

        # Step 2: Extract canonical URL and get print version
        canonical = _extract_canonical(response.text)
        if not canonical:
            logger.warning("Could not find canonical URL for %s", identifier)
            return None

        print_url = f"{canonical}?print=1"
        rusprofile_id = canonical.rstrip("/").split("/")[-1]

        try:
            response = await client.get(print_url)
            response.raise_for_status()
        except httpx.HTTPError as e:
            logger.error("rusprofile print page failed: %s", e)
            return None

        # Step 3: Parse
        company = _parse_print_page(response.text)
        company.rusprofile_id = rusprofile_id
        return company


# ── HTML Parsers ──────────────────────────────────────────────────────────

def _extract_canonical(html: str) -> Optional[str]:
    """Extract canonical URL from rusprofile search results page."""
    match = re.search(r'<link[^>]+rel="canonical"[^>]+href="([^"]+)"', html)
    if match:
        return match.group(1)
    # Fallback: find first search result link
    match = re.search(r'<a[^>]+href="(/id/\d+)"[^>]*class="[^"]*list-element__title', html)
    if match:
        return f"https://www.rusprofile.ru{match.group(1)}"
    return None


def _parse_search_results(html: str) -> list[dict]:
    """Parse search results page into list of company summaries."""
    results = []
    # Match each search result block
    pattern = re.compile(
        r'<a[^>]+href="(/id/\d+)"[^>]*class="[^"]*list-element__title[^"]*">(.*?)</a>'
        r'.*?<div class="list-element__address">(.*?)</div>'
        r'.*?ИНН:\s*(\d+).*?ОГРН:\s*(\d+)',
        re.DOTALL,
    )
    for match in pattern.finditer(html):
        results.append({
            "rusprofile_id": match.group(1).split("/")[-1],
            "name": re.sub(r"<[^>]+>", "", match.group(2)).strip(),
            "address": match.group(3).strip(),
            "inn": match.group(4),
            "ogrn": match.group(5),
        })
    return results


def _parse_print_page(html: str) -> RusprofileCompany:
    """Parse rusprofile print page into RusprofileCompany."""
    c = RusprofileCompany()

    # Remove all HTML tags for text extraction
    text = re.sub(r"<[^>]+>", "\n", html)
    text = re.sub(r"&quot;", '"', text)
    text = re.sub(r"&amp;", "&", text)
    text = re.sub(r"&lt;", "<", text)
    text = re.sub(r"&gt;", ">", text)
    text = re.sub(r"\n\s*\n", "\n", text)
    lines = [l.strip() for l in text.split("\n") if l.strip()]

    # Extract structured data
    for i, line in enumerate(lines):
        # INN
        if "ИНН" in line and not c.inn:
            # Next line or same line contains the number
            m = re.search(r"ИНН\s*(\d{10,12})", line)
            if m:
                c.inn = m.group(1)
            elif i + 1 < len(lines) and re.match(r"^\d{10,12}$", lines[i + 1]):
                c.inn = lines[i + 1]

        # OGRN
        if "ОГРН" in line and not c.ogrn:
            m = re.search(r"ОГРН\s*(\d{13,15})", line)
            if m:
                c.ogrn = m.group(1)

        # KPP
        if "КПП" in line and not c.kpp:
            m = re.search(r"КПП\s*(\d{9})", line)
            if m:
                c.kpp = m.group(1)

        # Registration date
        if "Дата регистрации" in line and not c.registration_date:
            m = re.search(r"(\d{1,2}\s+\w+\s+\d{4})\s*г\.?", line)
            if m:
                c.registration_date = m.group(1)

        # Tax regime
        if "Специальный налоговый режим" in line or "УСН" in line:
            m = re.search(r"(УСН|ОСН|ЕНВД|ПСН|ЕСХН)\s*(\(?\d{4}\)?)?", line)
            if m:
                c.tax_regime = m.group(0).strip()
        if "УСН" in line and not c.tax_regime:
            c.tax_regime = "УСН"

        # MSP category
        if "Категория субъекта МСП" in line:
            m = re.search(r"(Малое|Среднее|Микро)\s*предприятие", line)
            if m:
                c.msp_category = m.group(0)

        # Director/founder
        if "директор" in line.lower() or "руководитель" in line.lower():
            m = re.search(r"(?:директор|руководитель|генеральный\s+директор)\s*[-–—]\s*(.+)", line, re.IGNORECASE)
            if m:
                c.director = m.group(1).strip()

        # Founder
        if "Учредитель" in line and "Юцковская" in line:  # Will match any name
            m = re.search(r"Учредители?\s*(.+)", line)
            if m:
                c.founder_name = m.group(1).strip()

        # OKVED
        if re.match(r"^\d{2}\.\d{2}", line) and not c.okved_main:
            c.okved_main = line.strip()

        # License count
        if "Лицензии" in line:
            m = re.search(r"Всего\s*(\d+)", line)
            if m:
                c.license_count = int(m.group(1))

        # Trademarks
        if "Товарные знаки" in line or "товарных знаков" in line:
            m = re.search(r"(\d+)\s*(?:действующих|товарных)", line)
            if m:
                c.trademark_count = int(m.group(1))

    # Parse financial table (Выручка / Прибыль / Стоимость by year)
    _parse_financial_table(lines, c)

    return c


def _parse_financial_table(lines: list[str], c: RusprofileCompany) -> None:
    """Extract financial data (year → revenue/profit/value) from parsed lines."""
    # Pattern: year line followed by "Выручка: X млн руб.", "Прибыль: Y млн руб.", etc.
    for i, line in enumerate(lines):
        year_match = re.match(r"^(\d{4})$", line)
        if not year_match:
            continue
        year = int(year_match.group(1))

        # Look ahead for financial values
        revenue = None
        profit = None
        value = None
        for j in range(i + 1, min(i + 10, len(lines))):
            look = lines[j]
            # Stop at next year
            if re.match(r"^\d{4}$", look):
                break
            if "Выручка" in look:
                m = re.search(r"([\d\s.]+)\s*(?:млн|тыс)?\s*руб", look)
                if m:
                    amount = float(m.group(1).replace(" ", "").replace(",", "."))
                    if "млн" in look:
                        amount *= 1_000_000
                    elif "тыс" in look:
                        amount *= 1_000
                    revenue = int(amount)
            elif "Прибыль" in look:
                m = re.search(r"([\d\s.]+)\s*(?:млн|тыс)?\s*руб", look)
                if m:
                    amount = float(m.group(1).replace(" ", "").replace(",", "."))
                    if "млн" in look:
                        amount *= 1_000_000
                    elif "тыс" in look:
                        amount *= 1_000
                    profit = int(amount)
            elif "Стоимость" in look:
                m = re.search(r"([\d\s.]+)\s*(?:млн|тыс)?\s*руб", look)
                if m:
                    amount = float(m.group(1).replace(" ", "").replace(",", "."))
                    if "млн" in look:
                        amount *= 1_000_000
                    elif "тыс" in look:
                        amount *= 1_000
                    value = int(amount)

        if revenue is not None:
            c.revenue[year] = revenue
        if profit is not None:
            c.profit[year] = profit
        if value is not None:
            c.value[year] = value


# ── Singleton ──────────────────────────────────────────────────────────────

_rusprofile: RusprofileClient | None = None


def get_rusprofile_client() -> RusprofileClient:
    global _rusprofile
    if _rusprofile is None:
        _rusprofile = RusprofileClient()
    return _rusprofile
