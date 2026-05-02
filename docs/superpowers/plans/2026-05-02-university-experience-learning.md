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

- [ ] **Step 1: Write failing test for Experience Tracker**

```python
# tests/unit/test_experience_tracker.py
import pytest
from datetime import datetime, timezone

from meai.learning.experience_tracker import ExperienceTracker


@pytest.mark.asyncio
async def test_experience_tracker_initialization():
    """Test ExperienceTracker can be initialized"""
    tracker = ExperienceTracker(database_url="sqlite+aiosqlite:///:memory:")
    
    await tracker.initialize()
    
    assert tracker is not None
    
    await tracker.shutdown()


@pytest.mark.asyncio
async def test_record_experience():
    """Test recording task experience"""
    tracker = ExperienceTracker(database_url="sqlite+aiosqlite:///:memory:")
    await tracker.initialize()
    
    # Record successful experience
    experience_id = await tracker.record_experience(
        magister_id="seo-magister-1",
        task_id="task-123",
        knowledge_ids=["knowledge-1", "knowledge-2"],
        outcome="success",
        outcome_score=0.9,
        feedback="Task completed successfully",
    )
    
    assert experience_id is not None
    assert experience_id.startswith("exp-")
    
    await tracker.shutdown()


@pytest.mark.asyncio
async def test_get_knowledge_success_rate():
    """Test calculating knowledge success rate"""
    tracker = ExperienceTracker(database_url="sqlite+aiosqlite:///:memory:")
    await tracker.initialize()
    
    # Record multiple experiences
    for i in range(10):
        outcome = "success" if i < 8 else "failure"
        score = 0.9 if i < 8 else 0.2
        
        await tracker.record_experience(
            magister_id="seo-magister-1",
            task_id=f"task-{i}",
            knowledge_ids=["knowledge-test"],
            outcome=outcome,
            outcome_score=score,
        )
    
    # Calculate success rate
    success_rate = await tracker.get_knowledge_success_rate("knowledge-test")
    
    assert success_rate == 0.8  # 8 out of 10
    
    await tracker.shutdown()
```

- [ ] **Step 2: Run test to verify it fails**

```bash
pytest tests/unit/test_experience_tracker.py -v
```

Expected: FAIL

- [ ] **Step 3: Create learning package**

```python
# src/meai/learning/__init__.py
"""Experience-based learning system"""

from meai.learning.experience_tracker import ExperienceTracker

__all__ = ["ExperienceTracker"]
```

- [ ] **Step 4: Write Experience Tracker implementation**

```python
# src/meai/learning/experience_tracker.py
"""Track task outcomes and knowledge usage"""

import json
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from sqlalchemy import text

from meai.storage.database import Database


class ExperienceTracker:
    """Track task experiences and knowledge usage"""

    def __init__(self, database_url: str = "sqlite+aiosqlite:///./data/meai.db"):
        """Initialize Experience Tracker
        
        Args:
            database_url: Database URL
        """
        self.db = Database(database_url)

    async def initialize(self) -> None:
        """Initialize tracker"""
        await self.db.connect()
        await self._create_tables()

    async def shutdown(self) -> None:
        """Shutdown tracker"""
        await self.db.disconnect()

    async def _create_tables(self) -> None:
        """Create experience tracking tables"""
        async with self.db.session() as session:
            # Experiences table
            await session.execute(
                text("""
                CREATE TABLE IF NOT EXISTS experiences (
                    id TEXT PRIMARY KEY,
                    magister_id TEXT NOT NULL,
                    task_id TEXT NOT NULL,
                    knowledge_ids TEXT NOT NULL,
                    outcome TEXT NOT NULL,
                    outcome_score REAL,
                    feedback TEXT,
                    created_at TIMESTAMP NOT NULL
                )
                """)
            )
            
            # Knowledge usage table
            await session.execute(
                text("""
                CREATE TABLE IF NOT EXISTS knowledge_usage (
                    id TEXT PRIMARY KEY,
                    knowledge_id TEXT NOT NULL,
                    magister_id TEXT NOT NULL,
                    used_at TIMESTAMP NOT NULL,
                    task_outcome TEXT NOT NULL,
                    outcome_score REAL
                )
                """)
            )
            
            await session.commit()

    async def record_experience(
        self,
        magister_id: str,
        task_id: str,
        knowledge_ids: list[str],
        outcome: str,
        outcome_score: float,
        feedback: str = None,
    ) -> str:
        """Record task experience
        
        Args:
            magister_id: Magister ID
            task_id: Task ID
            knowledge_ids: List of knowledge IDs used
            outcome: Task outcome (success/failure/partial)
            outcome_score: Outcome score (0.0-1.0)
            feedback: Optional feedback
            
        Returns:
            Experience ID
        """
        experience_id = f"exp-{uuid4().hex[:8]}"
        
        async with self.db.session() as session:
            # Record experience
            await session.execute(
                text("""
                INSERT INTO experiences
                (id, magister_id, task_id, knowledge_ids, outcome, 
                 outcome_score, feedback, created_at)
                VALUES (:id, :magister_id, :task_id, :knowledge_ids, :outcome,
                        :outcome_score, :feedback, :created_at)
                """),
                {
                    "id": experience_id,
                    "magister_id": magister_id,
                    "task_id": task_id,
                    "knowledge_ids": json.dumps(knowledge_ids),
                    "outcome": outcome,
                    "outcome_score": outcome_score,
                    "feedback": feedback,
                    "created_at": datetime.now(timezone.utc),
                },
            )
            
            # Record knowledge usage for each knowledge item
            for knowledge_id in knowledge_ids:
                usage_id = f"usage-{uuid4().hex[:8]}"
                
                await session.execute(
                    text("""
                    INSERT INTO knowledge_usage
                    (id, knowledge_id, magister_id, used_at, 
                     task_outcome, outcome_score)
                    VALUES (:id, :knowledge_id, :magister_id, :used_at,
                            :task_outcome, :outcome_score)
                    """),
                    {
                        "id": usage_id,
                        "knowledge_id": knowledge_id,
                        "magister_id": magister_id,
                        "used_at": datetime.now(timezone.utc),
                        "task_outcome": outcome,
                        "outcome_score": outcome_score,
                    },
                )
            
            await session.commit()
        
        return experience_id

    async def get_knowledge_success_rate(self, knowledge_id: str) -> float:
        """Calculate success rate for knowledge
        
        Args:
            knowledge_id: Knowledge ID
            
        Returns:
            Success rate (0.0-1.0)
        """
        async with self.db.session() as session:
            # Get all usage records
            result = await session.execute(
                text("""
                SELECT task_outcome, outcome_score
                FROM knowledge_usage
                WHERE knowledge_id = :knowledge_id
                """),
                {"knowledge_id": knowledge_id},
            )
            
            rows = result.fetchall()
            
            if len(rows) == 0:
                return 0.0
            
            # Calculate success rate
            successful = sum(1 for row in rows if row[0] == "success")
            total = len(rows)
            
            return successful / total if total > 0 else 0.0

    async def get_magister_experiences(
        self,
        magister_id: str,
        limit: int = 100,
    ) -> list[dict[str, Any]]:
        """Get Magister's experience history
        
        Args:
            magister_id: Magister ID
            limit: Maximum number of experiences
            
        Returns:
            List of experiences
        """
        async with self.db.session() as session:
            result = await session.execute(
                text("""
                SELECT id, task_id, knowledge_ids, outcome, 
                       outcome_score, feedback, created_at
                FROM experiences
                WHERE magister_id = :magister_id
                ORDER BY created_at DESC
                LIMIT :limit
                """),
                {"magister_id": magister_id, "limit": limit},
            )
            
            rows = result.fetchall()
            
            experiences = []
            for row in rows:
                experiences.append({
                    "id": row[0],
                    "task_id": row[1],
                    "knowledge_ids": json.loads(row[2]),
                    "outcome": row[3],
                    "outcome_score": row[4],
                    "feedback": row[5],
                    "created_at": row[6].isoformat() if row[6] else None,
                })
            
            return experiences

    async def get_knowledge_usage_count(self, knowledge_id: str) -> int:
        """Get usage count for knowledge
        
        Args:
            knowledge_id: Knowledge ID
            
        Returns:
            Usage count
        """
        async with self.db.session() as session:
            result = await session.execute(
                text("""
                SELECT COUNT(*) FROM knowledge_usage
                WHERE knowledge_id = :knowledge_id
                """),
                {"knowledge_id": knowledge_id},
            )
            
            count = result.scalar()
            return count if count else 0
```

- [ ] **Step 5: Run tests**

```bash
pytest tests/unit/test_experience_tracker.py -v
```

Expected: PASS (3 tests)

- [ ] **Step 6: Commit**

```bash
git add src/meai/learning/ tests/unit/test_experience_tracker.py
git commit -m "feat: add Experience Tracker for learning system

Experience Tracker features:
- Record task outcomes with knowledge used
- Track knowledge usage per Magister
- Calculate knowledge success rates
- Get Magister experience history

Database tables:
- experiences (task outcomes)
- knowledge_usage (knowledge usage tracking)

Tests cover initialization, recording, and success rate calculation.

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>"
```

---

## Task 2: Quality Updater

**Files:**
- Create: `src/meai/learning/quality_updater.py`
- Create: `tests/unit/test_quality_updater.py`

**Implementation:** Update knowledge quality scores based on experiences

**Key algorithm:**
```python
new_score = initial_score + experience_adjustment

experience_adjustment = (
    success_rate_factor +      # -1.5 to +1.5
    usage_frequency_factor +   # -0.5 to +0.5
    recency_factor            # -1.0 to +0.5
)
```

**Commit:** `feat: add Quality Updater with experience-based algorithm`

---

## Task 3: Deprecation Manager

**Files:**
- Create: `src/meai/learning/deprecation_manager.py`
- Create: `tests/unit/test_deprecation_manager.py`

**Implementation:** Automatically deprecate low-performing knowledge

**Deprecation criteria:**
- Quality score < 4.0 after 10+ uses
- Success rate < 30% after 10+ uses
- Not used in 180+ days

**Commit:** `feat: add Deprecation Manager with automatic detection`

---

## Task 4: Learning Analytics

**Files:**
- Create: `src/meai/learning/learning_analytics.py`
- Create: `tests/unit/test_learning_analytics.py`

**Implementation:** Analytics and insights

**Key metrics:**
- Knowledge quality distribution
- Success rate trends
- Deprecation rate
- Most/least used knowledge

**Commit:** `feat: add Learning Analytics and metrics`

---

## Task 5: Integrate Experience Tracking into Magisters

**Files:**
- Modify: `src/meai/agents/magisters/base_magister.py`

**Changes:**
```python
async def execute_task(self, task: Task) -> TaskResult:
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
    )
    
    return result
```

**Commit:** `feat: integrate experience tracking into Magisters`

---

## Task 6: Integrate Quality Updates into Teacher

**Files:**
- Modify: `src/meai/agents/teacher.py`

**Changes:**
```python
async def update_knowledge_quality(self, knowledge_id: str) -> dict:
    # Get new quality score
    update_result = await self.quality_updater.update_quality_score(knowledge_id)
    
    # Update in database
    await self._update_quality_in_db(knowledge_id, update_result["new_score"])
    
    # Update in Qdrant
    await self._update_quality_in_qdrant(knowledge_id, update_result["new_score"])
    
    return update_result
```

**Commit:** `feat: integrate quality updates into Teacher`

---

## Task 7: Scheduled Quality Updates

**Files:**
- Create: `scripts/update_qualities.py`

**Implementation:** Cron job to update quality scores daily

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

**Test scenario:**
1. Magister executes tasks using knowledge A (8 success, 2 failure)
2. Quality updater runs → quality score increases
3. Magister executes tasks using knowledge B (5 failures)
4. Quality updater runs → quality score decreases
5. Deprecation manager runs → knowledge B deprecated

**Commit:** `test: add experience learning integration test`

---

## Task 9: Integration Test - Quality Update Propagation

**Files:**
- Create: `tests/integration/test_quality_update_propagation.py`

**Test scenario:**
1. Knowledge stored in Teacher's Qdrant
2. Magister caches knowledge locally
3. Experiences recorded → quality updated
4. Teacher updates quality in Qdrant
5. Teacher notifies Magisters
6. Magisters update local cache

**Commit:** `test: add quality update propagation test`

---

## Task 10: Analytics Script

**Files:**
- Create: `scripts/analyze_learning.py`

**Implementation:** Generate learning analytics report

**Report includes:**
- System-wide metrics
- Per-Magister metrics
- Top/bottom performing knowledge
- Quality trends
- Deprecation statistics

**Commit:** `feat: add learning analytics report script`

---

## Task 11: End-to-End Test

**Files:**
- Create: `scripts/test_experience_learning.py`

**Test flow:**
1. Initialize system
2. SEO Magister executes 20 tasks
3. Record experiences (15 success, 5 failure)
4. Run quality updater
5. Run deprecation scan
6. Generate analytics report
7. Verify quality changes propagated

**Commit:** `test: add end-to-end test for experience learning`

---

## Success Criteria

- [ ] ✅ Experience tracking implemented
- [ ] ✅ Quality updater working
- [ ] ✅ Deprecation manager detecting low-performing knowledge
- [ ] ✅ Learning analytics generating insights
- [ ] ✅ Magisters recording experiences
- [ ] ✅ Teacher updating qualities
- [ ] ✅ Quality updates propagating
- [ ] ✅ Scheduled updates running
- [ ] ✅ All tests passing

---

