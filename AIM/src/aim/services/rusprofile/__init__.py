"""DaData + SPARK + Rusprofile company search and competitor discovery.

DaData (dadata.ru) — official REST API for Russian company search.
SPARK-Interfax — optional premium fallback with richer financials.
Rusprofile (rusprofile.ru) — public financial data scraping by INN/OGRN.
"""

from .client import DaDataClient, get_dadata_client
from .models import ClientProfile, CompanyProfile, CompetitorMatch
from .parser import RusprofileClient, RusprofileCompany, get_rusprofile_client

__all__ = [
    "DaDataClient",
    "get_dadata_client",
    "CompanyProfile",
    "CompetitorMatch",
    "ClientProfile",
    "RusprofileClient",
    "RusprofileCompany",
    "get_rusprofile_client",
]
