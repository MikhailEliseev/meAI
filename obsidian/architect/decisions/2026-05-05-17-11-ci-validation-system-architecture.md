---
title: "CI Validation System Architecture"
decision_id: "ci-validation-system-2026-05-05"
timestamp: "2026-05-05T17:11:00"
confidence: 0.88
status: "pending"
tags: [decision, strategic, ci-system, validation, architecture]
---

# Strategic Decision: CI Validation System Architecture

## Question

Как спроектировать систему валидации результатов CI Deep Analyzer на основе аудита и исследования Perplexity?

## Context

**Проблема:** Аудит показал, что CI Deep Analyzer работает поверхностно:
- Проверяет только 4 метрики из 15-20 необходимых (20-27% покрытие)
- Не анализирует CWV, mobile, accessibility, security
- Возвращает подозрительно идеальные результаты (100% quality, 0 issues)
- Quality Score = просто процент SEO-покрытия, не реальное качество

**Исследование Perplexity:** Дало конкретные метрики и архитектуру для валидации AI-агентов.

**Цель:** Построить production-ready систему валидации, которая:
1. Проверяет качество работы агентов
2. Находит реальные проблемы на сайтах
3. Не пропускает поверхностные результаты
4. Кросс-проверяет с внешними API

## Decision

**Действие:** Построить 3-слойную систему валидации с расширенным анализом и автоматическими проверками качества

## Rationale

### Почему 3 слоя?

**Слой 1: Enhanced CI Deep Analyzer** (расширенный анализ)
- Добавляем CWV, mobile, accessibility, security проверки
- Увеличиваем checks_per_page с 4 до 15-20
- Меняем формулу Quality Score на взвешенную

**Слой 2: QA Validator Agent** (автоматическая валидация)
- Проверяет coverage, depth, sanity метрики
- Кросс-проверка с внешними API (PageSpeed, Lighthouse, axe-core)
- Флагирует подозрительные результаты (SUSPICIOUS_PERFECT_SCORE, LOW_COVERAGE)

**Слой 3: Human Operator** (финальная проверка)
- Смотрит только на результаты с флагами
- Принимает решение: accept / reject / retry
- Пополняет golden dataset для обучения

### Почему это лучший подход?

1. **Data-driven:** Основан на реальных проблемах из аудита
2. **Автоматизирован:** QA Validator работает без человека
3. **Масштабируем:** Можно добавлять новые проверки
4. **Обучаемый:** Golden dataset улучшает качество со временем

### Учёт прошлого опыта:

- **Урок 2026-05-05:** CI URL Validation Silent Failure — агенты не должны fail silently
- **Feedback:** Quality Over Speed — глубина важнее скорости
- **Аудит 2026-05-05:** Агент работает поверхностно, нужна валидация

### План отката:

Если система валидации окажется слишком строгой (много false positives):
- Настроить пороги флагов (например, LOW_COVERAGE при < 10 страниц вместо < 20)
- Добавить confidence scores для флагов
- Разрешить оператору override флагов

## Confidence

**0.88** (высокая уверенность)

Почему не 0.95:
- Нужно протестировать на реальных данных
- Внешние API могут быть недоступны (rate limits)
- Формула Quality Score требует калибровки

## Alternatives Considered

### 1. Сразу переделать CI Deep Analyzer без QA-слоя
**Плюсы:** Проще, меньше кода  
**Минусы:** Нет автоматической проверки качества, можем пропустить проблемы  
**Почему не выбрано:** Нужна валидация, чтобы не повторить ошибку

### 2. Только QA Validator без расширения CI Deep Analyzer
**Плюсы:** Быстрее реализовать  
**Минусы:** QA будет флагировать все результаты как LOW_DEPTH  
**Почему не выбрано:** Нужно сначала исправить источник проблемы

### 3. Построить 3-слойную систему (выбрано)
**Плюсы:** Комплексное решение, автоматизация, обучаемость  
**Минусы:** Больше кода, сложнее поддержка  
**Почему выбрано:** Единственный способ гарантировать качество

## Risks

### Риск 1: Внешние API недоступны или медленные
**Вероятность:** Средняя  
**Влияние:** Высокое (валидация не работает)  
**Митигация:**
- Кэшировать результаты внешних API (15 минут)
- Fallback на локальные проверки (Lighthouse CLI)
- Graceful degradation (если API недоступен → флаг WARNING, не REJECT)

### Риск 2: QA Validator слишком строгий (много false positives)
**Вероятность:** Средняя  
**Влияние:** Среднее (оператор тратит время на проверку)  
**Митигация:**
- Калибровка порогов на golden dataset
- Confidence scores для флагов (0.0-1.0)
- Оператор может override флаги

### Риск 3: Расширенный анализ работает медленно
**Вероятность:** Высокая  
**Влияние:** Низкое (Quality Over Speed)  
**Митигация:**
- Параллельный запуск проверок (CWV, mobile, accessibility)
- Кэширование результатов для повторных анализов
- Прогресс-бар для пользователя

## Implementation Plan

### Phase 1: Enhanced CI Deep Analyzer (P0, 2-3 дня)

**Задачи:**
1. Добавить Core Web Vitals анализ
   - Интеграция с PageSpeed Insights API
   - Метрики: LCP, INP, CLS, TTFB, FCP
   - Сбор на 10-20 страницах

2. Добавить Mobile Usability анализ
   - Lighthouse mobile mode
   - Проверки: viewport, responsive, tap targets
   - Метрики: mobile_score (0-100)

3. Добавить Accessibility анализ
   - Интеграция с axe-core
   - Проверки: alt, contrast, keyboard, forms, WCAG 2.1 AA
   - Метрики: accessibility_score (0-100)

4. Добавить Security анализ
   - Проверки: HTTPS, mixed content, SSL, headers
   - Метрики: security_score (0-100)

5. Изменить формулу Quality Score
   ```python
   quality_score = weighted_average([
       seo_coverage * 0.15,
       cwv_score * 0.25,
       mobile_score * 0.20,
       accessibility_score * 0.20,
       security_score * 0.10,
       technical_seo * 0.10
   ])
   ```

6. Добавить детальный отчёт о проблемах
   - Список найденных issues (critical/major/minor)
   - Для каждой проблемы: severity, page, description, how_to_fix

**Результат:** CI Deep Analyzer проверяет 15-20 метрик вместо 4

---

### Phase 2: QA Validator Agent (P0, 1-2 дня)

**Задачи:**
1. Создать QA Validator Agent
   - Файл: `AIM/src/aim/subagents/competitive_intel/agents/ci_qa_validator.py`
   - Базовый класс: `BaseAgent`

2. Реализовать Coverage проверки
   ```python
   if audit.coverage.pages_crawled < 20:
       flags.append('LOW_COVERAGE')
   if audit.coverage.templates_covered < 3:
       flags.append('LOW_TEMPLATE_DIVERSITY')
   ```

3. Реализовать Depth проверки
   ```python
   if audit.metrics.avg_checks_per_page < 10:
       flags.append('SHALLOW_AUDIT')
   ```

4. Реализовать Sanity проверки
   ```python
   if audit.score == 100 and len(audit.issues) == 0:
       flags.append('SUSPICIOUS_PERFECT_SCORE')
   ```

5. Реализовать External Validation
   ```python
   psi = await fetch_pagespeed(domain)
   if audit.cwv.lcp < 2.5 and psi.lcp > 4.0:
       flags.append('EXTERNAL_MISMATCH_CWV')
   ```

6. Вернуть QA Verdict
   ```python
   return {
       'status': 'OK' | 'SUSPECT' | 'REJECT',
       'flags': [...],
       'confidence': 0.0-1.0
   }
   ```

**Результат:** Автоматическая валидация результатов CI Deep Analyzer

---

### Phase 3: Integration в CI Orchestrator (P0, 1 день)

**Задачи:**
1. Добавить validation gate после Phase 5
   ```python
   # Phase 5: Deep Analysis
   phase5_result = await self._execute_phase(5, payload, results)
   
   # VALIDATION GATE
   qa_validator = CIQAValidator(...)
   for competitor in phase5_result:
       qa_verdict = await qa_validator.validate(competitor)
       
       if qa_verdict['status'] == 'REJECT':
           # Ask user what to do
           action = await self.ask_user(
               f"Анализ {competitor['name']} не прошёл валидацию.\n"
               f"Флаги: {qa_verdict['flags']}\n"
               f"Что делать?\n"
               f"1. Retry с другими настройками\n"
               f"2. Skip этого конкурента\n"
               f"3. Accept as is (override)"
           )
   ```

2. Добавить логирование QA результатов
   - Сохранять в `AIM/data/ci-deep/qa_reports/`
   - Формат: `qa_report_{competitor}_{timestamp}.json`

3. Добавить метрики QA Validator
   - Сколько результатов прошло валидацию
   - Сколько было отклонено
   - Какие флаги чаще всего

**Результат:** CI Orchestrator автоматически валидирует результаты

---

### Phase 4: Golden Dataset (P1, 1-2 дня)

**Задачи:**
1. Создать golden dataset
   - 5-10 сайтов с заранее размеченными проблемами
   - Эталонные выводы для каждого сайта
   - Хранить в `AIM/data/ci-deep/golden_dataset/`

2. Добавить тесты на golden dataset
   ```python
   async def test_golden_dataset():
       for site in golden_dataset:
           result = await ci_deep_analyzer.analyze(site.url)
           qa_verdict = await qa_validator.validate(result)
           
           assert result.quality_score == site.expected_score ± 5
           assert set(result.issues) == set(site.expected_issues)
   ```

3. Добавить regression tests
   - Запускать после каждого изменения CI Deep Analyzer
   - Проверять, что качество не деградирует

**Результат:** Автоматическое тестирование качества агента

---

### Phase 5: External API Integration (P1, 2-3 дня)

**Задачи:**
1. PageSpeed Insights API
   - Регистрация API key
   - Интеграция в CI Deep Analyzer
   - Кэширование результатов (15 минут)

2. Lighthouse CLI
   - Установка через npm
   - Запуск через subprocess
   - Парсинг JSON результатов

3. axe-core
   - Интеграция в Playwright
   - Запуск на каждой странице
   - Агрегация результатов

4. Rate limiting и error handling
   - Retry с exponential backoff
   - Fallback на локальные проверки
   - Graceful degradation

**Результат:** Кросс-проверка с внешними источниками

---

### Phase 6: Operator Dashboard (P2, 2-3 дня)

**Задачи:**
1. Создать dashboard для оператора
   - Список результатов с флагами
   - Детали каждого флага
   - Кнопки: Accept / Reject / Retry

2. Добавить статистику
   - Pass rate на golden dataset
   - Распределение флагов
   - Regression trend

3. Добавить feedback loop
   - Оператор помечает результаты как correct/incorrect
   - Пополнение golden dataset
   - Обучение QA Validator

**Результат:** Удобный интерфейс для оператора

---

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                     CI Orchestrator                          │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
                    ┌─────────────────┐
                    │   Phase 5:      │
                    │ CI Deep Analyzer│
                    │   (Enhanced)    │
                    └─────────────────┘
                              │
                    ┌─────────┴─────────┐
                    │  Parallel Checks  │
                    ├───────────────────┤
                    │ • CWV (PageSpeed) │
                    │ • Mobile (Light.) │
                    │ • A11y (axe-core) │
                    │ • Security (SSL)  │
                    │ • SEO (existing)  │
                    └─────────┬─────────┘
                              │
                              ▼
                    ┌─────────────────┐
                    │  Audit Result   │
                    │  + Issues List  │
                    └─────────────────┘
                              │
                              ▼
                    ┌─────────────────┐
                    │ VALIDATION GATE │
                    └─────────────────┘
                              │
                              ▼
                    ┌─────────────────┐
                    │ QA Validator    │
                    │     Agent       │
                    └─────────────────┘
                              │
                    ┌─────────┴─────────┐
                    │   QA Checks       │
                    ├───────────────────┤
                    │ • Coverage        │
                    │ • Depth           │
                    │ • Sanity          │
                    │ • External API    │
                    └─────────┬─────────┘
                              │
                              ▼
                    ┌─────────────────┐
                    │   QA Verdict    │
                    │ OK/SUSPECT/     │
                    │    REJECT       │
                    └─────────────────┘
                              │
                    ┌─────────┴─────────┐
                    │                   │
                    ▼                   ▼
            ┌──────────┐        ┌──────────┐
            │    OK    │        │ REJECT   │
            │  Pass    │        │ Ask User │
            └──────────┘        └──────────┘
                    │                   │
                    │                   ▼
                    │           ┌──────────┐
                    │           │ Retry /  │
                    │           │ Skip /   │
                    │           │ Override │
                    │           └──────────┘
                    │                   │
                    └───────────┬───────┘
                                ▼
                    ┌─────────────────┐
                    │  Next Phase     │
                    │  (Phase 10+)    │
                    └─────────────────┘
```

---

## Data Structures

### Enhanced Audit Result

```python
@dataclass
class EnhancedAuditResult:
    # Basic info
    name: str
    url: str
    analyzed_at: datetime
    
    # Coverage metrics
    coverage: CoverageMetrics
    
    # Analysis results
    seo: SEOAnalysis
    cwv: CoreWebVitals
    mobile: MobileAnalysis
    accessibility: AccessibilityAnalysis
    security: SecurityAnalysis
    technical: TechnicalSEO
    
    # Issues
    issues: List[Issue]
    
    # Quality score
    quality_score: float  # 0-100, weighted average
    component_scores: Dict[str, float]
    
    # Raw evidence
    raw_evidence: Dict[str, Any]

@dataclass
class CoverageMetrics:
    pages_crawled: int
    templates_covered: int
    depth_max: int
    cwv_pages_sampled: int

@dataclass
class CoreWebVitals:
    lcp: float  # Largest Contentful Paint (seconds)
    inp: float  # Interaction to Next Paint (ms)
    cls: float  # Cumulative Layout Shift
    ttfb: float  # Time to First Byte (ms)
    fcp: float  # First Contentful Paint (seconds)
    score: float  # 0-100

@dataclass
class Issue:
    severity: Literal['critical', 'major', 'minor']
    category: str  # 'cwv', 'mobile', 'accessibility', 'security', 'seo'
    code: str  # 'LCP_TOO_HIGH', 'MISSING_ALT', etc.
    page: str
    description: str
    how_to_fix: str
```

### QA Verdict

```python
@dataclass
class QAVerdict:
    status: Literal['OK', 'SUSPECT', 'REJECT']
    flags: List[str]
    confidence: float  # 0.0-1.0
    external_checks: Dict[str, Any]
    recommendations: List[str]
```

---

## Metrics to Track

### Agent Quality Metrics
- **Pass rate on golden dataset:** % результатов, прошедших валидацию
- **Agreement rate with external API:** корреляция с PageSpeed/Lighthouse
- **Regression trend:** график качества после деплоев
- **False positive rate:** % REJECT, которые оператор override

### Validation Metrics
- **Coverage rate:** % результатов с достаточным покрытием
- **Depth rate:** % результатов с достаточной глубиной
- **Sanity rate:** % результатов без подозрительных паттернов
- **External validation rate:** % результатов, прошедших кросс-проверку

### Performance Metrics
- **Analysis time:** время анализа одного конкурента
- **API latency:** время ответа внешних API
- **Cache hit rate:** % запросов, обслуженных из кэша

---

## Success Criteria

### Phase 1 (Enhanced Analyzer):
- ✅ CI Deep Analyzer проверяет ≥15 метрик (было 4)
- ✅ Quality Score учитывает CWV, mobile, accessibility, security
- ✅ Детальный отчёт с issues (critical/major/minor)

### Phase 2 (QA Validator):
- ✅ QA Validator флагирует подозрительные результаты
- ✅ Кросс-проверка с PageSpeed, Lighthouse, axe-core
- ✅ Автоматическое определение OK/SUSPECT/REJECT

### Phase 3 (Integration):
- ✅ Validation gate работает в CI Orchestrator
- ✅ Оператор получает уведомления о REJECT
- ✅ Логирование QA результатов

### Phase 4 (Golden Dataset):
- ✅ Golden dataset с 5-10 сайтами
- ✅ Regression tests проходят
- ✅ Pass rate ≥90% на golden dataset

### Phase 5 (External API):
- ✅ Интеграция с PageSpeed, Lighthouse, axe-core
- ✅ Кэширование работает
- ✅ Graceful degradation при недоступности API

### Phase 6 (Dashboard):
- ✅ Operator dashboard работает
- ✅ Статистика отображается
- ✅ Feedback loop работает

---

## Timeline

- **Phase 1:** 2-3 дня (Enhanced CI Deep Analyzer)
- **Phase 2:** 1-2 дня (QA Validator Agent)
- **Phase 3:** 1 день (Integration)
- **Phase 4:** 1-2 дня (Golden Dataset)
- **Phase 5:** 2-3 дня (External API)
- **Phase 6:** 2-3 дня (Operator Dashboard)

**Итого:** 9-14 дней (2-3 недели)

**MVP (Phase 1-3):** 4-6 дней (1 неделя)

---

## Status

- **Created:** 2026-05-05T17:11:00
- **Status:** pending
- **Implemented:** false

---

## Related Documents

- **Audit Report:** `obsidian/architect/decisions/2026-05-05-17-09-ci-deep-analyzer-audit-report.md`
- **Research:** `inbox/Мне нужно построить систему валидации результатов.md`
- **Lesson:** `obsidian/architect/wiki/lessons/2026-05-05-ci-url-validation-silent-failure.md`
- **Feedback:** `.claude/memory/feedback_ci_validation.md`
