# Session: 2026-05-20

## PRODUCTION DEPLOYED 🚀

**Date:** 2026-05-19 14:20 GMT+3
**Server:** 138.16.224.188
**Domain:** https://iamaim.ru

### Deployed Services (all healthy):
- ✅ aim-app (FastAPI backend)
- ✅ aim-frontend (Next.js 14 — 21 pages)
- ✅ aim-hermes (Hermes AIAgent operator)
- ✅ aim-postgres (PostgreSQL 16)
- ✅ aim-redis (Redis 7)
- ✅ aim-nginx (SSL via Let's Encrypt)
- ✅ aim-prometheus + grafana + alertmanager + postgres-exporter + node-exporter

### All Pages Live (200 OK):
Home, About, Blog, Services, Contact, Privacy Policy, Case Studies, Health endpoint

### Pending:
- ⚠️ Telegram webhook — Telegram DNS ещё не видит iamaim.ru, попробовать позже
- ⚠️ TELEGRAM_API_ID + TELEGRAM_API_HASH — Миша сказал "позже"
- ⚠️ Alertmanager Telegram chat_id + SendGrid API key для реальных алертов
- ⚠️ POSTGRES_PASSWORD warning в docker-compose — косметическое

### Commits (deploy session):
- `c419a3d` fix: commit correct nginx config (frontend routing) + monitoring configs
- `144b6cc` fix: add missing deps (sendgrid, apscheduler), remove duplicates
- `2427cc7` fix: PYTHONPATH should point to /app/AIM/src where aim package lives
- `24c1c1c` fix: add missing web framework deps (fastapi, uvicorn)
- `d0a97e2` fix: add frontend/data JSON files (case-studies, faq)
- `1b80edc` fix: add all untracked frontend files (Phase 14) + fix gitignore lib/ blocking frontend/lib/

### Known issues fixed during deploy:
- Docker build context mismatch (app needed repo root, not AIM/)
- requirements.txt missing core deps (fastapi, uvicorn, sendgrid, apscheduler)
- PYTHONPATH wrong (was /app, should be /app/AIM/src)
- frontend/lib/utils.ts gitignored by AIM/.gitignore lib/ rule
- frontend/data/case-studies.json gitignored by root .gitignore data/ rule
- nginx config on server was old version (all traffic to backend, no frontend routing)
- alertmanager had env var placeholders instead of actual values
- SSL chain.pem symlink missing in ./ssl/

---

## Phase 18: Hermes Learning Bus — Implementation (Plan 18-01)

**Date:** 2026-05-20 10:30 GMT+3
**Status:** Plan 18-01 COMPLETE ✅ (5/5 tasks)

### Completed Tasks:

**Task 1.1: Hermes Knowledge Vault** ✅
- `AIM/hermes/knowledge/__init__.py` — exports HermesKnowledgeVault + LLMIngest
- `AIM/hermes/knowledge/vault.py` (160 lines) — full vault manager
  - ingest_execution(event), ingest_agent_result(event)
  - query_context(domain, action), store_learning(domain, knowledge)
  - get_status(), get_execution(id), get_latest_executions(limit)
- Directory structure: raw/executions/, wiki/patterns/, wiki/learnings/, decisions/rules/

**Task 1.2: EventBus Listener** ✅
- `AIM/hermes/app/main.py` — startup subscribes to ci.execution.* events
  - ci.execution.started → vault.ingest_execution
  - ci.agent.completed → vault.ingest_agent_result
  - ci.execution.completed → vault.ingest_execution

**Task 1.3: CI Orchestrator — execution events** ✅
- `ci_orchestrator.py` — publish 3 event types with correlation_id
  - ci.execution.started (before phases loop)
  - ci.agent.completed (after each agent execution)
  - ci.execution.completed (before return, with summary)
- correlation_id = f"ci-{uuid4().hex[:8]}" for traceability
- Fixed _delegate_to_agent: Event() instead of kwargs
- Added Event import from event_bus

**Task 1.4: Knowledge API Endpoints** ✅
- `AIM/hermes/app/knowledge_router.py` (172 lines) — 5 endpoints
  - POST /api/knowledge/ingest — store execution event
  - GET /api/knowledge/context?domain=&action= — search vault
  - GET /api/knowledge/status — vault health
  - POST /api/knowledge/learn — LLM pattern extraction
  - GET /api/knowledge/search?q=&domain= — full-text search

**Task 1.5: LLM Ingest** ✅
- `AIM/hermes/knowledge/ingest.py` (154 lines) — pattern extraction via OmniRoute
  - extract_patterns(execution_id) — single or "latest"
  - extract_all() — process all unprocessed executions
  - Uses omniroute_direct.chat() for LLM calls
  - Updates wiki/patterns/index.md with entries

### Flow:
```
CI Orchestrator → EventBus.publish(Event) → Hermes.subscribe → vault.ingest_execution
                                                                    ↓
                                                            raw/executions/
                                                                    ↓
                                    POST /api/knowledge/learn → LLMIngest → wiki/patterns/
                                                                    ↓
                        Magisters → GET /api/knowledge/context → enriched task
```

### Next: Plan 18-02 (Teacher↔Hermes + Magisters context + Activation)
- Task 2.1: Teacher → Hermes sync (teacher_sync.py)
- Task 2.2: Magisters → Hermes context query (hermes_context.py)
- Task 2.3: Activation Sequence doc (DONE — ACTIVATION_SEQUENCE.md)
- Task 2.4: Health endpoint with knowledge loop monitoring
- Task 2.5: Tool Training Guide (DONE)
