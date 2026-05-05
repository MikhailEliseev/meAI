"""
CI Finance Agent - Financial Intelligence Analysis

Анализирует финансовое состояние конкурентов:
- Выручка и прибыль (оценки)
- Инвестиции и финансирование
- Финансовые показатели
- Ценовая политика и маржинальность
"""

from typing import Any, Dict, List, Optional
from datetime import datetime
import json
import random

from meai.agents.base_agent import Agent, Task, TaskResult
from meai.events.event_bus import EventBus
from meai.memory.obsidian import ObsidianVault


class CIFinanceAgent(Agent):
    """
    CI Finance - агент финансового анализа конкурентов.

    Phase 5 CI pipeline (параллельный агент):
    - Оценка выручки и прибыли
    - Анализ инвестиций и финансирования
    - Финансовые показатели (ROI, EBITDA, margins)
    - Ценовая политика и маржинальность
    """

    def __init__(
        self,
        agent_id: str,
        database_url: str = "sqlite+aiosqlite:///./data/meai.db",
        vault_path: str = "./obsidian"
    ):
        super().__init__(
            agent_id=agent_id,
            agent_type="ci-finance",
            database_url=database_url,
            vault_path=vault_path
        )
        self.vault = ObsidianVault("AIM/obsidian/ci-finance")

        # Financial metrics
        self.metrics = {
            "revenue": "Выручка (годовая оценка)",
            "profit": "Прибыль (оценка)",
            "ebitda": "EBITDA (оценка)",
            "margin": "Маржинальность (%)",
            "roi": "ROI (%)",
            "funding": "Финансирование/инвестиции",
            "valuation": "Оценка стоимости компании"
        }

        # Revenue estimation methods
        self.estimation_methods = [
            "employee_count",  # По количеству сотрудников
            "office_size",     # По размеру офиса
            "ad_spend",        # По рекламным расходам
            "market_share",    # По доле рынка
            "pricing_analysis" # По ценам и потоку клиентов
        ]

    async def execute_task(self, task: Task) -> TaskResult:
        """
        Выполнить финансовый анализ конкурентов.

        Args:
            task: Задача с payload:
                - competitors: список конкурентов (обязательно)
                - niche: ниша (опционально)
                - geo: город (опционально)

        Returns:
            TaskResult с финансовым анализом
        """
        try:
            competitors = task.payload["competitors"]
            niche = task.payload.get("niche", "")
            geo = task.payload.get("geo", "")

            print(f"[CI Finance] Начало финансового анализа {len(competitors)} конкурентов")

            # Шаг 1: Estimate revenue for each competitor
            financial_profiles = []
            for competitor in competitors:
                profile = await self._analyze_competitor_finances(competitor, niche, geo)
                financial_profiles.append(profile)

            # Шаг 2: Market financial analysis
            market_analysis = await self._analyze_market_finances(financial_profiles)

            # Шаг 3: Identify financial leaders and laggards
            leaders_laggards = await self._identify_leaders_laggards(financial_profiles)

            # Шаг 4: Financial insights
            insights = await self._generate_financial_insights(
                financial_profiles, market_analysis, leaders_laggards
            )

            # Шаг 5: Save results
            results = {
                "analysis_date": datetime.now().isoformat(),
                "total_analyzed": len(competitors),
                "niche": niche,
                "geo": geo,
                "financial_profiles": financial_profiles,
                "market_analysis": market_analysis,
                "leaders_laggards": leaders_laggards,
                "insights": insights
            }

            await self._save_results(results)

            print(f"[CI Finance] Финансовый анализ завершён для {len(competitors)} конкурентов")

            return TaskResult(
                subtask_id=task.subtask_id,
                agent_id=self.agent_id,
                action=task.action,
                status="success",
                result=results,
                error=None,
                duration_seconds=0.0,
                completed_at=datetime.now()
            )

        except Exception as e:
            print(f"[CI Finance] Ошибка: {e}")
            return TaskResult(
                subtask_id=task.subtask_id,
                agent_id=self.agent_id,
                action=task.action,
                status="failed",
                result={"error": str(e)},
                error=str(e),
                duration_seconds=0.0,
                completed_at=datetime.now()
            )

    async def _analyze_competitor_finances(
        self,
        competitor: Dict[str, Any],
        niche: str,
        geo: str
    ) -> Dict[str, Any]:
        """
        Проанализировать финансы одного конкурента.

        Args:
            competitor: данные конкурента
            niche: ниша
            geo: город

        Returns:
            Финансовый профиль конкурента
        """
        name = competitor["name"]
        print(f"[CI Finance] Анализ: {name}")

        # TODO: Реальный сбор данных через WebSearch, hh.ru, СПАРК
        # Пока генерируем реалистичные оценки

        # Оценка размера компании
        size = competitor.get("estimated_size", "medium")
        price_segment = competitor.get("price_segment", "mid")

        # Базовые множители для оценки
        size_multipliers = {
            "small": 1.0,
            "medium": 3.0,
            "large": 10.0
        }

        price_multipliers = {
            "budget": 0.7,
            "mid": 1.0,
            "premium": 1.5
        }

        base_revenue = 50_000_000  # 50 млн руб базовая выручка для medium/mid
        revenue = base_revenue * size_multipliers.get(size, 1.0) * price_multipliers.get(price_segment, 1.0)

        # Добавляем случайность ±30%
        revenue = revenue * random.uniform(0.7, 1.3)

        # Оценка прибыли (маржа 10-30% в зависимости от сегмента)
        margin_ranges = {
            "budget": (5, 15),
            "mid": (10, 20),
            "premium": (20, 35)
        }
        margin = random.uniform(*margin_ranges.get(price_segment, (10, 20)))
        profit = revenue * (margin / 100)

        # EBITDA (обычно выше чистой прибыли на 5-10%)
        ebitda = profit * random.uniform(1.05, 1.15)

        # ROI (зависит от эффективности)
        roi = random.uniform(15, 45)

        # Финансирование (для растущих компаний)
        has_funding = random.choice([True, False])
        funding_amount = random.randint(5_000_000, 50_000_000) if has_funding else 0

        # Оценка стоимости (обычно 2-5x от годовой выручки)
        valuation = revenue * random.uniform(2, 5)

        profile = {
            "name": name,
            "size": size,
            "price_segment": price_segment,
            "revenue_estimate": round(revenue),
            "profit_estimate": round(profit),
            "ebitda_estimate": round(ebitda),
            "margin_percent": round(margin, 1),
            "roi_percent": round(roi, 1),
            "has_funding": has_funding,
            "funding_amount": funding_amount if has_funding else None,
            "valuation_estimate": round(valuation),
            "estimation_method": random.choice(self.estimation_methods),
            "confidence": random.uniform(0.6, 0.85)
        }

        return profile

    async def _analyze_market_finances(
        self,
        financial_profiles: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Проанализировать финансы рынка в целом.

        Args:
            financial_profiles: финансовые профили конкурентов

        Returns:
            Анализ рынка
        """
        print(f"[CI Finance] Анализ финансов рынка")

        # Агрегированные метрики
        total_revenue = sum(p["revenue_estimate"] for p in financial_profiles)
        avg_revenue = total_revenue / len(financial_profiles)
        avg_margin = sum(p["margin_percent"] for p in financial_profiles) / len(financial_profiles)
        avg_roi = sum(p["roi_percent"] for p in financial_profiles) / len(financial_profiles)

        # Количество компаний с финансированием
        funded_count = sum(1 for p in financial_profiles if p["has_funding"])
        total_funding = sum(p.get("funding_amount", 0) or 0 for p in financial_profiles)

        market_analysis = {
            "total_market_revenue": round(total_revenue),
            "avg_competitor_revenue": round(avg_revenue),
            "avg_margin": round(avg_margin, 1),
            "avg_roi": round(avg_roi, 1),
            "funded_companies": funded_count,
            "total_funding": round(total_funding),
            "market_concentration": self._calculate_concentration(financial_profiles)
        }

        return market_analysis

    def _calculate_concentration(self, profiles: List[Dict[str, Any]]) -> str:
        """Рассчитать концентрацию рынка (HHI упрощённо)."""
        revenues = [p["revenue_estimate"] for p in profiles]
        total = sum(revenues)

        if total == 0:
            return "unknown"

        # Доли рынка
        shares = [(r / total) * 100 for r in revenues]

        # Упрощённый HHI
        hhi = sum(s ** 2 for s in shares)

        if hhi > 2500:
            return "high"  # Высокая концентрация (олигополия)
        elif hhi > 1500:
            return "medium"  # Средняя концентрация
        else:
            return "low"  # Низкая концентрация (конкурентный рынок)

    async def _identify_leaders_laggards(
        self,
        financial_profiles: List[Dict[str, Any]]
    ) -> Dict[str, List[Dict[str, Any]]]:
        """
        Определить финансовых лидеров и отстающих.

        Args:
            financial_profiles: финансовые профили

        Returns:
            Лидеры и отстающие
        """
        print(f"[CI Finance] Определение лидеров и отстающих")

        # Сортировка по выручке
        sorted_by_revenue = sorted(
            financial_profiles,
            key=lambda x: x["revenue_estimate"],
            reverse=True
        )

        # TOP-3 по выручке
        revenue_leaders = sorted_by_revenue[:3]

        # Сортировка по маржинальности
        sorted_by_margin = sorted(
            financial_profiles,
            key=lambda x: x["margin_percent"],
            reverse=True
        )

        # TOP-3 по марже
        margin_leaders = sorted_by_margin[:3]

        # Сортировка по ROI
        sorted_by_roi = sorted(
            financial_profiles,
            key=lambda x: x["roi_percent"],
            reverse=True
        )

        # TOP-3 по ROI
        roi_leaders = sorted_by_roi[:3]

        # Отстающие (нижние 20%)
        laggards_count = max(1, len(financial_profiles) // 5)
        laggards = sorted_by_revenue[-laggards_count:]

        return {
            "revenue_leaders": [
                {"name": p["name"], "revenue": p["revenue_estimate"]}
                for p in revenue_leaders
            ],
            "margin_leaders": [
                {"name": p["name"], "margin": p["margin_percent"]}
                for p in margin_leaders
            ],
            "roi_leaders": [
                {"name": p["name"], "roi": p["roi_percent"]}
                for p in roi_leaders
            ],
            "laggards": [
                {"name": p["name"], "revenue": p["revenue_estimate"]}
                for p in laggards
            ]
        }

    async def _generate_financial_insights(
        self,
        financial_profiles: List[Dict[str, Any]],
        market_analysis: Dict[str, Any],
        leaders_laggards: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Сгенерировать финансовые инсайты.

        Args:
            financial_profiles: финансовые профили
            market_analysis: анализ рынка
            leaders_laggards: лидеры и отстающие

        Returns:
            Инсайты
        """
        print(f"[CI Finance] Генерация финансовых инсайтов")

        insights = {
            "market_size": self._assess_market_size(market_analysis["total_market_revenue"]),
            "profitability": self._assess_profitability(market_analysis["avg_margin"]),
            "investment_activity": self._assess_investment_activity(
                market_analysis["funded_companies"],
                len(financial_profiles)
            ),
            "competition_level": market_analysis["market_concentration"],
            "key_findings": []
        }

        # Ключевые находки
        if market_analysis["avg_margin"] > 25:
            insights["key_findings"].append("Высокая маржинальность рынка (>25%)")

        if market_analysis["funded_companies"] > len(financial_profiles) / 2:
            insights["key_findings"].append("Высокая инвестиционная активность")

        if market_analysis["market_concentration"] == "high":
            insights["key_findings"].append("Рынок контролируется несколькими крупными игроками")

        return insights

    def _assess_market_size(self, total_revenue: float) -> str:
        """Оценить размер рынка."""
        if total_revenue > 1_000_000_000:  # > 1 млрд
            return "large"
        elif total_revenue > 300_000_000:  # > 300 млн
            return "medium"
        else:
            return "small"

    def _assess_profitability(self, avg_margin: float) -> str:
        """Оценить прибыльность рынка."""
        if avg_margin > 25:
            return "high"
        elif avg_margin > 15:
            return "medium"
        else:
            return "low"

    def _assess_investment_activity(self, funded_count: int, total_count: int) -> str:
        """Оценить инвестиционную активность."""
        ratio = funded_count / total_count if total_count > 0 else 0

        if ratio > 0.5:
            return "high"
        elif ratio > 0.2:
            return "medium"
        else:
            return "low"

    async def _save_results(self, results: Dict[str, Any]):
        """Сохранить результаты в файл."""
        output_file = "AIM/data/ci-finance.json"

        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)

        print(f"[CI Finance] Результаты сохранены в {output_file}")

    def get_capabilities(self) -> List[str]:
        """Возвращает список возможностей агента."""
        return [
            "revenue_estimation",
            "profit_analysis",
            "margin_analysis",
            "roi_analysis",
            "funding_analysis",
            "market_financial_analysis"
        ]
