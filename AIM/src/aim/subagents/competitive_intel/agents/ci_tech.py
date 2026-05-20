"""
DEPRECATED: Use ci_tech_real.py instead.

Kept for reference. Orchestrator uses CITechAgent from ci_tech_real.
This module contains mock/random data and is no longer wired into the CI pipeline.
"""

# fmt: off
_OLD_DOC = """
CI Tech Agent - Technology Stack Analysis

Анализирует технологический стек конкурентов:
- Используемые технологии (frontend, backend, infrastructure)
- CMS и платформы
- Аналитика и маркетинговые инструменты
- Уровень технологической зрелости

DEPRECATED: Use ci_tech_real.py instead.
Kept for reference. Orchestrator uses CITechAgent from ci_tech_real.
"""

from typing import Any, Dict, List, Optional
from datetime import datetime
import json
import random

from meai.agents.base_agent import Agent, Task, TaskResult
from meai.events.event_bus import EventBus
from meai.memory.obsidian import ObsidianVault


class CITechAgent(Agent):
    """CI Tech - агент анализа технологического стека."""

    def __init__(self, agent_id: str, database_url: str = "sqlite+aiosqlite:///./data/meai.db", vault_path: str = "./obsidian"):
        super().__init__(agent_id=agent_id, agent_type="ci-tech", database_url=database_url, vault_path=vault_path)
        self.vault = ObsidianVault("AIM/obsidian/ci-tech")

    async def execute_task(self, task: Task) -> TaskResult:
        try:
            competitors = task.payload["competitors"]
            print(f"[CI Tech] Анализ tech stack {len(competitors)} конкурентов")

            tech_profiles = [await self._analyze_tech(c) for c in competitors]
            market_tech = await self._analyze_market_tech(tech_profiles)
            insights = await self._generate_tech_insights(tech_profiles, market_tech)

            results = {
                "analysis_date": datetime.now().isoformat(),
                "total_analyzed": len(competitors),
                "tech_profiles": tech_profiles,
                "market_tech": market_tech,
                "insights": insights
            }

            await self._save_results(results)
            print(f"[CI Tech] Анализ завершён")

            return TaskResult(subtask_id=task.subtask_id, agent_id=self.agent_id, action=task.action,
                            status="success", result=results, error=None, duration_seconds=0.0, completed_at=datetime.now())
        except Exception as e:
            return TaskResult(subtask_id=task.subtask_id, agent_id=self.agent_id, action=task.action,
                            status="failed", result={"error": str(e)}, error=str(e), duration_seconds=0.0, completed_at=datetime.now())

    async def _analyze_tech(self, competitor: Dict[str, Any]) -> Dict[str, Any]:
        # TODO: Реальный анализ через Wappalyzer, BuiltWith
        cms_options = ["WordPress", "Tilda", "1C-Bitrix", "Custom", "Wix"]
        analytics = random.sample(["Google Analytics", "Яндекс.Метрика", "Google Tag Manager"], k=random.randint(1, 3))

        return {
            "name": competitor["name"],
            "cms": random.choice(cms_options),
            "frontend": random.choice(["React", "Vue", "jQuery", "Vanilla JS"]),
            "analytics": analytics,
            "has_online_booking": random.choice([True, False]),
            "has_chat": random.choice([True, False]),
            "tech_maturity": random.choice(["low", "medium", "high"])
        }

    async def _analyze_market_tech(self, profiles: List[Dict[str, Any]]) -> Dict[str, Any]:
        cms_usage = {}
        for p in profiles:
            cms = p["cms"]
            cms_usage[cms] = cms_usage.get(cms, 0) + 1

        return {
            "most_popular_cms": max(cms_usage.items(), key=lambda x: x[1])[0],
            "online_booking_adoption": sum(1 for p in profiles if p["has_online_booking"]) / len(profiles) * 100,
            "chat_adoption": sum(1 for p in profiles if p["has_chat"]) / len(profiles) * 100
        }

    async def _generate_tech_insights(self, profiles: List[Dict[str, Any]], market: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "digitalization_level": "high" if market["online_booking_adoption"] > 50 else "medium" if market["online_booking_adoption"] > 25 else "low",
            "key_findings": [
                f"Самая популярная CMS: {market['most_popular_cms']}",
                f"Онлайн-запись: {market['online_booking_adoption']:.0f}% компаний"
            ]
        }

    async def _save_results(self, results: Dict[str, Any]):
        with open("AIM/data/ci-tech.json", 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)

    def get_capabilities(self) -> List[str]:
        return ["tech_stack_analysis", "cms_detection", "analytics_detection", "tech_maturity_assessment"]
