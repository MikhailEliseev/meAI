"""Сборка финального HTML-отчёта — v2 (дизайн-система + эталон ИПХиК).

Новая структура отчёта:
  - <style> с canonical CSS (Inter + Playfair, dual theme)
  - .aim-report-scope (вся страница)
    - .water-ripples (6 origin × 5 колец = анимация «круги на воде»)
    - .report-nav (sticky, логотип + ссылки + theme-toggle)
    - .report-container
      - .hero (label + h1 с <em>подзаголовком</em> + subtitle + meta)
      - revenue-block (вау-блок «Выручка vs Конкуренты»)
      - .section × N (section-label + h2 + interpretation)
      - .cta-box (CTA с кнопкой)
      - .report-footer
"""

import json
import re

from app.report_builder.css import _CANONICAL_CSS, get_fonts_import
from app.report_builder.markdown_engine import _esc, _interpretation_to_html
from app.report_builder.revenue_block import build_revenue_vs_competitors_block


# phase_order: (phase_key, section_id, nav_label, default_h2)
_PHASE_ORDER = [
    ("PROFILE",     "sec-profile",     "О клинике",     "Профиль клиники"),
    ("OVERVIEW",    "sec-overview",    "Рынок",         "Обзор рынка и тенденции"),
    ("COMPETITORS", "sec-competitors", "Конкуренты",    "Конкуренты и сравнение"),
    ("REVIEWS",     "sec-reviews",     "Отзывы",        "Отзывы пациентов"),
]


def _extract_client_financials(data: dict) -> tuple[float | None, float | None]:
    """Извлечь client_revenue и client_profit из data["FINANCE"]."""
    fin_phase = data.get("FINANCE", {})
    if not isinstance(fin_phase, dict):
        return None, None
    fin_raw = fin_phase.get("find_company_financials", "")
    if not isinstance(fin_raw, str) or not fin_raw:
        return None, None
    try:
        fin = json.loads(fin_raw)
    except (json.JSONDecodeError, TypeError):
        return None, None
    comp = fin.get("company", {}) if isinstance(fin, dict) else {}
    revenue = comp.get("latest_revenue")
    profit = comp.get("latest_profit")
    rev_f = float(revenue) if revenue is not None else None
    profit_f = float(profit) if profit is not None else None
    return rev_f, profit_f


def _build_ripple_html() -> str:
    """Построить HTML для анимации «круги на воде».

    6 origin × 5 колец в каждом = 30 ripple-ring элементов.
    Анимация полностью на GPU (transform: scale) через CSS — не вызывает
    repaint других элементов (в отличие от width/height анимации).
    """
    origins = []
    for i in range(1, 7):
        rings = "".join(['<div class="ripple-ring"></div>'] * 5)
        origins.append(
            f'<div class="ripple-origin ripple-origin-{i}">{rings}</div>'
        )
    return f'<div class="water-ripples" aria-hidden="true">{"".join(origins)}</div>'


def _build_nav_html(nav_sections: list[dict], company_name: str) -> str:
    """Шапка сайта iamaim.ru уже содержит кнопку переключения темы.

    Возвращаем пустую строку — не дублируем toggle. Тема отчёта синхронизирована
    с темой сайта через CSS (html[data-theme="dark"] → .aim-report-scope).
    """
    return ""


def _build_hero_html(data: dict, title: str) -> str:
    """Построить hero-секцию: label + h1 с подзаголовком + subtitle + meta.

    Структура вдохновлена эталоном ИПХиК.html.
    """
    meta = data.get("metadata", {}) or {}
    hero_meta = data.get("hero_meta", {}) or {}
    company_name = meta.get("company_name") or title

    # Подзаголовок h1 <em>: короткая характеристика (subtitle из hero_meta)
    subtitle_text = hero_meta.get("subtitle", "") or "Маркетинговый аудит и точки роста"

    # meta-строка: город, врачи, год, рейтинг
    meta_items: list[str] = []
    city = hero_meta.get("city", "")
    address = hero_meta.get("address", "")
    if city and address:
        meta_items.append(f"📍 {_esc(city)}, {_esc(address)}")
    elif city:
        meta_items.append(f"📍 {_esc(city)}")

    doctors = hero_meta.get("doctors_count")
    if doctors:
        meta_items.append(f"🏥 {_doctors_emoji(doctors)} {_esc(str(doctors))} врачей")

    founded = hero_meta.get("founded_year", "")
    if founded:
        meta_items.append(f"📅 С {_esc(founded)}")

    rating = hero_meta.get("rating")
    if rating is not None:
        reviews_count = hero_meta.get("reviews_count")
        if reviews_count:
            meta_items.append(
                f'<span class="rating">⭐ {rating:.1f} ({_esc(str(reviews_count))} отзывов)</span>'
            )
        else:
            meta_items.append(f'<span class="rating">⭐ {rating:.1f}</span>')

    meta_html = "".join(f"<span>{m}</span>" for m in meta_items)

    return (
        '<div class="hero">'
        '<div class="label">AI MARKETING ANALYSIS</div>'
        f'<h1>{_esc(company_name)}<em>{_esc(subtitle_text)}</em></h1>'
        '<div class="subtitle">Полный разбор рынка, конкурентов, отзывов и '
        'цифрового присутствия. Ниже — что мы нашли, где вы сильны и где есть '
        'точки роста.</div>'
        f'<div class="meta">{meta_html}</div>'
        '</div>'
    )


def _doctors_emoji(count: int) -> str:
    """Эмодзи в зависимости от размера клиники."""
    if count >= 100:
        return "🏥"
    if count >= 20:
        return "👨‍⚕️"
    return "🩺"


def build_report_html(data: dict, title: str) -> str:
    """Собрать финальный HTML-отчёт из data dict.

    Args:
        data: dict в формате adapter.build_data_dict(). Ожидаемые ключи:
            - metadata: {company_name, url, inn}
            - hero_meta: {city, address, founded_year, doctors_count,
              rating, reviews_count, revenue_str, subtitle, nav_sections}
            - PROFILE_interp, OVERVIEW_interp, COMPETITORS_interp,
              REVIEWS_interp: {content, label}
            - FINANCE: {find_company_financials: <json>}
            - COMPETITORS: {find_competitors: <json>}

        title: Заголовок отчёта (fallback для company_name).

    Returns:
        Полный HTML-документ (CSS + разметка, wpautop-совместимый —
        каждый блочный элемент в одну строку).
    """
    meta = data.get("metadata", {}) or {}
    company_name = meta.get("company_name") or title
    hero_meta = data.get("hero_meta", {}) or {}
    nav_sections = hero_meta.get("nav_sections", []) or []

    # ── Секции (интерпретации) ────────────────────────────────────────────────
    phase_sections = []
    for phase_key, section_id, nav_label, default_h2 in _PHASE_ORDER:
        interp = data.get(f"{phase_key}_interp", {})
        if not isinstance(interp, dict):
            continue
        content = interp.get("content", "") or ""
        if not content.strip():
            continue
        label = interp.get("label") or default_h2

        # Markdown → HTML
        html_content = _interpretation_to_html(content)

        # section-label: "01 — О КЛИНИКЕ", "02 — РЫНОК", ...
        section_num = _PHASE_ORDER.index((phase_key, section_id, nav_label, default_h2)) + 1
        section_label = f"{section_num:02d} — {nav_label.upper()}"

        phase_sections.append(
            f'<section class="section" id="{section_id}">'
            f'<div class="section-label">{_esc(section_label)}</div>'
            f'<h2>{_esc(label)}</h2>'
            f'<div class="interpretation">{html_content}</div>'
            f'</section>'
        )

    # ── Revenue block ──────────────────────────────────────────────────────────
    client_revenue, client_profit = _extract_client_financials(data)

    competitors_result = ""
    comp_phase = data.get("COMPETITORS", {})
    if isinstance(comp_phase, dict):
        competitors_result = comp_phase.get("find_competitors", "") or ""

    revenue_block_html = build_revenue_vs_competitors_block(
        client_revenue=client_revenue,
        client_profit=client_profit,
        competitors_result=competitors_result,
        company_name=company_name,
    )

    # ── CTA ────────────────────────────────────────────────────────────────────
    cta_html = (
        '<div class="cta-box">'
        '<h2>Обсудить стратегию роста</h2>'
        '<p>Готовы внедрить рекомендации? Свяжитесь с нами для индивидуальной '
        'консультации и пошагового плана.</p>'
        '<a href="https://t.me/eliseev_me" class="btn-primary">Связаться в Telegram</a>'
        '</div>'
    )

    # ── Footer ─────────────────────────────────────────────────────────────────
    footer_html = (
        '<div class="report-footer">'
        '<div class="footer-logo">AIM</div>'
        '<div>Marketing Agency · Анализ и стратегия для медицинских клиник</div>'
        '<div style="margin-top:8px;">'
        '<a href="https://iamaim.ru">iamaim.ru</a> · '
        '<a href="https://t.me/eliseev_me">Telegram</a>'
        '</div>'
        '</div>'
    )

    # ── Сборка INNER HTML ──────────────────────────────────────────────────────
    # Каждый блочный элемент в одну строку (wpautop-safe для WordPress).
    def _flatten(html: str) -> str:
        """Свернуть многострочный HTML в одну строку (wpautop-safe)."""
        return re.sub(r'\s+', ' ', html).strip()

    nav_html = _build_nav_html(nav_sections, company_name)
    ripple_html = _build_ripple_html()
    hero_html = _build_hero_html(data, title)
    sections_html = "".join(phase_sections)

    body_inner = (
        ripple_html
        + nav_html
        + '<div class="report-container">'
        + hero_html
        + (_flatten(revenue_block_html) if revenue_block_html else "")
        + _flatten(sections_html)
        + _flatten(cta_html)
        + _flatten(footer_html)
        + '</div>'
    )

    # ── CSS (минифицированный) ────────────────────────────────────────────────
    css_minified = re.sub(r'\s+', ' ', _CANONICAL_CSS).strip()
    fonts = get_fonts_import()

    # ── Финальная сборка ──────────────────────────────────────────────────────
    # Возвращаем scoped блок: <style> + fonts + .aim-report-scope.
    # WordPress вставит это в post_content — всё будет работать.
    html = (
        fonts
        + css_minified
        + '<div class="aim-report-scope" data-theme="light">'
        + _flatten(body_inner)
        + '</div>'
    )

    return html
