"""generate_html_report — Hermes tool: Generate AIM design system HTML report.

v7.1: Uses LLM interpretations as primary content for each phase.
Reads session archive data, builds metrics from raw data,
and renders each phase's LLM interpretation as a report section.
"""

import json
import logging
import os
import pymysql
from datetime import datetime, timezone
from typing import Any

from tools.registry import registry

logger = logging.getLogger(__name__)

# ── WordPress DB ───────────────────────────────────────────────────
WP_DB_HOST = os.getenv("WP_DB_HOST", "")
WP_DB_USER = os.getenv("WP_DB_USER", "")
WP_DB_PASSWORD = os.getenv("WP_DB_PASSWORD", "")
WP_DB_NAME = os.getenv("WP_DB_NAME", "")


def _env_with_dotenv_fallback(key: str, default: str = "") -> str:
    """Try os.getenv, then load .env file as fallback."""
    val = os.getenv(key)
    if val:
        return val
    try:
        env_path = os.path.join(os.getenv("HERMES_HOME", "/opt/data"), ".env")
        if os.path.exists(env_path):
            with open(env_path) as f:
                for line in f:
                    line = line.strip()
                    if line.startswith("#") or "=" not in line:
                        continue
                    k, v = line.split("=", 1)
                    if k.strip() == key:
                        return v.strip().strip('"').strip("'")
    except Exception:
        pass
    return default


def _esc(text: str) -> str:
    """Escape HTML entities."""
    if not isinstance(text, str):
        text = str(text)
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")


def _fmt_num(val, default="—"):
    """Format number with digit grouping."""
    if val is None:
        return default
    try:
        n = int(float(val))
        if n >= 1_000_000:
            return f"{n/1_000_000:.1f} млн"
        if n >= 1_000:
            return f"{n:,}".replace(",", " ")
        return str(n)
    except (ValueError, TypeError):
        return default


def _fmt_revenue_short(val) -> str:
    """Format revenue: 120000000 → 120 млн ₽."""
    if val is None:
        return "—"
    try:
        n = int(float(val))
        if n >= 1_000_000_000:
            return f"{n/1_000_000_000:.1f} млрд ₽"
        if n >= 1_000_000:
            return f"{n/1_000_000:.0f} млн ₽"
        return f"{n:,} ₽".replace(",", " ")
    except (ValueError, TypeError):
        return "—"


def _fmt_trend(trend: str) -> str:
    """Format trend: up → ↑, down → ↓, stable → →."""
    if not trend:
        return "—"
    t = trend.lower()
    if t in ("up", "growth", "growing", "positive", "растёт", "рост"):
        return '<span class="trend-up">↑</span>'
    if t in ("down", "decline", "shrinking", "negative", "падает", "снижение"):
        return '<span class="trend-down">↓</span>'
    if t in ("stable", "flat", "стабильно"):
        return '<span class="trend-stable">→</span>'
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


# ── Report CSS (AIM Design System v7.1) ────────────────────────────

_REPORT_CSS = """<style>
*, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
:root {
  --bg: #ffffff; --text: #1A1A1A; --text-dim: #666666; --text-secondary: #444444;
  --accent: #1A1A1A; --border: #E0E0E0; --surface: #fafafa; --surface-2: #f5f5f5;
  --glass-bg: rgba(255,255,255,0.85); --shadow-color: rgba(0,0,0,0.06);
  --font-heading: 'Playfair Display', Georgia, serif;
  --font-body: 'Jost', -apple-system, sans-serif;
}
[data-theme="dark"] {
  --bg: #0d0d0d; --text: #f5f0e8; --text-dim: #99958f; --text-secondary: #b0aba3;
  --accent: #c9a96e; --border: rgba(201,169,110,0.18); --surface: #1a1a1a;
  --surface-2: #141414; --glass-bg: rgba(13,13,13,0.85); --shadow-color: rgba(0,0,0,0.3);
}
body { background: var(--bg); color: var(--text); font-family: var(--font-body); font-size: 16px; line-height: 1.7; -webkit-font-smoothing: antialiased; }
.report-container { max-width: 800px; margin: 0 auto; padding: 60px 32px; }
hr { border: none; border-top: 1px solid var(--border); margin: 0; }
h1 { font-family: var(--font-heading); font-size: 2.25rem; font-weight: 400; letter-spacing: -0.01em; margin: 8px 0 4px; }
h2 { font-family: var(--font-heading); font-size: 1.5rem; font-weight: 400; letter-spacing: -0.01em; margin-bottom: 20px; color: var(--accent); }
h3 { font-size: 1.1rem; font-weight: 500; margin: 16px 0 8px; }
h4 { font-size: 1rem; font-weight: 500; margin-bottom: 4px; }
p { margin: 8px 0; }
a { color: var(--accent); text-decoration: none; }
a:hover { text-decoration: underline; }
strong { font-weight: 600; }
ul, ol { margin: 8px 0 16px 20px; }
li { margin: 4px 0; }
code { font-family: monospace; font-size: 0.9em; background: var(--surface-2); padding: 1px 4px; border-radius: 2px; }
table { width: 100%; border-collapse: collapse; margin: 12px 0; font-size: 0.9rem; }
th { text-align: left; padding: 8px 12px; font-weight: 500; font-size: 0.75rem; text-transform: uppercase; letter-spacing: 0.05em; border-bottom: 2px solid var(--border); color: var(--text-dim); }
td { padding: 8px 12px; border-bottom: 1px solid var(--border); vertical-align: middle; }
tr:hover td { background: var(--surface); }
.section { padding: 48px 0; }
.section:first-child { padding-top: 20px; }
.section-label { display: inline-block; font-size: 0.75rem; text-transform: uppercase; letter-spacing: 0.1em; color: var(--text-dim); margin-bottom: 12px; }
.text-dim { color: var(--text-dim); font-size: 0.95rem; }
.text-meta { color: var(--text-dim); font-size: 0.8rem; }
.text-accent-link { color: var(--accent); }
.metrics { display: grid; grid-template-columns: repeat(auto-fit, minmax(160px, 1fr)); gap: 1px; background: var(--border); margin: 16px 0; }
.metric { background: var(--bg); padding: 24px 20px; text-align: center; }
.metric .value { font-family: var(--font-heading); font-size: 1.75rem; font-weight: 400; letter-spacing: -0.01em; }
.metric .label { font-size: 0.75rem; text-transform: uppercase; letter-spacing: 0.05em; color: var(--text-dim); margin-top: 4px; }
.surface-card { background: var(--surface); border: 1px solid var(--border); border-radius: 8px; padding: 20px 24px; margin: 8px 0; }
.grid-1 { display: grid; gap: 8px; }
.grid-2 { display: grid; grid-template-columns: 1fr 1fr; gap: 8px; }
@media (max-width: 600px) { .grid-2 { grid-template-columns: 1fr; } }
.interpretation p { margin: 12px 0; }
.interpretation h3 { margin: 24px 0 8px; border-bottom: 1px solid var(--border); padding-bottom: 6px; }
.interpretation ul, .interpretation ol { margin: 8px 0 16px 20px; }
.interpretation table { margin: 16px 0; }
.cta-box { text-align: center; padding: 48px 0; }
.cta-box h2 { margin-bottom: 12px; }
.btn { display: inline-block; background: var(--accent); color: var(--bg); padding: 14px 32px; font-size: 0.85rem; text-transform: uppercase; letter-spacing: 0.1em; font-weight: 500; border-radius: 1px; margin-top: 20px; }
.btn:hover { opacity: 0.9; text-decoration: none; }
.section-footer { padding: 32px 0; border-top: 1px solid var(--border); }
.trend-up { color: #22c55e; font-weight: 500; }
.trend-down { color: #ef4444; font-weight: 500; }
.trend-stable { color: #888; }
</style>"""


# ── Data normalization (v7 phase names → report keys) ─────────────

def _is_error_data(val) -> bool:
    if not isinstance(val, dict):
        return False
    non_error_keys = [k for k in val if k not in ("error", "detail", "status")]
    if not non_error_keys:
        return True
    if "error" in val and len(val) <= 2:
        return True
    return False


def _parse_tool_value(raw_val) -> dict | None:
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


def _unwrap_tool_output(phase_data: dict) -> dict | None:
    if not isinstance(phase_data, dict):
        return None
    merged: dict = {}
    for key, val in phase_data.items():
        parsed = _parse_tool_value(val)
        if parsed is not None and isinstance(parsed, dict):
            merged.update(parsed)
    return merged if merged else None


def _normalize_pipeline_keys(data: dict) -> dict:
    """Map v7 pipeline phase-name keys to the keys _build_report_html expects."""
    # Extract LLM interpretations
    interpretations = {}
    for key in list(data.keys()):
        if key.endswith("_interpretation") and isinstance(data[key], dict):
            phase_name = key[:-15]
            content = data[key].get("content", "")
            if content:
                interpretations[phase_name] = str(content)
    data["interpretations"] = interpretations

    # Phase → tool → expected key mapping (v7.1 phase names)
    _phase_tool_map = {
        "PERPLEXITY": {"perplexity_search": "market_research"},
        "COMPETITORS": {"find_competitors": "competitors", "run_ci_analysis": "ci_analysis"},
        "TECH AUDIT": {"run_pagespeed": "pagespeed", "run_seo_audit": "seo_audit"},
        "SOCIAL VERIFIER": {"run_review_platforms": "review_platforms"},
        "CONTENT ANALYSIS": {"run_content_analysis": "content_analysis"},
        "KEY PERSONS": {"run_hh_analysis": "hh_analysis", "run_doctor_dossiers": "doctor_dossiers"},
        "SMI MENTIONS": {"run_smi_mentions": "smi_mentions"},
        "FORUM PAINS": {"web_search": "forum_pains"},
        "FINANCE": {"find_company_financials": "financials"},
        "CONTENT PLAN": {"run_content_gaps": "content_gaps"},
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
                    unwrapped = _unwrap_tool_output(phase_data)
                    if unwrapped and unwrapped != phase_data and not _is_error_data(unwrapped):
                        data[expected_key] = unwrapped

    # CI analysis fallback
    if "COMPETITORS" in data and not data.get("ci_analysis"):
        comp = data["COMPETITORS"]
        if isinstance(comp, dict) and "run_ci_analysis" in comp:
            parsed = _parse_tool_value(comp["run_ci_analysis"])
            if parsed is not None:
                data["ci_analysis"] = parsed

    # Review platforms transform
    for review_key in ("review_platforms", "SOCIAL VERIFIER"):
        raw = data.get(review_key, {})
        if isinstance(raw, dict) and "platforms" in raw:
            existing = data.get("review_platforms", {})
            if isinstance(existing, dict):
                existing.update(raw.get("platforms", {}))
                data["review_platforms"] = existing

    # Financials transform
    fin = data.get("financials", {}) or {}
    if isinstance(fin, dict) and "financials" not in data:
        data["financials"] = fin

    # Doctor dossiers transform
    docs = data.get("doctor_dossiers", {}) or {}
    if isinstance(docs, dict) and "doctor_dossiers" not in data:
        data["doctor_dossiers"] = docs

    # Metadata
    meta = data.get("metadata", {}) or {}
    for src_key in ("PERPLEXITY", "TECH AUDIT", "SOCIAL VERIFIER"):
        if not meta.get("city") and data.get(src_key, {}).get("city"):
            pass  # city extraction if needed
    data["metadata"] = meta

    return data


# ── HTML Report Builder ────────────────────────────────────────────

def _build_report_html(data: dict, title: str) -> str:
    """Build full HTML page from v7 session archive data.

    Uses LLM interpretations as primary content for each phase.
    Raw data provides the executive summary metrics.
    """
    data = _normalize_pipeline_keys(data)

    metadata = data.get("metadata", {}) or {}
    interpretations = data.get("interpretations", {}) or {}

    client_name = metadata.get("company_name") or title or "Клиника"
    client_url = metadata.get("url", "")
    city = metadata.get("city", "")
    scan_date = metadata.get("scan_completed") or datetime.now(timezone.utc).isoformat()

    try:
        dt = datetime.fromisoformat(scan_date.replace("Z", "+00:00"))
        date_str = dt.strftime("%d.%m.%Y")
    except (ValueError, AttributeError):
        date_str = "—"

    phases = [
        ("PERPLEXITY",      "Исследование рынка",   "🔍"),
        ("COMPETITORS",     "Конкуренты",           "🏛️"),
        ("TECH AUDIT",      "Технический аудит",    "⚡"),
        ("SOCIAL VERIFIER", "Отзывы и репутация",   "⭐"),
        ("CONTENT ANALYSIS","Контент-анализ",       "📝"),
        ("KEY PERSONS",     "Врачи и эксперты",     "👨‍⚕️"),
        ("SMI MENTIONS",    "Упоминания в СМИ",     "📰"),
        ("FORUM PAINS",     "Боли пациентов",       "💬"),
        ("FINANCE",         "Финансы",              "💰"),
        ("CONTENT PLAN",    "Контент-план",         "📋"),
        ("QC CRITIQUE",     "Проверка качества",    "✅"),
    ]

    sections = []

    # Hero
    sections.append(f"""<section class="section">
  <span class="section-label">AIM Scout Report</span>
  <h1>{_esc(client_name)}</h1>
  <p class="text-dim">{_esc(city)}{' · ' + _esc(client_url) if client_url else ''}</p>
  <p class="text-meta">Исследование завершено {date_str}</p>
</section>
<hr>""")

    # Executive Summary
    metrics = _build_metrics(data)
    if metrics:
        sections.append(f"""<section class="section">
  <span class="section-label">Ключевые метрики</span>
  <h2>Обзор</h2>
  <div class="metrics">{metrics}</div>
</section>
<hr>""")

    # Phase interpretations
    for phase_key, phase_label, phase_icon in phases:
        content = interpretations.get(phase_key, "")
        if not content or len(str(content).strip()) < 15:
            continue
        content_html = _format_interpretation(str(content))
        sections.append(f"""<section class="section">
  <span class="section-label">{phase_icon} {phase_label}</span>
  <h2>{phase_label}</h2>
  <div class="interpretation">{content_html}</div>
</section>
<hr>""")

    # CTA
    sections.append("""<section class="section">
  <div class="cta-box">
    <h2>Готовы действовать?</h2>
    <p>Команда AIM реализует эти рекомендации под ключ.</p>
    <a href="https://t.me/aim_hermes_bot" class="btn" target="_blank" rel="noopener noreferrer">Связаться в Telegram</a>
  </div>
</section>""")

    # Footer
    sections.append("""<section class="section section-footer">
  <p class="text-meta">
    <a href="https://iamaim.ru" class="text-accent-link">iamaim.ru</a> · AI-first маркетинг в медицине<br>
    Этот отчёт сгенерирован автоматически
  </p>
</section>""")

    body = "\n".join(sections)

    return f"""<!DOCTYPE html>
<html lang="ru-RU" data-theme="light">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>AIM Scout — {_esc(client_name)}</title>
{_REPORT_CSS}
</head>
<body>
<div class="report-container">
{body}
</div>
</body>
</html>"""


def _build_metrics(data: dict) -> str:
    """Extract metrics from raw phase data."""
    metrics = []

    comp_data = data.get("competitors", {})
    if isinstance(comp_data, dict):
        comp_list = comp_data.get("competitors", [])
        if isinstance(comp_list, list) and comp_list:
            metrics.append(("Конкурентов", str(len(comp_list))))

    ps_data = data.get("pagespeed", {})
    if isinstance(ps_data, dict):
        mobile = ps_data.get("mobile", {})
        if isinstance(mobile, dict) and mobile.get("performance_score"):
            score = mobile["performance_score"]
            color = "#22c55e" if score >= 90 else ("#eab308" if score >= 50 else "#ef4444")
            metrics.append((f'Скорость сайта <span style="color:{color}">{score}/100</span>', ""))

    seo_data = data.get("seo_audit", {})
    if isinstance(seo_data, dict):
        wow = seo_data.get("wow", {})
        if isinstance(wow, dict) and wow.get("patients_per_month"):
            metrics.append(("Пациентов из поиска", f'+{wow["patients_per_month"]}/мес'))

    rev_data = data.get("review_platforms", {})
    if isinstance(rev_data, dict):
        total = rev_data.get("total_mentions", 0)
        platforms = rev_data.get("platforms_with_results", 0)
        if total or platforms:
            metrics.append(("Платформ с отзывами", str(platforms)))
            metrics.append(("Упоминаний", str(total)))

    smi_data = data.get("smi_mentions", {})
    if isinstance(smi_data, dict) and smi_data.get("total_mentions"):
        metrics.append(("Упоминаний в СМИ", str(smi_data["total_mentions"])))

    cg_data = data.get("content_gaps", {})
    if isinstance(cg_data, dict):
        covered = cg_data.get("topics_covered_by_client", 0)
        total = cg_data.get("topics_analyzed", 0)
        if total:
            metrics.append(("Тем контента", f"{covered}/{total}"))

    if not metrics:
        return ""

    return "\n".join(
        f'<div class="metric"><div class="value">{v or "—"}</div><div class="label">{l}</div></div>'
        for l, v in metrics[:8]
    )


def _format_interpretation(text: str) -> str:
    """Convert LLM interpretation text to formatted HTML."""
    import re
    lines = text.strip().split('\n')
    parts = []
    in_table = False
    in_list = False
    buf = []

    def flush():
        nonlocal in_list
        if in_list:
            parts.append('</ul>')
            in_list = False
        if buf:
            parts.append('<p>' + '<br>'.join(buf) + '</p>')
            buf.clear()

    for line in lines:
        s = line.strip()

        if s.startswith('|') and '|' in s[1:]:
            flush()
            cells = [c.strip() for c in s.split('|')[1:-1]]
            if not in_table:
                parts.append('<div class="table-wrap"><table>')
                in_table = True
            if all(c.startswith('---') for c in cells):
                continue
            parts.append('<tr>' + ''.join(f'<td>{_esc(c)}</td>' for c in cells) + '</tr>')
            continue
        elif in_table:
            parts.append('</table></div>')
            in_table = False

        if not s:
            flush()
            continue

        if s.startswith('###'):
            flush()
            parts.append(f'<h3>{_esc(s[3:].strip())}</h3>')
            continue
        if s.startswith('##'):
            flush()
            parts.append(f'<h3>{_esc(s[2:].strip())}</h3>')
            continue

        if s.startswith('- ') or s.startswith('* '):
            if not in_list:
                flush()
                parts.append('<ul>')
                in_list = True
            formatted = _fmt_inline(s[2:])
            parts.append(f'<li>{formatted}</li>')
            continue

        if s[0].isdigit() and '. ' in s[:4]:
            if not in_list:
                flush()
                parts.append('<ol>')
                in_list = True
            formatted = _fmt_inline(s.split('. ', 1)[1])
            parts.append(f'<li>{formatted}</li>')
            continue

        buf.append(_fmt_inline(s))

    flush()
    if in_table:
        parts.append('</table></div>')
    return '\n'.join(parts) if parts else f'<p>{_esc(text[:500])}</p>'


def _fmt_inline(text: str) -> str:
    """Format inline markdown: **bold**, `code`."""
    text = _esc(text)
    text = __import__('re').sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', text)
    text = __import__('re').sub(r'`(.+?)`', r'<code>\1</code>', text)
    return text


# ── Random slug ─────────────────────────────────────────────────────

def _random_slug(length: int = 8) -> str:
    import secrets
    import string
    return ''.join(secrets.choice(string.ascii_lowercase + string.digits) for _ in range(length))


# ── Handler ─────────────────────────────────────────────────────────

async def handle_generate_html_report(
    session_hash: str = None,
    title: str = None,
    client_name: str = None,
    client_url: str = None,
    **kwargs,
) -> str:
    """Generate and publish an AIM design system HTML report from session data."""
    if isinstance(session_hash, dict):
        d = session_hash
        session_hash = d.get("session_hash", "")
        title = title or d.get("title", "")
        client_name = client_name or d.get("client_name", "")
        client_url = client_url or d.get("client_url", "")

    if not session_hash:
        return json.dumps({"error": "session_hash is required"}, ensure_ascii=False)

    report_title = title or client_name or "AIM Scout Report"

    # Load data from session archive
    from app.tools.session_archive import load_all_data
    data = load_all_data(session_hash)

    # Merge metadata overrides
    meta = data.get("metadata", {}) or {}
    if client_name:
        meta["company_name"] = client_name
    if client_url:
        meta["url"] = client_url
    data["metadata"] = meta

    # Generate HTML
    html = _build_report_html(data, report_title)

    # Publish
    if not WP_DB_PASSWORD:
        from app.tools.session_archive import SESSIONS_ROOT
        report_path = os.path.join(SESSIONS_ROOT, session_hash, "report.html")
        os.makedirs(os.path.dirname(report_path), exist_ok=True)
        with open(report_path, "w", encoding="utf-8") as f:
            f.write(html)
        return json.dumps({
            "status": "saved_locally",
            "path": report_path,
            "session_hash": session_hash,
        }, ensure_ascii=False)

    page_slug = _random_slug()
    wp_title = f"AIM Scout — {report_title}"

    conn = None
    try:
        conn = pymysql.connect(
            host=WP_DB_HOST, user=WP_DB_USER, password=WP_DB_PASSWORD,
            database=WP_DB_NAME, charset="utf8mb4", connect_timeout=5,
        )

        now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")

        with conn.cursor() as cur:
            cur.execute("SELECT ID FROM wp_posts WHERE post_name = %s LIMIT 1", (page_slug,))
            existing = cur.fetchone()

            if existing:
                cur.execute(
                    "UPDATE wp_posts SET post_content=%s, post_modified=%s WHERE ID=%s",
                    (html, now, existing[0]),
                )
                post_id = existing[0]
            else:
                cur.execute(
                    """INSERT INTO wp_posts
                       (post_author, post_date, post_date_gmt, post_content, post_title,
                        post_status, comment_status, ping_status, post_name, post_type,
                        post_excerpt, to_ping, pinged, post_content_filtered, menu_order)
                       VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)""",
                    (1, now, now, html, wp_title,
                     "publish", "closed", "closed", page_slug, "page",
                     "", "", "", "", 0),
                )
                post_id = cur.lastrowid
            conn.commit()

        report_url = f"https://iamaim.ru/{page_slug}"

        logger.info("generate_html_report: published report for %s → %s (post_id=%s)", session_hash[:12], report_url, post_id)

        return json.dumps({
            "status": "published",
            "url": report_url,
            "slug": page_slug,
            "post_id": post_id,
            "title": wp_title,
            "session_hash": session_hash,
        }, ensure_ascii=False)

    except Exception as e:
        logger.exception("generate_html_report: WordPress publish failed")
        from app.tools.session_archive import SESSIONS_ROOT
        report_path = os.path.join(SESSIONS_ROOT, session_hash, "report.html")
        os.makedirs(os.path.dirname(report_path), exist_ok=True)
        with open(report_path, "w", encoding="utf-8") as f:
            f.write(html)
        return json.dumps({
            "status": "saved_locally",
            "path": report_path,
            "error": str(e),
            "session_hash": session_hash,
        }, ensure_ascii=False)
    finally:
        if conn:
            conn.close()


# ── Registry ────────────────────────────────────────────────────────

registry.register(
    name="generate_html_report",
    toolset="aim-operations",
    schema={
        "type": "function",
        "function": {
            "name": "generate_html_report",
            "description": (
                "Собрать и опубликовать HTML-отчёт разведки из данных сессии. "
                "Читает session_archive по session_hash, генерирует отчёт "
                "в дизайн-системе AIM и публикует в WordPress."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "session_hash": {
                        "type": "string",
                        "description": "Хеш сессии (session_id)",
                    },
                    "title": {
                        "type": "string",
                        "description": "Заголовок отчёта",
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
