"""
Analytics Magister - Магистр аналитики и статистики

Отвечает за:
- Сбор данных из Яндекс.Метрики, Google Analytics, рекламных кабинетов
- Обработку и маркировку данных
- Анализ эффективности кампаний
- Генерацию инсайтов для стратегических решений

Субагенты:
1. Data Collector - сбор данных из всех источников
2. Data Processor - обработка, маркировка, нормализация
3. Performance Analyzer - анализ эффективности
4. Insights Generator - генерация рекомендаций
"""

from datetime import datetime
from typing import Any, Dict, List, Optional
from pathlib import Path
import json

from meai.events.event_bus import EventBus, Event, EventPriority
from meai.agents.magister_base import BaseMagister


class AnalyticsMagister(BaseMagister):
    """
    Analytics Magister - координирует работу субагентов аналитики

    Управляет:
    - Data Collector (сбор данных)
    - Data Processor (обработка данных)
    - Performance Analyzer (анализ эффективности)
    - Insights Generator (генерация инсайтов)
    """

    def __init__(
        self,
        magister_id: str,
        event_bus: EventBus | None = None,
        vault_path: Path | None = None,
        data_path: Path | None = None,
        vault: Any | None = None,
    ):
        """Initialize Analytics Magister

        Args:
            magister_id: Unique Magister ID
            event_bus: Optional EventBus instance (for testing)
            vault_path: Optional Path to Analytics Magister's Obsidian vault
            data_path: Optional Path to data directory
            vault: Optional ObsidianVault instance (for testing)
        """
        # Use defaults if not provided
        if vault_path is None:
            vault_path = Path("./AIM/obsidian/analytics-magister")
        if data_path is None:
            data_path = Path("./AIM/data/analytics")

        # Initialize parent (only if event_bus provided)
        if event_bus is not None:
            super().__init__(
                magister_id=magister_id,
                name="Analytics Magister",
                specialization="analytics",
                event_bus=event_bus,
                vault_path=vault_path
            )
        else:
            # For testing without event_bus
            self.magister_id = magister_id
            self.name = "Analytics Magister"
            self.specialization = "analytics"
            self.vault_path = vault_path

        # Allow dependency injection for testing
        if vault is not None:
            self.vault = vault

        self.data_path = data_path
        self.data_path.mkdir(parents=True, exist_ok=True)

        # Субагенты
        self.subagents = {
            "data_collector": "Data Collector Agent",
            "data_processor": "Data Processor Agent",
            "performance_analyzer": "Performance Analyzer Agent",
            "insights_generator": "Insights Generator Agent"
        }

        # Источники данных
        self.data_sources = [
            "yandex_metrika",
            "google_analytics",
            "yandex_direct",
            "google_ads",
            "vk_ads",
            "facebook_ads"
        ]

        # Метрики для отслеживания
        self.metrics = {
            "traffic": ["sessions", "users", "pageviews", "bounce_rate"],
            "conversions": ["goals", "transactions", "revenue", "conversion_rate"],
            "campaigns": ["impressions", "clicks", "ctr", "cpc", "cpa", "roas"],
            "engagement": ["avg_session_duration", "pages_per_session", "return_rate"]
        }

    async def execute_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """
        Выполнить задачу аналитики

        Типы задач:
        - collect_data: собрать данные из источников
        - analyze_performance: проанализировать эффективность
        - generate_report: сгенерировать отчёт
        - get_insights: получить инсайты и рекомендации
        """
        task_type = task.get("type")

        if task_type == "collect_data":
            return await self._collect_data(task)
        elif task_type == "analyze_performance":
            return await self._analyze_performance(task)
        elif task_type == "generate_report":
            return await self._generate_report(task)
        elif task_type == "get_insights":
            return await self._get_insights(task)
        else:
            return {
                "status": "error",
                "message": f"Unknown task type: {task_type}"
            }

    async def _collect_data(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """
        Собрать данные из всех источников

        Делегирует Data Collector субагенту
        """
        sources = task.get("sources", self.data_sources)
        date_range = task.get("date_range", {"start": "7daysAgo", "end": "today"})

        # Делегируем Data Collector
        await self._delegate_to_subagent(
            subagent="data_collector",
            task={
                "action": "collect",
                "sources": sources,
                "date_range": date_range,
                "metrics": self.metrics
            }
        )

        # Сохраняем задачу в vault
        await self._log_to_vault(
            f"Collecting data from {len(sources)} sources: {', '.join(sources)}"
        )

        return {
            "status": "delegated",
            "subagent": "data_collector",
            "sources": sources,
            "date_range": date_range
        }

    async def _analyze_performance(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """
        Проанализировать эффективность кампаний

        Делегирует Performance Analyzer субагенту
        """
        period = task.get("period", "last_month")
        campaigns = task.get("campaigns", "all")

        # Делегируем Performance Analyzer
        await self._delegate_to_subagent(
            subagent="performance_analyzer",
            task={
                "action": "analyze",
                "period": period,
                "campaigns": campaigns,
                "compare_with": task.get("compare_with", "previous_period")
            }
        )

        await self._log_to_vault(
            f"Analyzing performance for period: {period}"
        )

        return {
            "status": "delegated",
            "subagent": "performance_analyzer",
            "period": period
        }

    async def _generate_report(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """
        Сгенерировать отчёт

        Собирает данные от всех субагентов и формирует отчёт
        """
        report_type = task.get("report_type", "monthly")
        recipients = task.get("recipients", [])

        # Собираем данные
        data = await self._collect_report_data(report_type)

        # Генерируем отчёт
        report = {
            "type": report_type,
            "generated_at": datetime.now().isoformat(),
            "period": task.get("period", "last_month"),
            "summary": data.get("summary", {}),
            "metrics": data.get("metrics", {}),
            "insights": data.get("insights", []),
            "recommendations": data.get("recommendations", [])
        }

        # Сохраняем отчёт
        report_file = self.data_path / f"report_{report_type}_{datetime.now().strftime('%Y%m%d')}.json"
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)

        await self._log_to_vault(
            f"Generated {report_type} report: {report_file.name}"
        )

        # Отправляем уведомление
        await self.event_bus.publish(Event(
            event_type="analytics.report_generated",
            payload={
                "report_type": report_type,
                "file": str(report_file),
                "recipients": recipients
            },
            priority=EventPriority.P1
        ))

        return {
            "status": "success",
            "report_file": str(report_file),
            "summary": report["summary"]
        }

    async def _get_insights(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """
        Получить инсайты и рекомендации

        Делегирует Insights Generator субагенту
        """
        focus_area = task.get("focus_area", "all")

        # Делегируем Insights Generator
        await self._delegate_to_subagent(
            subagent="insights_generator",
            task={
                "action": "generate_insights",
                "focus_area": focus_area,
                "include_recommendations": True
            }
        )

        await self._log_to_vault(
            f"Generating insights for: {focus_area}"
        )

        return {
            "status": "delegated",
            "subagent": "insights_generator",
            "focus_area": focus_area
        }

    async def _collect_report_data(self, report_type: str) -> Dict[str, Any]:
        """
        Собрать данные для отчёта от всех субагентов
        """
        # В реальной реализации здесь будет сбор данных от субагентов
        # Пока возвращаем mock данные
        return {
            "summary": {
                "total_sessions": 10000,
                "total_users": 7500,
                "conversion_rate": 3.5,
                "revenue": 150000
            },
            "metrics": {
                "traffic": {"growth": "+15%"},
                "conversions": {"growth": "+8%"},
                "campaigns": {"roas": 4.2}
            },
            "insights": [
                "Organic traffic показывает стабильный рост",
                "Конверсия из Яндекс.Директ выше на 20%",
                "Мобильный трафик требует оптимизации"
            ],
            "recommendations": [
                "Увеличить бюджет на Яндекс.Директ",
                "Оптимизировать мобильную версию сайта",
                "Запустить ретаргетинг для брошенных корзин"
            ]
        }

    async def _delegate_to_subagent(
        self,
        subagent: str,
        task: Dict[str, Any]
    ) -> None:
        """
        Делегировать задачу субагенту через Event Bus
        """
        await self.event_bus.publish(Event(
            event_type=f"analytics.{subagent}.task",
            payload={
                "magister_id": self.magister_id,
                "subagent": subagent,
                "task": task,
                "timestamp": datetime.now().isoformat()
            },
            priority=EventPriority.P2
        ))

    async def _log_to_vault(self, message: str) -> None:
        """
        Логировать действие в Obsidian vault
        """
        log_file = self.vault_path / "wiki" / "log.md"
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        with open(log_file, 'a', encoding='utf-8') as f:
            f.write(f"\n## [{timestamp}] {message}\n")

    def get_capabilities(self) -> List[str]:
        """
        Возвращает список возможностей магистра
        """
        return [
            "collect_data",
            "analyze_performance",
            "generate_report",
            "get_insights",
            "track_metrics",
            "compare_periods",
            "identify_trends",
            "provide_recommendations"
        ]

    async def get_performance_metrics(self) -> Dict[str, Any]:
        """
        Получить метрики производительности магистра
        """
        return {
            "magister_id": self.magister_id,
            "name": self.name,
            "specialization": self.specialization,
            "subagents_count": len(self.subagents),
            "data_sources_count": len(self.data_sources),
            "capabilities_count": len(self.get_capabilities()),
            "status": "active"
        }
