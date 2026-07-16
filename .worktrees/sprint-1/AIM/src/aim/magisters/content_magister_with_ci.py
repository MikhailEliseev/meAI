"""
Content Magister with CI Integration

Расширенная версия Content Magister с интеграцией CI системы.
"""

from typing import Any, Dict, List
from datetime import datetime

from AIM.src.aim.magisters.content_magister import ContentMagister
from AIM.src.aim.integration.ci_magisters_integration import CIMagisterIntegration


class ContentMagisterWithCI(ContentMagister):
    """
    Content Magister с интеграцией CI системы.

    Дополнительные возможности:
    - Анализ контент-стратегий конкурентов
    - Выявление пробелов в контенте
    - Рекомендации по типам и темам контента
    - Приоритизация контент-задач
    """

    def __init__(
        self,
        magister_id: str = "content-magister",
        database_url: str = "sqlite+aiosqlite:///./AIM/data/aim.db",
        vault_path: str = "./AIM/obsidian/content-magister",
        ci_integration: CIMagisterIntegration = None
    ):
        """
        Инициализация Content Magister с CI.

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
                magister_type="content",
                action=action
            )

            # Обогащаем план CI данными
            plan["ci_insights"] = ci_insights
            plan["enhanced"] = True

            # Добавляем контент-стратегию на основе CI
            plan["content_strategy"] = self._build_content_strategy_with_ci(
                ci_insights
            )

            # Добавляем пробелы в контенте
            plan["content_gaps"] = ci_insights.get("content_gaps", [])

            print(f"[Content Magister] План обогащён CI инсайтами:")
            print(f"  - Пробелов в контенте: {len(ci_insights.get('content_gaps', []))}")
            print(f"  - Возможностей: {len(ci_insights.get('opportunities', []))}")
            print(f"  - Рекомендаций: {len(ci_insights.get('recommendations', []))}")

        return plan

    def _build_content_strategy_with_ci(
        self,
        ci_insights: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Построить контент-стратегию на основе CI инсайтов.

        Args:
            ci_insights: CI инсайты

        Returns:
            Контент-стратегия
        """
        strategy = {
            "focus_areas": [],
            "content_types": [],
            "priorities": [],
            "quick_wins": []
        }

        # Фокусные области из пробелов
        for gap in ci_insights.get("content_gaps", []):
            if gap.get("opportunity") == "high":
                strategy["focus_areas"].append({
                    "area": gap.get("type"),
                    "description": gap.get("description"),
                    "priority": "high"
                })

        # Типы контента из рекомендаций
        for rec in ci_insights.get("recommendations", []):
            if "tactics" in rec:
                for tactic in rec.get("tactics", []):
                    if tactic not in strategy["content_types"]:
                        strategy["content_types"].append(tactic)

        # Приоритеты из возможностей
        for opp in ci_insights.get("opportunities", []):
            strategy["priorities"].append({
                "type": opp.get("type"),
                "description": opp.get("description"),
                "impact": opp.get("impact")
            })

        return strategy

    async def get_content_gaps(self) -> List[Dict[str, Any]]:
        """
        Получить пробелы в контенте из CI системы.

        Returns:
            Пробелы в контенте
        """
        if not self.ci_integration:
            return []

        insights = await self.ci_integration.get_insights_for_magister(
            magister_type="content",
            action="gap_analysis"
        )

        return insights.get("content_gaps", [])

    async def get_competitor_content_analysis(self) -> Dict[str, Any]:
        """
        Получить анализ контента конкурентов.

        Returns:
            Анализ контента конкурентов
        """
        if not self.ci_integration:
            return {}

        insights = await self.ci_integration.get_insights_for_magister(
            magister_type="content",
            action="competitor_analysis"
        )

        return {
            "market_context": insights.get("market_context", {}),
            "opportunities": insights.get("opportunities", []),
            "recommendations": insights.get("recommendations", [])
        }

    async def suggest_content_topics(self, count: int = 10) -> List[Dict[str, Any]]:
        """
        Предложить темы для контента на основе CI анализа.

        Args:
            count: Количество тем

        Returns:
            Список тем
        """
        if not self.ci_integration:
            return []

        insights = await self.ci_integration.get_insights_for_magister(
            magister_type="content",
            action="topic_suggestions"
        )

        topics = []

        # Темы из пробелов
        for gap in insights.get("content_gaps", [])[:count]:
            topics.append({
                "topic": gap.get("description"),
                "type": gap.get("type"),
                "priority": "high" if gap.get("opportunity") == "high" else "medium",
                "source": "Content Gap Analysis"
            })

        # Темы из возможностей
        for opp in insights.get("opportunities", [])[:count - len(topics)]:
            topics.append({
                "topic": opp.get("description"),
                "type": opp.get("type"),
                "priority": "medium",
                "source": "Market Opportunity"
            })

        return topics[:count]
