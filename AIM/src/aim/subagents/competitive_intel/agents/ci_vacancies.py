"""
CI Vacancies Agent - HR Intelligence Analysis

Анализирует HR-активность конкурентов:
- Открытые вакансии (hh.ru, Авито)
- Размер команды и структура
- Зарплаты и условия
- Темпы роста команды
"""

from typing import Any, Dict, List, Optional
from datetime import datetime
import json

import httpx

from meai.agents.base_agent import Agent, Task, TaskResult
from meai.events.event_bus import EventBus
from meai.memory.obsidian import ObsidianVault


class CIVacanciesAgent(Agent):
    """
    CI Vacancies - агент анализа HR-активности конкурентов.

    Phase 5 CI pipeline (параллельный агент):
    - Сбор открытых вакансий
    - Оценка размера команды
    - Анализ зарплат и условий
    - Определение темпов роста
    """

    def __init__(
        self,
        agent_id: str,
        database_url: str = "sqlite+aiosqlite:///./data/meai.db",
        vault_path: str = "./obsidian"
    ):
        super().__init__(
            agent_id=agent_id,
            agent_type="ci-vacancies",
            database_url=database_url,
            vault_path=vault_path
        )
        self.vault = ObsidianVault("AIM/obsidian/ci-vacancies")

        # Vacancy sources
        self.sources = {
            "hh": "HeadHunter",
            "avito": "Авито Работа",
            "superjob": "SuperJob",
            "zarplata": "Зарплата.ру"
        }

        # Position categories
        self.position_categories = {
            "medical": "Медицинский персонал",
            "admin": "Администраторы",
            "marketing": "Маркетинг",
            "sales": "Продажи",
            "tech": "IT/Техподдержка",
            "management": "Менеджмент"
        }

    async def execute_task(self, task: Task) -> TaskResult:
        """
        Выполнить анализ вакансий конкурентов.

        Args:
            task: Задача с payload:
                - competitors: список конкурентов (обязательно)
                - niche: ниша (опционально)
                - geo: город (опционально)

        Returns:
            TaskResult с анализом вакансий
        """
        try:
            competitors = task.payload["competitors"]
            niche = task.payload.get("niche", "")
            geo = task.payload.get("geo", "")

            print(f"[CI Vacancies] Начало анализа вакансий {len(competitors)} конкурентов")

            # Шаг 1: Collect vacancies for each competitor
            vacancy_profiles = []
            for competitor in competitors:
                profile = await self._analyze_competitor_vacancies(competitor, niche, geo)
                vacancy_profiles.append(profile)

            # Шаг 2: Market HR analysis
            market_analysis = await self._analyze_market_hr(vacancy_profiles)

            # Шаг 3: Identify hiring leaders
            hiring_leaders = await self._identify_hiring_leaders(vacancy_profiles)

            # Шаг 4: Salary analysis
            salary_analysis = await self._analyze_salaries(vacancy_profiles)

            # Шаг 5: HR insights
            insights = await self._generate_hr_insights(
                vacancy_profiles, market_analysis, hiring_leaders, salary_analysis
            )

            # Шаг 6: Save results
            results = {
                "analysis_date": datetime.now().isoformat(),
                "total_analyzed": len(competitors),
                "niche": niche,
                "geo": geo,
                "vacancy_profiles": vacancy_profiles,
                "market_analysis": market_analysis,
                "hiring_leaders": hiring_leaders,
                "salary_analysis": salary_analysis,
                "insights": insights
            }

            await self._save_results(results)

            print(f"[CI Vacancies] Анализ вакансий завершён для {len(competitors)} конкурентов")

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
            print(f"[CI Vacancies] Ошибка: {e}")
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

    async def _analyze_competitor_vacancies(
        self,
        competitor: Dict[str, Any],
        niche: str,
        geo: str
    ) -> Dict[str, Any]:
        """
        Проанализировать вакансии одного конкурента через hh.ru API.

        Args:
            competitor: данные конкурента
            niche: ниша
            geo: город

        Returns:
            Профиль вакансий конкурента на реальных данных
        """
        name = competitor["name"]
        print(f"[CI Vacancies] Анализ: {name}")

        size = competitor.get("estimated_size", "medium")

        async with httpx.AsyncClient(timeout=httpx.Timeout(15.0)) as client:
            employer = await self._find_employer_on_hh(client, name, geo)

            if employer:
                hh_data = await self._fetch_hh_vacancies(client, employer["id"])

                total_found = hh_data.get("found", 0)
                open_vacancies = min(total_found, 100)
                vacancies_list = hh_data.get("items", [])

                vacancies_by_category: dict[str, int] = {}
                total_salary_by_cat: dict[str, float] = {}
                count_salary_by_cat: dict[str, int] = {}

                for vac in vacancies_list:
                    roles = vac.get("professional_roles", [])
                    for role in roles:
                        role_name = role.get("name", "")
                        cat = self._map_hh_role_to_category(role_name)
                        vacancies_by_category[cat] = vacancies_by_category.get(cat, 0) + 1

                    salary = vac.get("salary")
                    if salary and salary.get("from"):
                        sal_from = salary.get("from") or 0
                        sal_to = salary.get("to") or sal_from
                        avg_sal = (sal_from + sal_to) / 2
                        for role in roles:
                            role_name = role.get("name", "")
                            cat = self._map_hh_role_to_category(role_name)
                            total_salary_by_cat[cat] = total_salary_by_cat.get(cat, 0.0) + avg_sal
                            count_salary_by_cat[cat] = count_salary_by_cat.get(cat, 0) + 1

                avg_salaries = {}
                for cat in vacancies_by_category:
                    if count_salary_by_cat.get(cat, 0) > 0:
                        avg_salaries[cat] = round(total_salary_by_cat[cat] / count_salary_by_cat[cat])

                team_size = employer.get("open_vacancies", 0)
                if team_size == 0:
                    team_size_ranges = {
                        "small": (5, 15),
                        "medium": (15, 50),
                        "large": (50, 200)
                    }
                    low, high = team_size_ranges.get(size, (15, 50))
                    team_size = (low + high) // 2

                vacancy_ratio = open_vacancies / max(team_size, 1)
                if vacancy_ratio > 0.2:
                    growth_rate = "fast"
                elif vacancy_ratio > 0.05:
                    growth_rate = "moderate"
                else:
                    growth_rate = "slow"

                profile = {
                    "name": name,
                    "size": size,
                    "open_vacancies": open_vacancies,
                    "vacancies_list": [
                        {
                            "title": v.get("name", ""),
                            "url": v.get("alternate_url", ""),
                            "salary": v.get("salary"),
                        }
                        for v in vacancies_list[:10]
                    ],
                    "team_size_estimate": team_size,
                    "vacancies_by_category": vacancies_by_category,
                    "avg_salaries": avg_salaries,
                    "growth_rate": growth_rate,
                    "hiring_active": open_vacancies > 0,
                    "sources": ["hh.ru"],
                    "data_source": "hh.ru API",
                    "confidence": 0.8,
                }
            else:
                profile = {
                    "name": name,
                    "size": size,
                    "open_vacancies": None,
                    "vacancies_list": [],
                    "team_size_estimate": None,
                    "vacancies_by_category": {},
                    "avg_salaries": {},
                    "growth_rate": None,
                    "hiring_active": None,
                    "sources": [],
                    "data_source": "unavailable",
                    "confidence": 0.0,
                    "note": f"Компания '{name}' не найдена на hh.ru",
                }

        return profile

    async def _find_employer_on_hh(
        self,
        client: httpx.AsyncClient,
        company_name: str,
        area: str = "",
    ) -> dict | None:
        """Найти работодателя на hh.ru по названию."""
        url = "https://api.hh.ru/employers"
        params: dict[str, Any] = {"text": company_name, "per_page": 5}
        if area:
            params["area"] = area
        try:
            resp = await client.get(url, params=params,
                                    headers={"User-Agent": "AIM-CI/1.0"})
            resp.raise_for_status()
            data = resp.json()
            items = data.get("items", [])
            if items:
                return items[0]
            # Fallback: search by first word of company name
            short_name = company_name.split()[0] if company_name else ""
            if short_name and short_name != company_name:
                params["text"] = short_name
                resp = await client.get(url, params=params,
                                        headers={"User-Agent": "AIM-CI/1.0"})
                resp.raise_for_status()
                data = resp.json()
                items = data.get("items", [])
                if items:
                    return items[0]
        except Exception as e:
            print(f"[CI Vacancies] hh.ru employer search error: {e}")
        return None

    async def _fetch_hh_vacancies(
        self,
        client: httpx.AsyncClient,
        employer_id: str,
    ) -> dict:
        """Получить вакансии работодателя с hh.ru."""
        url = "https://api.hh.ru/vacancies"
        params = {
            "employer_id": employer_id,
            "per_page": 100,
            "only_with_salary": "false",
        }
        resp = await client.get(url, params=params,
                                headers={"User-Agent": "AIM-CI/1.0"})
        resp.raise_for_status()
        return resp.json()

    def _map_hh_role_to_category(self, hh_role_name: str) -> str:
        """Маппинг специализации hh.ru → категория позиции."""
        role_lower = hh_role_name.lower()
        if any(w in role_lower for w in [
            "врач", "медицинск", "доктор", "медсестр", "стоматолог",
            "фельдшер", "косметолог", "массажист",
        ]):
            return "medical"
        elif any(w in role_lower for w in [
            "администрат", "ресепш", "секретар", "оператор",
            "хостес",
        ]):
            return "admin"
        elif any(w in role_lower for w in [
            "маркет", "smm", "seo", "продвижени", "реклам",
            "контент", "копирайт",
        ]):
            return "marketing"
        elif any(w in role_lower for w in [
            "прода", "менеджер по продаж", "торгов",
        ]):
            return "sales"
        elif any(w in role_lower for w in [
            "it", "программист", "разработчик", "техническ",
            "devops", "системный",
        ]):
            return "tech"
        elif any(w in role_lower for w in [
            "управл", "директор", "руководител", "начальник",
        ]):
            return "management"
        return "other"

    async def _analyze_market_hr(
        self,
        vacancy_profiles: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Проанализировать HR-активность рынка.

        Args:
            vacancy_profiles: профили вакансий

        Returns:
            Анализ рынка
        """
        print(f"[CI Vacancies] Анализ HR-активности рынка")

        total_vacancies = sum(p["open_vacancies"] for p in vacancy_profiles)
        avg_vacancies = total_vacancies / len(vacancy_profiles)

        hiring_companies = sum(1 for p in vacancy_profiles if p["hiring_active"])
        hiring_rate = (hiring_companies / len(vacancy_profiles)) * 100

        # Средний размер команды
        avg_team_size = sum(p["team_size_estimate"] for p in vacancy_profiles) / len(vacancy_profiles)

        # Самые востребованные категории
        category_demand = {}
        for profile in vacancy_profiles:
            for category, count in profile["vacancies_by_category"].items():
                category_demand[category] = category_demand.get(category, 0) + count

        most_demanded = sorted(category_demand.items(), key=lambda x: x[1], reverse=True)[:3]

        market_analysis = {
            "total_open_vacancies": total_vacancies,
            "avg_vacancies_per_company": round(avg_vacancies, 1),
            "hiring_companies_percent": round(hiring_rate, 1),
            "avg_team_size": round(avg_team_size),
            "most_demanded_positions": [
                {"category": cat, "count": count} for cat, count in most_demanded
            ]
        }

        return market_analysis

    async def _identify_hiring_leaders(
        self,
        vacancy_profiles: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Определить лидеров по найму.

        Args:
            vacancy_profiles: профили вакансий

        Returns:
            Лидеры по найму
        """
        print(f"[CI Vacancies] Определение лидеров по найму")

        # Сортировка по количеству вакансий
        sorted_profiles = sorted(
            vacancy_profiles,
            key=lambda x: x["open_vacancies"],
            reverse=True
        )

        # TOP-3
        leaders = sorted_profiles[:3]

        return [
            {
                "name": p["name"],
                "open_vacancies": p["open_vacancies"],
                "growth_rate": p["growth_rate"],
                "team_size": p["team_size_estimate"]
            }
            for p in leaders if p["open_vacancies"] > 0
        ]

    async def _analyze_salaries(
        self,
        vacancy_profiles: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Проанализировать зарплаты.

        Args:
            vacancy_profiles: профили вакансий

        Returns:
            Анализ зарплат
        """
        print(f"[CI Vacancies] Анализ зарплат")

        # Агрегировать зарплаты по категориям
        salary_by_category = {}

        for profile in vacancy_profiles:
            for category, salary in profile["avg_salaries"].items():
                if category not in salary_by_category:
                    salary_by_category[category] = []
                salary_by_category[category].append(salary)

        # Средние зарплаты по категориям
        avg_salaries = {}
        for category, salaries in salary_by_category.items():
            if salaries:
                avg_salaries[category] = {
                    "avg": round(sum(salaries) / len(salaries)),
                    "min": min(salaries),
                    "max": max(salaries)
                }

        return {
            "avg_salaries_by_category": avg_salaries,
            "highest_paying_category": max(avg_salaries.items(), key=lambda x: x[1]["avg"])[0] if avg_salaries else None
        }

    async def _generate_hr_insights(
        self,
        vacancy_profiles: List[Dict[str, Any]],
        market_analysis: Dict[str, Any],
        hiring_leaders: List[Dict[str, Any]],
        salary_analysis: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Сгенерировать HR-инсайты.

        Args:
            vacancy_profiles: профили вакансий
            market_analysis: анализ рынка
            hiring_leaders: лидеры по найму
            salary_analysis: анализ зарплат

        Returns:
            Инсайты
        """
        print(f"[CI Vacancies] Генерация HR-инсайтов")

        insights = {
            "market_activity": "high" if market_analysis["hiring_companies_percent"] > 50 else "medium" if market_analysis["hiring_companies_percent"] > 25 else "low",
            "competition_for_talent": "high" if market_analysis["total_open_vacancies"] > 20 else "medium" if market_analysis["total_open_vacancies"] > 10 else "low",
            "key_findings": []
        }

        # Ключевые находки
        if market_analysis["hiring_companies_percent"] > 60:
            insights["key_findings"].append("Высокая HR-активность (>60% компаний нанимают)")

        if len(hiring_leaders) > 0:
            top_leader = hiring_leaders[0]
            insights["key_findings"].append(f"{top_leader['name']} активно растёт ({top_leader['open_vacancies']} вакансий)")

        if salary_analysis.get("highest_paying_category"):
            insights["key_findings"].append(f"Самые высокие зарплаты в категории: {salary_analysis['highest_paying_category']}")

        return insights

    async def _save_results(self, results: Dict[str, Any]):
        """Сохранить результаты в файл."""
        output_file = "AIM/data/ci-vacancies.json"

        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)

        print(f"[CI Vacancies] Результаты сохранены в {output_file}")

    def get_capabilities(self) -> List[str]:
        """Возвращает список возможностей агента."""
        return [
            "vacancy_collection",
            "team_size_estimation",
            "salary_analysis",
            "hiring_velocity_analysis",
            "hr_market_analysis"
        ]
