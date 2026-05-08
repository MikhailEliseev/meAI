# Magisters + Event Store Integration Plan

**Goal:** Integrate EventStore with all Magisters for complete audit trail

**Approach:** Add EventStore to BaseMagister, auto-propagate to all 9 Magisters

---

## Current State

**Magisters (9 total):**
- SEO, Content, Ads, Analytics, Social, Intelligence
- Brand, Reputation, AI

**EventBus:** Already integrated in BaseMagister ✅
**EventStore:** Not integrated ❌

---

## Integration Strategy

### Option 1: BaseMagister Integration (Recommended)
**Pros:**
- Single point of integration
- All 9 Magisters get it automatically
- Consistent behavior
- Minimal code changes

**Cons:**
- None

### Option 2: Per-Magister Integration
**Pros:**
- Granular control

**Cons:**
- 9 files to modify
- Inconsistent implementations
- More maintenance

**Decision:** Option 1 (BaseMagister)

---

## Implementation Plan

### Phase 1: Add EventStore to BaseMagister

**File:** `src/meai/agents/magisters/base_magister.py`

**Changes:**
1. Import EventStore
2. Add event_store parameter to __init__
3. Connect EventStore to EventBus in initialize()
4. Update all Magister constructors to pass event_store

**Code:**
```python
# In __init__
from meai.events import EventStore

def __init__(
    self,
    agent_id: str,
    magister_type: str,
    domain: str,
    event_bus: EventBus,
    event_store: EventStore,  # Add this
    vault_path: Path,
    database_url: str = "sqlite+aiosqlite:///./data/meai.db",
):
    # ...
    self.event_store = event_store

# In initialize()
async def initialize(self) -> None:
    # ...
    # Connect EventStore to EventBus
    self.event_bus.set_event_store(self.event_store)
```

### Phase 2: Update All Magisters

**Files (9 total):**
- seo_magister.py
- content_magister.py
- ads_magister.py
- analytics_magister.py
- social_magister.py
- intelligence_magister.py
- brand_magister.py
- reputation_magister.py
- ai_magister.py

**Changes per file:**
```python
def __init__(
    self,
    agent_id: str,
    event_bus: EventBus,
    event_store: EventStore,  # Add this
    vault_path: Path,
    database_url: str = "sqlite+aiosqlite:///./data/meai.db",
):
    super().__init__(
        agent_id=agent_id,
        magister_type="seo",  # or content, ads, etc.
        domain="seo",
        event_bus=event_bus,
        event_store=event_store,  # Add this
        vault_path=vault_path,
        database_url=database_url,
    )
```

### Phase 3: Update Factory/Tests

**Files:**
- Any factory methods creating Magisters
- Test files

**Changes:**
- Pass EventStore instance when creating Magisters

---

## Testing Strategy

1. Unit test: BaseMagister with EventStore
2. Integration test: Magister publishes event → EventStore has it
3. Regression test: All existing tests still pass

---

## Execution

**Approach:** Subagent-Driven Development
- Task 1: BaseMagister integration
- Task 2: Update all 9 Magisters
- Task 3: Update tests
- Task 4: Verification

**Estimated time:** 1-2 hours

---

## Success Criteria

✅ BaseMagister accepts EventStore parameter
✅ EventStore connected to EventBus in initialize()
✅ All 9 Magisters updated
✅ All tests passing
✅ Events from Magisters appear in EventStore
✅ Complete audit trail for all Magister operations
