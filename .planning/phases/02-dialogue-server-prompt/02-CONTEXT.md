# Phase 2: Диалоговый сервер + промпт — Context

**Gathered:** 2026-07-14
**Status:** Ready for planning
**Source:** Spec `2026-07-14-hermes-interactive-redesign-design.md` (разделы 5, 7) + ROADMAP + REQUIREMENTS + Phase 1 results

<domain>
## Phase Boundary

Контейнер `aim-hermes-v2` (из Phase 1) оживает: начинает принимать чат-сообщения и отвечать через LLM. Модель общается текстом по системному промпту, история хранится per-session в SQLite. Тулзы пока НЕ подключаются (кроме `find_competitors` из Phase 1 как proof — но без tool-calling оркестрации; модель просто текстом отвечает).

**Что входит в Phase 2:**
- `POST /api/chat/stream` — SSE-эндпоинт, совместимый с Theme-чатом (форматы событий `text-delta`, `finish`, `error`)
- LLM-клиент `deepseek-chat` через Z.AI-шлюз (OpenAI-совместимый SDK), стриминг токенов
- Системный промпт «база → кнопки → по запросу» + питч услуг AIM (раздел 5 спеки)
- SQLite-хранилище истории диалога, keyed by `session_id`
- Per-session состояние (не глобальная очередь — исправление бага старого `main.py:47`)

**Что НЕ входит в Phase 2 (явно):**
- Tool-calling оркестрация (модель НЕ вызывает тулзы автоматически — это Phase 3)
- Перенос остальных 9 тулов (Phase 3)
- Кнопки suggestions в SSE (Phase 4)
- Сборка отчётов (Phase 5)
- Деплой/переключение nginx (Phase 6)
- Суммаризация истории при >20 сообщениях (отложено — Phase 3/4)

</domain>

<decisions>
## Implementation Decisions (locked)

### LLM-клиент — сырой openai SDK, БЕЗ hermes-agent
- Старый hermes использовал библиотеку `hermes-agent==0.14.0` (SDK-обёртка над OpenAI). Phase 2 пишет с нуля — используем **сырой `openai` Python SDK** (нативно поддерживает streaming + tool-calling + Z.AI-шлюз через `base_url`).
- Зависимость: добавить `openai` в requirements.txt (кроме fastapi/uvicorn/httpx из Phase 1).
- Z.AI-шлюз: `base_url=OMNIROUTE_URL` (=`https://api.z.ai/api/coding/paas/v4`), `api_key=OMNIROUTE_AUTH` (=DEEPSEEK_API_KEY). Модель `deepseek-chat`.
- Streaming: `client.chat.completions.create(..., stream=True)` → итерация `chunk.choices[0].delta.content`.

### SSE-формат — копия старого hermes (точные имена событий)
Фронт Theme-чата (`useStreamChat.js:251-315`) парсит эти события — НЕЛЬЗЯ менять имена:
- `data: {"type":"text-delta","textDelta":"<token>"}` — стриминг текста
- `data: {"type":"finish","session_id":"<id>"}` — конец ответа
- `data: {"type":"error","message":"..."}` — ошибка
- (Phase 4 добавит `suggestions`; Phase 3 — `tool-progress`)
- Источник истины: бэкап `main.py:554,556,561` — точный формат yield'ов.

### SQLite — сырой sqlite3 (не SQLAlchemy)
- Старый hermes использовал SQLAlchemy+aiosqlite (`main.py:255`). Phase 2 упрощает: **сырой `sqlite3`** (синхронный, в отдельном потоке через `asyncio.to_thread` — БД локальная, I/O быстрый).
- Меньше зависимостей (нет sqlalchemy/aiosqlite), проще дебажить.
- Схема: одна таблица `messages (session_id TEXT, role TEXT, content TEXT, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)`. Индекс на `session_id`.
- Файл БД: `/opt/data/sessions.db` (на volume `/opt/hermes-v2-data`).

### Per-session состояние (исправление бага DIALOG-05)
- Старый баг: `_tool_progress_queue` — одна на процесс (`main.py:47`), сессии смешивались.
- Phase 2: состояние сессии хранится в SQLite + in-memory dict `session_id → lock`. Каждый запрос берёт lock для своего session_id, не блокируя другие.
- `session_id` — client-supplied (как в старом hermes).

### Эндпоинт
- `POST /api/chat/stream` с body `{session_id: str, message: str}`.
- Response: `text/event-stream` (SSE).
- Flow: загрузить историю из SQLite → добавить сообщение пользователя → вызвать LLM (stream) → стримить токены в SSE → по завершении сохранить ответ ассистента в SQLite → `finish` событие.

### Системный промпт — из спеки раздел 5 (адаптация)
Копия промпта из спеки, с пометкой что тулзы пока недоступны (Phase 2 — только диалог). Промпт в отдельном модуле `app/prompts/dialogue.py`.

### Claude's Discretion
- Структура модулей (один `app/llm.py` или разделить)
- Детали thread-safety (asyncio.Lock per session vs sqlite с WAL mode)
- Формат `error` event (message text)
- Health-check расширение (добавить проверку БД?)

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Спека
- `docs/superpowers/specs/2026-07-14-hermes-interactive-redesign-design.md` — раздел 5 (системный промпт), раздел 7 (сессии: per-session, session_id client-supplied, баг глобальной очереди)

### Phase 1 (фундамент, НЕ пересматривать)
- `.planning/phases/01-walking-skeleton-health-1/01-01-SUMMARY.md` — что уже работает (FastAPI app, /health, find_competitors прокси)
- `AIM/hermes-v2/app/main.py` — текущая структура FastAPI-приложения (расширяем, не переписываем)
- `AIM/hermes-v2/app/config.py` — env-заготовки УЖЕ содержат OMNIROUTE_URL, LLM_MODEL (использовать их)

### Реальные паттерны из бэкапа (КОПИРОВАТЬ, не угадывать)
- `~/Desktop/Dev/meAI_1-backups/extracted/aim-chat-system-20260714-133205/hermes-container-code/app/main.py:554,556,561` — ТОЧНЫЙ формат SSE yield'ов (`text-delta`, `finish`)
- `~/Desktop/Dev/meAI_1-backups/extracted/aim-chat-system-20260714-133205/hermes-container-code/app/agent_wrapper.py:55-57` — env OMNIROUTE_URL/AUTH/DEFAULT_MODEL паттерн
- `AIM/theme/chat/src/useStreamChat.js:251-315` — фронт парсит события: `text-delta`, `tool-progress`, `phase-progress`, `finish`, `report-ready`, `error`

### REQUIREMENTS
- `.planning/REQUIREMENTS.md` — DIALOG-01..05, TOLS-11

</canonical_refs>

<specifics>
## Specific Ideas

- Контейнер уже healthy (Phase 1). Phase 2 = добавить LLM-логику БЕЗ пересоздания образа-фундамента (но пересборка образа нужна — добавится `openai` dep).
- `find_competitors` из Phase 1 НЕ убираем — но в Phase 2 модель его пока НЕ вызывает (нет tool-calling). Он пригодится в Phase 3.
- Промпт должен явно говорить «ты пока не можешь вызывать инструменты» — иначе модель будет галлюцинировать вызовы.
- Тестовый сценарий Phase 2: «Привет» → Гермес отвечает осмысленно (кто он, чем занимается AIM). «А что ты умеешь?» → перечисляет возможности. Повторный запрос с тем же session_id → помнит контекст.
- Streaming важен UX-wise — клиент видит печатающийся текст (не ждёт 10с до полного ответа).

</specifics>

<deferred>
## Deferred Ideas (не в Phase 2)

- Tool-calling оркестрация — модель вызывает тулзы автоматически (Phase 3)
- Перенос 9 тулов (Phase 3)
- Суммаризация истории >20 сообщений (Phase 3/4)
- Кнопки suggestions в SSE (Phase 4)
- Сборка HTML-отчёта (Phase 5)
- Деплой на прод / nginx (Phase 6)
- Контекстное окно management (Phase 3+)

</deferred>

---

*Phase: 02-dialogue-server-prompt*
*Context gathered: 2026-07-14*
