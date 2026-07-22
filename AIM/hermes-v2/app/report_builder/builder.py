"""Сборка финального HTML-отчёта.

Перенесено из v1 build_report.py (строки 1485-1574, функция build_report_html) с
адаптацией под v2:
- CSS берётся из css.py (_CANONICAL_CSS)
- Markdown→HTML берётся из markdown_engine.py (_interpretation_to_html)
- Revenue block — из revenue_block.py (новая сигнатура с распакованными аргументами)
- phase_order использует новое v2-mapping (PROFILE/OVERVIEW/COMPETITORS/REVIEWS)
"""

import json
import re

from app.report_builder.css import _CANONICAL_CSS
from app.report_builder.markdown_engine import _esc, _interpretation_to_html
from app.report_builder.revenue_block import build_revenue_vs_competitors_block


# phase_order: (phase_key, label) — порядок секций в отчёте.
# phase_key используется как data[f"{phase_key}_interp"].
# Соответствует mapping в adapter.py.
_PHASE_ORDER = [
    ("PROFILE",     "Профиль клиники"),
    ("OVERVIEW",    "Обзор рынка"),
    ("COMPETITORS", "Конкуренты"),
    ("REVIEWS",     "Отзывы пациентов"),
]


def _extract_client_financials(data: dict) -> tuple[float | None, float | None]:
    """Извлечь client_revenue и client_profit из data["FINANCE"].

    В v1 данные лежали как ``data["FINANCE"]["find_company_financials"]`` —
    вложенный JSON с ``company.latest_revenue``. adapter.py нормализует
    v2 company_financials в ту же структуру, поэтому читаем одинаково.
    """
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
    # Приводим к float|None
    rev_f = float(revenue) if revenue is not None else None
    profit_f = float(profit) if profit is not None else None
    return rev_f, profit_f


def build_report_html(data: dict, title: str) -> str:
    """Собрать финальный HTML-отчёт из data dict.

    Args:
        data: dict в формате, который строит ``adapter.build_data_dict``::

            {
              "metadata": {"company_name": ..., "url": ..., "inn": ...},
              "PROFILE_interp":     {"content": "...", "label": "..."},
              "OVERVIEW_interp":    {"content": "...", "label": "..."},
              "COMPETITORS_interp": {"content": "...", "label": "..."},
              "REVIEWS_interp":     {"content": "...", "label": "..."},
              "FINANCE":      {"find_company_financials": "<json>"},
              "COMPETITORS":  {"find_competitors": "<json>"},
            }

        title: Заголовок отчёта (fallback для company_name).

    Returns:
        Полный HTML-документ (CSS + разметка, wpautop-совместимый —
        контент свёрнут в одну строку на каждый блочный элемент).
    """
    # ── Metadata ──────────────────────────────────────────────────────────────
    meta = data.get("metadata", {}) or {}
    company_name = meta.get("company_name") or title
    url = meta.get("url", "") or ""

    # ── Секции (интерпретации) ────────────────────────────────────────────────
    phase_sections = []
    for phase_key, default_label in _PHASE_ORDER:
        interp = data.get(f"{phase_key}_interp", {})
        if not isinstance(interp, dict):
            continue
        content = interp.get("content", "") or ""
        if not content.strip():
            continue
        label = interp.get("label") or default_label

        # Markdown → HTML с canonical classes (STATS, tables, headers, lists)
        html_content = _interpretation_to_html(content)

        phase_sections.append(
            f'<div class="section">'
            f'<span class="sec-tag">{_esc(label)}</span>'
            f'<div class="interpretation">{html_content}</div>'
            f'</div>'
        )

    # ── CTA ───────────────────────────────────────────────────────────────────
    cta_html = (
        '<div class="cta-box">'
        '<h2>Обсудить результаты</h2>'
        '<p>Готовы внедрить рекомендации? Свяжитесь с нами для индивидуальной консультации.</p>'
        '<a href="https://t.me/eliseev_me" class="btn-primary">Связаться</a>'
        '</div>'
    )

    # ── CSS: минификация в одну строку (wpautop оборачивает многострочный контент в <p>) ──
    css_minified = re.sub(r'\s+', ' ', _CANONICAL_CSS).strip()

    # WordPress theme имеет свой theme-toggle в header — НЕ добавляем свой
    # (конфликтует). Только секция отчёта.

    # ── Сборка INNER HTML: каждый блочный элемент в одну строку (wpautop-safe) ──
    sections_html = ''.join(phase_sections).replace('\n', ' ').replace('\r', '')
    cta_min = cta_html.replace('\n', ' ').replace('\r', '')

    # ── Revenue block (вау-блок «Выручка vs Конкуренты») ───────────────────────
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
    revenue_block_min = (
        revenue_block_html.replace('\n', ' ').replace('\r', '')
        if revenue_block_html else ''
    )

    # ── Финальная сборка (одна строка — wpautop не сломает) ───────────────────
    html = (
        '<style>' + css_minified.replace('<style>', '').replace('</style>', '') + '</style>'
        + '<div class="aim-report-scope">'
        + '<div class="report-container">'
        + f'<h1>{_esc(company_name)}</h1>'
        + (f'<p class="text-dim">URL: <a href="{_esc(url)}" target="_blank">{_esc(url)}</a></p>'
           if url else '')
        + revenue_block_min
        + sections_html
        + cta_min
        + '</div>'
        + '</div>'
    )

    return html
