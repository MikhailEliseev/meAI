# Teacher Agent v2.0 - Product Brief

**Date:** 2026-05-13  
**Feature:** Teacher Agent v2.0 - Autonomous Deep Analysis & Full Adoption  
**Status:** Awaiting Approval

---

## Product Summary

**Что строим:**
- Teacher Agent v2.0 — полностью автономная система глубокого анализа и автоматического внедрения лучших практик из GitHub
- Upgrade от v1.0 (pattern detection) к v2.0 (autonomous deep analysis + full adoption)

**Основные возможности:**
1. **Autonomous Decision Making** — Teacher САМ решает Full/Partial/Custom/Reject без user approval
2. **Adoption Sandbox** — изолированное тестирование GitHub решений перед внедрением
3. **Intelligent Analysis** — глубокий анализ архитектуры, кода, тестов, метрик
4. **Automated Validation** — полный test suite + метрики + безопасность перед adoption
5. **Self-Learning** — Teacher учится на результатах и улучшает решения

**Проблемы, которые решаем:**
- ❌ v1.0 только детектирует паттерны, не анализирует качество
- ❌ Нет понимания, подходит ли GitHub решение под наши задачи
- ❌ Ручной процесс внедрения (долго, ошибки)
- ❌ Нет безопасности (можем сломать production)
- ❌ Требуется manual approval (замедляет процесс)
- ✅ v2.0 анализирует архитектуру целиком, принимает умные решения АВТОНОМНО, внедряет автоматически с гарантиями безопасности

**НЕ в scope:**
- Manual approval workflow (Teacher решает сам)
- Автоматическое внедрение без валидации (слишком рискованно)
- LibCST-based AST engine (over-engineered для solo developer)
- Feature flags для каждого adoption (начнём с sandbox, добавим позже если нужно)
- Поддержка других языков кроме Python (пока только Python)

**Ключевые решения:**
1. **Autonomous Workflow:** Analyze → Decide → Validate → Adopt (без user approval)
2. **Decision Criteria:** Quality score + Fit score + Risk assessment → автоматическое решение
3. **Validation Bar:** Tests pass + metrics improve + security checks (balanced подход)
4. **Safety First:** Sandbox → validate → auto-adopt if safe → rollback if issues
5. **Medical Context:** Security 2x weight, compliance checks обязательны

**Defaults assumed:**
- Git worktree для каждого adoption attempt (изоляция)
- Full test suite запускается автоматически
- Adoption report генерируется всегда
- Rollback доступен через `teacher undo`
- Teacher логирует все решения для audit trail

---

## Problem Statement

Teacher Agent v1.0 детектирует отсутствующие паттерны, но не понимает, лучше ли GitHub решение чем наше. Это приводит к ручному анализу (2-4 часа на adoption) и риску внедрения неподходящих решений в medical marketing систему с zero-error tolerance.

**Дополнительная проблема:** Manual approval замедляет процесс обучения системы. Teacher должен быть автономным, чтобы непрерывно улучшать субагенты без человеческого вмешательства.

---

## Jobs to be Done

- **When** я нахожу интересное GitHub решение, **I want** Teacher автономно понял подходит ли оно под мои задачи, **so I can** не тратить время на ручной анализ
- **When** Teacher решает внедрить GitHub паттерн, **I want** он протестировал его в изоляции автоматически, **so I can** быть уверен что production не сломается
- **When** adoption проходит валидацию, **I want** Teacher автоматически применил изменения, **so I can** не тратить время на ручную работу
- **When** adoption оказывается неудачным, **I want** Teacher автоматически откатил изменения, **so I can** минимизировать downtime
- **When** Teacher принимает решения, **I want** видеть audit trail всех решений, **so I can** понимать почему он сделал тот или иной выбор

---

## User Stories

1. **As a** solo developer, **I want** Teacher Agent анализировал и внедрял GitHub решения автономно, **so that** я не трачу 2-4 часа на каждый паттерн

2. **As a** medical marketing agency owner, **I want** все adoptions проходили через sandbox с полной валидацией автоматически, **so that** я уверен что production не сломается

3. **As a** developer auditing system, **I want** видеть adoption reports с обоснованием решений Teacher, **so that** я понимаю что именно изменилось и почему

4. **As a** busy developer, **I want** Teacher автоматически применял safe adoptions без моего участия, **so that** система непрерывно улучшается

5. **As a** compliance-focused developer, **I want** audit trail всех adoptions в Obsidian, **so that** я могу показать историю изменений при аудите

---

## Success Criteria

1. **Adoption time:** Снижение с 2-4 часов до 15-30 минут (полностью автоматически)
2. **Failed adoptions:** <5% (vs ~30% при ручном подходе)
3. **Confidence:** 90%+ adoptions проходят валидацию с первого раза
4. **Safety:** 0 production incidents из-за Teacher Agent adoptions
5. **Autonomy:** 95%+ adoptions без human intervention
6. **ROI:** 10+ successful adoptions в первый месяц

---

## Edge Cases

### Happy Path (Fully Autonomous)

1. Teacher находит GitHub решение с circuit breaker
2. Анализирует архитектуру (Decision Matrix: score 85/100 → Full adoption)
3. Создаёт sandbox, применяет паттерн, запускает тесты
4. Все тесты pass, metrics improve (test coverage +15%, complexity -10%)
5. Security checks pass, compliance validated
6. **Teacher автоматически merges в main** (без user approval)
7. Генерирует adoption report в Obsidian
8. Отправляет notification пользователю: "Adopted circuit breaker from repo X"

### Failure Mode 1: Tests Fail (Auto-Rollback)

1. Teacher создаёт sandbox, применяет паттерн
2. Tests fail (breaking change detected)
3. **Teacher автоматически rollback sandbox**
4. Генерирует failure analysis
5. Сохраняет в Obsidian: "REJECTED - tests failed, reason: X"
6. Notification пользователю: "Rejected adoption from repo Y, reason: tests failed"

### Failure Mode 2: Metrics Degrade (Auto-Reject)

1. Tests pass, но metrics worse (complexity +20%, performance -15%)
2. **Teacher автоматически rejects adoption** (metrics degradation threshold exceeded)
3. Генерирует analysis: "REJECTED - metrics degraded"
4. Сохраняет в Obsidian с reasoning
5. Notification пользователю: "Rejected adoption, metrics degraded"

### Failure Mode 3: Semantic Mismatch (Auto-Adapt)

1. GitHub solution uses 5s timeout, наш use case needs 30s
2. Decision Matrix catches это (compatibility score low)
3. **Teacher автоматически adapts timeout parameter** (Partial adoption)
4. Validates adapted version в sandbox
5. If validation pass → auto-merge
6. Генерирует report: "ADAPTED - changed timeout 5s → 30s"

### Edge Case 4: Security Risk Detected (Auto-Reject)

1. Teacher анализирует GitHub solution
2. Находит security vulnerability (hardcoded credentials, SQL injection)
3. **Teacher автоматически rejects** (security score below threshold)
4. Генерирует security report
5. Notification пользователю: "REJECTED - security risk detected"

### Edge Case 5: Better Third-Party Agent Found (Auto-Adopt)

1. Teacher анализирует GitHub solution
2. Находит сторонний агент лучше нашего (higher quality score)
3. Анализирует совместимость с нашей системой
4. **Teacher автоматически adopts сторонний агент** (если validation pass)
5. Интегрирует в нашу систему
6. Генерирует report: "REPLACED our agent with third-party agent X"

---

## Autonomous Decision Framework

**Decision Criteria (автоматические):**

1. **Quality Score (0-100):**
   - Architecture: modularity, testability, maintainability
   - Code Quality: complexity, documentation, patterns
   - Test Coverage: unit, integration, e2e
   - Threshold: ≥70 для adoption

2. **Fit Score (0-100):**
   - Task Match: соответствие задаче субагента
   - Integration Effort: сложность интеграции
   - Dependency Compatibility: совместимость зависимостей
   - Threshold: ≥70 для adoption

3. **Risk Score (0-100):**
   - Security: vulnerabilities, hardcoded secrets
   - Compliance: HIPAA, medical marketing requirements
   - Breaking Changes: impact на существующий код
   - Threshold: ≤30 для adoption (low risk)

**Automatic Decision Rules:**

```python
if quality_score >= 80 and fit_score >= 80 and risk_score <= 20:
    decision = "FULL_ADOPTION"  # Auto-merge after validation
elif quality_score >= 70 and fit_score >= 70 and risk_score <= 30:
    decision = "PARTIAL_ADOPTION"  # Auto-adapt + validate + merge
elif quality_score >= 60 and fit_score >= 60 and risk_score <= 40:
    decision = "CUSTOM_DEVELOPMENT"  # Use as reference, build custom
else:
    decision = "REJECT"  # Not suitable, log reasoning
```

**Validation Gates (автоматические):**

1. **Sandbox Tests:** All tests must pass
2. **Metrics Check:** Metrics must improve or stay same
3. **Security Scan:** No vulnerabilities detected
4. **Compliance Check:** HIPAA requirements met
5. **Integration Test:** Works with Event Bus + Obsidian

**Auto-Merge Conditions:**

- All validation gates pass
- Risk score ≤ 30
- No breaking changes detected
- Rollback plan available

---

**Created:** 2026-05-13  
**Author:** meAI Architect (via Claude Sonnet 4)  
**Status:** 📋 Awaiting Product Approval
