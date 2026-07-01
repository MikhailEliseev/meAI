# 05 — Dead Code Inventory

Полный список zombie-кода, legacy-файлов, дубликатов и мусора. Готов к удалению.

---

## 🧟 Категория 1: Deprecated архитектурные слои

### Magisters (19 файлов, 260 KB)

**Локация:** `/opt/aim/AIM/src/aim/magisters/`

CLAUDE.md явно: "Магистры deprecated, архитектура избыточна, Hermes справляется сам".

| Файл | Размер | Статус |
|---|---|---|
| `__init__.py` | — | — |
| `ads_magister.py` | — | ❌ не импортируется |
| `ads_magister_ai.py` | — | ❌ variant |
| `ads_magister_v2.py` | — | ❌ variant |
| `ads_magister_with_ci.py` | — | ❌ variant |
| `analytics_magister.py` | — | ❌ не импортируется |
| `analytics_magister_v2.py` | — | ❌ variant |
| `content_magister.py` | — | ❌ |
| `content_magister_ai.py` | — | ❌ variant |
| `content_magister_v2.py` | — | ❌ variant |
| `content_magister_with_ci.py` | — | ❌ variant |
| `seo_magister.py` | — | ❌ |
| `seo_magister_ai.py` | — | ❌ variant |
| `seo_magister_v2.py` | — | ❌ variant |
| `seo_magister_with_ci.py` | — | ❌ variant |
| `prescan_magister.py` | — | ❌ |
| `sales_admin_magister.py` | — | ⚠️ в try/except в main.py |
| `sales_admin_base.py` | — | ❌ |
| `linear_mixin.py` | — | ❌ Linear интеграция не используется |

**Подтверждение неиспользуемости:**
```bash
$ grep -rE "from src.aim.magisters|from .magisters" /opt/aim/AIM/hermes/
(empty)

$ grep -rE "magister" /opt/aim/AIM/src/aim/api/*.py
(только sales_admin в main.py)
```

**Действие:** удалить всю директорию. Если `sales_admin_magister` важен — выделить в отдельный сервис.

---

### Subagents (133 файла, 3.0 MB)

**Локация:** `/opt/aim/AIM/src/aim/subagents/`

CLAUDE.md явно: "CI Orchestrator (23 агента, 16 фаз) заменён прямым вызовом инструментов".

**Подкатегории:**
- `subagents/ads/` — Ads Campaign Creator, Ads Magister helpers
- `subagents/analytics/` — Analytics Agent, Base Domain Analytics
- `subagents/seo/` — Keyword Research, Content Gap Analysis
- `subagents/content/` — Content Writer Agent
- `subagents/social_agent.py`
- `subagents/competitive_intel/` — **23 файла CI orchestrator**
- `subagents/sales/` — Knowledge Manager

**Использование:**
```bash
$ grep -rE "from src.aim.subagents|from .subagents" /opt/aim/AIM/hermes/
(empty)

$ grep -rE "subagents" /opt/aim/AIM/src/aim/api/*.py
- /opt/aim/AIM/src/aim/api/content.py:42: from src.aim.subagents.competitive_intel.orchestrator.ci_orchestrator import CIOrchestrator
- /opt/aim/AIM/src/aim/api/sales.py:23: from src.aim.subagents.sales.knowledge_manager import KnowledgeManager
- /opt/aim/AIM/src/aim/api/seo.py:131: from src.aim.subagents.competitive_intel.orchestrator.ci_orchestrator import CIOrchestrator
```

Только 3 endpoints ссылаются на subagents. Все три — формальные импорты в lazy function.

**Действие:** удалить `competitive_intel/`, `ads/`, `analytics/`, `seo/`, `content/`, `social_agent.py`. `sales/knowledge_manager.py` проверить отдельно.

---

### EventBus (используется минимально)

**Локация:** `/opt/aim/AIM/src/aim/orchestration/shared_event_bus.py`

- Таблицы `event_bus_events` (0 строк), `event_bus_messages` (4 строки)
- Импортируется в main.py (lifespan), api/content.py, api/seo.py

**Действие:** удалить, заменить прямым вызовом endpoint (если нужно) или вообще убрать event-driven архитектуру.

---

### `agents/ci_swarm/`

**Локация:** `/opt/aim/AIM/src/aim/agents/ci_swarm/`

Не используется. Swarm логика для CI orchestrator.

**Действие:** удалить.

---

### `integration/ci_magisters_integration.py`

**Локация:** `/opt/aim/AIM/src/aim/integration/`

CI Magisters integration — deprecated вместе с magisters.

**Действие:** удалить.

---

## 🧟 Категория 2: Hermes pipeline v7 (2692 строки)

**Локация:** `/opt/aim/AIM/hermes/app/pipeline/`

| Файл | Строк | Назначение |
|---|---:|---|
| `engine.py` | 1841 | PipelineEngine v7 State Machine |
| `phases.py` | 451 | 14 фаз definitions |
| `file_guard.py` | 175 | File protection |
| `mode_gate.py` | 131 | Mode gating |
| `states.py` | 94 | State definitions |
| `test_all_phases.py` | 165 | Tests |
| `test_phase.py` | 97 | Tests |
| `test_tools.py` | 49 | Tests |

**Подтверждение неиспользуемости:**
- `agent_wrapper.py` переписан на жёсткий 3-сообщений формат (commit 017acba)
- В логах за 24h — `app.pipeline.engine` warnings показывают что engine **частично вызывается** (PipelineEngine: could not detect city / specialization), но это скорее legacy paths

**Действие:** проверить, действительно ли pipeline engine мёртв. Если да — удалить всю директорию.

---

## 🧟 Категория 3: Hermes legacy файлы

### `omniroute_direct.py`

**Локация:** `/opt/aim/AIM/hermes/app/omniroute_direct.py`

CLAUDE.md: "Legacy LLM proxy, not used since DeepSeek API direct".

**Действие:** удалить.

---

### Hermes `_archive/`

**Локация:** `/opt/aim/AIM/hermes/_archive/20260621/`

```
3PHASE_PIPELINE.md
presale-pipeline/
```

Старый 3-фазный pipeline (18 KB) и presale-pipeline skill. Не используются.

**Действие:** удалить (в git history останется).

---

### Hermes `knowledge/`

**Локация:** `/opt/aim/AIM/hermes/knowledge/`

188 KB LLM Wiki. CLAUDE.md: "Obsidian vaults для агентов не используется кроме teacher и architect".

**Действие:** удалить.

---

### Hermes `patches/`

**Локация:** `/opt/aim/AIM/hermes/patches/`

```
__init__.py
firecrawl_provider_bank.py
```

Patches для firecrawl — вероятно уже в основном коде.

**Действие:** проверить, удалить если дублирует.

---

### Hermes `mcp-proxy/`

**Локация:** `/opt/aim/AIM/hermes/mcp-proxy/`

```
proxy.py
```

MCP protocol bridge. По описанию "external clients use it" — неясно, запущен ли.

**Действие:** проверить usage, удалить если не запущен.

---

## 🧟 Категория 4: Дубликаты framework

### meai framework — ДВА ЭКЗЕМПЛЯРА

```
/opt/aim/src/meai          868 KB   ← root level
/opt/aim/AIM/src/meai      820 KB   ← inside AIM

  Common subdirectories: agents, core, events, integrations,
                         knowledge, learning, memory, models,
                         reports, storage, tracking
```

В Docker PYTHONPATH: `/app/AIM:/app:/app/src` — значит `/opt/aim/AIM/src/meai` это тот, что используется.

**Действие:** удалить `/opt/aim/src/meai` (внешний).

---

## 🧟 Категория 5: Локальные копии того что в Docker

### `/opt/aim/AIM/frontend/` (3.5 MB)

Локальная копия Next.js проекта. В Docker собирается образ `aim-frontend:latest` из этих исходников, но в runtime — всё из образа.

**Действие:** удалить после подтверждения что Dockerfile не зависит от этой директории (или что есть CI rebuild).

---

### `/opt/aim/AIM/.venv` (236 MB)

Python venv на хосте. В Docker образах есть свой `site-packages`.

**Действие:** удалить.

---

### `/opt/aim/AIM/.planning` (3.1 MB)

CLAUDE.md: ".planning — исторические планы, не актуальны".

**Действие:** удалить.

---

## 🧟 Категория 6: WordPress theme node_modules

**Локация:** `/var/www/html/wp-content/themes/aim-theme/node_modules/` (в Docker volume)

**Размер:** 15.7 MB

`node_modules` в production volume. Build артефакты (chat-bundle.js, chat-bundle.css) уже в `chat/dist/`.

**Действие:** удалить и добавить в `.dockerignore`.

---

## 🧟 Категория 7: Backup files (15+ файлов)

### В Hermes app

```
/opt/aim/AIM/hermes/app/main.py.backup-phase09-20260628-075019
/opt/aim/AIM/hermes/app/main.py.backup-phase09-20260628-075030
/opt/aim/AIM/hermes/app/agent_wrapper.py.bak
```

### В WordPress theme

```
aim-theme/chat-inline.php.backup-1781386127
aim-theme/chat-inline.php.backup-before-pro
aim-theme/chat-inline.php.backup-1781787857
aim-theme/chat/hermes-chat.html.bak
aim-theme/functions.php.bak
```

### В AIM root

```
/opt/aim/AIM/docker-compose.yml.bak
/opt/aim/AIM/docker-compose.headroom-deepseek.yml.backup
/opt/aim/AIM/SESSION.md.bak
/opt/aim/AIM/ROADMAP.md.bak
/opt/aim/AIM/.env.production.bak-20260617-150905
/opt/aim/AIM/data/apify_keys.json.bak
```

### В Hermes skills

```
/opt/hermes/skills/aim/SOUL.backup.md
```

**Действие:** удалить все `*.bak`, `*.backup-*`, `*.backup-*`. Git history — единственный backup.

---

## 🧟 Категория 8: Logs без ротации

### `/opt/aim/AIM/logs/app.log` — 62 MB

Логи FastAPI app. Без ротации (или с плохой).

### `/opt/aim/AIM/logs/nginx/` — 25 MB

Логи nginx на хосте. Дублирует access.log/error.log в контейнере.

**Действие:** настроить logrotate или удалить (логи в Docker json-driver есть).

---

## 🧟 Категория 9: Тестовые SQLite БД

**Локация:** `/opt/aim/AIM/data/`

```
test_init.db              36 KB
test_ads_agent.db         56 KB
test_content_writer.db    56 KB
test_complete_system.db   68 KB
test_seo_real.db          68 KB
```

Тестовые БД в production-директории.

**Действие:** удалить.

---

## 🧟 Категория 10: CI cached результаты

**Локация:** `/opt/aim/AIM/data/`

```
ci-audits.json
ci-competitors.json
ci-content-improved.json
ci-content.json
ci-deep/                1.2 MB
ci-tech/                1000 KB
ci-ecosystem.json
ci-factcheck.json
ci-finance.json
ci-marketing-strategy.json
ci-offer.json
ci-offer-клиент.md
ci-offer-тестовая-клиника.md
ci-pricing.json
ci-prioritizer.json     52 KB
```

Cached результаты старых CI analyses. В `/opt/data/sessions-archive/` уже есть эти данные по сессиям.

**Действие:** удалить (или заархивировать если нужны для тестирования).

---

## 🧟 Категория 11: Прочий мусор

### `/opt/data/bin/tirith` (22 MB)

Бинарник неизвестного назначения в `aim_hermes_data` volume.

**Действие:** выяснить происхождение (дата 19 июня), удалить.

---

### `.cache/`, `.pytest_cache/`, `.local/`, `.superflow/`, `.playwright-mcp/`

**Локация:** `/opt/aim/AIM/`

- `.cache/` — 20 KB
- `.pytest_cache/` — 264 KB
- `.local/` — 36 KB
- `.superflow/` — 92 KB
- `.playwright-mcp/` — 128 KB

Dev-артефакты.

**Действие:** удалить.

---

### `.superflow-state.json`, `.current-task`, `*.md` старые

Файлы в корне AIM:
```
.superflow-state.json     (1.5 KB)
.current-task             (104 B)
2026-05-04.md             (0 B - пустой)
```

233 markdown файлов в корне AIM — много исторических (CHECKPOINTS.md 92 KB, ARCHITECT_GUIDE.md 25 KB, etc.).

**Действие:** переместить исторические .md в `docs/archive/`, удалить пустые.

---

### `hermes-temp/`, `hermes-archive/`, `hermes-backup-*`, `backups/`

```
/opt/aim/hermes-temp/                  (временный compose)
/opt/hermes-archive/                   (5 KB + tar.gz 43 KB)
/opt/hermes-backup-20260618-000755/    (старый бекап)
/opt/aim/AIM/.backups/                 (64 KB)
/opt/backups/                          (внутренние бекапы сервера)
```

**Действие:** удалить старые бекапы (старше 30 дней), оставить один канонический.

---

### `ChatExport_2026-06-18.zip` (416 KB)

**Локация:** `/opt/data/`

Telegram chat export.

**Действие:** заархивировать или удалить.

---

## 📊 Сводка по объёму удаляемого

| Категория | Кол-во файлов | Размер |
|---|---:|---:|
| Magisters | 19 | 260 KB |
| Subagents | 133 | 3.0 MB |
| EventBus | 3 | 60 KB |
| ci_swarm, integration | 5+ | ~100 KB |
| Hermes pipeline v7 | 8 | ~150 KB |
| Hermes legacy (omniroute, _archive, knowledge, patches, mcp-proxy) | ~10 | 200 KB |
| Дубликат meai | ~60 | 868 KB |
| Локальный frontend | 90 | 3.5 MB |
| .venv | — | **236 MB** |
| .planning | ~50 | 3.1 MB |
| Theme node_modules | ~500 | **15.7 MB** |
| Backup files | 15+ | ~150 KB |
| Логи без ротации | 2 | **87 MB** |
| Тестовые SQLite БД | 5 | 280 KB |
| CI cached results | ~30 | 2.4 MB |
| tirith binary | 1 | **22 MB** |
| Dev artifacts | ~10 | 540 KB |
| **ИТОГО** | **~950 файлов** | **~370 MB** |

---

## ⚠️ Перед удалением

1. **Сделать полный backup** Docker volumes (postgres, hermes_data, wp_content, wp_db)
2. **Закоммитить** состояние git
3. **Создать тег** `pre-cleanup-20260630`
4. **Удалять по фазам**, не всё сразу
5. **После каждой фазы** — smoke test: `curl https://iamaim.ru/` + `curl https://iamaim.ru/api/chat` (с Bearer)

---

## 🎯 Порядок удаления (безопасный)

1. **Фаза 1 (низкий риск):** Backup files, .cache, .pytest_cache, .playwright-mcp, тестовые SQLite, CI cached results, ChatExport, logs без ротации
2. **Фаза 2 (средний риск):** .venv, .planning, дубликат meai, frontend локально, theme node_modules
3. **Фаза 3 (высокий риск — требует тестирования):** Magisters, Subagents, EventBus, Hermes pipeline v7, omniroute_direct, _archive, knowledge, mcp-proxy
4. **Фаза 4 (требует понимания):** tirith binary, aim-paperclip

---

*Этот документ — карта для cleanup. Каждый пункт требует подтверждения перед удалением.*
