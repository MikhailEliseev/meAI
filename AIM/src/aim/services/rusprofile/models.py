"""DaData + SPARK company profile models."""

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class CompanyProfile:
    """Company profile from DaData / SPARK / rusprofile.

    Primary key: inn (taxpayer identification number).
    Supports multi-entity clinics: inns list collects all legal entities
    found on a clinic website (different INNs under different licenses).
    """

    inn: str
    ogrn: Optional[str] = None
    legal_name: str = ""
    brand_name: Optional[str] = None

    # Multi-entity support: some clinics operate under multiple legal entities
    # with different INNs (e.g. two licenses under two ООО).
    # inns = ALL valid INNs found on the website; inn = primary (best-scoring).
    inns: list[str] = field(default_factory=list)
    licenses: list[dict] = field(default_factory=list)
    is_multi_entity: bool = False

    # Financials (annual, RUB)
    revenue_year: Optional[int] = None
    profit_year: Optional[int] = None
    revenue_trend: Optional[str] = None  # "growing" | "stable" | "declining"
    financial_year: Optional[int] = None
    revenue_source: str = "none"  # "tax_filed" | "estimated" | "none"

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

    # Digital presence
    website: Optional[str] = None
    social_links: dict[str, str] = field(default_factory=dict)

    # Services extracted from competitor's website (populated after scraping)
    scraped_services: list[str] = field(default_factory=list)

    # Multi-year revenue history from ФНС (for trend analysis)
    revenue_history: list[dict] = field(default_factory=list)

    # Consumer signals (from Yandex Maps, 2GIS, etc.)
    rating: Optional[float] = None
    reviews_count: Optional[int] = None

    # What specialization query found this candidate (e.g. "косметология", "стоматология")
    source_specialization: str = ""

    # Source metadata
    data_source: str = "dadata"
    confidence: float = 0.7
    last_updated: Optional[str] = None

    @property
    def revenue_rub(self) -> Optional[int]:
        return self.revenue_year

    def has_real_financials(self) -> bool:
        return self.revenue_source == "tax_filed" and self.revenue_year is not None


@dataclass
class CompetitorMatch:
    """A single competitor matched to the client's profile."""

    profile: CompanyProfile
    website: Optional[str] = None
    social_links: dict[str, str] = field(default_factory=dict)
    services: list[str] = field(default_factory=list)

    # Scoring components (0.0 – 1.0)
    revenue_match: float = 0.0
    location_score: float = 0.0
    service_overlap: float = 0.0
    specialization_purity: float = 0.0
    popularity_score: float = 0.0
    visibility_score: float = 0.0
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
