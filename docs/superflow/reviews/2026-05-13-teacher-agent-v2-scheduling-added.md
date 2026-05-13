# Teacher Agent v2.0 - Scheduling & Audit System Added ✅

**Date:** 2026-05-13  
**Status:** COMPLETE

---

## Summary

Добавил критически важные компоненты для автономной работы Teacher Agent: систему планирования, аудита и триггеров.

**Spec Size:**
- Before: 4508 lines, 150 KB
- After: 5139 lines, 173 KB
- Added: +631 lines, +23 KB

**Time:** ~20 minutes

---

## User Requirement

**Вопрос пользователя:**
> "Как часто активируется и запускается teacher для обучения всей системы? Как часто он вызывается вручную по команде, или каким образом? Для того чтобы:
> 1. Проаудировать всю систему на предмет того, кто из его учеников в классе.
> 2. Прорисовать и сделать исследование, что есть на рынке.
> Кстати, если один из учеников заболел, убежал или отчислился, то что тут делать вообще? Это вопрос."

**Проблема:** Текущая спецификация описывала только как Teacher учит конкретного субагента, но не отвечала на вопросы:
- Когда и как часто запускается Teacher?
- Как он аудирует всю систему?
- Что делать с "заболевшими/отчисленными" субагентами?
- Как приоритизировать обучение?

---

## Solution: 3 New Components

### 1. Section 1.4: Triggers & Workflow

**Автоматические триггеры:**

```python
# Scheduled (cron-like)
- Каждые 2 недели: Полный цикл обучения всех субагентов
- Каждую неделю: GitHub market research (новые топовые репо)
- Каждый день: Health check всех субагентов

# Event-driven
- Новый субагент создан → Initial research + teaching
- Субагент показывает плохие метрики → Check for better solutions
- GitHub webhook: новый релиз → Analyze changes
- Субагент "заболел" (код удалён) → Handle via SystemAuditor
```

**Ручные триггеры:**

```bash
# Полный цикл для всех
python scripts/teacher_cli.py run-learning-cycle --strategy sequential

# Аудит системы
python scripts/teacher_cli.py audit-system

# Обучение конкретного субагента
python scripts/teacher_cli.py teach <subagent_name> --depth deep

# Исследование рынка
python scripts/teacher_cli.py research-market --category seo
```

**Complete Workflow:**

```
TRIGGER (auto/manual)
  ↓
1. SYSTEM AUDIT (SystemAuditor)
   - Discover all subagents
   - Check health (healthy/degraded/missing/deprecated)
   - Check last taught date
   - Check performance metrics
   - Handle missing/deprecated
  ↓
2. LEARNING PLAN (LearningScheduler)
   - Prioritize (P1-P4)
   - Choose strategy (sequential/parallel/batch)
   - Estimate time & cost
  ↓
3. MARKET RESEARCH (for each subagent)
   - Deep research (Exa)
   - GitHub search (API + Exa)
   - Rank repos
  ↓
4. TEACH (for each subagent)
   - Clone → Analyze → Extract → Compare
   - Select → Teach → Validate
  ↓
5. REPORT
   - Update Obsidian vault
   - Send summary to Operator
   - Schedule next learning cycle
```

### 2. Section 2.1: SystemAuditor

**Purpose:** Аудит всех субагентов, обработка "заболевших/отчисленных".

**Key Features:**

**Discovery:**
- Находит всех субагентов из registry, specs, Obsidian vaults
- Проверяет существование кода
- Читает метаданные

**Health Check:**
```python
@dataclass
class SubagentHealth:
    name: str
    status: str                    # "healthy" | "degraded" | "missing" | "deprecated"
    last_taught: datetime | None
    performance_metrics: dict
    needs_update: bool
    priority: int                  # 1-5 (1 = critical)
    reason: str
```

**Status Classification:**
- **healthy**: Работает хорошо, обучен недавно
- **degraded**: Работает, но метрики падают или давно не обучался
- **missing**: Код отсутствует (удалён/переименован)
- **deprecated**: Помечен как устаревший

**Handling Missing Subagents:**

```python
async def _handle_missing_subagent(self, subagent: SubagentHealth):
    """
    Субагент "отчислился" (код удалён/переименован).
    
    Actions:
    1. Check git history - was it renamed?
    2. If renamed → update registry
    3. If deleted → mark as deprecated
    4. If critical → alert user via Operator
    """
    
    git_log = await self._check_git_history(subagent.name)
    
    if git_log.get("renamed_to"):
        # Переименован → обновить registry
        await self.obsidian.log(f"Subagent renamed: {subagent.name} → {new_name}")
    
    elif git_log.get("deleted"):
        # Удалён → пометить deprecated
        await self.obsidian.log(f"Subagent deleted: {subagent.name}")
        
        # Если критический → алерт
        if subagent.name in self.critical_subagents:
            await self.event_bus.publish(Event(
                type="teacher.critical_subagent_missing",
                priority=Priority.P0,
                data={"message": f"🚨 Critical subagent {subagent.name} was deleted!"}
            ))
```

**CLI Output Example:**

```
╔═══════════════════════════════════════════════════════════╗
║  System Audit Report - 2026-05-13 17:15                  ║
╚═══════════════════════════════════════════════════════════╝

Total subagents: 25
✅ Healthy: 20
⚠️  Degraded: 3
   - keyword_research (not taught for 45 days)
   - content_gap_analysis (high error rate: 12%)
   - ads_budget_optimizer (not taught for 35 days)
❌ Missing: 1
   - old_analytics_agent (deleted)
🗑️  Deprecated: 1
   - legacy_seo_agent

Priority Queue (needs teaching):
1. [P1] content_gap_analysis (high error rate)
2. [P2] keyword_research (not taught for 45 days)
3. [P2] ads_budget_optimizer (not taught for 35 days)
4. [P3] technical_seo (routine update)
5. [P3] competitor_analyzer (routine update)
```

### 3. Section 2.2: LearningScheduler

**Purpose:** Планирование и приоритизация обучения на основе аудита.

**Priorities:**

```python
# P1 (CRITICAL): Degraded + critical for business
- High error rate
- System failures
- Critical subagent down

# P2 (HIGH): Not taught for >4 weeks
- Routine updates needed
- Performance degrading

# P3 (MEDIUM): New top repos on GitHub
- New best practices available
- Better solutions found

# P4 (LOW): Optional improvements
- Nice-to-have features
- Minor optimizations
```

**Strategies:**

```python
# Sequential: Teach one by one (safe, slow)
- Best for: Critical updates
- Risk: Low
- Time: Longest

# Parallel: Teach multiple in parallel (fast, risky)
- Best for: Independent subagents
- Risk: Medium
- Time: Shortest

# Batch: Group by category (SEO, Content, Ads)
- Best for: Related subagents
- Risk: Low-Medium
- Time: Medium
```

**Learning Plan Output:**

```python
@dataclass
class LearningPlan:
    created_at: datetime
    strategy: str                   # "sequential" | "parallel" | "batch"
    total_subagents: int
    total_estimated_time: int       # Minutes
    total_estimated_cost: float     # USD
    tasks: list[LearningTask]
```

**CLI Output Example:**

```
╔═══════════════════════════════════════════════════════════╗
║  Learning Plan Created - 2026-05-13 17:20                 ║
╚═══════════════════════════════════════════════════════════╝

Strategy: sequential
Total subagents: 5
Estimated time: 3 hours 15 minutes
Estimated cost: $9.50

Tasks:
1. [P1] content_gap_analysis (deep, 60 min, $3.00)
2. [P2] keyword_research (standard, 30 min, $1.50)
3. [P2] ads_budget_optimizer (standard, 30 min, $1.50)
4. [P3] technical_seo (quick, 15 min, $0.50)
5. [P3] competitor_analyzer (quick, 15 min, $0.50)

Plan saved to: obsidian/teacher/wiki/projects/learning-plans/2026-05-13.md

Execute plan? (y/n)
```

---

## Updated Architecture

```
Teacher Agent v2.0 Complete Workflow:

TRIGGER (auto/manual) ⭐ NEW
  ↓
SystemAuditor ⭐ NEW
  ↓
LearningScheduler ⭐ NEW
  ↓
ResearchOrchestrator (Section 2.0)
  ↓
SkillExtractionOrchestrator (Section 2.3)
  ↓
AdoptionDecisionMaker (Section 4)
  ↓
FullAdopter (Section 5)
  ↓
HealthMonitor (Section 9)
```

---

## Frequency & Cost Estimates

**Full Learning Cycle (all subagents):**
- Frequency: Every 2 weeks (automatic)
- Duration: 2-4 hours (depends on # of subagents)
- Cost: $5-15 (depends on research depth)

**Single Subagent Teaching:**
- Duration: 15-30 minutes
- Cost: $1.50-3.00 (standard/deep research)

**Daily Health Check:**
- Duration: 5 minutes
- Cost: $0 (no external APIs)

**Weekly Market Research:**
- Duration: 30-60 minutes
- Cost: $3-6 (GitHub + Exa search)

---

## Key Benefits

**1. Full Autonomy:**
- Teacher работает по расписанию без ручного запуска
- Автоматический аудит каждые 2 недели
- Автоматическое обучение по приоритетам

**2. System Visibility:**
- Всегда знаешь состояние всех субагентов
- Видишь кто "здоров", кто "болен", кто "отчислен"
- Priority queue для обучения

**3. Smart Prioritization:**
- P1: Критические проблемы (высокий error rate)
- P2: Давно не обучались (>4 недели)
- P3: Routine updates
- P4: Optional improvements

**4. Handling Edge Cases:**
- Субагент удалён → проверка git history → rename/deprecate
- Субагент критический → алерт через Operator
- Субагент переименован → обновление registry

**5. Cost Control:**
- Оценка стоимости перед обучением
- Выбор research depth (quick/standard/deep)
- Batch processing для экономии

---

## CLI Commands Summary

```bash
# Full workflow
python scripts/teacher_cli.py run-learning-cycle --strategy sequential

# Individual steps
python scripts/teacher_cli.py audit-system
python scripts/teacher_cli.py create-learning-plan --strategy sequential
python scripts/teacher_cli.py execute-plan <plan_file>

# Single subagent
python scripts/teacher_cli.py teach <subagent_name> --depth deep
python scripts/teacher_cli.py check-health <subagent_name>

# Market research
python scripts/teacher_cli.py research-market --category seo
```

---

## Integration with Existing Components

**SystemAuditor → LearningScheduler:**
- Audit report → Learning plan
- Health status → Priority assignment
- Missing subagents → Handled before planning

**LearningScheduler → ResearchOrchestrator:**
- Learning plan → Research topics
- Priority → Research depth
- Cost estimate → Budget control

**ResearchOrchestrator → SkillExtractionOrchestrator:**
- Research result → GitHub repos
- Best practices → Skill extraction
- Tools/libraries → Dependency installation

---

## Success Metrics

**System Coverage:**
- Target: 100% subagents audited every 2 weeks
- Target: 90%+ subagents taught within 4 weeks

**Health Monitoring:**
- Target: 0 critical subagents degraded >7 days
- Target: 0 missing subagents unhandled

**Learning Efficiency:**
- Target: Average cost per subagent < $2.00
- Target: Average time per subagent < 30 minutes

**Automation:**
- Target: 80%+ learning cycles triggered automatically
- Target: 0 manual interventions for routine updates

---

## Next Steps

1. ✅ Triggers & Workflow added to spec
2. ✅ SystemAuditor added to spec
3. ✅ LearningScheduler added to spec
4. ⏳ Final user approval (Task #25)
5. ⏳ Begin Phase 1.0 implementation (3-4 hours)
6. ⏳ Begin Phase 1.5 implementation (4-5 hours)
7. ⏳ Begin Phase 2+ implementation (8-12 hours)

---

## Recommendation

**READY FOR FINAL APPROVAL** ✅

Спецификация теперь полностью отвечает на вопросы пользователя:
- ✅ Когда запускается Teacher? → Автоматически каждые 2 недели + события + ручные команды
- ✅ Как аудирует систему? → SystemAuditor проверяет всех субагентов
- ✅ Что делать с "заболевшими"? → SystemAuditor обрабатывает missing/deprecated
- ✅ Как приоритизировать? → LearningScheduler создаёт план по приоритетам
- ✅ Что с рынком? → Автоматический market research каждую неделю

Можно начинать implementation после финального approval.

---

**Created:** 2026-05-13 17:15 GMT+3  
**Changes:** +631 lines, +23 KB  
**New Components:** 3 (Triggers, SystemAuditor, LearningScheduler)  
**Status:** ✅ Complete - Ready for Final Approval
