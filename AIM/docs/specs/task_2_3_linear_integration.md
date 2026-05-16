# Task 2.3: Linear Integration

**Estimated Time:** 12 hours  
**Priority:** High  
**Dependencies:** Task 2.2 (AI Lead Scoring)

## Overview

Автоматическое создание задач в Linear для Hot leads (score >= 80) с назначением на sales team и отслеживанием статуса.

## Goals

1. **Автоматизация:** Создавать Linear задачи для Hot leads без ручного вмешательства
2. **Приоритизация:** Hot leads получают задачи немедленно, Warm leads - через 1 час
3. **Отслеживание:** Синхронизация статуса задач между Linear и AIM
4. **Уведомления:** Slack/Telegram уведомления для sales team

## Architecture

```
Lead Capture
    ↓
AI Lead Scoring (Task 2.2)
    ↓
Linear Integration (Task 2.3)
    ↓
    ├─ Hot Lead (score >= 80) → Create Linear Task (immediate)
    ├─ Warm Lead (50-79) → Create Linear Task (delayed 1h)
    └─ Cold Lead (< 50) → No task (email automation only)
```

## Components

### 1. Linear Client (`AIM/src/aim/integrations/linear/client.py`)

**Purpose:** API client for Linear GraphQL API

**Features:**
- GraphQL query/mutation execution
- Authentication with API key
- Rate limiting (100 req/min)
- Retry with exponential backoff
- Error handling

**Key Methods:**
```python
class LinearClient:
    async def create_issue(
        self,
        team_id: str,
        title: str,
        description: str,
        priority: int,
        labels: list[str],
        assignee_id: str | None = None,
    ) -> LinearIssue
    
    async def update_issue(
        self,
        issue_id: str,
        state_id: str | None = None,
        assignee_id: str | None = None,
    ) -> LinearIssue
    
    async def get_issue(self, issue_id: str) -> LinearIssue
    
    async def list_teams(self) -> list[LinearTeam]
    
    async def list_workflow_states(self, team_id: str) -> list[LinearWorkflowState]
```

### 2. Linear Service (`AIM/src/aim/integrations/linear/service.py`)

**Purpose:** Business logic for Linear integration

**Features:**
- Create tasks for Hot/Warm leads
- Assign tasks to sales team (round-robin)
- Update task status based on lead progress
- Sync Linear status back to AIM database

**Key Methods:**
```python
class LinearService:
    async def create_task_for_lead(
        self,
        lead: Lead,
        score_result: LeadScore,
    ) -> LinearTask
    
    async def update_task_status(
        self,
        task_id: str,
        status: str,
    ) -> None
    
    async def sync_task_status(
        self,
        task_id: str,
    ) -> None
    
    async def get_next_assignee(self) -> str
```

### 3. Linear Schemas (`AIM/src/aim/integrations/linear/schemas.py`)

**Purpose:** Pydantic models for Linear data

**Models:**
```python
class LinearIssue(BaseModel):
    id: str
    title: str
    description: str
    priority: int
    state: LinearWorkflowState
    assignee: LinearUser | None
    labels: list[LinearLabel]
    url: str
    created_at: datetime
    updated_at: datetime

class LinearTask(BaseModel):
    id: str
    lead_id: str
    linear_issue_id: str
    linear_url: str
    status: str
    assignee_id: str | None
    created_at: datetime
    updated_at: datetime

class LinearTeam(BaseModel):
    id: str
    name: str
    key: str

class LinearWorkflowState(BaseModel):
    id: str
    name: str
    type: str  # "backlog", "unstarted", "started", "completed", "canceled"

class LinearUser(BaseModel):
    id: str
    name: str
    email: str

class LinearLabel(BaseModel):
    id: str
    name: str
    color: str
```

### 4. Database Model (`AIM/src/aim/models/linear_task.py`)

**Purpose:** Store Linear task metadata in AIM database

**Schema:**
```python
class LinearTask(Base):
    __tablename__ = "linear_tasks"
    
    id: Mapped[str] = mapped_column(String, primary_key=True)
    lead_id: Mapped[str] = mapped_column(String, ForeignKey("leads.id"), nullable=False)
    linear_issue_id: Mapped[str] = mapped_column(String, nullable=False, unique=True)
    linear_url: Mapped[str] = mapped_column(String, nullable=False)
    status: Mapped[str] = mapped_column(String, nullable=False)  # "backlog", "in_progress", "completed", "canceled"
    assignee_id: Mapped[str | None] = mapped_column(String, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    
    # Relationship
    lead: Mapped["Lead"] = relationship("Lead", back_populates="linear_tasks")
```

### 5. Configuration (`AIM/src/aim/config/settings.py`)

**Environment Variables:**
```python
class LinearSettings(BaseSettings):
    linear_api_key: str = Field(..., description="Linear API key")
    linear_team_id: str = Field(..., description="Linear team ID for sales")
    linear_hot_label_id: str = Field(..., description="Label ID for Hot leads")
    linear_warm_label_id: str = Field(..., description="Label ID for Warm leads")
    linear_assignees: list[str] = Field(default_factory=list, description="List of assignee IDs for round-robin")
    linear_rate_limit: int = Field(default=100, description="Rate limit (req/min)")
```

## Task Creation Logic

### Priority Mapping

```python
PRIORITY_MAP = {
    "Hot": 1,    # Urgent (Linear priority 1)
    "Warm": 2,   # High (Linear priority 2)
    "Cold": 4,   # Low (Linear priority 4) - not created by default
}
```

### Task Title Format

```python
def generate_task_title(lead: Lead, score: int, tier: str) -> str:
    specialty = lead.specialty.replace("_", " ").title()
    return f"[{tier}] {specialty} Lead - Score {score}"

# Examples:
# "[Hot] Plastic Surgery Lead - Score 87"
# "[Warm] Dentistry Lead - Score 65"
```

### Task Description Format

```python
def generate_task_description(lead: Lead, score_result: LeadScore) -> str:
    # Decrypt sensitive fields for sales team
    name = decrypt(lead.name_encrypted)
    phone = decrypt(lead.phone_encrypted)
    email = decrypt(lead.email_encrypted)
    clinic = decrypt(lead.clinic_name_encrypted)
    message = decrypt(lead.message_encrypted) if lead.message_encrypted else "N/A"
    
    # Format explanation
    explanation = "\n".join(f"- {item}" for item in score_result.explanation)
    
    return f"""
## Lead Information

**Name:** {name}  
**Phone:** {phone}  
**Email:** {email}  
**Clinic:** {clinic}  
**Specialty:** {lead.specialty.replace("_", " ").title()}

## Message

{message}

## Scoring Details

**Score:** {score_result.score}/100  
**Tier:** {score_result.tier}

**Why this lead scored high:**
{explanation}

## Source

**Traffic Source:** {lead.source}  
**UTM Campaign:** {lead.utm_campaign or "N/A"}  
**Submitted:** {lead.created_at.strftime("%Y-%m-%d %H:%M UTC")}

## Next Steps

1. Call within 15 minutes (Hot leads)
2. Verify specialty and clinic details
3. Schedule consultation
4. Update task status in Linear
"""
```

### Delay Logic

```python
async def create_task_with_delay(lead: Lead, score_result: LeadScore):
    if score_result.tier == "Hot":
        # Immediate creation
        await linear_service.create_task_for_lead(lead, score_result)
    elif score_result.tier == "Warm":
        # Delayed 1 hour
        await asyncio.sleep(3600)
        await linear_service.create_task_for_lead(lead, score_result)
    else:
        # Cold leads: no task, email automation only
        pass
```

## Status Synchronization

### Linear → AIM Sync

**Webhook Handler:**
```python
@router.post("/webhooks/linear")
async def linear_webhook(
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    payload = await request.json()
    
    if payload["action"] == "update" and payload["type"] == "Issue":
        issue_id = payload["data"]["id"]
        new_state = payload["data"]["state"]["name"]
        
        # Update AIM database
        await linear_service.sync_task_status(issue_id)
        
        # Update lead status if task completed
        if new_state == "Done":
            await update_lead_status(issue_id, "contacted")
    
    return {"status": "ok"}
```

### AIM → Linear Sync

**Trigger:** When lead status changes in AIM (e.g., "contacted", "qualified", "converted")

```python
async def update_lead_status(lead_id: str, new_status: str):
    # Find Linear task
    task = await db.execute(
        select(LinearTask).where(LinearTask.lead_id == lead_id)
    )
    task = task.scalar_one_or_none()
    
    if task:
        # Map AIM status to Linear state
        linear_state = STATUS_MAP.get(new_status)
        if linear_state:
            await linear_client.update_issue(
                issue_id=task.linear_issue_id,
                state_id=linear_state,
            )
```

## Round-Robin Assignment

**Algorithm:**
```python
class LinearService:
    def __init__(self):
        self._assignee_index = 0
        self._assignees = settings.linear_assignees
    
    async def get_next_assignee(self) -> str:
        if not self._assignees:
            return None
        
        assignee = self._assignees[self._assignee_index]
        self._assignee_index = (self._assignee_index + 1) % len(self._assignees)
        return assignee
```

## Error Handling

### Retry Strategy

```python
@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=1, max=10),
    retry=retry_if_exception_type((httpx.HTTPError, httpx.TimeoutException)),
)
async def create_issue_with_retry(...):
    ...
```

### Fallback

```python
async def create_task_for_lead(lead: Lead, score_result: LeadScore):
    try:
        task = await linear_client.create_issue(...)
        await db.add(LinearTask(...))
        await db.commit()
    except Exception as e:
        # Log error
        logger.error(f"Failed to create Linear task for lead {lead.id}: {e}")
        
        # Fallback: Send Slack notification
        await slack_client.send_message(
            channel="#sales-alerts",
            text=f"⚠️ Failed to create Linear task for Hot lead {lead.id}. Manual action required.",
        )
        
        # Don't fail lead capture
        pass
```

## Testing Strategy

### Unit Tests

**Test Coverage:**
- Linear client GraphQL queries
- Task creation logic
- Priority mapping
- Description generation
- Round-robin assignment
- Status synchronization
- Error handling

**Example Tests:**
```python
@pytest.mark.asyncio
async def test_create_task_for_hot_lead():
    """Should create Linear task immediately for Hot lead"""
    lead = create_hot_lead()
    score_result = LeadScore(score=85, tier="Hot", ...)
    
    task = await linear_service.create_task_for_lead(lead, score_result)
    
    assert task.linear_issue_id is not None
    assert task.status == "backlog"
    assert task.assignee_id in settings.linear_assignees

@pytest.mark.asyncio
async def test_round_robin_assignment():
    """Should assign tasks in round-robin fashion"""
    assignees = ["user1", "user2", "user3"]
    service = LinearService(assignees=assignees)
    
    assignments = [await service.get_next_assignee() for _ in range(6)]
    
    assert assignments == ["user1", "user2", "user3", "user1", "user2", "user3"]

@pytest.mark.asyncio
async def test_sync_task_status():
    """Should sync Linear status to AIM database"""
    task = create_linear_task()
    
    # Simulate Linear webhook
    await linear_service.sync_task_status(task.linear_issue_id)
    
    # Check database updated
    updated_task = await db.get(LinearTask, task.id)
    assert updated_task.status == "completed"
```

### Integration Tests

**Test Scenarios:**
1. End-to-end: Lead capture → Scoring → Linear task creation
2. Webhook: Linear status update → AIM database sync
3. Error handling: Linear API failure → Slack notification

## Implementation Plan

### Phase 1: Linear Client (4 hours)

1. Create `linear/client.py` with GraphQL client
2. Implement authentication and rate limiting
3. Add retry logic and error handling
4. Write unit tests (10 tests)

### Phase 2: Linear Service (4 hours)

1. Create `linear/service.py` with business logic
2. Implement task creation with priority mapping
3. Add round-robin assignment
4. Implement status synchronization
5. Write unit tests (15 tests)

### Phase 3: Database Integration (2 hours)

1. Create `models/linear_task.py`
2. Add migration for `linear_tasks` table
3. Update `Lead` model with relationship
4. Test database operations

### Phase 4: Webhook Handler (2 hours)

1. Create webhook endpoint in FastAPI
2. Implement Linear → AIM sync
3. Add webhook signature verification
4. Test webhook handling

## Configuration

### Environment Variables

Add to `.env`:
```bash
# Linear Integration
LINEAR_API_KEY=lin_api_...
LINEAR_TEAM_ID=team_abc123
LINEAR_HOT_LABEL_ID=label_hot123
LINEAR_WARM_LABEL_ID=label_warm123
LINEAR_ASSIGNEES=user_id1,user_id2,user_id3
LINEAR_RATE_LIMIT=100
```

### Linear Setup

1. **Create API Key:**
   - Go to Linear Settings → API
   - Create new API key with permissions: `read`, `write`

2. **Get Team ID:**
   ```graphql
   query {
     teams {
       nodes {
         id
         name
         key
       }
     }
   }
   ```

3. **Create Labels:**
   - "Hot Lead" (red)
   - "Warm Lead" (orange)

4. **Get Assignee IDs:**
   ```graphql
   query {
     users {
       nodes {
         id
         name
         email
       }
     }
   }
   ```

5. **Setup Webhook:**
   - URL: `https://iamaim.ru/api/webhooks/linear`
   - Events: `Issue` (create, update, delete)
   - Secret: Generate and store in `.env`

## Cost Analysis

**Linear Pricing:**
- Free tier: 250 issues/month
- Standard: $8/user/month (unlimited issues)

**Expected Usage:**
- 100 leads/month
- 60% Hot/Warm (60 Linear tasks)
- Well within free tier

## Success Metrics

**Automation:**
- 100% Hot leads get Linear tasks within 1 minute
- 100% Warm leads get Linear tasks within 1 hour
- 0% manual task creation

**Response Time:**
- Average time from lead capture to sales contact: < 15 minutes (Hot)
- Average time from lead capture to sales contact: < 2 hours (Warm)

**Conversion:**
- Hot lead → Qualified: 40%+
- Warm lead → Qualified: 20%+

## Next Steps

After Task 2.3 completion:
- **Task 2.4:** Email Automation (10h) - Send follow-up emails by tier
- **Task 2.5:** Analytics Dashboard (10h) - Visualize lead scoring and Linear metrics

## References

- [Linear API Documentation](https://developers.linear.app/docs/graphql/working-with-the-graphql-api)
- [Linear GraphQL Schema](https://studio.apollographql.com/public/Linear-API/variant/current/home)
- [Linear Webhooks](https://developers.linear.app/docs/graphql/webhooks)
