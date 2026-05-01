"""SQLAlchemy models"""

from datetime import datetime
from sqlalchemy import JSON, Float, String, DateTime
from sqlalchemy.orm import Mapped, mapped_column

from .database import Base


class Metric(Base):
    """Metric model"""

    __tablename__ = "metrics"

    id: Mapped[int] = mapped_column(primary_key=True)
    metric_name: Mapped[str] = mapped_column(String, index=True)
    metric_type: Mapped[str] = mapped_column(String)  # counter, gauge, histogram
    value: Mapped[float] = mapped_column(Float)
    labels: Mapped[dict] = mapped_column(JSON, default=dict)
    timestamp: Mapped[datetime] = mapped_column(DateTime, index=True)
