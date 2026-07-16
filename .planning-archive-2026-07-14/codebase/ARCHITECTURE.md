<!-- refreshed: 2026-06-19 -->
# Architecture

**Analysis Date:** 2026-06-19

## System Overview

```text
+-------------------------------------------------------------------+
|                     Chat Entry Points                              |
|  +----- iamaim.ru chat -----+  +----- Telegram bot ------+        |
|  | Next.js frontend (3099)  |  | Bot API webhook/polling  |        |
|  +------------+--------------+  +------------+-------------+        |
|               |                             |                      |
|               v                             v                      |
+-------------------------------------------------------------------+
|                    Hermes FastAPI (port 8000)                       |
|  `AIM/hermes/app/main.py`                                          |
|  /api/chat    /api/chat/stream    /telegram/webhook                |
|  +------------+-------------------+------------------+             |
|  | auth.py    | session_api.py    | knowledge_router  |             |
|  | (Bearer)   | (archive GET)     | /api/knowledge/*  |             |
+--+------------+-------------------+------------------+-------------+
|  | agent_wrapper.py              | agent_wrapper_optimized.py      |
|  | run_agent (async)             | _presale_prompt / _active_prompt|
|  | run_agent_sync (Telegram)     | build_system_prompt()           |
|  +-------------------------------+                                 |
|  | SOUL.md (69KB identity)       | 3PHASE_PIPELINE.md              |
|  | $HERMES_HOME/SOUL.md          | (pipeline rules, when present)   |
+--+-------------------------------+---------------------------------+
|                  hermes-agent Library (pip package v0.14.0)         |
|  AIAgent | SessionDB (SQLite) | tools.registry | skill_view()      |
+--+-------------------+----------+------------------+---------------+
|  | Tool Registry     | Skills System            | Config           |
|  | tools.registry    | SKILL.md in /opt/hermes/ | config.yaml      |
|  | register() at     | LLM calls skill_view()   | model: deepseek  |
|  | module import     | to load context on demand| v4-pro/v4-flash  |
+--+-------------------+--------------------------+------------------+
         |                          |
         v                          v
+-------------------------------------------------------------------+
|                     AIM Backend (http://app:8000)                   |
|  `AIM/src/aim/` — REST API                                         |
|  /api/presale/prescan-staged    /api/competitors/find              |
|  /api/seo/audit                 /api/ads/report                    |
|  /api/leads                     /api/sales/*                       |
+-------------------------------------------------------------------+
         |
         v
+-------------------------------------------------------------------+
|  External Services                                                 |
|  PostgreSQL | Redis | DeepSeek API | Apify | Brave Search          |
|  Firecrawl  | AssemblyAI | Telegram | nalog.ru                    |
+-------------------------------------------------------------------+
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

Local-only (not on server):
| Component | Responsibility | File |
|-----------|----------------|------|
| OmniRoute Direct | Legacy LLM proxy (not used since DeepSeek API direct) | `AIM/hermes/app/omniroute_direct.py` |
| MCP Proxy | MCP protocol bridge for external clients | `AIM/hermes/mcp-proxy/proxy.py` |

## Pattern Overview

**Overall:** LLM-First Tool Orchestration

**Key Characteristics:**
- **Hermes (LLM) decides what tools to call** — no hardcoded orchestration. The LLM reads SOUL.md, receives user message, and selects tools autonomously.
- **All AI logic lives in the LLM prompt** — SOUL.md + mode prompts define the entire behavior, workflow, and decision tree.
- **Tools are REST API proxies** — each tool call translates to a single HTTP request to `http://app:8000` (aim-app container on Docker internal network). Tools are thin wrappers around API endpoints.
- **Skills are LLM-loaded Markdown documents** — SKILL.md files are loaded by the LLM at runtime via the `skill_view()` function from hermes-agent. The LLM reads them as context and follows their instructions.
- **Dual entry points** — web chat (Next.js proxy via FastAPI) and Telegram (webhook + getUpdates polling), both flowing through the same AIAgent.
- **Session persistence in SQLite** — hermes-agent's SessionDB stores conversation history in `/opt/data/state.db`, surviving container restarts.

## Layers

**HTTP Layer:**
- Purpose: Accept HTTP requests, verify auth, route to agent
- Location: `AIM/hermes/app/main.py` (FastAPI routes), `AIM/hermes/app/auth.py` (Bearer auth)
- Contains: Chat endpoints (sync + SSE streaming), Telegram webhook, health/metrics, session archive
- Depends on: Agent Wrapper layer
- Used by: Next.js frontend, Telegram Bot API, Prometheus, bootstrap script

**Agent Wrapper Layer:**
- Purpose: Manage AIAgent lifecycle, build prompts, handle session caching and concurrency
- Location: `AIM/hermes/app/agent_wrapper.py`, `AIM/hermes/app/agent_wrapper_optimized.py`
- Contains: `run_agent()` (async), `run_agent_sync()` (for Telegram thread), `build_system_prompt()`, `_create_agent()`, `get_mode_prompt()`, SOUL.md caching, session locking
- Depends on: hermes-agent library (AIAgent, SessionDB)
- Used by: HTTP Layer, Telegram Gateway

**hermes-agent Library (external pip):**
- Purpose: Core AI agent framework — LLM conversation loop, tool invocation, session state, skill loading
- Location: `hermes-agent==0.14.0` pip package with extras: `[mcp, messaging, web, anthropic]`
- Contains: `AIAgent.run_conversation()`, `tools.registry` (tool registry with register() decorator), `skill_view()` (load SKILL.md into LLM context), SessionDB (SQLite session storage)
- Depends on: DeepSeek API (or OmniRoute, configurable via `config.yaml`)
- Used by: Agent Wrapper Layer

**Tool Layer:**
- Purpose: Register tools in the hermes-agent registry, implement tool handlers that call AIM backend API
- Location: `AIM/hermes/app/tools/*.py`
- Contains: Tool handlers (async functions), registry.register() calls at module level, HTTP calls to `http://app:8000`
- Depends on: AIM Backend (aim-app container)
- Used by: hermes-agent (LLM invokes tools via the registry)

**Skills Layer:**
- Purpose: Load context (SKILL.md files) into the LLM's working memory for specific tasks
- Location: `AIM/hermes/skills/` (local), `/opt/hermes/skills/` (Docker build), `/opt/data/skills/` (server runtime — curated by the system)
- Contains: SKILL.md documents with YAML frontmatter (name, version, triggers, description)
- Depends on: hermes-agent's `skill_view()` function
- Used by: LLM (reads skill content as system context on demand)

**Backend Layer (aim-app):**
- Purpose: Execute actual business logic — prescan, competitor search, SEO audit, lead management
- Location: `AIM/src/aim/` (local), Docker container `aim-app` at `http://app:8000`
- Contains: REST API endpoints called by tool handlers
- Depends on: PostgreSQL, Redis, external APIs (Apify, nalog.ru, etc.)
- Used by: Tool Layer

## Data Flow

### Primary Request Path (Web Chat — SSE Streaming)

1. Next.js frontend sends POST `/api/chat/stream` with `{message, session_id, mode}` and `Authorization: Bearer <HERMES_API_KEY>` (`AIM/hermes/app/main.py:312`)
2. Auth verified by `verify_api_key()` dependency (`AIM/hermes/app/auth.py:18`)
3. SSE generator creates progress queue, sets `_tool_progress_queue` global (`AIM/hermes/app/main.py:345`)
4. `run_agent()` called in background `asyncio.Task` (`AIM/hermes/app/main.py:360`)
5. `run_agent()` acquires per-session `asyncio.Lock`, dispatches `run_agent_sync()` to executor thread (`AIM/hermes/app/agent_wrapper.py:679`)
6. `run_agent_sync()` creates/reuses AIAgent with SOUL.md identity + mode prompt, calls `agent.run_conversation()` in a ThreadPoolExecutor with 900s timeout (`AIM/hermes/app/agent_wrapper.py:538`)
7. AIAgent sends conversation to DeepSeek API with full tool list. LLM decides which tools to call.
8. For each tool call, hermes-agent invokes the registered handler (e.g., `handle_run_prescan()` in `AIM/hermes/app/tools/run_prescan.py:30`)
9. Tool handler makes HTTP request to `http://app:8000/api/presale/prescan-staged` via `httpx.AsyncClient` (`AIM/hermes/app/tools/run_prescan.py:65`)
10. Tool handler pushes progress events via `push_tool_progress()` (`AIM/hermes/app/main.py:63`) — thread-safe via `loop.call_soon_threadsafe`
11. SSE generator loop reads progress events from queue, yields `data: {"type": "tool-progress", ...}` (`AIM/hermes/app/main.py:378`)
12. After agent completes, SSE generator streams: step-start/step-end lifecycle events, text-delta tokens, finish signal (`AIM/hermes/app/main.py:419-443`)
13. Return `StreamingResponse` with `text/event-stream` media type (`AIM/hermes/app/main.py:460`)

### Telegram Request Path

1. Telegram sends message to webhook (`/telegram/webhook`) or is fetched by polling thread (`AIM/hermes/app/telegram_gateway.py:351` polling loop)
2. Mode determined from `chat_id`: admin chat gets ADMIN, active leads ACTIVE, others PRESALE (`AIM/hermes/app/telegram_gateway.py:36-46`)
3. Voice messages transcribed via AssemblyAI (`AIM/hermes/app/voice_transcriber.py`)
4. `_call_hermes_agent()` invokes `run_agent_sync()` synchronously in the polling thread (`AIM/hermes/app/telegram_gateway.py:329`)
5. Reply sent via Telegram Bot API with HTML-to-plaintext fallback (`AIM/hermes/app/telegram_gateway.py:198`)
6. Large reports (>3500 chars) saved to `/opt/data/reports/` and linked in truncated message

### Bootstrap Self-Study Flow

1. Container starts, `Dockerfile` ENTRYPOINT runs `copy_soul.sh && uvicorn ...` (`AIM/hermes/Dockerfile:87`)
2. `copy_soul.sh` copies `SOUL.md`, `services.md`, `processes.md`, `kpi.md` from `/opt/hermes/skills/aim/` to `/opt/data/` (`AIM/hermes/scripts/copy_soul.sh:28-48`)
3. `copy_soul.sh` launches `bootstrap.sh` in background (`AIM/hermes/scripts/copy_soul.sh:54`)
4. `bootstrap.sh` waits for `/health` to become available, then POSTs to `/api/chat` with ADMIN mode and BOOTSTRAP.md content as the message (`AIM/hermes/scripts/bootstrap.sh:34-73`)
5. Hermes reads BOOTSTRAP.md instructions, studies all tools and skills, writes learnings to `/opt/data/learnings.md`, creates `/opt/data/.bootstrapped` flag
6. On subsequent starts, `bootstrap.sh` checks for `/.bootstrapped` and skips

## System Prompt Assembly

The full system prompt seen by the LLM is built from two sources:

**1. SOUL.md (Identity + Permanent Knowledge):**
- Location: `/opt/data/SOUL.md` (copied from `/opt/hermes/skills/aim/SOUL.md` at startup)
- Size: ~69KB (server), loaded once and cached in memory
- Content: Agent identity, working principles, modes of operation, tool catalog, pricing, architecture, self-learning protocols, niche detection
- Loaded via: `AIAgent(load_soul_identity=True)` for web path, `load_soul_md()` + `build_system_prompt()` for Telegram path
- Cached in: `_soul_md_cache` module variable (`AIM/hermes/app/agent_wrapper.py:57`)

**2. Ephemeral Mode Prompts:**
- Built by `get_mode_prompt(mode)` (`AIM/hermes/app/agent_wrapper.py:130`)
- Four modes: PRESALE, ACTIVE, ADMIN, SALES_ADMIN
- Each mode prompt defines tool usage rules, dialog flow, tone, and constraints
- PRESALE prompt optionally prepends `3PHASE_PIPELINE.md` when available (`AIM/hermes/app/agent_wrapper.py:156`)
- Mode is determined by `X-Client-Mode` header (web) or chat_id lookup (Telegram)

**Assembly for web path:** `SOUL.md` (via load_soul_identity) + ephemeral prompt (via `ephemeral_system_prompt` parameter)
**Assembly for Telegram path:** `load_soul_md() + get_mode_prompt(mode)` manually concatenated

## Key Abstractions

**AIAgent (hermes-agent library):**
- Purpose: Core conversation loop — sends messages to LLM, parses tool calls, invokes registered handlers, returns results
- Created via: `_create_agent()` in `AIM/hermes/app/agent_wrapper.py:397`
- Configuration: `base_url` (DeepSeek API), `model` (deepseek-v4-pro), `session_db` (SQLite persistence), `load_soul_identity=True`, `ephemeral_system_prompt`, `enabled_toolsets=["aim-operations", "hermes-debug"]`, `max_iterations=25`
- Cached per session_id in `_agent_cache` dict with 24h TTL

**Tool Registry (tools.registry):**
- Purpose: Map tool names to handler functions and JSON schemas, exposed to LLM via function calling
- Registration pattern: `registry.register(name="run_prescan", toolset="aim-operations", schema={...}, handler=handle_run_prescan, ...)`
- Called at module import time (side-effect in each `tools/*.py` file)
- Two toolsets: `aim-operations` (business tools, 18 tools on server) and `hermes-debug` (system tools, 15 tools)

**Skill System (skill_view):**
- Purpose: Load domain-specific instructions (SKILL.md) into the LLM's context on demand
- The LLM calls `skill_view(name='client-onboarding-pipeline')` to load a skill
- Skills are YAML-frontmatter Markdown files with name, version, triggers, description
- Key skills: `client-onboarding-pipeline` (v5.5.0, 15-phase onboarding), `presale-pipeline` (v3.3.0, 8-skill orchestration), `deep-research-phase-0`, `aim` (identity + supplementary docs)
- Skills are loaded dynamically by hermes-agent — the LLM decides when to invoke `skill_view()`

**Session Lock:**
- Purpose: Prevent SQLite "database is locked" errors from concurrent requests on the same session
- Per-session `asyncio.Lock` for web path (`AIM/hermes/app/agent_wrapper.py:42`)
- Per-session `threading.Lock` for Telegram/sync path (`AIM/hermes/app/agent_wrapper.py:716`)
- Agent cache uses real session_id as key after first run (not input session_id)

## Entry Points

**POST /api/chat:**
- Location: `AIM/hermes/app/main.py:263`
- Triggers: Next.js frontend (iamaim.ru chat widget) via proxy
- Responsibilities: Synchronous chat — run agent, return reply + tool_calls in JSON. Used for quick interactions that don't need streaming.

**POST /api/chat/stream:**
- Location: `AIM/hermes/app/main.py:312`
- Triggers: Next.js full-page chat page
- Responsibilities: SSE streaming chat — runs agent in background, streams tool-progress events in real-time, emits text-delta tokens word-by-word, 420s hard deadline

**POST /telegram/webhook:**
- Location: `AIM/hermes/app/telegram_gateway.py:110`
- Triggers: Telegram Bot API (when webhook is configured)
- Responsibilities: Receive Telegram messages, handle /start deep-link binding, transcribe voice, route to Hermes agent, send reply

**Telegram getUpdates Polling:**
- Location: `AIM/hermes/app/telegram_gateway.py:351` (polling loop started from `/health` or `/telegram/webhook`)
- Triggers: Automatic — starts on first health check if webhook not configured
- Responsibilities: Long-poll Telegram for messages, process through Hermes, reply via Bot API. Runs in separate OS thread.

**GET /health:**
- Location: `AIM/hermes/app/main.py:188`
- Triggers: Docker HEALTHCHECK, Prometheus scraping, bootstrap.sh
- Responsibilities: Return health status + knowledge loop stats. Lazy-initializes Telegram polling on first call.

**GET /metrics:**
- Location: `AIM/hermes/app/main.py:230`
- Triggers: Prometheus scraping
- Responsibilities: Expose RED metrics (Rate, Errors, Duration) + chat metrics as Prometheus text format

**GET /api/session/{hash}:**
- Location: `AIM/hermes/app/routers/session_api.py:87`
- Triggers: Admin dashboard, report viewing
- Responsibilities: Retrieve archived session data (conversation, prescan results, CI analysis) by 8-char hex hash

## How Pipeline Execution Works

The client-onboarding pipeline is defined in two layers:

**Layer 1: SOUL.md + Mode Prompts (LLM Behavior)**
- SOUL.md defines the agent's identity, tool catalog, working principles, and presale flow steps
- Mode prompts (PRESALE) define the 3-phase approach: Phase 1 (quick_overview + run_prescan), Phase 2 (find_competitors + run_ci_analysis), Phase 3 (present results + collect contact)
- The LLM reads these as behavioral instructions and follows them autonomously
- There is NO hardcoded pipeline execution code — the LLM decides which tools to call and in what order

**Layer 2: SKILL.md Documents (Loaded on Demand)**
- `client-onboarding-pipeline/SKILL.md` (v5.5.0): Detailed 15-phase protocol with execution checklists, tool calling patterns, competitor verification, report generation
- `presale-pipeline/SKILL.md` (v3.3.0): 8-phase auto-orchestration — runs all skills sequentially without asking permission, produces HTML proposal
- Skills are loaded by the LLM calling `skill_view()` — they provide detailed instructions for complex tasks
- Skills contain execution logs with `[ ]` checkboxes — the LLM tracks completion

**Execution flow:**
1. User sends URL in chat
2. LLM (reading SOUL.md) knows to call `quick_overview` first (Phase 1, Round 1)
3. LLM presents quick_overview results, then calls `run_prescan` (Phase 1, Round 2)
4. `run_prescan` calls `http://app:8000/api/presale/prescan-staged` — 3-stage pipeline: financials → deep analysis → market
5. After prescan, LLM calls `find_competitors` → `run_ci_analysis` → presents results
6. When LLM needs detailed instructions, it calls `skill_view('client-onboarding-pipeline')` to load the full protocol

## Architectural Constraints

- **Threading:** FastAPI async event loop for HTTP; Telegram polling runs in a separate OS thread via `run_in_executor`; AIAgent calls are synchronous and wrapped in `ThreadPoolExecutor` with 900s timeout
- **Global state:** `_tool_progress_queue` (asyncio.Queue) is set per-request; `_agent_cache` (dict) shared across requests with threading.Lock per session; `_soul_md_cache` (string) immutable after first load
- **Circular imports:** `app.main.py` imports from `app.tools` which imports from `app.main` (for `push_tool_progress`) — resolved by late import inside `handle_run_prescan()` function body
- **SQLite concurrency:** Single-writer lock per session (both async and thread variants) prevents "database is locked" errors from state.db (21MB+ on server)
- **Network:** Hermes and aim-app communicate on Docker internal network `aim_aim-network` via DNS name `app:8000` — never exposed to host; Hermes port 8000 exposed only within Docker network (proxy:nginx → aim-frontend → Hermes)
- **Configurable LLM backend:** Switched by changing `config.yaml` model/provider or `LLM_MODEL` env var. Currently DeepSeek API direct. Previously OmniRoute proxy. SOUL.md identity, tool schemas, and mode prompts are model-agnostic.

## Error Handling

**Strategy:** Multi-layer — each layer handles its own failures and propagates structured errors upward.

**Patterns:**
- Tool handlers catch `httpx.HTTPStatusError` and `httpx.RequestError` separately, return JSON error strings (`AIM/hermes/app/tools/run_prescan.py:109-127`)
- Agent wrapper catches `FutureTimeoutError` from ThreadPoolExecutor, returns graceful timeout message (`AIM/hermes/app/agent_wrapper.py:584-609`)
- SSE generator catches all exceptions, yields `{"type": "error", "message": ...}` SSE event (`AIM/hermes/app/main.py:445-448`)
- Failed tools should NOT be retried more than once — Mode prompts explicitly forbid re-calling failed tools
- Learnings extraction failures are logged but never propagated (fire-and-forget)

## Cross-Cutting Concerns

**Logging:** Root logger configured in `main.py` with INFO level, format: `%(asctime)s [%(levelname)s] %(name)s: %(message)s` to stdout. Docker captures stdout → journald.

**Validation:** Auth via Bearer token (HERMES_API_KEY env var). Mode is trusted from Next.js `X-Client-Mode` header. Admin protection is at NextAuth layer, not Hermes.

**Authentication:** Bearer token for all `/api/chat/*` endpoints (`AIM/hermes/app/auth.py:18`). `/health` and `/metrics` are unauthenticated. Telegram uses Bot API token (separate env var).

**File Write Permissions:** Hermes runs as root inside Docker container. Can write to:
- `/opt/data/` — volume mount (persistent): memories, learnings, reports, sessions, proposals, skills, state.db
- `/opt/hermes/` — Docker image layer (read-only after build, but writable at runtime since it's the image root)
- `/opt/data/memories/proposals/` — where file_write creates HTML proposals
- `/opt/data/memories/learnings/` — self-learning diary entries
- `/opt/data/reports/` — large Telegram reports
- `/opt/data/.bootstrapped` — bootstrap completion flag

---

*Architecture analysis: 2026-06-19*
