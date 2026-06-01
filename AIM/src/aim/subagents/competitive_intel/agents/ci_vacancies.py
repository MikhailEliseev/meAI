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
import os
import re
import asyncio

import httpx

from meai.agents.base_agent import Agent, Task, TaskResult
from meai.memory.obsidian import ObsidianVault


class CIVacanciesAgent(Agent):
    """
    CI Vacancies - агент анализа HR-активности конкурентов.

    Phase 5 CI pipeline (параллельный агент):
    - Сбор открытых вакансий (hh.ru API → Brave Search fallback)
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
        self.brave_api_key = os.getenv("BRAVE_API_KEY")
        self.brave_base_url = "https://api.search.brave.com/res/v1/web/search"

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
        Проанализировать вакансии одного конкурента.
        Методы: hh.ru API → Brave Search → DuckDuckGo Lite.
        """
        name = competitor["name"]
        print(f"[CI Vacancies] Анализ: {name}")

        size = competitor.get("estimated_size", "medium")

        async with httpx.AsyncClient(timeout=httpx.Timeout(15.0)) as client:
            # Method 1: hh.ru API
            employer = await self._find_employer_on_hh(client, name, geo)

            if employer:
                hh_data = await self._fetch_hh_vacancies(client, employer["id"])
                total_found = hh_data.get("found", 0)
                if total_found > 0:
                    return self._build_profile_from_hh(name, size, employer, hh_data)

            # Method 2: Brave Search fallback
            brave_data = await self._search_vacancies_brave(client, name)
            if brave_data and brave_data.get("open_vacancies", 0) is not None:
                return brave_data

            # Method 3: DuckDuckGo Lite (free, no API key)
            ddg_data = await self._search_vacancies_duckduckgo(client, name, size)
            if ddg_data and ddg_data.get("open_vacancies", 0) is not None:
                return ddg_data

        # Method 3: Unavailable
        return {
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
            "note": f"Не удалось получить данные о вакансиях для '{name}'",
        }

    def _build_profile_from_hh(
        self, name: str, size: str, employer: dict, hh_data: dict
    ) -> Dict[str, Any]:
        """Build vacancy profile from hh.ru API data."""
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

        # Estimate team size from vacancy count (proxy method)
        if open_vacancies <= 2:
            team_size = 8
        elif open_vacancies <= 8:
            team_size = 25
        elif open_vacancies <= 30:
            team_size = 80
        else:
            team_size = min(open_vacancies * 2, 500)

        vacancy_ratio = open_vacancies / max(team_size, 1)
        if vacancy_ratio > 0.2:
            growth_rate = "fast"
        elif vacancy_ratio > 0.05:
            growth_rate = "moderate"
        else:
            growth_rate = "slow"

        return {
            "name": name, "size": size,
            "open_vacancies": open_vacancies,
            "vacancies_list": [
                {"title": v.get("name", ""), "url": v.get("alternate_url", ""), "salary": v.get("salary")}
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

    async def _search_vacancies_brave(
        self, client: httpx.AsyncClient, company_name: str
    ) -> Dict[str, Any] | None:
        """Search for company vacancies via Brave Search API."""
        if not self.brave_api_key:
            return None
        try:
            headers = {
                "Accept": "application/json",
                "Accept-Encoding": "gzip",
                "X-Subscription-Token": self.brave_api_key,
            }
            # Search hh.ru for this company
            query = f"{company_name} вакансии site:hh.ru"
            params = {"q": query, "count": 10, "search_lang": "ru", "country": "RU"}
            resp = await client.get(self.brave_base_url, params=params, headers=headers)
            resp.raise_for_status()
            data = resp.json()

            web_results = data.get("web", {}).get("results", [])

            # Count unique company vacancy pages
            vacancy_urls: set[str] = set()
            vacancy_titles: list[dict] = []
            estimated_count = 0

            for r in web_results:
                url = r.get("url", "")
                title = r.get("title", "")
                description = r.get("description", "")

                # hh.ru vacancy URLs contain "vacancy/"
                if "hh.ru/vacancy/" in url:
                    vacancy_urls.add(url)
                    vacancy_titles.append({"title": title, "url": url})

                # Try to extract total vacancy count from snippets
                # Pattern: "Найдено 23 вакансии" or "23 вакансии"
                count_match = re.search(
                    r'(?:найдено|найдено|открыто|активных)\s*(\d+)\s*(?:ваканси|vacanc)',
                    description, re.IGNORECASE
                )
                if count_match:
                    estimated_count = max(estimated_count, int(count_match.group(1)))

                # Also check title for count
                count_match2 = re.search(
                    r'(\d+)\s*(?:ваканси|vacanc)',
                    title, re.IGNORECASE
                )
                if count_match2:
                    estimated_count = max(estimated_count, int(count_match2.group(1)))

            open_count = estimated_count or len(vacancy_urls)

            # Second attempt: broader search if no results
            if open_count == 0:
                query2 = f"{company_name} работа вакансии врач косметолог"
                params2 = {"q": query2, "count": 5, "search_lang": "ru", "country": "RU"}
                resp2 = await client.get(self.brave_base_url, params=params2, headers=headers)
                resp2.raise_for_status()
                data2 = resp2.json()
                for r in data2.get("web", {}).get("results", []):
                    desc = r.get("description", "")
                    cm = re.search(r'(\d+)\s*(?:ваканси|vacanc)', desc, re.IGNORECASE)
                    if cm:
                        open_count = max(open_count, int(cm.group(1)))

            # Filter vacancies: keep only those where company name (or part) appears in title
            company_words = [w.lower() for w in re.findall(r'[A-Za-zА-Яа-я]+', company_name) if len(w) > 2]
            filtered_titles = []
            for vt in vacancy_titles:
                title_lower = vt["title"].lower()
                # Check if at least 2 company words match (or 1 for short names)
                match_threshold = 1 if len(company_words) <= 2 else 2
                matches = sum(1 for w in company_words if w in title_lower)
                if matches >= match_threshold:
                    filtered_titles.append(vt)
            if not filtered_titles:
                filtered_titles = vacancy_titles[:3]

            # Parse salaries from snippets
            salaries = []
            for r in web_results:
                desc = r.get("description", "")
                salary_match = re.findall(
                    r'(\d[\d\s]*)\s*(?:000|тыс|тысяч|₽|руб|р\.)',
                    desc, re.IGNORECASE
                )
                for s in salary_match:
                    try:
                        amount = int(s.replace(' ', ''))
                        if 20 <= amount <= 500:
                            salaries.append(amount)
                    except ValueError:
                        pass
            avg_salary = sum(salaries) // len(salaries) if salaries else None

            # Classify vacancies by category
            categories = {
                "врачи": ["врач", "доктор", "хирург", "дерматолог", "косметолог", "терапевт"],
                "медсёстры": ["медсестра", "медбрат", "сестринск", "медицинская сестра"],
                "администраторы": ["администратор", "менеджер", "управляющий", "директор"],
                "маркетинг": ["маркетолог", "smm", "seo", "таргет", "продвижени", "реклам"],
            }
            by_category = {cat: 0 for cat in categories}
            for vt in vacancy_titles:
                title_lower = vt["title"].lower()
                for cat, keywords in categories.items():
                    if any(kw in title_lower for kw in keywords):
                        by_category[cat] += 1
                        break

            # Estimate team size from vacancy count (proxy method)
            if open_count <= 2:
                size = "small"
                team_size = 8
            elif open_count <= 8:
                size = "medium"
                team_size = 25
            elif open_count <= 30:
                size = "large"
                team_size = 80
            else:
                size = "enterprise"
                team_size = min(open_count * 2, 500)

            vacancy_ratio = open_count / max(team_size, 1)
            if vacancy_ratio > 0.2:
                growth_rate = "fast"
            elif vacancy_ratio > 0.05:
                growth_rate = "moderate"
            else:
                growth_rate = "slow"

            print(f"[CI Vacancies] Brave found ~{open_count} vacancies for {company_name} (size={size}, team={team_size})")

            return {
                "name": company_name,
                "size": size,
                "open_vacancies": open_count,
                "vacancies_list": filtered_titles[:10],
                "team_size_estimate": team_size,
                "vacancies_by_category": {k: v for k, v in by_category.items() if v > 0},
                "avg_salaries": {"avg_monthly_rub": avg_salary} if avg_salary else {},
                "growth_rate": growth_rate,
                "hiring_active": open_count > 0,
                "sources": ["brave_search"],
                "data_source": "brave_search",
                "confidence": 0.6 if company_words and filtered_titles else 0.4,
            }

        except Exception as e:
            print(f"[CI Vacancies] Brave search error for {company_name}: {e}")
            return None

    async def _search_vacancies_duckduckgo(
        self, client: httpx.AsyncClient, company_name: str, size: str
    ) -> Dict[str, Any] | None:
        """Search for company vacancies via DuckDuckGo Lite (free, no API key)."""
        try:
            headers = {
                "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
            }
            query = f"{company_name} вакансии site:hh.ru"
            params = {"q": query}
            resp = await client.get(
                "https://lite.duckduckgo.com/lite/",
                params=params, headers=headers
            )
            if resp.status_code != 200:
                return None

            html = resp.text

            # DDG Lite HTML structure:
            # <tr class="result-snippet"><td>snippet</td></tr>
            # <tr class="result-link"><td><a href="url">title</a></td></tr>
            snippets = []
            snippet_matches = re.findall(
                r'<tr[^>]*class="result-snippet"[^>]*>.*?<td[^>]*>(.*?)</td>.*?</tr>',
                html, re.DOTALL | re.IGNORECASE
            )
            for s in snippet_matches[:5]:
                clean = re.sub(r'<[^>]+>', '', s).strip()
                if clean and len(clean) > 15:
                    snippets.append(clean)

            # Extract vacancy count from snippets
            open_count = 0
            all_text = " ".join(snippets)
            count_match = re.search(
                r'(\d+)\s*(?:ваканси|vacanc)', all_text, re.IGNORECASE
            )
            if count_match:
                open_count = int(count_match.group(1))
            else:
                # Count unique hh.ru vacancy URLs
                link_matches = re.findall(
                    r'<a[^>]*href="(https?://[^"]*hh\.ru/vacancy/[^"]*)"[^>]*>',
                    html, re.IGNORECASE
                )
                open_count = len(set(link_matches))

            if open_count == 0:
                # Try broader search
                query2 = f"{company_name} работа вакансии"
                params2 = {"q": query2}
                resp2 = await client.get(
                    "https://lite.duckduckgo.com/lite/",
                    params=params2, headers=headers
                )
                if resp2.status_code == 200:
                    html2 = resp2.text
                    cm = re.search(r'(\d+)\s*(?:ваканси|vacanc)', html2, re.IGNORECASE)
                    if cm:
                        open_count = int(cm.group(1))

            if open_count == 0:
                return None

            # Estimate team size from vacancy count
            if open_count <= 2:
                estimated_size = "small"
                team_size = 8
            elif open_count <= 8:
                estimated_size = "medium"
                team_size = 25
            elif open_count <= 30:
                estimated_size = "large"
                team_size = 80
            else:
                estimated_size = "enterprise"
                team_size = min(open_count * 2, 500)

            vacancy_ratio = open_count / max(team_size, 1)
            if vacancy_ratio > 0.2:
                growth_rate = "fast"
            elif vacancy_ratio > 0.05:
                growth_rate = "moderate"
            else:
                growth_rate = "slow"

            print(f"[CI Vacancies] DuckDuckGo found ~{open_count} vacancies for {company_name} (size={estimated_size}, team={team_size})")

            return {
                "name": company_name,
                "size": estimated_size,
                "open_vacancies": open_count,
                "vacancies_list": [],
                "team_size_estimate": team_size,
                "vacancies_by_category": {},
                "avg_salaries": {},
                "growth_rate": growth_rate,
                "hiring_active": open_count > 0,
                "sources": ["duckduckgo"],
                "data_source": "duckduckgo_lite",
                "confidence": 0.4,
            }

        except Exception as e:
            print(f"[CI Vacancies] DuckDuckGo error for {company_name}: {e}")
            return None

    # hh.ru area ID mapping
    HH_AREA_IDS = {
        "москва": "1",
        "мск": "1",
        "moscow": "1",
        "санкт-петербург": "2",
        "спб": "2",
        "питер": "2",
        "екатеринбург": "3",
        "новосибирск": "4",
        "казань": "88",
        "нижний новгород": "66",
        "краснодар": "53",
        "ростов-на-дону": "76",
        "ростов": "76",
        "челябинск": "104",
        "самара": "78",
        "уфа": "99",
        "омск": "68",
        "пермь": "72",
        "воронеж": "26",
        "волгоград": "24",
    }

    # Rotating User-Agent pool to avoid IP-based blocking
    _USER_AGENTS = [
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36",
        "AIM-CI/1.0 (aim@iamaim.ru)",
    ]

    def _hh_headers(self) -> dict:
        """Build browser-like headers for hh.ru API requests."""
        # Cycle through User-Agents deterministically (no random import)
        import time
        idx = int(time.time() * 1000) % len(self._USER_AGENTS)
        ua = self._USER_AGENTS[idx]
        return {
            "User-Agent": ua,
            "Accept": "application/json, text/plain, */*",
            "Accept-Language": "ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7",
            "Accept-Encoding": "gzip, deflate, br",
            "Referer": "https://hh.ru/",
            "Origin": "https://hh.ru",
            "Connection": "keep-alive",
        }

    async def _hh_request(
        self, client: httpx.AsyncClient, url: str, params: dict, retries: int = 2
    ) -> httpx.Response | None:
        """Make hh.ru API request with retry on 403."""
        last_error = None
        for attempt in range(retries + 1):
            try:
                headers = self._hh_headers()
                resp = await client.get(url, params=params, headers=headers)
                if resp.status_code == 403:
                    last_error = f"403 Forbidden (attempt {attempt + 1})"
                    if attempt < retries:
                        await asyncio.sleep(1.0 * (attempt + 1))
                    continue
                resp.raise_for_status()
                return resp
            except httpx.HTTPStatusError as e:
                if e.response.status_code == 403:
                    last_error = f"403 Forbidden (attempt {attempt + 1})"
                    if attempt < retries:
                        await asyncio.sleep(1.0 * (attempt + 1))
                    continue
                last_error = str(e)
                break
            except Exception as e:
                last_error = str(e)
                if attempt < retries:
                    await asyncio.sleep(0.5 * (attempt + 1))
                else:
                    break
        if last_error:
            print(f"[CI Vacancies] hh.ru request failed: {last_error}")
        return None

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
            area_id = self.HH_AREA_IDS.get(area.lower().strip(), "")
            if area_id:
                params["area"] = area_id
        resp = await self._hh_request(client, url, params)
        if resp:
            data = resp.json()
            items = data.get("items", [])
            if items:
                return items[0]
            # Fallback: search by first word
            short_name = company_name.split()[0] if company_name else ""
            if short_name and short_name != company_name:
                params["text"] = short_name
                resp2 = await self._hh_request(client, url, params)
                if resp2:
                    data2 = resp2.json()
                    items2 = data2.get("items", [])
                    if items2:
                        return items2[0]
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
        resp = await self._hh_request(client, url, params)
        if resp:
            return resp.json()
        # Return empty structure on failure
        return {"found": 0, "items": []}

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

        total_vacancies = sum(p["open_vacancies"] or 0 for p in vacancy_profiles)
        avg_vacancies = total_vacancies / len(vacancy_profiles) if vacancy_profiles else 0

        hiring_companies = sum(1 for p in vacancy_profiles if p.get("hiring_active"))
        hiring_rate = (hiring_companies / len(vacancy_profiles)) * 100 if vacancy_profiles else 0

        # Средний размер команды (пропускаем None)
        team_sizes = [p["team_size_estimate"] for p in vacancy_profiles if p["team_size_estimate"] is not None]
        avg_team_size = sum(team_sizes) / len(team_sizes) if team_sizes else 0

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

        # Сортировка по количеству вакансий (None → 0)
        sorted_profiles = sorted(
            vacancy_profiles,
            key=lambda x: x["open_vacancies"] or 0,
            reverse=True
        )

        # TOP-3 (только где есть вакансии)
        leaders = [
            {
                "name": p["name"],
                "open_vacancies": p["open_vacancies"] or 0,
                "growth_rate": p["growth_rate"],
                "team_size": p["team_size_estimate"]
            }
            for p in sorted_profiles[:3] if (p["open_vacancies"] or 0) > 0
        ]

        return leaders

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
