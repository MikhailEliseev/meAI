# 08 — Target Architecture (TO-BE)

Целевая архитектура AIM после рефакторинга. Основа: то, что работает сейчас (LLM-оркестратор), очищенное от всего лишнего.

---

## 🎯 Принципы целевой архитектуры

1. **LLM — единственный оркестратор.** Hermes (через hermes-agent) решает что вызывать, когда, в каком порядке. Никаких жёстких pipelines.
2. **Tools — атомарные REST-прокси.** Каждый tool = один HTTP-вызов к aim-app или внешнему API. Тонкие wrapper'ы.
3. **Persistent state — только SQLite.** PostgreSQL не нужен для основного flow (32 сессии, 161 сообщение — SQLite справляется).
4. **Single source of truth для identity.** SOUL.md в образе = SOUL.md в runtime. Автоматическое обновление при деплое.
5. **WordPress как CMS.** Контент и landing — там. Chat UI — React bundle в теме.
6. **Документация = код.** SESSION.md и CLAUDE.md обновляются вместе с деплоем.

---

## 🏗️ Целевая топология

```
                    Internet → iamaim.ru
                          │
                          ▼
              ┌────────────────────────┐
              │  Nginx (TLS + routing) │
              └───────────┬────────────┘
                          │
            ┌─────────────┼─────────────┐
            ▼             ▼             ▼
    ┌──────────────┐ ┌──────────┐ ┌──────────────┐
    │  WordPress   │ │  Hermes  │ │   Static     │
    │  (CMS+theme) │ │ FastAPI  │ │  /wp-content │
    │              │ │          │ │              │
    │ PHP 8.2-FPM  │ │ 67 tools │ │              │
    │ MariaDB      │ │ SOUL.md  │ │              │
    │ aim-theme    │ │ SQLite   │ │              │
    └──────────────┘ └─────┬────┘ └──────────────┘
                           │
                           ▼
              ┌────────────────────────┐
              │   hermes-agent (pip)   │
              │   AIAgent + SessionDB  │
              │   + skill_view()       │
              └───────────┬────────────┘
                          │
                          ▼
              ┌────────────────────────┐
              │   External LLM APIs    │
              │   - DeepSeek primary   │
              │   - (OpenRouter alt)   │
              └────────────────────────┘
                          │
                          ▼
              ┌────────────────────────┐
              │   Hermes Tools (67)    │
              │   ───────────────────  │
              │   aim-app REST proxy:  │
              │   - prescan            │
              │   - find_competitors   │
              │   - ci_analysis        │
              │   - seo/tech/content   │
              │   ───────────────────  │
              │   Direct external:     │
              │   - Firecrawl (9 var)  │
              │   - Perplexity (2)     │
              │   - Telegram (3)       │
              │   - nalog.ru           │
              │   ───────────────────  │
              │   Debug:               │
              │   - shell_exec         │
              │   - file_read/write    │
              │   - restart_myself     │
              └───────────┬────────────┘
                          │
                          ▼
              ┌────────────────────────┐
              │   External Services    │
              │   - Apify (14 keys)    │
              │   - Brave Search       │
              │   - AssemblyAI         │
              │   - Google PageSpeed   │
              │   - hh.ru              │
              │   - Yandex Direct      │
              │   - nalog.ru           │
              │   - Telegram Bot API   │
              └────────────────────────┘
```

**Что УБИРАЕМ:**
- ❌ PostgreSQL (заменяем на SQLite для всего)
- ❌ EventBus (не нужен)
- ❌ Magisters (19 файлов)
- ❌ Subagents (133 файла, включая CI orchestrator)
- ❌ Orchestration layer
- ❌ Integration layer (ci_magisters_integration)
- ❌ Teacher agent (если не используется)
- ❌ HeadroomGuard sidecar (если не активирован)
- ❌ aim-frontend Next.js (если не нужен, всё в WordPress)
- ❌ `omniroute_direct.py` legacy
- ❌ Hermes pipeline v7 (2692 строки)

**Что ОСТАВЛЯЕМ:**
- ✅ Hermes FastAPI + hermes-agent
- ✅ 67 tools (после очистки от дублей)
- ✅ WordPress + MariaDB + aim-theme
- ✅ Nginx + Let's Encrypt
- ✅ Monitoring stack (Prometheus, Grafana, etc.)
- ✅ Redis (cache + queue)
- ✅ Key rotation system (Firecrawl, Apify)
- ✅ Telegram bot integration

**Под вопросом:**
- ❓ aim-paperclip (выяснить назначение)
- ❓ aim-app FastAPI (если tools могут работать напрямую)

---

## 🎯 Целевая структура проекта

```
meAI_1/                                ← project root
├── CLAUDE.md                          ← обновлённый, точный
├── SESSION.md                         ← обновлённый, актуальный
├── .current-task                      ← одна строка, точная
├── .env.example                       ← template без секретов
│
├── AIM/
│   ├── docker-compose.yml             ← один canonical, не 4
│   ├── .env.production                ← gitignored
│   ├── .gitignore                     ← полный список игнора
│   │
│   ├── hermes/                        ← Hermes app
│   │   ├── Dockerfile                 ← multi-stage build
│   │   ├── entrypoint.sh              ← copy_soul + uvicorn
│   │   ├── app/
│   │   │   ├── main.py                ← FastAPI server
│   │   │   ├── agent_wrapper.py       ← AIAgent lifecycle
│   │   │   ├── auth.py
│   │   │   ├── token_economy.py
│   │   │   ├── voice_transcriber.py
│   │   │   ├── telegram_gateway.py
│   │   │   ├── knowledge_router.py
│   │   │   ├── key_bank.py
│   │   │   ├── routers/
│   │   │   │   └── session_api.py
│   │   │   └── tools/                 ← 67 tools (после cleanup)
│   │   ├── skills/                    ← 5 skills
│   │   │   ├── aim/
│   │   │   ├── aim-scout/
│   │   │   ├── client-onboarding-pipeline/
│   │   │   ├── deep-research-phase-0/
│   │   │   └── software-development/
│   │   ├── scripts/
│   │   │   ├── copy_soul.sh           ← ВСЕГДА копирует
│   │   │   ├── bootstrap.sh
│   │   │   └── key_rotation.py
│   │   └── config.yaml                ← LLM config (не pipeline)
│   │
│   ├── wordpress-core/                ← исходники темы
│   │   └── wp-content/themes/aim-theme/
│   │       ├── functions.php          ← без Phase 09 если не используется
│   │       ├── chat-inline.php        ← активный
│   │       ├── chat/
│   │       │   ├── hermes-chat.html   ← один canonical
│   │       │   ├── src/               ← React sources
│   │       │   ├── dist/              ← build artifacts
│   │       │   └── esbuild.config.mjs
│   │       ├── assets/
│   │       ├── design-showcase-dual-theme.html
│   │       └── page-*.php
│   │
│   └── docs/                          ← вся документация тут
│       ├── architecture.md
│       ├── deployment.md
│       ├── troubleshooting.md
│       └── archive/                   ← исторические .md
│
└── refactor-analysis/                 ← этот анализ
    ├── README.md
    ├── 01-EXECUTIVE-SUMMARY.md
    ├── ... (10 файлов)
```

**Что УБИРАЕМ из структуры:**
- ❌ `src/aim/magisters/` (19 файлов)
- ❌ `src/aim/subagents/` (133 файла)
- ❌ `src/aim/orchestration/`
- ❌ `src/aim/integration/`
- ❌ `src/aim/agents/ci_swarm/`
- ❌ `hermes/app/pipeline/` (2692 строки)
- ❌ `hermes/app/omniroute_direct.py`
- ❌ `hermes/_archive/`
- ❌ `hermes/knowledge/`
- ❌ `hermes/patches/`
- ❌ `hermes/mcp-proxy/` (если не используется)
- ❌ `obsidian/` (30 vaults, кроме architect и teacher если нужны)
- ❌ `.planning/`
- ❌ `.venv/`, `.cache/`, `.pytest_cache/`, `.local/`, `.superflow/`
- ❌ `frontend/` локально (если есть Docker образ)
- ❌ Дубликат `meai/` (один из двух)
- ❌ Все `*.bak`, `*.backup-*`
- ❌ `data/test_*.db`, `data/ci-*.json`
- ❌ `logs/` (настраиваем logrotate или удаляем)

---

## 🎯 Целевая Hermes architecture

### Single source of truth для SOUL.md

**Проблема сейчас:** SOUL.md в образе (47 KB) ≠ SOUL.md в volume (106 KB).

**Решение:**
1. Хранить SOUL.md **только** в Docker образе (`/opt/hermes/skills/aim/SOUL.md`)
2. При запуске контейнера — **всегда копировать** в `/opt/data/SOUL.md` (перезаписывая)
3. Скрипт `copy_soul.sh` изменить:
   ```bash
   # Always copy (not conditional)
   cp "$SOURCE" "$TARGET"
   ```
4. При `docker-compose build` — новый SOUL.md автоматически подхватывается

### Tools cleanup

Из 67 tools оставить:
- **aim-operations** (45 шт): все run_*, find_*, present_*, generate_html_report, etc.
- **hermes-debug** (22 шт): shell_exec, file_*, firecrawl_*, perplexity_*, etc.

Убрать дублирующие:
- `omniroute_direct.py` (legacy)
- Возможно `pipeline/` (если pipeline engine не используется)
- Дублирование между `key_bank.py` и `firecrawl_key_bank.py` (объединить)

### Mode prompts

Currently 4 mode: PRESALE, ACTIVE, ADMIN, SALES_ADMIN.

**Реально используется:** PRESALE (основной поток).

Упростить:
- PRESALE — основной mode для чата на iamaim.ru
- ADMIN — для Telegram admin chat
- Убрать ACTIVE и SALES_ADMIN если не используются

### Pipeline v7 — удалить

Pipeline v7 (2692 строки в `app/pipeline/`) — заменить на:
- LLM вызывает tools напрямую через свой внутренний цикл
- `agent_wrapper.py` управляет диалогом
- Никакого state machine с фазами

---

## 🎯 Целевая WordPress architecture

### Theme cleanup

**Активные файлы:**
- `style.css` — metadata
- `functions.php` — setup + endpoint registration
- `front-page.php`, `home.php`, `index.php`
- `header.php`, `footer.php`
- `page-prices.php`, `page-philosophy.php`, `page-contact.php`, `page-privacy-policy.php`, `page-confidentiality.php`, `page-requisites.php`, `page-sessions.php`
- `chat-inline.php` — активный чат
- `archive-research.php` — CPT
- `aim-pro-endpoints.php` — если Phase 09 нужна
- `design-showcase-dual-theme.html` — reference

**Удалить:**
- Все `*.bak`, `*.backup-*`
- `node_modules/` (15.7 MB) — должен быть только в Docker build context
- `hermes-chat-glass.html` если не используется (или оставить как alternative)

### Build process

- `package.json` и `esbuild.config.mjs` остаются (для сборки chat-bundle)
- Build происходит в Dockerfile (multi-stage):
  ```
  Stage 1: npm install + npm run build → dist/
  Stage 2: copy dist/ to final image
  ```
- В volume `aim_wp_content` попадает только собранный bundle, не node_modules

---

## 🎯 Целевая data flow

### Chat request flow (без изменений)

```
1. Client → POST /api/chat (Nginx → Hermes)
2. Hermes auth → verify_api_key(Bearer)
3. agent_wrapper → create AIAgent (cached per session)
4. AIAgent → DeepSeek API → tool calls
5. Tools → aim-app REST API → external services
6. AIAgent → return text response
7. Hermes → JSON response → Nginx → Client
```

### Session persistence flow (упрощённый)

```
Currently:
  - state.db (SQLite, /opt/data/state.db)
  - sessions-archive/ (legacy, separate files)
  - sessions/ (active session files)

Target:
  - state.db (single source, /opt/data/state.db)
  - sessions-archive/ — для viewable archives (через session_api.py)
```

Удалить дублирование между `sessions/` и `sessions-archive/`.

---

## 🎯 Целевая БД стратегия

### Decision: PostgreSQL ИЛИ SQLite

**Аргументы за SQLite:**
- Hermes уже использует (state.db, 32 sessions работает)
- Simple, no auth issues
- Backup = copy file
- Достаточно для текущей нагрузки (46 запросов/24h)

**Аргументы за PostgreSQL:**
- Если планируется growth до 1000+ лидов/мес
- Если нужны транзакции across services
- Если aim-app backend будет активно использоваться

**Рекомендация:** **SQLite для всего**, пока нагрузка не превысит 100 одновременных операций/сек.

### Если оставляем PostgreSQL

Тогда:
1. **Починить auth** (синхронизировать пароли)
2. Удалить `event_bus_*` таблицы (EventBus не нужен)
3. Оставить `leads`, `documents`, `fz152_audit_log`, `email_*`, `sales_*`
4. Написать integration test: каждый endpoint пишет в свою таблицу

---

## 🎯 Целевая monitoring стратегия

**Сейчас:** Prometheus + Grafana + Alertmanager + node-exporter + postgres-exporter.

**Цель:** оставить как есть, но:
- Убрать экспонирование портов 9090, 3000, 6379 наружу (только localhost)
- Если убрать PostgreSQL — убрать `postgres-exporter`
- Добавить alert на `aim-hermes down` и `aim-hermes /ready` returning false

---

## 🎯 Целевая deployment стратегия

### Сейчас

```
Local commit → ssh aim → docker cp files → docker restart
```

Или:
```
Local commit → ssh aim → cd /opt/aim/AIM → docker-compose build && docker-compose up -d
```

### Цель (рекомендация)

**Git-based deployment:**
1. Local: commit + push to `main`
2. Server: `git pull && docker-compose build && docker-compose up -d`
3. `deploy-hermes.sh` скрипт automate это

**Никаких `docker cp` файлов** (кроме emergency hotfixes).

### SOUL.md hot-reload

```
1. Edit SOUL.md в hermes/skills/aim/
2. Commit
3. Push
4. Server: git pull && docker-compose build hermes && docker-compose up -d hermes
5. copy_soul.sh копирует новую SOUL.md в /opt/data/
6. Hermes начинает использовать обновлённую идентичность
```

---

## 🎯 Целевая документация стратегия

### Принципы

1. **CLAUDE.md** — stable principles (архитектура, conventions, philosophy)
2. **SESSION.md** — current state (что делается прямо сейчас)
3. **.current-task** — одна строка, точная задача
4. **README.md в подпапках** — локальная документация

### Правила обновления

- **Перед deploy:** обновить `.current-task` и SESSION.md "Текущий фокус"
- **После deploy:** обновить "Что сделано" в SESSION.md
- **При architecture pivot:** обновить CLAUDE.md
- **При удалении компонента:** проверить что CLAUDE.md не ссылается

### Anti-patterns

- ❌ Описывать в CLAUDE.md то, что планируется (но не сделано)
- ❌ Использовать `.current-task` как "что хочется когда-нибудь сделать"
- ❌ Держать SESSION.md "вообще про проект" — это для текущего состояния

---

## 🎯 Целевые метрики успеха рефакторинга

После рефакторинга:

| Метрика | До | Цель |
|---|---|---|
| Docker образы | 14 | 8-10 |
| Общий размер образов | 13.1 GB | 6-8 GB |
| Python файлов в коде | ~250 | ~100 |
| Markdown файлов в корне | 233 | 5-10 |
| `*.bak` файлов | 15+ | 0 |
| Объём zombie кода | ~3 MB | 0 |
| .venv на хосте | 236 MB | 0 |
| Логи без ротации | 87 MB | <10 MB (с rot) |
| Tools зарегистрировано | 67 | 50-60 (после cleanup дублей) |
| Endpoints в aim-app | 53 | 30-40 (если убрать неиспользуемые) |
| Postgres tables | 45 (пустые) | 0 (если уходим от PG) или 20-25 (если оставляем) |
| Расхождений с CLAUDE.md | 15+ | 0 |

---

## 🎯 Roadmap (детальный план)

См. следующий документ: `09-REFACTOR-ROADMAP.md`

---

*Этот документ — vision. Для плана реализации см. 09-REFACTOR-ROADMAP.md. Для вопросов к владельцу — 10-DECISIONS-NEEDED.md.*
