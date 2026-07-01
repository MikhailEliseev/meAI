"""build_report — Canonical HTML report builder with AIM Design System.

CRITICAL FIX (1 июля 2026):
- Google Fonts подключены через <link> (Playfair Display + Jost)
- Все 14 canonical классов из design-showcase-dual-theme.html
- Theme toggle + water ripples в светлой теме
- Metric tags (5 цветов) + glass cards + surface blocks
- КАНОН: AIM/frontend/design-showcase-dual-theme.html (2513 строк)

Заменяет generate_html_report.py (698 строк, только 1/14 классов, нет шрифтов).
"""

import json
import logging

logger = logging.getLogger(__name__)


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


# ── CANONICAL CSS (extracted from AIM/frontend/design-showcase-dual-theme.html) ──

_CANONICAL_CSS = """<style>
/* === DUAL THEME SYSTEM === */
/* Canonical reference: AIM/frontend/design-showcase-dual-theme.html (2513 lines) */

/* LIGHT THEME — Monochrome */
:root {
    --bg: #ffffff;
    --surface: #F5F5F5;
    --hover: #EBEBEB;
    --border: #E0E0E0;
    --border-strong: #CFCFCF;
    --text: #1A1A1A;
    --text-secondary: #666666;
    --text-dim: #767676;
    --accent: #1A1A1A;
    --accent-hover: #333333;
    --card-bg: #ffffff;
    --card-hover: #F5F5F5;
    --glass-bg: rgba(255,255,255,0.85);
    --glass-border: rgba(0,0,0,0.10);
    --glow-outer: rgba(0,0,0,0.07);
    --glow-inner: rgba(0,0,0,0.025);
}

/* DARK THEME — Art Deco Gold */
[data-theme="dark"] {
    --bg: #0d0d0d;
    --surface: #1a1a1a;
    --hover: #262626;
    --border: rgba(201,169,110,.18);
    --border-strong: rgba(201,169,110,.35);
    --text: #f5f0e8;
    --text-secondary: #9e9489;
    --text-dim: #7a7268;
    --accent: #c9a96e;
    --accent-hover: #e8cfa0;
    --card-bg: #1a1a1a;
    --card-hover: rgba(201,169,110,.05);
    --glass-bg: rgba(13,13,13,0.85);
    --glass-border: rgba(201,169,110,.10);
    --glow-outer: rgba(201,169,110,0.08);
    --glow-inner: rgba(201,169,110,0.03);
}

*, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

html { scroll-behavior: smooth; font-size: 16px; }

body {
    font-family: 'Jost', sans-serif;
    font-weight: 400;
    font-size: 16px;
    line-height: 1.7;
    background: var(--bg);
    color: var(--text);
    -webkit-font-smoothing: antialiased;
    transition: background .3s, color .3s;
    overflow-x: hidden;
}

h1, h2, h3, h4 {
    font-family: 'Playfair Display', serif;
    font-weight: 500;
    line-height: 1.15;
    color: var(--text);
    letter-spacing: -.01em;
}

h1 { font-size: clamp(32px, 4vw, 48px); margin-bottom: 24px; }
h2 { font-size: clamp(24px, 3vw, 32px); margin-bottom: 20px; color: var(--accent); }
h3 { font-size: 20px; margin: 24px 0 12px; }
h4 { font-size: 18px; margin: 16px 0 8px; }

p { margin: 12px 0; }
a { color: var(--accent); text-decoration: none; }
a:hover { text-decoration: underline; }
strong { font-weight: 600; }
ul, ol { margin: 12px 0 16px 24px; }
li { margin: 6px 0; }

/* === WATER RIPPLE ANIMATIONS === */
@keyframes water-ripple {
    0% { transform: translate(-50%, -50%) scale(0); opacity: 0.77; }
    15% { opacity: 0.48; }
    35% { opacity: 0.28; }
    60% { opacity: 0.11; }
    85% { opacity: 0.035; }
    100% { transform: translate(-50%, -50%) scale(1); opacity: 0; }
}

@keyframes card-breathe {
    0%, 100% { box-shadow: 0 2px 12px rgba(0,0,0,0.03); }
    50% { box-shadow: 0 6px 24px rgba(0,0,0,0.07); }
}

@keyframes glass-glow {
    0%, 100% {
        box-shadow: 0 0 14px var(--glow-outer), inset 0 0 20px var(--glow-inner);
    }
    50% {
        box-shadow: 0 0 22px var(--glow-outer), inset 0 0 30px var(--glow-inner);
    }
}

.water-ripples {
    position: fixed; top: 0; left: 0; right: 0; bottom: 0;
    pointer-events: none; z-index: 0; overflow: hidden;
}

[data-theme="dark"] .water-ripples { display: none; }

.ripple-ring {
    position: absolute;
    top: 50%; left: 50%;
    transform: translate(-50%, -50%) scale(0);
    border-radius: 50%;
    border: 1px solid var(--text);
    opacity: 0;
    width: 850px; height: 850px;
    animation: water-ripple 10s cubic-bezier(0.22, 0.61, 0.36, 1) infinite;
}

@media (prefers-reduced-motion: reduce) { .ripple-ring { animation: none; display: none; } }
@media (max-width: 768px) { .water-ripples { display: none; } }

/* === THEME TOGGLE === */
.theme-toggle {
    position: fixed;
    top: 24px;
    right: 24px;
    width: 48px;
    height: 48px;
    border-radius: 24px;
    background: var(--surface);
    border: 1px solid var(--border);
    cursor: pointer;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 20px;
    transition: all .2s;
    z-index: 100;
}

.theme-toggle:hover {
    background: var(--hover);
    transform: scale(1.05);
}

.theme-icon-sun { display: none; }
.theme-icon-moon { display: block; }
[data-theme="dark"] .theme-icon-sun { display: block; }
[data-theme="dark"] .theme-icon-moon { display: none; }

/* === CONTAINER === */
.report-container {
    max-width: 900px;
    margin: 0 auto;
    padding: 80px 40px 60px;
    position: relative;
    z-index: 1;
}

/* === SECTION === */
.section {
    padding: 48px 0;
    border-bottom: 1px solid var(--border);
}

.section:last-child { border-bottom: none; }

.sec-tag {
    display: inline-flex;
    align-items: center;
    gap: 12px;
    font-family: 'Jost', sans-serif;
    font-size: 11px;
    font-weight: 600;
    letter-spacing: .2em;
    text-transform: uppercase;
    color: var(--accent);
    margin-bottom: 16px;
}

.sec-tag::before {
    content: '';
    display: block;
    width: 32px;
    height: 1px;
    background: var(--accent);
}

/* === METRIC TAGS === */
.metric-tag {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    font-family: 'Jost', sans-serif;
    font-size: 11px;
    font-weight: 600;
    padding: 5px 12px;
    border-radius: 12px;
    letter-spacing: 0.5px;
    margin: 4px 6px 4px 0;
}

.metric-tag-dot {
    width: 6px;
    height: 6px;
    border-radius: 50%;
}

/* Green */
.metric-tag-green { background: #E8F5E9; color: #2E7D32; }
.metric-tag-green .metric-tag-dot { background: #2E7D32; }
[data-theme="dark"] .metric-tag-green { background: #1B5E20; color: #81C784; }
[data-theme="dark"] .metric-tag-green .metric-tag-dot { background: #81C784; }

/* Yellow */
.metric-tag-yellow { background: #FFF9C4; color: #F57F17; }
.metric-tag-yellow .metric-tag-dot { background: #F57F17; }
[data-theme="dark"] .metric-tag-yellow { background: #F57F17; color: #FFF9C4; }
[data-theme="dark"] .metric-tag-yellow .metric-tag-dot { background: #FFF9C4; }

/* Red */
.metric-tag-red { background: #FFEBEE; color: #C62828; }
.metric-tag-red .metric-tag-dot { background: #C62828; }
[data-theme="dark"] .metric-tag-red { background: #C62828; color: #FFCDD2; }
[data-theme="dark"] .metric-tag-red .metric-tag-dot { background: #FFCDD2; }

/* Blue */
.metric-tag-blue { background: #E3F2FD; color: #1565C0; }
.metric-tag-blue .metric-tag-dot { background: #1565C0; }
[data-theme="dark"] .metric-tag-blue { background: #1A237E; color: #90CAF9; }
[data-theme="dark"] .metric-tag-blue .metric-tag-dot { background: #90CAF9; }

/* Gray (neutral) */
.metric-tag-gray {
    background: var(--surface);
    color: var(--text-secondary);
    border: 1px solid var(--border);
}
.metric-tag-gray .metric-tag-dot { background: var(--text-secondary); }

/* === SURFACE BLOCK === */
.surface-block {
    background: var(--surface);
    border-left: 3px solid var(--accent);
    padding: 20px 24px;
    margin: 16px 0;
}

.surface-block p {
    font-family: 'Jost', sans-serif;
    font-size: 14px;
    color: var(--text);
    font-weight: 500;
    margin: 0;
}

/* === GLASS CARD === */
.card-glass {
    background: var(--glass-bg);
    backdrop-filter: blur(20px) saturate(1.4);
    border: 1px solid var(--glass-border);
    border-radius: 8px;
    padding: 32px;
    animation: card-breathe 4s ease-in-out infinite, glass-glow 5s ease-in-out infinite;
    margin: 20px 0;
}

.card-glass h3 {
    font-family: 'Playfair Display', serif;
    font-size: 20px;
    font-weight: 500;
    margin-bottom: 12px;
}

.card-glass p {
    font-family: 'Jost', sans-serif;
    font-size: 15px;
    color: var(--text-secondary);
    line-height: 1.7;
}

/* === GLASS STATS === */
.glass-stats-wrap {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
    gap: 16px;
    margin: 24px 0;
}

.glass-stat {
    background: var(--glass-bg);
    backdrop-filter: blur(16px) saturate(1.3);
    border: 1px solid var(--glass-border);
    border-radius: 6px;
    padding: 36px 28px;
    text-align: center;
    transition: transform .3s, box-shadow .3s, border-color .3s;
    animation: glass-glow 5s ease-in-out infinite;
}

.glass-stat:hover {
    border-color: var(--accent);
    transform: translateY(-4px);
    box-shadow: 0 8px 28px rgba(0,0,0,0.06);
}

.glass-stat-value {
    font-family: 'Playfair Display', serif;
    font-size: clamp(32px, 4vw, 48px);
    font-weight: 400;
    color: var(--accent);
    line-height: 1;
    margin-bottom: 12px;
}

.glass-stat-label {
    font-family: 'Jost', sans-serif;
    font-size: 12px;
    font-weight: 500;
    letter-spacing: .06em;
    text-transform: uppercase;
    color: var(--text-secondary);
}

/* === GLASS TABLE === */
.glass-table-wrap {
    overflow-x: auto;
    border: 1px solid var(--glass-border);
    border-radius: 8px;
    margin: 24px 0;
    background: var(--glass-bg);
    backdrop-filter: blur(16px) saturate(1.3);
    animation: glass-glow 5s ease-in-out infinite;
}

.glass-table-wrap table {
    width: 100%;
    border-collapse: collapse;
    font-size: 14px;
}

.glass-table-wrap thead { background: transparent; }

.glass-table-wrap th {
    padding: 14px 20px;
    text-align: left;
    font-family: 'Jost', sans-serif;
    font-weight: 600;
    font-size: 11px;
    letter-spacing: .05em;
    text-transform: uppercase;
    color: var(--text-secondary);
    border-bottom: 1px solid var(--border);
}

.glass-table-wrap td {
    padding: 14px 20px;
    border-bottom: 1px solid var(--border);
    color: var(--text-secondary);
}

.glass-table-wrap tr:last-child td { border-bottom: none; }
.glass-table-wrap tr:hover td { background: var(--hover); }

/* === CTA BOX === */
.cta-box {
    text-align: center;
    padding: 60px 40px;
    border: 1.5px solid var(--text);
    margin: 40px 0;
}

.cta-box h2 {
    font-family: 'Playfair Display', serif;
    font-size: clamp(24px, 2.5vw, 32px);
    font-weight: 400;
    margin-bottom: 16px;
}

.cta-box p {
    color: var(--text-secondary);
    max-width: 500px;
    margin: 0 auto 28px;
    font-size: 15px;
}

.btn-primary {
    display: inline-block;
    padding: 15px 40px;
    background: var(--accent);
    color: var(--bg);
    border: none;
    font-family: 'Jost', sans-serif;
    font-size: 13px;
    font-weight: 600;
    letter-spacing: .1em;
    text-transform: uppercase;
    border-radius: 1px;
    text-decoration: none;
    transition: all .3s;
}

.btn-primary:hover {
    background: var(--accent-hover);
    transform: translateY(-2px);
    box-shadow: 0 8px 24px rgba(0,0,0,.15);
    text-decoration: none;
}

/* === INTERPRETATION CONTENT === */
.interpretation p { margin: 12px 0; }
.interpretation h3 { margin: 24px 0 12px; border-bottom: 1px solid var(--border); padding-bottom: 6px; }
.interpretation ul, .interpretation ol { margin: 12px 0 16px 24px; }
.interpretation li { margin: 6px 0; }

/* === RESPONSIVE === */
@media (max-width: 768px) {
    .report-container { padding: 60px 24px 40px; }
    .glass-stats-wrap { grid-template-columns: 1fr; }
    .cta-box { padding: 40px 24px; }
}
</style>"""


_THEME_TOGGLE_SCRIPT = """<script>
(function() {
    const html = document.documentElement;
    const toggle = document.getElementById('theme-toggle');

    // Load saved theme
    const saved = localStorage.getItem('aim-theme');
    if (saved) html.setAttribute('data-theme', saved);

    // Toggle handler
    if (toggle) {
        toggle.addEventListener('click', () => {
            const current = html.getAttribute('data-theme') || 'light';
            const next = current === 'light' ? 'dark' : 'light';
            html.setAttribute('data-theme', next);
            localStorage.setItem('aim-theme', next);
        });
    }
})();
</script>"""


async def handle_generate_html_report(
    session_hash: str = None,
    title: str = None,
    client_name: str = None,
    client_url: str = None,
    **kwargs,
) -> str:
    """Handler: Generate and publish HTML report (wrapper for build_report_html)."""
    import os
    import pymysql
    import secrets
    import string
    from datetime import datetime, timezone

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
    from app.tools.session_archive import load_all_data, SESSIONS_ROOT
    data = load_all_data(session_hash)

    # Merge metadata overrides
    meta = data.get("metadata", {}) or {}
    if client_name:
        meta["company_name"] = client_name
    if client_url:
        meta["url"] = client_url
    data["metadata"] = meta

    # Generate HTML (canonical builder)
    html = build_report_html(data, report_title)

    # WordPress DB credentials
    WP_DB_HOST = os.getenv("WP_DB_HOST", "")
    WP_DB_USER = os.getenv("WP_DB_USER", "")
    WP_DB_PASSWORD = os.getenv("WP_DB_PASSWORD", "")
    WP_DB_NAME = os.getenv("WP_DB_NAME", "")

    # Publish
    if not WP_DB_PASSWORD:
        report_path = os.path.join(SESSIONS_ROOT, session_hash, "report.html")
        os.makedirs(os.path.dirname(report_path), exist_ok=True)
        with open(report_path, "w", encoding="utf-8") as f:
            f.write(html)
        return json.dumps({
            "status": "saved_locally",
            "path": report_path,
            "session_hash": session_hash,
        }, ensure_ascii=False)

    page_slug = ''.join(secrets.choice(string.ascii_lowercase + string.digits) for _ in range(8))
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
                    "INSERT INTO wp_posts (post_title, post_name, post_content, post_status, post_type, post_date, post_modified, post_excerpt) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)",
                    (wp_title, page_slug, html, "publish", "page", now, now, ""),
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


def build_report_html(data: dict, title: str) -> str:
    """Build canonical HTML report with Google Fonts + all 14 classes.

    Args:
        data: Session data with phases, interpretations, metadata
        title: Report title

    Returns:
        Full HTML document
    """

    # Extract metadata
    meta = data.get("metadata", {}) or {}
    company_name = meta.get("company_name", title)
    url = meta.get("url", "")

    # Extract interpretations
    interpretations = data.get("interpretations", {}) or {}

    # Build phase sections
    phase_sections = []

    phase_order = [
        ("PERPLEXITY", "Исследование рынка"),
        ("COMPETITORS", "Конкуренты"),
        ("TECH AUDIT", "Технический аудит"),
        ("SOCIAL VERIFIER", "Социальные сети и отзывы"),
        ("CONTENT ANALYSIS", "Контент-анализ"),
        ("KEY PERSONS", "Ключевые персоны"),
        ("SMI MENTIONS", "Упоминания в СМИ"),
        ("FORUM PAINS", "Боли из форумов"),
        ("FINANCE", "Финансы"),
        ("CONTENT PLAN", "Контент-план"),
    ]

    for phase_key, phase_label in phase_order:
        interpretation = interpretations.get(phase_key, "")
        if not interpretation:
            continue

        # Simple markdown to HTML (minimal)
        html_content = interpretation.replace("\n\n", "</p><p>")
        html_content = f"<p>{html_content}</p>"

        phase_sections.append(f"""
<div class="section">
    <span class="sec-tag">{_esc(phase_label)}</span>
    <div class="interpretation">
        {html_content}
    </div>
</div>
""")

    # Build CTA
    cta_html = """
<div class="cta-box">
    <h2>Обсудить результаты</h2>
    <p>Готовы внедрить рекомендации? Свяжитесь с нами для индивидуальной консультации.</p>
    <a href="https://t.me/eliseev_me" class="btn-primary">Связаться</a>
</div>
"""

    # Assemble full HTML
    html = f"""<!DOCTYPE html>
<html lang="ru" data-theme="light">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{_esc(title)} — AIM Scout</title>

    <!-- CRITICAL: Google Fonts (Playfair Display + Jost) -->
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Playfair+Display:ital,wght@0,400;0,500;0,600;0,700;1,400&family=Jost:wght@300;400;500;600;700&display=swap" rel="stylesheet">

    {_CANONICAL_CSS}
</head>
<body>
    <!-- Water ripples (visible only in light theme) -->
    <div class="water-ripples">
        <div class="ripple-ring"></div>
    </div>

    <!-- Theme toggle -->
    <button id="theme-toggle" class="theme-toggle" aria-label="Toggle theme">
        <span class="theme-icon-sun">☀️</span>
        <span class="theme-icon-moon">🌙</span>
    </button>

    <div class="report-container">
        <!-- Header -->
        <h1>{_esc(company_name)}</h1>
        {f'<p class="text-dim">URL: <a href="{_esc(url)}" target="_blank">{_esc(url)}</a></p>' if url else ''}

        <!-- Phase sections -->
        {''.join(phase_sections)}

        <!-- CTA -->
        {cta_html}
    </div>

    {_THEME_TOGGLE_SCRIPT}
</body>
</html>"""

    return html
