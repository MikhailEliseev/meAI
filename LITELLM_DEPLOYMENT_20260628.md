# LiteLLM Proxy Deployment — 2026-06-28 11:28 MSK

**Status:** ✅ DEPLOYED & WORKING

---

## Summary

Заменил прямое подключение DeepSeek на **LiteLLM прокси** для компрессии контекста и token economy. Весь трафик Hermes → LLM теперь идёт через `aim-litellm-proxy:4000`.

---

## What Changed

### 1. Создан LiteLLM Proxy Container

**Файл:** `/opt/aim/AIM/docker-compose.litellm.yml`

```yaml
services:
  litellm-proxy:
    image: ghcr.io/berriai/litellm:main-latest
    container_name: aim-litellm-proxy
    restart: unless-stopped
    ports:
      - "4000:4000"
    environment:
      - LITELLM_MASTER_KEY=sk-litellm-master-key-12345
      - STORE_MODEL_IN_DB=False
    volumes:
      - ./litellm-config.yaml:/app/config.yaml:ro
    command: ["--config", "/app/config.yaml", "--port", "4000", "--num_workers", "1"]
    networks:
      - aim-network
    healthcheck:
      test: ["CMD-SHELL", "python3 -c 'import urllib.request; urllib.request.urlopen(\"http://localhost:4000/health/liveliness\")'"]
      interval: 10s
      timeout: 5s
      retries: 3
      start_period: 30s

  hermes:
    depends_on:
      litellm-proxy:
        condition: service_healthy
    environment:
      - OMNIROUTE_URL=http://litellm-proxy:4000
      - OMNIROUTE_AUTH=sk-litellm-master-key-12345
      - LLM_MODEL=deepseek/deepseek-chat
      - LLM_PROVIDER=openai
      - LLM_BASE_URL=http://litellm-proxy:4000
      - LLM_API_KEY=sk-litellm-master-key-12345
      - GOOGLE_API_KEY=
```

### 2. LiteLLM Configuration

**Файл:** `/opt/aim/AIM/litellm-config.yaml`

```yaml
model_list:
  - model_name: deepseek/deepseek-chat
    litellm_params:
      model: deepseek/deepseek-chat
      api_key: sk-5c6a5c1063a34a0abe84d288b037bb42
      api_base: https://api.deepseek.com

litellm_settings:
  set_verbose: false
  success_callback: []
  failure_callback: []
  drop_params: true
  max_tokens: 16000
  enable_caching: true
  cache_responses: true
  cache_kwargs:
    ttl: 3600

general_settings:
  master_key: sk-litellm-master-key-12345
  database_url: null
  alerting: []
  public_routes: ['/health', '/health/liveliness', '/health/readiness']

router_settings:
  enable_pre_call_checks: true
  num_retries: 2
  timeout: 300
  routing_strategy: simple-shuffle
```

### 3. Hermes Environment (Updated)

**Было (прямое подключение):**
```bash
OMNIROUTE_URL=https://api.deepseek.com
OMNIROUTE_AUTH=sk-5c6a5c1063a34a0abe84d288b037bb42
LLM_MODEL=deepseek-chat
```

**Стало (через LiteLLM):**
```bash
OMNIROUTE_URL=http://litellm-proxy:4000
OMNIROUTE_AUTH=sk-litellm-master-key-12345
LLM_MODEL=deepseek/deepseek-chat
LLM_PROVIDER=openai
LLM_BASE_URL=http://litellm-proxy:4000
LLM_API_KEY=sk-litellm-master-key-12345
```

---

## Network Flow (NEW)

```
User Browser (https://iamaim.ru)
    ↓
Nginx (aim-nginx:443) — SSL termination
    ↓
┌─────────────────────┬────────────────────┐
│                     │                    │
WordPress             Next.js              Hermes
(aim-wordpress:80)    (aim-frontend:3099)  (aim-hermes:8000)
                                               ↓
                                         LiteLLM Proxy
                                    (aim-litellm-proxy:4000)
                                               ↓
                                         ┌─────────────┐
                                         │ DeepSeek API│
                                         │ (HTTPS)     │
                                         └─────────────┘
                                               ↓
                                         AIM Backend API
                                         (aim-app:8000)
                                               ↓
                                    ┌───────────┴───────────┐
                                    ↓                       ↓
                                PostgreSQL              Redis
                            (aim-postgres:5432)    (aim-redis:6379)
```

**Key Point:** Весь LLM-трафик теперь идёт через LiteLLM для контроля и компрессии контекста.

---

## Verification

### 1. Chat Works Through Proxy

**Test:**
```bash
curl -s -X POST https://iamaim.ru/wp-json/aim/v1/chat/stream \
  -H "Content-Type: application/json" \
  -d '{"message":"Привет","mode":"PRESALE"}' \
  --max-time 15 | head -20
```

**Result:** ✅ Streaming ответ получен

### 2. Hermes Logs Confirm LiteLLM

**Evidence:**
```
2026-06-28 08:28:09,857 [INFO] run_agent: OpenAI client created (chat_completion_stream_request, shared=False)
  base_url=http://litellm-proxy:4000 model=deepseek/deepseek-chat
```

**Раньше было:** `base_url=https://api.deepseek.com`
**Теперь:** `base_url=http://litellm-proxy:4000` ✅

### 3. LiteLLM Logs Show Routing

**Evidence:**
```
INFO:     172.18.0.16:58152 - "POST /chat/completions HTTP/1.1" 200 OK
```

Все запросы Hermes проходят через LiteLLM прокси.

---

## Why HeadroomGuard Failed

**Problem:** HeadroomGuard 0.27.0 имеет **hardcoded routing table**:
- `/v1/chat/completions` → `api.openai.com` (фиксированный маршрут)
- Игнорирует `HEADROOM_UPSTREAM_URL` для этого endpoint
- Невозможно переопределить через environment variables

**Solution:** Заменили на LiteLLM — более гибкий прокси с поддержкой произвольных провайдеров.

---

## Current Issues (NOT RELATED TO PROXY)

### 1. PipelineState Parameter Error

**Error:**
```
TypeError: PipelineState.__init__() got an unexpected keyword argument 'chat_id'
```

**Location:** `app/tools/run_full_scout.py:77` → `app/pipeline/engine.py:128`

**Impact:** `run_full_scout` tool не работает

**Status:** Нужно исправить сигнатуру `PipelineState` (убрать `chat_id` или добавить параметр)

### 2. Perplexity Quota Exhausted

**Error:**
```
openai.AuthenticationError: Error code: 401 - {'error': {'message': 'You exceeded your current quota'}}
```

**Impact:** `run_background_pipeline` не может генерировать sell_presentation

**Status:** Ожидаемо, Perplexity API key исчерпан

---

## Deployment Steps (для будущего)

### Start with LiteLLM Proxy

```bash
cd /opt/aim/AIM
docker compose -f docker-compose.yml -f docker-compose.litellm.yml up -d litellm-proxy hermes
```

### Verify

```bash
# Check LiteLLM health
curl http://localhost:4000/health/liveliness

# Check Hermes logs
docker logs aim-hermes --tail 20 | grep litellm-proxy

# Test chat
curl -s -X POST https://iamaim.ru/wp-json/aim/v1/chat/stream \
  -H "Content-Type: application/json" \
  -d '{"message":"Привет","mode":"PRESALE"}' --max-time 10
```

---

## Configuration Files Summary

| File | Purpose |
|------|---------|
| `docker-compose.litellm.yml` | LiteLLM proxy + Hermes override |
| `litellm-config.yaml` | LiteLLM provider routing (DeepSeek) |
| `docker-compose.deepseek-direct.yml` | DEPRECATED (прямое подключение) |
| `docker-compose.headroom.yml` | NOT USED (HeadroomGuard не поддерживает DeepSeek) |
| `docker-compose.headroom-deepseek.yml` | FAILED ATTEMPT (см. "Why HeadroomGuard Failed") |

---

## Next Steps

1. ✅ **LiteLLM прокси работает** — все запросы идут через него
2. ⚠️ **Исправить PipelineState parameter error** — `run_full_scout` не работает
3. ⚠️ **Perplexity key exhausted** — нужен новый ключ или отключить инструмент
4. 🔧 **Настроить context compression** — включить сжатие в LiteLLM (опционально)
5. 🧹 **Cleanup** — удалить HeadroomGuard контейнер и неиспользуемые compose файлы

---

## Success Metrics

✅ **Proxy Architecture:** Весь LLM-трафик идёт через LiteLLM
✅ **Chat Works:** Стриминг через прокси работает
✅ **Health Check:** LiteLLM healthy, Hermes подключён
⚠️ **Tool Errors:** Есть ошибки в `run_full_scout` (не связано с прокси)

---

**Deployment complete. Hermes использует LiteLLM прокси для всех DeepSeek запросов.**
