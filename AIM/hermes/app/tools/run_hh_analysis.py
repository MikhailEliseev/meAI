"""
run_hh_analysis — Hermes tool: Multi-Pass HH.ru Vacancy Analysis

4 независимых пасса для определения наличия вакансий клиники на hh.ru:
  Pass 1: Apify hh.ru scraper (bypasses Cloudflare blocking)
  Pass 2: Perplexity sonar-pro STRUCTURED (web search, JS-рендеринг)
  Pass 3: _search_fallback site:hh.ru (Perplexity → Firecrawl chain)
  Pass 4: Альтернативные имена (бренд/юрлицо/домен через API + Perplexity)

Confidence level:
  - Pass 1 (Apify) нашёл → HIGH (bypasses Cloudflare)
  - Pass 2 нашёл → MEDIUM (Perplexity web search)
  - ВСЕ пассы пустые → HIGH для NO_DATA (независимое подтверждение)
  - Часть пассов упала, часть подтвердила отсутствие → MEDIUM для NO_DATA
"""

import asyncio
import json
import logging
import os
import re
import time
from urllib.parse import urlparse

import httpx

from tools.registry import registry

logger = logging.getLogger(__name__)

REQUEST_TIMEOUT = 60.0
PERPLEXITY_TIMEOUT = 90.0
MAX_TOKENS = 4000

PERPLEXITY_API_KEY = os.getenv("PERPLEXITY_API_KEY", "").strip()
PERPLEXITY_MODEL = "sonar-pro"
USE_PERPLEXITY = bool(PERPLEXITY_API_KEY)

# ── hh.ru area ID mapping ──────────────────────────────────────────────
HH_AREA_IDS: dict[str, int] = {
    "москва": 1, "мск": 1, "moscow": 1,
    "санкт-петербург": 2, "спб": 2, "питер": 2,
    "екатеринбург": 3,
    "новосибирск": 4,
    "казань": 88,
    "нижний новгород": 66,
    "краснодар": 53,
    "ростов-на-дону": 76, "ростов": 76,
    "челябинск": 104,
    "самара": 78,
    "уфа": 99,
    "омск": 68,
    "пермь": 72,
    "воронеж": 26,
    "волгоград": 24,
}


def _get_area_id(city: str) -> int:
    """Map city name to hh.ru area ID. Defaults to 113 (Russia) if unknown."""
    if not city:
        return 113
    city_lower = city.lower().strip()
    return HH_AREA_IDS.get(city_lower, 113)


def _normalize_args(first_param, defaults):
    if isinstance(first_param, dict):
        return {k: first_param.get(k, defaults[k]) for k in defaults}
    return None


# ── hh.ru Browser Headers ──────────────────────────────────────────────

_USER_AGENTS = [
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
    "AIM-Hermes/1.0 (aim@iamaim.ru)",
]


def _hh_headers() -> dict:
    """Build browser-like headers for hh.ru API requests to avoid 403."""
    idx = int(time.time() * 1000) % len(_USER_AGENTS)
    return {
        "User-Agent": _USER_AGENTS[idx],
        "Accept": "application/json, text/plain, */*",
        "Accept-Language": "ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7",
        "Accept-Encoding": "gzip, deflate, br",
        "Referer": "https://hh.ru/",
        "Origin": "https://hh.ru",
        "Connection": "keep-alive",
    }


# ── Pass 1: Apify hh.ru API Scraper ──────────────────────────────────

APIFY_BASE = "https://api.apify.com/v2"
HH_APIFY_ACTOR = os.getenv("HH_APIFY_ACTOR", "abotapi~hh-ru-jobs-scraper").strip()
APIFY_POLL_TIMEOUT = 120  # max seconds to wait for actor run


async def _search_hh_apify(company_name: str, area_id: int) -> dict | None:
    """Pass 1: Search hh.ru via Apify actor (bypasses Cloudflare blocking).

    Uses Apify's proxy infrastructure to call hh.ru API through residential IPs.
    Rotates through available Apify keys on exhaustion.
    """
    try:
        from app.key_bank import key_bank
    except ImportError:
        return {"status": "skipped", "note": "key_bank not available"}

    apify_keys = key_bank.get_apify_keys(active_only=True)
    if not apify_keys:
        return {"status": "skipped", "note": "No active Apify keys"}

    for api_key in apify_keys:
        try:
            result = await _run_apify_hh_actor(api_key, company_name, area_id)
            if result and result.get("employer_name"):
                return result
        except Exception as e:
            err_str = str(e).lower()
            if any(kw in err_str for kw in ("402", "429", "quota", "exceeded", "insufficient", "balance", "limit")):
                key_bank.mark_apify_exhausted(api_key)
                logger.warning("Apify key exhausted during hh.ru actor, rotating…")
                continue
            logger.warning("Apify hh.ru actor error: %s", str(e)[:150])
            continue

    return {"status": "error", "note": "All Apify keys failed"}


async def _run_apify_hh_actor(api_key: str, company_name: str, area_id: int) -> dict | None:
    """Execute Apify hh.ru actor: start run → poll → fetch dataset."""
    async with httpx.AsyncClient(timeout=120.0) as client:
        # Step 1: Start actor run
        run_input = {
            "mode": "search",
            "queries": [company_name],
            "areas": [str(area_id)],
            "maxPages": 1,
            "maxListings": 50,
            "fetchDetails": True,
        }
        resp = await client.post(
            f"{APIFY_BASE}/acts/{HH_APIFY_ACTOR}/runs",
            params={"token": api_key},
            json=run_input,
        )
        if resp.status_code == 404:
            logger.warning("Apify actor '%s' not found (404)", HH_APIFY_ACTOR)
            return None
        if resp.status_code == 400:
            logger.warning("Apify actor bad request (400): %s", resp.text[:200])
            return None
        if resp.status_code == 402:
            logger.warning("Apify actor: insufficient credits (402)")
            raise Exception("402 insufficient credits")
        if resp.status_code == 403:
            logger.warning("Apify actor: access denied (403) — %s", resp.text[:200])
            raise Exception("403 quota exceeded")
        if resp.status_code != 201:
            logger.warning("Apify actor start returned %d: %s", resp.status_code, resp.text[:200])
            resp.raise_for_status()

        run_data = resp.json()["data"]
        run_id = run_data["id"]
        logger.info("Apify hh.ru run %s started (actor=%s)", run_id, HH_APIFY_ACTOR)

        # Step 2: Poll for completion
        for attempt in range(APIFY_POLL_TIMEOUT // 3):
            await asyncio.sleep(3)
            status_resp = await client.get(
                f"{APIFY_BASE}/actor-runs/{run_id}",
                params={"token": api_key},
            )
            status_data = status_resp.json()["data"]
            status = status_data["status"]

            if status == "SUCCEEDED":
                dataset_id = status_data.get("defaultDatasetId")
                if not dataset_id:
                    logger.warning("Apify run %s succeeded but no dataset", run_id)
                    return None
                items = await _fetch_apify_dataset(client, api_key, dataset_id)
                return _parse_apify_items(items, company_name, run_id)
            elif status in ("FAILED", "ABORTED", "TIMED-OUT"):
                logger.warning("Apify hh.ru run %s: %s", run_id, status)
                return None
            elif status in ("READY", "RUNNING"):
                continue

        logger.warning("Apify hh.ru run %s: poll timeout (%ds)", run_id, APIFY_POLL_TIMEOUT)
        return None


async def _fetch_apify_dataset(client: httpx.AsyncClient, api_key: str, dataset_id: str) -> list[dict]:
    """Fetch dataset items from completed Apify actor run."""
    resp = await client.get(
        f"{APIFY_BASE}/datasets/{dataset_id}/items",
        params={"token": api_key, "limit": 50},
    )
    resp.raise_for_status()
    data = resp.json()
    if isinstance(data, list):
        return data
    # Some actors wrap items
    return data.get("items", data.get("data", []))


def _parse_apify_items(items: list[dict], company_name: str, run_id: str) -> dict | None:
    """Parse Apify dataset items into structured vacancy data.

    Input format (abotapi~hh-ru-jobs-scraper):
      vacancyId, url, name, publicationDate, creationDate,
      salaryFrom, salaryTo, salaryCurrency, salaryGross,
      company.id, company.name, company.visibleName,
      area.id, area.name
    """
    if not items:
        logger.info("Apify run %s: empty dataset for '%s'", run_id, company_name)
        return None

    vacancies = []
    employer_name = company_name
    employer_id = ""

    for v in items:
        # abotapi~hh-ru-jobs-scraper format: flat fields
        area_data = v.get("area") or {}
        company_data = v.get("company") or {}

        vacancies.append({
            "name": v.get("name", ""),
            "area": area_data.get("name", ""),
            "salary_from": v.get("salaryFrom"),
            "salary_to": v.get("salaryTo"),
            "salary_currency": v.get("salaryCurrency"),
            "published_at": v.get("publicationDate", ""),
            "url": v.get("url", ""),
        })

        # Track employer from first item
        if not employer_id and company_data.get("id"):
            employer_id = str(company_data.get("id", ""))
            employer_name = company_data.get("name", company_data.get("visibleName", company_name))

    # Category breakdown
    categories: dict[str, int] = {}
    for v in vacancies:
        cat = v["name"].split("(")[0].strip()
        categories[cat] = categories.get(cat, 0) + 1

    logger.info("Apify run %s: %d vacancies for '%s'", run_id, len(vacancies), employer_name)

    return {
        "source": f"Apify ({HH_APIFY_ACTOR})",
        "employer_name": employer_name,
        "employer_id": employer_id,
        "employer_url": f"https://hh.ru/employer/{employer_id}" if employer_id else "",
        "open_vacancies": len(items),
        "vacancies": vacancies[:20],
        "top_categories": dict(sorted(categories.items(), key=lambda x: x[1], reverse=True)[:5]),
    }


# ── Pass 2: Perplexity Structured Search ────────────────────────────────

def _build_hh_perplexity_query(company_name: str, city: str) -> str:
    """Build Perplexity query for hh.ru employer vacancy search."""
    location = f" в г. {city}" if city else ""
    return (
        f"Найди страницу работодателя «{company_name}»{location} на сайте hh.ru.\n\n"
        f"1. Введи в google: {company_name} site:hh.ru/employer\n"
        "2. Перейди на страницу вида hh.ru/employer/ЦИФРЫ\n"
        "3. Посмотри количество открытых вакансий (цифра на странице)\n"
        "4. Перечисли эти вакансии (название, зарплата)\n\n"
        f"Если страница работодателя «{company_name}» не найдена на hh.ru — напиши ровно: EMPLOYER_NOT_FOUND\n"
        "Если страница найдена но вакансий нет — напиши ровно: NO_VACANCIES\n"
        "НЕ ищи вакансии по ключевым словам — ищи конкретного работодателя."
    )


async def _search_via_perplexity(company_name: str, city: str) -> dict | None:
    """Pass 2: Use Perplexity (sonar-pro) to search for vacancies on hh.ru."""
    if not USE_PERPLEXITY:
        return {"status": "skipped", "note": "PERPLEXITY_API_KEY not set"}

    try:
        from openai import AsyncOpenAI

        client = AsyncOpenAI(
            api_key=PERPLEXITY_API_KEY,
            base_url="https://api.perplexity.ai",
            timeout=PERPLEXITY_TIMEOUT,
        )

        query = _build_hh_perplexity_query(company_name, city)
        response = await client.chat.completions.create(
            model=PERPLEXITY_MODEL,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "Ты — аналитик рынка труда. Твоя задача — найти страницу "
                        "конкретной компании на hh.ru и проверить её открытые вакансии. "
                        "Ищи фактические данные. Если компания не найдена — честно скажи об этом. "
                        "Не выдумывай."
                    ),
                },
                {"role": "user", "content": query},
            ],
            temperature=0.2,
            max_tokens=MAX_TOKENS,
        )
        content = response.choices[0].message.content or ""

        # Check for explicit "not found" markers
        if "EMPLOYER_NOT_FOUND" in content.upper():
            return {"status": "empty", "note": "Employer not found on hh.ru via Perplexity"}
        if "NO_VACANCIES" in content.upper():
            return {"status": "empty", "note": "Employer found but no open vacancies"}

        # Try to extract vacancy count — only from employer-page context
        vac_count = 0
        # Pattern: "открытых вакансий: N" or "N вакансий" near employer mention
        count_patterns = [
            r'открытых?\s*ваканси[йя][:\s]*(\d+)',
            r'количество\s*ваканси[йя][:\s]*(\d+)',
            r'ваканси[йя][:\s]*(\d+)\s*(?:шт|штук)?',
        ]
        for pat in count_patterns:
            count_match = re.search(pat, content, re.IGNORECASE)
            if count_match:
                vac_count = int(count_match.group(1))
                break

        # Sanity check: if vac_count > 50, likely a market-wide number, not employer-specific
        if vac_count > 50:
            logger.warning(
                "Perplexity returned %d vacancies for '%s' — likely market-wide, capping at 50",
                vac_count, company_name,
            )
            vac_count = min(vac_count, 50)  # Cap but don't discard

        return {
            "status": "data_found" if vac_count > 0 else "inconclusive",
            "vacancies_found": vac_count,
            "raw_response": content[:2000],
            "note": "Perplexity web search result",
        }

    except Exception as e:
        logger.warning("Perplexity HH search failed: %s", str(e)[:150])
        return {"status": "error", "note": f"Perplexity error: {str(e)[:200]}"}


# ── Pass 3: _search_fallback site:hh.ru ─────────────────────────────────

async def _search_via_fallback(company_name: str) -> dict | None:
    """Pass 3: Search for HH vacancies via search fallback (Perplexity → Firecrawl chain).

    Two-phase approach:
    1. site:hh.ru query → focused hh.ru results (best quality)
    2. If phase 1 empty → broad query without site: (catches what strict mode missed)
    """
    try:
        from app.tools._search_fallback import search as fallback_search
    except ImportError:
        return {"status": "error", "note": "_search_fallback not available"}

    # Phase 1: site-specific (focused, high quality)
    query_site = f'{company_name} вакансии site:hh.ru'
    results, provider = await fallback_search(query_site, max_results=10)

    # Phase 2: if site:hh.ru returned nothing, retry without site restriction
    if not results:
        logger.info("Fallback phase 1 (site:hh.ru) empty for '%s', retrying without site:", company_name)
        query_broad = f'{company_name} hh.ru вакансии работодатель'
        results, provider = await fallback_search(query_broad, max_results=10)
        if not results:
            return {"status": "empty", "note": f"No hh.ru pages found via {provider} (both phases)"}

    links = []
    employer_links = 0
    vacancy_links = 0
    extracted_vacancy_count = 0
    for r in results:
        url = r.get("url", "")
        title = r.get("title", "")
        description = r.get("description", "")
        links.append({
            "title": title,
            "url": url,
            "description": description,
        })
        if re.search(r'hh\.ru/employer/\d+', url):
            employer_links += 1
        if re.search(r'hh\.ru/vacancy/\d+', url):
            vacancy_links += 1
        # Extract vacancy count from title/description (e.g. "365 вакансий на hh.ru")
        combined = f"{title} {description}"
        for m in re.finditer(r'(\d[\d\s]*\d)\s*ваканси', combined, re.IGNORECASE):
            try:
                count = int(m.group(1).replace(" ", ""))
                if count > extracted_vacancy_count:
                    extracted_vacancy_count = count
            except ValueError:
                pass

    # Status determination:
    # - Extracted count from titles → data_found (strong signal)
    # - Employer page + multiple vacancy URLs → data_found (employer has vacancies)
    # - Employer page only → inconclusive (employer exists, unclear if hiring)
    # - Vacancy URLs without employer → inconclusive (likely search results)
    if extracted_vacancy_count > 0:
        status = "data_found"
        logger.info("Extracted %d vacancies from fallback results for '%s'", extracted_vacancy_count, company_name)
    elif employer_links > 0 and vacancy_links >= 3:
        status = "data_found"
        extracted_vacancy_count = vacancy_links  # minimum estimate
        logger.info("Fallback: employer + %d vacancy URLs for '%s' — treating as data_found (min estimate)", vacancy_links, company_name)
    elif employer_links > 0:
        status = "inconclusive"
    elif vacancy_links > 0:
        status = "inconclusive"  # Vacancy URLs without employer — likely search results
    else:
        status = "inconclusive"

    note = (f"Found {len(links)} hh.ru links ({employer_links} employer pages, {vacancy_links} vacancies) via {provider}"
            if links else f"No hh.ru pages found via {provider}")

    return {
        "status": status,
        "source": provider,
        "query": query_site,
        "search_results": links,
        "vacancies_found": extracted_vacancy_count,
        "note": note,
    } if links else {"status": "empty", "note": note}


# ── Pass 4: Alternative Names ────────────────────────────────────────────

def _derive_alternative_names(company_name: str, domain: str = "") -> list[str]:
    """Derive alternative search names from company name and domain."""
    alternatives = []

    if domain:
        # Domain without TLD
        domain_clean = domain.replace("www.", "").split(".")[0]
        if domain_clean and domain_clean.lower() != company_name.lower():
            alternatives.append(domain_clean)

    # Try different forms
    name = company_name.strip()

    # Remove quotes
    cleaned = name.replace('"', '').replace('«', '').replace('»', '')
    if cleaned != name:
        alternatives.append(cleaned)

    # Add ООО prefix if not present
    if "ООО" not in name.upper() and not name.startswith("ИП "):
        alternatives.append(f"ООО {name}")

    # Remove ООО prefix if present
    if name.upper().startswith("ООО "):
        alternatives.append(name[4:].strip())

    # Deduplicate
    seen = {name.lower()}
    result = []
    for alt in alternatives:
        if alt.lower() not in seen:
            seen.add(alt.lower())
            result.append(alt)

    return result[:3]  # Max 3 alternatives


async def _search_alternative_names(
    company_name: str,
    domain: str,
    area_id: int,
) -> dict | None:
    """Pass 4: Try alternative names (brand, legal name, domain) via Apify."""
    alternatives = _derive_alternative_names(company_name, domain)
    if not alternatives:
        return {"status": "skipped", "note": "No alternative names to try"}

    results = []
    for alt_name in alternatives:
        try:
            api_result = await _search_hh_apify(alt_name, area_id)
            if api_result and api_result.get("employer_name"):
                results.append({
                    "searched_as": alt_name,
                    "result": api_result,
                })
        except Exception as e:
            logger.debug("Alt name search failed for '%s': %s", alt_name, str(e)[:100])

    if results:
        return {
            "status": "data_found",
            "note": f"Found employer under alternative name",
            "alternatives_checked": alternatives,
            "matches": results,
        }
    return {
        "status": "empty",
        "note": f"No employer found under {len(alternatives)} alternative names",
        "alternatives_checked": alternatives,
    }


# ── Confidence Computation ───────────────────────────────────────────────

def _compute_confidence(passes: dict) -> str:
    """Compute confidence level based on pass agreement.

    HIGH: Pass 1 found data (official API), OR all passes agree on empty
    MEDIUM: Pass 2 found data, OR some passes errored but rest agree on empty
    LOW: Conflicting results or all passes errored
    """
    statuses = {}

    for pass_name, pass_data in passes.items():
        if not pass_data:
            statuses[pass_name] = "empty"
            continue
        st = pass_data.get("status", "")
        statuses[pass_name] = st

    # Pass 1 (Apify — bypasses Cloudflare) found → HIGH
    if statuses.get("apify") == "data_found":
        return "HIGH"

    # Pass 2 (Perplexity) found → MEDIUM
    if statuses.get("perplexity") == "data_found":
        return "MEDIUM"

    # Pass 3/4 found → need cross-validation with Pass 2
    if statuses.get("fallback") == "data_found" or statuses.get("alternative_names") == "data_found":
        # If Perplexity (Pass 2) agrees → MEDIUM
        if statuses.get("perplexity") == "data_found":
            return "MEDIUM"
        # If Perplexity says EMPTY (explicit NO_VACANCIES/EMPLOYER_NOT_FOUND) → LOW (direct conflict)
        if statuses.get("perplexity") == "empty":
            return "LOW"
        # If Perplexity is inconclusive/error/skipped/blocked → MEDIUM (fallback found real data)
        return "MEDIUM"

    # All successful passes agree on "empty"/"inconclusive" → HIGH confidence for NO_DATA
    non_error = {
        k: v for k, v in statuses.items()
        if v not in ("error", "skipped", "blocked")
    }
    if non_error and all(v in ("empty", "inconclusive") for v in non_error.values()):
        if len(non_error) >= 2:
            return "HIGH"
        return "MEDIUM"

    # All errored/blocked/skipped → LOW
    if all(v in ("error", "skipped", "blocked") for v in statuses.values()):
        return "LOW"

    return "MEDIUM"


# ── Main Handler ─────────────────────────────────────────────────────────

async def handle_run_hh_analysis(url=None, company_name="", city="", **kwargs) -> str:
    """Analyze HeadHunter vacancies for a clinic using 4 independent passes.

    Multi-pass approach ensures confidence in both "data found" and "no data" results.
    90% of small clinics won't have hh.ru vacancies — that's normal.

    Args:
        url: Website URL or company name to search HH vacancies for.
        company_name: Optional company name for more precise search.
        city: City name for geo-targeting (maps to hh.ru area ID).

    Returns:
        JSON with structured vacancy data, confidence level, and pass details.
    """
    unpacked = _normalize_args(url, {"url": "", "company_name": "", "city": ""})
    if unpacked:
        url = unpacked.get("url", url)
        company_name = unpacked.get("company_name", company_name)
        city = unpacked.get("city", city or "")

    # Extract from kwargs
    cn = kwargs.get("company_name", "")
    if cn and not company_name:
        company_name = cn
    ct = kwargs.get("city", "")
    if ct and not city:
        city = ct

    search_term = company_name or url or ""
    if not search_term:
        return json.dumps({"error": "URL or company name is required"}, ensure_ascii=False)

    # Clean search term: extract domain if URL
    domain = ""
    if search_term.startswith("http"):
        parsed = urlparse(search_term)
        domain = parsed.netloc.replace("www.", "")
        if not company_name:
            company_name = domain
        search_term = company_name

    # Normalize
    search_term = search_term.replace("www.", "").strip()
    company_name = company_name.replace("www.", "").strip()

    area_id = _get_area_id(city)

    # File cache key
    cache_key = f"hh_{search_term}_{area_id}"

    # Check file cache
    try:
        from app.tools._file_cache import file_cache
        cached = await file_cache.get(cache_key)
        if cached is not None:
            logger.info("HH analysis cache HIT for: %s (area=%d)", search_term, area_id)
            return cached
    except Exception:
        pass

    logger.info("HH multi-pass analysis for: %s, city=%s, area_id=%d", search_term, city, area_id)

    try:
        from app.main import push_tool_progress

        passes: dict[str, dict | None] = {}
        all_vacancies: list[dict] = []
        searched_as = [company_name]

        push_tool_progress("hh", f"💼 Pass 1/4: Apify hh.ru scraper для {search_term}…")

        # ── Pass 1: Apify hh.ru Scraper ──────────────────────────────
        try:
            apify_result = await _search_hh_apify(search_term, area_id)
            if apify_result and apify_result.get("employer_name"):
                passes["apify"] = {
                    "status": "data_found",
                    "employer_name": apify_result["employer_name"],
                    "employer_url": apify_result.get("employer_url", ""),
                    "vacancies_found": apify_result.get("open_vacancies", 0),
                    "source": apify_result.get("source", ""),
                }
                all_vacancies.extend(apify_result.get("vacancies", []))
                push_tool_progress("hh", f"✅ Pass 1: Apify нашёл {apify_result.get('open_vacancies', 0)} вакансий!")
            elif apify_result and apify_result.get("status") in ("skipped", "blocked", "error"):
                passes["apify"] = apify_result
                push_tool_progress("hh", f"⚠️ Pass 1: Apify — {apify_result.get('note', '')[:80]}")
            else:
                passes["apify"] = {"status": "empty", "note": "Employer not found on hh.ru via Apify"}
                push_tool_progress("hh", "Pass 1: работодатель не найден через Apify")
        except Exception as e:
            logger.warning("Pass 1 (Apify) error: %s", str(e)[:150])
            passes["apify"] = {"status": "error", "note": str(e)[:200]}
            push_tool_progress("hh", f"⚠️ Pass 1: ошибка Apify — {str(e)[:80]}")

        # ── Pass 2: Perplexity Structured Search ─────────────────────
        push_tool_progress("hh", f"🔍 Pass 2/4: Perplexity ищет {search_term} на hh.ru…")
        try:
            pp_result = await _search_via_perplexity(company_name, city)
            passes["perplexity"] = pp_result or {"status": "empty", "note": "No result"}
            if pp_result and pp_result.get("status") == "data_found":
                push_tool_progress("hh", f"✅ Pass 2: Perplexity нашёл {pp_result.get('vacancies_found', 0)} вакансий")
            elif pp_result and pp_result.get("status") == "error":
                push_tool_progress("hh", f"⚠️ Pass 2: ошибка Perplexity")
            else:
                push_tool_progress("hh", "Pass 2: Perplexity не нашёл вакансий")
        except Exception as e:
            logger.warning("Pass 2 (Perplexity) error: %s", str(e)[:150])
            passes["perplexity"] = {"status": "error", "note": str(e)[:200]}

        # ── Pass 3: _search_fallback site:hh.ru ──────────────────────
        # Only run if Pass 1 + Pass 2 both found nothing
        p1_data = passes.get("apify", {})
        p1_empty = p1_data.get("status") not in ("data_found",)  # no employer found via Apify
        p2_empty = passes.get("perplexity", {}).get("status") in ("empty", "error", "skipped", "inconclusive", "blocked")

        if p1_empty and p2_empty:
            push_tool_progress("hh", "🔄 Pass 3/4: search fallback site:hh.ru…")
            try:
                fb_result = await _search_via_fallback(search_term)
                passes["fallback"] = fb_result or {"status": "empty", "note": "No result"}
                if fb_result and fb_result.get("status") == "data_found":
                    push_tool_progress("hh", f"✅ Pass 3: fallback нашёл {len(fb_result.get('search_results', []))} результатов")
                else:
                    push_tool_progress("hh", "Pass 3: fallback ничего не нашёл")
            except Exception as e:
                logger.warning("Pass 3 (fallback) error: %s", str(e)[:150])
                passes["fallback"] = {"status": "error", "note": str(e)[:200]}
        else:
            passes["fallback"] = {"status": "skipped", "note": "Not needed — earlier passes found data or agree on empty"}

        # ── Pass 4: Alternative Names ─────────────────────────────────
        p3_empty = passes.get("fallback", {}).get("status") in ("empty", "error", "skipped", "blocked")
        if p1_empty and p2_empty and p3_empty:
            push_tool_progress("hh", "🔄 Pass 4/4: альтернативные имена…")
            try:
                alt_result = await _search_alternative_names(company_name, domain, area_id)
                passes["alternative_names"] = alt_result or {"status": "empty", "note": "No result"}
                if alt_result and alt_result.get("status") == "data_found":
                    searched_as.extend(alt_result.get("alternatives_checked", []))
                    for match in alt_result.get("matches", []):
                        all_vacancies.extend(match.get("result", {}).get("vacancies", []))
                    push_tool_progress("hh", "✅ Pass 4: найдено через альтернативные имена!")
                else:
                    push_tool_progress("hh", "Pass 4: альтернативные имена тоже не дали результатов")
            except Exception as e:
                logger.warning("Pass 4 (alt names) error: %s", str(e)[:150])
                passes["alternative_names"] = {"status": "error", "note": str(e)[:200]}
        else:
            passes["alternative_names"] = {"status": "skipped", "note": "Not needed"}

        # ── Compute confidence & verdict ──────────────────────────────
        confidence = _compute_confidence(passes)
        total_vacancies = len(all_vacancies)

        # Count from passes (fallback already includes extracted vacancy count)
        for pass_name, pass_data in passes.items():
            if pass_data and pass_data.get("vacancies_found"):
                total_vacancies = max(total_vacancies, pass_data["vacancies_found"])

        verdict = "data_found" if total_vacancies > 0 else "no_data"

        push_tool_progress(
            "hh",
            f"{'✅' if verdict == 'data_found' else '📭'} HH-анализ: "
            f"{total_vacancies} вакансий, confidence={confidence}, verdict={verdict}",
        )

        result = {
            "search_term": search_term,
            "searched_as": searched_as,
            "area_id": area_id,
            "city": city or "не указан",
            "confidence": confidence,
            "verdict": verdict,
            "vacancies_found": total_vacancies,
            "passes": passes,
            "vacancies": all_vacancies[:20],
        }

        result_json = json.dumps(result, ensure_ascii=False, indent=2)

        # Save to file cache
        try:
            from app.tools._file_cache import file_cache
            await file_cache.set(cache_key, result_json)
        except Exception:
            pass

        return result_json

    except Exception as e:
        logger.exception("HH analysis error")
        return json.dumps({"error": "Unexpected error", "detail": str(e)}, ensure_ascii=False)


registry.register(
    name="run_hh_analysis",
    toolset="aim-operations",
    schema={
            "name": "run_hh_analysis",
            "description": (
                "Multi-pass HeadHunter.ru vacancy analysis for a clinic. "
                "Uses 4 independent passes (hh API, Perplexity, search fallback, "
                "alternative names) to determine if clinic has open vacancies. "
                "Returns structured data with confidence level — even 'no data' "
                "result is verified across multiple sources."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "url": {"type": "string", "description": "Website URL or company name to search HH vacancies for"},
                    "company_name": {"type": "string", "description": "Optional: exact company name for more precise search"},
                    "city": {"type": "string", "description": "Optional: city for geo-targeting (maps to hh.ru area ID)"},
                },
                "required": ["url"],
            },
        },
    handler=handle_run_hh_analysis,
    check_fn=lambda: True,
    is_async=True,
    description="Multi-pass HeadHunter.ru vacancy analysis with confidence scoring",
    emoji="💼",
)
