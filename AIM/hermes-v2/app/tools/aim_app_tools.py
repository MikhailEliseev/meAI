"""aim-app proxy tools: financials, content analysis, SEO audit, company profiles.

Phase 7: прокси к aim-app:8000 — использует Playwright, Trafilatura, BS4, lxml
для скрейпинга. Финансовые данные из ФНС (ЕГРЮЛ) через /api/companies/financials.
"""
import json
import logging

import httpx

from app.config import AIM_API_BASE, REQUEST_TIMEOUT
from app.tools.registry import register

logger = logging.getLogger(__name__)


async def _aim_post(path: str, payload: dict, timeout: float = None) -> dict:
    """POST к aim-app, возвращает JSON или error dict."""
    try:
        async with httpx.AsyncClient(timeout=timeout or REQUEST_TIMEOUT) as client:
            resp = await client.post(f"{AIM_API_BASE}{path}", json=payload)
            resp.raise_for_status()
            return resp.json()
    except httpx.HTTPStatusError as e:
        logger.error("aim-app %s error: %s", path, e.response.status_code)
        return {"error": f"aim-app {path} returned {e.response.status_code}",
                "detail": e.response.text[:500]}
    except httpx.RequestError as e:
        logger.error("aim-app %s unreachable: %s", path, e)
        return {"error": f"cannot reach aim-app {path}", "detail": str(e)}


async def _aim_get(path: str, timeout: float = None) -> dict:
    """GET к aim-app, возвращает JSON или error dict."""
    try:
        async with httpx.AsyncClient(timeout=timeout or REQUEST_TIMEOUT) as client:
            resp = await client.get(f"{AIM_API_BASE}{path}")
            resp.raise_for_status()
            return resp.json()
    except httpx.HTTPStatusError as e:
        logger.error("aim-app %s error: %s", path, e.response.status_code)
        return {"error": f"aim-app {path} returned {e.response.status_code}"}
    except httpx.RequestError as e:
        logger.error("aim-app %s unreachable: %s", path, e)
        return {"error": f"cannot reach aim-app {path}", "detail": str(e)}


# === company_financials: выручка из ФНС по ИНН ================================

async def handle_company_financials(inn: str = "", **kwargs) -> str:
    """Финансовые данные компании из ЕГРЮЛ (ФНС): выручка, прибыль по годам."""
    if not inn:
        return json.dumps({"error": "inn is required"}, ensure_ascii=False)
    result = await _aim_get(f"/api/companies/financials?inn={inn}", timeout=15)
    if "error" in result:
        return json.dumps(result, ensure_ascii=False)
    company = result.get("company", {})
    revenue = company.get("revenue", {})
    latest = company.get("latest_revenue")
    return json.dumps({
        "inn": inn,
        "name": company.get("short_name", ""),
        "status": company.get("status", ""),
        "revenue": latest,
        "revenue_history": revenue,
        "revenue_trend": company.get("revenue_trend", ""),
        "profit": company.get("latest_profit"),
        "profit_history": company.get("profit", {}),
        "data_source": company.get("data_source", ""),
    }, ensure_ascii=False)


register(
    name="company_financials",
    schema={
        "type": "function",
        "function": {
            "name": "company_financials",
            "description": (
                "Финансовые данные компании из ЕГРЮЛ (ФНС): выручка и прибыль по годам. "
                "Очень точные данные из налоговой. БЫСТРО (~1-3 сек). "
                "ВЫЗЫВАЙ когда нужен ИНН → выручка. "
                "Используй ВСЕГДА когда есть ИНН компании или конкурента."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "inn": {"type": "string", "description": "ИНН компании (10 или 12 цифр)"},
                },
                "required": ["inn"],
            },
        },
    },
    handler=handle_company_financials,
)


# === company_profile: данные о сайте компании =================================

async def handle_company_profile(url: str = "", **kwargs) -> str:
    """Профиль компании по URL из БД aim-app."""
    if not url:
        return json.dumps({"error": "url is required"}, ensure_ascii=False)
    result = await _aim_get(f"/api/company-profiles/by-url?url={url}", timeout=15)
    return json.dumps(result, ensure_ascii=False)


register(
    name="company_profile",
    schema={
        "type": "function",
        "function": {
            "name": "company_profile",
            "description": (
                "Профиль компании из БД: название, ИНН, адрес, услуги. "
                "БЫСТРЫЙ (~1-2 сек) если данные уже есть в БД."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "url": {"type": "string", "description": "URL сайта компании"},
                },
                "required": ["url"],
            },
        },
    },
    handler=handle_company_profile,
)


# === analyze_website: глубокий аудит сайта (Playwright+SEO+репутация) =========

async def handle_analyze_website(url: str = "", **kwargs) -> str:
    """Глубокий аудит сайта через aim-app content analysis.

    Использует Playwright + Trafilatura + BS4 для анализа:
    - Технический SEO (скорость, mobile-friendly, schema.org, sitemap)
    - Контент (структура, ключевые слова, заголовки)
    - UX/UI (навигация, конверсия, дизайн, формы)
    - Репутация (отзывы на Яндекс.Карты, 2ГИС, ПроДокторов)
    """
    if not url:
        return json.dumps({"error": "url is required"}, ensure_ascii=False)
    if not url.startswith(("http://", "https://")):
        url = "https://" + url

    result = await _aim_post("/api/content/analyze", {"url": url}, timeout=120)

    if "error" in result:
        return json.dumps(result, ensure_ascii=False)

    # Извлекаем ключевые метрики из большого ответа
    findings = result.get("findings", {})

    # Phase 2: site audit
    audit = findings.get("phase_2", {}).get("result", {})
    audits = audit.get("audits", [])
    site_audit = audits[0] if audits else {}

    # Phase 4: reputation
    rep = findings.get("phase_4", {}).get("result", {})
    rep_data = rep.get("reviews_data", [])

    # Narrative summary
    narrative = result.get("narrative", {})
    feature_matrix = result.get("feature_matrix", {})
    steal_tactics = result.get("steal_worthy_tactics", [])

    summary = {
        "url": url,
        "site_audit": {
            "total_score": site_audit.get("total_score"),
            "grade": site_audit.get("grade"),
            "dimension_scores": site_audit.get("dimension_scores", {}),
            "strengths": [
                k for k, v in site_audit.get("dimensions", {}).get("technical", {}).items()
                if isinstance(v, dict) and v.get("status") == "good"
            ],
            "weaknesses": [
                k for k, v in site_audit.get("dimensions", {}).items()
                for k2, v2 in (v.items() if isinstance(v, dict) else [])
                if isinstance(v2, dict) and v2.get("status") == "poor"
            ][:10],
        },
        "reputation": {
            "sources": [
                {"source": r.get("sources", {}).__class__ and name,
                 "rating": s.get("avg_rating"),
                 "reviews": s.get("count")}
                for r in rep_data
                for name, s in r.get("sources", {}).items()
            ][:10],
        },
        "narrative": narrative.get("opening", ""),
        "key_findings": narrative.get("key_findings", []),
        "wow": result.get("wow", {}),
        "top_recommendation": result.get("top_recommendation", ""),
        "steal_tactics": steal_tactics[:5],
    }
    return json.dumps(summary, ensure_ascii=False, indent=2)


register(
    name="analyze_website",
    schema={
        "type": "function",
        "function": {
            "name": "analyze_website",
            "description": (
                "Глубокий аудит сайта клиники через Playwright+SEO+репутация: "
                "технический аудит (скорость, mobile, schema.org), "
                "контент-анализ (структура, ключевые слова), "
                "UX/UI (навигация, конверсия), "
                "репутация (Яндекс.Карты, 2ГИС, ПроДокторов). "
                "Занимает ~10-30 сек. "
                "ВЫЗЫВАЙ когда клиент нажал 'Глубокий анализ' или попросил детальный разбор сайта."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "url": {"type": "string", "description": "URL сайта для анализа"},
                },
                "required": ["url"],
            },
        },
    },
    handler=handle_analyze_website,
)


# === seo_audit: SEO аудит сайта ===============================================

async def handle_seo_audit(url: str = "", **kwargs) -> str:
    """SEO аудит сайта через aim-app."""
    if not url:
        return json.dumps({"error": "url is required"}, ensure_ascii=False)
    if not url.startswith(("http://", "https://")):
        url = "https://" + url
    result = await _aim_post("/api/seo/audit", {"url": url}, timeout=120)
    return json.dumps(result, ensure_ascii=False)


register(
    name="seo_audit",
    schema={
        "type": "function",
        "function": {
            "name": "seo_audit",
            "description": (
                "SEO аудит сайта: технические ошибки, мета-теги, скорость, "
                "структура, индексация. ВЫЗЫВАЙ когда клиент спросил про SEO."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "url": {"type": "string", "description": "URL сайта"},
                },
                "required": ["url"],
            },
        },
    },
    handler=handle_seo_audit,
)
