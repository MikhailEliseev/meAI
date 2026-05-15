# Server Requirements for AIM Agency Production

## Recommended Server Specifications

### Minimum Configuration (Start Small, Scale Later)

**VPS/Cloud Server:**
- **CPU:** 2 vCPU cores
- **RAM:** 4 GB
- **Storage:** 40 GB SSD
- **Bandwidth:** 2 TB/month
- **OS:** Ubuntu 22.04 LTS

**Estimated Cost:** $10-20/month

**Providers:**
- DigitalOcean: Droplet $12/month (2 vCPU, 2 GB RAM, 50 GB SSD)
- Hetzner: CX21 €5.83/month (~$6.50) (2 vCPU, 4 GB RAM, 40 GB SSD) ⭐ BEST VALUE
- Vultr: $12/month (2 vCPU, 4 GB RAM, 80 GB SSD)
- Linode: $12/month (2 vCPU, 4 GB RAM, 80 GB SSD)

---

### Recommended Configuration (Production Ready)

**VPS/Cloud Server:**
- **CPU:** 4 vCPU cores
- **RAM:** 8 GB
- **Storage:** 80 GB SSD
- **Bandwidth:** 4 TB/month
- **OS:** Ubuntu 22.04 LTS

**Estimated Cost:** $30-50/month

**Providers:**
- Hetzner: CX31 €11.90/month (~$13) (2 vCPU, 8 GB RAM, 80 GB SSD) ⭐ BEST VALUE
- Hetzner: CX41 €23.90/month (~$26) (4 vCPU, 16 GB RAM, 160 GB SSD) ⭐ RECOMMENDED
- DigitalOcean: Droplet $48/month (4 vCPU, 8 GB RAM, 160 GB SSD)
- Vultr: $48/month (4 vCPU, 8 GB RAM, 180 GB SSD)

---

## Why These Specs?

### CPU (2-4 cores)
- **FastAPI workers:** 4 workers = 4 CPU cores ideal
- **Background tasks:** Keyword research, competitor analysis
- **Docker containers:** 5 services (app, redis, nginx, prometheus, grafana)
- **Recommendation:** Start with 2 cores, upgrade to 4 when traffic grows

### RAM (4-8 GB)
- **FastAPI app:** ~500 MB per worker × 4 = 2 GB
- **Redis:** ~500 MB for caching
- **PostgreSQL/SQLite:** ~200 MB
- **Prometheus:** ~500 MB for metrics storage
- **Grafana:** ~200 MB
- **nginx:** ~50 MB
- **OS overhead:** ~500 MB
- **Total:** ~4 GB minimum, 8 GB comfortable

### Storage (40-80 GB SSD)
- **Application code:** ~500 MB
- **Docker images:** ~2 GB
- **Database:** ~1 GB (grows over time)
- **Logs:** ~5 GB (30-day retention)
- **Backups:** ~10 GB (30-day retention)
- **Prometheus metrics:** ~10 GB (30-day retention)
- **OS + packages:** ~10 GB
- **Free space:** ~20 GB buffer
- **Total:** 40 GB minimum, 80 GB comfortable

### Bandwidth (2-4 TB/month)
- **API requests:** ~1 KB per request
- **Expected traffic:** 100K requests/month = 100 MB
- **Monitoring data:** ~10 GB/month
- **Backups:** ~5 GB/month
- **Buffer:** 2 TB is more than enough

---

## Recommended Provider: Hetzner ⭐

**Why Hetzner?**
1. **Best price/performance ratio** (2-3x cheaper than DigitalOcean/AWS)
2. **European data centers** (Germany, Finland) - good for Russia/Europe
3. **Excellent network** (20 Gbit/s uplink)
4. **Free traffic** (20 TB included)
5. **Reliable** (99.9% uptime SLA)
6. **Easy to scale** (upgrade in 1 click)

**Recommended Plan: CX31**
- **Price:** €11.90/month (~$13)
- **CPU:** 2 vCPU (AMD EPYC or Intel Xeon)
- **RAM:** 8 GB
- **Storage:** 80 GB SSD (NVMe)
- **Traffic:** 20 TB/month
- **Location:** Falkenstein, Germany (closest to Russia)

**Link:** https://www.hetzner.com/cloud

---

## Alternative: Start Even Smaller

**Hetzner CX21** (€5.83/month, ~$6.50)
- 2 vCPU, 4 GB RAM, 40 GB SSD
- Perfect for MVP/testing
- Upgrade to CX31 when traffic grows

**When to upgrade:**
- Traffic > 10K requests/day
- Database > 5 GB
- Response time > 1 second
- CPU usage > 70%

---

## Server Setup Checklist

### 1. Initial Setup (30 min)
```bash
# Update system
apt update && apt upgrade -y

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sh get-docker.sh

# Install Docker Compose
apt install docker-compose-plugin -y

# Create user
adduser aim
usermod -aG docker aim
usermod -aG sudo aim

# Setup firewall
ufw allow 22/tcp    # SSH
ufw allow 80/tcp    # HTTP
ufw allow 443/tcp   # HTTPS
ufw enable
```

### 2. Deploy Application (15 min)
```bash
# Clone repository
git clone https://github.com/your-repo/meAI.git
cd meAI/AIM

# Copy production config
cp .env.example .env.production
nano .env.production  # Edit with your API keys

# Start services
docker-compose up -d

# Check health
curl http://localhost/health
```

### 3. Setup SSL (10 min)
```bash
# Install Certbot
apt install certbot python3-certbot-nginx -y

# Get certificate
certbot --nginx -d iamaim.ru -d www.iamaim.ru

# Auto-renewal (already configured)
systemctl status certbot.timer
```

### 4. Setup Monitoring (5 min)
```bash
# Access Grafana
# Open: https://iamaim.ru:3000
# Login: admin / admin (change on first login)

# Access Prometheus
# Open: https://iamaim.ru:9090
```

---

## Cost Breakdown (Monthly)

### Server: Hetzner CX31
- **Server:** €11.90 (~$13)
- **Backups (optional):** €2.38 (~$2.60)
- **Total:** €14.28 (~$15.60)

### Domain: iamaim.ru
- **Registration:** ~$10/year (~$0.83/month)
- **SSL:** Free (Let's Encrypt)

### API Costs (Variable)
- **SEMrush:** $0.01 per request
- **Ahrefs:** $0.01 per request
- **Google Analytics:** Free
- **Yandex Metrica:** Free
- **Yandex Direct:** Free (API access)
- **Estimated:** $5-20/month (depends on usage)

### Total Monthly Cost
- **Infrastructure:** ~$16/month
- **APIs:** ~$5-20/month
- **Total:** ~$21-36/month

---

## Scaling Strategy

### Phase 1: Single Server (0-1K users)
- Hetzner CX31 (2 vCPU, 8 GB RAM)
- Cost: ~$13/month
- Handles: 10K requests/day

### Phase 2: Vertical Scaling (1K-10K users)
- Upgrade to CX41 (4 vCPU, 16 GB RAM)
- Cost: ~$26/month
- Handles: 100K requests/day

### Phase 3: Horizontal Scaling (10K+ users)
- Load balancer + 2-3 app servers
- Separate database server
- Redis cluster
- Cost: ~$100-200/month
- Handles: 1M+ requests/day

---

## Monitoring & Alerts

### Key Metrics to Watch
1. **CPU usage** - Alert if >80% for 5 min
2. **Memory usage** - Alert if >90% for 5 min
3. **Disk usage** - Alert if >85%
4. **Response time** - Alert if p95 >2s
5. **Error rate** - Alert if >5%

### Grafana Alerts (Already Configured)
- HighErrorRate: >0.1 errors/sec for 5m
- HighAPICost: >$5/hour for 10m
- ServiceDown: up == 0 for 1m
- HighResponseTime: p95 >2s for 5m

---

## Backup Strategy

### Automated Backups (Already Configured)
- **Frequency:** Daily at 3am GMT+3
- **Retention:** 30 days
- **Location:** ./backups/ (on server)
- **Size:** ~1-2 GB per backup

### Off-site Backups (Recommended)
- **Hetzner Storage Box:** €3.81/month for 100 GB
- **AWS S3:** ~$2/month for 100 GB
- **Backblaze B2:** ~$0.50/month for 100 GB ⭐ CHEAPEST

**Setup:**
```bash
# Install rclone
curl https://rclone.org/install.sh | sudo bash

# Configure Backblaze B2
rclone config

# Sync backups daily
0 4 * * * rclone sync /app/backups/ b2:aim-backups/
```

---

## Security Checklist

- [x] Firewall configured (ufw)
- [x] SSH key authentication (disable password)
- [x] Fail2ban installed (block brute force)
- [x] SSL/TLS certificates (Let's Encrypt)
- [x] Security headers (nginx)
- [x] Rate limiting (nginx)
- [x] Environment variables secured (600 permissions)
- [x] Regular updates (unattended-upgrades)

---

## Recommendation Summary

**For MVP/Testing:**
- **Server:** Hetzner CX21 (€5.83/month, ~$6.50)
- **Total cost:** ~$10/month (server + domain)
- **Upgrade when:** Traffic >5K requests/day

**For Production:**
- **Server:** Hetzner CX31 (€11.90/month, ~$13)
- **Total cost:** ~$30/month (server + domain + APIs)
- **Handles:** 10K requests/day comfortably

**Start with CX21, upgrade to CX31 when needed. Hetzner allows instant upgrades without downtime.**

---

**Next Steps:**
1. Register Hetzner account: https://www.hetzner.com/cloud
2. Create CX21 or CX31 server (Ubuntu 22.04)
3. Follow setup checklist above
4. Deploy AIM Agency
5. Configure monitoring
6. Test first workflow

**Questions?** Ask me anything about server setup, deployment, or scaling!
