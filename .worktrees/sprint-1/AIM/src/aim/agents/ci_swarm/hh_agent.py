"""HeadHunter Competitive Intelligence Agent.

Monitors competitor vacancies on hh.ru to track:
- Open positions (business directions)
- Tech stack requirements (technology trends)
- Salary ranges (market rates)
- Hiring dynamics (growth indicators)
"""

import asyncio
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

import httpx
from pydantic import BaseModel, Field

from meai.agents.base_agent import Agent, Task, TaskResult
from meai.memory.obsidian import ObsidianVault


class Competitor(BaseModel):
    """Competitor profile."""

    employer_id: str
    name: str
    industry: str | None = None
    website: str | None = None
    description: str | None = None


class Vacancy(BaseModel):
    """Vacancy snapshot."""

    id: str
    name: str
    employer_id: str
    employer_name: str
    salary_from: int | None = None
    salary_to: int | None = None
    salary_currency: str | None = None
    area: str | None = None
    experience: str | None = None
    employment: str | None = None
    schedule: str | None = None
    description: str | None = None
    key_skills: list[str] = Field(default_factory=list)
    published_at: str
    url: str
    snapshot_date: str = Field(default_factory=lambda: datetime.now().isoformat())


class VacancyChange(BaseModel):
    """Detected change in vacancy."""

    change_type: str  # new, closed, updated
    vacancy_id: str
    vacancy_name: str
    employer_name: str
    details: dict[str, Any]
    detected_at: str = Field(default_factory=lambda: datetime.now().isoformat())


class HHAgent(Agent):
    """HeadHunter competitive intelligence agent."""

    def __init__(
        self,
        agent_id: str,
        database_url: str,
        vault_path: str,
        competitors: list[Competitor] | None = None,
        access_token: str | None = None,
    ):
        super().__init__(
            agent_id=agent_id,
            agent_type="ci_hh",
            database_url=database_url,
            vault_path=vault_path,
        )
        self.competitors = competitors or []
        self.base_url = "https://api.hh.ru"
        self.user_agent = "AIM-CI-Agent/1.0 (me@mikhaileliseev.com)"
        self.access_token = access_token or self._load_token_from_env()

    def _load_token_from_env(self) -> str | None:
        """Load access token from environment variable."""
        import os
        from pathlib import Path

        # Try to load from .env file
        env_file = Path(__file__).parent.parent.parent.parent / ".env"
        if env_file.exists():
            for line in env_file.read_text().splitlines():
                if line.startswith("HH_ACCESS_TOKEN="):
                    return line.split("=", 1)[1].strip()

        # Fallback to environment variable
        return os.getenv("HH_ACCESS_TOKEN")

    async def execute_task(self, task: Task) -> TaskResult:
        """Execute CI task."""
        start_time = datetime.now()

        try:
            if task.action == "monitor_competitors":
                result = await self._monitor_competitors(task)
            elif task.action == "analyze_vacancy":
                result = await self._analyze_vacancy(task)
            elif task.action == "detect_changes":
                result = await self._detect_changes(task)
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
            "analyze_vacancy",
            "detect_changes",
            "generate_report",
        ]

    async def _monitor_competitors(self, task: Task) -> dict[str, Any]:
        """Monitor all competitors and collect vacancy snapshots."""
        results = []

        async with httpx.AsyncClient() as client:
            for competitor in self.competitors:
                try:
                    vacancies = await self._fetch_vacancies(
                        client,
                        competitor.employer_id,
                    )

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

                    import json
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
                    })

                except Exception as e:
                    results.append({
                        "competitor": competitor.name,
                        "error": str(e),
                    })

        return {"monitored": results}

    async def _fetch_vacancies(
        self,
        client: httpx.AsyncClient,
        employer_id: str,
    ) -> list[Vacancy]:
        """Fetch all vacancies for employer."""
        vacancies = []
        page = 0
        per_page = 100

        # Prepare headers
        headers = {"HH-User-Agent": self.user_agent}
        if self.access_token:
            headers["Authorization"] = f"Bearer {self.access_token}"

        while True:
            response = await client.get(
                f"{self.base_url}/vacancies",
                params={
                    "employer_id": employer_id,
                    "page": page,
                    "per_page": per_page,
                },
                headers=headers,
            )
            response.raise_for_status()
            data = response.json()

            for item in data.get("items", []):
                # Fetch full vacancy details
                detail_response = await client.get(
                    f"{self.base_url}/vacancies/{item['id']}",
                    headers=headers,
                )
                detail_response.raise_for_status()
                detail = detail_response.json()

                vacancy = Vacancy(
                    id=detail["id"],
                    name=detail["name"],
                    employer_id=detail["employer"]["id"],
                    employer_name=detail["employer"]["name"],
                    salary_from=detail.get("salary", {}).get("from") if detail.get("salary") else None,
                    salary_to=detail.get("salary", {}).get("to") if detail.get("salary") else None,
                    salary_currency=detail.get("salary", {}).get("currency") if detail.get("salary") else None,
                    area=detail.get("area", {}).get("name"),
                    experience=detail.get("experience", {}).get("name"),
                    employment=detail.get("employment", {}).get("name"),
                    schedule=detail.get("schedule", {}).get("name"),
                    description=detail.get("description"),
                    key_skills=[s["name"] for s in detail.get("key_skills", [])],
                    published_at=detail["published_at"],
                    url=detail["alternate_url"],
                )
                vacancies.append(vacancy)

                # Rate limiting
                await asyncio.sleep(0.1)

            # Check if there are more pages
            if page >= data.get("pages", 0) - 1:
                break
            page += 1

        return vacancies

    async def _analyze_vacancy(self, task: Task) -> dict[str, Any]:
        """Analyze single vacancy and extract insights."""
        vacancy_id = task.description  # Assuming vacancy_id is in description

        # Prepare headers
        headers = {"HH-User-Agent": self.user_agent}
        if self.access_token:
            headers["Authorization"] = f"Bearer {self.access_token}"

        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/vacancies/{vacancy_id}",
                headers=headers,
            )
            response.raise_for_status()
            data = response.json()

        # Extract insights
        insights = {
            "tech_stack": data.get("key_skills", []),
            "salary_range": {
                "from": data.get("salary", {}).get("from"),
                "to": data.get("salary", {}).get("to"),
                "currency": data.get("salary", {}).get("currency"),
            } if data.get("salary") else None,
            "experience_required": data.get("experience", {}).get("name"),
            "employment_type": data.get("employment", {}).get("name"),
        }

        # Save to wiki
        wiki_path = (
            Path(self.vault.vault_path)
            / "wiki"
            / "vacancies"
            / f"{vacancy_id}.md"
        )
        wiki_path.parent.mkdir(parents=True, exist_ok=True)

        content = f"""---
vacancy_id: {vacancy_id}
name: {data['name']}
employer: {data['employer']['name']}
analyzed_at: {datetime.now().isoformat()}
status: processed
---

# {data['name']}

**Работодатель:** {data['employer']['name']}

## Требования

**Опыт:** {insights['experience_required']}
**Занятость:** {insights['employment_type']}

## Технологии

{chr(10).join(f"- {skill['name']}" for skill in data.get('key_skills', []))}

## Зарплата

{f"От {insights['salary_range']['from']} до {insights['salary_range']['to']} {insights['salary_range']['currency']}" if insights['salary_range'] else "Не указана"}

## Ссылка

{data['alternate_url']}
"""

        wiki_path.write_text(content)

        return {"insights": insights, "wiki_path": str(wiki_path)}

    async def _detect_changes(self, task: Task) -> dict[str, Any]:
        """Detect changes between snapshots."""
        import json

        snapshot_dir = Path(self.vault.vault_path) / "raw" / "snapshots"
        dates = sorted([d.name for d in snapshot_dir.iterdir() if d.is_dir()])

        if len(dates) < 2:
            return {"message": "Not enough snapshots to compare"}

        # Compare last two snapshots
        prev_date = dates[-2]
        curr_date = dates[-1]

        changes: list[VacancyChange] = []

        for competitor in self.competitors:
            prev_file = snapshot_dir / prev_date / f"{competitor.employer_id}.json"
            curr_file = snapshot_dir / curr_date / f"{competitor.employer_id}.json"

            if not prev_file.exists() or not curr_file.exists():
                continue

            prev_vacancies = {
                v["id"]: v
                for v in json.loads(prev_file.read_text())
            }
            curr_vacancies = {
                v["id"]: v
                for v in json.loads(curr_file.read_text())
            }

            # Detect new vacancies
            for vid in curr_vacancies.keys() - prev_vacancies.keys():
                v = curr_vacancies[vid]
                changes.append(VacancyChange(
                    change_type="new",
                    vacancy_id=vid,
                    vacancy_name=v["name"],
                    employer_name=v["employer_name"],
                    details={"skills": v.get("key_skills", [])},
                ))

            # Detect closed vacancies
            for vid in prev_vacancies.keys() - curr_vacancies.keys():
                v = prev_vacancies[vid]
                changes.append(VacancyChange(
                    change_type="closed",
                    vacancy_id=vid,
                    vacancy_name=v["name"],
                    employer_name=v["employer_name"],
                    details={},
                ))

        # Save changes to wiki
        if changes:
            alert_path = (
                Path(self.vault.vault_path)
                / "wiki"
                / "alerts"
                / f"{curr_date}.md"
            )
            alert_path.parent.mkdir(parents=True, exist_ok=True)

            content = f"""---
date: {curr_date}
changes_count: {len(changes)}
status: processed
---

# Изменения за {curr_date}

"""

            for change in changes:
                content += f"\n## {change.change_type.upper()}: {change.vacancy_name}\n"
                content += f"**Работодатель:** {change.employer_name}\n"
                content += f"**ID:** {change.vacancy_id}\n"
                if change.details:
                    content += f"**Детали:** {change.details}\n"

            alert_path.write_text(content)

        return {
            "changes_count": len(changes),
            "changes": [c.model_dump() for c in changes],
        }

    async def _generate_report(self, task: Task) -> dict[str, Any]:
        """Generate weekly CI report."""
        import json

        snapshot_dir = Path(self.vault.vault_path) / "raw" / "snapshots"
        dates = sorted([d.name for d in snapshot_dir.iterdir() if d.is_dir()])

        if not dates:
            return {"message": "No snapshots available"}

        # Analyze last snapshot
        last_date = dates[-1]

        stats = {
            "total_vacancies": 0,
            "by_competitor": {},
            "top_skills": {},
            "salary_ranges": [],
        }

        for competitor in self.competitors:
            snapshot_file = snapshot_dir / last_date / f"{competitor.employer_id}.json"

            if not snapshot_file.exists():
                continue

            vacancies = json.loads(snapshot_file.read_text())
            stats["total_vacancies"] += len(vacancies)
            stats["by_competitor"][competitor.name] = len(vacancies)

            # Collect skills
            for v in vacancies:
                for skill in v.get("key_skills", []):
                    stats["top_skills"][skill] = stats["top_skills"].get(skill, 0) + 1

            # Collect salaries
            for v in vacancies:
                if v.get("salary_from") or v.get("salary_to"):
                    stats["salary_ranges"].append({
                        "from": v.get("salary_from"),
                        "to": v.get("salary_to"),
                        "currency": v.get("salary_currency"),
                    })

        # Sort top skills
        top_skills = sorted(
            stats["top_skills"].items(),
            key=lambda x: x[1],
            reverse=True,
        )[:10]

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

## Топ-10 технологий

{chr(10).join(f"{i+1}. **{skill}** — {count} упоминаний" for i, (skill, count) in enumerate(top_skills))}

## Зарплатные диапазоны

Собрано {len(stats['salary_ranges'])} вакансий с указанием зарплаты.

"""

        report_path.write_text(content)

        return {
            "report_path": str(report_path),
            "stats": stats,
        }
