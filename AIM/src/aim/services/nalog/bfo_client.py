"""BfoNalogClient — official ФНС financial data from bo.nalog.gov.ru (ГИР БО).

Free, public, no authentication required. Provides:
- Organization search by INN or name
- Full P&L (форма 0710002) with revenue, net profit, trends
- Balance sheet data
- Multi-year history

Values are in thousands of rubles (тыс. руб.) as per Russian accounting standards.
"""

import logging
import re
import time
from typing import Optional

import httpx

from .models import FinancialStatement, OrganizationResult

logger = logging.getLogger(__name__)

BASE_URL = "https://bo.nalog.gov.ru"
USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/148.0.0.0 Safari/537.36"
)

_HTML_TAG = re.compile(r"<[^>]+>")


def _strip_html(text: str) -> str:
    return _HTML_TAG.sub("", text)


class BfoNalogClient:
    """HTTP client for bo.nalog.gov.ru public API.

    Rate-limited (max 5 req/s) to be respectful of ФНС infrastructure.
    Results cached for 1 hour (financial data doesn't change intra-day).
    """

    def __init__(self, timeout: float = 10.0, cache_ttl: int = 3600) -> None:
        self._client = httpx.Client(
            timeout=httpx.Timeout(timeout),
            headers={
                "User-Agent": USER_AGENT,
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                "Accept-Language": "ru-RU,ru;q=0.9,en;q=0.5",
            },
        )
        self._cache: dict[str, tuple[float, object]] = {}
        self._cache_ttl = cache_ttl

        # Simple token bucket: 5 req/s
        self._tokens = 5.0
        self._max_tokens = 5.0
        self._refill_rate = 5.0  # tokens/sec
        self._last_refill = time.monotonic()

    def close(self) -> None:
        self._client.close()

    # ── Cache ────────────────────────────────────────────────────

    def _cache_get(self, key: str) -> Optional[object]:
        entry = self._cache.get(key)
        if entry is None:
            return None
        ts, value = entry
        if time.monotonic() - ts > self._cache_ttl:
            del self._cache[key]
            return None
        return value

    def _cache_set(self, key: str, value: object) -> None:
        self._cache[key] = (time.monotonic(), value)

    # ── Rate limiting ────────────────────────────────────────────

    def _acquire_token(self) -> None:
        now = time.monotonic()
        elapsed = now - self._last_refill
        self._tokens = min(self._max_tokens, self._tokens + elapsed * self._refill_rate)
        self._last_refill = now

        if self._tokens < 1.0:
            wait = (1.0 - self._tokens) / self._refill_rate
            time.sleep(wait)
            self._tokens = 0.0
        else:
            self._tokens -= 1.0

    # ── HTTP helpers ─────────────────────────────────────────────

    def _get(self, path: str) -> dict:
        self._acquire_token()
        resp = self._client.get(f"{BASE_URL}{path}")
        resp.raise_for_status()
        return resp.json()

    def _get_cached(self, cache_key: str, path: str) -> dict:
        cached = self._cache_get(cache_key)
        if cached is not None:
            logger.debug("nalog_cache_hit: %s", cache_key)
            return cached
        logger.debug("nalog_api_call: %s", path)
        data = self._get(path)
        self._cache_set(cache_key, data)
        return data

    # ── Public API ───────────────────────────────────────────────

    def search(self, query: str) -> list[OrganizationResult]:
        """Search organizations by INN or name.

        Returns list of OrganizationResult with basic info + latest BFO period/revenue.
        """
        cache_key = f"search:{query}"
        data = self._get_cached(cache_key, f"/advanced-search/organizations/search?query={query}&page=0&size=20")

        results: list[OrganizationResult] = []
        for item in data.get("content", []):
            bfo = item.get("bfo") or {}
            results.append(OrganizationResult(
                id=item["id"],
                inn=_strip_html(item.get("inn", "")),
                short_name=_strip_html(item.get("shortName", "")),
                ogrn=item.get("ogrn", ""),
                address=_build_address(item),
                okved2=item.get("okved2", ""),
                status=item.get("statusCode", ""),
                latest_period=bfo.get("period"),
                latest_revenue=bfo.get("gainSum"),
            ))

        return results

    def get_financials(self, org_id: int) -> list[FinancialStatement]:
        """Get full P&L statements for an organization (all available years).

        Returns list sorted by period descending (newest first).
        """
        cache_key = f"bfo:{org_id}"
        data = self._get_cached(cache_key, f"/nbo/organizations/{org_id}/bfo/")

        statements: list[FinancialStatement] = []
        for bfo in data:
            period = bfo.get("period", "")
            if not period:
                continue

            gain = bfo.get("gainSum")
            stmt = FinancialStatement(period=period, revenue=gain)

            # Extract detailed P&L from the first correction (type=12 = annual)
            for tc in bfo.get("typeCorrections", []):
                if tc.get("type") != 12:
                    continue
                fr = tc.get("correction", {}).get("financialResult", {})
                if fr:
                    stmt.revenue = fr.get("current2110") or stmt.revenue
                    stmt.cost_of_sales = fr.get("current2120")
                    stmt.gross_profit = fr.get("current2100")
                    stmt.selling_expenses = fr.get("current2210")
                    stmt.admin_expenses = fr.get("current2220")
                    stmt.operating_profit = fr.get("current2200")
                    stmt.pre_tax_profit = fr.get("current2300")
                    stmt.net_profit = fr.get("current2400")
                    stmt.prev_revenue = fr.get("previous2110")
                    stmt.prev_net_profit = fr.get("previous2400")
                break

            statements.append(stmt)

        statements.sort(key=lambda s: s.period, reverse=True)
        return statements

    def get_latest_financials(self, org_id: int) -> Optional[FinancialStatement]:
        """Get the most recent P&L statement for an organization."""
        statements = self.get_financials(org_id)
        return statements[0] if statements else None

    def get_organization(self, org_id: int) -> dict:
        """Get full organization details."""
        cache_key = f"org:{org_id}"
        return self._get_cached(cache_key, f"/nbo/organizations/{org_id}")


# ── Helpers ──────────────────────────────────────────────────────

def _build_address(item: dict) -> str:
    """Build a human-readable address from organization search result."""
    parts = [
        item.get("index"),
        item.get("region"),
        item.get("district"),
        item.get("city"),
        item.get("settlement"),
        item.get("street"),
        item.get("house"),
    ]
    parts = [p for p in parts if p]
    if item.get("building"):
        parts.append(f"стр.{item['building']}")
    if item.get("office"):
        parts.append(f"оф.{item['office']}")
    return ", ".join(parts)
