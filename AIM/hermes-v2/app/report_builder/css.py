"""Canonical CSS для HTML-отчётов AIM Design System. Перенесено из v1 build_report.py (строки 615-1184)."""

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

/* === THEME TOGGLE (scoped to report) — does not affect WP theme toggle === */
.aim-report-scope .theme-toggle-report {
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

.aim-report-scope .theme-toggle-report:hover {
    background: var(--hover);
    transform: scale(1.05);
}

/* === CONTAINER === */
.report-container {
    max-width: 900px;
    margin: 0 auto;
    padding: 80px 40px 60px;
    position: relative;
    z-index: 1;
}

/* === REVENUE vs COMPETITORS BLOCK (вау-блок в начале) === */
.revenue-block {
    margin: 40px 0 60px;
    padding: 32px 28px;
    background: var(--surface);
    border-radius: 16px;
    border-left: 4px solid var(--accent);
    position: relative;
}
.revenue-block h2 {
    font-family: 'Playfair Display', serif;
    font-size: 28px;
    font-weight: 400;
    line-height: 1.2;
    margin-bottom: 8px;
}
.revenue-block .text-dim {
    font-size: 14px;
    color: var(--text-dim);
    margin-bottom: 16px;
}
.wow-banner {
    background: linear-gradient(90deg, var(--accent), transparent);
    color: var(--bg);
    padding: 12px 20px;
    border-radius: 8px;
    margin: 16px 0;
    font-size: 16px;
    font-weight: 500;
}
[data-theme="dark"] .wow-banner {
    color: var(--bg);
    background: linear-gradient(90deg, var(--accent), rgba(255,255,255,0.05));
}
.wow-banner strong {
    letter-spacing: 0.05em;
}
.comp-table {
    width: 100%;
    border-collapse: collapse;
    margin: 20px 0;
    font-size: 14px;
}
.comp-table thead th {
    text-align: left;
    padding: 12px 14px;
    border-bottom: 2px solid var(--border-strong);
    font-size: 11px;
    font-weight: 600;
    letter-spacing: 0.1em;
    text-transform: uppercase;
    color: var(--text-dim);
}
.comp-table thead th:nth-child(3),
.comp-table thead th:nth-child(4) {
    text-align: center;
}
.comp-row {
    border-bottom: 1px solid var(--border);
    transition: background .2s;
}
.comp-row:hover {
    background: var(--hover);
}
.comp-row.row-client {
    background: var(--hover);
    font-weight: 600;
}
.comp-row.row-client .comp-name,
.comp-row.row-client .comp-revenue {
    color: var(--accent);
    font-weight: 700;
}
.comp-row td {
    padding: 14px;
    vertical-align: middle;
}
.comp-rank {
    width: 40px;
    text-align: center;
    font-weight: 700;
    font-size: 16px;
    color: var(--text-dim);
}
.comp-rank.rank-gold { color: #D4AF37; }
.comp-rank.rank-silver { color: #A8A8A8; }
.comp-rank.rank-bronze { color: #CD7F32; }
.comp-name {
    font-size: 15px;
}
.comp-revenue {
    text-align: center;
    font-size: 18px;
    font-weight: 500;
    font-variant-numeric: tabular-nums;
}
.comp-trend {
    text-align: center;
    font-size: 18px;
}
.comp-trend.trend-up { color: var(--green); }
.comp-trend.trend-down { color: var(--red); }
.comp-trend.trend-stable { color: var(--text-dim); }
.comp-source {
    font-size: 11px !important;
    color: var(--text-dim);
    margin-top: 12px !important;
    text-align: right;
}
.sec-tag-highlight {
    background: var(--accent) !important;
    color: var(--bg) !important;
    font-weight: 600;
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
    letter-spacing: 0.3px;
    margin: 4px 6px 4px 0;
    max-width: 100%;
    word-break: break-word;
    overflow-wrap: break-word;
    hyphens: auto;
    -webkit-hyphens: auto;
    line-height: 1.3;
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
    grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
    gap: 16px;
    margin: 24px 0;
}

.glass-stat {
    background: var(--glass-bg);
    backdrop-filter: blur(16px) saturate(1.3);
    border: 1px solid var(--glass-border);
    border-radius: 6px;
    padding: 28px 20px;
    text-align: center;
    transition: transform .3s, box-shadow .3s, border-color .3s;
    animation: glass-glow 5s ease-in-out infinite;
    display: flex;
    flex-direction: column;
    justify-content: flex-start;
    align-items: center;
    min-height: 0;
    overflow: hidden;
}

.glass-stat:hover {
    border-color: var(--accent);
    transform: translateY(-4px);
    box-shadow: 0 8px 28px rgba(0,0,0,0.06);
}

.glass-stat-value {
    font-family: 'Playfair Display', serif;
    font-size: clamp(22px, 2.5vw, 38px);
    font-weight: 400;
    color: var(--accent);
    line-height: 1.15;
    margin-bottom: 12px;
    word-break: break-word;
    overflow-wrap: break-word;
    hyphens: auto;
    -webkit-hyphens: auto;
    width: 100%;
}

.glass-stat-label {
    font-family: 'Jost', sans-serif;
    font-size: 12px;
    font-weight: 500;
    letter-spacing: .02em;
    text-transform: none;
    color: var(--text-secondary);
    line-height: 1.4;
    word-break: break-word;
    overflow-wrap: break-word;
    hyphens: auto;
    -webkit-hyphens: auto;
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
    .glass-stat { padding: 24px 16px; }
    .glass-stat-value { font-size: clamp(20px, 6vw, 28px); }
    .glass-stat-label { font-size: 11px; }
    .cta-box { padding: 40px 24px; }
}

@media (max-width: 480px) {
    .glass-stats-wrap { grid-template-columns: 1fr; gap: 12px; }
    .glass-stat { padding: 20px 14px; }
    .glass-stat-value { font-size: clamp(18px, 5vw, 24px); margin-bottom: 8px; }
    .metric-tag { font-size: 10px; padding: 4px 10px; }
}
</style>"""
