# Coding Conventions

**Analysis Date:** 2026-06-19

## Naming Patterns

**Functions:**
- Tool handlers: `handle_<tool_name>` with `async def`. Example: `handle_run_prescan()`, `handle_find_competitors()`, `handle_collect_contact()`. All tool handlers must be async.
- Private/helper functions: `_lowercase_underscore`. Example: `_normalize_args()`, `_extract_url_from_message()`, `_build_learnings_prompt()`, `_get_thread_lock()`.
- Mode prompt builders: `_mode_prompt()` where mode is lowercase. Example: `_presale_prompt()`, `_active_prompt()`, `_admin_prompt()`.
- Check functions: `_is_<condition>`. Example: `_is_allowed()` in `shell_exec.py` (`/Users/mikhaileliseev/Desktop/Dev/meAI/AIM/hermes/app/tools/shell_exec.py:68`).

**Variables:**
- Module-level constants: `UPPER_CASE`. Example: `AIM_API_BASE`, `REQUEST_TIMEOUT`, `MAX_LATENCY_SAMPLES`, `_AGENT_TIMEOUT`, `_AGENT_CACHE_TTL`.
- Instance members: `snake_case`. Example: `self._ledgers`, `self.base`, `self._lock`.
- Global singletons: `lowercase_snake`. Example: `token_economy` (`/Users/mikhaileliseev/Desktop/Dev/meAI/AIM/hermes/app/token_economy.py:144`), `_session_db`, `_agent_cache`, `_main_event_loop`.

**Types:**
- Dataclasses used for state objects. Example: `LeadBudget` (`/Users/mikhaileliseev/Desktop/Dev/meAI/AIM/hermes/app/token_economy.py:21-27`).
- Pydantic `BaseModel` for API request/response models. Example: `ChatRequest`, `ChatResponse`, `HealthResponse` (`/Users/mikhaileliseev/Desktop/Dev/meAI/AIM/hermes/app/main.py:163-181`).
- Typed dicts via plain `dict` typed with `dict[str, ...]` annotations.

**Files:**
- Tool files: `snake_case.py` matching tool name. Example: `run_prescan.py`, `find_competitors.py`, `collect_contact.py`.
- Core modules: `snake_case.py`. Example: `agent_wrapper.py`, `token_economy.py`, `voice_transcriber.py`.
- Test files: `test_<module>.py`. Example: `test_deep_research_merge.py`, `test_service_categorizer.py`, `test_presale_flow.py`.
- Router files: `<domain>_api.py` or `<domain>_router.py`. Example: `session_api.py`, `knowledge_router.py`.

## Code Style

**Formatting:**
- No formatter tool detected (no `.prettierrc`, `pyproject.toml` with formatter config, or `eslint.config.*` in Hermes directory).
- Manual indentation uses 4 spaces consistently.
- Docstrings use triple-quote `"""` with a single-line summary, blank line, then details.
- Section separators use `# ── Name ──` comment style with 60-char dashes. Example from `main.py:85`: `# ── Metrics ──` and `agent_wrapper.py:28`: `# ── Persistent session DB (survives container restarts) ──`.

**Linting:**
- No linting tool configuration detected in Hermes directory.
- Pylint/mypy/flake8 not configured.
- Code relies on Python runtime `logging` for observability, not static analysis.

**Line Length:**
- Generally 100-120 characters. No enforced limit.

**Comments:**
- File-level docstrings describe purpose and reference architecture decisions ("Per D-10", "Per Pitfall 2"). Example: `agent_wrapper.py:1-12`.
- Inline comments explain "why" not "what". Example: `agent_wrapper.py:32`: `# Cache is an optimisation, not the source of truth`.
- Architecture decision references use `Per D-NN` or `Per Pitfall N` prefixes consistently across all files.

## Import Organization

**Order (observed pattern):**
1. Standard library imports
2. Third-party imports
3. Local/project imports (frameworks first, then project modules)

**Example from `agent_wrapper.py`:**
```python
# Standard library
import asyncio
import json
import logging
import os
import re
import secrets
import time
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FutureTimeoutError
from datetime import datetime
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)
```

**Example from tool files (`run_prescan.py`):**
```python
import json
import logging
import httpx
from tools.registry import registry

logger = logging.getLogger(__name__)
```

**Path Aliases:**
- No path aliases configured (no `pyproject.toml` with `[tool.pytest.ini_options]` or `setup.py` `package_dir`).
- Internal framework imports use `hermes_state`, `run_agent`, `tools.registry` — these resolve from the hermes-agent package installed in the Docker image.
- Cross-module imports use relative paths: `from .auth import verify_api_key`, `from .agent_wrapper import run_agent`.

**Logging Pattern:**
- Every module defines `logger = logging.getLogger(__name__)` at module level.
- Root logger configured in `main.py` with `INFO` level and format: `"%(asctime)s [%(levelname)s] %(name)s: %(message)s"`.
- `logger.info()` for normal operations, `logger.warning()` for non-critical issues, `logger.error()` for failures, `logger.exception()` inside except blocks for full tracebacks.
- Debug logging via `logger.debug()` used sparingly (mostly in `agent_wrapper.py` for tool extraction details).

## Error Handling

**Primary Pattern — Return JSON error, never raise:**
All tool handlers return `json.dumps({"error": "..."})` strings rather than raising exceptions. This ensures the LLM always receives a structured response it can reason about. Example from `collect_contact.py:72-117`:
```python
try:
    # ... happy path ...
except httpx.HTTPStatusError as e:
    return json.dumps({
        "error": "AIM API returned an error",
        "status": e.response.status_code,
        "detail": str(e),
    })
except httpx.RequestError as e:
    return json.dumps({
        "error": "Cannot reach AIM API",
        "detail": str(e),
    })
except Exception as e:
    logger.exception("Unexpected error in tool handler")
    return json.dumps({
        "error": "Unexpected error in tool handler",
        "detail": str(e),
    })
```

**Three-layer error handling (standard in all tool handlers):**
1. `httpx.HTTPStatusError` — known API error responses (4xx, 5xx)
2. `httpx.RequestError` — network-level failures (timeout, connection refused)
3. `Exception` — catch-all for unexpected errors (with `logger.exception()` for full traceback)

In 16 tool files, there are **69 occurrences** of `json.dumps({"error": ...})` — indicating this is the universal tool error response pattern.

**Edge case: shell_exec.py — Command validation before execution:**
The `shell_exec` tool (`/Users/mikhaileliseev/Desktop/Dev/meAI/AIM/hermes/app/tools/shell_exec.py:68-95`) validates commands against an allowlist BEFORE execution. It uses both an allowed-prefix whitelist (curl, cat, grep, ls, find, python3 -c, etc.) and a blocked-pattern blacklist (rm, kill, sudo, chmod, `>`, `| sh`, etc.). Rejected commands return `{"error": "Command rejected: <reason>"}`.

**Wrapper-level error handling (`agent_wrapper.py`):**
- `run_agent_sync()` wraps the AIAgent call in `ThreadPoolExecutor` with `future.result(timeout=_AGENT_TIMEOUT=900s)`. On timeout, it returns a user-facing apology message (not the raw exception). Also handles the race condition where the future completes at the exact instant the timeout fires.
- `run_agent()` adds a second layer of `asyncio.wait_for(timeout=_AGENT_TIMEOUT+10)`.
- `_try_extract_learnings()` wraps its learning extraction in a try/except that logs warnings but NEVER propagates errors — learning failures must not break the main conversation.

**Key error handling conventions:**
- Tool handlers NEVER raise exceptions — they return error JSON.
- HTTP-level errors are always logged: `logger.error("AIM API returned error: %s", e)` or `logger.exception("...")`.
- Catch-all Exception blocks always include `logger.exception()` to preserve stack traces.
- API timeout values are declared as module-level constants (e.g., `REQUEST_TIMEOUT = 300.0`).
- Fallback patterns: `run_prescan.py` falls back to `_legacy_prescan()` when the staged endpoint returns 404 (`/Users/mikhaileliseev/Desktop/Dev/meAI/AIM/hermes/app/tools/run_prescan.py:72-76`).

## Logging

**Framework:** Python `logging` module. No third-party logging framework.

**Configuration:** Set once in `main.py:13-17`:
```python
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    stream=sys.stdout,
)
```

**Patterns:**
- Always use `logger.info()` for tracing tool execution: `"Running staged prescan for URL: %s", url`
- Use `%s` printf-style formatting (not f-strings) in logging calls.
- Progress reporting via `push_tool_progress()` function — a thread-safe mechanism that pushes events to an `asyncio.Queue` for SSE streaming, with fallback to `logger.info()` when no active queue.

## Argument Handling Convention

**Dict-first parameter unpacking:**
All tool handlers accept their first parameter as either a direct value or a dict (because hermes-agent v0.14.0 passes arguments as a single dict). The `_normalize_args()` helper is used for handlers with multiple parameters. Example from `collect_contact.py:58-59`:
```python
unpacked = _normalize_args(contact_type, {
    "contact_type": "", "contact_value": "", "website": "", "name": "", "source": "web_chat"
})
```

For single-parameter handlers, a simpler pattern is used (`run_prescan.py:46-47`):
```python
if isinstance(url, dict):
    url = url.get("url", "")
```

**URL normalization:**
Every tool that accepts a URL validates it:
```python
if not url or not isinstance(url, str):
    return json.dumps({"error": "url is required"})
if not url.startswith(("http://", "https://")):
    url = "https://" + url
```

## Tool Registration Pattern

Every tool file ends with a `registry.register()` call at module level. Registration includes:
- `name`: tool name string
- `toolset`: which toolset it belongs to ("aim-operations" for business tools, "hermes-debug" for system tools)
- `schema`: OpenAI-compatible function schema with `type`, `function.name`, `function.description`, `function.parameters`
- `handler`: the async handler function
- `check_fn`: lambda returning bool (always `lambda: True`)
- `is_async`: `True` for all tools
- `description`: short one-liner
- `emoji`: decorative emoji for UI

Example pattern from `run_prescan.py:481-517`:
```python
registry.register(
    name="run_prescan",
    toolset="aim-operations",
    schema={...},
    handler=handle_run_prescan,
    check_fn=lambda: True,
    is_async=True,
    description="3-stage intelligence pipeline...",
    emoji="🔎",
)
```

## SKILL.md Format Conventions

SKILL.md files are LLM-readable instruction documents stored under `skills/<skill-name>/SKILL.md`. They follow a specific format observed across the codebase:

**YAML Frontmatter (required):**
```yaml
---
name: deep-research-phase-0
version: 1.0.0
description: >
  ...
metadata:
  version: 1.0.0
  author: AIM
  depends_on: ...
---
```

**Structure:**
1. **Purpose section** — explains what the skill does and when to load it
2. **Iron Rules** — numbered, non-negotiable constraints (e.g., "Iron Rule 1 — No Confirmation Gates")
3. **Step-by-step instructions** — explicit numbered steps with exact commands/queries to use
4. **Execution Log with `[ ]` checkboxes** — the `client-onboarding-pipeline/SKILL.md` (`/Users/mikhaileliseev/Desktop/Dev/meAI/AIM/hermes/skills/client-onboarding-pipeline/SKILL.md`) uses this most explicitly: each phase has an "Execution Log" section with `[ ]` checkboxes that Hermes must check off. If a checkbox remains empty (`[ ]`), the phase is incomplete:
```markdown
### Execution Log
- [ ] Analyse website (quick_overview)
- [ ] Run prescan
- [ ] Present competitors
```
This is described as: "Этот скилл — не справочник. Это чек-лист."

5. **Error Handling table** — markdown table with situation/action columns (`deep-research-phase-0/SKILL.md:492-501`)
6. **Version History table** — markdown table with version/date/changes columns
7. **Forbidden patterns** — uses `❌` for forbidden actions, `✅` for allowed/correct actions
8. **FULL AUTO MODE declarations** — explicit lists of what NOT to do (e.g., "Никогда не спрашивай разрешения")
9. **Model routing instructions** — specifies which model to use for which phase (e.g., "Flash for Phase 0-3, Pro for Phase 4")

**Versioning:** Semantic versioning (MAJOR.MINOR.PATCH). Observed versions: `v3.3.0`, `v5.5.0`, `v1.0.0`.

## Configuration Management

**Primary:** `.env` file at `/opt/data/.env` (server). Contains all API keys and runtime settings. Never committed.

**Secondary:** `config.yaml` at `/opt/data/config.yaml` (server) — referenced in `rotate_keys.py` (`/opt/hermes-data/scripts/rotate_keys.py:39`).

**Key environment variables (from code references, NOT actual values):**
- `HERMES_API_KEY` — Bearer token for Next.js to Hermes communication
- `OMNIROUTE_URL` / `OMNIROUTE_AUTH` — LLM provider endpoint
- `LLM_MODEL` — model identifier (e.g., `ds/deepseek-v4-pro`)
- `HERMES_HOME` — data directory (`/opt/data`)
- `DATABASE_URL` — SQLite connection string
- `TELEGRAM_WEBHOOK_URL` — optional Telegram webhook
- Pooled API keys: `APIFY_API_TOKEN`, `APIFY_API_TOKEN_01` through `_13`, `FIRECRAWL_API_KEY`, `FIRECRAWL_API_KEY_01` through `_14`
- Single API keys: `BRAVE_API_KEY`, `DEEPSEEK_API_KEY`, `ANTHROPIC_API_KEY`, `PERPLEXITY_API_KEY`, `ASSEMBLYAI_API_KEY`, `AHREFS_API_KEY`, `SEMRUSH_API_KEY`

**Key rotation:** `rotate_keys.py` (`/opt/hermes-data/scripts/rotate_keys.py`) manages API key rotation for Apify (14 keys) and Firecrawl (15 keys). Tests each key's validity via HTTP health checks, writes rotation state to `/opt/data/keys/rotation_state.json`, and preserves all non-rotated env vars on write. Services with single keys get health-check-only treatment.

**Docker config:** `Dockerfile` (`/Users/mikhaileliseev/Desktop/Dev/meAI/AIM/hermes/Dockerfile`) sets defaults:
```dockerfile
ENV HERMES_HOME=/opt/data
ENV PYTHONUNBUFFERED=1
ENV HERMES_CONFIG_QUIET=1
```

## Module Design

**Exports:** No explicit `__all__` in most modules. Tools module uses:
```python
__all__ = ["register_all_tools", "register_debug_tools"]
```

**Barrel Files:** `app/tools/__init__.py` (`/Users/mikhaileliseev/Desktop/Dev/meAI/AIM/hermes/app/tools/__init__.py`) serves as the central tool registration point. It imports tool modules in groups (Phase 0, 1, 2, 3, Sales/CRM) with each import wrapped in `_import_tool()` which catches and logs errors from any individual tool that fails to load.

**Functions exported to LLM:** Only functions registered via `registry.register()` are exposed to the LLM. Other functions in tool files remain internal.

## Threading Model

- **FastAPI async endpoints** use `asyncio` event loop.
- **AIAgent calls** are synchronous and wrapped in `loop.run_in_executor()` (thread pool) for web, or `ThreadPoolExecutor` for Telegram/sync paths.
- **Per-session locking**: `asyncio.Lock` for async (web), `threading.Lock` for sync (Telegram). Both exist in `agent_wrapper.py`.
- **Thread-safe progress dispatch**: `push_tool_progress()` uses `loop.call_soon_threadsafe(queue.put_nowait, event)` to safely cross from tool thread to event loop.
- **Global singleton state**: `token_economy` uses `threading.Lock` for its in-memory dict.

---

*Convention analysis: 2026-06-19*
