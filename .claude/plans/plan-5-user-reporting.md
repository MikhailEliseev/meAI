# Plan 5: User Reporting & Error Handling

**Date:** 2026-05-02 22:37  
**Status:** In Progress  
**Goal:** Complete full cycle USER → Operator → Magisters → Operator → USER

## Current State

✅ **Working:**
- Operator receives tasks from user
- Operator delegates to Magisters
- Magisters execute tasks
- Magisters report results back
- Operator collects and aggregates results

❌ **Missing:**
- Operator doesn't report back to user
- No error handling or retries
- No timeout management
- No task prioritization
- No performance monitoring

## Architecture

```
┌─────────────────────────────────────────────┐
│                  USER                       │
│  1. Sends task                              │
│  10. Receives report ← NEW!                 │
└─────────────────┬───────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────┐
│              OPERATOR                       │
│  2. Receives task                           │
│  3. Creates plan                            │
│  4. Delegates to Magisters                  │
│  8. Collects results                        │
│  9. Aggregates report                       │
│  10. Reports to user ← NEW!                 │
│  + Error handling ← NEW!                    │
│  + Retry logic ← NEW!                       │
└─────────────────┬───────────────────────────┘
                  │
                  │ Event Bus
                  │
        ┌─────────┴─────────┐
        │                   │
        ▼                   ▼
┌───────────────┐   ┌───────────────┐
│ SEO Magister  │   │Content Magister│
│ 5. Executes   │   │ 5. Executes   │
│ 6. Reports    │   │ 6. Reports    │
│ + Errors ← NEW│   │ + Errors ← NEW│
└───────────────┘   └───────────────┘
```

## Implementation Steps

### Step 1: Add User Reporting to Operator ✅

**File:** `src/meai/agents/operator.py`

Add method:
```python
async def report_to_user(self, report: Report) -> dict[str, Any]:
    """Report aggregated results to user
    
    Returns:
        User-friendly report dict
    """
    user_report = {
        "task_id": report.task_id,
        "status": "completed",
        "summary": report.summary,
        "insights": report.insights,
        "metrics": report.metrics,
        "issues": report.issues,
        "recommendations": report.recommendations,
        "completed_at": report.created_at.isoformat(),
    }
    
    # Write to vault for user
    await self._write_user_report(user_report)
    
    # Publish user notification event
    await self._notify_user(user_report)
    
    return user_report
```

Update `_finalize_task()`:
```python
async def _finalize_task(self, task_id: str) -> None:
    # ... existing code ...
    
    # Report to user
    await self.report_to_user(report)
```

### Step 2: Add Error Handling to Magisters ✅

**File:** `src/meai/agents/magisters/base_magister.py`

Update `execute_task()` wrapper:
```python
async def execute_task(self, task: Task) -> TaskResult:
    """Execute task with error handling"""
    try:
        # Call subclass implementation
        result = await self._execute_task_impl(task)
        return result
    except Exception as e:
        # Log error
        await self._log_error(task, e)
        
        # Return failed result
        return TaskResult(
            task_id=task.task_id,
            status="failed",
            result={},
            error=str(e),
            duration_seconds=0.0,
            completed_at=datetime.now(timezone.utc),
        )
```

Add error logging:
```python
async def _log_error(self, task: Task, error: Exception) -> None:
    """Log task execution error"""
    error_id = f"error-{uuid4().hex[:8]}"
    
    async with self.db.session() as session:
        await session.execute(
            text("""
            INSERT INTO magister_errors
            (id, magister_id, task_id, error_type, error_message, 
             stack_trace, occurred_at)
            VALUES (:id, :magister_id, :task_id, :error_type, 
                    :error_message, :stack_trace, :occurred_at)
            """),
            {
                "id": error_id,
                "magister_id": self.agent_id,
                "task_id": task.task_id,
                "error_type": type(error).__name__,
                "error_message": str(error),
                "stack_trace": traceback.format_exc(),
                "occurred_at": datetime.now(timezone.utc),
            },
        )
        await session.commit()
```

### Step 3: Add Retry Logic to Operator ✅

**File:** `src/meai/agents/operator.py`

Add retry configuration:
```python
# Retry settings
MAX_RETRIES = 3
RETRY_DELAY_SECONDS = 5
```

Update `_handle_task_result()`:
```python
async def _handle_task_result(self, message: Message) -> None:
    """Handle task result with retry logic"""
    payload = message.payload
    
    # Update subtask
    await self._update_subtask_result(...)
    
    # Check if failed
    if payload["status"] == "failed":
        subtask = await self._get_subtask(payload["subtask_id"])
        
        # Check retry count
        retry_count = subtask.get("retry_count", 0)
        
        if retry_count < self.MAX_RETRIES:
            # Retry task
            await self._retry_subtask(subtask, retry_count + 1)
            return
    
    # Check if all completed
    if await self._all_subtasks_completed(parent_task_id):
        await self._finalize_task(parent_task_id)
```

Add retry method:
```python
async def _retry_subtask(
    self, 
    subtask: Subtask, 
    retry_count: int
) -> None:
    """Retry failed subtask
    
    Args:
        subtask: Failed subtask
        retry_count: Current retry attempt
    """
    # Wait before retry
    await asyncio.sleep(self.RETRY_DELAY_SECONDS)
    
    # Update retry count
    subtask.metadata["retry_count"] = retry_count
    
    # Re-delegate
    await self.delegate_to_agent(subtask)
    
    # Log retry
    await self._log_retry(subtask, retry_count)
```

### Step 4: Add Timeout Management ✅

**File:** `src/meai/agents/operator.py`

Add timeout tracking:
```python
async def _monitor_timeouts(self) -> None:
    """Monitor and handle task timeouts
    
    Should be called periodically (e.g., every minute)
    """
    now = datetime.now(timezone.utc)
    
    # Get all in-progress subtasks
    async with self.db.session() as session:
        result = await session.execute(
            text("""
            SELECT subtask_id, agent_id, action, created_at
            FROM operator_subtasks
            WHERE status IN ('delegated', 'in_progress')
            """)
        )
        subtasks = result.fetchall()
    
    for row in subtasks:
        subtask_id, agent_id, action, created_at = row
        
        # Check timeout
        timeout = self.AGENT_TIMEOUTS.get(agent_id, timedelta(minutes=30))
        elapsed = now - created_at
        
        if elapsed > timeout:
            # Handle timeout
            await self._handle_timeout(subtask_id, agent_id)
```

Add timeout handler:
```python
async def _handle_timeout(
    self, 
    subtask_id: str, 
    agent_id: str
) -> None:
    """Handle subtask timeout
    
    Args:
        subtask_id: Timed out subtask
        agent_id: Agent that timed out
    """
    # Mark as failed
    await self._update_subtask_result(
        subtask_id=subtask_id,
        status="failed",
        result={"error": "timeout"},
    )
    
    # Log timeout
    await self._log_timeout(subtask_id, agent_id)
    
    # Trigger retry logic
    subtask = await self._get_subtask(subtask_id)
    await self._handle_task_result({
        "subtask_id": subtask_id,
        "status": "failed",
        "result": {"error": "timeout"},
    })
```

### Step 5: Add Performance Monitoring ✅

**File:** `src/meai/agents/operator.py`

Add metrics collection:
```python
async def _collect_metrics(self, task_id: str) -> dict[str, Any]:
    """Collect performance metrics for task
    
    Returns:
        Metrics dict
    """
    async with self.db.session() as session:
        # Get task timing
        result = await session.execute(
            text("""
            SELECT created_at, updated_at
            FROM operator_tasks
            WHERE task_id = :task_id
            """),
            {"task_id": task_id},
        )
        task_row = result.fetchone()
        
        # Get subtask stats
        result = await session.execute(
            text("""
            SELECT 
                COUNT(*) as total,
                SUM(CASE WHEN status = 'completed' THEN 1 ELSE 0 END) as completed,
                SUM(CASE WHEN status = 'failed' THEN 1 ELSE 0 END) as failed,
                AVG(JULIANDAY(completed_at) - JULIANDAY(created_at)) * 86400 as avg_duration
            FROM operator_subtasks
            WHERE parent_task_id = :task_id
            """),
            {"task_id": task_id},
        )
        stats = result.fetchone()
    
    return {
        "total_subtasks": stats[0],
        "completed": stats[1],
        "failed": stats[2],
        "success_rate": stats[1] / stats[0] if stats[0] > 0 else 0,
        "avg_duration_seconds": stats[3] or 0,
        "total_duration_seconds": (
            task_row[1] - task_row[0]
        ).total_seconds(),
    }
```

### Step 6: Integration Test ✅

**File:** `tests/integration/test_user_reporting.py`

Test full cycle:
```python
async def test_full_user_cycle():
    """Test complete USER → Operator → Magisters → Operator → USER"""
    
    # 1. User sends task
    operator = Operator(...)
    await operator.initialize()
    
    # Create magisters
    seo = SEOMagister(...)
    await seo.initialize()
    
    # 2. Send task
    task = Task(...)
    await operator.receive_task(task)
    
    # 3. Magisters process
    await seo.poll_and_process_tasks()
    
    # 4. Operator collects
    await operator.poll_and_collect_results()
    
    # 5. Wait for finalization
    await asyncio.sleep(1)
    
    # 6. Verify user report
    report = await operator.get_user_report(task.task_id)
    
    assert report["status"] == "completed"
    assert "summary" in report
    assert "insights" in report
    assert "metrics" in report
```

Test error handling:
```python
async def test_error_handling_and_retry():
    """Test error handling with retry logic"""
    
    # Create failing magister
    class FailingMagister(SEOMagister):
        async def execute_task(self, task):
            raise Exception("Simulated failure")
    
    operator = Operator(...)
    failing = FailingMagister(...)
    
    # Send task
    await operator.receive_task(task)
    
    # Process (will fail)
    await failing.poll_and_process_tasks()
    
    # Operator should retry
    await operator.poll_and_collect_results()
    
    # Verify retry happened
    subtask = await operator._get_subtask(...)
    assert subtask["retry_count"] > 0
```

## Files to Modify

1. ✅ `src/meai/agents/operator.py` - User reporting, retry, timeout
2. ✅ `src/meai/agents/magisters/base_magister.py` - Error handling
3. ✅ `tests/integration/test_user_reporting.py` - Full cycle test

## Success Criteria

- [ ] Operator reports to user after task completion
- [ ] Magisters handle errors gracefully
- [ ] Failed tasks are retried automatically
- [ ] Timeouts are detected and handled
- [ ] Performance metrics are collected
- [ ] Integration tests pass

## Timeline

- **Step 1-2:** 20 min (User reporting + error handling)
- **Step 3-4:** 25 min (Retry logic + timeouts)
- **Step 5:** 15 min (Metrics)
- **Step 6:** 20 min (Tests)
- **Total:** ~80 min

## Next Steps After Plan 5

1. **Dashboard** - Real-time monitoring UI
2. **Advanced Prioritization** - Smart queue management
3. **Load Balancing** - Distribute work efficiently
4. **Production Deployment** - Deploy to production

---

**Ready to start implementation!** 🚀
