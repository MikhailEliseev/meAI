# Architecture Audit — 2026-06-19

Full landscape discovered during skill extraction from SOUL.md.

## MCP Servers (3)

| Server | Transport | Key Tools |
|--------|-----------|-----------|
| Firecrawl | npx firecrawl-mcp | scrape, search, crawl, map, agent, extract, interact, monitors |
| Apify | npx @apify/actors-mcp-server | search_actors, call_actor, dataset/storage ops |
| Novamira | WordPress | file ops, WP-CLI, Gutenberg blocks, PHP execute |

## AIM API (app:8000) — 8+ endpoints

```
POST /api/presale/prescan-staged       — 3-stage clinic reconnaissance
POST /api/hermes/orchestrate            — unified orchestrator (ALIVE, partial impl)
POST /api/competitors/find              — competitor discovery
POST /api/competitors/save              — persist competitor list (requires lead_id)
POST /api/competitors/analyze           — CI deep analysis (broken: meai module)
POST /api/competitors/analyze/stream    — streaming variant (same meai bug)
POST /api/seo/audit                     — SEO analysis
POST /api/content/analyze              — Content analysis
GET  /api/companies/financials?inn=X    — FNS financial data
POST /api/performance/cache/clear       — analytics cache only
GET  /api/company-profiles/by-url       — unreliable (500/empty)
GET  /health                            — returns {"status":"healthy"}
```

## Hermes Tools (/opt/hermes/app/tools/) — 19 files

Core pipeline: `orchestrate.py`, `find_competitors.py`, `present_competitors.py`, `find_company_financials.py`, `collect_contact.py`, `publish_scout_report.py`, `quality_gate.py`, `quick_overview.py`

Infrastructure: `rotate_api_key.py`, `firecrawl_key_bank.py`, `firecrawl_web.py`, `external_api.py`

Other: `bitrix_scraper.py`, `deep_research_merge.py`, `escalate_to_manager.py`, `finalize_research.py`, `geo_optimizer_tools.py`, `get_lead_pipeline.py`, `qualify_lead.py`

## Skills Architecture

- **Location**: `/opt/hermes/skills/` (configured as `skills.external_dirs`)
- **Sync**: bidirectional with `/opt/data/skills/` — creates duplicates causing `skill_view` ambiguity
- **Workaround**: `skills_list` works; `skill_view` with bare names fails on duplicates

### Current skills (2): aim-operations (75 lines), client-onboarding-pipeline (~400 lines)

### SOUL.md status: ~800 lines of pipeline still in system prompt — duplicates skill

## Key Findings

1. **orchestrate.py is ALIVE** — endpoint responds. `knowledge_query` returns `not_implemented`.
2. **ci-analysis-fallback needed** — `/api/competitors/analyze` broken (meai module).
3. **Skill sync duplicates** — deletion from one propagates to other.
4. **Missing skills**: seo-audit, content-analysis, ads-reporting, design-system, api-key-rotation.
