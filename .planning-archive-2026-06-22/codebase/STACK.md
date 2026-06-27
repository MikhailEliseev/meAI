# Technology Stack

**Analysis Date:** 2026-06-19

## Languages

**Primary:**
- Python 3.11 - Hermes agent, AIM backend services, FastAPI wrapper, key rotation scripts
- JavaScript/TypeScript - Next.js frontend, WordPress theme, Node.js MCP servers

**Secondary:**
- YAML - Configuration (`config.yaml`, `docker-compose.yml`, `prometheus.yml`)
- Shell (bash) - Docker entrypoint scripts, deployment helpers
- Markdown - Knowledge vaults, agent skills, SOUL.md identity prompt

## Runtime

**Environment:**
- Docker Engine on Ubuntu (Polish server: `ssh aim`)
- Python 3.11-slim base image (`AIM/hermes/Dockerfile`, line 5)
- Server host Python: 3.12.3 (not used by containers)

**Container Orchestration:**
- Docker Compose v3 (`AIM/docker-compose.yml`) — 13 containers
- Container names: `aim-hermes`, `aim-app`, `aim-frontend`, `aim-nginx`, `aim-wordpress`, `aim-mysql`, `aim-postgres`, `aim-redis`, `aim-prometheus`, `aim-grafana`, `aim-alertmanager`, `aim-postgres-exporter`, `aim-node-exporter`

**Hermes Container:**
- Production image: `aim-hermes-nous:backup-2026-06-18` (Nous Research official Hermes agent)
- Custom image: `aim-hermes:latest` built from `AIM/hermes/Dockerfile`
- Both use `python:3.11-slim` base
- Process: `uvicorn app.main:app --host 0.0.0.0 --port 8000`
- Volume mount: `hermes_data:/opt/data` (persistent state.db, sessions, config, keys)
- Volume mount: `./hermes/skills:/opt/hermes/skills:ro` (agent skills)

**Package Manager:**
- pip (no lockfile — `requirements.txt` only, pinned versions)
- requirements.txt at `AIM/hermes/requirements.txt`
- npm for Node.js MCP servers (firecrawl-mcp, apify actors MCP, novamira WordPress MCP)

## Frameworks

**Core:**
- **Nous Research Hermes Agent v0.14.0** - AI agent framework, LLM orchestration, tool registry, session management
  - Package: `hermes-agent==0.14.0` (PyPI)
  - Extras: `hermes-agent[mcp]>=0.14.0`, `hermes-agent[messaging]>=0.14.0`, `hermes-agent[web]>=0.14.0`, `hermes-agent[anthropic]>=0.14.0`
- **FastAPI** - Custom HTTP wrapper (`app/main.py`) for Next.js chat proxy, SSE streaming, Telegram webhook, Prometheus metrics
- **Uvicorn** - ASGI server (launched in Dockerfile entrypoint)

**Backend (AIM app):**
- FastAPI - AIM API (`http://app:8000`) consumed by Hermes tools over internal Docker network
- SQLAlchemy (async) - PostgreSQL ORM
- `apify_client` - Apify Actor API client with key pool rotation

**Frontend:**
- Next.js 14+ - `aim-frontend` container on port 3099
- React - Full-page chat component with SSE streaming
- WordPress PHP 8.2 - `aim-wordpress` container, theme at `AIM/wordpress-core/wp-content/themes/aim-theme/`

**Testing:**
- `hermes-agent` built-in test framework (tests in `AIM/hermes/tests/`)
- `AIM/hermes/app/tools/test_deep_research_merge.py` — tool-specific tests
- `AIM/hermes/app/tools/test_service_categorizer.py` — tool-specific tests
- `AIM/hermes/app/tools/test_presale_pipeline.py` — pipeline tests

**Build/Dev:**
- Docker Compose for local development
- esbuild for chat theme JS bundling (`AIM/theme/chat/esbuild.config.mjs`)

## Key Dependencies

**Critical (from `AIM/hermes/requirements.txt`):**
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

**Supplemental (Dockerfile-level pip installs, not in requirements.txt):**
| Package | Purpose |
|---------|---------|
| `beautifulsoup4`, `lxml`, `parsel` | HTML parsing for web scraping |
| `pymysql` | MySQL/MariaDB connector (WordPress DB for report publishing) |
| `instagrapi`, `instaloader` | Instagram private API scraping |
| `playwright` + Chromium | Headless browser automation |

**AIM App Dependencies:**
- `apify_client` (async) - Apify Actor API
- `fast_bitrix24` - Bitrix24 REST API client
- `pybreaker` - Circuit breaker pattern for external services
- `aiosqlite` - Async SQLite for session DB
- `asyncpg` - Async PostgreSQL driver
- `redis` (aioredis) - Redis caching and queues

**Monitoring:**
- In-memory Python metrics (custom) exposed at `/metrics` in Prometheus text format
- `prometheus-client` for AIM app Prometheus metrics
- Prometheus + Grafana + Alertmanager + node-exporter + postgres-exporter — full monitoring stack

## Configuration

**Hermes Runtime Configuration:**
- Primary: `config.yaml` at `$HERMES_HOME/config.yaml` (`/opt/data/config.yaml` on server)
- Key sections:
  - `model.default: deepseek-v4-pro`, `model.provider: deepseek`, `model.base_url: https://api.deepseek.com/v1`
  - `fallback_providers: []` — no fallback model configured
  - `web.backend: brave`, `web.search_backend: brave`, `web.extract_backend: firecrawl`
  - `agent.max_turns: 60`, `agent.gateway_timeout: 1800`
  - `browser.engine: auto` (Playwright/Chromium in Docker)
  - `checkpoints.enabled: false`
  - `x_search.model: grok-4.20-reasoning` (X/Twitter search via Grok)
  - `mcp_servers.firecrawl`, `mcp_servers.apify`, `mcp_servers.novamira` — MCP server configs

**Environment Variables (`.env` at `/opt/data/.env` on server, 34 lines):**
| Variable | Purpose |
|----------|---------|
| `DEEPSEEK_API_KEY` | Primary LLM provider API key |
| `DEEPSEEK_BASE_URL` | DeepSeek API base URL |
| `APIFY_API_TOKEN` + `_01` through `_13` | 14 Apify rotating keys |
| `FIRECRAWL_API_KEY` + `_01` through `_14` | 15 Firecrawl rotating keys |
| `OPENROUTER_API_KEY` | Alternative model gateway |
| `TELEGRAM_HOME_CHANNEL` | Telegram channel for Hermes notifications |
| `TELEGRAM_HOME_CHANNEL_THREAD_ID` | Thread ID within that channel |

**Environment Variables (`.env.production` for Docker Compose):**
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

**Model Provider Chain:**
1. Primary: DeepSeek API (`https://api.deepseek.com/v1`) — model `deepseek-v4-pro`
2. Proxy layer: `deepseek_proxy.py` on server (port 11888) — non-streaming proxy that bypasses CloudFront stream drops; reads `DEEPSEEK_API_KEY` from `/opt/data/.env` or `/opt/hermes/.env`
3. Legacy: `OMNIROUTE_URL` and `OMNIROUTE_AUTH` env vars — legacy proxy URL, overridden at runtime
4. No fallback providers configured in config.yaml (`fallback_providers: []`)

## Platform Requirements

**Development:**
- Python 3.11+
- Docker Desktop (for local Docker Compose)
- Git
- SSH access to Polish server (`ssh aim`)

**Production:**
- Ubuntu Linux (Polish server, IP 78.17.128.169)
- Docker Engine with Docker Compose
- 13 running containers (Hermes, AIM app, Frontend, Nginx, WordPress, MySQL, PostgreSQL, Redis, Prometheus, Grafana, Alertmanager, postgres-exporter, node-exporter)
- Nginx reverse proxy handling SSL termination (Let's Encrypt)
- Internal Docker network `aim-network` (bridge mode)
- Persistent Docker volumes: `hermes_data`, `postgres_data`, `redis-data`, `prometheus-data`, `grafana-data`, `aim_wp_content`, `aim_wp_db`

## Model Configuration Details

**DeepSeek Proxy (`/opt/hermes-data/app/deepseek_proxy.py`) on server:**
- Purpose: Non-streaming proxy that wraps DeepSeek chat completions as SSE to work around streaming timeouts
- Listens on `127.0.0.1:11888` (PROXY_PORT env var)
- Reads API key directly from `.env` files (not environment variables)
- Returns SSE-wrapped completion in a single POST response
- Started separately from the main Hermes container (not in Dockerfile entrypoint)

**OmniRoute Direct Client (`AIM/hermes/app/omniroute_direct.py`):**
- Purpose: Direct OpenAI SDK wrapper bypassing AIAgent for fast non-streaming responses
- Used by Telegram gateway when AIAgent streaming times out
- Model: `HERMES_MODEL` env var (default `deepseek-chat`)
- URL: `OMNIROUTE_URL` env var (default `https://api.deepseek.com`)
- Key: `OMNIROUTE_AUTH` env var

**AIAgent Configuration (`AIM/hermes/app/agent_wrapper.py`, lines 397-422):**
- `base_url`: `OMNIROUTE_URL` (env var)
- `api_key`: `OMNIROUTE_AUTH` (env var)
- `provider`: `"custom"` (not built-in DeepSeek)
- `api_mode`: `"openai_chat"` (OpenAI-compatible API)
- `model`: `LLM_MODEL` env var (default `ds/deepseek-v4-pro`)
- `max_tokens`: 16000
- `max_iterations`: 25
- `quiet_mode`: True

## Key Rotation

**API Key Rotation v3 (`/opt/hermes-data/scripts/rotate_keys.py` on server):**
- Manages multi-key pools for Apify (14 keys) and Firecrawl (15 keys)
- Health-checks single keys: Perplexity, Brave, DeepSeek, Anthropic, Ahrefs, SEMrush, AssemblyAI
- Reads/writes `.env` file directly (preserves all non-rotated keys)
- State tracked in `/opt/data/keys/rotation_state.json`
- Rotation log: `/opt/data/keys/rotation.log`
- Key pool file: `/opt/data/keys/key_pool.json`
- Exit codes: 0=no rotation, 1=all exhausted, 2=rotated (restart needed)
- CLI modes: `--auto`, `--status`, `--check`, `--switch <service>`
- Invoked by Hermes tool `rotate_api_key` when Firecrawl/Apify return 402/credit-exhausted

**Firecrawl Key Bank (`/opt/hermes-data/app/tools/firecrawl_key_bank.py` on server):**
- Round-robin key rotation with exhaustion tracking
- Two exhaustion types: `insufficient_credits` (permanent) and `rate_limited` (30-min recovery)
- Loads from `FIRECRAWL_KEYS_FILE` (default: `/opt/data/firecrawl_keys.json`)
- Falls back to `FIRECRAWL_API_KEY` env var if no bank file
- Minimum 1.2s interval between calls (account-level rate limit)

**Apify Key Pool (`AIM/src/aim/services/apify_client.py`):**
- Async key pool with auto-rotation on quota errors
- Loads from `APIFY_KEYS_FILE` (default: `AIM/data/apify_keys.json`)
- Detects quota keywords: "quota", "exceeded", "insufficient", "balance", "limit"

---

*Stack analysis: 2026-06-19*
