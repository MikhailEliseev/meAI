# External Integrations

**Analysis Date:** 2026-06-19

## APIs & External Services

### LLM Providers

**DeepSeek API (Primary):**
- Service: https://api.deepseek.com/v1
- Model: `deepseek-v4-pro` (configurable via `LLM_MODEL` / `HERMES_MODEL`)
- Auth: `DEEPSEEK_API_KEY` in `.env` on server (`/opt/data/.env`)
- SDK: OpenAI-compatible (no dedicated SDK — uses `openai.OpenAI()` client or hermes-agent built-in)
- Config: `AIM/hermes/app/agent_wrapper.py` line 410, `config.yaml` line 2-4
- Proxy: `deepseek_proxy.py` on server (port 11888) wraps non-streaming completions as SSE to bypass CloudFront stream drops
- Fallback: `OMNIROUTE_URL` env var — legacy proxy URL, overridden at runtime

**Perplexity API:**
- Service: https://api.perplexity.ai
- Purpose: Secondary AI model for certain query types
- Auth: `PERPLEXITY_API_KEY` in server `.env`, managed by `rotate_keys.py` health check
- Config: `rotate_keys.py` lines 62-63 (test URL + method)

**Anthropic API:**
- Service: https://api.anthropic.com/v1
- Purpose: Secondary AI model (Claude)
- Auth: `ANTHROPIC_API_KEY` in server `.env`, managed by `rotate_keys.py` health check
- Config: `rotate_keys.py` lines 65-66 (test URL + body)
- SDK: `hermes-agent[anthropic]>=0.14.0` extra installed in Dockerfile

**OpenRouter:**
- Service: OpenRouter API gateway
- Auth: `OPENROUTER_API_KEY` in server `.env`
- Purpose: Alternative model access gateway

### Web Scraping & Search

**Apify:**
- Service: https://api.apify.com
- Purpose: Google Maps scraping for competitor discovery (`find_competitors`), social media content finding
- SDK: `apify_client` (async, via `AIM/src/aim/services/apify_client.py`)
- Auth: 14 rotating API tokens (`APIFY_API_TOKEN` + `_01` through `_13`) in server `.env`
- Key pool file: `/opt/data/keys/key_pool.json`
- Script: `rotate_keys.py --switch apify` for rotation, triggered by `rotate_api_key` Hermes tool
- MCP server: `@apify/actors-mcp-server` configured in `config.yaml` mcp_servers section
- Timeout: 600s (find_competitors full pipeline including Apify + Playwright + nalog enrichment)
- File: `AIM/hermes/app/tools/find_competitors.py`
- File: `AIM/src/aim/services/apify_google_maps.py`
- File: `AIM/src/aim/services/apify_client.py`
- File: `AIM/src/aim/services/apify_key_pool.py`

**Firecrawl:**
- Service: https://api.firecrawl.dev
- Purpose: Web scraping, search, crawl, and site maps for Hermes debug tools
- SDK: `firecrawl-py>=4.28.0`
- Auth: 15 rotating API keys (`FIRECRAWL_API_KEY` + `_01` through `_14`) in server `.env`
- Key bank: `AIM/hermes/app/tools/firecrawl_key_bank.py` (round-robin with exhaustion tracking)
- MCP server: `firecrawl-mcp` (npx) configured in `config.yaml` mcp_servers section
- Credit exhaustion: `insufficient_credits` = permanent, `rate_limited` = 30-min recovery
- File: `AIM/hermes/app/tools/firecrawl_web.py`

**Brave Search:**
- Service: https://api.search.brave.com
- Purpose: Web search backend for Hermes agent (configured in `config.yaml`: `web.backend: brave`, `web.search_backend: brave`)
- Auth: `BRAVE_API_KEY` (in server `.env` and AIM `.env.production`)
- Managed by: `rotate_keys.py` health check (single key)

### Government & Business Data (Russia)

**nalog.gov.ru (ФНС ГИР БО):**
- Purpose: Official Russian tax-filed financial data (P&L, форма 0710002) — revenue, net profit, gross profit by year
- Auth: None — public government open data API
- Endpoint: `GET http://app:8000/api/companies/financials?inn=...` (AIM app proxies the call)
- Tool: `find_company_financials` (`AIM/hermes/app/tools/find_company_financials.py`)
- Timeout: 10s (fast JSON endpoint)

**DaData (dadata.ru):**
- Purpose: Russian company enrichment — legal name, INN, address, OKVED codes from official registries
- Used by: Competitor matcher pipeline (enriches Google Maps results with official company data)
- Integrated via: AIM app backend (not directly from Hermes tools)
- Referenced in: `find_competitors.py` docstring ("enriches with DaData + rusprofile financials")

**rusprofile.ru:**
- Purpose: Russian company financial data — revenue, profit, founding documents
- Used by: Competitor financial analysis pipeline (Playwright-based INN extraction)
- File: `AIM/src/aim/services/competitor_matcher.py`

### Marketing & SEO Analytics

**SEMrush:**
- Service: https://api.semrush.com
- Purpose: SEO analytics — domain rank, keyword positions, competitor comparison
- Auth: `SEMRUSH_API_KEY` in `.env` (disabled in production — `ENABLE_SEMRUSH=true` in dev, empty in `.env.production`)
- Managed by: `rotate_keys.py` health check
- Rate limiting: `SEMRUSH_RATE_LIMIT_CAPACITY=10`, `SEMRUSH_RATE_LIMIT_REFILL=1.0`
- File: `AIM/.env.example` lines 50, 147-148, 245, 262

**Ahrefs:**
- Service: https://api.ahrefs.com
- Purpose: SEO backlink profile analysis
- Auth: `AHREFS_API_KEY` in `.env` (disabled — `ENABLE_AHREFS=false`)
- Managed by: `rotate_keys.py` health check
- Rate limiting: `AHREFS_RATE_LIMIT_CAPACITY=10`, `AHREFS_RATE_LIMIT_REFILL=1.0`
- File: `AIM/.env.example` lines 62, 151-152, 248, 265

### Communication & Social

**Telegram Bot API:**
- Service: https://api.telegram.org
- Purpose: Incoming client messages via getUpdates polling + webhook fallback
- Auth: `TELEGRAM_BOT_TOKEN` (in `.env.production`)
- Admin chat: `TELEGRAM_ADMIN_CHAT_ID=322367335` (Mikhail — gets ADMIN mode, all tools)
- Webhook: `TELEGRAM_WEBHOOK_URL=https://iamaim.ru/telegram/webhook` (Nginx proxies to Hermes)
- Proxy: Traffic routed through `http://193.111.152.14:7451` (old OmniRoute server) because NL hosting blocks Telegram port 443
- Proxy auth: `TELEGRAM_PROXY_AUTH` env var
- File: `AIM/hermes/app/telegram_gateway.py`
- Hybrid architecture: polling primary, webhook fallback, Telethon user-client for outgoing

**Telethon (Telegram User Client):**
- Purpose: Sending outgoing messages as Mikhail, Telegram channel search, monitoring
- Auth: `TELEGRAM_API_ID`, `TELEGRAM_API_HASH`, `TELEGRAM_SESSION_STRING` (in `.env`)
- SDK: `telethon>=1.39.0,<2.0.0`
- Session string stored in `.env` (persistent auth across restarts)

**AssemblyAI:**
- Service: https://api.assemblyai.com
- Purpose: Voice message transcription — Telegram voice messages (OGG/Opus, 16000 Hz mono)
- SDK: `assemblyai>=0.38.0,<1.0.0`
- Auth: `ASSEMBLYAI_API_KEY` env var
- Flow: Download voice via Telegram API through proxy → upload to AssemblyAI → request transcription (Russian language) → poll for 60s
- File: `AIM/hermes/app/voice_transcriber.py`
- Managed by: `rotate_keys.py` health check

### Social Media Scraping

**Instagram:**
- Purpose: Instagram content analysis for competitor research
- SDK: `instagrapi` (private API), `instaloader` (public scraper)
- No browser needed — uses private API
- Tool: `run_instagram_content` (`/opt/hermes-data/app/tools/run_instagram_content.py` on server, 14.2KB)
- Installed at Dockerfile build: `pip install instagrapi instaloader`

**YouTube, VK (VKontakte):**
- Purpose: Social media competitor monitoring
- Scraped via: `web_scraper` and `external_api` Hermes tools (generic HTTP+HTML tools)

### CRM

**Bitrix24:**
- Service: Bitrix24 REST API
- Purpose: Lead management, contact sync, deal pipeline for client clinics
- SDK: `fast_bitrix24` (async)
- Resilience: Circuit breaker (`pybreaker`), exponential backoff retry (`tenacity`)
- Auth modes: Webhook (`https://{domain}/rest/{user_id}/{webhook_code}/`) and OAuth 2.0
- File: `AIM/src/aim/integrations/bitrix24/client.py`
- File: `AIM/src/aim/integrations/bitrix24/schemas.py`
- Used by: `AIM/src/aim/subagents/sales/crm_agent.py`

### Content Management

**WordPress REST API (novamira MCP):**
- Purpose: Publishing HTML scout reports, managing AIM website content
- MCP server: `@automattic/mcp-wordpress-remote@latest` (configured in `config.yaml` mcp_servers section)
- Endpoint: `https://iamaim.ru/wp-json/mcp/novamira`
- Auth: WP credentials in config.yaml (`WP_API_USERNAME`, `WP_API_PASSWORD`)
- Container: `aim-wordpress` (wordpress:php8.2-fpm-alpine)
- Report archive: `https://iamaim.ru/wp-json/aim/v1/session`
- File: `AIM/hermes/app/tools/publish_scout_report.py`

## Data Storage

**PostgreSQL 16:**
- Container: `aim-postgres` (postgres:16-alpine)
- Purpose: AIM application primary database — leads, projects, clients, prescan results
- Connection: `DATABASE_URL` with `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_DB`
- Client: SQLAlchemy async (`asyncpg` driver)
- Locale: `ru_RU.UTF-8`
- Exposed only locally: `127.0.0.1:5432`
- Config: `AIM/config/postgresql.conf`
- Health check: `pg_isready`

**MariaDB 11 (MySQL):**
- Container: `aim-mysql` (mariadb:11)
- Purpose: WordPress database — site content, theme settings, users
- Connection: `WP_DB_HOST=aim-mysql`, `WP_DB_USER=wp_user`, `WP_DB_PASSWORD`, `WP_DB_NAME=wordpress`
- Client: `pymysql` (installed in Hermes Dockerfile for HTML report publishing)
- Volume: `aim_wp_db` (external, pre-existing)

**SQLite (Hermes State):**
- File: `/opt/data/state.db` (21 MB on server, with WAL and SHM)
- Purpose: Hermes agent session state — conversation history, tool call records, agent memory
- Client: `hermes_state.SessionDB` (from hermes-agent framework)
- Survives container restarts (volume-mounted)
- Additional DB: `/opt/data/kanban.db` (114KB) — task/tool tracking
- Per-session locks: `asyncio.Lock` per session_id for concurrency safety

**Redis 7:**
- Container: `aim-redis` (redis:7-alpine)
- Purpose: Caching, task queues, SSE progress event pub/sub
- Connection: `REDIS_URL=redis://redis:6379/0`
- AIM app depends on Redis being healthy before starting

### File Storage

**Local filesystem (Docker volumes):**
- `hermes_data:/opt/data` — Hermes persistent data (state.db, config.yaml, .env, sessions, memories, keys, logs, reports)
- `./hermes/skills:/opt/hermes/skills:ro` — Agent skills mounted read-only from repo
- `aim_wp_content` — WordPress content (themes, plugins, uploads)
- `./logs:/app/logs` — AIM app logs
- `./AIM/data:/app/AIM/data` — AIM data files (prescan results, competitor data)
- Audio cache: `/opt/data/audio_cache/` — cached voice message files
- Image cache: `/opt/data/image_cache/` — cached scraped images

### Caching

- In-memory Python caches:
  - Agent instances: 24-hour TTL cache (`_agent_cache` in `agent_wrapper.py`)
  - SOUL.md: loaded once, cached in `_soul_md_cache` variable
  - 3PHASE_PIPELINE.md: loaded once, cached in `_pipeline_md_cache` variable
  - SEO audit results: 10-minute TTL cache in `run_seo_audit.py` (`_seo_cache`)
- Redis: Used by AIM app for task queues and session data
- Provider model caches on server: `models_dev_cache.json` (2.3MB), `provider_models_cache.json`, `ollama_cloud_models_cache.json`

## Authentication & Identity

**Hermes API Authentication:**
- Auth provider: Custom API key verification
- Endpoint: `POST /api/chat` and `POST /api/chat/stream` protected by `Depends(verify_api_key)`
- Key: `HERMES_API_KEY=hmr_...` in `.env.production`
- File: `AIM/hermes/app/auth.py`

**Telegram Authentication:**
- Bot Token: `TELEGRAM_BOT_TOKEN` for Bot API calls
- Telethon session: `TELEGRAM_SESSION_STRING` for user-client operations
- Webhook verification: Token in URL path `/telegram/webhook/{token}`

**WordPress Authentication:**
- API credentials: `WP_API_USERNAME: admin`, `WP_API_PASSWORD` in config.yaml novamira MCP section

## Monitoring & Observability

**Prometheus:**
- Container: `aim-prometheus` (prom/prometheus:latest)
- Scrapes: Hermes `/metrics` endpoint, AIM app, postgres-exporter, node-exporter
- Config: `AIM/prometheus.yml`, `AIM/prometheus-alerts.yml`, `AIM/deploy/monitoring/rules.yml`
- Retention: 30 days

**Grafana:**
- Container: `aim-grafana` (grafana/grafana:latest)
- Port: 3000
- Dashboards provisioned from `AIM/grafana/dashboards/`

**Hermes Custom Metrics (exposed at `/metrics`):**
- `aim_hermes_requests_total` — total chat requests
- `aim_hermes_errors_total` — total errors
- `aim_chat_sessions_active` — active SSE sessions
- `aim_chat_messages_total` — total messages
- `aim_chat_leads_total` — total leads collected
- `aim_chat_token_cost_total` — token cost in USD
- `aim_hermes_latency_avg` — average request latency

**Error Tracking:**
- Structured logging: Python `logging` module to stdout (JSON-file driver in Docker)
- Log rotation: max 10MB per file, 3 files retained (per container)
- Server logs: `/opt/data/logs/` directory
- Tool-level: errors logged but never propagated to break conversation (graceful degradation)

**Health Checks:**
- `GET /health` on Hermes (container health check, Docker: 30s interval)
- `GET /health` on AIM app
- PostgreSQL: `pg_isready`
- Redis: `redis-cli ping`
- MariaDB: `healthcheck.sh --connect --innodb_initialized`

## CI/CD & Deployment

**Hosting:**
- Polish server (IP: 78.17.128.169), accessible via `ssh aim`
- Single host running all Docker containers
- Nginx reverse proxy: SSL termination via Let's Encrypt, routing to internal containers

**CI Pipeline:**
- No formal CI/CD pipeline detected
- Manual `docker-compose build` and `docker-compose up -d`
- Server SSH key configured for GitHub push (deploy key)
- Backup: `hermes-backup-20260618/` directory in project root (local), `/opt/hermes-data/backups/` on server

**Deployment:**
- `docker-compose.yml` at project root handles all services
- Hermes: custom Dockerfile at `AIM/hermes/Dockerfile`
- AIM App: Dockerfile at `AIM/Dockerfile`
- Frontend: Dockerfile at `AIM/frontend/Dockerfile`
- External volumes: `aim_wp_content`, `aim_wp_db` (pre-existing, managed outside Compose)

## Environment Configuration

**Required env vars (critical — must be present in `.env.production`):**
- `HERMES_API_KEY` — API key for Next.js → Hermes auth
- `HERMES_URL` — internal Docker URL to Hermes
- `HERMES_MODEL` — model name (e.g., `deepseek-v4-pro`)
- `TELEGRAM_BOT_TOKEN` — Telegram bot token
- `TELEGRAM_ADMIN_CHAT_ID` — Mikhail's chat ID for ADMIN mode
- `BRAVE_API_KEY` — Brave Search API key
- `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_DB` — PostgreSQL credentials
- `WP_DB_PASSWORD` — WordPress/MariaDB password
- `DEEPSEEK_API_KEY` — Primary LLM provider

**Secrets location:**
- Server: `/opt/data/.env` (34 lines) — contains all API keys for LLM, scraping, search services
- Server: `/opt/data/keys/` — key pool files and rotation state
- Local: `AIM/.env` (development, includes real Telegram token/session)
- Local: `AIM/.env.production` (used by Docker Compose, some keys empty/masked)
- Managed by: `rotate_keys.py` script which reads/writes `.env` directly

**Notable:**
- Apify: 14 separate keys (`APIFY_API_TOKEN` + indexed suffixes) in `.env`
- Firecrawl: 15 separate keys (`FIRECRAWL_API_KEY` + indexed suffixes) in `.env`
- Rotation preserves all non-rotated keys when writing back (bug fixed in v3)

## Webhooks & Callbacks

**Incoming:**
- `POST /telegram/webhook/{token}` — Telegram Bot API webhook (Nginx proxies to Hermes)
- `POST /api/chat` — Next.js frontend chat (requires Bearer HERMES_API_KEY)
- `POST /api/chat/stream` — SSE streaming chat (requires Bearer HERMES_API_KEY)
- `POST /api/knowledge/ingest` — Knowledge vault ingestion from CI Orchestrator

**Outgoing (from Hermes to external):**
- All AIM API calls (`POST http://app:8000/api/*`) — tool execution
- Telegram Bot API calls (`POST https://api.telegram.org/bot{token}/*`) — send messages
- DeepSeek API calls (`POST https://api.deepseek.com/v1/chat/completions`) — LLM inference
- DeepSeek proxy calls (`POST http://127.0.0.1:11888`) — proxied LLM calls (server only)
- AssemblyAI upload/transcription/poll — voice transcription
- Firecrawl API — web scraping
- Apify Actor API — Google Maps scraping

## MCP Servers

**3 MCP servers configured in `config.yaml` on server:**

1. **Firecrawl MCP** — `npx -y firecrawl-mcp`
   - Env: `FIRECRAWL_API_KEY` (hardcoded key in config)
   - Timeout: 120s connect, 120s execution

2. **Apify MCP** — `npx -y @apify/actors-mcp-server`
   - Tools: actors, docs, experimental, run, storage
   - Env: `APIFY_TOKEN` (hardcoded key in config)
   - Timeout: 120s connect, 120s execution

3. **Novamira (WordPress) MCP** — `npx -y @automattic/mcp-wordpress-remote@latest`
   - Endpoint: `https://iamaim.ru/wp-json/mcp/novamira`
   - Auth: WP admin credentials in config
   - Timeout: 120s connect, 120s execution

---

*Integration audit: 2026-06-19*
