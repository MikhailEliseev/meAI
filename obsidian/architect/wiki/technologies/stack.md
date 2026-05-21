# Technology Stack

**Updated:** 2026-05-21

## Core

| Technology | Version | Purpose |
|-----------|---------|---------|
| Python | 3.11+ | Основной язык |
| FastAPI | 0.115+ | Web framework |
| SQLAlchemy | 2.0 | Async ORM |
| Pydantic | 2.x | Data validation |
| Alembic | — | Миграции БД |

## Infrastructure

| Technology | Purpose |
|-----------|---------|
| PostgreSQL | Production database |
| SQLite | Development database |
| Redis | Caching |
| Docker Compose | Deployment |
| Nginx | Reverse proxy |

## Monitoring

| Technology | Purpose |
|-----------|---------|
| Prometheus | Metrics collection |
| Grafana | Dashboards |
| Alertmanager | Alerts routing |
| structlog | Structured logging |

## Frontend

| Technology | Purpose |
|-----------|---------|
| Next.js | Landing page (iamaim.ru) |
| React | UI components |
| TypeScript | Type safety |

## Integrations

| Service | Purpose | Status |
|---------|---------|--------|
| Claude API (Anthropic) | AI decisions | ✅ Active |
| Bitrix24 | CRM | ✅ Integrated |
| YooKassa | Payments | ✅ Integrated |
| Telegram Bot API | Alerts + Admin | ✅ Active |
| Linear | Task tracking | ✅ Active |
| SEMrush | Keyword research | ✅ Ready |
| Ahrefs | SEO (fallback) | ✅ Ready |
| Yandex Direct API v5 | Ads | ✅ Ready |
| VK Ads API v5.199 | Ads | ✅ Ready |
| HH.ru API | Job market intelligence | ✅ Ready |

## Resilience

| Pattern | Implementation |
|---------|---------------|
| Circuit Breaker | pybreaker (fail_max=5, reset=60s) |
| Retry | tenacity (exponential backoff 1s→30s) |
| Rate Limiting | aiolimiter (token bucket) |
| Caching | aiocache + Redis (1h TTL) |
