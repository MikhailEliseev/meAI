"""PDF-конвертация HTML→PDF через WeasyPrint (Phase 12).

Два режима:
1. Если есть data dict (collected_results + profile_cache) → build_pdf_html()
   генерирует PDF-оптимизированный HTML (table-based, WeasyPrint-friendly).
2. Fallback: если есть только HTML slug из MySQL → извлекаем данные и перестраиваем.
"""
import json
import logging
import re
from pathlib import Path

logger = logging.getLogger(__name__)


def html_to_pdf(html: str) -> bytes:
    """Конвертирует готовый HTML в PDF через WeasyPrint.

    Args:
        html: HTML-строка (PDF-оптимизированная через build_pdf_html,
              или HTML из MySQL — будет перестроен через _rebuild_for_pdf)

    Returns:
        PDF в виде bytes
    """
    from weasyprint import HTML

    # Если HTML содержит .aim-report-scope (дизайн-система) — перестраиваем
    # в table-based HTML для WeasyPrint
    if "aim-report-scope" in html:
        logger.info("Detected design-system HTML, rebuilding for WeasyPrint...")
        html = _rebuild_for_pdf(html)

    try:
        html_doc = HTML(string=html)
        pdf_bytes = html_doc.write_pdf()
        logger.info("PDF generated: %d bytes", len(pdf_bytes))
        return pdf_bytes
    except Exception as e:
        logger.error("WeasyPrint PDF generation failed: %s", e)
        raise


def _rebuild_for_pdf(html: str) -> str:
    """Перестроить design-system HTML в PDF-оптимизированный.

    Извлекает: hero, sections, tables, surface-blocks из .aim-report-scope
    и строит table-based HTML через pdf_builder.
    """
    from app.report_builder.pdf_builder import _pdf_css

    # Извлечь <style> блок из оригинального HTML (для CSS variables)
    # Но он не нужен — мы используем свой _pdf_css()

    # Извлечь company_name из h1
    name_match = re.search(r'<h1>([^<]+)</h1>', html)
    company_name = name_match.group(1).strip() if name_match else "Клиника"

    # Извлечь subtitle из <em> внутри h1
    subtitle_match = re.search(r'<h1>[^<]*<em>([^<]+)</em>', html)
    subtitle = subtitle_match.group(1).strip() if subtitle_match else ""

    # Извлечь meta из .hero .meta
    meta_html = ""
    meta_match = re.search(r'<div class="meta">(.*?)</div>', html, re.DOTALL)
    if meta_match:
        # Извлечь текст из span
        spans = re.findall(r'<span[^>]*>(.*?)</span>', meta_match.group(1))
        meta_html = "  ·  ".join(spans)

    # Извлечь revenue block
    revenue_html = ""
    rev_match = re.search(r'<section class="revenue-block">(.*?)</section>', html, re.DOTALL)
    if rev_match:
        # Извлечь title
        rev_title = ""
        rt = re.search(r'<h2[^>]*>(.*?)</h2>', rev_match.group(1), re.DOTALL)
        if rt:
            rev_title = re.sub(r'<[^>]+>', '', rt.group(1)).strip()

        # Извлечь таблицу
        table_match = re.search(r'<table[^>]*>(.*?)</table>', rev_match.group(1), re.DOTALL)
        if table_match:
            revenue_html = _convert_revenue_table(table_match.group(0), rev_title)

    # Извлечь секции
    sections_html = ""
    section_pattern = re.compile(
        r'<section class="section"[^>]*>(.*?)</section>',
        re.DOTALL
    )
    label_pattern = re.compile(r'<div class="section-label"[^>]*>(.*?)</div>', re.DOTALL)

    for sm in section_pattern.finditer(html):
        section_content = sm.group(1)

        # Извлечь label
        label_match = label_pattern.search(section_content)
        section_label = label_match.group(1).strip() if label_match else ""
        # Очистить от HTML
        section_label = re.sub(r'<[^>]+>', '', section_label).strip()

        # Извлечь h2
        h2_match = re.search(r'<h2[^>]*>(.*?)</h2>', section_content, re.DOTALL)
        section_title = ""
        if h2_match:
            section_title = re.sub(r'<[^>]+>', '', h2_match.group(1)).strip()

        # Извлечь interpretation content
        interp_match = re.search(
            r'<div class="interpretation">(.*?)</div>\s*(?:</section>|<section|$)',
            section_content, re.DOTALL
        )
        interp_html = interp_match.group(1).strip() if interp_match else ""

        # Конвертировать interpretation HTML в PDF-friendly
        pdf_content = _convert_interp_html(interp_html)

        sections_html += (
            f'<div class="section">'
            f'<div class="section-label">{section_label}</div>'
            f'<h2>{section_title}</h2>'
            f'{pdf_content}'
            f'</div>'
        )

    # Собрать финальный HTML
    from app.report_builder.markdown_engine import _esc
    from datetime import datetime

    now = datetime.now().strftime("%d.%m.%Y")
    full_html = (
        '<!DOCTYPE html><html><head><meta charset="UTF-8">'
        f'<title>{_esc(company_name)} — AIM Report</title>'
        + _pdf_css()
        + '</head><body>'
        + f'<div class="hero">'
        + '<div class="label">AI MARKETING ANALYSIS</div>'
        + f'<h1>{_esc(company_name)}'
        + (f'<em>{_esc(subtitle)}</em>' if subtitle else '')
        + '</h1>'
        + '<div class="subtitle">Полный разбор рынка, конкурентов, отзывов '
        + 'и цифрового присутствия.</div>'
        + (f'<div class="meta">{meta_html}</div>' if meta_html else '')
        + '</div>'
        + revenue_html
        + sections_html
        + '<div class="report-footer">'
        + '<div class="logo">AIM</div>'
        + f'<div>Marketing Agency · Сгенерировано {now}</div>'
        + '<div>iamaim.ru</div>'
        + '</div>'
        + '</body></html>'
    )

    return full_html


def _convert_revenue_table(table_html: str, title: str) -> str:
    """Конвертировать design-system таблицу в PDF-friendly."""
    # Извлечь строки
    rows = re.findall(r'<tr[^>]*>(.*?)</tr>', table_html, re.DOTALL)
    if len(rows) < 2:
        return ""

    # Header
    header_cells = re.findall(r'<th[^>]*>(.*?)</th>', rows[0], re.DOTALL)
    header_html = "".join(f"<th>{re.sub(r'<[^>]+>', '', c).strip()}</th>" for c in header_cells[:4])

    # Body
    body_html = ""
    for row in rows[1:]:
        cells = re.findall(r'<t[dh][^>]*>(.*?)</t[dh]>', row, re.DOTALL)
        if not cells:
            continue
        # Check if client row
        is_client = "row-client" in row or "rev-row-client" in row
        cls = ' class="row-client"' if is_client else ""
        cells_html = "".join(
            f"<td>{re.sub(r'<[^>]+>', '', c).strip()}</td>" for c in cells[:4]
        )
        body_html += f"<tr{cls}>{cells_html}</tr>"

    from app.report_builder.markdown_engine import _esc
    return f"""
<div class="section">
    <div class="section-label">СРАВНЕНИЕ С КОНКУРЕНТАМИ</div>
    <h2>{_esc(title)}</h2>
    <table class="data-table">
        <thead><tr>{header_html}</tr></thead>
        <tbody>{body_html}</tbody>
    </table>
</div>
"""


def _convert_interp_html(html: str) -> str:
    """Конвертировать interpretation HTML в PDF-friendly формат.

    Простое преобразование: h3, p, ul/li, table, blockquote.
    """
    if not html:
        return ""

    result = html

    # glass-stats-wrap → stats-table
    result = re.sub(
        r'<div class="glass-stats-wrap">(.*?)</div>',
        lambda m: _convert_stats_to_table(m.group(1)),
        result, flags=re.DOTALL
    )

    # surface-block → оставить как есть (стили есть в PDF CSS)
    # card → упростить
    result = re.sub(
        r'<div class="card[^"]*"[^>]*>(.*?)</div>',
        r'<div class="card">\1</div>',
        result, flags=re.DOTALL
    )

    # metric-tag → tag
    result = re.sub(
        r'<span class="metric-tag metric-tag-(\w+)"[^>]*>.*?<span class="metric-tag-dot"[^>]*></span>(.*?)</span>',
        r'<span class="tag tag-\1">\2</span>',
        result, flags=re.DOTALL
    )

    # glass-table-wrap → data-table
    result = re.sub(
        r'<div class="glass-table-wrap[^"]*">(.*?)</div>',
        r'<div>\1</div>',
        result, flags=re.DOTALL
    )
    result = result.replace("<table>", '<table class="data-table">')

    # Убрать секции с ::: (если проскочили)
    result = re.sub(r':::\w[\w-]*:::', '', result)

    return result


def _convert_stats_to_table(stats_html: str) -> str:
    """Конвертировать glass-stat элементы в stats-table."""
    stats = re.findall(
        r'<div class="glass-stat[^"]*">.*?<div class="glass-stat-value"[^>]*>(.*?)</div>.*?<div class="glass-stat-label"[^>]*>(.*?)</div>',
        stats_html, re.DOTALL
    )
    if not stats:
        return stats_html

    cells = ""
    for value, label in stats:
        v = re.sub(r'<[^>]+>', '', value).strip()
        l = re.sub(r'<[^>]+>', '', label).strip()
        cells += f'<td><div class="value">{v}</div><div class="label">{l}</div></td>'

    rows = ""
    # Split cells into rows of 4
    cell_list = cells.split("</td>")
    cell_list = [c + "</td>" for c in cell_list if c.strip()]
    for i in range(0, len(cell_list), 4):
        row_cells = "".join(cell_list[i:i+4])
        rows += f"<tr>{row_cells}</tr>"

    return f'<table class="stats-table">{rows}</table>'


def data_to_pdf(
    collected_results: dict,
    profile_cache: dict,
    llm_text: str = "",
) -> bytes:
    """Конвертирует v2 данные напрямую в PDF (без MySQL roundtrip).

    Args:
        collected_results: dict tool_name → JSON-строка
        profile_cache: dict с метаданными клиента
        llm_text: текст анализа от LLM

    Returns:
        PDF в виде bytes
    """
    from app.report_builder.adapter import build_data_dict
    from app.report_builder.pdf_builder import build_pdf_html

    data = build_data_dict(collected_results, profile_cache, llm_text)
    title = profile_cache.get("company_name") or "Клиника"
    html = build_pdf_html(data, title)

    return html_to_pdf(html)

