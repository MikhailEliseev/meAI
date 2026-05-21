"""DaData + SPARK company search and competitor discovery.

DaData (dadata.ru) — official REST API for Russian company search.
SPARK-Interfax — optional premium fallback with richer financials.
"""

from .client import DaDataClient, get_dadata_client
from .models import ClientProfile, CompanyProfile, CompetitorMatch

__all__ = [
    "DaDataClient",
    "get_dadata_client",
    "CompanyProfile",
    "CompetitorMatch",
    "ClientProfile",
]
