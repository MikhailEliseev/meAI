# AIM System Diagnostics Report
**Date:** 2026-06-28 11:12 MSK
**Server:** Polish (78.17.128.169, ssh aim)

---

## 1. Docker Containers Status ✅

| Container | Status | Health |
|-----------|--------|--------|
| aim-hermes | Up ~2min | healthy |
| aim-headroom-proxy | Up ~2min | healthy (not used) |
| aim-app | Up 8h | healthy |
| aim-postgres | Up 8h | healthy |
| aim-redis | Up 8h | healthy |
| aim-frontend | Up 44min | healthy |
| aim-wordpress | Up 40min | healthy |
| aim-mysql | Up 40min | healthy |
| aim-nginx | Up 44min | healthy |
| aim-grafana | Up 8h | running |
| aim-prometheus | Up 8h | running |
| aim-alertmanager | Up 8h | running |
| aim-node-exporter | Up 8h | running |
| aim-postgres-exporter | Up 44min | running |

**Total:** 14 containers running

---

## 2. Hermes Environment Variables ✅

```bash
DEEPSEEK_API_KEY=sk-37839c50424c4d37b0c2a071eb3d5e55  # UNUSED (старый ключ)
GOOGLE_API_KEY=                                      # DISABLED ✅
LLM_API_KEY=sk-5c6a5c1063a34a0abe84d288b037bb42     # ACTIVE ✅
LLM_BASE_URL=https://api.deepseek.com                # ACTIVE ✅
LLM_MODEL=deepseek-chat                              # ACTIVE ✅
LLM_PROVIDER=custom                                  # ACTIVE ✅
OMNIROUTE_AUTH=sk-5c6a5c1063a34a0abe84d288b037bb42   # ACTIVE ✅
OMNIROUTE_URL=https://api.deepseek.com               # ACTIVE ✅
```

**Status:** ✅ Правильная конфигурация для прямого подключения DeepSeek

---

## 3. DeepSeek API Connectivity ✅

**Test Request:**
```bash
POST https://api.deepseek.com/v1/chat/completions
Authorization: Bearer sk-5c6a5c1063a34a0abe84d288b037bb42
```

**Response ID:** `f9ed0a59-f46e-487f-a2b6-dbe4fb0e50e8`

**Status:** ✅ API работает, ключ валидный

---

## 4. Internal Docker Network ✅

| Connection | Status |
|-----------|--------|
| Hermes → AIM App (http://app:8000) | ✅ healthy |
| Hermes → PostgreSQL (postgres:5432) | ✅ Connected |
| Hermes → Redis (redis:6379) | ✅ Connected |

**Status:** ✅ Вся внутренняя сеть работает

---

## 5. External HTTPS Endpoints ✅

### Chat Stream Endpoint
```
POST https://iamaim.ru/wp-json/aim/v1/chat/stream
```
**Response:** SSE stream started, first token: `"Добрый"`

**Status:** ✅ Работает

### Fallback Endpoint
```
POST https://iamaim.ru/wp-json/aim/v1/fallback
```
**Response:** `{"ok": true}`

**Status:** ✅ Работает

---

## 6. Hermes Health Status ✅

```json
{
  "status": "ok",
  "hermes": "healthy",
  "uptime_seconds": 116.6,
  "requests_total": 2,
  "errors_total": 0,
  "knowledge_loop": {
    "executions_total": 0,
    "patterns_total": 0,
    "learnings_total": 0,
    "rules_total": 0,
    "last_ingest": null,
    "loop_health": "idle"
  }
}
```

**Status:** ✅ Здоров, работает

---

## 7. Docker Compose Configuration Chain

**Active Project:** `aim` (14 containers)

**Compose Files Chain (порядок применения):**
1. `docker-compose.yml` — базовая конфигурация
2. `docker-compose.deepseek-direct.yml` — **ACTIVE** прямое подключение DeepSeek
3. `docker-compose.headroom.yml` — HeadroomGuard (запущен, но не используется)
4. `docker-compose.headroom-deepseek.yml` — конфиг для HeadroomGuard + DeepSeek (не используется)
5. `docker-compose.zai-override.yml` — z.ai override (не активен)
6. `docker-compose.override.yml` — локальные переопределения

**Проблема:** ⚠️ Слишком много наложенных compose файлов, некоторые конфликтуют

**Используется:** `docker-compose.deepseek-direct.yml` для прямого DeepSeek API

---

## 8. Recent Hermes Errors ⚠️

```
[ERROR] Tool registration REJECTED: 'web_search' (toolset 'web') would shadow existing tool
[ERROR] run_full_scout: pipeline failed for https://erasmile.ru
[WARNING] Tool run_full_scout returned error: PipelineState.__init__() got an unexpected keyword argument 'chat_id'
[WARNING] Tool run_background_pipeline returned error: session_hash is required
[WARNING] Tool run_validation_check returned error: company_name is required
```

**Проблемы:**
1. ⚠️ Дублирующаяся регистрация инструмента `web_search`
2. ⚠️ Ошибка в `run_full_scout` — неправильная сигнатура `PipelineState.__init__()`
3. ⚠️ Инструменты требуют параметры, которые LLM не передаёт

**Влияние:** Hermes отвечает, но некоторые инструменты не работают

---

## 9. Network Flow Diagram

```
User Browser (https://iamaim.ru)
    ↓
Nginx (aim-nginx:443) — SSL termination
    ↓
┌─────────────────────┬────────────────────┐
│                     │                    │
WordPress             Next.js              Hermes
(aim-wordpress:80)    (aim-frontend:3099)  (aim-hermes:8000)
    ↓                     ↓                    ↓
MariaDB            (proxies to Hermes)     ┌───────────────┐
(aim-mysql:3306)                           │ DeepSeek API  │
                                           │ (direct HTTPS)│
                                           └───────────────┘
                                                ↓
                                           AIM Backend API
                                           (aim-app:8000)
                                                ↓
                                    ┌───────────┴───────────┐
                                    ↓                       ↓
                                PostgreSQL              Redis
                            (aim-postgres:5432)    (aim-redis:6379)
```

---

## 10. HeadroomGuard Status 🚫

**Container:** Running but NOT USED

**Problem:** HeadroomGuard автоматически роутит `/v1/chat/completions` на OpenAI API, игнорируя `HEADROOM_UPSTREAM_URL`

**Solution:** Отключён в пользу прямого подключения через `docker-compose.deepseek-direct.yml`

**Future:** Если понадобится компрессия контекста, нужно настроить HeadroomGuard для OpenAI-compatible endpoints или использовать другой прокси

---

## Summary

### ✅ Working
- DeepSeek API connection (direct)
- All Docker containers healthy
- Internal network (Hermes ↔ App ↔ DB ↔ Redis)
- External HTTPS endpoints (chat stream, fallback)
- Phase 09 React components deployed

### ⚠️ Issues
- Некоторые инструменты Hermes выдают ошибки (`run_full_scout`, `run_background_pipeline`)
- Дублирующаяся регистрация `web_search`
- Слишком много наложенных compose файлов (6 штук)

### 🚫 Not Used
- HeadroomGuard (запущен, но не используется из-за проблем с роутингом)
- Google Gemini API (отключён)
- z.ai API (не активен)

### 📋 Recommendations
1. Почистить docker-compose файлы: оставить только базовый + deepseek-direct
2. Исправить ошибки в `run_full_scout` (неправильная сигнатура `PipelineState`)
3. Отключить HeadroomGuard, если не используется (остановить контейнер)
4. Проверить регистрацию инструментов (дубль `web_search`)
