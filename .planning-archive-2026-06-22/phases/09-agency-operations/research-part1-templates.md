# Research Part 1: Client Project Templates & Automation

**Date:** 2026-05-15  
**Focus:** Agency project templates, automation patterns, and client onboarding workflows

---

## Executive Summary

Исследовал 5 production-ready репозиториев с фокусом на автоматизацию проектов для агентств и SaaS. Ключевые находки:

1. **GitHub Projects v2 + GraphQL** — стандарт для автоматизации project management
2. **Slash commands + AI agents** — паттерн для управления задачами через CLI
3. **Template-driven workflows** — автоматическое создание проектов из seed файлов
4. **Event-driven automation** — GitHub Actions + webhooks для синхронизации состояния

---

## Top 3 GitHub Repositories

### 1. github-project-llm-management (dyvan)

**URL:** https://github.com/dyvan/github-project-llm-management  
**Stars:** 2 | **Language:** Python (61.2%), Shell (38.8%)  
**Last Updated:** 2026-03-17

#### Что делает:
Полная автоматизация GitHub project management для AI-powered команд. Slash commands + PM agent + Kanban automation + AI code review.

#### Ключевые компоненты:

**1. Slash Commands для Claude Code** (`.claude/commands/`):
- `/start-task <issue-number>` — начать работу над задачей (checkout branch, load context, update board)
- `/finish-task` — завершить задачу (commit, PR, update board)
- `/next-task` — автоматически выбрать следующую задачу (Priority > Milestone > Effort)
- `/plan-task` — создать план выполнения задачи
- `/task-status` — проверить статус текущей задачи
- `/sprint-report` — отчёт по спринту
- `/save-session` / `/load-session` — сохранение/восстановление контекста

**2. GitHub Projects v2 Sync** (`scripts/project_sync.py`):
```python
class GitHubProjectSync:
    def __init__(self, token: str, owner: str, repo: str):
        self.api_url = "https://api.github.com/graphql"
        
    def sync_issue(self, issue_number: int, fields: Dict[str, str]):
        # 1. Get issue ID via GraphQL
        # 2. Find or create project item
        # 3. Update custom fields (Status, Priority, Effort, Type)
        
    def update_project_field(self, project_id: str, item_id: str, 
                            field_name: str, value: str):
        # Single select fields: get option ID
        # Text fields: direct update
        # GraphQL mutation to update
```

**Паттерны:**
- GraphQL API для Projects v2 (не REST)
- Автоматическое определение project ID (repository/user/organization)
- Поддержка custom fields (Status, Priority, Effort, Type, Owner, Version)
- Idempotent operations (safe to run multiple times)

**3. GitHub Actions Workflows** (`.github/workflows/`):

| Workflow | Trigger | Purpose |
|----------|---------|---------|
| `create-branch.yml` | Label `auto-branch` | Auto-create branch from issue |
| `update-project.yml` | Issue/PR events | Sync project board status |
| `code-review-agent.yml` | PR opened | Gemini AI code review |
| `auto-close-feature.yml` | PR merged | Auto-close parent issue when all subs done |

**Пример `update-project.yml`:**
```yaml
on:
  issues:
    types: [opened, labeled]
  pull_request:
    types: [opened, closed]

jobs:
  update-project:
    steps:
      - name: Add issue to project
        if: github.event.action == 'opened'
        run: gh project item-add $PROJECT_NUM --url "${{ github.event.issue.html_url }}"
      
      - name: Update on label
        if: github.event.action == 'labeled'
        run: |
          case "$LABEL" in
            auto-branch) python scripts/project_sync.py --status "In progress" ;;
            priority:high) python scripts/project_sync.py --priority "High" ;;
            type:feature) python scripts/project_sync.py --type "Feature" ;;
          esac
```

**4. Setup Script** (`template-setup.sh`):
- Idempotent setup (safe to run multiple times)
- Creates `.env` interactively
- Validates prerequisites (gh CLI, Python, git)
- Sets up labels, project board, workflows, issue templates

#### Что взять для AIM:

✅ **GraphQL-based project sync** — адаптировать `project_sync.py` для Linear API  
✅ **Slash commands pattern** — создать команды для управления клиентскими проектами  
✅ **Event-driven automation** — webhooks для синхронизации состояния проектов  
✅ **Idempotent setup scripts** — безопасное создание проектов для клиентов

---

### 2. python-agentic-template (ai-enhanced-engineer)

**URL:** https://github.com/ai-enhanced-engineer/python-agentic-template  
**Stars:** N/A | **Language:** Python  
**Last Updated:** 2026-05-15

#### Что делает:
Autonomous Python project template — описываешь проект в seed файлах, агенты исследуют, планируют и реализуют с production patterns.

#### Ключевые компоненты:

**1. Workflow-Driven Project Creation** (`workflows/PROJECT_INIT_WORKFLOW.md`):

```
Phase 0: Agent Discovery & Setup
├── 0.1: Scan & Match (find available specialists)
├── 0.2: Gap Analysis (identify missing roles)
└── 0.3: Specialist Creation (create custom agents)

Phase 1: Research
├── Expand seeds into full PRD
├── Research best practices
└── Output: PRD.md, RESEARCH_SYNTHESIS.md

Phase 2: Architecture
├── Create ADRs and project plan
├── Define MVP scope (MoSCoW)
└── Output: ADR.md, PROJECT_PLAN.md

Phase 3: MVP Implementation
├── Build must-have features with tests
├── Per deliverable: IMPLEMENT → REVIEW → FIX → PASS
└── Output: Working code in src/

Phase 4: Feature Enhancement
└── Add features from roadmap (same validation loop)
```

**2. Seed Files Pattern** (`context/`):
```
context/
├── PRODUCT.md          # What you're building (user input)
├── ENGINEERING.md      # Technical preferences (user input)
├── PRD.md              # Expanded PRD (generated)
├── RESEARCH_SYNTHESIS.md  # Research findings (generated)
└── PROJECT_PLAN.md     # MVP scope + roadmap (generated)
```

**Пример PRODUCT.md:**
```markdown
# Product Vision
What: RAG system for legal documents
For whom: Law firms
Why: Users waste 2 hours/day searching case law
Success: 50% reduction in search time

# Constraints
- Must run on GCP
- Budget: $5k/month
- Timeline: 3 months
```

**3. Agent Role Mapping:**

| Role | Capability | Keywords |
|------|------------|----------|
| `research` | Web research, evidence synthesis | research, context, synthesis |
| `architecture` | ADRs, system design, MVP scoping | architect, design, planning, ADR |
| `implementation` | Code writing, testing | engineer, developer, implement |
| `review` | Test enforcement, quality auditing | review, audit, quality, test |
| `domain-expert` | Business alignment, PRD compliance | domain, business, product, user |

**4. Production-Ready Foundation:**
- Structured logging (structlog)
- Type hints throughout
- Pre-commit hooks (Ruff, Black, mypy)
- 80% test coverage requirement
- CI/CD with GitHub Actions

#### Что взять для AIM:

✅ **Seed files pattern** — клиент заполняет PRODUCT.md, система генерирует проект  
✅ **Multi-phase workflow** — Research → Architecture → Implementation с approval gates  
✅ **Agent role mapping** — автоматический выбор специалистов для задач  
✅ **Production-first philosophy** — 90% infrastructure, 10% model code

---

### 3. phantom-template (nayasuda)

**URL:** https://github.com/nayasuda/phantom-template  
**Stars:** 4 | **Language:** Python (84.7%), Shell (11.4%)  
**Last Updated:** 2026-02-27

#### Что делает:
Multi-agent AI system template powered by Gemini CLI. 10 specialized agents для автоматизации daily operations (GitHub, Gmail, Google Tasks).

#### Ключевые компоненты:

**1. Multi-Agent Architecture** (`.gemini/agents/`):

| Agent | Role | Specialty |
|-------|------|-----------|
| **Navi** 🛰️ | Orchestrator | Coordinates all agents |
| **Queen** 👑 | Strategist | Mission planning & quality checks |
| **Mona** 🐱 | Manager | Task decomposition & PR reviews |
| **Skull** 💀 | Engineer | Git operations & shell execution |
| **Panther** 💃 | Writer | Documentation & reports |
| **Wolf** 🐺 | Backend | APIs & server-side code |
| **Fox** 🦊 | Frontend | UI & client-side code |
| **Noir** 🎀 | Tester | Test creation & verification |
| **Violet** 🎻 | Researcher | Technical research |
| **Crow** 🪶 | Debugger | Bug analysis & diagnosis |
| **Sophie** 🛡️ | Security | Security audits |

**2. Hook System** (`.gemini/hooks/`):
- Pre/post tool execution guards
- Secret detection
- Git safety checks
- Budget control

**3. Integration Patterns:**
- GitHub Project v2 → Google Tasks sync
- Gmail auto-classification (Gemini AI)
- PDCA self-improvement (agents log failures)

**4. Setup Automation:**
- Windows: `setup-windows.bat` (WSL + Ubuntu + Node.js + Gemini CLI)
- Linux/macOS: `setup.sh` (interactive wizard)
- `/initial_setup` command (Google OAuth, GitHub Secrets, Actions)

#### Что взять для AIM:

✅ **Multi-agent orchestration** — Navi-style coordinator для управления субагентами  
✅ **Hook system** — pre/post execution guards для безопасности и контроля  
✅ **Cross-platform integration** — GitHub + Google Workspace + Linear  
✅ **Self-improvement loop** — PDCA для обучения агентов на ошибках

---

## Additional Repositories (Brief Analysis)

### 4. agency-cli-tools (SCTY-Inc)

**URL:** https://github.com/SCTY-Inc/agency-cli-tools  
**Stars:** 378 | **Language:** Python

**Ключевые паттерны:**
- Agent-first CLI (non-interactive by default, `--interactive` flag for HITL)
- Composable stages (research → strategy → creative → activate)
- JSON file storage for pipeline artifacts
- Protocol-based communication between agents

**Pipeline:**
```
Brief → research → ResearchResult
      → strategy → StrategyResult  
      → creative → CreativeResult
      → activate → ActivationResult
```

**Что взять:**
- Protocol-based agent communication
- Composable pipeline stages
- JSON artifact storage

### 5. Vibe-Marketer/Agentic-Workflows-Template

**URL:** https://github.com/Vibe-Marketer/Agentic-Workflows-Template  
**Stars:** 1 | **Language:** Python

**Ключевые паттерны:**
- Three-layer architecture: Directives (plain English) → Orchestration (AI decisions) → Execution (Python scripts)
- "Build once, run forever" — workflows saved and reused
- Template pattern: `directives/_TEMPLATE.md` + `execution/_TEMPLATE.py`

**Что взять:**
- Directive-based workflow definition
- Reusable workflow templates
- Separation: instructions vs execution

---

## Code Patterns & Architecture

### Pattern 1: GraphQL-Based Project Sync

**From:** github-project-llm-management

```python
class ProjectSync:
    def __init__(self, api_key: str, workspace_id: str):
        self.api_url = "https://api.linear.app/graphql"
        self.headers = {"Authorization": api_key}
        
    def sync_project(self, project_id: str, fields: Dict[str, Any]):
        """Sync project to Linear workspace"""
        # 1. Get project node ID
        project_node = self.get_project(project_id)
        
        # 2. Update custom fields
        for field, value in fields.items():
            self.update_field(project_node, field, value)
            
        # 3. Create issues from template
        for task in self.get_template_tasks(project_id):
            self.create_issue(project_node, task)
```

**Применение для AIM:**
- Адаптировать для Linear API (GraphQL)
- Создание проектов для клиентов из шаблонов
- Синхронизация статусов задач

### Pattern 2: Seed-Based Project Generation

**From:** python-agentic-template

```python
class ProjectGenerator:
    def __init__(self, seed_dir: Path):
        self.product_md = seed_dir / "PRODUCT.md"
        self.engineering_md = seed_dir / "ENGINEERING.md"
        
    async def generate(self) -> Project:
        # Phase 1: Research
        prd = await self.research_agent.expand_prd(
            product=self.product_md.read_text(),
            engineering=self.engineering_md.read_text()
        )
        
        # Phase 2: Architecture
        adr = await self.architect_agent.create_adr(prd)
        plan = await self.architect_agent.create_plan(prd, adr)
        
        # Phase 3: Implementation
        code = await self.implementation_agent.build_mvp(plan)
        
        return Project(prd=prd, adr=adr, plan=plan, code=code)
```

**Применение для AIM:**
- Клиент заполняет brief (PRODUCT.md)
- Система генерирует проект автоматически
- Approval gates на каждом этапе

### Pattern 3: Slash Commands for Task Management

**From:** github-project-llm-management

```markdown
# /start-task command

Steps:
1. Fetch issue details (gh issue view)
2. Determine branch name (prefix + issue-number + slug)
3. Create or checkout branch
4. Update project board (Status → "In Progress")
5. Display context summary
6. Scan for affected files
```

**Применение для AIM:**
- `/create-project <client-name>` — создать проект для клиента
- `/add-task <project-id> <task-name>` — добавить задачу
- `/assign-agent <task-id> <agent-name>` — назначить агента
- `/project-status <project-id>` — статус проекта

### Pattern 4: Event-Driven Automation

**From:** github-project-llm-management

```yaml
# Webhook → GitHub Actions → Python Script → Linear API

on:
  issues:
    types: [opened, labeled, closed]

jobs:
  sync:
    steps:
      - name: Sync to Linear
        run: |
          python scripts/linear_sync.py \
            --issue ${{ github.event.issue.number }} \
            --action ${{ github.event.action }} \
            --label ${{ github.event.label.name }}
```

**Применение для AIM:**
- Linear webhook → FastAPI endpoint → Update project state
- Client action → Trigger agent workflow
- Task completed → Notify client + Update metrics

---

## Tools & Libraries

### 1. GitHub Projects v2 API (GraphQL)

**Docs:** https://docs.github.com/en/graphql/reference/objects#projectv2

**Key Operations:**
- `addProjectV2ItemById` — add issue/PR to project
- `updateProjectV2ItemFieldValue` — update custom fields
- Query project items with filters

**Adaptation for Linear:**
```graphql
# Linear GraphQL API
mutation CreateProject {
  projectCreate(input: {
    name: "Client Project"
    teamId: "team-id"
    description: "Auto-generated from template"
  }) {
    project {
      id
      name
    }
  }
}
```

### 2. Template Engines

**Jinja2** (Python):
```python
from jinja2 import Environment, FileSystemLoader

env = Environment(loader=FileSystemLoader('templates/'))
template = env.get_template('project.md.j2')

output = template.render(
    client_name="Acme Corp",
    project_type="SEO Audit",
    start_date="2026-05-15"
)
```

**Cookiecutter** (Project scaffolding):
```bash
cookiecutter gh:audreyr/cookiecutter-pypackage
# Interactive prompts for project setup
```

**Применение для AIM:**
- Jinja2 для генерации документов (briefs, reports)
- Cookiecutter для создания структуры проектов
- Шаблоны для разных типов проектов (SEO, Content, Ads)

### 3. Linear API (Python SDK)

**Docs:** https://developers.linear.app/docs/graphql/working-with-the-graphql-api

```python
from linear import LinearClient

client = LinearClient(api_key="lin_api_...")

# Create project
project = client.create_project(
    name="Client Project",
    team_id="team-id",
    description="Auto-generated"
)

# Create issues from template
for task in template_tasks:
    client.create_issue(
        title=task.title,
        description=task.description,
        project_id=project.id,
        assignee_id=agent_id
    )
```

### 4. Workflow Orchestration

**Temporal** (Durable workflows):
```python
@workflow.defn
class ClientOnboardingWorkflow:
    @workflow.run
    async def run(self, client_data: ClientData) -> Project:
        # Step 1: Create project
        project = await workflow.execute_activity(
            create_project,
            client_data,
            start_to_close_timeout=timedelta(minutes=5)
        )
        
        # Step 2: Generate tasks
        tasks = await workflow.execute_activity(
            generate_tasks,
            project.id,
            start_to_close_timeout=timedelta(minutes=10)
        )
        
        # Step 3: Assign agents
        await workflow.execute_activity(
            assign_agents,
            tasks,
            start_to_close_timeout=timedelta(minutes=5)
        )
        
        return project
```

**Применение для AIM:**
- Durable workflows для long-running процессов
- Automatic retries и error handling
- State persistence между шагами

---

## Implementation Recommendations

### 1. Project Template System

**Architecture:**
```
AIM/templates/
├── seo-audit/
│   ├── template.yaml          # Project metadata
│   ├── tasks.yaml             # Task templates
│   ├── brief.md.j2            # Client brief template
│   └── deliverables/          # Expected outputs
├── content-strategy/
│   ├── template.yaml
│   ├── tasks.yaml
│   └── ...
└── ads-campaign/
    ├── template.yaml
    ├── tasks.yaml
    └── ...
```

**template.yaml:**
```yaml
name: "SEO Audit"
description: "Comprehensive SEO audit for client website"
duration_days: 14
agents:
  - seo-magister
  - ci-tech-agent
  - ci-content-agent
phases:
  - name: "Discovery"
    duration_days: 3
    tasks:
      - "Collect website data"
      - "Analyze competitors"
  - name: "Analysis"
    duration_days: 7
    tasks:
      - "Technical SEO audit"
      - "Content gap analysis"
  - name: "Recommendations"
    duration_days: 4
    tasks:
      - "Generate report"
      - "Create action plan"
```

### 2. Client Onboarding Workflow

**Slash Command:**
```bash
/create-project --client "Acme Corp" --template "seo-audit" --start-date "2026-05-20"
```

**Workflow Steps:**
1. **Load template** — read `templates/seo-audit/template.yaml`
2. **Create Linear project** — via GraphQL API
3. **Generate tasks** — from `tasks.yaml` with Jinja2
4. **Assign agents** — based on `agents` field
5. **Create brief** — render `brief.md.j2` with client data
6. **Setup webhooks** — for status updates
7. **Notify client** — email with project link

**Code:**
```python
class ProjectCreator:
    def __init__(self, linear_client: LinearClient, template_dir: Path):
        self.linear = linear_client
        self.templates = template_dir
        
    async def create_project(self, client_name: str, template_name: str) -> Project:
        # 1. Load template
        template = self.load_template(template_name)
        
        # 2. Create Linear project
        project = await self.linear.create_project(
            name=f"{client_name} - {template.name}",
            description=template.description,
            target_date=datetime.now() + timedelta(days=template.duration_days)
        )
        
        # 3. Generate tasks
        for phase in template.phases:
            for task_template in phase.tasks:
                task = await self.linear.create_issue(
                    title=task_template.title,
                    description=self.render_task(task_template, client_name),
                    project_id=project.id,
                    estimate=task_template.estimate
                )
                
        # 4. Assign agents
        for agent_name in template.agents:
            agent = self.get_agent(agent_name)
            await self.assign_agent(project.id, agent.id)
            
        return project
```

### 3. Event-Driven Sync

**Linear Webhook → FastAPI:**
```python
@app.post("/webhooks/linear")
async def linear_webhook(request: Request):
    payload = await request.json()
    
    event_type = payload["type"]
    data = payload["data"]
    
    if event_type == "Issue":
        if data["action"] == "create":
            await handle_task_created(data["issue"])
        elif data["action"] == "update":
            await handle_task_updated(data["issue"])
            
    return {"status": "ok"}

async def handle_task_updated(issue: Dict):
    # If task completed → notify agent
    if issue["state"]["name"] == "Done":
        agent = get_assigned_agent(issue["id"])
        await agent.on_task_completed(issue)
```

### 4. Slash Commands for Operator

**Commands:**
```python
# AIM/.claude/commands/create-project.md
---
description: Create new client project from template
allowed-tools: Bash, Read, Write
argument-hint: --client <name> --template <type>
---

# Create Project

Steps:
1. Parse arguments (client name, template type)
2. Load template from AIM/templates/{type}/
3. Call Linear API to create project
4. Generate tasks from template
5. Assign agents based on template.agents
6. Create brief document
7. Setup webhooks
8. Return project URL
```

---

## Next Steps

### Phase 1: Foundation (Week 1-2)
- [ ] Implement Linear API client (GraphQL)
- [ ] Create project template system (YAML + Jinja2)
- [ ] Build ProjectCreator class
- [ ] Add slash commands for Operator

### Phase 2: Automation (Week 3-4)
- [ ] Setup Linear webhooks → FastAPI
- [ ] Implement event handlers (task created/updated/completed)
- [ ] Add agent assignment logic
- [ ] Create notification system (email/Slack)

### Phase 3: Templates (Week 5-6)
- [ ] Create SEO Audit template
- [ ] Create Content Strategy template
- [ ] Create Ads Campaign template
- [ ] Add template validation

### Phase 4: Integration (Week 7-8)
- [ ] Connect Operator with ProjectCreator
- [ ] Add project status tracking
- [ ] Implement client dashboard
- [ ] Add metrics and reporting

---

## Cost Analysis

**GitHub Projects v2:** Free (included in GitHub)  
**Linear API:** $8/user/month (Team plan)  
**Temporal Cloud:** $200/month (Starter plan) — optional  
**Total:** ~$200-300/month for 10-20 users

**ROI:**
- Manual project setup: 2-4 hours per project
- Automated setup: 5-10 minutes per project
- Time saved: ~3.5 hours per project
- Cost saved: ~$350 per project (at $100/hour)
- Break-even: 1 project per month

---

## Sources

- [github-project-llm-management](https://github.com/dyvan/github-project-llm-management) — GitHub Projects v2 automation
- [python-agentic-template](https://github.com/ai-enhanced-engineer/python-agentic-template) — Autonomous project generation
- [phantom-template](https://github.com/nayasuda/phantom-template) — Multi-agent orchestration
- [agency-cli-tools](https://github.com/SCTY-Inc/agency-cli-tools) — Agent-first CLI patterns
- [Agentic-Workflows-Template](https://github.com/Vibe-Marketer/Agentic-Workflows-Template) — Directive-based workflows

---

**Status:** Part 1 Complete ✅  
**Next:** Part 2 — Task Templates & Workflow Builders
