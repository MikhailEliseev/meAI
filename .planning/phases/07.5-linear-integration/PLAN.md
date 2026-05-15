# Phase 7.5: Linear Integration & Project Structure

**Status:** IN PROGRESS (2026-05-15)  
**Duration:** 4-6 hours (estimated)  
**Progress:** 50% (Part 1-2 completed)

---

## Overview

**Goal:** Integrate Linear for project management + Setup AIM as Project #0 (сапожник с сапогами)

**Why Phase 7.5:**
- Urgent need for project management visibility
- Foundation for Phase 8 (multi-tenant frontend)
- AIM должен быть проектом номер 0 - сам себя продвигать
- Transparency для клиентов

**Key Concept:** AIM Development = Project #0
- Разработка AIM отслеживается в Linear
- Маркетинг AIM отслеживается в Linear
- AIM использует сам себя для управления проектами
- Демонстрация возможностей для клиентов

---

## Part 1: Linear CLI Integration ✅ COMPLETED

**Time:** 26 minutes (12:28-12:54 GMT+3)

**Deliverables:**
- ✅ GraphQL API client (`scripts/linear_cli.py`, 479 lines)
- ✅ 7 commands: list, show, create, update, comment, teams, states
- ✅ Wrapper script with auto API key (`scripts/linear`)
- ✅ Documentation (`docs/LINEAR_INTEGRATION.md`, 200+ lines)
- ✅ Testing completed (MIK-5 task created, updated, completed)

**Files:**
- `scripts/linear_cli.py` - Full CLI implementation
- `scripts/linear` - Wrapper with auto API key
- `docs/LINEAR_INTEGRATION.md` - Complete guide

**Commit:** 7e08964

---

## Part 2: Linear Structure Setup ✅ COMPLETED

**Goal:** Create Teams, Projects, and Labels in Linear

**Estimated Time:** 1-1.5 hours

**Actual Time:** 1.5 hours (2026-05-15 12:54-14:24 GMT+3)

**Deliverables:**
- ✅ 6 Teams created (DEV, MKT, SEO, CNT, ADS, ANL)
- ✅ Project #0: AIM Development (ID: cfde805b-64a9-4351-b7e3-61de2b21a8e3)
- ✅ Project #0.1: AIM Marketing (ID: 09301e27-8ead-4b22-99ed-e953b049f2a8)
- ✅ 17 Labels created (priority: P0-P3, type: bug/feature/docs/test/refactor/deploy/design, domain: seo/content/ads/analytics/infrastructure/automation)
- ✅ 22 Tasks created:
  - Milestone 1: DEV-1 to DEV-7 (retrospective, marked as Done)
  - Milestone 2: DEV-8 to DEV-12 (DEV-8, DEV-9 Done; DEV-10, DEV-11, DEV-12 Todo)
  - Milestone 3: DEV-13 to DEV-14 (future, marked as Todo)
  - Marketing: MKT-1 to MKT-8 (all Todo)

**Files Created:**
- `scripts/setup_linear_structure.py` (388 lines) - Automated setup script

**Commit:** TBD

---

## Part 3: Operator ↔ Linear Integration ⏳ TODO

**Goal:** Automatic task creation and status updates

**Estimated Time:** 2-3 hours

### 3.1 Operator Integration

**File:** `src/meai/agents/operator.py`

**Changes needed:**

```python
class Operator:
    def __init__(self, linear_client: Optional[LinearClient] = None):
        self.linear_client = linear_client
    
    async def delegate_to_agent(self, task: Task) -> None:
        """Delegate task to agent and create Linear task."""
        # Existing delegation logic
        await self._publish_task_event(task)
        
        # NEW: Create Linear task
        if self.linear_client:
            linear_task = await self.linear_client.create_issue(
                title=task.description,
                description=self._format_task_description(task),
                team_id=self._get_team_for_agent(task.agent_type),
                priority=self._map_priority(task.priority),
            )
            
            # Store Linear task ID for future updates
            task.metadata["linear_task_id"] = linear_task["id"]
            
            await self._log_linear_task_created(task, linear_task)
```

### 3.2 Magister Integration

**File:** `AIM/src/aim/magisters/base_magister.py`

**Changes needed:**

```python
class BaseMagister:
    async def complete_task(self, result: TaskResult) -> None:
        """Complete task and update Linear."""
        # Existing completion logic
        await self._publish_result_event(result)
        
        # NEW: Update Linear task
        if self.linear_client and result.task.metadata.get("linear_task_id"):
            await self.linear_client.update_issue(
                issue_id=result.task.metadata["linear_task_id"],
                state_id=self._get_done_state_id(),
            )
            
            await self.linear_client.add_comment(
                issue_id=result.task.metadata["linear_task_id"],
                body=self._format_completion_comment(result),
            )
```

### 3.3 Configuration

**File:** `AIM/src/aim/config/settings.py`

**Add Linear settings:**

```python
class Settings(BaseSettings):
    # Existing settings...
    
    # Linear Integration
    linear_api_key: Optional[str] = None
    linear_enabled: bool = False
    linear_team_mapping: dict[str, str] = {
        "seo": "SEO",
        "content": "CNT",
        "ads": "ADS",
        "analytics": "ANL",
    }
```

**Tasks:**
- [ ] Add LinearClient to Operator
- [ ] Implement auto-create on delegation
- [ ] Add LinearClient to BaseMagister
- [ ] Implement auto-update on completion
- [ ] Add Linear settings to config
- [ ] Test end-to-end workflow
- [ ] Add error handling for Linear API failures

---

## Part 4: Client Dashboard ⏳ TODO

**Goal:** Client-specific project views in Linear

**Estimated Time:** 1-1.5 hours

### 4.1 Client Project Template

**Structure:**

```
Project: Client A - Full Service (Team: SEO)
│
├── SEO Campaign
│   ├── Keyword Research ⏳
│   ├── Competitor Analysis ⏳
│   └── Content Optimization ⏳
│
├── Content Creation (linked to Content team)
│   ├── Blog Post #1 ⏳
│   └── Blog Post #2 ⏳
│
└── Ads Campaign (linked to Ads team)
    └── Yandex Direct Setup ⏳
```

### 4.2 Progress Tracking

**Metrics to track:**
- Tasks completed / total tasks
- Budget spent / total budget
- Timeline progress (on track / at risk / behind)
- Quality score (from Magisters)

### 4.3 Client Access

**Setup:**
- Create guest user for client
- Grant read-only access to their project
- Setup email notifications for updates
- Weekly progress reports

**Tasks:**
- [ ] Create client project template
- [ ] Implement progress tracking
- [ ] Setup guest user access
- [ ] Configure notifications
- [ ] Test client view

---

## Success Criteria

**Part 1:** ✅ COMPLETED
- [x] Linear CLI working
- [x] All commands tested
- [x] Documentation complete

**Part 2:** ⏳ TODO
- [ ] 6 Teams created in Linear
- [ ] Project #0 "AIM Development" created
- [ ] Project #0.1 "AIM Marketing" created
- [ ] All labels created
- [ ] Milestone 1-3 tasks created

**Part 3:** ⏳ TODO
- [ ] Operator creates Linear tasks automatically
- [ ] Magisters update task status automatically
- [ ] Comments synced to Linear
- [ ] Error handling works

**Part 4:** ⏳ TODO
- [ ] Client project template ready
- [ ] Progress tracking implemented
- [ ] Guest access configured
- [ ] Client can view their project

---

## Dependencies

**Requires:**
- Phase 7 (Production Deployment) - ✅ COMPLETED
- Linear CLI - ✅ COMPLETED

**Blocks:**
- Phase 8 (Multi-Tenant Frontend) - needs project structure

---

## Timeline

**Total Estimated:** 4-6 hours

- Part 1: Linear CLI - ✅ 26 minutes (COMPLETED)
- Part 2: Structure Setup - ⏳ 1-1.5 hours (TODO)
- Part 3: Operator Integration - ⏳ 2-3 hours (TODO)
- Part 4: Client Dashboard - ⏳ 1-1.5 hours (TODO)

**Current Progress:** 25% (Part 1 completed)

---

**Created:** 2026-05-15 13:10 GMT+3  
**Last Updated:** 2026-05-15 13:10 GMT+3
