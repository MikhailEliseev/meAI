# Content Gap Analysis Agent - Спецификация

**Дата:** 2026-05-12  
**Magister:** SEO Magister  
**Приоритет:** P0  
**Статус:** Draft

---

## 🎯 РОЛЬ И НАЗНАЧЕНИЕ

### Основная роль:
Анализирует контент конкурентов для выявления пробелов (gaps) и возможностей создания нового контента. Находит темы, которые есть у конкурентов, но отсутствуют у клиента, и приоритизирует их по потенциалу трафика и конверсий.

### Что делает:
- ✅ Собирает и анализирует контент конкурентов (web scraping + API)
- ✅ Кластеризует контент по темам и подтемам (topic clustering)
- ✅ Выявляет gaps между контентом клиента и конкурентов
- ✅ Оценивает качество контента (E-E-A-T для медицинского контента)
- ✅ Приоритизирует gaps по opportunity score (трафик × качество / сложность)
- ✅ Генерирует рекомендации по созданию контента

### Что НЕ делает:
- ❌ Не создаёт контент (это задача Content Magister)
- ❌ Не анализирует keywords (это задача Keyword Research Agent)
- ❌ Не проверяет compliance (это задача Compliance Checker)
- ❌ Не оптимизирует существующий контент (это задача Content Optimizer)

### Место в иерархии:
```
SEO Magister
    ↓
SEO Orchestrator
    ↓
Content Gap Analysis Agent ← вы здесь
```

---

## 📥 ВХОДНЫЕ ДАННЫЕ

### Получает от Orchestrator:

**Формат события:**
```json
{
  "event_type": "subagent.task.assigned",
  "correlation_id": "uuid",
  "task_id": "uuid",
  "subagent_id": "content-gap-analysis-agent",
  "payload": {
    "client_url": "https://example-clinic.com",
    "competitor_urls": [
      "https://competitor1.com",
      "https://competitor2.com",
      "https://competitor3.com"
    ],
    "niche": "dental implants",
    "analysis_depth": "deep",
    "max_pages_per_site": 50,
    "max_cost_usd": 1.0
  }
}
```

**Обязательные параметры:**
- `client_url` (string) - URL сайта клиента для анализа существующего контента
- `competitor_urls` (array[string]) - Список URL конкурентов (3-10 сайтов)
- `niche` (string) - Целевая ниша/тематика (например, "dental implants", "cosmetic dentistry")

**Опциональные параметры:**
- `analysis_depth` (string) - Глубина анализа: "quick" (10 pages), "standard" (30 pages), "deep" (50+ pages). Default: "standard"
- `max_pages_per_site` (int) - Максимум страниц для анализа на каждом сайте. Default: 30
- `max_cost_usd` (float) - Максимальный бюджет на API calls. Default: 1.0
- `min_content_quality` (float) - Минимальное качество контента для анализа (0.0-1.0). Default: 0.5
- `include_keywords` (array[string]) - Список keywords для фокусировки анализа (интеграция с Keyword Research Agent)

---

## 📤 ВЫХОДНЫЕ ДАННЫЕ

### Отправляет Orchestrator:

**Формат события:**
```json
{
  "event_type": "subagent.task.completed",
  "correlation_id": "uuid",
  "task_id": "uuid",
  "subagent_id": "content-gap-analysis-agent",
  "payload": {
    "status": "success",
    "result": {
      "gaps": [
        {
          "topic": "All-on-4 dental implants recovery time",
          "gap_type": "missing_topic",
          "opportunity_score": 85.5,
          "priority": "P0",
          "competitor_coverage": {
            "competitor1.com": {
              "url": "https://competitor1.com/all-on-4-recovery",
              "quality_score": 0.92,
              "traffic_estimate": 1200,
              "word_count": 2500
            }
          },
          "recommended_actions": [
            "Create comprehensive guide (2000+ words)",
            "Include doctor author credentials",
            "Add patient testimonials",
            "Cite medical studies"
          ]
        }
      ],
      "topic_clusters": [
        {
          "cluster_name": "Dental Implants Procedures",
          "topics": ["All-on-4", "Single tooth implant", "Full arch"],
          "client_coverage": 2,
          "competitor_coverage": 5,
          "gap_count": 3
        }
      ],
      "content_quality_comparison": {
        "client": {
          "avg_word_count": 800,
          "avg_eeat_score": 0.65,
          "doctor_authored_pct": 0.4
        },
        "competitors_avg": {
          "avg_word_count": 1500,
          "avg_eeat_score": 0.82,
          "doctor_authored_pct": 0.75
        }
      },
      "summary": {
        "total_gaps_found": 15,
        "p0_gaps": 5,
        "p1_gaps": 7,
        "p2_gaps": 3,
        "total_pages_analyzed": 180,
        "total_cost_usd": 0.85
      }
    },
    "metrics": {
      "execution_time_ms": 480000,
      "pages_scraped": 180,
      "api_calls": 12,
      "gaps_detected": 15,
      "clusters_created": 8
    },
    "errors": []
  }
}
```

**Структура результата:**
- `gaps` (array) - Список выявленных content gaps с приоритетами
- `topic_clusters` (array) - Кластеры тем с покрытием клиента vs конкурентов
- `content_quality_comparison` (object) - Сравнение качества контента
- `summary` (object) - Сводка по анализу

**Метрики:**
- `execution_time_ms` - Время выполнения в миллисекундах (~8 минут для deep analysis)
- `pages_scraped` - Количество проанализированных страниц
- `api_calls` - Количество API вызовов (Ahrefs, GSC)
- `gaps_detected` - Количество найденных gaps
- `clusters_created` - Количество созданных topic clusters

---

## 🔄 АЛГОРИТМ РАБОТЫ

### Шаг 1: Получение задачи и валидация
1. Подписаться на события `subagent.task.assigned`
2. Фильтровать по `subagent_id == "content-gap-analysis-agent"`
3. Валидировать входные параметры:
   - `client_url` - валидный URL, доступен
   - `competitor_urls` - 3-10 URL, все доступны
   - `max_cost_usd` - положительное число
4. Проверить бюджет: если `max_cost_usd < 0.10` → вернуть warning

### Шаг 2: Сбор контента клиента
1. **Crawl client site** (custom scraping):
   - Начать с `client_url`, следовать internal links
   - Ограничение: `max_pages_per_site` страниц
   - Извлечь: title, meta description, H1-H6, body text, word count
   - Определить author credentials (врач/не врач)
   - Извлечь medical citations (PubMed links, journal references)
2. **Parse content structure**:
   - Определить content type (blog post, service page, FAQ, etc.)
   - Извлечь topics из H1-H3
   - Рассчитать readability score (Flesch-Kincaid)
3. **Calculate E-E-A-T score** для каждой страницы:
   - Experience: author credentials (0.3 weight)
   - Expertise: medical citations (0.3 weight)
   - Authoritativeness: domain authority, backlinks (0.2 weight)
   - Trustworthiness: HTTPS, contact info, privacy policy (0.2 weight)
4. **Store in database**: client_pages table

### Шаг 3: Сбор контента конкурентов
1. **Для каждого competitor_url**:
   - Crawl site (аналогично Шагу 2)
   - Ограничение: `max_pages_per_site` страниц
   - Извлечь те же данные
   - Рассчитать E-E-A-T score
2. **Fallback to Ahrefs API** (если budget позволяет):
   - Endpoint: `/v3/site-explorer/top-pages`
   - Получить top pages по organic traffic
   - Стоимость: $0.05-0.10 per request
   - Обогатить данные: traffic estimate, backlinks, keywords
3. **Store in database**: competitor_pages table

### Шаг 4: Topic Clustering
1. **Extract topics** из всех страниц (client + competitors):
   - Использовать H1-H3 как primary topics
   - Извлечь keywords из title и meta description
2. **Generate embeddings** (Sentence-BERT):
   - Model: `all-MiniLM-L6-v2` (fast, good quality)
   - Embed каждую страницу (title + H1 + first 200 words)
3. **Cluster topics** (BERTopic):
   - Algorithm: HDBSCAN для автоматического определения количества кластеров
   - Min cluster size: 3 pages
   - Получить cluster labels и representative docs
4. **Build topic hierarchy**:
   - Parent topics (кластеры)
   - Subtopics (страницы внутри кластеров)
5. **Store in database**: topic_clusters table


### Шаг 5: Gap Detection
1. **Identify missing topics** (URL-based gaps):
   - Для каждого topic cluster:
     - Подсчитать client coverage (сколько страниц у клиента)
     - Подсчитать competitor coverage (сколько страниц у конкурентов)
     - Если competitor_coverage > client_coverage → gap detected
2. **Calculate gap severity**:
   - Missing topic (0 pages у клиента) → HIGH severity
   - Underrepresented topic (1-2 pages vs 5+ у конкурентов) → MEDIUM severity
   - Comparable coverage → LOW severity (не gap)
3. **Filter by quality**:
   - Учитывать только competitor pages с E-E-A-T score > `min_content_quality`
   - Исключить low-quality gaps (competitor content плохого качества)
4. **Store in database**: content_gaps table

### Шаг 6: Opportunity Scoring
1. **Для каждого gap рассчитать opportunity_score**:
   ```python
   opportunity_score = (
       competitor_avg_traffic * 0.4 +
       competitor_avg_quality * 0.3 +
       topic_relevance_to_niche * 0.2 +
       keyword_search_volume * 0.1
   ) / (
       content_difficulty * 0.6 +
       existing_client_coverage * 0.4
   )
   ```
   - Normalize to 0-100 scale
2. **Assign priority tier**:
   - P0 (High Priority): score >= 80
   - P1 (Medium Priority): score 60-79
   - P2 (Low Priority): score 40-59
   - P3 (Very Low Priority): score < 40
3. **Generate recommendations** для каждого gap:
   - Recommended word count (based on competitor avg)
   - Content type (blog post, service page, FAQ)
   - Required elements (doctor author, citations, testimonials)
   - Target keywords (from Keyword Research Agent if available)

### Шаг 7: Quality Comparison
1. **Aggregate client metrics**:
   - Average word count
   - Average E-E-A-T score
   - Doctor-authored percentage
   - Medical citations per page
2. **Aggregate competitor metrics** (same metrics)
3. **Calculate gaps in quality**:
   - Word count gap: competitor_avg - client_avg
   - E-E-A-T gap: competitor_avg - client_avg
   - Doctor authorship gap: competitor_pct - client_pct

### Шаг 8: Формирование результата
1. Собрать все gaps с приоритетами
2. Собрать topic clusters с coverage
3. Собрать quality comparison
4. Рассчитать summary metrics
5. Сформировать событие результата

### Шаг 9: Сохранение и отправка
1. **Сохранить в Obsidian vault**:
   - `wiki/reports/content-gap-analysis/YYYYMMDD_HHMMSS_[niche].md`
   - Markdown report с таблицами gaps
2. **Отправить событие** `subagent.task.completed`
3. **Логировать в Event Store**
4. **Обновить метрики** в database

---

## 🔧 ИНТЕГРАЦИИ

### Внешние сервисы:

**Ahrefs Content Explorer API:**
- API endpoint: `https://api.ahrefs.com/v3/site-explorer/top-pages`
- Аутентификация: API key в header `Authorization: Bearer {token}`
- Rate limit: 60 requests/minute
- Стоимость: $0.05-0.10 per request (50 units minimum)
- Документация: https://ahrefs.com/api/documentation
- **Использование:** Fallback для получения traffic estimates и backlinks
- **Когда использовать:** Если budget позволяет И нужны точные traffic данные

**Google Search Console API:**
- API endpoint: `https://www.googleapis.com/webmasters/v3/sites/{siteUrl}/searchAnalytics/query`
- Аутентификация: OAuth 2.0
- Rate limit: 200 requests/day
- Стоимость: Free
- Документация: https://developers.google.com/webmaster-tools/search-console-api-original
- **Использование:** Получить данные о своём сайте (позиции, CTR, impressions)
- **Когда использовать:** Для анализа client_url (если доступ предоставлен)

**Google Trends API:**
- API endpoint: `https://trends.google.com/trends/api/explore`
- Аутентификация: None (public API)
- Rate limit: ~100 requests/hour (unofficial)
- Стоимость: Free
- Документация: Unofficial (pytrends library)
- **Использование:** Определить trending topics в нише
- **Когда использовать:** Для приоритизации gaps по актуальности

**Custom Web Scraping:**
- Library: BeautifulSoup4 + Playwright (для JS-heavy сайтов)
- Rate limiting: 1-2 requests/second per domain
- Proxy: Residential proxies (optional, $10-50/month)
- Robots.txt: Обязательно соблюдать
- **Использование:** PRIMARY метод для сбора контента
- **Когда использовать:** Всегда (основной источник данных)

### Внутренние зависимости:

**Обязательные:**
- Event Bus - для получения задач и отправки результатов
- Event Store - для логирования всех операций
- Obsidian vault - для сохранения отчётов
- Database (SQLite) - для хранения pages, clusters, gaps

**Опциональные:**
- Keyword Research Agent - для обогащения gaps keywords
- Compliance Checker - для проверки medical content compliance

---

## 📊 МЕТРИКИ УСПЕХА

### Качественные метрики:

**Точность gap detection:**
- Метрика: Precision (релевантные gaps / все найденные gaps)
- Целевое значение: > 90%
- Как измерять: Manual review выборки из 20 gaps, подсчёт false positives

**Полнота gap detection:**
- Метрика: Recall (найденные gaps / все существующие gaps)
- Целевое значение: > 85%
- Как измерять: Manual review competitor content, подсчёт missed gaps

**Качество приоритизации:**
- Метрика: P0 gaps действительно high-value (manual review)
- Целевое значение: > 80% P0 gaps приводят к созданию контента
- Как измерять: Tracking созданного контента по рекомендациям

**Качество кластеризации:**
- Метрика: Silhouette score (качество кластеров)
- Целевое значение: > 0.5
- Как измерять: Автоматически при кластеризации

### Производительность:

**Скорость:**
- Quick analysis (10 pages/site): < 2 минуты
- Standard analysis (30 pages/site): < 5 минут
- Deep analysis (50+ pages/site): < 10 минут
- 95-й перцентиль: < 12 минут
- Максимальное время: < 15 минут

**Надёжность:**
- Success rate: > 95% (все gaps найдены, отчёт сгенерирован)
- Partial success rate: > 99% (часть gaps найдена, отчёт частичный)
- Failure rate: < 1% (полный сбой, нет результата)

**Стоимость:**
- Средняя стоимость анализа: < $1.00
- 95-й перцентиль: < $1.50
- Максимальная стоимость: $5.00 (budget guard)

### Бизнес-метрики:

**Влияние на контент-стратегию:**
- Процент созданного контента по рекомендациям: > 60%
- Процент P0 gaps, закрытых контентом: > 80%
- Среднее время от gap detection до публикации: < 30 дней

**Влияние на трафик:**
- Прирост organic traffic после закрытия gaps: > 20% за 6 месяцев
- Процент нового контента в top 10 SERP: > 40%

---

## 🧪 ПРИМЕРЫ ИСПОЛЬЗОВАНИЯ

### Пример 1: Успешное выполнение (Standard Analysis)

**Входные данные:**
```json
{
  "client_url": "https://smile-dental.com",
  "competitor_urls": [
    "https://competitor1-dental.com",
    "https://competitor2-dental.com",
    "https://competitor3-dental.com"
  ],
  "niche": "dental implants",
  "analysis_depth": "standard",
  "max_pages_per_site": 30,
  "max_cost_usd": 1.0
}
```

**Выходные данные:**
```json
{
  "status": "success",
  "result": {
    "gaps": [
      {
        "topic": "All-on-4 dental implants recovery time",
        "gap_type": "missing_topic",
        "opportunity_score": 85.5,
        "priority": "P0",
        "competitor_coverage": {
          "competitor1-dental.com": {
            "url": "https://competitor1-dental.com/all-on-4-recovery",
            "quality_score": 0.92,
            "traffic_estimate": 1200,
            "word_count": 2500,
            "doctor_authored": true,
            "medical_citations": 8
          },
          "competitor2-dental.com": {
            "url": "https://competitor2-dental.com/recovery-guide",
            "quality_score": 0.88,
            "traffic_estimate": 800,
            "word_count": 2000,
            "doctor_authored": true,
            "medical_citations": 5
          }
        },
        "recommended_actions": [
          "Create comprehensive guide (2000+ words)",
          "Include doctor author credentials (DDS/DMD)",
          "Add patient testimonials with photos",
          "Cite medical studies (PubMed)",
          "Include recovery timeline infographic"
        ],
        "target_keywords": [
          "all on 4 recovery time",
          "all on 4 healing process",
          "dental implant recovery"
        ]
      }
    ],
    "topic_clusters": [
      {
        "cluster_name": "Dental Implants Procedures",
        "topics": [
          "All-on-4",
          "Single tooth implant",
          "Full arch implants",
          "Mini implants"
        ],
        "client_coverage": 2,
        "competitor_coverage": 8,
        "gap_count": 6
      }
    ],
    "content_quality_comparison": {
      "client": {
        "avg_word_count": 800,
        "avg_eeat_score": 0.65,
        "doctor_authored_pct": 0.4,
        "medical_citations_per_page": 2.1
      },
      "competitors_avg": {
        "avg_word_count": 1500,
        "avg_eeat_score": 0.82,
        "doctor_authored_pct": 0.75,
        "medical_citations_per_page": 5.3
      }
    },
    "summary": {
      "total_gaps_found": 15,
      "p0_gaps": 5,
      "p1_gaps": 7,
      "p2_gaps": 3,
      "total_pages_analyzed": 120,
      "total_cost_usd": 0.45
    }
  },
  "metrics": {
    "execution_time_ms": 280000,
    "pages_scraped": 120,
    "api_calls": 3,
    "gaps_detected": 15,
    "clusters_created": 6
  },
  "errors": []
}
```

### Пример 2: Частичный успех (Scraping Failures)

**Входные данные:**
```json
{
  "client_url": "https://smile-dental.com",
  "competitor_urls": [
    "https://competitor1-dental.com",
    "https://competitor2-dental.com",
    "https://competitor3-dental.com"
  ],
  "niche": "dental implants",
  "analysis_depth": "deep",
  "max_pages_per_site": 50
}
```

**Выходные данные:**
```json
{
  "status": "partial_success",
  "result": {
    "gaps": [
      {
        "topic": "All-on-4 dental implants recovery time",
        "opportunity_score": 85.5,
        "priority": "P0"
      }
    ],
    "summary": {
      "total_gaps_found": 12,
      "p0_gaps": 4,
      "total_pages_analyzed": 95,
      "total_cost_usd": 0.30
    }
  },
  "metrics": {
    "execution_time_ms": 420000,
    "pages_scraped": 95,
    "api_calls": 2,
    "gaps_detected": 12,
    "clusters_created": 5
  },
  "errors": [
    {
      "code": "SCRAPING_FAILED",
      "message": "Failed to scrape competitor3-dental.com (blocked by Cloudflare)",
      "details": {
        "url": "https://competitor3-dental.com",
        "pages_scraped": 0,
        "pages_expected": 50
      }
    }
  ]
}
```

### Пример 3: Ошибка (Invalid Input)

**Входные данные:**
```json
{
  "client_url": "invalid-url",
  "competitor_urls": [],
  "niche": ""
}
```

**Выходные данные:**
```json
{
  "status": "failure",
  "result": null,
  "metrics": {
    "execution_time_ms": 100,
    "pages_scraped": 0,
    "api_calls": 0,
    "gaps_detected": 0,
    "clusters_created": 0
  },
  "errors": [
    {
      "code": "INVALID_INPUT",
      "message": "Invalid client_url: must be valid HTTP/HTTPS URL",
      "details": {
        "param": "client_url",
        "value": "invalid-url"
      }
    },
    {
      "code": "INVALID_INPUT",
      "message": "competitor_urls must contain 3-10 URLs",
      "details": {
        "param": "competitor_urls",
        "value": []
      }
    },
    {
      "code": "INVALID_INPUT",
      "message": "niche cannot be empty",
      "details": {
        "param": "niche",
        "value": ""
      }
    }
  ]
}
```

---

## 🔒 ОБРАБОТКА ОШИБОК

### Типы ошибок:

**Валидация входных данных:**
- Код: `INVALID_INPUT`
- Причины: Invalid URL, empty competitor_urls, negative max_cost_usd
- Действие: Вернуть failure сразу, не начинать анализ
- Retry: Нет (требуется исправление входных данных)

**Ошибка web scraping:**
- Код: `SCRAPING_FAILED`
- Причины: Blocked by Cloudflare, timeout, 404, robots.txt disallow
- Действие: Пропустить проблемный сайт, продолжить с остальными
- Retry: 3 попытки с exponential backoff (1s, 2s, 4s)
- Graceful degradation: Вернуть partial_success с обработанными сайтами

**Ошибка внешнего API (Ahrefs, GSC):**
- Код: `EXTERNAL_API_ERROR`
- Причины: Rate limit exceeded, invalid API key, timeout
- Действие: Fallback to scraping-only mode (без API enrichment)
- Retry: 2 попытки с exponential backoff (2s, 4s)
- Graceful degradation: Продолжить без traffic estimates

**Timeout:**
- Код: `TIMEOUT`
- Причины: Анализ превысил 15 минут
- Действие: Вернуть partial_success с обработанными данными
- Retry: Нет (требуется уменьшение max_pages_per_site)

**Clustering failure:**
- Код: `CLUSTERING_FAILED`
- Причины: Недостаточно данных для кластеризации (< 10 pages)
- Действие: Вернуть gaps без кластеров (flat list)
- Retry: Нет
- Graceful degradation: Gap detection работает без кластеризации

**Budget exceeded:**
- Код: `BUDGET_EXCEEDED`
- Причины: API calls превысили max_cost_usd
- Действие: Остановить API calls, продолжить scraping
- Retry: Нет
- Graceful degradation: Вернуть результат без API enrichment

**Internal error:**
- Код: `INTERNAL_ERROR`
- Причины: Unhandled exception, database error
- Действие: Логировать stack trace, вернуть failure
- Retry: Нет (требуется fix в коде)

### Graceful degradation:

При частичном сбое:
1. Обработать максимум данных (все доступные сайты)
2. Вернуть partial_success с тем, что удалось собрать
3. Указать в errors, что именно не удалось обработать
4. Позволить Orchestrator решить: retry или использовать partial результат

### Retry strategy:

**Web scraping:**
- Max retries: 3
- Backoff: Exponential (1s, 2s, 4s)
- Retry on: Timeout, 5xx errors, connection errors
- No retry on: 4xx errors (кроме 429), robots.txt disallow

**API calls:**
- Max retries: 2
- Backoff: Exponential (2s, 4s)
- Retry on: 429 (rate limit), 5xx errors, timeout
- No retry on: 401 (invalid key), 403 (forbidden), 4xx (bad request)

---

## 🧠 ОБУЧЕНИЕ И АДАПТАЦИЯ

### Источники обучения:

**От SEO Magister:**
- Best practices по content gap analysis
- Актуальные E-E-A-T требования Google
- Обновления алгоритмов кластеризации
- Новые источники данных (API, tools)

**Из собственного опыта:**
- Успешные кейсы: какие gaps привели к росту трафика
- Неудачные попытки: какие gaps не сработали (low traffic, low conversions)
- Метрики результатов: correlation между opportunity_score и actual traffic
- Паттерны: какие типы gaps чаще всего приводят к успеху

**Из Obsidian vault:**
- Исторические данные по анализам
- Паттерны успешных gaps (по нишам)
- Корреляции: opportunity_score vs actual traffic
- Feedback от Content Magister: какие рекомендации были полезны

### Адаптация:

**Когда адаптироваться:**
- Метрики падают ниже целевых (precision < 90%, recall < 85%)
- Появляются новые E-E-A-T требования от Google
- Изменяются алгоритмы кластеризации (новые модели)
- Feedback от Content Magister: рекомендации не работают

**Как адаптироваться:**
1. Получить обновлённые знания от SEO Magister
2. Протестировать на небольшой выборке (5 сайтов)
3. Сравнить метрики до/после (precision, recall, opportunity_score accuracy)
4. Применить, если улучшение подтверждено (> 5% improvement)
5. Сохранить в Obsidian vault для будущих анализов

**Примеры адаптации:**
- Обновление E-E-A-T weights (если Google изменил требования)
- Добавление новых SERP features в opportunity_score
- Изменение clustering algorithm (если BERTopic даёт плохие результаты)
- Корректировка opportunity_score formula (на основе actual traffic data)

---

## 📝 ЛОГИРОВАНИЕ

### Что логировать:

**В Event Store (обязательно):**
- Все входящие события `subagent.task.assigned`
- Все исходящие события `subagent.task.completed`
- Correlation ID для трейсинга
- Timestamp каждого события

**В Obsidian vault (обязательно):**
- Результаты выполнения: `wiki/reports/content-gap-analysis/YYYYMMDD_HHMMSS_[niche].md`
- Метрики производительности: execution_time, pages_scraped, api_calls
- Инсайты и паттерны: успешные gaps, неудачные gaps
- Feedback от Content Magister: какие рекомендации сработали

**В системные логи (опционально):**
- Debug информация: scraping progress, clustering steps
- Ошибки и warnings: scraping failures, API errors
- Performance traces: time per step, bottlenecks

### Формат логов:

```
[2026-05-12 09:15:23] [INFO] [content-gap-analysis-agent] [correlation_id] Started analysis for niche: dental implants
[2026-05-12 09:15:45] [DEBUG] [content-gap-analysis-agent] [correlation_id] Scraped 30 pages from client site
[2026-05-12 09:16:12] [WARNING] [content-gap-analysis-agent] [correlation_id] Failed to scrape competitor3.com (Cloudflare block)
[2026-05-12 09:18:34] [INFO] [content-gap-analysis-agent] [correlation_id] Detected 15 gaps, 5 P0, 7 P1, 3 P2
[2026-05-12 09:18:35] [INFO] [content-gap-analysis-agent] [correlation_id] Completed analysis in 4.2 minutes
```

---

## 🧪 ТЕСТИРОВАНИЕ

### Unit тесты:

**Покрытие:** > 80%

**Обязательные тесты:**
- Валидация входных данных (valid/invalid URLs, empty arrays, negative numbers)
- Web scraping (HTML parsing, content extraction, robots.txt compliance)
- E-E-A-T scoring (author detection, citation extraction, score calculation)
- Topic clustering (embedding generation, clustering algorithm, hierarchy building)
- Gap detection (missing topics, underrepresented topics, quality filtering)
- Opportunity scoring (formula calculation, priority assignment, normalization)
- Error handling (scraping failures, API errors, timeouts, budget exceeded)

### Integration тесты:

**Обязательные сценарии:**
- Получение задачи от Orchestrator (Event Bus)
- Отправка результата Orchestrator (Event Bus)
- Логирование в Event Store
- Сохранение в Obsidian vault
- API integration (Ahrefs, GSC, Google Trends)
- Database operations (insert, update, query)

### E2E тесты:

**Обязательные сценарии:**
- Полный цикл: задача → scraping → clustering → gap detection → результат
- Graceful degradation: scraping failure → partial_success
- Budget guard: API calls stop at max_cost_usd
- Timeout handling: return partial_success after 15 minutes

### Performance тесты:

**Обязательные сценарии:**
- Quick analysis (10 pages/site): < 2 minutes
- Standard analysis (30 pages/site): < 5 minutes
- Deep analysis (50 pages/site): < 10 minutes
- Memory usage: < 500 MB
- Database size: < 100 MB per analysis

---

## 🚀 DEPLOYMENT

### Требования:

**Окружение:**
- Python 3.11+
- Event Bus доступен
- Event Store доступен
- Obsidian vault доступен
- Database (SQLite) доступен

**Зависимости:**
- `httpx >= 0.27.0` - HTTP client для scraping
- `beautifulsoup4 >= 4.12.0` - HTML parsing
- `playwright >= 1.40.0` - Headless browser для JS-heavy сайтов
- `sentence-transformers >= 2.2.0` - Sentence-BERT embeddings
- `bertopic >= 0.16.0` - Topic modeling
- `scikit-learn >= 1.3.0` - Clustering algorithms
- `aiohttp >= 3.9.0` - Async HTTP для API calls
- `pydantic >= 2.5.0` - Data validation
- `sqlalchemy >= 2.0.0` - Database ORM
- `textstat >= 0.7.0` - Readability metrics

**Конфигурация:**
```env
SUBAGENT_ID=content-gap-analysis-agent
EVENT_BUS_URL=sqlite:///./data/event_bus.db
EVENT_STORE_URL=sqlite:///./data/event_store.db
OBSIDIAN_VAULT_PATH=./AIM/obsidian/seo-magister
DATABASE_URL=sqlite+aiosqlite:///./AIM/data/content_gap_analysis.db

# API Keys (optional)
AHREFS_API_KEY=your_ahrefs_key_here
GOOGLE_SEARCH_CONSOLE_CREDENTIALS=path/to/credentials.json

# Scraping Config
MAX_PAGES_PER_SITE=30
SCRAPING_RATE_LIMIT=2.0
SCRAPING_TIMEOUT=30
USER_AGENT=Mozilla/5.0 (compatible; ContentGapBot/1.0)

# Clustering Config
EMBEDDING_MODEL=all-MiniLM-L6-v2
MIN_CLUSTER_SIZE=3
MIN_CONTENT_QUALITY=0.5

# Budget Control
MAX_COST_USD=1.0
AHREFS_COST_PER_REQUEST=0.075
```

### Мониторинг:

**Метрики для алертов:**
- Success rate < 95% → Warning
- Success rate < 90% → Critical
- Avg execution time > 10 minutes → Warning
- 95th percentile > 12 minutes → Critical
- Gap detection precision < 90% → Warning
- Gap detection recall < 85% → Warning
- Scraping failure rate > 10% → Warning
- API error rate > 5% → Warning

**Dashboards:**
- Execution time distribution (histogram)
- Success/partial_success/failure rate (pie chart)
- Gaps detected per analysis (time series)
- Cost per analysis (time series)
- Scraping success rate by domain (bar chart)
- API usage and cost (time series)

---

## 📚 СВЯЗАННЫЕ ДОКУМЕНТЫ

### Спецификации:
- `SEO_MAGISTER_SPEC.md` - Спецификация родительского SEO Magister
- `SEO_ORCHESTRATOR_SPEC.md` - Спецификация родительского SEO Orchestrator
- `KEYWORD_RESEARCH_AGENT_SPEC.md` - Спецификация Keyword Research Agent (интеграция)
- `COMPLIANCE_CHECKER_SPEC.md` - Спецификация Compliance Checker (интеграция)

### Код:
- `AIM/src/aim/subagents/seo/content_gap_analysis_agent.py` - Реализация
- `AIM/tests/subagents/seo/test_content_gap_analysis_agent.py` - Тесты

### Документация:
- Event Bus API
- Event Store API
- Obsidian integration guide
- Ahrefs Content Explorer API docs
- Google Search Console API docs

### Исследования:
- `docs/briefs/CONTENT_GAP_ANALYSIS_AGENT_BRIEF.md` - Бриф агента
- `~/Documents/Content_Gap_Analysis_Research_20260512/` - Deep research отчёт

---

**Дата создания:** 2026-05-12  
**Автор:** meAI Architect (via spec-writer skill)  
**Версия:** 1.0  
**Статус:** Draft
