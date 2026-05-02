# University Experience Learning Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement experience-based learning system where agents learn from successes and failures, update knowledge quality scores, and deprecate outdated information.

**Architecture:** Magisters track task outcomes, Teacher updates knowledge quality based on real-world results, system automatically deprecates low-performing knowledge.

**Tech Stack:** Python 3.11+, SQLAlchemy, Qdrant (metadata updates), Event Bus

**Dependencies:** Plan 1 and Plan 2 must be completed

---

## File Structure

**New files:**
```
src/meai/
├── learning/
│   ├── __init__.py
│   ├── experience_tracker.py      # Track task outcomes
│   ├── quality_updater.py         # Update knowledge quality
│   ├── deprecation_manager.py     # Deprecate outdated knowledge
│   └── learning_analytics.py      # Learning metrics

tests/
├── unit/
│   ├── test_experience_tracker.py
│   ├── test_quality_updater.py
│   ├── test_deprecation_manager.py
│   └── test_learning_analytics.py
│
├── integration/
│   ├── test_experience_learning_flow.py
│   └── test_quality_update_propagation.py

scripts/
├── analyze_learning.py
└── test_experience_learning.py
```

**Modified files:**
- `src/meai/agents/magisters/base_magister.py` — add experience tracking
- `src/meai/agents/teacher.py` — add quality updates

---

## Task 1: Experience Tracker

**Files:**
- Create: `src/meai/learning/__init__.py`
- Create: `src/meai/learning/experience_tracker.py`
- Create: `tests/unit/test_experience_tracker.py`

**Implementation:** Track task outcomes and link them to knowledge used.

**Key features:**
- Record task execution (success/failure)
- Link tasks to knowledge sources
- Track knowledge usage frequency
- Calculate success rates per knowledge item

**Database tables:**
```sql
CREATE TABLE experiences (
    id TEXT PRIMARY KEY,
    magister_id TEXT NOT NULL,
    task_id TEXT NOT NULL,
    knowledge_ids TEXT NOT NULL,  -- JSON array
    outcome TEXT NOT NULL,         -- success/failure/partial
    outcome_score REAL,            -- 0.0-1.0
    feedback TEXT,
    created_at TIMESTAMP NOT NULL
);

CREATE TABLE knowledge_usage (
    id TEXT PRIMARY KEY,
    knowledge_id TEXT NOT NULL,
    magister_id TEXT NOT NULL,
    used_at TIMESTAMP NOT NULL,
    task_outcome TEXT NOT NULL,
    outcome_score REAL
);
```

**Key methods:**
```python
async def record_experience(
    magister_id: str,
    task_id: str,
    knowledge_ids: list[str],
    outcome: str,
    outcome_score: float,
    feedback: str = None,
) -> str:
    """Record task experience"""

async def get_knowledge_success_rate(
    knowledge_id: str,
) -> float:
    """Calculate success rate for knowledge"""

async def get_magister_experiences(
    magister_id: str,
    limit: int = 100,
) -> list[dict]:
    """Get Magister's experience history"""
```

**Commit:** `feat: add experience tracking system`

---

## Task 2: Quality Updater

**Files:**
- Create: `src/meai/learning/quality_updater.py`
- Create: `tests/unit/test_quality_updater.py`

**Implementation:** Update knowledge quality scores based on real-world outcomes.

**Quality Update Algorithm:**
```python
# Initial quality score (from Teacher evaluation): 1-10
# Experience-based adjustment: -3 to +3

new_score = initial_score + experience_adjustment

experience_adjustment = (
    success_rate_factor +      # -1.5 to +1.5
    usage_frequency_factor +   # -0.5 to +0.5
    recency_factor            # -1.0 to +0.5
)

# Success rate factor
if success_rate >= 0.8: +1.5
elif success_rate >= 0.6: +0.5
elif success_rate >= 0.4: 0.0
elif success_rate >= 0.2: -0.5
else: -1.5

# Usage frequency factor
if usage_count >= 20: +0.5
elif usage_count >= 10: +0.3
elif usage_count >= 5: 0.0
else: -0.5

# Recency factor
if last_used < 7 days ago: +0.5
elif last_used < 30 days ago: 0.0
elif last_used < 90 days ago: -0.5
else: -1.0
```

**Database tables:**
```sql
CREATE TABLE quality_updates (
    id TEXT PRIMARY KEY,
    knowledge_id TEXT NOT NULL,
    old_score REAL NOT NULL,
    new_score REAL NOT NULL,
    adjustment_reason TEXT NOT NULL,  -- JSON
    updated_at TIMESTAMP NOT NULL
);
```

**Key methods:**
```python
async def update_quality_score(
    knowledge_id: str,
) -> dict:
    """Update quality score based on experiences"""

async def batch_update_scores(
    knowledge_ids: list[str] = None,
) -> int:
    """Batch update quality scores"""

async def get_quality_history(
    knowledge_id: str,
) -> list[dict]:
    """Get quality score history"""
```

**Commit:** `feat: add quality score updater with experience-based algorithm`

---

## Task 3: Deprecation Manager

**Files:**
- Create: `src/meai/learning/deprecation_manager.py`
- Create: `tests/unit/test_deprecation_manager.py`

**Implementation:** Automatically deprecate low-performing or outdated knowledge.

**Deprecation Criteria:**
```python
# Knowledge should be deprecated if:
1. Quality score < 4.0 after 10+ uses
2. Success rate < 30% after 10+ uses
3. Not used in 180+ days
4. Marked as outdated by Magister
5. Superseded by newer knowledge
```

**Deprecation Levels:**
- **Warning:** Quality 4.0-5.0, still usable but flagged
- **Deprecated:** Quality < 4.0, not recommended
- **Archived:** Not used in 180+ days, removed from active search

**Database tables:**
```sql
CREATE TABLE deprecations (
    id TEXT PRIMARY KEY,
    knowledge_id TEXT NOT NULL,
    deprecation_level TEXT NOT NULL,  -- warning/deprecated/archived
    reason TEXT NOT NULL,
    deprecated_at TIMESTAMP NOT NULL,
    superseded_by TEXT  -- knowledge_id that replaces this
);
```

**Key methods:**
```python
async def check_deprecation(
    knowledge_id: str,
) -> dict:
    """Check if knowledge should be deprecated"""

async def deprecate_knowledge(
    knowledge_id: str,
    level: str,
    reason: str,
    superseded_by: str = None,
) -> None:
    """Deprecate knowledge"""

async def scan_for_deprecation() -> list[str]:
    """Scan all knowledge for deprecation candidates"""

async def archive_old_knowledge(
    days_threshold: int = 180,
) -> int:
    """Archive knowledge not used in X days"""
```

**Commit:** `feat: add deprecation manager with automatic detection`

---

## Task 4: Learning Analytics

**Files:**
- Create: `src/meai/learning/learning_analytics.py`
- Create: `tests/unit/test_learning_analytics.py`

**Implementation:** Analytics and insights about learning system.

**Key metrics:**
- Knowledge quality distribution
- Success rate trends
- Deprecation rate
- Most/least used knowledge
- Magister learning curves

**Key methods:**
```python
async def get_system_metrics() -> dict:
    """Get overall system metrics"""
    return {
        "total_knowledge": 1234,
        "avg_quality_score": 7.2,
        "deprecated_count": 45,
        "avg_success_rate": 0.78,
        "total_experiences": 5678,
    }

async def get_magister_metrics(
    magister_id: str,
) -> dict:
    """Get Magister-specific metrics"""

async def get_knowledge_metrics(
    knowledge_id: str,
) -> dict:
    """Get knowledge-specific metrics"""

async def get_quality_trends(
    days: int = 30,
) -> list[dict]:
    """Get quality score trends over time"""
```

**Commit:** `feat: add learning analytics and metrics`

---

## Task 5: Integrate Experience Tracking into Magisters

**Files:**
- Modify: `src/meai/agents/magisters/base_magister.py`
- Modify: `tests/unit/test_base_magister.py`

**Implementation:** Add experience tracking to Magister task execution.

**Changes to BaseMagister:**
```python
async def execute_task(self, task: Task) -> TaskResult:
    """Execute task with experience tracking"""
    
    # Track knowledge used
    knowledge_ids = self._get_knowledge_used(task)
    
    # Execute task
    result = await self._execute_task_impl(task)
    
    # Record experience
    await self.experience_tracker.record_experience(
        magister_id=self.agent_id,
        task_id=task.task_id,
        knowledge_ids=knowledge_ids,
        outcome=result.status,
        outcome_score=self._calculate_outcome_score(result),
        feedback=result.metadata.get("feedback"),
    )
    
    return result

async def provide_feedback(
    self,
    task_id: str,
    knowledge_id: str,
    feedback: str,
    helpful: bool,
) -> None:
    """Provide feedback on knowledge usefulness"""
```

**Commit:** `feat: integrate experience tracking into Magisters`

---

## Task 6: Integrate Quality Updates into Teacher

**Files:**
- Modify: `src/meai/agents/teacher.py`
- Modify: `tests/unit/test_teacher.py`

**Implementation:** Add quality update capability to Teacher.

**Changes to TeacherAgent:**
```python
async def update_knowledge_quality(
    self,
    knowledge_id: str,
) -> dict:
    """Update knowledge quality based on experiences"""
    
    # Get new quality score
    update_result = await self.quality_updater.update_quality_score(knowledge_id)
    
    # Update in database
    await self._update_quality_in_db(knowledge_id, update_result["new_score"])
    
    # Update in Qdrant (metadata)
    await self._update_quality_in_qdrant(knowledge_id, update_result["new_score"])
    
    # Notify Magisters if significant change
    if abs(update_result["adjustment"]) >= 2.0:
        await self._notify_quality_change(knowledge_id, update_result)
    
    return update_result

async def batch_update_qualities(self) -> int:
    """Batch update all knowledge qualities"""
    
    # Get all knowledge IDs
    knowledge_ids = await self._get_all_knowledge_ids()
    
    # Update in batches
    updated = 0
    for batch in self._batch(knowledge_ids, size=100):
        updated += await self.quality_updater.batch_update_scores(batch)
    
    return updated
```

**Commit:** `feat: integrate quality updates into Teacher`

---

## Task 7: Scheduled Quality Updates

**Files:**
- Create: `scripts/update_qualities.py`

**Implementation:** Cron job to periodically update quality scores.

**Functionality:**
- Run daily at 2 AM
- Update all knowledge qualities
- Scan for deprecation candidates
- Archive old knowledge
- Generate daily report

**Usage:**
```bash
# Manual run
python scripts/update_qualities.py

# Cron (add to crontab)
0 2 * * * cd /path/to/meai && python scripts/update_qualities.py
```

**Commit:** `feat: add scheduled quality update script`

---

## Task 8: Integration Test - Experience Learning Flow

**Files:**
- Create: `tests/integration/test_experience_learning_flow.py`

**Implementation:** Test complete experience learning flow.

**Test scenario:**
1. Magister executes task using knowledge A
2. Task succeeds → record positive experience
3. Magister executes 10 more tasks with knowledge A (8 success, 2 failure)
4. Quality updater runs → quality score increases
5. Magister executes task using knowledge B
6. Task fails 5 times in a row
7. Quality updater runs → quality score decreases
8. Deprecation manager runs → knowledge B deprecated

**Commit:** `test: add experience learning integration test`

---

## Task 9: Integration Test - Quality Update Propagation

**Files:**
- Create: `tests/integration/test_quality_update_propagation.py`

**Implementation:** Test quality updates propagate correctly.

**Test scenario:**
1. Knowledge stored in Teacher's Qdrant
2. Magister caches knowledge locally
3. Experiences recorded → quality updated
4. Teacher updates quality in Qdrant
5. Teacher notifies Magisters of quality change
6. Magisters update local cache

**Commit:** `test: add quality update propagation test`

---

## Task 10: Analytics Script

**Files:**
- Create: `scripts/analyze_learning.py`

**Implementation:** Generate learning analytics report.

**Report includes:**
- System-wide metrics
- Per-Magister metrics
- Top/bottom performing knowledge
- Quality trends
- Deprecation statistics

**Output:**
```
📊 University Learning Analytics Report
   Generated: 2026-05-02 18:30

═══════════════════════════════════════════════════════════════

📈 System Metrics:
   Total Knowledge: 1,234
   Avg Quality Score: 7.2 / 10
   Deprecated: 45 (3.6%)
   Avg Success Rate: 78%
   Total Experiences: 5,678

═══════════════════════════════════════════════════════════════

🏆 Top Performing Knowledge:
   1. "SEO best practices 2026" - Quality: 9.5, Success: 95%
   2. "Content marketing strategies" - Quality: 9.2, Success: 92%
   3. "Google Ads optimization" - Quality: 8.8, Success: 88%

═══════════════════════════════════════════════════════════════

⚠️  Low Performing Knowledge:
   1. "Old SEO tactics" - Quality: 3.2, Success: 25% → DEPRECATED
   2. "Outdated content tips" - Quality: 4.1, Success: 35% → WARNING
   3. "Legacy ad strategies" - Quality: 4.5, Success: 40% → WARNING

═══════════════════════════════════════════════════════════════

📊 Quality Trends (Last 30 Days):
   Week 1: Avg 6.8
   Week 2: Avg 7.0 (+0.2)
   Week 3: Avg 7.1 (+0.1)
   Week 4: Avg 7.2 (+0.1)

═══════════════════════════════════════════════════════════════

🤖 Magister Performance:
   SEO Magister: 85% success rate, 234 tasks
   Content Magister: 82% success rate, 189 tasks
   Ads Magister: 78% success rate, 156 tasks
   SMM Magister: 80% success rate, 145 tasks
   Analytics Magister: 88% success rate, 123 tasks
   Intelligence Magister: 75% success rate, 98 tasks
```

**Commit:** `feat: add learning analytics report script`

---

## Task 11: End-to-End Test

**Files:**
- Create: `scripts/test_experience_learning.py`

**Implementation:** Complete E2E test of experience learning system.

**Test flow:**
1. Initialize system (Teacher, Magisters, Learning components)
2. SEO Magister executes 20 tasks using various knowledge
3. Record experiences (15 success, 5 failure)
4. Run quality updater → scores adjusted
5. Run deprecation scan → 2 items deprecated
6. Generate analytics report
7. Verify quality changes propagated to Qdrant
8. Verify Magisters notified of changes

**Commit:** `test: add end-to-end test for experience learning`

---

## Success Criteria

- [ ] ✅ Experience tracking implemented
- [ ] ✅ Quality updater working with experience-based algorithm
- [ ] ✅ Deprecation manager automatically detecting low-performing knowledge
- [ ] ✅ Learning analytics generating insights
- [ ] ✅ Magisters recording experiences after tasks
- [ ] ✅ Teacher updating qualities in Qdrant
- [ ] ✅ Quality updates propagating to Magisters
- [ ] ✅ Scheduled updates running
- [ ] ✅ All unit tests passing
- [ ] ✅ All integration tests passing
- [ ] ✅ End-to-end test passing

---

## Next Steps

After completing this plan:

**System is complete!** 🎉

All three plans implemented:
- ✅ Plan 1: Infrastructure + Core (Qdrant, Teacher, Researcher)
- ✅ Plan 2: Magisters + Hybrid Search
- ✅ Plan 3: Experience Learning

**Ready for production use:**
- University knowledge system fully operational
- 6 specialized Magisters
- Hybrid search with 3-layer fallback
- Self-improving through experience learning

---

## Notes

- **Quality updates:** Run daily at 2 AM via cron
- **Deprecation threshold:** Quality < 4.0 after 10+ uses
- **Archive threshold:** Not used in 180+ days
- **Success rate calculation:** (successful_tasks / total_tasks) * 100
- **Quality adjustment range:** -3 to +3 points
