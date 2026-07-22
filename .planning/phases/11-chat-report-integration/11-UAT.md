# 11-UAT.md — Phase 11: Chat Report Integration

> **Дата:** 2026-07-22
> **Тестирующий:** Claude (automated)
> **Tag:** `phase-11-review-fixed`

---

## Сводка результатов

| # | Тест | Результат |
|---|------|-----------|
| UAT-1 | URL клиники → карточка отчёта появляется | ✅ PASS |
| UAT-2 | Карточка содержит кликабельную ссылку на iamaim.ru/{slug} | ✅ PASS |
| UAT-3 | Отчёт содержит 4 секции (профиль, обзор, конкуренты, отзывы) | ✅ PASS |
| UAT-4 | «Привет» → отчёт НЕ публикуется | ✅ PASS |
| UAT-5 | При ошибке публикации чат не падает | ✅ PASS |
| UAT-6 | Повторное сообщение → отчёт НЕ дублируется | ✅ PASS |
| UAT-7 | Все unit-тесты PASS (17/17) | ✅ PASS |
| UAT-8 | Smoke-тест на проде (визуально) | ✅ PASS |

**Итог:** 8/8 PASS. Phase 11 готова к релизу.

---

## Детали тестов

### UAT-1: URL клиники → карточка отчёта появляется ✅

**Метод:** E2E через `curl -sN POST /api/chat/stream` с `https://arclinic.ru`
**Session:** `uat-full-test`

**Результат:**
```
Event types:
  1 "type": "finish"
  1 "type": "report-ready"     ← КЛЮЧЕВОЕ
  1 "type": "suggestions"
  677 "type": "text-delta"
  10 "type": "tool-progress"
```

**report-ready event:**
```json
{"type": "report-ready", "url": "https://iamaim.ru/btu2vneu", "title": "ARclinic", "summary": "Полный разбор: ARclinic"}
```

**Вердикт:** PASS — отчёт автоматически опубликован, URL получен.

---

### UAT-2: Карточка содержит кликабельную ссылку ✅

**Метод:** `curl -sI https://iamaim.ru/btu2vneu`

**Результат:** `HTTP/2 301` → постоянный редирект на `/btu2vneu/`

**Вердикт:** PASS — URL работает, отчёт доступен.

---

### UAT-3: Отчёт содержит 4 секции ✅

**Метод:** `curl -s https://iamaim.ru/btu2vneu/ | grep section-label`

**Результат:**
- ✅ «01 — О КЛИНИКЕ»
- ✅ «02 — РЫНОК»
- ✅ «03 — КОНКУРЕНТЫ»
- ✅ «04 — ОТЗЫВЫ»
- ✅ Revenue block (сравнение с конкурентами)
- ✅ CTA-box
- ✅ Footer

**Вердикт:** PASS — все 4 секции + дополнительные блоки.

---

### UAT-4: «Привет» → отчёт НЕ публикуется ✅

**Метод:** E2E через `curl -sN POST /api/chat/stream` с `привет`
**Session:** `uat-negative-test`

**Результат:**
```
Event types:
  1 "type": "finish"
  1 "type": "suggestions"
  144 "type": "text-delta"
```

`report-ready` отсутствует.

**Вердикт:** PASS — короткие сообщения без анализа не триггерят публикацию.

---

### UAT-5: При ошибке публикации чат не падает ✅

**Метод:** Симуляция `WP_DB_PASSWORD=invalid_password` в контейнере

**Результат:**
```
Result: {'status': 'error', 'error': 'Database error: (1045, "Access denied...")'}
```

`publish_report` возвращает `status: error` без исключения.

Unit-тест `test_auto_publish_report_failure_no_crash` подтверждает: `_auto_publish_report` не падает, `finish` уходит.

**Вердикт:** PASS — ошибки БД изолированы, чат продолжает работать.

---

### UAT-6: Повторное сообщение → отчёт НЕ дублируется ✅

**Метод:**
1. Первый запрос: `https://arclinic.ru` (session: `uat-full-test`) → отчёт опубликован (post_id=233)
2. Второй запрос: `расскажи подробнее про конкурентов` (та же session)

**Результат (логи hermes-v2 за 8 минут):**
```
2026-07-22 16:29:47 Report published: slug=btu2vneu post_id=233
2026-07-22 16:29:47 Auto-publish: report ready at https://iamaim.ru/btu2vneu
2026-07-22 16:29:47 SSE: emitting report-ready url=https://iamaim.ru/btu2vneu
```

Только **ОДНА** публикация. Второй запрос не вызвал `Auto-publish` (гвард сработал через `[REPORT_READY]` маркер в history).

**Вердикт:** PASS — персистентный гвард (W-3 fix) работает корректно.

---

### UAT-7: Все unit-тесты PASS ✅

**Метод:** `python -m pytest tests/test_phase11_chat_report.py -v`

**Результат:** 17/17 PASS (0.36s)

Ключевые тесты:
- `test_auto_publish_report_success` — happy path
- `test_auto_publish_report_failure_no_crash` — error handling
- `test_trigger_skip_without_find_competitors` — negative trigger
- `test_duplicate_guard_prevents_republish` — guard logic
- `test_w1_no_collected_results_reset` — W-1 regression
- `test_w2_frontend_pendingReportReady_pattern` — W-2 regression
- `test_w3_db_guard_in_main_py` — W-3 implementation
- `test_i2_report_marker_persisted_to_db` — I-2 implementation

**Вердикт:** PASS — все тесты зелёные.

---

### UAT-8: Smoke-тест на проде (визуально) ✅

**Метод:** Открыть `https://iamaim.ru/btu2vneu/` в Chrome DevTools

**Результат:**
- ✅ Hero с заголовком «ARclinic»
- ✅ 4 секции с section-labels
- ✅ Revenue block (сравнение с конкурентами)
- ✅ CTA-box с кнопкой «Связаться в Telegram»
- ✅ Footer с лого AIM
- ✅ Title: «AIM — ARclinic – AIM»

**Дополнительно:** Проверена персистентность в БД — `[REPORT_READY]` маркер сохранён в assistant message (5110 символов), содержит URL и summary.

**Вердикт:** PASS — отчёт рендерится корректно на проде.

---

## Дополнительные проверки (code review fixes)

| Fix | Тест | Результат |
|-----|------|-----------|
| W-1: collected_results reset | `test_w1_no_collected_results_reset` | ✅ Кода-переприсваивания нет |
| W-2: Frontend RAF race | `test_w2_frontend_pendingReportReady_pattern` | ✅ handler не вставляет в SSE loop |
| W-2: Post-stream insert | `test_w2_frontend_post_stream_insert` | ✅ Вставка после removeStreamingBubble |
| W-3: DB guard | `test_w3_db_guard_in_main_py` + UAT-6 | ✅ Персистентный гвард работает |
| I-2: URL в БД | `test_i2_report_marker_persisted_to_db` + DB check | ✅ Маркер сохраняется |
| Duplicate guard | `test_duplicate_guard_works_with_history` | ✅ Detects existing report |
| No false positive | `test_no_false_positive_in_clean_history` | ✅ Clean history → no guard |

---

## Известные ограничения

1. **Telegram бот** — не получает report-ready events (использует v1, не v2). Вне scope Phase 11.
2. **PDF download** — кнопка «Скачать отчёт» не реализована (Phase 12).
3. **QC critique** — проверка качества перед публикацией не реализована (Phase 13).

---

## Заключение

**Phase 11: Chat Report Integration — ✅ ВЫПРОБОВАН И ГОТОВ.**

Все 8 acceptance criteria выполнены. Все 4 code review fix (W-1, W-2, W-3, I-2) верифицированы.

**Следующий шаг:** Phase 12 (Report Download) — кнопка «Скачать отчёт» (PDF/HTML).
