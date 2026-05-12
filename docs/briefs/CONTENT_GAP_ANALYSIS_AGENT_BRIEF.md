# Бриф: Content Gap Analysis Agent

**Дата:** 2026-05-12  
**Приоритет:** P0  
**Родительский Magister:** SEO Magister

## Назначение

Анализировать контент конкурентов для выявления пробелов (gaps) и возможностей для создания нового контента. Агент должен находить темы, которые есть у конкурентов, но отсутствуют у клиента, и приоритизировать их по потенциалу.

## Контекст и специфика

**Медицинский маркетинг:**
- E-E-A-T требования (Experience, Expertise, Authoritativeness, Trustworthiness)
- Врачи-авторы как критерий качества
- Цитирование медицинских источников
- Compliance с FDA/HIPAA

**Конкурентная разведка:**
- Глубокий анализ контента конкурентов (не поверхностный)
- Выявление gaps между клиентом и конкурентами
- Анализ качества контента (depth, freshness, engagement)

**SEO оптимизация:**
- Анализ с точки зрения поисковой оптимизации
- Topic clustering (группировка по темам)
- Content quality metrics

## Интеграции

**Входные данные:**
- URL клиента (для анализа существующего контента)
- Список URL конкурентов (3-10 сайтов)
- Целевая ниша/тематика (например, "dental implants", "cosmetic dentistry")
- Параметры анализа (глубина, количество страниц, фильтры)

**Выходные данные:**
- Content Gap Report (markdown + JSON)
- Список тем с приоритетами (P0-P3)
- Рекомендации по созданию контента
- Метрики качества конкурентов
- Topic clusters с gaps

**Связанные агенты:**
- **Keyword Research Agent** - получает keywords для анализа контента
- **SEO Magister** - отправляет результаты для стратегии
- **Content Magister** - передаёт gaps для создания контента

**Внешние API:**
- **Ahrefs Content Explorer** - поиск популярного контента, backlinks, social shares
- **Google Search Console** - данные о своём сайте (позиции, CTR, impressions)
- **Google Trends** - трендовые темы
- **Yandex.Metrica** - метрики своего сайта (опционально)
- **TopWizard** - анализ топов (опционально)
- **Custom scraping** - парсинг сайтов конкурентов (обязательно, так как API дорогие)

## Приоритеты исследования

### 🔴 КРИТИЧНО (обязательно глубоко изучить)

1. **Content Quality Metrics**
   - Как измерять качество медицинского контента
   - E-E-A-T scoring для медицины (врачи-авторы, цитирование, экспертность)
   - Depth metrics (глубина раскрытия темы, количество слов, структура)
   - Freshness metrics (актуальность, дата обновления)
   - Engagement metrics (время на странице, bounce rate, social shares)
   - Readability metrics (читабельность для пациентов)

2. **Topic Clustering Algorithms**
   - Как группировать контент по темам и подтемам
   - Алгоритмы кластеризации (K-means, DBSCAN, hierarchical)
   - Semantic similarity (TF-IDF, embeddings, BERT)
   - Topic modeling (LDA, NMF)
   - Как определять parent topics и subtopics
   - Как находить gaps в кластерах

3. **Content Gap Analysis Methodology**
   - Как правильно находить gaps между клиентом и конкурентами
   - Методы сравнения контента (URL-based, topic-based, keyword-based)
   - Приоритизация gaps (opportunity score, difficulty, potential traffic)
   - Как учитывать качество контента конкурентов
   - Как избежать ложных gaps (темы, которые не нужны клиенту)

### 🟡 ВАЖНО (изучить, но не так глубоко)

1. **Web Scraping Best Practices**
   - Как парсить сайты конкурентов без блокировок
   - Robots.txt compliance
   - Rate limiting и politeness
   - Headless browsers vs HTTP requests
   - Proxy rotation

2. **API Integration**
   - Ahrefs Content Explorer API (endpoints, pricing, limits)
   - Google Search Console API (authentication, data extraction)
   - Google Trends API (trending topics, regional data)
   - Cost optimization (кэширование, batch requests)

3. **Medical Content Compliance**
   - FDA guidelines для контента
   - HIPAA compliance для медицинских сайтов
   - Prohibited claims detection
   - Risk scoring для контента

### 🟢 ОПЦИОНАЛЬНО (можно пропустить или поверхностно)

1. **Yandex.Metrica Integration**
   - API для метрик (если клиент использует)
   - Альтернатива Google Analytics

2. **TopWizard Integration**
   - Анализ топов выдачи
   - Альтернатива ручному анализу SERP

3. **Social Media Analysis**
   - Анализ social shares (Facebook, Twitter, LinkedIn)
   - Влияние на SEO (косвенное)

## Дополнительные материалы

**Интервью:** Этот бриф  
**Связанные спецификации:**
- `docs/subagents-specs/KEYWORD_RESEARCH_AGENT_SPEC.md` - для интеграции с keywords
- `docs/ARCHITECTURE-COMMUNICATION.md` - паттерны коммуникации

**TODO из других агентов:**
- Keyword Research Agent может передавать список keywords для анализа контента
- Content Magister будет использовать gaps для создания контента

## Важные замечания от пользователя

> "Смотрим, здесь короче какая фигня: **Content Gap**. Можно подключить по исследованиям также **TopWizard**, **Yandex.Metric**, чтобы на свои сайты ориентироваться. **Google Trends**, то есть еще что-то, **Google Search Console**. Что там еще может быть? То есть этими инструментами я пользуюсь постоянно. Просто их левцы и 7 Rush достаточно дорогие, и надо посмотреть, сюда сложить. Возможно, есть что-то в инструментах кейсов такое, плюс кастомная. Здесь надо будет дописывать, то есть каких данных нам не будет хватать. Заложи, пожалуйста, что нужно будет что-то придумывать, какие-то еще инструменты подключать точно."

**Ключевые выводы:**
- SEMrush и Ahrefs дорогие → нужен custom scraping как основной метод
- Использовать бесплатные API где возможно (GSC, Google Trends)
- Заложить возможность добавления новых инструментов в будущем
- Фокус на cost optimization (кэширование, batch requests, fallback patterns)

## Метрики успеха

**Качество анализа:**
- Точность gap detection (>90% релевантных gaps)
- Полнота анализа (>95% контента конкурентов покрыто)
- Качество приоритизации (P0 gaps действительно приоритетные)

**Производительность:**
- Время анализа: <10 минут для 5 конкурентов (50-100 страниц каждый)
- Стоимость: <$1 per analysis (за счёт custom scraping)
- Успешность парсинга: >95% страниц успешно обработаны

**Интеграция:**
- Seamless integration с Keyword Research Agent
- Event Bus messaging работает без ошибок
- Database persistence для результатов и кэша
