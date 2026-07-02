#!/usr/bin/env python3
"""render_report_preview — Генерирует standalone HTML-отчёт для визуальной отладки.

Читает session data из /sessions-archive/{slug}/ и генерирует полный HTML
документ (с DOCTYPE/head/body + Google Fonts), который можно открыть в браузере
локально — без WordPress, без LLM, без пайплайна.

Использование:
    python scripts/render_report_preview.py <slug> [--out PATH]
    python scripts/render_report_preview.py mira-med-1783003747
    python scripts/render_report_preview.py mira-med-1783003747 --out ~/Desktop/preview.html

По умолчанию:
    --session-root:  ../_reference/  (эталонная сессия в репозитории)
    --out:           ./preview-{slug}.html  (открывается в браузере)

Файл сразу открывается в браузере (macOS: `open`).
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import webbrowser
from pathlib import Path

# Подкладываем путь к app/ чтобы импорт сработал локально
HERE = Path(__file__).resolve().parent
HERMES_ROOT = HERE.parent
sys.path.insert(0, str(HERMES_ROOT))

import app.tools.session_archive as session_archive
from app.tools.build_report import build_report_html  # noqa: E402
from app.tools.session_archive import load_all_data  # noqa: E402


def find_session(slug: str, session_root: Path) -> Path:
    """Найти директорию сессии по slug."""
    candidate = session_root / slug
    if candidate.is_dir():
        return candidate
    matches = sorted(session_root.glob(f"{slug}*"))
    if matches:
        return matches[0]
    raise FileNotFoundError(f"Session '{slug}' not found in {session_root}")


def wrap_inner_html(inner: str, title: str) -> str:
    """Обернуть inner HTML из build_report_html в полный документ для standalone просмотра.

    build_report_html возвращает только содержимое <body> + inline <style>.
    Для локального просмотра нужно добавить DOCTYPE, <head> с Google Fonts, и обёртку.
    """
    # Извлекаем inline <style> из inner (если есть)
    style_block = ""
    if "<style>" in inner and "</style>" in inner:
        start = inner.index("<style>")
        end = inner.index("</style>") + len("</style>")
        style_block = inner[start:end]
        inner_without_style = inner[:start] + inner[end:]
    else:
        inner_without_style = inner

    return f"""<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Jost:wght@400;500;600&family=Playfair+Display:wght@400;500;600&display=swap" rel="stylesheet">
    <style>
        body {{
            margin: 0;
            padding: 0;
            background: #f5f5f5;
        }}
        body > div {{
            background: var(--bg);
        }}
        /* Простая страница без шапки WP — для отладки верстки */
        .__preview_header {{
            background: #fff;
            border-bottom: 1px solid #E0E0E0;
            padding: 12px 24px;
            font-family: 'Jost', sans-serif;
            font-size: 11px;
            color: #767676;
            letter-spacing: 0.1em;
            text-transform: uppercase;
        }}
        .__preview_header strong {{
            color: #1A1A1A;
        }}
    </style>
    {style_block}
</head>
<body>
    <div class="__preview_header">
        AIM Scout — <strong>{title}</strong> &nbsp;·&nbsp; Standalone preview (no WP theme)
    </div>
    {inner_without_style}
</body>
</html>"""


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate standalone HTML preview for visual debugging.")
    parser.add_argument("slug", help="Session slug (e.g. mira-med-1783003747)")
    parser.add_argument(
        "--session-root",
        type=Path,
        default=HERMES_ROOT / "_reference",
        help=f"Root for sessions (default: {HERMES_ROOT / '_reference'})",
    )
    parser.add_argument(
        "--out",
        type=Path,
        default=None,
        help="Output HTML path (default: ./preview-{slug}.html)",
    )
    parser.add_argument("--no-open", action="store_true", help="Do not open in browser")
    parser.add_argument("--quiet", "-q", action="store_true", help="Less output")
    args = parser.parse_args()

    session_dir = find_session(args.slug, args.session_root)
    slug = session_dir.name
    if not args.quiet:
        print(f"[i] Session: {session_dir}")

    # Подменяем SESSIONS_ROOT модуля чтобы load_all_data нашла нашу сессию
    session_archive.SESSIONS_ROOT = str(args.session_root)
    data = load_all_data(slug)
    if not data or len(data) <= 1:
        # fallback на прямое чтение data.json
        data_json_path = session_dir / "data.json"
        if data_json_path.exists():
            with open(data_json_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            if not args.quiet:
                print(f"[i] Loaded via data.json fallback")
        else:
            print(f"[!] No data found in {session_dir}", file=sys.stderr)
            return 1

    meta = data.get("metadata", {}) or {}
    title = meta.get("company_name") or meta.get("client_name") or slug
    if not args.quiet:
        print(f"[i] Title: {title}")

    # Генерируем inner HTML
    inner_html = build_report_html(data, title)

    # Оборачиваем в полный документ для standalone просмотра
    full_html = wrap_inner_html(inner_html, title)

    out_path = args.out or (Path.cwd() / f"preview-{slug}.html")
    out_path.write_text(full_html, encoding="utf-8")
    print(f"[✓] Wrote {len(full_html):,} bytes → {out_path}")

    if not args.no_open:
        url = f"file://{out_path.resolve()}"
        if not args.quiet:
            print(f"[i] Opening in browser: {url}")
        webbrowser.open(url)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
