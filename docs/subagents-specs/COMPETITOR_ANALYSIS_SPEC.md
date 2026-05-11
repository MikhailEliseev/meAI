# Competitor Analysis Agent - Спецификация

**Дата:** 2026-05-11  
**Magister:** SEO Magister  
**Приоритет:** P1  
**Статус:** Ready for Implementation

---

## 🎯 РОЛЬ И НАЗНАЧЕНИЕ

### Основная роль:
Competitor Analysis Agent проводит глубокий многофакторный анализ конкурентов для выявления keyword gaps, content opportunities, backlink strategies, technical advantages и compliance risks в медицинском маркетинге.

### Что делает:
- ✅ Анализирует keyword gaps между клиентом и конкурентами с приоритизацией по потенциалу
- ✅ Оценивает контент-стратегии конкурентов (темы, форматы, E-E-A-T, частота публикаций)
- ✅ Исследует backlink профили конкурентов и выявляет link building opportunities
- ✅ Проводит технический SEO аудит (Core Web Vitals, schema markup, mobile optimization)
- ✅ Верифицирует compliance конкурентов (FDA, HIPAA, этические стандарты)
- ✅ Анализирует local SEO присутствие (GBP, reviews, NAP consistency)
- ✅ Оценивает AI platform visibility (ChatGPT, Perplexity, Gemini citations)
- ✅ Отслеживает paid advertising стратегии (креативы, бюджеты, landing pages)

### Что НЕ делает:
- ❌ Не создаёт контент (передаёт gaps Content Strategy Agent)
- ❌ Не строит ссылки (передаёт opportunities Link Building Agent)
- ❌ Не исправляет технические проблемы (передаёт findings Technical SEO Agent)
- ❌ Не проводит keyword research с нуля (получает базовый список от Keyword Research Agent)

### Место в иерархии:
```
SEO Magister
    ↓
SEO Orchestrator
    ↓
Competitor Analysis Agent ← вы здесь
    ↓ (передаёт данные)
├─→ Keyword Research Agent (keyword gaps)
├─→ Content Strategy Agent (content gaps)
├─→ Technical SEO Agent (technical findings)
└─→ Link Building Agent (backlink opportunities)
```

### Уникальная ценность:
**Статистика из исследования:**
- 72% пациентов находят медицинские услуги через local search
- Competitor analysis выявляет gaps, которые приводят к +132% до +39,900% росту трафика
- E-E-A-T architecture audit перед контентом = +1,882% трафика (Dallas Orthopedic)
- Compliance-first подход предотвращает катастрофические нарушения (200+ FDA писем в 2025)

---

## 📥 ВХОДНЫЕ ДАННЫЕ

### Получает от Orchestrator:

**Формат события:**
```json
{
  "event_type": "subagent.task.assigned",
  "correlation_id": "uuid",
  "task_id": "uuid",
  "subagent_id": "competitor-analysis-agent",
  "payload": {
    "client_url": "https://client-clinic.com",
    "competitor_urls": [
      "https://competitor1.com",
      "https://competitor2.com",
      "https://competitor3.com"
    ],
    "analysis_depth": "comprehensive",
    "focus_areas": [
      "keyword_gaps",
      "content_strategy",
      "backlinks",
      "technical_seo",
      "compliance",
      "local_seo"
    ],
    "priority_keywords": [
      "knee replacement surgeon",
      "orthopedic clinic near me",
      "sports medicine doctor"
    ]
  }
}
```

**Обязательные параметры:**
- `client_url` (string) - URL сайта клиента для сравнения
- `competitor_urls` (array[string]) - Список URL конкурентов (1-5 сайтов)
- `analysis_depth` (enum) - "quick" | "standard" | "comprehensive" | "deep"

**Опциональные параметры:**
- `focus_areas` (array[string]) - Области анализа (по умолчанию все)
- `priority_keywords` (array[string]) - Приоритетные ключевые слова для gap analysis
- `geo_location` (string) - Географическая локация для local SEO анализа
- `compliance_frameworks` (array[string]) - Фреймворки для проверки ["FDA", "HIPAA", "AMA"]

---

## 📤 ВЫХОДНЫЕ ДАННЫЕ

### Отправляет Orchestrator:

**Формат события:**
```json
{
  "event_type": "subagent.task.completed",
  "correlation_id": "uuid",
  "task_id": "uuid",
  "subagent_id": "competitor-analysis-agent",
  "payload": {
    "status": "success",
    "result": {
      "competitor_profiles": [
        {
          "url": "https://competitor1.com",
          "domain_authority": 45,
          "organic_traffic": 125000,
          "ranking_keywords": 3456,
          "backlinks": 8900,
          "compliance_score": 85,
          "e_e_a_t_score": 78
        }
      ],
      "keyword_gaps": {
        "total_gaps": 1234,
        "high_priority": 45,
        "medium_priority": 189,
        "low_priority": 1000,
        "top_opportunities": [
          {
            "keyword": "knee replacement cost",
            "search_volume": 2400,
            "difficulty": 42,
            "competitor_position": 3,
            "client_position": null,
            "opportunity_score": 87,
            "priority": "P0"
          }
        ]
      },
      "content_gaps": {
        "missing_topics": 23,
        "thin_content": 12,
        "outdated_content": 8,
        "top_opportunities": [
          {
            "topic": "Knee Replacement Recovery Timeline",
            "competitor_coverage": 4,
            "avg_word_count": 2500,
            "avg_citations": 7,
            "estimated_traffic": 1500,
            "priority": "P1"
          }
        ]
      },
      "backlink_gaps": {
        "total_donor_domains": 456,
        "high_quality_donors": 78,
        "top_opportunities": [
          {
            "donor_domain": "healthline.com",
            "domain_rating": 92,
            "linking_to_competitors": 3,
            "link_type": "editorial",
            "estimated_difficulty": "medium",
            "priority": "P1"
          }
        ]
      },
      "technical_findings": {
        "core_web_vitals": {
          "client_lcp": 3.2,
          "competitor_avg_lcp": 2.1,
          "gap": "client_slower"
        },
        "schema_markup": {
          "client_schemas": 3,
          "competitor_avg_schemas": 8,
          "missing_schemas": ["MedicalProcedure", "FAQPage", "Physician"]
        },
        "mobile_optimization": {
          "client_score": 78,
          "competitor_avg_score": 89,
          "gap": "needs_improvement"
        }
      },
      "compliance_findings": {
        "fda_violations": 0,
        "hipaa_risks": 2,
        "ethical_concerns": 1,
        "risk_level": "medium",
        "details": [
          {
            "competitor": "competitor1.com",
            "violation_type": "HIPAA",
            "description": "Meta Pixel on patient portal",
            "severity": "high"
          }
        ]
      },
      "local_seo_analysis": {
        "gbp_optimization": {
          "client_score": 65,
          "competitor_avg_score": 82,
          "gaps": ["missing_services", "low_review_count"]
        },
        "review_velocity": {
          "client_reviews_per_month": 3,
          "competitor_avg_reviews_per_month": 8,
          "gap": "needs_improvement"
        }
      },
      "ai_platform_visibility": {
        "chatgpt_citations": {
          "client": 12,
          "competitor_avg": 45,
          "gap": "significant"
        },
        "perplexity_citations": {
          "client": 8,
          "competitor_avg": 32,
          "gap": "significant"
        }
      }
    },
    "metrics": {
      "execution_time_ms": 450000,
      "competitors_analyzed": 3,
      "keyword_gaps_found": 1234,
      "content_gaps_found": 23,
      "backlink_opportunities": 78,
      "api_calls_made": 45
    },
    "errors": []
  }
}
```

**Структура результата:**
- `competitor_profiles` - Профили конкурентов с ключевыми метриками
- `keyword_gaps` - Keyword opportunities с приоритизацией
- `content_gaps` - Content opportunities с оценкой потенциала
- `backlink_gaps` - Link building opportunities с оценкой сложности
- `technical_findings` - Технические преимущества конкурентов
- `compliance_findings` - Compliance риски конкурентов
- `local_seo_analysis` - Local SEO gaps и opportunities
- `ai_platform_visibility` - AI platform citation gaps

**Метрики:**
- `execution_time_ms` - Время выполнения анализа
- `competitors_analyzed` - Количество проанализированных конкурентов
- `keyword_gaps_found` - Найдено keyword gaps
- `content_gaps_found` - Найдено content gaps
- `backlink_opportunities` - Найдено backlink opportunities
- `api_calls_made` - Количество API вызовов

---

## 🔄 АЛГОРИТМ РАБОТЫ

### Шаг 1: Получение задачи и валидация
1. Подписаться на события `subagent.task.assigned`
2. Фильтровать по `subagent_id == "competitor-analysis-agent"`
3. Валидировать входные параметры:
   - `client_url` - валидный URL, доступен
   - `competitor_urls` - 1-5 URL, все доступны
   - `analysis_depth` - допустимое значение
4. Проверить доступность API (SEMrush, Ahrefs, GSC, PageSpeed)

### Шаг 2: Сбор базовых данных о конкурентах
**Для каждого конкурента:**
1. **Domain metrics** (SEMrush API):
   - Organic traffic estimate
   - Ranking keywords count
   - Domain Authority / Trust Score
   - Backlinks count
2. **Technical baseline** (PageSpeed Insights API):
   - Core Web Vitals (LCP, INP, CLS)
   - Performance score
   - Mobile optimization score
3. **Compliance scan** (custom crawler):
   - FDA clearance/approval verification
   - HIPAA tracking pixel detection
   - Ethical standards check

### Шаг 3: Keyword Gap Analysis
1. **Получить keyword sets:**
   - Client keywords (SEMrush API: domain_organic)
   - Competitor keywords (SEMrush API: domain_organic)
2. **Идентифицировать gaps:**
   - Keywords где competitors rank top-10, client не ранжируется
   - Фильтровать branded terms
3. **Приоритизация gaps:**
   - Рассчитать Opportunity Score для каждого keyword
   - Formula: `(Volume × Intent × Current_Position) / (Difficulty × Competition)`
   - Классифицировать: P0 (score 80-100), P1 (60-79), P2 (40-59), P3 (0-39)
4. **Сохранить top opportunities:**
   - Top 50 gaps с highest opportunity score
   - Группировать по intent (informational, commercial, transactional)

### Шаг 4: Content Strategy Analysis
1. **Crawl competitor content:**
   - Использовать Screaming Frog или custom crawler
   - Извлечь: URL, title, word count, publish date, author
2. **Анализ E-E-A-T signals:**
   - Author credentials (MD, DO, board certification)
   - Citations count (peer-reviewed sources)
   - Trust signals (certifications, affiliations)
3. **Topic clustering:**
   - Группировать content по темам
   - Идентифицировать missing topics у client
4. **Publication frequency:**
   - Рассчитать posts per month (last 12 months)
   - Сравнить с client frequency
5. **Content depth analysis:**
   - Avg word count per topic
   - Avg citations per article
   - Media richness (images, videos)

### Шаг 5: Backlink Profile Analysis
1. **Получить backlink data:**
   - Ahrefs API: backlinks, referring domains
   - Фильтровать: DR 20+, organic traffic 500+
2. **Идентифицировать donor gaps:**
   - Domains linking to 2+ competitors but not client
   - Оценить quality: DR, traffic, relevance, spam score
3. **Anchor text analysis:**
   - Distribution: branded, commercial, informational
   - Сравнить с client anchor text profile
4. **Link building strategy patterns:**
   - Guest posts, digital PR, broken links, resource pages
   - Идентифицировать replicable tactics
5. **Приоритизация opportunities:**
   - High priority: DR 50-70, editorial links, relevant niche
   - Medium priority: DR 30-50, mixed links
   - Low priority: DR 20-30, directory links

### Шаг 6: Technical SEO Competitive Audit
1. **Core Web Vitals benchmarking:**
   - PageSpeed Insights API для каждого competitor
   - Сравнить LCP, INP, CLS с client
2. **Schema markup analysis:**
   - Crawl и extract structured data
   - Идентифицировать missing schemas у client
3. **Site structure analysis:**
   - URL structure patterns
   - Internal linking depth
   - Navigation architecture
4. **Mobile optimization:**
   - Mobile-friendly test
   - Responsive design check
   - Mobile page speed

### Шаг 7: Compliance Verification
1. **FDA compliance check:**
   - Verify product clearance/approval
   - Scan for fair balance violations
   - Check risk disclosure prominence
2. **HIPAA compliance scan:**
   - Detect tracking pixels (Meta, GA)
   - Check form processors for BAA
   - Verify email/SMS vendors
3. **Ethical standards review:**
   - AMA Code violations (exclusive claims, testimonials)
   - State-specific law compliance
4. **Risk scoring:**
   - Critical: off-label promotion, unapproved claims
   - High: fair balance violations, HIPAA gaps
   - Medium: technical violations
   - Low: minor documentation gaps

### Шаг 8: Local SEO Analysis (если geo_location указан)
1. **Google Business Profile audit:**
   - Completeness score
   - Review count and velocity
   - Response rate and time
   - Photos and posts frequency
2. **NAP consistency check:**
   - Verify Name, Address, Phone across directories
   - Identify inconsistencies
3. **Local pack rankings:**
   - Check rankings for "[service] near me" queries
   - Analyze local pack competitors
4. **Review analysis:**
   - Sentiment analysis
   - Response patterns
   - Review velocity trends

### Шаг 9: AI Platform Visibility (GEO)
1. **Citation tracking:**
   - Query ChatGPT, Perplexity, Gemini for target topics
   - Count citations for client vs competitors
2. **Semantic relevance:**
   - Analyze content structure for AI citability
   - Check entity recognition (schema markup)
3. **Gap identification:**
   - Topics where competitors cited but client not
   - Content optimization opportunities

### Шаг 10: Формирование результата
1. Агрегировать findings по всем областям
2. Рассчитать priority scores для opportunities
3. Генерировать actionable recommendations
4. Создать executive summary с key insights

### Шаг 11: Отправка результата
1. Сформировать событие `subagent.task.completed`
2. Включить полный результат + метрики
3. Логировать в Event Store
4. Сохранить в Obsidian vault (`obsidian/seo-magister/competitor-analysis/`)

---

## 🔧 ИНТЕГРАЦИИ

### Внешние сервисы:

**SEMrush API:**
- **Endpoints:**
  - `domain_overview` - Domain metrics (traffic, keywords, backlinks)
  - `domain_organic` - Organic keyword rankings
  - `domain_domains` - Keyword gap analysis
  - `backlinks` - Backlink profile
- **Аутентификация:** API key
- **Rate Limits:** 10,000-40,000 units/day (зависит от плана)
- **Pricing:** $449.95/month (Business plan) для API access
- **Документация:** https://www.semrush.com/api-documentation/

**Ahrefs API:**
- **Endpoints:**
  - `domain-rating` - Domain authority metrics
  - `backlinks` - Backlink data
  - `broken-backlinks` - Broken link opportunities
  - `refdomains` - Referring domains
- **Аутентификация:** Bearer token
- **Rate Limits:** 60 requests per minute
- **Pricing:** $129-$449/month (зависит от плана)
- **Документация:** https://ahrefs.com/api/documentation

**Google Search Console API:**
- **Endpoints:**
  - `searchAnalytics` - Search performance data
  - `sitemaps` - Sitemap status
  - `urlInspection` - URL inspection
- **Аутентификация:** OAuth 2.0
- **Rate Limits:** 1,200 queries per minute per site
- **Pricing:** Free
- **Документация:** https://developers.google.com/webmaster-tools/v1/api_reference_index

**PageSpeed Insights API:**
- **Endpoints:**
  - `runPagespeed` - Performance and Core Web Vitals
- **Аутентификация:** API key
- **Rate Limits:** 25,000 requests per day
- **Pricing:** Free
- **Документация:** https://developers.google.com/speed/docs/insights/v5/get-started

### Внутренние зависимости:

- **Event Bus** (обязательно) - Получение задач, отправка результатов
- **Event Store** (обязательно) - Логирование всех операций
- **Obsidian vault** (обязательно) - Сохранение результатов анализа
- **Keyword Research Agent** (опционально) - Получение базового keyword list
- **Content Strategy Agent** (опционально) - Передача content gaps
- **Technical SEO Agent** (опционально) - Передача technical findings
- **Link Building Agent** (опционально) - Передача backlink opportunities

---

## 📊 МЕТРИКИ УСПЕХА

### Качественные метрики:

**Точность keyword gap analysis:**
- Метрика: % keyword gaps, которые действительно приводят к трафику после оптимизации
- Целевое значение: >70%
- Как измерять: Tracking keyword rankings через 3-6 месяцев после оптимизации

**Полнота competitor coverage:**
- Метрика: % критичных аспектов конкурентов, покрытых анализом
- Целевое значение: >90%
- Как измерять: Checklist из 50 критичных элементов (keywords, content, backlinks, technical, compliance)

**Actionability recommendations:**
- Метрика: % recommendations, которые были имплементированы клиентом
- Целевое значение: >60%
- Как измерять: Follow-up через 1-3 месяца после анализа

### Производительность:

**Скорость:**
- Quick analysis: < 5 минут (1 competitor, basic metrics)
- Standard analysis: < 15 минут (3 competitors, core areas)
- Comprehensive analysis: < 30 минут (5 competitors, all areas)
- Deep analysis: < 60 минут (5 competitors, all areas + compliance)

**Надёжность:**
- Success rate: > 95% (анализ завершён без критичных ошибок)
- Partial success rate: > 99% (анализ завершён с minor gaps)
- Failure rate: < 1% (анализ не завершён)

### Бизнес-метрики:

**Влияние на клиентские результаты:**
- Traffic growth: +132% до +39,900% (benchmark из case studies)
- Keyword rankings: +1,826% до +3,486% (benchmark из case studies)
- Lead generation: +115% до +520% (benchmark из case studies)
- ROI: 200-400% (Year 1), 400-800% (Year 2), 800-1,500% (Year 3+)

**Timeline to results:**
- Technical improvements: 1-3 месяца
- Ranking movement: 3-6 месяцев
- Significant traffic: 6-12 месяцев
- ROI positive: 8-18 месяцев

---

## 🧪 ПРИМЕРЫ ИСПОЛЬЗОВАНИЯ

### Пример 1: Comprehensive Analysis (Success)

**Входные данные:**
```json
{
  "client_url": "https://orthopedic-clinic.com",
  "competitor_urls": [
    "https://competitor-ortho1.com",
    "https://competitor-ortho2.com",
    "https://competitor-ortho3.com"
  ],
  "analysis_depth": "comprehensive",
  "focus_areas": [
    "keyword_gaps",
    "content_strategy",
    "backlinks",
    "technical_seo",
    "compliance"
  ],
  "priority_keywords": [
    "knee replacement surgeon",
    "orthopedic clinic near me",
    "sports medicine doctor"
  ],
  "geo_location": "Dallas, TX"
}
```

**Выходные данные:**
```json
{
  "status": "success",
  "result": {
    "competitor_profiles": [
      {
        "url": "https://competitor-ortho1.com",
        "domain_authority": 52,
        "organic_traffic": 145000,
        "ranking_keywords": 4567,
        "backlinks": 12500,
        "compliance_score": 92,
        "e_e_a_t_score": 85
      }
    ],
    "keyword_gaps": {
      "total_gaps": 1456,
      "high_priority": 67,
      "top_opportunities": [
        {
          "keyword": "knee replacement cost Dallas",
          "search_volume": 1200,
          "difficulty": 38,
          "competitor_position": 2,
          "client_position": null,
          "opportunity_score": 89,
          "priority": "P0"
        },
        {
          "keyword": "best orthopedic surgeon near me",
          "search_volume": 2400,
          "difficulty": 45,
          "competitor_position": 4,
          "client_position": null,
          "opportunity_score": 85,
          "priority": "P0"
        }
      ]
    },
    "content_gaps": {
      "missing_topics": 28,
      "top_opportunities": [
        {
          "topic": "Knee Replacement Recovery Timeline",
          "competitor_coverage": 3,
          "avg_word_count": 2800,
          "avg_citations": 8,
          "estimated_traffic": 2100,
          "priority": "P0"
        }
      ]
    },
    "backlink_gaps": {
      "total_donor_domains": 567,
      "high_quality_donors": 89,
      "top_opportunities": [
        {
          "donor_domain": "healthline.com",
          "domain_rating": 92,
          "linking_to_competitors": 3,
          "link_type": "editorial",
          "estimated_difficulty": "medium",
          "priority": "P1"
        }
      ]
    },
    "technical_findings": {
      "core_web_vitals": {
        "client_lcp": 3.4,
        "competitor_avg_lcp": 2.0,
        "gap": "client_slower",
        "improvement_potential": "high"
      },
      "schema_markup": {
        "client_schemas": 3,
        "competitor_avg_schemas": 9,
        "missing_schemas": ["MedicalProcedure", "FAQPage", "Physician", "Review"]
      }
    },
    "compliance_findings": {
      "fda_violations": 0,
      "hipaa_risks": 1,
      "ethical_concerns": 0,
      "risk_level": "low",
      "details": [
        {
          "competitor": "competitor-ortho2.com",
          "violation_type": "HIPAA",
          "description": "Google Analytics on appointment booking page",
          "severity": "medium"
        }
      ]
    }
  },
  "metrics": {
    "execution_time_ms": 420000,
    "competitors_analyzed": 3,
    "keyword_gaps_found": 1456,
    "content_gaps_found": 28,
    "backlink_opportunities": 89,
    "api_calls_made": 42
  }
}
```

### Пример 2: Quick Analysis (Partial Success)

**Входные данные:**
```json
{
  "client_url": "https://dental-clinic.com",
  "competitor_urls": [
    "https://competitor-dental.com"
  ],
  "analysis_depth": "quick",
  "focus_areas": ["keyword_gaps", "technical_seo"]
}
```

**Выходные данные:**
```json
{
  "status": "partial_success",
  "result": {
    "competitor_profiles": [
      {
        "url": "https://competitor-dental.com",
        "domain_authority": 38,
        "organic_traffic": 45000,
        "ranking_keywords": 1234,
        "backlinks": 3400
      }
    ],
    "keyword_gaps": {
      "total_gaps": 456,
      "high_priority": 23,
      "top_opportunities": [
        {
          "keyword": "dental implants cost",
          "search_volume": 1800,
          "difficulty": 42,
          "opportunity_score": 78,
          "priority": "P1"
        }
      ]
    },
    "technical_findings": {
      "core_web_vitals": {
        "client_lcp": 2.8,
        "competitor_avg_lcp": 2.2,
        "gap": "minor"
      }
    }
  },
  "metrics": {
    "execution_time_ms": 180000,
    "competitors_analyzed": 1,
    "keyword_gaps_found": 456,
    "api_calls_made": 8
  },
  "errors": [
    {
      "code": "BACKLINK_DATA_UNAVAILABLE",
      "message": "Ahrefs API rate limit exceeded, backlink analysis skipped",
      "severity": "warning"
    }
  ]
}
```

### Пример 3: Invalid Input (Failure)

**Входные данные:**
```json
{
  "client_url": "invalid-url",
  "competitor_urls": [],
  "analysis_depth": "comprehensive"
}
```

**Выходные данные:**
```json
{
  "status": "failure",
  "result": null,
  "metrics": {
    "execution_time_ms": 500,
    "competitors_analyzed": 0,
    "api_calls_made": 0
  },
  "errors": [
    {
      "code": "INVALID_INPUT",
      "message": "client_url is not a valid URL",
      "details": {
        "param": "client_url",
        "value": "invalid-url"
      }
    },
    {
      "code": "INVALID_INPUT",
      "message": "competitor_urls must contain at least 1 URL",
      "details": {
        "param": "competitor_urls",
        "value": []
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
- Действие: Вернуть failure сразу с описанием проблемы
- Retry: Нет
- Примеры:
  - Invalid URL format
  - Empty competitor_urls array
  - Invalid analysis_depth value

**Ошибка внешнего API:**
- Код: `EXTERNAL_API_ERROR`
- Действие: Retry с exponential backoff (1s, 2s, 4s)
- Retry: До 3 попыток
- Примеры:
  - SEMrush API timeout
  - Ahrefs rate limit exceeded
  - GSC authentication failure

**Timeout:**
- Код: `TIMEOUT`
- Действие: Вернуть partial_success с обработанными данными
- Retry: Нет
- Примеры:
  - Deep analysis превысил 60 минут
  - Competitor site не отвечает

**Недоступность competitor site:**
- Код: `COMPETITOR_UNAVAILABLE`
- Действие: Пропустить competitor, продолжить с остальными
- Retry: 1 попытка через 30 секунд
- Примеры:
  - Site returns 404/500
  - DNS resolution failure
  - SSL certificate error

**Недостаточно данных:**
- Код: `INSUFFICIENT_DATA`
- Действие: Вернуть partial_success с доступными данными
- Retry: Нет
- Примеры:
  - Competitor не имеет backlinks в Ahrefs
  - GSC data недоступна для competitor
  - PageSpeed API не может проанализировать site

### Graceful degradation:

При частичном сбое:
1. Обработать максимум данных из доступных источников
2. Вернуть partial_success с заполненными секциями
3. Указать в errors[], какие данные недоступны и почему
4. Позволить Orchestrator решить, достаточно ли данных для продолжения

**Пример graceful degradation:**
```json
{
  "status": "partial_success",
  "result": {
    "keyword_gaps": { /* полные данные */ },
    "content_gaps": { /* полные данные */ },
    "backlink_gaps": null,
    "technical_findings": { /* полные данные */ }
  },
  "errors": [
    {
      "code": "EXTERNAL_API_ERROR",
      "message": "Ahrefs API unavailable, backlink analysis skipped",
      "severity": "warning",
      "impact": "backlink_gaps section empty"
    }
  ]
}
```

### Retry Strategy:

**Exponential backoff для API errors:**
```python
def retry_with_backoff(func, max_retries=3):
    for attempt in range(max_retries):
        try:
            return func()
        except APIError as e:
            if attempt == max_retries - 1:
                raise
            wait_time = 2 ** attempt  # 1s, 2s, 4s
            time.sleep(wait_time)
```

**Rate limit handling:**
```python
def handle_rate_limit(api_name, retry_after):
    if retry_after > 60:
        # Слишком долго ждать, skip этот API
        log_warning(f"{api_name} rate limit exceeded, skipping")
        return None
    else:
        # Подождать и retry
        time.sleep(retry_after)
        return retry_request()
```

---

## 🧠 ОБУЧЕНИЕ И АДАПТАЦИЯ

### Источники обучения:

**От SEO Magister:**
- Обновлённые best practices по competitor analysis
- Новые ranking factors от Google
- Изменения в алгоритмах (Core Updates, Medic Updates)
- Актуальные compliance требования (FDA, HIPAA)

**Из собственного опыта:**
- Успешные keyword gaps (которые привели к traffic growth)
- Неудачные recommendations (которые не дали результата)
- Correlation между competitor metrics и client success
- Паттерны в winning competitor strategies

**Из Obsidian vault:**
- Исторические competitor analyses
- Tracking keyword gap outcomes (3-6 месяцев после)
- Case studies с documented ROI
- Compliance violation patterns

### Адаптация:

**Когда адаптироваться:**
- Success rate keyword gaps падает ниже 70%
- Google выпускает major algorithm update
- FDA/HIPAA вводят новые enforcement guidelines
- Появляются новые competitor analysis tools/APIs

**Как адаптироваться:**
1. **Получить обновлённые знания от SEO Magister:**
   - Новые ranking factors
   - Изменения в prioritization formula
   - Обновлённые compliance checklists

2. **Протестировать на небольшой выборке:**
   - Выбрать 3-5 recent analyses
   - Применить новый подход
   - Сравнить outcomes через 3 месяца

3. **Сравнить метрики до/после:**
   - Success rate keyword gaps
   - Actionability recommendations
   - Client satisfaction scores

4. **Применить, если улучшение подтверждено:**
   - Rollout новый подход на все analyses
   - Документировать изменения в Obsidian
   - Обновить алгоритм работы

**Пример адаптации (Google Core Update):**
```
Событие: Google Core Update (May 2026) усилил E-E-A-T signals
Адаптация: Увеличить вес E-E-A-T score в competitor profiles с 15% до 25%
Тестирование: 5 analyses с новым весом
Результат: Recommendations accuracy +12%
Решение: Применить новый вес для всех future analyses
```

---

## 📝 ЛОГИРОВАНИЕ

### Что логировать:

**В Event Store (обязательно):**
- Все входящие события `subagent.task.assigned`
- Все исходящие события `subagent.task.completed`
- Correlation ID для трейсинга
- Timestamp каждого события
- Payload (входные и выходные данные)

**В Obsidian vault (обязательно):**
```
obsidian/seo-magister/competitor-analysis/
├── analyses/
│   ├── 2026-05-11_orthopedic-clinic_analysis.md
│   ├── 2026-05-10_dental-clinic_analysis.md
│   └── ...
├── keyword-gaps/
│   ├── orthopedic-clinic_keyword-gaps.json
│   └── ...
├── insights/
│   ├── winning-strategies.md
│   ├── compliance-patterns.md
│   └── ...
└── metrics/
    ├── success-rates.json
    └── performance-trends.json
```

**Структура analysis document:**
```markdown
# Competitor Analysis: [Client Name]

**Date:** 2026-05-11  
**Competitors Analyzed:** 3  
**Analysis Depth:** Comprehensive  
**Execution Time:** 7 minutes

## Executive Summary
[Key findings and recommendations]

## Competitor Profiles
[Detailed profiles with metrics]

## Keyword Gaps
[Top opportunities with prioritization]

## Content Gaps
[Missing topics and opportunities]

## Backlink Gaps
[Link building opportunities]

## Technical Findings
[Performance and optimization gaps]

## Compliance Findings
[Risk assessment and violations]

## Recommendations
[Actionable next steps prioritized]

## Metadata
- Task ID: uuid
- Correlation ID: uuid
- API Calls: 42
- Success Rate: 100%
```

**В системные логи (опционально):**
- Debug информация (API requests/responses)
- Ошибки и warnings
- Performance traces (slow queries, timeouts)

### Формат логов:

```
[2026-05-11 18:30:45] [INFO] [competitor-analysis-agent] [corr-id-123] Starting analysis for orthopedic-clinic.com
[2026-05-11 18:31:12] [DEBUG] [competitor-analysis-agent] [corr-id-123] SEMrush API call: domain_organic (competitor1.com)
[2026-05-11 18:31:15] [DEBUG] [competitor-analysis-agent] [corr-id-123] Found 1456 keyword gaps
[2026-05-11 18:37:23] [INFO] [competitor-analysis-agent] [corr-id-123] Analysis completed successfully
```

---

## 🧪 ТЕСТИРОВАНИЕ

### Unit тесты:

**Покрытие:** > 80%

**Обязательные тесты:**

1. **Валидация входных данных:**
   - Valid URLs accepted
   - Invalid URLs rejected
   - Empty competitor_urls rejected
   - Invalid analysis_depth rejected

2. **Keyword gap calculation:**
   - Opportunity score formula correct
   - Prioritization logic correct
   - Branded terms filtered
   - Intent classification accurate

3. **E-E-A-T scoring:**
   - Author credentials detected
   - Citations counted correctly
   - Trust signals identified
   - Score calculation accurate

4. **Compliance detection:**
   - FDA violations detected
   - HIPAA tracking pixels detected
   - Ethical violations flagged
   - Risk scoring correct

5. **Error handling:**
   - API errors handled gracefully
   - Timeouts return partial_success
   - Invalid competitor URLs skipped
   - Retry logic works correctly

### Integration тесты:

**Обязательные сценарии:**

1. **End-to-end analysis flow:**
   - Receive task from Orchestrator
   - Call all required APIs
   - Process data correctly
   - Return complete result
   - Log to Event Store
   - Save to Obsidian vault

2. **API integration:**
   - SEMrush API returns valid data
   - Ahrefs API returns valid data
   - GSC API returns valid data
   - PageSpeed API returns valid data
   - Rate limits respected

3. **Error scenarios:**
   - API unavailable → partial_success
   - Competitor site down → skip competitor
   - Timeout → return processed data
   - Invalid input → failure immediately

### E2E тесты:

**Обязательные сценарии:**

1. **Comprehensive analysis (3 competitors):**
   - All focus_areas analyzed
   - All APIs called successfully
   - Complete result returned
   - Execution time < 30 minutes
   - Success status

2. **Quick analysis (1 competitor):**
   - Limited focus_areas
   - Minimal API calls
   - Basic result returned
   - Execution time < 5 minutes
   - Success status

3. **Graceful degradation:**
   - Ahrefs API unavailable
   - Backlink analysis skipped
   - Other areas completed
   - Partial_success status
   - Error logged

**Test data:**
```python
TEST_CASES = [
    {
        "name": "orthopedic_clinic_comprehensive",
        "client_url": "https://test-ortho-clinic.com",
        "competitor_urls": [
            "https://test-competitor1.com",
            "https://test-competitor2.com",
            "https://test-competitor3.com"
        ],
        "analysis_depth": "comprehensive",
        "expected_execution_time_ms": 1800000,  # 30 min
        "expected_keyword_gaps": 1000,
        "expected_status": "success"
    },
    {
        "name": "dental_clinic_quick",
        "client_url": "https://test-dental-clinic.com",
        "competitor_urls": ["https://test-competitor.com"],
        "analysis_depth": "quick",
        "expected_execution_time_ms": 300000,  # 5 min
        "expected_keyword_gaps": 200,
        "expected_status": "success"
    }
]
```

---

## 🚀 DEPLOYMENT

### Требования:

**Окружение:**
- Python 3.11+
- Event Bus доступен
- Event Store доступен
- Obsidian vault доступен
- Internet connectivity для API calls

**Зависимости:**
```
semrush-api >= 1.0.0
ahrefs-api >= 2.0.0
google-api-python-client >= 2.0.0
requests >= 2.31.0
beautifulsoup4 >= 4.12.0
lxml >= 4.9.0
pydantic >= 2.0.0
asyncio >= 3.11.0
```

**Конфигурация:**
```env
SUBAGENT_ID=competitor-analysis-agent
EVENT_BUS_URL=redis://localhost:6379
EVENT_STORE_URL=postgresql://localhost:5432/meai
OBSIDIAN_VAULT_PATH=/Users/mikhaileliseev/Desktop/Dev/!meAI/AIM/obsidian/seo-magister

# API Keys
SEMRUSH_API_KEY=your_semrush_key
AHREFS_API_KEY=your_ahrefs_key
GOOGLE_API_KEY=your_google_key
GOOGLE_CLIENT_ID=your_client_id
GOOGLE_CLIENT_SECRET=your_client_secret

# Rate Limits
SEMRUSH_RATE_LIMIT=10000
AHREFS_RATE_LIMIT=60
GOOGLE_RATE_LIMIT=1200
PAGESPEED_RATE_LIMIT=25000

# Timeouts
QUICK_ANALYSIS_TIMEOUT_MS=300000
STANDARD_ANALYSIS_TIMEOUT_MS=900000
COMPREHENSIVE_ANALYSIS_TIMEOUT_MS=1800000
DEEP_ANALYSIS_TIMEOUT_MS=3600000
```

### Мониторинг:

**Метрики для алертов:**

| Метрика | Warning | Critical |
|---------|---------|----------|
| Success rate | < 95% | < 90% |
| Avg execution time (comprehensive) | > 35 min | > 45 min |
| API error rate | > 5% | > 10% |
| Keyword gap accuracy | < 75% | < 70% |

**Health check endpoint:**
```python
@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "apis": {
            "semrush": await check_semrush_api(),
            "ahrefs": await check_ahrefs_api(),
            "google": await check_google_api()
        },
        "event_bus": await check_event_bus(),
        "event_store": await check_event_store(),
        "obsidian_vault": check_obsidian_vault()
    }
```

**Grafana dashboard metrics:**
- Analyses per hour
- Success/partial_success/failure rates
- Avg execution time by analysis_depth
- API call distribution
- Error rate by error_code
- Keyword gap accuracy (tracked over 3-6 months)

---

## 📚 СВЯЗАННЫЕ ДОКУМЕНТЫ

### Спецификации:
- `SEO_MAGISTER_SPEC.md` - Спецификация родительского SEO Magister
- `SEO_ORCHESTRATOR_SPEC.md` - Спецификация SEO Orchestrator
- `KEYWORD_RESEARCH_SPEC.md` - Спецификация Keyword Research Agent (v1.0.0)
- `CONTENT_STRATEGY_SPEC.md` - Спецификация Content Strategy Agent (TODO)
- `TECHNICAL_SEO_SPEC.md` - Спецификация Technical SEO Agent (TODO)
- `LINK_BUILDING_SPEC.md` - Спецификация Link Building Agent (TODO)

### Код:
- `AIM/src/aim/subagents/seo/competitor_analysis_agent.py` - Реализация
- `AIM/tests/subagents/seo/test_competitor_analysis_agent.py` - Тесты

### Документация:
- Event Bus API - `docs/EVENT_BUS_API.md`
- Event Store API - `docs/EVENT_STORE_API.md`
- Obsidian integration guide - `docs/OBSIDIAN_INTEGRATION.md`
- SEMrush API docs - https://www.semrush.com/api-documentation/
- Ahrefs API docs - https://ahrefs.com/api/documentation
- Google Search Console API - https://developers.google.com/webmaster-tools
- PageSpeed Insights API - https://developers.google.com/speed/docs/insights

### Research:
- `~/Documents/Competitor_Analysis_Medical_Marketing_Research_20260511/report.md` - Deep research report (18,000 слов, 36 источников)
- `docs/briefs/COMPETITOR_ANALYSIS_AGENT_BRIEF.md` - Исходный бриф

---

## 📋 CHANGELOG

### Version 1.0.0 (2026-05-11)

**Created:**
- Initial specification based on deep research (18,000 words, 36 sources)
- Comprehensive competitor analysis methodology
- Multi-factor keyword gap prioritization framework
- E-E-A-T competitive audit methodology
- Compliance verification framework (FDA, HIPAA, AMA)
- Local SEO analysis methodology
- AI platform visibility tracking (GEO)
- API integration guides (SEMrush, Ahrefs, GSC, PageSpeed)
- Case study benchmarks (5 medical SEO implementations)

**Key Features:**
- 8-step analysis workflow (validation → data collection → gaps → compliance → results)
- Graceful degradation for partial API failures
- Exponential backoff retry strategy
- Comprehensive error handling
- Obsidian vault integration for knowledge persistence
- Success metrics tracking (70%+ keyword gap accuracy target)

**Research Insights Applied:**
- Compliance-first approach (200+ FDA letters, 250+ HIPAA settlements in 2025)
- E-E-A-T as architectural foundation (Dallas Orthopedic case study)
- Local SEO dominance (72% patients find providers via local search)
- ROI patterns (200-400% Year 1, 400-800% Year 2, 800-1,500% Year 3+)
- Timeline expectations (6-12 months to significant results)

---

## 🔮 TODO / FUTURE ENHANCEMENTS

### Phase 2 (Post-MVP):
- [ ] **Automated competitor discovery** - Identify competitors automatically via SERP overlap
- [ ] **Competitive intelligence alerts** - Notify when competitor launches new content/campaign
- [ ] **Historical trend analysis** - Track competitor metrics over time (traffic, keywords, backlinks)
- [ ] **Predictive gap scoring** - ML model to predict which gaps will convert best
- [ ] **Social media competitive analysis** - Expand to Instagram, Facebook, LinkedIn presence
- [ ] **Video content analysis** - YouTube competitor analysis (views, engagement, topics)
- [ ] **Voice search optimization** - Analyze competitor voice search visibility
- [ ] **International expansion** - Multi-language competitor analysis

### Phase 3 (Advanced):
- [ ] **Automated report generation** - PDF/PowerPoint reports for clients
- [ ] **Competitive benchmarking dashboard** - Real-time competitor tracking UI
- [ ] **AI-powered insights** - LLM analysis of competitor strategies
- [ ] **Sentiment analysis** - Analyze competitor review sentiment vs client
- [ ] **Conversion rate estimation** - Estimate competitor conversion rates from public data
- [ ] **Budget estimation** - More accurate competitor ad spend estimation

### Research Gaps (from deep research report):
- [ ] **Paid advertising intelligence** - Deeper analysis of competitor ad strategies
- [ ] **Social media presence** - Comprehensive social competitive analysis
- [ ] **Email marketing** - Competitor email campaign tracking
- [ ] **Offline presence** - Physical location and offline advertising analysis

---

**Дата создания:** 2026-05-11  
**Автор:** meAI Architect (via spec-writer skill v2.0)  
**Версия:** 1.0.0  
**Статус:** Ready for Implementation

**Research Source:** Competitor Analysis Medical Marketing Research (May 11, 2026)  
**Research Mode:** Deep (8 phases, 18 minutes)  
**Research Cost:** ~$3.00-$4.00  
**Sources:** 36 high-quality sources (18 WebSearch + 3 sub-agents)

---

## ПРИЛОЖЕНИЕ A: ПОЛНОЕ ИССЛЕДОВАНИЕ

Полный research report доступен в:
`~/Documents/Competitor_Analysis_Medical_Marketing_Research_20260511/report.md`

**Размер:** 18,000 слов, 135 KB, 3,530 строк  
**Структура:** 12 основных секций + Executive Summary + Synthesis + Bibliography

**Ключевые секции:**
1. Medical Marketing Compliance Framework (FDA, HIPAA, AMA)
2. E-E-A-T Architecture for Medical Sites
3. Keyword Gap Analysis Methodology
4. Content Strategy Competitive Analysis
5. Backlink Profile Analysis
6. Technical SEO Competitive Audit
7. Local SEO Competitive Analysis
8. AI Platform Competitive Intelligence (GEO)
9. Paid Advertising Competitive Intelligence
10. API Integration Guide (SEMrush, Ahrefs, GSC, PageSpeed)
11. Implementation Workflow & Timeline
12. Success Metrics & KPIs

**Case Studies (5):**
1. Dallas Orthopedic Associates (+1,882% traffic, $1.98M revenue, 9.9:1 ROI)
2. Multi-Location Dental Practice (+187% traffic, +340% inquiries)
3. Natura Dermatology (+39,900% traffic, 672 AI citations)
4. London Beauty Clinic (+718% traffic, +213% leads)
5. Private Aesthetic Clinic (+132% traffic, +115% leads)

**API Integrations (4):**
1. SEMrush API ($449.95/month, 10,000-40,000 units/day)
2. Ahrefs API ($129-$449/month, 60 RPM)
3. Google Search Console API (Free, 1,200 QPM)
4. PageSpeed Insights API (Free, 25,000 requests/day)

**Compliance Framework:**
- FDA: 21 CFR Part 202, 801 (200+ enforcement letters 2025)
- HIPAA: 45 CFR §164 (250+ settlements 2024+)
- AMA: Code of Medical Ethics Opinion 5.02
- State laws: CA CMIA/CCPA, WA My Health My Data Act

**Implementation Budget:**
- Year 1: $77,650-$146,650 (labor + tools)
- Expected ROI: 200-400% (Y1), 400-800% (Y2), 800-1,500% (Y3+)

---

**END OF SPECIFICATION**
