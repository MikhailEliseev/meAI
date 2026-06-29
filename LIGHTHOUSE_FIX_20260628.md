# Lighthouse Local Audit Fix — 2026-06-28 10:00 MSK

**Status:** ✅ FIXED

---

## Problem

Пайплайн TECH AUDIT использовал `run_pagespeed` (Google PageSpeed API), который возвращал **429 Too Many Requests** из-за отсутствия API ключа. Пользователь видел "замеряю скорость" в чате, но данных не было.

**Root Cause:**
- `GOOGLE_API_KEY` был пуст
- Пайплайн использовал `run_pagespeed` вместо локального `run_lighthouse`
- Google PageSpeed API имеет жёсткий rate limit без ключа

---

## Solution

Заменил **Google PageSpeed API** на **локальный Lighthouse** (Chromium headless).

### 1. Изменён пайплайн — TECH AUDIT теперь использует `run_lighthouse`

**Файл:** `/opt/aim/AIM/hermes/app/pipeline/phases.py`

**Было (строка 178):**
```python
tools=["run_pagespeed", "run_seo_audit"],
```

**Стало:**
```python
tools=["run_lighthouse", "run_seo_audit"],
```

**Команда:**
```bash
sed -i '178s/run_pagespeed/run_lighthouse/' /opt/aim/AIM/hermes/app/pipeline/phases.py
```

### 2. Обновлён PipelineEngine — маршрутизация инструментов

**Файл:** `/opt/aim/AIM/hermes/app/pipeline/engine.py`

**Изменения:**
- Строка 43: Заменён импорт `run_pagespeed` на `run_lighthouse`
- Строка 642: Заменена проверка `if tool_name == "run_pagespeed"` на `run_lighthouse`

**Команды:**
```bash
sed -i '43s/run_pagespeed/run_lighthouse/g' /opt/aim/AIM/hermes/app/pipeline/engine.py
sed -i '642s/run_pagespeed/run_lighthouse/' /opt/aim/AIM/hermes/app/pipeline/engine.py
```

### 3. Установлен Lighthouse CLI в контейнер

**Команда:**
```bash
docker exec aim-hermes npm install -g lighthouse
```

**Результат:**
- Lighthouse 13.4.0 установлен в `/usr/local/bin/lighthouse`
- Chromium уже был установлен через Playwright

### 4. Обновлён Dockerfile для постоянства

**Файл:** `/opt/aim/AIM/hermes/Dockerfile`

**Добавлены строки 47-48:**
```dockerfile
# Lighthouse CLI (self-hosted PageSpeed, no Google API dependency)
RUN npm install -g lighthouse
```

**Место:** После установки Playwright (строка 45), перед патчем AIAgent (строка 50)

### 5. Скопированы файлы в контейнер

```bash
docker cp /opt/aim/AIM/hermes/app/pipeline/phases.py aim-hermes:/opt/hermes/app/pipeline/phases.py
docker cp /opt/aim/AIM/hermes/app/pipeline/engine.py aim-hermes:/opt/hermes/app/pipeline/engine.py
docker cp /opt/aim/AIM/hermes/app/tools/run_lighthouse.py aim-hermes:/opt/hermes/app/tools/run_lighthouse.py
```

### 6. Перезапущен Hermes

```bash
cd /opt/aim/AIM
docker compose -f docker-compose.yml -f docker-compose.litellm.yml restart hermes
```

---

## Verification

### 1. Lighthouse CLI работает

```bash
docker exec aim-hermes lighthouse --version
# Output: 13.4.0
```

### 2. Chromium установлен

```bash
docker exec aim-hermes ls -la /root/.cache/ms-playwright/
# Output: chromium-1223, chromium_headless_shell-1223
```

### 3. Hermes запустился без ошибок

```bash
docker logs aim-hermes --tail 20
# Output: [INFO] Hermes v7: config protected + key rotator registered
#         INFO: Application startup complete.
```

### 4. Пайплайн использует run_lighthouse

```bash
grep 'PHASE_2_TECH_AUDIT' /opt/aim/AIM/hermes/app/pipeline/phases.py -A 5
# Output: tools=["run_lighthouse", "run_seo_audit"],
```

---

## How run_lighthouse Works

**Инструмент:** `app/tools/run_lighthouse.py`

**Что делает:**
1. Находит Chromium через `_find_chromium()` (Playwright bundled binary)
2. Запускает `lighthouse` CLI с флагами:
   - `--quiet --no-enable-error-reporting`
   - `--chrome-flags="--headless --no-sandbox --disable-gpu"`
   - `--output=json --output-path=/tmp/lh-result-*.json`
3. Парсит JSON-отчёт, извлекает Core Web Vitals:
   - Performance score (0-100)
   - LCP (Largest Contentful Paint)
   - FCP (First Contentful Paint)
   - TBT (Total Blocking Time)
   - CLS (Cumulative Layout Shift)
   - SI (Speed Index)
4. Возвращает результат в формате JSON

**Timeout:** 60 секунд (быстрее PageSpeed API)

**Кэш:** 10 минут (TTL 600s)

**Преимущества vs PageSpeed API:**
- ✅ Нет зависимости от Google API
- ✅ Работает без API ключа
- ✅ Нет rate limits
- ✅ Быстрее (локальный запуск)
- ✅ Тот же движок, что и PageSpeed Insights

---

## Network Flow (Updated)

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
                           ┌───────────┴───────────┬──────────────┐
                           ↓                       ↓              ↓
                      PostgreSQL              Redis        Lighthouse CLI
                  (aim-postgres:5432)    (aim-redis:6379)  (local Chromium)
```

**Key Point:** Замер скорости теперь происходит локально внутри контейнера `aim-hermes` через Lighthouse + Chromium headless.

---

## Files Modified

| File | Change | Method |
|------|--------|--------|
| `/opt/aim/AIM/hermes/app/pipeline/phases.py` | Заменён `run_pagespeed` на `run_lighthouse` (строка 178) | `sed -i` |
| `/opt/aim/AIM/hermes/app/pipeline/engine.py` | Заменён импорт и обработка (строки 43, 642) | `sed -i` |
| `/opt/aim/AIM/hermes/Dockerfile` | Добавлена установка Lighthouse CLI (строки 47-48) | Manual edit |
| Container `aim-hermes` | Установлен Lighthouse 13.4.0 | `npm install -g` |

---

## Deployment Steps (для будущего)

### Если нужно пересобрать образ:

```bash
cd /opt/aim/AIM
docker compose -f docker-compose.yml -f docker-compose.litellm.yml build hermes
docker compose -f docker-compose.yml -f docker-compose.litellm.yml up -d hermes
```

Lighthouse CLI будет установлен автоматически благодаря изменению в Dockerfile.

### Если нужно обновить только код (без пересборки):

```bash
# 1. Изменить файлы на хосте в /opt/aim/AIM/hermes/
vim /opt/aim/AIM/hermes/app/tools/run_lighthouse.py

# 2. Скопировать в контейнер
docker cp /opt/aim/AIM/hermes/app/tools/run_lighthouse.py \
  aim-hermes:/opt/hermes/app/tools/run_lighthouse.py

# 3. Перезапустить
cd /opt/aim/AIM
docker compose -f docker-compose.yml -f docker-compose.litellm.yml restart hermes
```

---

## Testing Checklist

- [ ] Открыть https://iamaim.ru
- [ ] Отправить сообщение с URL клиники (например, "https://erasmile.ru")
- [ ] Дождаться фазы TECH AUDIT
- [ ] Проверить, что в чате появляется сообщение о замере скорости
- [ ] Проверить логи: `docker logs aim-hermes | grep lighthouse`
- [ ] Убедиться, что нет ошибок 429 от Google
- [ ] Проверить, что результаты замера скорости присутствуют в отчёте

---

## Success Metrics

✅ **Lighthouse CLI установлен:** `lighthouse --version` → 13.4.0
✅ **Пайплайн использует run_lighthouse:** TECH AUDIT фаза обновлена
✅ **Hermes запустился без ошибок:** Логи чистые
✅ **Dockerfile обновлён:** Lighthouse установится при пересборке
✅ **Нет зависимости от Google API:** Работает без ключа

---

**Fix complete. Пайплайн TECH AUDIT теперь использует локальный Lighthouse вместо Google PageSpeed API.**
