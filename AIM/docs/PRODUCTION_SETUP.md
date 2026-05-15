# Production Environment Setup Guide

## Overview

This guide covers the complete setup of the AIM Agency production environment, including environment configuration, API keys, database initialization, and validation.

**Last Updated:** 2026-05-15  
**Status:** ✅ Environment Configuration Complete

---

## Prerequisites

- Python 3.11+
- Virtual environment activated
- Git repository cloned
- Domain: iamaim.ru (configured)

---

## 1. Environment Configuration

### 1.1 Create Production Environment File

The `.env.production` file contains all production configuration:

```bash
# Location
AIM/.env.production

# Permissions (restrictive)
chmod 600 .env.production

# Git ignore (already configured)
echo ".env.production" >> .gitignore
```

### 1.2 Environment Variables

**Application Settings:**
```bash
ENVIRONMENT=production
DEBUG=false
LOG_LEVEL=INFO
SECRET_KEY=<64-char-hex-string>
```

**Database:**
```bash
DATABASE_URL=sqlite+aiosqlite:///./data/production/aim.db
```

**API Keys:**
```bash
# Google Analytics 4 (service account JSON path)
GOOGLE_ANALYTICS_KEY=/Users/mikhaileliseev/Desktop/Dev/!meAI/AIM/config/ga4-service-account.json

# Yandex Metrica (OAuth credentials)
YANDEX_METRICA_CLIENT_ID=c3582220a6634313a721333e51de6d6b
YANDEX_METRICA_CLIENT_SECRET=a5e7c56fc35745448510ce40963a54d6

# Yandex Direct (API token)
YANDEX_DIRECT_TOKEN=9bce35db-4041-4825-91e8-2f24a1ee1316
```

---

## 2. Database Setup

### 2.1 Initialize Database

**Create Directory:**
```bash
mkdir -p data/production
```

**Initialize Schema:**
```bash
source ../venv/bin/activate
python scripts/validate_environment.py
```

---

## 3. Environment Validation

### 3.1 Run Validation Script

```bash
source ../venv/bin/activate
python scripts/validate_environment.py
```

**Expected:** ✅ All checks passed (21/21)

---

## 4. Security Checklist

- [x] `.env.production` has 600 permissions
- [x] Service account JSON has 600 permissions
- [x] Secrets not committed to git
- [x] SECRET_KEY is 64+ characters
- [x] DEBUG=false in production
- [x] Database file has restrictive permissions
- [x] API keys tested and working
- [x] Validation script passes all checks

---

**Status:** ✅ Environment Configuration Complete  
**Validation:** ✅ All checks passed (21/21)  
**Ready for:** Deployment Infrastructure (Plan 07-02)
