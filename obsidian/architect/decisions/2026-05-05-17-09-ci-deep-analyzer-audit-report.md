---
title: "CI Deep Analyzer Audit Report"
date: "2026-05-05"
type: "audit"
status: "completed"
severity: "critical"
tags: [ci-system, validation, quality-audit, data-quality]
---

# CI Deep Analyzer Audit Report

## Executive Summary

**Вердикт:** CI Deep Analyzer работает **поверхностно** и **не находит реальные проблемы**.

**Ключевые находки:**
- ❌ Все 4 "успешных" конкурента получили 95-100% без единой найденной проблемы
- ❌ Агент анализирует только SEO-покрытие (title/description/h1/schema)
- ❌ Нет анализа Core Web Vitals, accessibility, mobile, security
- ❌ Нет анализа контента, структуры, технических проблем
- ❌ "Quality score" = просто процент SEO-покрытия, не реальное качество

**Согласно исследованию Perplexity:** Это классический случай "агент плохо искал, а не не нашёл проблем".

---

## 1. Coverage Метрики (Покрытие)

### Цели из исследования:
- pages_crawled: ≥50 ✅
- templates_covered: ≥5-7 типов ❌
- depth_max: ≥3 клика от главной ❓
- cwv_pages_sampled: ≥10-20 страниц ❌

### Реальные результаты:

| Конкурент | Pages Analyzed | Templates | Depth | CWV Sampled |
|-----------|---------------|-----------|-------|-------------|
| Tori Clinic | 50 | 4 типа | ❓ | 0 ❌ |
| Professional Clinic | 50 | 6 типов | ❓ | 0 ❌ |
| CIDK | 50 | 2 типа ❌ | ❓ | 0 ❌ |
| Frau Clinic | 50 | 5 типов | ❓ | 0 ❌ |
| Щербатова | 1 ❌ | 1 тип ❌ | ❓ | 0 ❌ |

**Проблемы:**
1. **CIDK:** Только 2 типа страниц (homepage + services) — очень низкое покрытие
2. **Нет CWV анализа:** 0 страниц проверено на Core Web Vitals
3. **Нет depth метрики:** Не знаем, анализировались ли глубокие страницы

**Вердикт Coverage:** ⚠️ PARTIAL — страниц достаточно, но типов мало, CWV нет

---

## 2. Depth Метрики (Глубина)

### Цели из исследования:
- avg_checks_per_page: ≥15-20 проверок
- Проверки: CWV, mobile, SEO, accessibility, security, content
- tools_used: PageSpeed, Lighthouse, axe-core

### Реальные результаты:

**Что проверяется:**
1. ✅ SEO coverage: title, description, h1
2. ✅ Schema coverage: наличие разметки
3. ❌ Core Web Vitals: НЕТ
4. ❌ Mobile usability: НЕТ
5. ❌ Accessibility (WCAG): НЕТ
6. ❌ Security (HTTPS, headers): НЕТ
7. ❌ Content quality: НЕТ
8. ❌ Technical issues: НЕТ
9. ❌ Performance: НЕТ

**Checks per page:** ~4 проверки (title, description, h1, schema)

**Цель:** ≥15-20 проверок  
**Реально:** 4 проверки  
**Разрыв:** 73-80% проверок отсутствует

**Вердикт Depth:** ❌ SHALLOW_AUDIT — агент проверяет только 20-27% от необходимого

---

## 3. Sanity Метрики (Здравый смысл)

### Цели из исследования:
- score == 100 && issues == 0 → SUSPICIOUS_PERFECT_SCORE
- На реальных сайтах ВСЕГДА есть проблемы (CWV, alt, accessibility, meta)
- Нулевая корреляция с внешними метриками → подозрительно

### Реальные результаты:

#### Tori Clinic: 100% quality
```json
"seo_coverage": {
  "title": "50/50",      // 100%
  "description": "50/50", // 100%
  "h1": "50/50"          // 100%
},
"schema_coverage": "50/50", // 100%
"quality_score": 100.0
```

**Проблемы:**
- ✅ SEO покрытие идеальное
- ❓ Но что с CWV? Mobile? Accessibility? Security?
- ❓ Нет ни одной найденной проблемы — подозрительно

#### Professional Clinic: 95.33% quality
```json
"seo_coverage": {
  "title": "48/50",      // 96%
  "description": "47/50", // 94%
  "h1": "48/50"          // 96%
},
"schema_coverage": "48/50", // 96%
"quality_score": 95.33
```

**Проблемы:**
- 2-3 страницы без title/description/h1
- Но это ЕДИНСТВЕННЫЕ найденные проблемы
- Нет проблем с CWV, mobile, accessibility, security

#### CIDK: 99.33% quality
```json
"seo_coverage": {
  "title": "50/50",      // 100%
  "description": "50/50", // 100%
  "h1": "49/50"          // 98%
},
"schema_coverage": "50/50", // 100%
"quality_score": 99.33
```

**Проблемы:**
- 1 страница без h1
- Это ЕДИНСТВЕННАЯ найденная проблема
- 99.33% качество — почти идеально

#### Frau Clinic: 100% quality
```json
"seo_coverage": {
  "title": "50/50",      // 100%
  "description": "50/50", // 100%
  "h1": "50/50"          // 100%
},
"schema_coverage": "49/50", // 98%
"quality_score": 100.0
```

**Проблемы:**
- 1 страница без schema
- Но quality_score = 100% (не учитывает schema?)
- Нет других проблем

### Согласно исследованию, на реальных сайтах ВСЕГДА есть:
- ✅ Мелкие CWV issues (LCP > 2.5s, INP > 200ms)
- ✅ Пара изображений без alt
- ✅ Accessibility issues (контраст, фокус, labels)
- ✅ Meta descriptions отсутствуют где-то
- ✅ Redirect цепочки
- ✅ Странная иерархия H1/H2

**Наш агент нашёл:** 0 из этих проблем

**Вердикт Sanity:** ❌ SUSPICIOUS_PERFECT_SCORE — агент не видит реальные проблемы

---

## 4. Что агент НЕ проверяет (критично!)

### Core Web Vitals (КРИТИЧНО для медицины)
- ❌ LCP (Largest Contentful Paint)
- ❌ INP (Interaction to Next Paint)
- ❌ CLS (Cumulative Layout Shift)
- ❌ TTFB (Time to First Byte)
- ❌ FCP (First Contentful Paint)

**Почему важно:** Google использует CWV для ранжирования, особенно для медицинских сайтов.

### Mobile Usability (КРИТИЧНО)
- ❌ Responsive дизайн
- ❌ Viewport meta
- ❌ Горизонтальный скролл
- ❌ Размер кликабельных элементов
- ❌ Контент мобильной версии

**Почему важно:** 60-70% трафика медицинских сайтов с мобильных.

### Accessibility (КРИТИЧНО для медицины)
- ❌ Alt-тексты для изображений
- ❌ WCAG 2.1 AA compliance
- ❌ Контраст текста
- ❌ Навигация с клавиатуры
- ❌ Формы для скринридеров
- ❌ Семантическая разметка

**Почему важно:** Healthcare сайты ОБЯЗАНЫ соответствовать WCAG (ADA compliance).

### Security (КРИТИЧНО для медицины)
- ❌ HTTPS на всех страницах
- ❌ Mixed content
- ❌ SSL сертификаты
- ❌ Security headers (CSP, X-Frame-Options, HSTS)
- ❌ Формы записи (персональные данные)

**Почему важно:** HIPAA compliance, защита персональных данных пациентов.

### Technical SEO
- ❌ Robots.txt
- ❌ XML sitemap
- ❌ Canonical теги
- ❌ 4xx/5xx ошибки
- ❌ Redirect цепочки
- ❌ Глубина вложенности
- ❌ Внутренняя перелинковка

### Content Quality
- ❌ Качество текстов
- ❌ Уникальность контента
- ❌ Структура контента
- ❌ Читабельность
- ❌ E-E-A-T сигналы

---

## 5. Формула Quality Score (проблема!)

**Текущая формула:**
```python
quality_score = (
    (title_coverage + description_coverage + h1_coverage + schema_coverage) / 4
) * 100
```

**Проблемы:**
1. Учитывает только SEO-покрытие (4 метрики)
2. Не учитывает CWV, mobile, accessibility, security
3. Не учитывает найденные проблемы
4. 100% = "все теги на месте", а не "сайт качественный"

**Правильная формула (из исследования):**
```python
quality_score = weighted_average([
    seo_coverage * 0.15,           # 15%
    cwv_score * 0.25,              # 25% (критично!)
    mobile_score * 0.20,           # 20% (критично!)
    accessibility_score * 0.20,    # 20% (критично для медицины!)
    security_score * 0.10,         # 10% (критично для медицины!)
    technical_seo * 0.10           # 10%
])
```

---

## 6. Сравнение с целями исследования

| Метрика | Цель | Реально | Статус |
|---------|------|---------|--------|
| **Coverage** |
| pages_crawled | ≥50 | 50 | ✅ |
| templates_covered | ≥5-7 | 2-6 | ⚠️ |
| cwv_pages_sampled | ≥10-20 | 0 | ❌ |
| **Depth** |
| avg_checks_per_page | ≥15-20 | 4 | ❌ |
| CWV checks | ✅ | ❌ | ❌ |
| Mobile checks | ✅ | ❌ | ❌ |
| Accessibility checks | ✅ | ❌ | ❌ |
| Security checks | ✅ | ❌ | ❌ |
| **Sanity** |
| Issues found | ≥5-10 | 0-3 | ❌ |
| Perfect scores | Подозрительно | 2 из 4 | ❌ |
| External validation | ✅ | ❌ | ❌ |

**Итого:** 2/15 метрик выполнено (13%)

---

## 7. Конкретные примеры проблем

### Пример 1: Tori Clinic (100% quality)

**Что агент нашёл:**
- ✅ 50/50 страниц с title
- ✅ 50/50 страниц с description
- ✅ 50/50 страниц с h1
- ✅ 50/50 страниц с schema

**Что агент НЕ проверил:**
- ❓ Какой LCP на мобильных? (скорее всего > 2.5s)
- ❓ Есть ли alt у изображений? (скорее всего нет у части)
- ❓ Контраст текста по WCAG? (скорее всего проблемы есть)
- ❓ Формы доступны для скринридеров? (скорее всего нет)
- ❓ HTTPS на всех страницах? (скорее всего да, но не проверено)

**Реальность:** На любом сайте есть 5-10 минорных проблем. Агент их не видит.

### Пример 2: CIDK (99.33% quality)

**Что агент нашёл:**
- ✅ 50/50 страниц с title
- ✅ 50/50 страниц с description
- ⚠️ 49/50 страниц с h1 (1 проблема!)
- ✅ 50/50 страниц с schema

**Проблемы:**
- Только 2 типа страниц (homepage + services) — очень низкое покрытие
- Нет about, contacts, prices, blog
- Но quality_score = 99.33% (почти идеально!)

**Реальность:** Низкое покрытие типов страниц = проблема, но агент не учитывает.

---

## 8. Выводы

### Критические проблемы:

1. **Агент работает поверхностно**
   - Проверяет только 4 метрики из 15-20 необходимых
   - Не видит 73-80% проблем

2. **Quality Score не отражает реальное качество**
   - 100% = "все SEO-теги на месте"
   - Не учитывает CWV, mobile, accessibility, security

3. **Нет валидации с внешними источниками**
   - Нет кросс-проверки с PageSpeed, Lighthouse, axe-core
   - Агент работает в изоляции

4. **Подозрительно идеальные результаты**
   - 2 из 4 конкурентов = 100% quality
   - 0 найденных проблем у "идеальных" сайтов
   - Согласно исследованию: это флаг SUSPICIOUS_PERFECT_SCORE

### Что нужно исправить:

**P0 (Критично):**
1. Добавить Core Web Vitals анализ (PageSpeed API)
2. Добавить Mobile usability анализ (Lighthouse mobile)
3. Добавить Accessibility анализ (axe-core)
4. Пересчитать Quality Score с учётом всех метрик

**P1 (Важно):**
5. Добавить Security анализ (HTTPS, headers)
6. Добавить Technical SEO анализ (robots, sitemap, canonicals)
7. Добавить External validation (кросс-проверка с API)

**P2 (Желательно):**
8. Добавить Content quality анализ
9. Добавить Performance анализ
10. Добавить QA Validator слой

---

## 9. Рекомендации

### Немедленные действия:

1. **НЕ использовать текущие результаты для принятия решений**
   - Quality scores не отражают реальность
   - Нужна полная переработка анализа

2. **Создать QA Validator Agent**
   - Проверяет coverage, depth, sanity метрики
   - Флагирует подозрительные результаты
   - Кросс-проверка с внешними API

3. **Переработать CI Deep Analyzer**
   - Добавить CWV, mobile, accessibility, security
   - Изменить формулу Quality Score
   - Добавить детальный отчёт о проблемах

### Долгосрочные действия:

4. **Построить систему валидации по исследованию**
   - Multi-layer validation (agent → QA → operator)
   - Golden dataset для тестирования
   - LLM-as-a-judge для оценки качества

5. **Добавить метрики качества агента**
   - Pass rate на golden set
   - Agreement rate с внешними API
   - Regression trend после деплоев

---

## 10. Связанные документы

- **Исследование:** `inbox/Мне нужно построить систему валидации результатов.md`
- **Урок:** `obsidian/architect/wiki/lessons/2026-05-05-ci-url-validation-silent-failure.md`
- **Feedback:** `.claude/memory/feedback_ci_validation.md`
- **Результаты:** `AIM/data/ci-deep/deep_analysis_20260505_161902.json`

---

**Дата аудита:** 2026-05-05  
**Аудитор:** meAI Architect  
**Статус:** Критические проблемы найдены, требуется переработка
