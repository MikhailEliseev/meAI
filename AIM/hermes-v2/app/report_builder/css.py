"""Canonical CSS для HTML-отчётов AIM Design System.

Объединяет:
- Дизайн-систему (Inter+Playfair light, Art Deco Gold dark, ripple, glass)
- Эталонный стиль отчёта ИПХиК.html (nav, hero, section-label, metrics, gap, footer)

Все классы scoped под .aim-report-scope — не конфликтуют с WP темой.
Шрифты: Playfair Display (заголовки) + Inter (текст). Jost как fallback для
тех классов, что пришли из дизайн-системы (metric-tag, glass-stat, etc).
"""

_CANONICAL_CSS = """<style>
/* === AIM REPORT SCOPE — Dual Theme === */
/* Light: Monochrome Black/White (Inter+Playfair) */
/* Dark:  Art Deco Gold/Black               */

.aim-report-scope {
  --bg-rp: #ffffff;
  --surface-rp: #F5F5F5;
  --hover-rp: #EBEBEB;
  --border-rp: #E0E0E0;
  --border-strong-rp: #CFCFCF;
  --text-rp: #1A1A1A;
  --text-sec-rp: #666666;
  --text-dim-rp: #999999;
  --accent-rp: #1A1A1A;
  --accent-hov-rp: #333333;
  --glass-bg-rp: rgba(255,255,255,0.85);
  --glass-border-rp: rgba(0,0,0,0.10);
  --glow-out-rp: rgba(0,0,0,0.07);
  --glow-in-rp: rgba(0,0,0,0.025);
  --green-rp: #2E7D32;
  --red-rp: #C62828;
  --gold-rp: #D4AF37;
  --silver-rp: #A8A8A8;
  --bronze-rp: #CD7F32;
}

.aim-report-scope[data-theme="dark"] {
  --bg-rp: #0d0d0d;
  --surface-rp: #1a1a1a;
  --hover-rp: #262626;
  --border-rp: rgba(201,169,110,.18);
  --border-strong-rp: rgba(201,169,110,.35);
  --text-rp: #f5f0e8;
  --text-sec-rp: #9e9489;
  --text-dim-rp: #7a7268;
  --accent-rp: #c9a96e;
  --accent-hov-rp: #e8cfa0;
  --glass-bg-rp: rgba(13,13,13,0.85);
  --glass-border-rp: rgba(201,169,110,.10);
  --glow-out-rp: rgba(201,169,110,0.08);
  --glow-in-rp: rgba(201,169,110,0.03);
  --green-rp: #66BB6A;
  --red-rp: #EF5350;
  --gold-rp: #c9a96e;
  --silver-rp: #9e9489;
  --bronze-rp: #b87333;
}

.aim-report-scope *, .aim-report-scope *::before, .aim-report-scope *::after {
  box-sizing: border-box; margin: 0; padding: 0;
}

.aim-report-scope {
  font-family: 'Inter', 'Jost', -apple-system, BlinkMacSystemFont, sans-serif;
  font-weight: 400;
  font-size: 16px;
  line-height: 1.7;
  background: var(--bg-rp);
  color: var(--text-rp);
  -webkit-font-smoothing: antialiased;
  transition: background .3s, color .3s;
  overflow-x: hidden;
  display: block;
}

.aim-report-scope h1, .aim-report-scope h2, .aim-report-scope h3, .aim-report-scope h4 {
  font-family: 'Playfair Display', Georgia, serif;
  font-weight: 500;
  line-height: 1.15;
  color: var(--text-rp);
  letter-spacing: -.01em;
}

.aim-report-scope h1 { font-size: clamp(32px, 4vw, 48px); margin-bottom: 24px; }
.aim-report-scope h2 { font-size: clamp(24px, 3vw, 32px); margin-bottom: 20px; color: var(--text-rp); }
.aim-report-scope h3 { font-size: 20px; margin: 24px 0 12px; }
.aim-report-scope h4 { font-size: 14px; font-weight: 600; margin: 16px 0 8px; text-transform: none; letter-spacing: 0; font-family: 'Inter', sans-serif; }

.aim-report-scope p { margin: 12px 0; color: var(--text-sec-rp); font-size: 15px; line-height: 1.75; }
.aim-report-scope p strong { color: var(--text-rp); font-weight: 600; }
.aim-report-scope a { color: var(--accent-rp); text-decoration: none; }
.aim-report-scope a:hover { text-decoration: underline; text-underline-offset: 2px; }
.aim-report-scope strong { font-weight: 600; color: var(--text-rp); }
.aim-report-scope ul, .aim-report-scope ol { margin: 12px 0 16px 24px; }
.aim-report-scope li { margin: 6px 0; color: var(--text-sec-rp); }

/* === RIPPLE — КРУГИ НА ВОДЕ (из дизайн-системы) === */
@keyframes aim-water-ripple {
  0% { width: 0; height: 0; opacity: 0.77; border-width: 1.4px; }
  15% { opacity: 0.48; border-width: 1.0px; }
  35% { opacity: 0.28; border-width: 0.7px; }
  60% { opacity: 0.11; border-width: 0.4px; }
  85% { opacity: 0.035; border-width: 0.25px; }
  100% { width: 850px; height: 850px; opacity: 0; border-width: 0.12px; }
}

@keyframes aim-card-breathe {
  0%, 100% { box-shadow: 0 2px 12px rgba(0,0,0,0.03); }
  50% { box-shadow: 0 6px 24px rgba(0,0,0,0.07); }
}

@keyframes aim-glass-glow {
  0%, 100% { box-shadow: 0 0 14px var(--glow-out-rp), inset 0 0 20px var(--glow-in-rp); }
  50% { box-shadow: 0 0 22px var(--glow-out-rp), inset 0 0 30px var(--glow-in-rp); }
}

@keyframes aim-pulse-ring {
  0%, 100% { opacity: 0.03; transform: scale(1); }
  50% { opacity: 0.07; transform: scale(1.15); }
}

.aim-report-scope .water-ripples {
  position: fixed; top: 0; left: 0; right: 0; bottom: 0;
  pointer-events: none; z-index: 0; overflow: hidden;
}
.aim-report-scope[data-theme="dark"] .water-ripples { display: none; }

.aim-report-scope .ripple-origin {
  position: absolute; width: 4px; height: 4px;
  border-radius: 50%; background: var(--text-rp);
  opacity: 0.08; transform: translate(-50%, -50%);
}
.aim-report-scope .ripple-origin .ripple-ring {
  position: absolute; top: 50%; left: 50%;
  transform: translate(-50%, -50%);
  border-radius: 50%; border-style: solid;
  border-color: var(--text-rp); background: none;
  opacity: 0; width: 0; height: 0;
  animation: aim-water-ripple cubic-bezier(0.22, 0.61, 0.36, 1) infinite;
}

.aim-report-scope .ripple-origin-1 { top: 50%; left: 50%; }
.aim-report-scope .ripple-origin-2 { top: 18%; left: 14%; }
.aim-report-scope .ripple-origin-3 { top: 72%; right: 12%; left: auto; }
.aim-report-scope .ripple-origin-4 { top: 30%; right: 18%; left: auto; }
.aim-report-scope .ripple-origin-5 { top: 62%; left: 20%; }
.aim-report-scope .ripple-origin-6 { top: 44%; right: 28%; left: auto; }

.aim-report-scope .ripple-origin-1 .ripple-ring { animation-duration: 10s; }
.aim-report-scope .ripple-origin-1 .ripple-ring:nth-child(1) { animation-delay: 0s; }
.aim-report-scope .ripple-origin-1 .ripple-ring:nth-child(2) { animation-delay: 2s; }
.aim-report-scope .ripple-origin-1 .ripple-ring:nth-child(3) { animation-delay: 4s; }
.aim-report-scope .ripple-origin-1 .ripple-ring:nth-child(4) { animation-delay: 6s; }
.aim-report-scope .ripple-origin-1 .ripple-ring:nth-child(5) { animation-delay: 8s; }

.aim-report-scope .ripple-origin-2 .ripple-ring { animation-duration: 11s; }
.aim-report-scope .ripple-origin-2 .ripple-ring:nth-child(1) { animation-delay: 1.5s; }
.aim-report-scope .ripple-origin-2 .ripple-ring:nth-child(2) { animation-delay: 3.7s; }
.aim-report-scope .ripple-origin-2 .ripple-ring:nth-child(3) { animation-delay: 5.9s; }
.aim-report-scope .ripple-origin-2 .ripple-ring:nth-child(4) { animation-delay: 8.1s; }
.aim-report-scope .ripple-origin-2 .ripple-ring:nth-child(5) { animation-delay: 10.3s; }

.aim-report-scope .ripple-origin-3 .ripple-ring { animation-duration: 9s; }
.aim-report-scope .ripple-origin-3 .ripple-ring:nth-child(1) { animation-delay: 0.8s; }
.aim-report-scope .ripple-origin-3 .ripple-ring:nth-child(2) { animation-delay: 2.6s; }
.aim-report-scope .ripple-origin-3 .ripple-ring:nth-child(3) { animation-delay: 4.4s; }
.aim-report-scope .ripple-origin-3 .ripple-ring:nth-child(4) { animation-delay: 6.2s; }
.aim-report-scope .ripple-origin-3 .ripple-ring:nth-child(5) { animation-delay: 8s; }

.aim-report-scope .ripple-origin-4 .ripple-ring { animation-duration: 12s; }
.aim-report-scope .ripple-origin-4 .ripple-ring:nth-child(1) { animation-delay: 0s; }
.aim-report-scope .ripple-origin-4 .ripple-ring:nth-child(2) { animation-delay: 2.4s; }
.aim-report-scope .ripple-origin-4 .ripple-ring:nth-child(3) { animation-delay: 4.8s; }
.aim-report-scope .ripple-origin-4 .ripple-ring:nth-child(4) { animation-delay: 7.2s; }
.aim-report-scope .ripple-origin-4 .ripple-ring:nth-child(5) { animation-delay: 9.6s; }

.aim-report-scope .ripple-origin-5 .ripple-ring { animation-duration: 10.5s; }
.aim-report-scope .ripple-origin-5 .ripple-ring:nth-child(1) { animation-delay: 2.2s; }
.aim-report-scope .ripple-origin-5 .ripple-ring:nth-child(2) { animation-delay: 4.3s; }
.aim-report-scope .ripple-origin-5 .ripple-ring:nth-child(3) { animation-delay: 6.4s; }
.aim-report-scope .ripple-origin-5 .ripple-ring:nth-child(4) { animation-delay: 8.5s; }
.aim-report-scope .ripple-origin-5 .ripple-ring:nth-child(5) { animation-delay: 10.6s; }

.aim-report-scope .ripple-origin-6 .ripple-ring { animation-duration: 8.5s; }
.aim-report-scope .ripple-origin-6 .ripple-ring:nth-child(1) { animation-delay: 4.5s; }
.aim-report-scope .ripple-origin-6 .ripple-ring:nth-child(2) { animation-delay: 6.2s; }
.aim-report-scope .ripple-origin-6 .ripple-ring:nth-child(3) { animation-delay: 7.9s; }
.aim-report-scope .ripple-origin-6 .ripple-ring:nth-child(4) { animation-delay: 9.6s; }
.aim-report-scope .ripple-origin-6 .ripple-ring:nth-child(5) { animation-delay: 11.3s; }

/* === NAV (плавающая навигация — НЕ конфликтует с WP header) === */
.aim-report-scope .report-nav {
  position: sticky; top: 0; z-index: 50;
  padding: 14px 32px;
  background: var(--glass-bg-rp);
  backdrop-filter: blur(20px) saturate(1.4);
  -webkit-backdrop-filter: blur(20px) saturate(1.4);
  border-bottom: 1px solid var(--border-rp);
  display: flex; align-items: center; justify-content: space-between;
  gap: 16px; flex-wrap: wrap;
}

.aim-report-scope .report-nav .logo-block {
  display: flex; align-items: center; gap: 12px;
}
.aim-report-scope .report-nav .logo {
  font-family: 'Playfair Display', serif;
  font-size: 20px; font-weight: 700; color: var(--text-rp);
}
.aim-report-scope .report-nav .tag {
  font-size: 11px; color: var(--text-dim-rp);
  letter-spacing: 1.5px; text-transform: uppercase;
}

.aim-report-scope .report-nav .nav-links {
  display: flex; gap: 4px; flex-wrap: wrap;
}
.aim-report-scope .report-nav .nav-links a {
  padding: 6px 12px; font-size: 12px; font-weight: 500;
  color: var(--text-sec-rp); text-decoration: none;
  border-radius: 16px; transition: all .2s;
}
.aim-report-scope .report-nav .nav-links a:hover {
  background: var(--surface-rp); color: var(--text-rp);
}

.aim-report-scope .theme-toggle-report {
  width: 36px; height: 36px; border-radius: 18px;
  background: var(--surface-rp);
  border: 1px solid var(--border-rp);
  cursor: pointer; display: flex; align-items: center; justify-content: center;
  font-size: 16px; transition: all .2s; flex-shrink: 0;
}
.aim-report-scope .theme-toggle-report:hover {
  background: var(--hover-rp); transform: scale(1.08);
}

/* === CONTAINER === */
.aim-report-scope .report-container {
  max-width: 920px; margin: 0 auto;
  padding: 64px 32px 48px;
  position: relative; z-index: 1;
}

/* === HERO === */
.aim-report-scope .hero {
  padding: 64px 0 56px;
  border-bottom: 1px solid var(--border-rp);
  margin-bottom: 72px;
  position: relative; overflow: hidden;
}

.aim-report-scope .hero .label {
  font-size: 11px; letter-spacing: 3px; text-transform: uppercase;
  color: var(--text-dim-rp); margin-bottom: 24px;
  font-family: 'Inter', sans-serif; font-weight: 600;
}

.aim-report-scope .hero h1 {
  font-family: 'Playfair Display', serif;
  font-size: clamp(34px, 5vw, 56px);
  font-weight: 400; line-height: 1.15;
  margin-bottom: 32px; position: relative; z-index: 1;
  color: var(--text-rp); letter-spacing: -.01em;
}
.aim-report-scope .hero h1 em {
  font-style: italic;
  font-size: 0.65em;
  display: block;
  margin-top: 12px;
  color: var(--text-sec-rp);
  font-weight: 400;
}

.aim-report-scope .hero .subtitle {
  font-size: 17px; color: var(--text-sec-rp);
  max-width: 640px; line-height: 1.75;
  position: relative; z-index: 1;
}

.aim-report-scope .hero .meta {
  display: flex; gap: 28px; margin-top: 40px;
  font-size: 13px; color: var(--text-dim-rp);
  flex-wrap: wrap; position: relative; z-index: 1;
  font-family: 'Inter', sans-serif;
}
.aim-report-scope .hero .meta span { white-space: nowrap; }
.aim-report-scope .hero .meta .rating {
  color: var(--accent-rp); font-weight: 600;
}

/* === SECTION LABEL === */
.aim-report-scope .section {
  margin-bottom: 96px; position: relative; z-index: 1;
}
.aim-report-scope .section:last-of-type { margin-bottom: 64px; }

.aim-report-scope .section-label {
  font-size: 11px; letter-spacing: 3px;
  text-transform: uppercase; color: var(--text-dim-rp);
  margin-bottom: 16px; font-family: 'Inter', sans-serif;
  font-weight: 600; display: flex; align-items: center; gap: 12px;
}
.aim-report-scope .section-label::before {
  content: ''; display: block;
  width: 28px; height: 1px; background: var(--accent-rp);
}

.aim-report-scope .section h2 {
  font-family: 'Playfair Display', serif;
  font-size: clamp(26px, 3.2vw, 36px);
  font-weight: 400; line-height: 1.2;
  margin-bottom: 16px; color: var(--text-rp);
}

/* === METRICS (большие цифры, как в ИПХиК) === */
.aim-report-scope .metrics {
  display: flex; gap: 48px; margin: 32px 0; flex-wrap: wrap;
}
.aim-report-scope .metric .value {
  font-family: 'Playfair Display', serif;
  font-size: 36px; font-weight: 400;
  color: var(--text-rp); line-height: 1.1;
}
.aim-report-scope .metric .label {
  font-size: 12px; color: var(--text-dim-rp);
  margin-top: 6px; letter-spacing: 0.5px;
  font-family: 'Inter', sans-serif;
}

/* === GRID === */
.aim-report-scope .grid-2 {
  display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
  gap: 16px; margin: 24px 0;
}
.aim-report-scope .grid-3 {
  display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
  gap: 16px; margin: 24px 0;
}

/* === CARD (простые карточки, как в ИПХиК) === */
.aim-report-scope .card {
  background: var(--surface-rp);
  border-radius: 16px; padding: 24px;
  transition: background .2s, transform .2s;
  border: 1px solid transparent;
}
.aim-report-scope .card:hover {
  background: var(--hover-rp);
}
.aim-report-scope .card h4 {
  font-size: 14px; font-weight: 600;
  margin-bottom: 8px; color: var(--text-rp);
  font-family: 'Inter', sans-serif;
}
.aim-report-scope .card .num {
  font-family: 'Playfair Display', serif;
  font-size: 28px; font-weight: 300;
  margin-bottom: 4px; color: var(--text-rp);
}
.aim-report-scope .card p {
  font-size: 13px; color: var(--text-sec-rp); margin: 0; line-height: 1.65;
}

/* === GLASS CARD (дизайн-система — анимированные) === */
.aim-report-scope .card-glass {
  background: var(--glass-bg-rp);
  backdrop-filter: blur(20px) saturate(1.4);
  -webkit-backdrop-filter: blur(20px) saturate(1.4);
  border: 1px solid var(--glass-border-rp);
  border-radius: 8px; padding: 32px;
  animation: aim-card-breathe 4s ease-in-out infinite, aim-glass-glow 5s ease-in-out infinite;
  margin: 20px 0;
}
.aim-report-scope .card-glass h3 {
  font-family: 'Playfair Display', serif;
  font-size: 20px; font-weight: 500; margin-bottom: 12px;
}
.aim-report-scope .card-glass p {
  font-size: 15px; color: var(--text-sec-rp); line-height: 1.75;
}

/* === GLASS STATS (сетка статистик) === */
.aim-report-scope .glass-stats-wrap {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
  gap: 16px; margin: 24px 0;
}
.aim-report-scope .glass-stat {
  background: var(--glass-bg-rp);
  backdrop-filter: blur(16px) saturate(1.3);
  -webkit-backdrop-filter: blur(16px) saturate(1.3);
  border: 1px solid var(--glass-border-rp);
  border-radius: 6px; padding: 28px 20px;
  text-align: center; transition: transform .3s, box-shadow .3s, border-color .3s;
  animation: aim-glass-glow 5s ease-in-out infinite;
  display: flex; flex-direction: column; align-items: center;
}
.aim-report-scope .glass-stat:hover {
  border-color: var(--accent-rp);
  transform: translateY(-4px);
  box-shadow: 0 8px 28px rgba(0,0,0,0.06);
}
.aim-report-scope .glass-stat-value {
  font-family: 'Playfair Display', serif;
  font-size: clamp(22px, 2.5vw, 38px);
  font-weight: 400; color: var(--accent-rp);
  line-height: 1.15; margin-bottom: 12px;
  word-break: break-word;
}
.aim-report-scope .glass-stat-label {
  font-family: 'Inter', sans-serif;
  font-size: 12px; font-weight: 500;
  color: var(--text-sec-rp); line-height: 1.4;
  text-align: center;
}

/* === GLASS TABLE === */
.aim-report-scope .glass-table-wrap, .aim-report-scope .table-wrap {
  overflow-x: auto;
  border: 1px solid var(--glass-border-rp);
  border-radius: 8px; margin: 24px 0;
  background: var(--glass-bg-rp);
  backdrop-filter: blur(16px) saturate(1.3);
  -webkit-backdrop-filter: blur(16px) saturate(1.3);
}
.aim-report-scope .glass-table-wrap table, .aim-report-scope .table-wrap table {
  width: 100%; border-collapse: collapse; font-size: 14px;
}
.aim-report-scope .glass-table-wrap th, .aim-report-scope .table-wrap th {
  padding: 14px 20px; text-align: left;
  font-family: 'Inter', sans-serif; font-weight: 600;
  font-size: 11px; letter-spacing: .06em;
  text-transform: uppercase; color: var(--text-sec-rp);
  border-bottom: 1px solid var(--border-rp);
}
.aim-report-scope .glass-table-wrap td, .aim-report-scope .table-wrap td {
  padding: 14px 20px; border-bottom: 1px solid var(--border-rp);
  color: var(--text-sec-rp);
}
.aim-report-scope .glass-table-wrap tr:last-child td, .aim-report-scope .table-wrap tr:last-child td {
  border-bottom: none;
}
.aim-report-scope .glass-table-wrap tr:hover td, .aim-report-scope .table-wrap tr:hover td {
  background: var(--hover-rp);
}
.aim-report-scope .highlight-row td {
  font-weight: 500; color: var(--text-rp); background: var(--surface-rp);
}

/* === SURFACE BLOCK (цитата/инсайт) === */
.aim-report-scope .surface-block {
  background: var(--surface-rp);
  border-left: 3px solid var(--accent-rp);
  padding: 20px 24px; margin: 16px 0;
  border-radius: 0 8px 8px 0;
}
.aim-report-scope .surface-block p {
  font-family: 'Inter', sans-serif;
  font-size: 14px; color: var(--text-rp);
  font-weight: 500; margin: 0;
}

/* === BLOCKQUOTE === */
.aim-report-scope blockquote {
  border-left: 2px solid var(--text-rp);
  padding-left: 24px; margin: 24px 0;
  font-size: 16px; line-height: 1.7;
  color: var(--text-sec-rp);
}
.aim-report-scope blockquote strong { color: var(--text-rp); }

/* === GAP (сильные стороны / точки роста) === */
.aim-report-scope .gap {
  background: var(--surface-rp);
  border-radius: 12px; padding: 20px;
  margin-bottom: 12px;
  border-left: 3px solid var(--border-rp);
}
.aim-report-scope .gap.gap-green { border-left-color: var(--green-rp); }
.aim-report-scope .gap.gap-red { border-left-color: var(--red-rp); }
.aim-report-scope .gap h4 {
  font-size: 14px; margin-bottom: 6px; color: var(--text-rp);
  font-family: 'Inter', sans-serif; font-weight: 600;
}
.aim-report-scope .gap p { font-size: 13px; margin: 0; }

/* === METRIC TAGS (цветные пилюли) === */
.aim-report-scope .metric-tag {
  display: inline-flex; align-items: center; gap: 6px;
  font-family: 'Inter', sans-serif;
  font-size: 11px; font-weight: 600;
  padding: 5px 12px; border-radius: 12px;
  letter-spacing: 0.3px; margin: 4px 6px 4px 0;
  max-width: 100%; word-break: break-word; line-height: 1.3;
}
.aim-report-scope .metric-tag-dot {
  width: 6px; height: 6px; border-radius: 50%; flex-shrink: 0;
}

.aim-report-scope .metric-tag-green { background: #E8F5E9; color: #2E7D32; }
.aim-report-scope .metric-tag-green .metric-tag-dot { background: #2E7D32; }
.aim-report-scope[data-theme="dark"] .metric-tag-green { background: #1B5E20; color: #81C784; }
.aim-report-scope[data-theme="dark"] .metric-tag-green .metric-tag-dot { background: #81C784; }

.aim-report-scope .metric-tag-yellow { background: #FFF9C4; color: #F57F17; }
.aim-report-scope .metric-tag-yellow .metric-tag-dot { background: #F57F17; }
.aim-report-scope[data-theme="dark"] .metric-tag-yellow { background: #F57F17; color: #FFF9C4; }
.aim-report-scope[data-theme="dark"] .metric-tag-yellow .metric-tag-dot { background: #FFF9C4; }

.aim-report-scope .metric-tag-red { background: #FFEBEE; color: #C62828; }
.aim-report-scope .metric-tag-red .metric-tag-dot { background: #C62828; }
.aim-report-scope[data-theme="dark"] .metric-tag-red { background: #C62828; color: #FFCDD2; }
.aim-report-scope[data-theme="dark"] .metric-tag-red .metric-tag-dot { background: #FFCDD2; }

.aim-report-scope .metric-tag-blue { background: #E3F2FD; color: #1565C0; }
.aim-report-scope .metric-tag-blue .metric-tag-dot { background: #1565C0; }
.aim-report-scope[data-theme="dark"] .metric-tag-blue { background: #1A237E; color: #90CAF9; }
.aim-report-scope[data-theme="dark"] .metric-tag-blue .metric-tag-dot { background: #90CAF9; }

.aim-report-scope .metric-tag-gray {
  background: var(--surface-rp); color: var(--text-sec-rp);
  border: 1px solid var(--border-rp);
}
.aim-report-scope .metric-tag-gray .metric-tag-dot { background: var(--text-sec-rp); }

/* === REVENUE vs COMPETITORS BLOCK (вау-блок) === */
.aim-report-scope .revenue-block {
  margin: 40px 0 60px;
  padding: 32px 28px;
  background: var(--surface-rp);
  border-radius: 16px;
  border-left: 4px solid var(--accent-rp);
  position: relative;
}
.aim-report-scope .revenue-block h2 {
  font-family: 'Playfair Display', serif;
  font-size: 28px; font-weight: 400;
  line-height: 1.2; margin-bottom: 8px;
}
.aim-report-scope .revenue-block .text-dim {
  font-size: 14px; color: var(--text-dim-rp); margin-bottom: 16px;
}
.aim-report-scope .wow-banner {
  background: linear-gradient(90deg, var(--accent-rp), transparent);
  color: var(--bg-rp);
  padding: 12px 20px; border-radius: 8px;
  margin: 16px 0; font-size: 16px; font-weight: 500;
}
.aim-report-scope[data-theme="dark"] .wow-banner {
  color: #0d0d0d;
  background: linear-gradient(90deg, var(--accent-rp), rgba(255,255,255,0.05));
}
.aim-report-scope .wow-banner strong { letter-spacing: 0.05em; }

.aim-report-scope .comp-table {
  width: 100%; border-collapse: collapse;
  margin: 20px 0; font-size: 14px;
}
.aim-report-scope .comp-table thead th {
  text-align: left; padding: 12px 14px;
  border-bottom: 2px solid var(--border-strong-rp);
  font-size: 11px; font-weight: 600;
  letter-spacing: 0.1em; text-transform: uppercase;
  color: var(--text-dim-rp);
}
.aim-report-scope .comp-table thead th:nth-child(3),
.aim-report-scope .comp-table thead th:nth-child(4) { text-align: center; }

.aim-report-scope .comp-row {
  border-bottom: 1px solid var(--border-rp);
  transition: background .2s;
}
.aim-report-scope .comp-row:hover { background: var(--hover-rp); }
.aim-report-scope .comp-row.row-client {
  background: var(--hover-rp); font-weight: 600;
}
.aim-report-scope .comp-row.row-client .comp-name,
.aim-report-scope .comp-row.row-client .comp-revenue {
  color: var(--accent-rp); font-weight: 700;
}
.aim-report-scope .comp-row td { padding: 14px; vertical-align: middle; }

.aim-report-scope .comp-rank {
  width: 40px; text-align: center;
  font-weight: 700; font-size: 16px; color: var(--text-dim-rp);
}
.aim-report-scope .comp-rank.rank-gold { color: var(--gold-rp); }
.aim-report-scope .comp-rank.rank-silver { color: var(--silver-rp); }
.aim-report-scope .comp-rank.rank-bronze { color: var(--bronze-rp); }

.aim-report-scope .comp-name { font-size: 15px; color: var(--text-rp); }
.aim-report-scope .comp-revenue {
  text-align: center; font-size: 18px;
  font-weight: 500; font-variant-numeric: tabular-nums; color: var(--text-rp);
}
.aim-report-scope .comp-trend { text-align: center; font-size: 18px; }
.aim-report-scope .comp-trend.trend-up { color: var(--green-rp); }
.aim-report-scope .comp-trend.trend-down { color: var(--red-rp); }
.aim-report-scope .comp-trend.trend-stable { color: var(--text-dim-rp); }
.aim-report-scope .comp-source {
  font-size: 11px !important; color: var(--text-dim-rp);
  margin-top: 12px !important; text-align: right;
}
.aim-report-scope .sec-tag-highlight {
  background: var(--accent-rp) !important;
  color: var(--bg-rp) !important; font-weight: 600;
}

/* === SEC-TAG === */
.aim-report-scope .sec-tag {
  display: inline-flex; align-items: center; gap: 12px;
  font-family: 'Inter', sans-serif;
  font-size: 11px; font-weight: 600;
  letter-spacing: .2em; text-transform: uppercase;
  color: var(--accent-rp); margin-bottom: 16px;
}
.aim-report-scope .sec-tag::before {
  content: ''; display: block;
  width: 32px; height: 1px; background: var(--accent-rp);
}

/* === INTERPRETATION === */
.aim-report-scope .interpretation p { margin: 12px 0; }
.aim-report-scope .interpretation h3 {
  margin: 24px 0 12px;
  border-bottom: 1px solid var(--border-rp);
  padding-bottom: 6px;
}
.aim-report-scope .interpretation ul, .aim-report-scope .interpretation ol {
  margin: 12px 0 16px 24px;
}
.aim-report-scope .interpretation li { margin: 6px 0; }
.aim-report-scope .interpretation hr {
  border: none; border-top: 1px solid var(--border-rp);
  margin: 32px 0;
}

/* === CTA BOX === */
.aim-report-scope .cta-box {
  border: 2px solid var(--text-rp);
  border-radius: 16px; padding: 48px 40px;
  text-align: center; margin: 48px 0 32px;
}
.aim-report-scope .cta-box h2 {
  font-family: 'Playfair Display', serif;
  font-size: clamp(24px, 2.5vw, 32px);
  font-weight: 400; margin-bottom: 16px;
}
.aim-report-scope .cta-box p {
  color: var(--text-sec-rp); max-width: 500px;
  margin: 0 auto 28px; font-size: 15px;
}
.aim-report-scope .btn-primary {
  display: inline-block; padding: 14px 40px;
  background: var(--accent-rp); color: var(--bg-rp);
  border: none; font-family: 'Inter', sans-serif;
  font-size: 13px; font-weight: 600;
  letter-spacing: .1em; text-transform: uppercase;
  border-radius: 28px; text-decoration: none;
  transition: all .3s; cursor: pointer;
}
.aim-report-scope .btn-primary:hover {
  background: var(--accent-hov-rp);
  transform: translateY(-2px);
  box-shadow: 0 8px 24px rgba(0,0,0,.15);
  text-decoration: none;
}

/* === FOOTER === */
.aim-report-scope .report-footer {
  margin-top: 64px; padding: 32px 0;
  border-top: 1px solid var(--border-rp);
  text-align: center; color: var(--text-dim-rp);
  font-size: 12px; line-height: 1.7;
}
.aim-report-scope .report-footer .footer-logo {
  font-family: 'Playfair Display', serif;
  font-size: 18px; font-weight: 700;
  color: var(--text-rp); margin-bottom: 8px;
}
.aim-report-scope .report-footer a {
  color: var(--accent-rp); text-decoration: none;
}
.aim-report-scope .report-footer a:hover { text-decoration: underline; }

/* === RESPONSIVE === */
@media (max-width: 768px) {
  .aim-report-scope .report-container { padding: 32px 20px 32px; }
  .aim-report-scope .report-nav { padding: 12px 20px; }
  .aim-report-scope .report-nav .nav-links { display: none; }
  .aim-report-scope .hero { padding: 40px 0 40px; margin-bottom: 48px; }
  .aim-report-scope .hero h1 { font-size: clamp(28px, 7vw, 36px); }
  .aim-report-scope .hero .meta { gap: 16px; font-size: 12px; }
  .aim-report-scope .metrics { gap: 24px; }
  .aim-report-scope .metric .value { font-size: 28px; }
  .aim-report-scope .glass-stats-wrap { grid-template-columns: 1fr 1fr; }
  .aim-report-scope .glass-stat { padding: 20px 14px; }
  .aim-report-scope .glass-stat-value { font-size: clamp(20px, 6vw, 28px); }
  .aim-report-scope .glass-stat-label { font-size: 11px; }
  .aim-report-scope .cta-box { padding: 32px 20px; }
  .aim-report-scope .section { margin-bottom: 64px; }
  .aim-report-scope .water-ripples { display: none; }
}

@media (max-width: 480px) {
  .aim-report-scope .glass-stats-wrap { grid-template-columns: 1fr; gap: 12px; }
  .aim-report-scope .grid-2, .aim-report-scope .grid-3 { grid-template-columns: 1fr; }
  .aim-report-scope .metric-tag { font-size: 10px; padding: 4px 10px; }
}

@media (prefers-reduced-motion: reduce) {
  .aim-report-scope .ripple-ring,
  .aim-report-scope .card-glass,
  .aim-report-scope .glass-stat,
  .aim-report-scope .glass-table-wrap { animation: none !important; }
}
</style>"""


def get_fonts_import() -> str:
    """Google Fonts <link> теги для шрифтов Inter + Playfair Display + Jost.

    Вставляется в <head> (или в начало post_content) до CSS.
    """
    return (
        '<link rel="preconnect" href="https://fonts.googleapis.com">'
        '<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>'
        '<link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=Playfair+Display:ital,wght@0,400;0,500;0,700;1,400&family=Jost:wght@300;400;500;600&display=swap" rel="stylesheet">'
    )
