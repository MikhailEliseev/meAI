# AIM Agency - Production Deployment Guide

**Version:** 1.0.0  
**Last Updated:** 2026-05-13  
**Status:** Production Ready

---

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Environment Setup](#environment-setup)
3. [API Keys Configuration](#api-keys-configuration)
4. [Docker Deployment](#docker-deployment)
5. [Manual Deployment](#manual-deployment)
6. [Health Checks](#health-checks)
7. [Monitoring](#monitoring)
8. [Troubleshooting](#troubleshooting)
9. [Security Best Practices](#security-best-practices)

---

## Prerequisites

### System Requirements

- **Python:** 3.11 or higher
- **Memory:** Minimum 2GB RAM (4GB recommended)
- **Storage:** 10GB free space
- **OS:** Linux (Ubuntu 20.04+), macOS 12+, or Windows 10+ with WSL2

### Required Services

- **Database:** SQLite (included) or PostgreSQL (optional)
- **Cache:** Redis (optional, for distributed caching)
- **Monitoring:** Prometheus + Grafana (optional)

### API Access

- **SEMrush API:** Business plan ($499.95/month) or higher
- **DataForSEO API:** Pay-as-you-go account
- **PageSpeed Insights API:** Free tier (25,000 requests/day)

---

## Environment Setup

### 1. Clone Repository

```bash
git clone https://github.com/MikhailEliseev/meAI.git
cd meAI/AIM
```

### 2. Create Virtual Environment

```bash
python3.11 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure Environment Variables

```bash
# Copy example configuration
cp .env.example .env

# Edit .env with your credentials
nano .env  # or vim, code, etc.
```

---

## API Keys Configuration

### SEMrush API (Required)

1. **Get API Key:**
   - Visit: https://www.semrush.com/api-documentation/
   - Sign up for Business plan ($499.95/month)
   - Generate API key from dashboard

2. **Add to .env:**
   ```bash
   SEMRUSH_API_KEY=your_actual_api_key_here
   ```

3. **Test Connection:**
   ```bash
   python -c "from AIM.src.aim.subagents.api_clients.semrush import SEMrushClient; import asyncio; asyncio.run(SEMrushClient(api_key='YOUR_KEY').test_connection())"
   ```

### DataForSEO API (Required for Clustering)

1. **Get Credentials:**
   - Visit: https://dataforseo.com/
   - Create account (pay-as-you-go)
   - Get login and password from dashboard

2. **Add to .env:**
   ```bash
   DATAFORSEO_LOGIN=your_login_here
   DATAFORSEO_PASSWORD=your_password_here
   SERP_PROVIDER=dataforseo
   ```

### PageSpeed Insights API (Optional)

1. **Get API Key:**
   - Visit: https://developers.google.com/speed/docs/insights/v5/get-started
   - Create Google Cloud project
   - Enable PageSpeed Insights API
   - Generate API key

2. **Add to .env:**
   ```bash
   PAGESPEED_API_KEY=your_api_key_here
   ```

### Ahrefs API (Optional Fallback)

1. **Get API Key:**
   - Visit: https://ahrefs.com/api
   - Subscribe to Advanced plan + API addon ($949/month)
   - Generate API key

2. **Add to .env:**
   ```bash
   AHREFS_API_KEY=your_api_key_here
   ```

---

## Docker Deployment

### 1. Build Docker Image

```bash
# From AIM directory
docker build -t aim-agency:latest .
```

### 2. Run Container

```bash
docker run -d \
  --name aim-agency \
  -p 8000:8000 \
  -p 9090:9090 \
  -v $(pwd)/data:/app/data \
  -v $(pwd)/.env:/app/.env \
  --restart unless-stopped \
  aim-agency:latest
```

### 3. Docker Compose (Recommended)

```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

**docker-compose.yml:**
```yaml
version: '3.8'

services:
  aim-agency:
    build: .
    container_name: aim-agency
    ports:
      - "8000:8000"
      - "9090:9090"
    volumes:
      - ./data:/app/data
      - ./.env:/app/.env
    environment:
      - ENVIRONMENT=production
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s

  redis:
    image: redis:7-alpine
    container_name: aim-redis
    ports:
      - "6379:6379"
    volumes:
      - redis-data:/data
    restart: unless-stopped

  prometheus:
    image: prom/prometheus:latest
    container_name: aim-prometheus
    ports:
      - "9091:9090"
    volumes:
      - ./prometheus.yml:/etc/prometheus/prometheus.yml
      - prometheus-data:/prometheus
    restart: unless-stopped

volumes:
  redis-data:
  prometheus-data:
```

---

## Manual Deployment

### 1. Run Development Server

```bash
# Activate virtual environment
source venv/bin/activate

# Run with uvicorn
uvicorn aim.main:app --host 0.0.0.0 --port 8000 --reload
```

### 2. Run Production Server

```bash
# Install gunicorn
pip install gunicorn

# Run with gunicorn (4 workers)
gunicorn aim.main:app \
  --workers 4 \
  --worker-class uvicorn.workers.UvicornWorker \
  --bind 0.0.0.0:8000 \
  --timeout 600 \
  --access-logfile - \
  --error-logfile -
```

### 3. Systemd Service (Linux)

Create `/etc/systemd/system/aim-agency.service`:

```ini
[Unit]
Description=AIM Agency Service
After=network.target

[Service]
Type=notify
User=aim
Group=aim
WorkingDirectory=/opt/aim-agency/AIM
Environment="PATH=/opt/aim-agency/venv/bin"
ExecStart=/opt/aim-agency/venv/bin/gunicorn aim.main:app \
  --workers 4 \
  --worker-class uvicorn.workers.UvicornWorker \
  --bind 0.0.0.0:8000 \
  --timeout 600
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Enable and start:
```bash
sudo systemctl enable aim-agency
sudo systemctl start aim-agency
sudo systemctl status aim-agency
```

---

## Health Checks

### 1. Basic Health Check

```bash
curl http://localhost:8000/health
```

**Expected Response:**
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "timestamp": "2026-05-13T07:40:00Z"
}
```

### 2. API Clients Health

```bash
curl http://localhost:8000/health/api-clients
```

**Expected Response:**
```json
{
  "semrush": "healthy",
  "dataforseo": "healthy",
  "pagespeed": "healthy",
  "ahrefs": "not_configured"
}
```

### 3. Database Health

```bash
curl http://localhost:8000/health/database
```

**Expected Response:**
```json
{
  "status": "healthy",
  "connection": "ok",
  "migrations": "up_to_date"
}
```

---

## Monitoring

### 1. Prometheus Metrics

**Endpoint:** `http://localhost:9090/metrics`

**Key Metrics:**
- `api_requests_total` - Total API requests
- `api_request_duration_seconds` - Request duration histogram
- `api_errors_total` - Total API errors
- `circuit_breaker_state` - Circuit breaker state (0=closed, 1=open)
- `cache_hits_total` - Cache hit count
- `cache_misses_total` - Cache miss count

### 2. Grafana Dashboard

1. **Install Grafana:**
   ```bash
   docker run -d -p 3000:3000 grafana/grafana
   ```

2. **Add Prometheus Data Source:**
   - URL: `http://prometheus:9090`
   - Access: Server (default)

3. **Import Dashboard:**
   - Use template: `AIM/monitoring/grafana-dashboard.json`

### 3. Logging

**Log Levels:**
- `DEBUG` - Detailed debugging information
- `INFO` - General informational messages
- `WARNING` - Warning messages
- `ERROR` - Error messages

**Log Format (JSON):**
```json
{
  "timestamp": "2026-05-13T07:40:00Z",
  "level": "INFO",
  "logger": "aim.magisters.seo_magister_v2",
  "message": "SEO analysis completed",
  "duration_ms": 12500,
  "url": "https://example.com"
}
```

**View Logs:**
```bash
# Docker
docker logs -f aim-agency

# Systemd
journalctl -u aim-agency -f

# File
tail -f /var/log/aim-agency/app.log
```

---

## Troubleshooting

### Common Issues

#### 1. API Key Errors

**Symptom:** `401 Unauthorized` or `403 Forbidden`

**Solution:**
```bash
# Verify API key in .env
grep SEMRUSH_API_KEY .env

# Test API connection
python -c "from AIM.src.aim.subagents.api_clients.semrush import SEMrushClient; import asyncio; asyncio.run(SEMrushClient(api_key='YOUR_KEY').test_connection())"
```

#### 2. Circuit Breaker Open

**Symptom:** `CircuitBreakerError: Circuit breaker is open`

**Solution:**
```bash
# Check error logs
docker logs aim-agency | grep "circuit_breaker"

# Wait for reset (60 seconds default)
# Or restart service to reset immediately
docker restart aim-agency
```

#### 3. Rate Limit Exceeded

**Symptom:** `429 Too Many Requests`

**Solution:**
```bash
# Increase rate limit in .env
RATE_LIMIT_CAPACITY=20
RATE_LIMIT_REFILL=2.0

# Restart service
docker restart aim-agency
```

#### 4. Timeout Errors

**Symptom:** `TimeoutError: Analysis timed out`

**Solution:**
```bash
# Increase timeout in .env
SEO_ANALYSIS_TIMEOUT=1200  # 20 minutes

# Restart service
docker restart aim-agency
```

#### 5. Database Locked

**Symptom:** `sqlite3.OperationalError: database is locked`

**Solution:**
```bash
# Switch to PostgreSQL for production
DATABASE_URL=postgresql+asyncpg://user:pass@localhost/aim

# Or increase SQLite timeout
# Add to database.py: connect_args={"timeout": 30}
```

---

## Security Best Practices

### 1. API Keys

- **Never commit .env to git** (already in .gitignore)
- **Use environment variables** for all secrets
- **Rotate keys regularly** (every 90 days)
- **Use separate keys** for dev/staging/production

### 2. Network Security

- **Use HTTPS** in production (Let's Encrypt)
- **Enable CORS** only for trusted origins
- **Use firewall** to restrict access
- **Enable rate limiting** on all endpoints

### 3. Database Security

- **Use PostgreSQL** in production (not SQLite)
- **Enable SSL** for database connections
- **Regular backups** (daily minimum)
- **Encrypt sensitive data** at rest

### 4. Monitoring

- **Enable Sentry** for error tracking
- **Set up alerts** for critical errors
- **Monitor API costs** to prevent overruns
- **Track performance metrics** for optimization

### 5. Updates

- **Keep dependencies updated** (monthly)
- **Monitor security advisories** (GitHub Dependabot)
- **Test updates** in staging before production
- **Have rollback plan** for failed deployments

---

## Production Checklist

Before deploying to production:

- [ ] All API keys configured and tested
- [ ] Environment set to `production` in .env
- [ ] Database backups configured
- [ ] HTTPS enabled with valid certificate
- [ ] CORS configured for production domains
- [ ] Rate limiting enabled
- [ ] Monitoring and alerting configured
- [ ] Error tracking (Sentry) enabled
- [ ] Health checks passing
- [ ] Load testing completed
- [ ] Rollback plan documented
- [ ] Team trained on deployment process

---

## Support

**Documentation:** https://github.com/MikhailEliseev/meAI/wiki  
**Issues:** https://github.com/MikhailEliseev/meAI/issues  
**Email:** support@iamaim.ru

---

**Version:** 1.0.0  
**Last Updated:** 2026-05-13  
**Maintained by:** AIM Agency Team
