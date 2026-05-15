# Disaster Recovery Plan

## Overview

This document outlines procedures for recovering AIM Agency system from various disaster scenarios.

## Objectives

- **RTO (Recovery Time Objective):** 1 hour
- **RPO (Recovery Point Objective):** 24 hours
- **Availability Target:** 99.9% (8.76 hours downtime/year)

## Disaster Scenarios

### 1. Complete Server Failure

**Symptoms:** Server unresponsive, cannot SSH

**Recovery Steps:**
1. Provision new server (same specs)
2. Install Docker and dependencies
3. Clone repository: `git clone https://github.com/user/meAI.git`
4. Restore latest backup: `./scripts/restore.sh <timestamp>`
5. Update DNS to point to new server
6. Verify all services running
7. Monitor for 24 hours

**Estimated Time:** 45-60 minutes

### 2. Database Corruption

**Symptoms:** Database errors, data inconsistency

**Recovery Steps:**
1. Stop application: `docker-compose stop app`
2. Backup corrupted database: `cp data/production/aim.db data/production/aim.db.corrupted`
3. Restore from backup: `gunzip -c /backups/aim_db_<timestamp>.db.gz > data/production/aim.db`
4. Verify database integrity: `sqlite3 data/production/aim.db "PRAGMA integrity_check;"`
5. Start application: `docker-compose start app`
6. Verify health: `curl http://localhost/health`

**Estimated Time:** 15-30 minutes

### 3. Configuration Loss

**Symptoms:** Services fail to start, configuration errors

**Recovery Steps:**
1. Restore configurations: `tar -xzf /backups/config_<timestamp>.tar.gz`
2. Verify environment variables: `cat .env.production`
3. Restart services: `docker-compose restart`
4. Verify health: `curl http://localhost/health`

**Estimated Time:** 10-15 minutes

### 4. Security Breach

**Symptoms:** Unauthorized access, suspicious activity

**Recovery Steps:**
1. **Immediate:** Isolate system (disconnect from network)
2. **Assess:** Review logs for breach extent
3. **Contain:** Change all passwords and API keys
4. **Eradicate:** Remove malicious code/access
5. **Recover:** Restore from clean backup
6. **Monitor:** Enhanced monitoring for 30 days
7. **Report:** Document incident and lessons learned

**Estimated Time:** 2-4 hours

## Contact Information

- **Primary:** Mikhail Eliseev (me@mikhaileliseev.com)
- **Hosting Provider:** [Provider support]
- **Domain Registrar:** [Registrar support]

## Testing Schedule

- **Monthly:** Backup verification (restore to test environment)
- **Quarterly:** DR drill (simulate scenario, measure RTO)
- **Annually:** Full recovery test (complete system rebuild)

## Post-Recovery Checklist

- [ ] All services running and healthy
- [ ] Database integrity verified
- [ ] API keys working
- [ ] Monitoring operational
- [ ] Logs being collected
- [ ] Backups resuming
- [ ] Performance normal
- [ ] Document incident and recovery time
