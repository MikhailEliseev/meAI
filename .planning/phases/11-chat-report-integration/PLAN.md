# PLAN.md — Phase 11: Chat Report Integration

> **Phase:** 11
> **Milestone:** 3 (Chat Report Delivery)
> **Created:** 2026-07-22
> **Depends on:** Phase 10 (WordPress Publisher) ✅, Phase 9 (HTML Builder) ✅

---

## Goal

Когда чат hermes-v2 завершает анализ (собраны данные по 4 блокам: профиль, конкуренты, отзывы, аудит), автоматически:
1. Сгенерировать HTML-отчёт через готовый `build_report_html()`
2. Опубликовать на iamaim.ru/{slug} через готовый `publish_report()`
3. Отправить SSE-событие `report-ready` с URL на фронтенд
4. Показать карточку отчёта в чате с кнопкой «Открыть отчёт»

---

## Architecture

### Data Flow

```
chat_with_tools() in llm.py
   │
   ├─ [существующее] LLM стримит токены → ("text", str)
   ├─ [существующее] Tool вызовы → ("tool_start"/"tool_result")
   ├─ [существующее] Форматированные блоки → ("formatted", str)
   │
   ├─ [НОВОЕ] Перед yield("finish",):
   │   ├─ Проверка: enough_data? (find_competitors в collected_results)
   │   ├─ build_data_dict(collected_results, profile_cache, llm_text)
   │   ├─ build_report_html(data, title)
   │   ├─ await publish_report(html, title)
   │   └─ yield ("report_ready", url, title)
   │
   └─ [существующее] yield ("finish",)
                                │
                                ▼
event_generator() in main.py
   │
   ├─ [существующее] ("text", ...) → SSE text-delta
   ├─ [существующее] ("tool_start", ...) → SSE tool-progress
   ├─ [НОВОЕ] ("report_ready", url, title) → SSE report-ready
   └─ [существующее] ("finish",) → SSE finish
                                │
                                ▼
chat-inline.php (фронтенд)
   │
   ├─ [существующее] text-delta → стриминг в bubble
   ├─ [существующее] tool-progress → статус
   ├─ [НОВОЕ] report-ready → renderReportCard(data)
   │   └─ карточка с кнопкой «Открыть отчёт»
   └─ [существующее] finish → завершение
```

---

## Задачи

### Task 1: Backend — автопубликация отчёта в `llm.py`

**Файл:** `AIM/hermes-v2/app/llm.py`
**Где:** В `chat_with_tools()`, после anti-hallucination check (~line 901) и **перед** `yield ("finish",)` (line 903).

**Логика:**
```python
# ── Авто-публикация отчёта ──────────────────────────────────────────────────
# Срабатывает когда есть достаточно данных (минимум find_competitors).
# Не срабатывает на «привет/как дела» сообщениях.
REPORT_TRIGGER_TOOLS = {"find_competitors"}  # минимум — конкурентный анализ

if REPORT_TRIGGER_TOOLS.issubset(collected_results.keys()):
    try:
        from app.report_builder import build_data_dict, build_report_html, publish_report
        llm_text_str = "".join(llm_text) if isinstance(llm_text, list) else (llm_text or "")
        data = build_data_dict(collected_results, profile_cache, llm_text_str)
        title = profile_cache.get("company_name") or "Клиника"
        html = build_report_html(data, title)
        result = await publish_report(html, title)
        if result.get("url"):
            yield ("report_ready", result["url"], title)
    except Exception as e:
        logger.warning("Auto-publish report failed: %s", e)
        # Не блокируем finish при ошибке публикации
```

**Гварды:**
- `collected_results` должен содержать `find_competitors` (иначе это не полный анализ)
- Все ошибки логируются, но НЕ прерывают поток (`try/except`)
- Дубли-защита: если в `profile_cache` уже есть `_report_published_url` — пропустить

**ВАЖНО (багфикс):** На line 591 есть `collected_results = {}` внутри параллельного блока, который сбрасывает результаты. Проверить что к моменту line 901 в `collected_results` есть `find_competitors`. Если нет — брать из `profile_cache["_raw_result"]` или иным путём.

### Task 2: Backend — новый SSE event type в `main.py`

**Файл:** `AIM/hermes-v2/app/main.py`
**Где:** В `event_generator()`, после обработки `"formatted"` (~line 170) и **до** `finish`.

**Логика:**
```python
elif kind == "report_ready":
    # ("report_ready", url, title)
    report_url = event[1] if len(event) > 1 else ""
    report_title = event[2] if len(event) > 2 else ""
    yield f"data: {json.dumps({
        'type': 'report-ready',
        'url': report_url,
        'title': report_title,
        'summary': f'Полный разбор: {report_title}' if report_title else 'Полный разбор клиники',
    }, ensure_ascii=False)}\n\n"
```

**Порядок критичен:** `report-ready` должен прийти **до** `finish`, чтобы фронтенд ещё слушал поток.

### Task 3: Frontend — обработка `report-ready` в `chat-inline.php`

**Файл:** `AIM/theme/chat-inline.php`
**Где:** В SSE parsing loop, после `suggestions` handler (~line 1478).

**Логика:**
```javascript
if (data.type === 'report-ready' && data.url) {
    // Карточка уже есть в CSS (.report-ready-card) и JS (renderReportCard)
    const cardHtml = renderReportCard({
        summary: data.summary || data.title || 'Полный разбор сайта, конкурентов и рынка',
        session_url: data.url,
        archived_at: new Date().toLocaleDateString('ru-RU'),
    });
    // Добавляем карточку в текущее ассистент-сообщение
    assistantMessage += '\n\n' + cardHtml;
    // Обновляем DOM
    updateAssistantBubble(assistantMessage);
}
```

**Использует СУЩЕСТВУЮЩИЕ:**
- `renderReportCard()` (chat-inline.php:969-989)
- CSS `.report-ready-card` (chat-inline.php:316-389)

### Task 4: Гвард дубликатов в `llm.py`

**Проблема:** Если пользователь отправит ещё одно сообщение в той же сессии, отчёт может опубликоваться повторно.

**Решение:** Добавить флаг в `profile_cache`:
```python
# После успешной публикации:
profile_cache["_report_published_url"] = result["url"]

# В начале автопубликации:
if profile_cache.get("_report_published_url"):
    return  # Уже опубликован, пропускаем
```

### Task 5: Тесты

**Файл:** `AIM/hermes-v2/tests/test_phase11_chat_report.py`

**Тест-кейсы:**
1. `test_enough_data_trigger`: collected_results с `find_competitors` → триггер срабатывает
2. `test_insufficient_data_skip`: collected_results без `find_competitors` → триггер пропускается (не падает)
3. `test_publish_failure_no_crash`: publish_report падает → поток не прерывается, finish уходит
4. `test_duplicate_guard`: повторный вызов с тем же profile_cache → не публикует повторно
5. `test_report_ready_event_format`: yield ("report_ready", url, title) → корректный формат
6. `test_main_sse_format`: event_generator с report_ready → SSE `data: {"type":"report-ready",...}`

**Моки:**
- `publish_report` → мок-функция возвращающая `{"status":"published","url":"https://iamaim.ru/test"}`
- `build_report_html` → мок возвращающий `"<html>...</html>"`

### Task 6: Smoke-тест на проде

**Сценарий:**
1. Открыть iamaim.ru (чат)
2. Отправить URL клиники (например arclinic.ru)
3. Дождаться завершения анализа (~5 минут)
4. Проверить: в чате появилась карточка с кнопкой «Открыть отчёт»
5. Кликнуть → открывается отчёт на iamaim.ru/{slug}
6. Проверить логи: `docker logs aim-hermes-v2 | grep "report"`

---

## Out of Scope (отложено)

- **Phase 12: Скачать отчёт (PDF/HTML)** — следующая фаза
- **Phase 13: QC Critique** — проверка качества перед публикацией
- **Telegram integration** — отдельный milestone
- **Auth/sessions** — отдельный milestone

---

## Risks

| Risk | Impact | Mitigation |
|------|--------|------------|
| `collected_results` reset bug (llm.py:591) | Профиль не попадает в отчёт | Проверить данные в логах перед публикацией; adapter.py fallback на `profile_cache["_raw_result"]` |
| MySQL медленный → задержка `finish` | Юзер ждёт ответа дольше | `publish_report` в `try/except`, timeout 5s уже в publisher.py |
| Дубликат отчёта при re-ask | Мусор в wp_posts | Гвард `profile_cache["_report_published_url"]` (Task 4) |
| chat-inline.php кэш браузера | Фронт не видит новый handler | Версионирование через `?v=` в URL или cache-bust |

---

## Acceptance Criteria

- [ ] При отправке URL клиники в чат, в конце анализа появляется карточка отчёта
- [ ] Карточка содержит кнопку «Открыть отчёт» → кликабельная ссылка на iamaim.ru/{slug}
- [ ] Отчёт содержит 4 секции: профиль, обзор, конкуренты, отзывы
- [ ] При «привет» сообщении отчёт НЕ публикуется (нет `find_competitors`)
- [ ] При ошибке публикации чат продолжает работать (не падает)
- [ ] При повторном сообщении в той же сессии отчёт НЕ дублируется
- [ ] 6/6 unit-тестов PASS
- [ ] Smoke-тест на проде: карточка появляется, ссылка работает

---

## Files to Modify

| File | Changes |
|------|---------|
| `AIM/hermes-v2/app/llm.py` | + автопубликация перед finish (Task 1, 4) |
| `AIM/hermes-v2/app/main.py` | + SSE report-ready event (Task 2) |
| `AIM/theme/chat-inline.php` | + report-ready handler (Task 3) |
| `AIM/hermes-v2/tests/test_phase11_chat_report.py` | NEW: 6 тестов (Task 5) |

---

## Estimated Effort

- Task 1-2 (backend): ~2 часа
- Task 3 (frontend): ~30 минут
- Task 4 (guard): ~15 минут
- Task 5 (tests): ~1 час
- Task 6 (smoke): ~30 минут
- **Итого: ~4-5 часов**
