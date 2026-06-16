"""
run_prescan — Hermes tool: 3-Stage Ultra-Deep Pre-Sale Intelligence Gathering

Calls POST http://app:8000/api/presale/prescan-staged (3-stage pipeline):
  Stage 1 (20-30s): Financial hook — revenue, profit, legal entity, specialization
  Stage 2 (40-60s): Under the hood — licenses, founders, deep SEO, reviews, social
  Stage 3 (60-90s): Market — Yandex/Google Maps, nearby competitors, content audit

Falls back to legacy /api/presale/prescan if staged endpoint returns 404.

Progress messages streamed via push_tool_progress after each stage.
Target: 60-90 seconds total.

Registered in Hermes internal registry under toolset "aim-operations".
"""

import json
import logging

import httpx

from tools.registry import registry

logger = logging.getLogger(__name__)

AIM_API_BASE = "http://app:8000"
REQUEST_TIMEOUT = 900.0  # prescan can take 6-10 min (Apify, INN scraping, rusprofile)


async def handle_run_prescan(url=None, **kwargs) -> str:
    """Run 3-stage ultra-deep intelligence gathering for a client website.

    Stages:
      1. Financial hook — revenue, profit, legal entity, specialization
      2. Under the hood — licenses, founders, deep SEO, reviews, social
      3. Market — maps, competitors, revenue trends, content audit

    Progress messages pushed via push_tool_progress as each stage completes.

    Args:
        url: Client clinic website URL (e.g., "https://clinic.ru")

    Returns:
        JSON string with staged results and denormalized backward-compat fields.
    """
    if isinstance(url, dict):
        url = url.get("url", "")

    if not url:
        return json.dumps({"error": "url is required"})

    if not url.startswith(("http://", "https://")):
        url = "https://" + url

    logger.info("Running staged prescan for URL: %s", url)

    from app.main import push_tool_progress

    try:
        push_tool_progress(
            "prescan",
            "🎭 Запускаю 5 агентов разведки: сайт, финансы, лицензии, SEO, отзывы. Первый этап через 20-30 секунд…",
        )

        async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT) as client:
            response = await client.post(
                f"{AIM_API_BASE}/api/presale/prescan-staged",
                json={"url": url, "force_refresh": False},
            )

            # ── Fallback to legacy prescan if staged endpoint not deployed ──
            if response.status_code == 404:
                logger.info(
                    "Staged prescan not available — falling back to legacy prescan"
                )
                return await _legacy_prescan(client, url, push_tool_progress)

            response.raise_for_status()
            data = response.json()

            if not data.get("success"):
                logger.warning("run_prescan returned error: %s", data.get("error"))
                return json.dumps({
                    "error": "Prescan failed",
                    "detail": data.get("error", "Unknown error"),
                })

        # ── Extract stage data ──────────────────────────────────────────
        profile_data = data.get("profile_data", {})
        stage_1 = profile_data.get("stage_1", {})
        stage_2 = profile_data.get("stage_2", {})
        stage_3 = profile_data.get("stage_3", {})
        errors = profile_data.get("_errors", [])

        # ── Stage 1 narration ───────────────────────────────────────────
        _narrate_stage_1(stage_1, push_tool_progress)

        # ── Stage 2 narration ───────────────────────────────────────────
        _narrate_stage_2(stage_2, push_tool_progress)

        # ── Stage 3 narration ───────────────────────────────────────────
        _narrate_stage_3(stage_1, stage_2, stage_3, push_tool_progress)

        # ── Build merged summary ────────────────────────────────────────
        summary = _build_merged_summary(url, data, stage_1, stage_2, stage_3, errors)

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


# ── Stage narrators ────────────────────────────────────────────────────────


def _narrate_stage_1(stage_1: dict, push_fn) -> None:
    """Push Stage 1 progress: financial hook."""
    legal = stage_1.get("legal_entity", {})
    revenue = stage_1.get("revenue", {})
    spec = stage_1.get("specialization", "")
    city = stage_1.get("city", "")

    rev_val = revenue.get("latest")
    profit_val = stage_1.get("profit", {}).get("latest")
    legal_name = legal.get("legal_name", "")
    years = _compute_years_on_market(legal.get("registration_date"))

    parts = ["🔍 Этап 1/3 — Финансовый хук:"]
    if legal_name:
        parts.append(f'клиника "{legal_name}"')
    if spec and city:
        parts.append(f"{spec} в {city}")
    if rev_val:
        parts.append(f"оборот {_fmt_rub(rev_val)}")
    if profit_val:
        parts.append(f"прибыль {_fmt_rub(profit_val)}")
    if years:
        parts.append(f"на рынке {years}")

    push_fn("prescan", ", ".join(parts) if len(parts) > 1 else parts[0])


def _narrate_stage_2(stage_2: dict, push_fn) -> None:
    """Push Stage 2 progress: under the hood."""
    licenses = stage_2.get("licenses", [])
    seo = stage_2.get("seo_deep", {})
    reviews = stage_2.get("reviews", {})
    social = stage_2.get("social", {})

    lic_count = len(licenses)
    seo_score = seo.get("score", 0)
    rating = reviews.get("rating")
    reviews_count = reviews.get("count", 0)
    social_count = len(social.get("links", {}))

    parts = ["⚙️ Этап 2/3 — Под капотом:"]
    if lic_count:
        parts.append(f"лицензий {lic_count}")
    parts.append(f"SEO {seo_score}/100")
    if rating:
        parts.append(f"отзывов {reviews_count} (рейтинг {rating})")
    if social_count:
        parts.append(f"соцсетей {social_count}")

    push_fn("prescan", ", ".join(parts))


def _narrate_stage_3(stage_1: dict, stage_2: dict, stage_3: dict, push_fn) -> None:
    """Push Stage 3 progress and celebratory final message."""
    maps_data = stage_3.get("yandex_maps", {})
    competitors = stage_3.get("nearby_competitors", [])
    content = stage_3.get("content_audit", {})

    maps_rating = maps_data.get("rating") if isinstance(maps_data, dict) else None
    comp_count = len(competitors)
    pages = content.get("total_pages_estimated", 0) if isinstance(content, dict) else 0

    parts = ["🌐 Этап 3/3 — Рынок:"]
    if maps_rating:
        parts.append(f"Яндекс.Карты рейтинг {maps_rating}")
    if comp_count:
        parts.append(f"конкурентов рядом {comp_count}")
    if pages:
        parts.append(f"страниц на сайте ~{pages}")

    push_fn("prescan", ", ".join(parts))

    # Celebratory final message
    seo_score = stage_2.get("seo_deep", {}).get("score", 0)
    lic_count = len(stage_2.get("licenses", []))
    reviews_count = stage_2.get("reviews", {}).get("count", 0)
    spec = stage_1.get("specialization", "")
    city = stage_1.get("city", "")

    push_fn(
        "prescan",
        f"✅ Разведка завершена! 5 агентов проанализировали: сайт, финансы, "
        f"{lic_count} лицензий, SEO ({seo_score}/100), "
        f"{reviews_count} отзывов, соцсети, карты, "
        f"{comp_count} конкурентов и контент",
    )


# ── Merged summary builder ─────────────────────────────────────────────────


def _build_merged_summary(
    url: str, data: dict, stage_1: dict, stage_2: dict, stage_3: dict, errors: list
) -> dict:
    """Build merged JSON summary with stage blocks + denormalized fields."""
    legal = stage_1.get("legal_entity", {})
    revenue = stage_1.get("revenue", {})
    profit = stage_1.get("profit", {})
    seo = stage_2.get("seo_deep", {})
    reviews = stage_2.get("reviews", {})
    social = stage_2.get("social", {})
    maps_data = stage_3.get("yandex_maps", {})
    content = stage_3.get("content_audit", {})

    # Pre-computed speed label (anti-hallucination)
    load_speed_ms_val = seo.get("load_speed_ms", 0)
    if load_speed_ms_val > 0:
        load_speed_sec = load_speed_ms_val / 1000
        if load_speed_ms_val < 1000:
            speed_desc = "мгновенная загрузка — очень быстро"
        elif load_speed_ms_val < 2000:
            speed_desc = f"{load_speed_sec:.1f} сек — хорошая скорость"
        elif load_speed_ms_val < 3000:
            speed_desc = f"{load_speed_sec:.1f} сек — средняя скорость"
        elif load_speed_ms_val < 5000:
            speed_desc = f"{load_speed_sec:.1f} сек — медленно, нужно ускорять"
        else:
            speed_desc = f"{load_speed_sec:.1f} сек — критически медленно"
    else:
        speed_desc = "не измерена"

    # Pre-computed SEO health label
    seo_score_val = seo.get("score", 0)
    if seo_score_val >= 80:
        seo_health = f"{seo_score_val}/100 — отличное SEO, сайт хорошо оптимизирован"
    elif seo_score_val >= 60:
        seo_health = f"{seo_score_val}/100 — хорошее состояние, но есть потенциал для улучшения"
    elif seo_score_val >= 40:
        seo_health = f"{seo_score_val}/100 — среднее состояние, требуется оптимизация"
    elif seo_score_val > 0:
        seo_health = f"{seo_score_val}/100 — слабое SEO, сайт плохо виден в поиске"
    else:
        seo_health = "не оценено"

    competitors_list = stage_3.get("nearby_competitors", [])

    return {
        "url": url,
        "cached": data.get("cached", False),
        "elapsed_seconds": data.get("elapsed_seconds", 0),
        # Stage summaries for progressive narration
        "stage_1_financials": {
            "revenue": revenue,
            "profit": profit,
            "legal_name": legal.get("legal_name", ""),
            "inn": legal.get("inn", ""),
            "ogrn": legal.get("ogrn", ""),
            "registration_date": legal.get("registration_date"),
            "years_on_market": _compute_years_on_market(legal.get("registration_date")),
            "specialization": stage_1.get("specialization", ""),
            "city": stage_1.get("city", ""),
            "services": stage_1.get("services", []),
            "doctors": stage_1.get("doctors", []),
        },
        "stage_2_under_the_hood": {
            "licenses_count": len(stage_2.get("licenses", [])),
            "licenses": stage_2.get("licenses", []),
            "founders": stage_2.get("founders", []),
            "general_director": stage_2.get("general_director"),
            "seo_score": seo_score_val,
            "seo_health": seo_health,
            "seo_deep_issues": seo.get("issues", []),
            "has_sitemap": seo.get("has_sitemap", False),
            "has_structured_data": seo.get("has_structured_data", False),
            "has_mobile_viewport": seo.get("has_mobile_viewport", False),
            "has_ssl": seo.get("has_ssl", False),
            "load_speed_ms": load_speed_ms_val,
            "web_speed": speed_desc,
            "rating": reviews.get("rating"),
            "reviews_count": reviews.get("count", 0),
            "review_praise": reviews.get("praise", []),
            "review_complaints": reviews.get("complaints", []),
            "social_links": social.get("links", {}),
            "last_post_date": social.get("last_post_date"),
            "last_post_platform": social.get("last_post_platform"),
        },
        "stage_3_market": {
            "yandex_maps": maps_data if isinstance(maps_data, dict) else {},
            "google_maps": stage_3.get("google_maps", {}),
            "nearby_competitors": competitors_list,
            "nearby_competitors_count": len(competitors_list),
            "content_audit": content if isinstance(content, dict) else {},
            "revenue_trend": stage_3.get("revenue_multi_year", {}),
        },
        # Denormalized fast-access fields (backward compat)
        "specialization": stage_1.get("specialization", ""),
        "city": stage_1.get("city", ""),
        "inn": legal.get("inn", ""),
        "revenue_year": revenue.get("latest"),
        "profit_year": profit.get("latest"),
        "seo_score": seo_score_val,
        "seo_health": seo_health,
        "seo_issues": seo.get("issues", []),
        "rating": reviews.get("rating"),
        "reviews_count": reviews.get("count", 0),
        "review_praise": reviews.get("praise", []),
        "review_complaints": reviews.get("complaints", []),
        "social_links": social.get("links", {}),
        "web_speed": speed_desc,
        "errors": errors,
    }


# ── Legacy fallback ────────────────────────────────────────────────────────


async def _legacy_prescan(client: httpx.AsyncClient, url: str, push_fn) -> str:
    """Fallback to old /api/presale/prescan when staged endpoint is 404."""
    push_fn("prescan", "🔍 Запускаю параллельную разведку (5 потоков)…")

    response = await client.post(
        f"{AIM_API_BASE}/api/presale/prescan",
        json={"url": url},
        timeout=120.0,
    )
    response.raise_for_status()
    data = response.json()

    if not data.get("success"):
        return json.dumps({
            "error": "Prescan failed",
            "detail": data.get("error", "Unknown error"),
        })

    result = data.get("result", {})

    # Pre-computed labels (anti-hallucination)
    load_speed_ms_val = result.get("load_speed_ms", 0)
    if load_speed_ms_val > 0:
        load_speed_sec = load_speed_ms_val / 1000
        if load_speed_ms_val < 1000:
            speed_desc = "мгновенная загрузка — очень быстро"
        elif load_speed_ms_val < 2000:
            speed_desc = f"{load_speed_sec:.1f} сек — хорошая скорость"
        elif load_speed_ms_val < 3000:
            speed_desc = f"{load_speed_sec:.1f} сек — средняя скорость"
        elif load_speed_ms_val < 5000:
            speed_desc = f"{load_speed_sec:.1f} сек — медленно, нужно ускорять"
        else:
            speed_desc = f"{load_speed_sec:.1f} сек — критически медленно"
    else:
        speed_desc = "не измерена"

    seo_score_val = result.get("seo_score", 0)
    if seo_score_val >= 80:
        seo_health = f"{seo_score_val}/100 — отличное SEO, сайт хорошо оптимизирован"
    elif seo_score_val >= 60:
        seo_health = f"{seo_score_val}/100 — хорошее состояние, но есть потенциал для улучшения"
    elif seo_score_val >= 40:
        seo_health = f"{seo_score_val}/100 — среднее состояние, требуется оптимизация"
    elif seo_score_val > 0:
        seo_health = f"{seo_score_val}/100 — слабое SEO, сайт плохо виден в поиске"
    else:
        seo_health = "не оценено"

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
        "seo_health": seo_health,
        "seo_issues": result.get("seo_issues", []),
        "has_mobile_viewport": result.get("has_mobile_viewport", False),
        "has_ssl": result.get("has_ssl", False),
        "web_speed": speed_desc,
        # Reviews
        "rating": result.get("rating"),
        "reviews_count": result.get("reviews_count", 0),
        "review_praise": result.get("review_praise", []),
        "review_complaints": result.get("review_complaints", []),
        # Social
        "last_post_date": result.get("last_post_date"),
        "last_post_platform": result.get("last_post_platform"),
        "social_links": result.get("social_links", {}),
        # Errors
        "errors": result.get("errors", []),
    }

    push_fn(
        "prescan",
        f"✅ Разведка завершена: {result.get('specialization', '')} в {result.get('city', '') or 'городе'}, "
        f"оборот ~{result.get('revenue_year', '?')} ₽, "
        f"SEO={seo_score_val}/100, "
        f"рейтинг={result.get('rating', '?')}",
    )

    return json.dumps(summary, ensure_ascii=False, indent=2)


# ── Helpers ────────────────────────────────────────────────────────────────


def _compute_years_on_market(reg_date) -> int | None:
    """Compute years since registration date.

    Handles ISO strings, integer years, and already-parsed dates.
    """
    if not reg_date:
        return None
    try:
        from datetime import datetime

        # Integer — assume it's a year (e.g. 2015)
        if isinstance(reg_date, int):
            if reg_date > 1900 and reg_date < 2100:
                return datetime.now().year - reg_date
            # Could be a Unix timestamp (seconds since epoch)
            if reg_date > 1_000_000_000:
                dt = datetime.fromtimestamp(reg_date)
                return datetime.now().year - dt.year
            return None

        # String — ISO format
        if isinstance(reg_date, str):
            dt = datetime.fromisoformat(reg_date.replace("Z", "+00:00"))
            return datetime.now().year - dt.year

        return None
    except (ValueError, TypeError):
        return None


def _fmt_rub(value) -> str:
    """Format ruble value for human reading."""
    if value is None:
        return "?"
    try:
        v = int(value)
        if v >= 1_000_000:
            return f"{v / 1_000_000:.1f} млн ₽"
        elif v >= 1_000:
            return f"{v / 1_000:.0f} тыс ₽"
        return f"{v} ₽"
    except (ValueError, TypeError):
        return str(value)


# ── Registry ───────────────────────────────────────────────────────────────

registry.register(
    name="run_prescan",
    toolset="aim-operations",
    schema={
        "type": "function",
        "function": {
            "name": "run_prescan",
            "description": (
                "3-stage ultra-deep intelligence pipeline for a client website: "
                "Stage 1 (20-30s) — financials, legal entity, website structure. "
                "Stage 2 (40-60s) — licenses, founders, deep SEO, reviews, social media. "
                "Stage 3 (60-90s) — maps, nearby competitors, revenue trends, content audit. "
                "Progress messages streamed as each stage completes. "
                "60-90 seconds total. "
                "Use this at the START of PRESALE — before searching for competitors — "
                "to gather client context and show immediate value. "
                "Returns stage-by-stage summaries (stage_1_financials, stage_2_under_the_hood, "
                "stage_3_market) plus denormalized backward-compat fields."
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
    description="3-stage intelligence pipeline (financials → deep analysis → market). Progress per stage. 60-90s",
    emoji="🔎",
)
