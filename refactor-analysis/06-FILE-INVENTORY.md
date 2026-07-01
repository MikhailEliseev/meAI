# 06 — File Inventory

Полный инвентарь значимых файлов и директорий на сервере `aim`.

---

## 🗺️ Карта путей

```
/opt/aim/                              ← project root на сервере
├── AIM/                               ← application code
│   ├── docker-compose.yml             (367 строк, главный)
│   ├── docker-compose.zai.yml         (Z.AI вариант)
│   ├── .env.production                (prod env vars)
│   ├── .env.production.bak-*          (старый бекап)
│   ├── docker-compose.yml.bak
│   ├── docker-compose.headroom-deepseek.yml.backup
│   ├── SESSION.md.bak, ROADMAP.md.bak
│   ├── .current-task                  ("Phase 09 deployed" — false)
│   ├── .planning/                     (3.1 MB, deprecated)
│   ├── .venv/                         (236 MB, дубликат образа)
│   ├── .cache/, .pytest_cache/, .local/, .superflow/, .playwright-mcp/
│   ├── .backups/, .claude/
│   ├── data/                          (SQLites, ci-*.json, apify_keys)
│   ├── docs/, e2e/, scripts/
│   ├── frontend/                      (3.5 MB, дубликат образа)
│   ├── hermes/                        ← Hermes app
│   │   ├── Dockerfile
│   │   ├── app/                       (FastAPI wrapper)
│   │   ├── skills/                    (5 skills)
│   │   ├── config.yaml
│   │   ├── knowledge/                 (deprecated)
│   │   ├── patches/, mcp-proxy/
│   │   ├── _archive/                  (deprecated pipeline)
│   │   ├── 3PHASE_PIPELINE.md
│   │   └── *.md                       (исторические)
│   ├── src/
│   │   ├── aim/                       (134 py файлов + 76 тестов)
│   │   │   ├── main.py                (419 строк, FastAPI)
│   │   │   ├── api/                   (19 router файлов, 53 endpoints)
│   │   │   ├── magisters/             (19 файлов, deprecated)
│   │   │   ├── subagents/             (133 файлов, deprecated)
│   │   │   ├── agents/ci_swarm/       (deprecated)
│   │   │   ├── orchestration/         (3 файла)
│   │   │   ├── integration/           (2 файла)
│   │   │   ├── services/              (21 файл, активные)
│   │   │   ├── integrations/
│   │   │   ├── ai/, teacher/, models/, schemas/, templates/
│   │   │   ├── middleware/, config/, utils/
│   │   │   └── database.py, metrics.py
│   │   └── meai/                      (820 KB, framework)
│   ├── wordpress-core/                (aim-theme source)
│   ├── obsidian/                      (7.1 MB, 30 vaults)
│   ├── logs/                          (87 MB: app.log 62MB, nginx 25MB)
│   ├── config/
│   ├── alembic/, alembic.ini
│   └── 233 markdown files             (исторические)
├── src/meai/                          (868 KB, ДУБЛИКАТ)
├── docker-compose.headroom.yml        (HeadroomGuard, не активен)
├── hermes-temp/                       (временный compose)
└── leads/                             (volume mount для frontend)

/var/lib/docker/volumes/
├── aim_hermes_data/_data/             ← Hermes persistent (/opt/data)
│   ├── SOUL.md                        (106 KB, 1411 строк)
│   ├── state.db                       (3.4 MB, 32 sessions)
│   ├── state.db-wal                   (5.2 MB)
│   ├── state.db-shm                   (32 KB)
│   ├── sessions/                      (5.9 MB)
│   ├── sessions-archive/              (88 KB, 12 сессий)
│   ├── memories/                      (12 KB, MEMORY.md, USER.md)
│   ├── proposals/                     (44 KB)
│   ├── competitors/                   (48 KB)
│   ├── cache/                         (5.4 MB)
│   ├── skills/                        (124 KB: aim-scout, geo)
│   ├── keys/                          (rotation state)
│   ├── firecrawl_keys.json
│   ├── auth.json, auth.lock
│   ├── gateway.lock, gateway_state.json
│   ├── channel_directory.json
│   ├── kanban.db                      (100 KB)
│   ├── models_dev_cache.json         (2.3 MB)
│   ├── ChatExport_2026-06-18.zip     (416 KB)
│   ├── audio_cache/, image_cache/
│   ├── logs/                          (3 MB: agent.log, errors.log, gateway.log)
│   ├── cron/, hooks/, pairing/, sandboxes/
│   └── bin/tirith                     (22 MB, неизвестно)
├── aim_postgres_data/_data/           ← PostgreSQL (45 таблиц, все пустые)
├── aim_redis-data/_data/
├── aim_prometheus-data/_data/
├── aim_grafana-data/_data/
└── aim_wp_content/_data/              ← WordPress files (volume)
    └── themes/aim-theme/
        ├── functions.php, *.php pages
        ├── chat/
        │   ├── hermes-chat.html      (active)
        │   ├── hermes-chat-glass.html (active)
        │   ├── hermes-chat.html.bak
        │   ├── src/                   (React sources)
        │   ├── dist/                  (chat-bundle.js, chat-bundle.css)
        │   ├── package.json, package-lock.json
        │   └── esbuild.config.mjs
        ├── assets/, node_modules/    (15.7 MB — мусор)
        └── design-showcase-dual-theme.html (102 KB, reference)
```

---

## 📄 Ключевые файлы — детально

### `/opt/aim/AIM/docker-compose.yml` (367 строк)

Главный compose. 13 services: postgres, app, hermes, frontend, redis, wordpress, mysql, nginx, prometheus, grafana, postgres-exporter, alertmanager, node-exporter.

Ключевые моменты:
- `aim-hermes`: depends_on redis + app
- `aim-app`: depends_on postgres (healthy) + redis (healthy)
- `aim-wordpress`: depends_on mysql (healthy)
- Volume mounts:
  - `hermes_data:/opt/data` (rw)
  - `./hermes/skills:/opt/hermes/skills:ro` (read-only)
  - `aim_wp_content:/var/www/html/wp-content` (without local mount — volume only)
- Resources limits: cpus 1-2, memory 2-3.8 GB per container
- Logging: json-file driver, max 10m × 3 files

---

### `/opt/aim/AIM/hermes/app/main.py` (671 строка)

FastAPI server. Содержит:
- `/api/chat` — sync chat endpoint
- `/api/chat/stream` — SSE streaming (420s deadline)
- `/telegram/webhook` — Telegram webhook
- `/health` — health check
- `/metrics` — Prometheus metrics
- Lifespan: lazy-init Telegram polling

Imports:
- `from .auth import verify_api_key`
- `from .agent_wrapper import run_agent, run_agent_sync`
- `from .routers.session_api import router as session_router`
- `from .knowledge_router import router as knowledge_router`

---

### `/opt/aim/AIM/hermes/app/agent_wrapper.py` (911 строк)

AIAgent lifecycle. Ключевые функции:
- `run_agent(message, session_id, mode)` — async для web
- `run_agent_sync(message, session_id, mode)` — для Telegram (ThreadPoolExecutor)
- `build_system_prompt()` — собирает system prompt из SOUL.md + mode
- `_create_agent()` — создаёт AIAgent с config
- `get_mode_prompt(mode)` — возвращает промпт для режима

Cached:
- `_soul_md_cache` — module variable, immutable after first load
- `_agent_cache` — dict {session_id: agent}, 24h TTL

Per-session locks:
- `_session_locks` — dict {session_id: asyncio.Lock}
- `_session_locks_sync` — dict {session_id: threading.Lock}

Modes:
- PRESALE (с 3PHASE_PIPELINE.md если есть)
- ACTIVE
- ADMIN
- SALES_ADMIN

---

### `/opt/aim/AIM/hermes/app/tools/` (59 py файлов, 67 tools)

**По категориям:**

**aim-operations tools** (42 шт):
- `run_prescan.py` — staged prescan
- `run_full_scout.py` — 13-фазный scout
- `run_aim_scout.py` — AIM scout
- `find_competitors.py` — Apify поиск
- `present_competitors.py` — форматирование для клиента
- `run_ci_analysis.py` — CI анализ
- `run_seo_audit.py`, `run_tech_seo_audit.py` (через lighthouse)
- `run_content_analysis.py`, `run_content_gaps.py`
- `run_lighthouse.py`, `run_pagespeed.py`, `run_validation_check.py`
- `run_instagram_content.py`, `run_review_platforms.py`, `run_smi_mentions.py`
- `run_doctor_dossiers.py`, `run_hh_analysis.py`
- `run_ads_report.py`, `run_ads_intelligence.py`
- `find_company_financials.py` — nalog.ru
- `run_geo_audit.py`, `geo_optimizer_tools.py`
- `run_background_pipeline.py`, `finalize_research.py`, `orchestrate.py`
- `generate_html_report.py`, `post_report.py`, `publish_scout_report.py`, `read_report_reference.py`
- `quick_overview.py`
- `collect_contact.py`, `qualify_lead.py`, `escalate_to_manager.py`
- `show_all_leads.py`, `get_lead_pipeline.py`, `show_project_status.py`
- `update_knowledge.py`
- `service_categorizer.py`
- `quality_gate.py`
- `engine.py` — общая логика
- `external_api.py`
- `session_archive.py` (баг с leading dot)

**hermes-debug tools** (25 шт):
- `shell_exec.py`, `restart_myself.py`
- `file_read`/`file_write` (через quality_gate.py?)
- `api_debug.py`, `call_api.py`
- `web_fetch.py`, `web_search.py`, `_search_fallback.py`, `_ddg.py`
- `firecrawl_web.py` (9 tools), `firecrawl_key_bank.py`
- `crawlee_web.py`, `scrapy_runner.py`, `web_scraper.py`
- `perplexity_tools.py` (2 tools)
- `bitrix_scraper.py`
- `telegram_tools.py` (3 tools)
- `send_telegram_file.py`

**Test files:**
- `test_deep_research_merge.py`
- `test_presale_pipeline.py`
- `test_service_categorizer.py`

---

### `/opt/aim/AIM/hermes/skills/aim/SOUL.md` (в образе)

**В образе:** 47 KB, 760 строк, name=`aim-operator-v4`
**В runtime (`/opt/data/SOUL.md`):** 106 KB, 1411 строк, name=`aim-operator`

Описание (из runtime версии):
- AIM = AI-first marketing agency для медицинских клиник
- Operator = единый AI интерфейс агентства
- Под капотом — армия AI-агентов (4 Magisters, 70+ субагентов) ← **расхождение с CLAUDE.md "Магистры deprecated"**
- Режимы: PRESALE, ACTIVE, ADMIN, SALES_ADMIN
- 67 tools каталогизированы

---

### `/opt/aim/AIM/hermes/config.yaml`

```yaml
# v7 State Machine (deprecated в коде, но конфиг остался)
pipeline:
  timeouts:
    preflight: 30
    perplexity: 120
    tech_audit: 300
    social_verifier: 180
    content_analysis: 120
    key_persons: 180
    smi_mentions: 120
    competitors: 600
    forum_pains: 120
    finance: 60
    content_plan: 120
    html_build: 120
    qc_critique: 90
    presentation: 60
  total_timeout: 900
  max_retries_default: 1
  competitor_max_retries: 3

# File Protection
# ...
```

---

### `/opt/aim/AIM/src/aim/main.py` (419 строк)

```python
import asyncio, os
from contextlib import asynccontextmanager
from fastapi import FastAPI, status, Request
from sqlalchemy import text

# 19 router импортов (329-346)
from src.aim.api.leads import router as leads_router
# ... 18 more routers

@asynccontextmanager
async def lifespan(app):
    # Alembic migrations with advisory lock
    if AUTO_MIGRATE:
        # pg_try_advisory_lock(42)
        # alembic upgrade head

    # SalesAdminMagister start (try/except)
    try:
        from src.aim.magisters.sales_admin_magister import SalesAdminMagister
        sales_magister = SalesAdminMagister(event_bus=event_bus)
        await sales_magister.start(event_bus)
    except Exception as e:
        logger.error("sales_admin_magister_failed", error=str(e))

    # PartitionManager для documents и fz152_audit_log
    yield
```

---

### `/opt/aim/AIM/src/aim/api/` — 19 router файлов

| Файл | Endpoints | Назначение |
|---|---|---|
| `leads.py` | 4 | CRUD лидов |
| `onboarding.py` | 6 | Onboarding flow |
| `analytics.py` | 5 | Analytics endpoints |
| `email.py` | 2 | Email metrics, SendGrid webhook |
| `webhooks.py` | — | Webhooks |
| `gdpr.py` | 1 | DELETE lead (GDPR) |
| `seo.py` | 3 | SEO audit (sync + stream) |
| `content.py` | 1 | Content analysis |
| `ads.py` | 1 | Ads report |
| `projects.py` | 1 | Project status |
| `telegram.py` | — | Telegram integration |
| `sales.py` | 7 | Sales pipeline, knowledge |
| `competitors.py` | 4 | Find, analyze, save |
| `pre_sale.py` | 3 | Pre-sale chat/session |
| `presale.py` | 2 | Prescan, prescan-staged |
| `companies.py` | 1 | Financials |
| `company_profiles.py` | 2 | By URL, upsert |
| `hermes.py` | 1 | /api/hermes/orchestrate |
| `endpoints/` | — | Sub-dir |

---

### `/opt/aim/AIM/src/aim/services/` — 21 файл (2.4 MB)

| Файл | Назначение |
|---|---|
| `apify_client.py` | Apify API client |
| `apify_key_pool.py` | 14-key rotation |
| `apify_google_maps.py` | Google Maps scraper |
| `api_key_rotator.py` | General rotator |
| `lead_capture.py` | Lead capture endpoint logic |
| `lead_email_automation.py` | Email workflows |
| `linear_leads.py` | Linear CRM sync |
| `named_competitor_search.py` | By name search |
| `nalog/` | nalog.ru finance service |
| `osm_discovery.py` | OpenStreetMap |
| `pre_sale_folder.py` | Folder structure |
| `prescan_orchestrator.py` | Prescan flow |
| `project_creator.py` | Create projects |
| `report_generator.py`, `report_scheduler.py` | Reports |
| `roszdravnadzor/` | Medical license check |
| `scraping_service.py` | Web scraping |
| `service_extractor.py` | Extract services from site |
| `email/` | Email sending |
| `payment/` | Payment processing |
| `documents/` | Document handling |
| `document_processing/` | Doc processing |
| `onboarding/` | Onboarding flow |
| `ci/` | CI analysis service |
| `analytics/` | Analytics service |
| `sales/` | Sales service |
| `rusprofile/` | Company profiles |
| `contracts/` | Contracts |
| `retention/` | Data retention (partition_manager) |

---

### `/opt/aim/AIM/hermes/skills/aim/` (5 skills)

```
aim/
├── BOOTSTRAP.md           # First-run self-study prompt
├── SOUL.md                # Identity (47 KB в образе, 106 KB в volume)
├── SOUL.backup.md         # backup
├── kpi.md                 # KPI definitions
├── learnings.md           # Learning diary
├── processes.md           # Process docs
└── services.md            # Services docs
```

### `/opt/aim/AIM/hermes/skills/aim-scout/`

Конкурентная разведка (16 фаз сбора данных).

### `/opt/aim/AIM/hermes/skills/client-onboarding-pipeline/`

15-фазный onboarding клиентов (v5.5.0).

### `/opt/aim/AIM/hermes/skills/deep-research-phase-0/`

Deep research pattern.

### `/opt/aim/AIM/hermes/skills/software-development/`

Software development tasks.

---

### `/opt/aim/AIM/wordpress-core/wp-content/themes/aim-theme/`

**Активная тема WordPress** (v2.1.76). 38 элементов в корне.

Основное:
- `style.css` — theme metadata
- `functions.php` — setup, CPT research, Phase 09 endpoints
- `aim-pro-endpoints.php` — Phase 09 fallback REST API (172 строки)
- `front-page.php`, `home.php`, `index.php`
- `header.php`, `footer.php`
- `page-*.php` (7 static pages: prices, philosophy, contact, privacy, confidentiality, requisites, sessions)
- `chat-inline.php` — активный inline chat на главной
- `chat-inline-pro.php` — Phase 09 inline chat
- `archive-research.php` — CPT research archive
- `design-showcase-dual-theme.html` — design reference (102 KB)
- `nachalo-clinica-proposal.html` — demo proposal
- `assets/` — JS/CSS bundles
- `chat/` — React chat (hermes-chat.html, hermes-chat-glass.html, src/, dist/)
- `docs/` — documentation
- `node_modules/` (15.7 MB, МУСОР)
- `*.bak`, `*.backup-*` (5 backup файлов)

---

## 📊 Сводная статистика

### По типам файлов

| Тип | Кол-во | Где |
|---|---:|---|
| Python (.py) в `src/aim/` | 134 + 76 тестов | AIM backend |
| Python в `hermes/app/` | 59 (tools) + 12 (core) | Hermes |
| Python в `src/meai/` | 61 (framework) | дубликат |
| Markdown (.md) в корне AIM | 233 | документация |
| PHP в aim-theme | ~15 | WordPress theme |
| TypeScript/TSX в frontend | 90 | Next.js |
| Docker compose файлы | 4 | оркестрация |

### По размерам (топ)

| Путь | Размер |
|---|---:|
| `/opt/aim/AIM/.venv/` | **236 MB** |
| `/opt/aim/AIM/logs/app.log` | **62 MB** |
| Docker image `aim` | **3.13 GB** |
| Docker image `aim-hermes` | **3.21 GB** |
| Docker image `paperclip-paperclip` | **2.76 GB** |
| Docker image `grafana/grafana` | 1.47 GB |
| Docker image `prom/prometheus` | 593 MB |
| `/opt/aim/AIM/logs/nginx/` | **25 MB** |
| `/opt/data/bin/tirith` | **22 MB** |
| `aim-theme/node_modules/` | **15.7 MB** |
| `/opt/aim/AIM/.planning/` | 3.1 MB |
| `/opt/aim/AIM/frontend/` (local) | 3.5 MB |
| `/opt/aim/AIM/obsidian/` | 7.1 MB |
| `/opt/aim/AIM/src/aim/subagents/` | 3.0 MB |
| `/opt/aim/AIM/src/aim/services/` | 2.4 MB |

---

## 🔑 Файлы с чувствительными данными

| Файл | Содержимое |
|---|---|
| `/opt/aim/AIM/.env.production` | Все API ключи (DeepSeek, Apify ×14, Firecrawl ×15, Telegram, WP_DB, POSTGRES, Redis) |
| `/opt/aim/AIM/.env.production.bak-20260617-150905` | Старый snapshot |
| `/opt/data/firecrawl_keys.json` | 15 Firecrawl keys |
| `/opt/data/keys/key_pool.json` | Key pool config |
| `/opt/data/keys/rotation_state.json` | Rotation state |
| `/opt/data/auth.json`, `auth.lock` | Telegram auth state |
| `/opt/aim/AIM/data/apify_keys.json` | Apify keys (также в .env) |
| `/opt/aim/AIM/data/apify_keys.json.bak` | backup |

**Внимание:** эти файлы **нельзя** коммитить в git или публиковать.

---

## 📁 Директории для git ignore (если ещё не)

```
# Already cleaned in commit 017acba
backup-june24-work-*
hermes-backup-*
.playwright-mcp/

# Should be added
.venv/
.planning/
.cache/
.pytest_cache/
.local/
.superflow/
.backups/
hermes/_archive/
hermes/knowledge/
logs/
data/test_*.db
data/ci-*.json
node_modules/
*.bak
*.backup-*
```

---

*Этот документ — карта файлов. Используй для навигации при рефакторинге.*
