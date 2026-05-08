---
title: "Teaching Cases Index"
created: "2026-05-05"
updated: "2026-05-05"
total_cases: 1
status: active
---

# Teaching Cases Index

Структурированная библиотека обучающих кейсов для Teacher Agent.

## Purpose

Teaching Cases создаются для:
1. **Обучения Magisters** - как решать сложные проблемы
2. **Обучения Subagents** - как применять паттерны и правила
3. **Обучения Operator** - как координировать агентов
4. **Передачи знаний** - от опытных агентов к новым

## How to Use

### For Teacher Agent
1. Читай кейсы перед обучением Magisters/Subagents
2. Используй Practice Exercises для проверки понимания
3. Адаптируй Teaching Points под конкретного ученика
4. Отслеживай прогресс через Discussion Questions

### For Humans
1. Читай кейсы для понимания системы
2. Используй как документацию реальных решений
3. Применяй паттерны в новых задачах
4. Обновляй кейсы при изменении системы

### For Agents
1. Читай кейсы перед похожими задачами
2. Применяй Prevention Rules из кейсов
3. Используй паттерны из Solution Design
4. Учись на ошибках из Lessons Learned

## Case Structure

Каждый Teaching Case содержит:
- **Metadata:** difficulty, duration, skills, prerequisites
- **Executive Summary:** краткое описание (2-3 предложения)
- **The Problem:** что случилось, симптомы, impact
- **Investigation:** как исследовали, что нашли
- **Solution Design:** альтернативы, архитектура, план
- **Implementation:** что сделали, код, результаты
- **Results:** метрики до/после, success criteria
- **Lessons Learned:** что работало, что нет, правила
- **Teaching Points:** для Magisters, Subagents, Operator
- **Practice Exercises:** задания для проверки понимания
- **Related Materials:** документы, код, ресурсы
- **Discussion Questions:** вопросы для обсуждения

## Difficulty Levels

- **Beginner:** Базовые концепции, простые задачи (1-2 часа)
- **Intermediate:** Средняя сложность, несколько компонентов (2-4 часа)
- **Advanced:** Сложные системы, архитектура (4-6 часов)
- **Expert:** Комплексные решения, исследования (6+ часов)

## Skills Taxonomy

### Problem Solving
- Root cause analysis
- System auditing
- Research-driven design
- Incremental implementation

### Architecture
- Multi-layer validation
- Validation gates
- Agent coordination
- Data flow design

### Quality
- Metrics definition
- Quality assurance
- Testing strategies
- Performance optimization

### Integration
- Agent Learning
- Lessons Learned
- Prevention Rules
- External APIs

## All Teaching Cases

### 2026-05-05

#### 1. [CI URL Validation & Quality Audit](2026-05-05-ci-validation-quality-audit.md)
- **Difficulty:** Advanced
- **Duration:** 4-6 hours
- **Skills:** Problem diagnosis, System auditing, Multi-layer validation, Agent learning
- **Status:** Phase 0 completed, Phase 1-6 pending
- **Summary:** CI Deep Analyzer вернул подозрительные результаты (4×100%, 1×0%). Глубокий аудит показал поверхностный анализ (20-27% метрик). Спроектировали 3-слойную систему валидации, реализовали URL Validator. Результат: 100% validation rate, план улучшения на 2-3 недели.

---

## Statistics

- **Total cases:** 1
- **By difficulty:**
  - Beginner: 0
  - Intermediate: 0
  - Advanced: 1
  - Expert: 0

- **By status:**
  - Completed: 0
  - In Progress: 1
  - Planned: 0

- **By skills:**
  - Problem diagnosis: 1
  - System auditing: 1
  - Multi-layer validation: 1
  - Agent learning: 1

---

## How to Create a Teaching Case

1. **Identify valuable experience**
   - Complex problem solved
   - Architectural decision made
   - Pattern discovered
   - Mistake learned from

2. **Use the template**
   - Copy `TEMPLATE.md`
   - Fill all sections
   - Add code examples
   - Include metrics

3. **Add metadata**
   - Difficulty level
   - Duration estimate
   - Skills taught
   - Prerequisites

4. **Create exercises**
   - 2-3 practice exercises
   - Clear expected results
   - Helpful hints

5. **Add to INDEX**
   - Update this file
   - Add to appropriate section
   - Update statistics

6. **Review and refine**
   - Check completeness
   - Verify code examples
   - Test exercises
   - Get feedback

---

## Related Systems

### Lessons Learned
- **Purpose:** Record specific mistakes and prevention rules
- **Location:** `obsidian/architect/wiki/lessons/`
- **Format:** Problem → Why → Solution → Prevention Rules
- **Usage:** Agents read before tasks

### Feedback Memory
- **Purpose:** Store user feedback and preferences
- **Location:** `.claude/memory/feedback_*.md`
- **Format:** Rule → Why → How to apply
- **Usage:** Persistent across sessions

### Agent Learning
- **Purpose:** Agents learn from failures and successes
- **Location:** `AIM/src/aim/core/agent_learning.py`
- **Format:** Code + JSON history
- **Usage:** Automatic lesson application

### Teaching Cases (this)
- **Purpose:** Comprehensive learning materials
- **Location:** `obsidian/architect/teaching-cases/`
- **Format:** Full case study with exercises
- **Usage:** Teacher Agent training

---

## Future Cases (Planned)

### High Priority
- [ ] **Enhanced CI Deep Analyzer Implementation** (when Phase 1 completed)
- [ ] **QA Validator Agent Design** (when Phase 2 completed)
- [ ] **Multi-Agent Coordination** (from Operator experience)

### Medium Priority
- [ ] **Agent Learning Integration** (from multiple agents)
- [ ] **External API Integration** (from Phase 5)
- [ ] **Golden Dataset Creation** (from Phase 4)

### Low Priority
- [ ] **Operator Dashboard Design** (from Phase 6)
- [ ] **Performance Optimization** (when needed)
- [ ] **Error Handling Patterns** (from production)

---

## Maintenance

### Monthly Review
- Check if cases are still relevant
- Update with new learnings
- Archive obsolete cases
- Add new cases from recent work

### Quarterly Audit
- Review all cases for accuracy
- Update code examples
- Refresh external links
- Gather feedback from users

### Annual Cleanup
- Archive old cases
- Consolidate similar cases
- Update taxonomy
- Refresh statistics

---

**Last Updated:** 2026-05-05  
**Maintainer:** meAI Architect  
**Next Review:** 2026-06-05
