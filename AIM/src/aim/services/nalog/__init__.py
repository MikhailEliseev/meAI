"""bo.nalog.gov.ru (ГИР БО) API client — official ФНС financial data."""

from .bfo_client import BfoNalogClient
from .models import FinancialStatement, OrganizationResult

__all__ = ["BfoNalogClient", "FinancialStatement", "OrganizationResult", "get_nalog_client"]

# Singleton instance — survives across requests so the in-memory cache
# (1 hour TTL) can serve repeated queries without hitting ФНС again.
_nalog_client: BfoNalogClient | None = None


def get_nalog_client() -> BfoNalogClient:
    """Get the shared singleton BfoNalogClient.

    The client has an in-memory cache (TTL 3600s) for search and financials.
    Using a singleton ensures repeated queries for the same clinic hit the
    cache instead of re-fetching from ФНС. This makes repeat requests ~5x faster.
    """
    global _nalog_client
    if _nalog_client is None:
        _nalog_client = BfoNalogClient()
    return _nalog_client

