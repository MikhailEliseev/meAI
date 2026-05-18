# Phase 12: Production Deployment — Research Synthesis

**Date:** 2026-05-18
**Status:** Complete
**Sources:** async_yookassa SDK, Контур.Диадок developer docs, Alembic docs, Docker/Prometheus docs

---

## 1. ЮKassa Integration

### Recommendation
**Primary:** `async_yookassa` (prodreams) — async-native httpx-based, matches our stack. 38 snippets, 87.4 benchmark.
**Fallback:** `aioyookassa` (masasibata) — more features, built-in webhook server, 575 snippets.
**Last resort:** `yookassa` official SDK — sync-only, needs `asyncio.to_thread()` wrapper.

```bash
pip install async-yookassa
```

### CRITICAL: Interface Change Required

YooKassa does NOT allow handling card data. The current `HelcimClient.process_payment(card_number, card_expiry, card_cvv, ...)` interface is fundamentally incompatible. 

**New flow:** Create payment → get `confirmation_url` → redirect user to YooKassa page → user pays → receive webhook.

**New interface:**
- `create_payment(amount, currency, description, return_url, metadata)` → returns `YooKassaPayment` with `confirmation_url`
- `check_payment_status(payment_id)` → returns status (pending/waiting_for_capture/succeeded/canceled)
- `refund_payment(payment_id, amount, reason)` → returns refund status

**New `PaymentStatus` enum needed:** Add `PENDING` (current: PAID, REFUNDED, FAILED).

### Webhooks
- YooKassa resends webhooks every 10 min for 24h if not HTTP 200
- Endpoint: `POST /api/webhooks/yookassa/payment`
- Must validate IP (YooKassa provides IP ranges)
- Events: `payment.succeeded`, `payment.waiting_for_capture`, `payment.canceled`, `refund.succeeded`

### Test Environment
- shopId: `54401`, secret: `test_Fh8hUAVVBGUGbjmlzba6TB0iyUbos_lueTHE-axOwM0`
- Test card: `5555 5555 5555 4444`, expiry `12/25+`, CVV `000`

### Env Vars
```
YOOKASSA_SHOP_ID=123456
YOOKASSA_SECRET_KEY=live_xxxxxx
YOOKASSA_RETURN_URL=https://iamaim.ru/payment/callback
```

### Files affected
- **NEW:** `aim/services/payment/yookassa_client.py` — replaces helcim_client.py
- **NEW:** `aim/api/webhooks.py` — YooKassa webhook endpoint
- **MODIFY:** `aim/services/payment/payment_service.py` — redirect flow, PENDING status
- **MODIFY:** `aim/schemas/payment.py` — new PaymentStatus, PaymentRequest fields
- **MODIFY:** `aim/api/endpoints/payments.py` — return confirmation_url
- **MODIFY:** `.env.example`, `requirements.txt`, `aim/config/settings.py`
- **DEPRECATE:** `helcim_client.py` (keep as reference, mark deprecated)

---

## 2. Контур.Диадок Integration

### Recommendation
Build our own Python client using `httpx` — no official Python SDK exists (only C#, Java, C++). Use **JSON format** (simpler, no protobuf compilation).

### Authentication
**OpenID Connect** via `identity.kontur.ru`. Use **Device Authorization Flow** for server-to-server:
1. Register integration at diadoc.ru/integrations/api → get `client_id` + `client_secret`
2. POST `/connect/deviceauthorization` → get `device_code` + `verification_uri`
3. One-time: open verification URI in browser, log in, grant permissions
4. POST `/connect/token` → get `access_token` (1h initial, 24h after refresh)
5. Refresh before expiry (store `refresh_token`)

**Required scopes:** `openid profile email offline_access Diadoc.PublicAPI`

### API Base URLs
- Production: `https://diadoc-api.kontur.ru`
- Staging: `https://diadoc-api-staging.kontur.ru`
- Identity: `https://identity.kontur.ru`

### Core Endpoints
| Use Case | Endpoint |
|----------|----------|
| Get our box ID | `GET /GetMyOrganizations` |
| Find recipient by INN | `GET /GetOrganizationsByInnKpp?inn=...` |
| Send document | `POST /V3/PostMessage` |
| Sign via cloud cert | `POST /DssSign` + poll `GET /DssSignResult` |
| Check status | `GET /V3/GetDocument` |
| Poll for changes | `GET /V8/GetNewEvents?afterIndexKey=...` |
| Download signed doc | `GET /V4/GetEntityContent` |
| Get signature info | `GET /GetSignatureInfo` |

### CRITICAL: No Webhooks
Диадок is **polling-based** — no webhooks, no HMAC verification. Replace `KontourWebhookHandler` with a polling service calling `GetNewEvents (V8)`:
- 30s interval during active signing
- Exponential backoff to 5min when idle
- Store `IndexKey` cursor for pagination

### Signing
- Diadoc does NOT generate signatures — use `DssSign` for cloud-based certificates (carrier-less)
- Alternative: КриптоПро CSP + `PostMessage` with pre-signed content
- `SignWithTestSignature = true` for testing only (no legal force)
- Signature types (Simple/Enhanced/Qualified) map to legal requirements under ФЗ-63, same API call

### Rate Limits
- 200 RPS max / 100 RPS recommended
- Max 4 parallel threads
- Max 40 docs per message, 70 MB per doc

### Env Vars
```
KONTOUR_CLIENT_ID=<from diadoc manager>
KONTOUR_CLIENT_SECRET=<from integrations.kontur.ru>
KONTOUR_ORGANIZATION_INN=7701234567
KONTOUR_API_URL=https://diadoc-api.kontur.ru
```

### Files affected
- **NEW:** `aim/services/contracts/kontour_auth.py` — OIDC token management
- **NEW:** `aim/services/contracts/kontour_poller.py` — GetNewEvents polling service
- **REWRITE:** `aim/services/contracts/kontour_client.py` — real API calls (preserve interface)
- **DELETE:** `aim/services/onboarding/docusign_client.py` (554 lines)
- **MODIFY:** `aim/services/onboarding/workflow.py` — remove DocuSign references
- **MODIFY:** `.env.example`, `requirements.txt`

---

## 3. PostgreSQL Migration (SQLite → PostgreSQL)

### Connection URL Change
Single change in `database.py`:
```
sqlite+aiosqlite:///./AIM/data/aim.db
→ postgresql+asyncpg://aim_user:${PG_PASS}@postgres:5432/aim_db
```

### Engine Configuration
```python
engine = create_async_engine(
    settings.database_url,
    pool_size=20,        # Up from default 5
    max_overflow=10,
    pool_pre_ping=True,  # Verify connections before use
    pool_recycle=3600,   # Recycle hourly
)
```

### Alembic Setup (CRITICAL PATTERN)
Alembic default `env.py` uses `engine_from_config()` which does NOT support async drivers. Required pattern:

```python
# alembic/env.py — async bridge
connectable = async_engine_from_config(
    config.get_section(config.config_ini_section, {}),
    prefix="sqlalchemy.",
    poolclass=pool.NullPool,  # No pooling for migrations
)

async def run_async_migrations():
    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)
    await connectable.dispose()

def run_migrations_online():
    asyncio.run(run_async_migrations())
```

**Four requirements:**
1. `async_engine_from_config()` instead of `engine_from_config()`
2. `connection.run_sync()` to bridge sync→async
3. `pool.NullPool` (short-lived migration connections)
4. Import ALL models before `Base.metadata` (or autogenerate produces empty migrations)

### Auto-migrate on FastAPI Startup
```python
@asynccontextmanager
async def lifespan(app: FastAPI):
    await asyncio.to_thread(lambda: command.upgrade(Config("alembic.ini"), "head"))
    yield
```

### Data Migration Strategy
**Option A (dev/small data):** SQLAlchemy script — read SQLite, write PostgreSQL per table.
**Option B (larger data):** `pgloader sqlite:///aim.db postgresql://...`
**Option C (PG→PG):** `pg_dump` / `pg_restore`

### Dependencies
```
asyncpg>=0.29.0,<0.30.0
alembic>=1.14.0,<2.0.0
```

### Env Vars
```
DATABASE_URL=postgresql+asyncpg://aim_user:${POSTGRES_PASSWORD}@postgres:5432/aim_db
POSTGRES_USER=aim_user
POSTGRES_PASSWORD=<generate>
POSTGRES_DB=aim_db
```

### Files affected
- **MODIFY:** `aim/database.py` — connection URL + pool config
- **NEW:** `alembic/` directory (env.py, versions/, alembic.ini)
- **NEW:** `scripts/migrate_sqlite_to_pg.py` — data migration
- **MODIFY:** `docker-compose.yml` — add postgres:16-alpine service
- **MODIFY:** `aim/main.py` — add lifespan with auto-migration
- **MODIFY:** `.env.example`, `requirements.txt`

---

## 4. Docker Compose Production Stack

### Full 7-Service Architecture
```
nginx (:80, :443) → certbot (SSL auto-renew)
                  → api (:8000, FastAPI + uvicorn)
                    → postgres (:5432, postgres:16-alpine)
                    → redis (:6379, redis:7-alpine)
                    
prometheus (:9090) → api (:8000/metrics)
                   → postgres-exporter (:9187)
                   → node-exporter (:9100)
                   
alertmanager (:9093) → Telegram webhook

grafana (:3000) → prometheus
```

### Key Production Patterns
- `restart: unless-stopped` on all services
- Resource limits on all services (CPU + memory)
- JSON-file logging with rotation (max-size + max-file)
- Health checks with start_period for slow-starting services
- Bind ports to `127.0.0.1` for security (except nginx 80/443)
- `.env.production` with `chmod 600`

### PostgreSQL Docker Config
```yaml
postgres:
  image: postgres:16-alpine
  environment:
    POSTGRES_INITDB_ARGS: "--locale=ru_RU.UTF-8"
  volumes:
    - postgres_data:/var/lib/postgresql/data
    - ./config/postgresql.conf:/etc/postgresql/postgresql.conf:ro
  healthcheck:
    test: ["CMD-SHELL", "pg_isready -U ${POSTGRES_USER} -d ${POSTGRES_DB}"]
  deploy:
    resources:
      limits: {cpus: '2', memory: 2G}
```

### PostgreSQL Tuning (2GB container)
```
shared_buffers = 512MB           # 25% of RAM
effective_cache_size = 1536MB    # 75% of RAM
work_mem = 32MB
random_page_cost = 1.1           # SSD
statement_timeout = 30000        # 30s max query
idle_in_transaction_session_timeout = 60000
autovacuum = on
```

---

## 5. SSL & Security

### Let's Encrypt
- Certbot in Docker container, auto-renews every 12h
- Initial cert: `certbot certonly --standalone -d iamaim.ru -d www.iamaim.ru`
- Mount certs to nginx container

### Nginx TLS Configuration
- TLS 1.2+ only, strong ciphers
- OCSP stapling, HSTS header
- Security headers: X-Frame-Options, X-Content-Type-Options, CSP

### Firewall (UFW)
```bash
ufw allow 22/tcp
ufw allow 80/tcp
ufw allow 443/tcp
ufw enable
```

### Fail2ban
- SSH protection: 5 failures → 10min ban
- Custom jails for: nginx 401/403 floods, API endpoint abuse

---

## 6. Monitoring Enhancements

### PostgreSQL Exporter
```yaml
postgres-exporter:
  image: quay.io/prometheuscommunity/postgres-exporter:latest
  environment:
    DATA_SOURCE_URI: "postgres:5432/aim_db?sslmode=disable"
    DATA_SOURCE_USER: "${POSTGRES_USER}"
    DATA_SOURCE_PASS: "${POSTGRES_PASSWORD}"
```

**Key metrics:** `pg_stat_database_tup_fetched` (cache hit ratio), `pg_stat_activity_count` (connections), `pg_stat_database_xact_rollback` (rollback rate), `pg_database_size_bytes` (growth).

### Telegram Alerting
Alertmanager → Telegram Bot API:
```yaml
receivers:
- name: 'telegram'
  telegram_configs:
  - bot_token: '${TELEGRAM_BOT_TOKEN}'
    chat_id: ${TELEGRAM_CHAT_ID}
    parse_mode: 'HTML'
    message: |
      <b>{{ .Status | toUpper }}</b>: {{ .CommonLabels.alertname }}
      {{ .CommonAnnotations.description }}
```

### Prometheus Alert Rules (new)
- `PostgresDown` — pg_exporter unreachable
- `HighConnectionCount` — >80% of max_connections
- `LowCacheHitRatio` — <90% buffer cache hit
- `HighRollbackRate` — >5% rollback ratio
- `PaymentFailureRate` — >5% payment failures in 5min
- `DiskSpaceLow` — <20% free disk

### Sentry
```python
import sentry_sdk
sentry_sdk.init(
    dsn=settings.sentry_dsn,
    environment="production",
    traces_sample_rate=0.1,  # 10% of transactions
    integrations=[FastApiIntegration(), SqlalchemyIntegration()],
)
```

### Env Vars
```
SENTRY_DSN=https://<key>@sentry.io/<project>
TELEGRAM_BOT_TOKEN=<token>
TELEGRAM_CHAT_ID=<chat_id>
```

### Files affected
- **MODIFY:** `docker-compose.yml` — add postgres-exporter, alertmanager, node-exporter
- **NEW:** `deploy/monitoring/rules.yml` — alert rules
- **NEW:** `deploy/monitoring/alertmanager.yml` — alert routing
- **MODIFY:** `deploy/prometheus.yml` — add scrape targets
- **MODIFY:** `deploy/RUNBOOK.md` — PG + YooKassa runbooks
- **MODIFY:** `aim/main.py` — Sentry init
- **MODIFY:** `requirements.txt` — sentry-sdk[fastapi]

---

## 7. ФЗ-152 Data Retention

### Legal Requirements
- **7-year retention for medical records** (ФЗ-323 ст.13)
- Right to data deletion upon request (ФЗ-152 ст.21)
- Data must be stored on Russian servers

### Partitioning Strategy
Partition `leads`, `documents`, `fz152_audit` tables by `created_at` (monthly):
```sql
CREATE TABLE leads_2026_06 PARTITION OF leads
FOR VALUES FROM ('2026-06-01') TO ('2026-07-01');
```

### PartitionManager
Python class to:
- Create future partitions (next 3 months)
- Detach expired partitions (>7 years)
- Drop detached partitions after 30-day grace period

### Data Deletion
- Anonymize PII (name→"DELETED", phone→null, email→null) instead of hard delete
- Keep metadata for audit trail (id, created_at, source, lead_temperature)
- Right-to-deletion endpoint: `DELETE /api/leads/{id}/gdpr-delete`

---

## Summary: Plan Structure Recommendation

Based on research, the original 3-plan split should be adjusted:

**12-01: ЮKassa + Контур.Диадок Real Integrations**
- YooKassaClient (async_yookassa) with redirect flow
- YooKassa webhook endpoint
- PaymentService refactor (PENDING status, confirmation_url)
- KontourClient OIDC auth + real API
- KontourPoller (GetNewEvents polling)
- Delete DocuSignClient, update onboarding workflow
- Payment schemas update

**12-02: PostgreSQL Migration + Production Deploy**
- Alembic setup with async pattern
- PostgreSQL Docker service + tuning
- Data migration script (SQLite → PG)
- Full docker-compose.prod.yml (7 services)
- FastAPI lifespan with auto-migration
- SSL certbot setup
- UFW + Fail2ban hardening
- Deploy to iamaim.ru

**12-03: Monitoring, Alerting & FZ-152 Compliance**
- PostgreSQL exporter + Prometheus scrape config
- Alertmanager + Telegram alerts
- Sentry integration
- Grafana dashboards (PG metrics)
- FZ-152 data retention (partitioning + PartitionManager)
- Right-to-deletion endpoint
- RUNBOOK.md updates (PG + YooKassa scenarios)

---

*Research complete. Ready for planning.*
