# REVIEW.md — Phase 11: Chat Report Integration

> **Дата:** 2026-07-22
> **Depth:** standard
> **Файлов рассмотрено:** 4 (llm.py, main.py, chat-inline.php, test_phase11_chat_report.py)

---

## Сводка

| Severity | Count |
|----------|-------|
| 🔴 Critical | 0 |
| 🟡 Warning | 3 |
| 🔵 Info | 3 |

**Вердикт:** Код пригоден к продакшену. Найденные проблемы — Warning (ухудшают UX, но не ломают функциональность) и Info (стиль/улучшения).

---

## 🟡 Warning (3)

### W-1: `collected_results` reset bug может потерять `extract_clinic_profile`

**Файл:** `AIM/hermes-v2/app/llm.py:636`
**Severity:** Warning

```python
collected_results = {}  # tool_name → result_str (for formatting)
```

Эта строка переприсваивает `collected_results`, уничтожая результаты `extract_clinic_profile`, который выполняется в Фазе 1 (до параллельного блока). После reset в `collected_results` остаются только `other_tcs` (find_competitors, quick_overview и т.д.), а `extract_clinic_profile` — теряется.

**Влияние на Phase 11:** `build_data_dict()` в `_auto_publish_report()` пытается взять `extract_clinic_profile` из `collected_results` (его там нет → fallback на `profile_cache["_raw_result"]`). Адаптер написан с fallback, поэтому отчёт собирается, но SECTION "01 — О клинике" может оказаться пустой или с данными только из profile_cache (без форматированного блока).

**Рекомендация:** Не менять сейчас (адаптер обрабатывает fallback). Но в следующей итерации заменить `collected_results = {}` на фильтрацию:
```python
# Очищаем только ошибочные результаты, не затирая всю историю
for tc, result in zip(other_tcs, results):
    if isinstance(result, Exception):
        collected_results.pop(tc.function.name, None)
    else:
        collected_results[tc.function.name] = result[1]
```

### W-2: Frontend handler срабатывает до завершения streaming-bubble

**Файл:** `AIM/theme/chat-inline.php:1485`
**Severity:** Warning

`report-ready` event обрабатывается внутри SSE loop, где `assistantMessage` — строка-аккумулятор. В этот момент `RAF loop` (строка 1512) ещё активен и перерисовывает streaming-bubble каждые 16мс на основе `assistantMessage`. Добавление `[REPORT_READY]...` в `assistantMessage` во время RAF loop может вызвать:
1. Однократный «бланк» карточки в streaming-bubble до финального render
2. Если RAF-loop стрельнёт между `assistantMessage += ...` и `renderMessages()`, карточка отрендерится, но потом будет перерисована streaming-bubble без неё

**Фактическое поведение (по E2E тесту):** Работает корректно — `report-ready` приходит ПОСЛЕ последнего text-delta (LLM уже закончил), поэтому RAF-loop либо уже остановлен, либо вот-вот остановится. Но теоретически возможен рэйс.

**Рекомендация:** Не блокирующая проблема. В будущем — добавить проверку `if (streamEnded)` перед вставкой маркера.

### W-3: Дублирование отчёта при multi-round диалогах (гвард не вечный)

**Файл:** `AIM/hermes-v2/app/llm.py:954`
**Severity:** Warning

Гвард `profile_cache.get("_report_published_url")` защищает от дубликатов **в рамках одной сессии**. Но `profile_cache` — это **локальная переменная** в `chat_with_tools()`, она НЕ персистится между HTTP запросами.

Каждый новый `/api/chat/stream` запрос создаёт новый `chat_with_tools()` вызов → новый `profile_cache = {}`. Это значит, что если пользователь отправил URL, получил отчёт, потом задал уточняющий вопрос (новый запрос) — **отчёт опубликуется повторно**, если в collected_results опять окажется `find_competitors`.

**Сценарий:**
1. User: "arclinic.ru" → отчёт опубликован, URL в `profile_cache["_report_published_url"]`
2. User: "расскажи подробнее про конкурентов" → новый запрос, новый `profile_cache = {}`
3. LLM может вызвать `find_competitors` снова → триггер сработает → **дубликат отчёта**

**Фактическая вероятность:** Низкая. `find_competitors` обычно не вызывается повторно в уточняющих вопросах (LLM использует уже известные данные). Но возможна при явном запросе "найди ещё конкурентов".

**Рекомендация:** В будущей итерации — персистировать флаг в сессии БД (через `async_save_message` или отдельное поле в sessions table). На сейчас — приемлемый риск.

---

## 🔵 Info (3)

### I-1: Импорт внутри функции (`from app.report_builder import ...`)

**Файл:** `AIM/hermes-v2/app/llm.py:506`
**Severity:** Info

```python
async def _auto_publish_report(...):
    from app.report_builder import build_data_dict, build_report_html, publish_report
```

Импорт внутри функции — обычно anti-pattern (circular import workaround). Здесь это оправдано: `app.report_builder` может тянуть `app.main` (через publisher), что создало бы circular import на module level.

**Рекомендация:** Оставить как есть. Работает корректно, Python кэширует импорт после первого вызова.

### I-2: SSE event `report-ready` не сохраняется в БД (сессиях)

**Файл:** `AIM/hermes-v2/app/main.py:188-202`
**Severity:** Info

После `report-ready` SSE event, `full_response` (который сохраняется в БД) **не содержит** URL отчёта. Это значит:
- При перезагрузке страницы и восстановлении сессии из БД — пользователь не увидит ссылку на отчёт в истории чата
- Только `[REPORT_READY]` маркер в `assistantMessage` на фронтенде → localStorage сохраняет его → при reload карточка отрендерится

**Но:** Если localStorage очищен, а сессия в БД есть — карточка пропадёт.

**Рекомендация:** В будущей итерации — добавить URL отчёта в сохраняемый assistant message (на backend), либо в отдельное поле sessions table. На сейчас — приемлемо (карточка сохраняется в localStorage).

### I-3: Тесты не покрывают `_auto_publish_report` с реальным `build_data_dict`

**Файл:** `AIM/hermes-v2/tests/test_phase11_chat_report.py`
**Severity:** Info

Тесты мокают `publish_report`, но НЕ мокают `build_data_dict` и `build_report_html`. Это значит:
- Если `build_data_dict` упадёт на невалидных данных — тест упадёт (хорошо — ловит регрессии)
- Но тесты запускают реальный `build_report_html` → каждый тест генерирует ~30KB HTML (медленно)

**Рекомендация:** Для unit-тестов можно замокать и builder. На сейчас — integration-style coverage, приемлемо.

---

## ✅ Что сделано хорошо

1. **Гвард `try/except` вокруг `_auto_publish_report`** — ошибка публикации не блокирует `finish` event. Пользователь всегда получает ответ.
2. **Логирование на 3 уровнях** — `publisher.py`, `_auto_publish_report`, `main.py` логируют каждый шаг. Легко отлаживать.
3. **SSE event приходит ДО `finish`** — правильный порядок, фронтенд успевает обработать.
4. **Использование существующего `[REPORT_READY]` маркера** — не дублирует логику, использует готовый `renderReportCard()` и CSS.
5. **Гвард дубликатов через `profile_cache`** — простая и эффективная защита (с оговоркой W-3).
6. **10 тестов покрывают happy path, ошибки, saved_locally, SSE format, frontend** — хорошая coverage для фичи.

---

## Рекомендации (приоритизированы)

| # | Что | Когда | Сложность |
|---|-----|-------|-----------|
| 1 | W-1: Убрать `collected_results = {}` reset | Следующая итерация | 30 мин |
| 2 | W-3: Персистировать `_report_published_url` в сессии БД | Phase 12 или позже | 1 час |
| 3 | I-2: Сохранять URL отчёта в assistant message БД | Phase 12 | 30 мин |
| 4 | W-2: Добавить `streamEnded` проверку во frontend | Опционально | 15 мин |

---

## Заключение

Phase 11 реализована корректно. Код готов к продакшену. Найденные Warning — это известные ограничения текущей архитектуры (collected_results reset, session persistence), которые не блокируют функциональность, но требуют внимания в будущих итерациях.

**E2E smoke-test подтверждает:** arclinic.ru → авто-публикация → SSE report-ready → URL работает (https://iamaim.ru/4mwsv6w8).

Код ревью завершено. Можно переходить к Phase 12.
