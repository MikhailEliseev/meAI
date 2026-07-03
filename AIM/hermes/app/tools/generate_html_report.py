"""generate_html_report — Hermes tool: Generate AIM design system HTML report.

Reads all available data from /opt/data/sessions-archive/{session_hash}/,
generates a self-contained HTML report page using AIM theme CSS classes,
and publishes it to WordPress via direct DB insert.

Called by:
  - run_full_scout.py (end of full scout pipeline)
  - finalize_research.py (when publish_html_report=True)
"""

import json
import logging
import os
import random
import string
from datetime import datetime, timezone

import pymysql

from tools.registry import registry
from app.tools.session_archive import load_all_data

logger = logging.getLogger(__name__)

def _env_with_dotenv_fallback(key: str, default: str = "") -> str:
    """Read env var, falling back to /opt/hermes/.env (dotenv format)."""
    val = os.getenv(key, "")
    if val:
        return val
    # Try reading from .env file
    for env_path in ("/opt/hermes/.env", "/opt/data/.env"):
        try:
            with open(env_path, "r") as f:
                for line in f:
                    line = line.strip()
                    if line.startswith(f"{key}=") or line.startswith(f"{key} ="):
                        return line.split("=", 1)[1].strip().strip('"').strip("'")
        except (OSError, IOError):
            continue
    return default


WP_DB_HOST = _env_with_dotenv_fallback("WP_DB_HOST", "mysql")
WP_DB_USER = _env_with_dotenv_fallback("WP_DB_USER", "wp_user")
WP_DB_PASSWORD = _env_with_dotenv_fallback("WP_DB_PASSWORD", "")
WP_DB_NAME = _env_with_dotenv_fallback("WP_DB_NAME", "wordpress")


def _esc(text: str) -> str:
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")


def _fmt_num(val, default="—"):
    if val is None:
        return default
    if isinstance(val, (int, float)):
        return str(val)
    return str(val)


def _fmt_revenue_short(val) -> str:
    """Format revenue as human-readable: 4.3 млрд ₽, 742 млн ₽, 12.5 млн ₽."""
    if val is None:
        return "—"
    if not isinstance(val, (int, float)):
        return str(val)
    if val >= 1_000_000_000:
        return f"{val / 1_000_000_000:.1f} млрд ₽"
    if val >= 1_000_000:
        return f"{val / 1_000_000:.0f} млн ₽"
    if val >= 1_000:
        return f"{val / 1_000:.0f} тыс ₽"
    return f"{int(val):,} ₽".replace(",", " ")


def _fmt_trend(trend: str) -> str:
    """Format revenue trend with arrow and color class."""
    if not trend:
        return "—"
    t = trend.lower()
    if t in ("growing", "↑", "up"):
        return '<span class="trend-up">↑ Растущий</span>'
    if t in ("declining", "↓", "down"):
        return '<span class="trend-down">↓ Падение</span>'
    if t in ("stable", "→"):
        return '<span class="trend-stable">→ Стабильный</span>'
    if t == "mixed":
        return '<span class="trend-mixed">~ Смешанный</span>'
    return _esc(trend)


def _fmt_instagram(details: dict) -> str:
    """Format Instagram: @username (~587K) or Нет."""
    username = details.get("instagram_username", "")
    subscribers = details.get("instagram_subscribers")
    if not username:
        return "Нет"
    if subscribers and isinstance(subscribers, (int, float)) and subscribers > 0:
        if subscribers >= 1_000_000:
            sub_str = f"{subscribers / 1_000_000:.1f}M"
        elif subscribers >= 1_000:
            sub_str = f"{int(subscribers / 1_000)}K"
        else:
            sub_str = str(int(subscribers))
        return f"@{username} (~{sub_str})"
    return f"@{username}"


def _build_competitor_table(details: list[dict], client_url: str = "") -> str:
    """Build HTML comparison table from competitor_details."""
    if not details:
        return '<p class="text-dim">Нет данных о конкурентах.</p>'

    rows = ""
    for i, c in enumerate(details):
        is_client = bool(client_url and c.get("url") == client_url)
        row_class = ' class="client-row"' if is_client else ""
        name = _esc(str(c.get("name", "—")))
        if is_client:
            name = f"<strong>{name}</strong>"
        revenue = _fmt_revenue_short(c.get("revenue"))
        trend = _fmt_trend(c.get("revenue_trend", ""))
        doctors = str(c.get("doctors_count")) if c.get("doctors_count") else "—"
        instagram = _fmt_instagram(c)
        seo = f"{c['seo_score']}/100" if c.get("seo_score") is not None else "—"

        rows += f"""<tr{row_class}>
  <td class="comp-name">{name}</td>
  <td class="comp-revenue">{revenue}</td>
  <td class="comp-trend">{trend}</td>
  <td class="comp-doctors">{doctors}</td>
  <td class="comp-instagram">{instagram}</td>
  <td class="comp-seo">{seo}</td>
</tr>\n"""

    return f"""<table class="comp-table">
<thead>
<tr>
  <th>Конкурент</th>
  <th>Выручка</th>
  <th>Тренд</th>
  <th>Врачей</th>
  <th>Instagram</th>
  <th>SEO</th>
</tr>
</thead>
<tbody>
{rows}</tbody>
</table>"""
    """Flatten tool-output wrapper {tool_name: json_string_or_dict} → actual data.

    Pipeline saves tool results as ``{tool_name: "{...}"}`` (JSON string) or
    ``{tool_name: {...}}`` (already a dict).  This function parses any JSON
    strings and returns a flat dict with the inner keys merged.
    """
    if not isinstance(raw, dict):
        return raw or {}
    result = {}
    for key, value in raw.items():
        if isinstance(value, str):
            try:
                inner = json.loads(value)
            except (json.JSONDecodeError, TypeError):
                inner = value
        elif isinstance(value, dict):
            inner = value
        else:
            inner = value
        # If inner has useful keys, merge them directly
        if isinstance(inner, dict):
            result.update(inner)
        else:
            result[key] = inner
    return result


def _is_error_data(val) -> bool:
    """Check if a parsed value looks like an error response, not real data."""
    if not isinstance(val, dict):
        return False
    # If only error-related keys, it's an error
    non_error_keys = [k for k in val if k not in ("error", "detail", "status")]
    if not non_error_keys:
        return True
    # If has error key and very few other keys, likely error
    if "error" in val and len(val) <= 2:
        return True
    return False


def _parse_tool_value(raw_val) -> dict | None:
    """Parse a tool output value (JSON string or dict) into a dict, skipping errors."""
    if isinstance(raw_val, str):
        try:
            parsed = json.loads(raw_val)
        except (json.JSONDecodeError, TypeError):
            return None
    elif isinstance(raw_val, dict):
        parsed = raw_val
    else:
        return None
    if _is_error_data(parsed):
        return None
    return parsed


def _normalize_pipeline_keys(data: dict) -> dict:
    """Map pipeline phase-name keys to the keys _build_report_html expects.

    v7 pipeline saves data under phase names (e.g. "TECH AUDIT", "COMPETITORS"),
    with tool outputs wrapped as ``{tool_name: json_string}``.
    This function unwraps the tool outputs and creates the aliases the report
    builder expects (e.g. "pagespeed", "competitors", "ci_analysis").

    Also copies LLM interpretations into data["interpretations"][phase_name].
    """
    # ── Extract LLM interpretations ────────────────────────────────
    interpretations = {}
    for key in list(data.keys()):
        if key.endswith("_interpretation") and isinstance(data[key], dict):
            phase_name = key[:-15]  # strip "_interpretation" (15 chars)
            content = data[key].get("content", "")
            if content:
                interpretations[phase_name] = str(content)

    data["interpretations"] = interpretations

    # ── Phase → tool → expected key mapping (v7 phase names) ──────
    _phase_tool_map = {
        "PRE-FLIGHT": {
            "web_search": "market_research",
        },
        "INSTAGRAM PROFILE": {
            "web_search": "instagram_profile",
        },
        "INSTAGRAM CONTENT": {
            "web_search": "instagram_content",
        },
        "ADS INTELLIGENCE": {
            "web_search": "ads_intelligence",
        },
        "TECH AUDIT: SPEED": {
            "run_pagespeed": "pagespeed",
        },
        "TECH AUDIT: SEO+OSINT": {
            "run_seo_audit": "seo_audit",
        },
        "SOCIAL: CROSS-PLATFORM": {
            "web_search": "social_search",
            "run_review_platforms": "social_review_platforms",
        },
        "TELEGRAM CHANNELS": {
            "web_search": "telegram_channels",
        },
        "KEY PERSONS": {
            "run_hh_analysis": "hh_analysis",
            "run_doctor_dossiers": "doctor_dossiers",
        },
        "SMI MENTIONS": {
            "run_smi_mentions": "smi_mentions",
        },
        "COMPETITOR MATRIX": {
            "find_competitors": "competitors",
            "run_ci_analysis": "ci_analysis",
        },
        "RATINGS & REVIEWS": {
            "run_review_platforms": "review_platforms",
        },
        "FINANCIAL: FNS+": {
            "find_company_financials": "financials",
        },
        "GAPS & ADVANTAGES": {
            "run_content_gaps": "content_gaps",
            "run_content_analysis": "content_analysis",
        },
    }

    for phase_key, tool_map in _phase_tool_map.items():
        phase_data = data.get(phase_key, {})
        if not isinstance(phase_data, dict):
            continue
        for tool_name, expected_key in tool_map.items():
            if expected_key not in data or not data.get(expected_key):
                if tool_name in phase_data:
                    parsed = _parse_tool_value(phase_data[tool_name])
                    if parsed is not None:
                        data[expected_key] = parsed
                else:
                    # Try unwrapped merge
                    unwrapped = _unwrap_tool_output(phase_data)
                    if unwrapped and unwrapped != phase_data and not _is_error_data(unwrapped):
                        data[expected_key] = unwrapped

    # ── CI analysis needs to be set separately ───────────────────
    if "COMPETITOR MATRIX" in data and not data.get("ci_analysis"):
        comp = data["COMPETITOR MATRIX"]
        if isinstance(comp, dict) and "run_ci_analysis" in comp:
            parsed = _parse_tool_value(comp["run_ci_analysis"])
            if parsed is not None:
                data["ci_analysis"] = parsed

    # ── Transform reviews from platforms[] → {platform: {rating, count}} ─
    for review_key in ("review_platforms", "SOCIAL: CROSS-PLATFORM", "RATINGS & REVIEWS"):
        raw = data.get(review_key, {})
        if isinstance(raw, dict):
            has_platforms_list = "platforms" in raw
            if has_platforms_list:
                platforms_list = raw.get("platforms", [])
                transformed = {}
                for p in platforms_list:
                    if isinstance(p, dict) and p.get("found"):
                        pname = p.get("platform", "Unknown")
                        transformed[pname] = {
                            "rating": p.get("rating"),
                            "reviews_count": p.get("review_count", 0),
                        }
                if transformed:
                    existing = data.get("review_platforms", {})
                    if isinstance(existing, dict):
                        existing.update(transformed)
                    else:
                        existing = transformed
                    data["review_platforms"] = existing
                break  # Only process once

    # ── Transform financials: find_company_financials → revenue_estimate ─
    fin = data.get("financials", {}) or {}
    if fin and isinstance(fin, dict) and not fin.get("revenue_estimate"):
        company = fin.get("company", {}) or {}
        if company:
            latest_rev = company.get("latest_revenue")
            if latest_rev:
                fin["revenue_estimate"] = {
                    "annual": f"{latest_rev:,.0f} ₽".replace(",", " "),
                    "monthly": f"{latest_rev / 12:,.0f} ₽".replace(",", " "),
                    "methodology": "nalog.ru (ФНС)",
                }
        data["financials"] = fin

    # ── Transform doctor_dossiers: doctor_names[] → doctors[] ─────
    docs = data.get("doctor_dossiers", {}) or {}
    if docs and isinstance(docs, dict) and not docs.get("doctors") and not docs.get("stars"):
        names = docs.get("doctor_names", []) or []
        if names:
            docs["doctors"] = [{"full_name": n} for n in names]
        data["doctor_dossiers"] = docs

    # ── Extract metadata from phase data ─────────────────────────
    meta = data.get("metadata", {}) or {}
    if not meta.get("company_name"):
        # Try to get from hh_analysis or doctor_dossiers
        for src_key in ("hh_analysis", "doctor_dossiers"):
            src = data.get(src_key, {})
            if isinstance(src, dict) and src.get("company_name"):
                meta["company_name"] = src["company_name"]
                break
    data["metadata"] = meta

    return data


def _build_report_html(data: dict, title: str) -> str:
    """Build full HTML page from session archive data using AIM CSS classes.

    Supports both legacy prescan format (stage_1/2/3) and v7 pipeline format
    (PERPLEXITY, TECH AUDIT, SOCIAL VERIFIER, etc. as phase-name keys).
    """
    data = _normalize_pipeline_keys(data)

    metadata = data.get("metadata", {}) or {}
    prescan = data.get("prescan", {}) or {}
    market_research = data.get("market_research", {}) or {}
    competitors = data.get("competitors", {}) or {}
    ci_analysis = data.get("ci_analysis", {}) or {}
    pagespeed = data.get("pagespeed", {}) or {}
    financials = data.get("financials", {}) or {}
    seo_audit = data.get("seo_audit", {}) or {}
    ads = data.get("ads_intelligence", {}) or {}
    reviews = data.get("review_platforms", {}) or {}
    doctors = data.get("doctor_dossiers", {}) or {}
    instagram = data.get("instagram_content", {}) or {}
    content_gaps = data.get("content_gaps", {}) or {}
    forum_pains = data.get("forum_pains", {}) or {}
    smi_mentions = data.get("smi_mentions", {}) or {}
    interpretations = data.get("interpretations", {}) or {}

    client_name = metadata.get("company_name") or title or "Клиника"
    client_url = metadata.get("url", "")
    city = metadata.get("city") or prescan.get("city", "")
    scan_date = metadata.get("scan_completed") or datetime.now(timezone.utc).isoformat()

    try:
        dt = datetime.fromisoformat(scan_date.replace("Z", "+00:00"))
        date_str = dt.strftime("%d.%m.%Y")
    except (ValueError, AttributeError):
        date_str = "—"

    # ── Build sections ──────────────────────────────────────────────────

    sections = []

    # Hero
    sections.append(f"""<section class="section">
  <span class="section-label">AIM Scout Report</span>
  <h1>{_esc(client_name)}</h1>
  <p class="text-dim">{_esc(city)}{' · ' + _esc(client_url) if client_url else ''}</p>
  <p class="text-meta">Исследование завершено {date_str}</p>
</section>
<hr>""")

    # ── Executive Summary ────────────────────────────────────────────────
    metrics = []

    # From legacy prescan
    prescan_fin = prescan.get("stage_1_financials", {}) or {}
    revenue = prescan_fin.get("revenue_year") or prescan_fin.get("revenue")
    if revenue:
        metrics.append(("Выручка / год", _fmt_num(revenue)))

    if prescan_fin.get("profit_year"):
        metrics.append(("Прибыль / год", _fmt_num(prescan_fin.get("profit_year"))))

    prescan_seo = prescan.get("stage_2_under_the_hood", {}) or {}
    if prescan_seo.get("seo_health"):
        metrics.append(("SEO health", _esc(str(prescan_seo.get("seo_health")))))
    if prescan_seo.get("licenses_count"):
        metrics.append(("Лицензий", _fmt_num(prescan_seo.get("licenses_count"))))
    if prescan_seo.get("reviews_count"):
        metrics.append(("Отзывов", _fmt_num(prescan_seo.get("reviews_count"))))

    prescan_market = prescan.get("stage_3_market", {}) or {}
    if prescan_market.get("nearby_competitors_count"):
        metrics.append(("Конкурентов рядом", _fmt_num(prescan_market.get("nearby_competitors_count"))))

    # From v7 pipeline data
    if market_research.get("results_count"):
        metrics.append(("Источников исследования", str(market_research.get("results_count"))))

    # Total reviews from social verifier
    total_reviews = 0
    if isinstance(reviews, dict):
        for rdata in reviews.values():
            if isinstance(rdata, dict):
                total_reviews += int(rdata.get("reviews_count", 0) or 0)
    if total_reviews > 0:
        metrics.append(("Всего отзывов", str(total_reviews)))

    # Competitors count
    comp_list = competitors.get("competitors", [])
    if not comp_list:
        comp_list = ci_analysis.get("competitors", [])
    if comp_list:
        metrics.append(("Конкурентов", str(len(comp_list))))

    if pagespeed:
        # v7 format: {scores: {mobile: {...}}}
        ps_scores = pagespeed.get("scores", {}) or {}
        mobile_ps = pagespeed.get("mobile", {}) or ps_scores.get("mobile", {}) or {}
        if mobile_ps.get("cwv_status"):
            metrics.append(("Core Web Vitals", _esc(str(mobile_ps.get("cwv_status")))))
        elif pagespeed.get("assessment"):
            metrics.append(("Скорость", _esc(str(pagespeed.get("assessment")))))

    if smi_mentions.get("total_mentions"):
        metrics.append(("Упоминаний в СМИ", _fmt_num(smi_mentions.get("total_mentions"))))

    if instagram.get("followers"):
        metrics.append(("Instagram", _fmt_num(instagram.get("followers"))))

    if metrics:
        metric_cards = ""
        for label, value in metrics[:8]:
            metric_cards += f"""<div class="metric"><div class="value">{value}</div><div class="label">{label}</div></div>\n"""
        sections.append(f"""<section class="section">
  <span class="section-label">Ключевые метрики</span>
  <h2>Обзор</h2>
  <div class="metrics">{metric_cards}</div>
</section>
<hr>""")

    # ── Market Research (PERPLEXITY / Deep Research) ───────────────────
    mr_data = market_research if isinstance(market_research, dict) else {}
    mr_results = mr_data.get("results", [])
    if not mr_results and isinstance(market_research, dict):
        # Try prescan merged data
        mr_results = market_research.get("stage_3_market", {}).get("competitors", []) if isinstance(market_research.get("stage_3_market"), dict) else []
    if mr_results:
        mr_html = ""
        for r in mr_results[:5]:
            if isinstance(r, str):
                mr_html += f'<div class="surface-card"><p>{_esc(r)}</p></div>\n'
            elif isinstance(r, dict):
                title_r = r.get("title", r.get("name", ""))
                snippet = r.get("snippet", r.get("description", r.get("content", "")))
                url_r = r.get("url", r.get("link", ""))
                mr_html += f"""<div class="surface-card">
  {f'<h4>{_esc(str(title_r))}</h4>' if title_r else ''}
  {f'<p class="text-dim">{_esc(str(snippet)[:300])}</p>' if snippet else ''}
  {f'<p class="text-meta"><a href="{_esc(url_r)}" target="_blank" rel="noopener noreferrer">Источник</a></p>' if url_r else ''}
</div>\n"""
        sections.append(f"""<section class="section">
  <span class="section-label">Исследование рынка</span>
  <h2>Deep Research</h2>
  <p class="text-meta">По запросу: {_esc(str(mr_data.get('query', '')))} · Найдено: {mr_data.get('results_count', len(mr_results))} источников</p>
  <div class="grid-1">{mr_html}</div>
</section>
<hr>""")
    elif market_research.get("query"):
        # Minimal market research card — search was done but results are unstructured
        sections.append(f"""<section class="section">
  <span class="section-label">Исследование рынка</span>
  <h2>Deep Research</h2>
  <p>{_esc(str(market_research.get('query', '')))}</p>
  <p class="text-dim">Исследование рынка выполнено. Подробные результаты включены в интерпретации фаз.</p>
</section>
<hr>""")

    # ── Competitors ──────────────────────────────────────────────────────
    competitor_details = ci_analysis.get("competitor_details", [])

    if competitor_details:
        # Structured table mode (Phase 1 v2)
        comp_table = _build_competitor_table(competitor_details, client_url)
        sections.append(f"""<section class="section">
  <span class="section-label">Конкуренты</span>
  <h2>Конкурентный ландшафт</h2>
  {comp_table}
</section>
<hr>""")
    else:
        # Legacy card mode
        comp_list = competitors.get("competitors", [])
        if not comp_list:
            comp_list = ci_analysis.get("competitors", [])
        if comp_list:
            comp_cards = ""
            for c in comp_list[:6]:
                name = c.get("brand_name") or c.get("legal_name") or c.get("name", "—")
                services = c.get("services", [])
                segment = c.get("segment", "") or (", ".join(services[:3]) if services else "")
                reviews_n = c.get("reviews_count") or c.get("reviews", "—")
                revenue_y = c.get("revenue_year")
                price = c.get("price_range", "—")
                comp_cards += f"""<div class="surface-card">
  <h3>{_esc(str(name))}</h3>
  {f'<p class="text-meta">{_esc(str(segment))}</p>' if segment else ''}
  {f'<div class="row"><span class="k">Выручка</span><span class="v">{_fmt_num(revenue_y)} ₽</span></div>' if revenue_y else ''}
  <div class="row"><span class="k">Отзывов</span><span class="v">{_esc(str(reviews_n))}</span></div>
  {f'<div class="row"><span class="k">Цены</span><span class="v">{_esc(str(price))}</span></div>' if price and price != "—" else ''}
</div>\n"""
            sections.append(f"""<section class="section">
  <span class="section-label">Конкуренты</span>
  <h2>Конкурентный ландшафт</h2>
  <div class="grid-2">{comp_cards}</div>
</section>
<hr>""")

    # ── CI Analysis ──────────────────────────────────────────────────────
    ci_gaps = ci_analysis.get("gaps_vs_competitors", []) or []
    ci_advantages = ci_analysis.get("advantages", []) or []
    if ci_gaps or ci_advantages:
        gaps_html = ""
        if ci_gaps:
            gaps_html += '<h3>Что теряете</h3>\n'
            for g in ci_gaps[:6]:
                sev = g.get("severity", "medium")
                sev_class = "gap-high" if sev == "high" else ("gap-medium" if sev == "medium" else "gap-low")
                gaps_html += f"""<div class="gap {sev_class}">
  <h4>{_esc(str(g.get('gap', '')))}</h4>
  <p class="text-dim">{_esc(str(g.get('fix', '')))}</p>
</div>\n"""

        if ci_advantages:
            gaps_html += '<h3>Уникальные преимущества</h3>\n'
            for a in ci_advantages[:4]:
                rarity = a.get("rarity", "standard")
                rarity_tag = ""
                if rarity == "unique":
                    rarity_tag = '<span class="tag-badge tag-green">unique</span>'
                elif rarity == "rare":
                    rarity_tag = '<span class="tag-badge tag-accent">rare</span>'
                else:
                    rarity_tag = '<span class="tag-badge">standard</span>'

                gaps_html += f"""<div class="gap gap-advantage">
  <h4>{_esc(str(a.get('advantage', '')))} {rarity_tag}</h4>
  <p class="text-dim">{_esc(str(a.get('monetization', '')))}</p>
</div>\n"""

        sections.append(f"""<section class="section">
  <span class="section-label">Разрывы и преимущества</span>
  <h2>Где сильны — где есть точки роста</h2>
  {gaps_html}
</section>
<hr>""")

    # ── Key Doctors ─────────────────────────────────────────────────────
    doctor_list = doctors.get("doctors") or doctors.get("stars") or []
    if not doctor_list:
        doctor_list = prescan.get("doctors") or []
    # v7 format: single doctor dossier {doctor_name, platforms, specialization, ...}
    if not doctor_list and isinstance(doctors, dict) and doctors.get("doctor_name"):
        platforms_count = doctors.get("platforms_with_presence") or doctors.get("total_profiles_found", 0)
        doctor_list = [{
            "full_name": doctors.get("doctor_name"),
            "specialization": doctors.get("specialization", ""),
            "experience": f"Найден на {platforms_count} платформах" if platforms_count else "",
        }]
    if doctor_list:
        doc_cards = ""
        for d in doctor_list[:6]:
            name = d.get("full_name") or d.get("name", "—")
            spec = d.get("specialization") or d.get("speciality", "")
            exp = d.get("experience_years") or d.get("experience", "")
            degree = d.get("degree", "")
            info = " · ".join(filter(None, [spec, degree]))
            doc_cards += f"""<div class="expert-card">
  <h4>{_esc(str(name))}</h4>
  {f'<p class="text-meta">{_esc(info)}</p>' if info else ''}
  {f'<p class="text-accent-sm">{_esc(str(exp))}</p>' if exp else ''}
</div>\n"""
        sections.append(f"""<section class="section">
  <span class="section-label">Ключевые врачи</span>
  <h2>Специалисты</h2>
  <div class="grid-2">{doc_cards}</div>
</section>
<hr>""")

    # ── PageSpeed ────────────────────────────────────────────────────────
    if pagespeed:
        # v7 format: {scores: {mobile: {...}}} or {assessment, scores, method}
        ps_scores = pagespeed.get("scores", {}) or {}
        mobile_ps = pagespeed.get("mobile", {}) or ps_scores.get("mobile", {}) or {}
        if mobile_ps:
            lcp = mobile_ps.get("lcp_seconds", "—")
            inp = mobile_ps.get("inp_ms", "—")
            cls = mobile_ps.get("cls", "—")
            lcp_dist = mobile_ps.get("lcp_distribution", {}) or {}
            inp_dist = mobile_ps.get("inp_distribution", {}) or {}
            cls_dist = mobile_ps.get("cls_distribution", {}) or {}

            sections.append(f"""<section class="section">
  <span class="section-label">Core Web Vitals</span>
  <h2>Скорость сайта</h2>
  <div class="table-wrap">
  <table>
    <tr><th>Метрика</th><th>Значение</th><th>Good</th><th>Needs Improvement</th><th>Poor</th></tr>
    <tr><td>LCP</td><td>{_esc(str(lcp))}s</td><td>{_esc(str(lcp_dist.get('good', '—')))}%</td><td>{_esc(str(lcp_dist.get('needs_improvement', '—')))}%</td><td>{_esc(str(lcp_dist.get('poor', '—')))}%</td></tr>
    <tr><td>INP</td><td>{_esc(str(inp))}ms</td><td>{_esc(str(inp_dist.get('good', '—')))}%</td><td>{_esc(str(inp_dist.get('needs_improvement', '—')))}%</td><td>{_esc(str(inp_dist.get('poor', '—')))}%</td></tr>
    <tr><td>CLS</td><td>{_esc(str(cls))}</td><td>{_esc(str(cls_dist.get('good', '—')))}%</td><td>{_esc(str(cls_dist.get('needs_improvement', '—')))}%</td><td>{_esc(str(cls_dist.get('poor', '—')))}%</td></tr>
  </table>
  </div>
</section>
<hr>""")
        elif pagespeed.get("assessment"):
            # v7 simplified format
            sections.append(f"""<section class="section">
  <span class="section-label">Скорость сайта</span>
  <h2>Core Web Vitals</h2>
  <p>{_esc(str(pagespeed.get("assessment")))}</p>
  <p class="text-meta">Метод: {_esc(str(pagespeed.get("method", "—")))}</p>
</section>
<hr>""")

    # ── SEO Audit ────────────────────────────────────────────────────────
    seo_summary = seo_audit.get("summary") or seo_audit.get("overall_score")
    seo_issues = seo_audit.get("issues") or seo_audit.get("critical_issues") or []
    if seo_summary or seo_issues:
        seo_html = f'<p>{_esc(str(seo_summary))}</p>' if seo_summary else ""
        if seo_issues:
            seo_html += '<div class="surface-block">\n'
            for issue in seo_issues[:8]:
                issue_text = issue if isinstance(issue, str) else issue.get("description", str(issue))
                severity = issue.get("severity", "") if isinstance(issue, dict) else ""
                seo_html += f'<div class="gap{(" gap-" + severity) if severity else ""}"><p>{_esc(str(issue_text))}</p></div>\n'
            seo_html += '</div>\n'
        sections.append(f"""<section class="section">
  <span class="section-label">SEO-аудит</span>
  <h2>Поисковая оптимизация</h2>
  {seo_html}
</section>
<hr>""")

    # ── Advertising ──────────────────────────────────────────────────────
    ad_data = ads.get("yandex_direct") or ads.get("summary") or ads.get("ads", [])
    if ad_data:
        ad_text = ""
        if isinstance(ad_data, str):
            ad_text = f'<p>{_esc(ad_data)}</p>'
        elif isinstance(ad_data, list):
            for item in ad_data[:5]:
                name = item.get("name", "") if isinstance(item, dict) else str(item)
                cost = item.get("cost", "") if isinstance(item, dict) else ""
                cost_html = ("<p class=\"text-dim\">" + _esc(str(cost)) + "</p>") if cost else ""
                ad_text += f'<div class="surface-card"><h4>{_esc(str(name))}</h4>{cost_html}</div>\n'
        elif isinstance(ad_data, dict):
            ad_text = f'<p>{_esc(str(ad_data))}</p>'

        sections.append(f"""<section class="section">
  <span class="section-label">Реклама</span>
  <h2>Рекламная активность</h2>
  {ad_text}
</section>
<hr>""")

    # ── Content Gaps ────────────────────────────────────────────────────
    cg_list = content_gaps.get("gaps") or content_gaps.get("recommendations") or []
    if cg_list:
        cg_html = ""
        for cg in cg_list[:8]:
            desc = cg if isinstance(cg, str) else cg.get("description", str(cg))
            cg_html += f'<div class="surface-card"><p>{_esc(str(desc))}</p></div>\n'
        sections.append(f"""<section class="section">
  <span class="section-label">Контент</span>
  <h2>Контент-анализ</h2>
  {cg_html}
</section>
<hr>""")

    # ── Reviews ──────────────────────────────────────────────────────────
    if reviews:
        rev_html = ""
        for platform, rdata in reviews.items():
            if isinstance(rdata, dict):
                rating = rdata.get("rating") or rdata.get("average_rating", "—")
                count = rdata.get("reviews_count") or rdata.get("count", "—")
                rev_html += f"""<div class="surface-card">
  <h4>{_esc(str(platform))}</h4>
  <div class="row"><span class="k">Рейтинг</span><span class="v">{_esc(str(rating))}</span></div>
  <div class="row"><span class="k">Отзывов</span><span class="v">{_esc(str(count))}</span></div>
</div>\n"""
        if rev_html:
            sections.append(f"""<section class="section">
  <span class="section-label">Отзывы</span>
  <h2>Репутация на платформах</h2>
  <div class="grid-2">{rev_html}</div>
</section>
<hr>""")

    # ── SMI Mentions ─────────────────────────────────────────────────────
    smi_sources = smi_mentions.get("sources", []) or []
    smi_media = smi_mentions.get("media_presence", "")
    smi_total = smi_mentions.get("total_mentions", 0)
    if smi_sources or smi_media or smi_total:
        smi_html = ""
        if smi_total:
            smi_html += f'<p>Упоминаний в СМИ: <strong>{_esc(str(smi_total))}</strong></p>\n'
        if smi_media:
            smi_html += f'<p>{_esc(str(smi_media))}</p>\n'
        if smi_sources:
            for s in smi_sources[:6]:
                if isinstance(s, dict):
                    src_name = s.get("source", s.get("name", ""))
                    mentions = s.get("mentions", "")
                    url_s = s.get("url", "")
                    smi_html += f"""<div class="surface-card">
  <h4>{_esc(str(src_name))}</h4>
  {f'<p class="text-dim">{_esc(str(mentions))}</p>' if mentions else ''}
  {f'<a href="{_esc(url_s)}" target="_blank" rel="noopener noreferrer" class="text-accent-link">Ссылка</a>' if url_s else ''}
</div>\n"""
        if smi_html:
            sections.append(f"""<section class="section">
  <span class="section-label">Медийное присутствие</span>
  <h2>Упоминания в СМИ</h2>
  {smi_html}
</section>
<hr>""")

    # ── Forum Pains ─────────────────────────────────────────────────────
    fp_results = forum_pains.get("results", [])
    if not fp_results:
        fp_results = forum_pains.get("findings", [])
    fp_query = forum_pains.get("query", "")
    if fp_results:
        fp_html = ""
        for r in fp_results[:6]:
            if isinstance(r, str):
                fp_html += f'<div class="surface-card"><p>{_esc(r)}</p></div>\n'
            elif isinstance(r, dict):
                title_r = r.get("title", r.get("name", ""))
                snippet = r.get("snippet", r.get("description", r.get("content", "")))
                url_r = r.get("url", r.get("link", ""))
                fp_html += f"""<div class="surface-card">
  {f'<h4>{_esc(str(title_r))}</h4>' if title_r else ''}
  {f'<p class="text-dim">{_esc(str(snippet)[:300])}</p>' if snippet else ''}
  {f'<p class="text-meta"><a href="{_esc(url_r)}" target="_blank" rel="noopener noreferrer">Источник</a></p>' if url_r else ''}
</div>\n"""
        sections.append(f"""<section class="section">
  <span class="section-label">Боли пациентов</span>
  <h2>Что обсуждают на форумах</h2>
  {f'<p class="text-meta">Поиск: {_esc(fp_query)}</p>' if fp_query else ''}
  <div class="grid-1">{fp_html}</div>
</section>
<hr>""")

    # ── Financial ───────────────────────────────────────────────────────
    rev_est = financials.get("revenue_estimate", {}) or {}
    if rev_est:
        sections.append(f"""<section class="section">
  <span class="section-label">Финансы</span>
  <h2>Финансовые показатели</h2>
  <div class="metrics">
    <div class="metric"><div class="value">{_esc(_fmt_num(rev_est.get('monthly')))}</div><div class="label">Выручка / мес</div></div>
    <div class="metric"><div class="value">{_esc(_fmt_num(rev_est.get('annual')))}</div><div class="label">Выручка / год</div></div>
  </div>
  {f'<p class="text-meta">{_esc(str(rev_est.get("methodology", "")))}</p>' if rev_est.get("methodology") else ''}
</section>
<hr>""")

    # ── Instagram ───────────────────────────────────────────────────────
    if instagram:
        ig_html = ""
        if instagram.get("followers"):
            ig_html += f'<div class="metric"><div class="value">{_esc(_fmt_num(instagram.get("followers")))}</div><div class="label">Подписчиков</div></div>'
        if instagram.get("engagement_rate") or instagram.get("er_percent"):
            er = instagram.get("engagement_rate") or instagram.get("er_percent")
            ig_html += f'<div class="metric"><div class="value">{_esc(str(er))}</div><div class="label">Engagement Rate</div></div>'
        if instagram.get("avg_likes"):
            ig_html += f'<div class="metric"><div class="value">{_esc(_fmt_num(instagram.get("avg_likes")))}</div><div class="label">Среднее лайков</div></div>'

        if ig_html:
            sections.append(f"""<section class="section">
  <span class="section-label">Соцсети</span>
  <h2>Instagram</h2>
  <div class="metrics">{ig_html}</div>
</section>
<hr>""")

    # ── Executive Insights (LLM interpretations) ────────────────────────
    if interpretations:
        insight_order = [
            "PRE-FLIGHT", "INSTAGRAM PROFILE", "INSTAGRAM CONTENT", "ADS INTELLIGENCE",
            "TECH AUDIT: SPEED", "TECH AUDIT: SEO+OSINT", "SOCIAL: CROSS-PLATFORM",
            "TELEGRAM CHANNELS", "KEY PERSONS", "SMI MENTIONS", "COMPETITOR MATRIX",
            "RATINGS & REVIEWS", "FINANCIAL: FNS+", "GAPS & ADVANTAGES",
        ]
        insight_cards = ""
        for phase_name in insight_order:
            content = interpretations.get(phase_name, "")
            if content and len(str(content).strip()) > 10:
                insight_cards += f"""<div class="surface-card">
  <h4>{_esc(phase_name)}</h4>
  <p class="text-dim">{_esc(str(content)[:500])}</p>
</div>\n"""
        if insight_cards:
            sections.append(f"""<section class="section">
  <span class="section-label">Ключевые выводы</span>
  <h2>Что это значит для бизнеса</h2>
  <div class="grid-1">{insight_cards}</div>
</section>
<hr>""")

    # ── CTA ──────────────────────────────────────────────────────────────
    sections.append("""<section class="section">
  <div class="cta-box">
    <h2>Готовы действовать?</h2>
    <p>Команда AIM реализует эти рекомендации под ключ.</p>
    <a href="https://t.me/aim_hermes_bot" class="btn" target="_blank" rel="noopener noreferrer">Связаться в Telegram</a>
  </div>
</section>""")

    # ── Footer ───────────────────────────────────────────────────────────
    sections.append(f"""<section class="section section-footer">
  <p class="text-meta">
    <a href="https://iamaim.ru" class="text-accent-link">iamaim.ru</a> · AI-first маркетинг в медицине<br>
    Этот отчёт сгенерирован автоматически
  </p>
</section>""")

    comp_table_styles = """<style>
/* ── Competitor Table (Phase 1 v2) ── */
.comp-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 0.9rem;
  margin: 1rem 0;
}
.comp-table thead th {
  text-align: left;
  padding: 0.6rem 0.8rem;
  font-weight: 500;
  font-size: 0.75rem;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  border-bottom: 2px solid var(--border, #e0e0e0);
  color: var(--text-dim, #888);
}
.comp-table tbody td {
  padding: 0.7rem 0.8rem;
  border-bottom: 1px solid var(--border, rgba(0,0,0,0.08));
  vertical-align: middle;
}
.comp-table tbody tr.client-row {
  background: var(--glass-bg, rgba(255,255,255,0.5));
  font-weight: 500;
}
.comp-table tbody tr.client-row td {
  border-bottom: 2px solid var(--accent, #c9a96e);
}
[data-theme="dark"] .comp-table tbody tr.client-row {
  background: rgba(201,169,110,0.08);
}
.comp-table tbody tr:hover {
  background: var(--glass-bg, rgba(0,0,0,0.02));
}
.trend-up { color: #2e7d32; font-weight: 500; }
.trend-down { color: #c62828; font-weight: 500; }
.trend-stable { color: #6d6d6d; }
.trend-mixed { color: #e65100; }
[data-theme="dark"] .trend-up { color: #66bb6a; }
[data-theme="dark"] .trend-down { color: #ef5350; }
[data-theme="dark"] .trend-stable { color: #9e9e9e; }
[data-theme="dark"] .trend-mixed { color: #ff9800; }
.comp-name { min-width: 160px; }
.comp-revenue { white-space: nowrap; }
.comp-trend { white-space: nowrap; }
.comp-doctors { text-align: center; }
.comp-seo { text-align: center; font-weight: 500; }
@media (max-width: 768px) {
  .comp-table { font-size: 0.8rem; }
  .comp-table thead th,
  .comp-table tbody td { padding: 0.5rem 0.4rem; }
}
</style>
"""
    return comp_table_styles + '<meta name="robots" content="noindex, nofollow">\n<div data-aim="report">\n' + "\n".join(sections) + '\n</div>'


def _random_slug(length: int = 8) -> str:
    chars = string.ascii_lowercase + string.digits
    return "".join(random.choices(chars, k=length))


def _validate_report_quality(data: dict) -> tuple[bool, list[str]]:
    """Валидация минимального качества отчёта перед публикацией.
    
    Returns:
        (is_valid, list_of_warnings)
    """
    warnings = []
    
    # 1. Проверка конкурентов
    competitors = data.get("COMPETITORS", {})
    if isinstance(competitors, dict):
        comp_list = competitors.get("competitors", [])
    else:
        comp_list = []
    
    if len(comp_list) < 3:
        warnings.append(f"⚠️ Найдено только {len(comp_list)} конкурентов (минимум 3)")
    
    # 2. Проверка врачей (если есть KEY PERSONS)
    key_persons = data.get("KEY PERSONS", {}) or data.get("KEY_PERSONS", {})
    if isinstance(key_persons, dict):
        doctors = key_persons.get("doctors", [])
        doctors_with_handles = [d for d in doctors if d.get("instagram") or d.get("instagram_username")]
        if len(doctors_with_handles) < 3:
            warnings.append(f"⚠️ Найдено только {len(doctors_with_handles)} врачей с Instagram (минимум 3)")
    
    # 3. Проверка interpretation контента (если есть)
    for phase_name in ["COMPETITORS_interpretation", "KEY PERSONS_interpretation"]:
        interpretation = data.get(phase_name, {})
        if isinstance(interpretation, dict):
            content = interpretation.get("content", "")
            if len(content) < 500:
                warnings.append(f"⚠️ {phase_name} слишком короткая ({len(content)} символов)")
    
    # Решение: блокируем только если 2+ критичных предупреждения
    is_valid = len(warnings) < 2
    
    return is_valid, warnings


async def handle_generate_html_report(
    session_hash: str = None,
    title: str = None,
    client_name: str = None,
    client_url: str = None,
    **kwargs,
) -> str:
    """Generate and publish an AIM design system HTML report from session data.

    Args:
        session_hash: Session archive key (reads /opt/data/sessions-archive/{hash}/)
        title: Report title (falls back to client_name, then metadata)
        client_name: Clinic name override (optional — read from metadata if omitted)
        client_url: Website URL override (optional — read from metadata if omitted)
    """
    if isinstance(session_hash, dict):
        d = session_hash
        session_hash = d.get("session_hash", "")
        title = title or d.get("title", "")
        client_name = client_name or d.get("client_name", "")
        client_url = client_url or d.get("client_url", "")

    if not session_hash:
        return json.dumps({"error": "session_hash is required"}, ensure_ascii=False)

    report_title = title or client_name or "AIM Scout Report"

    # Load all data from session archive
    data = load_all_data(session_hash)

    # Валидация качества данных
    is_valid, warnings = _validate_report_quality(data)
    
    if not is_valid:
        logger.error(f"Report quality validation failed for session {session_hash}: {warnings}")
        from app.main import push_wow_comment
        push_wow_comment(
            f"⚠️ Качество отчёта ниже минимума:\n" + "\n".join(warnings), 
            "error"
        )
        return json.dumps({
            "error": "Report quality below minimum threshold",
            "warnings": warnings,
            "session_hash": session_hash,
            "suggestion": "Retry pipeline with named_competitors or ensure find_doctor_handles was called"
        }, ensure_ascii=False)
    
    # Логируем warnings даже если valid
    if warnings:
        logger.warning(f"Report quality warnings for session {session_hash}: {warnings}")

    # Merge metadata overrides
    meta = data.get("metadata", {}) or {}
    if client_name:
        meta["company_name"] = client_name
    if client_url:
        meta["url"] = client_url

    # Generate HTML
    html = _build_report_html(data, report_title)

    # Publish to WordPress
    if not WP_DB_PASSWORD:
        # Save locally if no DB access
        report_path = os.path.join(
            os.getenv("SESSIONS_ROOT", "/opt/data/sessions-archive"),
            session_hash,
            "report.html",
        )
        with open(report_path, "w", encoding="utf-8") as f:
            f.write(html)
        return json.dumps({
            "status": "saved_locally",
            "path": report_path,
            "url": None,
            "session_hash": session_hash,
        }, ensure_ascii=False)

    page_slug = _random_slug()
    wp_title = f"AIM Scout — {report_title}"

    conn = None
    try:
        conn = pymysql.connect(
            host=WP_DB_HOST,
            user=WP_DB_USER,
            password=WP_DB_PASSWORD,
            database=WP_DB_NAME,
            charset="utf8mb4",
            connect_timeout=5,
        )

        now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")

        with conn.cursor() as cur:
            cur.execute("SELECT ID FROM wp_posts WHERE post_name = %s LIMIT 1", (page_slug,))
            attempts = 0
            while cur.fetchone() and attempts < 10:
                page_slug = _random_slug()
                cur.execute("SELECT ID FROM wp_posts WHERE post_name = %s LIMIT 1", (page_slug,))
                attempts += 1

            cur.execute(
                """INSERT INTO wp_posts
                   (post_author, post_date, post_date_gmt, post_content, post_title,
                    post_status, comment_status, ping_status, post_name, post_type,
                    post_excerpt, to_ping, pinged, post_content_filtered, menu_order)
                   VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)""",
                (
                    1, now, now, html, wp_title,
                    "publish", "closed", "closed", page_slug, "page",
                    "", "", "", "", 0,
                ),
            )
            post_id = cur.lastrowid
        conn.commit()

        url = f"https://iamaim.ru/{page_slug}"
        logger.info("HTML report published: session=%s post_id=%s url=%s", session_hash, post_id, url)

        return json.dumps({
            "status": "published",
            "url": url,
            "slug": page_slug,
            "post_id": post_id,
            "title": wp_title,
            "session_hash": session_hash,
        }, ensure_ascii=False)

    except pymysql.Error as e:
        logger.error("MySQL error publishing report: %s", e)
        return json.dumps({"error": f"Database error: {str(e)}"}, ensure_ascii=False)
    except Exception as e:
        logger.exception("Failed to publish report")
        return json.dumps({"error": f"Failed to publish: {str(e)}"}, ensure_ascii=False)
    finally:
        if conn:
            conn.close()


# ── Registry ──────────────────────────────────────────────────────────────
registry.register(
    name="generate_html_report",
    toolset="aim-operations",
    schema={
        "type": "function",
        "function": {
            "name": "generate_html_report",
            "description": "Генерирует и публикует HTML-отчёт в дизайн-системе AIM. "
                           "Читает все данные из session archive (/opt/data/sessions-archive/{hash}/), "
                           "строит секции (hero, метрики, конкуренты, врачи, SEO, реклама, отзывы, финансы), "
                           "и публикует как WordPress страницу на iamaim.ru. "
                           "Вызывается автоматически в конце run_full_scout.",
            "parameters": {
                "type": "object",
                "properties": {
                    "session_hash": {
                        "type": "string",
                        "description": "[REQUIRED] Ключ сессии в архиве (session_hash)",
                    },
                    "title": {
                        "type": "string",
                        "description": "Заголовок отчёта (по умолчанию — название клиники из metadata)",
                    },
                    "client_name": {
                        "type": "string",
                        "description": "Название клиники (переопределяет metadata)",
                    },
                    "client_url": {
                        "type": "string",
                        "description": "URL сайта (переопределяет metadata)",
                    },
                },
                "required": ["session_hash"],
            },
        },
    },
    handler=handle_generate_html_report,
    check_fn=lambda: True,
    is_async=True,
    description="Generate and publish AIM design system HTML report from session archive data",
    emoji="📊",
)
