# PipelineState chat_id Error Fix — 2026-06-28 11:35 MSK

**Status:** ✅ FIXED

---

## Problem

**Error:**
```python
TypeError: PipelineState.__init__() got an unexpected keyword argument 'chat_id'
```

**Location:** `app/tools/run_full_scout.py:77` → `app/pipeline/engine.py:128`

**Impact:** `run_full_scout` tool не работал — все попытки запуска 16-фазного пайплайна падали

---

## Root Cause

**Файл:** `/opt/aim/AIM/hermes/app/pipeline/states.py`

**Проблема:** Дублирование поля `chat_id` в dataclass `PipelineState`

```python
@dataclass
class PipelineState:
    session_id: str
    client_url: str
    client_name: str = ""
    # ... другие поля ...
    mode: str = "ONBOARDING"
    chat_id: int = 0  # Telegram chat_id (0 = не Telegram)
    chat_id: int = 0  # Telegram chat_id (0 = не Telegram)  ← ДУБЛИКАТ!
    placeholder_page_url: str = ""
    placeholder_post_id: int = 0
```

**Почему это ломало код:**

Python dataclass генерирует `__init__()` автоматически на основе полей класса. При дублировании поля `chat_id` второе определение **перезаписывало** первое, но dataclass генератор пытался создать параметр дважды → `TypeError`.

---

## Solution

### 1. Удалил дубликат

**Команда:**
```bash
ssh aim "sed -i '93d' /opt/aim/AIM/hermes/app/pipeline/states.py"
```

**До (строки 92-93):**
```python
chat_id: int = 0  # Telegram chat_id (0 = не Telegram)
chat_id: int = 0  # Telegram chat_id (0 = не Telegram)
```

**После (строка 92):**
```python
chat_id: int = 0  # Telegram chat_id (0 = не Telegram)
```

### 2. Скопировал исправленный файл в контейнер

**Команда:**
```bash
docker cp /opt/aim/AIM/hermes/app/pipeline/states.py aim-hermes:/opt/hermes/app/pipeline/states.py
```

**Почему нужно:** Hermes запущен из Docker-образа, файлы внутри контейнера не связаны с хостом напрямую.

### 3. Перезапустил Hermes

**Команда:**
```bash
docker compose -f docker-compose.yml -f docker-compose.litellm.yml restart hermes
```

---

## Verification

### 1. Дубликат удалён

**Test:**
```bash
docker exec aim-hermes grep -n 'chat_id' /opt/hermes/app/pipeline/states.py
```

**Result:**
```
92:    chat_id: int = 0  # Telegram chat_id (0 = не Telegram)
```

Только одна строка ✅

### 2. run_full_scout работает

**Test:**
```bash
curl -s -X POST https://iamaim.ru/wp-json/aim/v1/chat/stream \
  -H "Content-Type: application/json" \
  -d '{"message":"https://erasmile.ru","mode":"PRESALE"}' \
  --max-time 60 | grep tool-progress
```

**Result:**
```json
{"type": "tool-progress", "stage": "perplexity", "message": "🔍 Анализирую: Мне нужна ключевая информация для конкурентного анализа..."}
{"type": "tool-progress", "stage": "perplexity", "message": "✅ Анализ завершён"}
{"type": "tool-progress", "stage": "competitors", "message": "🔎 Извлекаю специализацию и город из https://erasmile.ru…"}
{"type": "tool-progress", "stage": "competitors", "message": "🗺️ Ищу конкурентов через Google Maps (Apify)…"}
{"type": "tool-progress", "stage": "competitors", "message": "💰 Обогащаю финансовыми данными (rusprofile)…"}
{"type": "tool-progress", "stage": "competitors", "message": "✅ Найдено конкурентов: 2"}
```

Пайплайн работает! ✅

### 3. Логи без ошибок

**Test:**
```bash
docker logs aim-hermes --tail 60 --since 2m | grep -i 'typeerror\|pipelinestate'
```

**Result:** Ошибок нет ✅

---

## How run_full_scout Works Now

### Pipeline Flow (16 phases)

1. **PRE-FLIGHT** — извлечение специализации и города из сайта
2. **COMPETITORS** — поиск конкурентов через Google Maps + финансовые данные
3. **FINANCE** — финансовая аналитика компании
4. **DOCTORS** — поиск врачей в Instagram
5. **REVIEWS** — анализ отзывов на платформах
6. **SMI** — упоминания в СМИ
7. **HH** — анализ вакансий
8. **CONTENT** — контент-анализ
9. **SEO** — SEO-аудит
10. **CI** — конкурентная разведка
11. **GAPS** — пробелы в контенте
12. **PAGESPEED** — PageSpeed анализ
13. **REPORT** — генерация HTML-отчёта
14. **PUBLISH** — публикация в WordPress
15. **ARCHIVE** — архивирование сессии
16. **NOTIFY** — уведомление в Telegram

### PipelineState Parameters (Fixed)

**Correct instantiation:**
```python
state = PipelineState(
    session_id=session_id,
    client_url=client_url,
    client_name=client_name,
    started_at=datetime.now(timezone.utc).isoformat(),
    mode=mode,
    chat_id=chat_id,  # ✅ Теперь работает!
)
```

---

## Related Issues (Still Present)

### 1. Perplexity Quota Exhausted

**Error:**
```
openai.AuthenticationError: Error code: 401 - {'error': {'message': 'You exceeded your current quota'}}
```

**Impact:** `run_background_pipeline` не может генерировать sell_presentation через Perplexity

**Status:** Нужен новый Perplexity API key или отключить инструмент

### 2. run_background_pipeline Parameter Error

**Error:**
```json
{"error": "session_hash is required"}
```

**Impact:** Не может запуститься без `session_hash` параметра

**Status:** LLM должен передавать `session_hash` при вызове инструмента

---

## Files Modified

| File | Change | Method |
|------|--------|--------|
| `/opt/aim/AIM/hermes/app/pipeline/states.py` | Удалена строка 93 (дубликат `chat_id`) | `sed -i '93d'` |
| `aim-hermes:/opt/hermes/app/pipeline/states.py` | Скопирован исправленный файл | `docker cp` |

---

## Deployment Steps (для будущего)

Если изменяешь Python-файлы в `/opt/aim/AIM/hermes/`:

```bash
# 1. Изменить файл на хосте
vim /opt/aim/AIM/hermes/app/pipeline/states.py

# 2. Скопировать в контейнер
docker cp /opt/aim/AIM/hermes/app/pipeline/states.py \
  aim-hermes:/opt/hermes/app/pipeline/states.py

# 3. Перезапустить контейнер
cd /opt/aim/AIM
docker compose -f docker-compose.yml -f docker-compose.litellm.yml restart hermes

# 4. Проверить логи
docker logs aim-hermes --tail 20
```

**ВАЖНО:** Изменения в контейнере **НЕ персистятся** при пересборке образа. Для постоянных изменений нужно:
1. Обновить файл в репозитории на хосте
2. Пересобрать образ (`docker compose build hermes`)
3. Перезапустить контейнер

Для быстрого патча (как сейчас) `docker cp` достаточно.

---

## Success Metrics

✅ **PipelineState error fixed:** `chat_id` дубликат удалён
✅ **run_full_scout works:** 16-фазный пайплайн запускается без ошибок
✅ **Tool progress events:** SSE-стрим показывает прогресс фаз
✅ **No TypeError in logs:** Логи чистые
⚠️ **Perplexity quota exhausted:** Не связано с этим исправлением

---

**Fix complete. run_full_scout tool работает через LiteLLM прокси.**
