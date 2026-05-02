# Plan 4: Operator-Magisters Integration

**Date:** 2026-05-02 19:27  
**Status:** In Progress  
**Goal:** Integrate Magisters with Operator for automatic task delegation

## Current State

✅ **Operator** (850+ lines)
- Receives tasks from user/Architect
- Makes tactical decisions
- Delegates via Event Bus (`task_assignment` events)
- 4 execution strategies

✅ **Magisters** (6 specialists)
- SEO, Content, Ads, SMM, Analytics, Intelligence
- Hybrid search (local → Teacher → Researcher)
- Inherit from `Agent` base class
- Have `execute_task()` method

❌ **Missing Integration**
- Magisters don't subscribe to Operator events
- Operator uses old agent IDs (`seo-agent`, not `seo-magister-1`)
- No automatic task execution flow
- No result reporting back to Operator

## Integration Architecture

```
┌─────────────────────────────────────────────┐
│              OPERATOR                       │
│  1. Receives task from user                 │
│  2. Creates tactical plan                   │
│  3. Publishes task_assignment events        │
└─────────────────┬───────────────────────────┘
                  │
                  │ Event Bus
                  │
        ┌─────────┴─────────┐
        │                   │
        ▼                   ▼
┌───────────────┐   ┌───────────────┐
│ SEO Magister  │   │Content Magister│
│ 4. Subscribes │   │ 4. Subscribes │
│ 5. Executes   │   │ 5. Executes   │
│ 6. Reports    │   │ 6. Reports    │
└───────┬───────┘   └───────┬───────┘
        │                   │
        └─────────┬─────────┘
                  │
                  ▼
        ┌─────────────────┐
        │    OPERATOR     │
        │ 7. Collects     │
        │ 8. Aggregates   │
        │ 9. Reports      │
        └─────────────────┘
```

## Implementation Steps

### Step 1: Update Operator Agent IDs ✅
**File:** `src/meai/agents/operator.py`

Change agent IDs to match Magisters:
```python
AGENT_CAPABILITIES = {
    "seo-magister-1": ["analyze_keywords", "optimize_content", ...],
    "content-magister-1": ["generate_content", "edit_content", ...],
    "ads-magister-1": ["create_campaign", "optimize_budget", ...],
}
```

### Step 2: Add Event Subscription to Magisters ✅
**File:** `src/meai/agents/magisters/base_magister.py`

Add method:
```python
async def _subscribe_to_events(self) -> None:
    """Subscribe to Operator task assignments"""
    await self.event_bus.subscribe(
        agent_id=self.agent_id,
        message_type="task_assignment",
        callback=self._handle_task_assignment,
    )
```

### Step 3: Add Task Assignment Handler ✅
**File:** `src/meai/agents/magisters/base_magister.py`

Add method:
```python
async def _handle_task_assignment(self, message: Message) -> None:
    """Handle task assignment from Operator
    
    1. Extract task details from message
    2. Create Task object
    3. Execute task
    4. Report result back to Operator
    """
    # Extract payload
    payload = message.payload
    
    # Create Task
    task = Task(
        task_id=payload["subtask_id"],
        description=payload["description"],
        metadata={"action": payload["action"]},
    )
    
    # Execute
    result = await self.execute_task(task)
    
    # Report back
    await self._report_result_to_operator(result, payload["parent_task_id"])
```

### Step 4: Add Result Reporting ✅
**File:** `src/meai/agents/magisters/base_magister.py`

Add method:
```python
async def _report_result_to_operator(
    self, 
    result: TaskResult, 
    parent_task_id: str
) -> None:
    """Report task result back to Operator"""
    await self.event_bus.publish(
        Message(
            from_agent=self.agent_id,
            to_agent="operator",
            message_type="task_result",
            priority=1,
            payload={
                "subtask_id": result.task_id,
                "parent_task_id": parent_task_id,
                "status": result.status,
                "result": result.result,
            },
            timestamp=datetime.now(timezone.utc).isoformat(),
        )
    )
```

### Step 5: Add Result Collection to Operator ✅
**File:** `src/meai/agents/operator.py`

Add methods:
```python
async def _subscribe_to_events(self) -> None:
    """Subscribe to agent result events"""
    await self.event_bus.subscribe(
        agent_id=self.agent_id,
        message_type="task_result",
        callback=self._handle_task_result,
    )

async def _handle_task_result(self, message: Message) -> None:
    """Handle task result from agent"""
    payload = message.payload
    
    # Update subtask in database
    await self._update_subtask_result(
        subtask_id=payload["subtask_id"],
        status=payload["status"],
        result=payload["result"],
    )
    
    # Check if all subtasks completed
    parent_task_id = payload["parent_task_id"]
    if await self._all_subtasks_completed(parent_task_id):
        await self._finalize_task(parent_task_id)
```

### Step 6: Add Report Aggregation ✅
**File:** `src/meai/agents/operator.py`

Add method:
```python
async def _finalize_task(self, task_id: str) -> None:
    """Finalize task after all subtasks completed
    
    1. Collect all subtask results
    2. Aggregate into report
    3. Store in database
    4. Write to vault
    5. Report to user
    """
    # Collect results
    results = await self._collect_subtask_results(task_id)
    
    # Aggregate
    report = await self._aggregate_report(task_id, results)
    
    # Store
    await self._store_report(report)
    
    # Write to vault
    await self._write_report_to_vault(report)
    
    # Report to user
    await self._report_to_user(report)
```

### Step 7: Integration Test ✅
**File:** `tests/integration/test_operator_magisters.py`

Test flow:
```python
async def test_operator_magisters_integration():
    """Test full Operator → Magisters → Operator flow"""
    
    # 1. Create Operator
    operator = Operator(...)
    await operator.initialize()
    
    # 2. Create Magisters
    seo = SEOMagister(...)
    content = ContentMagister(...)
    await seo.initialize()
    await content.initialize()
    
    # 3. Send task to Operator
    task = Task(
        goal="Launch marketing campaign",
        description="SEO + Content",
        ...
    )
    await operator.receive_task(task)
    
    # 4. Wait for completion
    await asyncio.sleep(5)
    
    # 5. Verify results
    report = await operator.get_report(task.task_id)
    assert report.status == "completed"
    assert len(report.insights) > 0
```

## Files to Modify

1. ✅ `src/meai/agents/operator.py` - Update agent IDs, add result handling
2. ✅ `src/meai/agents/magisters/base_magister.py` - Add event subscription
3. ✅ `tests/integration/test_operator_magisters.py` - Integration test

## Success Criteria

- [ ] Operator delegates to Magisters (not old agent IDs)
- [ ] Magisters receive and execute tasks
- [ ] Magisters report results back to Operator
- [ ] Operator collects and aggregates results
- [ ] Operator reports to user
- [ ] Integration test passes

## Timeline

- **Step 1-2:** 15 min (Update IDs, add subscription)
- **Step 3-4:** 20 min (Task handler, result reporting)
- **Step 5-6:** 25 min (Result collection, aggregation)
- **Step 7:** 20 min (Integration test)
- **Total:** ~80 min

## Next Steps After Plan 4

1. Add periodic quality updates (Experience Learning integration)
2. Add Operator dashboard (metrics, status)
3. Add error handling and retries
4. Add task prioritization and queuing

---

**Ready to start implementation!** 🚀
