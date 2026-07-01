# 02 — AS-IS Architecture (как есть)

Текущая архитектура AIM на основе прямого аудита сервера. Только факты.

---

## Высокоуровневая схема

```
┌─────────────────────────────────────────────────────────────────┐
│                   Internet → iamaim.ru                          │
└──────────────────────────────┬──────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────┐
│   Nginx (aim-nginx, 94 MB) — TLS termination + routing          │
│   - HTTP/80 → 301 HTTPS                                         │
│   - HTTP/80 default_server → aim-paperclip:3100 (IP-based)       │
│   - HTTPS/443 → routes by location                              │
└──────────────────────────────┬──────────────────────────────────┘
                               │
            ┌──────────────────┼──────────────────┬──────────────┐
            ▼                  ▼                  ▼              ▼
    ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐
    │ aim-wordpress│  │  aim-hermes  │  │   aim-app    │  │aim-frontend  │
    │ PHP-FPM 8.2  │  │  FastAPI Py  │  │  FastAPI Py  │  │  Next.js     │
    │   port 9000  │  │   port 8000  │  │   port 8000  │  │  port 3099   │
    │  theme v2.1  │  │  LLM агент   │  │  AIM backend │  │ /chat-test   │
    │  90 страниц  │  │  67 tools    │  │ 53 endpoints │  │ /chat-old    │
    │  chat inline │  │ SOUL.md 106K │  │ PG/Redis dep │  │ /chat-new    │
    └──────┬───────┘  └──────┬───────┘  └──────┬───────┘  └──────────────┘
           │                 │                 │
           │                 │   ┌─────────────┘
           │                 ▼   ▼
           │         ┌─────────────────┐
           │         │  hermes-agent   │
           │         │  (pip package   │
           │         │   v0.14.0)      │
           │         │  - AIAgent      │
           │         │  - SessionDB    │
           │         │  - skill_view() │
           │         └─────────────────┘
           │                 │
           ▼                 ▼
    ┌──────────────┐  ┌──────────────────────────────────────────┐
    │  aim-mysql   │  │          External APIs                   │
    │  MariaDB 11  │  │  - DeepSeek API (LLM, deepseek-v4-pro)   │
    │  WP tables   │  │  - Apify (14 keys pool)                  │
    │  11 таблиц   │  │  - Firecrawl (15 keys pool)              │
    │  90 страниц  │  │  - Brave Search                          │
    └──────────────┘  │  - Perplexity                            │
                      │  - AssemblyAI (voice transcription)      │
                      │  - Telegram Bot API                      │
                      │  - nalog.ru (finances)                   │
                      │  - hh.ru, yandex direct, google pagespeed│
                      └──────────────────────────────────────────┘

    ┌─────────────────────────── Persistence ──────────────────────┐
    │                                                              │
    │  ┌────────────┐  ┌─────────┐  ┌──────────────┐              │
    │  │ aim-postgres│ │aim-redis│  │aim_hermes_data│              │
    │  │  16-alpine │  │ 7-alpine│  │   (volume)   │              │
    │  │  45 таблиц │  │ cache   │  │ -state.db    │              │
    │  │  все пустые│  │ + queues│  │ -sessions    │              │
    │  │  (auth fail)│ │         │  │ -SOUL.md     │              │
    │  └────────────┘  └─────────┘  │ -skills/     │              │
    │                              │ -memories/   │              │
    │                              │ -bin/tirith  │              │
    │                              └──────────────┘              │
    │                                                              │
    │  ┌─────────────────────────────────────────────────┐         │
    │  │  Monitoring stack                               │         │
    │  │  - Prometheus (9090)                            │         │
    │  │  - Grafana (3000)                               │         │
    │  │  - Alertmanager (9093)                          │         │
    │  │  - node-exporter, postgres-exporter             │         │
    │  └─────────────────────────────────────────────────┘         │
    │                                                              │
    └──────────────────────────────────────────────────────────────┘
```

---

## Docker контейнеры (полный список, 16 шт)

| Контейнер | Образ | Размер | Port | Health | Зависимости |
|---|---|---|---|---|---|
| `aim-nginx` | nginx:alpine | 94 MB | 80, 443 | ✅ | — |
| `aim-frontend` | aim-frontend:latest | 281 MB | 3099 (internal) | ✅ | — |
| `aim-wordpress` | wordpress:php8.2-fpm-alpine | 431 MB | 9000 (internal) | ✅ | mysql |
| `aim-hermes` | aim-hermes:latest | 3.21 GB | 8000 (internal) | ✅ | redis, app |
| `aim-app` | aim:latest | 3.13 GB | 8000 (internal) | ✅ | postgres, redis |
| `aim-mysql` | mariadb:11 | 458 MB | 3306 | ✅ | — |
| `aim-postgres` | postgres:16-alpine | 396 MB | 5432 (localhost) | ✅ | — |
| `aim-redis` | redis:7-alpine | 58 MB | 6379 (exposed!) | ✅ | — |
| `aim-prometheus` | prom/prometheus | 593 MB | 9090 (exposed!) | — | — |
| `aim-grafana` | grafana/grafana | 1.47 GB | 3000 (exposed!) | — | — |
| `aim-alertmanager` | prom/alertmanager | 110 MB | 9093 (localhost) | — | — |
| `aim-node-exporter` | prom/node-exporter | 41 MB | 9100 (localhost) | — | — |
| `aim-postgres-exporter` | postgres-exporter | 35 MB | 9187 (localhost) | — | postgres |
| `aim-paperclip` | paperclip-paperclip | **2.76 GB** | 80 (default), 3100 | — | — |

**Подсвеченные проблемы:**
- Redis (6379), Prometheus (9090), Grafana (3000) — **экспонированы наружу**, не должны быть в production
- `aim-paperclip` — отдельный контейнер 2.76 GB, не описан в CLAUDE.md, занимает default HTTP route в Nginx

---

## Внутренняя сеть

Все контейнеры (кроме paperclip) на bridge-сети `aim_aim-network` (172.18.0.0/16):

```
aim-mysql:           172.18.0.2
aim-hermes:          172.18.0.3
aim-frontend:        172.18.0.4
aim-redis:           172.18.0.5
aim-grafana:         172.18.0.6
aim-app:             172.18.0.7
aim-node-exporter:   172.18.0.8
aim-alertmanager:    172.18.0.9
aim-prometheus:      172.18.0.10
aim-postgres-exporter: 172.18.0.11
aim-wordpress:       172.18.0.12
aim-postgres:        172.18.0.14
aim-nginx:           172.18.0.15
aim-paperclip:       172.18.0.18
```

---

## Nginx routing (точные location-блоки)

| Path | Цель | Комментарий |
|---|---|---|
| `/` (HTTP, default_server) | `aim-paperclip:3100` | IP-based, rate limit 50r/s |
| `/.well-known/acme-challenge/` | /var/www/certbot | Let's Encrypt |
| `/health` (HTTP) | return 200 OK | Без auth |
| `/` (HTTP, iamaim.ru) | 301 HTTPS | redirect |
| `/reports/` | (в конфиге) | — |
| `/api/chat/send` | `hermes:8000/api/chat` | Sync чат |
| `/api/chat/stream` | `hermes:8000/api/chat/stream` | SSE streaming |
| `/api/chat` | `hermes:8000` | Fallback |
| `/api/` | `app:8000` | aim-app REST API |
| `/health`, `/ready`, `/metrics` | `app:8000` | — |
| `/telegram/webhook` | `hermes:8000` | — |
| `/_next/` | `frontend:3099` | Next.js static |
| `/chat-test`, `/chat-old`, `/chat-new` | `frontend:3099` | — |
| `/wp-content/` (static) | filesystem (nginx) | JS/CSS/images |
| `/wp-admin`, `/wp-login.php` | `wordpress:9000` | Admin |
| `/` (HTTPS) | `wordpress:9000` | Default catch-all |

---

## Hermes (aim-hermes) — внутреннее устройство

### Файлы приложения

| Файл | Строк | Назначение |
|---|---:|---|
| `app/main.py` | 671 | FastAPI server: /api/chat, /api/chat/stream, /telegram/webhook, /metrics |
| `app/agent_wrapper.py` | 911 | AIAgent lifecycle, sync/async adapter, mode prompts |
| `app/agent_wrapper_optimized.py` | 90 | Mode prompt fragments (PRESALE, ACTIVE, ADMIN, SALES_ADMIN) |
| `app/telegram_gateway.py` | 497 | Webhook + getUpdates polling, voice transcription |
| `app/knowledge_router.py` | 172 | Knowledge vault CRUD |
| `app/routers/session_api.py` | 112 | Archived session retrieval by hash |
| `app/auth.py` | — | Bearer token validation |
| `app/key_bank.py` | — | Multi-key pool for Apify/Firecrawl |
| `app/token_economy.py` | — | Token usage tracking |
| `app/voice_transcriber.py` | — | AssemblyAI voice → text |
| `app/omniroute_direct.py` | — | **Legacy LLM proxy, не используется** |
| `app/pipeline/` | 1841+175+131+451+94 = 2692 | **v7 State Machine — deprecated, не используется** |
| `app/tools/` | 67 tools | Core business logic |

### Hermes tools (67 шт, по категориям)

**aim-operations (бизнес-инструменты):**
- Пресейл: `run_prescan`, `run_full_scout`, `run_aim_scout`, `quick_overview`
- Разведка: `find_competitors`, `run_ci_analysis`, `present_competitors`
- Аналитика: `run_seo_audit`, `run_tech_seo_audit`, `run_content_analysis`, `run_content_gaps`
- Технический: `run_lighthouse`, `run_pagespeed`, `run_validation_check`
- Соц-сети: `run_instagram_content`, `run_review_platforms`, `run_smi_mentions`
- Персоналии: `run_doctor_dossiers`, `run_hh_analysis`
- Реклама: `run_ads_report`, `run_ads_intelligence`
- Финансы: `find_company_financials`
- Гео: `run_geo_audit`
- Финальный: `run_background_pipeline`, `finalize_research`, `orchestrate`
- Отчёты: `generate_html_report`, `post_report`, `publish_scout_report`, `read_report_reference`
- Лиды: `collect_contact`, `qualify_lead`, `escalate_to_manager`, `show_all_leads`, `get_lead_pipeline`, `show_project_status`
- Знания: `update_knowledge`

**hermes-debug (системные):**
- Shell: `shell_exec`, `pip_install`, `restart_myself`
- Files: `file_read`, `file_write`
- HTTP: `api_debug`, `call_api`, `web_fetch`, `web_search`
- Browser: `browser_screenshot`, `viewport`, `robots`
- Firecrawl (9 шт): `firecrawl_scrape`, `firecrawl_search`, `firecrawl_crawl`, `firecrawl_map`, `firecrawl_extract`, `firecrawl_parse`, `firecrawl_batch_scrape`, `firecrawl_agent`, `firecrawl_agent_status`
- Crawlee: `crawlee_scrape`, `crawlee_search`
- Scrapy: `scrapy_crawl`
- Perplexity: `perplexity_search`, `perplexity_deep_analyze`
- Bitrix: `bitrix_scrape`
- Telegram: `search_telegram_chats`, `send_telegram_message`, `send_telegram_file`

### Hermes persistent state

| Путь | Размер | Что |
|---|---:|---|
| `/opt/data/state.db` | 3.4 MB | SQLite сессии (32 sessions, 161 messages) |
| `/opt/data/state.db-wal` | 5.2 MB | WAL |
| `/opt/data/SOUL.md` | 106 KB | Identity prompt (рассинхрон с образом) |
| `/opt/data/skills/` | 124 KB | 2 skills: aim-scout, geo |
| `/opt/data/memories/` | 12 KB | MEMORY.md, USER.md |
| `/opt/data/sessions/` | 5.9 MB | Активные сессии (raw) |
| `/opt/data/sessions-archive/` | 88 KB | Архив (nachalo-clinica + 11 hash-сессий) |
| `/opt/data/proposals/` | 44 KB | HTML отчёты |
| `/opt/data/cache/` | 5.4 MB | LLM responses cache |
| `/opt/data/logs/` | 3 MB | agent.log 2.1MB + errors.log 624KB + gateway.log 312KB |
| `/opt/data/bin/tirith` | **22 MB** | Бинарник, назначение неизвестно |
| `/opt/data/keys/` | — | Key pools + rotation state |
| `/opt/data/firecrawl_keys.json` | — | 15 Firecrawl ключей |

---

## aim-app (FastAPI backend)

### 53 REST endpoints (по OpenAPI)

```
GET    /
GET    /api/v1/status
POST   /api/ads/report
GET    /api/analytics/{emails,export,funnel,leads,realtime}
GET    /api/companies/financials
GET    /api/company-profiles/by-url
POST   /api/company-profiles/upsert
POST   /api/competitors/{analyze,analyze/stream,find,save}
POST   /api/content/analyze
GET    /api/email/metrics
POST   /api/email/webhook/sendgrid
DELETE /api/gdpr/leads/{lead_id}
POST   /api/hermes/orchestrate
GET    /api/leads
POST   /api/leads
POST   /api/leads/capture
GET    /api/onboarding/lead/{lead_id}
POST   /api/onboarding/start
POST   /api/onboarding/{id}/complete
POST   /api/onboarding/{id}/documents
POST   /api/onboarding/{id}/payment
POST   /api/onboarding/{id}/retry
GET    /api/onboarding/{id}/status
POST   /api/performance/cache/clear
GET    /api/performance/stats
POST   /api/pre-sale/chat
POST   /api/pre-sale/session
POST   /api/pre-sale/session/phase
POST   /api/presale/prescan
POST   /api/presale/prescan-staged
GET    /api/projects/{project_id}/status
GET    /api/sales/{activity,conversations,pipeline,knowledge/{client_id}}
POST   /api/sales/{escalate,knowledge/sync,qualify}
PUT    /api/sales/knowledge/update
POST   /api/seo/{audit,audit/stream}
GET    /api/seo/audit/{task_id}
```

### Структура `src/aim/`

```
src/aim/
├── main.py (419 строк)         # FastAPI app, lifespan, 19 router импортов
├── database.py                 # SQLAlchemy async engine
├── metrics.py                  # Prometheus
├── api/ (19 router файлов)     # REST endpoints
├── magisters/ (19 файлов)      # ❌ DEPRECATED — почти не импортируется
├── subagents/ (133 файла)     # ❌ DEPRECATED — ci-orchestrator
├── agents/ci_swarm/            # ❌ DEPRECATED
├── orchestration/ (3 файла)    # hermes_orchestrator, knowledge_bridge, shared_event_bus
├── integration/ (2 файла)      # ci_magisters_integration, hermes_context
├── services/ (21 файл)         # Apify, payment, email, scraping, lead_capture
├── integrations/               # Внешние интеграции
├── ai/                         # AI/LLM modules
├── teacher/                    # ❌ Teacher Agent (CLAUDE.md: "не реализован полностью")
├── models/                     # SQLAlchemy модели
├── schemas/                    # Pydantic schemas
├── templates/                  # Jinja2
├── middleware/                 # profiling, cache
├── config/                     # logging, settings
└── utils/
```

### База данных PostgreSQL (aim_db)

**45 таблиц**, все пустые. Топ по потенциальному использованию:

| Таблица | Назначение | Строк |
|---|---|---:|
| event_bus_messages | EventBus | 4 |
| linear_tasks | Интеграция с Linear | 0 |
| fz152_audit_log_* | Логи ФЗ-152 (partitioned по годам) | 0 |
| sales_messages | Сообщения клиентам | 0 |
| sales_escalations | Эскалации | 0 |
| payments | Платежи | 0 |
| email_workflows, email_events, email_templates | Email automation | 0 |
| documents_* | Документы (partitioned по годам 2026-2033) | 0 |
| audit_trail | Аудит | 0 |
| campaigns, campaign_attributions | Рекламные кампании | 0 |
| alembic_version | Миграции | 1 |

**Только 1 таблица активно записывается — `event_bus_messages` (4 строки).**

---

## WordPress (aim-wordpress)

- **Версия темы:** aim-theme v2.1.76
- **Активная тема:** `aim-theme`
- **Контент:** 90 страниц (page), 4 поста (post), 5 ревизий, 2 navigation menus, 1 global_styles
- **БД:** MariaDB 11, 11 стандартных WP таблиц

### Структура aim-theme (38 элементов в корне)

| Файл/директория | Назначение |
|---|---|
| `style.css` | Theme metadata |
| `functions.php` | Theme setup, CPT research, Phase 09 endpoints |
| `aim-pro-endpoints.php` | Phase 09 fallback REST API |
| `front-page.php` | Главная страница |
| `home.php`, `index.php` | Блог |
| `header.php`, `footer.php` | Layout |
| `page-prices.php`, `page-philosophy.py`, `page-contact.php`, etc. | Static pages |
| `chat-inline.php` | Inline chat на главной (активный) |
| `chat-inline-pro.php` | Phase 09 inline chat |
| `archive-research.php` | CPT research archive |
| `design-showcase-dual-theme.html` | Reference для дизайн-системы (102 KB) |
| `nachalo-clinica-proposal.html` | Demo proposal |
| `chat/` | React chat компоненты: hermes-chat.html (active), hermes-chat-glass.html |
| `assets/` | JS/CSS bundle |
| `docs/` | Documentation pages |
| **`node_modules/`** | **15.7 MB — НЕ должно быть в production volume** |
| **`*.bak`, `*.backup-*`** | 5 backup-файлов |

### Nginx для WordPress

```nginx
location /wp-content/ {
    location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg|woff|woff2|ttf|eot|webp|avif)$ {
        # serve static
    }
}

location /wp-admin {
    location ~ \.php$ { proxy_pass wordpress:9000; }
}

location / {
    location ~ \.php$ { proxy_pass wordpress:9000; }
    # else: try_files
}
```

---

## aim-frontend (Next.js)

- **Стек:** Next.js 14+ standalone, React, TanStack Query v5
- **Страницы:** services, contact, blog, case-studies, about, privacy-policy, chat-test, chat-old, chat-new, + dashboard routes
- **Роль:** в основном history, активный продукт — chat-inline.php в WordPress
- **Build:** standalone output, optimizeCss, optimizePackageImports
- **API proxy:** через Nginx (paths `/api/`, `/_next/`)

---

## aim-paperclip (не описан в CLAUDE.md!)

```
Image:    paperclip-paperclip:latest (2.76 GB)
Entrypoint: docker-entrypoint.sh
Cmd:      paperclipai run
WorkDir:  /home/paperclip
Port:     3100 (internal), 80 (default_server в nginx)
Network:  aim_aim-network
```

- Логи показывают только health-check (`GET /health 200`, `GET /metrics 403`, `GET / 403`)
- В Nginx — отдельный default_server для IP-based доступа на порт 80
- Роль не документирована

---

## Конфигурация env

### LLM
- `LLM_MODEL=deepseek-v4-pro`
- `OMNIROUTE_URL=https://api.deepseek.com/v1` (прямой, **без headroom-proxy**)
- `OMNIROUTE_AUTH=sk-...`

### Keys
- `APIFY_API_TOKEN` + `_01.._13` (14 ключей)
- `FIRECRAWL_API_KEY` + `_01.._14` (15 ключей)
- `BRAVE_API_KEY`, `PERPLEXITY_API_KEY`, `ASSEMBLYAI_API_KEY`, etc.

### Интеграции
- `WP_DB_HOST=aim-mysql`, `WP_DB_USER=wp_user`, `WP_DB_PASSWORD=***`, `WP_DB_NAME=wordpress`
- `POSTGRES_USER=aim_user`, `POSTGRES_PASSWORD=***`, `POSTGRES_DB=aim_db` (в .env, но не работает с volume)
- `REDIS_URL=redis://redis:6379/0`
- `SESSIONS_ROOT=/opt/data/sessions-archive`
- `ARCHIVE_BASE_URL=https://iamaim.ru/wp-json/aim/v1/session`
- `HERMES_HOME=/opt/data`

### Telegram
- `TELEGRAM_BOT_TOKEN`, `TELEGRAM_ADMIN_CHAT_ID`, `TELEGRAM_API_ID`, `TELEGRAM_API_HASH`
- `TELEGRAM_WEBHOOK_URL=https://iamaim.ru/telegram/webhook`

---

## Docker compose (главный)

`/opt/aim/AIM/docker-compose.yml` — 367 строк, описывает 13 services:
postgres, app, hermes, frontend, redis, wordpress, mysql, nginx, prometheus, grafana, postgres-exporter, alertmanager, node-exporter.

Дополнительные compose:
- `docker-compose.zai.yml` (731 B) — Z.AI вариант
- `docker-compose.headroom.yml` (на хосте в /opt/aim) — HeadroomGuard sidecar (**не активен**)
- `hermes-temp/docker-compose.yml` — временный

---

## Точки отказа (single points of failure)

1. **PostgreSQL auth** — нарушена, всё что пишет в БД падает
2. **SOUL.md в volume** — обновления не подхватываются автоматически
3. **aim-paperclip** — 2.76 GB образ, unknown роль, default HTTP route
4. **`/opt/data/bin/tirith`** — 22 MB бинарник без документации

---

*Этот документ — снимок архитектуры на 30.06.2026. Для целевой архитектуры см. `08-TARGET-ARCHITECTURE.md`.*
