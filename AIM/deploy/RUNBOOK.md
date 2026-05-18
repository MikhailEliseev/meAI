# AIM Agency — Operations Runbook

## Service Overview

| Component | Port | Health Check | Metrics |
|-----------|------|-------------|---------|
| AIM API | 8000 | /health, /ready | /metrics |
| PostgreSQL | 5432 | pg_isready | PG exporter :9187 |
| Redis | 6379 | PING | — |
| Prometheus | 9090 | /-/healthy | — |
| Grafana | 3000 | /api/health | — |
| Alertmanager | 9093 | /-/healthy | — |

## Common Alerts

### ServiceDown (CRITICAL)

Service unreachable for >2 min.

1. `systemctl status aim-api` — check if process is running
2. `journalctl -u aim-api -n 100` — recent logs
3. `uvicorn aim.main:app --reload` — restart manually if needed
4. Check disk space: `df -h`

### HighErrorRate (CRITICAL)

Error rate >5% over 5 min.

1. Check Sentry dashboard for grouped errors
2. `GET /api/performance/stats` — check slow queries
3. Check DB: `ls -lh AIM/data/aim.db` — file size/permissions
4. If after deploy: rollback to last known good version

### NoLeadsCaptured (WARNING)

Zero leads for 1+ hour.

1. `curl -X POST http://localhost:8000/api/leads ...` — test capture
2. Check frontend form is loading: visit iamaim.ru
3. Check reCAPTCHA: Google may have changed API
4. Check rate limit stats: `GET /api/performance/stats`

### RateLimitSpike (WARNING)

Abnormal rate limit triggers.

1. Check access logs: `journalctl -u aim-api | grep "rate_limit"`
2. Identify abusive IPs
3. If legitimate traffic: adjust `RATE_LIMIT_PER_MINUTE` env var
4. If attack: add IP to firewall

### PostgresDown (CRITICAL)

PostgreSQL unreachable for >1min.

1. `docker ps | grep postgres` — check container running
2. `docker logs aim-postgres --tail 50` — check PG logs
3. `docker restart aim-postgres` — restart if hung
4. Check disk: `df -h /var/lib/docker/volumes/`
5. If data corruption: restore from backup (see Backup & Recovery)

### HighConnectionCount (WARNING)

Active connections >80% of max_connections.

1. `docker exec aim-postgres psql -U aim_user -d aim_db -c "SELECT count(*) FROM pg_stat_activity;"`
2. `docker exec aim-postgres psql -U aim_user -d aim_db -c "SELECT application_name, count(*) FROM pg_stat_activity GROUP BY application_name;"`
3. Kill idle connections: `SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE state = 'idle in transaction';`
4. If persistent: increase pool_size in database.py or restart app

### PaymentFailureRate (CRITICAL)

Payment failure rate >5% over 5min.

1. Check YooKassa status: https://status.yookassa.ru
2. `docker logs aim-app --tail 100 | grep "[YOOKASSA]"` — check payment logs
3. `docker exec aim-postgres psql -U aim_user -d aim_db -c "SELECT status, count(*) FROM payments WHERE created_at > NOW() - INTERVAL '1 hour' GROUP BY status;"`
4. Verify YOOKASSA_SECRET_KEY is valid in .env.production
5. If YooKassa outage: payments will auto-retry via webhook when restored

### YooKassaWebhookMissing (WARNING)

No webhooks received for 30min while payments were initiated.

1. Check webhook endpoint accessible: `curl -X POST http://localhost:8000/api/webhooks/yookassa/payment`
2. Check YooKassa merchant dashboard for webhook delivery logs
3. Verify Nginx is not blocking YooKassa IP ranges (185.71.76.0/27, etc.)
4. Check webhook URL registered in YooKassa settings: POST https://iamaim.ru/api/webhooks/yookassa/payment

## Health Check Endpoints

```bash
# Basic health (is process alive?)
curl http://localhost:8000/health

# Readiness (are dependencies available?)
curl http://localhost:8000/ready

# Performance stats (query profiling)
curl http://localhost:8000/api/performance/stats

# Clear analytics cache
curl -X POST http://localhost:8000/api/performance/cache/clear
```

## Backup & Recovery

### Database Backup (PostgreSQL)

```bash
docker exec aim-postgres pg_dump -U aim_user aim_db | gzip > "backups/aim_$(date +%Y%m%d_%H%M%S).sql.gz"
```

### Restore (PostgreSQL)

```bash
gunzip -c backups/aim_20260518_120000.sql.gz | docker exec -i aim-postgres psql -U aim_user aim_db
```

### Automatic Backups (cron)

```bash
0 3 * * * cd /opt/aim && docker exec aim-postgres pg_dump -U aim_user aim_db | gzip > backups/aim_$(date +\%Y\%m\%d).sql.gz
```

## Logging

- **Structured logs:** JSON format to stdout → `journalctl -u aim-api -f`
- **Query profiling:** Slow queries (>100ms) logged at WARNING level
- **Audit logs:** ФЗ-152 events in `fz152_audit_log` table + structlog
- **Sentry:** Errors grouped with full context (env, user, stacktrace)

## Performance Tuning

- **Slow queries:** Check `/api/performance/stats` → add missing indexes
- **Cache hit rate:** Monitor `aim_cache_hits_total` vs misses
- **Memory:** If RSS >2GB, clear analytics cache: `POST /api/performance/cache/clear`
- **DB size:** VACUUM runs automatically via autovacuum. Monitor: `docker exec aim-postgres psql -U aim_user -d aim_db -c "SELECT pg_size_pretty(pg_database_size('aim_db'));"`
