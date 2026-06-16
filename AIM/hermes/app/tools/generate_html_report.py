"""
generate_html_report — Hermes tool: Generate HTML report in AIM design system.

Reads session data from /opt/data/sessions-archive/{hash}/, generates a
self-contained HTML page in the AIM design system (glass morphism, light theme,
dual-theme Inter+Playfair), and publishes it as a WordPress page.

Registered in Hermes internal registry under toolset "aim-operations".
"""

import json
import logging
import os
import random
import string
from datetime import datetime, timezone

import pymysql

from tools.registry import registry

logger = logging.getLogger(__name__)

WP_DB_HOST = os.getenv("WP_DB_HOST", "wp-db")
WP_DB_USER = os.getenv("WP_DB_USER", "wp_user")
WP_DB_PASSWORD = os.getenv("WP_DB_PASSWORD", "")
WP_DB_NAME = os.getenv("WP_DB_NAME", "wordpress")

SESSIONS_ROOT = os.getenv("SESSIONS_ROOT", "/opt/data/sessions-archive")

# ── AIM Design System CSS (dual-theme: light + dark, Inter + Playfair) ──────

AIM_DESIGN_CSS = """
  *,*::before,*::after{box-sizing:border-box;margin:0;padding:0}
  :root {
    --bg:#ffffff;--surface:#F5F5F5;--hover:#EBEBEB;
    --border:#E0E0E0;--text:#1A1A1A;--text-secondary:#666666;
    --text-dim:#999999;--accent:#1A1A1A;--accent-hover:#333333;
    --glass-bg:rgba(255,255,255,0.6);--glass-border:rgba(0,0,0,0.06);
    --section-gap:120px;--green:#2E7D32;--red:#C62828;
  }
  [data-theme="dark"] {
    --bg:#0D0D0D;--surface:#1A1A1A;--hover:#262626;
    --border:#333333;--text:#F0F0F0;--text-secondary:#999999;
    --text-dim:#666666;--accent:#F0F0F0;--accent-hover:#CCCCCC;
    --glass-bg:rgba(13,13,13,0.6);--glass-border:rgba(255,255,255,0.06);
    --green:#66BB6A;--red:#EF5350;
  }
  html{scroll-behavior:smooth}
  body{font-family:'Inter',-apple-system,sans-serif;background:var(--bg);color:var(--text);line-height:1.6;-webkit-font-smoothing:antialiased;transition:background .3s,color .3s}
  h1,h2,h3,h4{font-family:'Playfair Display',serif;font-weight:400;line-height:1.2;color:var(--text)}
  h2{font-size:36px;margin-bottom:16px}
  h3{font-size:22px;margin-bottom:12px}
  h4{font-size:14px;font-weight:600;margin-bottom:6px}
  p{color:var(--text-secondary);margin-bottom:16px;font-size:15px;line-height:1.7}
  p strong{color:var(--text);font-weight:500}
  blockquote{border-left:2px solid var(--text);padding-left:24px;margin:24px 0;font-size:16px;line-height:1.6;color:var(--text-secondary)}
  hr{border:none;border-top:1px solid var(--border);margin:48px 0}
  .container{max-width:900px;margin:0 auto;padding:0 32px;position:relative;z-index:1}
  .section-label{font-size:11px;letter-spacing:3px;text-transform:uppercase;color:var(--text-dim);margin-bottom:16px}
  section{margin-bottom:var(--section-gap)}
  nav{position:fixed;top:0;left:0;right:0;z-index:99;padding:16px 40px;background:var(--glass-bg);backdrop-filter:blur(16px);-webkit-backdrop-filter:blur(16px);border-bottom:1px solid var(--glass-border);display:flex;align-items:center;justify-content:space-between}
  nav .logo{font-family:'Playfair Display',serif;font-size:18px;font-weight:700}
  nav .tag{font-size:12px;color:var(--text-dim);letter-spacing:1px;text-transform:uppercase}
  nav .links{display:flex;gap:8px}
  nav .links a{text-decoration:none;color:var(--text-secondary);font-size:13px;padding:6px 14px;border-radius:20px;transition:.2s}
  nav .links a:hover{background:var(--surface);color:var(--text)}
  .theme-toggle{width:32px;height:32px;border-radius:16px;background:transparent;border:none;cursor:pointer;display:flex;align-items:center;justify-content:center;font-size:15px;transition:.2s;flex-shrink:0}
  .theme-toggle:hover{background:var(--surface)}
  .hero{padding:180px 0 100px;border-bottom:1px solid var(--border);margin-bottom:var(--section-gap);position:relative;overflow:hidden}
  .hero .label{font-size:12px;letter-spacing:3px;text-transform:uppercase;color:var(--text-dim);margin-bottom:24px}
  .hero h1{font-family:'Playfair Display',serif;font-size:56px;font-weight:400;line-height:1.15;margin-bottom:32px;position:relative;z-index:1}
  .hero h1 em{font-style:italic}
  .hero .subtitle{font-size:18px;color:var(--text-secondary);max-width:600px;line-height:1.7;position:relative;z-index:1}
  .hero .meta{display:flex;gap:32px;margin-top:48px;font-size:13px;color:var(--text-dim);flex-wrap:wrap;position:relative;z-index:1}
  .ripple{position:fixed;inset:0;pointer-events:none;z-index:0;overflow:hidden}
  .ripple-ring{position:absolute;border-radius:50%;border:1px solid var(--text);opacity:0.04;background:none}
  .ring-lg-1{width:420px;height:420px;top:-12%;right:-8%}
  .ring-lg-2{width:340px;height:340px;top:15%;right:70%}
  .ring-lg-3{width:280px;height:280px;top:45%;left:-10%}
  .ring-lg-4{width:380px;height:380px;top:75%;right:-15%}
  .ring-lg-5{width:300px;height:300px;top:60%;left:60%}
  .ring-lg-6{width:240px;height:240px;top:30%;left:-6%}
  .ring-pulse-1{width:200px;height:200px;top:10%;left:8%;animation:pulse-ring 6s ease-in-out infinite}
  .ring-pulse-2{width:160px;height:160px;top:12%;left:12%;animation:pulse-ring 6s ease-in-out infinite;animation-delay:3s}
  .ring-pulse-3{width:100px;height:100px;bottom:18%;right:4%;animation:pulse-ring 8s ease-in-out infinite;animation-delay:1s}
  .ring-pulse-4{width:70px;height:70px;bottom:22%;right:10%;animation:pulse-ring 8s ease-in-out infinite;animation-delay:5s}
  .ring-pulse-5{width:130px;height:130px;top:35%;right:20%;animation:pulse-ring 7s ease-in-out infinite;animation-delay:2s}
  .ring-pulse-6{width:90px;height:90px;top:70%;left:30%;animation:pulse-ring 9s ease-in-out infinite;animation-delay:4s}
  .ring-pulse-7{width:110px;height:110px;top:88%;left:50%;animation:pulse-ring 6.5s ease-in-out infinite;animation-delay:1.5s}
  .ring-pulse-8{width:150px;height:150px;top:50%;right:40%;animation:pulse-ring 7.5s ease-in-out infinite;animation-delay:3.5s}
  @keyframes pulse-ring{0%,100%{opacity:0.03;transform:scale(1)}50%{opacity:0.07;transform:scale(1.15)}}
  .card{background:var(--surface);border-radius:16px;padding:24px;transition:.2s;border:1px solid transparent}
  .card:hover{background:var(--hover)}
  .card h4{font-size:14px;font-weight:600;margin-bottom:6px;color:var(--text)}
  .card .num{font-size:28px;font-weight:300;margin-bottom:4px;color:var(--text)}
  .card p{font-size:13px;color:var(--text-secondary);margin:0}
  .metrics{display:flex;gap:48px;margin:32px 0;flex-wrap:wrap}
  .metric .value{font-size:36px;font-weight:300;color:var(--text)}
  .metric .label{font-size:13px;color:var(--text-dim);margin-top:4px}
  .grid-2{display:grid;grid-template-columns:1fr 1fr;gap:16px;margin:24px 0}
  .grid-3{display:grid;grid-template-columns:1fr 1fr 1fr;gap:16px;margin:24px 0}
  .row{display:flex;padding:12px 0;border-bottom:1px solid var(--border)}
  .row:last-child{border-bottom:none}
  .row .k{width:180px;flex-shrink:0;font-size:13px;color:var(--text-dim)}
  .row .v{font-size:14px;color:var(--text)}
  .gap{background:var(--surface);border-radius:12px;padding:20px;margin-bottom:12px;border-left:3px solid var(--border)}
  .gap h4{font-size:14px;margin-bottom:6px;color:var(--text)}
  .gap p{font-size:13px;margin:0}
  .tag-badge{display:inline-block;padding:2px 8px;border-radius:100px;border:1px solid var(--border);font-size:11px;color:var(--text-dim);margin:1px}
  .metric-tag{display:inline-flex;align-items:center;gap:6px;font-family:'Inter',-apple-system,sans-serif;font-size:11px;font-weight:600;padding:5px 12px;border-radius:12px;letter-spacing:.5px;margin:4px 6px 4px 0}
  .metric-tag-dot{width:6px;height:6px;border-radius:50%}
  .metric-tag-green{background:#1B5E20;color:#81C784}.metric-tag-green .metric-tag-dot{background:#81C784}
  .metric-tag-yellow{background:#F57F17;color:#FFF9C4}.metric-tag-yellow .metric-tag-dot{background:#FFF9C4}
  .metric-tag-red{background:#C62828;color:#FFCDD2}.metric-tag-red .metric-tag-dot{background:#FFCDD2}
  .metric-tag-blue{background:#1A237E;color:#90CAF9}.metric-tag-blue .metric-tag-dot{background:#90CAF9}
  .metric-tag-gray{background:var(--surface);color:var(--text-secondary);border:1px solid var(--border)}.metric-tag-gray .metric-tag-dot{background:var(--text-secondary)}
  .expert-category{margin-bottom:28px}
  .expert-category .cat-title{font-size:13px;font-weight:600;color:var(--text-dim);text-transform:uppercase;letter-spacing:2px;margin-bottom:10px}
  .expert-item{display:flex;justify-content:space-between;align-items:baseline;padding:10px 0;border-bottom:1px solid var(--border);font-size:14px;gap:12px;flex-wrap:wrap}
  .expert-item:last-child{border-bottom:none}
  .expert-item .name{color:var(--text);font-weight:500}
  .expert-item .spec{color:var(--text-secondary);font-size:13px}
  .expert-item .social{font-size:12px;color:var(--text-dim);white-space:nowrap}
  .social-found{color:var(--green)}
  .social-notfound{color:var(--text-dim)}
  .comp-expert{margin-bottom:12px}
  .comp-expert .name{font-weight:600;font-size:14px}
  .comp-expert .spec{font-size:13px;color:var(--text-secondary)}
  .comp-expert .social{font-size:12px;color:var(--text-dim)}
  .article-link{display:block;padding:12px 16px;border-radius:8px;background:var(--surface);margin-bottom:8px;text-decoration:none;transition:.2s;font-size:14px}
  .article-link:hover{background:var(--hover)}
  .article-link .title{color:var(--text)}
  .article-link .expert{font-size:12px;color:var(--text-dim);margin-top:2px}
  .article-link .url{font-size:12px;color:var(--text-dim);word-break:break-all}
  .strategy-block{margin-bottom:32px}
  .strategy-block .header{display:flex;align-items:baseline;gap:12px;margin-bottom:8px}
  .strategy-block .step{font-size:12px;color:var(--text-dim);letter-spacing:2px}
  .strategy-block h3{margin:0}
  .cta-box{border:2px solid var(--text);border-radius:16px;padding:48px;text-align:center;margin:48px 0}
  .cta-box h3{margin-bottom:16px}
  .cta-box p{margin-bottom:24px}
  .cta-box .btn{display:inline-block;padding:14px 40px;border:1px solid var(--text);color:var(--text);text-decoration:none;font-size:14px;border-radius:28px;transition:.2s;letter-spacing:1px}
  .cta-box .btn:hover{background:var(--text);color:var(--bg)}
  table{width:100%;border-collapse:collapse;font-size:14px}
  thead th{background:var(--surface);padding:14px 20px;text-align:left;font-weight:600;font-size:11px;letter-spacing:.05em;text-transform:uppercase;color:var(--text-secondary);border-bottom:1px solid var(--border)}
  td{padding:14px 20px;border-bottom:1px solid var(--border);color:var(--text-secondary)}
  tr:last-child td{border-bottom:none}
  tr:hover td{background:var(--surface)}
  tr:nth-child(even) td{background:var(--surface)}
  .footer{padding:80px 0;text-align:center;border-top:1px solid var(--border);margin-top:48px}
  .footer .logo{font-family:'Playfair Display',serif;font-size:28px;font-weight:700;color:var(--text);letter-spacing:-.02em;margin-bottom:8px}
  .footer .tagline{font-size:12px;color:var(--text-dim);text-transform:uppercase;letter-spacing:.1em}
  .footer p{font-family:'Inter',-apple-system,sans-serif;font-size:13px;color:var(--text-dim);letter-spacing:.1em}
  .footer a{color:var(--accent);text-decoration:none}
  @media(max-width:768px){.hero h1{font-size:32px}h2{font-size:28px}.grid-2,.grid-3{grid-template-columns:1fr}.metrics{gap:24px}.row{flex-direction:column;gap:2px}.row .k{width:auto}nav .links{display:none}.hero{padding:140px 0 60px}.cta-box{padding:32px 20px}.ripple{display:none}}
  @media(max-width:480px){.container{padding:0 20px}section{margin-bottom:80px}}
"""

# ── Helpers ─────────────────────────────────────────────────────────────────

def _esc(text: str) -> str:
    """HTML-escape a string."""
    if not isinstance(text, str):
        text = str(text) if text is not None else ""
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")


def _parse_num(val):
    """Try to parse a number from a string like '3.89%' or '5.0'."""
    if isinstance(val, (int, float)):
        return float(val)
    if isinstance(val, str):
        clean = val.replace("%", "").replace(",", ".").replace("₽", "").replace("\xa0", "").strip()
        try:
            return float(clean)
        except ValueError:
            return None
    return None


def _random_slug(length: int = 8) -> str:
    """Generate a random URL-safe slug."""
    chars = string.ascii_lowercase + string.digits
    return "".join(random.choices(chars, k=length))


def _format_currency(val) -> str:
    """Format a number as a readable currency string (RUB)."""
    n = _parse_num(val)
    if n is None:
        return str(val) if val else "—"
    if n >= 1_000_000:
        return f"{n/1_000_000:.1f} млн ₽"
    if n >= 1_000:
        return f"{n/1_000:.0f} тыс ₽"
    return f"{n:,.0f} ₽"


def _tag_class_for_score(score) -> str:
    """Return metric-tag class for a numeric score."""
    n = _parse_num(score)
    if n is None:
        return "metric-tag-gray"
    if n >= 80:
        return "metric-tag-green"
    if n >= 50:
        return "metric-tag-yellow"
    return "metric-tag-red"


# ── Data Loading ────────────────────────────────────────────────────────────

def _load_session_data(session_hash: str) -> dict:
    """Load all available data from a session archive directory."""
    data = {
        "session_hash": session_hash,
        "metadata": {},
        "prescan": {},
        "ci_analysis": {},
    }

    session_dir = os.path.join(SESSIONS_ROOT, session_hash)
    if not os.path.isdir(session_dir):
        logger.warning("Session directory not found: %s", session_dir)
        return data

    # metadata.json
    meta_path = os.path.join(session_dir, "metadata.json")
    if os.path.exists(meta_path):
        try:
            with open(meta_path, "r") as f:
                data["metadata"] = json.load(f)
        except (json.JSONDecodeError, OSError) as e:
            logger.warning("Failed to read metadata.json: %s", e)

    # prescan-data.json
    prescan_path = os.path.join(session_dir, "prescan-data.json")
    if os.path.exists(prescan_path):
        try:
            with open(prescan_path, "r") as f:
                data["prescan"] = json.load(f)
        except (json.JSONDecodeError, OSError) as e:
            logger.warning("Failed to read prescan-data.json: %s", e)

    # ci-analysis.json
    ci_path = os.path.join(session_dir, "ci-analysis.json")
    if os.path.exists(ci_path):
        try:
            with open(ci_path, "r") as f:
                data["ci_analysis"] = json.load(f)
        except (json.JSONDecodeError, OSError) as e:
            logger.warning("Failed to read ci-analysis.json: %s", e)

    # New optional data sources (graceful — file absence is normal)
    for filename, key in [
        ("doctor_dossiers.json", "doctor_dossiers"),
        ("instagram_content.json", "instagram_content"),
        ("smi_mentions.json", "smi_mentions"),
        ("pagespeed.json", "pagespeed"),
    ]:
        path = os.path.join(session_dir, filename)
        if os.path.exists(path):
            try:
                with open(path, "r") as f:
                    data[key] = json.load(f)
            except (json.JSONDecodeError, OSError) as e:
                logger.warning("Failed to read %s: %s", filename, e)

    return data


# ── Section Builders ────────────────────────────────────────────────────────

def _build_hero(data: dict) -> str:
    """Hero section with client name, city, URL, scan date."""
    meta = data.get("metadata", {})
    prescan = data.get("prescan", {})

    client_name = meta.get("client_name") or prescan.get("client_name") or "Клиника"
    client_url = meta.get("client_url") or prescan.get("website") or ""
    city = prescan.get("city") or ""
    scan_date = meta.get("archived_at") or ""

    if scan_date:
        try:
            dt = datetime.fromisoformat(scan_date.replace("Z", "+00:00"))
            scan_date = dt.strftime("%d.%m.%Y")
        except (ValueError, AttributeError):
            pass

    subtitle_parts = []
    if city:
        subtitle_parts.append(city)
    if client_url:
        subtitle_parts.append(client_url)
    subtitle = " • ".join(subtitle_parts)

    return f"""<div class="hero" id="hero">
      <div class="container">
        <div class="label">AIM Research Report</div>
        <h1>{_esc(client_name)}</h1>
        {'<p class="subtitle">' + _esc(subtitle) + '</p>' if subtitle else ''}
        {'<div class="meta"><span>Исследование завершено ' + _esc(scan_date) + '</span></div>' if scan_date else ''}
      </div>
    </div>"""


def _build_nav(data: dict) -> str:
    """Fixed navigation bar with conditional section links and theme toggle."""
    ci = data.get("ci_analysis", {})
    has_competitors = bool(ci.get("feature_matrix"))
    has_whitefields = bool(ci.get("gaps") or ci.get("advantages"))
    has_strategy = bool(ci.get("top_recommendation") or ci.get("priority_actions"))

    links = []
    links.append('<a href="#about">О клинике</a>')  # Always renders
    if has_competitors:
        links.append('<a href="#market">Рынок</a>')
    if data.get("doctor_dossiers"):
        links.append('<a href="#experts">Эксперты</a>')
    if data.get("instagram_content"):
        links.append('<a href="#content-analysis">Контент</a>')
    if data.get("smi_mentions"):
        links.append('<a href="#media">СМИ</a>')
    if has_competitors:
        links.append('<a href="#competitors">Конкуренты</a>')
    if has_whitefields:
        links.append('<a href="#whitefields">Белые поля</a>')
    # reviews always in prescan — check platforms
    reviews = (data.get("prescan", {}).get("stage_2_under_the_hood", {}) or {}).get("reviews_data") or data.get("prescan", {}).get("reviews", {})
    platforms = reviews.get("platforms", []) if isinstance(reviews, dict) else []
    if platforms:
        links.append('<a href="#presence">Присутствие</a>')
    if has_strategy:
        links.append('<a href="#strategy">Стратегия</a>')

    return f"""<nav>
  <div style="display:flex;align-items:center;gap:16px">
    <div class="logo">AIM</div>
    <div class="tag">Marketing Agency</div>
  </div>
  <div style="display:flex;align-items:center;gap:4px">
    <div class="links">{"".join(links)}</div>
    <button class="theme-toggle" onclick="var d=document.documentElement;var t=d.dataset.theme==='dark'?'light':'dark';d.dataset.theme=t;localStorage.setItem('theme',t)" aria-label="Toggle theme">🌓</button>
  </div>
</nav>"""


def _build_exec_summary(data: dict) -> str:
    """Executive summary with glass-stats: revenue, doctors, SEO, rating."""
    prescan = data.get("prescan", {})

    # Financials
    stage1 = prescan.get("stage_1_financials", {}) or {}
    revenue = stage1.get("revenue")
    profit = stage1.get("profit")

    # SEO
    stage2 = prescan.get("stage_2_under_the_hood", {}) or {}
    seo_score = stage2.get("seo_score")

    # Rating & reviews
    rating = stage2.get("rating")
    reviews = stage2.get("reviews")

    # Doctors
    doctors = stage1.get("doctors")

    stats = []
    if revenue:
        stats.append(f"""<div class="metric">
          <div class="value">{_format_currency(revenue)}</div>
          <div class="label">Выручка / год</div>
        </div>""")
    if doctors:
        stats.append(f"""<div class="metric">
          <div class="value">{_esc(str(doctors))}</div>
          <div class="label">Врачей</div>
        </div>""")
    if seo_score is not None:
        stats.append(f"""<div class="metric">
          <div class="value">{_esc(str(seo_score))}<span style="font-size:24px">/100</span></div>
          <div class="label">SEO Score</div>
        </div>""")
    if rating is not None:
        stats.append(f"""<div class="metric">
          <div class="value">{_esc(str(rating))}</div>
          <div class="label">Рейтинг</div>
        </div>""")

    if not stats:
        return ""

    return f"""<section id="market">
      <div class="container">
        <div class="section-label">Executive Summary</div>
        <h2>Ключевые метрики</h2>
        <div class="metrics">
          {''.join(stats)}
        </div>
      </div>
    </section>"""


def _build_competitors(data: dict) -> str:
    """Enhanced competitor comparison: table + per-competitor detail cards."""
    ci = data.get("ci_analysis", {})
    feature_matrix = ci.get("feature_matrix", [])
    if not feature_matrix:
        return ""

    # Score comparison table (kept from previous version)
    rows = ""
    for comp in feature_matrix:
        name = comp.get("name") or comp.get("brand_name") or "—"
        score = comp.get("total_score") or comp.get("score", "—")
        score_tag = _tag_class_for_score(score)
        services = comp.get("services") or ""
        if isinstance(services, list):
            services = ", ".join(services[:5])
        website = comp.get("website", "")

        rows += f"""<tr>
          <td style="color:var(--text);font-weight:500">{_esc(name)}</td>
          <td><span class="metric-tag {score_tag}"><span class="metric-tag-dot"></span>{_esc(str(score))}</span></td>
          <td>{_esc(str(services))}</td>
          <td>{'<a href="' + _esc(website) + '" style="color:var(--accent)" target="_blank" rel="noopener noreferrer">' + _esc(website) + '</a>' if website else '—'}</td>
        </tr>"""

    # Per-competitor detail cards
    comp_cards = ""
    for comp in feature_matrix:
        name = comp.get("name") or comp.get("brand_name") or "—"
        strengths = comp.get("strengths") or comp.get("advantages") or []
        weaknesses = comp.get("weaknesses") or comp.get("gaps") or []
        social = comp.get("social") or comp.get("instagram") or ""
        doctors = comp.get("doctors") or ""

        if not (strengths or weaknesses or social or doctors):
            continue  # Skip cards with no detail data

        card_body = f'<h3 style="font-size:16px;margin-bottom:8px">{_esc(name)}</h3>'

        if doctors:
            card_body += f'<p style="font-size:13px">Врачей: {_esc(str(doctors))}</p>'
        if social:
            card_body += f'<p style="font-size:13px">Instagram: {_esc(str(social))}</p>'

        if strengths:
            s_list = [str(s) if isinstance(s, str) else s.get("description", str(s)) for s in (strengths if isinstance(strengths, list) else [strengths])]
            card_body += f'<div class="social-found" style="font-size:12px;margin-top:8px">Сильные стороны: {", ".join(_esc(s) for s in s_list[:3])}</div>'
        if weaknesses:
            w_list = [str(w) if isinstance(w, str) else w.get("description", str(w)) for w in (weaknesses if isinstance(weaknesses, list) else [weaknesses])]
            card_body += f'<div class="social-notfound" style="font-size:12px;margin-top:4px">Слабые стороны: {", ".join(_esc(w) for w in w_list[:3])}</div>'

        comp_cards += f'<div class="card comp-expert">{card_body}</div>'

    cards_section = ""
    if comp_cards:
        cards_section = f'<h3 style="margin-top:32px">Детальный анализ конкурентов</h3><div class="grid-2">{comp_cards}</div>'

    return f"""<section id="competitors">
      <div class="container">
        <div class="section-label">Конкуренты</div>
        <h2>Сравнение с конкурентами</h2>
        <div style="overflow-x:auto;margin:24px 0">
          <table>
            <thead><tr><th>Клиника</th><th>Score</th><th>Услуги</th><th>Сайт</th></tr></thead>
            <tbody>{rows}</tbody>
          </table>
        </div>
        {cards_section}
      </div>
    </section>"""


def _build_ci_gaps(data: dict) -> str:
    """CI gaps & advantages with surface-block green/red."""
    ci = data.get("ci_analysis", {})
    gaps = ci.get("gaps", [])
    advantages = ci.get("advantages", [])
    best_practices = ci.get("best_practices", {}) or {}
    steal_worthy = best_practices.get("steal_worthy_tactics", [])
    top_rec = ci.get("top_recommendation", "")

    if not (gaps or advantages or steal_worthy or top_rec):
        return ""

    parts = []

    # Gaps (what client is missing)
    if gaps:
        gap_items = ""
        for g in gaps:
            sev = g.get("severity", "medium") if isinstance(g, dict) else "medium"
            text = g if isinstance(g, str) else (g.get("description") or g.get("gap") or str(g))
            icon = "🔴" if sev == "high" else ("🟡" if sev == "medium" else "🟢")
            gap_items += f'<div class="gap" style="border-left:3px solid var(--red)"><h4>{icon} {_esc(text)}</h4></div>'
        parts.append(f"""<h3 style="font-size:15px;font-weight:600;color:var(--text);margin-bottom:12px">Что теряете</h3>
        {gap_items}""")

    # Advantages (what client has that competitors don't)
    if advantages:
        adv_items = ""
        for a in advantages:
            text = a if isinstance(a, str) else (a.get("description") or a.get("advantage") or str(a))
            adv_items += f'<div class="gap" style="border-left:3px solid var(--green)"><h4>✅ {_esc(text)}</h4></div>'
        parts.append(f"""<h3 style="font-size:15px;font-weight:600;color:var(--text);margin-bottom:12px;margin-top:24px">Ваши преимущества</h3>
        {adv_items}""")

    # Steal-worthy tactics
    if steal_worthy:
        steal_items = ""
        for s in steal_worthy:
            text = s if isinstance(s, str) else (s.get("tactic") or s.get("description") or str(s))
            steal_items += f'<div class="gap"><h4>💡 {_esc(text)}</h4></div>'
        parts.append(f"""<h3 style="font-size:15px;font-weight:600;color:var(--text);margin-bottom:12px;margin-top:24px">Что стоит перенять у конкурентов</h3>
        {steal_items}""")

    # Top recommendation
    if top_rec:
        parts.append(f"""<div class="gap" style="margin-top:24px">
          <h4>Главная рекомендация</h4>
          <p>{_esc(top_rec)}</p>
        </div>""")

    if not parts:
        return ""

    return f"""<section id="gaps">
      <div class="container">
        <div class="section-label">CI Analysis</div>
        <h2>Разрывы и преимущества</h2>
        {''.join(parts)}
      </div>
    </section>"""


def _build_seo(data: dict) -> str:
    """SEO audit section with 18 checks in glass-table-wrap."""
    prescan = data.get("prescan", {})
    stage2 = prescan.get("stage_2_under_the_hood", {}) or {}

    seo_score = stage2.get("seo_score")
    seo_categories = stage2.get("seo_categories", {}) or {}
    seo_fails = stage2.get("seo_fails", []) or []

    if not (seo_score is not None or seo_fails):
        return ""

    # Summary row
    summary_html = ""
    if seo_score is not None:
        score_tag = _tag_class_for_score(seo_score)
        cats = []
        for cat_name, cat_data in seo_categories.items():
            if isinstance(cat_data, dict):
                cats.append(f'<span class="metric-tag {_tag_class_for_score(cat_data.get("score", 0))}"><span class="metric-tag-dot"></span>{_esc(cat_name)}: {cat_data.get("score", "—")}</span>')
        summary_html = f"""<div style="margin-bottom:20px">
          <span class="metric-tag {score_tag}" style="font-size:14px;padding:8px 18px"><span class="metric-tag-dot"></span>SEO Score: {seo_score}/100</span>
          {" ".join(cats)}
        </div>"""

    # Failed checks table
    if seo_fails:
        rows = ""
        for check in seo_fails:
            name = check.get("check") or check.get("name") or "—"
            status = check.get("status", "—")
            detail = check.get("detail") or check.get("description") or ""
            impact = check.get("business_impact") or ""
            sev = check.get("severity", "")
            sev_tag = "metric-tag-red" if sev == "critical" else ("metric-tag-yellow" if sev == "high" else "metric-tag-gray")
            rows += f"""<tr>
            <td style="color:var(--text);font-weight:500">{_esc(name)}</td>
            <td><span class="metric-tag {sev_tag}"><span class="metric-tag-dot"></span>{_esc(status)}</span></td>
            <td>{_esc(detail)}</td>
            <td>{_esc(impact)}</td>
          </tr>"""

        seo_table = f"""<div style="overflow-x:auto;margin:24px 0">
          <table>
            <thead><tr><th>Проверка</th><th>Статус</th><th>Детали</th><th>Влияние на бизнес</th></tr></thead>
            <tbody>{rows}</tbody>
          </table>
        </div>"""
    else:
        seo_table = ""

    return f"""<section id="seo">
      <div class="container">
        <div class="section-label">SEO Аудит</div>
        <h2>Технический SEO</h2>
        {summary_html}
        {seo_table}
      </div>
    </section>"""


def _build_pagespeed(data: dict) -> str:
    """PageSpeed Core Web Vitals section."""
    prescan = data.get("prescan", {})

    # Try prescan pagespeed data, then standalone pagespeed field
    ps = prescan.get("pagespeed", {}) or {}
    mobile = ps.get("mobile", {}) or {}

    if not mobile:
        return ""

    lcp = mobile.get("lcp_seconds") or mobile.get("lcp", "—")
    inp = mobile.get("inp_ms") or mobile.get("inp", "—")
    cls = mobile.get("cls", "—")
    cwv = mobile.get("cwv_status", "—")
    cwv_tag = "metric-tag-green" if cwv == "Passed" else "metric-tag-red"

    lcp_dist = mobile.get("lcp_distribution", {}) or {}
    inp_dist = mobile.get("inp_distribution", {}) or {}
    cls_dist = mobile.get("cls_distribution", {}) or {}

    return f"""<section id="pagespeed">
      <div class="container">
        <div class="section-label">PageSpeed</div>
        <h2>Core Web Vitals</h2>
        <div class="metrics" style="margin-bottom:24px">
          <div class="metric">
            <div class="value">{_esc(str(lcp))}<span style="font-size:20px">s</span></div>
            <div class="label">LCP</div>
          </div>
          <div class="metric">
            <div class="value">{_esc(str(inp))}<span style="font-size:20px">ms</span></div>
            <div class="label">INP</div>
          </div>
          <div class="metric">
            <div class="value">{_esc(str(cls))}</div>
            <div class="label">CLS</div>
          </div>
        </div>
        <div style="text-align:center;margin-bottom:24px">
          <span class="metric-tag {cwv_tag}" style="font-size:14px;padding:8px 18px"><span class="metric-tag-dot"></span>CWV: {_esc(cwv)}</span>
        </div>
        <div style="overflow-x:auto;margin:24px 0">
          <table>
            <thead><tr><th>Метрика</th><th>Значение</th><th>Good</th><th>Needs Improvement</th><th>Poor</th></tr></thead>
            <tbody>
              <tr><td>LCP</td><td>{_esc(str(lcp))}s</td><td>{lcp_dist.get('good','—')}%</td><td>{lcp_dist.get('needs_improvement','—')}%</td><td>{lcp_dist.get('poor','—')}%</td></tr>
              <tr><td>INP</td><td>{_esc(str(inp))}ms</td><td>{inp_dist.get('good','—')}%</td><td>{inp_dist.get('needs_improvement','—')}%</td><td>{inp_dist.get('poor','—')}%</td></tr>
              <tr><td>CLS</td><td>{_esc(str(cls))}</td><td>{cls_dist.get('good','—')}%</td><td>{cls_dist.get('needs_improvement','—')}%</td><td>{cls_dist.get('poor','—')}%</td></tr>
            </tbody>
          </table>
        </div>
      </div>
    </section>"""


def _build_reviews(data: dict) -> str:
    """Reviews aggregation section."""
    prescan = data.get("prescan", {})
    stage2 = prescan.get("stage_2_under_the_hood", {}) or {}

    # Try reviews from different paths
    reviews_data = stage2.get("reviews_data") or prescan.get("reviews") or {}
    review_platforms = reviews_data.get("platforms", []) if isinstance(reviews_data, dict) else []

    if not review_platforms:
        return ""

    cards = ""
    for platform in review_platforms:
        name = platform.get("platform") or platform.get("name") or "—"
        rating_val = platform.get("rating") or platform.get("score", "—")
        count = platform.get("reviews_count") or platform.get("count", "—")
        url = platform.get("url", "")

        # Format count label
        count_str = str(count)
        if count_str in ("данных нет", "None", "0", "—"):
            count_label = "нет данных"
        elif count_str.isdigit() or (count_str.startswith("~") and count_str[1:].isdigit()):
            count_label = f"{count_str} отзывов"
        else:
            count_label = count_str

        cards += f"""<div class="card">
          <h3>{_esc(name)}</h3>
          <div style="display:flex;align-items:baseline;gap:12px;margin-bottom:8px">
            <span style="font-family:'Playfair Display',serif;font-size:28px;color:var(--accent)">{_esc(str(rating_val))}</span>
            <span style="color:var(--text-secondary);font-size:14px">{_esc(count_label)}</span>
          </div>
          {f'<a href="{_esc(url)}" style="color:var(--accent);font-size:13px" target="_blank" rel="noopener noreferrer">Открыть →</a>' if url else ''}
        </div>"""

    return f"""<section id="reviews">
      <div class="container">
        <div class="section-label">Отзывы</div>
        <h2>Репутация на платформах</h2>
        <div class="grid-3">{cards}</div>
      </div>
    </section>"""


def _build_financials(data: dict) -> str:
    """Financial section with revenue, profit, trend."""
    prescan = data.get("prescan", {})
    stage1 = prescan.get("stage_1_financials", {}) or {}

    revenue = stage1.get("revenue")
    profit = stage1.get("profit")
    revenue_trend = stage1.get("revenue_trend") or prescan.get("stage_3_market", {}).get("revenue_trend")

    legal_name = stage1.get("legal_name") or ""
    inn = stage1.get("inn") or ""

    if not (revenue or profit):
        return ""

    stats = []
    if revenue:
        stats.append(f"""<div class="metric">
          <div class="value">{_format_currency(revenue)}</div>
          <div class="label">Выручка / год</div>
        </div>""")
    if profit:
        stats.append(f"""<div class="metric">
          <div class="value">{_format_currency(profit)}</div>
          <div class="label">Прибыль / год</div>
        </div>""")
    if revenue_trend:
        trend_str = str(revenue_trend)
        is_up = "+" in trend_str or "рост" in trend_str.lower() or "↑" in trend_str
        trend_tag = "metric-tag-green" if is_up else "metric-tag-red"
        stats.append(f"""<div class="metric">
          <div class="value" style="font-size:clamp(24px,3vw,36px)"><span class="metric-tag {trend_tag}"><span class="metric-tag-dot"></span>{_esc(trend_str)}</span></div>
          <div class="label">Тренд выручки</div>
        </div>""")

    legal_info = ""
    if legal_name or inn:
        legal_info = f'<p style="font-size:13px;color:var(--text-dim);margin-top:8px">{_esc(legal_name)}{" · ИНН " + _esc(inn) if inn else ""}</p>'

    return f"""<section id="financials">
      <div class="container">
        <div class="section-label">Финансы</div>
        <h2>Финансовые показатели</h2>
        <div class="metrics">
          {''.join(stats)}
        </div>
        {legal_info}
      </div>
    </section>"""


def _build_recommendations(data: dict) -> str:
    """Recommendations section with glass-cta."""
    ci = data.get("ci_analysis", {})
    top_rec = ci.get("top_recommendation", "")
    priority_actions = ci.get("priority_actions", []) or []

    prescan = data.get("prescan", {})
    stage2 = prescan.get("stage_2_under_the_hood", {}) or {}
    seo_fails = stage2.get("seo_fails", []) or []

    # Build priority actions as gap blocks
    actions_html = ""
    if priority_actions:
        for i, action in enumerate(priority_actions):
            text = action if isinstance(action, str) else (action.get("action") or action.get("name") or str(action))
            actions_html += f"""<div class="gap">
            <h4>Шаг {i + 1}</h4>
            <p>{_esc(text)}</p>
          </div>"""

    return f"""<section id="recommendations">
      <div class="container">
        <div class="section-label">Рекомендации</div>
        <h2>План действий</h2>
        {actions_html}
        {f'<div class="gap"><h4>Приоритетная рекомендация</h4><p>{_esc(top_rec)}</p></div>' if top_rec else ''}
        <div class="cta-box">
          <h3>Готовы вырасти?</h3>
          <p>Команда AIM готова реализовать эти рекомендации и вывести вашу клинику на новый уровень</p>
          <a href="https://t.me/aim_hermes_bot" class="btn" target="_blank" rel="noopener noreferrer">Связаться в Telegram</a>
        </div>
      </div>
    </section>"""


def _build_footer(data: dict) -> str:
    """Footer with AIM branding."""
    meta = data.get("metadata", {})
    scan_date = meta.get("archived_at") or ""
    if scan_date:
        try:
            dt = datetime.fromisoformat(scan_date.replace("Z", "+00:00"))
            scan_date = dt.strftime("%d.%m.%Y")
        except (ValueError, AttributeError):
            pass

    return f"""<footer class="footer">
      <div class="container">
        <div class="logo">AIM</div>
        <div class="tagline">AI-first маркетинг в медицине</div>
        <p style="margin-top:12px">
          <a href="https://iamaim.ru">iamaim.ru</a> • Этот отчёт сгенерирован автоматически
        </p>
        {f'<p style="margin-top:4px;font-size:11px">{_esc(scan_date)}</p>' if scan_date else ''}
      </div>
    </footer>"""


# ── New Section Builders (PLAN-02) ────────────────────────────────────────────

def _build_about(data: dict) -> str:
    """About section — merges exec summary + financials into one rich section."""
    prescan = data.get("prescan", {})
    stage1 = prescan.get("stage_1_financials", {}) or {}
    stage2 = prescan.get("stage_2_under_the_hood", {}) or {}

    revenue = stage1.get("revenue")
    profit = stage1.get("profit")
    legal_name = stage1.get("legal_name") or ""
    inn = stage1.get("inn") or ""
    okved = stage1.get("okved") or ""
    employees = stage1.get("employees")
    doctors = stage1.get("doctors")
    licenses = stage1.get("licenses")
    revenue_trend = stage1.get("revenue_trend") or prescan.get("stage_3_market", {}).get("revenue_trend")

    client_name = prescan.get("client_name") or data.get("metadata", {}).get("client_name") or ""

    if not (revenue or profit or legal_name):
        return ""

    # Build description paragraph
    desc_parts = []
    if legal_name:
        desc_parts.append(f"<strong>{_esc(legal_name)}</strong>")
    if inn:
        desc_parts.append(f"ИНН {_esc(inn)}")
    if okved:
        desc_parts.append(f"ОКВЭД {_esc(str(okved))}")
    if employees:
        desc_parts.append(f"{_esc(str(employees))} сотрудников")
    if licenses:
        lic_str = str(licenses)
        desc_parts.append(f"{_esc(lic_str)}")
    desc = " — ".join(desc_parts) + "." if desc_parts else ""

    # Metrics row
    metrics_items = []
    if revenue:
        metrics_items.append(
            f'<div class="metric"><div class="value">{_format_currency(revenue)}</div><div class="label">Выручка / год</div></div>'
        )
    if doctors is not None:
        metrics_items.append(
            f'<div class="metric"><div class="value">{_esc(str(doctors))}</div><div class="label">Врачей</div></div>'
        )
    if employees is not None:
        metrics_items.append(
            f'<div class="metric"><div class="value">{_esc(str(employees))}</div><div class="label">Сотрудников</div></div>'
        )
    if revenue_trend:
        trend_str = str(revenue_trend)
        is_up = "+" in trend_str or "рост" in trend_str.lower() or "↑" in trend_str
        trend_tag = "metric-tag-green" if is_up else "metric-tag-red"
        metrics_items.append(
            f'<div class="metric"><div class="value" style="font-size:clamp(24px,3vw,36px)"><span class="metric-tag {trend_tag}"><span class="metric-tag-dot"></span>{_esc(trend_str)}</span></div><div class="label">Тренд выручки</div></div>'
        )

    metrics_html = f'<div class="metrics">{"".join(metrics_items)}</div>' if metrics_items else ""

    # Dynamics description
    dynamics = ""
    if revenue_trend:
        trend_str = str(revenue_trend).lower()
        if "рост" in trend_str or "+" in trend_str or "↑" in trend_str:
            dynamics = f"<p>Выручка показывает положительную динамику. Это говорит о стабильном положении {_esc(client_name or legal_name or 'клиники')} на рынке.</p>"
        elif "пад" in trend_str or "-" in trend_str or "↓" in trend_str:
            dynamics = f"<p>Выручка показывает отрицательную динамику. Цифровой маркетинг может помочь переломить этот тренд и привлечь новых пациентов.</p>"

    # OKVED + Licenses in grid-2
    grid_items = ""
    if okved:
        grid_items += f'<div class="card"><h4>ОКВЭД</h4><p style="font-size:13px">{_esc(str(okved))}</p></div>'
    if licenses:
        lic_str = str(licenses)
        grid_items += f'<div class="card"><h4>Лицензии</h4><p style="font-size:13px">{_esc(lic_str)}</p></div>'

    grid_html = f'<div class="grid-2">{grid_items}</div>' if grid_items else ""

    # Key takeaway
    takeaway = ""
    if doctors and revenue:
        takeaway = "<blockquote>Ключевой вывод: при текущей выручке и штате врачей клиника имеет потенциал для роста за счёт усиления цифрового присутствия.</blockquote>"

    return f"""<section id="about">
  <div class="section-label">01 — О компании</div>
  <h2>{_esc(legal_name or client_name or 'Клиника')}</h2>
  {f'<p>{desc}</p>' if desc else ''}
  {dynamics}
  {metrics_html}
  {grid_html}
  {takeaway}
</section>
<hr>"""


def _build_market(data: dict) -> str:
    """Market section — revenue comparison table with competitors."""
    ci = data.get("ci_analysis", {})
    feature_matrix = ci.get("feature_matrix", [])
    if not feature_matrix:
        return ""

    prescan = data.get("prescan", {})
    stage1 = prescan.get("stage_1_financials", {}) or {}
    client_name = prescan.get("client_name") or data.get("metadata", {}).get("client_name") or "Клиника"
    client_revenue = stage1.get("revenue", "—")
    client_trend = stage1.get("revenue_trend") or prescan.get("stage_3_market", {}).get("revenue_trend") or "—"
    client_doctors = stage1.get("doctors", "—")
    client_instagram = prescan.get("instagram", {}).get("handle", "—") if prescan.get("instagram") else "—"

    # Build table rows
    rows = f"""<tr style="background:var(--hover);font-weight:700">
  <td style="color:var(--text)">{_esc(str(client_name))} ← <span style="font-size:12px;color:var(--text-dim)">Вы</span></td>
  <td style="color:var(--text)">{_format_currency(client_revenue)}</td>
  <td>{_esc(str(client_trend))}</td>
  <td>{_esc(str(client_doctors))}</td>
  <td>{_esc(str(client_instagram))}</td>
</tr>"""

    for comp in feature_matrix:
        name = comp.get("name") or comp.get("brand_name") or "—"
        rev = comp.get("revenue") or "—"
        rev_display = _format_currency(rev) if rev != "—" else "—"
        trend = comp.get("trend") or comp.get("revenue_trend") or "—"
        comp_doctors = comp.get("doctors") or "—"
        social = comp.get("social") or comp.get("instagram") or "—"
        rows += f"""<tr>
  <td style="color:var(--text);font-weight:500">{_esc(str(name))}</td>
  <td>{_esc(str(rev_display))}</td>
  <td>{_esc(str(trend))}</td>
  <td>{_esc(str(comp_doctors))}</td>
  <td>{_esc(str(social))}</td>
</tr>"""

    # Strengths and growth points
    advantages = ci.get("advantages", [])
    gaps = ci.get("gaps", [])

    strength_blocks = ""
    if advantages:
        strength_items = ""
        for a in advantages[:3]:
            text = a if isinstance(a, str) else (a.get("description") or a.get("advantage") or str(a))
            strength_items += f'<div class="gap" style="border-left:3px solid var(--green)"><h4>{_esc(text)}</h4></div>'
        strength_blocks += f"<h3>Где сильны</h3>{strength_items}"

    growth_blocks = ""
    if gaps:
        growth_items = ""
        for g in gaps[:3]:
            text = g if isinstance(g, str) else (g.get("description") or g.get("gap") or str(g))
            growth_items += f'<div class="gap" style="border-left:3px solid var(--border)"><h4>{_esc(text)}</h4></div>'
        growth_blocks += f"<h3 style=\"margin-top:24px\">Где есть точки роста</h3>{growth_items}"

    gaps_section = ""
    if strength_blocks or growth_blocks:
        gaps_section = f"<h3>Где сильны — где есть точки роста</h3>{strength_blocks}{growth_blocks}"

    return f"""<section id="market">
  <div class="section-label">02 — Рынок</div>
  <h2>{_esc(client_name)} vs конкуренты</h2>
  <p>Сравнение по выручке и ключевым метрикам.</p>
  <div style="overflow-x:auto;margin:24px 0">
    <table>
      <thead><tr><th>Клиника</th><th>Выручка</th><th>Тренд</th><th>Врачей</th><th>Instagram</th></tr></thead>
      <tbody>{rows}</tbody>
    </table>
  </div>
  {gaps_section}
</section>
<hr>"""


def _build_experts(data: dict) -> str:
    """Experts section — per-doctor cards from doctor_dossiers."""
    dossiers = data.get("doctor_dossiers")
    if not dossiers:
        return ""
    doctors = dossiers.get("doctors", [])
    if not doctors:
        return ""

    # Sort by followers descending
    sorted_doctors = sorted(doctors, key=lambda d: d.get("followers", 0) or 0, reverse=True)
    top_doctors = sorted_doctors[:5]

    cards = ""
    for i, doc in enumerate(top_doctors):
        name = doc.get("name") or doc.get("full_name") or "—"
        title = doc.get("title") or doc.get("specialty") or ""
        instagram = doc.get("instagram") or doc.get("handle") or ""
        followers = doc.get("followers", 0) or 0
        avg_likes = doc.get("avg_likes") or doc.get("avg_likes_count", 0) or 0
        content_style = doc.get("content_style") or ""

        follower_display = f"{followers:,}" if isinstance(followers, (int, float)) and followers > 0 else str(followers)
        is_top = i == 0

        cards += f"""<div class="card" {'style="background:var(--hover)"' if is_top else ''}>
  <div style="display:flex;justify-content:space-between;align-items:flex-start;gap:16px;flex-wrap:wrap">
    <div>
      <div class="name" style="font-size:16px;font-weight:600;color:var(--text)">{_esc(name)}</div>
      {f'<div class="spec">{_esc(title)}</div>' if title else ''}
      {f'<div class="social" style="margin-top:4px">{_esc(instagram)}</div>' if instagram else ''}
      {f'<p style="font-size:12px;color:var(--text-dim);margin-top:4px">Стиль: {_esc(content_style)}</p>' if content_style else ''}
    </div>
    <div style="text-align:right">
      <div class="social-found" style="font-size:24px;font-weight:300">{_esc(follower_display)}</div>
      <div class="social" style="font-size:12px">подписчиков</div>
      {f'<div class="social" style="font-size:12px;margin-top:4px">~{_esc(str(avg_likes))} лайков/пост</div>' if avg_likes else ''}
    </div>
  </div>
</div>"""

    # Summary for remaining doctors
    remaining = len(sorted_doctors) - len(top_doctors)
    summary = ""
    if remaining > 0:
        total_audience = sum(d.get("followers", 0) or 0 for d in sorted_doctors)
        summary = f"<blockquote>Всего найдено {len(sorted_doctors)} врачей с суммарной аудиторией {total_audience:,} подписчиков. Ещё {remaining} специалистов доступны в детальном отчёте.</blockquote>"

    return f"""<section id="experts">
  <div class="section-label">03 — Эксперты</div>
  <h2>Ключевые специалисты</h2>
  <p>Найдено {len(sorted_doctors)} врачей с соцсетями.</p>
  <div class="expert-category">
    <div class="cat-title">ТОП-{len(top_doctors)} врачей по аудитории</div>
    {cards}
  </div>
  {summary}
</section>
<hr>"""


def _build_content(data: dict) -> str:
    """Content analysis section from instagram_content.json."""
    ig_content = data.get("instagram_content")
    if not ig_content:
        return ""

    doctors = ig_content.get("doctors", [])
    patient_fears = ig_content.get("patient_fears", [])

    # Rating emoji helper
    def _rating_emoji(idx, total):
        if idx == 0 or total <= 2:
            return "🔥"
        if idx < total // 2:
            return "🟢"
        return "🟡"

    # Per-doctor content cards
    doctor_cards = ""
    for i, doc in enumerate(doctors):
        name = doc.get("name") or doc.get("full_name") or "—"
        style = doc.get("style") or doc.get("content_style") or ""
        avg_likes = doc.get("avg_likes") or doc.get("avg_likes_count", 0) or 0
        avg_views = doc.get("avg_views") or 0
        themes = doc.get("themes", [])
        gaps_list = doc.get("gaps", [])
        potential = doc.get("potential") or ""

        themes_html = ""
        if themes:
            theme_tags = " ".join(f'<span class="tag-badge">{_esc(t)}</span>' for t in (themes if isinstance(themes, list) else [themes]))
            themes_html = f'<div style="margin:8px 0">{theme_tags}</div>'

        gaps_html = ""
        if gaps_list:
            gap_strs = [str(g) for g in (gaps_list if isinstance(gaps_list, list) else [gaps_list])]
            gaps_html = f'<p style="font-size:12px;color:var(--red)">Пробелы: {", ".join(_esc(g) for g in gap_strs)}</p>'

        emoji = _rating_emoji(i, len(doctors))
        doctor_cards += f"""<div class="card">
  <h4>{emoji} {_esc(name)}</h4>
  {f'<p style="font-size:13px">{_esc(style)}</p>' if style else ''}
  {f'<p style="font-size:12px;color:var(--text-dim)">~{_esc(str(avg_likes))} лайков · ~{_esc(str(avg_views))} просмотров</p>' if avg_likes or avg_views else ''}
  {themes_html}
  {gaps_html}
  {f'<p style="font-size:12px;color:var(--text-secondary);margin-top:8px">Потенциал: {_esc(potential)}</p>' if potential else ''}
</div>"""

    # Patient fears section
    fears_html = ""
    if patient_fears:
        fear_cards = ""
        for fear in patient_fears[:5]:
            fear_name = fear.get("fear") or fear.get("name") or "—"
            frequency = fear.get("frequency") or ""
            covered_by = fear.get("covered_by") or ""
            if isinstance(covered_by, list):
                covered_by = ", ".join(covered_by)
            fear_cards += f"""<div class="card">
  <h4 style="color:var(--red)">{_esc(fear_name)}</h4>
  {f'<p style="font-size:13px">Частота: {_esc(str(frequency))}</p>' if frequency else ''}
  {f'<p style="font-size:12px;color:var(--text-dim)">Освещается: {_esc(str(covered_by)) if covered_by else "Нет"}</p>' if covered_by else ''}
</div>"""

        fears_html = f"""<h3>Топ-5 страхов пациентов (с форумов)</h3>
<div class="grid-2">{fear_cards}</div>"""

    key_insight = ""
    if doctors:
        key_insight = "<blockquote>Контент врачей — мощный канал доверия. Регулярные публикации с экспертным контентом повышают узнаваемость клиники и привлекают пациентов.</blockquote>"

    return f"""<section id="content-analysis">
  <div class="section-label">04 — Контент-анализ</div>
  <h2>Что публикуют врачи — и что волнует пациентов</h2>
  <p>Анализ контента ключевых специалистов.</p>
  {doctor_cards}
  {fears_html}
  {key_insight}
</section>
<hr>"""


def _build_media(data: dict) -> str:
    """Media section — SMI mentions from smi_mentions.json."""
    smi = data.get("smi_mentions")
    if not smi:
        return ""
    articles = smi.get("articles", [])
    if not articles:
        return ""

    article_html = ""
    for a in articles:
        publication = a.get("publication") or a.get("source") or "—"
        title = a.get("title") or ""
        url = a.get("url") or ""
        sentiment = a.get("sentiment") or ""
        year = a.get("year") or ""

        sentiment_tag = ""
        if sentiment:
            tag_color = "var(--green)" if sentiment.lower() in ("positive", "позитивная") else ("var(--red)" if sentiment.lower() in ("negative", "негативная") else "var(--text-dim)")
            sentiment_tag = f'<span class="tag-badge" style="color:{tag_color}">{_esc(sentiment)}</span>'

        if url:
            display_title = f'<a href="{_esc(url)}" class="article-link" target="_blank" rel="noopener noreferrer"><div class="title">{_esc(title or publication)}</div><div class="expert">{_esc(publication)} · {_esc(str(year))} {sentiment_tag}</div></a>'
        else:
            display_title = f'<div class="article-link"><div class="title">{_esc(title or publication)}</div><div class="expert">{_esc(publication)} · {_esc(str(year))} {sentiment_tag}</div></div>'
        article_html += display_title

    return f"""<section id="media">
  <div class="section-label">05 — Медийное присутствие</div>
  <h2>Упоминания в СМИ</h2>
  <p>Найдено {len(articles)} публикаций в деловых и профильных изданиях.</p>
  {article_html}
</section>
<hr>"""


def _build_whitefields(data: dict) -> str:
    """Whitefields section — CI gaps and advantages cross-competitor comparison."""
    ci = data.get("ci_analysis", {})
    gaps = ci.get("gaps", [])
    advantages = ci.get("advantages", [])
    if not (gaps or advantages):
        return ""

    # Gaps — what needs development
    gap_blocks = ""
    if gaps:
        gap_items = ""
        for g in gaps:
            text = g if isinstance(g, str) else (g.get("description") or g.get("gap") or str(g))
            sev = g.get("severity", "medium") if isinstance(g, dict) else "medium"
            border_color = "var(--red)" if sev == "high" else "var(--border)"
            gap_items += f'<div class="gap" style="border-left:3px solid {border_color}"><h4>{_esc(text)}</h4></div>'
        gap_blocks += f"<h3>Что нужно развивать</h3>{gap_items}"

    # Advantages — what the client has
    adv_blocks = ""
    if advantages:
        adv_items = ""
        for a in advantages:
            text = a if isinstance(a, str) else (a.get("description") or a.get("advantage") or str(a))
            adv_items += f'<div class="gap" style="border-left:3px solid var(--green)"><h4>{_esc(text)}</h4></div>'
        adv_blocks += f"<h3 style=\"margin-top:24px\">Конкурентные преимущества</h3>{adv_items}"

    return f"""<section id="whitefields">
  <div class="section-label">06 — Белые поля</div>
  <h2>Где конкуренты вас опережают</h2>
  <p>Сравнительный анализ цифрового присутствия.</p>
  {gap_blocks}
  {adv_blocks}
</section>
<hr>"""


def _build_presence(data: dict) -> str:
    """Digital presence section — platform status table and review ratings."""
    prescan = data.get("prescan", {})
    stage2 = prescan.get("stage_2_under_the_hood", {}) or {}

    reviews_data = stage2.get("reviews_data") or prescan.get("reviews") or {}
    review_platforms = reviews_data.get("platforms", []) if isinstance(reviews_data, dict) else []

    if not review_platforms:
        return ""

    # Review cards in grid-3
    review_cards = ""
    for platform in review_platforms:
        name = platform.get("platform") or platform.get("name") or "—"
        rating_val = platform.get("rating") or platform.get("score", "—")
        count = platform.get("reviews_count") or platform.get("count", "—")
        url = platform.get("url", "")

        count_str = str(count)
        if count_str in ("данных нет", "None", "0", "—"):
            count_label = "нет данных"
        elif count_str.startswith("~") or count_str.isdigit() or (count_str.replace(",", "").isdigit()):
            count_label = f"{count_str} отзывов"
        else:
            count_label = count_str

        review_cards += f"""<div class="card">
  <h4>{_esc(name)}</h4>
  <div class="num">{_esc(str(rating_val))}</div>
  <p>{_esc(count_label)}</p>
  {f'<a href="{_esc(url)}" style="color:var(--accent);font-size:12px" target="_blank" rel="noopener noreferrer">Открыть →</a>' if url else ''}
</div>"""

    # Platform presence table
    instagram = prescan.get("instagram", {}) or {}
    ig_handle = instagram.get("handle", "")

    platforms_status = []
    # 2GIS
    has_2gis = any(p.get("platform", "").lower() == "2gis" for p in review_platforms)
    platforms_status.append(f'<div class="row"><div class="k">2GIS</div><div class="v">{"✓ Найдено" if has_2gis else "— Не проверено"}</div></div>')
    # Yandex Maps
    has_yandex = any("yandex" in p.get("platform", "").lower() for p in review_platforms)
    platforms_status.append(f'<div class="row"><div class="k">Яндекс.Карты</div><div class="v">{"✓ Найдено" if has_yandex else "— Не проверено"}</div></div>')
    # Google Maps
    has_google = any("google" in p.get("platform", "").lower() for p in review_platforms)
    platforms_status.append(f'<div class="row"><div class="k">Google Maps</div><div class="v">{"✓ Найдено" if has_google else "— Не проверено"}</div></div>')
    # Instagram
    platforms_status.append(f'<div class="row"><div class="k">Instagram</div><div class="v">{_esc(ig_handle) if ig_handle else "— Не найден"}</div></div>')
    # Other platforms
    platforms_status.append('<div class="row"><div class="k">VK</div><div class="v">— Не проверено</div></div>')
    platforms_status.append('<div class="row"><div class="k">Telegram</div><div class="v">— Не проверено</div></div>')
    platforms_status.append('<div class="row"><div class="k">YouTube</div><div class="v">— Не проверено</div></div>')
    platforms_status.append('<div class="row"><div class="k">ПроДокторов</div><div class="v">— Не проверено</div></div>')

    return f"""<section id="presence">
  <div class="section-label">07 — Цифровое присутствие</div>
  <h2>Где вас находят пациенты</h2>
  <h3>Рейтинги на площадках</h3>
  <div class="grid-3">
    {review_cards}
  </div>
  <h3 style="margin-top:32px">Статус присутствия</h3>
  {''.join(platforms_status)}
</section>
<hr>"""


def _build_strategy(data: dict) -> str:
    """Strategy section — 5-pillar recommendations from CI analysis data."""
    ci = data.get("ci_analysis", {})
    top_rec = ci.get("top_recommendation", "")
    priority_actions = ci.get("priority_actions", []) or []
    gaps = ci.get("gaps", [])
    steal_worthy = ci.get("steal_worthy", [])

    if not (top_rec or priority_actions or gaps):
        return ""

    pillars = []

    # Pillar 1: SEO & Technical
    prescan = data.get("prescan", {})
    stage2 = prescan.get("stage_2_under_the_hood", {}) or {}
    seo_score = stage2.get("seo_score")
    seo_fails = stage2.get("seo_fails", []) or []
    if seo_score is not None or seo_fails:
        seo_desc = "Оптимизация технического SEO — фундамент видимости в поиске. "
        if seo_score is not None:
            seo_desc += f"Текущий SEO Score: {seo_score}/100. "
        if seo_fails:
            seo_desc += f"Найдено {len(seo_fails)} критических проблем."
        pillars.append(("01", "SEO и технический аудит", seo_desc))

    # Pillar 2: Content strategy
    if data.get("instagram_content"):
        pillars.append(("02", "Контент-стратегия", "Развитие контента врачей в Instagram и других соцсетях. Регулярный экспертный контент повышает доверие и привлекает пациентов из поиска."))

    # Pillar 3: Social media
    has_social_gaps = bool(gaps)
    if has_social_gaps:
        pillars.append(("03", "Социальные сети", "Закрытие пробелов в цифровом присутствии: Telegram, VK, YouTube. Каждая площадка — дополнительный канал привлечения пациентов."))

    # Pillar 4: Whitefields / steal-worthy
    if steal_worthy:
        tactics = [s if isinstance(s, str) else s.get("tactic", str(s)) for s in steal_worthy[:3]]
        tactics_str = ", ".join(tactics)
        pillars.append(("04", "Белые поля", f"Тактики конкурентов, которые стоит перенять: {_esc(tactics_str)}."))

    # Pillar 5: Top recommendation
    if top_rec:
        pillars.append(("05", "Главная рекомендация", _esc(top_rec)))

    # Build pillar blocks
    pillar_blocks = ""
    for step_num, title, desc in pillars[:5]:
        pillar_blocks += f"""<div class="strategy-block">
  <div class="header">
    <span class="step">{step_num}</span>
    <h3>{title}</h3>
  </div>
  <p>{desc}</p>
</div>"""

    # Priority actions
    actions_html = ""
    if priority_actions:
        action_items = ""
        for i, action in enumerate(priority_actions[:5]):
            text = action if isinstance(action, str) else (action.get("action") or action.get("name") or str(action))
            action_items += f'<div class="gap"><h4>Шаг {i + 1}</h4><p>{_esc(text)}</p></div>'
        actions_html = f"<h3>Первоочередные действия</h3>{action_items}"

    return f"""<section id="strategy">
  <div class="section-label">08 — Стратегия</div>
  <h2>План действий</h2>
  <p>На основе анализа конкурентов и цифрового присутствия.</p>
  {pillar_blocks}
  {actions_html}
  <div class="cta-box">
    <h3>Готовы действовать?</h3>
    <p>Команда AIM реализует эти рекомендации.</p>
    <a href="https://t.me/aim_hermes_bot" class="btn" target="_blank" rel="noopener noreferrer">Связаться в Telegram</a>
  </div>
</section>
<hr>"""


def _build_offer(data: dict) -> str:
    """Offer section — AIM services catalog. Template-driven, always renders."""
    prescan = data.get("prescan", {})
    client_name = prescan.get("client_name") or data.get("metadata", {}).get("client_name") or "вашей клинике"

    return f"""<section id="offer">
  <div class="section-label">09 — Предложение AIM</div>
  <h2>Как мы поможем {_esc(client_name)}</h2>
  <p>AIM — AI-first маркетинговое агентство для медицинских организаций. Мы не делаем &laquo;всё для всех&raquo;. Мы специализируемся на коммерческой медицине и знаем этот рынок досконально.</p>
  <div class="grid-2">
    <div class="card">
      <h4>SEO и поисковое продвижение</h4>
      <p>Технический аудит, оптимизация, рост позиций в Яндекс и Google. Приводим пациентов, которые уже ищут ваши услуги.</p>
    </div>
    <div class="card">
      <h4>Контент-маркетинг</h4>
      <p>Экспертный контент от врачей: статьи, посты, видео. Формируем доверие и повышаем конверсию.</p>
    </div>
    <div class="card">
      <h4>Социальные сети</h4>
      <p>Ведение Instagram, Telegram, VK. Стратегия, контент-план, съёмка, оформление.</p>
    </div>
    <div class="card">
      <h4>Управление репутацией</h4>
      <p>Работа с отзывами на 2GIS, Яндекс.Картах, ПроДокторов. Повышаем рейтинг и доверие.</p>
    </div>
    <div class="card">
      <h4>Контекстная реклама</h4>
      <p>Настройка и ведение Яндекс.Директ. Точное попадание в целевую аудиторию.</p>
    </div>
    <div class="card">
      <h4>Аналитика и отчётность</h4>
      <p>Сквозная аналитика: от показов до записи на приём. Прозрачные метрики и ROI.</p>
    </div>
  </div>
  <div class="cta-box">
    <h3>Начните с аудита</h3>
    <p>Первый шаг — глубокий анализ вашего цифрового присутствия. Это бесплатно и занимает 30 минут.</p>
    <a href="https://t.me/aim_hermes_bot" class="btn" target="_blank" rel="noopener noreferrer">Получить аудит</a>
  </div>
</section>
<hr>"""


# ── HTML Assembly ───────────────────────────────────────────────────────────

def _build_html(data: dict) -> str:
    """Build complete self-contained HTML page from session data."""
    sections = [
        _build_hero(data),
        _build_exec_summary(data),
        _build_financials(data),
        _build_competitors(data),
        _build_ci_gaps(data),
        _build_seo(data),
        _build_pagespeed(data),
        _build_reviews(data),
        _build_recommendations(data),
        _build_footer(data),
    ]
    body_sections = "".join(s for s in sections if s)
    nav_html = _build_nav(data)
    client_name = (
        data.get("metadata", {}).get("client_name")
        or data.get("prescan", {}).get("client_name")
        or "Клиника"
    )

    return f"""<!DOCTYPE html>
<html lang="ru">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="robots" content="noindex,nofollow">
<title>AIM Research — {_esc(str(client_name))}</title>
<script>var t=localStorage.getItem('theme');if(t)document.documentElement.dataset.theme=t;</script>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Inter:opsz@14..32&family=Playfair+Display:ital,wght@0,400;0,700;1,400&display=swap" rel="stylesheet">
<style>{AIM_DESIGN_CSS}</style>
</head>
<body>
<div class="ripple">
  <div class="ripple-ring ring-lg-1"></div>
  <div class="ripple-ring ring-lg-2"></div>
  <div class="ripple-ring ring-lg-3"></div>
  <div class="ripple-ring ring-lg-4"></div>
  <div class="ripple-ring ring-lg-5"></div>
  <div class="ripple-ring ring-lg-6"></div>
  <div class="ripple-ring ring-pulse-1"></div>
  <div class="ripple-ring ring-pulse-2"></div>
  <div class="ripple-ring ring-pulse-3"></div>
  <div class="ripple-ring ring-pulse-4"></div>
  <div class="ripple-ring ring-pulse-5"></div>
  <div class="ripple-ring ring-pulse-6"></div>
  <div class="ripple-ring ring-pulse-7"></div>
  <div class="ripple-ring ring-pulse-8"></div>
</div>
{nav_html}
<div class="container">
{body_sections}
</div>
</body>
</html>""".replace("\n", "")


# ── WordPress Publisher ─────────────────────────────────────────────────────

def _publish_to_wordpress(html: str, title: str) -> dict:
    """Insert HTML page into WordPress wp_posts table. Returns {url, slug, post_id}."""
    if not WP_DB_PASSWORD:
        return {"error": "WP_DB_PASSWORD not configured in Hermes environment"}

    page_slug = _random_slug()
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
                    1, now, now, html, title,
                    "publish", "closed", "closed", page_slug, "page",
                    "", "", "", "", 0,
                ),
            )
            post_id = cur.lastrowid
        conn.commit()

        url = f"https://iamaim.ru/{page_slug}"
        logger.info("HTML report published: post_id=%s url=%s", post_id, url)

        return {"status": "published", "url": url, "slug": page_slug, "post_id": post_id, "title": title}

    except pymysql.Error as e:
        logger.error("MySQL error: %s", e)
        return {"error": f"Database error: {str(e)}"}
    except Exception as e:
        logger.error("Unexpected error: %s", e)
        return {"error": f"Failed to publish page: {str(e)}"}
    finally:
        if conn:
            conn.close()


# ── Main Handler ────────────────────────────────────────────────────────────

async def handle_generate_html_report(
    session_hash=None,
    client_name=None,
    client_url=None,
    **kwargs,
) -> str:
    """Generate and publish an HTML report from session data in AIM design system.

    Reads session archive, builds a glass-morphism dark-theme HTML page,
    publishes it to WordPress, and returns the public URL.

    Args:
        session_hash: Session archive hash (from finalize_research)
        client_name: Override client name for the report
        client_url: Override client website URL
    """
    if isinstance(session_hash, dict):
        d = session_hash
        session_hash = d.get("session_hash", "")
        if not client_name:
            client_name = d.get("client_name", "")
        if not client_url:
            client_url = d.get("client_url", "")

    if not session_hash:
        return json.dumps({"error": "session_hash is required — the archive hash from finalize_research"})

    logger.info("Generating HTML report for session %s", session_hash)

    # 1. Load session data
    data = _load_session_data(session_hash)

    # Override with explicit params if provided
    if client_name:
        data.setdefault("metadata", {})["client_name"] = client_name
        data["prescan"]["client_name"] = client_name
    if client_url:
        data.setdefault("metadata", {})["client_url"] = client_url
        data["prescan"]["website"] = client_url

    # 2. Generate HTML
    client_label = client_name or data.get("metadata", {}).get("client_name") or data.get("prescan", {}).get("client_name") or "Клиника"
    html = _build_html(data)
    title = f"AIM Research — {client_label}"

    # 3. Publish
    result = _publish_to_wordpress(html, title)

    if "error" in result:
        return json.dumps(result, ensure_ascii=False)

    return json.dumps(result, ensure_ascii=False, indent=2)


# ── Registry ────────────────────────────────────────────────────────────────

registry.register(
    name="generate_html_report",
    toolset="aim-operations",
    schema={
        "type": "function",
        "function": {
            "name": "generate_html_report",
            "description": (
                "Создаёт и публикует красивый HTML-отчёт по результатам исследования сессии "
                "в дизайн-системе AIM (стекломорфизм, тёмная тема, Art Deco gold). "
                "Читает данные сессии из /opt/data/sessions-archive/{hash}/, "
                "генерирует самодостаточную HTML-страницу с метриками, SEO, конкурентами, "
                "финансами, PageSpeed — и публикует в WordPress. "
                "Возвращает публичный URL вида https://iamaim.ru/{random-slug}. "
                "Вызывай после finalize_research, когда сессия заархивирована. "
                "Либо используй в конце пресейла для финального отчёта клиенту."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "session_hash": {
                        "type": "string",
                        "description": (
                            "[REQUIRED] Хеш сессии (session_hash) — "
                            "возвращается из finalize_research. "
                            "Используется для чтения архива сессии."
                        ),
                    },
                    "client_name": {
                        "type": "string",
                        "description": "Название клиники (для заголовка отчёта). Если не указан — берётся из архива.",
                    },
                    "client_url": {
                        "type": "string",
                        "description": "Сайт клиники (для отчёта). Если не указан — берётся из архива.",
                    },
                },
                "required": ["session_hash"],
            },
        },
    },
    handler=handle_generate_html_report,
    check_fn=lambda: bool(WP_DB_PASSWORD),
    is_async=True,
    description="Generate and publish a beautiful AIM design system HTML report from session data",
    emoji="📄",
)
