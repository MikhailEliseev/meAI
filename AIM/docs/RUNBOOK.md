# Operational Runbook

## System Overview

**Service:** AIM Agency API
**Domain:** iamaim.ru
**Environment:** Production
**Stack:** Python 3.11, FastAPI, SQLite, Docker, nginx

## Daily Operations

### Morning Checklist (5 min)

```bash
# 1. Check all services running
docker-compose ps

# 2. Check health endpoints
curl https://iamaim.ru/health
curl https://iamaim.ru/ready

# 3. Check error rate (last 24h)
# Open Grafana: https://iamaim.ru:3000
# Check "Error Rate" panel

# 4. Check API costs (last 24h)
# Check "API Costs" panel in Grafana

# 5. Review alerts
# Open Prometheus: https://iamaim.ru:9090/alerts
```

### Weekly Tasks (30 min)

- Review logs for errors: `docker-compose logs app | grep ERROR`
- Check disk space: `df -h`
- Review API usage and costs
- Update dependencies if needed
- Review and close resolved alerts

### Monthly Tasks (2 hours)

- Security updates: `apt update && apt upgrade`
- Review and optimize database
- Test backup/restore procedures
- Review and update documentation
- Capacity planning review

## Common Tasks

### Restart Services

```bash
# Restart all services
docker-compose restart

# Restart specific service
docker-compose restart app

# Full restart (rebuild)
docker-compose down
docker-compose up -d --build
```

### View Logs

```bash
# All logs
docker-compose logs -f

# Specific service
docker-compose logs -f app

# Last 100 lines
docker-compose logs --tail=100 app

# Search for errors
docker-compose logs app | grep ERROR
```

### Check Resource Usage

```bash
# Container stats
docker stats

# Disk usage
df -h
du -sh data/production/

# Memory usage
free -h
```

### Update Configuration

```bash
# 1. Edit configuration
nano .env.production

# 2. Restart services
docker-compose restart

# 3. Verify changes
docker-compose logs app | tail -20
```

## Troubleshooting

### Service Won't Start

**Symptoms:** Container exits immediately

**Diagnosis:**
```bash
# Check logs
docker-compose logs app

# Check configuration
docker-compose config

# Check ports
netstat -tulpn | grep 8000
```

**Solutions:**
- Check environment variables
- Verify database connection
- Check port conflicts
- Review recent changes

### High Error Rate

**Symptoms:** Error rate >5%

**Diagnosis:**
```bash
# Check recent errors
docker-compose logs app | grep ERROR | tail -50

# Check Grafana dashboard
# Open: https://iamaim.ru:3000

# Check Prometheus alerts
# Open: https://iamaim.ru:9090/alerts
```

**Solutions:**
- Check API rate limits
- Verify API keys valid
- Check database connection
- Review recent deployments

### Slow Performance

**Symptoms:** Response time >2s

**Diagnosis:**
```bash
# Check resource usage
docker stats

# Check database size
ls -lh data/production/aim.db

# Check logs for slow queries
docker-compose logs app | grep "slow"
```

**Solutions:**
- Optimize database queries
- Increase container resources
- Check API rate limits
- Review caching strategy

## Emergency Procedures

### Complete Outage

1. Check server status: `ping iamaim.ru`
2. SSH to server: `ssh user@iamaim.ru`
3. Check services: `docker-compose ps`
4. Check logs: `docker-compose logs`
5. Restart if needed: `docker-compose restart`
6. If unrecoverable: Follow disaster recovery plan

### Security Incident

1. **Isolate:** Disconnect from network
2. **Assess:** Review logs for breach
3. **Contain:** Change all credentials
4. **Recover:** Restore from clean backup
5. **Monitor:** Enhanced monitoring
6. **Report:** Document incident

## Maintenance Windows

**Scheduled:** Every Sunday 3:00-4:00 AM GMT+3

**Procedure:**
1. Notify users (if applicable)
2. Create backup: `./scripts/backup.sh`
3. Perform maintenance
4. Test all functionality
5. Monitor for issues

## Contact Information

- **Primary:** Mikhail Eliseev (me@mikhaileliseev.com)
- **Hosting:** [Provider support]
- **Domain:** [Registrar support]
