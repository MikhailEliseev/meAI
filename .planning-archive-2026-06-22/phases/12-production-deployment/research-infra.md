# Phase 12: Production Deployment - Infrastructure Research

> **Date:** 2026-05-18
> **Status:** Research Complete
> **Sources:** Exa web search, Context7 (prometheus/alertmanager, postgresql docs), sentry.io docs, docker.com docs

---

## Table of Contents
1. [PostgreSQL Migration (SQLite → PostgreSQL)](#1-postgresql-migration-sqlite--postgresql)
2. [Docker Compose Production Deploy](#2-docker-compose-production-deploy)
3. [SSL & Security](#3-ssl--security)
4. [Monitoring Additions](#4-monitoring-additions)
5. [FZ-152 Data Retention](#5-fz-152-data-retention)

---

## 1. PostgreSQL Migration (SQLite → PostgreSQL)

### 1.1 SQLAlchemy 2.0 Async with asyncpg

**DATABASE_URL format:**
```
postgresql+asyncpg://user:password@host:5432/dbname
```

**Key dependencies to add to `requirements.txt`:**
```
asyncpg>=0.29.0,<0.30.0
alembic>=1.14.0,<2.0.0
```

**Current codebase impact:**

The project already uses SQLAlchemy 2.0 async (`AIM/src/aim/database.py`). The main change is switching the connection URL from `sqlite+aiosqlite:///...` to `postgresql+asyncpg://...`.

```python
# AIM/src/aim/database.py — updated for PostgreSQL
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import DeclarativeBase

from aim.config import get_settings

settings = get_settings()

# PostgreSQL async engine
engine = create_async_engine(
    settings.database_url,  # postgresql+asyncpg://user:pass@host:5432/aim
    echo=settings.debug,
    pool_size=20,            # Default: 5, increase for production
    max_overflow=10,         # Extra connections beyond pool_size
    pool_pre_ping=True,      # Verify connections before use
    pool_recycle=3600,       # Recycle connections every hour
)

AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)

class Base(DeclarativeBase):
    pass


async def get_db() -> AsyncSession:
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()
```

**Pool sizing guidelines:**
- `pool_size`: ~20% of max_connections (default PG max is 100)
- `max_overflow`: 10 connections above pool_size
- `pool_pre_ping=True`: tests connections before use (prevents stale connection errors)
- `pool_recycle=3600`: recycles after 1 hour (good default)

### 1.2 Alembic Setup for Async

**CRITICAL ISSUE:** Alembic's default `env.py` uses `engine_from_config()` which does NOT support async drivers like `asyncpg`. Without the correct bridging pattern, migrations either fail at runtime or autogenerate produces empty migration files.

**The FIX — Required `alembic/env.py` pattern:**

```python
# alembic/env.py
import asyncio
import os
from logging.config import fileConfig

from sqlalchemy import pool
from sqlalchemy.ext.asyncio import async_engine_from_config
from alembic import context

from aim.database import Base
# CRITICAL: Import ALL models so Base.metadata knows about them
import aim.models  # noqa: F401 — side-effect import registers models

config = context.config
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata

# Override sqlalchemy.url from environment if not in alembic.ini
db_url = os.getenv("DATABASE_URL")
if db_url:
    config.set_main_option("sqlalchemy.url", db_url)


def do_run_migrations(connection):
    """Runs migrations in a sync context (called via run_sync)."""
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
    )
    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations():
    """Create async engine, then bridge to sync migration runner."""
    connectable = async_engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,  # No pooling for migration runs
    )
    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)
    await connectable.dispose()


def run_migrations_online():
    """Entry point — runs async migrations via asyncio.run()."""
    asyncio.run(run_async_migrations())


# Wire up Alembic to use our async-aware runner
if context.is_offline_mode():
    context.configure(
        url=config.get_main_option("sqlalchemy.url"),
        target_metadata=target_metadata,
        literal_binds=True,
    )
    with context.begin_transaction():
        context.run_migrations()
else:
    run_migrations_online()
```

**`alembic.ini` changes:**
```ini
[alembic]
script_location = alembic
# Comment out the hardcoded URL — we set it from env var
# sqlalchemy.url = driver://user:pass@localhost/dbname

# Or set it for local dev:
sqlalchemy.url = postgresql+asyncpg://aim_user:aim_pass@localhost:5432/aim_db
```

**Four steps that MUST all be correct:**
1. Replace `engine_from_config()` with `async_engine_from_config()`
2. Wrap sync migration runner in `connection.run_sync()`
3. Use `pool.NullPool` (migrations are short-lived, no pooling needed)
4. Import ALL models before touching `Base.metadata` (otherwise autogenerate produces empty migrations)

### 1.3 Alembic Commands

```bash
# Initialize alembic with async template
alembic init -t async alembic

# After modifying models — autogenerate a new revision
alembic revision --autogenerate -m "add_patient_table"

# Apply all pending migrations
alembic upgrade head

# Roll back one migration
alembic downgrade -1

# Show current migration status
alembic current

# Show migration history
alembic history

# Generate SQL for a migration (review before apply)
alembic upgrade head --sql
```

### 1.4 Auto-migrate on FastAPI Startup (Production Pattern)

```python
# AIM/src/aim/main.py
import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI
from alembic.config import Config
from alembic import command
import logging

logger = logging.getLogger("uvicorn")


def run_migrations_sync():
    """Run alembic in a sync thread (required because alembic is sync)."""
    alembic_cfg = Config("alembic.ini")
    command.upgrade(alembic_cfg, "head")


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting up...")
    logger.info("Running alembic upgrade head...")
    # alembic is sync, must run in thread to not block event loop
    await asyncio.to_thread(run_migrations_sync)
    logger.info("Migrations complete.")
    yield
    logger.info("Shutting down...")


app = FastAPI(lifespan=lifespan)
```

### 1.5 Data Migration: SQLite → PostgreSQL

**Strategy:**

Option A — **SQLAlchemy Migration Script (recommended for dev/small data):**
```python
# scripts/migrate_sqlite_to_pg.py
import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from aim.database import Base
from aim.models import *  # Import all models

SQLITE_URL = "sqlite+aiosqlite:///./AIM/data/aim.db"
PG_URL = "postgresql+asyncpg://aim_user:aim_pass@localhost:5432/aim_db"

async def migrate():
    sqlite_engine = create_async_engine(SQLITE_URL)
    pg_engine = create_async_engine(PG_URL)

    # Create tables in PG
    async with pg_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # Copy data table by table
    sqlite_session = sessionmaker(sqlite_engine, class_=AsyncSession)
    pg_session = sessionmaker(pg_engine, class_=AsyncSession)

    async with sqlite_session() as src, pg_session() as dst:
        for table_name, table in Base.metadata.tables.items():
            result = await src.execute(table.select())
            rows = result.fetchall()
            for row in rows:
                dst.add(table.insert().values(**row._mapping))
            await dst.commit()
            print(f"Migrated {len(rows)} rows from {table_name}")

    await sqlite_engine.dispose()
    await pg_engine.dispose()

asyncio.run(migrate())
```

Option B — **pgloader (for larger datasets):**
```bash
# pgloader can convert SQLite to PostgreSQL directly
pgloader sqlite:///AIM/data/aim.db postgresql://aim_user:aim_pass@localhost:5432/aim_db
```

Option C — **Dump & Restore (for PostgreSQL → PostgreSQL):**
```bash
# Dump
pg_dump -h source_host -U user -d aim_db -Fc -f aim_backup.dump

# Restore
pg_restore -h target_host -U user -d aim_db --clean --if-exists aim_backup.dump
```

### 1.6 PostgreSQL Docker Configuration

**`postgres:16-alpine` with mounted config and init scripts:**

```yaml
# docker-compose.yml — PostgreSQL service
services:
  postgres:
    image: postgres:16-alpine
    container_name: aim-postgres
    restart: unless-stopped
    environment:
      POSTGRES_USER: ${POSTGRES_USER:-aim_user}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
      POSTGRES_DB: ${POSTGRES_DB:-aim_db}
      PGDATA: /var/lib/postgresql/data/pgdata
      # Russian locale for sorting
      POSTGRES_INITDB_ARGS: "--locale=ru_RU.UTF-8"
    ports:
      - "127.0.0.1:5432:5432"  # Bind only to localhost for security
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./init-scripts:/docker-entrypoint-initdb.d  # SQL init scripts
      - ./config/postgresql.conf:/etc/postgresql/postgresql.conf:ro
    command: postgres -c config_file=/etc/postgresql/postgresql.conf
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${POSTGRES_USER:-aim_user} -d ${POSTGRES_DB:-aim_db}"]
      interval: 10s
      timeout: 5s
      retries: 5
      start_period: 30s
    deploy:
      resources:
        limits:
          cpus: '2'
          memory: 2G
        reservations:
          cpus: '1'
          memory: 1G
    logging:
      driver: "json-file"
      options:
        max-size: "50m"
        max-file: "5"
    networks:
      - backend

volumes:
  postgres_data:
    driver: local

networks:
  backend:
    driver: bridge
```

**`config/postgresql.conf` — Production tuning for 2GB RAM container:**
```conf
# Memory (based on 2GB container limit)
shared_buffers = 512MB           # 25% of 2GB
effective_cache_size = 1536MB    # 75% of 2GB
work_mem = 32MB                  # Per-operation memory
maintenance_work_mem = 256MB     # For VACUUM, CREATE INDEX

# SSD optimizations
effective_io_concurrency = 200   # 200 for SSDs, 2 for HDDs
random_page_cost = 1.1           # Lower for SSDs (default 4.0)

# Write-Ahead Log (WAL)
wal_level = replica              # Required for backups
max_wal_size = 2GB
min_wal_size = 512MB
wal_buffers = 16MB

# Connection limits
max_connections = 100
superuser_reserved_connections = 5

# Query timeouts (prevent runaway queries)
statement_timeout = 30000        # 30 seconds max per statement
lock_timeout = 10000             # 10 seconds waiting for lock
idle_in_transaction_session_timeout = 60000  # 60 seconds

# Autovacuum (critical for production)
autovacuum = on
autovacuum_analyze_scale_factor = 0.05
autovacuum_vacuum_scale_factor = 0.1

# Logging
log_destination = 'stderr'
logging_collector = on
log_directory = '/var/lib/postgresql/data/logs'
log_filename = 'postgresql-%Y-%m-%d.log'
log_rotation_age = 7d
log_min_duration_statement = 1000  # Log queries taking > 1 second
log_line_prefix = '%t [%p]: [%l-1] user=%u,db=%d,app=%a,client=%h '
```

---

## 2. Docker Compose Production Deploy

### 2.1 Production `docker-compose.yml` — Full Stack

```yaml
# docker-compose.prod.yml
version: '3.8'

services:
  # ============================================================
  # Nginx Reverse Proxy + SSL Termination
  # ============================================================
  nginx:
    image: nginx:1.27-alpine
    container_name: aim-nginx
    restart: unless-stopped
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx/nginx.conf:/etc/nginx/nginx.conf:ro
      - ./nginx/conf.d:/etc/nginx/conf.d:ro
      - ./nginx/ssl:/etc/nginx/ssl:ro
      - ./certbot/www:/var/www/certbot:ro
      - certbot_certs:/etc/letsencrypt:ro
    depends_on:
      - api
    networks:
      - frontend
    logging:
      driver: "json-file"
      options:
        max-size: "50m"
        max-file: "5"
    deploy:
      resources:
        limits:
          cpus: '0.5'
          memory: 256M

  # ============================================================
  # Certbot — Let's Encrypt SSL auto-renewal
  # ============================================================
  certbot:
    image: certbot/certbot:latest
    container_name: aim-certbot
    volumes:
      - certbot_certs:/etc/letsencrypt
      - ./certbot/www:/var/www/certbot
    entrypoint: "/bin/sh -c 'trap exit TERM; while :; do certbot renew --quiet; sleep 12h; done'"
    restart: unless-stopped
    networks:
      - frontend

  # ============================================================
  # FastAPI Application
  # ============================================================
  api:
    build:
      context: .
      dockerfile: Dockerfile
    container_name: aim-api
    restart: unless-stopped
    env_file:
      - .env.production
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy
    healthcheck:
      test: ["CMD-SHELL", "curl -f http://localhost:8000/health || exit 1"]
      interval: 30s
      timeout: 5s
      retries: 3
      start_period: 10s
    volumes:
      - ./reports:/app/reports
      - ./logs:/app/logs
    networks:
      - frontend
      - backend
    logging:
      driver: "json-file"
      options:
        max-size: "100m"
        max-file: "5"
    deploy:
      resources:
        limits:
          cpus: '1.0'
          memory: 512M
        reservations:
          cpus: '0.25'
          memory: 128M

  # ============================================================
  # PostgreSQL Database
  # ============================================================
  postgres:
    image: postgres:16-alpine
    container_name: aim-postgres
    restart: unless-stopped
    environment:
      POSTGRES_USER: ${POSTGRES_USER:-aim_user}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
      POSTGRES_DB: ${POSTGRES_DB:-aim_db}
      PGDATA: /var/lib/postgresql/data/pgdata
      POSTGRES_INITDB_ARGS: "--locale=ru_RU.UTF-8"
    ports:
      - "127.0.0.1:5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./init-scripts:/docker-entrypoint-initdb.d
      - ./config/postgresql.conf:/etc/postgresql/postgresql.conf:ro
    command: postgres -c config_file=/etc/postgresql/postgresql.conf
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${POSTGRES_USER:-aim_user} -d ${POSTGRES_DB:-aim_db}"]
      interval: 10s
      timeout: 5s
      retries: 5
      start_period: 30s
    networks:
      - backend
    logging:
      driver: "json-file"
      options:
        max-size: "50m"
        max-file: "5"
    deploy:
      resources:
        limits:
          cpus: '2'
          memory: 2G
        reservations:
          cpus: '1'
          memory: 1G

  # ============================================================
  # Redis (for caching, rate limiting)
  # ============================================================
  redis:
    image: redis:7-alpine
    container_name: aim-redis
    restart: unless-stopped
    command: redis-server --appendonly yes --maxmemory 256mb --maxmemory-policy allkeys-lru
    ports:
      - "127.0.0.1:6379:6379"
    volumes:
      - redis_data:/data
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 5s
      retries: 3
    networks:
      - backend
    logging:
      driver: "json-file"
      options:
        max-size: "20m"
        max-file: "3"
    deploy:
      resources:
        limits:
          cpus: '0.5'
          memory: 512M

  # ============================================================
  # Prometheus — Metrics Collection
  # ============================================================
  prometheus:
    image: prom/prometheus:latest
    container_name: aim-prometheus
    restart: unless-stopped
    command:
      - '--config.file=/etc/prometheus/prometheus.yml'
      - '--storage.tsdb.path=/prometheus'
      - '--storage.tsdb.retention.time=30d'
      - '--web.console.libraries=/etc/prometheus/console_libraries'
      - '--web.console.templates=/etc/prometheus/consoles'
    ports:
      - "127.0.0.1:9090:9090"
    volumes:
      - ./monitoring/prometheus.yml:/etc/prometheus/prometheus.yml:ro
      - ./monitoring/rules.yml:/etc/prometheus/rules.yml:ro
      - prometheus_data:/prometheus
    networks:
      - monitoring
    logging:
      driver: "json-file"
      options:
        max-size: "50m"
        max-file: "5"

  # ============================================================
  # PostgreSQL Exporter — PG Metrics for Prometheus
  # ============================================================
  postgres-exporter:
    image: quay.io/prometheuscommunity/postgres-exporter:latest
    container_name: aim-pg-exporter
    restart: unless-stopped
    environment:
      DATA_SOURCE_URI: "postgres:5432/${POSTGRES_DB:-aim_db}?sslmode=disable"
      DATA_SOURCE_USER: "${POSTGRES_USER:-aim_user}"
      DATA_SOURCE_PASS: "${POSTGRES_PASSWORD}"
    ports:
      - "127.0.0.1:9187:9187"
    depends_on:
      postgres:
        condition: service_healthy
    networks:
      - monitoring
      - backend
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"

  # ============================================================
  # Alertmanager — Alert Routing
  # ============================================================
  alertmanager:
    image: prom/alertmanager:latest
    container_name: aim-alertmanager
    restart: unless-stopped
    command:
      - '--config.file=/etc/alertmanager/alertmanager.yml'
      - '--storage.path=/alertmanager'
    ports:
      - "127.0.0.1:9093:9093"
    volumes:
      - ./monitoring/alertmanager.yml:/etc/alertmanager/alertmanager.yml:ro
      - alertmanager_data:/alertmanager
    networks:
      - monitoring
    logging:
      driver: "json-file"
      options:
        max-size: "20m"
        max-file: "3"

volumes:
  postgres_data:
    driver: local
  redis_data:
    driver: local
  prometheus_data:
    driver: local
  alertmanager_data:
    driver: local
  certbot_certs:
    driver: local

networks:
  frontend:
    driver: bridge
  backend:
    driver: bridge
  monitoring:
    driver: bridge
```

### 2.2 Restart Policies — When to Use What

| Policy | Use Case |
|---|---|
| `unless-stopped` | **Default for production.** Restarts on crash and reboot, but respects `docker compose stop`. |
| `always` | Avoid — restarts even after manual stop. Use only if uptime is absolutely critical. |
| `on-failure` | One-off jobs (migrations, seed scripts). |
| `no` | Debug containers, temporary tools. |

### 2.3 Resource Limits

Always set limits to prevent one container from starving others:

```yaml
deploy:
  resources:
    limits:          # Hard cap — container is killed if exceeded
      cpus: '1.0'
      memory: 512M
    reservations:    # Soft minimum — Docker will try to guarantee
      cpus: '0.25'
      memory: 128M
```

**For a 4GB VPS:**
- PostgreSQL: 2GB limit (needs RAM for shared_buffers)
- API (FastAPI): 512MB limit
- Redis: 512MB limit
- Nginx: 256MB limit
- Monitoring stack: 512MB shared

### 2.4 Logging — JSON File with Rotation

Without rotation, a busy service can fill disk in hours:

```yaml
logging:
  driver: "json-file"
  options:
    max-size: "50m"   # Rotate after 50 MB
    max-file: "5"     # Keep 5 rotated files (250 MB max per service)
```

### 2.5 Secrets Management

```bash
# .env.production — on server ONLY, chmod 600
POSTGRES_USER=aim_user
POSTGRES_PASSWORD=<generate-64-char-random>
POSTGRES_DB=aim_db
DATABASE_URL=postgresql+asyncpg://aim_user:<password>@postgres:5432/aim_db
SENTRY_DSN=https://xxx@sentry.io/xxx
REDIS_URL=redis://redis:6379/0
TELEGRAM_BOT_TOKEN=<bot-token>
TELEGRAM_CHAT_ID=<chat-id>
```

```bash
# On server
chmod 600 .env.production
echo ".env.production" >> .gitignore
```

### 2.6 Production Checklist

- [ ] Health checks on all services (verify functionality, not just process alive)
- [ ] Restart policy: `unless-stopped` on all services
- [ ] Resource limits on all services (memory at minimum)
- [ ] Named volumes for persistent data (postgres, redis, prometheus)
- [ ] Log rotation configured on all services
- [ ] `.env.production` with chmod 600, never in git
- [ ] Bind databases to `127.0.0.1` (not `0.0.0.0`)
- [ ] Network isolation: frontend, backend, monitoring segments
- [ ] `depends_on` with `condition: service_healthy` (not just `service_started`)

---

## 3. SSL & Security

### 3.1 Let's Encrypt + Certbot in Docker Compose

**Initial certificate acquisition (run once):**

```bash
# First run: get certificate using standalone mode
docker compose -f docker-compose.prod.yml run --rm certbot certonly \
  --standalone \
  --preferred-challenges http \
  -d iamaim.ru \
  -d www.iamaim.ru \
  --email me@mikhaileliseev.com \
  --agree-tos \
  --no-eff-email
```

**Auto-renewal via the certbot container:**

The certbot service (defined in section 2.1) runs an infinite loop checking every 12 hours:
```
entrypoint: "/bin/sh -c 'trap exit TERM; while :; do certbot renew --quiet; sleep 12h; done'"
```

Certs renew automatically when they have < 30 days of validity left.

### 3.2 Nginx TLS Configuration

```nginx
# nginx/conf.d/iamaim.ru.conf
server {
    listen 80;
    server_name iamaim.ru www.iamaim.ru;

    # Let's Encrypt ACME challenge
    location /.well-known/acme-challenge/ {
        root /var/www/certbot;
    }

    # Redirect all other HTTP to HTTPS
    location / {
        return 301 https://$host$request_uri;
    }
}

server {
    listen 443 ssl http2;
    server_name iamaim.ru www.iamaim.ru;

    # SSL Certificate
    ssl_certificate     /etc/letsencrypt/live/iamaim.ru/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/iamaim.ru/privkey.pem;

    # Strong ciphers (TLS 1.2+, no weak ciphers)
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256:ECDHE-ECDSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-GCM-SHA384:ECDHE-ECDSA-CHACHA20-POLY1305:ECDHE-RSA-CHACHA20-POLY1305;
    ssl_prefer_server_ciphers off;

    # OCSP Stapling
    ssl_stapling on;
    ssl_stapling_verify on;
    resolver 1.1.1.1 8.8.8.8 valid=300s;
    resolver_timeout 5s;

    # Security headers
    add_header Strict-Transport-Security "max-age=63072000; includeSubDomains; preload" always;
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Referrer-Policy "strict-origin-when-cross-origin" always;

    # Session cache
    ssl_session_cache shared:SSL:10m;
    ssl_session_timeout 10m;

    # File upload limit
    client_max_body_size 50M;

    # Proxy to FastAPI
    location / {
        proxy_pass http://api:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 120s;
    }

    # Health check (no auth)
    location /health {
        proxy_pass http://api:8000/health;
        proxy_set_header Host $host;
    }

    # Metrics (internal only)
    location /metrics {
        allow 127.0.0.1;
        allow 10.0.0.0/8;
        deny all;
        proxy_pass http://api:8000/metrics;
    }
}
```

### 3.3 UFW Firewall Rules

```bash
# Install and configure UFW
sudo apt update && sudo apt install ufw -y

# Default deny incoming, allow outgoing
sudo ufw default deny incoming
sudo ufw default allow outgoing

# Allow SSH, HTTP, HTTPS
sudo ufw allow 22/tcp
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp

# Optional: allow monitoring on localhost only
sudo ufw allow from 127.0.0.1 to any port 9090
sudo ufw allow from 127.0.0.1 to any port 9093

# Enable firewall
sudo ufw enable

# Verify
sudo ufw status verbose
```

### 3.4 Fail2ban for SSH Protection

```bash
sudo apt install fail2ban -y

# /etc/fail2ban/jail.local
# [sshd]
# enabled = true
# bantime = 3600        # 1 hour ban
# findtime = 600        # 10 minute window
# maxretry = 5          # 5 failed attempts → ban

sudo systemctl enable fail2ban
sudo systemctl start fail2ban
```

---

## 4. Monitoring Additions

### 4.1 PostgreSQL Exporter — Key Metrics

**Critical PG metrics to monitor:**

| Metric | PromQL | What It Tells You |
|---|---|---|
| **DB Up** | `pg_up` | 1 = database is up |
| **Active Connections** | `pg_stat_database_numbackends` | Current connection count |
| **Connection Usage %** | `pg_stat_database_numbackends / pg_settings_max_connections` | How close to max_connections |
| **Cache Hit Ratio** | `pg_stat_database_blks_hit / (pg_stat_database_blks_hit + pg_stat_database_blks_read)` | Should be > 99% |
| **Transaction Rate** | `rate(pg_stat_database_xact_commit[5m])` | Commits per second |
| **Rollback Rate** | `rate(pg_stat_database_xact_rollback[5m])` | Should be near zero |
| **Database Size** | `pg_database_size_bytes` | Total DB size in bytes |
| **Disk Growth Prediction** | `predict_linear(pg_database_size_bytes[1h], 86400 * 7)` | Projected size in 7 days |
| **Longest Running Query** | `pg_stat_activity_max_tx_duration` | Seconds of longest active transaction |
| **Locks Waiting** | `pg_stat_database_conflicts` | Number of conflicting locks |
| **Exporter Healthy** | `pg_exporter_last_scrape_error` | 0 = no errors |

**Prometheus scrape config:**

```yaml
# monitoring/prometheus.yml
global:
  scrape_interval: 15s
  evaluation_interval: 10s

rule_files:
  - '/etc/prometheus/rules.yml'

alerting:
  alertmanagers:
    - static_configs:
        - targets: ['alertmanager:9093']

scrape_configs:
  # PostgreSQL Exporter
  - job_name: 'postgres'
    static_configs:
      - targets: ['postgres-exporter:9187']

  # FastAPI Application Metrics
  - job_name: 'aim-api'
    static_configs:
      - targets: ['api:8000']
    metrics_path: '/metrics'

  # Node Exporter (host-level metrics)
  - job_name: 'node'
    static_configs:
      - targets: ['node-exporter:9100']
```

### 4.2 Prometheus Alert Rules

```yaml
# monitoring/rules.yml
groups:
  - name: postgres
    rules:
      - alert: PostgresDown
        expr: pg_up == 0
        for: 1m
        labels:
          severity: critical
        annotations:
          summary: "PostgreSQL is DOWN"
          description: "PostgreSQL instance has been down for > 1m"

      - alert: PostgresHighConnections
        expr: (pg_stat_database_numbackends / pg_settings_max_connections) > 0.8
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "PostgreSQL connections > 80%"
          description: "{{ $value | humanizePercentage }} connections used"

      - alert: PostgresLowCacheHitRatio
        expr: (pg_stat_database_blks_hit / (pg_stat_database_blks_hit + pg_stat_database_blks_read)) < 0.99
        for: 15m
        labels:
          severity: warning
        annotations:
          summary: "PostgreSQL cache hit ratio < 99%"
          description: "Cache hit ratio is {{ $value | humanizePercentage }} — consider increasing shared_buffers"

      - alert: PostgresDiskGrowthWarning
        expr: predict_linear(pg_database_size_bytes[1h], 86400 * 7) > 50 * 1024 * 1024 * 1024
        for: 10m
        labels:
          severity: warning
        annotations:
          summary: "PostgreSQL projected > 50GB in 7 days"
          description: "Disk growth rate indicates {{ $value | humanize1024 }}B in a week"

      - alert: PostgresHighRollbacks
        expr: rate(pg_stat_database_xact_rollback[5m]) > rate(pg_stat_database_xact_commit[5m]) * 0.05
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "High transaction rollback rate"
          description: "Rollback rate is > 5% of commit rate"

  - name: api
    rules:
      - alert: ApiDown
        expr: up{job="aim-api"} == 0
        for: 1m
        labels:
          severity: critical
        annotations:
          summary: "AIM API is DOWN"
          description: "API has been unreachable for > 1m"

      - alert: ApiHighErrorRate
        expr: rate(http_requests_total{status=~"5.."}[5m]) / rate(http_requests_total[5m]) > 0.05
        for: 5m
        labels:
          severity: critical
        annotations:
          summary: "API 5xx error rate > 5%"
          description: "{{ $value | humanizePercentage }} of requests are 5xx errors"

      - alert: ApiHighLatency
        expr: histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m])) > 2
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "API p95 latency > 2 seconds"
```

### 4.3 Telegram Alerting via Alertmanager

```yaml
# monitoring/alertmanager.yml
global:
  resolve_timeout: 5m
  telegram_api_url: "https://api.telegram.org"

route:
  receiver: 'telegram-critical'
  group_by: ['alertname', 'severity']
  group_wait: 30s
  group_interval: 5m
  repeat_interval: 3h
  routes:
    - matchers:
        - severity="critical"
      receiver: 'telegram-critical'
      group_wait: 10s
      repeat_interval: 30m
    - matchers:
        - severity="warning"
      receiver: 'telegram-warnings'

receivers:
  - name: 'telegram-critical'
    telegram_configs:
      - bot_token: '{{ .TelegramBotToken }}'  # From env or file
        chat_id: -1001234567890  # Production alerts channel
        parse_mode: 'HTML'
        disable_notifications: false
        message: |
          <b>🚨 {{ .CommonLabels.severity | toUpper }} ALERT</b>
          <b>Alert:</b> {{ .CommonLabels.alertname }}
          <b>Status:</b> {{ .Status }}
          {{ range .Alerts }}
          ━━━━━━━━━━━━━━━
          <b>Summary:</b> {{ .Annotations.summary }}
          <b>Description:</b> {{ .Annotations.description }}
          <b>Instance:</b> {{ .Labels.instance }}
          <b>Started:</b> {{ .StartsAt.Format "15:04:05 02.01.2006" }}
          {{ end }}

  - name: 'telegram-warnings'
    telegram_configs:
      - bot_token: '{{ .TelegramBotToken }}'
        chat_id: -1001234567890
        parse_mode: 'HTML'
        disable_notifications: true  # Don't notify on warnings
        message: |
          <b>⚠️ {{ .CommonLabels.severity | toUpper }}</b>
          <b>Alert:</b> {{ .CommonLabels.alertname }}
          {{ range .Alerts }}
          ━━━━━━━━━━━━━━━
          <b>Summary:</b> {{ .Annotations.summary }}
          <b>Instance:</b> {{ .Labels.instance }}
          {{ end }}
```

**To get Telegram Bot Token:**
1. Talk to @BotFather on Telegram
2. `/newbot` → name: "AIM Monitor" → username: "aim_monitor_bot"
3. Save the token to `.env.production`

**To get Chat ID:**
1. Add your bot to a Telegram group/channel
2. Send a message, then: `curl https://api.telegram.org/bot<TOKEN>/getUpdates`
3. The `chat.id` field is your chat ID

### 4.4 Sentry SDK for FastAPI + SQLAlchemy

**Install:**
```bash
pip install sentry-sdk[fastapi]
```

The SQLAlchemy integration is **auto-enabled** when `sqlalchemy` package is detected. The FastAPI integration is **auto-enabled** when `fastapi` package is detected.

**Configuration in `AIM/src/aim/main.py`:**

```python
import sentry_sdk
from sentry_sdk.integrations.fastapi import FastApiIntegration
from sentry_sdk.integrations.starlette import StarletteIntegration
from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration

from aim.config import get_settings

settings = get_settings()

# Initialize Sentry BEFORE creating the FastAPI app
sentry_sdk.init(
    dsn=settings.sentry_dsn,  # Set SENTRY_DSN in .env.production
    environment=settings.environment,  # "production" / "staging"
    release=settings.release_version,  # Git commit hash or version

    # Error monitoring
    sample_rate=1.0,  # 100% of errors captured in production

    # Performance tracing
    traces_sample_rate=0.1,  # 10% of transactions (adjust for cost)
    profiles_sample_rate=0.1,  # 10% profiling

    # Explicitly configure integrations (needed for custom settings)
    integrations=[
        StarletteIntegration(
            transaction_style="endpoint",  # Names transactions by route handler
            failed_request_status_codes={*range(500, 599)},  # Only 5xx as errors
        ),
        FastApiIntegration(
            transaction_style="endpoint",
            failed_request_status_codes={*range(500, 599)},
            middleware_spans=True,  # Trace middleware execution
        ),
        SqlalchemyIntegration(),  # Auto-enabled, explicit here for clarity
    ],

    # Don't send PII by default
    send_default_pii=False,

    # Enable log integration (send log records as breadcrumbs)
    enable_logs=True,
)

# Create FastAPI app AFTER Sentry init
app = FastAPI(
    title="AIM Agency API",
    version=settings.release_version,
    lifespan=lifespan,
)
```

**Key Sentry configuration decisions:**

| Setting | Value | Rationale |
|---|---|---|
| `traces_sample_rate` | 0.1 (10%) | Balances cost vs visibility in production |
| `profiles_sample_rate` | 0.1 (10%) | Profiling is expensive, 10% is enough |
| `transaction_style` | "endpoint" | Groups by handler name (more useful than URL pattern) |
| `send_default_pii` | False | HIPAA analogy — medical project, don't send PII |
| `failed_request_status_codes` | `{*range(500, 599)}` | Only server errors, not 4xx client errors |
| `middleware_spans` | True | Useful for debugging middleware performance |

**What gets auto-instrumented:**
- **FastAPI:** All HTTP requests, middleware, route handlers
- **SQLAlchemy:** All queries as breadcrumbs and spans (with SQL text)
- **asyncpg:** Database connection events
- **Exceptions:** Unhandled + HTTPException (based on failed_request_status_codes)

### 4.5 Node Exporter (Host-Level Metrics)

```yaml
# docker-compose.prod.yml addition
  node-exporter:
    image: prom/node-exporter:latest
    container_name: aim-node-exporter
    restart: unless-stopped
    command:
      - '--path.rootfs=/host'
      - '--collector.filesystem.mount-points-exclude=^/(sys|proc|dev|host|etc)($$|/)'
    pid: host
    network_mode: host
    volumes:
      - '/:/host:ro,rslave'
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"
```

---

## 5. FZ-152 Data Retention

### 5.1 Legal Framework

**FZ-152 "On Personal Data"** requires:
- Personal data must be stored no longer than necessary for processing purposes
- Medical records: 7 years retention (per FZ-323 "On Health Protection")
- After retention period: data must be **destroyed or anonymized**
- Anonymization = irreversible removal of all identifying information

### 5.2 PostgreSQL Partitioning by Date

**Strategy:** Partition the `leads` and `documents` tables by `created_at` month. This enables efficient deletion of old partitions.

```sql
-- Create partitioned parent table
CREATE TABLE leads (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) NOT NULL,
    name VARCHAR(255),
    phone VARCHAR(50),
    source VARCHAR(100),
    status VARCHAR(50) DEFAULT 'new',
    metadata JSONB,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
) PARTITION BY RANGE (created_at);

-- Create monthly partitions
CREATE TABLE leads_2026_05 PARTITION OF leads
    FOR VALUES FROM ('2026-05-01') TO ('2026-06-01');

CREATE TABLE leads_2026_06 PARTITION OF leads
    FOR VALUES FROM ('2026-06-01') TO ('2026-07-01');

CREATE TABLE leads_2026_07 PARTITION OF leads
    FOR VALUES FROM ('2026-07-01') TO ('2026-08-01');

-- Create index on each partition (indexes are NOT inherited in PG)
CREATE INDEX ON leads_2026_05 (email);
CREATE INDEX ON leads_2026_05 (created_at);
```

### 5.3 Automated Partition Management

```python
# AIM/src/aim/services/retention/partition_manager.py
"""
Automated partition creation and retention enforcement.
Run via cron or as a scheduled background task.
"""
import asyncio
from datetime import datetime, timedelta
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from aim.database import AsyncSessionLocal


class PartitionManager:
    """Manages PostgreSQL partitions for data retention."""

    RETENTION_YEARS = 7
    PARTITIONED_TABLES = ["leads", "documents", "fz152_audit"]

    async def ensure_future_partitions(self, months_ahead: int = 3):
        """Create partitions for the next N months if they don't exist."""
        async with AsyncSessionLocal() as session:
            for table in self.PARTITIONED_TABLES:
                for i in range(months_ahead):
                    dt = datetime.utcnow().replace(day=1) + timedelta(days=32 * i)
                    dt = dt.replace(day=1)
                    next_month = dt.replace(day=28) + timedelta(days=4)
                    next_month = next_month.replace(day=1)

                    partition_name = f"{table}_{dt.strftime('%Y_%m')}"
                    sql = text(f"""
                        CREATE TABLE IF NOT EXISTS {partition_name}
                        PARTITION OF {table}
                        FOR VALUES FROM ('{dt.strftime('%Y-%m-%d')}')
                        TO ('{next_month.strftime('%Y-%m-%d')}');
                    """)
                    try:
                        await session.execute(sql)
                        await session.commit()
                    except Exception as e:
                        await session.rollback()
                        # Partition likely already exists — ignore
                        pass

    async def detach_expired_partitions(self):
        """Detach partitions older than retention period."""
        cutoff = datetime.utcnow() - timedelta(days=365 * self.RETENTION_YEARS)

        async with AsyncSessionLocal() as session:
            for table in self.PARTITIONED_TABLES:
                # Find old partitions
                result = await session.execute(text("""
                    SELECT tablename
                    FROM pg_tables
                    WHERE tablename LIKE :pattern
                      AND tablename < :cutoff_name
                """), {
                    "pattern": f"{table}_%",
                    "cutoff_name": f"{table}_{cutoff.strftime('%Y_%m')}",
                })

                for row in result:
                    old_partition = row[0]
                    # Detach the partition
                    await session.execute(text(
                        f"ALTER TABLE {table} DETACH PARTITION {old_partition};"
                    ))
                    await session.commit()
                    print(f"Detached: {old_partition}")

    async def drop_detached_partitions(self):
        """Drop partitions that were previously detached (run after backup)."""
        async with AsyncSessionLocal() as session:
            # Find detached partitions (not attached to any parent)
            result = await session.execute(text("""
                SELECT relname
                FROM pg_class
                WHERE relkind = 'r'
                  AND relname SIMILAR TO '(leads|documents|fz152_audit)_\d{4}_\d{2}'
                  AND relpartbound IS NULL
                  AND NOT relispartition;
            """))

            for row in result:
                await session.execute(text(f"DROP TABLE IF EXISTS {row[0]};"))
                await session.commit()
                print(f"Dropped: {row[0]}")

    async def anonymize_before_drop(self, partition_name: str):
        """Anonymize PII data in a partition before archiving/dropping."""
        async with AsyncSessionLocal() as session:
            # Replace PII with anonymized values
            await session.execute(text(f"""
                UPDATE {partition_name}
                SET email = CONCAT('anon_', id, '@deleted.aim'),
                    name = '[DELETED]',
                    phone = NULL,
                    metadata = '{{"anonymized": true}}'::jsonb
                WHERE email IS NOT NULL;
            """))
            await session.commit()
```

### 5.4 FZ-152 Audit Table Structure

```sql
CREATE TABLE fz152_audit (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    action VARCHAR(50) NOT NULL,  -- 'CREATE', 'ACCESS', 'UPDATE', 'DELETE', 'ANONYMIZE'
    entity_type VARCHAR(100),      -- 'lead', 'document', 'patient_record'
    entity_id UUID,
    user_id VARCHAR(255),          -- Who performed the action
    ip_address INET,               -- From which IP
    action_timestamp TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    details JSONB,                 -- What changed (sanitized)
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
) PARTITION BY RANGE (created_at);
```

### 5.5 Retention Cleanup Cron

```bash
# /etc/cron.d/aim-retention — Run monthly
0 3 1 * * root cd /opt/aim && docker compose exec -T api python -m aim.services.retention.cleanup >> /var/log/aim-retention.log 2>&1
```

**Cleanup script flow:**
1. Check for old partitions (> 7 years)
2. Export old partition data to compressed archive (for legal archive)
3. Anonymize data in old partition
4. Detach partition from parent table
5. Drop detached partition
6. Log to FZ-152 audit table

---

## Summary: Infrastructure Architecture

```
                        INTERNET
                           │
                    ┌──────▼──────┐
                    │   UFW:      │
                    │   22/80/443 │
                    └──────┬──────┘
                           │
                    ┌──────▼──────┐
                    │   NGINX     │
                    │  (SSL/TLS)  │
                    │  LetEncrypt │
                    └──────┬──────┘
                           │
              ┌────────────┼────────────┐
              │            │            │
       ┌──────▼─────┐ ┌───▼────┐ ┌────▼──────┐
       │  FastAPI   │ │Certbot │ │ Prometheus │
       │  (uvicorn) │ │(renew) │ │  :9090     │
       └──────┬─────┘ └────────┘ └────┬───────┘
              │                       │
       ┌──────┼───────────────┐       │
       │      │               │       │
  ┌────▼──┐ ┌▼──────┐ ┌──────▼───┐ ┌─▼──────────┐
  │ Post- │ │ Redis │ │ Postgres │ │ Alertmanager│
  │greSQL │ │  :6379│ │ Exporter │ │   :9093     │
  │ :5432 │ │       │ │   :9187  │ │→ Telegram   │
  └───────┘ └───────┘ └──────────┘ └─────────────┘
```

**Key infrastructure decisions:**
- `127.0.0.1` binding for all databases (security)
- Network segmentation: frontend (nginx+api) / backend (postgres+redis) / monitoring
- `unless-stopped` restart policy (standard for production)
- Log rotation on ALL services (prevent disk fill)
- Resource limits on ALL services (prevent OOM cascade)
- Sentry for error tracking, Prometheus + Alertmanager for metrics + Telegram alerts
- FZ-152 compliant data retention with date-based partitioning

---

## Sources

- [Alembic with Async SQLAlchemy — Brandon Wie](https://brandonwie.dev/posts/alembic-async-sqlalchemy) — Complete async alembic env.py pattern
- [FastAPI, async SQLAlchemy, pytest, and Alembic — thedmitry.pw](https://thedmitry.pw/blog/2023/08/fastapi-async-sqlalchemy-pytest-and-alembic/) — Test fixtures for async PG
- [Asynchronous SQLAlchemy 2 Guide — DEV Community](https://dev.to/amverum/asynchronous-sqlalchemy-2-a-simple-step-by-step-guide-to-configuration-models-relationships-and-3ob3) — Step-by-step alembic setup
- [Docker: Advanced PostgreSQL Configuration](https://docs.docker.com/guides/postgresql/advanced-configuration-and-initialization/) — Official Docker PostgreSQL guide
- [PostgreSQL Docker Compose — OneUptime](https://oneuptime.com/blog/post/2026-01-21-postgresql-docker-compose/view) — Production-ready compose config
- [Docker Compose Healthchecks — BetterLink](https://eastondev.com/blog/en/posts/dev/20251217-docker-compose-healthcheck/) — Health check best practices
- [Docker Compose Production Patterns — Essential Hustle](https://essentialhustle.dev/blog/docker-compose-production-patterns) — Battle-tested patterns (15+ containers)
- [Docker Compose in Production — alexsdev.io](https://alexsdev.io/blog/docker-compose-production/) — Complete production guide
- [PostgreSQL Exporter — Grafana Docs](https://grafana.com/docs/grafana-cloud/monitor-applications/asserts/enable-prom-metrics-collection/data-stores/postgresql) — Exporter metrics reference
- [Postgres Exporter Installation — Mintlify](https://mintlify.com/prometheus-community/postgres_exporter/installation) — Docker Compose setup
- [Postgres Exporter Deep Dive — Tiago Melo](https://tiagomelo.info/postgres/prometheus/grafana/2025/11/10/postgres-exporter.html) — End-to-end with Grafana
- [Prometheus Alertmanager — Context7](https://context7.com/prometheus/alertmanager/llms.txt) — Alertmanager config schemas
- [Sentry: FastAPI Integration](https://docs.sentry.io/platforms/python/integrations/fastapi/) — Official Sentry FastAPI docs
- [Sentry: SQLAlchemy Integration](https://docs.sentry.io/platforms/python/integrations/sqlalchemy/) — Official Sentry SQLAlchemy docs
- [PostgreSQL: Declarative Partitioning](https://www.postgresql.org/docs/current/ddl-partitioning.html) — Official PG partitioning docs
