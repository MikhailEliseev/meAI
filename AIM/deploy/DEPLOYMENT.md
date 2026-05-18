# AIM Agency — Deployment Guide

**Last Updated:** 2026-05-18
**Stack:** FastAPI + SQLite + Redis + Nginx + Prometheus + Grafana

---

## Prerequisites

- **Server:** Linux (Ubuntu 22.04+), 2 vCPU, 4GB RAM, 20GB SSD
- **Software:** Docker 24+, Docker Compose v2+, git
- **Domain:** iamaim.ru with DNS pointing to server IP
- **Access:** SSH with sudo, ports 80/443 open

## Quick Deploy (Docker Compose)

```bash
# 1. Clone and enter
git clone <repo-url> /opt/aim
cd /opt/aim/AIM

# 2. Configure environment
cp .env.example .env.production
vim .env.production  # fill SECRET_KEY, API keys, SENTRY_DSN

# 3. Set up SSL (first run)
mkdir -p ssl
# Place fullchain.pem and privkey.pem in ssl/
# Or use certbot: certbot certonly --standalone -d iamaim.ru

# 4. Start all services
docker compose up -d

# 5. Verify
curl http://localhost:8000/health
curl http://localhost:9090/-/healthy   # Prometheus
curl http://localhost:3000/api/health  # Grafana
```

## Architecture

```
                  ┌─────────┐
                  │  Nginx   │  :80, :443 (TLS termination, rate limiting)
                  └────┬────┘
                       │
                  ┌────▼────┐
                  │   App    │  :8000 (FastAPI + uvicorn, 4 workers)
                  └────┬────┘
                       │
         ┌─────────────┼─────────────┐
         │             │             │
    ┌────▼───┐   ┌────▼────┐  ┌─────▼──────┐
    │  Redis  │   │ SQLite  │  │  Obsidian   │
    │  :6379  │   │  (file) │  │  (vaults)  │
    └─────────┘   └─────────┘  └────────────┘

Monitoring:
    App (:8000/metrics) → Prometheus (:9090) → Grafana (:3000)
```

## Environment Variables

Critical variables in `.env.production`:

```bash
ENVIRONMENT=production
DEBUG=false
SECRET_KEY=<openssl rand -hex 32>
DATABASE_URL=sqlite+aiosqlite:///./data/production/aim.db

# API keys
SEMRUSH_API_KEY=<key>
AHREFS_API_KEY=<key>
GA4_PROPERTY_ID=<id>
YANDEX_METRICA_COUNTER_ID=<id>

# Monitoring
SENTRY_DSN=https://<key>@sentry.io/<project>
ENABLE_METRICS=true
SLOW_QUERY_THRESHOLD_MS=100

# Security
AIM_ENCRYPTION_KEY=<python -c "import base64,os;print(base64.b64encode(os.urandom(32)).decode())">
RECAPTCHA_SECRET_KEY=<key>
```

Set restrictive permissions: `chmod 600 .env.production`

## SSL Certificates

### Option A: Let's Encrypt (recommended)

```bash
apt install certbot
certbot certonly --standalone -d iamaim.ru -d www.iamaim.ru

# Auto-renewal cron (monthly)
echo "0 0 1 * * certbot renew --quiet --post-hook 'docker compose -f /opt/aim/AIM/docker-compose.yml reload nginx'" | crontab -

# Link to ssl directory
ln -sf /etc/letsencrypt/live/iamaim.ru/fullchain.pem ssl/fullchain.pem
ln -sf /etc/letsencrypt/live/iamaim.ru/privkey.pem ssl/privkey.pem
```

### Option B: Self-signed (development only)

```bash
mkdir -p ssl
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
  -keyout ssl/privkey.pem -out ssl/fullchain.pem \
  -subj "/CN=iamaim.ru"
```

## Monitoring Setup

### Prometheus

Access: `http://<server>:9090`
Config: `deploy/prometheus.yml` (scrape config)

### Grafana

Access: `http://<server>:3000` (default: admin/admin, change immediately)

Pre-configured dashboards in `deploy/grafana/dashboards/`:
- AIM Overview (request rate, latency, errors)
- Business Metrics (leads, scoring, tiers)
- Database (slow queries, connection pool)

### Sentry

Set `SENTRY_DSN` in `.env.production` for error tracking with:
- FastAPI integration (transaction tracing)
- SQLAlchemy integration (query tracking)
- Environment tagging (production/staging)

## Health Checks

| Endpoint | Purpose | Expected |
|----------|---------|----------|
| `GET /health` | Liveness (process running) | 200 `{"status":"healthy"}` |
| `GET /ready` | Readiness (DB, Redis up) | 200 `{"status":"ready"}` |
| `GET /metrics` | Prometheus scrape | 200 (text/plain) |
| `GET /api/performance/stats` | Query profiling | 200 (JSON) |

Docker health checks run every 30s with 3 retries before marking unhealthy.

## Backup

### Database

```bash
# Manual backup
cp data/production/aim.db "data/production/backups/aim_$(date +%Y%m%d_%H%M%S).db"

# Automated (cron, daily at 3am)
0 3 * * * cp /opt/aim/AIM/data/production/aim.db /opt/aim/AIM/data/production/backups/aim_$(date +\%Y\%m\%d).db
```

### Obsidian Vaults

```bash
tar -czf "obsidian_backup_$(date +%Y%m%d).tar.gz" AIM/obsidian/
```

### Restore

```bash
docker compose stop app
cp data/production/backups/aim_20260518.db data/production/aim.db
docker compose start app
```

## Scaling

### Vertical (single server)

Increase uvicorn workers in `Dockerfile`:
```
CMD ["uvicorn", "...", "--workers", "8"]  # 2× CPU cores
```

### Horizontal (multiple servers)

For multi-server, switch SQLite → PostgreSQL:
```bash
DATABASE_URL=postgresql+asyncpg://user:pass@postgres:5432/aim
```

Add to `docker-compose.yml`:
```yaml
postgres:
  image: postgres:16-alpine
  volumes:
    - postgres-data:/var/lib/postgresql/data
```

## Security Hardening

- [x] TLS 1.2+ with strong ciphers
- [x] Security headers (HSTS, X-Frame-Options, CSP)
- [x] `/metrics` restricted to localhost
- [x] Rate limiting (10 req/s per IP on API)
- [x] AES-256-GCM encryption for PII fields
- [x] reCAPTCHA v3 on lead capture
- [x] ФЗ-152 audit logging
- [ ] UFW firewall (allow 80, 443, 22 only)
- [ ] Fail2ban for SSH protection

Post-deploy hardening:
```bash
ufw allow 22/tcp
ufw allow 80/tcp
ufw allow 443/tcp
ufw enable
```

## Verification Checklist

After deployment, run:

```bash
# 1. Health checks
curl -s http://iamaim.ru/health | jq .
curl -s http://iamaim.ru/ready | jq .

# 2. Lead capture
curl -s -X POST http://iamaim.ru/api/leads \
  -H "Content-Type: application/json" \
  -d '{"name":"Test","phone":"+79001234567","email":"test@test.com","specialty":"dentistry","source":"landing_page","fz152_consent":true,"recaptcha_token":"test"}' | jq .

# 3. Metrics
curl -s http://localhost:8000/metrics | grep aim_leads

# 4. Prometheus targets
curl -s http://localhost:9090/api/v1/targets | jq '.data.activeTargets[] | {scrapeUrl, health}'

# 5. Grafana health
curl -s http://localhost:3000/api/health

# 6. Performance
curl -s http://iamaim.ru/api/performance/stats | jq .
```

## Common Issues

| Problem | Check |
|---------|-------|
| 502 Bad Gateway | `docker compose logs app` |
| SSL cert expired | `certbot renew --dry-run` |
| DB locked | `fuser data/production/aim.db` |
| High latency | `GET /api/performance/stats` → slow queries |
| No leads | `curl -X POST .../api/leads` → test capture manually |

For detailed troubleshooting, see [TROUBLESHOOTING.md](../docs/TROUBLESHOOTING.md).
For incident response, see [RUNBOOK.md](RUNBOOK.md).
