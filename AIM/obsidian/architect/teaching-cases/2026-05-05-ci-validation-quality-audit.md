---
title: "CI URL Validation & Quality Audit"
type: "teaching-case"
case_id: "TC-2026-05-05-ci-validation"
created: "2026-05-05"
difficulty: "Advanced"
duration: "4-6 hours to study"
skills_taught:
  - Problem diagnosis and root cause analysis
  - System auditing and quality metrics
  - Multi-layer validation architecture
  - Agent learning integration
  - Research-driven decision making
prerequisites:
  - Understanding of CI system architecture
  - Knowledge of Agent Learning system
  - Familiarity with Lessons Learned pattern
tags: [ci-system, validation, quality-audit, agent-learning, architecture]
---

# Teaching Case: CI URL Validation & Quality Audit

## Executive Summary

CI Deep Analyzer вернул подозрительные результаты: 4 конкурента с 100% качеством и 1 с 0%. Глубокий аудит показал, что агент работает поверхностно (проверяет только 20-27% необходимых метрик). Провели исследование через Perplexity, спроектировали 3-слойную систему валидации, реализовали URL Validator. Результат: 100% validation rate, план улучшения технического агента на 2-3 недели.

---

## The Problem (Проблема)

### Initial Situation

**Дата:** 2026-05-05  
**Контекст:** CI Deep Analyzer проанализировал 5 конкурентов из косметологии

**Результаты:**
- Tori Clinic: 100% quality
- Professional Clinic: 95.33% quality  
- CIDK: 99.33% quality
- Frau Clinic: 100% quality
- Клиника Юлии Щербатовой: 0% quality ❌

### Symptoms

1. **Подозрительно идеальные результаты**
   - 2 из 4 успешных конкурентов = 100% quality
   - 0 найденных проблем у "идеальных" сайтов
   - Согласно исследованию: на реальных сайтах ВСЕГДА есть 5-10 минорных проблем

2. **Провал 5-го конкурента**
   - 0% quality, 1 страница проанализирована
   - DNS error на URL: doctor-shcherbatova.ru
   - Правильный URL: juliasherbatova.ru

3. **Агент не спросил пользователя**
   - Вернул 0% молча, без вопросов
   - Нарушение Prevention Rule из Lesson 2026-05-05

### Impact

**Business Impact:**
- Клиентский отчёт неполный (4 из 5 конкурентов)
- Риск принятия решений на неполных данных
- Потеря доверия к CI системе

**Technical Impact:**
- Wasted resources на анализ недоступного URL
- Неполные данные в ci-deep/deep_analysis.json

**User Impact:**
- Потрачено время на анализ неправильного URL
- Плохой UX - система не спросила, просто вернула 0%

### Red Flags

1. **4×100% и 1×0%** - классический паттерн "агент плохо искал"
2. **Нет найденных проблем** - на реальных сайтах всегда есть проблемы
3. **Silent failure** - агент не спросил при ошибке

---

## Investigation (Исследование)

### Step 1: User Question

**Вопрос пользователя:**
> "Почему ты решил, что результаты, которые ты получил от этого агента, валидные и нормальные? Может быть, стоит каждый результат любого своего агента ставить под сомнение и перепроверять?"

**Инсайт:** Пользователь прав - мы приняли результаты как истину, не проверив качество работы агента.

### Step 2: Research via Perplexity

**Промпт для Perplexity:**
```
Мне нужно построить систему валидации результатов AI-агентов для конкурентного анализа сайтов...

ПРОБЛЕМА: Агент вернул 4 сайта с оценкой 100% (идеально) и 1 сайт с 0% (провал)...

МОИ ВОПРОСЫ:
1. МЕТРИКИ КАЧЕСТВА АНАЛИЗА
2. СИСТЕМА ВАЛИДАЦИИ РЕЗУЛЬТАТОВ  
3. ТЕХНИЧЕСКИЙ АУДИТ — ЧТО ПРОВЕРЯТЬ
4. АРХИТЕКТУРНЫЕ ПАТТЕРНЫ
5. СПЕЦИФИКА МЕДИЦИНСКИХ САЙТОВ
```

**Ключевые находки из исследования:**

1. **Coverage метрики:**
   - pages_crawled: ≥50
   - templates_covered: ≥5-7 типов
   - cwv_pages_sampled: ≥10-20

2. **Depth метрики:**
   - avg_checks_per_page: ≥15-20 проверок
   - Проверки: CWV, mobile, SEO, accessibility, security, content

3. **Sanity метрики:**
   - score == 100 && issues == 0 → SUSPICIOUS_PERFECT_SCORE
   - На реальных сайтах ВСЕГДА есть проблемы

4. **3-слойная архитектура:**
   - Layer 1: Enhanced Agent (расширенный анализ)
   - Layer 2: QA Validator (автоматическая валидация)
   - Layer 3: Human Operator (финальная проверка)

### Step 3: Deep Audit

**Проверили CI Deep Analyzer по метрикам из исследования:**

**Coverage метрики:**
| Конкурент | Pages | Templates | CWV Sampled |
|-----------|-------|-----------|-------------|
| Tori | 50 ✅ | 4 ⚠️ | 0 ❌ |
| Prof | 50 ✅ | 6 ✅ | 0 ❌ |
| CIDK | 50 ✅ | 2 ❌ | 0 ❌ |
| Frau | 50 ✅ | 5 ✅ | 0 ❌ |

**Depth метрики:**
- **Что проверяется:** title, description, h1, schema (4 метрики)
- **Что НЕ проверяется:** CWV, mobile, accessibility, security, content, technical SEO
- **Checks per page:** 4 (цель: 15-20)
- **Разрыв:** 73-80% проверок отсутствует ❌

**Sanity метрики:**
- 2 из 4 конкурентов = 100% quality ❌
- 0 найденных issues у "идеальных" сайтов ❌
- Нет кросс-проверки с внешними API ❌

**Формула Quality Score:**
```python
# ❌ ТЕКУЩАЯ (неправильная)
quality_score = (title + description + h1 + schema) / 4 * 100

# ✅ ПРАВИЛЬНАЯ (из исследования)
quality_score = weighted_average([
    seo_coverage * 0.15,
    cwv_score * 0.25,
    mobile_score * 0.20,
    accessibility_score * 0.20,
    security_score * 0.10,
    technical_seo * 0.10
])
```

### Step 4: Root Cause Analysis

**Найдено 4 корневых причины:**

1. **CI Scout генерирует URL автоматически**
   - Slugify: "Клиника Юлии Щербатовой" → "doctor-shcherbatova.ru"
   - Не проверяет доступность
   - Не спрашивает пользователя

2. **Нет URL validation между фазами**
   - Phase 1 (Scout) → Phase 5 (Deep Analyzer)
   - Нет проверки URL между фазами

3. **CI Deep Analyzer не спрашивает при ошибках**
   - Если quality_score == 0 → молча возвращает
   - Нарушение Prevention Rule

4. **Агент работает поверхностно**
   - Проверяет только 4 метрики из 15-20
   - Не видит 73-80% проблем

### Tools & Methods Used

- **Audit:** Чтение JSON результатов, сравнение с метриками
- **Research:** Perplexity для поиска best practices
- **Analysis:** Сравнение текущего vs целевого состояния
- **Documentation:** Создание Audit Report и Architecture Decision

### Key Findings

1. **CI Deep Analyzer работает поверхностно** - проверяет только 20-27% необходимых метрик
2. **Quality Score не отражает реальное качество** - это просто % SEO-покрытия
3. **Нет валидации результатов** - агент работает в изоляции, нет кросс-проверок
4. **Подозрительно идеальные результаты** - флаг SUSPICIOUS_PERFECT_SCORE

---

## Solution Design (Проектирование решения)

### Alternatives Considered

**1. Только исправить URL Validator без расширения анализа**
- **Pros:** Быстро (1-2 часа), решает проблему 5-го конкурента
- **Cons:** Не решает проблему поверхностного анализа
- **Why not chosen:** Исправляет симптом, не причину

**2. Сразу переделать CI Deep Analyzer без QA-слоя**
- **Pros:** Проще, меньше кода
- **Cons:** Нет автоматической проверки качества, можем пропустить проблемы
- **Why not chosen:** Нужна валидация, чтобы не повторить ошибку

**3. Построить 3-слойную систему (chosen)**
- **Pros:** Комплексное решение, автоматизация, обучаемость
- **Cons:** Больше кода (2-3 недели), сложнее поддержка
- **Why chosen:** Единственный способ гарантировать качество

### Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     CI Orchestrator                          │
└─────────────────────────────────────────────────────────────┘
                              │
                    ┌─────────┴─────────┐
                    │  Phase 1: Scout   │
                    └─────────┬─────────┘
                              │
                    ┌─────────────────┐
                    │ VALIDATION GATE │
                    │  URL Validator  │
                    └─────────┬─────────┘
                              │
                    ┌─────────┴─────────┐
                    │   Phase 5:        │
                    │ Enhanced Deep     │
                    │    Analyzer       │
                    └─────────┬─────────┘
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
                    ┌─────────────────┐
                    │ VALIDATION GATE │
                    │  QA Validator   │
                    └─────────┬─────────┘
                              │
                    ┌─────────┴─────────┐
                    │                   │
                    ▼                   ▼
            ┌──────────┐        ┌──────────┐
            │    OK    │        │ REJECT   │
            │  Pass    │        │ Ask User │
            └──────────┘        └──────────┘
```

### Implementation Plan

**Phase 0: URL Validator (P0, 1-2 часа) ✅ DONE**
1. Создать CI URL Validator Agent
2. Интегрировать в CI Orchestrator (validation gate перед Phase 5)
3. Протестировать с правильным URL 5-го конкурента

**Phase 1: Enhanced CI Deep Analyzer (P0, 2-3 дня)**
1. Добавить Core Web Vitals (PageSpeed API)
2. Добавить Mobile Usability (Lighthouse)
3. Добавить Accessibility (axe-core)
4. Добавить Security (HTTPS, headers)
5. Изменить формулу Quality Score
6. Добавить детальный отчёт о проблемах

**Phase 2: QA Validator Agent (P0, 1-2 дня)**
1. Создать QA Validator Agent
2. Реализовать Coverage/Depth/Sanity проверки
3. Реализовать External Validation (кросс-проверка с API)
4. Вернуть QA Verdict (OK/SUSPECT/REJECT)

**Phase 3: Integration (P0, 1 день)**
1. Добавить validation gate после Phase 5
2. Логирование QA результатов
3. Метрики QA Validator

**Phase 4-6: Golden Dataset, External API, Dashboard (P1-P2)**

---

## Implementation (Реализация)

### Phase 0: URL Validator ✅ COMPLETED

**What was done:**

1. **Created CI URL Validator Agent** (`ci_url_validator.py`)
   - Проверяет HTTP status, DNS resolution, SSL
   - Интегрирован с Agent Learning (читает lessons)
   - Placeholder для AskUserQuestion (будет реализовано)

2. **Integrated into CI Orchestrator**
   - Validation gate перед Phase 5
   - Работает для tier "deep" и "full"
   - Обновляет payload с validated URLs

3. **Tested with correct URL**
   - Все 5 конкурентов прошли валидацию
   - 5-й конкурент: juliasherbatova.ru ✅
   - Success rate: 100%

**Code Example:**

```python
# ci_url_validator.py
async def _validate_url(self, url: str, name: str) -> Dict[str, Any]:
    """Validate URL accessibility"""
    result = {
        "status": "error",
        "http_status": None,
        "dns_ok": False,
        "ssl_ok": False
    }
    
    # Check DNS
    socket.gethostbyname(parsed.netloc)
    result["dns_ok"] = True
    
    # Check HTTP
    async with session.get(url) as response:
        result["http_status"] = response.status
        if 200 <= response.status < 300:
            result["status"] = "ok"
    
    return result
```

**Challenges:**
- **Challenge:** Task dataclass не имеет поля payload
  - **Solution:** Добавили payload как атрибут после создания Task

- **Challenge:** TaskResult требует error parameter
  - **Solution:** Добавили error=None для успешных результатов

**Results:**
- ✅ URL Validator работает
- ✅ 100% validation rate на тесте
- ✅ Интеграция с CI Orchestrator работает

### Phase 1: Enhanced CI Deep Analyzer (PLANNED)

**What needs to be done:**

1. **Core Web Vitals Integration**
   ```python
   # Add PageSpeed Insights API
   async def _analyze_cwv(self, url: str) -> Dict:
       psi_result = await fetch_pagespeed(url)
       return {
           "lcp": psi_result["lcp"],
           "inp": psi_result["inp"],
           "cls": psi_result["cls"],
           "score": calculate_cwv_score(psi_result)
       }
   ```

2. **Mobile Usability**
   ```python
   # Add Lighthouse mobile mode
   async def _analyze_mobile(self, url: str) -> Dict:
       lighthouse_result = await run_lighthouse(url, mobile=True)
       return {
           "viewport_ok": check_viewport(lighthouse_result),
           "responsive": check_responsive(lighthouse_result),
           "score": lighthouse_result["mobile_score"]
       }
   ```

3. **Accessibility**
   ```python
   # Add axe-core integration
   async def _analyze_accessibility(self, url: str) -> Dict:
       axe_result = await run_axe_core(url)
       return {
           "wcag_violations": axe_result["violations"],
           "score": calculate_a11y_score(axe_result)
       }
   ```

4. **New Quality Score Formula**
   ```python
   def calculate_quality_score(self, analysis: Dict) -> float:
       return weighted_average([
           analysis["seo"]["score"] * 0.15,
           analysis["cwv"]["score"] * 0.25,
           analysis["mobile"]["score"] * 0.20,
           analysis["accessibility"]["score"] * 0.20,
           analysis["security"]["score"] * 0.10,
           analysis["technical"]["score"] * 0.10
       ])
   ```

**Expected Results:**
- CI Deep Analyzer проверяет 15-20 метрик (было 4)
- Quality Score отражает реальное качество
- Детальный отчёт с issues (critical/major/minor)

---

## Results (Результаты)

### Metrics Before (Phase 0)

**Coverage:**
- pages_crawled: 50 ✅
- templates_covered: 2-6 ⚠️
- cwv_pages_sampled: 0 ❌

**Depth:**
- avg_checks_per_page: 4 ❌ (цель: 15-20)
- CWV checks: 0 ❌
- Mobile checks: 0 ❌
- Accessibility checks: 0 ❌

**Sanity:**
- Perfect scores: 2 из 4 ❌
- Issues found: 0-3 ❌
- External validation: 0 ❌

**URL Validation:**
- 5th competitor: 0% ❌ (wrong URL)

### Metrics After (Phase 0 completed)

**URL Validation:**
- 5th competitor: 100% ✅ (correct URL)
- All competitors: 100% validation rate ✅
- Validation gate: Working ✅

**Coverage/Depth/Sanity:**
- Not yet improved (Phase 1 pending)

### Success Criteria

**Phase 0 (URL Validator):**
- ✅ URL Validator создан и работает
- ✅ Интеграция с CI Orchestrator работает
- ✅ 5-й конкурент проходит валидацию
- ✅ 100% validation rate на тесте

**Phase 1 (Enhanced Analyzer) - PENDING:**
- ⏳ CI Deep Analyzer проверяет ≥15 метрик
- ⏳ Quality Score учитывает CWV, mobile, accessibility
- ⏳ Детальный отчёт с issues

---

## Lessons Learned (Уроки)

### What Worked Well

1. **Research-driven approach**
   - Perplexity дал конкретные метрики и архитектуру
   - Исследование заняло 30 минут, сэкономило недели разработки

2. **Audit before implementation**
   - Глубокий аудит показал реальные проблемы
   - Избежали исправления симптомов вместо причин

3. **Incremental implementation**
   - Phase 0 (URL Validator) за 1-2 часа
   - Быстрая победа, подтверждение подхода

4. **Agent Learning integration**
   - URL Validator читает lessons перед работой
   - Автоматическое применение Prevention Rules

### What Didn't Work

1. **Слепое доверие результатам агента**
   - Приняли 100% quality как истину
   - Не проверили качество работы агента
   - **How to avoid:** Всегда проверять подозрительные результаты

2. **Отсутствие validation gates**
   - Агенты работали в изоляции
   - Нет проверок между фазами
   - **How to avoid:** Добавлять validation gates перед дорогими операциями

3. **Поверхностный анализ**
   - Проверяли только 20-27% метрик
   - Не видели реальные проблемы
   - **How to avoid:** Использовать метрики из исследований

### Prevention Rules

1. **ALWAYS: Validate URLs before expensive operations**
   - Before Phase 5 (Deep Analysis) → validate all URLs
   - Before any web crawling → check URL accessibility
   - Before any expensive operation → validate input data

2. **NEVER: Return 0% or empty results without asking user**
   - When quality_score < 10 → ask user what to do
   - When analysis fails → explain why and offer options
   - When URL validation fails → ask user for correct URL

3. **NEVER: Auto-generate URLs without validation**
   - Try to find real URL via WebSearch first
   - If not found → ask user for URL
   - Always validate URL accessibility before saving

4. **CHECK: Agent results for suspicious patterns**
   - score == 100 && issues == 0 → SUSPICIOUS_PERFECT_SCORE
   - All results in [95-100] range → LOW_VARIANCE_BATCH
   - time_spent < expected → TOO_FAST_TO_BE_TRUE

5. **ALWAYS: Add validation gates before expensive operations**
   - Between Phase 1 and Phase 5 → URL validation
   - Between Phase 5 and Phase 10 → Quality validation
   - Before any expensive operation → Input validation

### Applicable Patterns

**Pattern 1: Multi-layer Validation**
- **When to use:** When agent results are critical for business decisions
- **How:** Layer 1 (Enhanced Agent) → Layer 2 (QA Validator) → Layer 3 (Human)
- **Why:** Catches errors at multiple levels, reduces false positives

**Pattern 2: Research-Driven Design**
- **When to use:** When building complex systems without prior experience
- **How:** Research best practices → Audit current state → Design solution
- **Why:** Avoids reinventing the wheel, learns from others' mistakes

**Pattern 3: Incremental Implementation**
- **When to use:** When solution is large (2-3 weeks)
- **How:** Break into phases, implement P0 first, validate approach
- **Why:** Quick wins, early feedback, reduced risk

---

## Teaching Points (Обучающие моменты)

### For Magisters

1. **Always validate subagent results**
   - Don't trust results blindly
   - Check for suspicious patterns
   - Add validation gates between phases

2. **Research before building**
   - Use Perplexity/WebSearch for best practices
   - Learn from others' mistakes
   - Don't reinvent the wheel

3. **Audit before fixing**
   - Understand root cause before implementing
   - Measure current state vs target state
   - Fix causes, not symptoms

### For Subagents

1. **Never fail silently**
   - Always ask user when problems occur
   - Explain what went wrong
   - Offer options (retry, skip, fix)

2. **Integrate with Agent Learning**
   - Read lessons before starting task
   - Apply Prevention Rules automatically
   - Record successes and failures

3. **Validate inputs before expensive operations**
   - Check URL accessibility before crawling
   - Validate data quality before analysis
   - Ask user when uncertain

### For Operator

1. **Question suspicious results**
   - 100% quality + 0 issues = suspicious
   - All results in narrow range = suspicious
   - Too fast completion = suspicious

2. **Add validation gates**
   - Between phases with expensive operations
   - Before critical business decisions
   - When data quality is important

3. **Use research for complex problems**
   - Perplexity for best practices
   - WebSearch for specific solutions
   - Learn from industry standards

---

## Practice Exercises (Упражнения)

### Exercise 1: Audit Your Agent

**Task:** 
Выбери любого агента в системе и проведи аудит по метрикам из этого кейса:
- Coverage: сколько данных собирает?
- Depth: сколько проверок делает?
- Sanity: есть ли подозрительные паттерны?

**Expected Result:** 
Отчёт с метриками и рекомендациями по улучшению

**Hints:** 
- Используй метрики из исследования Perplexity
- Сравни текущее состояние с целевым
- Найди 3-5 конкретных проблем

### Exercise 2: Design Validation Gate

**Task:**
Спроектируй validation gate для любой фазы CI системы:
- Какие проверки нужны?
- Какие флаги использовать?
- Когда спрашивать пользователя?

**Expected Result:**
Архитектура validation gate с примерами кода

**Hints:**
- Используй паттерн из этого кейса
- Добавь Coverage/Depth/Sanity проверки
- Не забудь про user interaction

### Exercise 3: Implement Prevention Rules

**Task:**
Возьми любого агента и добавь Prevention Rules из этого кейса:
- ALWAYS: Validate before expensive operations
- NEVER: Return empty results without asking
- CHECK: Results for suspicious patterns

**Expected Result:**
Агент с интегрированными Prevention Rules

**Hints:**
- Используй Agent Learning для чтения lessons
- Добавь проверки перед execute_task()
- Добавь user interaction при проблемах

---

## Related Materials

### Documents Created Today

**Decisions:**
- [CI URL Validation Problem](../../decisions/2026-05-05-16-42-ci-url-validation-problem.md)
- [CI Deep Analyzer Audit Report](../../decisions/2026-05-05-17-09-ci-deep-analyzer-audit-report.md)
- [CI Validation System Architecture](../../decisions/2026-05-05-17-11-ci-validation-system-architecture.md)

**Lessons:**
- [CI URL Validation Silent Failure](../../wiki/lessons/2026-05-05-ci-url-validation-silent-failure.md)

**Feedback:**
- [CI Validation Rules](../../../.claude/memory/feedback_ci_validation.md)

**Research:**
- [Perplexity Research](../../../inbox/Мне нужно построить систему валидации результатов.md)

### Code Created Today

**Agents:**
- `AIM/src/aim/subagents/competitive_intel/agents/ci_url_validator.py`

**Orchestrator:**
- `AIM/src/aim/subagents/competitive_intel/orchestrator/ci_orchestrator.py` (updated)

**Tests:**
- `AIM/tests/test_ci_url_validator.py`

**Core:**
- `AIM/src/aim/core/agent_learning.py` (created earlier)

### External Resources

**Research:**
- [Perplexity: AI Agent Quality Validation](https://www.perplexity.ai/)
- [Technical SEO Audit Checklist](https://customwebaudits.com/technical-seo-audit-checklist/)
- [Core Web Vitals Guide](https://web.dev/vitals/)
- [WCAG 2.1 Guidelines](https://www.w3.org/WAI/WCAG21/quickref/)

**Tools:**
- [PageSpeed Insights API](https://developers.google.com/speed/docs/insights/v5/get-started)
- [Lighthouse](https://github.com/GoogleChrome/lighthouse)
- [axe-core](https://github.com/dequelabs/axe-core)

---

## Discussion Questions

1. **Почему мы не заметили проблему сразу?**
   - Что должно было насторожить?
   - Какие метрики нужно проверять автоматически?

2. **Как избежать подобных проблем в будущих агентах?**
   - Какие validation gates добавить?
   - Какие метрики отслеживать?

3. **Стоит ли всегда делать research перед реализацией?**
   - Когда research необходим?
   - Когда можно обойтись без него?

4. **Как балансировать между скоростью и качеством?**
   - Когда Quality Over Speed?
   - Когда можно пожертвовать качеством?

5. **Нужен ли QA Validator для всех агентов?**
   - Для каких агентов критично?
   - Для каких можно обойтись?

---

## Timeline

**Total Time:** ~6 hours

- **Problem Discovery:** 10 min (user question)
- **Research:** 30 min (Perplexity)
- **Audit:** 1 hour (deep analysis)
- **Solution Design:** 1 hour (architecture)
- **Implementation Phase 0:** 2 hours (URL Validator)
- **Testing:** 30 min
- **Documentation:** 1 hour (this case)

---

## Next Steps

**Immediate (P0):**
1. Implement Phase 1: Enhanced CI Deep Analyzer (2-3 дня)
2. Implement Phase 2: QA Validator Agent (1-2 дня)
3. Implement Phase 3: Integration (1 день)

**Short-term (P1):**
4. Create Golden Dataset (1-2 дня)
5. Integrate External APIs (2-3 дня)

**Long-term (P2):**
6. Build Operator Dashboard (2-3 дня)

**Total:** 9-14 дней (2-3 недели)

---

**Author:** meAI Architect  
**Reviewers:** TBD  
**Last Updated:** 2026-05-05  
**Status:** Phase 0 completed, Phase 1-6 pending
