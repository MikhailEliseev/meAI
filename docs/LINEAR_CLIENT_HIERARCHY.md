# Linear Client Hierarchy Structure

## Overview

Правильная иерархия для клиентских проектов в Linear.

## Structure

```
Teams (верхний уровень)
├── DEV: AIM Development (внутренняя разработка)
├── MKT: AIM Marketing (внутренний маркетинг)
└── CLI: Client Projects (клиентские проекты)
    │
    ├── Client A
    │   └── Project: Full Service
    │       ├── [Client A] SEO: Keyword Research
    │       ├── [Client A] SEO: Competitor Analysis
    │       ├── [Client A] SEO: On-Page Optimization
    │       ├── [Client A] SEO: Link Building
    │       ├── [Client A] Content: Strategy Development
    │       ├── [Client A] Content: Blog Creation
    │       ├── [Client A] Content: Social Media
    │       ├── [Client A] Content: Email Marketing
    │       ├── [Client A] Ads: Yandex Direct Setup
    │       ├── [Client A] Ads: Campaign Optimization
    │       └── [Client A] Ads: Campaign Scaling
    │
    └── Client B
        └── Project: SEO Only
            ├── [Client B] SEO: Keyword Research
            ├── [Client B] SEO: Competitor Analysis
            ├── [Client B] SEO: On-Page Optimization
            └── [Client B] SEO: Link Building
```

## Key Principles

### 1. Teams = Internal Organization

**DEV Team:**
- AIM Development tasks
- Internal infrastructure
- System improvements

**MKT Team:**
- AIM Marketing tasks
- Our own promotion
- Brand building

**CLI Team:**
- ALL client projects
- Client transparency
- Service delivery

### 2. Projects = Client Hierarchy

Each client gets their own project(s) in CLI team:
- Client Name → Project Name
- One client can have multiple projects
- Each project contains service tasks

### 3. Tasks = Service Delivery

Tasks are organized by service type:
- **SEO:** `[Client] SEO: Task Name`
- **Content:** `[Client] Content: Task Name`
- **Ads:** `[Client] Ads: Task Name`
- **Analytics:** `[Client] Analytics: Task Name`

### 4. Service Identification

Each task includes:
- **Title prefix:** `[Client Name] Service: Task`
- **Description field:** `**Service:** SEO/Content/Ads/Analytics`
- **Labels:** (optional) `seo`, `content`, `ads`, `analytics`

## Why This Structure?

### ✅ Correct Hierarchy

```
Client (top level)
  └─ Project (service package)
      └─ Tasks (deliverables)
```

This matches real business structure:
- One client, multiple projects
- One project, multiple services
- One service, multiple tasks

### ❌ Wrong Hierarchy (old)

```
Service Team (top level)
  └─ Client Project
      └─ Tasks
```

Problems:
- Client split across multiple teams
- No single client view
- Hard to track overall progress

## Creating Client Projects

### Using Script

```bash
python scripts/create_client_project.py "Client Name" \
  --services seo,content,ads \
  --budget 100000 \
  --timeline 12
```

This creates:
- Project in CLI team
- 11 tasks (4 SEO + 4 Content + 3 Ads)
- Budget allocation per task
- Timeline per task

### Manual Creation

1. Go to CLI team in Linear
2. Create new project: "Client Name - Service Package"
3. Add tasks with format: `[Client Name] Service: Task Name`
4. Include `**Service:** Type` in description

## Guest Access

Clients get read-only access to their project:

1. Invite guest user (client email)
2. Grant access to specific project
3. Client sees:
   - Their project only
   - All tasks and progress
   - Comments and updates
   - Timeline and budget

See `docs/LINEAR_CLIENT_ACCESS.md` for details.

## Progress Tracking

Use `ProgressTracker` to monitor:
- **Tasks:** Completed / Total
- **Budget:** Spent / Total
- **Timeline:** On track / At risk / Behind
- **Quality:** Scores from Magisters

See `src/meai/tracking/progress_tracker.py` for implementation.

## Migration from Old Structure

Old service teams (SEO, CNT, ADS, ANL) remain but are not used for new client projects.

All new client projects go to CLI team.

To reorganize:
```bash
python scripts/reorganize_linear_structure.py
```

This creates CLI team and documents the new structure.

## Examples

### Example 1: Full Service Client

**Client:** Medical Clinic "Здоровье"
**Services:** SEO, Content, Ads
**Budget:** 150,000 ₽
**Timeline:** 12 weeks

**Structure:**
```
CLI Team
  └─ Project: Здоровье - Full Service
      ├─ [Здоровье] SEO: Keyword Research (Week 1-2, 22,500 ₽)
      ├─ [Здоровье] SEO: Competitor Analysis (Week 2-3, 22,500 ₽)
      ├─ [Здоровье] SEO: On-Page Optimization (Week 3-6, 52,500 ₽)
      ├─ [Здоровье] SEO: Link Building (Week 6-12, 52,500 ₽)
      ├─ [Здоровье] Content: Strategy (Week 1-2, 30,000 ₽)
      ├─ [Здоровье] Content: Blog Creation (Week 2-8, 60,000 ₽)
      ├─ [Здоровье] Content: Social Media (Week 2-12, 37,500 ₽)
      ├─ [Здоровье] Content: Email Marketing (Week 4-12, 22,500 ₽)
      ├─ [Здоровье] Ads: Yandex Direct Setup (Week 1-2, 30,000 ₽)
      ├─ [Здоровье] Ads: Campaign Optimization (Week 2-6, 45,000 ₽)
      └─ [Здоровье] Ads: Campaign Scaling (Week 6-12, 75,000 ₽)
```

### Example 2: SEO Only Client

**Client:** Dental Clinic "Улыбка"
**Services:** SEO
**Budget:** 50,000 ₽
**Timeline:** 12 weeks

**Structure:**
```
CLI Team
  └─ Project: Улыбка - SEO Campaign
      ├─ [Улыбка] SEO: Keyword Research (Week 1-2, 7,500 ₽)
      ├─ [Улыбка] SEO: Competitor Analysis (Week 2-3, 7,500 ₽)
      ├─ [Улыбка] SEO: On-Page Optimization (Week 3-6, 17,500 ₽)
      └─ [Улыбка] SEO: Link Building (Week 6-12, 17,500 ₽)
```

## Best Practices

### 1. Naming Convention

**Projects:**
- Format: `Client Name - Service Package`
- Examples: "Здоровье - Full Service", "Улыбка - SEO Campaign"

**Tasks:**
- Format: `[Client Name] Service: Task Name`
- Examples: "[Здоровье] SEO: Keyword Research"

### 2. Budget Tracking

Include budget in task description:
```markdown
**Budget:** 22,500 ₽ (15% of total)
```

### 3. Timeline Tracking

Include timeline in task description:
```markdown
**Timeline:** Week 1-2
```

### 4. Service Identification

Include service type in task description:
```markdown
**Service:** SEO
```

### 5. Progress Updates

Use comments for progress updates:
- Weekly status
- Completed deliverables
- Blockers and issues
- Next steps

## Automation

### Weekly Reports

Automated weekly reports to clients:
```bash
python scripts/send_weekly_reports.py
```

Sends:
- Tasks completed this week
- Budget spent
- Timeline status
- Next week plan

### Progress Tracking

Real-time progress tracking:
```python
from src.meai.tracking import ProgressTracker

tracker = ProgressTracker()
report = tracker.generate_progress_report(
    project_id="...",
    client_name="Здоровье",
    # ... metrics
)
print(tracker.format_report(report))
```

## Summary

**Key Points:**
- ✅ CLI team for ALL client projects
- ✅ One client → One or more projects
- ✅ One project → Multiple service tasks
- ✅ Task naming: `[Client] Service: Task`
- ✅ Guest access for client transparency
- ✅ Automated progress tracking and reporting

**Old Structure (deprecated):**
- ❌ SEO/CNT/ADS/ANL teams for clients
- ❌ Service-first hierarchy
- ❌ Split client view

**New Structure (correct):**
- ✅ CLI team for clients
- ✅ Client-first hierarchy
- ✅ Unified client view

---

**Last Updated:** 2026-05-15
**Status:** Active
