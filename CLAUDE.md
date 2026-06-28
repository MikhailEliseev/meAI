# meAI Assistant

## Session Recovery (READ THIS FIRST!)

**⚠️ ВАЖНО: Компакт-саммари может ВРАТЬ!**
После компакта сессии саммари смешивает задачи из разных сессий и может выставить неправильные приоритеты. НЕ доверяй тегам CRITICAL в саммари слепо. SESSION.md — твой единственный надёжный источник.

**При обрыве сессии (СТРОГИЙ ПОРЯДОК):**

1. **Читай `SESSION.md`** — секция «Текущий фокус» = что ты делаешь ПРЯМО СЕЙЧАС. Это ИСТИНА.
2. **Читай `.current-task`** — одна строка, дубль SESSION.md, иммунна к компакту
3. **Если SESSION.md и компакт-саммари противоречат друг другу** — верь SESSION.md, игнорируй саммари
4. **CHECKPOINTS.md** — только если нужна историческая справка (85KB, не для быстрого восстановления)
5. **Auto-memory загружается автоматически** — знания о проекте

**Цель:** Восстановление контекста за < 30 секунд

**ЖЁСТКОЕ ПРАВИЛО:** Обновляй `SESSION.md` и `.current-task` при КАЖДОМ переходе к новой задаче. Без исключений.

---

## Project Overview

**meAI** — CEO-архитектор, который проектирует и создаёт **AIM** (AI-first medical marketing agency at iamaim.ru).

```
meAI/                           # Command Center
├── src/meai/                   # Framework (core, agents, events, memory, storage)
├── AIM/                        # Agency (приложение)
│   ├── src/aim/                # magisters/, subagents/, services/
│   ├── hermes/                 # Hermes AI agent (FastAPI + hermes-agent)
│   ├── obsidian/               # Vaults агентов (LLM Wiki)
│   └── frontend/               # Next.js landing
├── obsidian/architect/         # Твой vault
└── SESSION.md                  # Текущая работа
```

**User Role:** Medical marketer building AI-first agency
**Stack:** Python 3.11+, FastAPI, PostgreSQL, Redis, Docker, Next.js
**Deploy:** Docker на Polish server 78.17.128.169 (`ssh aim`) — см. auto-memory `deploy-target.md`

---

## Development Philosophy

### Deep & Correct
Делаем всё глубоко и правильно, без спешки. Полная автономность компонентов. Каждый агент — код с логикой, не просто vault. Никаких заглушек.

### Quality Over Speed
Качество важнее скорости. Поверхностный анализ = катастрофа. Если есть выбор между "быстро" и "качественно" → всегда качественно.

### Complete Before Next
Доводим до 100% перед переходом к следующей задаче. Не предлагаем варианты, пока текущая не завершена. Запрещено оставлять stubs "на потом".

### Mock Data Rule
Никаких mock данных в production коде. Агент запрашивает у пользователя или получает реальные данные из источника. Исключения: unit тесты (только в `tests/`).

### Large File Write Rule
Write tool имеет ограничение ~20-30 KB. Файлы 200+ строк разбивай на части: Write для первых 150-200 строк, Bash append для остального.

### Spec Writer Rule
При создании спецификаций агентов всегда используй spec-writer skill (`/spec-writer`). Skill делает deep research и даёт больше деталей, чем твои знания.

### Auto-Commit Before Deploy Rule

**КРИТИЧНО:** Любые изменения в `AIM/hermes/` или `AIM/theme/` **ОБЯЗАТЕЛЬНО** коммитятся перед деплоем на сервер.

**Перед каждым `docker cp` или `scp` на сервер:**
```bash
./scripts/auto-commit-deploy.sh
```

Скрипт автоматически:
1. Проверяет наличие изменений (`git status -s`)
2. Коммитит все изменения с меткой `auto: pre-deploy snapshot YYYYMMDD-HHMMSS`
3. Записывает в commit message: branch, timestamp, текущую задачу из `.current-task`

**Почему это важно:**
- Предотвращает потерю незакоммиченных изменений при откате сервера
- Сохраняет историю всех деплоев
- Позволяет восстановить любую версию из git

**Исключения:** Если изменения экспериментальные и точно не нужны в истории — явно скажи "не коммитить".

---

### Teacher Agent Rule

**Teacher Agent — Chief Learning Officer системы.** Его задача: следить за источниками знаний и обучать агентов, чтобы система не устаревала.

**ЗАПРЕЩЕНО:**
- ❌ Copy-paste одинаковых паттернов во все субагенты
- ❌ «Обучение» без deep research для каждого субагента
- ❌ Общие решения (Circuit Breaker, Retry, Rate Limiting) для всех
- ❌ Пропускать GitHub search специализированных решений

**ОБЯЗАТЕЛЬНО для каждого субагента:**
- ✅ Индивидуальное deep research
- ✅ GitHub search с правильными запросами (например: «yandex direct api python» для Ads)
- ✅ Клонирование и изучение кода из топовых репо
- ✅ Извлечение специфичных для домена паттернов

**Цикл обучения (каждые 2-4 недели):**
1. Проверить дату последнего обучения субагента
2. GitHub Search: новые топовые репо, обновления существующих
3. Deep Research: новые best practices, API updates
4. Gap Analysis: что есть в топовых решениях, но нет у нас
5. Learning Report с приоритетами: 🔴 CRITICAL (внедрить немедленно), 🟡 HIGH (запланировать), 🟢 LOW (backlog)

**Метрики:** Coverage (% субагентов проверено), Freshness (знания < 4 недель), Impact (% рекомендаций внедрено)

---

## Architecture: LLM-First Tool Orchestration

AIM — это набор инструментов (tools), которые LLM (Hermes) вызывает по своему усмотрению. Никакой хардкод-оркестрации. Модель решает, что и когда вызывать.

### Как это работает
1. Клиент пишет в чат на iamaim.ru
2. Hermes (LLM) получает сообщение + полный список инструментов (17 штук)
3. LLM сама решает, какой инструмент вызвать, в каком порядке
4. Результат инструмента возвращается LLM
5. LLM формирует ответ клиенту

### Смена модели
Меняется одна переменная: `LLM_MODEL` в `.env`. Всё остальное работает без изменений.

### Инструменты Hermes (17 штук)

**aim-operations (15 tools):**
| Tool | Что делает | Timeout |
|------|-----------|---------|
| `run_prescan` | Запускает prescan сайта (3 стадии) | 300s |
| `find_competitors` | Поиск конкурентов (Apify) | 600s |
| `present_competitors` | Форматирует конкурентов для клиента | 30s |
| `run_ci_analysis` | Глубокий анализ конкурентов | 300s |
| `run_seo_audit` | SEO-аудит | 120s |
| `run_content_analysis` | Контент-анализ | 120s |
| `run_ads_report` | Отчёт по рекламе | 120s |
| `show_project_status` | Статус проекта | 10s |
| `collect_contact` | Сбор контакта (имя, телефон, email) | 10s |
| `qualify_lead` | Квалификация лида | 10s |
| `escalate_to_manager` | Передача менеджеру | 10s |
| `show_all_leads` | Все лиды (для ADMIN) | 10s |
| `get_lead_pipeline` | Воронка лидов | 10s |
| `update_knowledge` | Запись знаний | 10s |
| `find_company_financials` | Финансы компании (nalog.ru) | 60s |

**hermes-debug (11 tools):**
`shell_exec`, `file_read`, `file_write`, `api_debug`, `web_fetch`, `web_search`, `firecrawl_web`, `bitrix_scrape`, `browser_screenshot`, `call_api`, `restart_myself`

### Что НЕ использовать (deprecated)
- **Магистры** (SEO, Content, Ads, Analytics) — архитектура избыточна, Hermes справляется сам
- **CI Orchestrator** (23 агента, 16 фаз) — заменён прямым вызовом инструментов
- **EventBus** — не используется в продакшене
- **Obsidian vaults для агентов** (кроме teacher и architect)
- **`.planning/`** — исторические планы, не актуальны

### AIM Agency Context

- **CRITICAL: Работаем ТОЛЬКО в коммерческой медицине.**
  - Никаких государственных учреждений (ГАУЗ, ГБУЗ, ГУЗ, МУЗ, МБУЗ)
  - Только: ООО, АО, ЗАО, ИП — частные коммерческие клиники
  - Фильтрация: `competitor_matcher.py:_is_state_healthcare()`
- AI-first approach, domain: iamaim.ru
- Российский рынок: Яндекс.Директ, Яндекс.Метрика, ФЗ-152 (не HIPAA/GDPR)
- Платёжки: ЮKassa/CloudPayments (не Stripe)
- Западные технические паттерны (AI, архитектура, CI/CD) применяются без изменений

---

## Design System — Dual Theme (КАНОНИЧЕСКИЙ РЕФЕРЕНС)

**Файл:** `AIM/wordpress-core/wp-content/themes/aim-theme/design-showcase-dual-theme.html`
**URL:** https://iamaim.ru/wp-content/themes/aim-theme/design-showcase-dual-theme.html
**CSS-переменные:** `AIM/wordpress-core/wp-content/themes/aim-theme/theme.css`

Это ЕДИНСТВЕННЫЙ источник истины для дизайна AIM. При любой работе с фронтендом, вёрсткой, стилями — сверяться с этим файлом.

### Две темы

| | Light | Dark |
|---|-------|------|
| Фон | `#ffffff` | `#0d0d0d` |
| Текст | `#1A1A1A` | `#f5f0e8` |
| Акцент | `#1A1A1A` (чёрный) | `#c9a96e` (Art Deco gold) |
| Бордер | `#E0E0E0` | `rgba(201,169,110,0.18)` |
| Glass bg | `rgba(255,255,255,0.85)` | `rgba(13,13,13,0.85)` |

### Типографика
- **Заголовки:** Playfair Display, weight 400, letter-spacing -0.01em
- **Тело:** Jost, 16px, line-height 1.7
- **Логотип:** "AIM", Playfair Display 400, 1.875rem, letter-spacing -0.02em

### Шапка (Header)
- `position: fixed`, `backdrop-filter: blur(20px) saturate(1.4)`
- Glass-фон (`var(--glass-bg)`)
- Бордер снизу: `1px solid var(--border)` (в тёмной теме — золотой оттенок)
- Таглайн "AI-first маркетинг в медицине" — центрирован абсолютно, Jost 0.75rem uppercase
- Theme toggle: круглый, 28×28px, sun/moon SVG-иконки

### Ключевые компоненты
- **Glass cards:** `backdrop-filter: blur(20px) saturate(1.4)`, дышащая анимация `card-breathe`
- **Buttons:** uppercase, letter-spacing 0.1em, border-radius 1px (острые углы)
- **Metric tags:** 5 цветов (success green, warning yellow, danger red, info blue, neutral gray)
- **Card grids:** 1px gap, hover lift-эффект
- **Water ripples:** фон в светлой теме (скрыты в тёмной)

### Переключение темы
- `localStorage` ключ: `aim-theme`
- Атрибут: `data-theme="light"|"dark"` на `<html>`
- Sun SVG видна в тёмной теме, Moon SVG — в светлой

---

## Project Structure

```
src/meai/           # Framework (переиспользуемый)
├── core/           # Architect, Orchestrator, Decision Maker
├── agents/         # Operator, BaseMagister, BaseAgent
├── events/         # Event Bus, Event Store
├── memory/         # Obsidian integration
└── storage/        # Database

AIM/                # Application (агентство)
├── src/aim/        # magisters/, subagents/, services/
├── hermes/         # Hermes AI agent
├── obsidian/       # Vaults агентов
├── frontend/       # Next.js
└── docker-compose.yml
```

Импорты: `from meai.xxx` (framework), `from aim.xxx` (agency). Работаешь из корня `/Users/mikhaileliseev/Desktop/Dev/meAI`.

---

## Hermes Backup

**Локальный архив:** `hermes-backup-20260618/` в корне проекта
- `hermes_full_20260618_213733.tar.gz` — 417 KB, полный бекап Hermes (18.06.2026)
- Содержит: `.env` (все API-ключи), `config.yaml`, скиллы (`client-onboarding-pipeline` v6.0, `ui-ux-pro-max`), скрипты (`generate-report.py`, `seo-audit.py`, `rotate_keys.py`), ключи (`key_pool.json`, `rotation_state.json`), память (`MEMORY.md`, `USER.md`)
- На сервере: `/opt/hermes-data/backups/hermes_full_20260618_213733.tar.gz`

---

## Быстрый старт для Hermes

Прочитай `/opt/data/AIM_HANDBOOK.md` — там всё про инструменты, архитектуру, пресейл, competitors, и технические детали.

<!-- GSD:project-start source:PROJECT.md -->
## Project

**Hermes v5 — Full Coverage Reports**

Переработка «души» (SOUL.md), пайплайна и оркестрации AI-агента Hermes для производства **полных отчётов пресейла** — на уровне референса `ИПХиК (2).html` (10 секций, 965 строк, 78 KB). Отказ от жёсткого pipeline-подхода v3/v7 («LLM = интерпретатор») в пользу **LLM-оркестратора с 3-проходным циклом**: сбор → анализ пробелов → допосбор + финальная сборка.

Проблема: текущий гибрид v4 (LLM-оркестратор + формальный pipeline) покрывает только ~30% данных, которые Hermes реально может собрать. Инструменты есть (40+), но LLM их не использует. Причины — требуют исследования.

**Core Value:** **Полнота данных через LLM-оркестратора с авторежимом 3 проходов.**

```
Проход 1: СБОР — LLM вызывает инструменты по ситуации, собирает сырьё
Проход 2: ГЭП-АНАЛИЗ — LLM сравнивает собранное с чек-листом покрытия
Проход 3: ДОПОСБОР + СБОРКА — LLM заполняет пробелы, генерирует отчёт
```

Это воспроизводит успешный паттерн v1 (когда админ вручную просил «перезапусти, обогати данные»), но в авторежиме — без ручного вмешательства.

### Constraints

- **Runtime:** Docker-контейнер `aim-hermes`, нельзя ломать работающий пресейл-поток
- **Модель:** DeepSeek V4 Pro, стримы рвутся на ~120с — long-running фазы нужно бить
- **Деплой:** Только через `docker cp` + перезапуск gateway (нельзя пересобирать образ)
- **Без даунтайма:** Фазы не должны прерываться при деплое изменений
- **Бюджет:** 1-2 месяца полноценной переработки (согласовано с пользователем)
- **Метрика успеха:** QC-чек-лист покрытия 10-20 пунктов (Instagram? Strategy? Offer? Динамика? СМИ-ссылки? ...)
<!-- GSD:project-end -->

<!-- GSD:stack-start source:codebase/STACK.md -->
## Technology Stack

## Languages
- Python 3.11 - Hermes agent, AIM backend services, FastAPI wrapper, key rotation scripts
- JavaScript/TypeScript - Next.js frontend, WordPress theme, Node.js MCP servers
- YAML - Configuration (`config.yaml`, `docker-compose.yml`, `prometheus.yml`)
- Shell (bash) - Docker entrypoint scripts, deployment helpers
- Markdown - Knowledge vaults, agent skills, SOUL.md identity prompt
## Runtime
- Docker Engine on Ubuntu (Polish server: `ssh aim`)
- Python 3.11-slim base image (`AIM/hermes/Dockerfile`, line 5)
- Server host Python: 3.12.3 (not used by containers)
- Docker Compose v3 (`AIM/docker-compose.yml`) — 13 containers
- Container names: `aim-hermes`, `aim-app`, `aim-frontend`, `aim-nginx`, `aim-wordpress`, `aim-mysql`, `aim-postgres`, `aim-redis`, `aim-prometheus`, `aim-grafana`, `aim-alertmanager`, `aim-postgres-exporter`, `aim-node-exporter`
- Production image: `aim-hermes-nous:backup-2026-06-18` (Nous Research official Hermes agent)
- Custom image: `aim-hermes:latest` built from `AIM/hermes/Dockerfile`
- Both use `python:3.11-slim` base
- Process: `uvicorn app.main:app --host 0.0.0.0 --port 8000`
- Volume mount: `hermes_data:/opt/data` (persistent state.db, sessions, config, keys)
- Volume mount: `./hermes/skills:/opt/hermes/skills:ro` (agent skills)
- pip (no lockfile — `requirements.txt` only, pinned versions)
- requirements.txt at `AIM/hermes/requirements.txt`
- npm for Node.js MCP servers (firecrawl-mcp, apify actors MCP, novamira WordPress MCP)
## Frameworks
- **Nous Research Hermes Agent v0.14.0** - AI agent framework, LLM orchestration, tool registry, session management
- **FastAPI** - Custom HTTP wrapper (`app/main.py`) for Next.js chat proxy, SSE streaming, Telegram webhook, Prometheus metrics
- **Uvicorn** - ASGI server (launched in Dockerfile entrypoint)
- FastAPI - AIM API (`http://app:8000`) consumed by Hermes tools over internal Docker network
- SQLAlchemy (async) - PostgreSQL ORM
- `apify_client` - Apify Actor API client with key pool rotation
- Next.js 14+ - `aim-frontend` container on port 3099
- React - Full-page chat component with SSE streaming
- WordPress PHP 8.2 - `aim-wordpress` container, theme at `AIM/wordpress-core/wp-content/themes/aim-theme/`
- `hermes-agent` built-in test framework (tests in `AIM/hermes/tests/`)
- `AIM/hermes/app/tools/test_deep_research_merge.py` — tool-specific tests
- `AIM/hermes/app/tools/test_service_categorizer.py` — tool-specific tests
- `AIM/hermes/app/tools/test_presale_pipeline.py` — pipeline tests
- Docker Compose for local development
- esbuild for chat theme JS bundling (`AIM/theme/chat/esbuild.config.mjs`)
## Key Dependencies
| Package | Version | Purpose |
|---------|---------|---------|
| `hermes-agent` | 0.14.0 | AI agent framework (core orchestrator) |
| `httpx` | 0.28.1 | Async HTTP client for all AIM API calls |
| `telethon` | >=1.39.0,<2.0 | Telegram user-client for outgoing messages + channel search |
| `assemblyai` | >=0.38.0,<1.0 | Voice message transcription (ogg/opus from Telegram) |
| `pydantic` | 2.12.5 | Data validation for FastAPI models |
| `tenacity` | 9.1.4 | Retry logic (used across tools and services) |
| `pyyaml` | 6.0.3 | YAML config parsing |
| `firecrawl-py` | >=4.28.0 | Firecrawl web scraping SDK |
| Package | Purpose |
|---------|---------|
| `beautifulsoup4`, `lxml`, `parsel` | HTML parsing for web scraping |
| `pymysql` | MySQL/MariaDB connector (WordPress DB for report publishing) |
| `instagrapi`, `instaloader` | Instagram private API scraping |
| `playwright` + Chromium | Headless browser automation |
- `apify_client` (async) - Apify Actor API
- `fast_bitrix24` - Bitrix24 REST API client
- `pybreaker` - Circuit breaker pattern for external services
- `aiosqlite` - Async SQLite for session DB
- `asyncpg` - Async PostgreSQL driver
- `redis` (aioredis) - Redis caching and queues
- In-memory Python metrics (custom) exposed at `/metrics` in Prometheus text format
- `prometheus-client` for AIM app Prometheus metrics
- Prometheus + Grafana + Alertmanager + node-exporter + postgres-exporter — full monitoring stack
## Configuration
- Primary: `config.yaml` at `$HERMES_HOME/config.yaml` (`/opt/data/config.yaml` on server)
- Key sections:
| Variable | Purpose |
|----------|---------|
| `DEEPSEEK_API_KEY` | Primary LLM provider API key |
| `DEEPSEEK_BASE_URL` | DeepSeek API base URL |
| `APIFY_API_TOKEN` + `_01` through `_13` | 14 Apify rotating keys |
| `FIRECRAWL_API_KEY` + `_01` through `_14` | 15 Firecrawl rotating keys |
| `OPENROUTER_API_KEY` | Alternative model gateway |
| `TELEGRAM_HOME_CHANNEL` | Telegram channel for Hermes notifications |
| `TELEGRAM_HOME_CHANNEL_THREAD_ID` | Thread ID within that channel |
| Variable | Purpose |
|----------|---------|
| `HERMES_API_KEY=hmr_...` | API key for Next.js → Hermes authentication |
| `HERMES_URL=http://hermes:8000` | Internal Docker network URL for Hermes |
| `HERMES_MODEL=deepseek-v4-pro` | Default model name |
| `TELEGRAM_BOT_TOKEN`, `TELEGRAM_ADMIN_CHAT_ID` | Telegram Bot API credentials |
| `TELEGRAM_WEBHOOK_URL=https://iamaim.ru/telegram/webhook` | Webhook endpoint |
| `TELEGRAM_API_ID`, `TELEGRAM_API_HASH` | Telethon user-client credentials |
| `BRAVE_API_KEY` | Brave Search API key |
| `FIRECRAWL_API_KEY` | Firecrawl default key |
| `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_DB` | PostgreSQL credentials |
| `WP_DB_HOST`, `WP_DB_USER`, `WP_DB_PASSWORD`, `WP_DB_NAME` | WordPress/MariaDB credentials |
| `REDIS_URL=redis://redis:6379/0` | Redis connection |
| `SESSIONS_ROOT=/opt/data/sessions-archive` | Session archive path |
| `ARCHIVE_BASE_URL=https://iamaim.ru/wp-json/aim/v1/session` | Archive API endpoint |
## Platform Requirements
- Python 3.11+
- Docker Desktop (for local Docker Compose)
- Git
- SSH access to Polish server (`ssh aim`)
- Ubuntu Linux (Polish server, IP 78.17.128.169)
- Docker Engine with Docker Compose
- 13 running containers (Hermes, AIM app, Frontend, Nginx, WordPress, MySQL, PostgreSQL, Redis, Prometheus, Grafana, Alertmanager, postgres-exporter, node-exporter)
- Nginx reverse proxy handling SSL termination (Let's Encrypt)
- Internal Docker network `aim-network` (bridge mode)
- Persistent Docker volumes: `hermes_data`, `postgres_data`, `redis-data`, `prometheus-data`, `grafana-data`, `aim_wp_content`, `aim_wp_db`
## Model Configuration Details
- Purpose: Non-streaming proxy that wraps DeepSeek chat completions as SSE to work around streaming timeouts
- Listens on `127.0.0.1:11888` (PROXY_PORT env var)
- Reads API key directly from `.env` files (not environment variables)
- Returns SSE-wrapped completion in a single POST response
- Started separately from the main Hermes container (not in Dockerfile entrypoint)
- Purpose: Direct OpenAI SDK wrapper bypassing AIAgent for fast non-streaming responses
- Used by Telegram gateway when AIAgent streaming times out
- Model: `HERMES_MODEL` env var (default `deepseek-chat`)
- URL: `OMNIROUTE_URL` env var (default `https://api.deepseek.com`)
- Key: `OMNIROUTE_AUTH` env var
- `base_url`: `OMNIROUTE_URL` (env var)
- `api_key`: `OMNIROUTE_AUTH` (env var)
- `provider`: `"custom"` (not built-in DeepSeek)
- `api_mode`: `"openai_chat"` (OpenAI-compatible API)
- `model`: `LLM_MODEL` env var (default `ds/deepseek-v4-pro`)
- `max_tokens`: 16000
- `max_iterations`: 25
- `quiet_mode`: True
## Key Rotation
- Manages multi-key pools for Apify (14 keys) and Firecrawl (15 keys)
- Health-checks single keys: Perplexity, Brave, DeepSeek, Anthropic, Ahrefs, SEMrush, AssemblyAI
- Reads/writes `.env` file directly (preserves all non-rotated keys)
- State tracked in `/opt/data/keys/rotation_state.json`
- Rotation log: `/opt/data/keys/rotation.log`
- Key pool file: `/opt/data/keys/key_pool.json`
- Exit codes: 0=no rotation, 1=all exhausted, 2=rotated (restart needed)
- CLI modes: `--auto`, `--status`, `--check`, `--switch <service>`
- Invoked by Hermes tool `rotate_api_key` when Firecrawl/Apify return 402/credit-exhausted
- Round-robin key rotation with exhaustion tracking
- Two exhaustion types: `insufficient_credits` (permanent) and `rate_limited` (30-min recovery)
- Loads from `FIRECRAWL_KEYS_FILE` (default: `/opt/data/firecrawl_keys.json`)
- Falls back to `FIRECRAWL_API_KEY` env var if no bank file
- Minimum 1.2s interval between calls (account-level rate limit)
- Async key pool with auto-rotation on quota errors
- Loads from `APIFY_KEYS_FILE` (default: `AIM/data/apify_keys.json`)
- Detects quota keywords: "quota", "exceeded", "insufficient", "balance", "limit"
<!-- GSD:stack-end -->

<!-- GSD:conventions-start source:CONVENTIONS.md -->
## Conventions

## Naming Patterns
- Tool handlers: `handle_<tool_name>` with `async def`. Example: `handle_run_prescan()`, `handle_find_competitors()`, `handle_collect_contact()`. All tool handlers must be async.
- Private/helper functions: `_lowercase_underscore`. Example: `_normalize_args()`, `_extract_url_from_message()`, `_build_learnings_prompt()`, `_get_thread_lock()`.
- Mode prompt builders: `_mode_prompt()` where mode is lowercase. Example: `_presale_prompt()`, `_active_prompt()`, `_admin_prompt()`.
- Check functions: `_is_<condition>`. Example: `_is_allowed()` in `shell_exec.py` (`/Users/mikhaileliseev/Desktop/Dev/meAI/AIM/hermes/app/tools/shell_exec.py:68`).
- Module-level constants: `UPPER_CASE`. Example: `AIM_API_BASE`, `REQUEST_TIMEOUT`, `MAX_LATENCY_SAMPLES`, `_AGENT_TIMEOUT`, `_AGENT_CACHE_TTL`.
- Instance members: `snake_case`. Example: `self._ledgers`, `self.base`, `self._lock`.
- Global singletons: `lowercase_snake`. Example: `token_economy` (`/Users/mikhaileliseev/Desktop/Dev/meAI/AIM/hermes/app/token_economy.py:144`), `_session_db`, `_agent_cache`, `_main_event_loop`.
- Dataclasses used for state objects. Example: `LeadBudget` (`/Users/mikhaileliseev/Desktop/Dev/meAI/AIM/hermes/app/token_economy.py:21-27`).
- Pydantic `BaseModel` for API request/response models. Example: `ChatRequest`, `ChatResponse`, `HealthResponse` (`/Users/mikhaileliseev/Desktop/Dev/meAI/AIM/hermes/app/main.py:163-181`).
- Typed dicts via plain `dict` typed with `dict[str, ...]` annotations.
- Tool files: `snake_case.py` matching tool name. Example: `run_prescan.py`, `find_competitors.py`, `collect_contact.py`.
- Core modules: `snake_case.py`. Example: `agent_wrapper.py`, `token_economy.py`, `voice_transcriber.py`.
- Test files: `test_<module>.py`. Example: `test_deep_research_merge.py`, `test_service_categorizer.py`, `test_presale_flow.py`.
- Router files: `<domain>_api.py` or `<domain>_router.py`. Example: `session_api.py`, `knowledge_router.py`.
## Code Style
- No formatter tool detected (no `.prettierrc`, `pyproject.toml` with formatter config, or `eslint.config.*` in Hermes directory).
- Manual indentation uses 4 spaces consistently.
- Docstrings use triple-quote `"""` with a single-line summary, blank line, then details.
- Section separators use `# ── Name ──` comment style with 60-char dashes. Example from `main.py:85`: `# ── Metrics ──` and `agent_wrapper.py:28`: `# ── Persistent session DB (survives container restarts) ──`.
- No linting tool configuration detected in Hermes directory.
- Pylint/mypy/flake8 not configured.
- Code relies on Python runtime `logging` for observability, not static analysis.
- Generally 100-120 characters. No enforced limit.
- File-level docstrings describe purpose and reference architecture decisions ("Per D-10", "Per Pitfall 2"). Example: `agent_wrapper.py:1-12`.
- Inline comments explain "why" not "what". Example: `agent_wrapper.py:32`: `# Cache is an optimisation, not the source of truth`.
- Architecture decision references use `Per D-NN` or `Per Pitfall N` prefixes consistently across all files.
## Import Organization
- No path aliases configured (no `pyproject.toml` with `[tool.pytest.ini_options]` or `setup.py` `package_dir`).
- Internal framework imports use `hermes_state`, `run_agent`, `tools.registry` — these resolve from the hermes-agent package installed in the Docker image.
- Cross-module imports use relative paths: `from .auth import verify_api_key`, `from .agent_wrapper import run_agent`.
- Every module defines `logger = logging.getLogger(__name__)` at module level.
- Root logger configured in `main.py` with `INFO` level and format: `"%(asctime)s [%(levelname)s] %(name)s: %(message)s"`.
- `logger.info()` for normal operations, `logger.warning()` for non-critical issues, `logger.error()` for failures, `logger.exception()` inside except blocks for full tracebacks.
- Debug logging via `logger.debug()` used sparingly (mostly in `agent_wrapper.py` for tool extraction details).
## Error Handling
- `run_agent_sync()` wraps the AIAgent call in `ThreadPoolExecutor` with `future.result(timeout=_AGENT_TIMEOUT=900s)`. On timeout, it returns a user-facing apology message (not the raw exception). Also handles the race condition where the future completes at the exact instant the timeout fires.
- `run_agent()` adds a second layer of `asyncio.wait_for(timeout=_AGENT_TIMEOUT+10)`.
- `_try_extract_learnings()` wraps its learning extraction in a try/except that logs warnings but NEVER propagates errors — learning failures must not break the main conversation.
- Tool handlers NEVER raise exceptions — they return error JSON.
- HTTP-level errors are always logged: `logger.error("AIM API returned error: %s", e)` or `logger.exception("...")`.
- Catch-all Exception blocks always include `logger.exception()` to preserve stack traces.
- API timeout values are declared as module-level constants (e.g., `REQUEST_TIMEOUT = 300.0`).
- Fallback patterns: `run_prescan.py` falls back to `_legacy_prescan()` when the staged endpoint returns 404 (`/Users/mikhaileliseev/Desktop/Dev/meAI/AIM/hermes/app/tools/run_prescan.py:72-76`).
## Logging
- Always use `logger.info()` for tracing tool execution: `"Running staged prescan for URL: %s", url`
- Use `%s` printf-style formatting (not f-strings) in logging calls.
- Progress reporting via `push_tool_progress()` function — a thread-safe mechanism that pushes events to an `asyncio.Queue` for SSE streaming, with fallback to `logger.info()` when no active queue.
## Argument Handling Convention
## Tool Registration Pattern
- `name`: tool name string
- `toolset`: which toolset it belongs to ("aim-operations" for business tools, "hermes-debug" for system tools)
- `schema`: OpenAI-compatible function schema with `type`, `function.name`, `function.description`, `function.parameters`
- `handler`: the async handler function
- `check_fn`: lambda returning bool (always `lambda: True`)
- `is_async`: `True` for all tools
- `description`: short one-liner
- `emoji`: decorative emoji for UI
## SKILL.md Format Conventions
### Execution Log
- [ ] Analyse website (quick_overview)
- [ ] Run prescan
- [ ] Present competitors
## Configuration Management
- `HERMES_API_KEY` — Bearer token for Next.js to Hermes communication
- `OMNIROUTE_URL` / `OMNIROUTE_AUTH` — LLM provider endpoint
- `LLM_MODEL` — model identifier (e.g., `ds/deepseek-v4-pro`)
- `HERMES_HOME` — data directory (`/opt/data`)
- `DATABASE_URL` — SQLite connection string
- `TELEGRAM_WEBHOOK_URL` — optional Telegram webhook
- Pooled API keys: `APIFY_API_TOKEN`, `APIFY_API_TOKEN_01` through `_13`, `FIRECRAWL_API_KEY`, `FIRECRAWL_API_KEY_01` through `_14`
- Single API keys: `BRAVE_API_KEY`, `DEEPSEEK_API_KEY`, `ANTHROPIC_API_KEY`, `PERPLEXITY_API_KEY`, `ASSEMBLYAI_API_KEY`, `AHREFS_API_KEY`, `SEMRUSH_API_KEY`
## Module Design
## Threading Model
- **FastAPI async endpoints** use `asyncio` event loop.
- **AIAgent calls** are synchronous and wrapped in `loop.run_in_executor()` (thread pool) for web, or `ThreadPoolExecutor` for Telegram/sync paths.
- **Per-session locking**: `asyncio.Lock` for async (web), `threading.Lock` for sync (Telegram). Both exist in `agent_wrapper.py`.
- **Thread-safe progress dispatch**: `push_tool_progress()` uses `loop.call_soon_threadsafe(queue.put_nowait, event)` to safely cross from tool thread to event loop.
- **Global singleton state**: `token_economy` uses `threading.Lock` for its in-memory dict.
<!-- GSD:conventions-end -->

<!-- GSD:architecture-start source:ARCHITECTURE.md -->
## Architecture

## System Overview
```text
|                     Chat Entry Points                              |
|  +----- iamaim.ru chat -----+  +----- Telegram bot ------+        |
|  | Next.js frontend (3099)  |  | Bot API webhook/polling  |        |
|  +------------+--------------+  +------------+-------------+        |
|               |                             |                      |
|               v                             v                      |
|                    Hermes FastAPI (port 8000)                       |
|  `AIM/hermes/app/main.py`                                          |
|  /api/chat    /api/chat/stream    /telegram/webhook                |
|  +------------+-------------------+------------------+             |
|  | auth.py    | session_api.py    | knowledge_router  |             |
|  | (Bearer)   | (archive GET)     | /api/knowledge/*  |             |
|  | agent_wrapper.py              | agent_wrapper_optimized.py      |
|  | run_agent (async)             | _presale_prompt / _active_prompt|
|  | run_agent_sync (Telegram)     | build_system_prompt()           |
|  +-------------------------------+                                 |
|  | SOUL.md (69KB identity)       | 3PHASE_PIPELINE.md              |
|  | $HERMES_HOME/SOUL.md          | (pipeline rules, when present)   |
|                  hermes-agent Library (pip package v0.14.0)         |
|  AIAgent | SessionDB (SQLite) | tools.registry | skill_view()      |
|  | Tool Registry     | Skills System            | Config           |
|  | tools.registry    | SKILL.md in /opt/hermes/ | config.yaml      |
|  | register() at     | LLM calls skill_view()   | model: deepseek  |
|  | module import     | to load context on demand| v4-pro/v4-flash  |
|                     AIM Backend (http://app:8000)                   |
|  `AIM/src/aim/` — REST API                                         |
|  /api/presale/prescan-staged    /api/competitors/find              |
|  /api/seo/audit                 /api/ads/report                    |
|  /api/leads                     /api/sales/*                       |
|  External Services                                                 |
|  PostgreSQL | Redis | DeepSeek API | Apify | Brave Search          |
|  Firecrawl  | AssemblyAI | Telegram | nalog.ru                    |
```
## Component Responsibilities
| Component | Responsibility | File |
|-----------|----------------|------|
| FastAPI App | HTTP server, routing, auth, SSE streaming | `AIM/hermes/app/main.py` |
| Agent Wrapper | AIAgent lifecycle, session persistence, sync-to-async adapter, prompt assembly | `AIM/hermes/app/agent_wrapper.py` |
| Optimized Prompt | Mode-specific system prompt fragments (PRESALE, ACTIVE, ADMIN, SALES_ADMIN) | `AIM/hermes/app/agent_wrapper_optimized.py` |
| Tool Registry | Tool registration via `registry.register()`, module-level side-effect imports | `AIM/hermes/app/tools/__init__.py` |
| Telegram Gateway | Webhook endpoint + getUpdates polling + Telethon user-client | `AIM/hermes/app/telegram_gateway.py` |
| Auth Module | Bearer token validation, HERMES_API_KEY from env | `AIM/hermes/app/auth.py` |
| Knowledge Router | Knowledge vault CRUD: ingest, search, learn, context, status | `AIM/hermes/app/knowledge_router.py` |
| Session API | Archived session retrieval by 8-char hex hash | `AIM/hermes/app/routers/session_api.py` |
| Voice Transcriber | Telegram voice message → text via AssemblyAI | `AIM/hermes/app/voice_transcriber.py` |
| Token Economy | Token usage tracking and cost monitoring | `AIM/hermes/app/token_economy.py` |
| Bootstrap System | First-run self-study: reads all tools, skills, API endpoints | `AIM/hermes/scripts/bootstrap.sh` + `AIM/hermes/skills/aim/BOOTSTRAP.md` |
| Component | Responsibility | File |
|-----------|----------------|------|
| OmniRoute Direct | Legacy LLM proxy (not used since DeepSeek API direct) | `AIM/hermes/app/omniroute_direct.py` |
| MCP Proxy | MCP protocol bridge for external clients | `AIM/hermes/mcp-proxy/proxy.py` |
## Pattern Overview
- **Hermes (LLM) decides what tools to call** — no hardcoded orchestration. The LLM reads SOUL.md, receives user message, and selects tools autonomously.
- **All AI logic lives in the LLM prompt** — SOUL.md + mode prompts define the entire behavior, workflow, and decision tree.
- **Tools are REST API proxies** — each tool call translates to a single HTTP request to `http://app:8000` (aim-app container on Docker internal network). Tools are thin wrappers around API endpoints.
- **Skills are LLM-loaded Markdown documents** — SKILL.md files are loaded by the LLM at runtime via the `skill_view()` function from hermes-agent. The LLM reads them as context and follows their instructions.
- **Dual entry points** — web chat (Next.js proxy via FastAPI) and Telegram (webhook + getUpdates polling), both flowing through the same AIAgent.
- **Session persistence in SQLite** — hermes-agent's SessionDB stores conversation history in `/opt/data/state.db`, surviving container restarts.
## Layers
- Purpose: Accept HTTP requests, verify auth, route to agent
- Location: `AIM/hermes/app/main.py` (FastAPI routes), `AIM/hermes/app/auth.py` (Bearer auth)
- Contains: Chat endpoints (sync + SSE streaming), Telegram webhook, health/metrics, session archive
- Depends on: Agent Wrapper layer
- Used by: Next.js frontend, Telegram Bot API, Prometheus, bootstrap script
- Purpose: Manage AIAgent lifecycle, build prompts, handle session caching and concurrency
- Location: `AIM/hermes/app/agent_wrapper.py`, `AIM/hermes/app/agent_wrapper_optimized.py`
- Contains: `run_agent()` (async), `run_agent_sync()` (for Telegram thread), `build_system_prompt()`, `_create_agent()`, `get_mode_prompt()`, SOUL.md caching, session locking
- Depends on: hermes-agent library (AIAgent, SessionDB)
- Used by: HTTP Layer, Telegram Gateway
- Purpose: Core AI agent framework — LLM conversation loop, tool invocation, session state, skill loading
- Location: `hermes-agent==0.14.0` pip package with extras: `[mcp, messaging, web, anthropic]`
- Contains: `AIAgent.run_conversation()`, `tools.registry` (tool registry with register() decorator), `skill_view()` (load SKILL.md into LLM context), SessionDB (SQLite session storage)
- Depends on: DeepSeek API (or OmniRoute, configurable via `config.yaml`)
- Used by: Agent Wrapper Layer
- Purpose: Register tools in the hermes-agent registry, implement tool handlers that call AIM backend API
- Location: `AIM/hermes/app/tools/*.py`
- Contains: Tool handlers (async functions), registry.register() calls at module level, HTTP calls to `http://app:8000`
- Depends on: AIM Backend (aim-app container)
- Used by: hermes-agent (LLM invokes tools via the registry)
- Purpose: Load context (SKILL.md files) into the LLM's working memory for specific tasks
- Location: `AIM/hermes/skills/` (local), `/opt/hermes/skills/` (Docker build), `/opt/data/skills/` (server runtime — curated by the system)
- Contains: SKILL.md documents with YAML frontmatter (name, version, triggers, description)
- Depends on: hermes-agent's `skill_view()` function
- Used by: LLM (reads skill content as system context on demand)
- Purpose: Execute actual business logic — prescan, competitor search, SEO audit, lead management
- Location: `AIM/src/aim/` (local), Docker container `aim-app` at `http://app:8000`
- Contains: REST API endpoints called by tool handlers
- Depends on: PostgreSQL, Redis, external APIs (Apify, nalog.ru, etc.)
- Used by: Tool Layer
## Data Flow
### Primary Request Path (Web Chat — SSE Streaming)
### Telegram Request Path
### Bootstrap Self-Study Flow
## System Prompt Assembly
- Location: `/opt/data/SOUL.md` (copied from `/opt/hermes/skills/aim/SOUL.md` at startup)
- Size: ~69KB (server), loaded once and cached in memory
- Content: Agent identity, working principles, modes of operation, tool catalog, pricing, architecture, self-learning protocols, niche detection
- Loaded via: `AIAgent(load_soul_identity=True)` for web path, `load_soul_md()` + `build_system_prompt()` for Telegram path
- Cached in: `_soul_md_cache` module variable (`AIM/hermes/app/agent_wrapper.py:57`)
- Built by `get_mode_prompt(mode)` (`AIM/hermes/app/agent_wrapper.py:130`)
- Four modes: PRESALE, ACTIVE, ADMIN, SALES_ADMIN
- Each mode prompt defines tool usage rules, dialog flow, tone, and constraints
- PRESALE prompt optionally prepends `3PHASE_PIPELINE.md` when available (`AIM/hermes/app/agent_wrapper.py:156`)
- Mode is determined by `X-Client-Mode` header (web) or chat_id lookup (Telegram)
## Key Abstractions
- Purpose: Core conversation loop — sends messages to LLM, parses tool calls, invokes registered handlers, returns results
- Created via: `_create_agent()` in `AIM/hermes/app/agent_wrapper.py:397`
- Configuration: `base_url` (DeepSeek API), `model` (deepseek-v4-pro), `session_db` (SQLite persistence), `load_soul_identity=True`, `ephemeral_system_prompt`, `enabled_toolsets=["aim-operations", "hermes-debug"]`, `max_iterations=25`
- Cached per session_id in `_agent_cache` dict with 24h TTL
- Purpose: Map tool names to handler functions and JSON schemas, exposed to LLM via function calling
- Registration pattern: `registry.register(name="run_prescan", toolset="aim-operations", schema={...}, handler=handle_run_prescan, ...)`
- Called at module import time (side-effect in each `tools/*.py` file)
- Two toolsets: `aim-operations` (business tools, 18 tools on server) and `hermes-debug` (system tools, 15 tools)
- Purpose: Load domain-specific instructions (SKILL.md) into the LLM's context on demand
- The LLM calls `skill_view(name='client-onboarding-pipeline')` to load a skill
- Skills are YAML-frontmatter Markdown files with name, version, triggers, description
- Key skills: `client-onboarding-pipeline` (v5.5.0, 15-phase onboarding), `presale-pipeline` (v3.3.0, 8-skill orchestration), `deep-research-phase-0`, `aim` (identity + supplementary docs)
- Skills are loaded dynamically by hermes-agent — the LLM decides when to invoke `skill_view()`
- Purpose: Prevent SQLite "database is locked" errors from concurrent requests on the same session
- Per-session `asyncio.Lock` for web path (`AIM/hermes/app/agent_wrapper.py:42`)
- Per-session `threading.Lock` for Telegram/sync path (`AIM/hermes/app/agent_wrapper.py:716`)
- Agent cache uses real session_id as key after first run (not input session_id)
## Entry Points
- Location: `AIM/hermes/app/main.py:263`
- Triggers: Next.js frontend (iamaim.ru chat widget) via proxy
- Responsibilities: Synchronous chat — run agent, return reply + tool_calls in JSON. Used for quick interactions that don't need streaming.
- Location: `AIM/hermes/app/main.py:312`
- Triggers: Next.js full-page chat page
- Responsibilities: SSE streaming chat — runs agent in background, streams tool-progress events in real-time, emits text-delta tokens word-by-word, 420s hard deadline
- Location: `AIM/hermes/app/telegram_gateway.py:110`
- Triggers: Telegram Bot API (when webhook is configured)
- Responsibilities: Receive Telegram messages, handle /start deep-link binding, transcribe voice, route to Hermes agent, send reply
- Location: `AIM/hermes/app/telegram_gateway.py:351` (polling loop started from `/health` or `/telegram/webhook`)
- Triggers: Automatic — starts on first health check if webhook not configured
- Responsibilities: Long-poll Telegram for messages, process through Hermes, reply via Bot API. Runs in separate OS thread.
- Location: `AIM/hermes/app/main.py:188`
- Triggers: Docker HEALTHCHECK, Prometheus scraping, bootstrap.sh
- Responsibilities: Return health status + knowledge loop stats. Lazy-initializes Telegram polling on first call.
- Location: `AIM/hermes/app/main.py:230`
- Triggers: Prometheus scraping
- Responsibilities: Expose RED metrics (Rate, Errors, Duration) + chat metrics as Prometheus text format
- Location: `AIM/hermes/app/routers/session_api.py:87`
- Triggers: Admin dashboard, report viewing
- Responsibilities: Retrieve archived session data (conversation, prescan results, CI analysis) by 8-char hex hash
## How Pipeline Execution Works
- SOUL.md defines the agent's identity, tool catalog, working principles, and presale flow steps
- Mode prompts (PRESALE) define the 3-phase approach: Phase 1 (quick_overview + run_prescan), Phase 2 (find_competitors + run_ci_analysis), Phase 3 (present results + collect contact)
- The LLM reads these as behavioral instructions and follows them autonomously
- There is NO hardcoded pipeline execution code — the LLM decides which tools to call and in what order
- `client-onboarding-pipeline/SKILL.md` (v5.5.0): Detailed 15-phase protocol with execution checklists, tool calling patterns, competitor verification, report generation
- `presale-pipeline/SKILL.md` (v3.3.0): 8-phase auto-orchestration — runs all skills sequentially without asking permission, produces HTML proposal
- Skills are loaded by the LLM calling `skill_view()` — they provide detailed instructions for complex tasks
- Skills contain execution logs with `[ ]` checkboxes — the LLM tracks completion
## Architectural Constraints
- **Threading:** FastAPI async event loop for HTTP; Telegram polling runs in a separate OS thread via `run_in_executor`; AIAgent calls are synchronous and wrapped in `ThreadPoolExecutor` with 900s timeout
- **Global state:** `_tool_progress_queue` (asyncio.Queue) is set per-request; `_agent_cache` (dict) shared across requests with threading.Lock per session; `_soul_md_cache` (string) immutable after first load
- **Circular imports:** `app.main.py` imports from `app.tools` which imports from `app.main` (for `push_tool_progress`) — resolved by late import inside `handle_run_prescan()` function body
- **SQLite concurrency:** Single-writer lock per session (both async and thread variants) prevents "database is locked" errors from state.db (21MB+ on server)
- **Network:** Hermes and aim-app communicate on Docker internal network `aim_aim-network` via DNS name `app:8000` — never exposed to host; Hermes port 8000 exposed only within Docker network (proxy:nginx → aim-frontend → Hermes)
- **Configurable LLM backend:** Switched by changing `config.yaml` model/provider or `LLM_MODEL` env var. Currently DeepSeek API direct. Previously OmniRoute proxy. SOUL.md identity, tool schemas, and mode prompts are model-agnostic.
## Error Handling
- Tool handlers catch `httpx.HTTPStatusError` and `httpx.RequestError` separately, return JSON error strings (`AIM/hermes/app/tools/run_prescan.py:109-127`)
- Agent wrapper catches `FutureTimeoutError` from ThreadPoolExecutor, returns graceful timeout message (`AIM/hermes/app/agent_wrapper.py:584-609`)
- SSE generator catches all exceptions, yields `{"type": "error", "message": ...}` SSE event (`AIM/hermes/app/main.py:445-448`)
- Failed tools should NOT be retried more than once — Mode prompts explicitly forbid re-calling failed tools
- Learnings extraction failures are logged but never propagated (fire-and-forget)
## Cross-Cutting Concerns
- `/opt/data/` — volume mount (persistent): memories, learnings, reports, sessions, proposals, skills, state.db
- `/opt/hermes/` — Docker image layer (read-only after build, but writable at runtime since it's the image root)
- `/opt/data/memories/proposals/` — where file_write creates HTML proposals
- `/opt/data/memories/learnings/` — self-learning diary entries
- `/opt/data/reports/` — large Telegram reports
- `/opt/data/.bootstrapped` — bootstrap completion flag
<!-- GSD:architecture-end -->

<!-- GSD:skills-start source:skills/ -->
## Project Skills

| Skill | Description | Path |
|-------|-------------|------|
| aim-intel | > Загрузка конкурентной разведки на сервер AIM для Hermes. Триггер: «/aim-intel», «залей конкурента», «разведка {slug}», «competitor intel». | `.claude/skills/aim-intel/SKILL.md` |
| aim-scout | > Глубокая конкурентная разведка: 16 фаз сбора данных перед LLM-анализом. Зеркальное отражение client-onboarding-pipeline, но для конкурентов. Триггер: «/aim-scout {name}», «разведай {name}», «competitor scout». | `.claude/skills/aim-scout/SKILL.md` |
| impeccable | Use when the user wants to design, redesign, shape, critique, audit, polish, clarify, distill, harden, optimize, adapt, animate, colorize, extract, or otherwise improve a frontend interface. Covers websites, landing pages, dashboards, product UI, app shells, components, forms, settings, onboarding, and empty states. Handles UX review, visual hierarchy, information architecture, cognitive load, accessibility, performance, responsive behavior, theming, anti-patterns, typography, fonts, spacing, layout, alignment, color, motion, micro-interactions, UX copy, error states, edge cases, i18n, and reusable design systems or tokens. Also use for bland designs that need to become bolder or more delightful, loud designs that should become quieter, live browser iteration on UI elements, or ambitious visual effects that should feel technically extraordinary. Not for backend-only or non-UI tasks. | `.claude/skills/impeccable/SKILL.md` |
<!-- GSD:skills-end -->

<!-- GSD:workflow-start source:GSD defaults -->
## GSD Workflow Enforcement

Before using Edit, Write, or other file-changing tools, start work through a GSD command so planning artifacts and execution context stay in sync.

Use these entry points:
- `/gsd-quick` for small fixes, doc updates, and ad-hoc tasks
- `/gsd-debug` for investigation and bug fixing
- `/gsd-execute-phase` for planned phase work

Do not make direct repo edits outside a GSD workflow unless the user explicitly asks to bypass it.
<!-- GSD:workflow-end -->

<!-- GSD:profile-start -->
## Developer Profile

> Profile not yet configured. Run `/gsd-profile-user` to generate your developer profile.
> This section is managed by `generate-claude-profile` -- do not edit manually.
<!-- GSD:profile-end -->
