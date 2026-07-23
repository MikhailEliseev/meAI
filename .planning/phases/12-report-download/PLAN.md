# PLAN.md — Phase 12: Report Download

> **Создан:** 2026-07-23
> **Milestone:** 3 (Chat Report Delivery)
> **Предыдущая фаза:** Phase 11 (Chat Report Integration) ✅

---

## Цель

Добавить кнопку **«Скачать отчёт»** в карточку отчёта в чате. При клике — скачивается HTML-файл с отчётом (или PDF, если успеем).

**Ценность для пользователя:**
- Клиент может скачать отчёт и пересматривать офлайн
- Можно переслать отчёт руководству по почте/мессенджеру
- Архивация отчётов для долгосрочного хранения

---

## Scope

### In Scope

1. **Backend:** Эндпоинт `/api/report/{slug}/download` (FastAPI)
   - Возвращает HTML с `Content-Disposition: attachment; filename="report-{slug}.html"`
   - Читает отчёт из MySQL (`wp_posts` по slug)
   - Self-contained HTML (инлайн CSS + JS через CDN)

2. **Frontend:** Кнопка «Скачать отчёт» в карточке (chat-inline.php)
   - Добавляется рядом с «Открыть отчёт»
   - Иконка: 📥 или ⬇️
   - При клике: `window.location = '/api/report/{slug}/download'`

3. **Self-contained HTML:**
   - Инлайнить критичный CSS (AIM Design System)
   - Внешние шрифты через CDN (Google Fonts)
   - Theme toggle через inline JS

4. **Тесты:**
   - Unit-тест: `/download` возвращает корректный HTML + headers
   - E2E: кнопка есть, клик скачивает файл

### Out of Scope (Phase 13+)

- **PDF конвертация** — требует headless Chrome (Playwright/Puppeteer), +20MB образа. Оставим на Phase 13.
- **Batch download** (скачать несколько отчётов) — не запрошено
- **Email delivery** — отдельная фича

---

## Tasks

### Task 1: Backend — эндпоинт `/api/report/{slug}/download`

**Файл:** `AIM/hermes-v2/app/main.py`

**Что делать:**
```python
@app.get("/api/report/{slug}/download")
async def download_report(slug: str):
    """Скачивание отчёта как HTML-файл.
    
    Читает HTML из MySQL wp_posts, возвращает с Content-Disposition: attachment.
    """
    from app.report_builder.publisher import get_report_html_by_slug
    
    html = await get_report_html_by_slug(slug)
    if not html:
        raise HTTPException(status_code=404, detail="Report not found")
    
    # Self-contained HTML: инлайним критичный CSS
    html_with_inline_css = inject_inline_styles(html)
    
    headers = {
        "Content-Disposition": f'attachment; filename="report-{slug}.html"',
        "Content-Type": "text/html; charset=utf-8",
    }
    return Response(content=html_with_inline_css, headers=headers, media_type="text/html")
```

**Новая функция в `publisher.py`:**
```python
async def get_report_html_by_slug(slug: str, db_config: dict | None = None) -> str | None:
    """Читает HTML отчёта из MySQL по slug."""
    config = db_config or _get_wp_db_config()
    conn = await aiomysql.connect(**config)
    try:
        async with conn.cursor() as cur:
            await cur.execute(
                "SELECT post_content FROM wp_posts WHERE post_name = %s AND post_type = 'page' LIMIT 1",
                (slug,)
            )
            row = await cur.fetchone()
            return row[0] if row else None
    finally:
        conn.close()
```

**Функция `inject_inline_styles(html: str)`:**
- Читает `report_builder/report_template.html` → берёт `<style>` блок
- Инлайнит в скачиваемый HTML через BeautifulSoup или regex

---

### Task 2: Frontend — кнопка в карточке отчёта

**Файл:** `AIM/theme/chat-inline.php`

**Где:** Функция `renderReportCard()` (строка ~970)

**Было:**
```html
<a href="${url}" target="_blank" class="report-ready-link">
    <span>📋</span>
    <span>Открыть полный отчёт</span>
    <span>→</span>
</a>
```

**Станет:**
```html
<div class="report-ready-actions">
    <a href="${url}" target="_blank" class="report-ready-link">
        <span>📋</span>
        <span>Открыть полный отчёт</span>
        <span>→</span>
    </a>
    <a href="/api/report/${url.split('/').pop()}/download" class="report-ready-link report-ready-download">
        <span>📥</span>
        <span>Скачать отчёт</span>
    </a>
</div>
```

**CSS (добавить рядом с `.report-ready-link`):**
```css
.report-ready-actions {
    display: flex;
    gap: 8px;
    flex-wrap: wrap;
}

.report-ready-download {
    background: linear-gradient(135deg, #10b981 0%, #059669 100%);
}

.report-ready-download:hover {
    background: linear-gradient(135deg, #059669 0%, #047857 100%);
}
```

---

### Task 3: Self-contained HTML (инлайн CSS)

**Файл:** `AIM/hermes-v2/app/report_builder/inline_styles.py` (NEW)

**Функция:**
```python
def inject_inline_styles(html: str) -> str:
    """Инлайнит критичный CSS в HTML для self-contained файла.
    
    Берёт CSS из report_template.html <style> блока, инлайнит в <head>.
    """
    from pathlib import Path
    template_path = Path(__file__).parent / "report_template.html"
    with open(template_path, "r", encoding="utf-8") as f:
        template = f.read()
    
    # Извлечь <style>...</style> из template
    import re
    style_match = re.search(r"<style>(.*?)</style>", template, re.DOTALL)
    if not style_match:
        return html  # Нет стилей — возвращаем как есть
    
    inline_css = style_match.group(1)
    
    # Вставить в <head> скачиваемого HTML
    head_close = html.find("</head>")
    if head_close == -1:
        return html  # Нет </head> — невалидный HTML
    
    html_with_styles = (
        html[:head_close]
        + f"\n<style>\n{inline_css}\n</style>\n"
        + html[head_close:]
    )
    return html_with_styles
```

---

### Task 4: Тесты

**Файл:** `AIM/hermes-v2/tests/test_phase12_download.py` (NEW)

**Тест-кейсы:**
1. `test_download_endpoint_returns_html` — GET `/api/report/{slug}/download` → 200, HTML
2. `test_download_headers` — проверить `Content-Disposition: attachment`
3. `test_download_not_found` — GET с несуществующим slug → 404
4. `test_inline_styles_present` — скачанный HTML содержит `<style>` с `.report-container`
5. `test_frontend_button_exists` — `renderReportCard()` возвращает кнопку «Скачать»

**Моки:**
- `get_report_html_by_slug` → возвращает тестовый HTML
- MySQL connection → мокнуть через `aiomysql` fixtures

---

### Task 5: E2E smoke-тест

**Сценарий:**
1. Открыть iamaim.ru (чат)
2. Отправить URL клиники (или взять существующую сессию с отчётом)
3. Проверить: карточка содержит 2 кнопки («Открыть», «Скачать»)
4. Кликнуть «Скачать» → браузер скачивает `report-{slug}.html`
5. Открыть файл локально → отчёт рендерится корректно (стили, шрифты)

---

## Acceptance Criteria

- [ ] Эндпоинт `/api/report/{slug}/download` возвращает HTML с `Content-Disposition: attachment`
- [ ] HTML self-contained (инлайн CSS, CDN шрифты)
- [ ] Карточка в чате содержит кнопку «Скачать отчёт»
- [ ] Клик по кнопке скачивает файл `report-{slug}.html`
- [ ] Скачанный файл открывается локально и рендерится корректно
- [ ] 5/5 unit-тестов PASS
- [ ] E2E smoke-тест: кнопка работает, файл скачивается

---

## Files to Modify

| File | Changes |
|------|---------|
| `AIM/hermes-v2/app/main.py` | + GET `/api/report/{slug}/download` |
| `AIM/hermes-v2/app/report_builder/publisher.py` | + `get_report_html_by_slug()` |
| `AIM/hermes-v2/app/report_builder/inline_styles.py` | NEW: `inject_inline_styles()` |
| `AIM/theme/chat-inline.php` | + кнопка «Скачать» в `renderReportCard()` |
| `AIM/hermes-v2/tests/test_phase12_download.py` | NEW: 5 тестов |

---

## Estimated Effort

- Task 1-2 (backend + frontend): ~1 час
- Task 3 (inline CSS): ~30 минут
- Task 4 (тесты): ~30 минут
- Task 5 (E2E): ~15 минут

**Итого:** ~2-2.5 часа

---

## Risks

| Risk | Impact | Mitigation |
|------|--------|------------|
| Скачанный HTML не рендерится (CSS не инлайнится) | Кнопка бесполезна | Task 3 проверяет через regex/BeautifulSoup, Task 5 — локальный рендер |
| MySQL read timeout при большом HTML | Download зависает | Установить timeout=5s в `aiomysql.connect()` |
| CDN шрифтов недоступен офлайн | Fallback на system fonts | В CSS добавить `font-family: Inter, system-ui, sans-serif` |

---

## Out of Scope → Phase 13

- **PDF конвертация:** Требует Playwright/Puppeteer (~20MB Docker image). Если захотят — отдельная фича.
- **Email delivery:** "Отправить отчёт на почту" — не запрошено.
- **Watermark:** "Downloaded from AIM" — не критично.

---

## Notes

- **Self-contained HTML:** Критично для офлайн-просмотра. Инлайним только AIM Design System CSS (~10KB), шрифты через CDN (Google Fonts).
- **Filename:** `report-{slug}.html` — уникальный, читаемый.
- **Security:** Slug уже публичный (отчёт на iamaim.ru/{slug}), так что `/download` не требует auth.
