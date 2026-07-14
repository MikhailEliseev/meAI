# Phase 2: Диалоговый сервер + промпт — Summary

**Phase:** 02-dialogue-server-prompt
**Plan:** 02-01
**Completed:** 2026-07-14
**Status:** ✅ COMPLETE — Гермес «заговорил», помнит контекст, сессии изолированы

---

## Что сделано

Контейнер `aim-hermes-v2` ожил: принимает чат-сообщения через `POST /api/chat/stream` (SSE), стримит ответы LLM, хранит историю per-session в SQLite. Модель общается текстом по системному промпту Гермеса.

**Главное доказательство** — диалог с памятью:
```
Шаг 1: «Меня зовут Михаил. Запомни моё имя.»
       → Гермес отвечает (38 токенов)
Шаг 2 (тот же session_id): «Как меня зовут?»
       → «Михаил.»  ← помнит!
Шаг 3 (ДРУГОЙ session_id): «Как меня зовут?»
       → «не знаю, ты не представился»  ← изолирован!
```

---

## Доказательства (evidence)

### DIALOG-01: SSE-эндпоинт
`POST /api/chat/stream` → `text/event-stream`. События `text-delta` (38 в тесте), `finish` (с session_id), `error`. Формат совместим с Theme-чатом (`useStreamChat.js`).

### DIALOG-02: LLM через Z.AI
- Модель: **`glm-5.2`** (НЕ deepseek-chat — расхождение со спекой, см. Замечания).
- Шлюз: `OMNIROUTE_URL=https://api.z.ai/api/coding/paas/v4`.
- Логи: 4 `stream_chat` вызова.

### DIALOG-03: Системный промпт активен
На «привет» Гермес отвечает «Я Гермес — AI-ассистент маркетингового агентства...». Промпт в `app/prompts/dialogue.py`.

### DIALOG-04: История в SQLite
`/opt/data/sessions.db`, таблица `messages`, WAL mode. Шаг 2 помнит имя из шага 1.

### DIALOG-05: Per-session изоляция
`_session_locks: dict[session_id → asyncio.Lock]`. Другой session_id НЕ видит чужую историю (шаг 3 доказал).

### Регрессия Phase 1
`/health` ✅, `/tools/find-competitors` (2 конкурента) ✅ — не сломано.

---

## Замечания / нюансы (ВАЖНО для следующих фаз)

1. **Модель `glm-5.2`, а не `deepseek-chat`** — спека и ROADMAP говорили deepseek-chat, но продакшн-сервер использует Z.AI-шлюз с `glm-5.2`. Расхождение обнаружено в деплое (400 «Unknown Model»). Поправил на glm-5.2 как у работающего старого hermes. **Спеку надо обновить** — Phase 3+ использует glm-5.2.

2. **OMNIROUTE_AUTH — отдельный Z.AI токен** (из `.env.production`), НЕ DeepSeek-ключ. Изначально заложил fallback `DEEPSEEK_API_KEY` — это была ошибка (разные ключи). Убрал fallback. `OMNIROUTE_AUTH` приходит через `env_file: .env.production`.

3. **Compose env правки Phase 2** (сервер + локально):
   - `OMNIROUTE_URL` хардкод `https://api.z.ai/...` (как у старого hermes, в env-файлах его нет)
   - `LLM_MODEL=glm-5.2`
   - `env_file` добавлен `.env.keys` (для DEEPSEEK_API_KEY, хотя LLM его не использует)

4. **Streaming работает** — клиент видит печатающийся текст (38 токенов в реальном ответе). UX важен.

---

## Артефакты

| Файл | Назначение |
|---|---|
| `app/prompts/dialogue.py` | SYSTEM_PROMPT — характер Гермеса, политика, питч AIM |
| `app/llm.py` | `stream_chat(history)` → async gen токенов; `get_client()` lazy init |
| `app/session.py` | SQLite: `init_db`, `load_history`, `save_message`, `get_session_lock` |
| `app/main.py` | расширен: `POST /api/chat/stream` (SSE), сохраняет Phase 1 маршруты |
| `app/config.py` | +OMNIROUTE_AUTH, SESSIONS_DB_PATH |
| `tests/test_llm.py` | 3 теста: системный промпт, стриминг, None-delta |
| `tests/test_session.py` | 4 теста: init_db, round-trip, изоляция, per-session lock |
| `requirements.txt` | +openai |
| `AIM/docker-compose.yml` | фиксы env: OMNIROUTE_URL хардкод, LLM_MODEL=glm-5.2, .env.keys |

---

## Покрытые требования

| ID | Требование | Статус |
|---|---|---|
| DIALOG-01 | SSE /api/chat/stream (text-delta, finish, error) | ✅ |
| DIALOG-02 | LLM через Z.AI (нативный streaming) | ✅ glm-5.2 |
| DIALOG-03 | Системный промпт «база → кнопки → по запросу» + питч AIM | ✅ |
| DIALOG-04 | История в SQLite, keyed by session_id | ✅ |
| DIALOG-05 | Per-session состояние (не глобальная очередь) | ✅ |
| TOLS-11 | (перенесено в Phase 3 — tool-calling) | ⏳ |

---

## Rollback план

```bash
# откат к Phase 1 (без чата):
ssh aim "cd /opt/aim/AIM && cp docker-compose.yml.bak-phase2-20260714-170757 docker-compose.yml && docker compose up -d hermes-v2"
# данные sessions.db сохранены (можно не трогать)
```

---

## Что дальше (Phase 3)

Перенос всех 10 тулов: 7 толстых (Perplexity, Apify, Firecrawl, Playwright, WordPress) + 3 прокси. Tool-calling оркестрация — модель вызывает тулы по описанию. find_competitors из Phase 1 подключается к LLM.

---

*Phase 02 — Plan 02-01 — COMPLETE*
