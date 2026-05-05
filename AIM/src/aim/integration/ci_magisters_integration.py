"""
CI Magisters Integration

Интегрирует CI систему с SEO, Content и Ads Magisters.
Позволяет Magisters использовать CI инсайты для принятия решений.
"""

from typing import Any, Dict, List, Optional
from datetime import datetime
import json
from pathlib import Path

from meai.events.event_bus import EventBus, Message
from meai.memory.obsidian import ObsidianVault


class CIMagisterIntegration:
    """
    Интеграция CI системы с Magisters.

    Предоставляет Magisters доступ к CI инсайтам:
    - Конкурентный анализ
    - Рыночные возможности
    - Стратегические рекомендации
    - Приоритизированные действия
    """

    def __init__(
        self,
        event_bus: EventBus,
        ci_data_path: str = "AIM/data"
    ):
        """
        Инициализация интеграции.

        Args:
            event_bus: Event Bus для коммуникации
            ci_data_path: Путь к данным CI системы
        """
        self.event_bus = event_bus
        self.ci_data_path = Path(ci_data_path)

        # Кэш CI данных
        self._cache: Dict[str, Any] = {}
        self._cache_timestamp: Optional[datetime] = None
        self._cache_ttl = 3600  # 1 час

    async def initialize(self) -> None:
        """Инициализация интеграции."""
        await self.event_bus.initialize()

        # Подписка на события CI системы
        await self._subscribe_to_ci_events()

        # Загрузка существующих данных
        await self._load_ci_data()

    async def _subscribe_to_ci_events(self) -> None:
        """Подписка на события CI системы."""
        # Подписываемся на завершение CI анализа
        # Magisters будут получать уведомления о новых инсайтах
        pass

    async def _load_ci_data(self) -> None:
        """Загрузка данных CI системы."""
        print("[CI Integration] Загрузка CI данных...")

        # Загружаем все JSON файлы из CI data
        ci_files = {
            "competitors": "ci-competitors.json",
            "audits": "ci-audits.json",
            "reputation": "ci-reputation.json",
            "strategy": "ci-strategy.json",
            "finance": "ci-finance.json",
            "vacancies": "ci-vacancies.json",
            "tech": "ci-tech.json",
            "content": "ci-content.json",
            "pricing": "ci-pricing.json",
            "ecosystem": "ci-ecosystem.json",
            "prioritizer": "ci-prioritizer.json",
            "marketing_strategy": "ci-marketing-strategy.json"
        }

        for key, filename in ci_files.items():
            file_path = self.ci_data_path / filename
            if file_path.exists():
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        self._cache[key] = json.load(f)
                except Exception as e:
                    print(f"[CI Integration] Ошибка загрузки {filename}: {e}")

        self._cache_timestamp = datetime.now()
        print(f"[CI Integration] Загружено {len(self._cache)} файлов")

    async def get_insights_for_magister(
        self,
        magister_type: str,
        action: str
    ) -> Dict[str, Any]:
        """
        Получить релевантные CI инсайты для Magister.

        Args:
            magister_type: Тип магистра (seo, content, ads)
            action: Действие, которое выполняет магистр

        Returns:
            Релевантные инсайты из CI системы
        """
        # Проверяем кэш
        if self._is_cache_stale():
            await self._load_ci_data()

        if magister_type == "seo":
            return await self._get_seo_insights(action)
        elif magister_type == "content":
            return await self._get_content_insights(action)
        elif magister_type == "ads":
            return await self._get_ads_insights(action)
        else:
            return {}

    def _is_cache_stale(self) -> bool:
        """Проверка актуальности кэша."""
        if not self._cache_timestamp:
            return True

        age = (datetime.now() - self._cache_timestamp).total_seconds()
        return age > self._cache_ttl

    async def _get_seo_insights(self, action: str) -> Dict[str, Any]:
        """
        Получить SEO инсайты из CI данных.

        Args:
            action: SEO действие

        Returns:
            SEO инсайты
        """
        insights = {
            "action": action,
            "competitors": [],
            "opportunities": [],
            "recommendations": [],
            "market_context": {}
        }

        # Конкуренты
        if "competitors" in self._cache:
            competitors_data = self._cache["competitors"]
            insights["competitors"] = competitors_data.get("competitors", [])[:5]

        # Аудиты сайтов
        if "audits" in self._cache:
            audits = self._cache["audits"]

            # Извлекаем SEO-релевантные инсайты
            for audit in audits.get("audits", []):
                seo_score = audit.get("scores", {}).get("technical", 0)
                if seo_score < 70:
                    insights["opportunities"].append({
                        "type": "technical_seo",
                        "competitor": audit.get("name"),
                        "score": seo_score,
                        "description": f"Слабое техническое SEO у {audit.get('name')} ({seo_score}/100)"
                    })

        # Контент
        if "content" in self._cache:
            content_data = self._cache["content"]
            market = content_data.get("market_analysis", {})

            insights["market_context"]["avg_content_quality"] = market.get("avg_quality_score", 0)
            insights["market_context"]["avg_seo_score"] = market.get("avg_seo_score", 0)

            # Возможности по контенту
            if market.get("avg_quality_score", 0) < 70:
                insights["opportunities"].append({
                    "type": "content_quality",
                    "description": "Низкое качество контента у конкурентов",
                    "impact": "high"
                })

        # Стратегические рекомендации
        if "strategy" in self._cache:
            strategy = self._cache["strategy"]
            for rec in strategy.get("recommendations", [])[:3]:
                if "seo" in rec.get("title", "").lower() or "контент" in rec.get("title", "").lower():
                    insights["recommendations"].append(rec)

        # Приоритизированные действия
        if "prioritizer" in self._cache:
            prioritizer = self._cache["prioritizer"]
            for action_item in prioritizer.get("action_plan", [])[:5]:
                if action_item.get("category") == "quick_win":
                    insights["recommendations"].append({
                        "title": action_item.get("title"),
                        "description": action_item.get("description"),
                        "priority": "high",
                        "estimated_time": action_item.get("estimated_time")
                    })

        return insights

    async def _get_content_insights(self, action: str) -> Dict[str, Any]:
        """
        Получить Content инсайты из CI данных.

        Args:
            action: Content действие

        Returns:
            Content инсайты
        """
        insights = {
            "action": action,
            "content_gaps": [],
            "opportunities": [],
            "recommendations": [],
            "market_context": {}
        }

        # Контент-анализ
        if "content" in self._cache:
            content_data = self._cache["content"]

            # Рыночный контекст
            market = content_data.get("market_analysis", {})
            insights["market_context"] = {
                "avg_content_pieces": market.get("avg_content_pieces", 0),
                "avg_quality": market.get("avg_quality_score", 0),
                "strategy_adoption": market.get("strategy_adoption_percent", 0)
            }

            # Пробелы в контенте
            gaps = content_data.get("content_gaps", [])
            insights["content_gaps"] = gaps

            # Возможности
            for gap in gaps:
                if gap.get("opportunity") == "high":
                    insights["opportunities"].append({
                        "type": gap.get("type"),
                        "description": gap.get("description"),
                        "impact": "high"
                    })

        # Маркетинговая стратегия
        if "marketing_strategy" in self._cache:
            strategy = self._cache["marketing_strategy"]

            # Каналы контента
            for channel in strategy.get("channel_strategy", []):
                if channel.get("channel") in ["content", "seo"]:
                    insights["recommendations"].append({
                        "title": f"Канал: {channel.get('channel')}",
                        "description": channel.get("rationale"),
                        "tactics": channel.get("tactics", []),
                        "budget_share": channel.get("budget_share")
                    })

        return insights

    async def _get_ads_insights(self, action: str) -> Dict[str, Any]:
        """
        Получить Ads инсайты из CI данных.

        Args:
            action: Ads действие

        Returns:
            Ads инсайты
        """
        insights = {
            "action": action,
            "competitors": [],
            "opportunities": [],
            "recommendations": [],
            "market_context": {}
        }

        # Ценообразование
        if "pricing" in self._cache:
            pricing_data = self._cache["pricing"]

            market = pricing_data.get("market_analysis", {})
            insights["market_context"]["avg_check"] = market.get("market_avg_check", 0)
            insights["market_context"]["price_transparency"] = market.get("price_transparency_percent", 0)

            # Ценовые возможности
            gaps = pricing_data.get("positioning_map", {}).get("price_gaps", [])
            for gap in gaps:
                insights["opportunities"].append({
                    "type": "pricing_gap",
                    "lower": gap.get("lower"),
                    "upper": gap.get("upper"),
                    "gap_percent": gap.get("gap_percent"),
                    "description": f"Ценовой разрыв: {gap.get('gap_percent')}%"
                })

        # Маркетинговая стратегия
        if "marketing_strategy" in self._cache:
            strategy = self._cache["marketing_strategy"]

            # Рекламные каналы
            for channel in strategy.get("channel_strategy", []):
                if channel.get("channel") in ["context", "social"]:
                    insights["recommendations"].append({
                        "title": f"Канал: {channel.get('channel')}",
                        "description": channel.get("rationale"),
                        "tactics": channel.get("tactics", []),
                        "budget_share": channel.get("budget_share"),
                        "priority": channel.get("priority")
                    })

            # Бюджет
            budget = strategy.get("budget_allocation", {})
            insights["market_context"]["recommended_budget"] = budget.get("total_budget", 0)
            insights["market_context"]["channel_allocation"] = budget.get("by_channel", {})

        # Репутация (для рекламных креативов)
        if "reputation" in self._cache:
            reputation = self._cache["reputation"]

            # Что хвалят/ругают конкуренты
            for profile in reputation.get("reputation_profiles", [])[:3]:
                insights["competitors"].append({
                    "name": profile.get("name"),
                    "rating": profile.get("avg_rating"),
                    "positive_topics": profile.get("topics", {}).get("positive", []),
                    "negative_topics": profile.get("topics", {}).get("negative", [])
                })

        return insights

    async def notify_magisters_about_new_analysis(
        self,
        analysis_id: str,
        niche: str,
        geo: str
    ) -> None:
        """
        Уведомить Magisters о новом CI анализе.

        Args:
            analysis_id: ID анализа
            niche: Ниша
            geo: География
        """
        # Отправляем событие через Event Bus
        message = Message(
            id=f"ci_analysis_{analysis_id}",
            type="ci_analysis_complete",
            priority=1,
            payload={
                "analysis_id": analysis_id,
                "niche": niche,
                "geo": geo,
                "timestamp": datetime.now().isoformat()
            },
            created_at=datetime.now()
        )

        await self.event_bus.publish(message)
        print(f"[CI Integration] Уведомление отправлено Magisters: {analysis_id}")

    async def get_summary_for_magister(
        self,
        magister_type: str
    ) -> str:
        """
        Получить краткую сводку CI инсайтов для Magister.

        Args:
            magister_type: Тип магистра

        Returns:
            Текстовая сводка
        """
        insights = await self.get_insights_for_magister(magister_type, "summary")

        summary_parts = []

        # Конкуренты
        if insights.get("competitors"):
            count = len(insights["competitors"])
            summary_parts.append(f"Проанализировано {count} конкурентов")

        # Возможности
        if insights.get("opportunities"):
            count = len(insights["opportunities"])
            summary_parts.append(f"Найдено {count} возможностей")

        # Рекомендации
        if insights.get("recommendations"):
            count = len(insights["recommendations"])
            summary_parts.append(f"Доступно {count} рекомендаций")

        return ". ".join(summary_parts) if summary_parts else "CI данные недоступны"
