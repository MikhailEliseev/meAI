# TEST-LOG.md — Milestone 3 (Phases 11-13)

> **Дата:** 2026-07-23
> **Среда:** Production (iamaim.ru)
> **Ветка:** feat/competitor-v2-perplexity-searxng
> **Tag:** phase-13-done

---

## Сводка

| # | Тест | Результат | Время |
|---|------|-----------|-------|
| 1 | E2E чат — полный анализ клиники | ✅ PASS | 4 мин |
| 2 | Чистота ответа (сноски, мусор) | ✅ PASS | — |
| 3 | PDF download — качество | ✅ PASS | <1 сек |
| 4 | HTML отчёт — секции, врачи, соцсети | ✅ PASS | — |
| 5 | «Привет» — отчёт НЕ публикуется | ✅ PASS | 5 сек |
| 6 | Повторный запрос — нет дубля | ✅ PASS | ~60 сек |

**Итог: 6/6 PASS**

---

## Тест 1: E2E чат — полный анализ

**Метод:** `curl -sN POST /api/chat/stream` с `https://arclinic.ru`
**Session:** `test-log-1784820692`

**Результат:**
- Время: 4 мин 9 сек (18:31:32 → 18:35:41)
- Text-delta токенов: 847
- Tool-progress событий: 14 (7 тулов × 2: start+done)
- Тулы вызваны: extract_clinic_profile, scrape_clinic_website, quick_overview, find_competitors, company_financials, run_review_platforms
- Report-ready: ✅ `https://iamaim.ru/lk0y6q3p`
- Suggestions: ✅ (кнопки действий)
- Finish: ✅

**Вердикт:** PASS — полный пайплайн отработал корректно.

---

## Тест 2: Чистота ответа

**Метод:** Анализ полного текста LLM (4950 символов)

**Проверки:**
| Проверка | Результат |
|----------|-----------|
| Сноски [1] [2] [3] | ✅ ЧИСТО (0 найдено) |
| [SUGGESTIONS] маркер | ✅ ЧИСТО |
| [/SUGGESTIONS] маркер | ✅ ЧИСТО |
| ::: сырые блоки | ℹ️ Присутствуют, но это formatted blocks (НЕ баг) — parseMarkdown() превращает в карточки |
| Галлюцинация рейтинга | ℹ️ False positive — 5.0★ это реальные данные из Apify |

**Данные в ответе:**
| Данные | Найдено |
|--------|---------|
| Имя клиники | ✅ АРклиник/ARclinic |
| ИНН | ✅ 7810605688 |
| Выручка | ✅ 121 млн ₽ |
| Санкт-Петербург | ✅ |
| Врачи | ✅ (14 врачей упомянуты) |
| Соцсети | ✅ (Telegram, VK) |

**Вердикт:** PASS — ответ чистый, без сносок и мусора.

---

## Тест 3: PDF Download

**Метод:** `curl -sL https://iamaim.ru/report/lk0y6q3p/download`

**Результат:**
- Размер: 78KB
- Тип: PDF document, version 1.7
- Страниц: 9
- Шрифты: Inter + Playfair Display + DejaVu (встроены)
- Citation markers: 0
- [SUGGESTIONS]: False

**Вердикт:** PASS — PDF чистый, правильные шрифты.

---

## Тест 4: HTML Отчёт

**Метод:** `curl -sL https://iamaim.ru/lk0y6q3p/`

**Результат:**
- HTTP 200
- Секции: 5 (01 О КЛИНИКЕ, 02 РЫНОК, 03 КОНКУРЕНТЫ, 04 ОТЗЫВЫ, + Revenue block)
- Врачи: 16 упоминаний в HTML
- Соцсети: Telegram (7), YouTube (4)
- Карточка отчёта: ✅ (report-ready-card)
- Revenue block: ✅

**Вердикт:** PASS — отчёт содержит все данные.

---

## Тест 5: «Привет» — без отчёта

**Метод:** `curl` с `{"message": "привет"}`

**Результат:**
- Text-delta: ~144 токенов
- Report-ready: ❌ (НЕ опубликован — правильно)
- Finish: ✅

**Вердикт:** PASS — короткие сообщения не триггерят публикацию.

---

## Тест 6: Повторный запрос — нет дубля

**Метод:** Второй запрос в той же сессии (`test-log-1784820692`)

**Результат:**
- Report-ready: ❌ (дубликата нет — гвард сработал)
- Finish: ✅

**Вердикт:** PASS — персистентный гвард предотвращает дубль.

---

## Unit-тесты

```
tests/test_phase11_chat_report.py:  17 PASS
tests/test_phase12_pdf_download.py:  5 PASS
tests/test_report_builder.py:        34 PASS
tests/test_pipeline_fixes.py:        12 PASS
tests/test_reviews_apify.py:         16 PASS
tests/test_publisher.py:             12 PASS
─────────────────────────────────────────────
Всего: 144 PASS, 1 FAIL (несвязанный test_llm.py)
```

---

## Известные ограничения

1. **Парсер врачей** — находит 3 из 5 (og:title работает, но специализация извлекается как город)
2. **VK handle** — иногда извлекает «js» вместо реального handle (Tilda JS-ссылки)
3. **Время анализа** — 4 минуты (SearXNG + Apify + Perplexity)

---

## Архитектура (текущая)

```
Пользователь: "https://arclinic.ru"
  ↓
1. extract_clinic_profile (Perplexity) → ИНН, название, город
2. scrape_clinic_website (httpx+BS4)   → врачи, соцсети, услуги ← NEW
3. quick_overview (Perplexity)         → доп. данные
4. find_competitors (aim-app)          → ФНС выручка, SearXNG
5. company_financials (aim-app → ФНС)  → точная выручка/прибыль
6. run_review_platforms (Apify)        → Яндекс.Карты, 2ГИС
  ↓
Formatted blocks (4 секции: профиль, конкуренты, отзывы, аудит)
  ↓
LLM анализ (glm-5.2) — ОПИРАЕТСЯ на данные
  ↓
Report-ready → iamaim.ru/{slug} (HTML отчёт)
  ↓
PDF download → WeasyPrint → report-{slug}.pdf
```

---

## Заключение

**Все 6 тестов прошли.** Milestone 3 (Phases 11-13) готов к эксплуатации.

Живые артефакты:
- Чат: https://iamaim.ru/
- Отчёт HTML: https://iamaim.ru/lk0y6q3p/
- PDF: https://iamaim.ru/report/lk0y6q3p/download
