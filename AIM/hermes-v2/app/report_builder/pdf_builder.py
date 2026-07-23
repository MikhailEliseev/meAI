"""PDF-оптимизированный HTML builder для WeasyPrint (Phase 12).

WeasyPrint НЕ поддерживает: CSS grid, backdrop-filter, CSS animations,
ограниченный flexbox. Этот модуль генерирует простой table-based HTML
с инлайн-стилями, который WeasyPrint рендерит корректно.

Дизайн: Inter + Playfair Display, светлая тема, минимализм.
Layout: table-based (не grid/flex), инлайн-CSS.
"""
import json
import logging
import re
from datetime import datetime

from app.report_builder.markdown_engine import _esc

logger = logging.getLogger(__name__)


# Цветовая палитра (light theme для PDF)
C = {
    "bg": "#ffffff",
    "surface": "#F5F5F5",
    "hover": "#EBEBEB",
    "border": "#E0E0E0",
    "border_strong": "#CFCFCF",
    "text": "#1A1A1A",
    "text_sec": "#666666",
    "text_dim": "#999999",
    "accent": "#1A1A1A",
    "green": "#2E7D32",
    "red": "#C62828",
}


def _pdf_css() -> str:
    """CSS специально для WeasyPrint — простые, поддерживаемые свойства."""
    return f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=Playfair+Display:ital,wght@0,400;0,500;0,700;1,400&display=swap');

@page {{
    size: A4;
    margin: 2cm 1.5cm 2.5cm 1.5cm;
    @bottom-center {{
        content: "AIM — Marketing Analysis  |  Страница " counter(page);
        font-size: 9pt;
        color: {C['text_dim']};
        font-family: 'Inter', sans-serif;
    }}
}}

* {{ box-sizing: border-box; margin: 0; padding: 0; }}

body {{
    font-family: 'Inter', sans-serif;
    font-size: 11pt;
    line-height: 1.6;
    color: {C['text_sec']};
    background: {C['bg']};
}}

h1, h2, h3, h4 {{
    font-family: 'Playfair Display', serif;
    color: {C['text']};
    line-height: 1.2;
}}

p {{ margin: 8pt 0; color: {C['text_sec']}; }}
p strong {{ color: {C['text']}; font-weight: 600; }}

/* Hero */
.hero {{
    border-bottom: 2px solid {C['text']};
    padding-bottom: 20pt;
    margin-bottom: 30pt;
}}
.hero .label {{
    font-size: 8pt;
    letter-spacing: 3pt;
    text-transform: uppercase;
    color: {C['text_dim']};
    font-weight: 600;
    margin-bottom: 12pt;
}}
.hero h1 {{
    font-size: 28pt;
    font-weight: 400;
    margin-bottom: 12pt;
}}
.hero h1 em {{
    font-style: italic;
    font-size: 14pt;
    display: block;
    margin-top: 8pt;
    color: {C['text_sec']};
    font-weight: 400;
}}
.hero .subtitle {{
    font-size: 11pt;
    color: {C['text_sec']};
    max-width: 500pt;
}}
.hero .meta {{
    font-size: 9pt;
    color: {C['text_dim']};
    margin-top: 15pt;
}}

/* Section */
.section {{
    margin-bottom: 30pt;
    page-break-inside: avoid;
}}
.section-label {{
    font-size: 8pt;
    letter-spacing: 3pt;
    text-transform: uppercase;
    color: {C['text_dim']};
    font-weight: 600;
    margin-bottom: 8pt;
    border-bottom: 1px solid {C['border']};
    padding-bottom: 4pt;
}}
.section h2 {{
    font-size: 18pt;
    font-weight: 400;
    margin-bottom: 10pt;
}}

/* Surface block (quote/insight) */
.surface-block {{
    background: {C['surface']};
    border-left: 3px solid {C['accent']};
    padding: 12pt 16pt;
    margin: 12pt 0;
}}
.surface-block p {{
    font-size: 10pt;
    color: {C['text']};
    font-weight: 500;
    margin: 0;
}}

/* Stats table */
.stats-table {{
    width: 100%;
    border-collapse: collapse;
    margin: 12pt 0;
}}
.stats-table td {{
    padding: 12pt;
    text-align: center;
    border: 1px solid {C['border']};
}}
.stats-table .value {{
    font-family: 'Playfair Display', serif;
    font-size: 20pt;
    font-weight: 400;
    color: {C['text']};
}}
.stats-table .label {{
    font-size: 8pt;
    color: {C['text_dim']};
    text-transform: uppercase;
    letter-spacing: 1pt;
}}

/* Data table */
.data-table {{
    width: 100%;
    border-collapse: collapse;
    margin: 12pt 0;
    font-size: 10pt;
}}
.data-table th {{
    background: {C['surface']};
    font-weight: 600;
    font-size: 8pt;
    text-transform: uppercase;
    letter-spacing: 1pt;
    color: {C['text_sec']};
    padding: 8pt 10pt;
    border: 1px solid {C['border']};
    text-align: left;
}}
.data-table td {{
    padding: 8pt 10pt;
    border: 1px solid {C['border']};
    color: {C['text_sec']};
}}
.data-table .row-client {{
    background: {C['hover']};
    font-weight: 600;
}}
.data-table .row-client td {{
    color: {C['accent']};
}}

/* Card */
.card {{
    background: {C['surface']};
    padding: 14pt;
    margin: 8pt 0;
    border-radius: 4pt;
    page-break-inside: avoid;
}}
.card h4 {{
    font-family: 'Inter', sans-serif;
    font-size: 10pt;
    font-weight: 600;
    color: {C['text']};
    margin-bottom: 4pt;
}}
.card p {{
    font-size: 9pt;
    color: {C['text_sec']};
    margin: 0;
}}

/* Lists */
ul, ol {{
    margin: 8pt 0 8pt 20pt;
}}
li {{
    margin: 4pt 0;
    font-size: 10pt;
    color: {C['text_sec']};
}}

/* Tags (metric-tags) */
.tag {{
    display: inline-block;
    font-size: 8pt;
    font-weight: 600;
    padding: 3pt 8pt;
    border-radius: 3pt;
    margin: 2pt 3pt 2pt 0;
}}
.tag-green {{ background: #E8F5E9; color: {C['green']}; }}
.tag-yellow {{ background: #FFF9C4; color: #F57F17; }}
.tag-red {{ background: #FFEBEE; color: {C['red']}; }}
.tag-blue {{ background: #E3F2FD; color: #1565C0; }}

/* Footer */
.report-footer {{
    margin-top: 30pt;
    padding-top: 12pt;
    border-top: 1px solid {C['border']};
    text-align: center;
    color: {C['text_dim']};
    font-size: 8pt;
}}
.report-footer .logo {{
    font-family: 'Playfair Display', serif;
    font-size: 14pt;
    font-weight: 700;
    color: {C['text']};
    margin-bottom: 4pt;
}}
</style>
"""


def _markdown_to_pdf_html(content: str) -> str:
    """Конвертирует Markdown в table-based HTML для WeasyPrint.

    Простая поддержка: ## h2, ### h3, **bold**, списки, таблицы, STATS:.
    """
    if not content:
        return ""

    lines = content.strip().split("\n")
    html_parts = []
    in_ul = False
    in_ol = False
    in_table = False
    table_rows = []

    def close_lists():
        nonlocal in_ul, in_ol
        if in_ul:
            html_parts.append("</ul>")
            in_ul = False
        if in_ol:
            html_parts.append("</ol>")
            in_ol = False

    def close_table():
        nonlocal in_table, table_rows
        if in_table and table_rows:
            html_parts.append('<table class="data-table">')
            # Header
            html_parts.append("<thead><tr>")
            for cell in table_rows[0]:
                html_parts.append(f"<th>{_inline_md(cell)}</th>")
            html_parts.append("</tr></thead><tbody>")
            # Body
            for row in table_rows[1:]:
                html_parts.append("<tr>")
                for cell in row:
                    html_parts.append(f"<td>{_inline_md(cell)}</td>")
                html_parts.append("</tr>")
            html_parts.append("</tbody></table>")
            table_rows = []
            in_table = False

    for line in lines:
        stripped = line.strip()

        # Empty line
        if not stripped:
            close_lists()
            close_table()
            continue

        # Table row
        if stripped.startswith("|"):
            cells = [c.strip() for c in stripped.split("|")[1:-1]]
            if cells and all(re.match(r'^[-:\s]+$', c) for c in cells):
                continue  # separator row
            if not in_table:
                in_table = True
                table_rows = []
            table_rows.append(cells)
            continue
        else:
            close_table()

        # STATS block → stats table
        if stripped.upper().startswith("STATS:"):
            close_lists()
            # Collect following - value: / label: pairs
            continue

        # Section headers (:::section-num)
        if stripped.startswith(":::"):
            continue

        # h2
        if stripped.startswith("### "):
            close_lists()
            html_parts.append(f"<h3>{_inline_md(stripped[4:])}</h3>")
            continue
        if stripped.startswith("## "):
            close_lists()
            html_parts.append(f"<h2>{_inline_md(stripped[3:])}</h2>")
            continue

        # Blockquote
        if stripped.startswith("> "):
            close_lists()
            html_parts.append(f'<div class="surface-block"><p>{_inline_md(stripped[2:])}</p></div>')
            continue

        # Lists
        if stripped.startswith("- ") or stripped.startswith("* "):
            if in_ol:
                html_parts.append("</ol>")
                in_ol = False
            if not in_ul:
                html_parts.append("<ul>")
                in_ul = True
            html_parts.append(f"<li>{_inline_md(stripped[2:])}</li>")
            continue

        ol_match = re.match(r'^(\d+)\.\s+(.+)$', stripped)
        if ol_match:
            if in_ul:
                html_parts.append("</ul>")
                in_ul = False
            if not in_ol:
                html_parts.append("<ol>")
                in_ol = True
            html_parts.append(f"<li>{_inline_md(ol_match.group(2))}</li>")
            continue

        # Paragraph
        close_lists()
        html_parts.append(f"<p>{_inline_md(stripped)}</p>")

    close_lists()
    close_table()

    # Process STATS blocks
    result = "\n".join(html_parts)
    result = _process_stats_blocks(result, content)

    return result


def _process_stats_blocks(html: str, original_content: str) -> str:
    """Извлекает STATS: блоки из оригинального контента и вставляет stats table."""
    stats_pattern = re.compile(
        r'STATS:\s*\n((?:\s*-\s*value:.*?\n(?:\s*label:.*?(?:\n|$|\s*-\s*value:))?)+)',
        re.IGNORECASE | re.DOTALL,
    )
    value_re = re.compile(r'-\s*value:\s*(.+?)\s*$', re.IGNORECASE)
    label_re = re.compile(r'-\s*label:\s*(.+?)\s*$', re.IGNORECASE)

    matches = list(stats_pattern.finditer(original_content))
    if not matches:
        return html

    # Build stats table HTML
    all_items = []
    for m in matches:
        block = m.group(1)
        block_lines = block.split('\n')
        i = 0
        while i < len(block_lines):
            line = block_lines[i]
            vm = value_re.search(line)
            if vm:
                value = vm.group(1).strip().strip('"').strip("'")
                label = ""
                # Look for label in same line or next
                inline_label = re.search(r'\|\s*label:\s*(.+?)$', line, re.IGNORECASE)
                if inline_label:
                    label = inline_label.group(1).strip().strip('"').strip("'")
                elif i + 1 < len(block_lines):
                    lm = label_re.search(block_lines[i + 1])
                    if lm:
                        label = lm.group(1).strip().strip('"').strip("'")
                        i += 1
                all_items.append((value, label))
            i += 1

    if not all_items:
        return html

    # Build table
    cells = []
    for value, label in all_items:
        cells.append(
            f'<td><div class="value">{_esc(value)}</div>'
            f'<div class="label">{_esc(label)}</div></td>'
        )
    # Max 4 per row
    rows_html = ""
    for i in range(0, len(cells), 4):
        row_cells = "".join(cells[i:i+4])
        rows_html += f"<tr>{row_cells}</tr>"

    stats_html = f'<table class="stats-table">{rows_html}</table>'

    # Insert after first <h2> or <h3>
    insert_pos = html.find("</h2>")
    if insert_pos == -1:
        insert_pos = html.find("</h3>")
    if insert_pos == -1:
        insert_pos = 0
    else:
        insert_pos += 5  # after closing tag

    return html[:insert_pos] + stats_html + html[insert_pos:]


def _inline_md(text: str) -> str:
    """Inline markdown: **bold**, *italic*, !!color:tag!!."""
    # Bold
    text = re.sub(r'\*\*([^*]+?)\*\*', r'<strong>\1</strong>', text)
    # Italic
    text = re.sub(r'(?<!\*)\*([^*\n]+?)\*(?!\*)', r'<em>\1</em>', text)
    # Metric tags: !!green:text!!
    def _tag_replacer(m):
        color = m.group(1).strip().lower()
        inner = m.group(2).strip()
        valid = {'green', 'yellow', 'red', 'blue'}
        if color not in valid:
            return m.group(0)
        return f'<span class="tag tag-{color}">{_esc(inner)}</span>'
    text = re.sub(r'!!(green|yellow|red|blue):\s*([^!\n]+?)!!', _tag_replacer, text)
    return text


def build_pdf_html(data: dict, title: str) -> str:
    """Собрать PDF-оптимизированный HTML для WeasyPrint.

    Args:
        data: dict из build_data_dict() (тот же формат что для build_report_html)
        title: Название клиники

    Returns:
        Полный HTML-документ, оптимизированный для WeasyPrint
    """
    meta = data.get("metadata", {}) or {}
    hero_meta = data.get("hero_meta", {}) or {}
    company_name = meta.get("company_name") or title

    # ── Hero ──────────────────────────────────────────────────────────
    subtitle_text = hero_meta.get("subtitle", "") or "Маркетинговый аудит и точки роста"
    meta_parts = []
    if hero_meta.get("city"):
        meta_parts.append(f"📍 {_esc(hero_meta['city'])}")
    if hero_meta.get("doctors_count"):
        meta_parts.append(f"🏥 {_esc(str(hero_meta['doctors_count']))} врачей")
    if hero_meta.get("founded_year"):
        meta_parts.append(f"📅 С {_esc(hero_meta['founded_year'])}")
    if hero_meta.get("rating") is not None:
        r = hero_meta["rating"]
        rc = hero_meta.get("reviews_count")
        if rc:
            meta_parts.append(f"⭐ {r:.1f} ({_esc(str(rc))})")
        else:
            meta_parts.append(f"⭐ {r:.1f}")
    meta_html = "  ·  ".join(meta_parts)

    hero_html = (
        '<div class="hero">'
        '<div class="label">AI MARKETING ANALYSIS</div>'
        f'<h1>{_esc(company_name)}<em>{_esc(subtitle_text)}</em></h1>'
        '<div class="subtitle">Полный разбор рынка, конкурентов, отзывов '
        'и цифрового присутствия.</div>'
        f'<div class="meta">{meta_html}</div>'
        '</div>'
    )

    # ── Revenue block ──────────────────────────────────────────────────
    revenue_html = ""
    client_revenue, _ = _extract_client_financials(data)
    competitors_result = ""
    comp_phase = data.get("COMPETITORS", {})
    if isinstance(comp_phase, dict):
        competitors_result = comp_phase.get("find_competitors", "") or ""

    if client_revenue or competitors_result:
        revenue_html = _build_revenue_table(client_revenue, competitors_result, company_name)

    # ── Sections ───────────────────────────────────────────────────────
    phase_config = [
        ("PROFILE", "01 — О КЛИНИКЕ", "Профиль клиники"),
        ("OVERVIEW", "02 — РЫНОК", "Обзор рынка"),
        ("COMPETITORS", "03 — КОНКУРЕНТЫ", "Конкуренты"),
        ("REVIEWS", "04 — ОТЗЫВЫ", "Отзывы пациентов"),
    ]

    sections_html = ""
    for phase_key, section_label, default_h2 in phase_config:
        interp = data.get(f"{phase_key}_interp", {})
        if not isinstance(interp, dict):
            continue
        content = interp.get("content", "") or ""
        if not content.strip():
            continue
        label = interp.get("label") or default_h2

        content_html = _markdown_to_pdf_html(content)

        sections_html += (
            f'<div class="section">'
            f'<div class="section-label">{_esc(section_label)}</div>'
            f'<h2>{_esc(label)}</h2>'
            f'{content_html}'
            f'</div>'
        )

    # ── Footer ─────────────────────────────────────────────────────────
    now = datetime.now().strftime("%d.%m.%Y")
    footer_html = (
        '<div class="report-footer">'
        '<div class="logo">AIM</div>'
        f'<div>Marketing Agency · Сгенерировано {now}</div>'
        '<div>iamaim.ru</div>'
        '</div>'
    )

    # ── Сборка ─────────────────────────────────────────────────────────
    full_html = (
        '<!DOCTYPE html><html><head><meta charset="UTF-8">'
        f'<title>{_esc(company_name)} — AIM Report</title>'
        + _pdf_css()
        + '</head><body>'
        + hero_html
        + revenue_html
        + sections_html
        + footer_html
        + '</body></html>'
    )

    return full_html


def _extract_client_financials(data: dict) -> tuple:
    """Extract client_revenue from data["FINANCE"]."""
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


def _fmt_revenue_short(val) -> str:
    """Format revenue: 120000000 → '120 млн ₽'."""
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


def _build_revenue_table(client_revenue, competitors_result: str, company_name: str) -> str:
    """Build revenue comparison table for PDF."""
    competitors = []
    if competitors_result:
        try:
            parsed = json.loads(competitors_result)
            competitors = parsed.get("competitors", []) if isinstance(parsed, dict) else []
        except (json.JSONDecodeError, TypeError):
            pass

    competitors_with_rev = [
        c for c in competitors
        if isinstance(c, dict) and c.get("revenue_year") and c.get("revenue_year") > 0
    ]

    if not client_revenue and not competitors_with_rev:
        return ""

    all_rows = []
    if client_revenue:
        all_rows.append({"name": company_name, "is_client": True, "revenue": client_revenue})
    for c in competitors_with_rev:
        brand = c.get("brand_name") or c.get("legal_name") or "Конкурент"
        all_rows.append({"name": brand, "is_client": False, "revenue": c.get("revenue_year", 0)})
    all_rows.sort(key=lambda r: r["revenue"], reverse=True)

    rows_html = ""
    for i, row in enumerate(all_rows, 1):
        rev_str = _fmt_revenue_short(row["revenue"])
        client_class = ' class="row-client"' if row["is_client"] else ""
        rows_html += f"<tr{client_class}><td>{i}</td><td>{_esc(row['name'])}</td><td>{rev_str}</td></tr>"

    title = f"{company_name} vs {len(competitors_with_rev)} конкурентов" if client_revenue else f"Топ-{len(competitors_with_rev)} конкурентов"

    return f"""
<div class="section">
    <div class="section-label">СРАВНЕНИЕ С КОНКУРЕНТАМИ</div>
    <h2>{_esc(title)}</h2>
    <table class="data-table">
        <thead><tr><th style="width:30pt">#</th><th>Клиника</th><th>Выручка</th></tr></thead>
        <tbody>{rows_html}</tbody>
    </table>
</div>
"""
