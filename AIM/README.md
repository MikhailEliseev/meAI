# AIM Agency

[![Tests](https://github.com/MikhailEliseev/meAI/actions/workflows/tests.yml/badge.svg)](https://github.com/MikhailEliseev/meAI/actions/workflows/tests.yml)
[![codecov](https://codecov.io/gh/MikhailEliseev/meAI/branch/main/graph/badge.svg)](https://codecov.io/gh/MikhailEliseev/meAI)

**AI-first Medical Marketing Agency**

Domain: iamaim.ru

## Architecture

```
AIM/
├── src/aim/                    # Agency code
│   ├── magisters/              # SEO, Content, Ads Magisters
│   ├── subagents/              # Specialized subagents
│   └── config/                 # Configuration
├── obsidian/                   # Agent vaults (LLM Wiki pattern)
│   ├── operator/               # Operator's vault
│   ├── seo-magister/           # SEO Magister's vault
│   ├── content-magister/       # Content Magister's vault
│   └── ads-magister/           # Ads Magister's vault
├── data/                       # SQLite database
└── scripts/                    # CLI tools
```

## Hierarchy

```
Operator (Tactical Layer)
  ↓
Magisters (Domain Layer)
  ├── SEO Magister
  ├── Content Magister
  └── Ads Magister
  ↓
Subagents (Execution Layer)
  ├── Keyword Research
  ├── Content Writer
  ├── Ads Creator
  └── ...
```

## Development

All code is built from `/Users/mikhaileliseev/Desktop/Dev/!meAI` (command center).

The agency lives here in `AIM/` subdirectory.

## Framework

Uses `meai` framework from `../src/meai/`:
- Base classes: Operator, BaseMagister, BaseAgent
- Infrastructure: Event Bus, Event Store, Obsidian integration
- Core: Architect, Orchestrator, Decision Maker

## Status

✅ **Phase 11: Client Acquisition — Complete** (2026-05-18)

### Sprint 4: Production Hardening ✅

| Task | Status | Artifacts |
|------|--------|-----------|
| 4.1 E2E Testing | ✅ Complete | 77 tests, 2 skipped |
| 4.2 Security Audit | ✅ Complete | [SECURITY.md](SECURITY.md) |
| 4.3 Performance Optimization | ✅ Complete | DB indexes, query profiling, response cache |
| 4.4 Monitoring & Alerting | ✅ Complete | Prometheus rules, Grafana, Sentry, RUNBOOK |
| 4.5 Documentation | ✅ Complete | Deployment guide, API docs |

### Core Features (Phase 11)

**Lead Capture:**
- AES-256-GCM field encryption (name, phone, email, clinic)
- ФЗ-152 consent tracking with audit log
- reCAPTCHA v3 verification
- Rate limiting (10 req/min per IP)
- Duplicate detection
- UTM tracking

**AI Lead Scoring:**
- Rule-based + ML scoring (30+ factors)
- Hot/Warm/Cold tier classification
- Real-time scoring on capture

**Onboarding Workflow:**
- Document upload & AI validation
- Payment integration (ЮKassa stub)
- Email automation (SendGrid)
- Linear task creation

**Email Automation:**
- Tier-based workflow engine
- 15-min response guarantee
- Template-based personalization

### Monitoring Stack

| Component | Port | Endpoint |
|-----------|------|----------|
| AIM API | 8000 | `/health`, `/ready`, `/metrics` |
| Prometheus | 9090 | `/-/healthy` |
| Grafana | 3000 | `/api/health` |
| Sentry | — | Error tracking (SENTRY_DSN) |

### Test Suite

- **E2E Tests:** 77 passing, 2 skipped
- **Security Tests:** ФЗ-152 compliance, encryption, rate limiting, input validation
- **Performance:** DB indexes, query profiling (>100ms threshold), 30s response cache

---

## Quick Start

```bash
cd AIM
source ../venv/bin/activate

# Run all E2E tests
pytest tests/e2e/ -v

# Start dev server
uvicorn aim.main:app --reload --port 8000

# API docs
open http://localhost:8000/docs
```

---

---

## Documentation

### Getting Started
- [Contributing Guidelines](CONTRIBUTING.md) — Dev setup, code style, git workflow
- [Test Architecture](docs/TEST_ARCHITECTURE.md) — Testing philosophy, test pyramid, fixtures
- [Troubleshooting Guide](docs/TROUBLESHOOTING.md) — Common issues and solutions

### Deployment & Operations
- [Deployment Guide](deploy/DEPLOYMENT.md) — Docker Compose, SSL, monitoring setup
- [Runbook](deploy/RUNBOOK.md) — Alert response procedures
- [Production Setup](docs/PRODUCTION_SETUP.md) — Environment configuration
- [Disaster Recovery](docs/DISASTER_RECOVERY.md) — Recovery procedures
- [Rollback Procedures](docs/ROLLBACK_PROCEDURES.md) — Safe rollback methods

### Security
- [Security Audit Report](SECURITY.md) — ФЗ-152 compliance, vulnerability assessment
- [Prometheus Alerts](deploy/prometheus-alerts.yml) — 9 alerting rules

### API Integration
- [API Integration Guide](docs/API_INTEGRATION.md) — All 6 API integrations with setup
  - SEMrush, Ahrefs, GA4, Yandex Metrica, PageSpeed Insights, Yandex Direct

---

**Last Updated:** 2026-05-18
