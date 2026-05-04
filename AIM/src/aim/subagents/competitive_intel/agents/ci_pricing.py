"""
CI Pricing Agent - Pricing Strategy Analysis

Анализирует ценовую стратегию конкурентов:
- Прайс-листы и цены на услуги
- Ценовые сегменты (budget/mid/premium)
- Акции и скидки
- Ценовое позиционирование
- Прозрачность цен
"""

from typing import Any, Dict, List
from datetime import datetime
import json
import random

from meai.agents.base_agent import Agent, Task, TaskResult
from meai.memory.obsidian import ObsidianVault


class CIPricingAgent(Agent):
    """CI Pricing - агент анализа ценовой стратегии конкурентов."""

    def __init__(
        self,
        agent_id: str,
        database_url: str = "sqlite+aiosqlite:///./data/meai.db",
        vault_path: str = "./obsidian"
    ):
        super().__init__(
            agent_id=agent_id,
            agent_type="ci-pricing",
            database_url=database_url,
            vault_path=vault_path
        )
        self.vault = ObsidianVault("AIM/obsidian/ci-pricing")

        # Price segments
        self.price_segments = {
            "budget": "Бюджетный сегмент",
            "mid": "Средний сегмент",
            "premium": "Премиум сегмент",
            "luxury": "Люкс сегмент"
        }

        # Pricing strategies
        self.pricing_strategies = [
            "penetration",  # Низкие цены для захвата рынка
            "skimming",     # Высокие цены для премиум позиционирования
            "competitive",  # Цены на уровне конкурентов
            "value_based",  # Цены на основе ценности
            "dynamic"       # Динамическое ценообразование
        ]

    async def execute_task(self, task: Task) -> TaskResult:
        """
        Выполнить анализ ценовой стратегии конкурентов.

        Args:
            task: Задача с payload:
                - competitors: список конкурентов (обязательно)
                - niche: ниша (опционально)
                - services: список услуг для анализа (опционально)

        Returns:
            TaskResult с анализом цен
        """
        try:
            competitors = task.payload["competitors"]
            niche = task.payload.get("niche", "")
            services = task.payload.get("services", [])

            print(f"[CI Pricing] Начало анализа цен {len(competitors)} конкурентов")

            # Шаг 1: Collect pricing for each competitor
            pricing_profiles = []
            for competitor in competitors:
                profile = await self._analyze_competitor_pricing(competitor, niche, services)
                pricing_profiles.append(profile)

            # Шаг 2: Market pricing analysis
            market_analysis = await self._analyze_market_pricing(pricing_profiles)

            # Шаг 3: Identify pricing leaders
            pricing_leaders = await self._identify_pricing_leaders(pricing_profiles)

            # Шаг 4: Price positioning map
            positioning_map = await self._create_positioning_map(pricing_profiles)

            # Шаг 5: Pricing insights
            insights = await self._generate_pricing_insights(
                pricing_profiles, market_analysis, pricing_leaders, positioning_map
            )

            # Шаг 6: Save results
            results = {
                "analysis_date": datetime.now().isoformat(),
                "total_analyzed": len(competitors),
                "niche": niche,
                "pricing_profiles": pricing_profiles,
                "market_analysis": market_analysis,
                "pricing_leaders": pricing_leaders,
                "positioning_map": positioning_map,
                "insights": insights
            }

            await self._save_results(results)

            print(f"[CI Pricing] Анализ цен завершён для {len(competitors)} конкурентов")

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
            print(f"[CI Pricing] Ошибка: {e}")
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

    async def _analyze_competitor_pricing(
        self,
        competitor: Dict[str, Any],
        niche: str,
        services: List[str]
    ) -> Dict[str, Any]:
        """
        Проанализировать цены одного конкурента.

        Args:
            competitor: данные конкурента
            niche: ниша
            services: список услуг

        Returns:
            Ценовой профиль конкурента
        """
        name = competitor["name"]
        print(f"[CI Pricing] Анализ цен: {name}")

        # TODO: Реальный парсинг прайс-листов с сайтов
        # Пока генерируем реалистичные данные

        # Ценовой сегмент
        price_segment = competitor.get("price_segment", random.choice(["budget", "mid", "premium"]))

        # Базовые множители для разных сегментов
        segment_multipliers = {
            "budget": 0.7,
            "mid": 1.0,
            "premium": 1.5,
            "luxury": 2.5
        }

        multiplier = segment_multipliers.get(price_segment, 1.0)

        # Генерация цен на типовые услуги (для медицинской ниши)
        if "стоматология" in niche.lower():
            base_prices = {
                "консультация": 1000,
                "чистка": 3000,
                "пломба": 5000,
                "отбеливание": 15000,
                "имплант": 50000
            }
        elif "косметология" in niche.lower():
            base_prices = {
                "консультация": 1500,
                "чистка_лица": 3500,
                "пилинг": 5000,
                "ботокс": 12000,
                "филлеры": 20000
            }
        else:
            base_prices = {
                "услуга_1": 2000,
                "услуга_2": 5000,
                "услуга_3": 10000
            }

        # Применяем множитель и добавляем случайность
        prices = {}
        for service, base_price in base_prices.items():
            price = base_price * multiplier * random.uniform(0.9, 1.1)
            prices[service] = round(price, -2)  # Округляем до сотен

        # Прозрачность цен (есть ли прайс на сайте)
        price_transparency = random.choice([True, True, False])  # 66% вероятность

        # Акции и скидки
        has_promotions = random.choice([True, False])
        promotions = []
        if has_promotions:
            promotions = [
                {"type": "first_visit", "discount": random.randint(10, 30)},
                {"type": "package", "discount": random.randint(15, 40)}
            ]

        # Ценовая стратегия
        pricing_strategy = random.choice(self.pricing_strategies)

        # Средняя цена чека
        avg_check = sum(prices.values()) / len(prices)

        profile = {
            "name": name,
            "price_segment": price_segment,
            "prices": prices,
            "avg_check": round(avg_check),
            "price_transparency": price_transparency,
            "has_promotions": has_promotions,
            "promotions": promotions,
            "pricing_strategy": pricing_strategy,
            "price_competitiveness": self._assess_competitiveness(price_segment)
        }

        return profile

    def _assess_competitiveness(self, segment: str) -> str:
        """Оценить конкурентоспособность цен."""
        if segment == "budget":
            return "high"  # Низкие цены = высокая конкурентоспособность
        elif segment == "mid":
            return "medium"
        else:
            return "low"  # Высокие цены = низкая конкурентоспособность

    async def _analyze_market_pricing(
        self,
        pricing_profiles: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Проанализировать ценообразование на рынке.

        Args:
            pricing_profiles: ценовые профили

        Returns:
            Анализ рынка
        """
        print(f"[CI Pricing] Анализ ценообразования рынка")

        # Распределение по сегментам
        segment_distribution = {}
        for profile in pricing_profiles:
            segment = profile["price_segment"]
            segment_distribution[segment] = segment_distribution.get(segment, 0) + 1

        # Средний чек по сегментам
        avg_check_by_segment = {}
        for segment in ["budget", "mid", "premium"]:
            segment_profiles = [p for p in pricing_profiles if p["price_segment"] == segment]
            if segment_profiles:
                avg_check = sum(p["avg_check"] for p in segment_profiles) / len(segment_profiles)
                avg_check_by_segment[segment] = round(avg_check)

        # Прозрачность цен на рынке
        transparent_count = sum(1 for p in pricing_profiles if p["price_transparency"])
        transparency_rate = (transparent_count / len(pricing_profiles)) * 100

        # Использование акций
        promotions_count = sum(1 for p in pricing_profiles if p["has_promotions"])
        promotions_rate = (promotions_count / len(pricing_profiles)) * 100

        # Средний чек по рынку
        market_avg_check = sum(p["avg_check"] for p in pricing_profiles) / len(pricing_profiles)

        market_analysis = {
            "segment_distribution": segment_distribution,
            "avg_check_by_segment": avg_check_by_segment,
            "market_avg_check": round(market_avg_check),
            "price_transparency_percent": round(transparency_rate, 1),
            "promotions_usage_percent": round(promotions_rate, 1),
            "dominant_segment": max(segment_distribution.items(), key=lambda x: x[1])[0]
        }

        return market_analysis

    async def _identify_pricing_leaders(
        self,
        pricing_profiles: List[Dict[str, Any]]
    ) -> Dict[str, List[Dict[str, Any]]]:
        """
        Определить ценовых лидеров.

        Args:
            pricing_profiles: ценовые профили

        Returns:
            Лидеры по ценам
        """
        print(f"[CI Pricing] Определение ценовых лидеров")

        # Самые дешёвые
        sorted_by_price = sorted(pricing_profiles, key=lambda x: x["avg_check"])
        cheapest = sorted_by_price[:3]

        # Самые дорогие
        most_expensive = sorted_by_price[-3:][::-1]

        # Лучшая прозрачность
        transparent = [p for p in pricing_profiles if p["price_transparency"]]
        best_transparency = sorted(transparent, key=lambda x: len(x["prices"]), reverse=True)[:3]

        return {
            "cheapest": [
                {"name": p["name"], "avg_check": p["avg_check"], "segment": p["price_segment"]}
                for p in cheapest
            ],
            "most_expensive": [
                {"name": p["name"], "avg_check": p["avg_check"], "segment": p["price_segment"]}
                for p in most_expensive
            ],
            "best_transparency": [
                {"name": p["name"], "services_count": len(p["prices"])}
                for p in best_transparency
            ]
        }

    async def _create_positioning_map(
        self,
        pricing_profiles: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Создать карту ценового позиционирования.

        Args:
            pricing_profiles: ценовые профили

        Returns:
            Карта позиционирования
        """
        print(f"[CI Pricing] Создание карты позиционирования")

        # Группировка по сегментам
        positioning = {
            "budget": [],
            "mid": [],
            "premium": [],
            "luxury": []
        }

        for profile in pricing_profiles:
            segment = profile["price_segment"]
            positioning[segment].append({
                "name": profile["name"],
                "avg_check": profile["avg_check"],
                "transparency": profile["price_transparency"]
            })

        # Ценовые разрывы (gaps)
        all_checks = sorted([p["avg_check"] for p in pricing_profiles])
        gaps = []
        for i in range(len(all_checks) - 1):
            diff = all_checks[i + 1] - all_checks[i]
            if diff > all_checks[i] * 0.3:  # Разрыв >30%
                gaps.append({
                    "lower": all_checks[i],
                    "upper": all_checks[i + 1],
                    "gap_percent": round((diff / all_checks[i]) * 100, 1)
                })

        return {
            "positioning": positioning,
            "price_gaps": gaps
        }

    async def _generate_pricing_insights(
        self,
        pricing_profiles: List[Dict[str, Any]],
        market_analysis: Dict[str, Any],
        pricing_leaders: Dict[str, Any],
        positioning_map: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Сгенерировать ценовые инсайты.

        Args:
            pricing_profiles: ценовые профили
            market_analysis: анализ рынка
            pricing_leaders: лидеры по ценам
            positioning_map: карта позиционирования

        Returns:
            Инсайты
        """
        print(f"[CI Pricing] Генерация ценовых инсайтов")

        insights = {
            "market_positioning": market_analysis["dominant_segment"],
            "price_transparency_level": "high" if market_analysis["price_transparency_percent"] > 70 else "medium" if market_analysis["price_transparency_percent"] > 40 else "low",
            "competition_intensity": "high" if len(pricing_profiles) > 10 else "medium" if len(pricing_profiles) > 5 else "low",
            "opportunities_count": len(positioning_map["price_gaps"]),
            "key_findings": []
        }

        # Ключевые находки
        if market_analysis["price_transparency_percent"] < 50:
            insights["key_findings"].append("Менее 50% конкурентов публикуют цены на сайте")

        if len(positioning_map["price_gaps"]) > 0:
            insights["key_findings"].append(f"Обнаружено {len(positioning_map['price_gaps'])} ценовых разрывов для позиционирования")

        if market_analysis["promotions_usage_percent"] > 60:
            insights["key_findings"].append("Высокая активность акций и скидок на рынке")

        return insights

    async def _save_results(self, results: Dict[str, Any]):
        """Сохранить результаты в файл."""
        output_file = "AIM/data/ci-pricing.json"

        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)

        print(f"[CI Pricing] Результаты сохранены в {output_file}")

    def get_capabilities(self) -> List[str]:
        """Возвращает список возможностей агента."""
        return [
            "price_collection",
            "pricing_strategy_analysis",
            "price_positioning",
            "promotion_analysis",
            "price_transparency_analysis",
            "competitive_pricing_analysis"
        ]
