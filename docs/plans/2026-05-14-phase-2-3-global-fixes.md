# Phase 2-3: Global Project Fixes

**Дата:** 2026-05-14 10:32 GMT+3  
**Статус:** READY TO EXECUTE  
**Приоритет:** P0

---

## Контекст

После исправления Teacher Agent (Phase 1 ✅), нужно:
1. **Phase 2:** Обучить ВСЕ субагенты правильно (индивидуальный research + GitHub)
2. **Phase 3:** Глобальный аудит проекта на соответствие правилам

**Проблема:** Сейчас субагенты могут иметь:
- Copy-paste generic patterns (Circuit Breaker, Retry, Rate Limiting)
- Отсутствие domain-specific решений
- Неправильное применение кода (до исправления Teacher Agent)

---

## Phase 2: Правильное обучение всех субагентов

### Принцип: Индивидуальный подход к каждому субагенту

**ЗАПРЕЩЕНО:**
- ❌ Copy-paste одинаковых паттернов во все субагенты
- ❌ "Обучение" без deep research для каждого субагента
- ❌ Общие решения для всех
- ❌ Пропускать GitHub search специализированных решений
- ❌ Не анализировать код из найденных репо

**ОБЯЗАТЕЛЬНО:**
- ✅ Для КАЖДОГО субагента: индивидуальное deep research
- ✅ GitHub search с правильными запросами
- ✅ Клонирование и изучение кода из топовых репо
- ✅ Извлечение специфичных для домена паттернов
- ✅ Каждый субагент получает уникальное обучение

### Список субагентов для обучения

**P0 субагенты (критичные для работы):**

1. **Keyword Research Agent** ✅ (уже обучен в Phase 1)
   - Domain: keyword research automation python
   - GitHub: semrush api, ahrefs api, keyword research tools
   - Status: DONE (context-aware code applied)

2. **Competitor Content Analyzer**
   - Domain: content analysis, competitor research, SEO analysis
   - GitHub: "python seo analyzer", "content scraper python", "competitor analysis tool"
   - Специфика: Trafilatura, BeautifulSoup, AI content detection

3. **Technical SEO Auditor**
   - Domain: technical SEO, site audit, performance analysis
   - GitHub: "lighthouse python", "technical seo audit", "site crawler python"
   - Специфика: Lighthouse, Screaming Frog patterns, Core Web Vitals

4. **Content Gap Analyzer**
   - Domain: content gap analysis, SERP analysis, topic clustering
   - GitHub: "serp analysis python", "content gap tool", "topic clustering"
   - Специфика: SERP overlap, keyword clustering, content scoring

5. **Backlink Analyzer**
   - Domain: backlink analysis, link building, domain authority
   - GitHub: "backlink checker python", "moz api python", "ahrefs backlinks"
   - Специфика: Moz API, Ahrefs backlinks, link quality scoring

6. **Rank Tracker**
   - Domain: rank tracking, SERP monitoring, position tracking
   - GitHub: "serp tracker python", "rank monitoring tool", "google search api"
   - Специфика: SerpAPI, DataForSEO, position tracking patterns

7. **Yandex Direct API Client** (Ads субагент)
   - Domain: Yandex Direct API v5, campaign management, bidding
   - GitHub: "yandex direct api python", "yandex ads mcp"
   - Специфика: OAuth 2.0, rate limits (10 req/s), medical advertising compliance
   - Repo: https://github.com/Yurich-ru/yandex-ads-mcp

### Workflow для каждого субагента

```
1. Deep Research (если нет актуального)
   ├─ Запрос: "[domain] python best practices"
   ├─ Режим: standard (6 фаз, 5-10 минут)
   └─ Результат: ~/Documents/[Topic]_Research_[YYYYMMDD]/

2. GitHub Search (обязательно)
   ├─ Запросы: 3-4 специфичных запроса для домена
   ├─ Клонирование: ВСЕ топовые репо (stars > 50)
   └─ Изучение: Читать КОД, не README

3. Teacher Agent (context-aware)
   ├─ teacher.teach_subagent(subagent_name, domain)
   ├─ Автоматически: research → clone → extract → compare → apply
   └─ Результат: Правильный код в нужном месте

4. Проверка
   ├─ Код async-compatible?
   ├─ Использует правильные библиотеки?
   ├─ Domain-specific паттерны применены?
   └─ Тесты проходят?

5. Коммит
   └─ teach([subagent]): apply [skill] from [repo]
```

### Оценка времени Phase 2

**На один субагент:**
- Deep research: 5-10 минут (если нужен)
- GitHub search + clone: 2-3 минуты
- Teacher Agent: 5-10 минут
- Проверка + коммит: 2-3 минуты
- **Итого:** 15-25 минут на субагента

**Всего (6 субагентов):**
- Оптимистичный: 1.5 часа
- Реалистичный: 2-2.5 часа
- Пессимистичный: 3 часа

---

## Phase 3: Глобальный аудит проекта

### Цель: Проверить соответствие всем правилам и обсуждениям

**Что проверяем:**

1. **Architecture Compliance**
   - Соответствие трёхслойной архитектуре (Architect → Operator → Agents)
   - Правильная иерархия Magisters → Subagents
   - Event Bus для коммуникации
   - Obsidian vaults по LLM Wiki паттерну

2. **Code Quality**
   - Все субагенты имеют domain-specific код (не generic patterns)
   - Async/sync compatibility соблюдена
   - Правильные библиотеки используются
   - Error handling правильный (raise, не sys.exit)

3. **Documentation**
   - Все спецификации актуальны
   - CLAUDE.md отражает текущее состояние
   - SESSION.md обновлён
   - Планы в docs/plans/ актуальны

4. **Testing**
   - Тесты существуют для критичных компонентов
   - Тесты проходят
   - Coverage достаточный

5. **Memory System**
   - Obsidian vaults следуют LLM Wiki паттерну
   - raw/ → wiki/ → decisions/ структура соблюдена
   - Deep research архивируется в obsidian/deep-research/

### Workflow Phase 3

```
1. Architecture Audit
   ├─ Проверить структуру директорий
   ├─ Проверить импорты (framework vs application)
   ├─ Проверить Event Bus usage
   └─ Проверить Obsidian vaults structure

2. Code Audit
   ├─ Для каждого субагента:
   │  ├─ Есть domain-specific код?
   │  ├─ Async/sync правильно?
   │  ├─ Библиотеки правильные?
   │  └─ Error handling правильный?
   └─ Список проблем → исправить

3. Documentation Audit
   ├─ CLAUDE.md актуален?
   ├─ Спецификации актуальны?
   ├─ SESSION.md обновлён?
   └─ Планы актуальны?

4. Testing Audit
   ├─ Какие тесты есть?
   ├─ Какие тесты проходят?
   ├─ Что не покрыто?
   └─ Добавить критичные тесты

5. Memory Audit
   ├─ Vaults следуют LLM Wiki?
   ├─ Deep research архивирован?
   ├─ Операции логируются?
   └─ Исправить несоответствия
```

### Оценка времени Phase 3

- Architecture Audit: 30 минут
- Code Audit: 1 час
- Documentation Audit: 30 минут
- Testing Audit: 30 минут
- Memory Audit: 30 минут
- Исправления: 1-2 часа
- **Итого:** 3-4 часа

---

## Общая оценка времени

**Phase 2:** 2-2.5 часа  
**Phase 3:** 3-4 часа  
**Итого:** 5-6.5 часов

---

## Критерий успеха

**Phase 2 (Обучение субагентов):**
- ✅ Все 6 P0 субагентов обучены индивидуально
- ✅ Каждый имеет domain-specific код (не generic patterns)
- ✅ Код async-compatible и использует правильные библиотеки
- ✅ GitHub repos изучены и лучшие паттерны применены

**Phase 3 (Глобальный аудит):**
- ✅ Архитектура соответствует трёхслойной модели
- ✅ Код качественный и domain-specific
- ✅ Документация актуальна
- ✅ Тесты покрывают критичные компоненты
- ✅ Memory system следует LLM Wiki паттерну

**Финальный результат:**
- ✅ Проект полностью соответствует всем правилам и обсуждениям
- ✅ Teacher Agent работает правильно
- ✅ Все субагенты обучены индивидуально
- ✅ Система готова к production использованию

---

**Автор:** Claude Sonnet 4  
**Дата:** 2026-05-14 10:32 GMT+3  
**Статус:** READY TO EXECUTE
