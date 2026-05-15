# Phase 7.5: Linear Integration & Project Structure

**Status:** IN PROGRESS (2026-05-15)  
**Duration:** 4-6 hours (estimated)  
**Progress:** 25% (Part 1 completed)

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

## Part 2: Linear Structure Setup ⏳ TODO

**Goal:** Create Teams, Projects, and Labels in Linear

**Estimated Time:** 1-1.5 hours

### 2.1 Create Teams

**Teams to create:**

1. **AIM Development** (Team Key: DEV)
   - Description: "Core AIM platform development"
   - Members: Mikhail Eliseev
   - Workflow: Todo → In Progress → Review → Done

2. **AIM Marketing** (Team Key: MKT)
   - Description: "AIM self-promotion and growth"
   - Members: Mikhail Eliseev
   - Workflow: Todo → In Progress → Review → Done

3. **SEO Services** (Team Key: SEO)
   - Description: "Client SEO campaigns"
   - Members: SEO Magister (bot)
   - Workflow: Todo → In Progress → Review → Done

4. **Content Services** (Team Key: CNT)
   - Description: "Client content creation"
   - Members: Content Magister (bot)
   - Workflow: Todo → In Progress → Review → Done

5. **Ads Services** (Team Key: ADS)
   - Description: "Client advertising campaigns"
   - Members: Ads Magister (bot)
   - Workflow: Todo → In Progress → Review → Done

6. **Analytics Services** (Team Key: ANL)
   - Description: "Client analytics and reporting"
   - Members: Analytics Magister (bot)
   - Workflow: Todo → In Progress → Review → Done

### 2.2 Create Project #0: AIM Development

**Project Structure:**

```
Project #0: AIM Development (Team: AIM Development)
│
├── Milestone 1: Core Infrastructure ✅ COMPLETED
│   ├── Phase 1: Foundation ✅
│   ├── Phase 2: Event Flow ✅
│   ├── Phase 3: API Integration ✅
│   ├── Phase 4: Magister Tests ✅
│   ├── Phase 5: Subagent Tests ✅
│   ├── Phase 6: E2E Tests ✅
│   └── Phase 7: Production Deployment ✅
│
├── Milestone 2: Project Management 🔄 IN PROGRESS
│   ├── Phase 7.5: Linear Integration 🔄
│   └── Phase 8: Multi-Tenant Frontend ⏳
│
└── Milestone 3: Client Acquisition ⏳ PLANNED
    ├── Phase 9: Marketing Automation ⏳
    └── Phase 10: First Client Onboarding ⏳
```

**Tasks to create in Linear:**

**Milestone 1 (Retrospective - mark as Done):**
- DEV-1: Foundation - Base classes and infrastructure ✅
- DEV-2: Event Flow - Async coordination ✅
- DEV-3: API Integration - Real API clients ✅
- DEV-4: Magister Tests - Production orchestrators ✅
- DEV-5: Subagent Tests - P1 subagents training ✅
- DEV-6: E2E Tests - Multi-agent coordination ✅
- DEV-7: Production Deployment - SSL/TLS and monitoring ✅

**Milestone 2 (Current):**
- DEV-8: Linear CLI Integration ✅ (completed today)
- DEV-9: Linear Structure Setup ⏳ (this task)
- DEV-10: Operator ↔ Linear Integration ⏳
- DEV-11: Client Dashboard in Linear ⏳
- DEV-12: Multi-Tenant Frontend ⏳

**Milestone 3 (Future):**
- DEV-13: Marketing Automation ⏳
- DEV-14: First Client Onboarding ⏳

### 2.3 Create Project #0.1: AIM Marketing

**Project Structure:**

```
Project #0.1: AIM Marketing (Team: AIM Marketing)
│
├── Content Strategy
│   ├── MKT-1: Blog content plan ⏳
│   ├── MKT-2: Case studies ⏳
│   └── MKT-3: Social media strategy ⏳
│
├── SEO Strategy
│   ├── MKT-4: Keyword research for iamaim.ru ⏳
│   ├── MKT-5: Technical SEO audit ⏳
│   └── MKT-6: Content optimization ⏳
│
└── Ads Strategy
    ├── MKT-7: Yandex Direct campaign ⏳
    └── MKT-8: Google Ads campaign ⏳
```

**Why separate project:**
- AIM Development = building the product
- AIM Marketing = promoting the product
- Different workflows and priorities
- Demonstrates multi-project management

### 2.4 Setup Labels

**Priority Labels:**
- 🔴 P0 - Critical (blocks production)
- 🟠 P1 - High (important for milestone)
- 🟡 P2 - Medium (nice to have)
- 🟢 P3 - Low (future enhancement)

**Type Labels:**
- 🐛 bug - Bug fix
- ✨ feature - New feature
- 📝 docs - Documentation
- 🧪 test - Testing
- 🔧 refactor - Code refactoring
- 🚀 deploy - Deployment
- 🎨 design - UI/UX design

**Domain Labels:**
- 🔍 seo - SEO related
- ✍️ content - Content related
- 📢 ads - Advertising related
- 📊 analytics - Analytics related
- 🏗️ infrastructure - Infrastructure
- 🤖 automation - Automation

### 2.5 Implementation Script

Create `scripts/setup_linear_structure.py`:

```python
#!/usr/bin/env python3
"""
Setup Linear structure for AIM Agency.

Creates:
- 6 Teams (AIM Development, AIM Marketing, SEO, Content, Ads, Analytics)
- Project #0: AIM Development
- Project #0.1: AIM Marketing
- Labels (priority, type, domain)
- Initial tasks for Milestone 1-3
"""

from scripts.linear_cli import LinearClient
import os

def setup_teams(client: LinearClient):
    """Create teams."""
    teams = [
        {"name": "AIM Development", "key": "DEV", "description": "Core AIM platform development"},
        {"name": "AIM Marketing", "key": "MKT", "description": "AIM self-promotion and growth"},
        {"name": "SEO Services", "key": "SEO", "description": "Client SEO campaigns"},
        {"name": "Content Services", "key": "CNT", "description": "Client content creation"},
        {"name": "Ads Services", "key": "ADS", "description": "Client advertising campaigns"},
        {"name": "Analytics Services", "key": "ANL", "description": "Client analytics and reporting"},
    ]
    
    for team in teams:
        print(f"Creating team: {team['name']}...")
        # TODO: Implement team creation via GraphQL
    
def setup_projects(client: LinearClient):
    """Create projects."""
    projects = [
        {
            "name": "AIM Development",
            "team": "DEV",
            "description": "Building the AIM platform",
        },
        {
            "name": "AIM Marketing",
            "team": "MKT",
            "description": "Promoting AIM to clients",
        },
    ]
    
    for project in projects:
        print(f"Creating project: {project['name']}...")
        # TODO: Implement project creation via GraphQL

def setup_labels(client: LinearClient):
    """Create labels."""
    labels = [
        # Priority
        {"name": "P0 - Critical", "color": "#FF0000"},
        {"name": "P1 - High", "color": "#FF8800"},
        {"name": "P2 - Medium", "color": "#FFFF00"},
        {"name": "P3 - Low", "color": "#00FF00"},
        # Type
        {"name": "bug", "color": "#FF0000"},
        {"name": "feature", "color": "#0088FF"},
        {"name": "docs", "color": "#888888"},
        # Domain
        {"name": "seo", "color": "#8800FF"},
        {"name": "content", "color": "#FF00FF"},
        {"name": "ads", "color": "#FF8800"},
    ]
    
    for label in labels:
        print(f"Creating label: {label['name']}...")
        # TODO: Implement label creation via GraphQL

def create_milestone_1_tasks(client: LinearClient):
    """Create retrospective tasks for Milestone 1."""
    tasks = [
        {"title": "Foundation - Base classes and infrastructure", "state": "Done"},
        {"title": "Event Flow - Async coordination", "state": "Done"},
        {"title": "API Integration - Real API clients", "state": "Done"},
        {"title": "Magister Tests - Production orchestrators", "state": "Done"},
        {"title": "Subagent Tests - P1 subagents training", "state": "Done"},
        {"title": "E2E Tests - Multi-agent coordination", "state": "Done"},
        {"title": "Production Deployment - SSL/TLS and monitoring", "state": "Done"},
    ]
    
    for task in tasks:
        print(f"Creating task: {task['title']}...")
        # TODO: Implement task creation

def main():
    api_key = os.getenv("LINEAR_API_KEY")
    if not api_key:
        print("Error: LINEAR_API_KEY not set")
        return
    
    client = LinearClient(api_key)
    
    print("Setting up Linear structure for AIM Agency...")
    print()
    
    setup_teams(client)
    setup_projects(client)
    setup_labels(client)
    create_milestone_1_tasks(client)
    
    print()
    print("✅ Linear structure setup complete!")

if __name__ == "__main__":
    main()
```

**Tasks:**
- [ ] Implement team creation via GraphQL
- [ ] Implement project creation via GraphQL
- [ ] Implement label creation via GraphQL
- [ ] Create all Milestone 1 tasks (retrospective)
- [ ] Create all Milestone 2 tasks (current)
- [ ] Create all Milestone 3 tasks (future)
- [ ] Test script end-to-end

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
