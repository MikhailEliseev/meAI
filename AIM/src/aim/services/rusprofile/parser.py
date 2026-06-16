"""Rusprofile.ru parser — Python port of RomanHuBoss/RusprofileParser VBScript.

Fetches company financial data from rusprofile.ru by INN or OGRN.
Uses rusprofile's internal AJAX API for search and SSR company pages for data.

rusprofile.ru (2026) is a Vue SPA. The old /search?query= endpoint no longer exists.
New approach:
  1. GET homepage → get __Host-csrf-token cookie
  2. POST /ajax/search/advanced (with CSRF token) → search results as JSON
  3. GET /id/{id} (with cookies) → SSR company page → parse HTML

Source: https://github.com/RomanHuBoss/RusprofileParser (VBScript → Python port)
"""

from __future__ import annotations

import logging
import random
import re
import time
from dataclasses import dataclass, field
from typing import Optional

import httpx

logger = logging.getLogger(__name__)

REQUEST_TIMEOUT = 15.0
USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
)
RUSPROFILE_BASE = "https://www.rusprofile.ru"
RUSPROFILE_SEARCH_API = "https://www.rusprofile.ru/ajax/search/advanced"
CSRF_COOKIE_NAME = "__Host-csrf-token"


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
    """Async client for rusprofile.ru company data scraping.

    Uses the 2026 AJAX API for search and SSR company pages for detailed data.
    Maintains an httpx session with CSRF cookie across requests.
    """

    def __init__(self):
        self._client: httpx.AsyncClient | None = None
        self._csrf_token: str = ""
        self._session_ready: bool = False

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
        self._session_ready = False

    # ── Session / CSRF ───────────────────────────────────────────────────

    async def _ensure_session(self) -> None:
        """Visit homepage to get CSRF cookie. Called once per session."""
        if self._session_ready and self._csrf_token:
            return

        client = await self._get_client()

        try:
            response = await client.get(RUSPROFILE_BASE)
            response.raise_for_status()

            # Extract CSRF token from cookies
            for cookie in client.cookies.jar:
                if cookie.name == CSRF_COOKIE_NAME and cookie.domain.endswith("rusprofile.ru"):
                    self._csrf_token = cookie.value
                    break

            if self._csrf_token:
                self._session_ready = True
                logger.debug("rusprofile session ready (CSRF token obtained)")
            else:
                logger.warning("rusprofile: no CSRF cookie found after homepage visit")
                self._session_ready = True  # Don't retry endlessly
        except httpx.HTTPError as e:
            logger.warning("rusprofile: failed to get session: %s", e)
            self._session_ready = True  # Don't retry endlessly

    # ── Public API ────────────────────────────────────────────────────

    async def search(self, query: str) -> list[dict]:
        """Search rusprofile.ru for companies matching query.

        Uses the internal AJAX API: POST /ajax/search/advanced
        Returns list of {name, inn, ogrn, address, link}.
        Used to find INN/OGRN when only the company name is known.
        """
        await self._ensure_session()

        if not self._csrf_token:
            logger.warning("rusprofile search: no CSRF token, cannot search")
            return []

        client = await self._get_client()
        cache_key = str(random.random())

        try:
            response = await client.post(
                RUSPROFILE_SEARCH_API + f"?cacheKey={cache_key}",
                headers={
                    "Content-Type": "application/json",
                    "Accept": "application/json, text/plain, */*",
                    "x-csrf-token": self._csrf_token,
                    "Referer": RUSPROFILE_BASE + "/",
                },
                json={"query": query, "action": "search"},
            )
            response.raise_for_status()
            data = response.json()
        except httpx.HTTPError as e:
            logger.error("rusprofile search API failed for '%s': %s", query[:80], e)
            return []

        if not data.get("success"):
            logger.debug("rusprofile search returned success=false for '%s'", query[:80])
            return []

        items = data.get("data", {}).get("items", [])
        results = []
        for item in items:
            link = item.get("link", "")
            results.append({
                "name": item.get("name", item.get("raw_name", "")),
                "inn": item.get("inn", ""),
                "ogrn": item.get("ogrn", ""),
                "address": item.get("address", ""),
                "link": link,
                "rusprofile_id": _extract_id_from_link(link),
                "ceo_name": item.get("ceo_name", ""),
                "okved_main": item.get("main_okved_id", ""),
                "okved_descr": item.get("okved_descr", ""),
                "inactive": bool(item.get("inactive")),
                "region": item.get("region", ""),
            })

        logger.debug("rusprofile search: '%s' → %d results", query[:60], len(results))
        return results

    async def get_by_inn(
        self, inn: str, name: str = ""
    ) -> Optional[RusprofileCompany]:
        """Fetch company data by INN, optionally using name for better results."""
        return await self._fetch(inn=inn, name=name)

    async def get_by_ogrn(self, ogrn: str) -> Optional[RusprofileCompany]:
        """Fetch company data by OGRN."""
        return await self._fetch(ogrn=ogrn)

    # ── Internal ──────────────────────────────────────────────────────

    async def _fetch(
        self, inn: str = "", ogrn: str = "", name: str = ""
    ) -> Optional[RusprofileCompany]:
        """Fetch and parse company data from rusprofile.ru.

        Strategy:
        1. Search for the company via AJAX API to get its rusprofile ID
        2. GET the SSR company page at /id/{ID}
        3. Parse the HTML for financials and metadata
        """
        identifier = inn or ogrn
        if not identifier and not name:
            return None

        search_query = identifier if identifier else name
        results = await self.search(search_query)
        if not results:
            logger.debug("rusprofile: no results for '%s'", search_query[:60])
            return None

        # Find the right result — match by INN if possible, otherwise first result
        best = results[0]
        if inn:
            for r in results:
                if r.get("inn") == inn:
                    best = r
                    break

        rusprofile_id = best.get("rusprofile_id", "")
        if not rusprofile_id:
            logger.debug("rusprofile: no ID in search result for '%s'", search_query[:60])
            return None

        # GET the company page (SSR — server-rendered)
        client = await self._get_client()
        page_url = f"{RUSPROFILE_BASE}/id/{rusprofile_id}"

        try:
            response = await client.get(
                page_url,
                headers={
                    "Referer": RUSPROFILE_BASE + "/",
                    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                },
            )
            response.raise_for_status()
            html = response.text
        except httpx.HTTPError as e:
            logger.error("rusprofile: failed to fetch company page %s: %s", page_url, e)
            return None

        if len(html) < 5000:
            logger.debug("rusprofile: page too short (%d bytes) — likely bot protection", len(html))
            return None

        company = _parse_company_html(html)
        company.rusprofile_id = rusprofile_id

        # Sanity check: verify the parsed INN matches what we requested
        if inn and company.inn and company.inn != inn:
            logger.warning(
                "rusprofile INN mismatch: requested %s, got %s (%s)",
                inn, company.inn, company.short_name,
            )
            return None

        return company


# ── HTML Parsers ──────────────────────────────────────────────────────────

def _extract_id_from_link(link: str) -> str:
    """Extract rusprofile ID from a link like /id/2835629."""
    if not link:
        return ""
    m = re.search(r"/id/(\d+)", link)
    return m.group(1) if m else ""


def _parse_company_html(html: str) -> RusprofileCompany:
    """Parse rusprofile company page HTML (SSR, 2026 format).

    Extracts metadata from meta tags and page text, and financials
    from embedded finance-col blocks.
    """
    c = RusprofileCompany()

    # ── 1. Company name from meta/og tags ──────────────────────────
    og_title = re.search(r'<meta property="og:title" content="([^"]+)"', html)
    if og_title:
        c.short_name = og_title.group(1).replace("&quot;", '"').replace("&amp;", "&")

    # Full name from meta description
    desc_m = re.search(r'<meta name="description" content="([^"]+)"', html)
    if desc_m:
        desc = desc_m.group(1)
        full_m = re.search(
            r'(?:ОБЩЕСТВО С ОГРАНИЧЕННОЙ ОТВЕТСТВЕННОСТЬЮ|АКЦИОНЕРНОЕ ОБЩЕСТВО|ПУБЛИЧНОЕ АКЦИОНЕРНОЕ ОБЩЕСТВО|НЕПУБЛИЧНОЕ АКЦИОНЕРНОЕ ОБЩЕСТВО)\s+"([^"]+)"',
            desc,
        )
        if full_m:
            c.full_name = full_m.group(0)

    # ── 2. Registrar identifiers ───────────────────────────────────
    kw_m = re.search(r'<meta name="keywords" content="([^"]+)"', html)
    if kw_m:
        keywords = kw_m.group(1)
        if not c.ogrn:
            ogrn_m = re.search(r"ОГРН\s*(\d{13,15})", keywords)
            if ogrn_m:
                c.ogrn = ogrn_m.group(1)

    # Extract INN, KPP, director, address from page text
    text = re.sub(r"<[^>]+>", "\n", html)
    text = re.sub(r"&quot;", '"', text)
    text = re.sub(r"&amp;", "&", text)
    text = re.sub(r"\n\s*\n", "\n", text)
    lines = [l.strip() for l in text.split("\n") if l.strip()]

    # Also try to extract OGRN from company-info section
    ogrn_section_m = re.search(
        r'<dt class="company-info__title">ОГРН</dt>\s*<dd[^>]*>([^<]+)</dd>',
        html,
    )
    if ogrn_section_m:
        company_info_ogrn = re.sub(r"<[^>]+>", "", ogrn_section_m.group(1)).strip()
        if company_info_ogrn.isdigit() and len(company_info_ogrn) >= 13:
            if not c.ogrn:
                c.ogrn = company_info_ogrn

    # Extract INN from company-info section
    inn_section_m = re.search(
        r'<dt class="company-info__title">ИНН</dt>\s*<dd[^>]*>([^<]+)</dd>',
        html,
    )
    page_inn = ""
    if inn_section_m:
        page_inn = re.sub(r"<[^>]+>", "", inn_section_m.group(1)).strip()

    # If page shows a different INN in company-info than in meta tags,
    # the page is mixing two companies — skip financial data entirely
    finance_reliable = True
    if page_inn and c.inn and page_inn != c.inn:
        logger.debug(
            "rusprofile: page INN mismatch — meta=%s vs company-info=%s, "
            "financial data skipped (unreliable)",
            c.inn, page_inn,
        )
        finance_reliable = False

    for line in lines:
        # INN
        if not c.inn:
            m = re.search(r"ИНН\s*(\d{10,12})", line)
            if m:
                c.inn = m.group(1)
        # OGRN
        if not c.ogrn:
            m = re.search(r"ОГРН\s*(\d{13,15})", line)
            if m:
                c.ogrn = m.group(1)
        # KPP
        if not c.kpp:
            m = re.search(r"КПП\s*(\d{9})", line)
            if m:
                c.kpp = m.group(1)
        # Director
        if re.search(r"(?:директор|руководитель|генеральный\s+директор)", line, re.IGNORECASE):
            m = re.search(r"(?:директор|руководитель|генеральный\s+директор)\s*[-–—]\s*(.+)", line, re.IGNORECASE)
            if m:
                c.director = m.group(1).strip()
        # Legal address
        if ("Юридический адрес" in line or "Адрес" in line) and not c.legal_address:
            m = re.search(r"(?:адрес|Адрес)\s*(.+)", line)
            if m:
                addr = m.group(1).strip()
                if len(addr) > 10:
                    c.legal_address = addr
        # Registration date
        if "Дата регистрации" in line:
            m = re.search(r"(\d{1,2}\s+\w+\s+\d{4})\s*г\.?", line)
            if m:
                c.registration_date = m.group(1)
        # Status
        if "Статус" in line:
            if "действую" in line.lower():
                c.status = "Действующее"
            elif "ликвидир" in line.lower():
                c.status = "Ликвидировано"
        # OKVED
        if re.match(r"^\d{2}\.\d{2}\b", line) and not c.okved_main:
            c.okved_main = line.strip()

    # ── 3. Financial data ───────────────────────────────────────────
    if finance_reliable:
        _parse_finance_widget(html, c)

    # ── 4. Revenue trend from text (fallback) ──────────────────────
    _parse_revenue_trend(lines, c)

    return c


# ── Finance Parsing ───────────────────────────────────────────────────────


def _decode_year(raw_year: str) -> int:
    """Decode rusprofile masked year. Masked years are offset by 1818."""
    try:
        y = int(raw_year)
    except (ValueError, TypeError):
        return 0
    if y > 3000:
        y -= 1818
    elif 2400 < y < 3000:
        candidate = y - 1818
        if 2015 <= candidate <= 2030:
            y = candidate
    if y < 2015 or y > 2030:
        return 0
    return y


def _parse_finance_widget(html: str, c: RusprofileCompany) -> None:
    """Extract financial data from rusprofile page.

    Tries TWO formats (rusprofile changes HTML structure frequently):

    1. NEW format (2026-05+): <div class="finance-columns">
       - Year from "Бухгалтерская отчётность YYYY–YYYY"
       - Revenue: unmasked <span class="num"> in finance-col
       - Profit/Value: may be behind <span class="under_mask"> (login wall)

    2. OLD format (pre-2026-05): <table> after "Финансовая отчетность"
    """
    if _parse_finance_columns(html, c):
        return
    _parse_finance_table(html, c)


def _parse_finance_columns(html: str, c: RusprofileCompany) -> bool:
    """Parse finance-col format (2026-05+ rusprofile HTML structure)."""
    year = 0
    year_range_m = re.search(r'Бухгалтерская\s+отчётность\s+(\d{4})[–-](\d{4})', html)
    if year_range_m:
        year = _decode_year(year_range_m.group(2))
    if not year:
        ym = re.search(r'Основные показатели за\s+(\d{4})\s+год', html)
        if ym:
            year = _decode_year(ym.group(1))

    cols_raw = re.split(r'<div class="[^"]*finance-col[^"]*"', html)
    if len(cols_raw) < 2:
        return False

    found_any = False
    for col_html in cols_raw[1:]:
        tab_match = re.search(r'data-tab_name="tab_(\w+)"', col_html)
        if not tab_match:
            continue
        metric = tab_match.group(1)

        if '<span class="under_mask">' in col_html or 'data-quemask="true"' in col_html:
            logger.debug("rusprofile: skipping %s (under_mask detected)", metric)
            continue

        num_match = re.search(
            r'<span class="num">([\d\s,]+)</span>\s*'
            r'<span class="num-text">(?:&nbsp;|\s)*(млрд|млн|тыс|руб)',
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

        if unit == "млрд":
            amount *= 1_000_000_000
        elif unit == "млн":
            amount *= 1_000_000
        elif unit == "тыс":
            amount *= 1_000

        trend_str = ""
        arr_match = re.search(r'<span class="arr">(&[a-z]+;)</span>', col_html)
        pct_match = re.search(r'([+-]\d+)\s*%', col_html)
        if arr_match:
            arrow_html = arr_match.group(1)
            direction = "↑" if "uarr" in arrow_html else "↓"
            change = pct_match.group(1) if pct_match else ""
            trend_str = f"{direction}{change}%"

        if metric == "revenue":
            if amount <= 0:
                continue
            c.revenue[year] = int(amount)
            c.financial_year = max(c.financial_year, year)
            if trend_str:
                c.revenue_trend = trend_str
            found_any = True
        elif metric == "profit":
            c.profit[year] = int(amount)
            if trend_str:
                c.profit_trend = trend_str
        elif metric in ("value", "costs"):
            c.value[year] = int(amount)
            if trend_str:
                c.value_trend = trend_str

    if found_any:
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
            r'(млрд|млн|тыс)\.?\s*руб\.?'
            r'(?:\s*<img[^>]*arrow-(up|down)\.svg[^>]*>)?',
            row_html,
        )

        for metric_name, raw_num, unit, arrow_dir in cells:
            try:
                amount = float(raw_num.replace(" ", "").replace(",", "."))
            except ValueError:
                continue

            if unit == "млрд":
                amount *= 1_000_000_000
            elif unit == "млн":
                amount *= 1_000_000
            elif unit == "тыс":
                amount *= 1_000

            if metric_name == "Выручка":
                if amount <= 0:
                    continue
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
    """Extract historical revenue data from stripped text (fallback)."""
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
