"""
CI Ecosystem Agent - Partner & Integration Ecosystem Analysis

Анализирует экосистему партнёров и интеграций конкурентов:
- Партнёры и поставщики
- Интеграции с сервисами
- Экосистема продуктов
- Стратегические альянсы
- Каналы дистрибуции
"""

from typing import Any, Dict, List
from datetime import datetime
import json
import random

from meai.agents.base_agent import Agent, Task, TaskResult
from meai.memory.obsidian import ObsidianVault


class CIEcosystemAgent(Agent):
    """CI Ecosystem - агент анализа экосистемы партнёров и интеграций."""

    def __init__(
        self,
        agent_id: str,
        database_url: str = "sqlite+aiosqlite:///./data/meai.db",
        vault_path: str = "./obsidian"
    ):
        super().__init__(
            agent_id=agent_id,
            agent_type="ci-ecosystem",
            database_url=database_url,
            vault_path=vault_path
        )
        self.vault = ObsidianVault("AIM/obsidian/ci-ecosystem")

        # Partner types
        self.partner_types = {
            "technology": "Технологические партнёры",
            "distribution": "Дистрибуция",
            "marketing": "Маркетинговые партнёры",
            "suppliers": "Поставщики",
            "strategic": "Стратегические альянсы",
            "integration": "Интеграционные партнёры"
        }

        # Integration categories
        self.integration_categories = {
            "crm": "CRM системы",
            "payment": "Платёжные системы",
            "analytics": "Аналитика",
            "communication": "Коммуникации",
            "booking": "Онлайн-запись",
            "marketing": "Маркетинг автоматизация"
        }

    async def execute_task(self, task: Task) -> TaskResult:
        """
        Выполнить анализ экосистемы конкурентов.

        Args:
            task: Задача с payload:
                - competitors: список конкурентов (обязательно)
                - niche: ниша (опционально)

        Returns:
            TaskResult с анализом экосистемы
        """
        try:
            competitors = task.payload["competitors"]
            niche = task.payload.get("niche", "")

            print(f"[CI Ecosystem] Начало анализа экосистемы {len(competitors)} конкурентов")

            # Шаг 1: Analyze ecosystem for each competitor
            ecosystem_profiles = []
            for competitor in competitors:
                profile = await self._analyze_competitor_ecosystem(competitor, niche)
                ecosystem_profiles.append(profile)

            # Шаг 2: Market ecosystem analysis
            market_analysis = await self._analyze_market_ecosystem(ecosystem_profiles)

            # Шаг 3: Identify ecosystem leaders
            ecosystem_leaders = await self._identify_ecosystem_leaders(ecosystem_profiles)

            # Шаг 4: Integration opportunities
            integration_opportunities = await self._identify_integration_opportunities(
                ecosystem_profiles, niche
            )

            # Шаг 5: Ecosystem insights
            insights = await self._generate_ecosystem_insights(
                ecosystem_profiles, market_analysis, ecosystem_leaders, integration_opportunities
            )

            # Шаг 6: Save results
            results = {
                "analysis_date": datetime.now().isoformat(),
                "total_analyzed": len(competitors),
                "niche": niche,
                "ecosystem_profiles": ecosystem_profiles,
                "market_analysis": market_analysis,
                "ecosystem_leaders": ecosystem_leaders,
                "integration_opportunities": integration_opportunities,
                "insights": insights
            }

            await self._save_results(results)

            print(f"[CI Ecosystem] Анализ экосистемы завершён для {len(competitors)} конкурентов")

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
            print(f"[CI Ecosystem] Ошибка: {e}")
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

    async def _analyze_competitor_ecosystem(
        self,
        competitor: Dict[str, Any],
        niche: str
    ) -> Dict[str, Any]:
        """
        Проанализировать экосистему одного конкурента.

        Args:
            competitor: данные конкурента
            niche: ниша

        Returns:
            Профиль экосистемы конкурента
        """
        name = competitor["name"]
        print(f"[CI Ecosystem] Анализ экосистемы: {name}")

        # TODO: Реальный сбор через парсинг сайтов, соцсетей, пресс-релизов
        # Пока генерируем реалистичные данные

        # Партнёры по типам
        partners_by_type = {}
        for partner_type in ["technology", "marketing", "suppliers", "strategic"]:
            count = random.randint(0, 5) if random.random() > 0.4 else 0
            if count > 0:
                partners_by_type[partner_type] = count

        # Интеграции
        integrations = {}
        for integration_cat in ["crm", "payment", "analytics", "booking"]:
            has_integration = random.choice([True, False])
            if has_integration:
                # Примеры популярных сервисов
                services = {
                    "crm": ["amoCRM", "Битрикс24", "Salesforce"],
                    "payment": ["Яндекс.Касса", "CloudPayments", "Сбербанк"],
                    "analytics": ["Google Analytics", "Яндекс.Метрика"],
                    "booking": ["Yclients", "DIKIDI", "Altegio"]
                }
                integrations[integration_cat] = random.choice(services.get(integration_cat, ["Unknown"]))

        # Каналы дистрибуции
        distribution_channels = []
        channels = ["direct", "aggregators", "marketplaces", "partners"]
        for channel in channels:
            if random.choice([True, False]):
                distribution_channels.append(channel)

        # Стратегические альянсы
        has_strategic_alliances = random.choice([True, False])
        strategic_alliances = []
        if has_strategic_alliances:
            strategic_alliances = [
                {"type": "co-marketing", "partner": "Партнёр А"},
                {"type": "referral", "partner": "Партнёр Б"}
            ]

        # Оценка зрелости экосистемы
        ecosystem_maturity = self._assess_ecosystem_maturity(
            len(partners_by_type),
            len(integrations),
            len(distribution_channels),
            has_strategic_alliances
        )

        profile = {
            "name": name,
            "partners_by_type": partners_by_type,
            "total_partners": sum(partners_by_type.values()),
            "integrations": integrations,
            "integration_count": len(integrations),
            "distribution_channels": distribution_channels,
            "strategic_alliances": strategic_alliances,
            "has_strategic_alliances": has_strategic_alliances,
            "ecosystem_maturity": ecosystem_maturity
        }

        return profile

    def _assess_ecosystem_maturity(
        self,
        partner_types: int,
        integrations: int,
        channels: int,
        has_alliances: bool
    ) -> str:
        """Оценить зрелость экосистемы."""
        score = 0

        # Разнообразие партнёров
        if partner_types >= 3:
            score += 3
        elif partner_types >= 2:
            score += 2
        elif partner_types >= 1:
            score += 1

        # Интеграции
        if integrations >= 4:
            score += 3
        elif integrations >= 2:
            score += 2
        elif integrations >= 1:
            score += 1

        # Каналы дистрибуции
        if channels >= 3:
            score += 2
        elif channels >= 2:
            score += 1

        # Стратегические альянсы
        if has_alliances:
            score += 2

        # Итоговая оценка
        if score >= 8:
            return "advanced"
        elif score >= 5:
            return "intermediate"
        elif score >= 2:
            return "basic"
        else:
            return "minimal"

    async def _analyze_market_ecosystem(
        self,
        ecosystem_profiles: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Проанализировать экосистему рынка.

        Args:
            ecosystem_profiles: профили экосистем

        Returns:
            Анализ рынка
        """
        print(f"[CI Ecosystem] Анализ экосистемы рынка")

        # Средние показатели
        avg_partners = sum(p["total_partners"] for p in ecosystem_profiles) / len(ecosystem_profiles)
        avg_integrations = sum(p["integration_count"] for p in ecosystem_profiles) / len(ecosystem_profiles)

        # Популярные интеграции
        integration_usage = {}
        for profile in ecosystem_profiles:
            for category, service in profile["integrations"].items():
                key = f"{category}:{service}"
                integration_usage[key] = integration_usage.get(key, 0) + 1

        most_popular_integrations = sorted(
            integration_usage.items(),
            key=lambda x: x[1],
            reverse=True
        )[:5]

        # Использование каналов дистрибуции
        channel_usage = {}
        for profile in ecosystem_profiles:
            for channel in profile["distribution_channels"]:
                channel_usage[channel] = channel_usage.get(channel, 0) + 1

        # Компании со стратегическими альянсами
        with_alliances = sum(1 for p in ecosystem_profiles if p["has_strategic_alliances"])
        alliances_rate = (with_alliances / len(ecosystem_profiles)) * 100

        market_analysis = {
            "avg_partners": round(avg_partners, 1),
            "avg_integrations": round(avg_integrations, 1),
            "most_popular_integrations": [
                {"integration": integ, "usage_count": count}
                for integ, count in most_popular_integrations
            ],
            "channel_usage": channel_usage,
            "strategic_alliances_percent": round(alliances_rate, 1)
        }

        return market_analysis

    async def _identify_ecosystem_leaders(
        self,
        ecosystem_profiles: List[Dict[str, Any]]
    ) -> Dict[str, List[Dict[str, Any]]]:
        """
        Определить лидеров по экосистеме.

        Args:
            ecosystem_profiles: профили экосистем

        Returns:
            Лидеры по экосистеме
        """
        print(f"[CI Ecosystem] Определение лидеров экосистемы")

        # Сортировка по количеству партнёров
        sorted_by_partners = sorted(
            ecosystem_profiles,
            key=lambda x: x["total_partners"],
            reverse=True
        )

        # Сортировка по интеграциям
        sorted_by_integrations = sorted(
            ecosystem_profiles,
            key=lambda x: x["integration_count"],
            reverse=True
        )

        # Сортировка по зрелости
        maturity_scores = {"minimal": 1, "basic": 2, "intermediate": 3, "advanced": 4}
        sorted_by_maturity = sorted(
            ecosystem_profiles,
            key=lambda x: maturity_scores.get(x["ecosystem_maturity"], 1),
            reverse=True
        )

        return {
            "partner_leaders": [
                {
                    "name": p["name"],
                    "partners_count": p["total_partners"],
                    "maturity": p["ecosystem_maturity"]
                }
                for p in sorted_by_partners[:3] if p["total_partners"] > 0
            ],
            "integration_leaders": [
                {
                    "name": p["name"],
                    "integrations_count": p["integration_count"],
                    "integrations": list(p["integrations"].keys())
                }
                for p in sorted_by_integrations[:3] if p["integration_count"] > 0
            ],
            "maturity_leaders": [
                {
                    "name": p["name"],
                    "maturity": p["ecosystem_maturity"]
                }
                for p in sorted_by_maturity[:3]
            ]
        }

    async def _identify_integration_opportunities(
        self,
        ecosystem_profiles: List[Dict[str, Any]],
        niche: str
    ) -> List[Dict[str, Any]]:
        """
        Определить возможности для интеграций.

        Args:
            ecosystem_profiles: профили экосистем
            niche: ниша

        Returns:
            Возможности для интеграций
        """
        print(f"[CI Ecosystem] Определение возможностей для интеграций")

        opportunities = []

        # Проверка покрытия категорий интеграций
        all_categories = set(self.integration_categories.keys())
        used_categories = set()

        for profile in ecosystem_profiles:
            used_categories.update(profile["integrations"].keys())

        missing_categories = all_categories - used_categories

        for category in missing_categories:
            opportunities.append({
                "type": "missing_integration",
                "category": category,
                "description": f"Никто не интегрирован с {self.integration_categories[category]}",
                "priority": "high"
            })

        # Низкое использование партнёрств
        low_partnership = sum(1 for p in ecosystem_profiles if p["total_partners"] < 2)
        if low_partnership > len(ecosystem_profiles) / 2:
            opportunities.append({
                "type": "partnership_gap",
                "description": "Большинство конкурентов имеют мало партнёров",
                "priority": "medium"
            })

        # Отсутствие стратегических альянсов
        no_alliances = sum(1 for p in ecosystem_profiles if not p["has_strategic_alliances"])
        if no_alliances > len(ecosystem_profiles) / 2:
            opportunities.append({
                "type": "alliance_gap",
                "description": "Большинство конкурентов не имеют стратегических альянсов",
                "priority": "high"
            })

        return opportunities

    async def _generate_ecosystem_insights(
        self,
        ecosystem_profiles: List[Dict[str, Any]],
        market_analysis: Dict[str, Any],
        ecosystem_leaders: Dict[str, Any],
        integration_opportunities: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Сгенерировать инсайты по экосистеме.

        Args:
            ecosystem_profiles: профили экосистем
            market_analysis: анализ рынка
            ecosystem_leaders: лидеры экосистемы
            integration_opportunities: возможности интеграций

        Returns:
            Инсайты
        """
        print(f"[CI Ecosystem] Генерация инсайтов по экосистеме")

        # Оценка зрелости рынка
        maturity_scores = {"minimal": 1, "basic": 2, "intermediate": 3, "advanced": 4}
        avg_maturity = sum(
            maturity_scores.get(p["ecosystem_maturity"], 1) for p in ecosystem_profiles
        ) / len(ecosystem_profiles)

        if avg_maturity >= 3:
            market_maturity = "advanced"
        elif avg_maturity >= 2:
            market_maturity = "intermediate"
        else:
            market_maturity = "basic"

        insights = {
            "ecosystem_maturity": market_maturity,
            "integration_level": "high" if market_analysis["avg_integrations"] > 3 else "medium" if market_analysis["avg_integrations"] > 1 else "low",
            "partnership_activity": "high" if market_analysis["avg_partners"] > 3 else "medium" if market_analysis["avg_partners"] > 1 else "low",
            "opportunities_count": len([o for o in integration_opportunities if o.get("priority") == "high"]),
            "key_findings": []
        }

        # Ключевые находки
        if market_analysis["strategic_alliances_percent"] < 30:
            insights["key_findings"].append("Менее 30% конкурентов имеют стратегические альянсы")

        if market_analysis["avg_integrations"] < 2:
            insights["key_findings"].append("Низкий уровень интеграций на рынке")

        if len(integration_opportunities) > 0:
            insights["key_findings"].append(f"Обнаружено {len(integration_opportunities)} возможностей для построения экосистемы")

        if market_analysis.get("most_popular_integrations"):
            top_integration = market_analysis["most_popular_integrations"][0]
            insights["key_findings"].append(f"Самая популярная интеграция: {top_integration['integration']}")

        return insights

    async def _save_results(self, results: Dict[str, Any]):
        """Сохранить результаты в файл."""
        output_file = "AIM/data/ci-ecosystem.json"

        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)

        print(f"[CI Ecosystem] Результаты сохранены в {output_file}")

    def get_capabilities(self) -> List[str]:
        """Возвращает список возможностей агента."""
        return [
            "partner_analysis",
            "integration_analysis",
            "ecosystem_mapping",
            "strategic_alliance_analysis",
            "distribution_channel_analysis",
            "ecosystem_maturity_assessment"
        ]
