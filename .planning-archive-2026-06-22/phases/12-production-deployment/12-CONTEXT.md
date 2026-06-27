# Phase 12: Production Deployment - Context

**Gathered:** 2026-05-18 (assumptions mode)
**Status:** Ready for planning

<domain>
## Phase Boundary

Замена stubs на реальные российские сервисы и production-ready деплой. Что входит:
- ЮKassa real integration (замена HelcimClient stub)
- Контур.Диадок real integration (замена KontourClient stub, удаление DocuSign)
- PostgreSQL миграция с SQLite
- Деплой в Yandex Cloud
- Production мониторинг и алертинг
- ФЗ-152 полный compliance

Что НЕ входит:
- Landing page (deferred to Phase 13)
- Маркетинговые кампании (Phase 13)
- Новые фичи агентства (только production-ready существующих)
</domain>

<decisions>
## Implementation Decisions

### Payment Integration (ЮKassa)

- **D-01:** Заменить `HelmClient` (stub) на `YooKassaClient` с использованием официального Python SDK (`yookassa`). Сохранить существующий интерфейс: `process_payment()`, `check_payment_status()`, `refund_payment()`. PaymentService остаётся без изменений.
- **D-02:** ЮKassa SDK поддерживает async (httpx-based), что совместимо с текущей async-архитектурой PaymentService.
- **D-03:** Добавить `YOOKASSA_SHOP_ID` и `YOOKASSA_SECRET_KEY` в `.env.production`.

### Contract Signing Integration (Контур.Диадок)

- **D-04:** Заменить `KontourClient` stub на реальные REST API вызовы Контур.Диадок. Существующий интерфейс уже правильный: `send_for_signature()`, `get_document_status()`, `download_signed_document()`, `get_signature_certificate()`.
- **D-05:** Типы подписей (Simple/Enhanced/Qualified) уже реализованы согласно российскому законодательству (<100k, 100k-600k, >600k RUB).
- **D-06:** Удалить `DocuSignClient` (docusign_client.py, ~430 строк) — не используется в РФ. Код Контур.Диадок полностью заменяет его функциональность.
- **D-07:** Добавить `KONTOUR_API_KEY`, `KONTOUR_ORGANIZATION_ID` в `.env.production`.

### Database Migration (SQLite → PostgreSQL)

- **D-08:** Миграция через смену `DATABASE_URL` в `database.py` с `sqlite+aiosqlite:///...` на `postgresql+asyncpg://...`. SQLAlchemy 2.0 async поддерживает оба драйвера без изменений в коде моделей.
- **D-09:** Добавить PostgreSQL сервис в `docker-compose.yml` (postgres:16-alpine). Использовать `asyncpg` драйвер (уже используется в Data Collector).
- **D-10:** Миграция через Alembic: создать initial migration из текущих моделей, настроить автогенерацию.

### Production Deploy (iamaim.ru)

- **D-11:** Сервер уже существует — `iamaim.ru`, доступ по `ssh aim`. Деплой на существующий сервер через Docker Compose. Провижионинг нового сервера не требуется.
- **D-12:** SSL через Let's Encrypt + certbot с авто-обновлением. Nginx уже настроен как TLS terminator (docker-compose.yml). Проверить текущий SSL-статус на сервере.
- **D-13:** UFW firewall (22, 80, 443), Fail2ban для SSH — hardening из DEPLOYMENT.md checklist. Проверить текущее состояние на сервере.

### Monitoring & Alerting

- **D-14:** Prometheus + Grafana уже настроены в docker-compose.yml. Добавить: PostgreSQL exporter, бизнес-метрики (leads, payments, signings), алерты в Telegram.
- **D-15:** Sentry для error tracking (DSN в `.env.production`). FastAPI + SQLAlchemy интеграция уже описана в DEPLOYMENT.md.
- **D-16:** Runbook уже существует (`deploy/RUNBOOK.md`) — дополнить сценариями для PostgreSQL и ЮKassa.

### ФЗ-152 Compliance

- **D-17:** AES-256-GCM шифрование PII уже реализовано (FieldEncryption в payment_service.py). Аудит-лог через FZ152AuditLog уже пишется.
- **D-18:** Добавить data retention policy (7 лет для медицинских записей), право на удаление данных.
- **D-19:** Убедиться что PostgreSQL данные хранятся на российских серверах (Yandex Cloud = российская юрисдикция).

### Claude's Discretion

- Сервер уже существует (iamaim.ru, `ssh aim`) — конкретный провайдер/конфигурация будет проверена при деплое
- Структура Alembic миграций
- Формат Telegram-алертов и дашбордов Grafana
- Нужен ли Sentry (рекомендуется) или достаточно Prometheus алертов
</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Payment
- `AIM/src/aim/services/payment/helcim_client.py` — Текущий Helcim stub (интерфейс для замены)
- `AIM/src/aim/services/payment/payment_service.py` — Payment service (НЕ менять, только заменить клиент)
- `AIM/src/aim/schemas/payment.py` — Pydantic схемы платежей

### Contracts
- `AIM/src/aim/services/contracts/kontour_client.py` — Контур.Диадок stub (интерфейс уже правильный)
- `AIM/src/aim/services/onboarding/docusign_client.py` — DocuSign (УДАЛИТЬ, заменён Контуром)
- `AIM/src/aim/services/onboarding/workflow.py` — Onboarding workflow (использует docusign_client)

### Database
- `AIM/src/aim/database.py` — Текущая конфигурация SQLite
- `AIM/src/aim/storage/models.py` — SQLAlchemy Base (единый источник истины)
- `AIM/src/aim/models/` — Все модели (Lead, Payment, Document, Onboarding, etc.)

### Deploy
- `AIM/docker-compose.yml` — Текущий Docker Compose (app, redis, nginx, prometheus, grafana)
- `AIM/Dockerfile` — Multi-stage build (уже включает libpq-dev)
- `AIM/deploy/DEPLOYMENT.md` — Deployment guide с инструкциями
- `AIM/deploy/RUNBOOK.md` — Operations runbook
- `AIM/deploy/prometheus-alerts.yml` — Production алерты

### Security & Compliance
- `AIM/src/aim/models/fz152_audit.py` — ФЗ-152 immutable audit log модель
- `AIM/SECURITY.md` — Security hardening checklist
- `AIM/src/aim/middleware/` — Security middleware

### Project
- `.planning/REQUIREMENTS.md` — PROD-01..04 требования для Phase 12
- `.planning/STATE.md` — Текущее состояние проекта
- `.planning/ROADMAP.md` — Roadmap с success criteria
- `CLAUDE.md` — Russian Market Adaptation Rule
</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- **PaymentService** (`payment_service.py`) — полностью готов, менять не нужно. Только заменить `HelmClient` → `YooKassaClient`.
- **KontourClient interface** (`kontour_client.py`) — правильный API, правильная legal-логика. Stub → real API calls.
- **FieldEncryption** (`utils/encryption.py`) — AES-256-GCM уже работает для ФЗ-152.
- **FZ152AuditLog** (`models/fz152_audit.py`) — immutable audit log модель готова.
- **Docker Compose** — 5 сервисов (app, redis, nginx, prometheus, grafana), добавить 6-й (postgres).
- **Multi-stage Dockerfile** — libpq-dev уже в builder stage.
- **Monitoring stack** — Prometheus + Grafana с дашбордами и алертами.

### Established Patterns
- **Stub → Real pattern:** Все stubs в Phase 11 следуют одному шаблону: класс с async методами, логгирование STUB-режима, mock-ответы. Замена = сохранить интерфейс, заменить реализацию.
- **Async throughout:** Все сервисы async (httpx, SQLAlchemy async). ЮKassa SDK тоже async.
- **Encryption by default:** Все PII поля шифруются перед сохранением. Платёжные данные, ФИО, email, телефон.
- **Audit everything:** Каждая операция с персональными данными пишет аудит-лог.

### Integration Points
- **PaymentService ← HelcimClient:** `payment_service.py:27,87` — заменить `HelcimClient` на `YooKassaClient` с тем же интерфейсом.
- **Onboarding Workflow ← DocuSignClient:** `workflow.py` — заменить на `KontourClient`.
- **Contracts API ← KontourClient:** `api/endpoints/contracts.py` — уже использует KontourClient.
- **Database ← DATABASE_URL:** `database.py:15` — единственная точка изменения для миграции.
- **Docker Compose ← PostgreSQL:** Добавить сервис и зависимость app → postgres.
</code_context>

<specifics>
## Specific Ideas

- ЮKassa SDK (`yookassa`) — официальный Python пакет с async поддержкой. Установка: `pip install yookassa`.
- Контур.Диадок API: REST JSON API с HMAC-подписью вебхуков. Документация: https://developer.kontur.ru/
- Alembic для миграций: `pip install alembic`, `alembic init`, `alembic revision --autogenerate`.
- Yandex Cloud: Compute Cloud (VMs) для Docker Compose деплоя. Альтернатива — Managed Service for Kubernetes.
- PostgreSQL 16 Alpine: легковесный образ (~250MB), совместим с asyncpg.
- Российские сервера: Yandex Cloud имеет три дата-центра в РФ (Москва, Владимир, Сасово).
</specifics>

<deferred>
## Deferred Ideas

- Auto-scaling (добавить когда трафик вырастет)
- Kubernetes миграция (Managed K8s в Yandex Cloud)
- VK Cloud как альтернативная платформа
- CI/CD pipeline (GitHub Actions → деплой в Yandex Cloud)
- Горизонтальное масштабирование (несколько инстансов app за load balancer)

[None of these are required for initial production deploy — Docker Compose на одной VM достаточно для запуска]
</deferred>

---

*Phase: 12-production-deployment*
*Context gathered: 2026-05-18 via assumptions mode*
