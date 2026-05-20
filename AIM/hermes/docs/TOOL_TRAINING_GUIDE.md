# Обучение Hermes на CI-инструментах

Каждый запуск CI-инструмента → Hermes запоминает опыт → следующий запуск умнее.

## Как это работает

```
Пользователь: "Гермес, проанализируй конкурентов для стоматологии в Москве"
        ↓
Hermes → run_seo_audit tool → CIOrchestrator.execute_ci_analysis()
        ↓
16 фаз → EventBus.publish(ci.agent.completed) → Hermes vault.ingest_agent_result()
        ↓
POST /api/knowledge/learn → LLM извлекает паттерны → wiki/patterns/
        ↓
Следующий запуск → Magister запрашивает контекст → HermesContextProvider.get_context()
        ↓
Результат умнее: использует паттерны из прошлых запусков
```

## Порядок активации

### Шаг 1: Запусти Hermes
```bash
cd AIM/hermes && uvicorn app.main:app --host 0.0.0.0 --port 8000
```
Проверь: `curl http://localhost:8000/api/knowledge/status`
→ Должен показать: `{"executions_count": 0, "patterns_count": 0}`

### Шаг 2: Первый SEO-аудит
```bash
curl -X POST https://iamaim.ru/api/seo/audit \
  -H "Content-Type: application/json" \
  -d '{"url": "https://твоя-клиника.рф", "niche": "стоматология", "geo": "Москва", "tier": "quick"}'
```
→ Hermes получит событие `ci.execution.completed`
→ Проверь: `curl http://localhost:8000/api/knowledge/status` → `executions_count: 1`

### Шаг 3: Извлеки паттерны (LLM-ingest)
```bash
curl -X POST http://localhost:8000/api/knowledge/learn \
  -H "Content-Type: application/json" \
  -d '{"execution_id": "latest"}'
```
→ Hermes проанализирует результат через LLM и сохранит паттерны в `wiki/patterns/`

### Шаг 4: Второй SEO-аудит (с контекстом)
```bash
curl -X POST https://iamaim.ru/api/seo/audit \
  -H "Content-Type: application/json" \
  -d '{"url": "https://другая-клиника.рф", "niche": "стоматология", "geo": "Москва", "tier": "full"}'
```
→ Magister запросит контекст у Hermes → использует паттерны из прошлого запуска → результат лучше

### Шаг 5: Повтори для каждого инструмента
- `run_content_analysis` — контент-анализ
- `run_ads_report` — отчёт по рекламе
- CI Full Cycle — все 16 фаз

### Шаг 6: Knowledge Loop замкнут
Каждый следующий запуск → система умнее.

---

## 16 CI-инструментов (фазы оркестратора)

### Фаза 1: ci_scout — Competitor Discovery
**Запрос:** "Гермес, запусти поиск конкурентов для стоматологии в Москве"
**Инструмент:** `run_seo_audit` → CIOrchestrator → ci_scout
**Результат:** Список конкурентов с URL, позициями, description
**Чему учится Hermes:** Какие конкуренты релевантны для конкретной ниши и гео

### Фаза 2–3: ci_auditor — Website Audit (2 прохода)
**Запрос:** "Гермес, сделай аудит сайта https://конкурент.рф"
**Инструмент:** CIOrchestrator → ci_auditor (PageSpeed API + httpx + BeautifulSoup)
**Результат:** 28 checks (PageSpeed, SEO, Security, Mobile, Content)
**Чему учится Hermes:** Типичные проблемы сайтов в нише, бенчмарки по скорости

### Фаза 4: ci_reputation — Reputation Analysis
**Запрос:** "Гермес, проверь репутацию клиники X"
**Инструмент:** CIOrchestrator → ci_reputation (SerpAPI + httpx)
**Источники:** Яндекс.Карты, 2ГИС, ПроДокторов, Google Maps
**Чему учится Hermes:** Репутационные паттерны: какие клиники имеют высокий рейтинг и почему

### Фаза 5 (Parallel): 9 агентов одновременно

**ci_finance** — Финансовый анализ
- Оценивает выручку, прибыль, средний чек по сигналам (трафик, цены, вакансии)
- Hermes учится: финансовая модель клиник в разных нишах

**ci_vacancies** — Анализ вакансий
- hh.ru API: количество, зарплаты, категории, рост
- Hermes учится: какие специалисты востребованы, зарплатные бенчмарки

**ci_tech** — Технический анализ (ci_tech_real)
- 50+ страниц, структура URL, технологии, structured data
- Hermes учится: технические паттерны успешных сайтов

**ci_site_crawler** — Обход сайта
- BFS crawl через httpx + BeautifulSoup
- Hermes учится: структура контента, внутренняя перелинковка

**ci_content** — Контент-анализ (ci_content_improved)
- Качество контента, пробелы, E-E-A-T сигналы
- Hermes учится: какие темы покрывают конкуренты, какие пробелы закрывать

**ci_pricing** — Анализ цен
- Парсинг цен с сайтов, российский формат (рубли)
- Hermes учится: ценовые бенчмарки по нишам и гео

**ci_ecosystem** — Экосистема конкурента
- Соцсети, CRM, платёжные системы, мессенджеры
- Hermes учится: какой tech stack используют лидеры рынка

**ci_backlink** — Бэклинки
- Ahrefs/SEMrush API для анализа ссылочного профиля
- Hermes учится: ссылочные стратегии конкурентов

**ci_rank_tracker** — Позиции в поиске
- SerpAPI для отслеживания позиций по ключевым словам
- Hermes учится: какие keywords реально приводят пациентов

### Фаза 6: ci_factchecker — Проверка фактов
**Инструмент:** CIOrchestrator → ci_factchecker
**Результат:** Верификация данных из предыдущих фаз, флаги неточностей
**Чему учится Hermes:** Какие источники надёжны, какие метрики коррелируют

### Фаза 7–8: ci_strategist — Стратегия (2 прохода)
**Инструмент:** CIOrchestrator → ci_strategist
**Результат:** "3 числа" — patients/month, time-to-result, cost-per-patient
**Формулы:** patients = traffic × conversion, cost = CPC / conversion_rate, time = base × niche × competition × budget
**Чему учится Hermes:** Реалистичные прогнозы для разных ниш и бюджетов

### Фаза 9: ci_prioritizer — Приоритизация
**Инструмент:** CIOrchestrator → ci_prioritizer
**Результат:** Приоритизированный список действий (impact × effort × urgency)
**Чему учится Hermes:** Какие действия дают максимальный ROI в конкретной нише

### Фаза 10: ci_marketing_strategy — Маркетинговая стратегия
**Инструмент:** CIOrchestrator → ci_marketing_strategy
**Результат:** Полная маркетинговая стратегия на основе всех данных
**Чему учится Hermes:** Какие стратегии работают в конкретных нишах и гео

### Фазы 11–15: TW-агенты (ThinkWeb)
**tw_competitor_scout, tw_creative_collector, tw_creative_analyzer, tw_pattern_finder, tw_traffic_analyzer**
**Статус:** Специфицированы, ожидают реализации
**Чему будет учиться Hermes:** Креативные и трафиковые паттерны конкурентов

### Фаза 16: ci_offer_generator — Генерация предложения
**Инструмент:** CIOrchestrator → ci_offer_generator
**Результат:** Финальное коммерческое предложение для клиента
**Формат:** "Вы теряете X пациентов/мес → мы приведём Y → через Z месяцев → цена пациента W₽"

---

## Проверка knowledge loop

```bash
# 1. Статус vault
curl http://localhost:8000/api/knowledge/status

# 2. Поиск паттернов
curl "http://localhost:8000/api/knowledge/search?q=стоматология&domain=seo"

# 3. Контекст для magister
curl "http://localhost:8000/api/knowledge/context?domain=seo&action=competitive_analysis"

# 4. Health с knowledge loop
curl http://localhost:8000/health | jq .knowledge_loop

# 5. E2E проверка
python scripts/verify_knowledge_loop.py
```
