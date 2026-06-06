"""Company Profile Database Model

Cached prescan results for repeat lookups.
Composite key (url, inn) ensures one profile per company.
JSON profile_data stores all staged prescan results.
"""

from datetime import datetime, timezone

from sqlalchemy import JSON, DateTime, Index, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from src.aim.storage.models import Base


class CompanyProfileModel(Base):
    """Cached company profile from prescan pipeline.

    profile_data stores structured results from all prescan stages:
    {
        "stage_1": {"revenue": ..., "profit": ..., "years_on_market": ...},
        "stage_2": {"licenses": [...], "seo_score": ..., "reviews": [...]},
        "stage_3": {"competitors_nearby": ..., "revenue_trend": ...}
    }
    """

    __tablename__ = "company_profiles"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    url: Mapped[str] = mapped_column(String(2048), nullable=False)
    inn: Mapped[str] = mapped_column(String(12), nullable=False, default="")
    profile_data: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    __table_args__ = (
        Index("idx_url_inn", "url", "inn", unique=True),
        Index("idx_created_at", "created_at"),
    )
