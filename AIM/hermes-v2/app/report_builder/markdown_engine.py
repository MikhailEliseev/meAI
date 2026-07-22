"""Markdown→HTML движок для отчётов. Перенесено из v1 build_report.py (строки 19-607)."""

import re


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


# ── Markdown → HTML + STATS extraction (added 1 июля 2026) ──────────────
#
# Контракт: LLM пишет markdown в interpretation. Builder преобразует в HTML
# используя canonical classes из design-showcase-dual-theme.html.
#
# Markdown поддерживает:
#   ## H2 / ### H3       → <h2>/<h3>
#   **bold**             → <strong>
#   *italic*             → <em>
#   - item               → <ul><li>
#   1. item              → <ol><li>
#   | table |            → <div class="glass-table-wrap"><table>
#   STATS:\n- value..    → <div class="glass-stats-wrap">
#   существующий HTML    → сохраняется как есть (не экранируется)
#


import re as _re

# Селекторы для определения "это уже HTML или markdown?"
_HTML_TAG_RE = _re.compile(r'<(h[1-6]|div|span|p|ul|ol|li|table|strong|em)\b', _re.IGNORECASE)
_STATS_BLOCK_RE = _re.compile(
    r'STATS:\s*\n((?:\s*-\s*value:.*?\n(?:\s*label:.*?(?:\n|$|\s*-\s*value:)|\s*-\s*label:.*?(?:\n|$|\s*-\s*value:))?)+)',
    _re.IGNORECASE | _re.DOTALL,
)
_STATS_VALUE_RE = _re.compile(r'-\s*value:\s*(.+?)\s*$', _re.IGNORECASE)
_STATS_LABEL_RE = _re.compile(r'-\s*label:\s*(.+?)\s*$', _re.IGNORECASE)
_STATS_LABEL_INDENT_RE = _re.compile(r'label:\s*(.+?)\s*$', _re.IGNORECASE)
_MD_TABLE_RE = _re.compile(
    r'(?:^|\n)(\|.+\|\n\|[\s\-:|]+\|\n(?:\|.+\|\n?)+)',
    _re.MULTILINE,
)


def _extract_stats_block(text: str) -> tuple[str, str]:
    """Извлечь ВСЕ STATS: блоки из текста (LLM может писать несколько в одном interpretation).

    Формат:
        STATS:
        - value: "4,1 млрд ₽"
          label: "Выручка 2024"

    Возвращает (text_without_stats, html_all_blocks).

    HTML содержит ОДИН <div class="glass-stats-wrap"> с объединёнными карточками.
    Блоки разделяются пустой строкой.
    """
    all_items: list[tuple[str, str]] = []
    blocks_found = 0

    while True:
        match = _STATS_BLOCK_RE.search(text)
        if not match:
            break

        blocks_found += 1
        block = match.group(1)
        items_in_block = _parse_stats_items(block)
        all_items.extend(items_in_block)

        # Remove this STATS block from text
        text = text[:match.start()] + '\n\n__STATS_PLACEHOLDER_' + str(blocks_found) + '__\n\n' + text[match.end():]

    if not all_items:
        return text.replace('\n\n__STATS_PLACEHOLDER_1__\n\n', '') if blocks_found == 0 else text, ""

    # Build HTML
    stats_html_parts = ['<div class="glass-stats-wrap">']
    for value, label in all_items:
        stats_html_parts.append(
            f'<div class="glass-stat">'
            f'<div class="glass-stat-value">{_esc(value)}</div>'
            f'<div class="glass-stat-label">{_esc(label)}</div>'
            f'</div>'
        )
    stats_html_parts.append('</div>')
    stats_html = '\n'.join(stats_html_parts)

    # Replace placeholders with the same HTML (or just remove if we'll insert once at end)
    # Simpler: replace all placeholders with empty, return stats_html once
    import re as _re_inline
    text_clean = _re_inline.sub(r'\n\n__STATS_PLACEHOLDER_\d+__\n\n', '\n\n', text)
    text_clean = _re_inline.sub(r'__STATS_PLACEHOLDER_\d+', '', text_clean)
    text_clean = _re_inline.sub(r'\n{3,}', '\n\n', text_clean).strip()

    return text_clean, stats_html


def _parse_stats_items(block: str) -> list[tuple[str, str]]:
    """Парсит один STATS блок, возвращает [(value, label), ...]."""
    items: list[tuple[str, str]] = []
    lines = block.split('\n')
    i = 0
    while i < len(lines):
        line = lines[i]
        value_match = _STATS_VALUE_RE.search(line)

        if value_match:
            value = value_match.group(1).strip().strip('"').strip("'")

            # Inline label (value: X | label: Y)
            inline_label = _re.search(r'\|\s*label:\s*(.+?)\s*$', line, _re.IGNORECASE)
            if inline_label:
                label = inline_label.group(1).strip().strip('"').strip("'")
                items.append((value, label))
                i += 1
                continue

            # Label on next non-empty line
            label = ""
            j = i + 1
            while j < len(lines):
                next_line = lines[j].strip()
                if not next_line:
                    j += 1
                    continue
                # Stop if it's another value or unrelated content
                if next_line.startswith('- ') and not _STATS_LABEL_INDENT_RE.search(next_line) and 'label' not in next_line.lower():
                    # It's a list item, but not a label
                    if not _STATS_VALUE_RE.search(next_line):
                        break
                # Try "label: X" pattern
                label_match = _STATS_LABEL_INDENT_RE.search(next_line)
                if label_match:
                    label = label_match.group(1).strip().strip('"').strip("'")
                    i = j
                    break
                # If next non-empty line is another "value:" without label — break
                if _STATS_VALUE_RE.search(next_line):
                    i = j - 1
                    break
                j += 1

            items.append((value, label))
        i += 1

    return items


def _markdown_table_to_html(table_text: str) -> str:
    """Преобразовать markdown таблицу в HTML с canonical wrapper.

    | Header 1 | Header 2 |
    |----------|----------|
    | Cell 1   | Cell 2   |

    →
    <div class="glass-table-wrap"><table>
      <thead><tr><th>Header 1</th><th>Header 2</th></tr></thead>
      <tbody><tr><td>Cell 1</td><td>Cell 2</td></tr></tbody>
    </table></div>
    """
    lines = [l.strip() for l in table_text.strip().split('\n') if l.strip().startswith('|')]
    if len(lines) < 2:
        return table_text

    def parse_row(line: str) -> list:
        # Split by |, drop empty first/last
        parts = line.split('|')
        if parts and parts[0].strip() == '':
            parts = parts[1:]
        if parts and parts[-1].strip() == '':
            parts = parts[:-1]
        return [p.strip() for p in parts]

    header = parse_row(lines[0])
    # lines[1] is separator (|---|---|)
    body_rows = [parse_row(l) for l in lines[2:]]

    html_parts = ['<div class="glass-table-wrap"><table><thead><tr>']
    for cell in header:
        # Process inline markdown: !!color:tag!!, **bold**, *italic*, `code`, [link](url)
        html_parts.append(f'<th>{_inline_markdown(cell)}</th>')
    html_parts.append('</tr></thead><tbody>')
    for row in body_rows:
        html_parts.append('<tr>')
        for cell in row:
            # Process inline markdown in cells — supports !!color:tag!!, **bold**, etc.
            html_parts.append(f'<td>{_inline_markdown(cell)}</td>')
        html_parts.append('</tr>')
    html_parts.append('</tbody></table></div>')

    return ''.join(html_parts)


def _inline_markdown(text: str) -> str:
    """Преобразовать inline markdown в HTML.

    Поддерживает (порядок важен):
    - `code` → <code> (обработать ПЕРВЫМ, чтобы не парсить markdown внутри code)
    - [text](url) → <a href="url" target="_blank">text</a>
    - **bold** → <strong>bold</strong>
    - *italic* → <em>italic</em>

    Защищаем уже существующие HTML теги от двойной обработки.
    """
    # Code: `text` → <code>text</code> (must be FIRST to protect content)
    text = _re.sub(r'`([^`\n]+?)`', r'<code>\1</code>', text)

    # Links: [text](url) — must process before bold since text may contain *
    def _link_replacer(m):
        link_text = m.group(1).strip()
        url = m.group(2).strip()
        # Skip obviously invalid URLs
        if not url or ' ' in url:
            return m.group(0)
        # Apply nested markdown to link text (bold inside link)
        link_text = _re.sub(r'\*\*([^*]+?)\*\*', r'<strong>\1</strong>', link_text)
        # Escape URL for HTML attribute
        url_esc = url.replace('"', '&quot;')
        return f'<a href="{url_esc}" target="_blank" rel="noopener">{link_text}</a>'
    text = _re.sub(r'\[([^\]]+?)\]\(([^)\s]+)\)', _link_replacer, text)

    # Bold: **text** → <strong>text</strong>
    text = _re.sub(r'\*\*([^*\n]+?)\*\*', r'<strong>\1</strong>', text)
    # Italic: *text* → <em>text</em> (только если ещё не <strong>)
    text = _re.sub(r'(?<!\*)\*([^*\n]+?)\*(?!\*)', r'<em>\1</em>', text)

    # Metric tags: !!color:text!! → <span class="metric-tag metric-tag-color">
    #              <span class="metric-tag-dot"></span>text</span>
    # Colors: green, yellow, red, blue, gray
    def _metric_tag_replacer(m):
        color = m.group(1).strip().lower()
        text_inner = m.group(2).strip()
        valid_colors = {'green', 'yellow', 'red', 'blue', 'gray'}
        if color not in valid_colors:
            return m.group(0)  # leave as-is if invalid color
        return (
            f'<span class="metric-tag metric-tag-{color}">'
            f'<span class="metric-tag-dot"></span>{text_inner}</span>'
        )
    text = _re.sub(r'!!(green|yellow|red|blue|gray):\s*([^!\n]+?)!!', _metric_tag_replacer, text)

    return text


def _markdown_to_html(text: str) -> str:
    """Преобразовать markdown в HTML.

    Поддерживает: ## h2, ### h3, **bold**, *italic*, - ul, 1. ol, | tables |,
    параграфы (разделяются пустой строкой).

    Сохраняет существующий HTML как есть.
    """
    if not text:
        return ""

    # If text contains substantial HTML tags (>2), assume it's already HTML
    if len(_HTML_TAG_RE.findall(text)) > 2:
        return text

    # Extract STATS blocks first (preserve them aside)
    text, stats_html = _extract_stats_block(text)

    # Extract markdown tables (replace with placeholders to avoid re-processing)
    tables: list[str] = []

    def _table_replacer(m):
        tables.append(_markdown_table_to_html(m.group(1)))
        return f'\n\n__TABLE_{len(tables) - 1}__\n\n'

    text = _MD_TABLE_RE.sub(_table_replacer, text)

    # Process line-by-line to handle lists properly
    lines = text.split('\n')
    html_parts = []
    in_ul = False
    in_ol = False
    in_paragraph: list[str] = []  # buffer for paragraph lines

    def close_lists():
        nonlocal in_ul, in_ol
        if in_ul:
            html_parts.append('</ul>')
            in_ul = False
        if in_ol:
            html_parts.append('</ol>')
            in_ol = False

    def flush_paragraph():
        nonlocal in_paragraph
        if in_paragraph:
            text_buf = ' '.join(line.strip() for line in in_paragraph if line.strip())
            if text_buf:
                text_buf = _inline_markdown(text_buf)
                html_parts.append(f'<p>{text_buf}</p>')
            in_paragraph = []

    # Process line-by-line with index (allows lookahead for blockquotes)
    i = 0
    while i < len(lines):
        line = lines[i]
        stripped = line.strip()

        # Empty line — flush paragraph
        if not stripped:
            flush_paragraph()
            close_lists()
            i += 1
            continue

        # Table placeholder
        if stripped.startswith('__TABLE_'):
            flush_paragraph()
            close_lists()
            idx = int(stripped.replace('__TABLE_', '').replace('__', ''))
            html_parts.append(tables[idx])
            i += 1
            continue

        # Headers
        if stripped.startswith('### '):
            flush_paragraph()
            close_lists()
            content = _inline_markdown(stripped[4:].strip())
            html_parts.append(f'<h3>{content}</h3>')
            i += 1
            continue
        if stripped.startswith('## '):
            flush_paragraph()
            close_lists()
            content = _inline_markdown(stripped[3:].strip())
            html_parts.append(f'<h2>{content}</h2>')
            i += 1
            continue
        if stripped.startswith('# '):
            flush_paragraph()
            close_lists()
            content = _inline_markdown(stripped[2:].strip())
            html_parts.append(f'<h2>{content}</h2>')  # h1 reserved for company name
            i += 1
            continue

        # === Section header === (LLM использует в PERPLEXITY фазе)
        eq_header_match = _re.match(r'^={2,}\s*(.+?)\s*={2,}$', stripped)
        if eq_header_match:
            flush_paragraph()
            close_lists()
            content = _inline_markdown(eq_header_match.group(1).strip())
            html_parts.append(f'<h3>{content}</h3>')
            i += 1
            continue

        # Horizontal rule: --- or *** or ___ (3+ chars, alone on line)
        if _re.match(r'^(-{3,}|\*{3,}|_{3,})$', stripped):
            flush_paragraph()
            close_lists()
            html_parts.append('<hr>')
            i += 1
            continue

        # Blockquote: > text → <blockquote>
        if stripped.startswith('> '):
            flush_paragraph()
            close_lists()
            # Collect consecutive > lines
            quote_lines = [stripped[2:].strip()]
            j = i + 1
            while j < len(lines):
                next_stripped = lines[j].strip()
                if next_stripped.startswith('> '):
                    quote_lines.append(next_stripped[2:].strip())
                    j += 1
                else:
                    break
            quote_text = ' '.join(quote_lines)
            quote_text = _inline_markdown(quote_text)
            html_parts.append(f'<blockquote class="surface-block">{quote_text}</blockquote>')
            i = j  # skip already-processed lines
            i += 1
            continue

        # Unordered list item
        if stripped.startswith('- ') or stripped.startswith('* '):
            flush_paragraph()
            if in_ol:
                html_parts.append('</ol>')
                in_ol = False
            if not in_ul:
                html_parts.append('<ul>')
                in_ul = True
            item = _inline_markdown(stripped[2:].strip())
            html_parts.append(f'<li>{item}</li>')
            i += 1
            continue

        # Ordered list item
        ol_match = _re.match(r'^(\d+)\.\s+(.+)$', stripped)
        if ol_match:
            flush_paragraph()
            if in_ul:
                html_parts.append('</ul>')
                in_ul = False
            if not in_ol:
                html_parts.append('<ol>')
                in_ol = True
            item = _inline_markdown(ol_match.group(2).strip())
            html_parts.append(f'<li>{item}</li>')
            i += 1
            continue

        # Default: paragraph line (buffer it)
        in_paragraph.append(stripped)
        i += 1

    # Flush remaining
    flush_paragraph()
    close_lists()

    # Insert STATS block after first element (usually h2 or p)
    if stats_html:
        insert_pos = 1 if html_parts else 0
        html_parts.insert(insert_pos, stats_html)

    return '\n'.join(html_parts)


def _interpretation_to_html(content: str) -> str:
    """Полный пайплайн: interpretation text → HTML с canonical classes.

    Это единая точка входа для всех interpretation в build_report.
    Делает:
      1. STATS: блок → .glass-stats-wrap
      2. Markdown таблицы → .glass-table-wrap
      3. Inline markdown (**bold**, *italic*, !!color:tag!!)
      4. ## headers → <h2>/<h3>
      5. - lists → <ul>/<ol>
      6. > blockquote → .surface-block
      7. --- horizontal rule → <hr>
      8. === Header === → <h3>
      9. Параграфы → <p>
      10. Сохраняет existing HTML если он есть

    Args:
        content: Текст interpretation от LLM.

    Returns:
        HTML строка (без обёртки <div class="interpretation"> —
        обёртку добавляет вызывающий код).
    """
    if not content:
        return ""

    # Удаляем маркер ошибки интерпретации если он есть
    if content.startswith("[Ошибка интерпретации"):
        return f'<p class="text-dim">{_esc(content)}</p>'

    return _markdown_to_html(content)


def validate_interpretation(content: str) -> dict:
    """Проверить interpretation на соответствие контракту.

    Возвращает dict с предупреждениями:
    {
        "has_stats": bool,           # STATS: блок использован?
        "has_headers": bool,         # ## или === заголовки есть?
        "has_lists": bool,           # - или 1. списки есть?
        "has_metric_tags": bool,     # !!color:text!! метки есть?
        "has_bold": bool,            # **bold** использовано?
        "has_blockquote": bool,      # > цитата есть?
        "length_chars": int,         # длина текста
        "warnings": list[str],       # список предупреждений
        "score": int,                # 0-100 quality score
    }

    Используется в QC фазе для оценки качества interpretation.
    """
    if not content:
        return {
            "has_stats": False, "has_headers": False, "has_lists": False,
            "has_metric_tags": False, "has_bold": False, "has_blockquote": False,
            "length_chars": 0, "warnings": ["Empty content"], "score": 0,
        }

    warnings = []

    # Feature detection
    has_stats = bool(_re.search(r'^STATS:', content, _re.MULTILINE | _re.IGNORECASE))
    has_h2 = bool(_re.search(r'^##\s+', content, _re.MULTILINE))
    has_h3 = bool(_re.search(r'^###\s+', content, _re.MULTILINE))
    has_eq_header = bool(_re.search(r'^={2,}\s*\w+\s*={2,}$', content, _re.MULTILINE))
    has_headers = has_h2 or has_h3 or has_eq_header

    has_ul = bool(_re.search(r'^[-*]\s+', content, _re.MULTILINE))
    has_ol = bool(_re.search(r'^\d+\.\s+', content, _re.MULTILINE))
    has_lists = has_ul or has_ol

    has_metric_tags = bool(_re.search(r'!!(green|yellow|red|blue|gray):', content))
    has_bold = '**' in content
    has_blockquote = bool(_re.search(r'^>\s+', content, _re.MULTILINE))

    length = len(content)

    # Quality score (0-100)
    score = 0
    if has_headers:
        score += 25
    if has_lists:
        score += 20
    if has_bold:
        score += 15
    if has_stats:
        score += 20  # bonus for using STATS
    if has_blockquote:
        score += 10
    if has_metric_tags:
        score += 10  # bonus for using metric tags
    score = min(score, 100)

    # Warnings
    if not has_headers:
        warnings.append("No headers (## or ===) — section will be wall of text")
    if not has_lists:
        warnings.append("No lists (- or 1.) — content may be hard to scan")
    if not has_bold:
        warnings.append("No **bold** — key points not highlighted")
    if not has_stats and length > 500:
        warnings.append("No STATS: block despite substantial content — key metrics not visualized")
    if length > 4000:
        warnings.append(f"Length {length} > 4000 chars — will be truncated")
    if length < 100:
        warnings.append(f"Very short ({length} chars) — may be insufficient analysis")

    return {
        "has_stats": has_stats,
        "has_headers": has_headers,
        "has_lists": has_lists,
        "has_metric_tags": has_metric_tags,
        "has_bold": has_bold,
        "has_blockquote": has_blockquote,
        "length_chars": length,
        "warnings": warnings,
        "score": score,
    }
