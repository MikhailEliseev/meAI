# Plan 12-03: Deploy + Monitoring — Execution Summary

**Phase:** 12 Production Deployment
**Plan:** 03 of 03
**Completed:** 2026-05-18
**Status:** COMPLETE

## Tasks Completed

### Task 1: Production Docker Compose Stack (9 services)
- `AIM/docker-compose.yml` — expanded from 6 to 9 services
  - postgres, app, redis, nginx, prometheus, grafana, postgres-exporter, alertmanager, node-exporter
  - All services: `restart: unless-stopped`, `json-file` logging with rotation, resource limits
- `AIM/config/postgresql.conf` — PostgreSQL tuning (2GB container)
  - `shared_buffers=512MB`, `effective_cache_size=1536MB`, `work_mem=32MB`, `maintenance_work_mem=128MB`
  - SSD-optimized: `random_page_cost=1.1`, `effective_io_concurrency=200`
  - `statement_timeout=30s`, `idle_in_transaction_session_timeout=60s`
  - `log_min_duration_statement=1s` (slow query logging)
- `AIM/deploy/nginx/iamaim.conf` — Nginx production config
  - HTTP→HTTPS redirect, TLS 1.2/1.3, HSTS (63072000s), OCSP stapling
  - Security headers: X-Frame-Options DENY, X-Content-Type-Options nosniff, CSP
  - Proxy to app:8000 with timeout config
- `AIM/deploy/certbot/docker-compose.certbot.yml` — SSL auto-renewal
  - Standalone mode, iamaim.ru + www.iamaim.ru, post-hook nginx reload
- `AIM/deploy/firewall/setup-ufw.sh` — UFW: deny incoming, allow 22/80/443
- `AIM/deploy/firewall/jail.local` — Fail2ban: sshd (5 failures→10min), nginx-http-auth, nginx-botsearch

### Task 2: Prometheus Monitoring + Telegram Alerting + RUNBOOK
- `AIM/deploy/monitoring/rules.yml` — 7 new alert rules
  - `aim_postgresql` group: PostgresDown (critical, 1m), HighConnectionCount (warning, 5m), LowCacheHitRatio (warning, 10m), HighRollbackRate (warning, 5m), DiskSpaceLow (warning, 10m)
  - `aim_payments` group: PaymentFailureRate (critical, 5m), YooKassaWebhookMissing (warning, 30m)
- `AIM/deploy/monitoring/alertmanager.yml` — Telegram routing
  - Critical alerts → telegram-critical every 15min, warnings → telegram-warning every 1h
  - HTML parse mode, `${TELEGRAM_BOT_TOKEN}` and `${TELEGRAM_CHAT_ID}` env vars
- `AIM/prometheus.yml` — updated scrape configs
  - Added: alertmanager:9093, postgres-exporter:9187, node-exporter:9100
  - Rule files: `rules.yml`
- `AIM/src/aim/metrics.py` — 4 new business counters
  - `payments_total` (by status), `payment_failures_total` (by reason)
  - `yookassa_webhooks_total` (by event), `signings_total` (by status)
- `AIM/src/aim/main.py` — Sentry `send_default_pii=False`, GDPR router registered, PartitionManager in lifespan
- `AIM/deploy/RUNBOOK.md` — PostgreSQL + YooKassa scenarios
  - Added: PostgresDown, HighConnectionCount, PaymentFailureRate, YooKassaWebhookMissing procedures
  - Backup: `pg_dump | gzip` with cron automation (`0 3 * * *`)
  - DB size: PostgreSQL autovacuum monitoring
- `AIM/.env.example` — added `SENTRY_DSN`, `TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID`

### Task 3: ФЗ-152 Data Retention + GDPR Endpoint
- `AIM/src/aim/services/retention/partition_manager.py` — PostgreSQL Partition Manager
  - Partitioned tables: `leads`, `documents`, `fz152_audit_log`
  - Monthly partitions, 7-year retention, 3 future months auto-created
  - `ensure_partitions()` — run on startup + monthly cron
  - `run_retention_cycle()` — detach expired + drop orphans after 30-day grace
  - Raw SQL via `sqlalchemy.text()` for partition DDL
- `AIM/src/aim/api/gdpr.py` — Right-to-deletion endpoint (ФЗ-152 ст.21)
  - `DELETE /api/gdpr/leads/{lead_id}` — anonymizes PII, preserves metadata
  - Sets `name_encrypted→"DELETED"`, `phone_encrypted→""`, `email_encrypted→""`
  - Writes `FZ152AuditLog` with `action="gdpr_deletion_request"`
  - Returns 404 if not found, 409 if already anonymized
- `AIM/src/aim/models/fz152_audit.py` — Audit model (id, lead_id, action, ip_address, details JSON, agent, timestamp)

## Verification Results (all passed)

| Check | Result |
|-------|--------|
| Docker Compose services (9) | app, postgres, redis, nginx, prometheus, grafana, postgres-exporter, alertmanager, node-exporter |
| Monitoring configs | rules.yml OK, alertmanager.yml OK |
| Firewall/security | ufw OK, fail2ban OK |
| Nginx security headers | 3 headers (HSTS, X-Frame-Options, X-Content-Type-Options) |
| Business metrics | 4 new counters (payments_total, payment_failures_total, yookassa_webhooks_total, signings_total) |
| RUNBOOK updated | 3 alert procedures added |
| Python compile | partition_manager.py, gdpr.py, metrics.py, main.py — all OK |
| PostgreSQL config | shared_buffers + statement_timeout configured |
| Sentry PII | send_default_pii=False confirmed |

## Files Created/Modified

**Created (13 files):**
- `AIM/config/postgresql.conf`
- `AIM/deploy/nginx/iamaim.conf`
- `AIM/deploy/certbot/docker-compose.certbot.yml`
- `AIM/deploy/firewall/setup-ufw.sh`
- `AIM/deploy/firewall/jail.local`
- `AIM/deploy/monitoring/rules.yml`
- `AIM/deploy/monitoring/alertmanager.yml`
- `AIM/deploy/RUNBOOK.md`
- `AIM/src/aim/services/retention/__init__.py`
- `AIM/src/aim/services/retention/partition_manager.py`
- `AIM/src/aim/api/gdpr.py`
- `AIM/src/aim/models/fz152_audit.py`

**Modified (5 files):**
- `AIM/docker-compose.yml` — 6→9 services, PG tuned, Nginx updated
- `AIM/prometheus.yml` — alertmanager target, rules.yml, new scrape jobs
- `AIM/src/aim/metrics.py` — 4 business counters
- `AIM/src/aim/main.py` — Sentry PII, GDPR router, PartitionManager startup
- `AIM/.env.example` — monitoring env vars
