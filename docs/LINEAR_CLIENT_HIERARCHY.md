# Linear Client Hierarchy Structure

## Overview

Правильная иерархия для клиентских проектов в Linear с использованием Team-per-Client подхода.

## Structure

```
Teams (верхний уровень)
├── DEV: AIM Development (внутренняя разработка)
├── MKT: AIM Marketing (внутренний маркетинг)
├── Client A (Project 1) — отдельная команда для первого проекта
│   └── Project: Full Service
│       ├── SEO: Keyword Research
│       ├── SEO: Competitor Analysis
│       ├── SEO: On-Page Optimization
│       ├── SEO: Link Building
│       ├── Content: Strategy Development
│       ├── Content: Blog Creation
│       ├── Content: Social Media
│       ├── Content: Email Marketing
│       ├── Ads: Yandex Direct Setup
│       ├── Ads: Campaign Optimization
│       └── Ads: Campaign Scaling
│
├── Client A (Project 2) — отдельная команда для второго проекта (если появится)
│   └── Project: SEO Campaign
│       ├── SEO: Keyword Research
│       ├── SEO: Competitor Analysis
│       ├── SEO: On-Page Optimization
│       └── SEO: Link Building
│
└── Client B (Project 1) — отдельная команда для клиента B
    └── Project: Content Marketing
        ├── Content: Strategy Development
        ├── Content: Blog Creation
        ├── Content: Social Media
        └── Content: Email Marketing
```

## Key Principles

### 1. Team per Client Project

**Каждый проект клиента = отдельная команда:**
- Формат команды: `Client Name (Project N)`
- Первый проект: `Client Name (Project 1)`
- Второй проект: `Client Name (Project 2)`
- И так далее

**Преимущества:**
- Полная изоляция проектов
- Чистая иерархия: Team → Project → Tasks
- Легко управлять доступом (guest user видит только свою команду)
- Масштабируемость (неограниченное количество проектов)

**DEV Team:**
- AIM Development tasks
- Internal infrastructure
- System improvements

**MKT Team:**
- AIM Marketing tasks
- Our own promotion
- Brand building

**Client Teams:**
- One team per client project
- Format: `Client Name (Project N)`
- Contains all service tasks for that project

### 2. Projects = Service Packages

Each client team contains one or more projects:
- Project name describes the service package (NO client name prefix)
- Examples: "Full Service", "SEO Campaign", "Content Marketing"
- One project per service package

### 3. Tasks = Service Delivery

Tasks are organized by service type (NO client name prefix):
- **SEO:** `SEO: Task Name`
- **Content:** `Content: Task Name`
- **Ads:** `Ads: Task Name`
- **Analytics:** `Analytics: Task Name`

### 4. Team Key Generation

Team keys are generated from client names:
- **Single word:** First 3 letters uppercase (e.g., "Clinic" → "CLI")
- **Multiple words:** First letter of each word (max 3) (e.g., "Medical Center" → "MC")
- **Project number:** Appended if > 1 (e.g., "CLI2", "MC3")

Examples:
- "Test Clinic" → "TES" (Project 1)
- "Test Clinic" → "TES2" (Project 2)
- "Medical Center Moscow" → "MCM" (Project 1)
- "Dental Implants Pro" → "DIP" (Project 1)

## Why This Structure?

### ✅ Correct Hierarchy (Team-per-Client)

```
Client Team (top level)
  └─ Project (service package)
      └─ Tasks (deliverables)
```

This matches real business structure:
- One client project = one team
- Multiple projects = multiple teams with numbered suffixes
- Clean isolation between projects
- Easy access control (guest sees only their team)

### ❌ Wrong Hierarchy (old CLI approach)

```
CLI Team (top level)
  └─ Multiple Clients
      └─ Projects
          └─ Tasks
```

Problems:
- All clients in one team (no isolation)
- Hard to manage access (guest sees all clients)
- Doesn't scale well (hundreds of clients in one team)
- Missing hierarchy level (Client entity doesn't exist in Linear)

## Creating Client Projects

### Using Script

```bash
python scripts/create_client_project.py "Client Name" \
  --services seo,content,ads \
  --budget 100000 \
  --timeline 12
```

This creates:
- **Team:** "Client Name (Project 1)" with auto-generated key
- **Project:** Service package name (e.g., "Full Service")
- **Tasks:** 11 tasks (4 SEO + 4 Content + 3 Ads) without client prefix
- Budget allocation per task
- Timeline per task

### Multiple Projects for Same Client

```bash
# First project
python scripts/create_client_project.py "Medical Clinic" \
  --services seo,content,ads \
  --budget 150000

# Second project (add --project-number flag when implemented)
# Creates team "Medical Clinic (Project 2)"
```

### Manual Creation

1. Create new team: "Client Name (Project 1)"
2. Generate team key from client name (3 letters or initials)
3. Create project inside team (no client prefix)
4. Add tasks with format: `Service: Task Name`
5. Include `**Service:** Type` in description

## Guest Access

Clients get read-only access to their team:

1. Invite guest user (client email)
2. Grant access to specific team (e.g., "Client Name (Project 1)")
3. Client sees:
   - Their team only (full isolation)
   - All projects in their team
   - All tasks and progress
   - Comments and updates
   - Timeline and budget

**Benefits:**
- Complete isolation (can't see other clients)
- Simple access control (one team = one client project)
- Easy to revoke (remove from team)

See `docs/LINEAR_CLIENT_ACCESS.md` for details.

## Progress Tracking

Use `ProgressTracker` to monitor:
- **Tasks:** Completed / Total
- **Budget:** Spent / Total
- **Timeline:** On track / At risk / Behind
- **Quality:** Scores from Magisters

See `src/meai/tracking/progress_tracker.py` for implementation.

## Migration from Old Structure

Old CLI team approach is deprecated. New structure uses Team-per-Client.

**Old service teams (SEO, CNT, ADS, ANL):**
- Remain in Linear (can't be archived via API)
- Not used for new client projects
- All new clients get dedicated teams

**To create new client:**
```bash
python scripts/create_client_project.py "Client Name" --services seo,content,ads --budget 100000
```

This automatically creates team "Client Name (Project 1)" with all tasks.

## Examples

### Example 1: Full Service Client

**Client:** Medical Clinic "Здоровье"
**Services:** SEO, Content, Ads
**Budget:** 150,000 ₽
**Timeline:** 12 weeks

**Structure:**
```
Team: Здоровье (Project 1)
  └─ Project: Full Service
      ├─ SEO: Keyword Research (Week 1-2, 22,500 ₽)
      ├─ SEO: Competitor Analysis (Week 2-3, 22,500 ₽)
      ├─ SEO: On-Page Optimization (Week 3-6, 52,500 ₽)
      ├─ SEO: Link Building (Week 6-12, 52,500 ₽)
      ├─ Content: Strategy (Week 1-2, 30,000 ₽)
      ├─ Content: Blog Creation (Week 2-8, 60,000 ₽)
      ├─ Content: Social Media (Week 2-12, 37,500 ₽)
      ├─ Content: Email Marketing (Week 4-12, 22,500 ₽)
      ├─ Ads: Yandex Direct Setup (Week 1-2, 30,000 ₽)
      ├─ Ads: Campaign Optimization (Week 2-6, 45,000 ₽)
      └─ Ads: Campaign Scaling (Week 6-12, 75,000 ₽)
```

### Example 2: SEO Only Client

**Client:** Dental Clinic "Улыбка"
**Services:** SEO
**Budget:** 50,000 ₽
**Timeline:** 12 weeks

**Structure:**
```
Team: Улыбка (Project 1)
  └─ Project: SEO Campaign
      ├─ SEO: Keyword Research (Week 1-2, 7,500 ₽)
      ├─ SEO: Competitor Analysis (Week 2-3, 7,500 ₽)
      ├─ SEO: On-Page Optimization (Week 3-6, 17,500 ₽)
      └─ SEO: Link Building (Week 6-12, 17,500 ₽)
```

### Example 3: Multiple Projects for Same Client

**Client:** Medical Clinic "Здоровье"
**First Project:** Full Service (150,000 ₽)
**Second Project:** SEO Campaign for new location (50,000 ₽)

**Structure:**
```
Team: Здоровье (Project 1)
  └─ Project: Full Service
      └─ [11 tasks as in Example 1]

Team: Здоровье (Project 2)
  └─ Project: SEO Campaign
      └─ [4 SEO tasks as in Example 2]
```

## Best Practices

### 1. Naming Convention

**Teams:**
- Format: `Client Name (Project N)`
- Examples: "Здоровье (Project 1)", "Улыбка (Project 1)"
- Key: Auto-generated from client name (3 letters or initials)

**Projects:**
- Format: `Service Package` (NO client prefix)
- Examples: "Full Service", "SEO Campaign", "Content Marketing"

**Tasks:**
- Format: `Service: Task Name` (NO client prefix)
- Examples: "SEO: Keyword Research", "Content: Blog Creation"

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
- ✅ Team-per-Client approach (one team per client project)
- ✅ Team naming: `Client Name (Project N)`
- ✅ Project naming: Service package (NO client prefix)
- ✅ Task naming: `Service: Task` (NO client prefix)
- ✅ Guest access: Full team isolation
- ✅ Scalable: Unlimited projects per client (numbered teams)

**Old Structure (deprecated):**
- ❌ CLI team for all clients
- ❌ Client prefixes in task names
- ❌ No isolation between clients

**New Structure (correct):**
- ✅ Dedicated team per client project
- ✅ Clean task names without prefixes
- ✅ Full isolation and access control

---

**Last Updated:** 2026-05-15
**Status:** Active (Team-per-Client approach)
