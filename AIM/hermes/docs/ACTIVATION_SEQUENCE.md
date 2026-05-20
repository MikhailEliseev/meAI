# Hermes Learning Bus — Activation Sequence

**Для:** Михаила Елисеева
**Цель:** Связать разрозненные инструменты в одну систему через Hermes
**Принцип:** Каждый запуск → Hermes запоминает → следующий запуск умнее

---

## Подготовка (однократно)

### 0. Делаю я (Claude Code) — код для Phase 18

Перед тем как ты начнёшь активацию, я создам:
- `AIM/hermes/knowledge/` — vault для хранения опыта (LLM Wiki Pattern)
- `AIM/hermes/app/knowledge_router.py` — API-endpoints для знаний
- `AIM/hermes/knowledge/teacher_sync.py` — синхронизация Teacher → Hermes
- `AIM/src/aim/integration/hermes_context.py` — Magisters запрашивают контекст
- Обновлю CI Orchestrator — публикация execution-событий в EventBus
- Обновлю Magisters — запрос контекста у Hermes перед делегированием

### После того как код создан — запусти:

```bash
# 1. Активируй окружение
cd /Users/mikhaileliseev/Desktop/Dev/!meAI
source venv/bin/activate

# 2. Запусти Hermes
cd AIM/hermes
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

### Проверь что всё работает:

```bash
# Health check
curl http://localhost:8000/health

# Knowledge status (должен быть пустой)
curl http://localhost:8000/api/knowledge/status
# → {"executions_count": 0, "patterns_count": 0, "loop_health": "idle"}
```

---

## Шаг 1: Первый SEO-аудит

**Что делаешь:**
Запускаешь SEO-аудит через API (или через Hermes напрямую):

```bash
curl -X POST https://iamaim.ru/api/seo/audit \
  -H "Content-Type: application/json" \
  -d '{"url": "https://твоя-клиника.рф", "niche": "стоматология", "geo": "Москва", "tier": "quick"}'
```

**Что происходит под капотом:**
1. API → CI Orchestrator → фазы 1-8 → 16 CI-агентов
2. Каждый агент публикует `ci.agent.completed` в EventBus
3. Hermes слушает EventBus → сохраняет в `raw/executions/`
4. Ты видишь результат аудита

**Проверь:**
```bash
curl http://localhost:8000/api/knowledge/status
# → {"executions_count": 1 (или больше), "patterns_count": 0}
```

---

## Шаг 2: Извлечение паттернов (LLM-ingest)

**Что делаешь:**
Говоришь Hermes проанализировать сохранённый опыт:

```bash
curl -X POST http://localhost:8000/api/knowledge/learn \
  -H "Content-Type: application/json" \
  -d '{"execution_id": "latest"}'
```

**Что происходит:**
1. Hermes читает `raw/executions/` → отправляет в LLM
2. LLM извлекает паттерны: что сработало, что нет, находки
3. Сохраняет в `wiki/patterns/`

**Проверь:**
```bash
curl http://localhost:8000/api/knowledge/status
# → {"executions_count": 1, "patterns_count": 1+}

# Посмотри паттерн
ls AIM/hermes/knowledge/wiki/patterns/
```

---

## Шаг 3: Синхронизация Teacher → Hermes

**Что делаешь:**
Teacher знает лучшие практики из внешних исследований. Передай их Hermes:

```bash
python scripts/teacher_cli.py sync-to-hermes --domain seo
```

**Что происходит:**
1. Teacher ищет знания в Qdrant (коллекция: seo_knowledge)
2. Отправляет топ-10 в Hermes
3. Hermes сохраняет в `wiki/learnings/seo/`

**Проверь:**
```bash
curl http://localhost:8000/api/knowledge/status
# → patterns_count и learnings_count > 0
```

---

## Шаг 4: Второй SEO-аудит (с контекстом)

**Что делаешь:**
Запускаешь SEO-аудит для другой клиники:

```bash
curl -X POST https://iamaim.ru/api/seo/audit \
  -H "Content-Type: application/json" \
  -d '{"url": "https://другая-клиника.рф", "niche": "стоматология", "geo": "Москва", "tier": "full"}'
```

**Что происходит (уже по-другому):**
1. SEO Magister запрашивает контекст у Hermes: `GET /api/knowledge/context?domain=seo&action=competitive_analysis`
2. Hermes возвращает: паттерны из прошлого запуска + знания от Teacher
3. Magister добавляет контекст в task payload
4. Subagents получают enriched task → делают более informed решения
5. Результат лучше, чем в первый раз

**Проверь:**
```bash
curl http://localhost:8000/api/knowledge/status
# → executions_count: 2, patterns_count: больше
```

---

## Шаг 5: Повтори для каждого CI-инструмента

Теперь пройди по каждому инструменту, чтобы Hermes обучился на всех:

### 5.1 Competitor Discovery (ci_scout)
```bash
# Через Hermes (Telegram или Web):
"Гермес, найди конкурентов для стоматологии в Москве"
# → ci_scout → список конкурентов → EventBus → raw/executions/
```

### 5.2 Website Audit (ci_auditor)
```bash
"Гермес, сделай полный аудит сайта https://конкурент.рф"
# → ci_auditor → 28 checks (PageSpeed + SEO + Security + Mobile) → EventBus
```

### 5.3 Content Analysis (ci_content)
```bash
"Гермес, проанализируй контент конкурентов"
# → ci_content_improved → trafilatura + BeautifulSoup → EventBus
```

### 5.4 Technical Stack (ci_tech)
```bash
"Гермес, какой тех-стек у конкурентов?"
# → ci_tech_real → HTTP + Wappalyzer-подобный анализ → EventBus
```

### 5.5 Pricing Analysis (ci_pricing)
```bash
"Гермес, какие цены у конкурентов?"
# → ci_pricing → real price scraping → EventBus
```

### 5.6 Reputation Analysis (ci_reputation)
```bash
"Гермес, какие отзывы у конкурентов?"
# → ci_reputation → SerpAPI review search → EventBus
```

### 5.7 Ecosystem Analysis (ci_ecosystem)
```bash
"Гермес, какая цифровая экосистема у конкурентов?"
# → ci_ecosystem → HTML signal detection → EventBus
```

### 5.8 Vacancies Analysis (ci_vacancies)
```bash
"Гермес, какие вакансии у конкурентов?"
# → ci_vacancies → hh.ru API → EventBus
```

### 5.9 Backlink Analysis (ci_backlink)
```bash
"Гермес, какие беклинки у конкурентов?"
# → ci_backlink → Ahrefs API → EventBus
```

### 5.10 Rank Tracking (ci_rank_tracker)
```bash
"Гермес, какие позиции у конкурентов?"
# → ci_rank_tracker → SerpAPI positions → EventBus
```

### 5.11 Financial Analysis (ci_finance)
```bash
"Гермес, какие финансовые показатели?"
# → ci_finance → logic-based estimates → EventBus
```

### 5.12 Deep Analysis (ci_deep_analyzer)
```bash
"Гермес, сделай глубокий анализ сайта"
# → ci_deep_analyzer → BFS crawl + PageSpeed → EventBus
```

### 5.13 Full CI Cycle (все вместе)
```bash
curl -X POST https://iamaim.ru/api/seo/audit \
  -H "Content-Type: application/json" \
  -d '{"url": "https://клиника.рф", "niche": "стоматология", "geo": "Москва", "tier": "full"}'
# → Все 16 агентов → 16 событий → Hermes обучен на всём
```

---

## Шаг 6: Knowledge Loop замкнут

**Проверь финальный статус:**
```bash
curl http://localhost:8000/api/knowledge/status
# → {
#     "executions_count": 15+,
#     "patterns_count": 10+,
#     "rules_count": 3+,
#     "learnings_count": 20+,
#     "loop_health": "active"
#   }
```

**Что это значит:**
- Hermes видел 15+ execution-циклов
- Извлёк 10+ паттернов
- Сформулировал 3+ правила
- Получил 20+ знаний от Teacher
- Knowledge loop активен

**Каждый следующий запуск:**
- Magister запрашивает контекст
- Получает релевантные паттерны и правила
- Subagents работают с учётом прошлого опыта
- Результат улучшается с каждым циклом

---

## Итог: что изменилось

**Было (до Phase 18):**
```
CI Agents ──(execute)──> JSON files ──(лежат мёртвым грузом)
Magisters ──(delegate)──> Subagents ──(без контекста)
Teacher ──(store)──> Qdrant ──(Hermes не видит)
```

**Стало (после Phase 18):**
```
CI Agents ──(execute)──> EventBus ──(publish)──> Hermes
                                                      │
                                                      ├── raw/executions/
                                                      ├── wiki/patterns/ (LLM)
                                                      ├── wiki/learnings/ (Teacher)
                                                      └── decisions/rules/
                                                           │
Magisters ──(query context)──> Hermes ──(return)──> enriched task
     │
     └──(delegate with context)──> Subagents ──> better results
```

Система перестала быть набором разрозненных инструментов. Теперь это единый адаптивный организм, который учится на каждом запуске.
