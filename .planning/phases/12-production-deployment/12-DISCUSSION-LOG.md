# Phase 12: Production Deployment - Discussion Log (Assumptions Mode)

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions captured in CONTEXT.md — this log preserves the analysis.

**Date:** 2026-05-18
**Phase:** 12-production-deployment
**Mode:** assumptions
**Areas analyzed:** Payment Integration, Contract Signing, Database Migration, Production Deploy, Monitoring & Alerting, ФЗ-152 Compliance

## Assumptions Presented

### Payment Integration (ЮKassa)
| Assumption | Confidence | Evidence |
|------------|-----------|----------|
| Replace HelcimClient stub with YooKassaClient using yookassa SDK | Confident | `helcim_client.py:20-28` — full stub, `payment_service.py:87` — stable interface |
| YooKassa SDK supports async (httpx-based) | Confident | yookassa official docs, current architecture uses httpx |
| Add YOOKASSA_SHOP_ID and YOOKASSA_SECRET_KEY env vars | Confident | Pattern from existing SEMRUSH_API_KEY, AHREFS_API_KEY |

### Contract Signing (Контур.Диадок)
| Assumption | Confidence | Evidence |
|------------|-----------|----------|
| Replace KontourClient stub with real REST API calls | Confident | `kontour_client.py:33-53` — correct interface, `api/endpoints/contracts.py` — already integrated |
| Delete DocuSignClient (~430 lines) | Confident | `docusign_client.py` — full implementation for non-RU market, replaced by Контур |
| Signature types already correct for Russian law | Confident | `kontour_client.py:382-402` — <100k, 100k-600k, >600k RUB thresholds |

### Database Migration (SQLite → PostgreSQL)
| Assumption | Confidence | Evidence |
|------------|-----------|----------|
| Change DATABASE_URL, add postgres to docker-compose | Confident | `database.py:15` — single config point, `docker-compose.yml` — structured for new services |
| SQLAlchemy async supports both drivers | Confident | `database.py:8-9` — uses create_async_engine, sqlalchemy 2.0 |
| Use Alembic for migrations | Likely | Standard pattern, no existing migration tooling found |

### Production Deploy (iamaim.ru)
| Assumption | Confidence | Evidence |
|------------|-----------|----------|
| Server exists at iamaim.ru, accessible via `ssh aim` | Confident | User confirmation during context gathering |
| Docker Compose deploy to existing server | Confident | `docker-compose.yml` — 5 services ready, `Dockerfile` — multi-stage build |
| SSL via Let's Encrypt on existing Nginx | Likely | `DEPLOYMENT.md:93-104` — certbot instructions exist |

### Monitoring & Alerting
| Assumption | Confidence | Evidence |
|------------|-----------|----------|
| Prometheus + Grafana already configured | Confident | `docker-compose.yml:68-100` — both services, `prometheus-alerts.yml` — ready |
| Add PostgreSQL exporter + Telegram alerts | Likely | `RUNBOOK.md` — runbook exists, needs PG-specific sections |
| Sentry for error tracking | Likely | `DEPLOYMENT.md:131-136` — Sentry DSN placeholder in env |

### ФЗ-152 Compliance
| Assumption | Confidence | Evidence |
|------------|-----------|----------|
| AES-256-GCM encryption already implemented | Confident | `payment_service.py:107-110` — FieldEncryption in use |
| FZ152AuditLog immutable audit trail ready | Confident | `fz152_audit.py` — complete model with indexes |
| Data stored on Russian servers (Yandex Cloud jurisdiction) | Confident | User confirmed iamaim.ru server exists, Russian hosting |

## Corrections Made

No corrections — all assumptions confirmed by user.

- **Original deploy assumption:** Yandex Cloud new provisioning
- **User correction:** Server iamaim.ru already exists (`ssh aim`) — deploy to existing, not provision new
- **Applied to:** D-11, D-12, D-13 — updated to reflect existing server

## External Research

No external research performed. Codebase analysis was sufficient — all stubs clearly marked, interfaces well-defined, Docker/infra already production-ready. External research for specific API docs (yookassa SDK, Контур.Диадок API) will happen during planning phase via gsd-phase-researcher.
