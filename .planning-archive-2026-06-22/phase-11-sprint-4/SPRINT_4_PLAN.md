# Phase 11 Sprint 4: Testing & Launch

**Date:** 2026-05-17 01:50 GMT+3  
**Status:** Planning  
**Duration:** Week 7-8 (50 hours)

---

## Overview

Sprint 4 завершает Phase 11 Client Acquisition с фокусом на тестирование, оптимизацию и запуск в production.

**Prerequisites:**
- ✅ Sprint 1: Landing Page (deferred)
- ✅ Sprint 2: Lead Generation (192 tests passing)
- ✅ Sprint 3: Payment & Onboarding (146 tests passing)

**Total Tests Before Sprint 4:** 338/338 passing

---

## Tasks

### Task 4.1: E2E Testing (16h)

**Goal:** End-to-end тестирование полного user journey от landing page до onboarding completion.

**Scope:**
1. **Lead Capture Flow** (4h):
   - User fills contact form → Lead created → AI scoring → Linear task created
   - Test all tiers: Hot, Warm, Cold
   - Test email workflow triggers
   - Test duplicate detection
   - Test rate limiting

2. **Onboarding Flow** (6h):
   - Lead → Start onboarding → Upload documents → Validate → Payment → Complete
   - Test all document types: license, inn, ogrn, contract
   - Test OCR + AI extraction
   - Test validation (INN, OGRN, KPP checksums)
   - Test payment processing (stub)
   - Test state machine transitions
   - Test retry logic

3. **Email Automation Flow** (3h):
   - Lead captured → Workflow triggered → Emails scheduled → Emails sent → Events tracked
   - Test Hot tier (1 email instant)
   - Test Warm tier (3 emails: day 0, 3, 7)
   - Test Cold tier (weekly digest)
   - Test webhook event processing

4. **Analytics Flow** (3h):
   - Lead metrics aggregation
   - Email metrics calculation
   - Conversion funnel tracking
   - Real-time stats
   - Export reports (CSV, JSON, PDF)

**Test Files:**
- `AIM/tests/e2e/test_lead_capture_flow.py` (150 lines)
- `AIM/tests/e2e/test_onboarding_flow.py` (250 lines)
- `AIM/tests/e2e/test_email_automation_flow.py` (180 lines)
- `AIM/tests/e2e/test_analytics_flow.py` (120 lines)

**Expected Tests:** 25-30 E2E tests

---

### Task 4.2: Security Audit (12h)

**Goal:** Проверка соответствия ФЗ-152 и security best practices.

**Scope:**
1. **ФЗ-152 Compliance Audit** (5h):
   - Personal data encryption (AES-256-GCM)
   - Consent tracking (timestamp, IP, audit log)
   - Data retention policies
   - Access control and audit logging
   - Right to be forgotten (GDPR-like)
   - Data breach notification procedures

2. **Security Vulnerabilities** (4h):
   - SQL injection prevention (SQLAlchemy parameterized queries)
   - XSS prevention (React auto-escaping, CSP headers)
   - CSRF protection (SameSite cookies, CSRF tokens)
   - Rate limiting (API endpoints)
   - Input validation (Pydantic schemas)
   - File upload security (type validation, size limits, virus scanning)

3. **Authentication & Authorization** (3h):
   - JWT token security (expiration, refresh)
   - Password hashing (bcrypt)
   - Role-based access control (RBAC)
   - API key management
   - Session management

**Deliverables:**
- `AIM/docs/security/FZ152_COMPLIANCE.md` (security audit report)
- `AIM/docs/security/SECURITY_CHECKLIST.md` (security checklist)
- `AIM/tests/security/test_fz152_compliance.py` (compliance tests)
- `AIM/tests/security/test_vulnerabilities.py` (security tests)

**Expected Tests:** 15-20 security tests

---

### Task 4.3: Performance Optimization (10h)

**Goal:** Оптимизация производительности для production нагрузки.

**Scope:**
1. **Database Optimization** (4h):
   - Index analysis and optimization
   - Query performance profiling
   - N+1 query elimination
   - Connection pooling tuning
   - Database migration to PostgreSQL (from SQLite)

2. **API Performance** (3h):
   - Response time optimization (<200ms p95)
   - Caching strategy (Redis)
   - Async processing (Celery tasks)
   - Rate limiting tuning
   - Load testing (Locust)

3. **Frontend Performance** (3h):
   - Bundle size optimization
   - Code splitting
   - Image optimization
   - Lazy loading
   - Core Web Vitals optimization

**Deliverables:**
- `AIM/docs/performance/OPTIMIZATION_REPORT.md`
- `AIM/tests/performance/test_api_performance.py`
- `AIM/tests/performance/test_database_performance.py`
- Load testing scripts (Locust)

**Performance Targets:**
- API response time: <200ms p95
- Database query time: <50ms p95
- Frontend load time: <2s (LCP)
- Throughput: >100 req/s

---

### Task 4.4: Monitoring & Alerting (8h)

**Goal:** Production monitoring и alerting для proactive issue detection.

**Scope:**
1. **Application Monitoring** (3h):
   - Prometheus metrics export
   - Grafana dashboards
   - Key metrics: request rate, error rate, latency, throughput
   - Business metrics: leads captured, emails sent, payments processed

2. **Error Tracking** (2h):
   - Sentry integration
   - Error grouping and deduplication
   - Stack trace capture
   - User context tracking

3. **Alerting** (3h):
   - Alert rules (Prometheus Alertmanager)
   - Critical alerts: API down, database down, high error rate
   - Warning alerts: high latency, low disk space, high memory usage
   - Notification channels: Telegram, email

**Deliverables:**
- `AIM/src/aim/monitoring/prometheus.py` (metrics exporter)
- `AIM/src/aim/monitoring/sentry.py` (error tracking)
- `AIM/config/prometheus/alerts.yml` (alert rules)
- `AIM/config/grafana/dashboards/` (Grafana dashboards)

**Dashboards:**
- Application Overview (request rate, error rate, latency)
- Business Metrics (leads, emails, payments)
- Infrastructure (CPU, memory, disk, network)

---

### Task 4.5: Documentation (4h)

**Goal:** Production-ready документация для deployment и maintenance.

**Scope:**
1. **Deployment Guide** (2h):
   - Infrastructure requirements
   - Environment variables
   - Database setup (PostgreSQL)
   - Redis setup
   - Docker deployment
   - Kubernetes deployment (optional)

2. **API Documentation** (1h):
   - OpenAPI/Swagger documentation
   - API endpoint descriptions
   - Request/response examples
   - Authentication guide

3. **Runbook** (1h):
   - Common issues and solutions
   - Troubleshooting guide
   - Monitoring and alerting guide
   - Backup and recovery procedures

**Deliverables:**
- `AIM/docs/deployment/DEPLOYMENT_GUIDE.md`
- `AIM/docs/api/API_DOCUMENTATION.md` (auto-generated from FastAPI)
- `AIM/docs/operations/RUNBOOK.md`

---

## Russian Market Adaptations

**ФЗ-152 Compliance:**
- Personal data encryption at rest (AES-256-GCM)
- Consent tracking with audit log
- Data retention policies (7 years for medical records)
- Right to data deletion
- Breach notification procedures

**Infrastructure:**
- Hosting: Russian data centers (Yandex Cloud, VK Cloud)
- CDN: Russian CDN providers
- Monitoring: Self-hosted or Russian providers

**Documentation:**
- Russian language documentation
- ФЗ-152 compliance guide
- Russian legal requirements

---

## Test Coverage Goals

**Current:** 338/338 tests passing (100%)

**Sprint 4 Additions:**
- E2E tests: 25-30 tests
- Security tests: 15-20 tests
- Performance tests: 10-15 tests
- **Total New Tests:** 50-65 tests

**Target:** 388-403 tests passing (100%)

---

## Timeline

**Week 7:**
- Day 1-2: Task 4.1 (E2E Testing) - 16h
- Day 3: Task 4.2 (Security Audit) - 12h

**Week 8:**
- Day 1: Task 4.3 (Performance Optimization) - 10h
- Day 2: Task 4.4 (Monitoring & Alerting) - 8h
- Day 3: Task 4.5 (Documentation) - 4h

**Total:** 50 hours

---

## Success Criteria

**Testing:**
- ✅ All E2E flows working end-to-end
- ✅ 388-403 tests passing (100%)
- ✅ No critical security vulnerabilities
- ✅ ФЗ-152 compliance verified

**Performance:**
- ✅ API response time <200ms p95
- ✅ Database query time <50ms p95
- ✅ Frontend load time <2s (LCP)
- ✅ Throughput >100 req/s

**Monitoring:**
- ✅ Prometheus metrics exported
- ✅ Grafana dashboards created
- ✅ Sentry error tracking configured
- ✅ Alert rules defined

**Documentation:**
- ✅ Deployment guide complete
- ✅ API documentation auto-generated
- ✅ Runbook created

---

## Next Steps After Sprint 4

**Phase 11 Complete:**
- Sprint 1: Landing Page (deferred)
- Sprint 2: Lead Generation ✅
- Sprint 3: Payment & Onboarding ✅
- Sprint 4: Testing & Launch ✅

**Phase 12: Production Deployment**
- Replace Helcim stub with ЮKassa
- Replace DocuSign stub with Контур.Диадок
- Deploy to production (Yandex Cloud)
- Monitor and iterate

**Phase 13: Landing Page (Sprint 1 deferred)**
- Implement landing page components
- Integrate with lead capture
- SEO optimization
- Launch marketing campaigns

---

## Dependencies

**External Services:**
- PostgreSQL database
- Redis cache
- Prometheus monitoring
- Grafana dashboards
- Sentry error tracking
- Yandex Cloud (hosting)

**Internal Dependencies:**
- All Sprint 2 components (Lead Generation)
- All Sprint 3 components (Payment & Onboarding)

---

## Risk Mitigation

**Performance Risks:**
- Database bottlenecks → Index optimization, connection pooling
- API latency → Caching, async processing
- Frontend load time → Code splitting, lazy loading

**Security Risks:**
- Data breaches → Encryption, access control, audit logging
- ФЗ-152 non-compliance → Compliance audit, legal review
- Vulnerabilities → Security testing, penetration testing

**Operational Risks:**
- Downtime → Monitoring, alerting, redundancy
- Data loss → Backups, replication
- Scaling issues → Load testing, horizontal scaling

---

## Estimated Effort

**Total:** 50 hours
- Task 4.1: E2E Testing - 16h
- Task 4.2: Security Audit - 12h
- Task 4.3: Performance Optimization - 10h
- Task 4.4: Monitoring & Alerting - 8h
- Task 4.5: Documentation - 4h

**Adaptation Overhead:** +3 hours (ФЗ-152 compliance, Russian infrastructure)

**Total with Adaptation:** 53 hours

---

## Notes

- Sprint 4 фокусируется на production readiness
- Все stubs (Helcim, DocuSign) остаются до Phase 12
- ФЗ-152 compliance критичен для российского рынка
- Monitoring и alerting обязательны для production
- Documentation необходима для maintenance

