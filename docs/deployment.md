# Deployment Guide

## Overview

Этот гайд описывает процесс развертывания meAI в production окружении.

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                     Load Balancer                        │
│                    (nginx/traefik)                       │
└─────────────────────────────────────────────────────────┘
                            │
        ┌───────────────────┼───────────────────┐
        │                   │                   │
┌───────▼────────┐  ┌──────▼───────┐  ┌───────▼────────┐
│   FastAPI      │  │   FastAPI    │  │   FastAPI      │
│   Instance 1   │  │   Instance 2 │  │   Instance 3   │
└───────┬────────┘  └──────┬───────┘  └───────┬────────┘
        │                   │                   │
        └───────────────────┼───────────────────┘
                            │
        ┌───────────────────┼───────────────────┐
        │                   │                   │
┌───────▼────────┐  ┌──────▼───────┐  ┌───────▼────────┐
│   PostgreSQL   │  │    Qdrant    │  │     Redis      │
│   (Primary)    │  │   (Vector)   │  │    (Cache)     │
└────────────────┘  └──────────────┘  └────────────────┘
```

## Prerequisites

- **Docker** 20.10+
- **Docker Compose** 2.0+
- **PostgreSQL** 14+
- **Qdrant** 1.7+
- **Redis** 7.0+ (optional, for caching)
- **Domain** with SSL certificate

## Quick Start (Docker Compose)

### Step 1: Clone and Configure

```bash
# Clone repository
git clone <repository-url>
cd meAI

# Copy environment file
cp .env.production.example .env.production

# Edit configuration
nano .env.production
```

### Step 2: Configure Environment

**.env.production:**
```bash
# Application
APP_ENV=production
APP_DEBUG=false
LOG_LEVEL=INFO

# Database
DATABASE_URL=postgresql+asyncpg://meai:password@postgres:5432/meai
DATABASE_POOL_SIZE=20
DATABASE_MAX_OVERFLOW=10

# Qdrant
QDRANT_URL=http://qdrant:6333
QDRANT_API_KEY=your-qdrant-api-key

# Redis (optional)
REDIS_URL=redis://redis:6379/0

# API Keys
PERPLEXITY_API_KEY=pplx-your-key
YOUTUBE_API_KEY=your-youtube-key
TELEGRAM_BOT_TOKEN=your-telegram-token

# Security
SECRET_KEY=your-secret-key-here-min-32-chars
ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com

# Obsidian
OBSIDIAN_VAULT_PATH=/app/obsidian

# Performance
WORKERS=4
MAX_REQUESTS=1000
MAX_REQUESTS_JITTER=50
```

### Step 3: Create Docker Compose

**docker-compose.prod.yml:**
```yaml
version: '3.8'

services:
  # PostgreSQL Database
  postgres:
    image: postgres:14-alpine
    container_name: meai-postgres
    environment:
      POSTGRES_DB: meai
      POSTGRES_USER: meai
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"
    restart: unless-stopped
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U meai"]
      interval: 10s
      timeout: 5s
      retries: 5

  # Qdrant Vector Database
  qdrant:
    image: qdrant/qdrant:v1.7.4
    container_name: meai-qdrant
    environment:
      QDRANT__SERVICE__API_KEY: ${QDRANT_API_KEY}
    volumes:
      - qdrant_data:/qdrant/storage
    ports:
      - "6333:6333"
      - "6334:6334"
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:6333/"]
      interval: 10s
      timeout: 5s
      retries: 5

  # Redis Cache (optional)
  redis:
    image: redis:7-alpine
    container_name: meai-redis
    command: redis-server --appendonly yes
    volumes:
      - redis_data:/data
    ports:
      - "6379:6379"
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 5s
      retries: 5

  # meAI Application
  app:
    build:
      context: .
      dockerfile: Dockerfile.prod
    container_name: meai-app
    env_file:
      - .env.production
    volumes:
      - ./obsidian:/app/obsidian
      - ./data:/app/data
    ports:
      - "8000:8000"
    depends_on:
      postgres:
        condition: service_healthy
      qdrant:
        condition: service_healthy
      redis:
        condition: service_healthy
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s

  # Nginx Reverse Proxy
  nginx:
    image: nginx:alpine
    container_name: meai-nginx
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf:ro
      - ./ssl:/etc/nginx/ssl:ro
    ports:
      - "80:80"
      - "443:443"
    depends_on:
      - app
    restart: unless-stopped

volumes:
  postgres_data:
  qdrant_data:
  redis_data:
```

### Step 4: Create Dockerfile

**Dockerfile.prod:**
```dockerfile
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY src/ ./src/
COPY scripts/ ./scripts/

# Create directories
RUN mkdir -p /app/data /app/obsidian

# Set environment
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
  CMD curl -f http://localhost:8000/health || exit 1

# Run application
CMD ["uvicorn", "meai.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]
```

### Step 5: Configure Nginx

**nginx.conf:**
```nginx
events {
    worker_connections 1024;
}

http {
    upstream meai_backend {
        least_conn;
        server app:8000 max_fails=3 fail_timeout=30s;
    }

    # Rate limiting
    limit_req_zone $binary_remote_addr zone=api_limit:10m rate=10r/s;

    server {
        listen 80;
        server_name yourdomain.com www.yourdomain.com;
        
        # Redirect to HTTPS
        return 301 https://$server_name$request_uri;
    }

    server {
        listen 443 ssl http2;
        server_name yourdomain.com www.yourdomain.com;

        # SSL Configuration
        ssl_certificate /etc/nginx/ssl/fullchain.pem;
        ssl_certificate_key /etc/nginx/ssl/privkey.pem;
        ssl_protocols TLSv1.2 TLSv1.3;
        ssl_ciphers HIGH:!aNULL:!MD5;

        # Security headers
        add_header X-Frame-Options "SAMEORIGIN" always;
        add_header X-Content-Type-Options "nosniff" always;
        add_header X-XSS-Protection "1; mode=block" always;

        # Proxy settings
        location / {
            limit_req zone=api_limit burst=20 nodelay;
            
            proxy_pass http://meai_backend;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
            
            # Timeouts
            proxy_connect_timeout 60s;
            proxy_send_timeout 60s;
            proxy_read_timeout 60s;
        }

        # Health check endpoint
        location /health {
            proxy_pass http://meai_backend/health;
            access_log off;
        }
    }
}
```

### Step 6: Deploy

```bash
# Build and start services
docker-compose -f docker-compose.prod.yml up -d

# Check logs
docker-compose -f docker-compose.prod.yml logs -f app

# Initialize database
docker-compose -f docker-compose.prod.yml exec app python scripts/init_db.py

# Setup Magisters
docker-compose -f docker-compose.prod.yml exec app python scripts/setup_magisters.py
```

## Manual Deployment (Without Docker)

### Step 1: System Setup

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Python 3.11
sudo apt install python3.11 python3.11-venv python3-pip

# Install PostgreSQL
sudo apt install postgresql postgresql-contrib

# Install Redis
sudo apt install redis-server
```

### Step 2: Database Setup

```bash
# Create database
sudo -u postgres psql
CREATE DATABASE meai;
CREATE USER meai WITH PASSWORD 'your-password';
GRANT ALL PRIVILEGES ON DATABASE meai TO meai;
\q

# Run migrations
python scripts/init_db.py
```

### Step 3: Install Qdrant

```bash
# Download and install Qdrant
wget https://github.com/qdrant/qdrant/releases/download/v1.7.4/qdrant-x86_64-unknown-linux-gnu.tar.gz
tar -xzf qdrant-x86_64-unknown-linux-gnu.tar.gz
sudo mv qdrant /usr/local/bin/

# Create systemd service
sudo nano /etc/systemd/system/qdrant.service
```

**/etc/systemd/system/qdrant.service:**
```ini
[Unit]
Description=Qdrant Vector Database
After=network.target

[Service]
Type=simple
User=meai
WorkingDirectory=/opt/qdrant
ExecStart=/usr/local/bin/qdrant
Restart=always

[Install]
WantedBy=multi-user.target
```

```bash
# Start Qdrant
sudo systemctl enable qdrant
sudo systemctl start qdrant
```

### Step 4: Application Setup

```bash
# Create user
sudo useradd -m -s /bin/bash meai

# Clone repository
sudo -u meai git clone <repository-url> /home/meai/meai
cd /home/meai/meai

# Create venv
sudo -u meai python3.11 -m venv venv
sudo -u meai venv/bin/pip install -r requirements.txt

# Configure
sudo -u meai cp .env.production.example .env.production
sudo -u meai nano .env.production

# Initialize
sudo -u meai venv/bin/python scripts/setup_magisters.py
```

### Step 5: Systemd Service

**/etc/systemd/system/meai.service:**
```ini
[Unit]
Description=meAI Application
After=network.target postgresql.service qdrant.service

[Service]
Type=simple
User=meai
WorkingDirectory=/home/meai/meai
Environment="PATH=/home/meai/meai/venv/bin"
ExecStart=/home/meai/meai/venv/bin/uvicorn meai.main:app --host 0.0.0.0 --port 8000 --workers 4
Restart=always

[Install]
WantedBy=multi-user.target
```

```bash
# Start service
sudo systemctl enable meai
sudo systemctl start meai
```

## Monitoring

### Health Checks

```bash
# Application health
curl http://localhost:8000/health

# Qdrant health
curl http://localhost:6333/

# PostgreSQL health
pg_isready -h localhost -U meai

# Redis health
redis-cli ping
```

### Logs

```bash
# Application logs
docker-compose logs -f app

# Or with systemd
sudo journalctl -u meai -f

# Nginx logs
tail -f /var/log/nginx/access.log
tail -f /var/log/nginx/error.log
```

### Metrics

**Prometheus configuration (prometheus.yml):**
```yaml
scrape_configs:
  - job_name: 'meai'
    static_configs:
      - targets: ['localhost:8000']
    metrics_path: '/metrics'
```

## Backup

### Database Backup

```bash
# Backup PostgreSQL
docker-compose exec postgres pg_dump -U meai meai > backup_$(date +%Y%m%d).sql

# Restore
docker-compose exec -T postgres psql -U meai meai < backup_20260502.sql
```

### Qdrant Backup

```bash
# Backup Qdrant
docker-compose exec qdrant tar -czf /qdrant/backup.tar.gz /qdrant/storage

# Copy to host
docker cp meai-qdrant:/qdrant/backup.tar.gz ./qdrant_backup_$(date +%Y%m%d).tar.gz
```

### Obsidian Backup

```bash
# Backup vaults
tar -czf obsidian_backup_$(date +%Y%m%d).tar.gz obsidian/
```

## Scaling

### Horizontal Scaling

```bash
# Scale app instances
docker-compose -f docker-compose.prod.yml up -d --scale app=3

# Update nginx upstream
# Add more servers to upstream block
```

### Database Replication

**PostgreSQL streaming replication:**
```bash
# On primary
# Edit postgresql.conf
wal_level = replica
max_wal_senders = 3

# On replica
# Create recovery.conf
primary_conninfo = 'host=primary_host port=5432 user=replicator password=password'
```

## Security

### SSL/TLS

```bash
# Generate certificate with Let's Encrypt
sudo certbot certonly --nginx -d yourdomain.com -d www.yourdomain.com

# Auto-renewal
sudo certbot renew --dry-run
```

### Firewall

```bash
# UFW configuration
sudo ufw allow 22/tcp
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw enable
```

### Secrets Management

```bash
# Use Docker secrets
echo "your-secret" | docker secret create db_password -

# Reference in compose
secrets:
  db_password:
    external: true
```

## Troubleshooting

### Application won't start

```bash
# Check logs
docker-compose logs app

# Check dependencies
docker-compose ps

# Restart services
docker-compose restart
```

### Database connection issues

```bash
# Check PostgreSQL
docker-compose exec postgres psql -U meai -c "SELECT 1"

# Check connection string
echo $DATABASE_URL
```

### Qdrant issues

```bash
# Check Qdrant
curl http://localhost:6333/collections

# Restart Qdrant
docker-compose restart qdrant
```

## Performance Tuning

### PostgreSQL

```sql
-- postgresql.conf
shared_buffers = 256MB
effective_cache_size = 1GB
maintenance_work_mem = 64MB
checkpoint_completion_target = 0.9
wal_buffers = 16MB
default_statistics_target = 100
random_page_cost = 1.1
effective_io_concurrency = 200
work_mem = 4MB
min_wal_size = 1GB
max_wal_size = 4GB
```

### Qdrant

```yaml
# config.yaml
storage:
  storage_path: /qdrant/storage
  optimizers:
    indexing_threshold: 20000
    memmap_threshold: 50000
```

### Application

```python
# Increase workers
CMD ["uvicorn", "meai.main:app", "--workers", "8"]

# Enable caching
REDIS_URL=redis://redis:6379/0
```

## Maintenance

### Updates

```bash
# Pull latest code
git pull origin main

# Rebuild and restart
docker-compose -f docker-compose.prod.yml build
docker-compose -f docker-compose.prod.yml up -d

# Run migrations
docker-compose exec app python scripts/migrate.py
```

### Cleanup

```bash
# Remove old images
docker image prune -a

# Remove old volumes
docker volume prune

# Clean logs
docker-compose logs --tail=0 -f
```

## See Also

- [Getting Started](getting-started.md)
- [API Reference](api-reference.md)
- [Monitoring Guide](monitoring.md)
