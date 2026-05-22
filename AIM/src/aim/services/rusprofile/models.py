"""DaData + SPARK company profile models."""

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class CompanyProfile:
    """Company profile from DaData / SPARK / rusprofile.

    Primary key: inn (taxpayer identification number).
    """

    inn: str
    ogrn: Optional[str] = None
    legal_name: str = ""
    brand_name: Optional[str] = None

    # Financials (annual, RUB)
    revenue_year: Optional[int] = None
    profit_year: Optional[int] = None
    revenue_trend: Optional[str] = None  # "growing" | "stable" | "declining"
    financial_year: Optional[int] = None

    # Operations
    employee_count: Optional[int] = None
    registration_date: Optional[str] = None
    okved_main: Optional[str] = None
    okved_secondary: list[str] = field(default_factory=list)

    # Location
    legal_address: Optional[str] = None
    actual_addresses: list[str] = field(default_factory=list)
    geo_lat: Optional[float] = None
    geo_lon: Optional[float] = None

    # Source metadata
    data_source: str = "dadata"
    confidence: float = 0.7
    last_updated: Optional[str] = None

    @property
    def revenue_rub(self) -> Optional[int]:
        return self.revenue_year

    def has_real_financials(self) -> bool:
        return self.revenue_year is not None and self.financial_year is not None


@dataclass
class CompetitorMatch:
    """A single competitor matched to the client's profile."""

    profile: CompanyProfile
    website: Optional[str] = None
    services: list[str] = field(default_factory=list)

    # Scoring components (0.0 – 1.0)
    revenue_match: float = 0.0
    location_score: float = 0.0
    service_overlap: float = 0.0
    data_quality: float = 0.7
    total_score: float = 0.0

    match_reason: str = ""


@dataclass
class ClientProfile:
    """Extracted profile of the client's own clinic."""

    url: str
    specialization: str = ""  # e.g. "стоматология", "косметология"
    city: str = ""
    services: list[str] = field(default_factory=list)
    estimated_revenue: Optional[int] = None
    company_name: Optional[str] = None
    inn: Optional[str] = None
    city_lat: Optional[float] = None
    city_lon: Optional[float] = None
