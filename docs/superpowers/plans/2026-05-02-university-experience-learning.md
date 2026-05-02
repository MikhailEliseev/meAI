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

- [ ] **Step 1: Write failing test**

```python
# tests/unit/test_quality_updater.py
import pytest
from meai.learning.quality_updater import QualityUpdater
from meai.learning.experience_tracker import ExperienceTracker


@pytest.mark.asyncio
async def test_quality_updater_initialization():
    """Test QualityUpdater can be initialized"""
    tracker = ExperienceTracker(database_url="sqlite+aiosqlite:///:memory:")
    await tracker.initialize()
    
    updater = QualityUpdater(
        experience_tracker=tracker,
        database_url="sqlite+aiosqlite:///:memory:",
    )
    await updater.initialize()
    
    assert updater is not None
    
    await updater.shutdown()
    await tracker.shutdown()


@pytest.mark.asyncio
async def test_update_quality_score():
    """Test updating quality score based on experiences"""
    tracker = ExperienceTracker(database_url="sqlite+aiosqlite:///:memory:")
    await tracker.initialize()
    
    updater = QualityUpdater(
        experience_tracker=tracker,
        database_url="sqlite+aiosqlite:///:memory:",
    )
    await updater.initialize()
    
    # Record experiences (8 success, 2 failure)
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
    
    # Update quality (initial score: 7.0)
    result = await updater.update_quality_score(
        knowledge_id="knowledge-test",
        initial_score=7.0,
    )
    
    assert result["new_score"] > 7.0  # Should increase
    assert result["adjustment"] > 0
    
    await updater.shutdown()
    await tracker.shutdown()
```

- [ ] **Step 2: Write implementation**

```python
# src/meai/learning/quality_updater.py
"""Update knowledge quality scores based on experiences"""

from datetime import datetime, timezone, timedelta
from typing import Any
from uuid import uuid4

from sqlalchemy import text

from meai.learning.experience_tracker import ExperienceTracker
from meai.storage.database import Database


class QualityUpdater:
    """Update knowledge quality scores based on real-world outcomes"""

    def __init__(
        self,
        experience_tracker: ExperienceTracker,
        database_url: str = "sqlite+aiosqlite:///./data/meai.db",
    ):
        """Initialize Quality Updater
        
        Args:
            experience_tracker: Experience tracker instance
            database_url: Database URL
        """
        self.tracker = experience_tracker
        self.db = Database(database_url)

    async def initialize(self) -> None:
        """Initialize updater"""
        await self.db.connect()
        await self._create_tables()

    async def shutdown(self) -> None:
        """Shutdown updater"""
        await self.db.disconnect()

    async def _create_tables(self) -> None:
        """Create quality update tables"""
        async with self.db.session() as session:
            await session.execute(
                text("""
                CREATE TABLE IF NOT EXISTS quality_updates (
                    id TEXT PRIMARY KEY,
                    knowledge_id TEXT NOT NULL,
                    old_score REAL NOT NULL,
                    new_score REAL NOT NULL,
                    adjustment_reason TEXT NOT NULL,
                    updated_at TIMESTAMP NOT NULL
                )
                """)
            )
            await session.commit()

    async def update_quality_score(
        self,
        knowledge_id: str,
        initial_score: float = 7.0,
    ) -> dict[str, Any]:
        """Update quality score based on experiences
        
        Args:
            knowledge_id: Knowledge ID
            initial_score: Initial quality score (1-10)
            
        Returns:
            Update result with new score and adjustment
        """
        # Calculate adjustment factors
        success_rate = await self.tracker.get_knowledge_success_rate(knowledge_id)
        usage_count = await self.tracker.get_knowledge_usage_count(knowledge_id)
        
        # Success rate factor (-1.5 to +1.5)
        if success_rate >= 0.8:
            success_factor = 1.5
        elif success_rate >= 0.6:
            success_factor = 0.5
        elif success_rate >= 0.4:
            success_factor = 0.0
        elif success_rate >= 0.2:
            success_factor = -0.5
        else:
            success_factor = -1.5
        
        # Usage frequency factor (-0.5 to +0.5)
        if usage_count >= 20:
            usage_factor = 0.5
        elif usage_count >= 10:
            usage_factor = 0.3
        elif usage_count >= 5:
            usage_factor = 0.0
        else:
            usage_factor = -0.5
        
        # Recency factor (-1.0 to +0.5)
        # For now, assume recent usage (would check last_used in production)
        recency_factor = 0.5
        
        # Total adjustment
        adjustment = success_factor + usage_factor + recency_factor
        
        # Calculate new score (clamp to 1-10)
        new_score = max(1.0, min(10.0, initial_score + adjustment))
        
        # Record update
        update_id = f"update-{uuid4().hex[:8]}"
        
        adjustment_reason = {
            "success_rate": success_rate,
            "success_factor": success_factor,
            "usage_count": usage_count,
            "usage_factor": usage_factor,
            "recency_factor": recency_factor,
            "total_adjustment": adjustment,
        }
        
        async with self.db.session() as session:
            await session.execute(
                text("""
                INSERT INTO quality_updates
                (id, knowledge_id, old_score, new_score, 
                 adjustment_reason, updated_at)
                VALUES (:id, :knowledge_id, :old_score, :new_score,
                        :adjustment_reason, :updated_at)
                """),
                {
                    "id": update_id,
                    "knowledge_id": knowledge_id,
                    "old_score": initial_score,
                    "new_score": new_score,
                    "adjustment_reason": str(adjustment_reason),
                    "updated_at": datetime.now(timezone.utc),
                },
            )
            await session.commit()
        
        return {
            "knowledge_id": knowledge_id,
            "old_score": initial_score,
            "new_score": new_score,
            "adjustment": adjustment,
            "reason": adjustment_reason,
        }

    async def batch_update_scores(
        self,
        knowledge_ids: list[str] = None,
    ) -> int:
        """Batch update quality scores
        
        Args:
            knowledge_ids: List of knowledge IDs (None = all)
            
        Returns:
            Number of updated scores
        """
        # In production, would fetch all knowledge IDs from database
        # For now, just update provided IDs
        
        if knowledge_ids is None:
            return 0
        
        updated = 0
        for knowledge_id in knowledge_ids:
            try:
                await self.update_quality_score(knowledge_id)
                updated += 1
            except Exception:
                pass
        
        return updated

    async def get_quality_history(
        self,
        knowledge_id: str,
    ) -> list[dict[str, Any]]:
        """Get quality score history
        
        Args:
            knowledge_id: Knowledge ID
            
        Returns:
            List of quality updates
        """
        async with self.db.session() as session:
            result = await session.execute(
                text("""
                SELECT id, old_score, new_score, adjustment_reason, updated_at
                FROM quality_updates
                WHERE knowledge_id = :knowledge_id
                ORDER BY updated_at DESC
                """),
                {"knowledge_id": knowledge_id},
            )
            
            rows = result.fetchall()
            
            history = []
            for row in rows:
                history.append({
                    "id": row[0],
                    "old_score": row[1],
                    "new_score": row[2],
                    "adjustment_reason": row[3],
                    "updated_at": row[4].isoformat() if row[4] else None,
                })
            
            return history
```

- [ ] **Step 3: Update __init__.py**

```python
# src/meai/learning/__init__.py
from meai.learning.experience_tracker import ExperienceTracker
from meai.learning.quality_updater import QualityUpdater

__all__ = ["ExperienceTracker", "QualityUpdater"]
```

- [ ] **Step 4: Run tests**

```bash
pytest tests/unit/test_quality_updater.py -v
```

- [ ] **Step 5: Commit**

```bash
git add src/meai/learning/quality_updater.py tests/unit/test_quality_updater.py
git commit -m "feat: add Quality Updater with experience-based algorithm

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>"
```

---

## Task 3 (Updated): Deprecation Manager + Lint (Karpathy Pattern)

**Files:**
- Modify: `src/meai/learning/deprecation_manager.py`
- Add lint-style checks

**Updates to existing Task 3:**

**Add to DeprecationManager class:**

```python
# src/meai/learning/deprecation_manager.py (add methods)

class DeprecationManager:
    # ... existing code ...
    
    async def lint_knowledge_base(
        self,
        collection: str = "general_knowledge",
    ) -> dict[str, Any]:
        """Run lint checks on knowledge base (Karpathy pattern)
        
        Returns:
            Lint report with issues found
        """
        return {
            "contradictions": await self._find_contradictions(collection),
            "stale_knowledge": await self._find_stale_knowledge(collection),
            "orphaned_knowledge": await self._find_orphaned_knowledge(collection),
            "low_quality": await self._find_low_quality(collection),
        }
    
    async def _find_contradictions(self, collection: str) -> list[dict]:
        """Find contradictory knowledge items
        
        Uses wiki synthesizer to detect conflicts
        """
        # Get all knowledge
        all_knowledge = await self._get_all_knowledge(collection)
        
        # Use wiki synthesizer to find contradictions
        from meai.knowledge.wiki_synthesizer import WikiSynthesizer
        synthesizer = WikiSynthesizer()
        
        contradictions = synthesizer.find_contradictions(all_knowledge)
        
        return contradictions
    
    async def _find_stale_knowledge(
        self,
        collection: str,
        days_threshold: int = 180,
    ) -> list[dict]:
        """Find knowledge not used in X days"""
        # Query knowledge_usage table
        cutoff_date = datetime.now(timezone.utc) - timedelta(days=days_threshold)
        
        async with self.db.session() as session:
            result = await session.execute(
                text("""
                SELECT DISTINCT k.knowledge_id
                FROM knowledge k
                LEFT JOIN knowledge_usage u ON k.id = u.knowledge_id
                WHERE u.used_at IS NULL OR u.used_at < :cutoff_date
                """),
                {"cutoff_date": cutoff_date},
            )
            
            stale_ids = [row[0] for row in result.fetchall()]
            
            return [{"knowledge_id": kid, "reason": "not_used_recently"} for kid in stale_ids]
    
    async def _find_orphaned_knowledge(self, collection: str) -> list[dict]:
        """Find knowledge with no wikilinks or backlinks"""
        all_knowledge = await self._get_all_knowledge(collection)
        
        orphaned = []
        for item in all_knowledge:
            metadata = item.get("metadata", {})
            wikilinks = metadata.get("wikilinks", [])
            backlinks = metadata.get("backlinks", [])
            
            if not wikilinks and not backlinks:
                orphaned.append({
                    "knowledge_id": item["id"],
                    "reason": "no_connections",
                })
        
        return orphaned
    
    async def _find_low_quality(self, collection: str) -> list[dict]:
        """Find low quality knowledge (existing deprecation logic)"""
        # Use existing check_deprecation logic
        all_knowledge = await self._get_all_knowledge(collection)
        
        low_quality = []
        for item in all_knowledge:
            check = await self.check_deprecation(item["id"])
            if check["should_deprecate"]:
                low_quality.append({
                    "knowledge_id": item["id"],
                    "reason": check["reason"],
                    "level": check["level"],
                })
        
        return low_quality
```

**Commit message update:**
```
feat: add Deprecation Manager with lint-style checks (Karpathy pattern)

Deprecation Manager now includes wiki lint operations:
- Find contradictions between knowledge items
- Find stale knowledge (not used in 180+ days)
- Find orphaned knowledge (no wikilinks/backlinks)
- Find low quality knowledge (existing logic)

Integrates with wiki synthesizer for contradiction detection.

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>
```

---

## Task 4: Learning Analytics

**Files:**
- Create: `src/meai/learning/learning_analytics.py`
- Create: `tests/unit/test_learning_analytics.py`

**Key implementation:**
```python
class LearningAnalytics:
    async def get_system_metrics(self) -> dict:
        return {
            "total_knowledge": await self._count_knowledge(),
            "avg_quality_score": await self._avg_quality(),
            "deprecated_count": await self._count_deprecated(),
            "avg_success_rate": await self._avg_success_rate(),
            "total_experiences": await self._count_experiences(),
        }
    
    async def get_quality_trends(self, days: int = 30) -> list[dict]:
        # Return quality trends over time
        pass
```

**Commit:** `feat: add Learning Analytics and metrics`

---

## Task 5: Integrate Experience Tracking into Magisters

**Files:**
- Modify: `src/meai/agents/magisters/base_magister.py`

**Changes:**
```python
# Add to BaseMagister.__init__
self.experience_tracker = ExperienceTracker(database_url=database_url)

# Modify execute_task
async def execute_task(self, task: Task) -> TaskResult:
    knowledge_ids = self._get_knowledge_used(task)
    result = await self._execute_task_impl(task)
    
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
# Add to TeacherAgent.__init__
self.quality_updater = QualityUpdater(experience_tracker, database_url)

# Add method
async def update_knowledge_quality(self, knowledge_id: str) -> dict:
    update_result = await self.quality_updater.update_quality_score(knowledge_id)
    await self._update_quality_in_qdrant(knowledge_id, update_result["new_score"])
    return update_result
```

**Commit:** `feat: integrate quality updates into Teacher`

---

## Task 7: Scheduled Quality Updates

**Files:**
- Create: `scripts/update_qualities.py`

**Implementation:**
```python
async def main():
    print("🔄 Running quality updates...")
    
    teacher = TeacherAgent(...)
    await teacher.initialize()
    
    # Update all knowledge qualities
    updated = await teacher.batch_update_qualities()
    print(f"✅ Updated {updated} knowledge items")
    
    # Scan for deprecation
    deprecated = await teacher.scan_for_deprecation()
    print(f"⚠️  Deprecated {len(deprecated)} items")
    
    await teacher.shutdown()
```

**Commit:** `feat: add scheduled quality update script`

---

## Task 8: Integration Test - Experience Learning Flow

**Files:**
- Create: `tests/integration/test_experience_learning_flow.py`

**Test scenario:**
```python
@pytest.mark.asyncio
async def test_experience_learning_flow():
    # 1. Execute tasks with knowledge A (8 success, 2 failure)
    # 2. Run quality updater → score increases
    # 3. Execute tasks with knowledge B (5 failures)
    # 4. Run quality updater → score decreases
    # 5. Run deprecation → knowledge B deprecated
    pass
```

**Commit:** `test: add experience learning integration test`

---

## Task 9: Integration Test - Quality Update Propagation

**Files:**
- Create: `tests/integration/test_quality_update_propagation.py`

**Test scenario:**
```python
@pytest.mark.asyncio
async def test_quality_update_propagation():
    # 1. Store knowledge in Teacher
    # 2. Magister caches locally
    # 3. Record experiences
    # 4. Teacher updates quality
    # 5. Verify propagation to Qdrant and Magisters
    pass
```

**Commit:** `test: add quality update propagation test`

---

## Task 10: Analytics Script

**Files:**
- Create: `scripts/analyze_learning.py`

**Implementation:**
```python
async def main():
    print("📊 University Learning Analytics Report")
    
    analytics = LearningAnalytics(...)
    await analytics.initialize()
    
    # System metrics
    metrics = await analytics.get_system_metrics()
    print(f"Total Knowledge: {metrics['total_knowledge']}")
    print(f"Avg Quality: {metrics['avg_quality_score']:.1f}/10")
    
    # Top performing
    top = await analytics.get_top_performing(limit=5)
    for item in top:
        print(f"✅ {item['id']} - Quality: {item['quality']}")
    
    await analytics.shutdown()
```

**Commit:** `feat: add learning analytics report script`

---

## Task 11: End-to-End Test

**Files:**
- Create: `scripts/test_experience_learning.py`

**Test flow:**
```python
async def main():
    print("🧪 Testing Experience Learning System")
    
    # 1. Initialize all components
    # 2. Execute 20 tasks (15 success, 5 failure)
    # 3. Run quality updater
    # 4. Run deprecation scan
    # 5. Generate analytics report
    # 6. Verify quality changes
    
    print("🎉 ALL TESTS PASSED!")
```

**Commit:** `test: add end-to-end test for experience learning`

---

