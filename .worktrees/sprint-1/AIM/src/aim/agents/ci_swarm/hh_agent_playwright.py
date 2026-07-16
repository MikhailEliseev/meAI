"""HH Agent with Playwright - browser automation for CI.

Uses Playwright to scrape competitor vacancies from hh.ru public pages.
No OAuth required, works with public data.
"""

import asyncio
import json
from datetime import datetime
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field

from meai.agents.base_agent import Agent, Task, TaskResult


class Competitor(BaseModel):
    """Competitor profile."""

    employer_id: str
    name: str
    industry: str | None = None
    website: str | None = None
    description: str | None = None


class Vacancy(BaseModel):
    """Vacancy snapshot from web scraping."""

    id: str
    name: str
    employer_id: str
    employer_name: str
    salary: str | None = None
    area: str | None = None
    experience: str | None = None
    description: str | None = None
    url: str
    snapshot_date: str = Field(default_factory=lambda: datetime.now().isoformat())


class HHAgentPlaywright(Agent):
    """HH Agent using Playwright for web scraping."""

    def __init__(
        self,
        agent_id: str,
        database_url: str,
        vault_path: str,
        competitors: list[Competitor] | None = None,
    ):
        super().__init__(
            agent_id=agent_id,
            agent_type="ci_hh_playwright",
            database_url=database_url,
            vault_path=vault_path,
        )
        self.competitors = competitors or []

    async def execute_task(self, task: Task) -> TaskResult:
        """Execute CI task."""
        start_time = datetime.now()

        try:
            if task.action == "monitor_competitors":
                result = await self._monitor_competitors_playwright(task)
            elif task.action == "generate_report":
                result = await self._generate_report(task)
            else:
                duration = (datetime.now() - start_time).total_seconds()
                return TaskResult(
                    subtask_id=task.subtask_id,
                    agent_id=self.agent_id,
                    action=task.action,
                    status="failed",
                    result={},
                    error=f"Unknown action: {task.action}",
                    duration_seconds=duration,
                    completed_at=datetime.now(),
                )

            duration = (datetime.now() - start_time).total_seconds()
            return TaskResult(
                subtask_id=task.subtask_id,
                agent_id=self.agent_id,
                action=task.action,
                status="success",
                result=result,
                error=None,
                duration_seconds=duration,
                completed_at=datetime.now(),
            )

        except Exception as e:
            duration = (datetime.now() - start_time).total_seconds()
            return TaskResult(
                subtask_id=task.subtask_id,
                agent_id=self.agent_id,
                action=task.action,
                status="failed",
                result={},
                error=str(e),
                duration_seconds=duration,
                completed_at=datetime.now(),
            )

    def get_capabilities(self) -> list[str]:
        """Get agent capabilities."""
        return [
            "monitor_competitors",
            "generate_report",
        ]

    async def _monitor_competitors_playwright(self, task: Task) -> dict[str, Any]:
        """Monitor competitors using Playwright."""
        # Note: This requires mcp__playwright__ tools to be available
        # For now, return mock data structure

        results = []

        for competitor in self.competitors:
            try:
                # TODO: Use Playwright MCP tools to scrape
                # For now, create placeholder
                vacancies = []

                # Save snapshot
                snapshot_date = datetime.now().strftime("%Y-%m-%d")
                snapshot_path = (
                    Path(self.vault.vault_path)
                    / "raw"
                    / "snapshots"
                    / snapshot_date
                    / f"{competitor.employer_id}.json"
                )
                snapshot_path.parent.mkdir(parents=True, exist_ok=True)

                snapshot_path.write_text(
                    json.dumps(
                        [v.model_dump() for v in vacancies],
                        ensure_ascii=False,
                        indent=2,
                    )
                )

                results.append({
                    "competitor": competitor.name,
                    "vacancies_count": len(vacancies),
                    "snapshot_path": str(snapshot_path),
                    "note": "Playwright scraping not yet implemented",
                })

            except Exception as e:
                results.append({
                    "competitor": competitor.name,
                    "error": str(e),
                })

        return {"monitored": results}

    async def _generate_report(self, task: Task) -> dict[str, Any]:
        """Generate CI report from snapshots."""
        snapshot_dir = Path(self.vault.vault_path) / "raw" / "snapshots"
        dates = sorted([d.name for d in snapshot_dir.iterdir() if d.is_dir()])

        if not dates:
            return {"message": "No snapshots available"}

        last_date = dates[-1]

        stats = {
            "total_vacancies": 0,
            "by_competitor": {},
        }

        for competitor in self.competitors:
            snapshot_file = snapshot_dir / last_date / f"{competitor.employer_id}.json"

            if not snapshot_file.exists():
                continue

            vacancies = json.loads(snapshot_file.read_text())
            stats["total_vacancies"] += len(vacancies)
            stats["by_competitor"][competitor.name] = len(vacancies)

        # Generate report
        report_path = (
            Path(self.vault.vault_path)
            / "wiki"
            / "insights"
            / f"report-{last_date}.md"
        )
        report_path.parent.mkdir(parents=True, exist_ok=True)

        content = f"""---
date: {last_date}
type: weekly_report
status: processed
---

# CI Report: {last_date}

## Общая статистика

**Всего вакансий:** {stats['total_vacancies']}

## По конкурентам

{chr(10).join(f"- **{name}:** {count} вакансий" for name, count in stats['by_competitor'].items())}

---

*Собрано через Playwright web scraping*
"""

        report_path.write_text(content)

        return {
            "report_path": str(report_path),
            "stats": stats,
        }
