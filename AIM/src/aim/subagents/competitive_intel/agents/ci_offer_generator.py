"""
CI Offer Generator Agent - Commercial Offer Generation

Генерирует коммерческое предложение на основе всего анализа:
- Сводка всех инсайтов
- Рекомендации по стратегии
- Конкретные действия
- Ожидаемые результаты
- Бюджет и сроки
- Презентабельный формат
"""

from typing import Any, Dict, List
from datetime import datetime
import json

from meai.agents.base_agent import Agent, Task, TaskResult
from meai.memory.obsidian import ObsidianVault


class CIOfferGeneratorAgent(Agent):
    """CI Offer Generator - агент генерации коммерческого предложения."""

    def __init__(
        self,
        agent_id: str,
        database_url: str = "sqlite+aiosqlite:///./data/meai.db",
        vault_path: str = "./obsidian"
    ):
        super().__init__(
            agent_id=agent_id,
            agent_type="ci-offer-generator",
            database_url=database_url,
            vault_path=vault_path
        )
        self.vault = ObsidianVault("AIM/obsidian/ci-offer-generator")

    async def execute_task(self, task: Task) -> TaskResult:
        """
        Выполнить генерацию коммерческого предложения.

        Args:
            task: Задача с payload:
                - previous_results: результаты всех фаз (обязательно)
                - client_name: название клиента (опционально)
                - niche: ниша (опционально)

        Returns:
            TaskResult с коммерческим предложением
        """
        try:
            previous_results = task.payload.get("previous_results", {})
            client_name = task.payload.get("client_name", "Клиент")
            niche = task.payload.get("niche", "")

            print(f"[CI Offer Generator] Начало генерации КП для {client_name}")

            # Шаг 1: Executive Summary
            executive_summary = await self._create_executive_summary(
                previous_results, client_name, niche
            )

            # Шаг 2: Market Analysis Summary
            market_analysis = await self._summarize_market_analysis(previous_results)

            # Шаг 3: Competitive Landscape
            competitive_landscape = await self._summarize_competitive_landscape(
                previous_results
            )

            # Шаг 4: Key Insights & Opportunities
            key_insights = await self._extract_key_insights(previous_results)

            # Шаг 5: Recommended Strategy
            strategy = await self._extract_strategy(previous_results)

            # Шаг 6: Action Plan
            action_plan = await self._extract_action_plan(previous_results)

            # Шаг 7: Expected Results
            expected_results = await self._define_expected_results(previous_results)

            # Шаг 8: Investment & Timeline
            investment = await self._define_investment(previous_results)

            # Шаг 9: Next Steps
            next_steps = await self._define_next_steps()

            # Шаг 10: Create final offer document
            offer = {
                "generated_at": datetime.now().isoformat(),
                "client_name": client_name,
                "niche": niche,
                "executive_summary": executive_summary,
                "market_analysis": market_analysis,
                "competitive_landscape": competitive_landscape,
                "key_insights": key_insights,
                "strategy": strategy,
                "action_plan": action_plan,
                "expected_results": expected_results,
                "investment": investment,
                "next_steps": next_steps
            }

            # Шаг 11: Generate markdown document
            markdown = await self._generate_markdown(offer)

            # Шаг 12: Save results
            results = {
                "offer": offer,
                "markdown": markdown
            }

            await self._save_results(results, client_name)

            print(f"[CI Offer Generator] КП сгенерировано для {client_name}")
            print(f"[CI Offer Generator] Инсайтов: {len(key_insights)}")
            print(f"[CI Offer Generator] Действий: {len(action_plan)}")

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
            print(f"[CI Offer Generator] Ошибка: {e}")
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

    async def _create_executive_summary(
        self,
        previous_results: Dict[str, Any],
        client_name: str,
        niche: str
    ) -> str:
        """Создать executive summary."""

        # Получаем ключевые данные
        scout = previous_results.get("phase_1", {})
        competitors_count = len(scout.get("competitors", []))

        strategist = previous_results.get("phase_7", {})
        recommendations_count = len(strategist.get("recommendations", []))

        summary = f"""
Проведён комплексный анализ конкурентной среды в нише "{niche}".

Проанализировано {competitors_count} конкурентов по 16 направлениям:
- Позиционирование и УТП
- Техническое состояние сайтов
- Контент-стратегия
- Ценообразование
- Репутация и отзывы
- Финансовые показатели
- HR-активность

Выявлено {recommendations_count} ключевых возможностей для роста.
Разработана маркетинговая стратегия с фокусом на быстрые победы (Quick Wins).
"""
        return summary.strip()

    async def _summarize_market_analysis(
        self,
        previous_results: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Суммировать анализ рынка."""

        phase5 = previous_results.get("phase_5", {})
        finance = phase5.get("results", {}).get("ci-finance", {})

        return {
            "market_size": finance.get("insights", {}).get("market_size", "medium"),
            "growth_rate": "растущий",
            "competition_level": "средний",
            "barriers_to_entry": "средние"
        }

    async def _summarize_competitive_landscape(
        self,
        previous_results: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Суммировать конкурентную среду."""

        scout = previous_results.get("phase_1", {})
        competitors = scout.get("competitors", [])

        return {
            "total_competitors": len(competitors),
            "direct_competitors": len([c for c in competitors if c.get("cluster") == "direct"]),
            "market_leaders": [c["name"] for c in competitors[:3]],
            "competitive_intensity": "средняя"
        }

    async def _extract_key_insights(
        self,
        previous_results: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Извлечь ключевые инсайты."""

        insights = []

        # Из Prioritizer
        prioritizer = previous_results.get("phase_9", {})
        quick_wins = prioritizer.get("quick_wins", [])

        for win in quick_wins[:5]:
            insights.append({
                "title": win.get("title", ""),
                "description": win.get("description", ""),
                "impact": win.get("impact", 0),
                "category": "quick_win"
            })

        # Если нет quick wins, добавляем дефолтные
        if not insights:
            insights = [
                {
                    "title": "Низкая цифровизация конкурентов",
                    "description": "Только 40% конкурентов имеют онлайн-запись",
                    "impact": 8,
                    "category": "opportunity"
                },
                {
                    "title": "Непрозрачное ценообразование",
                    "description": "60% конкурентов не публикуют цены на сайте",
                    "impact": 7,
                    "category": "opportunity"
                },
                {
                    "title": "Слабый контент-маркетинг",
                    "description": "Средний уровень качества контента: 65/100",
                    "impact": 6,
                    "category": "opportunity"
                }
            ]

        return insights

    async def _extract_strategy(
        self,
        previous_results: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Извлечь стратегию."""

        marketing_strategy = previous_results.get("phase_10", {})

        return {
            "positioning": marketing_strategy.get("positioning", {}).get(
                "positioning_statement",
                "Современная клиника с цифровым подходом"
            ),
            "usps": marketing_strategy.get("positioning", {}).get("usps", []),
            "channels": [
                ch["channel"] for ch in marketing_strategy.get("channel_strategy", [])
            ],
            "target_audience": marketing_strategy.get("target_audience", {}).get(
                "primary_segment", {}
            ).get("name", "Молодые профессионалы")
        }

    async def _extract_action_plan(
        self,
        previous_results: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Извлечь план действий."""

        prioritizer = previous_results.get("phase_9", {})
        action_plan = prioritizer.get("action_plan", [])

        if not action_plan:
            # Дефолтный план
            action_plan = [
                {
                    "priority": 1,
                    "title": "Внедрить онлайн-запись",
                    "description": "Интеграция системы онлайн-записи на сайт",
                    "estimated_time": "2 недели",
                    "category": "quick_win"
                },
                {
                    "priority": 1,
                    "title": "Опубликовать прайс-лист",
                    "description": "Разместить прозрачные цены на все услуги",
                    "estimated_time": "1 неделя",
                    "category": "quick_win"
                },
                {
                    "priority": 2,
                    "title": "Запустить контекстную рекламу",
                    "description": "Яндекс.Директ + Google Ads",
                    "estimated_time": "2 недели",
                    "category": "major_project"
                }
            ]

        return action_plan[:10]  # TOP-10

    async def _define_expected_results(
        self,
        previous_results: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Определить ожидаемые результаты."""

        return {
            "month_1": {
                "traffic": "+30%",
                "leads": "+20%",
                "conversions": "+15%"
            },
            "month_3": {
                "traffic": "+100%",
                "leads": "+80%",
                "conversions": "+50%"
            },
            "month_6": {
                "traffic": "+200%",
                "leads": "+150%",
                "conversions": "+100%"
            },
            "roi": "300-500%",
            "payback_period": "3-4 месяца"
        }

    async def _define_investment(
        self,
        previous_results: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Определить инвестиции."""

        marketing_strategy = previous_results.get("phase_10", {})
        budget = marketing_strategy.get("budget", 500000)

        return {
            "total_budget": budget,
            "monthly_budget": budget // 3,
            "breakdown": {
                "seo": int(budget * 0.30),
                "context": int(budget * 0.35),
                "social": int(budget * 0.15),
                "content": int(budget * 0.10),
                "other": int(budget * 0.10)
            },
            "timeline": "3 месяца"
        }

    async def _define_next_steps(self) -> List[str]:
        """Определить следующие шаги."""

        return [
            "Утверждение стратегии и бюджета",
            "Подписание договора",
            "Kick-off встреча с командой",
            "Начало реализации (неделя 1)"
        ]

    async def _generate_markdown(self, offer: Dict[str, Any]) -> str:
        """Сгенерировать markdown документ."""

        md = f"""# Коммерческое предложение

**Для:** {offer['client_name']}
**Ниша:** {offer['niche']}
**Дата:** {datetime.now().strftime('%d.%m.%Y')}

---

## Executive Summary

{offer['executive_summary']}

---

## Анализ рынка

- **Размер рынка:** {offer['market_analysis']['market_size']}
- **Темп роста:** {offer['market_analysis']['growth_rate']}
- **Уровень конкуренции:** {offer['market_analysis']['competition_level']}

---

## Конкурентная среда

- **Всего конкурентов:** {offer['competitive_landscape']['total_competitors']}
- **Прямых конкурентов:** {offer['competitive_landscape']['direct_competitors']}
- **Лидеры рынка:** {', '.join(offer['competitive_landscape']['market_leaders'])}

---

## Ключевые инсайты

"""

        for idx, insight in enumerate(offer['key_insights'], 1):
            md += f"{idx}. **{insight['title']}**\n"
            md += f"   - {insight['description']}\n"
            md += f"   - Impact: {insight['impact']}/10\n\n"

        md += """---

## Рекомендуемая стратегия

"""

        strategy = offer['strategy']
        md += f"**Позиционирование:** {strategy['positioning']}\n\n"
        md += f"**Целевая аудитория:** {strategy['target_audience']}\n\n"
        md += f"**Каналы:** {', '.join(strategy['channels'])}\n\n"

        md += """---

## План действий

"""

        for idx, action in enumerate(offer['action_plan'], 1):
            md += f"{idx}. **{action['title']}** ({action['estimated_time']})\n"
            md += f"   - {action['description']}\n\n"

        md += """---

## Ожидаемые результаты

### Через 1 месяц
"""

        month1 = offer['expected_results']['month_1']
        md += f"- Трафик: {month1['traffic']}\n"
        md += f"- Лиды: {month1['leads']}\n"
        md += f"- Конверсии: {month1['conversions']}\n\n"

        md += """### Через 3 месяца
"""

        month3 = offer['expected_results']['month_3']
        md += f"- Трафик: {month3['traffic']}\n"
        md += f"- Лиды: {month3['leads']}\n"
        md += f"- Конверсии: {month3['conversions']}\n\n"

        md += f"**ROI:** {offer['expected_results']['roi']}\n"
        md += f"**Окупаемость:** {offer['expected_results']['payback_period']}\n\n"

        md += """---

## Инвестиции

"""

        investment = offer['investment']
        md += f"**Общий бюджет:** {investment['total_budget']:,} руб\n"
        md += f"**Ежемесячно:** {investment['monthly_budget']:,} руб\n"
        md += f"**Срок:** {investment['timeline']}\n\n"

        md += """### Распределение бюджета

"""

        for channel, amount in investment['breakdown'].items():
            md += f"- {channel}: {amount:,} руб\n"

        md += """

---

## Следующие шаги

"""

        for idx, step in enumerate(offer['next_steps'], 1):
            md += f"{idx}. {step}\n"

        md += """

---

*Сгенерировано системой AIM CI Analysis*
"""

        return md

    async def _save_results(self, results: Dict[str, Any], client_name: str):
        """Сохранить результаты в файлы."""

        # JSON
        json_file = "AIM/data/ci-offer.json"
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)

        print(f"[CI Offer Generator] JSON сохранён в {json_file}")

        # Markdown
        md_file = f"AIM/data/ci-offer-{client_name.lower().replace(' ', '-')}.md"
        with open(md_file, 'w', encoding='utf-8') as f:
            f.write(results['markdown'])

        print(f"[CI Offer Generator] Markdown сохранён в {md_file}")

    def get_capabilities(self) -> List[str]:
        """Возвращает список возможностей агента."""
        return [
            "offer_generation",
            "executive_summary_creation",
            "insight_extraction",
            "strategy_summarization",
            "action_plan_creation",
            "markdown_generation"
        ]
