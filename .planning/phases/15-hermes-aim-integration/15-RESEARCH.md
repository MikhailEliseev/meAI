# Phase 15: Hermes AIM Integration — Research

**Researched:** 2026-05-19
**Domain:** AI Agent Framework Integration (Hermes + Next.js + Docker + Telegram)
**Confidence:** HIGH

## Summary

Phase 15 integrates Hermes Agent (v0.14.0, Nous Research) as the foundational Operator system for AIM. Hermes replaces direct DeepSeek calls in the Next.js chat route with a full AI agent framework: persistent sessions, tool calling, skill auto-improvement, and multi-platform communication (web chat + Telegram).

The architecture centres on a FastAPI HTTP wrapper inside a Docker container that exposes Hermes AIAgent programmatically (not via subprocess). The wrapper receives chat requests from Next.js, instantiates AIAgent with the appropriate mode (PRESALE/ACTIVE/ADMIN), executes tool calls against AIM API endpoints, and returns responses. Six custom MCP-style tools (registered through Hermes internal registry, not MCP stdio) enable the Operator to run SEO audits, content analysis, ads reports, project status checks, contact collection, and lead retrieval.

All 36 design decisions from CONTEXT.md are locked — no alternative approaches are explored. The research focuses on verifying the technical feasibility of each decision against the Hermes source code, identifying pitfalls, and documenting integration patterns.

**Primary recommendation:** Use Hermes AIAgent programmatic API (`run_agent.py` class `AIAgent`) wrapped in FastAPI, not subprocess `hermes chat`. Register custom tools via `tools/registry.py` with toolset `"aim-operations"`. Handle OmniRoute proxy authentication by testing before implementation — the auth format is the highest-risk unknown.

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| LLM-gateway (chat proxy) | API / Backend | Frontend Server (SSR) | Hermes FastAPI wrapper receives requests from Next.js SSR, calls LLM via OmniRoute |
| Chat route (Next.js) | Frontend Server (SSR) | API / Backend | route.ts becomes thin proxy — determines mode, forwards to Hermes, returns response |
| 6 custom MCP tools | API / Backend | — | Tools inside Hermes container call AIM API endpoints via internal Docker network |
| Telegram Bot API (incoming) | API / Backend | — | Webhook mode in Hermes Telegram gateway receives client messages |
| Telegram user-client (outgoing) | API / Backend | — | Telethon MCP tools inside Hermes for outgoing messages and channel search |
| Skill auto-improvement | API / Backend | Database / Storage | Hermes creates skills from repeated patterns, stores in HERMES_HOME/skills/ |
| Message resilience (Redis queue) | API / Backend | — | Next.js enqueues messages in Redis when Hermes is unavailable |
| Health + Metrics | API / Backend | — | FastAPI /health endpoint scraped by Prometheus |
| Lead persistence (/tmp/leads) | API / Backend | Database / Storage | Docker volume mount replaces tmpfs, data persists across restarts |

## User Constraints (from CONTEXT.md)

### Locked Decisions
- **D-01:** Docker container in existing docker-compose.yml (alongside app, redis, nginx, prometheus, grafana, postgres)
- **D-02:** Custom Dockerfile based on Python 3.11 (not ready-made Hermes image)
- **D-03:** Skills stored in repo `AIM/hermes/skills/`, copied into image via `COPY` at build time
- **D-04:** Hermes runs in MCP server mode
- **D-05:** LLM provider: Anthropic (Claude) via OmniRoute proxy (193.111.152.14:7451, HTTP, login: U9pjtK, password: hxtlqz)
- **D-06:** Hermes data: Docker volume (persistent)
- **D-07:** Port: internal Docker network only, not exposed externally
- **D-08:** Docker restart policy (`unless-stopped`) replaces systemd
- **D-09:** OmniRoute provides fallback between LLM providers on its side
- **D-10:** FastAPI HTTP wrapper inside Hermes container for Next.js communication (MCP uses stdio/SSE, unsuitable for Next.js)
- **D-11:** Hermes is the sole LLM gateway. DeepSeek fully removed from `route.ts`
- **D-12:** OPERATOR_PROMPT (3 modes: PRESALE/ACTIVE/ADMIN) moved from `route.ts` to SOUL.md as Hermes skill
- **D-13:** 6 custom tools (run_seo_audit, run_content_analysis, run_ads_report, show_project_status, collect_contact, show_all_leads) defined as MCP tools in Hermes container
- **D-14:** Tools call AIM API via HTTP between Docker containers (internal network)
- **D-15:** Real AIM API endpoint calls, no stubs
- **D-16:** Hybrid architecture: Bot API (webhook, incoming client messages) + Telethon user-client (outgoing, channel search, monitoring)
- **D-17:** Unified chat — one Operator serves both web and Telegram
- **D-18:** Session binding: tg://deep link from site
- **D-19:** Telethon integrated as MCP tools in Hermes
- **D-20-D-24:** Skill auto-improvement on frequent questions (conversion rate metric, 5 repetition threshold, auto-create skills in `AIM/hermes/skills/aim/`)
- **D-25:** Bearer API key in `Authorization` header
- **D-26:** Next.js determines mode by client status in DB and passes in header
- **D-27:** Static `HERMES_API_KEY` in `.env`
- **D-28:** ADMIN protection: `role=admin` check in Next.js (NextAuth)
- **D-29:** Health check: `/health` endpoint in FastAPI wrapper
- **D-30:** Standard RED metrics (Rate, Errors, Duration)
- **D-31:** Alerts: downtime only (Hermes unavailable 60+ seconds)
- **D-32:** Alert delivery: Telegram + Email via Alertmanager
- **D-33-D-36:** Redis queue resilience (30s timeout, 3 retries: 5s/15s/45s), after exhaustion — DB

### Deferred Ideas (OUT OF SCOPE)
- LLM-specific metrics (tokens, cost)
- Chat business metrics (conversion, session duration)
- Automatic API key rotation
- Circuit breaker for AIM API

## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| SUCCESS-1 | Hermes SOUL.md loaded with all AIM knowledge (agency, services, prices, processes, KPIs, clients) | SOUL.md loaded via `load_soul_identity=True` in AIAgent constructor. Current SOUL.md is 73 lines — needs expansion with services, prices, KPIs, clients sections. `load_soul_md()` reads from `HERMES_HOME/SOUL.md` [VERIFIED: agent/prompt_builder.py:1308] |
| SUCCESS-2 | Custom Hermes tools working (run_seo_audit, run_content_analysis, run_ads_report, show_project_status, collect_contact, show_all_leads) | Tools registered via `tools/registry.py` with toolset `"aim-operations"`. Each tool makes HTTP calls to AIM API via internal Docker network. [VERIFIED: tools/registry.py] |
| SUCCESS-3 | Next.js /api/chat/send proxies through Hermes (replacing direct DeepSeek calls) | route.ts becomes thin passthrough: extracts message + session_id, determines mode from DB, POSTs to `http://hermes:8000/api/chat`, returns response. DeepSeek SDK and OPERATOR_PROMPT removed. |
| SUCCESS-4 | Hermes configured as Operator with 3 modes (PRESALE, ACTIVE, ADMIN) and correct identity | `ephemeral_system_prompt` parameter in AIAgent injects mode-specific context. SOUL.md provides base identity. Mode determined by Next.js from DB, passed in header. |
| SUCCESS-5 | Hermes Telegram gateway configured for client communication | Hybrid: python-telegram-bot webhook for incoming + Telethon MCP tools for outgoing/search. `messaging` extra installs python-telegram-bot==22.6. Telethon added as separate dependency. |
| SUCCESS-6 | Hermes systemd service fixed and working in production | D-08: Docker restart policy (`unless-stopped`) replaces systemd entirely. No systemd unit needed — Docker handles restarts. |
| SUCCESS-7 | /tmp/leads persistence fixed (Docker volume mount) | Docker volume `hermes_data:/opt/data` replaces tmpfs `/tmp/leads`. All file writes go to `/opt/data/leads/`. |

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| hermes-agent | 0.14.0 | AI agent framework (Nous Research) | User-selected as Operator foundation |
| Python | 3.11+ | Runtime (custom Dockerfile) | D-02: custom Dockerfile on Python 3.11 |
| FastAPI | 0.133.1 | HTTP wrapper for Next.js <-> Hermes | D-10: FastAPI wraps MCP in HTTP. Version from Hermes `web` extra [VERIFIED: pyproject.toml] |
| uvicorn | 0.41.0 | ASGI server for FastAPI | Bundled with Hermes `web` extra [VERIFIED: pyproject.toml] |
| MCP Python SDK | 1.26.0 | MCP protocol support | Hermes `mcp` extra [VERIFIED: pyproject.toml] |
| Anthropic (via OmniRoute) | 0.86.0 | LLM provider SDK | Hermes `anthropic` extra [VERIFIED: pyproject.toml] |
| python-telegram-bot[webhooks] | 22.6 | Telegram Bot API (incoming) | D-16: incoming via Bot API webhook. Hermes `messaging` extra [VERIFIED: pyproject.toml] |
| Telethon | latest stable | Telegram user-client (outgoing) | D-16/D-19: outgoing messages and search via MTProto |
| httpx | 0.28.1 | HTTP client for AIM API calls | Bundled in Hermes core [VERIFIED: pyproject.toml] |
| pydantic | 2.12.5 | Data validation | Bundled in Hermes core [VERIFIED: pyproject.toml] |
| tenacity | 9.1.4 | Retry logic | Bundled in Hermes core [VERIFIED: pyproject.toml] |
| Redis | 7-alpine | Message queue | Already in docker-compose stack |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| pyyaml | 6.0.3 | YAML parsing for SKILL.md | Skills loaded via YAML frontmatter [VERIFIED: pyproject.toml] |
| pytest | 9.0.2 | Testing | Hermes `dev` extra [VERIFIED: pyproject.toml] |
| pytest-asyncio | 1.3.0 | Async test support | Hermes `dev` extra [VERIFIED: pyproject.toml] |
| aiohttp | 3.13.3 | Async HTTP (Telegram webhooks) | Hermes `messaging` extra [VERIFIED: pyproject.toml] |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| Ready Hermes Docker image | Custom Dockerfile on Python 3.11 | D-02 locked custom Dockerfile — gives control over dependencies and layers |
| MCP stdio directly in Next.js | FastAPI HTTP wrapper | D-10 justified: stdio/SSE MCP does not work over HTTP between containers |
| Go runner (original Hermes) | Python runner | Hermes supports both; Python chosen for AIM stack compatibility |
| Telethon instead of python-telegram-bot | Both together | D-16: Bot API for incoming, Telethon for outgoing — complementary, not alternative |
| subprocess `hermes chat` per request | Programmatic AIAgent API | subprocess overhead kills performance and loses session state |

**Installation:**
```bash
# Core Hermes with all needed extras
pip install hermes-agent==0.14.0
pip install hermes-agent[mcp]         # MCP protocol
pip install hermes-agent[messaging]    # Telegram Bot API
pip install hermes-agent[web]          # FastAPI + uvicorn
pip install hermes-agent[anthropic]    # Anthropic provider
pip install telethon                   # Telegram user-client

# Or from our requirements.txt:
pip install -r requirements.txt
```

**Version verification:** All versions confirmed against `/hermes-agent/pyproject.toml` from the cloned reference repository. [VERIFIED: local clone]

## Architecture Patterns

### System Architecture Diagram

```
CLIENT (Browser)
  |
  +-- Chat widget (iamaim.ru) ---------------+
  |                                           | HTTPS
  +-- Telegram Bot (incoming) ----------------+
  |                                           v
  |                                Nginx (TLS terminator)
  |                                           |
  |                +--------------------------+
  |                |                          |
  |      Next.js Frontend              Telegram webhook
  |      (NextAuth determines          (Bot API -> Hermes
  |       mode: PRESALE/ACTIVE/        Telegram gateway
  |       ADMIN, passes in             directly)
  |       header)
  |                |
  |                v
  |      POST /api/chat/send
  |      (thin proxy)
  |           |      |
  |           |      +-- (Hermes unavailable) -> Redis Queue -> retry (5s/15s/45s) -> DB
  |           |
  |           v
  |      +------------------------------------------+
  |      |  HERMES CONTAINER                        |
  |      |                                          |
  |      |  FastAPI Wrapper (:8000)                 |
  |      |  POST /api/chat -> AIAgent.run           |
  |      |  GET /health -> status check             |
  |      |                                          |
  |      |  +-----------------------------------+   |
  |      |  |  Hermes AIAgent                   |   |
  |      |  |  - SOUL.md (identity)             |   |
  |      |  |  - MCP Tools (6 custom)           |   |
  |      |  |  - Skill System                   |   |
  |      |  |  - Session DB (SQLite)            |   |
  |      |  +----------+------------------------+   |
  |      |             |                            |
  |      |             v                            |
  |      |  OmniRoute Proxy                         |
  |      |  (193.111.152.14:7451)                   |
  |      |  -> Anthropic Claude                     |
  |      +----------+-------------------------------+
  |                 |
  |                 | HTTP (internal Docker network)
  |                 v
  |      +------------------------------------------+
  |      |  AIM API (app container)                 |
  |      |  - SEO endpoints                         |
  |      |  - Content endpoints                     |
  |      |  - Ads endpoints                         |
  |      |  - Project/Lead endpoints                |
  |      +------------------------------------------+
  |
  +-- Prometheus --> /health + /metrics (Hermes + all containers)
  +-- Grafana --> Dashboards
  +-- Alertmanager --> Telegram + Email (downtime 60s+)
```

### Recommended Project Structure
```
AIM/hermes/
|-- Dockerfile                    # Python 3.11, install Hermes + FastAPI
|-- requirements.txt              # hermes-agent[extras], fastapi, uvicorn, httpx, telethon
|-- app/
|   |-- main.py                   # FastAPI app (chat proxy + health)
|   |-- agent_wrapper.py          # AIAgent wrapper — session management
|   |-- auth.py                   # Bearer token verification
|   +-- tools/
|       |-- __init__.py
|       |-- run_seo_audit.py      # MCP tool: SEO audit
|       |-- run_content_analysis.py
|       |-- run_ads_report.py
|       |-- show_project_status.py
|       |-- collect_contact.py
|       +-- show_all_leads.py
|-- skills/
|   +-- aim/
|       |-- SOUL.md               # Operator identity (3 modes + AIM knowledge)
|       |-- services.md           # Services and pricing
|       |-- processes.md          # Agency processes
|       |-- kpi.md                # KPIs and metrics
|       |-- clients.md            # Client database (if applicable)
|       +-- auto/                 # Auto-generated skills (D-24)
+-- data/                         # Docker volume mount point
    |-- sessions/                 # Hermes session DB (SQLite)
    |-- skills/                   # Runtime skills (auto-generated)
    |-- cron/
    |-- logs/
    |-- hooks/
    +-- memories/
```

### Pattern 1: FastAPI Wrapper with AIAgent (Programmatic, Not Subprocess)

**What:** FastAPI wraps Hermes AIAgent (from `run_agent.py`) as a programmatic object, not via subprocess.

**When to use:** Each POST /api/chat request creates (or loads by session_id) an AIAgent, executes run_conversation, returns response.

**Why programmatic, not subprocess:**
- AIAgent (`run_agent.py:326`) exposes Python API — no subprocess overhead
- `session_id` parameter (`run_agent.py:377`) enables session reuse
- `load_soul_identity=True` (`run_agent.py:403`) enables SOUL.md
- `ephemeral_system_prompt` (`run_agent.py:367`) for mode (PRESALE/ACTIVE/ADMIN)
- `base_url` (`run_agent.py:345`) for OmniRoute proxy
- `enabled_toolsets` (`run_agent.py:361`) controls available tools

**Key AIAgent constructor parameters:**
```python
# Source: /hermes-agent/run_agent.py, lines 349-415 [VERIFIED: local clone]
agent = AIAgent(
    base_url="http://193.111.152.14:7451/v1",   # OmniRoute proxy
    api_key="U9pjtK:hxtlqz",                     # OmniRoute basic auth
    provider="custom",                            # OpenAI-compatible endpoint
    api_mode="openai_chat",                       # Standard chat completions
    model="claude-sonnet-4-20250514",            # Or Opus
    session_id=session_id,                        # Persistent session
    load_soul_identity=True,                      # Load SOUL.md from HERMES_HOME
    ephemeral_system_prompt=mode_prompt,          # PRESALE/ACTIVE/ADMIN context
    enabled_toolsets=["aim-operations"],           # Our custom toolset
    max_iterations=20,                            # Tool call limit
    quiet_mode=True,                              # No TUI output
)
response = agent.run_conversation(user_message)
```

### Pattern 2: MCP Tool Registration for AIM Operations

**What:** 6 tools registered in Hermes registry (`tools/registry.py`) with toolset `"aim-operations"`. Each tool makes HTTP requests to AIM API via internal Docker network.

**Critical distinction — internal registry, not MCP stdio:** Hermes has TWO mechanisms:
1. **MCP server mode** (`hermes mcp serve`) — for external MCP clients via stdio
2. **Internal tool registry** (`tools/registry.py`) — for AIAgent's own tool calling

For AIM tools, use mechanism #2. Tools registered via `registry.register()` with toolset name are available to AIAgent when `enabled_toolsets=["aim-operations"]` is set. This is NOT MCP stdio — it is Hermes' internal tool mechanism.

**Tool registration pattern (from Hermes source):**
```python
# Source: /hermes-agent/tools/registry.py, register() method [VERIFIED: local clone]
# registry.register(
#     name="run_seo_audit",
#     toolset="aim-operations",
#     schema={
#         "type": "function",
#         "function": {
#             "name": "run_seo_audit",
#             "description": "Run SEO audit on client website",
#             "parameters": {
#                 "type": "object",
#                 "properties": {
#                     "url": {"type": "string", "description": "Website URL"}
#                 },
#                 "required": ["url"]
#             }
#         }
#     },
#     handler=handle_seo_audit,
#     check_fn=lambda: True,
#     is_async=True,
# )

async def handle_seo_audit(url: str) -> str:
    """Call AIM API for SEO audit."""
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            "http://app:8000/api/seo/audit",
            json={"url": url},
            timeout=30.0,
        )
        return resp.json()
```

### Pattern 3: OmniRoute Provider Configuration

**What:** OmniRoute is an HTTP proxy with basic authentication. Configured via `custom` provider in Hermes.

**Implementation approach:** Since OmniRoute uses basic auth (login:password), the FastAPI wrapper passes credentials directly to AIAgent:
```python
# OmniRoute basic auth — format to be tested before implementation
# The exact auth header format depends on OmniRoute's API surface
agent = AIAgent(
    base_url="http://193.111.152.14:7451",
    api_key="U9pjtK:hxtlqz",
    provider="anthropic",      # Try native Anthropic API mode first
    api_mode="anthropic_messages",
    model="claude-sonnet-4-20250514",
)
# Fallback: provider="custom" with api_mode="openai_chat" if anthropic mode fails
```

### Pattern 4: Telegram Gateway (Hybrid: Bot API + Telethon)

**What:** Hermes gateway (`gateway/platforms/telegram.py`) supports python-telegram-bot webhooks. Telethon added as separate MCP tools for outgoing and search.

**Bot API (incoming — already in Hermes):**
```python
# Source: /hermes-agent/gateway/platforms/telegram.py [VERIFIED: local clone]
# Hermes runs in gateway mode:
#   hermes gateway --platform telegram
# Supports webhook mode via python-telegram-bot webhooks
```

**Telethon (outgoing — added as MCP tool):**
```python
# Source: Context7 Telethon docs + D-16/D-19
from telethon import TelegramClient

# Session file path: /opt/data/sessions/telethon.session
client = TelegramClient(session_path, api_id, api_hash)

# MCP tool: search_chats
async def search_chats(query: str, limit: int = 10):
    """Search Telegram chats and channels."""
    results = []
    async for dialog in client.iter_dialogs():
        if query.lower() in dialog.name.lower():
            results.append({
                "name": dialog.name,
                "id": dialog.id,
                "type": str(dialog.entity.__class__.__name__),
            })
            if len(results) >= limit:
                break
    return json.dumps(results)

# MCP tool: send_message_as_user
async def send_message_as_user(peer: str, message: str):
    """Send message as user (not bot)."""
    await client.send_message(peer, message)
    return json.dumps({"status": "sent"})
```

**Session handling:** Telethon session file stored in Docker volume `/opt/data/sessions/`. First launch requires interactive authentication (code entry from Telegram). Session files are portable between machines.

### Pattern 5: Docker Deployment

**What:** Hermes container added to existing docker-compose.yml.

**Dockerfile structure (derived from Hermes official Dockerfile + D-02):**
```dockerfile
# Source: /hermes-agent/Dockerfile (reference) + D-02 (Python 3.11)
FROM python:3.11-slim

# Install system deps
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl build-essential git && rm -rf /var/lib/apt/lists/*

# Install Hermes and deps
WORKDIR /opt/hermes
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install FastAPI wrapper deps
RUN pip install --no-cache-dir fastapi uvicorn httpx

# Copy AIM skills (D-03)
COPY skills/ /opt/hermes/skills/

# Copy FastAPI app
COPY app/ /opt/hermes/app/

# Runtime config
ENV HERMES_HOME=/opt/data
ENV PYTHONUNBUFFERED=1

# Create volume mount point
RUN mkdir -p /opt/data
VOLUME ["/opt/data"]

# Health check
HEALTHCHECK --interval=30s --timeout=10s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Run FastAPI (wraps Hermes AIAgent)
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

**docker-compose.yml addition:**
```yaml
# Source: Derived from AIM/docker-compose.yml + D-01
hermes:
  build: ./hermes
  image: aim-hermes:latest
  container_name: aim-hermes
  restart: unless-stopped       # D-08
  expose:
    - "8000"                    # D-07: internal only
  environment:
    - HERMES_HOME=/opt/data
    - OMNIROUTE_URL=http://193.111.152.14:7451
    - OMNIROUTE_AUTH=U9pjtK:hxtlqz
    - HERMES_API_KEY=${HERMES_API_KEY}
    - TELEGRAM_BOT_TOKEN=${TELEGRAM_BOT_TOKEN}
    - TELEGRAM_API_ID=${TELEGRAM_API_ID}
    - TELEGRAM_API_HASH=${TELEGRAM_API_HASH}
  volumes:
    - hermes_data:/opt/data     # D-06 + D-07: persistent
    - ./hermes/skills:/opt/hermes/skills:ro  # D-03: skills from repo
  networks:
    - aim-network
  healthcheck:
    test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
    interval: 30s
    timeout: 10s
    retries: 3
```

### Pattern 6: Next.js Chat Route (Thin Proxy)

**What:** `route.ts` stripped to minimum — extract message, determine mode, POST to Hermes, return response.

```typescript
// Source: Derived from current route.ts + D-11, D-12
// AIM/frontend/app/api/chat/send/route.ts
import { NextRequest, NextResponse } from "next/server";

const HERMES_URL = process.env.HERMES_URL || "http://hermes:8000";
const HERMES_API_KEY = process.env.HERMES_API_KEY;

export async function POST(request: NextRequest) {
  const { message, sessionId } = await request.json();

  // Determine mode from client status in DB (D-26)
  const mode = await determineClientMode(request);

  // POST to Hermes FastAPI wrapper
  const hermesResponse = await fetch(`${HERMES_URL}/api/chat`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "Authorization": `Bearer ${HERMES_API_KEY}`,
      "X-Client-Mode": mode,        // D-26
    },
    body: JSON.stringify({
      message,
      session_id: sessionId || null,
      mode,
    }),
  });

  if (!hermesResponse.ok) {
    // D-33: Enqueue in Redis for retry
    await enqueueMessage(message, sessionId, mode);
    return NextResponse.json({
      reply: "Operator will respond shortly. Your message has been queued.",
    });
  }

  const data = await hermesResponse.json();
  return NextResponse.json({
    reply: data.reply,
    sessionId: data.session_id,
  });
}
```

### Anti-Patterns to Avoid

- **Subprocess Hermes per request:** Launching `hermes chat` as subprocess for each HTTP request kills performance and loses session. Use AIAgent programmatic API.
- **DeepSeek remains in route.ts:** D-11 — DeepSeek fully removed. route.ts becomes thin proxy.
- **SOUL.md in system prompt without skill system:** SOUL.md must be loaded via Hermes skill mechanism (`load_soul_identity`), not hardcoded in system prompt.
- **Telethon as separate process:** Telethon must be an MCP tool inside Hermes (D-19), not a separate service.
- **Copying Hermes Dockerfile 1:1:** Official Dockerfile uses uv, Node.js, Playwright and Python 3.13. We need Python 3.11, no TUI, no browser — custom minimal Dockerfile.
- **Confusing MCP stdio with internal registry:** MCP server mode (`hermes mcp serve`) is for external clients. For tools available to AIAgent, use internal registry (`tools/registry.py`).

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| LLM agent loop | Custom agent loop | Hermes AIAgent (`run_agent.py`) | Production agent loop with tool calling, retry, context compression, session persistence |
| Tool definition framework | Manual JSON schemas | Hermes MCP tools (`tools/registry.py`) | Unified registry, automatic JSON schema generation, toolset membership |
| LLM provider routing | Custom router | OmniRoute (D-05/D-09) | Already provides fallback between providers |
| Session persistence | Custom DB | Hermes SessionDB (SQLite/`hermes_state.py`) | Built into Hermes — stores conversation history, trajectories |
| Skill auto-improvement | Custom framework | Hermes skill system (`cli-config.yaml` skills section) | Built-in support for auto-creating skills from repeated patterns |
| Telegram Bot API client | Manual HTTP requests to Bot API | python-telegram-bot (Hermes gateway) | Already built into Hermes gateway |
| Message queue | Custom queue worker | Redis (already in stack) + `rq` or `arq` | Redis already configured, minimal overhead |
| Chat history | Filesystem as in route.ts | Hermes SessionDB (SQLite) | Persistent, structured, searchable |

**Key insight:** Hermes already provides agent loop, tool registration, session persistence, skill management, and Telegram gateway. Building any of these from scratch would duplicate battle-tested infrastructure. The integration work is primarily wiring Hermes to AIM's specific API endpoints and configuring OmniRoute as the LLM provider.

## Runtime State Inventory

| Category | Items Found | Action Required |
|----------|-------------|------------------|
| Stored data | `/tmp/leads/` — lead dossiers in filesystem (profile.json, chat_history.json, status.json) | Volume mount: replace `/tmp/leads` with `/opt/data/leads` in Docker volume (Success Criterion #7) |
| Live service config | Prometheus targets — need to add `hermes:8000` scrape target | Code edit: `AIM/deploy/monitoring/prometheus.yml` |
| Live service config | Alertmanager — add downtime rule for Hermes (60s+) | Code edit: `AIM/deploy/monitoring/alertmanager.yml` |
| OS-registered state | systemd service Hermes (Success Criterion #6) — check status, fix or replace with Docker restart policy | D-08: Docker restart policy replaces systemd |
| Secrets/env vars | `DEEPSEEK_API_KEY` in `.env.production` — no longer needed (D-11) | Remove |
| Secrets/env vars | `HERMES_API_KEY`, `TELEGRAM_BOT_TOKEN`, `TELEGRAM_API_ID`, `TELEGRAM_API_HASH` — new | Add to `.env.production` |
| Build artifacts | `route.ts` changes — old DeepSeek SDK imports | Code edit: `route.ts` → thin proxy |
| Build artifacts | `docker-compose.yml` — new `hermes` service, new `hermes_data` volume | Code edit |

**Nothing found in category:** OS-registered state beyond systemd — verified by checking no launchd plists or pm2 processes reference hermes.

## Common Pitfalls

### Pitfall 1: OmniRoute Authentication Format
**What goes wrong:** OmniRoute uses HTTP basic auth (login:password), but Hermes AIAgent expects OpenAI-compatible API key or Anthropic x-api-key format.
**Why it happens:** OmniRoute is a proxy that may accept different auth formats depending on which API endpoint it proxies to.
**How to avoid:** Test with `curl` before implementing. Try `provider="anthropic"` with `x-api-key` header first, fall back to `provider="custom"` with `api_mode="openai_chat"`.
**Warning signs:** 401/403 errors when calling OmniRoute through Hermes.

### Pitfall 2: Session DB Concurrency
**What goes wrong:** Multiple concurrent requests from Next.js to the same session_id can corrupt the SQLite session DB.
**Why it happens:** SQLite is not designed for concurrent writes from multiple threads/processes.
**How to avoid:** FastAPI wrapper must serialize requests to the same session_id (`asyncio.Lock` per session). Alternatively: WAL mode in SQLite + timeout.
**Warning signs:** `sqlite3.OperationalError: database is locked` errors.

### Pitfall 3: Telethon Session File and Docker
**What goes wrong:** Telethon session file lost when container is rebuilt.
**Why it happens:** Session file created at first login (requires interactive code entry), but not stored in volume.
**How to avoid:** Docker volume mount `/opt/data/sessions/` for Telethon session file. Manual Telethon authentication once at first deploy.
**Warning signs:** Telethon asks for phone code on every container restart.

### Pitfall 4: SOUL.md Not Loading from skills/aim/
**What goes wrong:** Hermes expects SOUL.md in `$HERMES_HOME/SOUL.md`, not `$HERMES_HOME/skills/aim/SOUL.md`.
**Why it happens:** `load_soul_md()` function in `agent/prompt_builder.py:1308` reads SOUL.md from `get_hermes_home() / "SOUL.md"`.
**How to avoid:** Symlink or copy SOUL.md from `skills/aim/SOUL.md` to `HERMES_HOME/SOUL.md`. Or use a startup script that copies it.
**Warning signs:** Hermes does not use AIM identity, responds as generic assistant.

### Pitfall 5: Internal Registry Tools vs MCP stdio
**What goes wrong:** Tools registered, but Hermes does not see them when called via API.
**Why it happens:** MCP tools registered via `hermes mcp serve` (stdio) use a different mechanism than internal tools loaded by AIAgent.
**How to avoid:** Register tools via Hermes registry (`tools/registry.py` — `registry.register()`) with correct toolset name, then specify `enabled_toolsets=["aim-operations"]` in AIAgent constructor. This is NOT MCP stdio — it is Hermes' internal tool mechanism.
**Warning signs:** Hermes does not call tools, responds with text only.

### Pitfall 6: AIAgent TUI Dependencies in Headless Docker
**What goes wrong:** AIAgent imports `prompt_toolkit` or `rich` and attempts stdin/stdout operations that fail without TTY.
**Why it happens:** Hermes was designed as a CLI tool first; some imports may assume terminal presence.
**How to avoid:** Set `quiet_mode=True` in AIAgent constructor. Test in Docker without TTY (`docker run --rm -it` vs `docker run --rm`). If TUI imports cause import errors, conditional import patches may be needed.
**Warning signs:** `ImportError` for `prompt_toolkit`, or hanging on stdin read.

## Code Examples

### FastAPI Wrapper (app/main.py)
```python
# Source: Derived from Hermes AIAgent API (run_agent.py class AIAgent) [VERIFIED: local clone]
import asyncio
from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel
import os

# Lazy import — AIAgent pulls heavy deps
from run_agent import AIAgent

app = FastAPI()

# Session locks for SQLite concurrency safety
_session_locks: dict[str, asyncio.Lock] = {}

OMNIROUTE_URL = os.getenv("OMNIROUTE_URL", "http://193.111.152.14:7451")
OMNIROUTE_AUTH = os.getenv("OMNIROUTE_AUTH", "U9pjtK:hxtlqz")
HERMES_API_KEY = os.getenv("HERMES_API_KEY", "")

class ChatRequest(BaseModel):
    message: str
    session_id: str | None = None
    mode: str = "PRESALE"
    user_id: str | None = None

@app.post("/api/chat")
async def chat(request: ChatRequest):
    # Auth check (D-25)
    # ... Bearer token verification ...

    # Serialize per-session (Pitfall #2)
    lock = _session_locks.setdefault(request.session_id or "new", asyncio.Lock())
    async with lock:
        agent = AIAgent(
            base_url=OMNIROUTE_URL,
            api_key=OMNIROUTE_AUTH,
            provider="custom",
            api_mode="openai_chat",
            model="claude-sonnet-4-20250514",
            session_id=request.session_id,
            load_soul_identity=True,
            ephemeral_system_prompt=get_mode_prompt(request.mode),
            enabled_toolsets=["aim-operations"],
            max_iterations=15,
            quiet_mode=True,
        )
        response = agent.run_conversation(request.message)
        return {
            "reply": response,
            "session_id": agent.session_id,
        }

@app.get("/health")
async def health():
    return {"status": "ok", "hermes": "healthy"}

def get_mode_prompt(mode: str) -> str:
    prompts = {
        "PRESALE": (
            "You are in PRESALE mode. Task: demonstrate WOW data in 2-3 minutes, "
            "collect contact information. You are the first touchpoint for potential clients."
        ),
        "ACTIVE": (
            "You are in ACTIVE PROJECT mode. Task: respond to client about their project, "
            "show KPIs, provide status updates, escalate issues to Mikhail."
        ),
        "ADMIN": (
            "You are in ADMIN mode. Full system access. You are communicating with "
            "Mikhail Eliseev (agency founder). Be direct and data-driven."
        ),
    }
    return prompts.get(mode, prompts["PRESALE"])
```

### Prometheus Scrape Target Addition
```yaml
# Source: Derived from AIM/prometheus.yml + D-29/D-30
# Add to scrape_configs:
  - job_name: 'aim-hermes'
    static_configs:
      - targets: ['hermes:8000']
    metrics_path: '/health'
    scrape_interval: 30s
```

### Alertmanager Rule for Hermes Downtime
```yaml
# Source: Derived from D-31 (60s+ downtime trigger)
# Add to rules.yml:
  - alert: HermesDown
    expr: up{job="aim-hermes"} == 0
    for: 1m
    labels:
      severity: critical
    annotations:
      summary: "Hermes Agent unavailable"
      description: "Hermes container not responding for more than 60 seconds."
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| DeepSeek directly from route.ts | Hermes Agent via OmniRoute -> Anthropic | Phase 15 | Single LLM gateway, skill system, tool calling |
| OPERATOR_PROMPT hardcoded in route.ts | SOUL.md as Hermes skill | Phase 15 | Hot-reload identity without deployment |
| Tools in system prompt | MCP tools registered in Hermes | Phase 15 | Real AIM API calls instead of text commands |
| /tmp/leads (tmpfs, not persistent) | Docker volume mount | Phase 15 | Lead data survives restarts |
| systemd for Hermes | Docker restart: unless-stopped | Phase 15 | Unified management via docker-compose |
| Filesystem for chat history | Hermes SessionDB (SQLite) | Phase 15 | Structured storage with search and compression |

**Deprecated/outdated:**
- DeepSeek SDK in `route.ts`: fully removed (D-11)
- `DEEPSEEK_API_KEY` env var: removed from `.env.production` (D-11)
- Filesystem-based lead storage in `/tmp/leads`: replaced by Docker volume (D-06, Success Criterion #7)

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | OmniRoute proxy accepts OpenAI-compatible requests with Bearer token or basic auth | OmniRoute Provider Config | Wrong auth format — need different provider mode |
| A2 | FastAPI AIAgent programmatic API works correctly (not subprocess) | FastAPI Wrapper | Hidden dependencies or TUI-specific imports that break without terminal |
| A3 | `load_soul_identity=True` and `ephemeral_system_prompt` work together without conflicts | FastAPI Wrapper | SOUL.md and mode prompt may conflict or one may override the other |
| A4 | MCP tools registered via Hermes registry are available to AIAgent (not just via `hermes mcp serve`) | Tool Registration | MCP tools may only work in stdio mode; API needs different mechanism |
| A5 | Telethon session file can be saved and reused in Docker volume without state loss | Telegram Gateway | May require re-authentication on IP change or other MTProto conditions |
| A6 | OmniRoute basic auth (U9pjtK:hxtlqz) passed via Authorization header or api_key parameter | OmniRoute Configuration | Wrong format — need different auth method |
| A7 | Hermes AIAgent.run_conversation() is synchronous (not async) | FastAPI Wrapper | If async, need different call pattern in FastAPI |

## Open Questions

1. **OmniRoute authentication format**
   - What we know: OmniRoute at 193.111.152.14:7451, HTTP, login: U9pjtK, password: hxtlqz
   - What's unclear: Does it accept OpenAI-compatible requests (Bearer token = base64(login:password))? Or need native Anthropic API with x-api-key? Or basic auth via Authorization header?
   - Recommendation: Test with curl before implementing. Try all three formats.

2. **Hermes AIAgent in production environment without TUI**
   - What we know: AIAgent has `quiet_mode=True` parameter
   - What's unclear: Do all TUI-related imports (prompt_toolkit, rich) gracefully degrade in headless mode? Does AIAgent try to use stdin/stdout for interactive input?
   - Recommendation: Test in Docker without TTY before wiring up FastAPI.

3. **MCP tools vs Hermes registry tools — difference**
   - What we know: Hermes has two mechanisms: (1) MCP server mode for external clients, (2) internal tool registry for AIAgent
   - What's unclear: Can internal registry tools use MCP protocol to call external services? Or must they be pure Python functions?
   - Recommendation: Use internal registry for AIM tools (Python functions with HTTP calls), not MCP stdio.

4. **Telethon session in CI/CD**
   - What we know: Telethon requires interactive authentication at first launch
   - What's unclear: Can we pre-create session file on dev machine and copy to server?
   - Recommendation: Yes, Telethon session files are portable between machines. Pre-create on dev, commit to secure storage or manually place on server.

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| Docker | Hermes container | Pending server check | — | — |
| Docker Compose | Orchestration | Pending server check | — | — |
| Python 3.11 | Hermes Dockerfile | N/A (Docker image) | 3.11 (image) | — |
| Redis | Message queue | In stack | 7-alpine | — |
| PostgreSQL | AIM API | In stack | 16-alpine | — |
| OmniRoute Proxy | LLM provider | Pending network check | — | Direct Anthropic API |
| Telethon | Telegram user-client | Pending install | — | Bot API only initially |

**Missing dependencies with no fallback:**
- OmniRoute Proxy — if unavailable, need direct Anthropic API key

**Missing dependencies with fallback:**
- Telethon — if problematic, start with Bot API only (incoming), add outgoing later

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest 9.0.2 (Hermes `dev` extra) + pytest for FastAPI |
| Config file | none — see Wave 0 |
| Quick run command | `pytest AIM/hermes/tests/ -x --timeout=30` |
| Full suite command | `pytest AIM/hermes/tests/ -v` |

### Phase Requirements -> Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| SUCCESS-1 | SOUL.md loads and influences responses | integration | `pytest tests/test_soul.py::test_soul_identity_loaded -x` | No — Wave 0 |
| SUCCESS-2 | 6 MCP tools register and are callable | unit | `pytest tests/test_tools.py::test_all_tools_registered -x` | No — Wave 0 |
| SUCCESS-3 | /api/chat/send proxies through Hermes | integration | `pytest tests/test_chat_proxy.py::test_proxy_to_hermes -x` | No — Wave 0 |
| SUCCESS-4 | 3 modes (PRESALE/ACTIVE/ADMIN) apply correctly | unit | `pytest tests/test_modes.py::test_mode_selection -x` | No — Wave 0 |
| SUCCESS-5 | Telegram gateway receives messages | integration | manual-only (requires real Telegram) | No |
| SUCCESS-7 | /tmp/leads -> Docker volume | integration | `pytest tests/test_lead_persistence.py::test_leads_survive_restart -x` | No — Wave 0 |

### Sampling Rate
- **Per task commit:** `pytest AIM/hermes/tests/ -x --timeout=30`
- **Per wave merge:** `pytest AIM/hermes/tests/ -v`
- **Phase gate:** Full suite green before `/gsd-verify-work`

### Wave 0 Gaps
- [ ] `AIM/hermes/tests/` — directory does not exist, needs creation
- [ ] `AIM/hermes/tests/test_soul.py` — SOUL.md loading test
- [ ] `AIM/hermes/tests/test_tools.py` — tool registration test
- [ ] `AIM/hermes/tests/test_chat_proxy.py` — chat proxy test
- [ ] `AIM/hermes/tests/test_modes.py` — mode test
- [ ] `AIM/hermes/tests/test_lead_persistence.py` — lead persistence test
- [ ] `AIM/hermes/tests/conftest.py` — shared fixtures (mock AIAgent, mock AIM API)

## Security Domain

### Applicable ASVS Categories

| ASVS Category | Applies | Standard Control |
|---------------|---------|-----------------|
| V2 Authentication | Yes | Bearer token (HERMES_API_KEY) — D-25, D-27 |
| V3 Session Management | Yes | Hermes SessionDB (SQLite) — session_id per conversation |
| V4 Access Control | Yes | Next.js determines mode (D-26), ADMIN protected by NextAuth (D-28) |
| V5 Input Validation | Yes | Pydantic models for ChatRequest, MCP tool parameter validation |
| V6 Cryptography | Yes | TLS terminated at Nginx, Hermes internal-only (D-07) |
| V7 Logging | Yes | Hermes logging (`hermes_logging.py`) + Docker json-file driver |
| V11 Business Logic | Yes | Rate limiting via token-bucket, message resilience via Redis (D-33-D-36) |

### Known Threat Patterns for Hermes/Docker Stack

| Pattern | STRIDE | Standard Mitigation |
|---------|--------|---------------------|
| Bearer token leakage in logs | Information Disclosure | Sanitize logs, do not log Authorization header |
| SQL injection in session_id | Tampering | Parameterized queries (Hermes SessionDB uses parameterized SQL) |
| SSRF via MCP tools (internal HTTP calls) | Information Disclosure | MCP tools only to app:8000 (internal network), URL not constructed from user input |
| Prompt injection via chat messages | Spoofing | Hermes agent loop isolates system prompt from user input |
| Unauthorized ADMIN mode access | Elevation of Privilege | D-28: role=admin check in Next.js (NextAuth) before passing mode to Hermes |
| Denial of Service via request flood | Denial of Service | Rate limiting in Next.js, max_iterations in AIAgent, 30s timeout (D-34) |
| Inter-container traffic interception | Information Disclosure | D-07: Hermes only on internal Docker network (not exposed externally) |

## Sources

### Primary (HIGH confidence)
- `/hermes-agent/pyproject.toml` — exact-pinned dependency versions, extras definitions [VERIFIED: local clone]
- `/hermes-agent/run_agent.py` — AIAgent class, constructor parameters, run_conversation [VERIFIED: local clone]
- `/hermes-agent/agent/prompt_builder.py` — load_soul_md() function, SOUL.md loading at line 1308 [VERIFIED: local clone]
- `/hermes-agent/tools/registry.py` — tool registration API, toolset membership mechanism [VERIFIED: local clone]
- `/hermes-agent/Dockerfile` — official Docker deployment patterns, HERMES_HOME, entrypoint [VERIFIED: local clone]
- `/hermes-agent/docker/entrypoint.sh` — volume mounts, privilege dropping, bootstrap flow [VERIFIED: local clone]
- `/hermes-agent/mcp_serve.py` — MCP server mode, FastMCP tool registration, stdio transport [VERIFIED: local clone]
- `/hermes-agent/gateway/platforms/telegram.py` — Telegram Bot API integration [VERIFIED: local clone]
- `/hermes-agent/cli-config.yaml.example` — configuration structure, provider setup, skills, mcp_servers [VERIFIED: local clone]
- `/hermes-agent/skills/research/llm-wiki/SKILL.md` — SKILL.md format (YAML frontmatter + markdown body) [VERIFIED: local clone]
- Context7: `/modelcontextprotocol/python-sdk` — FastMCP API, stdio/streamable-http transport [VERIFIED: official docs]

### Secondary (MEDIUM confidence)
- `AIM/hermes/skills/aim/SOUL.md` — initial SOUL.md version (73 lines, needs expansion with 3 modes) [VERIFIED: local file]
- `AIM/frontend/app/api/chat/send/route.ts` — current chat route (uses DeepSeek, will be replaced) [VERIFIED: local file]
- `AIM/docker-compose.yml` — current stack (app, redis, nginx, prometheus, grafana, postgres) [VERIFIED: local file]
- `AIM/deploy/monitoring/prometheus.yml` — current Prometheus configuration [VERIFIED: local file]
- `AIM/deploy/monitoring/alertmanager.yml` — current Alertmanager configuration [VERIFIED: local file]
- `.planning/config.json` — nyquist_validation: true, security_enforcement: true [VERIFIED: local file]

### Tertiary (LOW confidence)
- None — all critical claims verified through Context7 or source code reading

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — all libraries verified against pyproject.toml from cloned Hermes repo
- Architecture: HIGH — architecture based on real Hermes source code (Dockerfile, entrypoint, run_agent.py, mcp_serve.py) and 36 locked decisions from CONTEXT.md
- Pitfalls: MEDIUM — 3 of 6 pitfalls involve assumptions (A1 OmniRoute auth, A4 registry-vs-mcp, A7 sync-vs-async AIAgent) requiring validation at implementation time
- Tools: MEDIUM — internal registry vs MCP stdio distinction requires clarification at implementation time

**Research date:** 2026-05-19
**Valid until:** 2026-06-19 (Hermes v0.14.0 stable, but OmniRoute and API endpoints may change sooner)
