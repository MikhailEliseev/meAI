"""Models for bo.nalog.gov.ru (ГИР БО) financial data."""

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class OrganizationResult:
    """Organization from bo.nalog.gov.ru search results."""

    id: int
    inn: str
    short_name: str
    ogrn: str = ""
    address: str = ""
    okved2: str = ""
    status: str = ""
    latest_period: Optional[str] = None
    latest_revenue: Optional[int] = None


@dataclass
class FinancialStatement:
    """P&L data extracted from bo.nalog.gov.ru BFO (форма 0710002).

    Values are in thousands of rubles (тыс. руб.), following Russian
    accounting standards. Multiply by 1000 to get actual RUB.
    """

    period: str  # "2025"
    revenue: Optional[int] = None  # стр.2110
    cost_of_sales: Optional[int] = None  # стр.2120
    gross_profit: Optional[int] = None  # стр.2100
    selling_expenses: Optional[int] = None  # стр.2210
    admin_expenses: Optional[int] = None  # стр.2220
    operating_profit: Optional[int] = None  # стр.2200
    pre_tax_profit: Optional[int] = None  # стр.2300
    net_profit: Optional[int] = None  # стр.2400
    prev_revenue: Optional[int] = None  # previous year стр.2110
    prev_net_profit: Optional[int] = None  # previous year стр.2400

    @property
    def revenue_rub(self) -> Optional[int]:
        """Revenue in actual RUB (×1000 from accounting units)."""
        return self.revenue * 1000 if self.revenue is not None else None

    @property
    def net_profit_rub(self) -> Optional[int]:
        """Net profit in actual RUB."""
        return self.net_profit * 1000 if self.net_profit is not None else None

    @property
    def revenue_trend(self) -> str:
        """Revenue trend: 'growing', 'stable', 'declining', or ''."""
        if self.revenue and self.prev_revenue:
            change_pct = (self.revenue - self.prev_revenue) / self.prev_revenue
            if change_pct > 0.05:
                return "growing"
            elif change_pct < -0.05:
                return "declining"
            else:
                return "stable"
        return ""
