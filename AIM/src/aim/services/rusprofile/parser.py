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

        # Step 2: Extract canonical URL and get both print + regular versions
        canonical = _extract_canonical(response.text)
        if not canonical:
            logger.warning("Could not find canonical URL for %s", identifier)
            return None

        print_url = f"{canonical}?print=1"
        rusprofile_id = canonical.rstrip("/").split("/")[-1]

        # Fetch print page (metadata: name, INN, director, etc.)
        try:
            print_resp = await client.get(print_url)
            print_resp.raise_for_status()
        except httpx.HTTPError as e:
            logger.error("rusprofile print page failed: %s", e)
            return None

        print_html = print_resp.text

        # Fetch regular page (for financial data — unmasked revenue)
        finance_html = ""
        try:
            fin_resp = await client.get(canonical)
            fin_resp.raise_for_status()
            finance_html = fin_resp.text
        except httpx.HTTPError as e:
            logger.debug("rusprofile regular page failed: %s (will try print page finance)", e)

        # Step 3: Parse metadata from print page, financials from regular (or print fallback)
        company = _parse_print_page(print_html, finance_html=finance_html)
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


def _parse_print_page(html: str, finance_html: str = "") -> RusprofileCompany:
    """Parse rusprofile print page into RusprofileCompany.

    rusprofile.ru (as of mid-2026) loads financial data via JavaScript.
    The print page (?print=1) exposes a preview tile with the latest year's
    revenue (unmasked), while profit and company value are behind a login wall.

    The *regular* page (finance_html) often has fully unmasked financial data
    including profit, company value, and historical trends. We try it first,
    and fall back to the print page's preview tile.

    We parse BOTH the raw HTML (for financial widgets) and the stripped text
    (for metadata like INN/OGRN/director).
    """
    c = RusprofileCompany()

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
    # Try regular page first (unmasked data), then print page (preview tile)
    if finance_html:
        _parse_finance_widget(finance_html, c)
    if not c.revenue:
        _parse_finance_widget(html, c)

    # ── 3. Revenue trend from stripped text ─────────────────────────
    _parse_revenue_trend(lines, c)

    return c


def _parse_finance_widget(html: str, c: RusprofileCompany) -> None:
    """Extract financial data from rusprofile page.

    Tries TWO formats (rusprofile changes HTML structure frequently):

    1. NEW format (2026-05+): <div class="finance-columns">
       - Year in "Основные показатели за XXXX год" (may be masked: 3838 → 2020)
       - Revenue: unmasked <span class="num"> in finance-col
       - Profit/Value: may be behind <span class="under_mask"> (login wall)

    2. OLD format (pre-2026-05): <table> after "Финансовая отчетность"
       - <div class="dt-text">YYYY</div> per row
       - <div class="dt-text">Выручка/Прибыль/Стоимость:</div> per cell
       - Units: млн/тыс руб., arrows: arrow-up/arrow-down.svg
    """
    if _parse_finance_columns(html, c):
        return
    _parse_finance_table(html, c)


def _decode_year(raw_year: str) -> int:
    """Decode rusprofile masked year. Masked years are > 3000, offset by 1818.

    Returns 0 for clearly invalid years (sanitation against parsing garbage).
    """
    try:
        y = int(raw_year)
    except (ValueError, TypeError):
        return 0
    if y > 3000:
        y -= 1818
    # Valid financial years: 2015-2030
    if y < 2015 or y > 2030:
        return 0
    return y


def _parse_finance_columns(html: str, c: RusprofileCompany) -> bool:
    """Parse NEW finance-columns format. Returns True if data was extracted."""
    # Find the finance tile — look for "Основные показатели за" text
    year_match = re.search(
        r'Основные показатели за\s+(\d{4})\s+год',
        html,
    )
    if not year_match:
        # Try in print page format
        year_match = re.search(r'Основные показатели за\s+(\d{4})\s+год', html)

    # Find finance-columns block — go back to the opening <div
    fc_marker = html.find('class="finance-columns')
    if fc_marker == -1:
        # Try alternative: "finance-columns" without class= prefix
        fc_marker = html.find('finance-columns')
    if fc_marker == -1:
        return False

    # Back up to find the opening <div tag
    block_start = html.rfind('<div', fc_marker - 100, fc_marker)
    if block_start == -1:
        return False

    # Extract the year
    year = _decode_year(year_match.group(1)) if year_match else 0

    # Get the finance-columns block (up to 3000 chars from block start)
    block = html[block_start: block_start + 3000]

    # Split on each finance-col opening tag
    cols_raw = re.split(r'<div class="finance-col[^"]*">', block)
    if len(cols_raw) < 2:
        return False
    cols = cols_raw[1:]  # first element is everything before first finance-col

    for col_html in cols:
        # Detect metric type from data-tab_name
        tab_match = re.search(r'data-tab_name="tab_(\w+)"', col_html)
        if not tab_match:
            continue
        metric = tab_match.group(1)  # revenue, profit, value

        # Check if data is behind login wall — only skip if actual masked span exists
        if '<span class="under_mask">' in col_html:
            logger.debug("rusprofile: skipping %s (under_mask detected)", metric)
            continue

        # Extract numeric value — handle both "млн руб.", "тыс. руб.", and plain "руб."
        # Units may contain &nbsp; HTML entities
        num_match = re.search(
            r'<span class="num">([\d\s,]+)</span>\s*'
            r'<span class="num-text">(млн|тыс|руб)',
            col_html,
        )
        if not num_match:
            logger.debug("rusprofile: skipping %s (no num match)", metric)
            continue

        raw_num = num_match.group(1)
        unit = num_match.group(2)

        try:
            amount = float(raw_num.replace(" ", "").replace(",", "."))
        except ValueError:
            continue

        if unit == "млн":
            amount *= 1_000_000
        elif unit == "тыс":
            amount *= 1_000
        # unit == "руб": amount stays as-is

        # Extract trend (arrow direction + percentage change)
        trend_str = ""
        arr_match = re.search(r'<span class="arr">(&[a-z]+;)</span>', col_html)
        pct_match = re.search(r'([+-]\d+)\s*%', col_html)
        if arr_match:
            arrow_html = arr_match.group(1)
            direction = "↑" if "uarr" in arrow_html else "↓"
            change = pct_match.group(1) if pct_match else ""
            trend_str = f"{direction}{change}%"

        if metric == "revenue":
            c.revenue[year] = int(amount)
            c.financial_year = max(c.financial_year, year)
            if trend_str:
                c.revenue_trend = trend_str
        elif metric == "profit":
            c.profit[year] = int(amount)
            if trend_str:
                c.profit_trend = trend_str
        elif metric in ("value", "costs"):
            c.value[year] = int(amount)
            if trend_str:
                c.value_trend = trend_str

    if c.revenue:
        logger.debug(
            "rusprofile finance (columns): revenue=%s, profit=%s, value=%s, year=%d",
            c.revenue, c.profit, c.value, c.financial_year,
        )
        return True
    return False


def _parse_finance_table(html: str, c: RusprofileCompany) -> None:
    """Parse OLD table-based finance format (pre-2026-05)."""
    fin_idx = html.find("Финансовая отчетность")
    if fin_idx == -1:
        logger.debug("rusprofile: 'Финансовая отчетность' not found")
        return

    table_match = re.search(
        r'<table>\s*<tbody>(.*?)</tbody>\s*</table>',
        html[fin_idx: fin_idx + 3000],
        re.DOTALL,
    )
    if not table_match:
        logger.debug("rusprofile: no <table> after 'Финансовая отчетность'")
        return

    tbody = table_match.group(1)
    rows = re.findall(r'<tr>(.*?)</tr>', tbody, re.DOTALL)
    for row_html in rows:
        year_match = re.search(r'<div class="dt-text">(\d{4})</div>', row_html)
        if not year_match:
            continue
        year = int(year_match.group(1))

        cells = re.findall(
            r'<div class="dt-text">(Выручка|Прибыль|Стоимость):</div>\s*'
            r'<span class="num">([\d\s,]+)</span>\s*'
            r'(млн|тыс)\.?\s*руб\.?'
            r'(?:\s*<img[^>]*arrow-(up|down)\.svg[^>]*>)?',
            row_html,
        )

        for metric_name, raw_num, unit, arrow_dir in cells:
            try:
                amount = float(raw_num.replace(" ", "").replace(",", "."))
            except ValueError:
                continue

            if unit == "млн":
                amount *= 1_000_000
            elif unit == "тыс":
                amount *= 1_000

            if metric_name == "Выручка":
                c.revenue[year] = int(amount)
                c.financial_year = max(c.financial_year, year)
                if arrow_dir:
                    c.revenue_trend = f"{'↑' if arrow_dir == 'up' else '↓'}"
            elif metric_name == "Прибыль":
                c.profit[year] = int(amount)
                if arrow_dir:
                    c.profit_trend = f"{'↑' if arrow_dir == 'up' else '↓'}"
            elif metric_name == "Стоимость":
                c.value[year] = int(amount)
                if arrow_dir:
                    c.value_trend = f"{'↑' if arrow_dir == 'up' else '↓'}"

    logger.debug(
        "rusprofile finance (table): revenue=%s, profit=%s, value=%s, year=%d",
        c.revenue, c.profit, c.value, c.financial_year,
    )



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
