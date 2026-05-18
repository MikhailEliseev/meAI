# Roadmap: meAI → AIM Agency

## Overview

meAI — CEO-архитектор, который строит **AIM** (AI-first medical marketing agency at iamaim.ru). Проект проходит путь от создания фреймворка (meAI core) через построение агентской инфраструктуры (AIM) к production-ready системе с клиентским захватом (Phase 11), деплоем (Phase 12) и маркетингом (Phase 13).

Три слоя: Architect (Strategy) → Operator (Tactical) → Agents (Execution). Фреймворк переиспользуется агентством. Все Obsidian vaults следуют LLM Wiki Pattern (Karpathy). Российский рынок: ФЗ-152 вместо HIPAA, ЮKassa вместо Stripe, Контур.Диадок вместо DocuSign.

## Milestones

- ✅ **v1.0 Foundation** — Phases 1-7 (shipped 2026-05-11)
- ✅ **v1.1 Agency Operations** — Phases 7.5-9 (shipped 2026-05-15)
- ✅ **v2.0 AI Enhancement** — Phase 10 (shipped 2026-05-16)
- ✅ **v2.1 Client Acquisition** — Phase 11 (shipped 2026-05-18)
- ✅ **v3.0 Production** — Phase 12 (shipped 2026-05-18)
- 📋 **v3.0 Marketing** — Phase 13 (planned)

## Phases

**Phase Numbering:**
- Integer phases (1, 2, 3): Planned milestone work
- Decimal phases (7.5): Urgent insertions (marked with INSERTED)

<details>
<summary>✅ v1.0 Foundation (Phases 1-7) — SHIPPED 2026-05-11</summary>

### Phase 1: Framework Core
**Goal**: Базовый фреймворк meAI — стратегический слой
**Depends on**: Nothing (first phase)
**Success Criteria** (what must be TRUE):
  1. Architect принимает стратегические решения с обоснованием и confidence score
  2. Decision Maker обучается на истории решений
  3. Orchestrator координирует async операции
  4. Rollback поддерживает snapshot + event replay
**Plans**: 2 plans

Plans:
- [x] 01-01: Core components (Architect, Decision Maker, Orchestrator, Rollback)
- [x] 01-02: Tests and CLI for strategic layer

### Phase 2: Agent System
**Goal**: Тактический и исполнительный слои — Operator + BaseAgent + Factory
**Depends on**: Phase 1
**Success Criteria** (what must be TRUE):
  1. Operator получает задачи, принимает тактические решения, делегирует агентам
  2. BaseAgent реализует execute_task, get_capabilities, learn_from_feedback
  3. Factory создаёт агентов по типу
  4. Поддерживаются стратегии: Direct, Sequential, Parallel, Hybrid
**Plans**: 2 plans

Plans:
- [x] 02-01: Operator implementation with tactical decision making
- [x] 02-02: BaseAgent, Factory, and agent lifecycle

### Phase 3: Infrastructure
**Goal**: Event Bus, Event Store, Database, Obsidian integration
**Depends on**: Phase 2
**Success Criteria** (what must be TRUE):
  1. Event Bus поддерживает P0-P3 приоритеты и async messaging
  2. Event Store — immutable audit log всех событий
  3. Database — SQLAlchemy 2.0 async с миграциями
  4. Obsidian vaults следуют LLM Wiki Pattern (raw/ → wiki/ → schema/)
**Plans**: 2 plans

Plans:
- [x] 03-01: Event Bus (P0-P3) + Event Store (immutable audit log)
- [x] 03-02: Database layer + Obsidian memory integration

### Phase 4: API & CLI Layer
**Goal**: FastAPI приложение + CLI для управления системой
**Depends on**: Phase 3
**Success Criteria** (what must be TRUE):
  1. FastAPI app с health checks и metrics endpoints
  2. CLI команды для Architect, Operator, тестирования
  3. Agent creation scripts (aim_cli, create_aim_agency)
**Plans**: 2 plans

Plans:
- [x] 04-01: FastAPI application with endpoints
- [x] 04-02: CLI tools (aim_cli, use_architect, test scripts)

### Phase 5: SEO Foundation
**Goal**: Keyword Research Agent — API clients с resilience patterns
**Depends on**: Phase 4
**Success Criteria** (what must be TRUE):
  1. SEMrush client с circuit breaker, retry, rate limiting, caching
  2. Ahrefs client как fallback provider
  3. Pydantic schemas для валидации API ответов
  4. Budget control и cost tracking
  5. 27 tests passing
**Plans**: 2 plans

Plans:
- [x] 05-01: API clients layer (SEMrush, Ahrefs) with resilience patterns
- [x] 05-02: Data validation schemas + test suite (27 tests)

### Phase 6: Content & Ads Foundation
**Goal**: Content Agent + Ads Agent базовые реализации
**Depends on**: Phase 5
**Success Criteria** (what must be TRUE):
  1. Content Agent генерирует, редактирует, оптимизирует контент
  2. Ads Agent создаёт кампании, оптимизирует бюджет, A/B тестирует
  3. Оба агента интегрированы с Event Bus и Obsidian vaults
**Plans**: 2 plans

Plans:
- [x] 06-01: Content Agent with generation and editing capabilities
- [x] 06-02: Ads Agent with campaign management

### Phase 7: Agency Setup
**Goal**: AIM agency structure — Magisters, vaults, data layer
**Depends on**: Phase 6
**Success Criteria** (what must be TRUE):
  1. SEO, Content, Ads Magisters созданы и функционируют
  2. Agent vaults в AIM/obsidian/ с LLM Wiki Pattern
  3. AIM data layer с базой агентства
  4. Agency creation and testing scripts работают
**Plans**: 2 plans

Plans:
- [x] 07-01: Magisters (SEO, Content, Ads) + agency vaults
- [x] 07-02: Agency data layer + creation scripts

</details>

### Phase 7.5: Linear Integration (INSERTED)
**Goal**: Интеграция с Linear для task tracking — AIM как Project #0
**Depends on**: Phase 7
**Success Criteria** (what must be TRUE):
  1. GraphQL API client для Linear (479 lines)
  2. 7 CLI команд для управления задачами
  3. Двусторонняя синхронизация задач
**Plans**: 1 plan

Plans:
- [x] 07.5-01: Linear GraphQL client + CLI commands + tests

<details>
<summary>✅ v1.1 Agency Operations (Phases 8-9) — SHIPPED 2026-05-15</summary>

### Phase 8: Multi-Tenant Frontend
**Goal**: Next.js 14+ фронтенд с мульти-тенантностью
**Depends on**: Phase 7.5
**Success Criteria** (what must be TRUE):
  1. Next.js 14+ App Router с Tailwind CSS 4
  2. NextAuth.js для аутентификации
  3. Tenant isolation middleware
  4. RBAC (role-based access control)
**Plans**: 2 plans

Plans:
- [x] 08-01: Next.js app shell + auth + tenant middleware
- [x] 08-02: Dashboard layouts + RBAC components

### Phase 9: Agency Operations
**Goal**: Project Templates, Automated Reporting, Dashboards, Knowledge Base
**Depends on**: Phase 8
**Success Criteria** (what must be TRUE):
  1. Project templates для типовых медицинских проектов
  2. Automated reporting (weekly, monthly, quarterly)
  3. Analytics dashboards (SEO, Content, Ads performance)
  4. Knowledge base с LLM Wiki Pattern
**Plans**: 3 plans

Plans:
- [x] 09-01: Project templates system
- [x] 09-02: Automated reporting engine
- [x] 09-03: Dashboards + knowledge base

</details>

<details>
<summary>✅ v2.0 AI Enhancement (Phase 10) — SHIPPED 2026-05-16</summary>

### Phase 10: AI Enhancement
**Goal**: LLM Orchestrator, Ad Copy Generator, Predictive Analytics, Magisters Integration
**Depends on**: Phase 9
**Success Criteria** (what must be TRUE):
  1. LLM Orchestrator управляет несколькими AI провайдерами (Claude, GPT, Gemini)
  2. SEO Analyzer с глубоким анализом страниц
  3. Ad Copy Generator с A/B вариантами и tone of voice
  4. Predictive Analytics для прогнозирования кампаний
  5. Magisters интегрированы с AI компонентами
**Plans**: 5 plans

Plans:
- [x] 10-01: LLM Orchestrator (multi-provider AI management)
- [x] 10-02: SEO Analyzer (deep page analysis)
- [x] 10-03: Ad Copy Generator (variants + tone of voice)
- [x] 10-04: Predictive Analytics (campaign forecasting)
- [x] 10-05: Magisters Integration (connect AI to agency layer)

</details>

### ✅ v2.1 Client Acquisition (Shipped 2026-05-18)

**Milestone Goal:** Полный цикл захвата клиентов: landing page → lead capture → AI scoring → onboarding → payment → analytics

### Phase 11: Client Acquisition
**Goal**: Landing Page, Lead Generation, Payment & Onboarding, Testing & Launch
**Depends on**: Phase 10
**Success Criteria** (what must be TRUE):
  1. Landing page с конверсией >3% (deferred to Phase 13)
  2. AI Lead Scoring с 30+ факторами и Linear интеграцией
  3. Automated Onboarding с AI document processing (OCR + NLP)
  4. Payment processing (ЮKassa stub → real in Phase 12)
  5. Email automation workflows (Hot/Warm/Cold tiers)
  6. Real-time analytics и reporting
  7. Все E2E потоки работают, 388-403 тестов проходят
  8. ФЗ-152 compliance verified
**Plans**: 4 sprints

Plans:
- [ ] 11-01: Sprint 1 — Landing Page (DEFERRED to Phase 13)
- [x] 11-02: Sprint 2 — Lead Generation (192 tests passing)
- [x] 11-03: Sprint 3 — Payment & Onboarding (146 tests passing)
- [x] 11-04: Sprint 4 — Testing & Launch (77 tests, 50h)


### ✅ v3.0 Production (Shipped 2026-05-18)

**Milestone Goal:** Production-ready система на российском рынке с полным compliance

### Phase 12: Production Deployment ✅
**Goal**: Замена stubs на реальные сервисы, деплой в Yandex Cloud
**Depends on**: Phase 11
**Success Criteria** (what must be TRUE):
  1. ЮKassa integration (замена Helcim stub)
  2. Контур.Диадок integration (замена DocuSign stub)
  3. PostgreSQL migration (from SQLite)
  4. Deploy to Yandex Cloud / VK Cloud
  5. Production monitoring и alerting
  6. ФЗ-152 полный compliance
**Plans**: TBD

Plans:
- [x] 12-01: ЮKassa + Контур.Диадок real integrations
- [x] 12-02: PostgreSQL migration + production deploy
- [x] 12-03: Production monitoring, alerting, runbooks

### Phase 13: Landing Page & Marketing
**Goal**: Реализация landing page (deferred из Phase 11 Sprint 1) + запуск маркетинга
**Depends on**: Phase 12
**Success Criteria** (what must be TRUE):
  1. Landing page с конверсией >3%
  2. SEO оптимизация landing page
  3. Интеграция с lead capture (Phase 11)
  4. Запуск маркетинговых кампаний
  5. Аналитика и A/B тестирование
**Plans**: TBD

Plans:
- [x] 13-01: Landing page implementation (from Phase 11 Sprint 1)
- [ ] 13-02: Marketing campaigns launch + analytics (deferred — post-MVP)

### Phase 14: Final Integration — Operability & Client Dashboard
**Goal**: Закрыть оставшиеся gaps: LinearMixin на всех Magisters, клиентский веб-дашборд
**Depends on**: Phase 13
**Success Criteria** (what must be TRUE):
  1. LinearMixin работает на всех Magisters (SEO, Content, Ads, Analytics)
  2. update_linear_status() реально вызывает LinearClient API (не no-op)
  3. Клиентский веб-дашборд: layout + /dashboard/tasks + /api/dashboard/progress
  4. Убраны все hardcoded mock-данные из billing/contracts/onboarding
  5. Навигация между страницами дашборда работает
**Plans**: 2 plans

Plans:
- [x] 14-01: Finish LinearMixin → all Magisters + fix update_linear_status()
- [x] 14-02: Client web dashboard (layout, tasks page, progress API, de-mock)

## Progress

**Execution Order:**
Phases execute in numeric order: 7 → 7.5 → 8 → 9 → 10 → 11 → 12 → 13 → 14

| Phase | Milestone | Plans Complete | Status | Completed |
|-------|-----------|----------------|--------|-----------|
| 1. Framework Core | v1.0 | 2/2 | Complete | 2026-05-09 |
| 2. Agent System | v1.0 | 2/2 | Complete | 2026-05-09 |
| 3. Infrastructure | v1.0 | 2/2 | Complete | 2026-05-10 |
| 4. API & CLI | v1.0 | 2/2 | Complete | 2026-05-10 |
| 5. SEO Foundation | v1.0 | 2/2 | Complete | 2026-05-10 |
| 6. Content & Ads | v1.0 | 2/2 | Complete | 2026-05-11 |
| 7. Agency Setup | v1.0 | 2/2 | Complete | 2026-05-11 |
| 7.5. Linear Integration | v1.1 | 1/1 | Complete | 2026-05-13 |
| 8. Multi-Tenant Frontend | v1.1 | 2/2 | Complete | 2026-05-14 |
| 9. Agency Operations | v1.1 | 3/3 | Complete | 2026-05-15 |
| 10. AI Enhancement | v2.0 | 5/5 | Complete | 2026-05-16 |
| 11. Client Acquisition | v2.1 | 3/4 | Complete | 2026-05-18 |
| 12. Production Deployment | v3.0 | 3/3 | Complete | 2026-05-18 |
| 13. Landing Page | v3.0 | 1/2 | In progress | 2026-05-18 |
| 14. Final Integration | v3.0 | 2/2 | Complete | 2026-05-18 |

**Overall:** 32/33 plans complete (97%)
