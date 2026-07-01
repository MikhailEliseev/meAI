# 10 — Decisions Needed

Вопросы к владельцу продукта (Михаилу), которые требуют решения перед рефакторингом.

---

## 🔴 Блокирующие решения (нужны до Phase E)

### Решение #1: PostgreSQL vs SQLite

**Контекст:**
- PostgreSQL настроен, 45 таблиц создано, **все пустые**
- Auth сломан (volume password ≠ .env password)
- Hermes уже использует SQLite (`/opt/data/state.db`, 32 сессии, 161 сообщение работает стабильно)
- Backend CRM (leads/sales/onboarding/analytics) endpoints формально есть, но **не используются активно** (БД пустая)

**Вопрос:** Какой БД использовать дальше?

**Вариант A: Уйти от PostgreSQL, всё в SQLite**
- ✅ Простота (одна БД, нет auth проблем)
- ✅ Меньше ресурсов (~400 MB RAM экономии)
- ✅ Backup = copy file
- ✅ Достаточно для текущей нагрузки (46 chat/24h)
- ❌ Lose: transactions across services, JSON queries, full-text search scalability
- ❌ Если вдруг рост до 1000+ лидов/мес — придётся возвращать

**Вариант B: Починить PostgreSQL, оставить**
- ✅ Scale до больших объёмов
- ✅ Стандартная DB для FastAPI
- ❌ Сложнее (auth, migrations, monitoring)
- ❌ Сейчас все таблицы пустые

**Вариант C: Гибрид**
- SQLite для Hermes state (как сейчас)
- PostgreSQL для CRM данных (когда начнут использовать)
- Удалить неиспользуемые таблицы (event_bus_*)
- Оставить schema, но убрать expose наружу

**Рекомендация:** Вариант C (гибрид). минимально рискованно, оставляет опции.

---

### Решение #2: aim-frontend (Next.js)

**Контекст:**
- Контейнер `aim-frontend` запущен (47 MB RAM)
- Образ `aim-frontend:latest` 281 MB
- Экспонирует маршруты: `/chat-test`, `/chat-old`, `/chat-new`, `/_next/`
- Реальный landing — это WordPress (front-page.php)
- Чат-продукт — это `chat-inline.php` в WordPress теме + hermes-chat.html

**Вопрос:** Нужен ли Next.js?

**Вариант A: Удалить полностью**
- ✅ Меньше контейнеров (15 → 14)
- ✅ Проще nginx routes
- ✅ WordPress + chat = достаточно
- ❌ Если в Next.js есть страницы без аналогов в WordPress — потеряем

**Вариант B: Оставить**
- ✅ На случай будущих доработок
- ❌ 47 MB RAM просто так

**Вариант C: Оставить, но убрать expose ports**
- Внутренняя сеть только, доступ через Nginx где нужно

**Рекомендация:** Вариант A (удалить). Если landing на WordPress, то Next.js — артефакт прошлой архитектуры.

---

### Решение #3: aim-paperclip (2.76 GB unknown)

**Контекст:**
- Контейнер `aim-paperclip` запущен 37 часов
- Образ `paperclip-paperclip:latest` **2.76 GB**
- Entrypoint: `docker-entrypoint.sh`, Cmd: `paperclipai run`
- В Nginx — отдельный default_server на порту 80 для IP-based доступа
- В CLAUDE.md **не описан вообще**
- Логи показывают: `GET /health 200`, `GET /metrics 403`, `GET / 403`

**Вопрос:** Что это и нужно ли?

**Действия:**
1. Узнать у Михаила: что за `paperclipai`? Когда ставили? Зачем?
2. Проверить access логи nginx для paperclip route
3. Если не используется → удалить контейнер + образ

**Если ответ "не знаю" или "не нужно":** удалить, освободить 2.76 GB.

---

### Решение #4: Phase 09 — деплоить или удалить?

**Контекст:**
- `.current-task` и SESSION.md говорят Phase 09 развёрнута
- Реально: `hermes-chat-pro.html` возвращает **404**
- Backup-файлы от Phase 09 лежат: `main.py.backup-phase09-*` (2 шт)
- В `functions.php` подключены `aim-pro-endpoints.php` (Phase 09 endpoints)
- Phase 09 содержимое: Phase Tracker, Report Preview, Fallback Form

**Вопрос:** Деплоить Phase 09 или удалить упоминания?

**Вариант A: Задеплоить (закончить начатое)**
- Найти `hermes-chat-pro.html` (1020 строк) — должна быть в git history или в backup
- Скопировать на сервер
- Обновить `front-page.php` если нужно
- Smoke test

**Вариант B: Удалить (отказаться)**
- Удалить backup-файлы main.py.backup-phase09-*
- Удалить `aim-pro-endpoints.php`
- Убрать include из `functions.php`
- Обновить `.current-task`

**Вариант C: Оставить в текущем состоянии**
- Backup-файлы не трогать
- `.current-task` обновить на "Phase 09 deferred"

**Рекомендация:** Вариант A или B (явное решение). C — плохой (неопределённость).

---

### Решение #5: HeadroomGuard — возвращать или удалить упоминания?

**Контекст:**
- SESSION.md подробно описывает HeadroomGuard как "текущая конфигурация production"
- Реально: контейнера нет, OMNIROUTE_URL указывает на DeepSeek API напрямую
- Был deploй и откат (видимо)
- LLM_MODEL в SESSION.md = `glm-5`, реально = `deepseek-v4-pro`

**Вопрос:** Возвращать HeadroomGuard?

**Вариант A: Возвращать**
- Заново развернуть sidecar (compose файл есть)
- Переключить Hermes на прокси
- Протестировать компресию токенов

**Вариант B: Удалить (остановиться на DeepSeek direct)**
- Обновить SESSION.md — убрать секцию HeadroomGuard
- Удалить `docker-compose.headroom.yml`
- Удалить `.env.headroom`
- Убрать правила "Что НЕ делать" про HeadroomGuard

**Вариант C: Заменить другой компрессией**
- Изучить альтернативы (prompt caching, conversation summarization)
- Реализовать в agent_wrapper.py

**Рекомендация:** Вариант B (удалить). Текущий DeepSeek работает стабильно, лишний прокси — лишняя точка отказа.

---

## 🟡 Важные решения (на будущее)

### Решение #6: Backend CRM использовать или удалить?

**Контекст:**
- 53 endpoints в aim-app (leads, sales, onboarding, analytics, email, gdpr, etc.)
- 45 таблиц в PostgreSQL (пустые)
- Tools НЕ используют эти endpoints (Hermes tools делают прямые HTTP вызовы)

**Вопрос:** Планируется ли использовать backend CRM?

**Вариант A: Использовать активно**
- Починить PostgreSQL
- Подключить Hermes tools к endpoints (`/api/leads/capture` вместо прямых SQL)
- Начать собирать лиды в БД

**Вариант B: Удалить (минимализм)**
- Удалить aim-app полностью
- Hermes tools вызывают внешние API напрямую
- Чат-продукт сохраняет данные в SQLite Hermes'а

**Вариант C: Оставить минимально**
- Удалить неиспользуемые routers (sales, onboarding, email, gdpr если не нужны)
- Оставить только leads, analytics, presale
- Уменьшить aim-app до 10-15 endpoints

**Рекомендация:** Сначала **решить бизнес-цель**. Еслиleads через сайт — нужен. Если нет — удалить.

---

### Решение #7: Teacher Agent — реализовать или удалить?

**Контекст:**
- `src/aim/teacher/` существует (388 KB)
- В Hermes tools нет `teach_*`
- CLAUDE.md описывает амбициозный план: "каждые 2-4 недели GitHub search + deep research"
- В реальности: не реализован

**Вопрос:** Реализовывать?

**Вариант A: Реализовать по плану CLAUDE.md**
- Запланировать отдельный milestone (1-2 недели)
- Создать cron-job контейнер
- Реализовать цикл обучения

**Вариант B: Удалить**
- Удалить `src/aim/teacher/`
- Удалить `obsidian/teacher/` vault
- Убрать секцию из CLAUDE.md

**Вариант C: Минимально (manual trigger)**
- Оставить код
- Добавить CLI script `/scripts/teacher-run.py`
- Запускать вручную когда нужно

**Рекомендация:** B или C. Если не делали 2 месяца — не сделают. Удалить или сделать manual tool.

---

### Решение #8: Obsidian vaults — оставить или удалить?

**Контекст:**
- `obsidian/` — 7.1 MB, 30 vaults
- CLAUDE.md: "не используется кроме teacher и architect"
- 30 vaults: ads-magister, analytics-magister, architect, ci-* (15), content-magister, deep-research, email-magister, intelligence-magister, magisters, operator, seo-magister, social-magister, teacher, test-agent

**Вопрос:** Что делать с vaults?

**Вариант A: Удалить кроме architect + teacher**
- Удалить 28 vaults
- Оставить architect (968 KB) и teacher (если используется)
- ~6 MB экономии

**Вариант B: Удалить все**
- Полностью убрать `obsidian/`
- Уйти от концепции "vaults для агентов"

**Вариант C: Оставить как есть**
- Занимают место, но не мешают

**Рекомендация:** A. Architect может быть полезен.

---

### Решение #9: 233 markdown файла в корне AIM

**Контекст:**
- Исторические .md: CHECKPOINTS.md (92 KB), ARCHITECT_GUIDE.md (25 KB), BREAKTHROUGH_QUALITY_100.md, AUTONOMOUS_WORK_COMPLETE.md, etc.
- Никакой текущей роли не играют
- Но могут содержать ценный исторический контекст

**Вопрос:** Удалять или архивировать?

**Вариант A: Архивировать в `docs/archive/`**
- Создать `AIM/docs/archive/`
- Переместить все исторические .md
- Оставить в корне только README, SESSION, CLAUDE

**Вариант B: Удалить**
- Вся история в git
- Очистить корень

**Вариант C: Оставить**
- Не критично

**Рекомендация:** A. Безопасно и чисто.

---

## 🟢 Менее критичные решения

### Решение #10: aim-paperclip tirith binary

**Контекст:**
- `/opt/data/bin/tirith` — 22 MB ELF binary
- Дата: 19 июня 2026
- В `aim_hermes_data` volume

**Вопрос:** Что это?

**Действия:** спросить Михаила. Если не нужен — удалить.

---

### Решение #11: ChatExport_2026-06-18.zip

**Контекст:**
- 416 KB в `/opt/data/`
- Telegram chat export от 18 июня

**Вопрос:** Нужен для анализа?

**Действия:** заархивировать или удалить.

---

### Решение #12: 4 docker-compose файла

**Контекст:**
- `docker-compose.yml` (главный, 367 строк)
- `docker-compose.zai.yml` (731 B, Z.AI вариант)
- `docker-compose.headroom.yml` (1 KB, HeadroomGuard — не активен)
- `hermes-temp/docker-compose.yml` (временный)

**Вопрос:** Оставить override pattern или упростить?

**Вариант A:** Один canonical `docker-compose.yml`
**Вариант B:** Base + overrides (`docker-compose.yml` + `docker-compose.prod.yml` + `docker-compose.dev.yml`)

**Рекомендация:** A. Проще.

---

### Решение #13: Monitoring exposed ports

**Контекст:**
- Prometheus (9090), Grafana (3000), Redis (6379) экспонированы на 0.0.0.0

**Вопрос:** Оставить или закрыть?

**Рекомендация:** Закрыть (только localhost). Доступ через SSH tunnel если нужен.

---

### Решение #14: WordPress `chat-inline-pro.php` vs `chat-inline.php`

**Контекст:**
- `chat-inline.php` — активный
- `chat-inline-pro.php` — Phase 09 inline chat
- Если Phase 09 не деплоится — `chat-inline-pro.php` не нужен

**Вопрос:** Удалить pro версию?

---

### Решение #15: `frontend/` и `frontend/frontend/` вложенность

**Контекст:**
- В локальном frontend есть странная структура: `frontend/frontend/` с вложенными компонентами
- Похоже на артефакт переезда структуры

**Вопрос:** Это нужно?

---

## 📋 Сводка решений

| # | Решение | Срочность | Рекомендация |
|---|---|---|---|
| 1 | PostgreSQL vs SQLite | Phase E | Гибрид |
| 2 | aim-frontend | Phase E | Удалить |
| 3 | aim-paperclip | Phase A | Выяснить, удалить если не нужен |
| 4 | Phase 09 | Phase B | Деплоить или удалить |
| 5 | HeadroomGuard | Phase B | Удалить упоминания |
| 6 | Backend CRM | Стратегия | Решить по бизнес-цели |
| 7 | Teacher Agent | Phase D | Удалить или manual |
| 8 | Obsidian vaults | Phase D | Удалить кроме architect+teacher |
| 9 | 233 .md файла | Phase C | Архивировать |
| 10 | tirith binary | Phase A | Спросить |
| 11 | ChatExport | Phase C | Архивировать |
| 12 | Compose files | Phase E | Один canonical |
| 13 | Exposed ports | Phase A | Закрыть |
| 14 | chat-inline-pro | Зависит от #4 | — |
| 15 | frontend/frontend | Phase D | Проверить |

---

## 🎯 Что нужно от Михаила прямо сейчас

Перед началом Phase A рефакторинга, ответить на:

1. **aim-paperclip** что это? (Решение #3)
2. **tirith binary** что это? (Решение #10)
3. **Phase 09** — деплоить или нет? (Решение #4)
4. **HeadroomGuard** — возвращать? (Решение #5)
5. **Backend CRM** планируется использовать? (Решение #6)

Остальные решения можно принимать в процессе рефакторинга.

---

*После ответов на эти вопросы — Phase A можно начинать.*
