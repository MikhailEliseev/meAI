"""build_report — Canonical HTML report builder with AIM Design System.

CRITICAL FIX (1 июля 2026):
- Google Fonts подключены через <link> (Playfair Display + Jost)
- Все 14 canonical классов из design-showcase-dual-theme.html
- Theme toggle + water ripples в светлой теме
- Metric tags (5 цветов) + glass cards + surface blocks
- КАНОН: AIM/frontend/design-showcase-dual-theme.html (2513 строк)

Заменяет generate_html_report.py (698 строк, только 1/14 классов, нет шрифтов).
"""

import json
import logging

logger = logging.getLogger(__name__)


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
    r'STATS:\s*\n((?:\s*-\s*value:.*?\n(?:\s*label:.*?\n|\s*-\s*label:.*?\n)?)+)',
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
    """Извлечь STATS: блок из текста, вернуть (text_without_stats, stats_html).

    Формат:
        STATS:
        - value: "4,1 млрд ₽"
          label: "Выручка 2024"
        - value: "+24%"
          label: "Рост за год"

    Поддерживаемые варианты:
      - value: X \\n label: Y       (label на новой строке с отступом)
      - value: X \\n - label: Y     (label с дефисом)
      - value: X | label: Y          (в одну строку через |)

    Возвращает HTML:
        <div class="glass-stats-wrap">
          <div class="glass-stat">
            <div class="glass-stat-value">4,1 млрд ₽</div>
            <div class="glass-stat-label">Выручка 2024</div>
          </div>
          ...
        </div>
    """
    match = _STATS_BLOCK_RE.search(text)
    if not match:
        return text, ""

    block = match.group(1)
    items: list[tuple[str, str]] = []

    # Парсим построчно. Ищем пары value/label.
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

            # Label on next non-empty line (usually "label: ..." possibly with indent)
            label = ""
            j = i + 1
            while j < len(lines):
                next_line = lines[j].strip()
                if not next_line:
                    j += 1
                    continue
                # Try "label: X" pattern (with or without leading "-")
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

    if not items:
        return text, ""

    stats_html_parts = ['<div class="glass-stats-wrap">']
    for value, label in items:
        stats_html_parts.append(
            f'<div class="glass-stat">'
            f'<div class="glass-stat-value">{_esc(value)}</div>'
            f'<div class="glass-stat-label">{_esc(label)}</div>'
            f'</div>'
        )
    stats_html_parts.append('</div>')

    # Remove STATS block from text (from start of "STATS:" to end of block)
    text_clean = text[:match.start()] + text[match.end():]
    return text_clean, '\n'.join(stats_html_parts)


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
        html_parts.append(f'<th>{_esc(cell)}</th>')
    html_parts.append('</tr></thead><tbody>')
    for row in body_rows:
        html_parts.append('<tr>')
        for cell in row:
            html_parts.append(f'<td>{_esc(cell)}</td>')
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





# ── CANONICAL CSS (extracted from AIM/frontend/design-showcase-dual-theme.html) ──

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

/* === THEME TOGGLE === */
.theme-toggle {
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

.theme-toggle:hover {
    background: var(--hover);
    transform: scale(1.05);
}

.theme-icon-sun { display: none; }
.theme-icon-moon { display: block; }
[data-theme="dark"] .theme-icon-sun { display: block; }
[data-theme="dark"] .theme-icon-moon { display: none; }

/* === CONTAINER === */
.report-container {
    max-width: 900px;
    margin: 0 auto;
    padding: 80px 40px 60px;
    position: relative;
    z-index: 1;
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
    letter-spacing: 0.5px;
    margin: 4px 6px 4px 0;
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
    grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
    gap: 16px;
    margin: 24px 0;
}

.glass-stat {
    background: var(--glass-bg);
    backdrop-filter: blur(16px) saturate(1.3);
    border: 1px solid var(--glass-border);
    border-radius: 6px;
    padding: 36px 28px;
    text-align: center;
    transition: transform .3s, box-shadow .3s, border-color .3s;
    animation: glass-glow 5s ease-in-out infinite;
}

.glass-stat:hover {
    border-color: var(--accent);
    transform: translateY(-4px);
    box-shadow: 0 8px 28px rgba(0,0,0,0.06);
}

.glass-stat-value {
    font-family: 'Playfair Display', serif;
    font-size: clamp(32px, 4vw, 48px);
    font-weight: 400;
    color: var(--accent);
    line-height: 1;
    margin-bottom: 12px;
}

.glass-stat-label {
    font-family: 'Jost', sans-serif;
    font-size: 12px;
    font-weight: 500;
    letter-spacing: .06em;
    text-transform: uppercase;
    color: var(--text-secondary);
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
    .cta-box { padding: 40px 24px; }
}
</style>"""


_THEME_TOGGLE_SCRIPT = """<script>
(function() {
    const html = document.documentElement;
    const toggle = document.getElementById('theme-toggle');

    // Load saved theme
    const saved = localStorage.getItem('aim-theme');
    if (saved) html.setAttribute('data-theme', saved);

    // Toggle handler
    if (toggle) {
        toggle.addEventListener('click', () => {
            const current = html.getAttribute('data-theme') || 'light';
            const next = current === 'light' ? 'dark' : 'light';
            html.setAttribute('data-theme', next);
            localStorage.setItem('aim-theme', next);
        });
    }
})();
</script>"""


async def handle_generate_html_report(
    session_hash: str = None,
    title: str = None,
    client_name: str = None,
    client_url: str = None,
    **kwargs,
) -> str:
    """Handler: Generate and publish HTML report (wrapper for build_report_html)."""
    import os
    import pymysql
    import secrets
    import string
    from datetime import datetime, timezone

    if isinstance(session_hash, dict):
        d = session_hash
        session_hash = d.get("session_hash", "")
        title = title or d.get("title", "")
        client_name = client_name or d.get("client_name", "")
        client_url = client_url or d.get("client_url", "")

    if not session_hash:
        return json.dumps({"error": "session_hash is required"}, ensure_ascii=False)

    report_title = title or client_name or "AIM Scout Report"

    # Load data from session archive
    from app.tools.session_archive import load_all_data, SESSIONS_ROOT
    data = load_all_data(session_hash)

    # Merge metadata overrides
    meta = data.get("metadata", {}) or {}
    if client_name:
        meta["company_name"] = client_name
    if client_url:
        meta["url"] = client_url
    data["metadata"] = meta

    # Generate HTML (canonical builder)
    html = build_report_html(data, report_title)

    # WordPress DB credentials
    WP_DB_HOST = os.getenv("WP_DB_HOST", "")
    WP_DB_USER = os.getenv("WP_DB_USER", "")
    WP_DB_PASSWORD = os.getenv("WP_DB_PASSWORD", "")
    WP_DB_NAME = os.getenv("WP_DB_NAME", "")

    # Publish
    if not WP_DB_PASSWORD:
        report_path = os.path.join(SESSIONS_ROOT, session_hash, "report.html")
        os.makedirs(os.path.dirname(report_path), exist_ok=True)
        with open(report_path, "w", encoding="utf-8") as f:
            f.write(html)
        return json.dumps({
            "status": "saved_locally",
            "path": report_path,
            "session_hash": session_hash,
        }, ensure_ascii=False)

    page_slug = ''.join(secrets.choice(string.ascii_lowercase + string.digits) for _ in range(8))
    wp_title = f"AIM Scout — {report_title}"

    conn = None
    try:
        conn = pymysql.connect(
            host=WP_DB_HOST, user=WP_DB_USER, password=WP_DB_PASSWORD,
            database=WP_DB_NAME, charset="utf8mb4", connect_timeout=5,
        )

        now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")

        with conn.cursor() as cur:
            cur.execute("SELECT ID FROM wp_posts WHERE post_name = %s LIMIT 1", (page_slug,))
            existing = cur.fetchone()

            if existing:
                cur.execute(
                    "UPDATE wp_posts SET post_content=%s, post_modified=%s WHERE ID=%s",
                    (html, now, existing[0]),
                )
                post_id = existing[0]
            else:
                cur.execute(
                    "INSERT INTO wp_posts (post_title, post_name, post_content, post_status, post_type, post_date, post_modified, post_excerpt) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)",
                    (wp_title, page_slug, html, "publish", "page", now, now, ""),
                )
                post_id = cur.lastrowid
            conn.commit()

        report_url = f"https://iamaim.ru/{page_slug}"

        logger.info("generate_html_report: published report for %s → %s (post_id=%s)", session_hash[:12], report_url, post_id)

        return json.dumps({
            "status": "published",
            "url": report_url,
            "slug": page_slug,
            "post_id": post_id,
            "title": wp_title,
            "session_hash": session_hash,
        }, ensure_ascii=False)

    except Exception as e:
        logger.exception("generate_html_report: WordPress publish failed")
        from app.tools.session_archive import SESSIONS_ROOT
        report_path = os.path.join(SESSIONS_ROOT, session_hash, "report.html")
        os.makedirs(os.path.dirname(report_path), exist_ok=True)
        with open(report_path, "w", encoding="utf-8") as f:
            f.write(html)
        return json.dumps({
            "status": "saved_locally",
            "path": report_path,
            "error": str(e),
            "session_hash": session_hash,
        }, ensure_ascii=False)
    finally:
        if conn:
            conn.close()


def build_report_html(data: dict, title: str) -> str:
    """Build canonical HTML report with Google Fonts + all 14 classes.

    Args:
        data: Session data with phases, interpretations, metadata
        title: Report title

    Returns:
        Full HTML document
    """

    # Extract metadata
    meta = data.get("metadata", {}) or {}
    company_name = meta.get("company_name", title)
    url = meta.get("url", "")

    # Extract interpretations from *_interpretation.json files
    # load_all_data() returns: {"PERPLEXITY_interpretation": {"content": "..."}, ...}
    phase_sections = []

    phase_order = [
        ("PERPLEXITY", "Исследование рынка"),
        ("COMPETITORS", "Конкуренты"),
        ("TECH AUDIT", "Технический аудит"),
        ("SOCIAL VERIFIER", "Социальные сети и отзывы"),
        ("CONTENT ANALYSIS", "Контент-анализ"),
        ("KEY PERSONS", "Ключевые персоны"),
        ("SMI MENTIONS", "Упоминания в СМИ"),
        ("FORUM PAINS", "Боли из форумов"),
        ("FINANCE", "Финансы"),
        ("CONTENT PLAN", "Контент-план"),
    ]

    for phase_key, phase_label in phase_order:
        # Read from PHASE_NAME_interpretation.json → {"content": "..."}
        interp_data = data.get(f"{phase_key}_interpretation", {})
        interpretation = interp_data.get("content", "") if isinstance(interp_data, dict) else ""
        if not interpretation:
            continue

        # Markdown → HTML with canonical classes (STATS, tables, headers, lists)
        html_content = _interpretation_to_html(interpretation)

        phase_sections.append(f"""
<div class="section">
    <span class="sec-tag">{_esc(phase_label)}</span>
    <div class="interpretation">
        {html_content}
    </div>
</div>
""")

    # Build CTA
    cta_html = """
<div class="cta-box">
    <h2>Обсудить результаты</h2>
    <p>Готовы внедрить рекомендации? Свяжитесь с нами для индивидуальной консультации.</p>
    <a href="https://t.me/eliseev_me" class="btn-primary">Связаться</a>
</div>
"""

    # Assemble full HTML
    html = f"""<!DOCTYPE html>
<html lang="ru" data-theme="light">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{_esc(title)} — AIM Scout</title>

    <!-- CRITICAL: Google Fonts (Playfair Display + Jost) -->
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Playfair+Display:ital,wght@0,400;0,500;0,600;0,700;1,400&family=Jost:wght@300;400;500;600;700&display=swap" rel="stylesheet">

    {_CANONICAL_CSS}
</head>
<body>
    <!-- Water ripples (visible only in light theme) -->
    <div class="water-ripples">
        <div class="ripple-ring"></div>
    </div>

    <!-- Theme toggle -->
    <button id="theme-toggle" class="theme-toggle" aria-label="Toggle theme">
        <span class="theme-icon-sun">☀️</span>
        <span class="theme-icon-moon">🌙</span>
    </button>

    <div class="report-container">
        <!-- Header -->
        <h1>{_esc(company_name)}</h1>
        {f'<p class="text-dim">URL: <a href="{_esc(url)}" target="_blank">{_esc(url)}</a></p>' if url else ''}

        <!-- Phase sections -->
        {''.join(phase_sections)}

        <!-- CTA -->
        {cta_html}
    </div>

    {_THEME_TOGGLE_SCRIPT}
</body>
</html>"""

    return html
