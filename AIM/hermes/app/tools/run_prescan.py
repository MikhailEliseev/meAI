"""
run_prescan — Hermes tool: Parallel Pre-Sale Intelligence Gathering

POST http://app:8000/api/presale/prescan
Launches 5 parallel reconnaissance threads for a client website:
  1. Website structure (services, specialization, city, doctors, prices)
  2. Financial data (rusprofile/nalog by INN)
  3. Quick SEO scan (meta tags, mobile viewport, SSL, load speed)
  4. Reviews snapshot (rating, praise/complaint themes)
  5. Social media (last post date, platform)

Returns aggregated PrescanResult for Hermes to narrate conversationally.
Target: 60-90 seconds.

Registered in Hermes internal registry under toolset "aim-operations".
"""

import json
import logging

import httpx

from tools.registry import registry

logger = logging.getLogger(__name__)

AIM_API_BASE = "http://app:8000"
REQUEST_TIMEOUT = 120.0  # 5 threads in parallel, dominated by slowest (Playwright)


async def handle_run_prescan(url=None, **kwargs) -> str:
    """Run parallel pre-sale intelligence gathering for a client website.

    Launches 5 reconnaissance threads simultaneously and returns
    aggregated results including:
    - Specialization, city, services, doctors, price hints
    - Financial data (revenue, profit from tax filings)
    - SEO issues (meta tags, mobile, SSL, speed)
    - Reviews snapshot (rating, what patients praise/complain about)
    - Social media presence (platforms, last post date)

    Args:
        url: Client clinic website URL (e.g., "https://clinic.ru")

    Returns:
        JSON string with prescan results — all 5 categories.
    """
    if isinstance(url, dict):
        url = url.get("url", "")

    if not url:
        return json.dumps({"error": "url is required"})

    if not url.startswith(("http://", "https://")):
        url = "https://" + url

    logger.info("Running prescan for URL: %s", url)

    from app.main import push_tool_progress

    try:
        push_tool_progress("prescan", "🔍 Запускаю параллельную разведку (5 потоков)…")

        async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT) as client:
            response = await client.post(
                f"{AIM_API_BASE}/api/presale/prescan",
                json={"url": url},
            )
            response.raise_for_status()
            data = response.json()

            if not data.get("success"):
                logger.warning("run_prescan returned error: %s", data.get("error"))
                return json.dumps({
                    "error": "Prescan failed",
                    "detail": data.get("error", "Unknown error"),
                })

            result = data.get("result", {})

            # Build a compact, narrative-friendly summary
            summary = {
                "url": url,
                # Website structure
                "specialization": result.get("specialization", ""),
                "city": result.get("city", ""),
                "services": result.get("services", []),
                "doctors": result.get("doctors", []),
                "price_hints": result.get("price_hints", []),
                # Financials
                "inn": result.get("inn", ""),
                "revenue_year": result.get("revenue_year"),
                "profit_year": result.get("profit_year"),
                "financial_year": result.get("financial_year"),
                # SEO
                "seo_score": result.get("seo_score", 0),
                "seo_issues": result.get("seo_issues", []),
                "has_mobile_viewport": result.get("has_mobile_viewport", False),
                "has_ssl": result.get("has_ssl", False),
                "load_speed_ms": result.get("load_speed_ms", 0),
                # Reviews
                "rating": result.get("rating"),
                "reviews_count": result.get("reviews_count", 0),
                "review_praise": result.get("review_praise", []),
                "review_complaints": result.get("review_complaints", []),
                # Social
                "last_post_date": result.get("last_post_date"),
                "last_post_platform": result.get("last_post_platform"),
                "social_links": result.get("social_links", {}),
                # Errors (non-fatal)
                "errors": result.get("errors", []),
            }

            push_tool_progress(
                "prescan",
                f"✅ Разведка завершена: {result.get('specialization', '')} в {result.get('city', '')}, "
                f"оборот ~{result.get('revenue_year', '?')} ₽, "
                f"SEO={result.get('seo_score', '?')}, "
                f"рейтинг={result.get('rating', '?')}",
            )

            return json.dumps(summary, ensure_ascii=False, indent=2)

    except httpx.HTTPStatusError as e:
        logger.error("AIM API returned error for run_prescan: %s", e)
        return json.dumps({
            "error": "AIM API returned an error",
            "status": e.response.status_code,
            "detail": str(e),
        })
    except httpx.RequestError as e:
        logger.error("Cannot reach AIM API for run_prescan: %s", e)
        return json.dumps({
            "error": "Cannot reach AIM API",
            "detail": str(e),
        })
    except Exception as e:
        logger.exception("Unexpected error in run_prescan handler")
        return json.dumps({
            "error": "Unexpected error in tool handler",
            "detail": str(e),
        })


registry.register(
    name="run_prescan",
    toolset="aim-operations",
    schema={
        "type": "function",
        "function": {
            "name": "run_prescan",
            "description": (
                "Run parallel pre-sale intelligence gathering for a client website. "
                "Launches 5 reconnaissance threads simultaneously: "
                "1) website structure (services, doctors, prices), "
                "2) financial data from tax filings (revenue, profit), "
                "3) quick SEO scan (meta tags, mobile, SSL, speed), "
                "4) reviews snapshot (rating, what patients praise/complain about), "
                "5) social media presence (platforms, last post). "
                "Use this at the START of PRESALE — before searching for competitors — "
                "to gather client context and show immediate value. "
                "Takes 60-90 seconds. "
                "Returns aggregated intelligence: specialization, city, services, "
                "doctors, revenue, SEO score/issues, rating, reviews themes, social links."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "url": {
                        "type": "string",
                        "description": "Client clinic website URL (e.g., 'https://clinic.ru')",
                    },
                },
                "required": ["url"],
            },
        },
    },
    handler=handle_run_prescan,
    check_fn=lambda: True,
    is_async=True,
    description="Parallel pre-sale intelligence: website structure + financials + SEO + reviews + social (60-90s)",
    emoji="🔎",
)
