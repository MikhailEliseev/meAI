"""
run_hh_analysis — Hermes tool: HeadHunter Vacancy Intelligence

Uses hh.ru public API (no auth required) to find open vacancies at a competitor company.
Reveals: hiring velocity, salary ranges, growth signals, most in-demand roles.

NOTE: hh.ru API is protected by ddos-guard and blocks non-Russian IPs.
The tool tries direct API first, then falls back to web search for hh.ru pages.
If both fail, returns a graceful "unavailable" message rather than an error.

Registered in Hermes internal registry under toolset "aim-operations".
"""

import json
import logging
import os

import httpx

from tools.registry import registry

logger = logging.getLogger(__name__)

HH_API_BASE = "https://api.hh.ru"
HH_WEB_SEARCH_URL = "https://hh.ru/search/vacancy"
REQUEST_TIMEOUT = 15.0
PROXY_URL = os.getenv("TELEGRAM_PROXY_URL", "")  # reuse Telegram proxy for hh.ru


async def handle_run_hh_analysis(company_name=None, **kwargs) -> str:
    """Search HeadHunter for a company's open vacancies and hiring patterns.

    Tries hh.ru public API first, falls back to web search scraping if blocked.
    Returns structured data about open vacancies, roles, and growth signals.

    Args:
        company_name: Company name to search on HeadHunter (e.g., "ООО Клиника красоты")

    Returns:
        JSON string with employer info, open vacancies, salary ranges, and growth signals.
    """
    if isinstance(company_name, dict):
        company_name = company_name.get("company_name", "")

    if not company_name:
        try:
            cached = Path("/tmp/hermes_last_company.txt").read_text().strip()
            if cached:
                logger.info("Using cached company name: %s", cached)
                company_name = cached
        except Exception:
            pass

    if not company_name:
        return json.dumps({"error": "company_name is required"})

    logger.info("Searching hh.ru for employer: %s", company_name)

    from app.main import push_tool_progress

    push_tool_progress("hh-analysis", f"Ищу вакансии «{company_name}» на HeadHunter…")

    # Configure client with optional proxy
    client_kwargs = {
        "timeout": REQUEST_TIMEOUT,
        "headers": {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
            "Accept": "application/json",
            "Accept-Language": "ru-RU,ru;q=0.9,en;q=0.8",
        },
    }
    if PROXY_URL:
        client_kwargs["proxy"] = PROXY_URL
        logger.info("Using proxy for hh.ru: %s", PROXY_URL)

    # Step 1: Try direct API
    result = await _try_api(company_name, client_kwargs)
    if result is not None:
        return result

    # Step 2: API failed — try web search via Brave
    push_tool_progress("hh-analysis", f"hh.ru API недоступен, ищу через поиск…")
    result = await _try_web_search(company_name)
    if result is not None:
        return result

    # Step 3: Both failed — graceful degradation
    push_tool_progress("hh-analysis", f"⚠️ HeadHunter недоступен (блокировка по IP)")
    return json.dumps({
        "company_name": company_name,
        "found": False,
        "unavailable": True,
        "message": (
            "HeadHunter временно недоступен для автоматического анализа (hh.ru блокирует "
            "запросы не из РФ). Рекомендую проверить вакансии вручную: "
            f"https://hh.ru/search/vacancy?text={company_name.replace(' ', '+')}"
        ),
        "manual_url": f"https://hh.ru/search/vacancy?text={company_name.replace(' ', '+')}",
    }, ensure_ascii=False, indent=2)


async def _try_api(company_name: str, client_kwargs: dict) -> str | None:
    """Try direct hh.ru API. Returns JSON result or None if API is blocked."""
    try:
        async with httpx.AsyncClient(**client_kwargs) as client:
            emp_response = await client.get(
                f"{HH_API_BASE}/employers",
                params={"text": company_name, "per_page": 5, "only_with_vacancies": True},
            )

            if emp_response.status_code == 403:
                logger.warning("hh.ru API blocked (403), trying fallback")
                return None

            emp_response.raise_for_status()
            emp_data = emp_response.json()
            employers = emp_data.get("items", [])

            if not employers:
                logger.info("No employer found on hh.ru for: %s", company_name)
                return json.dumps({
                    "company_name": company_name,
                    "found": False,
                    "message": f"Компания «{company_name}» не найдена на HeadHunter или нет открытых вакансий",
                }, ensure_ascii=False, indent=2)

            employer = employers[0]
            employer_id = employer["id"]
            employer_name = employer.get("name", company_name)
            open_vacancies_count = employer.get("open_vacancies", 0)

            from app.main import push_tool_progress
            push_tool_progress(
                "hh-analysis",
                f"«{employer_name}»: {open_vacancies_count} открытых вакансий, собираю детали…",
            )

            vacancies = await _fetch_vacancies(client, employer_id)

            result = _build_result(employer_name, employer_id, open_vacancies_count, vacancies)
            return json.dumps(result, ensure_ascii=False, indent=2)

    except httpx.HTTPStatusError as e:
        logger.warning("hh.ru API HTTP error: %s", e)
        return None
    except httpx.RequestError as e:
        logger.warning("Cannot reach hh.ru API: %s", e)
        return None
    except Exception as e:
        logger.exception("Unexpected error in hh.ru API call")
        return None


async def _try_web_search(company_name: str) -> str | None:
    """Search hh.ru via Brave Search API as fallback."""
    brave_key = os.getenv("BRAVE_API_KEY", "")
    if not brave_key:
        return None

    try:
        query = f"site:hh.ru {company_name} вакансии"
        async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT) as client:
            response = await client.get(
                "https://api.search.brave.com/res/v1/web/search",
                params={"q": query, "count": 10, "search_lang": "ru"},
                headers={
                    "Accept": "application/json",
                    "Accept-Encoding": "gzip",
                    "X-Subscription-Token": brave_key,
                },
            )

            if response.status_code != 200:
                return None

            data = response.json()
            web_results = data.get("web", {}).get("results", [])
            if not web_results:
                return json.dumps({
                    "company_name": company_name,
                    "found": False,
                    "message": f"Вакансии «{company_name}» не найдены на HeadHunter",
                }, ensure_ascii=False, indent=2)

            # Extract vacancy info from search snippets
            vacancy_hints = []
            for r in web_results[:5]:
                vacancy_hints.append({
                    "title": r.get("title", ""),
                    "snippet": r.get("description", "")[:200],
                    "url": r.get("url", ""),
                })

            return json.dumps({
                "company_name": company_name,
                "found": True,
                "source": "web_search",
                "vacancy_hints": vacancy_hints,
                "note": "Данные из веб-поиска (hh.ru API заблокирован). Информация может быть неполной.",
                "hh_search_url": f"https://hh.ru/search/vacancy?text={company_name.replace(' ', '+')}",
            }, ensure_ascii=False, indent=2)

    except Exception as e:
        logger.warning("Brave search fallback failed: %s", e)
        return None


async def _fetch_vacancies(client: httpx.AsyncClient, employer_id: int) -> list[dict]:
    """Fetch vacancies for employer from hh.ru API."""
    vacancies = []
    for page in range(3):
        vac_response = await client.get(
            f"{HH_API_BASE}/vacancies",
            params={
                "employer_id": employer_id,
                "per_page": 50,
                "page": page,
                "only_with_salary": False,
            },
        )
        vac_response.raise_for_status()
        vac_data = vac_response.json()
        items = vac_data.get("items", [])
        if not items:
            break

        for v in items:
            salary = v.get("salary")
            vacancies.append({
                "title": v.get("name", ""),
                "area": v.get("area", {}).get("name", ""),
                "salary_from": salary.get("from") if salary else None,
                "salary_to": salary.get("to") if salary else None,
                "salary_currency": salary.get("currency") if salary else None,
                "experience": v.get("experience", {}).get("name", ""),
                "schedule": v.get("schedule", {}).get("name", ""),
                "url": v.get("alternate_url", ""),
            })

        if len(items) < 50:
            break

    return vacancies


def _build_result(employer_name: str, employer_id: int, open_count: int, vacancies: list[dict]) -> dict:
    """Build result dict with insights from vacancy data."""
    roles = [v["title"] for v in vacancies]
    salary_vacancies = [v for v in vacancies if v["salary_from"] or v["salary_to"]]
    avg_salary_from = (
        sum(v["salary_from"] for v in salary_vacancies if v["salary_from"]) / len(salary_vacancies)
        if salary_vacancies else None
    )

    growth_signals = []
    if open_count >= 10:
        growth_signals.append("Активный найм — компания растёт или расширяет штат")
    if len(vacancies) >= 5:
        growth_signals.append(f"Много вакансий ({len(vacancies)}) — признак расширения")
    doctor_roles = [r for r in roles if any(w in r.lower() for w in ["врач", "доктор", "хирург", "косметолог", "дермато"])]
    if doctor_roles:
        growth_signals.append(f"Ищут врачей: {', '.join(doctor_roles[:3])}")
    admin_roles = [r for r in roles if any(w in r.lower() for w in ["администратор", "менеджер", "управляю"])]
    if admin_roles:
        growth_signals.append(f"Ищут административный персонал: {', '.join(admin_roles[:2])}")
    marketing_roles = [r for r in roles if any(w in r.lower() for w in ["маркетолог", "smm", "таргетолог", "seo", "контент"])]
    if marketing_roles:
        growth_signals.append(f"Ищут маркетологов — вкладываются в продвижение: {', '.join(marketing_roles[:2])}")

    return {
        "company_name": employer_name,
        "found": True,
        "employer_id": str(employer_id),
        "open_vacancies": open_count,
        "vacancies_fetched": len(vacancies),
        "vacancies": vacancies,
        "top_roles": roles[:10],
        "avg_salary_from": round(avg_salary_from) if avg_salary_from else None,
        "salary_currency": salary_vacancies[0]["salary_currency"] if salary_vacancies else "RUR",
        "growth_signals": growth_signals,
        "hh_url": f"https://hh.ru/employer/{employer_id}",
    }


registry.register(
    name="run_hh_analysis",
    toolset="aim-operations",
    schema={
        "type": "function",
        "function": {
            "name": "run_hh_analysis",
            "description": (
                "Analyse a competitor's open vacancies on HeadHunter (hh.ru) to detect growth signals. "
                "Shows: hiring velocity, which roles are open (doctors, admins, marketers), "
                "salary ranges, and expansion patterns. "
                "Use this to understand if a competitor is growing, expanding services, "
                "or investing in marketing (marketing vacancies = they care about promotion). "
                "Public API, no authentication needed."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "company_name": {
                        "type": "string",
                        "description": "[REQUIRED] Company name to search on HeadHunter (e.g., 'ООО Клиника красоты', 'СМ-Клиника')",
                    },
                },
                "required": ["company_name"],
            },
        },
    },
    handler=handle_run_hh_analysis,
    check_fn=lambda: True,
    is_async=True,
    description="Analyse competitor vacancies on HeadHunter: hiring velocity, roles, salaries, growth signals",
    emoji="💼",
)
