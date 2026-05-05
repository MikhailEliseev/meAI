"""
CI Strategist Agent - Strategic Synthesis and Recommendations

Синтезирует данные от всех CI агентов и генерирует:
- Стратегические рекомендации
- Конкурентные преимущества
- Позиционирование
- Go-to-market стратегию
"""

from typing import Any, Dict, List, Optional
from datetime import datetime
import json

from meai.agents.base_agent import Agent, Task, TaskResult
from meai.events.event_bus import EventBus
from meai.memory.obsidian import ObsidianVault


class CIStrategistAgent(Agent):
    """
    CI Strategist - агент стратегического синтеза.

    Фаза 7-8 CI pipeline:
    - Синтез данных от Scout, Auditor, Reputation и других агентов
    - Генерация стратегических рекомендаций
    - Определение конкурентных преимуществ
    - Разработка позиционирования и GTM стратегии
    """

    def __init__(
        self,
        agent_id: str,
        database_url: str = "sqlite+aiosqlite:///./data/meai.db",
        vault_path: str = "./obsidian"
    ):
        super().__init__(
            agent_id=agent_id,
            agent_type="ci-strategist",
            database_url=database_url,
            vault_path=vault_path
        )
        # Переопределяем vault на специфичный для CI Strategist
        self.vault = ObsidianVault("AIM/obsidian/ci-strategist")

        # Strategy frameworks
        self.frameworks = {
            "positioning": {
                "name": "Позиционирование",
                "dimensions": ["price", "quality", "service", "innovation", "trust"]
            },
            "differentiation": {
                "name": "Дифференциация",
                "types": ["product", "service", "channel", "brand", "price"]
            },
            "competitive_advantage": {
                "name": "Конкурентное преимущество",
                "sources": ["cost", "differentiation", "focus", "innovation"]
            },
            "gtm": {
                "name": "Go-to-Market",
                "components": ["target_segment", "value_prop", "channels", "pricing", "messaging"]
            }
        }

        # Recommendation priorities
        self.priorities = {
            "critical": "Критично для успеха",
            "high": "Высокий приоритет",
            "medium": "Средний приоритет",
            "low": "Низкий приоритет"
        }

    async def execute_task(self, task: Task) -> TaskResult:
        """
        Выполнить стратегический синтез.

        Args:
            task: Задача с payload:
                - previous_results: результаты от предыдущих агентов (обязательно)
                - client_context: контекст клиента (опционально)

        Returns:
            TaskResult со стратегическими рекомендациями
        """
        try:
            previous_results = task.payload.get("previous_results", {})
            client_context = task.payload.get("client_context", {})

            # Логирование начала
            print(f"[CI Strategist] Начало стратегического синтеза")

            # Шаг 1: Extract insights from all previous phases
            insights = await self._extract_insights(previous_results)

            # Шаг 2: Analyze competitive landscape
            landscape = await self._analyze_landscape(insights)

            # Шаг 3: Identify strategic opportunities
            opportunities = await self._identify_opportunities(insights, landscape)

            # Шаг 4: Generate positioning recommendations
            positioning = await self._generate_positioning(insights, opportunities, client_context)

            # Шаг 5: Generate differentiation strategy
            differentiation = await self._generate_differentiation(insights, opportunities)

            # Шаг 6: Generate competitive advantages
            advantages = await self._generate_advantages(insights, opportunities)

            # Шаг 7: Generate GTM strategy
            gtm = await self._generate_gtm(positioning, differentiation, advantages)

            # Шаг 8: Prioritize recommendations
            recommendations = await self._prioritize_recommendations(
                positioning, differentiation, advantages, gtm
            )

            # Шаг 9: Save results
            results = {
                "synthesis_date": datetime.now().isoformat(),
                "insights": insights,
                "landscape": landscape,
                "opportunities": opportunities,
                "positioning": positioning,
                "differentiation": differentiation,
                "competitive_advantages": advantages,
                "gtm_strategy": gtm,
                "recommendations": recommendations
            }

            await self._save_results(results)

            # Логирование завершения
            print(f"[CI Strategist] Стратегический синтез завершён")

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
            print(f"[CI Strategist] Ошибка: {e}")
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

    async def _extract_insights(
        self,
        previous_results: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Извлечь инсайты из результатов предыдущих фаз.

        Args:
            previous_results: результаты от Scout, Auditor, Reputation и др.

        Returns:
            Агрегированные инсайты
        """
        print(f"[CI Strategist] Извлечение инсайтов из {len(previous_results)} фаз")

        insights = {
            "market": {},
            "competitors": {},
            "gaps": {},
            "strengths": {},
            "weaknesses": {}
        }

        # Извлечь market insights
        if "phase_1" in previous_results:  # Scout
            scout_data = previous_results["phase_1"]
            insights["market"] = {
                "total_players": scout_data.get("insights", {}).get("total_players", 0),
                "fragmentation": scout_data.get("insights", {}).get("fragmentation", "unknown"),
                "dominant_positioning": scout_data.get("insights", {}).get("dominant_positioning", "unknown")
            }

        # Извлечь competitor insights
        if "phase_2" in previous_results:  # Auditor
            auditor_data = previous_results["phase_2"]
            insights["competitors"]["audit"] = {
                "market_average": auditor_data.get("insights", {}).get("market_average", 0),
                "best_competitor": auditor_data.get("insights", {}).get("best_competitor", {}),
                "weakest_dimension": auditor_data.get("insights", {}).get("weakest_dimension", "unknown")
            }

        if "phase_4" in previous_results:  # Reputation
            reputation_data = previous_results["phase_4"]
            insights["competitors"]["reputation"] = {
                "market_avg_reputation": reputation_data.get("insights", {}).get("market_avg_reputation", 0),
                "best_reputation": reputation_data.get("insights", {}).get("best_reputation", {}),
                "reputation_spread": reputation_data.get("insights", {}).get("reputation_spread", 0)
            }

        # Извлечь gaps
        if "phase_2" in previous_results:
            auditor_data = previous_results["phase_2"]
            insights["gaps"]["audit"] = auditor_data.get("gaps", [])

        if "phase_4" in previous_results:
            reputation_data = previous_results["phase_4"]
            insights["gaps"]["reputation"] = reputation_data.get("risks_opportunities", {}).get("opportunities", [])

        return insights

    async def _analyze_landscape(
        self,
        insights: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Проанализировать конкурентный ландшафт.

        Args:
            insights: агрегированные инсайты

        Returns:
            Анализ ландшафта
        """
        print(f"[CI Strategist] Анализ конкурентного ландшафта")

        landscape = {
            "market_maturity": self._assess_market_maturity(insights),
            "competitive_intensity": self._assess_competitive_intensity(insights),
            "entry_barriers": self._assess_entry_barriers(insights),
            "key_success_factors": self._identify_key_success_factors(insights)
        }

        return landscape

    def _assess_market_maturity(self, insights: Dict[str, Any]) -> str:
        """Оценить зрелость рынка."""
        total_players = insights.get("market", {}).get("total_players", 0)
        fragmentation = insights.get("market", {}).get("fragmentation", "unknown")

        if total_players > 15 and fragmentation == "высокая":
            return "mature"
        elif total_players > 8:
            return "growing"
        else:
            return "emerging"

    def _assess_competitive_intensity(self, insights: Dict[str, Any]) -> str:
        """Оценить интенсивность конкуренции."""
        total_players = insights.get("market", {}).get("total_players", 0)

        if total_players > 15:
            return "high"
        elif total_players > 8:
            return "medium"
        else:
            return "low"

    def _assess_entry_barriers(self, insights: Dict[str, Any]) -> str:
        """Оценить барьеры входа."""
        # Упрощённая логика
        market_avg = insights.get("competitors", {}).get("audit", {}).get("market_average", 0)

        if market_avg > 80:
            return "high"
        elif market_avg > 65:
            return "medium"
        else:
            return "low"

    def _identify_key_success_factors(self, insights: Dict[str, Any]) -> List[str]:
        """Определить ключевые факторы успеха."""
        factors = []

        # На основе audit gaps
        audit_gaps = insights.get("gaps", {}).get("audit", [])
        for gap in audit_gaps[:3]:  # TOP-3
            if gap.get("type") == "market_gap":
                factors.append(f"Сильный {gap.get('dimension')}")

        # На основе reputation
        reputation_gaps = insights.get("gaps", {}).get("reputation", [])
        for gap in reputation_gaps[:2]:  # TOP-2
            if gap.get("type") == "competitor_weakness":
                factors.append(f"Качество {gap.get('topic')}")

        return factors if factors else ["Качество услуг", "Репутация", "Цифровизация"]

    async def _identify_opportunities(
        self,
        insights: Dict[str, Any],
        landscape: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Определить стратегические возможности.

        Args:
            insights: агрегированные инсайты
            landscape: анализ ландшафта

        Returns:
            Список возможностей
        """
        print(f"[CI Strategist] Определение стратегических возможностей")

        opportunities = []

        # Возможности из audit gaps
        audit_gaps = insights.get("gaps", {}).get("audit", [])
        for gap in audit_gaps:
            if gap.get("priority") in ["high", "critical"]:
                opportunities.append({
                    "type": "market_gap",
                    "source": "audit",
                    "dimension": gap.get("dimension"),
                    "description": gap.get("opportunity"),
                    "priority": gap.get("priority")
                })

        # Возможности из reputation gaps
        reputation_gaps = insights.get("gaps", {}).get("reputation", [])
        for gap in reputation_gaps[:5]:  # TOP-5
            opportunities.append({
                "type": "competitor_weakness",
                "source": "reputation",
                "competitor": gap.get("competitor"),
                "topic": gap.get("topic"),
                "description": gap.get("description"),
                "priority": "medium"
            })

        return opportunities

    async def _generate_positioning(
        self,
        insights: Dict[str, Any],
        opportunities: List[Dict[str, Any]],
        client_context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Сгенерировать рекомендации по позиционированию.

        Args:
            insights: агрегированные инсайты
            opportunities: возможности
            client_context: контекст клиента

        Returns:
            Рекомендации по позиционированию
        """
        print(f"[CI Strategist] Генерация позиционирования")

        # Определить оптимальное позиционирование на основе gaps
        positioning_dimensions = {}

        for opp in opportunities:
            if opp["type"] == "market_gap":
                dimension = opp["dimension"]
                positioning_dimensions[dimension] = {
                    "strength": "high",
                    "rationale": opp["description"]
                }

        positioning = {
            "recommended_position": "Цифровой лидер с высоким качеством",
            "dimensions": positioning_dimensions,
            "target_segment": client_context.get("target_audience", "Средний+ сегмент"),
            "value_proposition": "Современные технологии + персональный подход"
        }

        return positioning

    async def _generate_differentiation(
        self,
        insights: Dict[str, Any],
        opportunities: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Сгенерировать стратегию дифференциации.

        Args:
            insights: агрегированные инсайты
            opportunities: возможности

        Returns:
            Стратегия дифференциации
        """
        print(f"[CI Strategist] Генерация дифференциации")

        differentiation = {
            "primary": {
                "type": "service",
                "description": "Онлайн-запись + персональный менеджер",
                "rationale": "Рынок слаб в цифровизации"
            },
            "secondary": {
                "type": "quality",
                "description": "Прозрачность процесса + гарантии",
                "rationale": "Конкуренты получают критику за коммуникацию"
            },
            "supporting": [
                {
                    "type": "channel",
                    "description": "Telegram-бот для записи и консультаций"
                },
                {
                    "type": "brand",
                    "description": "Современный бренд с акцентом на технологии"
                }
            ]
        }

        return differentiation

    async def _generate_advantages(
        self,
        insights: Dict[str, Any],
        opportunities: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Сгенерировать конкурентные преимущества.

        Args:
            insights: агрегированные инсайты
            opportunities: возможности

        Returns:
            Список конкурентных преимуществ
        """
        print(f"[CI Strategist] Генерация конкурентных преимуществ")

        advantages = [
            {
                "advantage": "Полная цифровизация",
                "source": "innovation",
                "description": "Онлайн-запись, Telegram-бот, личный кабинет",
                "sustainability": "high",
                "rationale": "Конкуренты отстают в цифровизации на 2-3 года"
            },
            {
                "advantage": "Прозрачность и доверие",
                "source": "differentiation",
                "description": "Открытые цены, гарантии, отзывы с фото",
                "sustainability": "medium",
                "rationale": "Конкуренты получают критику за непрозрачность"
            },
            {
                "advantage": "Скорость обслуживания",
                "source": "focus",
                "description": "Запись за 2 минуты, быстрый ответ в чате",
                "sustainability": "medium",
                "rationale": "Конкуренты медленно отвечают и долго записывают"
            }
        ]

        return advantages

    async def _generate_gtm(
        self,
        positioning: Dict[str, Any],
        differentiation: Dict[str, Any],
        advantages: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Сгенерировать Go-to-Market стратегию.

        Args:
            positioning: позиционирование
            differentiation: дифференциация
            advantages: конкурентные преимущества

        Returns:
            GTM стратегия
        """
        print(f"[CI Strategist] Генерация GTM стратегии")

        gtm = {
            "target_segment": positioning["target_segment"],
            "value_proposition": positioning["value_proposition"],
            "channels": [
                {
                    "channel": "SEO",
                    "priority": "high",
                    "rationale": "Основной канал привлечения в нише"
                },
                {
                    "channel": "Яндекс.Директ",
                    "priority": "high",
                    "rationale": "Быстрый старт, высокая конверсия"
                },
                {
                    "channel": "Telegram",
                    "priority": "medium",
                    "rationale": "Дифференциация через бот"
                },
                {
                    "channel": "VK",
                    "priority": "medium",
                    "rationale": "Органический охват + таргет"
                }
            ],
            "pricing": {
                "strategy": "value-based",
                "position": "mid-premium",
                "rationale": "Качество выше среднего, цена справедливая"
            },
            "messaging": {
                "core": "Современная клиника с заботой о вас",
                "supporting": [
                    "Запись за 2 минуты",
                    "Прозрачные цены",
                    "Гарантии качества"
                ]
            }
        }

        return gtm

    async def _prioritize_recommendations(
        self,
        positioning: Dict[str, Any],
        differentiation: Dict[str, Any],
        advantages: List[Dict[str, Any]],
        gtm: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Приоритизировать рекомендации.

        Args:
            positioning: позиционирование
            differentiation: дифференциация
            advantages: конкурентные преимущества
            gtm: GTM стратегия

        Returns:
            Приоритизированный список рекомендаций
        """
        print(f"[CI Strategist] Приоритизация рекомендаций")

        recommendations = [
            {
                "priority": "critical",
                "category": "positioning",
                "recommendation": f"Позиционирование: {positioning['recommended_position']}",
                "action": "Разработать бренд-платформу и коммуникационную стратегию",
                "impact": "high",
                "effort": "medium"
            },
            {
                "priority": "critical",
                "category": "differentiation",
                "recommendation": f"Дифференциация: {differentiation['primary']['description']}",
                "action": "Внедрить онлайн-запись и персонального менеджера",
                "impact": "high",
                "effort": "high"
            },
            {
                "priority": "high",
                "category": "gtm",
                "recommendation": "Запуск через SEO + Яндекс.Директ",
                "action": "Создать SEO-оптимизированный сайт и настроить контекстную рекламу",
                "impact": "high",
                "effort": "medium"
            },
            {
                "priority": "high",
                "category": "advantage",
                "recommendation": advantages[0]["advantage"],
                "action": advantages[0]["description"],
                "impact": "high",
                "effort": "high"
            },
            {
                "priority": "medium",
                "category": "channel",
                "recommendation": "Telegram-бот для записи",
                "action": "Разработать и запустить Telegram-бот",
                "impact": "medium",
                "effort": "medium"
            }
        ]

        return recommendations

    async def _save_results(self, results: Dict[str, Any]):
        """Сохранить результаты в файл."""
        output_file = "AIM/data/ci-strategy.json"

        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)

        print(f"[CI Strategist] Результаты сохранены в {output_file}")

    def get_capabilities(self) -> List[str]:
        """Возвращает список возможностей агента."""
        return [
            "strategic_synthesis",
            "positioning_strategy",
            "differentiation_strategy",
            "competitive_advantage_identification",
            "gtm_strategy",
            "recommendation_prioritization"
        ]
