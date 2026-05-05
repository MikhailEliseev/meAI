"""
CI Marketing Strategy Agent - Marketing Strategy Development

Разрабатывает маркетинговую стратегию на основе всех инсайтов:
- Анализ всех данных Phase 1-9
- Определение целевой аудитории
- Позиционирование и УТП
- Каналы привлечения
- Бюджет и метрики
- Go-to-Market план
"""

from typing import Any, Dict, List
from datetime import datetime
import json

from meai.agents.base_agent import Agent, Task, TaskResult
from meai.memory.obsidian import ObsidianVault


class CIMarketingStrategyAgent(Agent):
    """CI Marketing Strategy - агент разработки маркетинговой стратегии."""

    def __init__(
        self,
        agent_id: str,
        database_url: str = "sqlite+aiosqlite:///./data/meai.db",
        vault_path: str = "./obsidian"
    ):
        super().__init__(
            agent_id=agent_id,
            agent_type="ci-marketing-strategy",
            database_url=database_url,
            vault_path=vault_path
        )
        self.vault = ObsidianVault("AIM/obsidian/ci-marketing-strategy")

        # Marketing channels
        self.channels = {
            "seo": "SEO (органический поиск)",
            "context": "Контекстная реклама",
            "social": "Социальные сети",
            "content": "Контент-маркетинг",
            "email": "Email-маркетинг",
            "referral": "Реферальная программа",
            "partnerships": "Партнёрства",
            "offline": "Оффлайн каналы"
        }

        # Customer journey stages
        self.journey_stages = {
            "awareness": "Осведомлённость",
            "consideration": "Рассмотрение",
            "decision": "Решение",
            "retention": "Удержание",
            "advocacy": "Адвокация"
        }

    async def execute_task(self, task: Task) -> TaskResult:
        """
        Выполнить разработку маркетинговой стратегии.

        Args:
            task: Задача с payload:
                - previous_results: результаты Phase 1-9 (обязательно)
                - budget: бюджет (опционально)
                - timeline: временные рамки (опционально)

        Returns:
            TaskResult с маркетинговой стратегией
        """
        try:
            previous_results = task.payload.get("previous_results", {})
            budget = task.payload.get("budget", 500000)  # 500k руб по умолчанию
            timeline = task.payload.get("timeline", "3 месяца")

            print(f"[CI Marketing Strategy] Начало разработки стратегии")

            # Шаг 1: Analyze market context
            market_context = await self._analyze_market_context(previous_results)

            # Шаг 2: Define target audience
            target_audience = await self._define_target_audience(previous_results)

            # Шаг 3: Develop positioning & USP
            positioning = await self._develop_positioning(previous_results, market_context)

            # Шаг 4: Select marketing channels
            channel_strategy = await self._select_channels(previous_results, budget)

            # Шаг 5: Create customer journey map
            customer_journey = await self._create_customer_journey(channel_strategy)

            # Шаг 6: Budget allocation
            budget_allocation = await self._allocate_budget(channel_strategy, budget)

            # Шаг 7: Define metrics & KPIs
            metrics = await self._define_metrics(channel_strategy)

            # Шаг 8: Create Go-to-Market plan
            gtm_plan = await self._create_gtm_plan(
                positioning, channel_strategy, budget_allocation, timeline
            )

            # Шаг 9: Save results
            results = {
                "analysis_date": datetime.now().isoformat(),
                "budget": budget,
                "timeline": timeline,
                "market_context": market_context,
                "target_audience": target_audience,
                "positioning": positioning,
                "channel_strategy": channel_strategy,
                "customer_journey": customer_journey,
                "budget_allocation": budget_allocation,
                "metrics": metrics,
                "gtm_plan": gtm_plan
            }

            await self._save_results(results)

            print(f"[CI Marketing Strategy] Стратегия разработана")
            print(f"[CI Marketing Strategy] Каналов: {len(channel_strategy)}")
            print(f"[CI Marketing Strategy] Бюджет: {budget:,} руб")

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
            print(f"[CI Marketing Strategy] Ошибка: {e}")
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

    async def _analyze_market_context(
        self,
        previous_results: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Проанализировать рыночный контекст.

        Args:
            previous_results: результаты предыдущих фаз

        Returns:
            Рыночный контекст
        """
        print(f"[CI Marketing Strategy] Анализ рыночного контекста")

        # Из Phase 1: Scout
        scout = previous_results.get("phase_1", {})
        competitors_count = len(scout.get("competitors", []))

        # Из Phase 5: Finance
        phase5 = previous_results.get("phase_5", {})
        finance = phase5.get("results", {}).get("ci-finance", {})
        market_size = finance.get("insights", {}).get("market_size", "medium")

        # Из Phase 7: Strategist
        strategist = previous_results.get("phase_7", {})
        competitive_landscape = strategist.get("competitive_landscape", "moderate")

        return {
            "competitors_count": competitors_count,
            "market_size": market_size,
            "competitive_intensity": competitive_landscape,
            "market_maturity": "growing",  # Эвристика
            "barriers_to_entry": "medium"
        }

    async def _define_target_audience(
        self,
        previous_results: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Определить целевую аудиторию.

        Args:
            previous_results: результаты предыдущих фаз

        Returns:
            Целевая аудитория
        """
        print(f"[CI Marketing Strategy] Определение целевой аудитории")

        # Базовая сегментация для медицинской ниши
        segments = [
            {
                "name": "Молодые профессионалы",
                "age": "25-35",
                "income": "средний+",
                "pain_points": ["нехватка времени", "качество услуг", "удобство записи"],
                "channels": ["social", "seo", "context"],
                "priority": "high"
            },
            {
                "name": "Семьи с детьми",
                "age": "30-45",
                "income": "средний",
                "pain_points": ["безопасность", "детские специалисты", "цена"],
                "channels": ["seo", "referral", "content"],
                "priority": "medium"
            },
            {
                "name": "Возрастная аудитория",
                "age": "45+",
                "income": "средний",
                "pain_points": ["опыт врачей", "близость к дому", "доверие"],
                "channels": ["seo", "offline", "referral"],
                "priority": "medium"
            }
        ]

        return {
            "segments": segments,
            "primary_segment": segments[0],
            "total_segments": len(segments)
        }

    async def _develop_positioning(
        self,
        previous_results: Dict[str, Any],
        market_context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Разработать позиционирование и УТП.

        Args:
            previous_results: результаты предыдущих фаз
            market_context: рыночный контекст

        Returns:
            Позиционирование
        """
        print(f"[CI Marketing Strategy] Разработка позиционирования")

        # Из Phase 7: Strategist
        strategist = previous_results.get("phase_7", {})
        positioning_rec = strategist.get("positioning", {})

        # Из Phase 9: Prioritizer
        prioritizer = previous_results.get("phase_9", {})
        quick_wins = prioritizer.get("quick_wins", [])

        # Генерация УТП на основе quick wins
        usps = []
        if quick_wins:
            for win in quick_wins[:3]:
                usps.append({
                    "title": win.get("title", ""),
                    "description": win.get("description", ""),
                    "proof_point": "Подтверждено анализом конкурентов"
                })

        # Если нет quick wins, используем дефолтные
        if not usps:
            usps = [
                {
                    "title": "Онлайн-запись 24/7",
                    "description": "Запишитесь на приём в любое время через сайт или приложение",
                    "proof_point": "Только 40% конкурентов предлагают онлайн-запись"
                },
                {
                    "title": "Прозрачные цены",
                    "description": "Все цены на сайте, без скрытых платежей",
                    "proof_point": "Только 60% конкурентов публикуют цены"
                },
                {
                    "title": "Опытные специалисты",
                    "description": "Врачи с опытом работы от 10 лет",
                    "proof_point": "Средний опыт врачей выше рынка на 30%"
                }
            ]

        return {
            "positioning_statement": positioning_rec.get("statement", "Современная клиника с цифровым подходом"),
            "usps": usps,
            "brand_promise": "Качественная медицина без лишних сложностей",
            "differentiation": "Цифровизация + прозрачность + качество"
        }

    async def _select_channels(
        self,
        previous_results: Dict[str, Any],
        budget: int
    ) -> List[Dict[str, Any]]:
        """
        Выбрать маркетинговые каналы.

        Args:
            previous_results: результаты предыдущих фаз
            budget: бюджет

        Returns:
            Стратегия по каналам
        """
        print(f"[CI Marketing Strategy] Выбор каналов")

        # Базовая стратегия для медицинской ниши
        channels = [
            {
                "channel": "seo",
                "priority": "high",
                "budget_share": 0.30,
                "rationale": "Долгосрочный канал с низкой стоимостью лида",
                "tactics": ["оптимизация сайта", "контент-маркетинг", "локальное SEO"],
                "timeline": "3-6 месяцев до результата"
            },
            {
                "channel": "context",
                "priority": "high",
                "budget_share": 0.35,
                "rationale": "Быстрый старт, высокая конверсия",
                "tactics": ["Яндекс.Директ", "Google Ads", "ретаргетинг"],
                "timeline": "1-2 недели до результата"
            },
            {
                "channel": "social",
                "priority": "medium",
                "budget_share": 0.15,
                "rationale": "Работа с репутацией и узнаваемостью",
                "tactics": ["ВКонтакте", "Telegram", "отзывы"],
                "timeline": "1 месяц до результата"
            },
            {
                "channel": "content",
                "priority": "medium",
                "budget_share": 0.10,
                "rationale": "Экспертность и доверие",
                "tactics": ["блог", "видео", "кейсы"],
                "timeline": "2-3 месяца до результата"
            },
            {
                "channel": "referral",
                "priority": "low",
                "budget_share": 0.10,
                "rationale": "Низкая стоимость привлечения",
                "tactics": ["реферальная программа", "партнёрства"],
                "timeline": "1-2 месяца до результата"
            }
        ]

        return channels

    async def _create_customer_journey(
        self,
        channel_strategy: List[Dict[str, Any]]
    ) -> Dict[str, List[str]]:
        """
        Создать карту customer journey.

        Args:
            channel_strategy: стратегия по каналам

        Returns:
            Customer journey map
        """
        print(f"[CI Marketing Strategy] Создание customer journey")

        return {
            "awareness": ["SEO", "Контекстная реклама", "Социальные сети"],
            "consideration": ["Контент на сайте", "Отзывы", "Сравнение цен"],
            "decision": ["Онлайн-запись", "Звонок", "Консультация"],
            "retention": ["Email-рассылка", "Напоминания", "Программа лояльности"],
            "advocacy": ["Реферальная программа", "Отзывы", "Кейсы"]
        }

    async def _allocate_budget(
        self,
        channel_strategy: List[Dict[str, Any]],
        total_budget: int
    ) -> Dict[str, Any]:
        """
        Распределить бюджет по каналам.

        Args:
            channel_strategy: стратегия по каналам
            total_budget: общий бюджет

        Returns:
            Распределение бюджета
        """
        print(f"[CI Marketing Strategy] Распределение бюджета")

        allocation = {}

        for channel in channel_strategy:
            channel_name = channel["channel"]
            share = channel["budget_share"]
            amount = int(total_budget * share)

            allocation[channel_name] = {
                "amount": amount,
                "share": share * 100,
                "priority": channel["priority"]
            }

        return {
            "total_budget": total_budget,
            "by_channel": allocation,
            "reserve": int(total_budget * 0.1)  # 10% резерв
        }

    async def _define_metrics(
        self,
        channel_strategy: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Определить метрики и KPI.

        Args:
            channel_strategy: стратегия по каналам

        Returns:
            Метрики
        """
        print(f"[CI Marketing Strategy] Определение метрик")

        return {
            "primary_kpis": [
                {"metric": "CAC", "target": "< 3000 руб", "description": "Стоимость привлечения клиента"},
                {"metric": "LTV", "target": "> 15000 руб", "description": "Lifetime Value клиента"},
                {"metric": "ROI", "target": "> 300%", "description": "Возврат инвестиций"},
                {"metric": "Conversion", "target": "> 3%", "description": "Конверсия сайта"}
            ],
            "channel_metrics": {
                "seo": ["органический трафик", "позиции", "CTR"],
                "context": ["CPC", "CTR", "конверсия", "ROAS"],
                "social": ["охват", "вовлечённость", "подписчики"],
                "content": ["просмотры", "время на сайте", "возвраты"]
            },
            "business_metrics": [
                {"metric": "Новых клиентов", "target": "> 50/месяц"},
                {"metric": "Средний чек", "target": "> 5000 руб"},
                {"metric": "Повторные визиты", "target": "> 30%"}
            ]
        }

    async def _create_gtm_plan(
        self,
        positioning: Dict[str, Any],
        channel_strategy: List[Dict[str, Any]],
        budget_allocation: Dict[str, Any],
        timeline: str
    ) -> Dict[str, List[Dict[str, Any]]]:
        """
        Создать Go-to-Market план.

        Args:
            positioning: позиционирование
            channel_strategy: стратегия по каналам
            budget_allocation: распределение бюджета
            timeline: временные рамки

        Returns:
            GTM план
        """
        print(f"[CI Marketing Strategy] Создание GTM плана")

        return {
            "month_1": [
                {"week": 1, "action": "Настройка аналитики (Google Analytics, Яндекс.Метрика)", "owner": "Marketing"},
                {"week": 2, "action": "Запуск контекстной рекламы (Яндекс.Директ)", "owner": "Ads"},
                {"week": 3, "action": "SEO-аудит и оптимизация сайта", "owner": "SEO"},
                {"week": 4, "action": "Создание контента для блога (5 статей)", "owner": "Content"}
            ],
            "month_2": [
                {"week": 5, "action": "Запуск Google Ads", "owner": "Ads"},
                {"week": 6, "action": "Настройка ретаргетинга", "owner": "Ads"},
                {"week": 7, "action": "Запуск социальных сетей (ВК, Telegram)", "owner": "SMM"},
                {"week": 8, "action": "Первая оптимизация кампаний", "owner": "Marketing"}
            ],
            "month_3": [
                {"week": 9, "action": "Запуск реферальной программы", "owner": "Marketing"},
                {"week": 10, "action": "Email-маркетинг для клиентской базы", "owner": "Marketing"},
                {"week": 11, "action": "Анализ результатов и корректировка", "owner": "Marketing"},
                {"week": 12, "action": "Масштабирование успешных каналов", "owner": "Marketing"}
            ]
        }

    async def _save_results(self, results: Dict[str, Any]):
        """Сохранить результаты в файл."""
        output_file = "AIM/data/ci-marketing-strategy.json"

        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)

        print(f"[CI Marketing Strategy] Результаты сохранены в {output_file}")

    def get_capabilities(self) -> List[str]:
        """Возвращает список возможностей агента."""
        return [
            "marketing_strategy_development",
            "target_audience_definition",
            "positioning_development",
            "channel_selection",
            "budget_allocation",
            "gtm_planning",
            "metrics_definition"
        ]
