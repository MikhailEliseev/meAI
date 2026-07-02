"""
run_seo_audit — Hermes tool: SEO Audit

POST http://aim-app:8000/api/seo/audit → starts async CI pipeline
GET  http://aim-app:8000/api/seo/audit/{task_id} → polls until done

Runs a full SEO audit on a client website: technical analysis, keyword positions,
competitor comparison, backlink profile. Returns patient acquisition potential
(3 key numbers: patients/month, time-to-result, cost-per-patient).

Registered in Hermes internal registry under toolset "aim-operations".
"""

import asyncio
import json
import logging
import os
import time

import httpx

from app.tools._url_utils import recover_url_from_context
from tools.registry import registry

logger = logging.getLogger(__name__)

# In-memory SEO audit cache: URL → (timestamp, result_json)
# Prevents duplicate API calls within the same session (TTL = 10 min)
_seo_cache: dict[str, tuple[float, str]] = {}
_SEO_CACHE_TTL = 600  # 10 minutes


def _normalize_args(first_param, defaults):
    """If hermes-agent passes the whole arguments object as first_param, extract all values."""
    if isinstance(first_param, dict):
        return {k: first_param.get(k, defaults[k]) for k in defaults}
    return None


AIM_API_BASE = "http://aim-app:8000"
REQUEST_TIMEOUT = 600.0  # full async pipeline: start + polling + competitor crawling
POLL_INTERVAL = 2.0       # seconds between status checks


def _compute_wow_numbers(findings: dict) -> dict:
    """Compute WOW estimates from available phase data when phase_7 (strategist) is missing.

    Uses phases 1-4 (scout, auditor, deep-analyzer, reputation) to produce rough but
    data-driven estimates for patients/month, time-to-result, and cost-per-patient.
    """
    # Phase 1 — competitors found
    phase1 = findings.get("phase_1", {})
    scout_result = phase1.get("result", {}) if isinstance(phase1, dict) else {}
    competitors = scout_result.get("top_for_analysis", [])
    competitor_count = len(competitors) if isinstance(competitors, list) else 0

    # Phase 2 — audit scores (average across competitors)
    phase2 = findings.get("phase_2", {})
    auditor_result = phase2.get("result", {}) if isinstance(phase2, dict) else {}
    audit_scores = auditor_result.get("scores", {}) or {}
    avg_competitor_score = 0
    if isinstance(audit_scores, dict):
        scores = [v for v in audit_scores.values() if isinstance(v, (int, float))]
        if scores:
            avg_competitor_score = sum(scores) / len(scores)

    # Phase 4 — reputation data
    phase4 = findings.get("phase_4", {})
    rep_result = phase4.get("result", {}) if isinstance(phase4, dict) else {}
    avg_rating = rep_result.get("avg_rating", 0) or 0

    # Estimations based on competitive landscape signals
    # More competitors + weak scores = more patients to capture
    base_patients = 10 + competitor_count * 5
    if avg_competitor_score < 50:
        base_patients += 15
    elif avg_competitor_score < 70:
        base_patients += 5

    # Time: weak competitors = faster results
    if avg_competitor_score < 50:
        time_weeks = 4
    elif avg_competitor_score < 70:
        time_weeks = 8
    else:
        time_weeks = 12

    # Cost: more competitors = higher acquisition cost
    if competitor_count <= 2:
        cost = 800
    elif competitor_count <= 5:
        cost = 1200
    else:
        cost = 1800

    # Adjust for low-rated competitors (easier to beat)
    if avg_rating > 0 and avg_rating < 4.0:
        cost = max(500, cost - 300)

    return {
        "patients_per_month": max(5, base_patients),
        "time_to_result_weeks": time_weeks,
        "cost_per_patient_rub": cost,
        "is_estimated": True,
    }


def _compact_quick_result(data: dict) -> dict:
    """Build compact result from quick-tier synchronous response.

    Quick tier returns flat fields (chat_summary, feature_matrix, wow, etc.)
    instead of the nested findings/{phase_N} structure of deep tier.
    """
    wow = data.get("wow") or {}
    feature_matrix = data.get("feature_matrix", {}) or {}
    pricing = data.get("pricing_comparison", {}) or {}
    positioning = data.get("positioning_map", {}) or {}

    # Extract competitors from feature_matrix keys
    competitors = []
    if isinstance(feature_matrix, dict):
        for name, features in feature_matrix.items():
            competitors.append({
                "name": name,
                "url": features.get("url", name) if isinstance(features, dict) else name,
            })

    return {
        "wow": {
            "patients_per_month": wow.get("patients_per_month"),
            "time_to_result_weeks": wow.get("time_to_result_weeks"),
            "cost_per_patient_rub": wow.get("cost_per_patient_rub"),
        },
        "market": {
            "competitive_intensity": positioning.get("competitive_intensity", "unknown"),
            "digital_maturity": positioning.get("digital_maturity", "unknown"),
            "niche_size": positioning.get("market_size", "unknown"),
        },
        "competitors": competitors[:5],
        "feature_matrix": feature_matrix,
        "pricing_comparison": pricing,
        "positioning_map": positioning,
        "best_practices": data.get("steal_worthy_tactics", []) or [],
        "top_recommendation": data.get("top_recommendation", ""),
        "chat_summary": data.get("chat_summary", ""),
        "meta": {
            "tier": "quick",
            "phases": len(data.get("phases_executed", [])),
            "time_seconds": data.get("duration_seconds"),
            "quality_score": data.get("quality_score"),
        },
    }


def _compact_audit_result(data: dict) -> dict:
    """Extract only LLM-essential metrics from the full CI result (18K → ~2K)."""
    findings = data.get("findings", {})

    # Helper: safely slice any iterable
    def _take(obj, n):
        if isinstance(obj, list):
            return obj[:n]
        if isinstance(obj, dict):
            return {k: obj[k] for k in list(obj.keys())[:n]}
        return obj

    # Phase 7 (ci-strategist) — 3 WOW numbers + insights (only at deep/full tier)
    phase7 = findings.get("phase_7", {})
    strat_result = phase7.get("result", {}) if isinstance(phase7, dict) else {}
    estimates = strat_result.get("estimates", {}) or {}

    # If phase_7 missing (quick tier), compute WOW from phases 1-4
    if not estimates or not any(estimates.values()):
        estimates = _compute_wow_numbers(findings)

    insights = _take(strat_result.get("insights", []), 5)
    opportunities = _take(strat_result.get("opportunities", []), 3)
    landscape = strat_result.get("landscape", {}) or {}

    # Phase 1 (ci-scout) — competitors found
    phase1 = findings.get("phase_1", {})
    scout_result = phase1.get("result", {}) if isinstance(phase1, dict) else {}
    competitors = _take(scout_result.get("top_for_analysis", []), 5)

    # Phase 9 (ci-prioritizer) — action items
    phase9 = findings.get("phase_9", {})
    prio_result = phase9.get("result", {}) if isinstance(phase9, dict) else {}
    actions = _take(prio_result.get("action_items", []), 5)

    return {
        "wow": {
            "patients_per_month": estimates.get("patients_per_month"),
            "time_to_result_weeks": estimates.get("time_to_result"),
            "cost_per_patient_rub": estimates.get("cost_per_patient"),
        },
        "market": {
            "competitive_intensity": landscape.get("competitive_intensity", "unknown"),
            "digital_maturity": landscape.get("digital_maturity", "unknown"),
            "niche_size": landscape.get("market_size", "unknown"),
        },
        "competitors": [
            {"name": c.get("name", c.get("url", "")), "url": c.get("url", "")}
            for c in (competitors if isinstance(competitors, list) else [])
        ],
        "insights": insights if isinstance(insights, list) else [],
        "opportunities": opportunities if isinstance(opportunities, list) else [],
        "actions": actions if isinstance(actions, list) else [],
        "meta": {
            "tier": data.get("tier"),
            "phases": len(data.get("phases_executed", [])),
            "time_seconds": data.get("execution_time_seconds"),
            "quality_score": data.get("quality_score"),
        },
    }


async def _direct_technical_audit(url: str) -> dict:
    """Прямой технический аудит сайта (бесплатно, без API).

    Парсит HTML сайта и проверяет:
    - H1, meta title, meta description
    - Open Graph tags, Twitter Cards
    - Schema.org JSON-LD (MedicalBusiness, Physician, FAQPage)
    - robots.txt, sitemap.xml
    - Размер HTML, число скриптов, lazy loading
    - HTTPS, HTTP/2, SSL
    """
    import re as _re
    result = {
        "url": url,
        "checks": {},
        "issues": [],
        "recommendations": [],
    }
    try:
        async with httpx.AsyncClient(timeout=15.0, follow_redirects=True) as client:
            # 1. Главная страница
            resp = await client.get(url, headers={"User-Agent": "Mozilla/5.0 (compatible; AIMSeoAudit/1.0)"})
            html = resp.text
            html_size = len(html)
            num_scripts = len(_re.findall(r'<script\b', html, _re.IGNORECASE))
            num_imgs = len(_re.findall(r'<img\b', html, _re.IGNORECASE))
            num_lazy = len(_re.findall(r'loading\s*=\s*["\']lazy["\']', html, _re.IGNORECASE))

            # H1
            h1_match = _re.findall(r'<h1[^>]*>([^<]+)</h1>', html, _re.IGNORECASE)
            # meta title
            title_match = _re.search(r'<title[^>]*>([^<]+)</title>', html, _re.IGNORECASE)
            # meta description
            desc_match = _re.search(r'<meta\s+name=["\']description["\']\s+content=["\']([^"\']+)["\']', html, _re.IGNORECASE)
            # OG tags
            og_title = _re.search(r'<meta\s+property=["\']og:title["\']', html, _re.IGNORECASE)
            og_image = _re.search(r'<meta\s+property=["\']og:image["\']', html, _re.IGNORECASE)
            og_url = _re.search(r'<meta\s+property=["\']og:url["\']', html, _re.IGNORECASE)
            twitter_card = _re.search(r'<meta\s+name=["\']twitter:card["\']', html, _re.IGNORECASE)
            # Schema.org
            json_ld = _re.findall(r'<script\s+type=["\']application/ld\+json["\'][^>]*>([^<]+)</script>', html, _re.IGNORECASE)
            schema_types = []
            for j in json_ld:
                for m in _re.finditer(r'"@type"\s*:\s*"([^"]+)"', j):
                    schema_types.append(m.group(1))

            result["checks"] = {
                "html_size_kb": round(html_size / 1024, 1),
                "num_scripts": num_scripts,
                "num_images": num_imgs,
                "lazy_loaded_images": num_lazy,
                "has_h1": bool(h1_match),
                "h1_text": h1_match[0].strip()[:100] if h1_match else None,
                "has_title": bool(title_match),
                "title_text": title_match.group(1).strip()[:120] if title_match else None,
                "has_meta_description": bool(desc_match),
                "meta_description": desc_match.group(1).strip()[:200] if desc_match else None,
                "has_og_title": bool(og_title),
                "has_og_image": bool(og_image),
                "has_og_url": bool(og_url),
                "has_twitter_card": bool(twitter_card),
                "schema_types_found": schema_types[:10],
                "has_medical_schema": any(t in schema_types for t in ("MedicalBusiness", "Physician", "MedicalClinic", "Hospital", "Dentist")),
                "has_faq_schema": "FAQPage" in schema_types,
                "has_llms_txt": False,  # проверим ниже
                "http_status": resp.status_code,
                "final_url": str(resp.url),
                "redirected": str(resp.url) != url,
            }

            # 2. robots.txt
            try:
                robots_resp = await client.get(f"{url.rstrip('/')}/robots.txt")
                if robots_resp.status_code == 200:
                    robots_text = robots_resp.text[:1000]
                    sitemap_in_robots = "sitemap" in robots_text.lower()
                    result["checks"]["robots_txt"] = True
                    result["checks"]["sitemap_in_robots"] = sitemap_in_robots
                else:
                    result["checks"]["robots_txt"] = False
            except Exception:
                result["checks"]["robots_txt"] = False

            # 3. sitemap.xml
            try:
                sm_resp = await client.get(f"{url.rstrip('/')}/sitemap.xml")
                result["checks"]["sitemap_xml"] = (sm_resp.status_code == 200)
            except Exception:
                result["checks"]["sitemap_xml"] = False

            # 4. llms.txt (новый стандарт для AI-поиска)
            try:
                llms_resp = await client.get(f"{url.rstrip('/')}/llms.txt")
                if llms_resp.status_code == 200:
                    result["checks"]["has_llms_txt"] = True
            except Exception:
                pass

            # SSL/HTTPS
            result["checks"]["https_enabled"] = url.startswith("https://")

        # Issues & recommendations
        c = result["checks"]
        if not c.get("has_h1"):
            result["issues"].append("КРИТИЧНО: нет <h1> на главной странице")
            result["recommendations"].append("Добавить H1 на главную страницу с ключевым запросом")
        if not c.get("has_meta_description"):
            result["issues"].append("НЕТ meta description — поисковики не видят описание сайта")
            result["recommendations"].append("Добавить meta description (150-160 символов)")
        if not c.get("has_og_title") or not c.get("has_og_image"):
            result["issues"].append("Неполные Open Graph теги — плохой preview при шеринге")
            result["recommendations"].append("Внедрить полные OG-теги: og:title, og:image, og:url")
        if not c.get("has_twitter_card"):
            result["issues"].append("Нет Twitter Cards")
        if not c.get("has_medical_schema"):
            result["issues"].append("КРИТИЧНО: нет MedicalBusiness/Physician Schema — нейросети (ChatGPT, Perplexity) не поймут что это клиника")
            result["recommendations"].append("Внедрить MedicalBusiness Schema.org JSON-LD")
        if not c.get("has_faq_schema"):
            result["recommendations"].append("Добавить FAQPage Schema для голосового и AI-поиска")
        if not c.get("has_llms_txt"):
            result["recommendations"].append("Создать llms.txt в корне — стандарт для AI-поиска (GEO)")
        if c.get("html_size_kb", 0) > 5000:
            result["issues"].append(f"Страница слишком тяжёлая: {c['html_size_kb']} KB (норма до 5000)")
        if c.get("num_scripts", 0) > 50:
            result["issues"].append(f"Слишком много скриптов: {c['num_scripts']} (норма до 30)")
        if c.get("num_images", 0) > 10 and c.get("lazy_loaded_images", 0) < c.get("num_images", 0) * 0.5:
            result["recommendations"].append("Добавить lazy loading для изображений")
        if not c.get("sitemap_xml"):
            result["recommendations"].append("Создать sitemap.xml и добавить в robots.txt")
        if not c.get("https_enabled"):
            result["issues"].append("КРИТИЧНО: сайт не использует HTTPS")

    except Exception as e:
        result["error"] = str(e)

    return result


async def handle_run_seo_audit(url=None, competitors=None, **kwargs) -> str:
    """Run a full SEO audit on a client website.

    Starts async CI pipeline, polls until complete, returns compact result.

    Args:
        url: Website URL to audit (e.g., "https://clinic.ru")
        competitors: Optional list of competitor URLs for comparison

    Returns:
        JSON string with audit results including:
        - patients_per_month: estimated monthly patient acquisition
        - time_to_result: estimated weeks to first results
        - cost_per_patient: estimated acquisition cost
    """
    unpacked = _normalize_args(url, {"url": "", "competitors": None})
    if unpacked:
        url = unpacked["url"]
        if competitors is None:
            competitors = unpacked.get("competitors")

    # ── Fallback: GLM-5.2 не передаёт URL в arguments, только в сообщении ──
    if not url:
        session_id_local = kwargs.get("session_id", "") or os.getenv("PIPELINE_SESSION_ID", "")
        recovered = recover_url_from_context(session_id_local, kwargs)
        if recovered:
            url = recovered
            if not url.startswith(("http://", "https://")):
                url = "https://" + url
            logger.info("run_seo_audit: URL recovered via fallback: %s", url)

    # Auto-prepend https:// if URL has no protocol
    if url and not url.startswith(("http://", "https://")):
        url = "https://" + url

    # Build cache key: URL + sorted competitor list fingerprint
    _cache_key = url or ""
    if competitors:
        _cache_key += "|" + ",".join(sorted(str(c) for c in competitors))

    # Check cache — prevent duplicate API calls within the same session
    cached = _seo_cache.get(_cache_key)
    if cached is not None:
        cached_ts, cached_result = cached
        if time.time() - cached_ts < _SEO_CACHE_TTL:
            logger.info("SEO audit cache HIT for key: %s (age=%.0fs)", _cache_key, time.time() - cached_ts)
            return cached_result
        else:
            del _seo_cache[_cache_key]
            logger.info("SEO audit cache EXPIRED for key: %s", _cache_key)

    logger.info("Running SEO audit for URL: %s", url)

    from app.main import push_tool_progress

    try:
        push_tool_progress("seo", f"🔍 Захожу на сайт {url}…")

        async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT) as client:
            # Step 1: Start audit (quick tier returns sync result, deep/full returns task_id)
            push_tool_progress("seo", "⚙️ Запускаю технический аудит…")
            start_response = await client.post(
                f"{AIM_API_BASE}/api/seo/audit",
                json={"url": url, "tier": "quick", "competitors": competitors or []},
            )
            start_response.raise_for_status()
            start_data = start_response.json()

            # Quick tier: synchronous response with success/error fields, no task_id
            task_id = start_data.get("task_id")
            if not task_id:
                if start_data.get("error"):
                    logger.error("SEO audit quick tier failed: %s", start_data["error"])
                    return json.dumps({
                        "error": "SEO audit failed",
                        "detail": start_data["error"],
                    })
                push_tool_progress("seo", "✅ SEO-аудит готов!")
                compact = _compact_quick_result(start_data)
                # Добавляем технический аудит через прямой scrape (бесплатно)
                tech_audit = await _direct_technical_audit(url)
                if tech_audit:
                    compact["technical_audit"] = tech_audit
                result_json = json.dumps(compact, ensure_ascii=False, indent=2)
                _seo_cache[_cache_key] = (time.time(), result_json)
                logger.info("SEO audit quick tier completed: compacted %d chars, cached (key=%s)", len(result_json), _cache_key)
                return result_json

            logger.info("SEO audit task started (deep/full): %s", task_id)

            # Step 2 (deep/full tier): Poll until done
            status_url = f"{AIM_API_BASE}/api/seo/audit/{task_id}"
            progress_messages = [
                "📊 Анализирую структуру сайта…",
                "🔗 Проверяю техническое SEO…",
                "🏗️ Изучаю архитектуру и контент…",
                "📊 Собираю WOW-цифры…",
            ]
            poll_count = 0

            while True:
                await asyncio.sleep(POLL_INTERVAL)
                poll_count += 1

                status_response = await client.get(status_url)
                status_response.raise_for_status()
                status_data = status_response.json()

                st = status_data.get("status", "unknown")
                progress_msg = status_data.get("progress", "")

                if st == "done":
                    push_tool_progress("seo", "✅ SEO-аудит готов!")
                    data = status_data.get("result", {})
                    compact = _compact_audit_result(data)
                    result_json = json.dumps(compact, ensure_ascii=False, indent=2)
                    _seo_cache[_cache_key] = (time.time(), result_json)
                    logger.info("SEO audit completed (task %s): %d polls, compacted %d chars, cached",
                                task_id, poll_count, len(result_json))
                    return result_json

                if st == "error":
                    err = status_data.get("error", "Unknown error")
                    logger.error("SEO audit failed (task %s): %s", task_id, err)
                    return json.dumps({
                        "error": "SEO audit failed",
                        "detail": err,
                    })

                # Rotate progress messages every few polls
                if progress_msg:
                    push_tool_progress("seo", progress_msg)
                else:
                    idx = (poll_count // 3) % len(progress_messages)
                    push_tool_progress("seo", progress_messages[idx])

    except httpx.HTTPStatusError as e:
        logger.error("AIM API returned error for SEO audit: %s", e)
        return json.dumps({
            "error": "AIM API returned an error",
            "status": e.response.status_code,
            "detail": str(e),
        })
    except httpx.RequestError as e:
        logger.error("Cannot reach AIM API for SEO audit: %s", e)
        return json.dumps({
            "error": "Cannot reach AIM API",
            "detail": str(e),
        })
    except Exception as e:
        logger.exception("Unexpected error in SEO audit handler")
        return json.dumps({
            "error": "Unexpected error in tool handler",
            "detail": str(e),
        })


registry.register(
    name="run_seo_audit",
    toolset="aim-operations",
    schema={
            "name": "run_seo_audit",
            "description": (
                "Run a full SEO audit on a client website: technical analysis, "
                "keyword positions, competitor comparison, backlink profile. "
                "Returns patient acquisition potential (3 key numbers: "
                "patients/month, time-to-result, cost-per-patient)."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "url": {
                        "type": "string",
                        "description": "Website URL to audit (e.g., 'https://clinic.ru')",
                    },
                },
                "required": ["url"],
            },
        },
    handler=handle_run_seo_audit,
    check_fn=lambda: True,
    is_async=True,
    description="Run a full SEO audit on a client website and return patient acquisition potential",
    emoji="🔍",
)
