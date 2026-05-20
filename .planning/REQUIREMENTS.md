# Requirements: meAI → AIM Agency

**Defined:** 2026-05-18
**Core Value:** AI-first medical marketing agency — полный цикл от захвата клиентов до автоматизированного маркетинга

## v1 Requirements

Requirements for full agency operation. Each maps to roadmap phases.

### Framework Core

- [x] **FRMW-01**: Architect принимает стратегические решения с confidence score и обоснованием
- [x] **FRMW-02**: Decision Maker обучается на истории решений для улучшения качества
- [x] **FRMW-03**: Orchestrator координирует async операции между компонентами
- [x] **FRMW-04**: Rollback поддерживает snapshot + event replay для восстановления

### Agent System

- [x] **AGNT-01**: Operator получает задачи и принимает тактические решения
- [x] **AGNT-02**: Operator делегирует задачи агентам через Event Bus
- [x] **AGNT-03**: Agent Factory создаёт агентов по типу (SEO, Content, Ads)
- [x] **AGNT-04**: Поддерживаются стратегии: Direct, Sequential, Parallel, Hybrid
- [x] **AGNT-05**: BaseAgent реализует execute_task, get_capabilities, learn_from_feedback

### Infrastructure

- [x] **INFR-01**: Event Bus поддерживает P0-P3 приоритеты и async messaging
- [x] **INFR-02**: Event Store — immutable audit log всех событий
- [x] **INFR-03**: Database — SQLAlchemy 2.0 async с поддержкой SQLite и PostgreSQL
- [x] **INFR-04**: Obsidian vaults следуют LLM Wiki Pattern (raw/ → wiki/ → schema/)

### API & CLI

- [x] **APIC-01**: FastAPI приложение с health checks и metrics endpoints
- [x] **APIC-02**: CLI команды для управления Architect, Operator, агентами
- [x] **APIC-03**: Agency creation и testing scripts

### Keyword Research

- [x] **KYWD-01**: SEMrush API client с circuit breaker, retry, rate limiting, caching
- [x] **KYWD-02**: Ahrefs API client как fallback provider
- [x] **KYWD-03**: Pydantic схемы для валидации API ответов
- [x] **KYWD-04**: Budget control и cost tracking для API вызовов

### Content & Ads

- [x] **CADV-01**: Content Agent генерирует, редактирует, оптимизирует контент
- [x] **CADV-02**: Ads Agent создаёт кампании, оптимизирует бюджет, A/B тестирует
- [x] **CADV-03**: Агенты интегрированы с Event Bus и Obsidian vaults

### Linear Integration

- [x] **LINE-01**: GraphQL API client для Linear (двусторонняя синхронизация)
- [x] **LINE-02**: CLI команды для управления задачами Linear
- [x] **LINE-03**: AIM projects tracked as Linear projects

### Frontend

- [x] **FRNT-01**: Next.js 14+ App Router с Tailwind CSS 4
- [x] **FRNT-02**: Мульти-тенантная архитектура с tenant isolation middleware
- [x] **FRNT-03**: NextAuth.js для аутентификации
- [x] **FRNT-04**: RBAC (role-based access control)

### Agency Operations

- [x] **OPS-01**: Project templates для типовых медицинских проектов
- [x] **OPS-02**: Automated reporting (weekly, monthly, quarterly)
- [x] **OPS-03**: Analytics dashboards (SEO, Content, Ads performance)
- [x] **OPS-04**: Knowledge base с LLM Wiki Pattern

### AI Enhancement

- [x] **AIEN-01**: LLM Orchestrator управляет несколькими AI провайдерами (Claude, GPT, Gemini)
- [x] **AIEN-02**: SEO Analyzer выполняет глубокий анализ страниц (>50 страниц)
- [x] **AIEN-03**: Ad Copy Generator создаёт A/B варианты с tone of voice
- [x] **AIEN-04**: Predictive Analytics прогнозирует результаты кампаний
- [x] **AIEN-05**: Magisters интегрированы с AI компонентами

### Lead Capture

- [x] **LEAD-01**: Contact form захватывает лиды с валидацией и rate limiting
- [x] **LEAD-02**: AI Lead Scoring с 30+ факторами (поведенческие, демографические, временные)
- [x] **LEAD-03**: Hot/Warm/Cold tier классификация
- [x] **LEAD-04**: Lead создаёт Linear задачу через интеграцию
- [x] **LEAD-05**: Duplicate detection для предотвращения повторных лидов
- [x] **LEAD-06**: Real-time lead analytics и метрики конверсии

### Payment

- [x] **PAYM-01**: Payment processing с обработкой успеха/ошибки
- [x] **PAYM-02**: Payment UI для onboarding flow
- [x] **PAYM-03**: Автоматическое создание инвойсов

### Onboarding

- [x] **ONBD-01**: Document upload с type validation и size limits
- [x] **ONBD-02**: OCR + AI extraction для документов (license, INN, OGRN, contract)
- [x] **ONBD-03**: Валидация ИНН, ОГРН, КПП контрольных сумм
- [x] **ONBD-04**: State machine для onboarding с корректными переходами
- [x] **ONBD-05**: Retry logic для fallable операций

### Email Automation

- [x] **MAIL-01**: Webhook-triggered email workflows
- [x] **MAIL-02**: Hot tier: 1 email мгновенно
- [x] **MAIL-03**: Warm tier: 3 письма (day 0, 3, 7)
- [x] **MAIL-04**: Cold tier: weekly digest
- [x] **MAIL-05**: Email event tracking (open, click, bounce, unsubscribe)

### End-to-End Testing

- [ ] **TEST-01**: Lead Capture flow E2E (form → lead → scoring → Linear task)
- [ ] **TEST-02**: Onboarding flow E2E (lead → documents → validation → payment → complete)
- [ ] **TEST-03**: Email Automation flow E2E (lead → workflow → emails → events)
- [ ] **TEST-04**: Analytics flow E2E (metrics aggregation, conversion funnel, reports)

### Security & Compliance

- [ ] **SECU-01**: ФЗ-152 персональные данные зашифрованы (AES-256-GCM)
- [ ] **SECU-02**: Consent tracking с timestamp, IP, audit log
- [ ] **SECU-03**: Data retention policies (7 лет для медицинских записей)
- [ ] **SECU-04**: Right to data deletion (GDPR-like)
- [ ] **SECU-05**: SQL injection prevention (parameterized queries)
- [ ] **SECU-06**: XSS prevention (React escaping, CSP headers)
- [ ] **SECU-07**: CSRF protection (SameSite cookies, CSRF tokens)
- [ ] **SECU-08**: JWT token security (expiration, refresh)
- [ ] **SECU-09**: Password hashing (bcrypt)
- [ ] **SECU-10**: File upload security (type validation, size limits, virus scanning)

### Performance

- [ ] **PERF-01**: API response time <200ms p95
- [ ] **PERF-02**: Database query time <50ms p95
- [ ] **PERF-03**: Frontend load time <2s (LCP)
- [ ] **PERF-04**: Throughput >100 req/s
- [ ] **PERF-05**: PostgreSQL migration completed (from SQLite)

### Monitoring

- [ ] **MONI-01**: Prometheus metrics export (request rate, error rate, latency)
- [ ] **MONI-02**: Grafana dashboards (Application, Business, Infrastructure)
- [ ] **MONI-03**: Sentry error tracking с группировкой и deduplication
- [ ] **MONI-04**: Alert rules (Critical + Warning) с Telegram/email уведомлениями

### Documentation

- [ ] **DOCS-01**: Deployment guide (Docker, Kubernetes, env vars)
- [ ] **DOCS-02**: API documentation (OpenAPI/Swagger auto-generated)
- [ ] **DOCS-03**: Operations runbook (troubleshooting, backup, recovery)
- [ ] **DOCS-04**: ФЗ-152 compliance guide

## v2 Requirements

Deferred to future release.

### Landing Page

- **LAND-01**: Landing page с конверсией >3%
- **LAND-02**: SEO оптимизация landing page
- **LAND-03**: Интеграция с lead capture из Phase 11
- **LAND-04**: A/B тестирование landing page вариантов

### Production

- **PROD-01**: ЮKassa real integration (замена Helcim stub)
- **PROD-02**: Контур.Диадок real integration (замена DocuSign stub)
- **PROD-03**: Deploy to Yandex Cloud / VK Cloud
- **PROD-04**: Production-grade monitoring и auto-scaling

### Marketing

- **MKTG-01**: Запуск маркетинговых кампаний (Яндекс.Директ, Telegram, VK)
- **MKTG-02**: Analytics воронки продаж от кампании до клиента
- **MKTG-03**: ROI tracking по каналам привлечения

## Out of Scope

| Feature | Reason |
|---------|--------|
| HIPAA compliance | Не применяется в РФ (вместо: ФЗ-152) |
| Stripe/Helcim payments | Не работают в РФ (вместо: ЮKassa) |
| DocuSign integration | Дорого, не популярно в РФ (вместо: Контур.Диадок) |
| Google Ads campaigns | Российский рынок использует Яндекс.Директ |
| FDA regulations | Не применяется в РФ |
| Mobile app | Web-first стратегия, мобильное приложение позже |

## Traceability

Which phases cover which requirements.

| Requirement | Category | Phase | Status |
|-------------|----------|-------|--------|
| FRMW-01..04 | Framework Core | 1 | Complete |
| AGNT-01..05 | Agent System | 2 | Complete |
| INFR-01..04 | Infrastructure | 3 | Complete |
| APIC-01..03 | API & CLI | 4 | Complete |
| KYWD-01..04 | Keyword Research | 5 | Complete |
| CADV-01..03 | Content & Ads | 6 | Complete |
| LINE-01..03 | Linear Integration | 7.5 | Complete |
| FRNT-01..04 | Frontend | 8 | Complete |
| OPS-01..04 | Agency Operations | 9 | Complete |
| AIEN-01..05 | AI Enhancement | 10 | Complete |
| LEAD-01..06 | Lead Capture | 11 | Complete |
| PAYM-01..03 | Payment | 11 | Complete |
| ONBD-01..05 | Onboarding | 11 | Complete |
| MAIL-01..05 | Email Automation | 11 | Complete |
| TEST-01..04 | E2E Testing | 11 | In Progress |
| SECU-01..10 | Security | 11 | In Progress |
| PERF-01..05 | Performance | 11 | In Progress |
| MONI-01..04 | Monitoring | 11 | In Progress |
| DOCS-01..04 | Documentation | 11 | In Progress |
| LAND-01..04 | Landing Page | 13 | Deferred |
| PROD-01..04 | Production | 12 | Planned |
| MKTG-01..03 | Marketing | 13 | Planned |

**Coverage:**
- v1 requirements: 72 total
- v1 Complete: 54 (75%)
- v1 In Progress: 22 (Phase 11 Sprint 4)
- v2 requirements: 11 (deferred to Phases 12-13)

---
*Requirements defined: 2026-05-18*
*Last updated: 2026-05-18 after GSD infrastructure creation*
