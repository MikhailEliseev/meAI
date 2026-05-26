"""bo.nalog.gov.ru (ГИР БО) API client — official ФНС financial data."""

from .bfo_client import BfoNalogClient
from .models import FinancialStatement, OrganizationResult

__all__ = ["BfoNalogClient", "FinancialStatement", "OrganizationResult"]
