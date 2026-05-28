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

REQUEST_TIMEOUT = 8.0
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

    async def get_by_inn(
        self, inn: str, name: str = ""
    ) -> Optional[RusprofileCompany]:
        """Fetch company data by INN, optionally using name for better results.

        When name is provided, tries name-based search first (more reliable —
        avoids rusprofile's session-scoped ID issues with INN redirects).
        Falls back to INN search if name search fails.
        """
        return await self._fetch(inn=inn, name=name)

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
        self, inn: str = "", ogrn: str = "", name: str = ""
    ) -> Optional[RusprofileCompany]:
        """Fetch and parse company data from rusprofile.ru.

        Strategy:
        1. If name is provided, try name-based search first. Name searches
           produce pages WITHOUT a company-info section, which means the
           finance_reliable consistency check passes by default — giving us
           access to financial data that INN searches often miss (due to
           rusprofile's session-scoped ID issues).
        2. Fall back to INN/OGRN search if name search fails or returns
           wrong company.
        """
        identifier = inn or ogrn
        if not identifier and not name:
            return None

        client = await self._get_client()

        # ── Strategy 1: Name-based search (more reliable for financials) ─
        if name:
            company = await self._try_name_search(client, name, inn)
            if company is not None:
                return company

        # ── Strategy 2: INN/OGRN search with print page ────────────────
        if not identifier:
            return None

        search_url = RUSPROFILE_SEARCH.format(identifier)

        try:
            response = await client.get(search_url)
            response.raise_for_status()
        except httpx.HTTPError as e:
            logger.error("rusprofile fetch failed for %s: %s", identifier, e)
            return None

        html = response.text

        # Extract rusprofile ID from redirect URL
        rusprofile_id = _extract_rusprofile_id(str(response.url), html)
        if not rusprofile_id:
            logger.debug("rusprofile: could not extract ID for %s", identifier)
            return None

        # Request print page for stable HTML (same client = same session)
        print_url = f"https://www.rusprofile.ru/id/{rusprofile_id}?print=1"
        try:
            response = await client.get(print_url)
            response.raise_for_status()
            html = response.text
        except httpx.HTTPError as e:
            logger.debug("rusprofile print page failed, using search page: %s", e)

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

    async def _try_name_search(
        self, client: httpx.AsyncClient, name: str, expected_inn: str = ""
    ) -> Optional[RusprofileCompany]:
        """Try name-based search on rusprofile.

        Only works when rusprofile redirects directly to a company page
        (single exact match). For multi-result pages, returns None and
        lets the caller fall back to INN search.

        Uses print page (?print=1) for stable HTML — finance-col blocks
        are always present on print pages.
        """
        search_url = RUSPROFILE_SEARCH.format(name)
        try:
            response = await client.get(search_url)
            response.raise_for_status()
        except httpx.HTTPError as e:
            logger.debug("rusprofile name search failed for '%s': %s", name, e)
            return None

        final_url = str(response.url)

        # Only proceed if rusprofile redirected to a company page
        # (single exact match). Search results pages are unreliable —
        # the first result often points to a different company.
        if "/id/" not in final_url:
            logger.debug(
                "rusprofile name search: multi-result page for '%s', skipping",
                name,
            )
            return None

        rusprofile_id = _extract_rusprofile_id(final_url, "")
        if not rusprofile_id:
            return None

        # Request print page for this ID (same client = same session)
        print_url = f"https://www.rusprofile.ru/id/{rusprofile_id}?print=1"
        try:
            response = await client.get(print_url)
            response.raise_for_status()
        except httpx.HTTPError as e:
            logger.debug("rusprofile print page failed: %s", e)
            return None

        html = response.text
        company = _parse_company_html(html)
        company.rusprofile_id = rusprofile_id

        # Verify INN matches if we have one
        if expected_inn and company.inn and company.inn != expected_inn:
            logger.debug(
                "rusprofile name search: INN mismatch — expected %s, got %s (%s)",
                expected_inn, company.inn, company.short_name,
            )
            return None

        logger.debug(
            "rusprofile name search: success — %s (INN %s, revenue=%s)",
            company.short_name, company.inn,
            {y: v for y, v in company.revenue.items()},
        )
        return company


# ── HTML Parsers ──────────────────────────────────────────────────────────

def _extract_rusprofile_id(url: str, html: str) -> Optional[str]:
    """Extract rusprofile internal ID from redirect URL or page content.

    rusprofile (2026-05+) redirects INN/OGRN searches directly to the company
    page via 303. We extract the ID from the final URL after redirect.

    Falls back to parsing HTML for search result links if no redirect occurred.
    """
    # Primary: extract from URL (search redirects to /id/{ID})
    m = re.search(r"/id/(\d+)", url)
    if m:
        return m.group(1)

    # Fallback 1: canonical link in HTML
    m = re.search(r'<link\s[^>]*rel="canonical"[^>]*href="[^"]*/id/(\d+)"', html)
    if m:
        return m.group(1)

    # Fallback 2: first search result link (old list-element format, may be Vue-rendered)
    m = re.search(r'href="(/id/\d+)"', html)
    if m:
        return m.group(1).split("/")[-1]

    return None


def _extract_canonical(html: str) -> Optional[str]:
    """Extract canonical URL from rusprofile search results page."""
    match = re.search(r'<link\s[^>]*rel="canonical"[^>]*href="([^"]+)"', html)
    if match:
        return match.group(1)
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


def _parse_company_html(html: str) -> RusprofileCompany:
    """Parse rusprofile company page HTML (after search redirect).

    Extracts metadata from meta tags and page text, and financials
    from embedded finance-col blocks. Single HTML response — no
    separate print page needed.
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
        full_m = re.search(r'(?:ОБЩЕСТВО С ОГРАНИЧЕННОЙ ОТВЕТСТВЕННОСТЬЮ|АКЦИОНЕРНОЕ ОБЩЕСТВО|ПУБЛИЧНОЕ АКЦИОНЕРНОЕ ОБЩЕСТВО|НЕПУБЛИЧНОЕ АКЦИОНЕРНОЕ ОБЩЕСТВО)\s+"([^"]+)"', desc)
        if full_m:
            c.full_name = f'{full_m.group(0)}'

    # ── 2. Registrar identifiers ───────────────────────────────────
    # Extract OGRN from meta keywords (reliable — always next to the correct INN)
    kw_m = re.search(r'<meta name="keywords" content="([^"]+)"', html)
    if kw_m:
        keywords = kw_m.group(1)
        if not c.ogrn:
            ogrn_m = re.search(r"ОГРН\s*(\d{13,15})", keywords)
            if ogrn_m:
                c.ogrn = ogrn_m.group(1)
        if not c.okved_main:
            okpo_m = re.search(r"(\d{8,10})\s*ОКПО", keywords)
            if okpo_m:
                pass  # OKPO is not OKVED, skip

    # Extract INN, KPP, director, address from page text
    text = re.sub(r"<[^>]+>", "\n", html)
    text = re.sub(r"&quot;", '"', text)
    text = re.sub(r"&amp;", "&", text)
    text = re.sub(r"\n\s*\n", "\n", text)
    lines = [l.strip() for l in text.split("\n") if l.strip()]

    # Also try to extract OGRN from company-info section (more reliable than random text)
    company_info_ogrn = ""
    ogrn_section_m = re.search(
        r'<dt class="company-info__title">ОГРН</dt>\s*<dd[^>]*>([^<]+)</dd>',
        html,
    )
    if ogrn_section_m:
        company_info_ogrn = re.sub(r"<[^>]+>", "", ogrn_section_m.group(1)).strip()
        if company_info_ogrn.isdigit() and len(company_info_ogrn) >= 13:
            if not c.ogrn:
                c.ogrn = company_info_ogrn

    # Extract INN from company-info section for consistency check
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
    _parse_finance_widget(html, c)

    # ── 4. Revenue trend from text (fallback) ──────────────────────
    _parse_revenue_trend(lines, c)

    return c


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
    """Decode rusprofile masked year. Masked years are offset by 1818.

    Also handles years in the 2400-3000 range (new masking scheme
    that produces values below the old >3000 threshold).
    """
    try:
        y = int(raw_year)
    except (ValueError, TypeError):
        return 0
    if y > 3000:
        y -= 1818
    elif 2400 < y < 3000:
        # New masking scheme produces values like 2493 for 2020
        candidate = y - 1818
        if 2015 <= candidate <= 2030:
            y = candidate
    if y < 2015 or y > 2030:
        return 0
    return y


def _parse_finance_columns(html: str, c: RusprofileCompany) -> bool:
    """Parse finance-col format (2026-05+ rusprofile HTML structure).

    New structure uses individual <div class="finance-col ..."> elements
    (note: plural "finance-col" with extra CSS classes like "space-between").
    Each col has data-tab_name="tab_{revenue|profit|costs}" and contains
    <span class="num">VALUE</span> <span class="num-text">UNIT</span>.

    Year is extracted from "Бухгалтерская отчётность YYYY–YYYY" text,
    taking the last (most recent) year.
    """
    # Extract the most recent financial year from the accounting period range
    year = 0
    year_range_m = re.search(r'Бухгалтерская\s+отчётность\s+(\d{4})[–-](\d{4})', html)
    if year_range_m:
        year = _decode_year(year_range_m.group(2))
    if not year:
        # Fallback: "Основные показатели за XXXX год" (older format)
        ym = re.search(r'Основные показатели за\s+(\d{4})\s+год', html)
        if ym:
            year = _decode_year(ym.group(1))

    # Find finance-col elements — class may be "finance-col space-between" etc.
    cols_raw = re.split(r'<div class="[^"]*finance-col[^"]*"', html)
    if len(cols_raw) < 2:
        return False

    found_any = False
    for col_html in cols_raw[1:]:  # first element is everything before first finance-col
        # Detect metric type from data-tab_name
        tab_match = re.search(r'data-tab_name="tab_(\w+)"', col_html)
        if not tab_match:
            continue
        metric = tab_match.group(1)  # revenue, profit, costs/value

        # Check if data is behind login wall (two known formats)
        if '<span class="under_mask">' in col_html or 'data-quemask="true"' in col_html:
            logger.debug("rusprofile: skipping %s (under_mask detected)", metric)
            continue

        # Extract numeric value
        # Unit may have leading whitespace/&nbsp; — " руб.", "&nbsp;руб.", "млн&nbsp;руб."
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
            # Russian number format: "1 234,5" or "1234,5" → 1234.5
            amount = float(raw_num.replace(" ", "").replace(",", "."))
        except ValueError:
            continue

        if unit == "млрд":
            amount *= 1_000_000_000
        elif unit == "млн":
            amount *= 1_000_000
        elif unit == "тыс":
            amount *= 1_000

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
            if amount <= 0:
                continue  # skip zero/missing revenue
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
