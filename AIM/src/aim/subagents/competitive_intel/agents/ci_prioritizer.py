"""
CI Prioritizer Agent - Insight Prioritization & Action Planning

Приоритизирует инсайты от всех агентов и создаёт action plan:
- Сбор всех инсайтов от Phase 1-8
- Оценка важности и срочности
- Приоритизация по impact/effort матрице
- Создание roadmap действий
- Определение quick wins
"""

from typing import Any, Dict, List
from datetime import datetime
import json

from meai.agents.base_agent import Agent, Task, TaskResult
from meai.memory.obsidian import ObsidianVault


class CIPrioritizerAgent(Agent):
    """CI Prioritizer - агент приоритизации инсайтов и планирования действий."""

    def __init__(
        self,
        agent_id: str,
        database_url: str = "sqlite+aiosqlite:///./data/meai.db",
        vault_path: str = "./obsidian"
    ):
        super().__init__(
            agent_id=agent_id,
            agent_type="ci-prioritizer",
            database_url=database_url,
            vault_path=vault_path
        )
        self.vault = ObsidianVault("AIM/obsidian/ci-prioritizer")

        # Priority levels
        self.priority_levels = {
            "critical": {"score": 4, "label": "Критично"},
            "high": {"score": 3, "label": "Высокий"},
            "medium": {"score": 2, "label": "Средний"},
            "low": {"score": 1, "label": "Низкий"}
        }

        # Impact/Effort matrix
        self.impact_effort_matrix = {
            "quick_wins": {"impact": "high", "effort": "low"},
            "major_projects": {"impact": "high", "effort": "high"},
            "fill_ins": {"impact": "low", "effort": "low"},
            "time_sinks": {"impact": "low", "effort": "high"}
        }

    async def execute_task(self, task: Task) -> TaskResult:
        """
        Выполнить приоритизацию инсайтов.

        Args:
            task: Задача с payload:
                - previous_results: результаты Phase 1-8 (обязательно)
                - business_goals: бизнес-цели (опционально)

        Returns:
            TaskResult с приоритизированным action plan
        """
        try:
            previous_results = task.payload.get("previous_results", {})
            business_goals = task.payload.get("business_goals", [])

            print(f"[CI Prioritizer] Начало приоритизации инсайтов")
            print(f"[CI Prioritizer] DEBUG: previous_results type={type(previous_results).__name__}, keys={list(previous_results.keys())}")

            # Шаг 1: Collect all insights from previous phases
            all_insights = await self._collect_all_insights(previous_results)
            print(f"[CI Prioritizer] Собрано инсайтов: {len(all_insights)}")

            # Шаг 2: Score each insight (impact, effort, urgency)
            scored_insights = await self._score_insights(all_insights, business_goals)

            # Шаг 3: Categorize by impact/effort matrix
            categorized = await self._categorize_by_matrix(scored_insights)

            # Шаг 4: Create prioritized action plan
            action_plan = await self._create_action_plan(categorized)

            # Шаг 5: Identify quick wins
            quick_wins = await self._identify_quick_wins(categorized)

            # Шаг 6: Create roadmap
            roadmap = await self._create_roadmap(action_plan)

            # Шаг 7: Save results
            results = {
                "analysis_date": datetime.now().isoformat(),
                "total_insights": len(all_insights),
                "scored_insights": scored_insights,
                "categorized": categorized,
                "action_plan": action_plan,
                "quick_wins": quick_wins,
                "roadmap": roadmap
            }

            await self._save_results(results)

            print(f"[CI Prioritizer] Приоритизация завершена")
            print(f"[CI Prioritizer] Quick wins: {len(quick_wins)}")
            print(f"[CI Prioritizer] Action items: {len(action_plan)}")

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
            print(f"[CI Prioritizer] Ошибка: {e}")
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

    async def _collect_all_insights(
        self,
        previous_results: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Собрать все инсайты из предыдущих фаз.

        Args:
            previous_results: результаты Phase 1-8
              Keys like 'phase_1' — values are wrapped:
              {phase, agent, status, result: {actual_data}}

        Returns:
            Список всех инсайтов
        """
        print(f"[CI Prioritizer] Сбор инсайтов из предыдущих фаз")

        def _unwrap(key: str) -> dict:
            """Extract inner result dict from wrapped phase data."""
            raw = previous_results.get(key, {})
            if isinstance(raw, dict) and "result" in raw:
                return raw["result"]
            return raw

        all_insights = []

        # ── Phase 1: Scout ──────────────────────────────────────────
        # insights is a DICT: {total_players, fragmentation, dominant_positioning,
        #                      digitalization_level, key_gaps: [str, ...]}
        scout_result = _unwrap("phase_1")
        scout_insights = scout_result.get("insights", {})
        if isinstance(scout_insights, dict):
            # Market structure insights
            for field, label in [
                ("fragmentation", "Фрагментация рынка"),
                ("digitalization_level", "Уровень диджитализации"),
                ("dominant_positioning", "Доминирующее позиционирование"),
            ]:
                val = scout_insights.get(field)
                if val:
                    all_insights.append({
                        "source": "Scout",
                        "phase": 1,
                        "type": "market_structure",
                        "title": label,
                        "description": f"{label}: {val}",
                        "value": val,
                    })
            # Key gaps → individual insights
            for gap in scout_insights.get("key_gaps", []):
                all_insights.append({
                    "source": "Scout",
                    "phase": 1,
                    "type": "market_gap",
                    "title": gap if isinstance(gap, str) else gap.get("title", str(gap)),
                    "description": gap if isinstance(gap, str) else gap.get("description", ""),
                    "value": None,
                })

        # ── Phase 2-3: Auditor ──────────────────────────────────────
        # insights is a DICT: {market_average, dimension_averages, best_competitor,
        #                      worst_competitor, strongest_dimension, weakest_dimension}
        # gaps is a LIST: [{type, dimension, avg_score, opportunity, priority}, ...]
        auditor_result = _unwrap("phase_2")
        auditor_insights = auditor_result.get("insights", {})
        if isinstance(auditor_insights, dict):
            strongest = auditor_insights.get("strongest_dimension")
            weakest = auditor_insights.get("weakest_dimension")
            market_avg = auditor_insights.get("market_average")
            if strongest:
                all_insights.append({
                    "source": "Auditor",
                    "phase": 2,
                    "type": "competitive_advantage",
                    "title": f"Сильнейшее измерение рынка: {strongest}",
                    "description": f"Рынок силён в измерении «{strongest}». Средняя оценка: {market_avg}/100.",
                    "value": strongest,
                })
            if weakest:
                all_insights.append({
                    "source": "Auditor",
                    "phase": 2,
                    "type": "market_opportunity",
                    "title": f"Слабейшее измерение рынка: {weakest}",
                    "description": f"Рынок слаб в измерении «{weakest}». Это ключевая возможность для дифференциации.",
                    "value": weakest,
                })
        # Gaps list (already structured)
        for gap in auditor_result.get("gaps", []):
            all_insights.append({
                "source": "Auditor",
                "phase": 2,
                "type": gap.get("type", "audit_gap"),
                "title": gap.get("dimension", ""),
                "description": gap.get("opportunity", ""),
                "value": gap.get("priority", "medium"),
            })

        # ── Phase 4: Reputation ─────────────────────────────────────
        # insights is a DICT: {market_avg_reputation, market_avg_sentiment,
        #                      best_reputation, worst_reputation, reputation_spread}
        # risks_opportunities: {risks: [...], opportunities: [...]}
        reputation_result = _unwrap("phase_4")
        rep_insights = reputation_result.get("insights", {})
        if isinstance(rep_insights, dict):
            best_rep = rep_insights.get("best_reputation", {})
            worst_rep = rep_insights.get("worst_reputation", {})
            market_avg_rep = rep_insights.get("market_avg_reputation")
            if isinstance(best_rep, dict) and best_rep.get("name"):
                all_insights.append({
                    "source": "Reputation",
                    "phase": 4,
                    "type": "competitive_advantage",
                    "title": f"Лучшая репутация: {best_rep.get('name')}",
                    "description": f"Конкурент с лучшей репутацией: {best_rep.get('name')} "
                                   f"(score: {best_rep.get('score')}, grade: {best_rep.get('grade')}). "
                                   f"Средняя репутация рынка: {market_avg_rep}.",
                    "value": best_rep.get("score"),
                })
            if isinstance(worst_rep, dict) and worst_rep.get("name"):
                all_insights.append({
                    "source": "Reputation",
                    "phase": 4,
                    "type": "market_opportunity",
                    "title": f"Худшая репутация: {worst_rep.get('name')}",
                    "description": f"Конкурент с худшей репутацией: {worst_rep.get('name')} "
                                   f"(score: {worst_rep.get('score')}). Возможность обойти.",
                    "value": worst_rep.get("score"),
                })
        # Risks & opportunities
        ro = reputation_result.get("risks_opportunities", {})
        for opp in ro.get("opportunities", []):
            all_insights.append({
                "source": "Reputation",
                "phase": 4,
                "type": "market_opportunity",
                "title": opp if isinstance(opp, str) else opp.get("title", str(opp)),
                "description": opp if isinstance(opp, str) else opp.get("description", ""),
                "value": None,
            })
        for risk in ro.get("risks", []):
            all_insights.append({
                "source": "Reputation",
                "phase": 4,
                "type": "risk",
                "title": risk if isinstance(risk, str) else risk.get("title", str(risk)),
                "description": risk if isinstance(risk, str) else risk.get("description", ""),
                "value": "high",
            })

        # ── Phase 5: Parallel agents ─────────────────────────────────
        # Each agent's result has insights dict with key_findings list
        phase5_raw = _unwrap("phase_5")
        if isinstance(phase5_raw, dict):
            for agent_name, agent_wrapper in phase5_raw.get("results", {}).items():
                # Unwrap agent result if wrapped
                agent_result = agent_wrapper
                if isinstance(agent_wrapper, dict) and "result" in agent_wrapper:
                    agent_result = agent_wrapper["result"]
                insights = agent_result.get("insights", {})
                if isinstance(insights, dict):
                    for key, value in insights.items():
                        if key == "key_findings" and isinstance(value, list):
                            for finding in value:
                                all_insights.append({
                                    "source": agent_name,
                                    "phase": 5,
                                    "type": "finding",
                                    "title": finding if isinstance(finding, str) else finding.get("title", str(finding)),
                                    "description": finding if isinstance(finding, str) else finding.get("description", ""),
                                    "value": None,
                                })
                        elif key in ("opportunities", "gap_analysis") and isinstance(value, list):
                            for item in value:
                                all_insights.append({
                                    "source": agent_name,
                                    "phase": 5,
                                    "type": "opportunity",
                                    "title": item if isinstance(item, str) else item.get("title", str(item)),
                                    "description": item if isinstance(item, str) else item.get("description", ""),
                                    "value": None,
                                })

        # ── Phase 7-8: Strategist ────────────────────────────────────
        # recommendations is a LIST of dicts: [{priority, category, recommendation,
        #                                       action, impact, effort}, ...]
        strategist_result = _unwrap("phase_7")
        for rec in strategist_result.get("recommendations", []):
            all_insights.append({
                "source": "Strategist",
                "phase": 7,
                "type": "recommendation",
                "title": rec.get("recommendation", rec.get("title", "")),
                "description": rec.get("action", rec.get("description", "")),
                "value": rec.get("priority"),
                "impact_hint": rec.get("impact"),
                "effort_hint": rec.get("effort"),
            })

        print(f"[CI Prioritizer] Всего собрано инсайтов: {len(all_insights)}")
        return all_insights

    async def _score_insights(
        self,
        insights: List[Dict[str, Any]],
        business_goals: List[str]
    ) -> List[Dict[str, Any]]:
        """
        Оценить каждый инсайт по impact, effort, urgency.

        Args:
            insights: список инсайтов
            business_goals: бизнес-цели

        Returns:
            Инсайты с оценками
        """
        print(f"[CI Prioritizer] Оценка инсайтов")

        scored = []

        for insight in insights:
            # Impact (1-10): насколько сильно повлияет на бизнес
            impact = self._calculate_impact(insight, business_goals)

            # Effort (1-10): сколько ресурсов потребуется
            effort = self._calculate_effort(insight)

            # Urgency (1-10): насколько срочно
            urgency = self._calculate_urgency(insight)

            # Total score
            total_score = (impact * 0.5) + (urgency * 0.3) - (effort * 0.2)

            scored.append({
                **insight,
                "impact": impact,
                "effort": effort,
                "urgency": urgency,
                "total_score": round(total_score, 2),
                "priority": self._determine_priority(total_score)
            })

        # Сортировка по total_score
        scored.sort(key=lambda x: x["total_score"], reverse=True)

        return scored

    def _calculate_impact(self, insight: Dict[str, Any], goals: List[str]) -> int:
        """Рассчитать impact (1-10)."""
        # Use strategist's hint if available
        if insight.get("impact_hint"):
            hint = insight["impact_hint"]
            if isinstance(hint, str):
                return {"high": 8, "medium": 5, "low": 3}.get(hint.lower(), 5)
            if isinstance(hint, (int, float)):
                return min(10, max(1, int(hint)))

        impact_by_type = {
            "competitive_advantage": 9,
            "market_opportunity": 8,
            "recommendation": 7,
            "risk": 7,
            "market_gap": 7,
            "opportunity": 6,
            "finding": 5,
            "market_structure": 4,
            "audit_gap": 6,
            "general": 4,
        }

        base_impact = impact_by_type.get(insight.get("type", "general"), 5)

        if goals and any(goal.lower() in insight.get("description", "").lower() for goal in goals):
            base_impact = min(10, base_impact + 2)

        return base_impact

    def _calculate_effort(self, insight: Dict[str, Any]) -> int:
        """Рассчитать effort (1-10)."""
        # Use strategist's hint if available
        if insight.get("effort_hint"):
            hint = insight["effort_hint"]
            if isinstance(hint, str):
                return {"high": 7, "medium": 4, "low": 2}.get(hint.lower(), 4)
            if isinstance(hint, (int, float)):
                return min(10, max(1, int(hint)))

        effort_by_source = {
            "Scout": 3,
            "Auditor": 5,
            "Reputation": 4,
            "Strategist": 7,
            "ci-finance": 6,
            "ci-tech": 5,
            "ci-content": 4,
            "ci-pricing": 4,
            "ci-vacancies": 3,
            "ci-site-crawler": 4,
        }

        return effort_by_source.get(insight.get("source", ""), 5)

    def _calculate_urgency(self, insight: Dict[str, Any]) -> int:
        """Рассчитать urgency (1-10)."""
        urgency_by_type = {
            "competitive_advantage": 9,
            "market_opportunity": 8,
            "recommendation": 7,
            "risk": 8,
            "market_gap": 7,
            "opportunity": 6,
            "finding": 5,
            "market_structure": 3,
            "audit_gap": 6,
            "general": 4,
        }

        return urgency_by_type.get(insight.get("type", "general"), 5)

    def _determine_priority(self, score: float) -> str:
        """Определить уровень приоритета."""
        if score >= 7:
            return "critical"
        elif score >= 5:
            return "high"
        elif score >= 3:
            return "medium"
        else:
            return "low"

    async def _categorize_by_matrix(
        self,
        scored_insights: List[Dict[str, Any]]
    ) -> Dict[str, List[Dict[str, Any]]]:
        """
        Категоризировать по impact/effort матрице.

        Args:
            scored_insights: инсайты с оценками

        Returns:
            Категоризированные инсайты
        """
        print(f"[CI Prioritizer] Категоризация по матрице")

        categorized = {
            "quick_wins": [],      # High impact, Low effort
            "major_projects": [],  # High impact, High effort
            "fill_ins": [],        # Low impact, Low effort
            "time_sinks": []       # Low impact, High effort
        }

        for insight in scored_insights:
            impact = insight["impact"]
            effort = insight["effort"]

            if impact >= 7 and effort <= 4:
                categorized["quick_wins"].append(insight)
            elif impact >= 7 and effort > 4:
                categorized["major_projects"].append(insight)
            elif impact < 7 and effort <= 4:
                categorized["fill_ins"].append(insight)
            else:
                categorized["time_sinks"].append(insight)

        return categorized

    async def _create_action_plan(
        self,
        categorized: Dict[str, List[Dict[str, Any]]]
    ) -> List[Dict[str, Any]]:
        """
        Создать приоритизированный action plan.

        Args:
            categorized: категоризированные инсайты

        Returns:
            Action plan
        """
        print(f"[CI Prioritizer] Создание action plan")

        action_plan = []

        # Приоритет 1: Quick Wins
        for idx, insight in enumerate(categorized["quick_wins"][:5], 1):
            action_plan.append({
                "priority": 1,
                "order": idx,
                "category": "quick_win",
                "title": insight["title"],
                "description": insight["description"],
                "impact": insight["impact"],
                "effort": insight["effort"],
                "estimated_time": "1-2 недели",
                "source": insight["source"]
            })

        # Приоритет 2: Major Projects
        for idx, insight in enumerate(categorized["major_projects"][:3], 1):
            action_plan.append({
                "priority": 2,
                "order": idx,
                "category": "major_project",
                "title": insight["title"],
                "description": insight["description"],
                "impact": insight["impact"],
                "effort": insight["effort"],
                "estimated_time": "1-3 месяца",
                "source": insight["source"]
            })

        # Приоритет 3: Fill-ins
        for idx, insight in enumerate(categorized["fill_ins"][:3], 1):
            action_plan.append({
                "priority": 3,
                "order": idx,
                "category": "fill_in",
                "title": insight["title"],
                "description": insight["description"],
                "impact": insight["impact"],
                "effort": insight["effort"],
                "estimated_time": "1 неделя",
                "source": insight["source"]
            })

        return action_plan

    async def _identify_quick_wins(
        self,
        categorized: Dict[str, List[Dict[str, Any]]]
    ) -> List[Dict[str, Any]]:
        """Определить quick wins."""
        return categorized["quick_wins"][:5]

    async def _create_roadmap(
        self,
        action_plan: List[Dict[str, Any]]
    ) -> Dict[str, List[Dict[str, Any]]]:
        """
        Создать roadmap по временным периодам.

        Args:
            action_plan: action plan

        Returns:
            Roadmap
        """
        print(f"[CI Prioritizer] Создание roadmap")

        roadmap = {
            "month_1": [],
            "month_2_3": [],
            "month_4_6": []
        }

        for action in action_plan:
            if action["category"] == "quick_win":
                roadmap["month_1"].append(action)
            elif action["category"] == "major_project":
                roadmap["month_2_3"].append(action)
            else:
                roadmap["month_4_6"].append(action)

        return roadmap

    async def _save_results(self, results: Dict[str, Any]):
        """Сохранить результаты в файл."""
        output_file = "AIM/data/ci-prioritizer.json"

        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)

        print(f"[CI Prioritizer] Результаты сохранены в {output_file}")

    def get_capabilities(self) -> List[str]:
        """Возвращает список возможностей агента."""
        return [
            "insight_prioritization",
            "impact_effort_analysis",
            "action_planning",
            "quick_wins_identification",
            "roadmap_creation"
        ]
