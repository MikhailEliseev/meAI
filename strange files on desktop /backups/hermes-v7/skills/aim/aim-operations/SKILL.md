---
name: aim-operations
description: Operational tasks for the AIM platform (iamaim.ru) — cache management, client data clearing, API quirks, database access patterns, CI analysis fallback.
triggers:
  - "почисть кеш"
  - "удали историю сборов"
  - "сбрось данные клиента"
  - "clear cache for <client>"
  - "reset <client> data"
  - "новый сбор"
  - "полный пайплайн"
  - Working with AIM API (app:8000) for maintenance
  - CI/competitor analysis when API is broken
---

# AIM Operations

Operational know-how for managing the AIM marketing agency platform (app:8000).

## Cache & Data Management

### Prescan cache

The prescan tool calls `POST /api/presale/prescan-staged`. Cached results return `cached: true`. To force refresh:
```bash
curl -s -X POST "http://app:8000/api/presale/prescan-staged" \
  -H "Content-Type: application/json" \
  -d '{"url": "https://clinic.ru", "force_refresh": true}' --max-time 300
```
Prescan takes 200-300 seconds with force_refresh. Use background mode with `notify_on_complete: true`.

There is **no dedicated cache-clear endpoint for prescan**. To clear: force_refresh overwrites old data, or delete local `/opt/data/reports/<slug>/` files.

### Analytics cache

`POST /api/performance/cache/clear` — only clears analytics response cache. Does NOT clear prescan or competitor data. Returns `{"cleared": N}`.

### Local report cache

Reports stored at `/opt/data/reports/<slug>/`:
- `report.html` — generated CP
- `data.json` — structured data from all phases

Delete with `rm -rf /opt/data/reports/<slug>/`.

### Pitfalls

- **`/api/competitors/analyze` fails with `"No module named 'meai'"`** — internal AIM API module not installed on app:8000. Fall back to manual CI analysis (see `references/ci-analysis-fallback.md`).
- **`/api/competitors/find` may time out silently** — exit code 28, no output. Use prescan stage_3 `nearby_competitors[]` as competitor list.
- **`/api/competitors/save` requires `lead_id`** — skip in admin-run pipelines where no lead exists.
- **`/api/competitors/analyze/stream`** — same `meai` error as non-stream. Requires `specialization`, `services`, `competitors` fields (NOT `named_competitors`).
- **Firecrawl `ClosedResourceError`** — rate limiting on parallel scrapes. Max 3 parallel; fall back to `web_extract` for remaining sites.
- **Prescan `force_refresh: true` takes 200-300 sec** — use background mode with `notify_on_complete`.
- **`orchestrate` endpoint** — `/api/hermes/orchestrate` EXISTS and responds (verified 2026-06-19). Some operations return `not_implemented` (knowledge_query). Use `orchestrate.py` Hermes tool as primary interface; fall back to direct curl for unimplemented operations.
- **`/api/company-profiles/by-url`** — may return `Internal Server Error` or empty. Not reliable for checking cached state.

## Full Pipeline (Admin Mode)

For a fresh collection on a clinic URL:

1. **Prescan**: `POST /api/presale/prescan-staged` with `force_refresh: true`
2. **Financials**: `GET /api/companies/financials?inn=<INN>`
3. **Competitors**: if `/api/competitors/find` times out, use prescan `nearby_competitors[]`
4. **CI Analysis**: if `/api/competitors/analyze` fails with `meai` error → manual fallback (see `references/ci-analysis-fallback.md`)
5. **CP Generation**: build HTML using AIM design system (dark theme: black + gold `#c9a96e`, fonts `Playfair Display` + `Jost`, glass CSS classes)

## Database Access

The AIM API uses its own internal database (not directly accessible from Hermes host). The Hermes host has:
- `/opt/data/state.db` — Hermes session DB (not AIM data)
- `/opt/data/kanban.db` — Hermes task DB (not AIM data)

## See also

- `references/ci-analysis-fallback.md` — manual CI analysis when AIM competitor API is broken.
- `references/architecture-audit-2026-06-19.md` — full tool landscape, API endpoints, MCP servers, Hermes tools.
- `aim/client-onboarding-pipeline` — full presale pipeline (prescan → CP → handoff).
