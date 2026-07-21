"""
run_pagespeed — Hermes tool: Google PageSpeed Insights

Analyses a website's Core Web Vitals and performance scores.
Uses Google PageSpeed Insights API (key from GOOGLE_API_KEY env) with fallback
to pagespeed.web.dev scraping via Firecrawl.

Registered in Hermes internal registry under toolset "aim-operations".
"""

import json
import logging
import os
from pathlib import Path

import httpx

from tools.registry import registry
from .firecrawl_key_bank import get_key_with_fallback, mark_exhausted, classify_exhaustion

logger = logging.getLogger(__name__)

AIM_API_BASE = "http://app:8000"
REQUEST_TIMEOUT = 60.0


async def handle_run_pagespeed(website=None, **kwargs) -> str:
    """Run Google PageSpeed Insights on a website.

    Measures Core Web Vitals (LCP, FCP, TBT, CLS) and returns
    Performance, Accessibility, Best Practices, and SEO scores.

    Args:
        website: URL to analyse (e.g., "https://clinic.ru")

    Returns:
        JSON string with scores, Core Web Vitals metrics, and improvement opportunities.
    """
    if isinstance(website, dict):
        website = website.get("website", "")

    # Fallback: if LLM forgot the URL, try the cache from run_prescan
    if not website:
        try:
            cached = Path("/tmp/hermes_last_url.txt").read_text().strip()
            if cached:
                logger.info("Using cached URL from prescan: %s", cached)
                website = cached
        except Exception:
            pass

    if not website:
        return json.dumps({"error": "website URL is required"})

    if not website.startswith(("http://", "https://")):
        website = "https://" + website

    logger.info("Running PageSpeed audit for: %s", website)

    from app.main import push_tool_progress

    push_tool_progress("pagespeed", f"Измеряю скорость загрузки {website}…")

    google_api_key = os.getenv("GOOGLE_API_KEY", "")

    try:
        # Try Google PSI API first (with key or anonymous)
        result = await _pagespeed_api(website, google_api_key, push_tool_progress)
        return json.dumps(result, ensure_ascii=False, indent=2)
    except Exception as api_error:
        logger.warning("Google PSI API failed (%s), trying Firecrawl fallback...", api_error)

    try:
        result = await _pagespeed_fallback(website, push_tool_progress)
        return json.dumps(result, ensure_ascii=False, indent=2)
    except Exception as fc_error:
        logger.exception("PageSpeed audit failed for %s", website)
        return json.dumps({"error": "PageSpeed audit failed", "detail": str(fc_error)})


async def _pagespeed_api(website: str, api_key: str, push_fn) -> dict:
    """Use Google PageSpeed Insights API (with key or anonymous)."""
    api_url = "https://www.googleapis.com/pagespeedonline/v5/runPagespeed"
    params = {"url": website, "strategy": "mobile"}
    if api_key:
        params["key"] = api_key

    async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT) as client:
        response = await client.get(api_url, params=params)
        if response.status_code == 403 and not api_key:
            raise RuntimeError("Anonymous PSI quota exceeded — need API key")
        response.raise_for_status()
        data = response.json()

    return _parse_psi_result(data, website, push_fn)


async def _pagespeed_fallback(website: str, push_fn) -> dict:
    """Fallback: use Firecrawl API to scrape pagespeed.web.dev with key rotation."""

    push_fn("pagespeed", "Замеряю через pagespeed.web.dev (может занять 20-30 сек)…")

    for attempt in range(3):
        try:
            key = get_key_with_fallback()
        except RuntimeError:
            push_fn("pagespeed", "⚠️ Нет ключей для PageSpeed")
            return {
                "url": website, "method": "none",
                "error": "No Firecrawl keys available",
                "scores": {"performance": None, "accessibility": None, "best_practices": None, "seo": None},
            }

        try:
            # Try mobile first, then desktop
            for form_factor in ["mobile", "desktop"]:
                psi_url = f"https://pagespeed.web.dev/report?url={website}&form_factor={form_factor}"
                async with httpx.AsyncClient(timeout=90.0) as client:
                    response = await client.post(
                        "https://api.firecrawl.dev/v2/scrape",
                        headers={"Authorization": f"Bearer {key}"},
                        json={
                            "url": psi_url,
                            "formats": ["markdown", "screenshot"],
                            "waitFor": 25000,
                            "onlyMainContent": True,
                            "mobile": True,
                        },
                    )
                    if response.status_code == 402:
                        err_text = response.text
                        reason = classify_exhaustion(err_text)
                        if reason:
                            mark_exhausted(key, reason)
                            logger.warning("Firecrawl 402 on pagespeed, rotating key (attempt %d)", attempt + 1)
                            break  # break form_factor loop, continue outer attempt loop

                    response.raise_for_status()
                    data = response.json()
                    markdown = data.get("data", {}).get("markdown", "")

                    # Check if we got actual scores (not loading screen)
                    if _has_scores(markdown):
                        return _parse_firecrawl_result(markdown, website, push_fn)

                    logger.warning("PageSpeed %s result has no scores, trying next format", form_factor)

            # If we exhausted all form_factors without usable data, but response was OK
            return _parse_firecrawl_result(markdown, website, push_fn)

        except httpx.HTTPStatusError as e:
            err = str(e)
            reason = classify_exhaustion(err)
            if reason:
                mark_exhausted(key, reason)
                logger.warning("Firecrawl credit exhausted on pagespeed, rotating (attempt %d)", attempt + 1)
                continue
            logger.warning("Firecrawl PageSpeed fallback failed (attempt %d): %s", attempt + 1, e)
            if attempt == 2:
                push_fn("pagespeed", f"⚠️ Не удалось измерить скорость")
                return {
                    "url": website, "method": "firecrawl_failed", "error": str(e)[:500],
                    "scores": {"performance": None, "accessibility": None, "best_practices": None, "seo": None},
                }
        except Exception as e:
            logger.warning("Firecrawl PageSpeed unexpected error (attempt %d): %s", attempt + 1, e)
            if attempt == 2:
                push_fn("pagespeed", f"⚠️ Не удалось измерить скорость")
                return {
                    "url": website, "method": "firecrawl_failed", "error": str(e)[:500],
                    "scores": {"performance": None, "accessibility": None, "best_practices": None, "seo": None},
                }

    push_fn("pagespeed", "⚠️ Все ключи Firecrawl исчерпаны")
    return {
        "url": website, "method": "all_keys_exhausted",
        "error": "All Firecrawl keys exhausted",
        "scores": {"performance": None, "accessibility": None, "best_practices": None, "seo": None},
    }


def _has_scores(markdown: str) -> bool:
    """Check if the scraped page contains actual PageSpeed scores."""
    import re
    # Look for score patterns like "76" near "Performance" or numbers in the 0-100 range
    score_indicators = [
        r"[Pp]erformance[:\s]*\d{1,3}",
        r"[Aa]ccessibility[:\s]*\d{1,3}",
        r"\d{1,3}\s*/\s*100",
        r"Core Web Vitals",
        r"LCP",
        r"FCP",
        r"Largest Contentful Paint",
    ]
    for pattern in score_indicators:
        if re.search(pattern, markdown):
            return True
    return False


def _parse_psi_result(data: dict, website: str, push_fn) -> dict:
    """Parse Google PSI API response."""
    lighthouse = data.get("lighthouseResult", {})
    categories = lighthouse.get("categories", {})
    audits = lighthouse.get("audits", {})

    scores = {}
    for cat_name in ["performance", "accessibility", "best-practices", "seo"]:
        cat = categories.get(cat_name, {})
        scores[cat_name] = cat.get("score", 0) * 100 if cat.get("score") is not None else None
        if scores[cat_name] is not None:
            scores[cat_name] = round(scores[cat_name])

    # Core Web Vitals from loadingExperience
    loading = data.get("loadingExperience", {})
    origin = data.get("originLoadingExperience", {})

    def extract_cwv(exp):
        if not exp:
            return {}
        metrics = exp.get("metrics", {})
        return {
            "largest_contentful_paint": _metric_val(metrics, "LARGEST_CONTENTFUL_PAINT_MS"),
            "first_contentful_paint": _metric_val(metrics, "FIRST_CONTENTFUL_PAINT_MS"),
            "total_blocking_time": _metric_val(metrics, "TOTAL_BLOCKING_TIME_MS"),
            "cumulative_layout_shift": _metric_val(metrics, "CUMULATIVE_LAYOUT_SHIFT_SCORE"),
        }

    perf_score = scores.get("performance", 0) or 0
    if perf_score >= 90:
        assessment = "отличная — сайт летает"
    elif perf_score >= 70:
        assessment = "хорошая — есть резервы для улучшения"
    elif perf_score >= 50:
        assessment = "средняя — нужна оптимизация"
    elif perf_score > 0:
        assessment = "плохая — сайт тормозит, теряют клиентов"
    else:
        assessment = "не измерена"

    push_fn("pagespeed", f"✅ PageSpeed: {perf_score}/100 — {assessment}")

    return {
        "url": website,
        "method": "api",
        "scores": scores,
        "core_web_vitals": {
            "page": extract_cwv(loading),
            "origin": extract_cwv(origin),
        },
        "assessment": assessment,
        "cwv_passed": perf_score >= 70,
    }


def _parse_firecrawl_result(markdown: str, website: str, push_fn) -> dict:
    """Parse Firecrawl-scraped pagespeed.web.dev markdown."""
    import re

    scores = {"performance": None, "accessibility": None, "best_practices": None, "seo": None}

    # Multiple regex patterns for different markdown formats
    # Pattern 1: "Performance 76" or "Performance: 76"
    perf_patterns = [
        r"[Pp]erformance[:\s]*(\d{1,3})",
        r"Производительность[:\s]*(\d{1,3})",
    ]
    for pat in perf_patterns:
        m = re.search(pat, markdown)
        if m:
            scores["performance"] = int(m.group(1))
            break

    acc_patterns = [
        r"[Aa]ccessibility[:\s]*(\d{1,3})",
        r"Специальные\s*возможности[:\s]*(\d{1,3})",
    ]
    for pat in acc_patterns:
        m = re.search(pat, markdown)
        if m:
            scores["accessibility"] = int(m.group(1))
            break

    bp_patterns = [
        r"[Bb]est\s*[Pp]ractices[:\s]*(\d{1,3})",
        r"Оптимальные\s*практики[:\s]*(\d{1,3})",
    ]
    for pat in bp_patterns:
        m = re.search(pat, markdown)
        if m:
            scores["best_practices"] = int(m.group(1))
            break

    seo_patterns = [
        r"SEO[:\s]*(\d{1,3})",
        r"Поисковая\s*оптимизация[:\s]*(\d{1,3})",
    ]
    for pat in seo_patterns:
        m = re.search(pat, markdown)
        if m:
            scores["seo"] = int(m.group(1))
            break

    # Fallback: look for any "NN/100" or "NN / 100" patterns
    if all(v is None for v in scores.values()):
        score_matches = re.findall(r'(\d{1,3})\s*/\s*100', markdown)
        if len(score_matches) >= 4:
            scores["performance"] = int(score_matches[0])
            scores["accessibility"] = int(score_matches[1])
            scores["best_practices"] = int(score_matches[2])
            scores["seo"] = int(score_matches[3])

    perf_score = scores.get("performance", 0) or 0
    if perf_score >= 90:
        assessment = "отличная — сайт летает"
    elif perf_score >= 70:
        assessment = "хорошая — есть резервы для улучшения"
    elif perf_score >= 50:
        assessment = "средняя — нужна оптимизация"
    elif perf_score > 0:
        assessment = "плохая — сайт тормозит, теряют клиентов"
    else:
        assessment = "не удалось определить (возможно, страница заблокировала измерение)"

    push_fn("pagespeed", f"✅ PageSpeed: {perf_score}/100 — {assessment}")

    return {
        "url": website,
        "method": "firecrawl",
        "scores": scores,
        "assessment": assessment,
        "raw_excerpt": markdown[:800] if markdown else "",
    }


def _metric_val(metrics, key):
    """Extract metric percentile value."""
    m = metrics.get(key)
    if not m:
        return None
    return {"percentile": m.get("percentile"), "category": m.get("category")}


registry.register(
    name="run_pagespeed",
    toolset="aim-operations",
    schema={
        "type": "function",
        "function": {
            "name": "run_pagespeed",
            "description": (
                "Measure website performance with Google PageSpeed Insights. "
                "Returns Core Web Vitals (LCP, FCP, TBT, CLS) and scores for "
                "Performance, Accessibility, Best Practices, and SEO (0-100). "
                "Use this to check a competitor's site speed — slow sites lose clients. "
                "Also reports whether Core Web Vitals are passed or failed."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "website": {
                        "type": "string",
                        "description": "[REQUIRED] Website URL to analyse (e.g., 'https://clinic.ru')",
                    },
                },
                "required": ["website"],
            },
        },
    },
    handler=handle_run_pagespeed,
    check_fn=lambda: True,
    is_async=True,
    description="Measure Core Web Vitals and performance scores (0-100) for a website via PageSpeed Insights",
    emoji="⚡",
)
