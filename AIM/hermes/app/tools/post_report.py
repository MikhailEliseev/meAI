"""post_report — Publish scout report as WordPress page with iframe-isolated design.

Architecture: saves standalone HTML to hermes data volume (served via nginx /reports/),
then creates a WordPress page with <iframe src="..."> pointing to the HTML file.
The iframe isolates the CSS from the WordPress theme — no conflicts.
"""
import json, logging, os, random, re, string
from datetime import datetime, timezone
import pymysql
from tools.registry import registry

logger = logging.getLogger(__name__)

def _env_with_fallback(key: str, default: str = "") -> str:
    val = os.getenv(key, "")
    if val: return val
    for env_path in ("/opt/hermes/.env", "/opt/data/.env",
                      "/opt/aim/AIM/.env.production", "/opt/aim/AIM/.env"):
        try:
            with open(env_path) as f:
                for line in f:
                    line = line.strip()
                    if line.startswith(f"{key}=") or line.startswith(f"{key} ="):
                        found = line.split("=", 1)[1].strip().strip('"').strip("'")
                        if found: return found
        except (OSError, IOError): continue
    if key == "WP_DB_PASSWORD":
        wp_val = os.getenv("WORDPRESS_DB_PASSWORD", "")
        if wp_val: return wp_val
    return default

WP_DB_HOST = _env_with_fallback("WP_DB_HOST", "mysql")
WP_DB_USER = _env_with_fallback("WP_DB_USER", "wp_user")
WP_DB_PASSWORD = _env_with_fallback("WP_DB_PASSWORD", "")
WP_DB_NAME = _env_with_fallback("WP_DB_NAME", "wordpress")

def _esc(text: str) -> str:
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")

def _random_slug(length: int = 8) -> str:
    return "".join(random.choices(string.ascii_lowercase + string.digits, k=length))

# ═══════════════════════════════════════════════════════════════════════
# AIM Design System CSS — standalone, no WordPress dependency
# ═══════════════════════════════════════════════════════════════════════
CSS = """@import url('https://fonts.googleapis.com/css2?family=Inter:opsz@14..32&family=Playfair+Display:ital,wght@0,400;0,700;1,400&display=swap');

*, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

:root {
  --bg: #ffffff; --surface: #F5F5F5; --hover: #EBEBEB; --border: #E0E0E0;
  --text: #1A1A1A; --text-secondary: #666666; --text-dim: #999999;
  --accent: #1A1A1A; --accent-hover: #333333;
  --glass-bg: rgba(255,255,255,0.6); --glass-border: rgba(0,0,0,0.06);
  --section-gap: 120px; --green: #2E7D32; --red: #C62828;
}
[data-theme="dark"] {
  --bg: #0D0D0D; --surface: #1A1A1A; --hover: #262626; --border: #333333;
  --text: #F0F0F0; --text-secondary: #999999; --text-dim: #666666;
  --accent: #F0F0F0; --accent-hover: #CCCCCC;
  --glass-bg: rgba(13,13,13,0.6); --glass-border: rgba(255,255,255,0.06);
  --green: #66BB6A; --red: #EF5350;
}

html { scroll-behavior: smooth; }
body {
  font-family: 'Inter', -apple-system, sans-serif; background: var(--bg);
  color: var(--text); line-height: 1.6; -webkit-font-smoothing: antialiased;
  transition: background .3s, color .3s;
}

.container { max-width: 900px; margin: 0 auto; padding: 0 32px; position: relative; z-index: 1; }

.hero {
  padding: 80px 0 80px; border-bottom: 1px solid var(--border);
  margin-bottom: var(--section-gap); position: relative; overflow: hidden;
}
.hero .label { font-size: 12px; letter-spacing: 3px; text-transform: uppercase; color: var(--text-dim); margin-bottom: 24px; }
.hero h1 { font-family: 'Playfair Display', serif; font-size: 56px; font-weight: 400; line-height: 1.15; margin-bottom: 32px; position: relative; z-index: 1; }
.hero h1 em { font-style: italic; }
.hero .subtitle { font-size: 18px; color: var(--text-secondary); max-width: 600px; line-height: 1.7; position: relative; z-index: 1; }
.hero .meta { display: flex; gap: 32px; margin-top: 48px; font-size: 13px; color: var(--text-dim); flex-wrap: wrap; position: relative; z-index: 1; }

.ripple { position: fixed; inset: 0; pointer-events: none; z-index: 0; overflow: hidden; }
.ripple-ring { position: absolute; border-radius: 50%; border: 1px solid var(--text); opacity: 0.04; background: none; }
.ring-lg-1 { width: 420px; height: 420px; top: -12%; right: -8%; }
.ring-lg-2 { width: 340px; height: 340px; top: 15%; right: 70%; }
.ring-lg-3 { width: 280px; height: 280px; top: 45%; left: -10%; }
.ring-lg-4 { width: 380px; height: 380px; top: 75%; right: -15%; }
.ring-lg-5 { width: 300px; height: 300px; top: 60%; left: 60%; }
.ring-lg-6 { width: 240px; height: 240px; top: 30%; left: -6%; }
.ring-pulse-1 { width: 200px; height: 200px; top: 10%; left: 8%; animation: pulse-ring 6s ease-in-out infinite; }
.ring-pulse-2 { width: 160px; height: 160px; top: 12%; left: 12%; animation: pulse-ring 6s ease-in-out infinite; animation-delay: 3s; }
.ring-pulse-3 { width: 100px; height: 100px; bottom: 18%; right: 4%; animation: pulse-ring 8s ease-in-out infinite; animation-delay: 1s; }
.ring-pulse-4 { width: 70px; height: 70px; bottom: 22%; right: 10%; animation: pulse-ring 8s ease-in-out infinite; animation-delay: 5s; }
.ring-pulse-5 { width: 130px; height: 130px; top: 35%; right: 20%; animation: pulse-ring 7s ease-in-out infinite; animation-delay: 2s; }
.ring-pulse-6 { width: 90px; height: 90px; top: 70%; left: 30%; animation: pulse-ring 9s ease-in-out infinite; animation-delay: 4s; }
.ring-pulse-7 { width: 110px; height: 110px; top: 88%; left: 50%; animation: pulse-ring 6.5s ease-in-out infinite; animation-delay: 1.5s; }
.ring-pulse-8 { width: 150px; height: 150px; top: 50%; right: 40%; animation: pulse-ring 7.5s ease-in-out infinite; animation-delay: 3.5s; }
@keyframes pulse-ring { 0%, 100% { opacity: 0.03; transform: scale(1); } 50% { opacity: 0.07; transform: scale(1.15); } }
@media (max-width: 768px) { .hero h1 { font-size: 32px; } .ripple { display: none; } }

section { margin-bottom: var(--section-gap); }
.section-label { font-size: 11px; letter-spacing: 3px; text-transform: uppercase; color: var(--text-dim); margin-bottom: 16px; }
h2 { font-family: 'Playfair Display', serif; font-size: 36px; font-weight: 400; line-height: 1.2; margin-bottom: 16px; }
h3 { font-family: 'Playfair Display', serif; font-size: 22px; font-weight: 400; margin: 48px 0 12px; }
h4 { font-size: 14px; font-weight: 600; margin-bottom: 6px; }
p { color: var(--text-secondary); margin-bottom: 16px; font-size: 15px; line-height: 1.7; }
p strong { color: var(--text); font-weight: 500; }

.grid-2 { display: grid; grid-template-columns: 1fr 1fr; gap: 16px; margin: 24px 0; }

.card { background: var(--surface); border-radius: 16px; padding: 24px; backdrop-filter: blur(8px); transition: .2s; border: 1px solid transparent; }
.card:hover { background: var(--hover); }
.card h4 { font-size: 14px; font-weight: 600; margin-bottom: 6px; color: var(--text); }
.card p { font-size: 13px; color: var(--text-secondary); margin: 0; }

.metrics { display: flex; gap: 48px; margin: 32px 0; flex-wrap: wrap; }
.metric .value { font-size: 36px; font-weight: 300; color: var(--text); }
.metric .label { font-size: 13px; color: var(--text-dim); margin-top: 4px; }

hr { border: none; border-top: 1px solid var(--border); margin: 48px 0; }

blockquote { border-left: 2px solid var(--text); padding-left: 24px; margin: 24px 0; font-size: 16px; line-height: 1.6; color: var(--text-secondary); }

.gap { background: var(--surface); border-radius: 12px; padding: 20px; margin-bottom: 12px; border-left: 3px solid var(--border); }
.gap h4 { font-size: 14px; margin-bottom: 6px; color: var(--text); }
.gap p { font-size: 13px; margin: 0; }

ul { margin: 0 0 16px 24px; }
li { color: var(--text-secondary); font-size: 15px; line-height: 1.7; margin-bottom: 6px; }
li strong { color: var(--text); }

.cta-box { border: 2px solid var(--text); border-radius: 16px; padding: 48px; text-align: center; margin: 48px 0; }
.cta-box h3 { margin-bottom: 16px; margin-top: 0; }
.cta-box p { margin-bottom: 24px; }
.cta-box .btn { display: inline-block; padding: 14px 40px; border: 1px solid var(--text); color: var(--text); text-decoration: none; font-size: 14px; border-radius: 28px; transition: .2s; letter-spacing: 1px; }
.cta-box .btn:hover { background: var(--text); color: var(--bg); }

@media (max-width: 768px) {
  .hero h1 { font-size: 32px; } h2 { font-size: 28px; }
  .grid-2 { grid-template-columns: 1fr; } .metrics { gap: 24px; }
  .hero { padding: 60px 0 60px; } .cta-box { padding: 32px 20px; }
}"""

RIPPLE = """<div class="ripple">
  <div class="ripple-ring ring-lg-1"></div><div class="ripple-ring ring-lg-2"></div>
  <div class="ripple-ring ring-lg-3"></div><div class="ripple-ring ring-lg-4"></div>
  <div class="ripple-ring ring-lg-5"></div><div class="ripple-ring ring-lg-6"></div>
  <div class="ripple-ring ring-pulse-1"></div><div class="ripple-ring ring-pulse-2"></div>
  <div class="ripple-ring ring-pulse-3"></div><div class="ripple-ring ring-pulse-4"></div>
  <div class="ripple-ring ring-pulse-5"></div><div class="ripple-ring ring-pulse-6"></div>
  <div class="ripple-ring ring-pulse-7"></div><div class="ripple-ring ring-pulse-8"></div>
</div>"""
# ═══════════════════════════════════════════════════════════════════════


async def handle_post_report(title: str = None, client_url: str = None, content: str = None, **kwargs) -> str:
    if isinstance(title, dict):
        d = title; title = d.get("title", ""); client_url = d.get("client_url", ""); content = d.get("content", "")
    if not content: return json.dumps({"error": "content is required"}, ensure_ascii=False)

    report_title = title or "AIM Scout Report"
    site_url = client_url or ""
    now = datetime.now(timezone.utc).strftime("%d.%m.%Y")
    hero_subtitle = "Полный разбор: сайт, конкуренты, репутация, рекомендации."
    body = _md_to_html(content)

    # Build standalone HTML page
    html = "<!DOCTYPE html>\n<html lang=\"ru\" data-theme=\"light\">\n<head>\n"
    html += "<meta charset=\"UTF-8\">\n<meta name=\"viewport\" content=\"width=device-width, initial-scale=1.0\">\n"
    html += f"<title>{_esc(report_title)} – AIM</title>\n<style>\n{CSS}\n</style>\n</head>\n<body>\n"
    html += RIPPLE + "\n<div class=\"container\">\n"
    html += "<div class=\"hero\">\n<div class=\"label\">AI ANALYSIS</div>\n"
    html += f"<h1>{_esc(report_title)}</h1>\n"
    html += f"<div class=\"subtitle\">{hero_subtitle}</div>\n"
    html += f"<div class=\"meta\"><span>{_esc(site_url)}</span><span>{now}</span></div>\n"
    html += "</div>\n"
    html += body + "\n"
    html += "<div class=\"cta-box\">\n<h3>Готовы действовать?</h3>\n"
    html += "<p>Команда AIM реализует эти рекомендации под ключ — от аудита до первой записи.</p>\n"
    html += "<a href=\"https://t.me/aim_hermes_bot\" class=\"btn\">Связаться в Telegram</a>\n</div>\n"
    html += "</div>\n</body>\n</html>"

    # Save to hermes data volume → served via nginx /reports/
    file_slug = _random_slug()
    filename = f"report-{file_slug}.html"
    reports_dir = "/opt/data/reports-publish"
    os.makedirs(reports_dir, exist_ok=True)
    filepath = os.path.join(reports_dir, filename)
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(html)
    report_url = f"https://iamaim.ru/reports/{filename}"

    # Create WordPress page with iframe (wpautop-safe: no srcdoc, just src=URL)
    page_html = (
        f'<div style="width:100%;max-width:100%;overflow:auto;">'
        f'<iframe src="{report_url}" style="width:100%;height:100vh;border:none;display:block;" '
        f'sandbox="allow-scripts allow-same-origin" loading="lazy" title="{_esc(report_title)}">'
        f'</iframe></div>'
    )

    if not WP_DB_PASSWORD:
        return json.dumps({"status": "no_db", "error": "WP_DB_PASSWORD not configured"}, ensure_ascii=False)

    page_slug = _random_slug()
    wp_title = f"AIM Scout — {report_title}"
    conn = None
    try:
        conn = pymysql.connect(host=WP_DB_HOST, user=WP_DB_USER, password=WP_DB_PASSWORD,
                               database=WP_DB_NAME, charset="utf8mb4", connect_timeout=5)
        now_ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
        with conn.cursor() as cur:
            cur.execute("SELECT ID FROM wp_posts WHERE post_name = %s LIMIT 1", (page_slug,))
            for _ in range(10):
                if not cur.fetchone(): break
                page_slug = _random_slug()
                cur.execute("SELECT ID FROM wp_posts WHERE post_name = %s LIMIT 1", (page_slug,))
            cur.execute("""INSERT INTO wp_posts (post_author,post_date,post_date_gmt,post_content,post_title,
                post_status,comment_status,ping_status,post_name,post_type,post_excerpt,to_ping,pinged,
                post_content_filtered,menu_order) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)""",
                (1, now_ts, now_ts, page_html, wp_title, "publish", "closed", "closed", page_slug, "page", "", "", "", "", 0))
            post_id = cur.lastrowid
        conn.commit()
        url = f"https://iamaim.ru/{page_slug}"
        logger.info("post_report: post_id=%s file=%s page=%s", post_id, report_url, url)
        return json.dumps({"status": "published", "url": url, "slug": page_slug, "post_id": post_id}, ensure_ascii=False)
    except pymysql.Error as e:
        logger.error("post_report MySQL: %s", e)
        return json.dumps({"error": f"Database error: {str(e)}"}, ensure_ascii=False)
    except Exception as e:
        logger.exception("post_report failed")
        return json.dumps({"error": str(e)}, ensure_ascii=False)
    finally:
        if conn: conn.close()


def _md_to_html(md: str) -> str:
    lines = md.split("\n")
    sections = []; label = None; heading = None; body = []

    for line in lines:
        s = line.strip()
        if s.startswith("## "):
            if heading or body: sections.append((label, heading, body))
            raw = s[3:].strip()
            for sep in (" — ", " - "):
                if sep in raw:
                    parts = raw.split(sep, 1)
                    if all(c in "0123456789." for c in parts[0].strip()):
                        label, heading = parts[0].strip(), parts[1].strip(); break
            else: label, heading = None, raw
            body = []
        elif s == "---":
            if heading or body: sections.append((label, heading, body))
            label = heading = None; body = []
        else:
            body.append(line)
    if heading or body: sections.append((label, heading, body))
    if not any(h for _, h, _ in sections): sections = [(None, None, [l for l in lines if l.strip()])]

    result = []
    for lab, hdr, body_lines in sections:
        inner = _render_body(body_lines)
        if not inner.strip(): continue
        result.append('<section>')
        if hdr:
            display = f"{lab} - {hdr}" if lab else hdr
            result.append(f'<div class="section-label">{_esc(display)}</div>')
        result.append(inner)
        result.append('</section>\n<hr>')
    return "\n".join(result)


def _render_body(lines: list) -> str:
    out = []; in_list = in_table = in_metrics = False

    def close():
        nonlocal in_list, in_table, in_metrics
        if in_list: out.append("</ul>"); in_list = False
        if in_table: out.append("</tbody></table></div>"); in_table = False
        if in_metrics: out.append("</div>"); in_metrics = False

    for line in lines:
        s = line.strip()
        if not s: close(); continue
        if s.startswith("### "): close(); out.append(f'<h3>{_esc(s[4:])}</h3>'); continue
        if s in ("---", "***"): close(); continue

        # Metrics: **number** — label
        if s.startswith("**") and not s.startswith("|"):
            m = re.match(r"\*\*(.+?)\*\*\s*[—\-]\s*(.+)", s)
            if m and re.search(r"[\d₽%×\+]", m.group(1)):
                v, l = m.group(1), m.group(2)
                if not in_metrics: out.append('<div class="metrics">'); in_metrics = True
                out.append(f'<div class="metric"><div class="value">{_esc(v)}</div><div class="label">{_esc(l)}</div></div>')
                continue

        # Table
        if s.startswith("|") and s.endswith("|"):
            cells = [c.strip() for c in s[1:-1].split("|")]
            if all(re.match(r"^:?-{2,}:?$", c) for c in cells): continue
            if not in_table:
                close()
                out.append('<div style="overflow-x: auto; margin: 24px 0;"><table style="width:100%; border-collapse: collapse; font-size: 14px; min-width: 640px;"><thead><tr style="background: var(--surface);">')
                for i, c in enumerate(cells):
                    bg = 'background: var(--hover); font-weight: 700;' if i == 1 else ''
                    align = 'text-align: center;' if i > 0 else 'text-align: left;'
                    out.append(f'<th style="padding: 12px; {align} border-bottom: 1px solid var(--border); {bg}">{_esc(c.replace("*", ""))}</th>')
                out.append('</tr></thead><tbody>')
                in_table = True
            else:
                clean = [c.replace("*", "") for c in cells]; is_client = any("**" in c for c in cells)
                bg = 'background: var(--hover);' if is_client else ('background: var(--surface);' if len(out) % 4 == 0 else '')
                out.append(f'<tr style="{bg}">')
                for i, c in enumerate(clean):
                    align = 'text-align: center;' if i > 0 else ''
                    fw = 'font-weight: 700;' if (is_client and i == 0) else 'font-weight: 500;' if i == 0 else ''
                    out.append(f'<td style="padding: 12px; border-bottom: 1px solid var(--border); {align} {fw}">{_inline(c)}</td>')
                out.append('</tr>')
            continue
        elif in_table: close()

        # Gap blocks
        if s.startswith("> ") and any(e in s for e in ("✅", "📍", "🔥", "⚠️")):
            close()
            text = s[2:]
            color = "var(--green)" if "✅" in text else ("var(--red)" if "⚠️" in text else "var(--border)")
            out.append(f'<div class="gap" style="border-left: 3px solid {color};"><h4>{_inline(text)}</h4></div>')
            continue

        # Blockquote
        if s.startswith("> "): close(); out.append(f"<blockquote>{_inline(s[2:])}</blockquote>"); continue

        # List
        if s.startswith("- ") or s.startswith("* "):
            if not in_list: close(); out.append("<ul>"); in_list = True
            out.append(f"<li>{_inline(s[2:])}</li>"); continue

        # Paragraph
        close(); out.append(f"<p>{_inline(s)}</p>")

    close()
    return "\n".join(out)


def _inline(text: str) -> str:
    text = _esc(text)
    return re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", text)


registry.register(
    name="post_report", toolset="aim-operations",
    schema={"type": "function", "function": {
        "name": "post_report",
        "description": "Публикует отчёт разведки на iamaim.ru как WordPress-страницу с iframe-изолированным дизайном.",
        "parameters": {"type": "object", "properties": {
            "title": {"type": "string", "description": "Заголовок отчёта"},
            "client_url": {"type": "string", "description": "URL сайта клиента"},
            "content": {"type": "string", "description": "Полный отчёт в markdown"}},
            "required": ["title", "content"]}}},
    handler=handle_post_report, check_fn=lambda: True, is_async=True,
    description="Publish scout report as WordPress page with iframe-isolated AIM design system")
