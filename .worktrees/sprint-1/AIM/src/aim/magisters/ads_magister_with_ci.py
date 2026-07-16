"""
Ads Magister with CI Integration

Расширенная версия Ads Magister с интеграцией CI системы.
"""

from typing import Any, Dict, List
from datetime import datetime

from AIM.src.aim.magisters.ads_magister import AdsMagister
from AIM.src.aim.integration.ci_magisters_integration import CIMagisterIntegration


class AdsMagisterWithCI(AdsMagister):
    """
    Ads Magister с интеграцией CI системы.

    Дополнительные возможности:
    - Анализ рекламных стратегий конкурентов
    - Рекомендации по бюджету на основе рынка
    - Ценовое позиционирование
    - Приоритизация рекламных каналов
    """

    def __init__(
        self,
        magister_id: str = "ads-magister",
        database_url: str = "sqlite+aiosqlite:///./AIM/data/aim.db",
        vault_path: str = "./AIM/obsidian/ads-magister",
        ci_integration: CIMagisterIntegration = None
    ):
        """
        Инициализация Ads Magister с CI.

        Args:
            magister_id: ID магистра
            database_url: URL базы данных
            vault_path: Путь к vault
            ci_integration: Интеграция с CI системой
        """
        super().__init__(magister_id, database_url, vault_path)
        self.ci_integration = ci_integration

    async def plan_task_with_ci(self, action: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Планирование задачи с учётом CI инсайтов.

        Args:
            action: Действие
            payload: Данные задачи

        Returns:
            План выполнения с CI инсайтами
        """
        # Базовый план
        plan = {
            "action": action,
            "payload": payload,
            "subagents": await self.identify_subagents(action),
            "created_at": datetime.now().isoformat()
        }

        # Добавляем CI инсайты
        if self.ci_integration:
            ci_insights = await self.ci_integration.get_insights_for_magister(
                magister_type="ads",
                action=action
            )

            # Обогащаем план CI данными
            plan["ci_insights"] = ci_insights
            plan["enhanced"] = True

            # Добавляем рекламную стратегию на основе CI
            plan["ads_strategy"] = self._build_ads_strategy_with_ci(
                ci_insights
            )

            # Добавляем бюджетные рекомендации
            plan["budget_recommendations"] = self._get_budget_recommendations(
                ci_insights
            )

            print(f"[Ads Magister] План обогащён CI инсайтами:")
            print(f"  - Конкурентов: {len(ci_insights.get('competitors', []))}")
            print(f"  - Возможностей: {len(ci_insights.get('opportunities', []))}")
            print(f"  - Рекомендаций: {len(ci_insights.get('recommendations', []))}")

        return plan

    def _build_ads_strategy_with_ci(
        self,
        ci_insights: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Построить рекламную стратегию на основе CI инсайтов.

        Args:
            ci_insights: CI инсайты

        Returns:
            Рекламная стратегия
        """
        strategy = {
            "channels": [],
            "budget_allocation": {},
            "targeting": {},
            "messaging": []
        }

        # Каналы из рекомендаций
        for rec in ci_insights.get("recommendations", []):
            channel = rec.get("title", "").split(":")[1].strip() if ":" in rec.get("title", "") else None
            if channel:
                strategy["channels"].append({
                    "channel": channel,
                    "rationale": rec.get("description"),
                    "tactics": rec.get("tactics", []),
                    "budget_share": rec.get("budget_share", 0),
                    "priority": rec.get("priority", "medium")
                })

        # Бюджет из market context
        market_context = ci_insights.get("market_context", {})
        if "channel_allocation" in market_context:
            strategy["budget_allocation"] = market_context["channel_allocation"]

        # Таргетинг из конкурентов
        for competitor in ci_insights.get("competitors", []):
            positive_topics = competitor.get("positive_topics", [])
            if positive_topics:
                strategy["messaging"].extend(positive_topics[:3])

        return strategy

    def _get_budget_recommendations(
        self,
        ci_insights: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Получить рекомендации по бюджету.

        Args:
            ci_insights: CI инсайты

        Returns:
            Рекомендации по бюджету
        """
        market_context = ci_insights.get("market_context", {})

        return {
            "recommended_total": market_context.get("recommended_budget", 0),
            "avg_market_check": market_context.get("avg_check", 0),
            "channel_allocation": market_context.get("channel_allocation", {}),
            "rationale": "На основе анализа рынка и конкурентов"
        }

    async def get_pricing_insights(self) -> Dict[str, Any]:
        """
        Получить ценовые инсайты из CI системы.

        Returns:
            Ценовые инсайты
        """
        if not self.ci_integration:
            return {}

        insights = await self.ci_integration.get_insights_for_magister(
            magister_type="ads",
            action="pricing_analysis"
        )

        return {
            "market_context": insights.get("market_context", {}),
            "opportunities": insights.get("opportunities", []),
            "competitors": insights.get("competitors", [])
        }

    async def get_competitor_messaging(self) -> List[Dict[str, Any]]:
        """
        Получить анализ месседжей конкурентов.

        Returns:
            Анализ месседжей
        """
        if not self.ci_integration:
            return []

        insights = await self.ci_integration.get_insights_for_magister(
            magister_type="ads",
            action="messaging_analysis"
        )

        messaging = []

        for competitor in insights.get("competitors", []):
            messaging.append({
                "competitor": competitor.get("name"),
                "rating": competitor.get("rating"),
                "positive_topics": competitor.get("positive_topics", []),
                "negative_topics": competitor.get("negative_topics", []),
                "recommendation": "Использовать positive topics в креативах, избегать negative topics"
            })

        return messaging

    async def suggest_ad_channels(self) -> List[Dict[str, Any]]:
        """
        Предложить рекламные каналы на основе CI анализа.

        Returns:
            Рекомендованные каналы
        """
        if not self.ci_integration:
            return []

        insights = await self.ci_integration.get_insights_for_magister(
            magister_type="ads",
            action="channel_selection"
        )

        channels = []

        for rec in insights.get("recommendations", []):
            if "Канал:" in rec.get("title", ""):
                channel_name = rec.get("title", "").split(":")[1].strip()
                channels.append({
                    "channel": channel_name,
                    "description": rec.get("description"),
                    "tactics": rec.get("tactics", []),
                    "budget_share": rec.get("budget_share", 0),
                    "priority": rec.get("priority", "medium")
                })

        return channels
