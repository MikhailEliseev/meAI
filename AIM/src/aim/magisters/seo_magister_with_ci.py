"""
SEO Magister with CI Integration

Расширенная версия SEO Magister с интеграцией CI системы.
"""

from typing import Any, Dict, List
from datetime import datetime

from aim.magisters.seo_magister import SEOMagister
from aim.integration.ci_magisters_integration import CIMagisterIntegration


class SEOMagisterWithCI(SEOMagister):
    """
    SEO Magister с интеграцией CI системы.

    Дополнительные возможности:
    - Использование CI инсайтов для принятия решений
    - Автоматическая приоритизация задач на основе конкурентного анализа
    - Рекомендации на основе рыночных возможностей
    """

    def __init__(
        self,
        magister_id: str = "seo-magister",
        database_url: str = "sqlite+aiosqlite:///./AIM/data/aim.db",
        vault_path: str = "./AIM/obsidian/seo-magister",
        ci_integration: CIMagisterIntegration = None
    ):
        """
        Инициализация SEO Magister с CI.

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
                magister_type="seo",
                action=action
            )

            # Обогащаем план CI данными
            plan["ci_insights"] = ci_insights
            plan["enhanced"] = True

            # Добавляем приоритеты на основе CI
            plan["priorities"] = self._calculate_priorities_with_ci(
                plan, ci_insights
            )

            # Добавляем рекомендации
            plan["ci_recommendations"] = ci_insights.get("recommendations", [])

            print(f"[SEO Magister] План обогащён CI инсайтами:")
            print(f"  - Конкурентов: {len(ci_insights.get('competitors', []))}")
            print(f"  - Возможностей: {len(ci_insights.get('opportunities', []))}")
            print(f"  - Рекомендаций: {len(ci_insights.get('recommendations', []))}")

        return plan

    def _calculate_priorities_with_ci(
        self,
        plan: Dict[str, Any],
        ci_insights: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Рассчитать приоритеты с учётом CI инсайтов.

        Args:
            plan: Базовый план
            ci_insights: CI инсайты

        Returns:
            Приоритизированные задачи
        """
        priorities = []

        # Высокий приоритет для quick wins из CI
        for rec in ci_insights.get("recommendations", []):
            if rec.get("priority") == "high":
                priorities.append({
                    "task": rec.get("title"),
                    "priority": "high",
                    "reason": "CI Quick Win",
                    "estimated_time": rec.get("estimated_time", "unknown"),
                    "impact": "high"
                })

        # Средний приоритет для возможностей
        for opp in ci_insights.get("opportunities", []):
            if opp.get("impact") == "high":
                priorities.append({
                    "task": opp.get("description"),
                    "priority": "medium",
                    "reason": "CI Opportunity",
                    "impact": opp.get("impact")
                })

        return priorities

    async def get_competitive_context(self) -> Dict[str, Any]:
        """
        Получить конкурентный контекст из CI системы.

        Returns:
            Конкурентный контекст
        """
        if not self.ci_integration:
            return {}

        insights = await self.ci_integration.get_insights_for_magister(
            magister_type="seo",
            action="competitive_analysis"
        )

        return {
            "competitors_count": len(insights.get("competitors", [])),
            "opportunities_count": len(insights.get("opportunities", [])),
            "market_context": insights.get("market_context", {}),
            "top_competitors": insights.get("competitors", [])[:3]
        }

    async def get_content_recommendations(self) -> List[Dict[str, Any]]:
        """
        Получить рекомендации по контенту из CI системы.

        Returns:
            Рекомендации по контенту
        """
        if not self.ci_integration:
            return []

        insights = await self.ci_integration.get_insights_for_magister(
            magister_type="seo",
            action="content_strategy"
        )

        recommendations = []

        # Рекомендации из CI
        for rec in insights.get("recommendations", []):
            if "контент" in rec.get("title", "").lower() or "content" in rec.get("title", "").lower():
                recommendations.append(rec)

        # Возможности по контенту
        for opp in insights.get("opportunities", []):
            if opp.get("type") == "content_quality":
                recommendations.append({
                    "title": "Улучшить качество контента",
                    "description": opp.get("description"),
                    "priority": "high",
                    "source": "CI Analysis"
                })

        return recommendations
