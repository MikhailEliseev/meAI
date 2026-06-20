# Hermes v7 — Баг-трекер (отладка)

## Контекст
PipelineEngine задеплоен и протестирован на psyholog48.ru. 14/14 фаз работают.
Теперь ручное тестирование чата на iamaim.ru.

Дата: 2026-06-19

---

## Баги

### 🐛 #1 — chat-bundle.js: `Dynamic require of "react" is not supported`
**Где:** `/wp-content/themes/aim-theme/assets/js/chat-bundle.js`
**Что произошло:** В консоли ошибка, `#hermes-chat` не рендерится. Бандл использует `require("react")` вместо статического импорта.
**Что ожидалось:** React-чат должен рендериться в `#hermes-chat` без ошибок.
**Как воспроизвести:** Открыть любую страницу с `#hermes-chat` контейнером (не главную — на главной чат работает через `#chat-emerge`).
**Статус:** 🔴 новый

### 🐛 #2 — AIM API возвращает 500/400 на несколько инструментов
**Где:** `app:8000` (aim-app контейнер)
**Что произошло:** При вызове инструментов:
- `run_seo_audit` → 500 Internal Server Error — **ИСПРАВЛЕНО:** PYTHONPATH дополнен `/app/src` (docker-compose.override.yml)
- `run_content_analysis` → 500 Internal Server Error — **ИСПРАВЛЕНО:** та же причина
- `find_competitors` → 422 Unprocessable Entity — **ИСПРАВЛЕНО:** `named_competitors` теперь передаётся как `list[str]` а не `str`
- `run_ci_analysis` → "at least one competitor is required" — **ИСПРАВЛЕНО:** `_extract_competitors_for_ci` теперь получает partial_results из той же фазы
**Статус:** 🟢 исправлено (19.06.2026)

### 🐛 #3 — SSE-сессия обрывается до завершения пайплайна
**Где:** `/api/chat/stream`
**Что произошло:** SSE Generator cleanup в 14:53:26, а пайплайн завершился только в 14:57:27. Клиент не получил финальный поток текста.
**Причина:** Тестовый запрос шёл через `/api/chat` (синхронный), а не SSE. Возможно, чат на главной использует синхронный эндпоинт.
**Как воспроизвести:** Отправить URL через чат на главной
**Статус:** 🔴 новый — нужно проверить, какой эндпоинт использует `chat-inline.php`

### 🐛 #4 — LLM вызывает несуществующий инструмент `web_search`
**Где:** Hermes tool registry
**Что произошло:** Модель попыталась вызвать `web_search`, которого нет в aim-operations.
**Реакция:** "Unknown tool 'web_search' — sending error to model for self-correction (1/3)"
**Влияние:** Минимальное — модель получает ошибку и корректируется. Но увеличивает latency.
**Статус:** 🟡 минорный — не актуально для v7 (PipelineEngine вызывает инструменты напрямую, без LLM)

### 🐛 #5 — `find_competitors` вызван без названия клиники
**Где:** PipelineEngine фаза COMPETITORS
**Что произошло:** `named: None` — клиент не указал название. Поиск только по URL.
**Исправлено:** `_resolve_client_name()` авто-извлекает название из домена (erasmile.ru → EraSmile)
**Статус:** 🟢 исправлено (19.06.2026)

### 🐛 #6 — `publish_scout_report`: "Scout data not found"
**Где:** PipelineEngine фаза PRESENTATION
**Что произошло:** `publish_scout_report` искал данные в `/opt/data/competitors/{slug}/data.json`, а pipeline сохраняет в `/opt/data/sessions-archive/{slug}/`.
**Исправлено:**
1. `_build_tool_params` для `publish_scout_report` извлекает URL из HTML BUILD фазы
2. Хендлер `publish_scout_report` принимает `url` + `already_published` — возвращает URL без дублирования
**Статус:** 🟢 исправлено (19.06.2026)

### 🐛 #7 — Firecrawl: все ключи исчерпаны (402 Payment Required)
**Где:** `web_search` (фазы PERPLEXITY, FORUM PAINS)
**Что произошло:** Все 3 ключа Firecrawl вернули 402. 14 дополнительных ключей есть в `.env` но не загружены в контейнер.
**Влияние:** `web_search` возвращает fallback-результаты (Perplexity через LLM), пайплайн не падает.
**Статус:** 🟡 operational — нужно загрузить дополнительные ключи

---

## Исправления (19.06.2026)

### Итерация 1: Параметры инструментов
1. **`named_competitors`: list вместо str** — `engine.py:421`: `params["named_competitors"] = [name]`
2. **PYTHONPATH** — `docker-compose.override.yml`: добавлен `/app/src` (meai модуль)
3. **`run_ci_analysis` → partial_results** — `engine.py`: `_build_tool_params` принимает `partial_results` для same-phase зависимостей; `_extract_competitors_for_ci` проверяет и accumulated_data, и partial_results
4. **`publish_scout_report` → already_published** — `engine.py`: извлекает URL из HTML BUILD; `publish_scout_report.py`: хендлер принимает `url` + `already_published`

### Результаты тестирования
- **test-ci-fix-v2:** 14/14 фаз, ~5 мин, отчёт: https://iamaim.ru/2oxn0s0x
- **test-final-v1:** 14/14 фаз, отчёт: https://iamaim.ru/66jb4hdt
- `run_ci_analysis`: 2407 chars (было 48 chars "at least one competitor is required")
- `publish_scout_report`: "already_published" (было "Scout data not found")

---

## Заметки по UX

- Чат на главной работает через vanilla JS (`chat-inline.php`), НЕ через React-бандл
- `chat-bundle.js` всё ещё загружается (13KB) но рендерится только в `#hermes-chat`, которого нет на главной
- Между отправкой URL и первым ответом — пауза ~20s (PERPLEXITY), пользователь не видит промежуточного прогресса
