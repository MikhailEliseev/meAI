# Rollback Procedures

## When to Rollback

Rollback immediately if:
- Critical functionality broken
- Data corruption detected
- Security vulnerability introduced
- Performance degradation >50%
- Error rate >10%

## Rollback Methods

### Method 1: Docker Image Rollback (Fastest)

**Use when:** New deployment has issues

**Steps:**
```bash
# 1. Check current version
docker images aim

# 2. Stop current version
docker-compose down

# 3. Update docker-compose.yml to previous image
# Change: image: aim:v1.2.0
# To: image: aim:v1.1.0

# 4. Start previous version
docker-compose up -d

# 5. Verify health
curl http://localhost/health

# 6. Monitor logs
docker-compose logs -f app
```

**Time:** 2-5 minutes

### Method 2: Git Rollback (Code Issues)

**Use when:** Code changes need to be reverted

**Steps:**
```bash
# 1. Find last good commit
git log --oneline

# 2. Revert to last good commit
git revert <commit-hash>

# 3. Rebuild and deploy
docker-compose build
docker-compose up -d

# 4. Verify health
curl http://localhost/health
```

**Time:** 5-10 minutes

### Method 3: Database Rollback (Schema Changes)

**Use when:** Database migration caused issues

**Steps:**
```bash
# 1. Stop application
docker-compose stop app

# 2. Rollback migration
alembic downgrade -1

# 3. Verify schema
sqlite3 data/production/aim.db ".schema"

# 4. Start application
docker-compose start app

# 5. Verify health
curl http://localhost/health
```

**Time:** 5-10 minutes

### Method 4: Full System Rollback (Complete Restore)

**Use when:** Multiple components affected

**Steps:**
```bash
# 1. Stop all services
docker-compose down

# 2. Restore from backup
./scripts/restore.sh <timestamp>

# 3. Verify all services
docker-compose ps

# 4. Run health checks
curl http://localhost/health
curl http://localhost/ready
```

**Time:** 15-30 minutes

## Post-Rollback Actions

1. **Notify stakeholders** of rollback
2. **Document root cause** of issue
3. **Create fix plan** for next deployment
4. **Test fix** in staging environment
5. **Schedule re-deployment** when ready

## Rollback Decision Matrix

| Issue Severity | User Impact | Rollback Decision |
|----------------|-------------|-------------------|
| Critical | High | Immediate rollback |
| High | Medium | Rollback within 15 min |
| Medium | Low | Fix forward if possible |
| Low | None | Fix in next release |
