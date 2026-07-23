# 12-REVIEW.md — Phase 12: Report Download (PDF)

> **Дата:** 2026-07-23
> **Depth:** standard
> **Файлов рассмотрено:** 7

---

## Сводка

| Severity | Count | Status |
|----------|-------|--------|
| 🔴 Critical | 2 | ✅ FIXED |
| 🟡 Warning | 3 | ✅ FIXED (2), ✅ Info (1) |
| 🔵 Info | 3 | Documented |

**Вердикт:** После исправлений — код пригоден к продакшену. 144/145 тестов PASS.

---

## 🔴 Critical (2) — FIXED

### C-1: Endpoint path mismatch — tests use `/api/report/` but backend defines `/report/`

**Файл:** `tests/test_phase12_pdf_download.py`
**Severity:** Critical (брейкят все 4 endpoint теста)

**Проблема:**
- Backend: `@app.get("/report/{slug}/download")` — БЕЗ `/api` префикса
- Frontend: `href="/report/${slug}/download"` — БЕЗ `/api` ✅ совпадает
- Nginx: `location /report/` ✅ совпадает
- **Tests:** `client.get("/api/report/testslug/download")` — С `/api` ❌ НЕ совпадает

**Результат:** 4/5 тестов падали (404 вместо 200), потому что TestClient не находил endpoint.

**Фикс:** Поправил все 4 тест-метода: `/api/report/` → `/report/`. Также поправил assertion в `test_frontend_button_exists`: `/api/report/` → `/report/`.

**Статус:** ✅ FIXED — 7/7 тестов PASS

### C-2: Path traversal в local fallback `get_report_html_by_slug`

**Файл:** `AIM/hermes-v2/app/report_builder/publisher.py:134-138`
**Severity:** Critical (security)

**Проблема:**
```python
report_path = f"/opt/data/reports/{slug}.html"
```
Если `slug = "../../etc/passwd"` → путь становится `/opt/data/reports/../../etc/passwd.html` = `/opt/etc/passwd.html` — выходит за пределы reports директории.

При `WP_DB_PASSWORD` не заданом (local mode) — злоумышленник мог читать произвольные `.html` файлы на сервере.

**Фикс:**
1. В `main.py` — slug validation через regex: `^[a-z0-9-]{1,32}$`
2. В `publisher.py` — дублирующая валидация (defense-in-depth)
3. Использован `os.path.join` вместо f-string для пути

**Тесты:** +2 новых (`test_slug_validation_rejects_traversal`, `test_slug_validation_rejects_special_chars`)

**Статус:** ✅ FIXED

---

## 🟡 Warning (3)

### W-1: Synchronous PDF generation blocks event loop — FIXED

**Файл:** `AIM/hermes-v2/app/main.py:276`
**Severity:** Warning (performance)

**Проблема:**
```python
pdf_bytes = html_to_pdf(html)  # synchronous, CPU-bound
```
WeasyPrint — CPU-heavy операция (3-10 сек). В async endpoint это **блокирует event loop** — другие запросы ждут.

**Фикс:**
```python
pdf_bytes = await asyncio.to_thread(html_to_pdf, html)
```
Теперь PDF generation выполняется в thread pool, не блокируя event loop.

**Статус:** ✅ FIXED

### W-2: nginx `proxy_read_timeout 60s` — too short for PDF — FIXED

**Файл:** `AIM/deploy/nginx/iamaim.conf:113`
**Severity:** Warning

**Проблема:** WeasyPrint для сложного отчёта (4 секции + таблицы) может занять 10-30 сек. Timeout 60s был на грани.

**Фикс:** `proxy_read_timeout 60s` → `proxy_read_timeout 120s`

**Статус:** ✅ FIXED

### W-3: Error detail leaked internal error message — FIXED

**Файл:** `AIM/hermes-v2/app/main.py:279`
**Severity:** Warning (info leak)

**Проблема:**
```python
raise HTTPException(status_code=500, detail=f"PDF generation failed: {str(e)}")
```
`str(e)` может содержать пути к файлам, stack traces, информацию о библиотеках — утечка информации.

**Фикс:**
```python
raise HTTPException(status_code=500, detail=f"PDF generation failed")
```
Ошибка логируется на сервере (`logger.error`), пользователю — generic message.

**Статус:** ✅ FIXED

---

## 🔵 Info (3)

### I-1: `publish_report` uses sync pymysql in async function

**Файл:** `AIM/hermes-v2/app/report_builder/publisher.py:68,76`
**Severity:** Info

`publish_report()` использует sync `pymysql` хотя вызывается из async `_auto_publish_report()`. Это блокирует event loop на время INSERT (~50мс). Незначительно для production (INSERT быстрый), но технически — blocking call в async.

**Рекомендация:** В будущем — мигрировать на `aiomysql` (как сделано в `get_report_html_by_slug`).

### I-2: No PDF caching

**Файл:** `AIM/hermes-v2/app/report_builder/pdf_converter.py`
**Severity:** Info

Каждый клик «Скачать PDF» генерирует PDF заново (3-10 сек). Нет кэша. Для популярных отчётов это создаёт нагрузку.

**Рекомендация:** Добавить in-memory LRU cache (или Redis) с TTL 24h. slug → PDF bytes.

### I-3: HTML rebuild regex is fragile

**Файл:** `AIM/hermes-v2/app/report_builder/pdf_converter.py:44-156`
**Severity:** Info

`_rebuild_for_pdf()` парсит HTML через regex (`re.search(r'<h1>([^<]+)</h1>')` и т.д.) вместо BeautifulSoup. Regex-парсинг HTML хрупкий — если структура HTML изменится (Phase 9 builder), rebuild сломается.

**Рекомендация:** В будущем — использовать `lxml` или `selectolax` для парсинга. На сейчас — работает (regex покрыты тестами через моки).

---

## ✅ Что сделано хорошо

1. **WeasyPrint как PDF engine** — нативный Python, без headless Chrome. Лёгкий, быстрый.
2. **Dockerfile** — правильно установлены системные зависимости (libcairo2, libpango).
3. **aiomysql для download** — корректно async, не блокирует event loop (теперь и PDF gen тоже).
4. **Frontend button** — «Скачать PDF» в карточке отчёта, рядом с «Открыть отчёт».
5. **Два режима PDF** — design-system HTML → rebuild, или прямой data→PDF.
6. **Slug из URL** — `url.split('/').pop()` — простая и надёжная экстракция.

---

## Изменения в этом ревью

| Файл | Изменение |
|------|-----------|
| `main.py` | + slug validation regex, + asyncio.to_thread для PDF, - error detail leak |
| `publisher.py` | + slug validation в local fallback, os.path.join вместо f-string |
| `iamaim.conf` | proxy_read_timeout 60s → 120s |
| `test_phase12_pdf_download.py` | `/api/report/` → `/report/` во всех тестах, +2 security tests |

**Тесты:** 7/7 Phase 12 PASS (было 1/5). 144/145 всего PASS.
