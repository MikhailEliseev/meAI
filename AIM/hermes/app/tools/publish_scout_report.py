"""publish_scout_report — Hermes tool: Publish scout report as a beautiful WordPress page.

Reads scout data from /opt/data/competitors/{slug}/data.json, generates a
self-contained HTML report page, inserts it into WordPress via direct DB,
and returns the public URL.

Registered in Hermes internal registry under toolset "aim-operations".
"""

import json
import logging
import os
import random
import string
import time
from datetime import datetime, timezone

import pymysql

from tools.registry import registry

logger = logging.getLogger(__name__)

WP_DB_HOST = os.getenv("WP_DB_HOST", "wp-db")
WP_DB_USER = os.getenv("WP_DB_USER", "wp_user")
WP_DB_PASSWORD = os.getenv("WP_DB_PASSWORD", "")
WP_DB_NAME = os.getenv("WP_DB_NAME", "wordpress")

SCOUT_DATA_DIR = "/opt/data/competitors"




def _esc(text: str) -> str:
    """HTML-escape a string."""
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")


def _parse_num(val):
    """Try to parse a number from a string like '3.89%' or '5.0'."""
    if isinstance(val, (int, float)):
        return float(val)
    if isinstance(val, str):
        clean = val.replace("%", "").replace(",", ".").strip()
        try:
            return float(clean)
        except ValueError:
            return None
    return None


def _build_html(data: dict) -> str:
    """Generate an AIM design system HTML report page from scout data."""
    target = data.get("target", "Клиника")
    city = data.get("city", "")
    website = data.get("website", "")
    scan_date = data.get("scan_date", "")

    # Format date
    try:
        dt = datetime.fromisoformat(scan_date.replace("Z", "+00:00"))
        date_str = dt.strftime("%d.%m.%Y")
    except (ValueError, AttributeError):
        date_str = scan_date or "—"

    preflight = phases.get("0_preflight", {}) if (phases := data.get("phases", {})) else {}
    instagram = phases.get("0_5_instagram_profile", {}) or {}
    insta_content = phases.get("0_75_instagram_content", {}) or {}
    pagespeed = phases.get("1_pagespeed", {}) or {}
    key_persons = phases.get("3_5_key_persons", {}) or {}
    competitors = phases.get("4_competitor_matrix", {}) or {}
    ratings = phases.get("5_ratings_reviews", {}) or {}
    financial = phases.get("6_financial", {}) or {}
    gaps_adv = phases.get("7_gaps_advantages", {}) or {}
    entry_points = data.get("aim_entry_points", [])
    presale_angle = data.get("presale_angle", "")

    # ── Sections ────────────────────────────────────────────────────────

    # Hero
    hero = f"""<section id="hero">
      <div class="section-label">AIM Scout Report</div>
      <h1>{_esc(target)}</h1>
      <p class="text-dim">{_esc(city)} · {_esc(website)}</p>
      <p class="text-meta">Исследование завершено {date_str}</p>
    </section>
    <hr>"""

    # Executive Summary
    doctor_count = key_persons.get("doctors_count", "—")
    ig_followers = instagram.get("followers", "—")
    ig_er = insta_content.get("engagement_rate", insta_content.get("er_percent", "—"))
    cwv_status = (pagespeed.get("mobile", {}) or {}).get("cwv_status", "—")
    prodoctorov = ratings.get("prodoctorov", {}) or {}
    pd_reviews = prodoctorov.get("reviews_count", "—")

    summary = f"""<section id="summary">
      <div class="section-label">Ключевые метрики</div>
      <h2>Обзор {_esc(target)}</h2>
      <div class="metrics">
        <div class="metric"><div class="value">{_esc(str(doctor_count))}</div><div class="label">Врачей</div></div>
        <div class="metric"><div class="value">{_esc(str(ig_followers))}</div><div class="label">Instagram подписчиков</div></div>
        <div class="metric"><div class="value">{_esc(str(ig_er))}</div><div class="label">Engagement Rate</div></div>
        <div class="metric"><div class="value">{_esc(str(cwv_status))}</div><div class="label">Core Web Vitals</div></div>
        <div class="metric"><div class="value">{_esc(str(pd_reviews))}</div><div class="label">Отзывов</div></div>
      </div>
    </section>
    <hr>"""

    # Competitors
    comp_html = ""
    comp_list = competitors.get("competitors", [])
    if comp_list:
        comp_cards = ""
        for c in comp_list[:5]:
            comp_cards += f"""<div class="surface-card">
              <h3>{_esc(c.get('name', '—'))}</h3>
              <p class="text-meta">{_esc(c.get('segment', '—'))}</p>
              <div class="row"><div class="k">Врачей</div><div class="v">{_esc(str(c.get('doctors', '—')))}</div></div>
              <div class="row"><div class="k">Отзывов</div><div class="v">{_esc(str(c.get('reviews_prodoctorov', '—')))}</div></div>
              <div class="row"><div class="k">Цены</div><div class="v">{_esc(str(c.get('price_range', '—')))}</div></div>
            </div>"""
        comp_html = f"""<section id="competitors">
      <div class="section-label">Конкуренты</div>
      <h2>Конкурентный ландшафт</h2>
      <div class="grid-2">{comp_cards}</div>
    </section>
    <hr>"""

    # Gaps & Advantages
    gaps_html = ""
    gaps_list = gaps_adv.get("gaps_vs_competitors", [])
    adv_list = gaps_adv.get("advantages", [])
    if gaps_list or adv_list:
        gaps_section = ""
        if gaps_list:
            for g in gaps_list:
                sev = g.get("severity", "medium")
                sev_class = "gap-high" if sev == "high" else ("gap-medium" if sev == "medium" else "gap-low")
                gaps_section += f"""<div class="gap {sev_class}">
              <h4>{_esc(g.get('gap', ''))}</h4>
              <p class="text-dim">→ {_esc(g.get('fix', ''))}</p>
            </div>"""

        adv_section = ""
        if adv_list:
            for a in adv_list:
                rarity = a.get("rarity", "standard")
                tag_class = "tag-green" if rarity == "unique" else ("tag-accent" if rarity == "rare" else "")
                adv_section += f"""<div class="gap gap-advantage">
              <h4>{_esc(a.get('advantage', ''))} <span class="tag-badge {tag_class}">{rarity}</span></h4>
              <p class="text-dim">{_esc(a.get('monetization', ''))}</p>
            </div>"""

        gaps_html = f"""<section id="gaps">
      <div class="section-label">Разрывы и преимущества</div>
      <h2>Где сильны — где есть точки роста</h2>
      {f'<h3>Что теряете</h3>{gaps_section}' if gaps_section else ''}
      {f'<h3>Уникальные преимущества</h3>{adv_section}' if adv_section else ''}
    </section>
    <hr>"""

    # Key Persons
    persons_html = ""
    stars = key_persons.get("stars", [])
    core = key_persons.get("core", [])
    if stars or core:
        person_cards = ""
        for p in stars + core[:4]:
            initials = "".join(w[0] for w in p.get("full_name", "?").split()[:2]).upper()
            degree = p.get("degree", "")
            exp = p.get("experience_years", "")
            person_cards += f"""<div class="expert-card comp-expert">
            <h4>{_esc(p.get('full_name', '—'))}</h4>
            <p class="text-meta">{_esc(p.get('specialization', ''))}{' · ' + _esc(degree) if degree else ''}</p>
            <p class="text-accent-sm">{_esc(str(exp))} лет стажа</p>
          </div>"""
        persons_html = f"""<section id="experts">
      <div class="section-label">Ключевые врачи</div>
      <h2>Специалисты</h2>
      <div class="grid-2">{person_cards}</div>
    </section>
    <hr>"""

    # PageSpeed
    ps_html = ""
    if pagespeed:
        mobile = pagespeed.get("mobile", {}) or {}
        if mobile:
            ps_html = f"""<section id="pagespeed">
      <div class="section-label">Core Web Vitals</div>
      <h2>Скорость сайта</h2>
      <div class="table-wrap">
      <table>
        <tr><th>Метрика</th><th>Значение</th><th>Good</th><th>Needs Improvement</th><th>Poor</th></tr>
        <tr><td>LCP</td><td>{mobile.get('lcp_seconds', '—')}s</td><td>{mobile.get('lcp_distribution',{}).get('good','—')}%</td><td>{mobile.get('lcp_distribution',{}).get('needs_improvement','—')}%</td><td>{mobile.get('lcp_distribution',{}).get('poor','—')}%</td></tr>
        <tr><td>INP</td><td>{mobile.get('inp_ms', '—')}ms</td><td>{mobile.get('inp_distribution',{}).get('good','—')}%</td><td>{mobile.get('inp_distribution',{}).get('needs_improvement','—')}%</td><td>{mobile.get('inp_distribution',{}).get('poor','—')}%</td></tr>
        <tr><td>CLS</td><td>{mobile.get('cls', '—')}</td><td>{mobile.get('cls_distribution',{}).get('good','—')}%</td><td>{mobile.get('cls_distribution',{}).get('needs_improvement','—')}%</td><td>{mobile.get('cls_distribution',{}).get('poor','—')}%</td></tr>
      </table>
      </div>
    </section>
    <hr>"""

    # Financial
    fin_html = ""
    if financial:
        rev = financial.get("revenue_estimate", {}) or {}
        fin_html = f"""<section id="financials">
      <div class="section-label">Финансы</div>
      <h2>Финансовые показатели</h2>
      <div class="metrics">
        <div class="metric"><div class="value">{_esc(str(rev.get('monthly', '—')))}</div><div class="label">Выручка / мес</div></div>
        <div class="metric"><div class="value">{_esc(str(rev.get('annual', '—')))}</div><div class="label">Выручка / год</div></div>
      </div>
      <p class="text-meta">{_esc(str(rev.get('methodology', '')))}</p>
    </section>
    <hr>"""

    # AIM Entry Points
    eps_html = ""
    if entry_points:
        ep_cards = ""
        for ep in entry_points:
            roi = ep.get("roi_potential", "medium")
            roi_class = "tag-green" if roi == "high" else ("" if roi == "medium" else "")
            ep_cards += f"""<div class="surface-card">
            <span class="tag-badge tag-accent">#{ep.get('priority', '—')}</span>
            <h3>{_esc(ep.get('name', ''))}</h3>
            <p class="text-dim">{_esc(ep.get('description', ''))}</p>
            <span class="tag-badge">{_esc(str(ep.get('estimated_monthly_budget', '')))}</span>
            <span class="tag-badge {roi_class}">{roi}</span>
          </div>"""
        eps_html = f"""<section id="entry-points">
      <div class="section-label">Точки входа AIM</div>
      <h2>С чего начать</h2>
      <div class="grid-2">{ep_cards}</div>
    </section>
    <hr>"""

    # Presale Angle
    angle_html = ""
    if presale_angle:
        angle_html = f"""<section id="angle">
      <div class="section-label">УТП для пресейла</div>
      <h2>Уникальное торговое предложение</h2>
      <blockquote>{_esc(presale_angle)}</blockquote>
    </section>
    <hr>"""

    # CTA
    cta = """<section id="cta">
      <div class="cta-box">
        <h3>Готовы действовать?</h3>
        <p>Команда AIM реализует эти рекомендации под ключ.</p>
        <a href="https://t.me/aim_hermes_bot" class="btn" target="_blank" rel="noopener noreferrer">Связаться в Telegram</a>
      </div>
    </section>"""

    # Footer
    footer = f"""<section class="section-footer">
      <p class="text-meta">
        <a href="https://iamaim.ru" class="text-accent-link">iamaim.ru</a> · AI-first маркетинг в медицине<br>
        Этот отчёт сгенерирован автоматически
      </p>
    </section>"""

    # ── Assemble with data-aim="report" wrapper (CSS lives in theme.css) ──
    return f'<div data-aim="report">\n{hero}{summary}{comp_html}{gaps_html}{persons_html}{ps_html}{fin_html}{eps_html}{angle_html}{cta}{footer}\n</div>'


def _random_slug(length: int = 8) -> str:
    """Generate a random URL-safe slug."""
    chars = string.ascii_lowercase + string.digits
    return "".join(random.choices(chars, k=length))


async def handle_publish_scout_report(slug=None, **kwargs) -> str:
    """Publish a scout report as a beautiful WordPress page.

    Args:
        slug: Scout data slug (e.g. 'nachalo-clinica'). Reads from /opt/data/competitors/{slug}/data.json
    """
    if isinstance(slug, dict):
        d = slug
        slug = d.get("slug", "")

    if not slug:
        return json.dumps({"error": "slug is required — the scout data identifier"})

    # 1. Read scout data
    data_path = os.path.join(SCOUT_DATA_DIR, slug, "data.json")
    if not os.path.exists(data_path):
        return json.dumps({
            "error": f"Scout data not found for slug '{slug}'",
            "detail": f"Expected at {data_path}",
            "available_slugs": _list_available_slugs(),
        })

    try:
        with open(data_path, "r") as f:
            data = json.load(f)
    except (json.JSONDecodeError, OSError) as e:
        return json.dumps({"error": f"Failed to read data.json: {str(e)}"})

    # 2. Generate HTML
    target = data.get("target", slug)
    html = _build_html(data)

    # 3. Generate random slug and insert into WordPress
    page_slug = _random_slug()
    title = f"AIM Scout — {target}"

    if not WP_DB_PASSWORD:
        return json.dumps({
            "error": "WP_DB_PASSWORD not configured in Hermes environment",
            "detail": "Cannot connect to WordPress database without credentials.",
        })

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
            # Ensure slug uniqueness
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
        logger.info("Scout report published: slug=%s post_id=%s url=%s", slug, post_id, url)

        return json.dumps({
            "status": "published",
            "url": url,
            "slug": page_slug,
            "post_id": post_id,
            "title": title,
        }, ensure_ascii=False)

    except pymysql.Error as e:
        logger.error("MySQL error: %s", e)
        return json.dumps({"error": f"Database error: {str(e)}"})
    except Exception as e:
        logger.error("Unexpected error: %s", e)
        return json.dumps({"error": f"Failed to publish page: {str(e)}"})
    finally:
        if conn:
            conn.close()


def _list_available_slugs() -> list:
    """List available scout data directories."""
    try:
        if os.path.isdir(SCOUT_DATA_DIR):
            return [d for d in os.listdir(SCOUT_DATA_DIR)
                    if os.path.isdir(os.path.join(SCOUT_DATA_DIR, d))
                    and os.path.exists(os.path.join(SCOUT_DATA_DIR, d, "data.json"))]
    except OSError:
        pass
    return []


registry.register(
    name="publish_scout_report",
    toolset="aim-operations",
    schema={
        "type": "function",
        "function": {
            "name": "publish_scout_report",
            "description": "Публикует готовый scout-отчёт как красивую страницу на iamaim.ru. "
                           "Читает данные сканирования из /opt/data/competitors/{slug}/data.json, "
                           "генерирует HTML-страницу с классами дизайн-системы AIM и вставляет в WordPress. "
                           "Возвращает публичный URL вида https://iamaim.ru/{random-slug}. "
                           "Вызывай после завершения всех фаз сканирования.",
            "parameters": {
                "type": "object",
                "properties": {
                    "slug": {
                        "type": "string",
                        "description": "[REQUIRED] Идентификатор сканирования (например 'nachalo-clinica')",
                    },
                },
                "required": ["slug"],
            },
        },
    },
    handler=handle_publish_scout_report,
    check_fn=lambda: bool(WP_DB_PASSWORD),
    is_async=True,
    description="Publish scout report as a beautiful WordPress page on iamaim.ru",
    emoji="📄",
)
