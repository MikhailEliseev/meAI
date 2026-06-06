---
gsd_state_version: 1.0
milestone: v2.1
milestone_name: Client Acquisition
status: in_progress
stopped_at: Phase 28 Plan 01 complete. Deep Research Phase 0 created.
last_updated: "2026-06-06T13:51:35.857Z"
last_activity: 2026-06-06
progress:
  total_phases: 22
  completed_phases: 16
  total_plans: 51
  completed_plans: 26
  percent: 91
---

# Project State

## Project Reference

See: .planning/ROADMAP.md (updated 2026-05-19)

**Core value:** AI-first medical marketing agency at iamaim.ru — полный цикл захвата клиентов
**Current focus:** Milestone complete

## Current Position

Phase: 28
Plan: 28-01 (complete)
Status: In progress — Deep Research Phase 0
Last activity: 2026-06-06

Progress: [████████░░] 91%

## Performance Metrics

**Velocity:**

- Total phases: 18
- Total plans executed: 49

**By Phase:**

| Phase | Plans | Status |
|-------|-------|--------|
| 1-7. Foundation | 13 | Complete ✅ |
| 7.5. Linear | 1 | Complete ✅ |
| 8-9. Operations | 5 | Complete ✅ |
| 10. AI Enhancement | 5 | Complete ✅ |
| 11. Client Acquisition | 4 sprints | Complete ✅ (Sprints 2-4 done; Sprint 1 → Phase 13) |
| 12. Production Deployment | 3 | Complete ✅ (ЮKassa, Контур.Диадок, Deploy+Monitoring) |
| 13. Landing Page | 4 | 2/4 done (13-01, 13-04), 2 pending (13-02, 13-03) |
| 14. Frontend | 2 | Complete ✅ (97% — 32/33 plans) |
| 15. Hermes AIM Integration | 4 | Complete ✅ (SOUL.md, tools, FastAPI, docker-compose, Telegram, мониторинг) |
| 16. Hermes Knowledge Training | 2 | Complete ✅ (SOUL.md 753 lines, 22/22 checks pass) |
| 17. No More Mock Data | 1 | Complete ✅ (deprecated files removed, import hygiene guard, 15/15 CI tests) |
| 18. Hermes Knowledge Bus | 2 | Complete ✅ (EventBus listener, TeacherSync, knowledge endpoints, LLM ingest) |
| 19. Competitor Discovery Quality | 1 | Complete ✅ (8 fixes across 4 files: name scoring, services, specialization, social links) |
| 20. Apify Competitor Intelligence | 1 | Complete ✅ (Google Maps Scraper + ApifyKeyPool + bugfixes + tests) |
| 21. CI Pipeline Unification | 5 | Complete ✅ (EventBus delegation, unified models, CiMarketingAnalyzer thin proxy, 49/49 tests) |
| 28. Deep Research Phase 0 | 1 | 1/1 done (28-01), deployment deferred |

*Updated 2026-06-06*

## Pending Plans (Phase 13)

### Wave 2 (depends on 13-04 — done ✅)

- **13-02**: Fix Yandex Direct MOCK stats via TSV parsing + ФЗ-38 compliance + tests + DB sync — 4 tasks
- **13-03**: VK Ads client + Telegram Ads client + tests + DB sync — 4 tasks

**Total:** 8 tasks across 2 plans
**Required tokens:** YANDEX_DIRECT_TOKEN, VK_ADS_TOKEN

### Decisions

- **Phase 11 Sprint 1 (Landing Page)**: Deferred to Phase 13 → Completed (35/35 tests)
- **ФЗ-152 compliance**: AES-256-GCM field-level encryption, consent tracking, 7-year retention
- **Russian market**: ЮKassa (async_yookassa), Контур.Диадок, SendGrid for email
- **Phase 7.5**: Inserted between Phases 7 and 8 — Linear integration
- **Sprint structure**: Phase 11 used 4 sprints (200h total)
- **Hermes**: Phase 15 replaced DeepSeek with Hermes AIAgent via OmniRoute
- **Telegram**: Hybrid Bot API (incoming) + Telethon (outgoing) gateway
- **Phase 28 Deep Research Phase 0**: Mandatory pre-flight intelligence inserted BEFORE Phase 1. Three-tier doctor classification (star/core/team). Python helper for JSON merge. Phase renumbering from old P0→P1, P1→P2 etc. Server deployment deferred (server DOWN).

### Pending Todos

None — all phases complete.

### Blockers/Concerns

None — infrastructure ready for production deploy.

- `HERMES_API_KEY` must be generated on server: `openssl rand -hex 32`
- `TELEGRAM_BOT_TOKEN`, `TELEGRAM_API_ID`, `TELEGRAM_API_HASH` must be set in .env.production
- `YOOKASSA_SHOP_ID` and `YOOKASSA_SECRET_KEY` must be set for real payments

## Deferred Items

| Category | Item | Status | Deferred At |
|----------|------|--------|-------------|
| Sprint | Landing Page (Phase 11 Sprint 1) | ✅ Completed in Phase 13 | 2026-05-15 |
| Integration | ЮKassa real (Helcim stub) | ✅ Completed in Phase 12 | 2026-05-16 |
| Integration | Контур.Диадок real (DocuSign stub) | ✅ Completed in Phase 12 | 2026-05-16 |
| Database | PostgreSQL migration | ✅ Completed in Phase 12 | 2026-05-16 |

## What's Built

### Landing & Client Acquisition

- Landing page: Hero, TrustBadges, CaseStudies, Testimonials, Awards, ProcessSteps, FAQ, ContactForm
- Sales chat: SalesChat, ChatBubble, ChatInput, UTMCapture
- Lead capture: extraction, validation, encrypted storage, dossier management
- AI Lead Scoring: 30+ factors, real-time scoring, tier classification
- Email automation: SendGrid sequences, queue, retry

### Payment & Onboarding

- YooKassa integration: redirect flow, webhooks, IP validation
- Payment UI: billing page, payment form
- Onboarding: AI document processing, workflow automation
- Контур.Диадок: electronic document signing

### AI Operations (Hermes)

- Operator identity: SOUL.md with 3 modes (PRESALE/ACTIVE/ADMIN)
- 8 Hermes tools: SEO audit, content analysis, ads report, project status, lead capture, lead list, Telegram search, Telegram send
- FastAPI wrapper: /api/chat, /health, /metrics
- Next.js chat proxy: retry + Redis fallback
- Telegram gateway: Bot API webhook + Telethon MCP tools
- EventBus listener: execution → raw/executions/ knowledge capture
- TeacherSync pipeline: external research → wiki/patterns/ enrichment

### Marketing & Analytics

- A/B testing engine: scipy-based chi² significance, sample size calculation, experiment tracking
- Attribution pipeline: UTM → campaign matching via EventBus, lead→revenue tracking
- ROI calculator: ROAS/ROI per channel, aggregated reports
- A/B variant middleware: Next.js Edge, 50/50 split, sticky cookie (HttpOnly, SameSite=Lax)

### Infrastructure

- Docker Compose: 12 services (postgres, app, frontend, hermes, redis, nginx, prometheus, grafana, postgres-exporter, alertmanager, node-exporter)
- Monitoring: Prometheus, Grafana, Alertmanager (Telegram + Email alerts)
- HermesDown alert: 60s downtime → critical → Telegram + Email
- CI/CD, health checks, persistent volumes

## Session Continuity

Last session: 2026-06-06T13:50:38Z
Stopped at: Phase 28 Plan 01 complete. Deep Research Phase 0 — all local files created.
Next: Deploy to server when root@138.16.224.188 is back up; verify against server presale-pipeline SKILL.md original.
