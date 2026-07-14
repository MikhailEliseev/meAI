# ROADMAP.md — Гермес v2

**Дата:** 2026-07-14
**Режим:** Vertical MVP (каждая фаза — end-to-end срез)
**Гранулярность:** standard
**Спека:** `docs/superpowers/specs/2026-07-14-hermes-interactive-redesign-design.md`

---

## Phases

| # | Phase | Goal | Requirements |
|---|-------|------|--------------|
| 1 | Walking Skeleton: контейнер + health + 1 тул | Минимальный end-to-end: контейнер v2 поднимается, отвечает /health, один тул (find_competitors) реально зовёт aim-app и возвращает данные | INFRA-01..05, TOLS-02 |
| 2 | Диалоговый сервер + промпт | FastAPI /api/chat/stream + deepseek-chat + системный промпт. Гермес отвечает на сообщения, хранит сессии в SQLite | DIALOG-01..05, TOLS-11 |
| 3 | Перенос всех 10 тулов | 7 толстых тулов перенесены из бэкапа + 3 прокси. Модель может их вызывать по запросу | TOLS-01,03..10,12 |
| 4 | Базовый сценарий (база → кнопки → по запросу) | URL → quick_overview + find_competitors → рынок + top-3 за ≤4 мин. Кнопки suggestions в SSE | FLOW-01..04, CHAT-01,05 |
| 5 | Кнопки в Theme-чате + сборка отчёта | Фронтенд рендерит кнопки, клик шлёт текст. generate_html_report собирает отчёт из сессии | CHAT-02..04, FLOW-05,06, REPORT-01..03 |
| 6 | Деплой на прод + переключение nginx | v2 на проде, nginx переключён, старый контейнер выключен но готов к откату | DEPLOY-01..05 |

---

## Phase Details

### Phase 1: Walking Skeleton — контейнер + health + 1 тул
**Goal:** Минимальный end-to-end рабочий срез. Новый контейнер aim-hermes-v2 поднимается, проходит healthcheck, и ОДИН тул (find_competitors) реально делает HTTP к aim-app:8000 и возвращает данные конкурентов. Доказывает, что вся инфраструктура (docker network, env, aim-app доступность) работает.
**Mode:** mvp
**Requirements:** INFRA-01, INFRA-02, INFRA-03, INFRA-04, INFRA-05, TOLS-02
**Plans:** 1 plan
Plans:
- [ ] 01-01-PLAN.md — FastAPI-приложение hermes-v2 + thin-wrapper find_competitors + Dockerfile + сервис в docker-compose + деплой на ssh aim с end-to-end верификацией
**Success Criteria:**
1. `docker compose up -d hermes-v2` поднимает контейнер без ошибок
2. `curl http://aim-hermes-v2:8000/health` (из docker network) → 200
3. `curl http://aim-hermes-v2:8000/tools/find-competitors?url=<тестовый>` возвращает JSON с массивом конкурентов (brand_name, rating) — реальный ответ от aim-app
4. Логи контейнера показывают успешный HTTP-запрос к aim-app:8000

### Phase 2: Диалоговый сервер + промпт
**Goal:** Контейнер принимает чат-сообщения через POST /api/chat/stream (SSE), ведёт диалог через deepseek-chat с системным промптом «база → кнопки → по запросу». История сессий в SQLite. На этой фазе модель общается текстом, но тулзы пока не подключены (кроме одного из Phase 1).
**Mode:** mvp
**Requirements:** DIALOG-01, DIALOG-02, DIALOG-03, DIALOG-04, DIALOG-05, TOLS-11
**Success Criteria:**
1. `POST /api/chat/stream` с {message: "привет"} возвращает SSE-стрим с text-delta + finish
2. Гермес отвечает осмысленно (по промпту — что он AI-ассистент AIM)
3. Повторный запрос с тем же session_id — модель помнит контекст (SQLite)
4. Разные session_id не смешиваются (per-session, не глобальная очередь)

### Phase 3: Перенос всех 10 тулов
**Goal:** Все 10 инструментов доступны модели через tool-calling. 7 толстых перенесены из бэкапа (hermes-container-code/app/tools/) с адаптацией импортов. Модель может вызывать любой тул по описанию.
**Mode:** mvp
**Requirements:** TOLS-01, TOLS-03, TOLS-04, TOLS-05, TOLS-06, TOLS-07, TOLS-08, TOLS-09, TOLS-10, TOLS-12
**Success Criteria:**
1. Каждый из 10 тулов зарегистрирован в OpenAI function-schema
2. Тестовый запрос «проверь упоминания в СМИ для <url>» → модель вызывает run_smi_mentions → реальный ответ
3. Каждый tool-schema содержит «когда вызывать» (when to call)
4. find_competitors вызывается не более одного раза за сессию

### Phase 4: Базовый сценарий (база → кнопки → по запросу)
**Goal:** Клиент присылает URL → Гермес за ≤4 минуты делает базу (quick_overview + find_competitors) → показывает рынок + top-3 конкурента → эмитит SSE-событие suggestions с 2-4 релевантными кнопками. Питч услуг AIM в конце.
**Mode:** mvp
**Requirements:** FLOW-01, FLOW-02, FLOW-03, FLOW-04, CHAT-01, CHAT-05
**Success Criteria:**
1. URL → базовый ответ за ≤4 минуты (стримится прогресс)
2. База содержит: чем занимается клиника, город, специализация, ключевые цифры рынка, top-3 конкурента (имя+rating+match_reason)
3. SSE содержит событие suggestions с 2-4 кнопками
4. Кнопки адаптивны (плохой сайт → «тех.аудит» в списке)
5. В конце базы — короткий питч услуг AIM

### Phase 5: Кнопки в Theme-чате + сборка отчёта
**Goal:** Фронтенд Theme-чата рендерит кнопки под сообщениями, клик шлёт текстом → Гермес вызывает тул. generate_html_report собирает отчёт из session_archive и публикует в WordPress.
**Mode:** mvp
**Requirements:** CHAT-02, CHAT-03, CHAT-04, FLOW-05, FLOW-06, REPORT-01, REPORT-02, REPORT-03
**Success Criteria:**
1. useStreamChat.js обрабатывает suggestions → рендерит кнопки
2. Клик по кнопке → новое сообщение → модель вызывает соответствующий тул
3. «Собрать отчёт» → generate_html_report → HTML-отчёт с публичным URL
4. Tool-results пишутся в /opt/hermes-v2-data/sessions-archive/{hash}/

### Phase 6: Деплой на прод + переключение nginx
**Goal:** v2 полностью на проде: rsync, build, up. nginx переключён на aim-hermes-v2:8000. Старый aim-hermes выключен, но контейнер и образ сохранены для отката.
**Mode:** mvp
**Requirements:** DEPLOY-01, DEPLOY-02, DEPLOY-03, DEPLOY-04, DEPLOY-05
**Success Criteria:**
1. rsync переносит код на сервер без ошибок
2. docker compose build hermes-v2 && docker compose up -d hermes-v2 на проде работает
3. nginx конфиг переключён, https://iamaim.ru чат ходит в v2
4. Старый aim-hermes остановлен (docker ps не показывает), но образ aim-hermes:latest сохранён
5. Откат: переключение nginx обратно + docker compose up -d hermes за <2 минуты

---
