---
phase: 15-hermes-aim-integration
plan: 02
type: execute
subsystem: Hermes tools
tags: [hermes, tools, registry, aim-operations, httpx]
depends_on: []
provides: ["aim-operations toolset with 6 tools"]
affects: ["Hermes AIAgent tool calling", "Operator autonomous operations"]
tech-stack:
  added: ["httpx (async HTTP)", "Hermes tools/registry API"]
  patterns: ["Internal registry registration", "Async handler + HTTP error handling"]
key-files:
  created:
    - AIM/hermes/app/tools/__init__.py
    - AIM/hermes/app/tools/run_seo_audit.py
    - AIM/hermes/app/tools/run_content_analysis.py
    - AIM/hermes/app/tools/run_ads_report.py
    - AIM/hermes/app/tools/show_project_status.py
    - AIM/hermes/app/tools/collect_contact.py
    - AIM/hermes/app/tools/show_all_leads.py
  modified: []
decisions:
  - "All 6 tools registered via Hermes INTERNAL registry (tools/registry.py), NOT MCP stdio"
  - "Each handler is async (is_async=True) using httpx.AsyncClient with 30s timeout"
  - "AIM_API_BASE = http://app:8000 for internal Docker network communication"
  - "collect_contact validates contact_type enum at tool level (telegram/email/phone only)"
  - "show_all_leads access control delegated to AIM API layer"
metrics:
  duration: "7m"
  completed_date: "2026-05-19"
  tasks: 2
  files: 7
---

# Phase 15 Plan 02: Custom Hermes AIM Operations Tools Summary

**One-liner:** 6 production-ready Hermes tool handlers that give the Operator real AIM agency capabilities via HTTP calls to AIM API endpoints through the internal Docker network -- all registered in the Hermes internal tool registry under toolset "aim-operations".

## Tasks Executed

### Task 1: Tool Registration Bootstrap (`__init__.py`)

**Commit:** `86960ed`

Created `AIM/hermes/app/tools/__init__.py` with a single `register_all_tools()` function. This function imports all 6 tool modules at FastAPI app startup, triggering their module-level `registry.register()` calls as a side effect. No manual registration needed -- importing is sufficient.

Key design decisions:
- Each tool module self-registers at import time (top-level `registry.register()` call)
- `register_all_tools()` only needs to import the modules -- registration is a side effect
- Toolset name "aim-operations" matches the `enabled_toolsets` list in AIAgent constructor
- Internal registry used, NOT MCP stdio (per RESEARCH.md Pitfall 5)

### Task 2: Six Tool Handler Modules

**Commit:** `6a2d02a`

All 6 tools follow the same architectural pattern:

| Tool | HTTP Method | AIM API Endpoint | Parameters |
|------|------------|-----------------|------------|
| `run_seo_audit` | POST | `/api/seo/audit` | `url` (required) |
| `run_content_analysis` | POST | `/api/content/analyze` | `url` (required), `content_type` (optional) |
| `run_ads_report` | POST | `/api/ads/report` | `project_id` (required), `period` (optional) |
| `show_project_status` | GET | `/api/projects/{id}/status` | `project_id` (required) |
| `collect_contact` | POST | `/api/leads` | `contact_type`, `contact_value` (required), `website`, `name`, `source` (optional) |
| `show_all_leads` | GET | `/api/leads` | `period`, `status` (both optional) |

**Shared implementation characteristics across all 6 tools:**
- Async handlers (`async def`, `is_async=True`)
- `httpx.AsyncClient` with `REQUEST_TIMEOUT=30.0s`
- `AIM_API_BASE = "http://app:8000"` (internal Docker network)
- Three-tier error handling: `HTTPStatusError`, `RequestError`, generic `Exception`
- All responses are `json.dumps(data, ensure_ascii=False, indent=2)` strings
- Structured logging at INFO level (normal) and ERROR level (failures)
- OpenAI function schema in `registry.register()` for LLM tool calling

**collect_contact** additionally validates `contact_type` against an enum (`telegram`, `email`, `phone`) at the tool level before making the HTTP call. Invalid types return an immediate error without hitting the API.

**show_all_leads** access control is delegated to the AIM API layer -- the tool handler makes the request unconditionally, and the API endpoint enforces authorization.

## Threat Model Compliance

All mitigations from the plan's STRIDE threat register are implemented:

| Threat ID | Mitigation | Status |
|-----------|-----------|--------|
| T-15-03 (Spoofing) | Hardcoded `AIM_API_BASE`, URL paths are constants | Implemented |
| T-15-04 (Tampering) | `collect_contact` validates `contact_type` enum | Implemented |
| T-15-05 (Info Disclosure) | `show_all_leads` delegates auth to AIM API | Implemented |
| T-15-06 (DoS) | `REQUEST_TIMEOUT=30.0s` on all HTTP calls | Implemented |
| T-15-07 (Elevation) | No custom auth -- AIM API enforces access control | Implemented |

## Verification Results

All 9 acceptance criteria checked and passing:

- 6/6 tool files exist
- 6/6 call `registry.register()` with `toolset="aim-operations"`
- 6/6 import `from tools.registry import registry`
- 6/6 use `async def handle_*` for handlers
- 6/6 use `AIM_API_BASE = "http://app:8000"`
- 6/6 use `httpx.AsyncClient` for HTTP calls
- 6/6 have `is_async=True` in registration
- 6/6 catch both `HTTPStatusError` and `RequestError`
- 6/6 return JSON strings via `json.dumps`

## Stub Analysis

No stubs detected. All 6 tool handlers make real HTTP calls to AIM API endpoints. Per the plan's guidance on missing endpoints: if an AIM API endpoint is not yet deployed, the tool returns a clear JSON error message (e.g., `{"error": "AIM API returned an error", "status": 404, ...}`) rather than crashing. This is real infrastructure, not mock data -- the behavior is determined at runtime by API availability.

## Deviations from Plan

None -- plan executed exactly as written. The `json.dumps` count verification in the plan expected 7 files (including `__init__.py`), but `__init__.py` legitimately doesn't need `json.dumps` since it only imports modules. The 6 tool handlers all correctly use `json.dumps` for response formatting.

## Architecture Summary

```
Hermes AIAgent (run_agent.py)
  enabled_toolsets=["aim-operations"]
    |
    +-- run_seo_audit        ---> POST http://app:8000/api/seo/audit
    +-- run_content_analysis ---> POST http://app:8000/api/content/analyze
    +-- run_ads_report       ---> POST http://app:8000/api/ads/report
    +-- show_project_status  ---> GET  http://app:8000/api/projects/{id}/status
    +-- collect_contact      ---> POST http://app:8000/api/leads
    +-- show_all_leads       ---> GET  http://app:8000/api/leads
```

All communication happens over the internal Docker network. Tools are available when `register_all_tools()` is called at FastAPI startup (plan 15-03) and `AIAgent` is constructed with `enabled_toolsets=["aim-operations"]`.

## Self-Check: PASSED

- All 7 created files confirmed on disk
- Commits `86960ed` and `6a2d02a` confirmed in git log
