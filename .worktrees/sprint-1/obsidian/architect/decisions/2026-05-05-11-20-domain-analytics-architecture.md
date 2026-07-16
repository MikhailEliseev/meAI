---
title: "Domain Analytics Architecture - Two-Level Analytics System"
decision_id: "domain-analytics-two-level-arch"
timestamp: "2026-05-05T11:20:35Z"
confidence: 0.88
status: approved
tags: [decision, strategic, analytics, architecture]
---

# Strategic Decision: Domain Analytics Architecture

## Question

Как реализовать систему аналитики для AIM Agency, где каждый Magister (SEO, Content, Ads, AI) имеет гетерогенные метрики и разные источники данных?

## Context

**Проблема:** Analytics Magister пытается централизованно собирать гетерогенные метрики из разных доменов. Это создаёт tight coupling и не масштабируется.

**Требования:**
- Каждый домен имеет уникальные метрики (SEO: позиции, Content: engagement, Ads: ROAS, AI: токены)
- Разные источники данных (Google Search Console, CMS, Яндекс.Директ, Anthropic API)
- Нужен кросс-доменный анализ для стратегических решений
- Система должна масштабироваться при добавлении новых доменов

**Принцип:** "Идеальность важнее скорости" - делаем правильно с первого раза

## Decision

**Реализовать двухуровневую архитектуру аналитики:**

1. **Уровень 1: Domain Analytics Subagents** (локальная агрегация)
   - Каждый Magister получает 5-го субагента - Domain Analytics
   - Субагент собирает и агрегирует доменные метрики
   - Знает специфику своего домена лучше всех
   - Публикует обработанные данные в Event Bus

2. **Уровень 2: Analytics Magister** (стратегический анализ)
   - Получает агрегированные метрики от всех доменов
   - Анализирует кросс-доменные корреляции
   - Генерирует стратегические инсайты
   - Создаёт executive отчёты

## Rationale

### Почему это лучшее решение

**1. Domain Expertise Preserved**
- SEO Analytics знает, как правильно агрегировать позиции и backlinks
- Content Analytics понимает engagement и качество контента
- Ads Analytics умеет считать ROAS и оптимизировать бюджет
- AI Analytics отслеживает токены и latency

**2. Loose Coupling**
- Analytics Magister не знает о внутренних метриках доменов
- Добавление нового домена не требует изменений в Analytics Magister
- Каждый домен может менять свои метрики независимо

**3. Scalability**
- Параллельный сбор метрик от всех доменов
- Локальная агрегация снижает нагрузку на Analytics Magister
- Легко добавить новый домен (просто добавить Domain Analytics субагента)

**4. Strategic Value**
- Analytics Magister фокусируется на стратегическом анализе
- Кросс-доменные корреляции (SEO ↑ → Ads CPA ↓)
- Стратегические инсайты для принятия решений

### Учёт прошлого опыта

**Похожие решения:**
- SEOMagister уже использует паттерн локальной агрегации (метод `aggregate_results()`)
- BaseMagister предоставляет инфраструктуру для координации субагентов
- Event Bus успешно используется для асинхронной коммуникации

**Уроки:**
- Централизованный сбор данных не работает для гетерогенных метрик (текущая проблема)
- Доменная экспертиза критична для правильной агрегации
- Стандартизированные интерфейсы упрощают интеграцию

### План отката

**Если не сработает:**

1. **Проблема:** Domain Analytics субагенты слишком сложны
   - **Откат:** Упростить до простого сбора данных без агрегации
   - **Время:** 1 день
   - **Риск:** Потеря доменной экспертизы

2. **Проблема:** Кросс-доменный анализ не даёт ценности
   - **Откат:** Оставить только Domain Analytics, убрать Analytics Magister
   - **Время:** 2 часа
   - **Риск:** Потеря стратегических инсайтов

3. **Проблема:** Performance проблемы
   - **Откат:** Добавить кэширование и инкрементальные обновления
   - **Время:** 1 день
   - **Риск:** Увеличение сложности

## Confidence

**88%** (0.88)

**Почему не выше:**
- Нет прецедентов двухуровневой аналитики в системе (новый паттерн)
- Неизвестно, насколько ценными будут кросс-доменные корреляции
- Может потребоваться итерация на метриках и форматах данных

**Почему не ниже:**
- Паттерн локальной агрегации уже работает в SEOMagister
- Архитектура следует принципам loose coupling и domain expertise
- Есть чёткий план отката для каждого риска

## Alternatives Considered

### Alternative 1: Centralized Analytics (Current)

**Описание:** Analytics Magister напрямую собирает данные из всех источников

**Pros:**
- Простая архитектура
- Единая точка контроля
- Легко понять

**Cons:**
- Tight coupling между доменами
- Analytics Magister знает слишком много
- Не масштабируется
- Теряется доменная экспертиза

**Почему отклонено:** Не масштабируется, создаёт tight coupling

### Alternative 2: Fully Distributed Analytics

**Описание:** Каждый Magister имеет полную аналитику, без центрального координатора

**Pros:**
- Максимальное разделение
- Полная автономность доменов
- Легко добавить новый домен

**Cons:**
- Нет кросс-доменного анализа
- Дублирование логики аналитики
- Сложно получить стратегические инсайты
- Нет центральной отчётности

**Почему отклонено:** Теряется стратегическая ценность

### Alternative 3: Two-Level Architecture (CHOSEN)

**Описание:** Domain Analytics субагенты + Analytics Magister

**Pros:**
- Баланс между разделением и координацией
- Сохранена доменная экспертиза
- Возможен кросс-доменный анализ
- Масштабируемая архитектура

**Cons:**
- Сложнее централизованного подхода
- Требует стандартизированных интерфейсов
- Два уровня агрегации

**Почему выбрано:** Лучший баланс trade-offs

## Risks

### Risk 1: Data Source API Changes

**Вероятность:** Medium  
**Влияние:** High  
**Митигация:**
- Абстрагировать доступ к источникам данных через интерфейсы
- Версионировать API клиенты
- Мониторить уведомления о deprecation
- Реализовать fallback источники данных

### Risk 2: Metric Heterogeneity

**Вероятность:** High  
**Влияние:** Medium  
**Митигация:**
- Стандартизированный формат `AggregatedMetrics`
- Разрешены доменные расширения
- Чёткая документация определений метрик
- Валидация на границах агрегации

### Risk 3: Performance at Scale

**Вероятность:** Low  
**Влияние:** Medium  
**Митигация:**
- Асинхронная обработка везде
- Кэширование агрегированных метрик
- Инкрементальные обновления (не полный пересчёт)
- Индексы БД на time-series данных

### Risk 4: Cross-Domain Correlation Accuracy

**Вероятность:** Medium  
**Влияние:** Low  
**Митигация:**
- Начать с простых корреляций (Pearson r)
- Валидировать корреляции на исторических данных
- Человеческий review стратегических инсайтов
- Confidence scores на всех корреляциях

## Implementation Plan

### Phase 1: Base Infrastructure (Day 1)
1. Create `BaseDomainAnalytics` class
2. Define data models (`DomainMetrics`, `AggregatedMetrics`, `CrossDomainMetrics`)
3. Update Event Bus with new event types
4. Create Obsidian vault structure for Domain Analytics

### Phase 2: Domain Analytics Subagents (Day 2-3)
1. Implement SEO Analytics Subagent
2. Implement Content Analytics Subagent
3. Implement Ads Analytics Subagent
4. Implement AI Analytics Subagent

### Phase 3: Analytics Magister Refactor (Day 4)
1. Refactor Analytics Magister to work with Domain Analytics
2. Implement cross-domain aggregation
3. Implement correlation analysis
4. Implement strategic insights generation

### Phase 4: Integration & Testing (Day 5)
1. Integrate with existing Magisters
2. Update Excalidraw diagram
3. End-to-end testing
4. Documentation

## Status

- **Created:** 2026-05-05T11:20:35Z
- **Status:** Approved
- **Implemented:** false
- **Implementation Start:** 2026-05-05
- **Estimated Completion:** 2026-05-10 (5 days)

## Self-Critique Results

✅ **Alternatives Completeness:** 3 alternatives (centralized, distributed, two-level)  
✅ **Risk Assessment:** 4 concrete risks with mitigation strategies  
✅ **Cognitive Biases:** No "obviously", confidence < 0.95, no sunk cost  
✅ **Past Experience:** Referenced SEOMagister pattern, BaseMagister infrastructure  
✅ **Failure Modes:** 3 rollback scenarios with time estimates

**All checks passed!** ✅

## References

- Full specification: `docs/superpowers/specs/2026-05-05-domain-analytics-architecture.md`
- SEOMagister pattern: `AIM/src/aim/magisters/seo_magister.py`
- BaseMagister: `src/meai/agents/magister_base.py`
- Current Analytics: `AIM/src/aim/magisters/analytics_magister.py`
