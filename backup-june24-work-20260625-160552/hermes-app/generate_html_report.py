"""generate_html_report — Hermes tool: Generate AIM design system HTML report.

Reads all available data from /opt/data/sessions-archive/{session_hash}/,
generates a self-contained HTML report page using AIM theme CSS classes,
and publishes it to WordPress via direct DB insert.

Called by:
  - run_full_scout.py (end of full scout pipeline)
  - finalize_research.py (when publish_html_report=True)

Phase 3 / D-07 (Plan 03-05): honest reporting when Instagram data is
unavailable for an Instagram-critical niche (plastic_surgery, cosmetology).
The new ``_build_no_instagram_block(reason)`` helper renders a transparent
"Instagram: данные недоступны — {reason}" block in sections 03 (Experts)
and 04 (Content Analysis) when:
  - ``niche`` is one of ``CRITICAL_NICHES`` (plastic_surgery / cosmetology)
  - AND ``instagram_data`` is None / empty / has ``analyzed_count == 0``
The block supports 4 reason variants per D-07 — "no_account" (Instagram
not attempted), "handle_not_found" (handle missing on site),
"private_profile" (profile is private), "perplexity_outside_index"
(handles tried, all returned no data). Non-critical niches do NOT
render the block — section appears without Instagram content, no warning.

``_build_report_html`` accepts ``niche`` and ``instagram_data`` as optional
kwargs (preserves Phase 2 backward compat). ``handle_generate_html_report``
extracts them from kwargs with safe defaults. Pass 3 prompt (Plan 03-05
Task 3) explicitly instructs the LLM to pass both kwargs.
"""

import json
import logging
import os
import random
import re
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


# ── Phase 4 / DAT-01 + DAT-04: Revenue dynamics + Clinic metrics ────────


def _build_revenue_dynamics_section(
    financials: dict,
    insight: str | None = None,
) -> str:
    """Build the 3-year revenue dynamics section (DAT-01, D-13..14).

    Reads ``financials.revenue_dynamics`` from the session archive. When
    ``dynamics_available=True``, renders a 3-year table (year, revenue,
    YoY %) + blockquote with the summary text per D-14. When False (D-13
    strict rule), renders an honest "Динамика выручки недоступна" block
    with the reason — NO partial-data table.

    Args:
        financials: ``data["financials"]`` dict (find_company_financials
            output). Reads the ``revenue_dynamics`` subkey.
        insight: Phase 5 / INT-05 — main strategic insight for this
            section (1-2 sentence business-language narrative from Pass 3
            LLM). When provided, rendered as ``<blockquote class=
            "section-insight">`` before the closing ``</section>``.

    Returns:
        HTML ``<section>`` block for the report. Always returns a section
        (even when data is missing — honest reporting per ORC-04).
    """
    if not isinstance(financials, dict):
        financials = {}
    revenue_dynamics = financials.get("revenue_dynamics", {}) or {}

    # D-13 strict <3-year rule: when dynamics_available is False (or
    # missing), render honest block — do NOT extrapolate or show partial.
    if not revenue_dynamics or not revenue_dynamics.get("dynamics_available"):
        reason = (
            revenue_dynamics.get("reason")
            if isinstance(revenue_dynamics, dict)
            else None
        ) or "недостаточно данных в открытых источниках"
        return f"""<section class="section" data-aim="revenue-dynamics">
  <span class="section-label">Динамика выручки</span>
  <h2>Динамика выручки за 3 года</h2>
  <div class="glass-card" style="padding: 1.5rem; border-radius: 8px; background: var(--glass-bg, rgba(255,255,255,0.5)); border: 1px solid var(--border, #E0E0E0);">
    <p class="text-dim">Динамика выручки недоступна — {_esc(reason)}.</p>
    <p class="text-meta"><em>По правилу D-13 — не показываем частичные данные.</em></p>
  </div>
</section>
<hr>"""

    years = revenue_dynamics.get("years", []) or []
    summary_text = revenue_dynamics.get("summary_text", "") or ""
    total_growth_pct = revenue_dynamics.get("total_growth_pct")

    # Build table rows from years list (expected: descending order)
    rows_html = ""
    for y in years:
        if not isinstance(y, dict):
            continue
        year = _esc(str(y.get("year", "—")))
        revenue_val = y.get("revenue")
        revenue_str = _fmt_revenue_short(revenue_val)
        yoy_pct = y.get("yoy_pct")
        if yoy_pct is None:
            yoy_cell = '<span class="text-dim">—</span>'
        else:
            try:
                pct_num = float(yoy_pct)
                if pct_num > 0:
                    yoy_cell = (
                        f'<span style="color: #2e7d32; font-weight: 500;">'
                        f'+{pct_num:.1f}%</span>'
                    )
                elif pct_num < 0:
                    yoy_cell = (
                        f'<span style="color: #c62828; font-weight: 500;">'
                        f'{pct_num:.1f}%</span>'
                    )
                else:
                    yoy_cell = f'<span class="text-dim">{pct_num:.1f}%</span>'
            except (TypeError, ValueError):
                yoy_cell = f'<span class="text-dim">{_esc(str(yoy_pct))}</span>'
        rows_html += f"""<tr>
  <td>{year}</td>
  <td>{_esc(revenue_str)}</td>
  <td>{yoy_cell}</td>
</tr>\n"""

    # Blockquote summary (D-14) — includes total growth %
    blockquote_html = ""
    if summary_text:
        blockquote_html = f"""<blockquote style="margin: 1rem 0 0 0; padding: 0.75rem 1.25rem; border-left: 3px solid var(--accent, #c9a96e); background: var(--glass-bg, rgba(255,255,255,0.3));">
  <p>{_esc(summary_text)}</p>
</blockquote>"""

    return f"""<section class="section" data-aim="revenue-dynamics">
  <span class="section-label">Динамика выручки (DAT-01)</span>
  <h2>Динамика выручки за 3 года</h2>
  <div class="glass-card" style="padding: 1.5rem; border-radius: 8px; background: var(--glass-bg, rgba(255,255,255,0.5)); border: 1px solid var(--border, #E0E0E0);">
    <table class="comp-table">
      <thead>
        <tr>
          <th>Год</th>
          <th>Выручка</th>
          <th>Прирост YoY</th>
        </tr>
      </thead>
      <tbody>
{rows_html}      </tbody>
    </table>
{blockquote_html}
  </div>
  {_render_section_insight(insight)}
</section>
<hr>"""


def _build_clinic_metrics_block(
    financials: dict,
    insight: str | None = None,
) -> str:
    """Build the clinic metrics block for the About section (DAT-04, D-21).

    Reads ``financials.clinic_metrics`` from the session archive. Renders
    a grid of metric tags (revenue, profit, employees, status, ОКВЭД).
    The ОКВЭД field is humanized by the Pass 3 LLM via
    ``okved_humanized`` (D-21); if absent, falls back to the raw code.

    Args:
        financials: ``data["financials"]`` dict. Reads ``clinic_metrics``
            subkey.
        insight: Phase 5 / INT-05 — main strategic insight for the About
            section (key 0 of the QC checklist). When provided, rendered
            as ``<blockquote class="section-insight">`` at the end of the
            clinic-metrics fragment (NO section wrapper — this block is
            always embedded inside the About/Executive Summary section).

    Returns:
        HTML block (NO ``<section>`` wrapper — this goes INSIDE the
        About/Executive Summary section). Empty string when
        clinic_metrics is missing (About section still shows other data).
    """
    if not isinstance(financials, dict):
        return ""
    clinic_metrics = financials.get("clinic_metrics", {}) or {}
    if not clinic_metrics:
        return ""

    # Build metric items — only render items with data
    items_html = ""

    # Revenue
    revenue_val = clinic_metrics.get("revenue_latest")
    if revenue_val is not None:
        items_html += f"""<div class="metric"><div class="value">{_esc(_fmt_revenue_short(revenue_val))}</div><div class="label">Выручка</div></div>\n"""

    # Profit
    profit_val = clinic_metrics.get("profit_latest")
    if profit_val is not None:
        items_html += f"""<div class="metric"><div class="value">{_esc(_fmt_revenue_short(profit_val))}</div><div class="label">Прибыль</div></div>\n"""

    # Employees
    employees = clinic_metrics.get("employees")
    if employees is not None:
        items_html += f"""<div class="metric"><div class="value">{_esc(_fmt_num(employees))}</div><div class="label">Сотрудников</div></div>\n"""

    # Status (Действующее / Ликвидировано)
    status = clinic_metrics.get("status")
    if status:
        status_class = "metric-tag-success" if "действу" in str(status).lower() else "metric-tag-warning"
        items_html += f"""<div class="metric"><div class="value"><span class="metric-tag {status_class}">{_esc(str(status))}</span></div><div class="label">Статус</div></div>\n"""

    # ОКВЭД (D-21: LLM-humanized via okved_humanized; fallback to raw code)
    okved_humanized = clinic_metrics.get("okved_humanized")
    okved_codes = clinic_metrics.get("okved_codes", []) or []
    if okved_humanized:
        okved_display = _esc(str(okved_humanized))
    elif okved_codes and isinstance(okved_codes[0], dict):
        first_code = okved_codes[0].get("code", "—")
        first_desc = okved_codes[0].get("description", "")
        okved_display = _esc(f"{first_code}" + (f" — {first_desc}" if first_desc else ""))
    elif okved_codes:
        okved_display = _esc(str(okved_codes[0]))
    else:
        okved_display = "—"
    items_html += f"""<div class="metric"><div class="value" style="font-size: 0.95rem;">{okved_display}</div><div class="label">Профиль (ОКВЭД)</div></div>\n"""

    if not items_html:
        return ""

    # Wrap in a glass-card container (no <section> — inserted into About)
    insight_html = _render_section_insight(insight)
    return f"""<div class="clinic-metrics-grid" style="margin-top: 1.5rem;">
  <h3 style="margin-bottom: 0.75rem; font-family: var(--font-display, 'Playfair Display', serif);">Метрики клиники</h3>
  <div class="metrics">
{items_html}  </div>
  {insight_html}
</div>"""


# ── Phase 4 / DAT-02 + DAT-05: Media URLs + Ratings ─────────────────────


def _build_media_urls_section(
    data: dict,
    insight: str | None = None,
) -> str:
    """Build the Media URLs section (DAT-02, D-17..18).

    Reads ``data["media_urls"]`` (run_media_urls tool output per Plan
    04-03). When total_mentions > 0, renders a SIMPLE LIST of hyperlinks
    per D-17 (not cards with logos — MVP scope guard). When 0 mentions
    (pr_needed=True per D-18), renders an honest "В СМИ не упоминалась"
    block with a PR recommendation feedback loop to the Strategy section.

    Args:
        data: Session archive data dict. Reads the ``media_urls`` subkey.
        insight: Phase 5 / INT-05 — main strategic insight for this
            section (1-2 sentence business-language narrative from Pass 3
            LLM). When provided, rendered as ``<blockquote class=
            "section-insight">`` before the closing ``</section>``.

    Returns:
        HTML ``<section>`` block. Empty string when media_urls key is
        entirely absent (section not rendered — graceful degradation).
    """
    if not isinstance(data, dict):
        return ""
    media_urls = data.get("media_urls") or {}

    # Section is skipped entirely if the key is absent (backward compat
    # for sessions that didn't call run_media_urls).
    if not media_urls:
        return ""

    total_mentions = media_urls.get("total_mentions", 0) or 0
    all_mentions = media_urls.get("all_mentions", []) or []
    mentions_by_source = media_urls.get("mentions_by_source", []) or []
    pr_needed = media_urls.get("pr_needed", False)

    # D-18: honest block when 0 mentions
    # Note: pr_needed badge extracted outside f-string for Python 3.11 compat
    # (f-string expression part cannot include backslash pre-3.12)
    pr_badge = '<span class="metric-tag metric-tag-warning">PR Needed</span>' if pr_needed else ''
    if total_mentions == 0 or not all_mentions:
        return f"""<section class="section" data-aim="media-urls">
  <span class="section-label">Media (DAT-02)</span>
  <h2>Упоминания в СМИ</h2>
  <div class="glass-card" style="padding: 1.5rem; border-radius: 8px; background: var(--glass-bg, rgba(255,255,255,0.5)); border: 1px solid var(--border, #E0E0E0);">
    <p class="text-dim">В СМИ не упоминалась за последние 3 года (0 упоминаний в 5 целевых источниках: Forbes, RBC, Vademecum, Kommersant, ТАСС).</p>
    <p class="text-meta"><em>Рекомендация: PR-активность для повышения узнаваемости (см. Strategy).</em></p>
    {pr_badge}
  </div>
  {_render_section_insight(insight)}
</section>
<hr>"""

    # D-17: SIMPLE LIST of hyperlinks (not card-grid with logos)
    list_items = ""
    for mention in all_mentions:
        if not isinstance(mention, dict):
            continue
        source = _esc(str(mention.get("source", "")))
        title = _esc(str(mention.get("title", "")))
        url = _esc(str(mention.get("url", "")))
        date = _esc(str(mention.get("date", "")))
        # Format: source tag · link with title · date
        source_tag = (
            f'<span class="metric-tag metric-tag-info">{source}</span>'
            if source else ""
        )
        link_html = (
            f'<a href="{url}" target="_blank" rel="noopener noreferrer">'
            f'<strong>{title}</strong></a>'
        ) if url else f'<strong>{title}</strong>'
        date_html = f' <span class="text-dim">{date}</span>' if date else ""
        list_items += f"<li>{source_tag} {link_html}{date_html}</li>\n"

    if not list_items:
        return ""

    return f"""<section class="section" data-aim="media-urls">
  <span class="section-label">Media (DAT-02)</span>
  <h2>Упоминания в СМИ</h2>
  <p class="text-meta">Найдено упоминаний: <strong>{total_mentions}</strong> в {len(mentions_by_source) or 5} источниках</p>
  <div class="glass-card" style="padding: 1.5rem; border-radius: 8px; background: var(--glass-bg, rgba(255,255,255,0.5)); border: 1px solid var(--border, #E0E0E0);">
    <ul class="media-mentions-list" style="list-style: none; padding: 0; margin: 0; line-height: 1.8;">
{list_items}    </ul>
  </div>
  {_render_section_insight(insight)}
</section>
<hr>"""


def _build_ratings_section(
    reviews: dict,
    insight: str | None = None,
    gap_blocks: list | None = None,
) -> str:
    """Build the Ratings section (DAT-05, D-22..23).

    Reads ``reviews["ratings_extracted"]`` — a list of structured ratings
    the Pass 3 LLM extracted from the raw review_platforms analysis text.
    Per D-22, only 2 platforms are required (ПроДокторов + Яндекс.Карты);
    the section gracefully handles 1, 2, or more platforms.

    Args:
        reviews: ``data["review_platforms"]`` dict. Reads the
            ``ratings_extracted`` subkey (LLM-populated per Plan 04-05
            item 15 contract).
        insight: Phase 5 / INT-05 — main strategic insight for this
            section (1-2 sentence narrative). Rendered as blockquote
            before the closing ``</section>``.
        gap_blocks: Phase 5 / INT-04 — list of gap-block dicts (strength +
            growth points for this section). Rendered before the insight
            blockquote via ``_render_gap_blocks``.

    Returns:
        HTML ``<section>`` block. Empty string when ratings_extracted is
        absent (section not rendered — backward compatible with Phase 3
        reviews rendering).
    """
    if not isinstance(reviews, dict):
        return ""
    ratings = reviews.get("ratings_extracted") or []
    if not ratings or not isinstance(ratings, list):
        return ""

    cards_html = ""
    for r in ratings:
        if not isinstance(r, dict):
            continue
        platform = _esc(str(r.get("platform", "—")))
        rating_val = r.get("rating")
        review_count = r.get("review_count")
        positive_themes = r.get("positive_themes", []) or []
        negative_themes = r.get("negative_themes", []) or []

        # Format rating — stars + numeric
        try:
            rating_num = float(rating_val) if rating_val is not None else 0.0
        except (TypeError, ValueError):
            rating_num = 0.0
        full_stars = int(rating_num)
        empty_stars = max(0, 5 - full_stars)
        stars_str = "★" * full_stars + "☆" * empty_stars

        # Review count line
        try:
            count_num = int(review_count) if review_count is not None else 0
            count_str = f"{count_num} отзывов"
        except (TypeError, ValueError):
            count_str = f"{_esc(str(review_count))} отзывов"

        # Themes — positive (green) + negative (orange)
        positive_html = ""
        if positive_themes:
            tags = "".join(
                f'<span class="metric-tag metric-tag-success">{_esc(str(t))}</span>'
                for t in positive_themes[:5]
            )
            positive_html = f'<p class="text-meta" style="margin-top: 0.5rem;"><strong>Плюсы:</strong> {tags}</p>'

        negative_html = ""
        if negative_themes:
            tags = "".join(
                f'<span class="metric-tag metric-tag-warning">{_esc(str(t))}</span>'
                for t in negative_themes[:5]
            )
            negative_html = f'<p class="text-meta" style="margin-top: 0.5rem;"><strong>Минусы:</strong> {tags}</p>'

        cards_html += f"""<div class="glass-card rating-card" style="padding: 1.25rem; border-radius: 8px; background: var(--glass-bg, rgba(255,255,255,0.5)); border: 1px solid var(--border, #E0E0E0);">
  <h3 style="margin-top: 0;">{platform}</h3>
  <div class="rating-score" style="display: flex; align-items: center; gap: 0.75rem; margin: 0.5rem 0;">
    <span class="rating-stars" style="color: #c9a96e; font-size: 1.2rem; letter-spacing: 0.1em;">{stars_str}</span>
    <span class="rating-number" style="font-size: 1.2rem; font-weight: 500;">{rating_num:.1f}</span>
  </div>
  <p class="text-dim">{count_str}</p>
  {positive_html}
  {negative_html}
</div>
"""

    if not cards_html:
        return ""

    return f"""<section class="section" data-aim="ratings">
  <span class="section-label">Рейтинги и отзывы (DAT-05)</span>
  <h2>Репутация на платформах</h2>
  <div class="ratings-grid" style="display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap: 1rem;">
{cards_html}  </div>
  {_render_gap_blocks(gap_blocks)}
  {_render_section_insight(insight)}
</section>
<hr>"""


# ── Phase 4 / DAT-03: Competitor cards ──────────────────────────────────


def _build_competitor_cards_section(
    competitors: dict,
    insight: str | None = None,
) -> str:
    """Build the detailed competitor cards section (DAT-03, D-20).

    Reads ``competitors["competitor_cards"]`` — a list of detailed card
    dicts (per D-20): name, year_founded, revenue_latest, revenue_trend,
    surgeons_count, instagram_handle, instagram_followers,
    specialization. Renders a glass-card grid (one card per competitor).

    This section is APPENDED after the existing ``_build_competitor_table``
    (which stays as the summary view). The new cards section adds depth:
    each competitor gets a detailed card with all D-20 fields, including
    LLM-generated specialization from site scrape.

    Args:
        competitors: ``data["competitors"]`` or
            ``data["ci_analysis"]`` dict. Reads the
            ``competitor_cards`` subkey (LLM-populated per Plan 04-05
            item 9 contract).
        insight: Phase 5 / INT-05 — main strategic insight for this
            section (1-2 sentence narrative). Rendered as blockquote
            before the closing ``</section>``.

    Returns:
        HTML ``<section>`` block. Honest "не собраны" block when
        competitor_cards is empty (graceful degradation per ORC-04).
    """
    if not isinstance(competitors, dict):
        competitors = {}
    cards = competitors.get("competitor_cards", []) or []
    if not cards:
        return ""

    # Limit to top 10 cards (DoS mitigation per T-04-06-D threat register)
    cards = cards[:10]

    # Trend → CSS class mapping per plan spec
    trend_class_map = {
        "растущая": "metric-tag-success",
        "растущий": "metric-tag-success",
        "growing": "metric-tag-success",
        "стабильная": "metric-tag-info",
        "стабильный": "metric-tag-info",
        "stable": "metric-tag-info",
        "падающая": "metric-tag-danger",
        "падающий": "metric-tag-danger",
        "declining": "metric-tag-danger",
    }

    cards_html = ""
    for card in cards:
        if not isinstance(card, dict):
            continue
        name = _esc(str(card.get("name", "—")))
        year_founded = card.get("year_founded")
        year_str = _esc(str(year_founded)) if year_founded else "—"
        revenue_latest = card.get("revenue_latest")
        revenue_str = _fmt_revenue_short(revenue_latest)
        revenue_trend = card.get("revenue_trend", "")
        # Trend tag with mapped CSS class (default: neutral)
        trend_lower = str(revenue_trend).lower() if revenue_trend else ""
        trend_class = trend_class_map.get(trend_lower, "metric-tag-info")
        trend_tag_html = (
            f'<span class="metric-tag {trend_class}">{_esc(str(revenue_trend))}</span>'
            if revenue_trend else ""
        )
        surgeons_count = card.get("surgeons_count")
        surgeons_str = _esc(str(surgeons_count)) if surgeons_count else "—"
        instagram_handle = card.get("instagram_handle")
        instagram_followers = card.get("instagram_followers")
        specialization = _esc(str(card.get("specialization", "")))

        # Instagram block — only if handle exists
        ig_block = ""
        if instagram_handle:
            ig_handle_esc = _esc(str(instagram_handle))
            if instagram_followers:
                try:
                    followers_num = int(instagram_followers)
                    if followers_num >= 1_000_000:
                        followers_str = f"{followers_num / 1_000_000:.1f}M"
                    elif followers_num >= 1_000:
                        followers_str = f"{followers_num / 1_000:.0f}K"
                    else:
                        followers_str = str(followers_num)
                except (TypeError, ValueError):
                    followers_str = str(instagram_followers)
                ig_block = (
                    f'<div class="metric-item"><span class="metric-label">Instagram</span>'
                    f'<span class="metric-value">@{ig_handle_esc} · {followers_str} подписчиков</span></div>'
                )
            else:
                ig_block = (
                    f'<div class="metric-item"><span class="metric-label">Instagram</span>'
                    f'<span class="metric-value">@{ig_handle_esc}</span></div>'
                )

        cards_html += f"""<div class="glass-card competitor-card" style="padding: 1.5rem; border-radius: 8px; background: var(--glass-bg, rgba(255,255,255,0.5)); border: 1px solid var(--border, #E0E0E0);">
  <h3 style="margin-top: 0;">{name}</h3>
  <div class="card-metrics" style="display: grid; grid-template-columns: repeat(auto-fit, minmax(160px, 1fr)); gap: 0.75rem; margin-top: 0.75rem;">
    <div class="metric-item"><span class="metric-label" style="display: block; font-size: 0.75rem; text-transform: uppercase; color: var(--text-dim, #6d6d6d); letter-spacing: 0.05em;">Год основания</span><span class="metric-value" style="display: block; font-weight: 500;">{year_str}</span></div>
    <div class="metric-item"><span class="metric-label" style="display: block; font-size: 0.75rem; text-transform: uppercase; color: var(--text-dim, #6d6d6d); letter-spacing: 0.05em;">Выручка</span><span class="metric-value" style="display: block; font-weight: 500;">{_esc(revenue_str)} {trend_tag_html}</span></div>
    <div class="metric-item"><span class="metric-label" style="display: block; font-size: 0.75rem; text-transform: uppercase; color: var(--text-dim, #6d6d6d); letter-spacing: 0.05em;">Хирургов / Косметологов</span><span class="metric-value" style="display: block; font-weight: 500;">{surgeons_str}</span></div>
{ig_block}  </div>
  {f'<div class="card-specialization" style="margin-top: 1rem; padding-top: 0.75rem; border-top: 1px solid var(--border, #E0E0E0);"><p class="text-dim"><strong>Специфика:</strong> {specialization}</p></div>' if specialization else ''}
</div>
"""

    if not cards_html:
        return ""

    return f"""<section class="section" data-aim="competitor-cards">
  <span class="section-label">Конкуренты (DAT-03)</span>
  <h2>Детальные карточки конкурентов</h2>
  <p class="text-meta">Подробный разбор каждой клиники-конкурента: финансы, врачи, Instagram, специфика.</p>
  <div class="competitor-cards-grid" style="display: grid; grid-template-columns: repeat(auto-fit, minmax(320px, 1fr)); gap: 1rem; margin-top: 1rem;">
{cards_html}  </div>
  {_render_section_insight(insight)}
</section>
<hr>"""


# ── Phase 4 / SEC-01 + SEC-02: Strategy + Offer (LLM-generated) ────────


def _build_strategy_section(
    strategy_data: dict | None,
    insight: str | None = None,
    gap_blocks: list | None = None,
) -> str:
    """Build the Strategy section with 5 LLM-generated directions (SEC-01).

    Per D-01: Strategy is LLM-generated in Pass 3 from all collected data
    (competitors, content_gaps, patient_fears, reputation_gaps).
    Per D-02: 5 directions are FIXED as the frame (Контент, Telegram,
    GEO, Репутация, Кросс-промо), but each direction's CONTENT is
    LLM-generated with concrete steps for this specific clinic.
    Per D-03: Each direction's ``basis`` field documents which of the 4
    basis sources informed the recommendations (конкуренты / content_gaps
    / страхи / reputation).

    Args:
        strategy_data: Dict with ``directions`` list. Each direction has
            ``name``, ``steps`` (list), ``basis`` (str), ``expected_impact``.
        insight: Phase 5 / INT-05 — main strategic insight (1-2 sentence
            narrative). Rendered as blockquote before closing ``</section>``.
        gap_blocks: Phase 5 / INT-04 — list of gap-block dicts (strength +
            growth points for this section). Rendered before the insight
            blockquote via ``_render_gap_blocks``.

    Returns:
        HTML ``<section>`` block. Empty string when strategy_data is None
        (section not rendered — backward compatible). Honest block when
        directions list is empty (graceful degradation per ORC-04).
    """
    if not strategy_data or not isinstance(strategy_data, dict):
        return ""
    directions = strategy_data.get("directions", []) or []
    if not directions:
        return """<section class="section" data-aim="strategy">
  <span class="section-label">Strategy (SEC-01)</span>
  <h2>Стратегия развития</h2>
  <div class="glass-card" style="padding: 1.5rem; border-radius: 8px; background: var(--glass-bg, rgba(255,255,255,0.5)); border: 1px solid var(--border, #E0E0E0);">
    <p class="text-dim">Стратегия не сгенерирована — недостаточно данных для рекомендаций.</p>
  </div>
</section>
<hr>"""

    # D-02: limit to 5 directions (frame is fixed)
    directions = directions[:5]

    # Direction icon mapping (D-02 fixed direction names)
    direction_icons = {
        "контент": "📝",
        "telegram": "📱",
        "geo": "📍",
        "репутация": "⭐",
        "кросс-промо": "🤝",
        "кросс промо": "🤝",
        "cross-promo": "🤝",
        "cross_promo": "🤝",
    }

    directions_html = ""
    for direction in directions:
        if not isinstance(direction, dict):
            continue
        name = str(direction.get("name", ""))
        name_lower = name.lower()
        icon = direction_icons.get(name_lower, "💡")
        steps = direction.get("steps", []) or []
        basis = direction.get("basis", "—")
        impact = direction.get("expected_impact", "")

        steps_html = ""
        for step in steps:
            steps_html += f"          <li>{_esc(str(step))}</li>\n"

        basis_html = (
            f'<p class="text-meta" style="margin-bottom: 0.5rem;">'
            f'<strong>Базис:</strong> {_esc(str(basis))}</p>'
        )

        impact_html = (
            f'<p style="margin-top: 0.5rem;">'
            f'<span class="metric-tag metric-tag-info">{_esc(str(impact))}</span>'
            f'</p>'
        ) if impact else ""

        steps_list_html = (
            f'<ol style="margin: 0.5rem 0 0.5rem 1.5rem; line-height: 1.6;">\n'
            f'{steps_html}        </ol>'
        ) if steps_html else ""

        directions_html += f"""        <div class="glass-card strategy-direction" style="padding: 1.25rem; border-radius: 8px; background: var(--glass-bg, rgba(255,255,255,0.5)); border: 1px solid var(--border, #E0E0E0); margin-bottom: 1rem;">
          <h3 style="margin-top: 0;">{icon} {_esc(name)}</h3>
          {basis_html}
          {steps_list_html}
          {impact_html}
        </div>
"""

    return f"""<section class="section" data-aim="strategy">
  <span class="section-label">Strategy (SEC-01)</span>
  <h2>Стратегия развития</h2>
  <blockquote style="margin: 1rem 0; padding: 0.75rem 1.25rem; border-left: 3px solid var(--accent, #c9a96e); background: var(--glass-bg, rgba(255,255,255,0.3));">
    <p>5 направлений развития, сгенерированных из собранных данных: конкуренты + content_gaps + страхи пациентов + репутация.</p>
  </blockquote>
  <div class="strategy-directions">
{directions_html}  </div>
  {_render_gap_blocks(gap_blocks)}
  {_render_section_insight(insight)}
</section>
<hr>"""


def _build_offer_section(
    offer_data: dict | None,
    insight: str | None = None,
    gap_blocks: list | None = None,
) -> str:
    """Build the Offer section "Что AIM может сделать для клиники" (SEC-02, D-04).

    Per D-04: Offer section follows the same LLM-generation pattern as
    SEC-01 — Pass 3 LLM generates concrete steps + CTA from collected
    data. Each step references a specific AIM service (контент-продакшн,
    SEO, репутация-менеджмент, Telegram-маркетинг).

    Args:
        offer_data: Dict with ``steps`` list (each: ``service``,
            ``description``, ``timeline``) + ``cta`` string.
        insight: Phase 5 / INT-05 — main strategic insight (1-2 sentence
            narrative). Rendered as blockquote before closing ``</section>``.
        gap_blocks: Phase 5 / INT-04 — list of gap-block dicts (strength +
            growth points for this section). Rendered before the insight
            blockquote via ``_render_gap_blocks``.

    Returns:
        HTML ``<section>`` block. Empty string when offer_data is None
        (section not rendered — backward compatible). Honest block when
        steps list is empty (graceful degradation per ORC-04).
    """
    if not offer_data or not isinstance(offer_data, dict):
        return ""
    steps = offer_data.get("steps", []) or []
    cta = offer_data.get("cta", "") or ""

    if not steps:
        return """<section class="section" data-aim="offer">
  <span class="section-label">Offer (SEC-02)</span>
  <h2>Что AIM может сделать для клиники</h2>
  <div class="glass-card" style="padding: 1.5rem; border-radius: 8px; background: var(--glass-bg, rgba(255,255,255,0.5)); border: 1px solid var(--border, #E0E0E0);">
    <p class="text-dim">Offer не сгенерирован — недостаточно данных.</p>
  </div>
</section>
<hr>"""

    steps_html = ""
    for step in steps:
        if not isinstance(step, dict):
            continue
        service = step.get("service", "Услуга")
        description = step.get("description", "")
        timeline = step.get("timeline", "—")

        desc_html = f"<p>{_esc(str(description))}</p>" if description else ""
        steps_html += f"""        <div class="glass-card offer-step" style="padding: 1.25rem; border-radius: 8px; background: var(--glass-bg, rgba(255,255,255,0.5)); border: 1px solid var(--border, #E0E0E0); margin-bottom: 0.75rem;">
          <h3 style="margin-top: 0;">{_esc(str(service))}</h3>
          {desc_html}
          <p class="text-meta" style="margin-bottom: 0;"><span class="metric-tag metric-tag-info">⏱ {_esc(str(timeline))}</span></p>
        </div>
"""

    cta_html = ""
    if cta:
        cta_html = f"""  <div class="offer-cta" style="margin-top: 1.5rem; padding: 1.25rem 1.5rem; border-radius: 8px; background: var(--accent, #c9a96e); color: var(--bg, #0d0d0d); text-align: center;">
    <p class="cta-text" style="margin: 0; font-size: 1.15rem; font-weight: 500;">{_esc(str(cta))}</p>
  </div>"""

    return f"""<section class="section" data-aim="offer">
  <span class="section-label">Offer (SEC-02)</span>
  <h2>Что AIM может сделать для клиники</h2>
  <blockquote style="margin: 1rem 0; padding: 0.75rem 1.25rem; border-left: 3px solid var(--accent, #c9a96e); background: var(--glass-bg, rgba(255,255,255,0.3));">
    <p>На основе анализа мы предлагаем следующие шаги:</p>
  </blockquote>
  <div class="offer-steps">
{steps_html}  </div>
{cta_html}
  {_render_gap_blocks(gap_blocks)}
  {_render_section_insight(insight)}
</section>
<hr>"""


# ── Phase 4 / SEC-03: Whitefields matrix ───────────────────────────────


def _build_whitefields_matrix(
    whitefields_data: dict | None,
    insight: str | None = None,
) -> str:
    """Build the 4×4 Whitefields comparison matrix (SEC-03, D-05..07).

    Per D-05: 4 category rows in the matrix:
      1. Услуги — services offered (пластика груди/липосакция/инъекции/...)
      2. Цены — top-3 services price ranges
      3. Врачи — surgeons/cosmetologists count + регалии
      4. Digital presence — Instagram/Telegram/SEO rank/rating
    Per D-06: minimum 4 columns (client + 3 competitors). If fewer than
    3 competitors found, render with honest "матрица неполная" note.
    Per D-07: cells are filled from already-collected data — no extra
    API calls. Cell key format: ``"{category}_{col_index}"``.

    Args:
        whitefields_data: Dict with ``categories`` (list of 4 str),
            ``columns`` (list of ``{name, is_client}`` dicts), ``cells``
            (dict keyed by ``"{category}_{col_index}"``).
        insight: Phase 5 / INT-05 — main strategic insight (1-2 sentence
            narrative). Rendered as blockquote before closing ``</section>``
            (after the scoped ``</style>`` block).

    Returns:
        HTML ``<section>`` block with ``<table>``. Empty string when
        whitefields_data is None (section not rendered). Honest block
        when categories/columns missing (graceful degradation).
    """
    if not whitefields_data or not isinstance(whitefields_data, dict):
        return ""
    categories = whitefields_data.get("categories", []) or []
    columns = whitefields_data.get("columns", []) or []
    cells = whitefields_data.get("cells", {}) or {}

    if not categories or not columns:
        return ""

    # D-06: honest note when fewer than 4 columns (<3 competitors)
    columns_count = len(columns)
    honest_note = ""
    if columns_count < 4:
        honest_note = (
            '<p class="text-meta" style="margin-top: 0.5rem;">'
            '<em>Менее 3 конкурентов найдено — матрица неполная.</em></p>'
        )

    # Build header row: Категория | col 1 | col 2 | col 3 | col 4
    header_cells = "<th>Категория</th>"
    for col in columns:
        if not isinstance(col, dict):
            col = {"name": str(col)}
        col_name = col.get("name", "—")
        is_client = col.get("is_client", False)
        client_class = ' class="client-column"' if is_client else ""
        header_cells += f"<th{client_class}>{_esc(str(col_name))}</th>"

    # Build body rows — one row per category
    body_rows = ""
    for category in categories:
        row_cells = (
            f'<td class="category-cell" style="font-weight: 500;">'
            f'{_esc(str(category))}</td>'
        )
        for col_idx in range(columns_count):
            cell_key = f"{category}_{col_idx}"
            cell_value = cells.get(cell_key, "—")
            # First data column (index 0) is the client column
            col_is_client = (
                isinstance(columns[col_idx], dict)
                and columns[col_idx].get("is_client", False)
            ) if col_idx < len(columns) else (col_idx == 0)
            client_class = ' class="client-column"' if col_is_client else ""
            row_cells += f"<td{client_class}>{_esc(str(cell_value))}</td>"
        body_rows += f"        <tr>{row_cells}</tr>\n"

    return f"""<section class="section" data-aim="whitefields-matrix">
  <span class="section-label">Whitefields Matrix (SEC-03)</span>
  <h2>Сравнение с конкурентами</h2>
  <blockquote style="margin: 1rem 0; padding: 0.75rem 1.25rem; border-left: 3px solid var(--accent, #c9a96e); background: var(--glass-bg, rgba(255,255,255,0.3));">
    <p>Сравнение по 4 категориям: Услуги, Цены, Врачи, Digital presence — клиент и топ-3 конкурента.</p>
  </blockquote>
  {honest_note}
  <div class="glass-card" style="padding: 1.5rem; border-radius: 8px; background: var(--glass-bg, rgba(255,255,255,0.5)); border: 1px solid var(--border, #E0E0E0); overflow-x: auto;">
    <table class="comp-table whitefields-matrix-table" style="width: 100%; border-collapse: collapse; font-size: 0.9rem;">
      <thead>
        <tr>{header_cells}</tr>
      </thead>
      <tbody>
{body_rows}      </tbody>
    </table>
  </div>
  <style>
.whitefields-matrix-table .client-column {{
  background: rgba(201,169,110,0.08);
  font-weight: 500;
  border-left: 2px solid var(--accent, #c9a96e);
  border-right: 2px solid var(--accent, #c9a96e);
}}
.whitefields-matrix-table .category-cell {{
  background: rgba(0,0,0,0.03);
  text-transform: uppercase;
  font-size: 0.75rem;
  letter-spacing: 0.05em;
  color: var(--text-dim, #6d6d6d);
}}
[data-theme="dark"] .whitefields-matrix-table .category-cell {{
  background: rgba(201,169,110,0.05);
}}
.whitefields-matrix-table thead th {{
  text-align: left;
  padding: 0.6rem 0.8rem;
  font-weight: 500;
  font-size: 0.75rem;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  border-bottom: 2px solid var(--border, #e0e0e0);
  color: var(--text-dim, #888);
}}
.whitefields-matrix-table tbody td {{
  padding: 0.7rem 0.8rem;
  border-bottom: 1px solid var(--border, rgba(0,0,0,0.08));
  vertical-align: top;
}}
  </style>
  {_render_section_insight(insight)}
</section>
<hr>"""


# ── Phase 4 / SEC-04 + SEC-05: Experts + Content Analysis with fears ───


def _build_experts_with_regalia(
    experts_data: list | None,
    insight: str | None = None,
    gap_blocks: list | None = None,
) -> str:
    """Build enhanced Experts section with регалии + Instagram metrics (SEC-04).

    Per D-08: Phase 4 adds регалии from site scrape (degree, academic_title,
    experience_years, education) via ``find_doctor_handles.structured_regalia``.
    Per D-09: site-scraped регалии are merged with Instagram metrics by
    ФИО via ``_merge_doctor_data`` (Plan 04-02). This function renders
    the merged result.

    Each expert has a ``source`` field indicating data origin:
      - ``"both"`` — site + Instagram (full picture)
      - ``"site"`` — only site (no Instagram; valid expert)
      - ``"instagram_only"`` — only Instagram (Регалии недоступны)

    Args:
        experts_data: List of expert dicts (max 5 rendered). Each dict:
            ``name``, ``structured_regalia`` (dict), ``instagram_metrics``
            (dict or None), ``source`` (str).
        insight: Phase 5 / INT-05 — main strategic insight (1-2 sentence
            narrative). Rendered as blockquote before closing ``</section>``.
        gap_blocks: Phase 5 / INT-04 — list of gap-block dicts (strength +
            growth points for this section). Rendered before the insight
            blockquote via ``_render_gap_blocks``.

    Returns:
        HTML ``<section>`` block. Empty string when list is None/empty.
    """
    if not experts_data or not isinstance(experts_data, list):
        return ""

    # Limit to top 5 experts (SEC-04 contract)
    experts_data = experts_data[:5]

    cards_html = ""
    for expert in experts_data:
        if not isinstance(expert, dict):
            continue
        name = expert.get("name", "—")
        regalia = expert.get("structured_regalia") or {}
        ig_metrics = expert.get("instagram_metrics")
        source = expert.get("source", "—")

        # Регалии badges (D-08)
        regalia_badges = ""
        if isinstance(regalia, dict):
            degree = regalia.get("degree")
            if degree:
                # ДМН > КМН per Russian academic hierarchy
                degree_class = (
                    "metric-tag-success" if str(degree).upper() in ("ДМН", "DMH")
                    else "metric-tag-info"
                )
                regalia_badges += f'<span class="metric-tag {degree_class}">{_esc(str(degree))}</span>'

            title = regalia.get("academic_title")
            if title:
                title_lower = str(title).lower()
                # профессор > доцент > others
                if "профессор" in title_lower or "академик" in title_lower:
                    title_class = "metric-tag-success"
                else:
                    title_class = "metric-tag-info"
                regalia_badges += f'<span class="metric-tag {title_class}">{_esc(str(title))}</span>'

            exp_years = regalia.get("experience_years")
            if exp_years is not None:
                try:
                    years_int = int(exp_years)
                    regalia_badges += f'<span class="metric-tag metric-tag-info">Стаж {years_int} лет</span>'
                except (TypeError, ValueError):
                    pass

        # Education line
        education_html = ""
        if isinstance(regalia, dict):
            education = regalia.get("education", []) or []
            if education:
                edu_items = [str(e) for e in education[:3] if e]
                if edu_items:
                    edu_str = ", ".join(edu_items)
                    education_html = f'<p class="text-meta" style="margin-top: 0.4rem;"><strong>Образование:</strong> {_esc(edu_str)}</p>'

        regalia_block = (
            f'<div class="expert-regalia" style="margin: 0.5rem 0;">{regalia_badges}</div>'
            if regalia_badges else ""
        )

        # Instagram metrics block (D-09)
        # Per plan: source='instagram_only' always shows "Регалии недоступны"
        # note, regardless of whether IG metrics are present (explains why
        # this expert has no регалии — they're not on the clinic site).
        ig_block = ""
        if ig_metrics and isinstance(ig_metrics, dict):
            followers = ig_metrics.get("followers_count")
            avg_likes = ig_metrics.get("avg_likes")
            avg_views = ig_metrics.get("avg_views")
            content_style = ig_metrics.get("content_style", "")

            ig_values = ""
            if followers is not None:
                ig_values += f'<div class="metric"><div class="value">{_esc(_fmt_num(followers))}</div><div class="label">Подписчиков</div></div>'
            if avg_likes is not None:
                ig_values += f'<div class="metric"><div class="value">{_esc(_fmt_num(avg_likes))}</div><div class="label">Ср. лайков</div></div>'
            if avg_views is not None:
                ig_values += f'<div class="metric"><div class="value">{_esc(_fmt_num(avg_views))}</div><div class="label">Ср. просмотров</div></div>'

            ig_metrics_block = ""
            if ig_values:
                ig_metrics_block = f'<div class="metrics" style="margin-top: 0.6rem;">{ig_values}</div>'
            style_block = ""
            if content_style:
                style_block = f'<p class="text-meta" style="margin-top: 0.4rem;">Стиль: {_esc(str(content_style))}</p>'
            if ig_metrics_block or style_block:
                ig_block = ig_metrics_block + style_block
        elif source == "site":
            ig_block = '<p class="text-meta text-dim" style="margin-top: 0.5rem;"><em>Instagram не обнаружен</em></p>'
        elif source == "instagram_only":
            ig_block = '<p class="text-meta text-dim" style="margin-top: 0.5rem;"><em>Регалии недоступны — врач не на сайте клиники</em></p>'

        # For source='instagram_only' WITH ig_metrics, append the note after metrics
        # so the user understands why no регалии badges appear.
        if (
            source == "instagram_only"
            and ig_metrics
            and isinstance(ig_metrics, dict)
            and ig_block
        ):
            ig_block += '<p class="text-meta text-dim" style="margin-top: 0.4rem; font-size: 0.8rem;"><em>Регалии недоступны — врач не на сайте клиники</em></p>'

        # Source indicator (small, at bottom)
        source_map = {
            "both": "Сайт + Instagram",
            "site": "Только сайт клиники",
            "instagram_only": "Только Instagram",
        }
        source_text = source_map.get(source, str(source))

        cards_html += f"""        <div class="glass-card expert-card" style="padding: 1.25rem; border-radius: 8px; background: var(--glass-bg, rgba(255,255,255,0.5)); border: 1px solid var(--border, #E0E0E0);">
          <h3 style="margin-top: 0;">{_esc(str(name))}</h3>
          {regalia_block}
          {education_html}
          {ig_block}
          <p class="text-meta text-dim" style="margin-top: 0.6rem; font-size: 0.75rem; margin-bottom: 0;"><em>Источник: {_esc(source_text)}</em></p>
        </div>
"""

    if not cards_html:
        return ""

    return f"""<section class="section" data-aim="experts-with-regalia">
  <span class="section-label">Experts (SEC-04)</span>
  <h2>Топ-эксперты клиники</h2>
  <p class="text-meta">Регалии из сайта клиники + Instagram-метрики, объединённые по ФИО.</p>
  <div class="experts-grid" style="display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 1rem; margin-top: 1rem;">
{cards_html}  </div>
  {_render_gap_blocks(gap_blocks)}
  {_render_section_insight(insight)}
</section>
<hr>"""


def _build_content_analysis_with_fears(
    content_data: dict | None,
    insight: str | None = None,
    gap_blocks: list | None = None,
) -> str:
    """Build enhanced Content Analysis with patient fears (SEC-05, D-10..11).

    Per D-10: combines per-doctor Instagram content analysis (style,
    themes, gaps, potential) with top-5 patient fears scraped from
    forums (ПроДокторов, Otzovik, IRecommend, Woman.ru).
    Per D-11: fears are extracted from review TEXTS (not star ratings),
    each with mention_count + context.

    Args:
        content_data: Dict with ``doctor_analyses`` (list of dicts) and
            ``patient_fears`` (list of dicts with ``fear``,
            ``mention_count``, ``context``). Optional ``total_reviews``.
        insight: Phase 5 / INT-05 — main strategic insight (1-2 sentence
            narrative). Rendered as blockquote before closing ``</section>``.
        gap_blocks: Phase 5 / INT-04 — list of gap-block dicts (strength +
            growth points for this section). Rendered before the insight
            blockquote via ``_render_gap_blocks``.

    Returns:
        HTML ``<section>`` block. Empty string when content_data is None
        or both lists empty. Honest note when fears not collected.
    """
    if not content_data or not isinstance(content_data, dict):
        return ""

    doctor_analyses = content_data.get("doctor_analyses", []) or []
    patient_fears = content_data.get("patient_fears", []) or []
    total_reviews = content_data.get("total_reviews", 0) or 0

    if not doctor_analyses and not patient_fears:
        return ""

    # Part 1: Per-doctor content analysis
    analyses_html = ""
    for doctor in doctor_analyses:
        if not isinstance(doctor, dict):
            continue
        name = doctor.get("name", "—")
        style = doctor.get("style", "—")
        themes = doctor.get("themes", []) or []
        gaps = doctor.get("gaps", []) or []
        potential = doctor.get("potential", "—")

        # Themes as inline metric-tag badges
        themes_html = ""
        for theme in themes[:5]:
            if isinstance(theme, dict):
                theme_name = theme.get("name", "")
                theme_pct = theme.get("pct", 0)
                if theme_name:
                    themes_html += f'<span class="metric-tag metric-tag-info">{_esc(str(theme_name))}: {_esc(str(theme_pct))}%</span>'

        themes_block = (
            f'<div style="margin: 0.4rem 0;">{themes_html}</div>'
            if themes_html else ""
        )

        gaps_str = ", ".join(str(g) for g in gaps) if gaps else ""
        gaps_block = (
            f'<p><strong>Пробелы:</strong> {_esc(gaps_str)}</p>'
            if gaps_str else ""
        )

        analyses_html += f"""        <div class="glass-card content-analysis-card" style="padding: 1.25rem; border-radius: 8px; background: var(--glass-bg, rgba(255,255,255,0.5)); border: 1px solid var(--border, #E0E0E0); margin-bottom: 0.75rem;">
          <h3 style="margin-top: 0;">{_esc(str(name))}</h3>
          <p><strong>Стиль:</strong> {_esc(str(style))}</p>
          {themes_block}
          {gaps_block}
          <p class="text-dim"><strong>Потенциал:</strong> {_esc(str(potential))}</p>
        </div>
"""

    analyses_section = ""
    if analyses_html:
        analyses_section = f"""  <div class="content-analyses">
{analyses_html}  </div>"""

    # Part 2: Top-5 patient fears (D-10, D-11)
    fears_section = ""
    if patient_fears:
        fears_list = ""
        for fear in patient_fears[:5]:
            if not isinstance(fear, dict):
                continue
            fear_text = fear.get("fear", "—")
            mention_count = fear.get("mention_count", 0)
            context = fear.get("context", "")

            context_html = (
                f'<p class="text-dim" style="margin: 0.25rem 0 0 0;">{_esc(str(context))}</p>'
                if context else ""
            )

            fears_list += f"""      <li style="margin-bottom: 0.75rem;">
        <strong>{_esc(str(fear_text))}</strong>
        <span class="metric-tag metric-tag-warning">{_esc(str(mention_count))} упоминаний</span>
        {context_html}
      </li>
"""

        if fears_list:
            total_str = str(total_reviews) if total_reviews else "собранных"
            fears_section = f"""  <div class="patient-fears-block" style="margin-top: 1.5rem;">
    <h3>🔥 Топ-5 страхов пациентов</h3>
    <blockquote style="margin: 1rem 0; padding: 0.75rem 1.25rem; border-left: 3px solid var(--accent, #c9a96e); background: var(--glass-bg, rgba(255,255,255,0.3));">
      <p>На основе {total_str} отзывов с ПроДокторов, Otzovik, IRecommend, Woman.ru</p>
    </blockquote>
    <ol class="fears-list" style="margin: 0.5rem 0 0 1.5rem; line-height: 1.6;">
{fears_list}    </ol>
  </div>"""
    else:
        fears_section = (
            '  <div class="patient-fears-block" style="margin-top: 1.5rem;">'
            '<p class="text-dim"><em>Страхи пациентов не собраны — '
            'run_forum_pains не вызван или не дал данных.</em></p></div>'
        )

    return f"""<section class="section" data-aim="content-analysis-with-fears">
  <span class="section-label">Content Analysis + Страхи (SEC-05)</span>
  <h2>Анализ контента и страхов пациентов</h2>
{analyses_section}
{fears_section}
  {_render_gap_blocks(gap_blocks)}
  {_render_section_insight(insight)}
</section>
<hr>"""


def _build_no_instagram_block(reason: str) -> str:
    """Render an honest "Instagram: данные недоступны — {reason}" block.

    Per Phase 3 / D-07: when a clinic is in an Instagram-critical niche
    (plastic_surgery, cosmetology) but Instagram data is unavailable, the
    HTML report must transparently explain WHY — rather than silently
    omit the section. This block is appended to sections 03 (Experts)
    and 04 (Content Analysis) by ``_build_report_html`` when the
    conditional render fires.

    Args:
        reason: One of 4 known variants:
            - ``"no_account"`` — Instagram not even attempted (no handle
              discovered / clinic has no Instagram).
            - ``"handle_not_found"`` — Instagram-handle врача не найден
              на сайте клиники.
            - ``"private_profile"`` — profile is private, data hidden.
            - ``"perplexity_outside_index"`` — handles tried via
              run_instagram_content, but Perplexity returned no data.
            Any other value falls back to a generic message that
            includes the raw reason (XSS-escaped).

    Returns:
        HTML ``<div class="no-instagram-block surface-card">`` block with:
          - Heading "Instagram: данные недоступны"
          - Russian user-facing reason text (XSS-escaped via ``_esc``)
          - Warning badge "Instagram N/A"
          - Scoped ``<style>`` block with light + dark theme variants
            matching the qc-coverage-section glass-card pattern.
    """
    reason_map = {
        "no_account": "У клиники нет аккаунта Instagram",
        "handle_not_found": "Instagram-handle врача не найден на сайте клиники",
        "private_profile": "Instagram-профиль приватный — данные недоступны",
        "perplexity_outside_index": (
            "Instagram-handle не в индексе Perplexity — данные недоступны "
            "(вызовы были произведены, ни один не вернул данных)"
        ),
    }
    mapped = reason_map.get(reason)
    if mapped is None:
        # Generic fallback — preserve the raw reason (XSS-escaped).
        reason_text = f"Instagram: данные недоступны — {_esc(str(reason))}"
    else:
        reason_text = _esc(mapped)

    return f"""<div class="no-instagram-block surface-card">
  <h4>Instagram: данные недоступны</h4>
  <p class="text-dim">{reason_text}</p>
  <span class="metric-tag metric-tag-warning">Instagram N/A</span>
</div>
<style>
.no-instagram-block {{
  margin-top: 1rem;
  padding: 1.5rem;
  border-radius: 8px;
  background: var(--glass-bg, rgba(255,255,255,0.5));
  border: 1px solid var(--border, #E0E0E0);
}}
.no-instagram-block h4 {{
  margin-top: 0;
  margin-bottom: 0.5rem;
}}
.no-instagram-block .text-dim {{
  margin-bottom: 0.75rem;
  line-height: 1.5;
}}
[data-theme="dark"] .no-instagram-block {{
  background: rgba(201,169,110,0.05);
  border-color: rgba(201,169,110,0.18);
}}
</style>
"""


def _maybe_build_no_instagram_block(
    niche: str, instagram_data: dict | None,
) -> str:
    """Return ``_build_no_instagram_block(reason)`` HTML or empty string.

    Per Phase 3 / D-07: render the no-Instagram block ONLY when:
      1. ``niche`` is one of ``CRITICAL_NICHES`` (plastic_surgery,
         cosmetology); AND
      2. ``instagram_data`` is None / not a dict / empty / has
         ``analyzed_count == 0``.

    For non-critical niches (dental, general_medicine, other, unknown),
    return empty string — the section appears without Instagram content,
    no warning is shown.

    Reason selection:
      - ``instagram_data is None`` → ``"no_account"`` (Instagram not even
        attempted; defensive default).
      - ``analyzed_count == 0`` (handles tried, all failed) →
        ``"perplexity_outside_index"``.
      - Other shape (e.g. dict with profiles but all empty) →
        ``"handle_not_found"`` (most common case — handle invalid).

    Args:
        niche: Clinic niche verdict (from Plan 03-02 mini-call).
        instagram_data: run_instagram_content batch response (or None).

    Returns:
        HTML block string (may be empty).
    """
    # Lazy import to avoid top-level orchestrator dependency.
    try:
        from app.orchestrator.qc_checklist import is_niche_instagram_critical
    except Exception:
        # If qc_checklist is unavailable (e.g. legacy deploy), bail out
        # safely — no block rendered. Defensive.
        return ""

    if not is_niche_instagram_critical(niche):
        return ""

    # Determine whether instagram_data represents "no data".
    has_no_data = False
    if instagram_data is None:
        has_no_data = True
        reason = "no_account"
    elif not isinstance(instagram_data, dict):
        has_no_data = True
        reason = "no_account"
    elif not instagram_data:
        has_no_data = True
        reason = "no_account"
    else:
        analyzed = instagram_data.get("analyzed_count")
        try:
            analyzed_n = int(analyzed) if analyzed is not None else 0
        except (TypeError, ValueError):
            analyzed_n = 0
        if analyzed_n == 0:
            has_no_data = True
            reason = "perplexity_outside_index"
        else:
            # Has analyzed profiles — Instagram data is real. Do NOT
            # render the block. (If individual handles failed, that's
            # shown in the per-doctor sections, not here.)
            return ""

    if not has_no_data:
        return ""

    return _build_no_instagram_block(reason)


def _build_qc_coverage_section(metadata: dict) -> str:
    """Build the QC Coverage Report section HTML (Plan 02-03 Task 3 / QC-03).

    Renders the final coverage report at the end of the HTML page so the
    client (and admin) can see exactly which checklist items are filled vs
    marked "данные недоступны" (ORC-04 honest-data principle).

    Phase 3 / D-08 (Plan 03-05 Task 2): the section now reads
    ``metadata["not_applicable_items"]`` as the CANONICAL source for
    items that do not apply to the current niche (e.g., item 5 Instagram
    analysis for a non-critical niche like dental). This field is
    populated by Plan 03-06's ``_apply_niche_conditional_coverage``
    helper, which mutates ``CoverageReport.not_applicable_items`` for
    non-critical niches (and leaves it empty for critical/unknown
    niches). The HTML renders not_applicable items with a distinct
    ⚪ icon + gray styling + opacity 0.6 — visually separated from
    missing items (❌ red) and partial items (🟡 yellow). The effective
    total (``metadata["total_items"]``) is already adjusted by Plan
    03-06's helper (14 for non-critical, 15 for critical), so the
    summary line's denominator reflects the post-helper value.

    Args:
        metadata: CoverageReport as dict (from
            ``dataclasses.asdict(coverage_report_final)``). Expected keys:
            ``total_items``, ``filled_items``, ``missing_items``,
            ``partial_items``, ``not_applicable_items`` (Plan 03-06),
            ``coverage_pct``, ``status``.

    Returns:
        HTML string for the section, or empty string if metadata is falsy.
    """
    if not metadata or not isinstance(metadata, dict):
        return ""

    total = metadata.get("total_items", 15)
    filled_ids = metadata.get("filled_items", []) or []
    missing_items = metadata.get("missing_items", []) or []
    partial_items = metadata.get("partial_items", []) or []
    # Plan 03-05 / D-08: canonical source for not-applicable items
    # (populated by Plan 03-06 _apply_niche_conditional_coverage helper).
    # Per Fix #2 — do NOT scan metadata["items"] for status as a fallback.
    not_applicable_items = metadata.get("not_applicable_items", []) or []
    coverage_pct = metadata.get("coverage_pct", 0.0)
    status = str(metadata.get("status", "FAIL")).upper()

    # Format percentage: 0.867 → "86.7%"
    try:
        pct_num = float(coverage_pct) * 100
        pct_str = f"{pct_num:.1f}%"
    except (TypeError, ValueError):
        pct_str = "—"

    # PASS / FAIL badge — design-system metric-tag classes
    if status == "PASS":
        badge = '<span class="metric-tag metric-tag-success">PASS</span>'
    else:
        badge = '<span class="metric-tag metric-tag-warning">FAIL</span>'

    # Build per-item list. We need names for items — try to import the
    # checklist for canonical names; degrade gracefully if unavailable.
    try:
        from app.orchestrator.qc_checklist import QC_CHECKLIST
        names_by_id = {it["id"]: it["name"] for it in QC_CHECKLIST}
    except Exception:
        names_by_id = {}

    filled_set = set(filled_ids)
    partial_by_id = {p.get("id"): p for p in partial_items if isinstance(p, dict)}
    missing_by_id = {m.get("id"): m for m in missing_items if isinstance(m, dict)}
    # Plan 03-05 / D-08: canonical not_applicable_by_id — sourced from
    # metadata["not_applicable_items"] (populated by Plan 03-06 helper).
    not_applicable_by_id = {
        item.get("id"): item
        for item in not_applicable_items
        if isinstance(item, dict)
    }

    item_rows = []
    for item_id in range(1, total + 1):
        name = names_by_id.get(item_id, f"Item {item_id}")
        if item_id in filled_set:
            icon = "✅"
            row_class = "qc-filled"
            note = ""
        elif item_id in partial_by_id:
            icon = "🟡"
            row_class = "qc-partial"
            p = partial_by_id[item_id]
            reason = p.get("reason", "") or p.get("detail", "")
            note = (
                f' — <em class="qc-reason">данные недоступны (частично): '
                f'{_esc(str(reason))}</em>'
                if reason else
                ' — <em class="qc-reason">данные недоступны (частично)</em>'
            )
        elif item_id in not_applicable_by_id:
            # Plan 03-05 / D-08: not-applicable item (e.g., item 5
            # Instagram for non-critical niche). Sourced from
            # metadata["not_applicable_items"] — canonical field
            # populated by Plan 03-06 _apply_niche_conditional_coverage.
            # Distinct styling: ⚪ icon, gray, opacity 0.6.
            icon = "⚪"
            row_class = "qc-not-applicable"
            na = not_applicable_by_id[item_id]
            reason = na.get("reason", "") or na.get("detail", "")
            note = (
                f' — <em class="qc-reason">N/A для данной ниши: '
                f'{_esc(str(reason))}</em>'
                if reason else
                ' — <em class="qc-reason">N/A — не critical ниша</em>'
            )
        elif item_id in missing_by_id:
            icon = "❌"
            row_class = "qc-missing"
            m = missing_by_id[item_id]
            reason = m.get("reason", "") or m.get("detail", "")
            note = (
                f' — <em class="qc-reason">данные недоступны: '
                f'{_esc(str(reason))}</em>'
                if reason else
                ' — <em class="qc-reason">данные недоступны</em>'
            )
        else:
            # Item not evaluated — show as missing with generic note.
            icon = "❌"
            row_class = "qc-missing"
            note = ' — <em class="qc-reason">данные недоступны (не оценён)</em>'

        item_rows.append(
            f'<li class="qc-item {row_class}">'
            f'<span class="qc-icon">{icon}</span> '
            f'<strong>#{item_id}.</strong> {_esc(str(name))}{note}'
            f'</li>'
        )

    items_html = "\n".join(item_rows) if item_rows else "<li>(нет пунктов)</li>"

    # Plan 03-05 / D-08: summary line reflects Plan 03-06's effective
    # total (already adjusted — 14 for non-critical niches, 15 for critical).
    # When not_applicable_items is non-empty, append a note about the N/A
    # count so the client understands why total < 15.
    na_count = len(not_applicable_by_id)
    na_note = (
        f' · {na_count} item N/A (не critical ниша)'
        if na_count > 0 else ""
    )

    section_style = """
<style>
.qc-coverage-section {
  margin-top: 3rem;
  padding: 1.5rem;
  border-radius: 8px;
  background: var(--glass-bg, rgba(255,255,255,0.5));
  border: 1px solid var(--border, #E0E0E0);
}
[data-theme="dark"] .qc-coverage-section {
  background: rgba(201,169,110,0.05);
  border-color: rgba(201,169,110,0.18);
}
.qc-coverage-section h2 { margin-top: 0; }
.qc-summary {
  font-size: 1.1rem;
  margin: 1rem 0;
  font-family: var(--font-display, 'Playfair Display', serif);
}
.qc-items-list {
  list-style: none;
  padding: 0;
  margin: 1rem 0 0 0;
}
.qc-items-list li {
  padding: 0.6rem 0;
  border-bottom: 1px solid var(--border, rgba(0,0,0,0.05));
  line-height: 1.5;
}
[data-theme="dark"] .qc-items-list li {
  border-bottom-color: rgba(201,169,110,0.10);
}
.qc-icon { display: inline-block; width: 1.5em; }
.qc-reason { color: var(--text-dim, #6d6d6d); font-style: italic; }
/* Plan 03-05 / D-08: not-applicable items rendered with reduced emphasis. */
.qc-not-applicable {
  color: var(--text-dim, #888);
  opacity: 0.6;
}
.qc-not-applicable .qc-icon { color: #aaa; }
[data-theme="dark"] .qc-not-applicable .qc-icon { color: #888; }
.metric-tag {
  display: inline-block;
  padding: 0.15rem 0.6rem;
  border-radius: 4px;
  font-size: 0.75rem;
  font-weight: 600;
  letter-spacing: 0.05em;
  text-transform: uppercase;
  margin-left: 0.5rem;
  vertical-align: middle;
}
.metric-tag-success { background: #2e7d32; color: #fff; }
.metric-tag-warning { background: #e65100; color: #fff; }
[data-theme="dark"] .metric-tag-success { background: #66bb6a; color: #0d0d0d; }
[data-theme="dark"] .metric-tag-warning { background: #ff9800; color: #0d0d0d; }
</style>
"""

    return f"""{section_style}
<section class="section qc-coverage-section" data-aim="qc-coverage">
  <span class="section-label">QC Coverage Report</span>
  <h2>QC Coverage Report</h2>
  <p class="qc-summary">
    QC Coverage: {len(filled_ids)}/{total} ({pct_str}) — {badge}{na_note}
  </p>
  <p class="text-meta">
    Каждый пункт presale-чеклиста (15 пунктов) оценивается: собраны ли данные,
    частично собраны, или данные недоступны. Прозрачность = доверие (ORC-04).
  </p>
  <ul class="qc-items-list">
{items_html}
  </ul>
</section>
<hr>
"""


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


# Per Phase 2 P0 fix — RESEARCH.md Section 5.3 (NameError broke 40% of HTML BUILD phases)
def _unwrap_tool_output(phase_data: dict) -> dict | None:
    """Try to extract tool output from phase_data when tool_name key is missing.

    Phase data is stored as ``{tool_name: json_string}`` but sometimes the
    expected tool_name key is absent.  This function walks all values in
    phase_data, tries to parse each as JSON, and returns the first valid
    non-error dict it finds — or None if nothing useful is present.
    """
    if not isinstance(phase_data, dict):
        return None
    for val in phase_data.values():
        parsed = _parse_tool_value(val)
        if parsed is not None:
            return parsed
    return None


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

    # ── Phase → tool → expected key mapping (v8 phase names) ──────
    _phase_tool_map = {
        "PERPLEXITY": {
            "perplexity_search": "market_research",
        },
        "COMPETITORS": {
            "find_competitors": "competitors",
            "run_ci_analysis": "ci_analysis",
        },
        "TECH AUDIT": {
            "run_pagespeed": "pagespeed",
            "run_tech_seo_audit": "seo_audit",
        },
        "SOCIAL VERIFIER": {
            "run_review_platforms": "review_platforms",
        },
        "CONTENT ANALYSIS": {
            "run_content_analysis": "content_analysis",
        },
        "KEY PERSONS": {
            "find_doctor_handles": "doctor_dossiers",
            "run_instagram_content": "instagram_content",
        },
        "HIRING SIGNALS": {
            "run_hh_analysis": "hh_analysis",
        },
        "SMI MENTIONS": {
            "run_smi_mentions": "smi_mentions",
        },
        "FORUM PAINS": {
            "web_search": "forum_pains",
        },
        "FINANCE": {
            "find_company_financials": "financials",
        },
        "CONTENT PLAN": {
            "run_content_gaps": "content_gaps",
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
    if "COMPETITORS" in data and not data.get("ci_analysis"):
        comp = data["COMPETITORS"]
        if isinstance(comp, dict) and "run_ci_analysis" in comp:
            parsed = _parse_tool_value(comp["run_ci_analysis"])
            if parsed is not None:
                data["ci_analysis"] = parsed

    # ── Transform reviews from platforms[] → {platform: {rating, count}} ─
    for review_key in ("review_platforms", "SOCIAL VERIFIER", "SOCIAL: CROSS-PLATFORM", "RATINGS & REVIEWS"):
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


# ── Phase 5 / INT-04 + INT-05: HTML helpers for narrative extras ────────


def _render_gap_blocks(gap_blocks: list | None) -> str:
    """Render a list of gap-block dicts as design-system HTML.

    Per Phase 5 D-07 — unified gap-block format across all sections.
    Matches reference ``ИПХиК (2).html`` ``.gap`` CSS class pattern.

    Each gap-block dict shape::

        {
            "type": "strength" | "growth",  # strength=green border, growth=default
            "title": str,                   # e.g., "Сильная сторона: масштаб"
            "description": str,             # 1-3 sentences with numbers
        }

    Args:
        gap_blocks: List of gap-block dicts from LLM (Pass 3 item 19 kwarg).

    Returns:
        HTML string with ``.gap`` divs. Empty string on None/empty list.
        List capped to 5 items max (DoS mitigation per T-05-02-D).
        All text XSS-escaped via ``_esc``.
    """
    if not gap_blocks:
        return ""

    blocks = gap_blocks[:5]  # DoS cap — top 5 only
    parts = []
    for block in blocks:
        if not isinstance(block, dict):
            continue
        btype = str(block.get("type", "growth")).lower()
        title = _esc(str(block.get("title", "")))
        description = _esc(str(block.get("description", "")))
        if not title and not description:
            continue
        if btype == "strength":
            style = "border-left: 3px solid var(--green);"
        else:
            style = ""  # default .gap class border
        # Note: build the complete style attribute as a local variable
        # OUTSIDE the f-string expression part. Python 3.11 forbids
        # backslash-escaped double quotes inside f-string expressions,
        # so we assemble the attribute string in a separate statement.
        if style:
            style_attr = ' style="' + style + '"'
        else:
            style_attr = ""
        parts.append(
            '<div class="gap"' + style_attr + ">"
            "<h4>" + title + "</h4>"
            "<p>" + description + "</p>"
            "</div>"
        )
    return "\n".join(parts)


def _render_section_insight(insight: str | None) -> str:
    """Render the main strategic insight as a section blockquote.

    Per Phase 5 D-09/D-10 — each section ends with a blockquote containing
    the 1-2 sentence main insight. Matches reference ``ИПХиК (2).html``
    blockquote pattern (border-left 2px solid).

    Args:
        insight: 1-2 sentence strategic insight from LLM (Pass 3 item 20
            kwarg).

    Returns:
        HTML string with ``<blockquote class="section-insight">`` element.
        Empty string on None/empty/non-str. Text XSS-escaped + truncated
        to 600 chars.
    """
    if not insight or not isinstance(insight, str):
        return ""

    text = insight.strip()
    if not text:
        return ""

    # DoS cap — 600 chars max (~80 tokens), enough for 2 Russian sentences
    if len(text) > 600:
        text = text[:597] + "..."

    # Assemble HTML without f-string expression nesting — avoids any
    # Python 3.11 backslash-in-f-string gotcha.
    escaped_text = _esc(text)
    return (
        '<blockquote class="section-insight" '
        'style="border-left: 2px solid var(--text); padding-left: 16px; '
        'margin: 24px 0;">' + escaped_text + '</blockquote>'
    )


def _build_report_html(
    data: dict,
    title: str,
    coverage_metadata: dict | None = None,
    niche: str = "unknown",
    instagram_data: dict | None = None,
    strategy_data: dict | None = None,
    offer_data: dict | None = None,
    whitefields_data: dict | None = None,
    experts_data: list | None = None,
    content_data: dict | None = None,
    section_insights: dict | None = None,
    section_gap_blocks: dict | None = None,
) -> str:
    """Build full HTML page from session archive data using AIM CSS classes.

    Supports both legacy prescan format (stage_1/2/3) and v7 pipeline format
    (PERPLEXITY, TECH AUDIT, SOCIAL VERIFIER, etc. as phase-name keys).

    Args:
        data: Session archive data (prescan + pipeline keys).
        title: Report title (falls back to client name / metadata).
        coverage_metadata: Optional CoverageReport-as-dict from the 3-pass
            orchestrator (Plan 02-03 / QC-03). When provided, a QC Coverage
            Report section is rendered at the end of the HTML. When None
            (PipelineEngine fallback path, ORC-05), no QC section appears —
            backward compatible.
        niche: Clinic niche verdict (Plan 03-02 mini-call). One of
            ``"plastic_surgery"``, ``"cosmetology"`` (Instagram-critical),
            ``"dental"``, ``"general_medicine"``, ``"other"``, or
            ``"unknown"`` (default — defensive). When niche is critical AND
            instagram_data is missing/empty, a "Instagram: данные
            недоступны" block (D-07) is appended to sections 03 (Experts)
            and 04 (Content Analysis).
        instagram_data: Optional run_instagram_content batch response from
            Pass 1 tool-call history. Used to determine the reason variant
            for the no-Instagram block: None → "no_account",
            ``analyzed_count == 0`` → "perplexity_outside_index". Absent
            for non-critical niches (block not rendered).
        strategy_data: Phase 4 / SEC-01 — LLM-generated Strategy section
            (5 directions). None when LLM didn't generate (section not
            rendered). Per Plan 04-05 item 7 contract.
        offer_data: Phase 4 / SEC-02 — LLM-generated Offer section (steps
            + CTA). None when LLM didn't generate. Per Plan 04-05 item 8.
        whitefields_data: Phase 4 / SEC-03 — LLM-assembled 4×4 matrix
            (4 categories × client + 3 competitors). None when LLM
            didn't generate. Per Plan 04-05 item 9.
        experts_data: Phase 4 / SEC-04 — list of merged expert dicts
            (site регалии + Instagram metrics via ``_merge_doctor_data``
            from Plan 04-02). None when LLM didn't merge. Per Plan 04-05
            item 10 contract. Renders as ENHANCED Experts section
            (existing Phase 3 Key Doctors section still renders).
        content_data: Phase 4 / SEC-05 — dict with ``doctor_analyses``
            (per-doctor Instagram content analysis) and ``patient_fears``
            (top-5 from forums). None when LLM didn't assemble. Per Plan
            04-05 item 11.
        section_insights: Phase 5 / INT-05 — dict mapping section_key →
            1-2 sentence strategic insight string (Pass 3 LLM item 20
            kwarg). Keys: strategy, offer, whitefields, experts, content,
            revenue-dynamics, media-urls, ratings, competitor-cards,
            about. When a key is absent, no insight blockquote rendered
            for that section (backward compatible).
        section_gap_blocks: Phase 5 / INT-04 — dict mapping section_key →
            list of gap-block dicts (Pass 3 LLM item 19 kwarg). Each
            gap-block: ``{"type": "strength"|"growth", "title": str,
            "description": str}``. Applied to 5 sections per reference
            HTML: strategy, offer, experts, content, ratings. Other
            sections silently ignore the kwarg.
    """
    data = _normalize_pipeline_keys(data)

    # Phase 5 / INT-04 + INT-05 — normalize optional narrative extras.
    # Defensive: callers may pass None, missing, or non-dict. Default {}.
    if not isinstance(section_insights, dict):
        section_insights = {}
    if not isinstance(section_gap_blocks, dict):
        section_gap_blocks = {}

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
    content_analysis = data.get("content_analysis", {}) or {}
    content_gaps = data.get("content_gaps", {}) or {}
    forum_pains = data.get("forum_pains", {}) or {}
    smi_mentions = data.get("smi_mentions", {}) or {}
    hh_analysis = data.get("hh_analysis", {}) or {}
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

    # Phase 4 / DAT-04: Clinic metrics block (revenue, profit, employees,
    # status, ОКВЭД humanized by LLM per D-21). Goes INSIDE the About
    # section when clinic_metrics is available; empty string otherwise.
    clinic_metrics_html = _build_clinic_metrics_block(
        financials,
        insight=section_insights.get("about"),
    )

    if metrics:
        metric_cards = ""
        for label, value in metrics[:8]:
            metric_cards += f"""<div class="metric"><div class="value">{value}</div><div class="label">{label}</div></div>\n"""
        sections.append(f"""<section class="section">
  <span class="section-label">Ключевые метрики</span>
  <h2>Обзор</h2>
  <div class="metrics">{metric_cards}</div>
  {clinic_metrics_html}
</section>
<hr>""")
    elif clinic_metrics_html:
        # Clinic metrics available but no executive-summary metrics —
        # still render the About section with just the clinic metrics.
        sections.append(f"""<section class="section">
  <span class="section-label">Ключевые метрики</span>
  <h2>Обзор</h2>
  {clinic_metrics_html}
</section>
<hr>""")

    # ── Phase 4 / DAT-01: Revenue dynamics section ──────────────────────
    # Rendered AFTER About, BEFORE Market — matches reference report order
    # (section 1 About → section 1b Revenue dynamics → section 2 Market).
    sections.append(_build_revenue_dynamics_section(
        financials,
        insight=section_insights.get("revenue-dynamics"),
    ))

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

    # ── Phase 4 / DAT-03: Competitor cards (detailed) ──────────────────
    # Rendered AFTER existing competitor table + CI Analysis sections.
    # The existing _build_competitor_table stays as summary view; this
    # section adds detail per D-20 (year, revenue, trend, surgeons,
    # Instagram, specialization). Empty string when competitor_cards
    # is absent (graceful degradation).
    competitor_cards_data = competitors if isinstance(competitors, dict) else {}
    # Also check ci_analysis as a fallback source (LLM may populate
    # competitor_cards in either dict per Plan 04-05 item 9).
    if not competitor_cards_data.get("competitor_cards") and isinstance(ci_analysis, dict):
        if ci_analysis.get("competitor_cards"):
            competitor_cards_data = ci_analysis
    competitor_cards_html = _build_competitor_cards_section(
        competitor_cards_data,
        insight=section_insights.get("competitor-cards"),
    )
    if competitor_cards_html:
        sections.append(competitor_cards_html)

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
        # Phase 3 / D-07: append no-Instagram block to section 03 when
        # niche is critical AND instagram_data is unavailable. The block
        # explains why expert Instagram metrics are missing.
        no_ig_block_03 = _maybe_build_no_instagram_block(niche, instagram_data)
        sections.append(f"""<section class="section">
  <span class="section-label">Ключевые врачи</span>
  <h2>Специалисты</h2>
  <div class="grid-2">{doc_cards}</div>
  {no_ig_block_03}
</section>
<hr>""")

    # ── Phase 4 / DAT-02: Media URLs section ────────────────────────────
    # Rendered AFTER Key Doctors, BEFORE Presence/SEO section (matches
    # reference report order: section 05 Media). Empty string when
    # media_urls key is absent (graceful degradation for sessions that
    # didn't call run_media_urls).
    media_urls_html = _build_media_urls_section(
        data,
        insight=section_insights.get("media-urls"),
    )
    if media_urls_html:
        sections.append(media_urls_html)

    # ── PageSpeed ────────────────────────────────────────────────────────
    if pagespeed:
        # v7 format: {mobile: {performance_score, lcp, fcp, tbt, cls, si, tti}, desktop: {...}}
        # or legacy: {scores: {mobile: {...}}} or {assessment, scores, method}
        ps_scores = pagespeed.get("scores", {}) or {}
        mobile_ps = pagespeed.get("mobile", {}) or ps_scores.get("mobile", {}) or {}
        desktop_ps = pagespeed.get("desktop", {}) or ps_scores.get("desktop", {}) or {}
        if mobile_ps:
            mobile_score = mobile_ps.get("performance_score", "—")
            desktop_score = desktop_ps.get("performance_score", "—") if desktop_ps else "—"

            # Build metrics rows from available data
            metrics_rows = []
            cwv_metrics = [
                ("LCP (Largest Contentful Paint)", "lcp"),
                ("FCP (First Contentful Paint)", "fcp"),
                ("TBT (Total Blocking Time)", "tbt"),
                ("CLS (Cumulative Layout Shift)", "cls"),
                ("SI (Speed Index)", "si"),
                ("TTI (Time to Interactive)", "tti"),
            ]
            for label, key in cwv_metrics:
                m_val = mobile_ps.get(key, "")
                d_val = desktop_ps.get(key, "") if desktop_ps else ""
                if m_val or d_val:
                    metrics_rows.append(f"<tr><td>{_esc(label)}</td><td>{_esc(str(m_val or '—'))}</td><td>{_esc(str(d_val or '—'))}</td></tr>")

            metrics_table = ""
            if metrics_rows:
                metrics_table = f"""<div class="table-wrap">
  <table>
    <tr><th>Метрика</th><th>Mobile</th><th>Desktop</th></tr>
    {''.join(metrics_rows)}
  </table>
  </div>"""

            sections.append(f"""<section class="section">
  <span class="section-label">Core Web Vitals</span>
  <h2>Скорость сайта</h2>
  <div class="metrics">
    <div class="metric"><div class="value">{_esc(str(mobile_score))}</div><div class="label">Performance (Mobile)</div></div>
    <div class="metric"><div class="value">{_esc(str(desktop_score))}</div><div class="label">Performance (Desktop)</div></div>
  </div>
  {metrics_table}
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

    # ── Content Analysis ─────────────────────────────────────────────────
    ca_analysis = content_analysis.get("analysis", "")
    ca_content_type = content_analysis.get("content_type", "")
    if ca_analysis:
        # Split markdown into sections for rendering
        ca_sections_html = ""
        ca_parts = ca_analysis.split("### ")
        for part in ca_parts:
            part = part.strip()
            if not part:
                continue
            lines = part.split("\n", 1)
            heading = lines[0].strip()
            body = lines[1].strip() if len(lines) > 1 else ""
            # Convert **bold** markers, truncate very long sections
            body_display = body[:1200]
            if len(body) > 1200:
                body_display += "\n\n…"
            ca_sections_html += f"""<div class="surface-card">
  <h4>{_esc(heading)}</h4>
  <div class="text-dim" style="white-space:pre-wrap;">{_esc(body_display)}</div>
</div>\n"""

        # Phase 3 / D-07: append no-Instagram block to section 04 when
        # niche is critical AND instagram_data is unavailable. The block
        # explains why content analysis cannot use Instagram metrics.
        no_ig_block_04 = _maybe_build_no_instagram_block(niche, instagram_data)
        sections.append(f"""<section class="section">
  <span class="section-label">Контент</span>
  <h2>Контент-анализ сайта</h2>
  {f'<p class="text-meta">Тип анализа: {_esc(ca_content_type)}</p>' if ca_content_type else ''}
  <div class="grid-1">{ca_sections_html}</div>
  {no_ig_block_04}
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

    # ── Content Plan ─────────────────────────────────────────────────────
    cg_topics = content_gaps.get("topic_details") or {}
    if not cg_topics:
        cg_topics = content_gaps.get("topics", {}) or {}
    cg_list = content_gaps.get("gaps") or content_gaps.get("recommendations") or []
    cg_analyzed = content_gaps.get("topics_analyzed", 0)
    cg_covered = content_gaps.get("topics_covered_by_client", 0)
    cg_uncovered = content_gaps.get("topics_uncovered", 0)

    if cg_topics or cg_list:
        cg_html = ""

        # Summary metrics
        if cg_analyzed:
            cg_html += f"""<div class="metrics">
  <div class="metric"><div class="value">{_esc(str(cg_analyzed))}</div><div class="label">Тем проанализировано</div></div>
  <div class="metric"><div class="value" style="color:var(--green,#2e7d32)">{_esc(str(cg_covered))}</div><div class="label">Покрыто</div></div>
  <div class="metric"><div class="value" style="color:var(--red,#c62828)">{_esc(str(cg_uncovered))}</div><div class="label">Не покрыто</div></div>
</div>\n"""

        # Topic details table
        if cg_topics:
            topic_rows = ""
            for topic_name, tdata in sorted(cg_topics.items()):
                covered = tdata.get("client_has_content", False)
                comp_has = tdata.get("competitor_has_content", False)
                status_icon = "✅" if covered else "❌"
                comp_icon = "✅" if comp_has else "—"
                topic_rows += f"<tr><td>{status_icon}</td><td>{_esc(topic_name)}</td><td>{comp_icon}</td></tr>\n"
            cg_html += f"""<div class="table-wrap">
  <table>
    <tr><th></th><th>Тема</th><th>Есть у конкурентов</th></tr>
    {topic_rows}
  </table>
  </div>\n"""

        # Legacy gaps list
        if cg_list and not cg_topics:
            for cg in cg_list[:8]:
                desc = cg if isinstance(cg, str) else cg.get("description", str(cg))
                cg_html += f'<div class="surface-card"><p>{_esc(str(desc))}</p></div>\n'

        sections.append(f"""<section class="section">
  <span class="section-label">Контент</span>
  <h2>Контент-план</h2>
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

    # ── Phase 4 / DAT-05: Ratings section (extracted by Pass 3 LLM) ─────
    # Renders structured ratings (ПроДокторов + Яндекс.Карты minimum per
    # D-22) when Pass 3 LLM populated reviews["ratings_extracted"].
    # Empty string when ratings_extracted is absent — graceful degradation.
    ratings_html = _build_ratings_section(
        reviews,
        insight=section_insights.get("ratings"),
        gap_blocks=section_gap_blocks.get("ratings"),
    )
    if ratings_html:
        sections.append(ratings_html)

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

    # ── Phase 4 / SEC-04: Enhanced Experts with регалии ───────────────
    # Renders top-5 experts with structured регалии (КМН/ДМН/профессор/
    # доцент) + Instagram metrics, handles source variants (both/site/
    # instagram_only). Existing Phase 3 Key Doctors section still renders
    # above; this ENHANCES with regalia + merged data. Empty string when
    # experts_data is absent (backward compatible).
    if experts_data:
        experts_enhanced_html = _build_experts_with_regalia(
            experts_data,
            insight=section_insights.get("experts"),
            gap_blocks=section_gap_blocks.get("experts"),
        )
        if experts_enhanced_html:
            sections.append(experts_enhanced_html)

    # ── Phase 4 / SEC-05: Enhanced Content Analysis with patient fears ─
    # Per-doctor content analysis + top-5 patient fears with mention
    # counts. Existing Phase 3 Content Analysis section still renders
    # above; this ENHANCES with fears + per-doctor depth. Empty string
    # when content_data is absent (backward compatible).
    if content_data:
        content_enhanced_html = _build_content_analysis_with_fears(
            content_data,
            insight=section_insights.get("content"),
            gap_blocks=section_gap_blocks.get("content"),
        )
        if content_enhanced_html:
            sections.append(content_enhanced_html)

    # ── Phase 4 / SEC-03: Whitefields matrix (LLM-assembled) ──────────
    # Rendered BEFORE Strategy (reference position 07). 4×4 matrix:
    # 4 categories (Услуги/Цены/Врачи/Digital) × client + 3 competitors.
    # Empty string when whitefields_data is absent (backward compatible).
    whitefields_html = _build_whitefields_matrix(
        whitefields_data,
        insight=section_insights.get("whitefields"),
    )
    if whitefields_html:
        sections.append(whitefields_html)

    # ── Phase 4 / SEC-01: Strategy section (LLM-generated) ─────────────
    # Rendered near the END (after data sections, before CTA) — matches
    # reference report position 09. Empty string when strategy_data is
    # absent (graceful degradation — backward compatible with Phase 3).
    strategy_html = _build_strategy_section(
        strategy_data,
        insight=section_insights.get("strategy"),
        gap_blocks=section_gap_blocks.get("strategy"),
    )
    if strategy_html:
        sections.append(strategy_html)

    # ── Phase 4 / SEC-02: Offer section (LLM-generated) ────────────────
    # Rendered AFTER Strategy (reference position 10). Empty string when
    # offer_data is absent (backward compatible).
    offer_html = _build_offer_section(
        offer_data,
        insight=section_insights.get("offer"),
        gap_blocks=section_gap_blocks.get("offer"),
    )
    if offer_html:
        sections.append(offer_html)

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
    # ── QC Coverage section (optional, Plan 02-03 / QC-03) ──────────────
    # Appended AFTER all data sections but BEFORE the closing </div> of the
    # report container. Empty string when no coverage_metadata supplied —
    # preserves backward compatibility for the PipelineEngine path (ORC-05).
    qc_section = ""
    if coverage_metadata is not None:
        qc_section = _build_qc_coverage_section(coverage_metadata)

    return (
        comp_table_styles
        + '<meta name="robots" content="noindex, nofollow">\n<div data-aim="report">\n'
        + "\n".join(sections)
        + '\n'
        + qc_section
        + '\n</div>'
    )


def _random_slug(length: int = 8) -> str:
    chars = string.ascii_lowercase + string.digits
    return "".join(random.choices(chars, k=length))


def _md_to_styled_html(md: str, title: str, client_url: str | None = None,
                        client_name: str | None = None) -> str:
    """Convert LLM-generated markdown narrative to AIM-styled HTML report.

    Phase 7 final fix: LLM produces excellent markdown but can't structure
    into 10 separate kwargs. This wraps markdown in proper AIM design-system
    HTML so the output matches reference quality.
    """
    import html as html_module
    from datetime import datetime

    # ── Convert markdown to HTML (minimal renderer — no markdown lib needed) ──
    lines = md.split("\n")
    body_parts: list[str] = []
    in_list: list[str] = []
    in_table = False
    table_rows: list[str] = []

    def flush_list():
        nonlocal in_list
        if in_list:
            body_parts.append("<ul>" + "".join(f"<li>{_esc_md(li)}</li>" for li in in_list) + "</ul>")
            in_list = []

    def flush_table():
        nonlocal in_table, table_rows
        if table_rows:
            rows_html = []
            for i, row in enumerate(table_rows):
                cells = [c.strip() for c in row.split("|") if c.strip() or True][1:-1]
                if not cells:
                    continue
                tag = "th" if i == 0 else "td"
                rows_html.append("<tr>" + "".join(f"<{tag}>{_esc_md(c)}</{tag}>" for c in cells) + "</tr>")
            if rows_html:
                body_parts.append('<table class="md-table">' + "".join(rows_html) + "</table>")
        in_table = False
        table_rows = []

    def _esc_md(text: str) -> str:
        # Inline markdown: **bold**, *italic*, `code`, [link](url)
        s = html_module.escape(text, quote=False)
        s = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", r'<a href="\2">\1</a>', s)
        s = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", s)
        s = re.sub(r"`([^`]+)`", r"<code>\1</code>", s)
        s = re.sub(r"\*([^*]+)\*", r"<em>\1</em>", s)
        return s

    for line in lines:
        stripped = line.rstrip()
        # Headers
        if stripped.startswith("### "):
            flush_list(); flush_table()
            body_parts.append(f'<h3>{_esc_md(stripped[4:])}</h3>')
        elif stripped.startswith("## "):
            flush_list(); flush_table()
            body_parts.append(f'<h2>{_esc_md(stripped[3:])}</h2>')
        elif stripped.startswith("# "):
            flush_list(); flush_table()
            body_parts.append(f'<h1>{_esc_md(stripped[2:])}</h1>')
        elif stripped.startswith("---"):
            flush_list(); flush_table()
            body_parts.append("<hr>")
        elif stripped.startswith("|") and stripped.endswith("|"):
            flush_list()
            table_rows.append(stripped)
            in_table = True
        elif re.match(r"^\s*[-*]\s+", stripped):
            flush_table()
            item = re.sub(r"^\s*[-*]\s+", "", stripped)
            in_list.append(item)
        elif stripped.strip() == "":
            flush_list(); flush_table()
        else:
            flush_list(); flush_table()
            body_parts.append(f"<p>{_esc_md(stripped)}</p>")

    flush_list(); flush_table()

    body_html = "\n".join(body_parts)
    today = datetime.now().strftime("%d.%m.%Y")
    clinic_line = client_url or client_name or ""

    return f"""<!DOCTYPE html>
<html lang="ru" data-theme="light">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<meta name="robots" content="noindex, nofollow">
<title>{html_module.escape(title)} — AIM</title>
<style>
:root {{
  --bg: #ffffff; --text: #1A1A1A; --text-dim: #888; --accent: #1A1A1A;
  --border: #E0E0E0; --glass-bg: rgba(255,255,255,0.85);
  --font-head: 'Playfair Display', Georgia, serif;
  --font-body: 'Jost', system-ui, sans-serif;
}}
[data-theme="dark"] {{
  --bg: #0d0d0d; --text: #f5f0e8; --text-dim: #888; --accent: #c9a96e;
  --border: rgba(201,169,110,0.18); --glass-bg: rgba(13,13,13,0.85);
}}
* {{ box-sizing: border-box; margin: 0; padding: 0; }}
body {{
  font-family: var(--font-body); background: var(--bg); color: var(--text);
  line-height: 1.7; padding: 2rem 1rem; max-width: 880px; margin: 0 auto;
}}
h1, h2, h3 {{ font-family: var(--font-head); font-weight: 400; margin: 2rem 0 1rem; letter-spacing: -0.01em; }}
h1 {{ font-size: 2.2rem; margin-top: 0; }}
h2 {{ font-size: 1.6rem; border-bottom: 1px solid var(--border); padding-bottom: 0.5rem; }}
h3 {{ font-size: 1.2rem; color: var(--text-dim); }}
p {{ margin: 0.8rem 0; }}
hr {{ border: none; border-top: 1px solid var(--border); margin: 2rem 0; }}
ul {{ padding-left: 1.5rem; margin: 0.8rem 0; }}
li {{ margin: 0.3rem 0; }}
strong {{ font-weight: 600; }}
em {{ font-style: italic; }}
code {{ background: var(--glass-bg); padding: 0.1rem 0.4rem; font-size: 0.9em; border-radius: 3px; }}
a {{ color: var(--accent); text-decoration: underline; }}
.md-table {{ width: 100%; border-collapse: collapse; margin: 1.5rem 0; font-size: 0.95rem; }}
.md-table th, .md-table td {{
  padding: 0.7rem 0.9rem; border-bottom: 1px solid var(--border); text-align: left; vertical-align: top;
}}
.md-table th {{ font-weight: 500; text-transform: uppercase; font-size: 0.75rem; letter-spacing: 0.05em; color: var(--text-dim); }}
.md-table tr:hover {{ background: var(--glass-bg); }}
.hero {{
  background: var(--glass-bg); padding: 2rem; border-radius: 4px; margin-bottom: 2rem;
  border-left: 3px solid var(--accent);
}}
.hero h1 {{ margin-top: 0; }}
.section-label {{
  font-size: 0.7rem; text-transform: uppercase; letter-spacing: 0.15em;
  color: var(--text-dim); margin-bottom: 0.5rem;
}}
.meta {{ font-size: 0.85rem; color: var(--text-dim); margin-top: 0.5rem; }}
@media (max-width: 600px) {{ body {{ padding: 1rem 0.5rem; }} h1 {{ font-size: 1.7rem; }} }}
</style>
</head>
<body>
<div class="hero">
  <div class="section-label">AIM Research Report</div>
  <h1>{html_module.escape(title)}</h1>
  <div class="meta">{html_module.escape(clinic_line)} · {today}</div>
</div>
{body_html}
</body>
</html>"""



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

    Per Phase 2 QC-03: optional ``coverage_metadata`` parameter triggers
    rendering of the QC Coverage section at the end of the HTML report.
    When omitted (PipelineEngine fallback path, ORC-05), no QC section
    appears — backward compatible.

    Per ORC-04: missing items in the QC section are displayed with
    "данные недоступны" + reason — never fabricated.

    The coverage_metadata value is read from kwargs (or from the args dict
    if the LLM passed a single dict as the first positional argument).
    Expected shape: ``dataclasses.asdict(CoverageReport)`` — keys
    ``total_items``, ``filled_items``, ``missing_items``, ``partial_items``,
    ``coverage_pct``, ``status``.

    Per Phase 3 / D-07 (Plan 03-05): optional ``niche`` and
    ``instagram_data`` kwargs trigger conditional rendering of the
    "Instagram: данные недоступны" block in sections 03 + 04 when niche
    is critical AND instagram_data is missing/empty. ``niche`` defaults
    to ``"unknown"`` (defensive — block is not rendered for unknown
    niches). ``instagram_data`` defaults to None. The Pass 3 prompt
    (Plan 03-05 Task 3) instructs the LLM to pass both kwargs.

    Per Phase 4 / SEC-01..02 (Plan 04-07): optional ``strategy_data``
    and ``offer_data`` kwargs trigger rendering of the LLM-generated
    Strategy and Offer sections. None when LLM didn't generate (sections
    not rendered — backward compatible with Phase 3 callers).

    Per Phase 4 / SEC-03 (Plan 04-07): optional ``whitefields_data``
    kwarg triggers rendering of the LLM-assembled 4×4 Whitefields matrix.
    None when LLM didn't assemble (section not rendered).

    Per Phase 4 / SEC-04..05 (Plan 04-07): optional ``experts_data``
    (list) and ``content_data`` (dict) kwargs trigger rendering of the
    enhanced Experts (with регалии + Instagram metrics) and Content
    Analysis (with patient fears) sections. None when LLM didn't
    assemble — sections not rendered.
    """
    # Optional: coverage_metadata for QC Coverage section (Plan 02-03 / QC-03)
    coverage_metadata = kwargs.get("coverage_metadata")
    # Optional: niche + instagram_data for D-07 no-Instagram block (Plan 03-05)
    niche = kwargs.get("niche") or "unknown"
    instagram_data = kwargs.get("instagram_data")
    # Optional: strategy + offer for Phase 4 LLM-generated sections (Plan 04-07)
    strategy_data = kwargs.get("strategy_data")
    offer_data = kwargs.get("offer_data")
    # Optional: whitefields matrix (Plan 04-07 Task 2)
    whitefields_data = kwargs.get("whitefields_data")
    # Optional: enhanced experts + content (Plan 04-07 Task 3)
    experts_data = kwargs.get("experts_data")
    content_data = kwargs.get("content_data")
    # Optional: Phase 5 narrative extras (Plan 05-02) — per-section insight
    # and gap_blocks dicts generated by Pass 3 LLM (items 19 + 20).
    section_insights = kwargs.get("section_insights")
    section_gap_blocks = kwargs.get("section_gap_blocks")
    # Phase 7 final fix: narrative_md lets LLM pass full markdown report
    # directly when structured kwargs are too hard. HTML renderer wraps it.
    narrative_md = kwargs.get("narrative_md") or kwargs.get("report_markdown") or kwargs.get("narrative")

    if isinstance(session_hash, dict):
        d = session_hash
        session_hash = d.get("session_hash", "")
        title = title or d.get("title", "")
        client_name = client_name or d.get("client_name", "")
        client_url = client_url or d.get("client_url", "")
        # If coverage_metadata wasn't passed as kwarg, try the args dict.
        if coverage_metadata is None:
            coverage_metadata = d.get("coverage_metadata")
        # Same fallback for niche + instagram_data (Plan 03-05).
        if not niche or niche == "unknown":
            niche = d.get("niche") or "unknown"
        if instagram_data is None:
            instagram_data = d.get("instagram_data")
        # Same fallback for strategy + offer + whitefields + experts + content.
        if strategy_data is None:
            strategy_data = d.get("strategy_data")
        if offer_data is None:
            offer_data = d.get("offer_data")
        if whitefields_data is None:
            whitefields_data = d.get("whitefields_data")
        if experts_data is None:
            experts_data = d.get("experts_data")
        if content_data is None:
            content_data = d.get("content_data")
        # Same fallback for Phase 5 narrative extras.
        if section_insights is None:
            section_insights = d.get("section_insights")
        if section_gap_blocks is None:
            section_gap_blocks = d.get("section_gap_blocks")
        if not narrative_md:
            narrative_md = d.get("narrative_md") or d.get("report_markdown") or d.get("narrative")

    if not session_hash:
        # Phase 7 orchestrator mode: LLM passes all data directly as kwargs,
        # no session archive to read from. Build minimal data dict from kwargs.
        session_hash = "inline-" + (client_name or client_url or "report").replace(" ", "-")[:40]
        data = {"metadata": {}, "collected_data": {}}
    else:
        # Load all data from session archive
        data = load_all_data(session_hash)

    report_title = title or client_name or "AIM Scout Report"

    # Merge metadata overrides
    meta = data.get("metadata", {}) or {}
    if client_name:
        meta["company_name"] = client_name
    if client_url:
        meta["url"] = client_url

    # Generate HTML. coverage_metadata is optional — when None, no QC
    # Coverage section is rendered (preserves PipelineEngine backward compat).
    # niche + instagram_data (Plan 03-05) are optional — when absent, no
    # Instagram block is rendered (backward compatible with Phase 2 callers).
    # strategy_data + offer_data + whitefields_data + experts_data +
    # content_data (Plan 04-07) are optional — when absent, those sections
    # are not rendered (backward compatible with Phase 3 callers).
    html = _build_report_html(
        data,
        report_title,
        coverage_metadata=coverage_metadata,
        niche=niche,
        instagram_data=instagram_data,
        strategy_data=strategy_data,
        offer_data=offer_data,
        whitefields_data=whitefields_data,
        experts_data=experts_data,
        content_data=content_data,
        section_insights=section_insights,
        section_gap_blocks=section_gap_blocks,
    )

    # Phase 7 final fix: if LLM passed narrative_md (full markdown report),
    # inject it as the main content body. This handles the case where LLM
    # generates excellent narrative but can't structure it into 10 separate kwargs.
    if narrative_md and isinstance(narrative_md, str) and len(narrative_md) > 200:
        try:
            narrative_html = _md_to_styled_html(narrative_md, report_title, client_url, client_name)
            if narrative_html and len(narrative_html) > 500:
                html = narrative_html
                logger.info("generate_html_report: using narrative_md (%d chars) as report body",
                            len(narrative_md))
        except Exception as exc:
            logger.warning("generate_html_report: narrative_md conversion failed: %s", exc)


    # Publish to WordPress
    if not WP_DB_PASSWORD:
        # Save locally if no DB access
        sessions_root = os.getenv("SESSIONS_ROOT", "/opt/data/sessions-archive")
        report_dir = os.path.join(sessions_root, session_hash)
        os.makedirs(report_dir, exist_ok=True)
        report_path = os.path.join(report_dir, "report.html")
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
                    "narrative_md": {
                        "type": "string",
                        "description": "ПОЛНЫЙ ОТЧЁТ В MARKDOWN (рекомендуемый способ). Вся сгенерированная разведка как markdown-строка: заголовки ## (01-10 секции), таблицы, gap-блоки (✅/📍), blockquotes. Рендерер сконвертирует в styled HTML. Это ПРЕДПОЧТИТЕЛЬНЕЕ чем передавать 10 отдельных kwargs.",
                    },
                },
                "required": ["client_url", "narrative_md"],
            },
        },
    handler=handle_generate_html_report,
    check_fn=lambda: True,
    is_async=True,
    description="Generate and publish AIM design system HTML report from session archive data",
    emoji="📊",
)
