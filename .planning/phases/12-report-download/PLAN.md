# PLAN.md — Phase 12: Report Download (PDF)

> **Создан:** 2026-07-23
> **Обновлён:** 2026-07-23 (PDF через WeasyPrint)
> **Milestone:** 3 (Chat Report Delivery)
> **Предыдущая фаза:** Phase 11 (Chat Report Integration) ✅

---

## Цель

Добавить кнопку **«Скачать PDF»** в карточку отчёта в чате. При клике — скачивается PDF-файл отчёта через **WeasyPrint** (HTML→PDF конвертация).

**Ценность для пользователя:**
- Клиент получает профессиональный PDF-отчёт для презентации руководству
- Можно печатать, архивировать, пересылать по почте
- Универсальный формат (открывается везде, офлайн-просмотр)

---

## Scope

### In Scope

1. **Backend:** Эндпоинт `/api/report/{slug}/download` (FastAPI)
   - Возвращает PDF с `Content-Disposition: attachment; filename="report-{slug}.pdf"`
   - Читает HTML из MySQL (`wp_posts` по slug)
   - Конвертирует HTML→PDF через **WeasyPrint**
   - WeasyPrint: Python-библиотека, ~15MB зависимостей, поддержка CSS @media print

2. **Frontend:** Кнопка «Скачать PDF» в карточке (chat-inline.php)
   - Добавляется рядом с «Открыть отчёт»
   - Иконка: 📥 или ⬇️
   - При клике: `window.location = '/api/report/{slug}/download'`

3. **PDF-оптимизация CSS:**
   - `@media print` стили для WeasyPrint
   - Page breaks (avoid break inside cards)
   - Оптимизация шрифтов (system fonts для PDF, не CDN)
   - Footer с нумерацией страниц

4. **Тесты:**
   - Unit-тест: `/download` возвращает PDF + headers
   - Проверка MIME type: `application/pdf`
   - E2E: кнопка есть, клик скачивает PDF

### Out of Scope

- **HTML download** — только PDF (проще для пользователя)
- **Playwright/Puppeteer** — избегаем +200MB Chromium
- **Batch download** (несколько отчётов) — не запрошено
- **Email delivery** — отдельная фича

---

## Tasks

### Task 1: Установка WeasyPrint

**Файл:** `AIM/hermes-v2/requirements.txt`

Добавить:
```
weasyprint==60.2
```

**Dockerfile:** Установить системные зависимости (Cairo, Pango)
```dockerfile
RUN apt-get update && apt-get install -y \
    libcairo2 \
    libpango-1.0-0 \
    libpangocairo-1.0-0 \
    libgdk-pixbuf2.0-0 \
    libffi-dev \
    shared-mime-info \
    && rm -rf /var/lib/apt/lists/*
```

Размер: ~15-20MB дополнительно к образу.

---

### Task 2: Backend — эндпоинт `/api/report/{slug}/download`

**Файл:** `AIM/hermes-v2/app/main.py`

```python
from fastapi.responses import Response
from weasyprint import HTML, CSS

@app.get("/api/report/{slug}/download")
async def download_report_pdf(slug: str):
    """Скачивание отчёта как PDF через WeasyPrint.
    
    Читает HTML из MySQL wp_posts, конвертирует в PDF.
    """
    from app.report_builder.publisher import get_report_html_by_slug
    from app.report_builder.pdf_converter import html_to_pdf
    
    html = await get_report_html_by_slug(slug)
    if not html:
        raise HTTPException(status_code=404, detail="Report not found")
    
    # HTML→PDF через WeasyPrint
    pdf_bytes = html_to_pdf(html)
    
    headers = {
        "Content-Disposition": f'attachment; filename="report-{slug}.pdf"',
        "Content-Type": "application/pdf",
    }
    return Response(content=pdf_bytes, headers=headers, media_type="application/pdf")
```

---

### Task 3: Функция `get_report_html_by_slug()`

**Файл:** `AIM/hermes-v2/app/report_builder/publisher.py`

Добавить:
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

---

### Task 4: PDF-конвертер через WeasyPrint

**Файл:** `AIM/hermes-v2/app/report_builder/pdf_converter.py` (NEW)

```python
"""PDF-конвертация HTML→PDF через WeasyPrint."""
import logging
from pathlib import Path
from weasyprint import HTML, CSS

logger = logging.getLogger(__name__)

def html_to_pdf(html: str) -> bytes:
    """Конвертирует HTML в PDF через WeasyPrint.
    
    Args:
        html: HTML-строка отчёта (из MySQL wp_posts.post_content)
    
    Returns:
        PDF в виде bytes
    """
    # Загрузить print CSS (если есть отдельный файл)
    print_css_path = Path(__file__).parent / "print.css"
    print_css = CSS(filename=str(print_css_path)) if print_css_path.exists() else None
    
    # HTML→PDF
    html_doc = HTML(string=html)
    pdf_bytes = html_doc.write_pdf(stylesheets=[print_css] if print_css else None)
    
    logger.info("PDF generated: %d bytes", len(pdf_bytes))
    return pdf_bytes
```

---

### Task 5: CSS для PDF (@media print)

**Файл:** `AIM/hermes-v2/app/report_builder/print.css` (NEW)

```css
/* PDF-оптимизация через @media print */
@media print {
    /* Page setup */
    @page {
        size: A4;
        margin: 2cm 1.5cm;
        @bottom-center {
            content: "AIM — Presale Intelligence Report | " counter(page);
            font-size: 10pt;
            color: #64748b;
        }
    }
    
    /* Избегаем разрывов внутри карточек */
    .surface-block,
    .stat-card,
    .section {
        page-break-inside: avoid;
    }
    
    /* Скрыть интерактивные элементы */
    .cta-box,
    .theme-toggle,
    button {
        display: none !important;
    }
    
    /* Упростить шрифты для WeasyPrint */
    * {
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif !important;
    }
    
    /* Цветовая схема для печати */
    body {
        background: white !important;
        color: #1e293b !important;
    }
    
    .report-container {
        max-width: 100%;
        box-shadow: none;
    }
}
```

---

### Task 6: Frontend — кнопка в карточке отчёта

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
        <span>Открыть отчёт</span>
        <span>→</span>
    </a>
    <a href="/api/report/${url.split('/').pop()}/download" class="report-ready-link report-ready-download">
        <span>📥</span>
        <span>Скачать PDF</span>
    </a>
</div>
```

**CSS (добавить):**
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

### Task 7: Тесты

**Файл:** `AIM/hermes-v2/tests/test_phase12_pdf_download.py` (NEW)

**Тест-кейсы:**
1. `test_download_endpoint_returns_pdf` — GET `/api/report/{slug}/download` → 200, PDF
2. `test_download_headers_pdf` — проверить `Content-Type: application/pdf`, `Content-Disposition`
3. `test_download_not_found` — GET с несуществующим slug → 404
4. `test_pdf_content_valid` — PDF начинается с `%PDF-1.` (валидный PDF)
5. `test_frontend_button_exists` — `renderReportCard()` возвращает кнопку «Скачать PDF»

**Моки:**
- `get_report_html_by_slug` → возвращает тестовый HTML
- `html_to_pdf` → возвращает `b'%PDF-1.4...'` (мок PDF)

---

### Task 8: E2E smoke-тест

**Сценарий:**
1. Открыть iamaim.ru (чат)
2. Взять существующую сессию с отчётом (или создать новую)
3. Проверить: карточка содержит 2 кнопки («Открыть», «Скачать PDF»)
4. Кликнуть «Скачать PDF» → браузер скачивает `report-{slug}.pdf`
5. Открыть PDF → проверить:
   - Рендеринг (текст, таблицы, стили)
   - Нумерация страниц в footer
   - Нет интерактивных элементов (кнопок CTA)

---

## Acceptance Criteria

- [ ] WeasyPrint установлен в Docker image (~15-20MB зависимостей)
- [ ] Эндпоинт `/api/report/{slug}/download` возвращает PDF с `Content-Type: application/pdf`
- [ ] PDF содержит корректный `Content-Disposition: attachment; filename="report-{slug}.pdf"`
- [ ] Карточка в чате содержит кнопку «Скачать PDF»
- [ ] Клик по кнопке скачивает файл `report-{slug}.pdf`
- [ ] PDF открывается корректно (текст, таблицы, стили)
- [ ] PDF имеет нумерацию страниц в footer
- [ ] 5/5 unit-тестов PASS
- [ ] E2E smoke-тест: кнопка работает, PDF скачивается и рендерится

---

## Files to Modify

| File | Changes |
|------|---------|
| `AIM/hermes-v2/requirements.txt` | + `weasyprint==60.2` |
| `AIM/hermes-v2/Dockerfile` | + Cairo/Pango системные зависимости |
| `AIM/hermes-v2/app/main.py` | + GET `/api/report/{slug}/download` |
| `AIM/hermes-v2/app/report_builder/publisher.py` | + `get_report_html_by_slug()` |
| `AIM/hermes-v2/app/report_builder/pdf_converter.py` | NEW: `html_to_pdf()` через WeasyPrint |
| `AIM/hermes-v2/app/report_builder/print.css` | NEW: `@media print` стили |
| `AIM/theme/chat-inline.php` | + кнопка «Скачать PDF» в `renderReportCard()` |
| `AIM/hermes-v2/tests/test_phase12_pdf_download.py` | NEW: 5 тестов |

---

## Estimated Effort

- Task 1 (WeasyPrint setup): ~15 минут
- Task 2-4 (backend PDF): ~1 час
- Task 5 (print CSS): ~30 минут
- Task 6 (frontend кнопка): ~15 минут
- Task 7 (тесты): ~30 минут
- Task 8 (E2E): ~15 минут

**Итого:** ~2.5-3 часа

---

## Risks

| Risk | Impact | Mitigation |
|------|--------|------------|
| WeasyPrint не поддерживает сложный CSS (gradients, backdrop-filter) | PDF выглядит упрощённо | `print.css` с fallback-стилями для PDF |
| Шрифты Inter не доступны в WeasyPrint | Используется system font | Явно указать `font-family: sans-serif` в print.css |
| PDF генерация медленная (>5 сек) | Timeout | Установить `timeout=10s` в эндпоинте, оптимизировать HTML |
| Docker image +20MB | Дольше деплой | Приемлемо, альтернатива (Playwright) — +200MB |

---

## Notes

- **WeasyPrint vs Playwright:** WeasyPrint легче (+15MB vs +200MB), быстрее (~500ms vs ~2-3s), не требует Chromium. Минус: не исполняет JS (theme toggle не работает в PDF, но это OK — печать всегда светлая тема).
- **@media print:** WeasyPrint отлично поддерживает CSS print media queries. Используем для page breaks, footer с нумерацией, скрытия интерактивных элементов.
- **Filename:** `report-{slug}.pdf` — уникальный, читаемый, профессиональный.
- **Security:** Slug публичный (отчёт на iamaim.ru/{slug}), так что `/download` не требует auth.
- **Альтернатива (если WeasyPrint не справится):** Можем добавить fallback на Playwright в Task 4, но сначала попробуем WeasyPrint.
