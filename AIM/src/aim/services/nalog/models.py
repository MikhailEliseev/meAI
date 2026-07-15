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
    registration_date: Optional[str] = None  # Дата регистрации (ISO)
    employee_count: Optional[int] = None  # СЧЛ — среднесписочная численность


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


def compute_revenue_dynamics(statements: list["FinancialStatement"]) -> dict:
    """Вычисляет динамику выручки за несколько лет из списка отчётов ФНС.

    Args:
        statements: Список FinancialStatement, отсортированный от новых к старым.

    Returns:
        {
            "change_3yr_pct": +79.2 (или None),
            "history": [{"year": "2025", "revenue_rub": 4300000000}, ...],
        }
    """
    history = []
    for s in statements[:4]:  # максимум 4 года
        if s.revenue_rub:
            history.append({"year": s.period, "revenue_rub": s.revenue_rub})

    change_3yr = None
    if len(history) >= 3:
        latest = history[0]["revenue_rub"]
        oldest = history[-1]["revenue_rub"]
        if oldest and oldest > 0:
            change_3yr = round((latest - oldest) / oldest * 100, 1)

    return {"change_3yr_pct": change_3yr, "history": history}
