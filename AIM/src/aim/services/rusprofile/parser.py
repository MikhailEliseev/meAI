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
    financial_year: int = 0
    revenue_trend: str = ""
    profit_trend: str = ""
    value_trend: str = ""

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
    # Canonical link: just grab the href
    match = re.search(r'<link\s[^>]*rel="canonical"[^>]*href="([^"]+)"', html)
    if match:
        return match.group(1)
    # Fallback: find first search result link (new HTML structure with list-element blocks)
    match = re.search(r'<div class="list-element">\s*<a\s[^>]*href="(/id/\d+)"', html)
    if match:
        return f"https://www.rusprofile.ru{match.group(1)}"
    return None


def _parse_search_results(html: str) -> list[dict]:
    """Parse search results page into list of company summaries.

    Splits on list-element blocks and extracts each field individually.
    More robust than a single monster regex — survives HTML structure changes.
    """
    results = []
    # Split into individual company blocks
    blocks = re.split(r'<div class="list-element">\s*', html)
    for block in blocks[1:]:  # first block is everything before first company
        # Extract href from the title link
        href_m = re.search(r'href="(/id/\d+)"', block)
        if not href_m:
            continue
        rusprofile_id = href_m.group(1).split("/")[-1]

        # Extract title text (may contain <mark> tags)
        title_m = re.search(
            r'<a[^>]*class="[^"]*list-element__title[^"]*"[^>]*>(.*?)</a>',
            block, re.DOTALL,
        )
        name = ""
        if title_m:
            name = re.sub(r"<[^>]+>", "", title_m.group(1)).strip()

        # Extract address
        addr_m = re.search(
            r'<div class="list-element__address">(.*?)</div>',
            block, re.DOTALL,
        )
        address = addr_m.group(1).strip() if addr_m else ""

        # Extract INN and OGRN
        inn_m = re.search(r"ИНН:\s*(\d{10,12})", block)
        ogrn_m = re.search(r"ОГРН:\s*(\d{13,15})", block)
        inn = inn_m.group(1) if inn_m else ""
        ogrn = ogrn_m.group(1) if ogrn_m else ""

        results.append({
            "rusprofile_id": rusprofile_id,
            "name": name,
            "address": address,
            "inn": inn,
            "ogrn": ogrn,
        })
    return results


def _parse_print_page(html: str) -> RusprofileCompany:
    """Parse rusprofile print page into RusprofileCompany.

    rusprofile.ru (as of mid-2026) loads financial data via JavaScript.
    The print page (?print=1) exposes a preview tile with the latest year's
    revenue (unmasked), while profit and company value are behind a login wall.

    We parse BOTH the raw HTML (for financial widgets) and the stripped text
    (for metadata like INN/OGRN/director).
    """
    c = RusprofileCompany()

    # DEBUG: check if financial keywords exist in raw HTML
    _fin_idx = html.find("Основные показатели")
    _fin_cols_idx = html.find("finance-columns")
    _fin_col_idx = html.find("finance-col")
    _rev_idx = html.find("Выручка")
    logger.info(
        "rusprofile _parse_print_page: html_len=%d, fin_section=%d, fin_cols=%d, fin_col=%d, revenue=%d",
        len(html), _fin_idx, _fin_cols_idx, _fin_col_idx, _rev_idx,
    )

    # ── 1. Metadata from stripped text ──────────────────────────────
    text = re.sub(r"<[^>]+>", "\n", html)
    text = re.sub(r"&quot;", '"', text)
    text = re.sub(r"&amp;", "&", text)
    text = re.sub(r"&lt;", "<", text)
    text = re.sub(r"&gt;", ">", text)
    text = re.sub(r"\n\s*\n", "\n", text)
    lines = [l.strip() for l in text.split("\n") if l.strip()]

    # Company name — first substantive line after title
    for line in lines:
        if "ИНН" in line and "адрес" in line:
            # e.g. 'ООО "Спектр" Ангарск (ИНН 3801134241) адрес и телефон'
            m = re.search(r'^(.+?)\s*\(ИНН\s*\d+\)', line)
            if m:
                c.short_name = m.group(1).strip()
            break

    for i, line in enumerate(lines):
        # INN
        if "ИНН" in line:
            m = re.search(r"ИНН\s*(\d{10,12})", line)
            if m and not c.inn:
                c.inn = m.group(1)

        # OGRN
        if "ОГРН" in line:
            m = re.search(r"ОГРН\s*(\d{13,15})", line)
            if m and not c.ogrn:
                c.ogrn = m.group(1)

        # KPP
        if "КПП" in line:
            m = re.search(r"КПП\s*(\d{9})", line)
            if m and not c.kpp:
                c.kpp = m.group(1)

        # Full legal name
        if "Полное наименование" in line:
            # Next line usually has the name
            if i + 1 < len(lines) and len(lines[i + 1]) > 5:
                c.full_name = lines[i + 1].strip('"').strip()
            else:
                m = re.search(r"Полное наименование\s*(.+)", line)
                if m:
                    c.full_name = m.group(1).strip('"').strip()

        # Short name
        if "Краткое наименование" in line and not c.short_name:
            if i + 1 < len(lines) and len(lines[i + 1]) > 3:
                c.short_name = lines[i + 1].strip('"').strip()
            else:
                m = re.search(r"Краткое наименование\s*(.+)", line)
                if m:
                    c.short_name = m.group(1).strip('"').strip()

        # Registration date
        if "Дата регистрации" in line:
            m = re.search(r"(\d{1,2}\s+\w+\s+\d{4})\s*г\.?", line)
            if m:
                c.registration_date = m.group(1)

        # Director
        if re.search(r"(?:директор|руководитель|генеральный\s+директор)", line, re.IGNORECASE):
            m = re.search(r"(?:директор|руководитель|генеральный\s+директор)\s*[-–—]\s*(.+)", line, re.IGNORECASE)
            if m:
                c.director = m.group(1).strip()

        # Legal address
        if "Юридический адрес" in line or "Адрес" in line:
            m = re.search(r"(?:адрес|Адрес)\s*(.+)", line)
            if m:
                addr = m.group(1).strip()
                if len(addr) > 10:
                    c.legal_address = addr

        # Tax regime
        if "Специальный налоговый режим" in line:
            m = re.search(r"(УСН|ОСН|ЕНВД|ПСН|ЕСХН)", line)
            if m:
                c.tax_regime = m.group(0)

        # MSP category
        if "Категория субъекта МСП" in line:
            m = re.search(r"(Малое|Среднее|Микро)\s*предприятие", line)
            if m:
                c.msp_category = m.group(0)

        # OKVED main
        if re.match(r"^\d{2}\.\d{2}\b", line) and not c.okved_main:
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

    # ── 2. Financial data from raw HTML ─────────────────────────────
    _parse_finance_widget(html, c)

    # ── 3. Revenue trend from stripped text ─────────────────────────
    _parse_revenue_trend(lines, c)

    return c


def _parse_finance_widget(html: str, c: RusprofileCompany) -> None:
    """Extract financial preview from the rusprofile print-page widget.

    The widget has this structure (mid-2026):
      <p>Основные показатели за NNNN год:</p>
      <div class="finance-col">
        <div>Выручка</div>
        <div><span class="num">1,0</span><span class="num-text">млн руб.</span></div>
        <span class="diff"><span class="arr">&uarr;</span>+180 %</span>
      </div>
      <!-- Прибыль and Стоимость are behind <span class="under_mask"> -->

    Revenue is publicly visible; profit and company value require login.
    """
    # Extract the "Основные показатели за XXXX год" block
    # Find the finance columns section
    fin_section = re.search(
        r'Основные показатели за\s+(\d{4})\s+год.*?<div class="finance-col[^"]*">\s*<div[^>]*>\s*Выручка\s*</div>',
        html, re.DOTALL,
    )
    year = 0
    if fin_section:
        year = int(fin_section.group(1))
        logger.info("rusprofile fin_section matched: year=%d", year)
    else:
        logger.info("rusprofile fin_section NOT matched")

    # Find ALL finance-col blocks in the finance-columns section
    # The finance-columns div contains 3 finance-col divs (revenue, profit, value)
    fin_cols_match = re.search(
        r'<div class="finance-columns[^"]*">(.*?)</div>\s*<div class="finance-chart',
        html, re.DOTALL,
    )
    if not fin_cols_match:
        logger.info("rusprofile fin_cols_match NOT found — returning empty")
        return

    fin_html = fin_cols_match.group(1)
    logger.info("rusprofile fin_cols_match found: len=%d", len(fin_html))

    # Extract individual finance-col blocks
    all_cols = re.findall(r'<div class="finance-col[^"]*">(.*?)</div>\s*</div>', fin_html, re.DOTALL)
    logger.info("rusprofile all_cols regex1: %d matches", len(all_cols))
    if not all_cols:
        # Try simpler pattern — each col ends with </div>
        all_cols = re.findall(
            r'<div class="finance-col[^"]*">(.*?)</div>\s*(?=<div class="finance-col|<div class="finance-chart|$)',
            fin_html, re.DOTALL,
        )
        logger.info("rusprofile all_cols regex2: %d matches", len(all_cols))

    for i, col_html in enumerate(all_cols):
        # Determine which metric this is
        has_revenue = "Выручка" in col_html or "tab_revenue" in col_html
        has_profit = "Прибыль" in col_html or "tab_profit" in col_html
        has_value = "Стоимость" in col_html or "tab_value" in col_html

        if has_revenue:
            metric = "revenue"
        elif has_profit:
            metric = "profit"
        elif has_value:
            metric = "value"
        else:
            logger.info("rusprofile col[%d]: unknown metric, skipping", i)
            continue

        is_masked = "under_mask" in col_html or "quetip" in col_html
        logger.info(
            "rusprofile col[%d]: metric=%s, masked=%s, col_len=%d",
            i, metric, is_masked, len(col_html),
        )

        # Skip if masked (requires login)
        if is_masked:
            # Still try to extract the growth percentage
            _extract_financial_growth(col_html, c, metric, year)
            continue

        # Extract numeric value: <span class="num">1,0</span>
        num_m = re.search(r'<span class="num">([\d\s,]+)</span>', col_html)
        if not num_m:
            logger.info("rusprofile col[%d]: num_m NOT matched", i)
            # Value is hidden — only extract growth if available
            _extract_financial_growth(col_html, c, metric, year)
            continue

        raw_num = num_m.group(1).replace(" ", "").replace(",", ".")
        try:
            amount = float(raw_num)
        except ValueError:
            logger.info("rusprofile col[%d]: float conversion failed for '%s'", i, raw_num)
            continue

        # Extract unit: <span class="num-text">млн&nbsp;руб.</span>
        unit_m = re.search(r'<span class="num-text">(млн|тыс)', col_html)
        unit = unit_m.group(1) if unit_m else ""
        logger.info("rusprofile col[%d]: amount=%s, unit=%s", i, raw_num, unit)

        if unit == "млн":
            amount *= 1_000_000
        elif unit == "тыс":
            amount *= 1_000

        if metric == "revenue":
            c.revenue[year] = int(amount)
            c.financial_year = year
        elif metric == "profit":
            c.profit[year] = int(amount)
        elif metric == "value":
            c.value[year] = int(amount)

        # Extract growth percentage
        _extract_financial_growth(col_html, c, metric, year)


def _extract_financial_growth(
    col_html: str, c: RusprofileCompany, metric: str, year: int,
) -> None:
    """Extract growth percentage and direction from a finance-col block.

    Sets c.revenue_trend, c.profit_trend, or leaves them unchanged.
    Growth format: <span class="arr">&uarr;</span>+180 %
    """
    diff_m = re.search(
        r'<span class="diff[^"]*">\s*<span class="arr">(&[a-z]+;)</span>\s*([+-]\d+)\s*%',
        col_html,
    )
    if not diff_m:
        return

    arrow_entity = diff_m.group(1)
    change_pct = diff_m.group(2)

    direction = ""
    if "uarr" in arrow_entity:
        direction = "↑"
    elif "darr" in arrow_entity:
        direction = "↓"

    trend_str = f"{direction}{change_pct}%"

    if metric == "revenue":
        c.revenue_trend = trend_str
    elif metric == "profit":
        c.profit_trend = trend_str
    elif metric == "value":
        c.value_trend = trend_str


def _parse_revenue_trend(lines: list[str], c: RusprofileCompany) -> None:
    """Extract historical revenue data from stripped text (fallback).

    The print page may include a "Динамика выручки" section with yearly
    revenue numbers in a comparison table. This serves as fallback when
    the finance widget is unavailable.
    """
    in_revenue_section = False
    for line in lines:
        if "Динамика выручки" in line:
            in_revenue_section = True
            continue
        if in_revenue_section and ("Динамика прибыли" in line or "Динамика стоимости" in line):
            in_revenue_section = False
            continue
        if not in_revenue_section:
            continue

        # Try to match year + revenue patterns
        # e.g. "2024  15,2 млн руб."
        m = re.search(r"(\d{4})\s+([\d\s,]+)\s*(млн|тыс)?\s*руб", line)
        if m:
            year = int(m.group(1))
            amount = float(m.group(2).replace(" ", "").replace(",", "."))
            unit = m.group(3) or ""
            if unit == "млн":
                amount *= 1_000_000
            elif unit == "тыс":
                amount *= 1_000
            if year not in c.revenue:
                c.revenue[year] = int(amount)


# ── Singleton ──────────────────────────────────────────────────────────────

_rusprofile: RusprofileClient | None = None


def get_rusprofile_client() -> RusprofileClient:
    global _rusprofile
    if _rusprofile is None:
        _rusprofile = RusprofileClient()
    return _rusprofile
