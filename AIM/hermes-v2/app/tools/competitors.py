"""Competitors tools: find_competitors + enrich_competitors + filter_competitors.

Phase 7:
- find_competitors: возвращает 15-30 кандидатов с ИНН (было 3)
- enrich_competitors: ИНН → выручка через Perplexity
- filter_competitors: фильтр по выручке ±30%, специализация, топ-5
"""
import json
import logging

import httpx

from app.config import AIM_API_BASE, REQUEST_TIMEOUT
from app.lib.perplexity import USE_PERPLEXITY, perplexity_chat
from app.tools.registry import register

logger = logging.getLogger(__name__)


def _normalize_url(url: str) -> str:
    if not url.startswith(("http://", "https://")):
        url = "https://" + url
    return url


# --- find_competitors: proxy to aim-app -----------------------------------------

async def find_competitors(url: str, count: int = 5,
                             client_inn: str = "", client_address: str = "") -> dict:
    """Прозрачный прокси к aim-app POST /api/competitors/find.

    Phase 7: по умолчанию возвращает 20 кандидатов (было 3).
    client_inn и client_address передаются для более точного поиска.

    Returns:
        JSON-ответ aim-app как есть, либо {"error": ...} при сбое.
    """
    url = _normalize_url(url)

    logger.info("find_competitors proxy: url=%s count=%d inn=%s addr=%s",
                url, count, client_inn, client_address[:40] if client_address else "")
    payload = {"url": url, "count": count}
    if client_inn:
        payload["client_inn"] = client_inn
    if client_address:
        payload["client_address"] = client_address

    try:
        async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT) as client:
            response = await client.post(
                f"{AIM_API_BASE}/api/competitors/find",
                json=payload,
            )
            response.raise_for_status()
            return response.json()
    except httpx.HTTPStatusError as e:
        logger.error("find_competitors upstream error: %s status=%s", url, e.response.status_code)
        return {
            "error": "upstream aim-app error",
            "status": e.response.status_code,
            "detail": str(e),
        }
    except httpx.RequestError as e:
        logger.error("find_competitors cannot reach aim-app: %s — %s", url, e)
        return {
            "error": "cannot reach aim-app",
            "detail": str(e),
        }


# --- enrich_competitors: ИНН → выручка (ФНС через aim-app, fallback Perplexity) ---

async def _enrich_single_via_aim_app(inn: str) -> dict | None:
    """Получает выручку из ФНС через aim-app endpoint. Быстро и точно."""
    if not inn or len(inn) < 10:
        return None
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.get(f"{AIM_API_BASE}/api/companies/financials?inn={inn}")
            if resp.status_code != 200:
                return None
            data = resp.json()
            company = data.get("company", {})
            if not company:
                return None
            return {
                "revenue": company.get("latest_revenue"),
                "revenue_year": max(company.get("revenue", {}).keys()) if company.get("revenue") else None,
                "revenue_history": company.get("revenue", {}),
                "profit": company.get("latest_profit"),
                "revenue_trend": company.get("revenue_trend"),
                "source": "nalog_egryul",
                "name": company.get("short_name", ""),
                "status": company.get("status", ""),
            }
    except Exception as e:
        logger.warning("aim-app financials for INN %s failed: %s", inn, e)
        return None


REVENUE_PROMPT_TEMPLATE = """Найди годовую выручку компании по ИНН {inn}.
Если ИНН неизвестен — по названию "{name}".
Ответь ТОЛЬКО JSON без markdown обёртки:
{{"inn": "{inn}", "revenue": null_or_number, "revenue_year": null_or_year, "source": "источник"}}
revenue — в рублях (число). Если не найдено — null.
revenue_year — год отчётности. Если не найдено — null."""


async def _enrich_single_competitor(competitor: dict) -> dict:
    """Получает выручку: 1) aim-app ФНС (точно), 2) Perplexity (fallback)."""
    inn = str(competitor.get("inn", "") or "").strip()
    name = competitor.get("name", competitor.get("brand_name", competitor.get("legal_name", "")))

    # Приоритет 1: ФНС через aim-app (точно, быстро)
    if inn:
        fins = await _enrich_single_via_aim_app(inn)
        if fins and fins.get("revenue"):
            competitor.update(fins)
            logger.info("enriched (ФНС) %s ИНН=%s: revenue=%s", (name or "")[:30], inn, competitor.get("revenue"))
            return competitor

    # Приоритет 2: Perplexity (если нет ИНН или ФНС не нашла)
    if USE_PERPLEXITY and (inn or name):
        try:
            prompt = REVENUE_PROMPT_TEMPLATE.format(inn=inn or "неизвестен", name=name)
            raw = await perplexity_chat([
                {"role": "system", "content": "Ты — аналитик. Возвращаешь ТОЛЬКО валидный JSON без markdown."},
                {"role": "user", "content": prompt},
            ])
            text = raw.strip()
            if text.startswith("```"):
                text = text.split("\n", 1)[-1]
                if text.endswith("```"):
                    text = text[:-3].strip()
            data = json.loads(text)
            competitor["revenue"] = data.get("revenue")
            competitor["revenue_year"] = data.get("revenue_year")
            competitor["revenue_source"] = data.get("source", "perplexity")
            logger.info("enriched (Perplexity) %s: revenue=%s", (name or "")[:30], competitor.get("revenue"))
        except Exception as e:
            logger.warning("enrich competitor %s failed: %s", (name or "")[:30], e)
            competitor["revenue"] = None
            competitor["revenue_source"] = None
    else:
        competitor["revenue"] = None
        competitor["revenue_source"] = None
    return competitor


async def handle_enrich_competitors(competitors_json: str = "",
                                     client_inn: str = "",
                                     client_address: str = "",
                                     **kwargs) -> str:
    """Обогащает список конкурентов данными по выручке.

    competitors_json — JSON string массив конкурентов от find_competitors.
    """
    import asyncio

    try:
        competitors = json.loads(competitors_json) if isinstance(competitors_json, str) else competitors_json
    except json.JSONDecodeError:
        return json.dumps({"error": "invalid competitors JSON"}, ensure_ascii=False)

    if not isinstance(competitors, list):
        # Может быть dict с ключом competitors
        if isinstance(competitors, dict):
            competitors = competitors.get("competitors", [competitors])
        else:
            competitors = [competitors]

    if not competitors:
        return json.dumps({"error": "no competitors to enrich"}, ensure_ascii=False)

    # Также обогащаем клиента если есть ИНН
    if client_inn:
        client_data = {"name": "Клиент", "inn": client_inn}
        enriched_client = await _enrich_single_competitor(client_data)
        # Сохраняем client_revenue для filter
        results = {"client_revenue": enriched_client.get("revenue"),
                   "client_revenue_year": enriched_client.get("revenue_year")}
    else:
        results = {}

    # Обогащаем конкурентов параллельно (макс 10 одновременно)
    semaphore = asyncio.Semaphore(10)

    async def _semaphored_enrich(c):
        async with semaphore:
            return await _enrich_single_competitor(c)

    enriched = await asyncio.gather(
        *[_semaphored_enrich(c) for c in competitors],
        return_exceptions=True,
    )

    results["competitors"] = []
    for c in enriched:
        if isinstance(c, Exception):
            logger.warning("enrich competitor error: %s", c)
            continue
        results["competitors"].append(c)

    logger.info("enriched %d/%d competitors, client_revenue=%s",
                len(results["competitors"]), len(competitors), results.get("client_revenue"))
    return json.dumps(results, ensure_ascii=False, indent=2)


# --- filter_competitors: фильтр по выручке -------------------------------------

def filter_competitors(client_revenue, competitors: list,
                         specialization: str = "") -> list:
    """Фильтрует конкурентов по выручке и специализации.

    Логика:
    1. Если выручка клиента неизвестна — top-3 по рейтингу
    2. Фильтр по выручке: от client_rev * 0.7 до client_rev * 1.5
    3. Если мало кандидатов — расширяем до 0.5 .. 2.0
    4. Сортировка по выручке (достижимые цели ближе к верху)
    5. Top 5
    """
    if not competitors:
        return []

    # Если выручка клиента неизвестна — берём top-3 по рейтингу
    if not client_revenue:
        return sorted(competitors,
                      key=lambda c: float(c.get("rating", 0) or 0),
                      reverse=True)[:3]

    # Фильтр по выручке
    def _get_revenue(c):
        r = c.get("revenue")
        return float(r) if r else 0

    has_revenue = [c for c in competitors if _get_revenue(c) > 0]

    if has_revenue:
        # Диапазон: -30% .. +50% от клиента
        min_rev = client_revenue * 0.7
        max_rev = client_revenue * 1.5

        filtered = [c for c in has_revenue
                    if min_rev <= _get_revenue(c) <= max_rev]

        if len(filtered) < 2:
            # Расширяем диапазон
            min_rev = client_revenue * 0.5
            max_rev = client_revenue * 2.0
            filtered = [c for c in has_revenue
                        if min_rev <= _get_revenue(c) <= max_rev]

        if not filtered:
            # Берём всех с выручкой
            filtered = has_revenue

        # Сортировка: ближайшие к верхней границе (достижимые цели)
        filtered.sort(key=lambda c: _get_revenue(c))
        return filtered[:5]
    else:
        # Нет данных по выручке — по рейтингу
        return sorted(competitors,
                      key=lambda c: float(c.get("rating", 0) or 0),
                      reverse=True)[:3]


# --- register tools -----------------------------------------------------------

register(
    name="find_competitors",
    schema={
        "type": "function",
        "function": {
            "name": "find_competitors",
            "description": (
                "Найти конкурентов для сайта клиники через Google Maps. "
                "Возвращает до 5 конкурентов с ИНН, рейтингом, отзывами. "
                "ВЫЗЫВАЙ ОДИН РАЗ на старте, ОДНОВРЕМЕННО с extract_clinic_profile и quick_overview. "
                "Обязательно передай client_inn и client_address если они известны."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "url": {"type": "string", "description": "URL сайта клиники"},
                    "count": {"type": "integer", "description": "Сколько конкурентов (max 5, default 5)", "default": 5},
                    "client_inn": {"type": "string", "description": "ИНН клиента (для точного поиска)"},
                    "client_address": {"type": "string", "description": "Адрес клиента"},
                },
                "required": ["url"],
            },
        },
    },
    handler=find_competitors,
)

register(
    name="enrich_competitors",
    schema={
        "type": "function",
        "function": {
            "name": "enrich_competitors",
            "description": (
                "Обогатить список конкурентов данными по выручке. "
                "Принимает JSON массив конкурентов от find_competitors. "
                "ВЫЗЫВАЙ после find_competitors, чтобы получить выручку каждого конкурента. "
                "Возвращает enriched список с полем revenue для каждого конкурента."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "competitors_json": {"type": "string",
                                        "description": "JSON массив конкурентов (как вернул find_competitors)"},
                    "client_inn": {"type": "string", "description": "ИНН клиента для получения его выручки"},
                    "client_address": {"type": "string", "description": "Адрес клиента"},
                },
                "required": ["competitors_json"],
            },
        },
    },
    handler=handle_enrich_competitors,
    check_fn=lambda: USE_PERPLEXITY,
)
