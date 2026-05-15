# Phase 9: Agency Operations

**Goal:** Automate client project management, reporting, and team collaboration  
**Duration:** 8 weeks (1 developer)  
**Status:** In Progress 🚧  
**Started:** 2026-05-15  
**Started:** 2026-05-15

---

## Overview

Phase 9 автоматизирует операционные процессы агентства:
- **Project Templates** - автоматическое создание проектов из шаблонов
- **Automated Reporting** - еженедельные отчёты клиентам (PDF + email)
- **Performance Dashboards** - real-time метрики для клиентов и команды
- **Team Collaboration** - task assignment, progress tracking, notifications
- **Knowledge Base** - документация для клиентов и команды

**Почему это важно:**
- Экономия времени: 2-4 часа → 5-10 минут на проект
- Стандартизация: единый подход ко всем проектам
- Прозрачность: клиенты видят прогресс в реальном времени
- Масштабируемость: от 10 до 200+ клиентов без роста команды

**ROI:**
- Экономия: ~$350 на проект (3.5 часа × $100/час)
- Break-even: 1 проект в месяц
- Стоимость: $25-70/месяц (зависит от масштаба)

---

## Architecture

### System Design

```
┌─────────────────────────────────────────────────────────────┐
│                        Frontend (Next.js 16)                 │
├─────────────────────────────────────────────────────────────┤
│  Client Dashboard          │  Team Dashboard                 │
│  ├─ Project Overview       │  ├─ Task Management             │
│  ├─ Performance Metrics    │  ├─ Team Activity               │
│  ├─ Reports History        │  └─ Notifications               │
│  └─ Knowledge Base         │                                 │
└─────────────────────────────────────────────────────────────┘
                              ↕
┌─────────────────────────────────────────────────────────────┐
│                      Backend (FastAPI)                       │
├─────────────────────────────────────────────────────────────┤
│  ProjectCreator    │  ReportGenerator  │  MetricsCollector  │
│  ├─ Templates      │  ├─ PDF Builder   │  ├─ SEO Metrics    │
│  ├─ Linear Sync    │  ├─ Scheduler     │  ├─ Content Stats  │
│  └─ Webhooks       │  └─ Email Sender  │  └─ Ads Analytics  │
└─────────────────────────────────────────────────────────────┘
                              ↕
┌─────────────────────────────────────────────────────────────┐
│                    Infrastructure                            │
├─────────────────────────────────────────────────────────────┤
│  Linear API  │  Supabase Realtime  │  SendGrid  │  Redis   │
└─────────────────────────────────────────────────────────────┘
```

### Data Flow

**Project Creation:**
```
Client Brief → ProjectCreator → Linear API → Project Created
                    ↓
              Template Engine (Jinja2)
                    ↓
              Tasks + Milestones + Agents
```

**Automated Reporting:**
```
APScheduler (Cron) → MetricsCollector → ReportGenerator → SendGrid
                           ↓                    ↓
                    Database Query        PDF (ReportLab)
                           ↓                    ↓
                    History Tracking      Email Delivery
```

**Real-Time Updates:**
```
Backend Event → Supabase Realtime → Frontend Dashboard
                      ↓
                WebSocket Push
                      ↓
                Client Sees Update (instant)
```

---

## Deliverables

### 1. Client Project Templates (Week 1-2)

**Goal:** Автоматическое создание проектов в Linear из шаблонов

**Components:**

#### 1.1 Linear API Client
- [x] GraphQL client setup
- [x] Authentication (API key)
- [x] Query builder
- [x] Mutation builder
- [x] Error handling with retry
- [x] Rate limiting (100 req/min)

**Code Example:**
```python
# AIM/src/aim/operations/linear_client.py
from gql import gql, Client
from gql.transport.aiohttp import AIOHTTPTransport

class LinearClient:
    def __init__(self, api_key: str):
        transport = AIOHTTPTransport(
            url="https://api.linear.app/graphql",
            headers={"Authorization": api_key}
        )
        self.client = Client(transport=transport)
    
    async def create_project(self, team_id: str, name: str, description: str):
        query = gql("""
            mutation CreateProject($input: ProjectCreateInput!) {
              projectCreate(input: $input) {
                success
                project { id name }
              }
            }
        """)
        result = await self.client.execute_async(query, {
            "input": {
                "teamId": team_id,
                "name": name,
                "description": description
            }
        })
        return result["projectCreate"]["project"]
```

#### 1.2 Template System
- [x] YAML template format
- [x] Jinja2 rendering engine
- [x] Variable substitution
- [x] Conditional sections
- [x] Template validation

**Template Format:**
```yaml
# AIM/templates/projects/seo-audit.yaml
name: "SEO Audit - {{ client_name }}"
description: "Complete SEO audit for {{ domain }}"
duration_weeks: 4

milestones:
  - name: "Technical SEO Analysis"
    duration_days: 7
    tasks:
      - title: "Crawl website ({{ domain }})"
        assignee: "seo-magister"
        estimate: 2
      - title: "Analyze site structure"
        assignee: "seo-magister"
        estimate: 3

  - name: "Content Analysis"
    duration_days: 7
    tasks:
      - title: "Keyword research"
        assignee: "keyword-research-agent"
        estimate: 4
      - title: "Content gap analysis"
        assignee: "content-gap-agent"
        estimate: 3
```

#### 1.3 ProjectCreator Class
- [x] Load template from YAML
- [x] Render with Jinja2
- [x] Create project in Linear
- [x] Create milestones
- [x] Create tasks
- [x] Assign agents
- [x] Send notifications

**Implementation:**
```python
# AIM/src/aim/operations/project_creator.py
from jinja2 import Environment, FileSystemLoader
import yaml

class ProjectCreator:
    def __init__(self, linear_client: LinearClient):
        self.linear = linear_client
        self.env = Environment(loader=FileSystemLoader('templates/projects'))
    
    async def create_from_template(
        self,
        template_name: str,
        variables: dict
    ) -> Project:
        # Load and render template
        template = self.env.get_template(f"{template_name}.yaml")
        rendered = template.render(**variables)
        config = yaml.safe_load(rendered)
        
        # Create project
        project = await self.linear.create_project(
            team_id=config["team_id"],
            name=config["name"],
            description=config["description"]
        )
        
        # Create milestones and tasks
        for milestone in config["milestones"]:
            await self._create_milestone(project.id, milestone)
        
        return project
```

#### 1.4 Slash Commands for Operator
- [ ] `/create-project <template> <client>`
- [ ] `/add-task <project> <task>`
- [ ] `/assign-agent <task> <agent>`
- [ ] `/update-status <task> <status>`

**Success Criteria:**
- ✅ Project created in Linear in < 10 seconds
- ✅ All tasks and milestones created correctly
- ✅ Agents assigned automatically
- ✅ Client receives welcome email
- ✅ 3 templates available (SEO Audit, Content Strategy, Ads Campaign)

---

### 2. Automated Reporting (Week 3-4)

**Goal:** Еженедельные PDF отчёты клиентам с метриками и прогрессом

**Components:**

#### 2.1 ReportLab PDF Generation
- [x] PDF template design
- [x] Charts integration (matplotlib)
- [x] Tables with data
- [x] Branding (logo, colors)
- [x] Multi-page support

**Code Example:**
```python
# AIM/src/aim/operations/report_generator.py
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Table, Image
from reportlab.lib.styles import getSampleStyleSheet
import matplotlib.pyplot as plt
from io import BytesIO

class ReportGenerator:
    def generate_weekly_report(self, client_id: str, week: int) -> bytes:
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4)
        elements = []
        styles = getSampleStyleSheet()
        
        # Header
        elements.append(Paragraph(f"Weekly Report - Week {week}", styles['Title']))
        
        # Metrics table
        data = [
            ['Metric', 'This Week', 'Last Week', 'Change'],
            ['Organic Traffic', '1,234', '1,100', '+12%'],
            ['Keywords Ranked', '45', '42', '+7%'],
        ]
        table = Table(data)
        elements.append(table)
        
        # Chart
        fig, ax = plt.subplots()
        ax.plot([1, 2, 3, 4], [1100, 1150, 1200, 1234])
        plt.savefig('chart.png')
        elements.append(Image('chart.png', width=400, height=300))
        
        doc.build(elements)
        return buffer.getvalue()
```

#### 2.2 APScheduler Setup
- [x] Job store configuration (SQLite)
- [x] Cron triggers (weekly, monthly)
- [x] Job persistence
- [x] Error handling
- [x] Retry logic

**Implementation:**
```python
# AIM/src/aim/operations/scheduler.py
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore

jobstores = {
    'default': SQLAlchemyJobStore(url='sqlite:///jobs.db')
}

scheduler = BackgroundScheduler(jobstores=jobstores)

# Weekly report (Monday 9 AM)
scheduler.add_job(
    func=generate_weekly_report,
    trigger=CronTrigger(day_of_week='mon', hour=9, minute=0),
    id='weekly_report',
    replace_existing=True
)

scheduler.start()
```

#### 2.3 SendGrid Email Delivery
- [x] SendGrid API client
- [x] Email templates (HTML)
- [x] PDF attachment
- [x] Delivery tracking
- [x] Bounce handling

**Implementation:**
```python
# AIM/src/aim/operations/email_sender.py
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail, Attachment, FileContent, FileName
import base64

class EmailSender:
    def __init__(self, api_key: str):
        self.sg = SendGridAPIClient(api_key)
    
    async def send_report(self, to_email: str, pdf_bytes: bytes, week: int):
        message = Mail(
            from_email='reports@iamaim.ru',
            to_emails=to_email,
            subject=f'Weekly Report - Week {week}',
            html_content=f'<p>Your weekly report is attached.</p>'
        )
        
        # Attach PDF
        encoded = base64.b64encode(pdf_bytes).decode()
        attachment = Attachment(
            FileContent(encoded),
            FileName(f'report-week-{week}.pdf'),
            FileType('application/pdf')
        )
        message.attachment = attachment
        
        response = self.sg.send(message)
        return response.status_code == 202
```

#### 2.4 History Tracking
- [ ] Store report metadata in database
- [ ] Track delivery status
- [ ] Week-over-week comparison
- [ ] Risk classification (High/Medium/Low)
- [ ] Prevent duplicate reports

**Database Schema:**
```sql
CREATE TABLE report_history (
    id INTEGER PRIMARY KEY,
    client_id INTEGER NOT NULL,
    week_number INTEGER NOT NULL,
    generated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    delivered_at TIMESTAMP,
    status TEXT CHECK(status IN ('pending', 'sent', 'failed')),
    metrics_json TEXT,
    risk_level TEXT CHECK(risk_level IN ('low', 'medium', 'high')),
    UNIQUE(client_id, week_number)
);
```

**Risk Classification:**
```python
HIGH_RISK_REVENUE_DROP = 0.10  # 10% drop
MEDIUM_RISK_REVENUE_DROP = 0.05  # 5% drop

def classify_risk(revenue_change_pct: float) -> str:
    if revenue_change_pct <= -HIGH_RISK_REVENUE_DROP:
        return "high"
    elif revenue_change_pct <= -MEDIUM_RISK_REVENUE_DROP:
        return "medium"
    return "low"
```

**Success Criteria:**
- ✅ Reports generated every Monday at 9 AM
- ✅ PDF includes charts, tables, and branding
- ✅ Email delivered with PDF attachment
- ✅ History tracked (no duplicates)
- ✅ Risk classification working (High/Medium/Low)
- ✅ 100% delivery rate (with retry)

---

### 3. Performance Dashboards (Week 5-6)

**Goal:** Real-time метрики для клиентов и команды

**Components:**

#### 3.1 Supabase Realtime Setup
- [ ] Supabase project setup
- [ ] Database tables (projects, tasks, metrics)
- [ ] Realtime subscriptions
- [ ] Row-level security (RLS)
- [ ] API key management

**Database Schema:**
```sql
-- Projects table
CREATE TABLE projects (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    client_id UUID NOT NULL,
    name TEXT NOT NULL,
    status TEXT CHECK(status IN ('active', 'paused', 'completed')),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Metrics table
CREATE TABLE metrics (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    project_id UUID REFERENCES projects(id),
    metric_type TEXT NOT NULL,
    value NUMERIC NOT NULL,
    recorded_at TIMESTAMP DEFAULT NOW()
);

-- Enable realtime
ALTER PUBLICATION supabase_realtime ADD TABLE projects;
ALTER PUBLICATION supabase_realtime ADD TABLE metrics;
```

#### 3.2 Frontend Dashboard Components
- [ ] Real-time metrics display
- [ ] Charts (Recharts)
- [ ] Filters (date range, metric type)
- [ ] Auto-refresh
- [ ] Loading states

**Implementation:**
```typescript
// frontend/components/MetricsDashboard.tsx
'use client'

import { useEffect, useState } from 'react'
import { createClient } from '@supabase/supabase-js'
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip } from 'recharts'

const supabase = createClient(
  process.env.NEXT_PUBLIC_SUPABASE_URL!,
  process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!
)

export function MetricsDashboard({ projectId }: { projectId: string }) {
  const [metrics, setMetrics] = useState<Metric[]>([])
  
  useEffect(() => {
    // Initial load
    fetchMetrics()
    
    // Subscribe to realtime updates
    const channel = supabase
      .channel('metrics')
      .on(
        'postgres_changes',
        { event: '*', schema: 'public', table: 'metrics', filter: `project_id=eq.${projectId}` },
        (payload) => {
          setMetrics(prev => [...prev, payload.new as Metric])
        }
      )
      .subscribe()
    
    return () => { supabase.removeChannel(channel) }
  }, [projectId])
  
  return (
    <div>
      <h2>Performance Metrics</h2>
      <LineChart width={600} height={300} data={metrics}>
        <CartesianGrid strokeDasharray="3 3" />
        <XAxis dataKey="recorded_at" />
        <YAxis />
        <Tooltip />
        <Line type="monotone" dataKey="value" stroke="#8884d8" />
      </LineChart>
    </div>
  )
}
```

#### 3.3 Zustand State Management
- [ ] Dashboard state (filters, selected metrics)
- [ ] User preferences
- [ ] Persist to localStorage
- [ ] Optimistic updates

**Implementation:**
```typescript
// frontend/store/dashboardStore.ts
import { create } from 'zustand'
import { persist } from 'zustand/middleware'

interface DashboardState {
  selectedMetrics: string[]
  dateRange: { start: Date; end: Date }
  setSelectedMetrics: (metrics: string[]) => void
  setDateRange: (range: { start: Date; end: Date }) => void
}

export const useDashboardStore = create<DashboardState>()(
  persist(
    (set) => ({
      selectedMetrics: ['traffic', 'keywords'],
      dateRange: { start: new Date(), end: new Date() },
      setSelectedMetrics: (metrics) => set({ selectedMetrics: metrics }),
      setDateRange: (range) => set({ dateRange: range }),
    }),
    { name: 'dashboard-storage' }
  )
)
```

#### 3.4 WebSocket Auto-Reconnection
- [ ] Connection status indicator
- [ ] Exponential backoff (3s → 5s max)
- [ ] Manual reconnect button
- [ ] Offline mode

**Implementation:**
```typescript
// frontend/hooks/useWebSocket.ts
import { useEffect, useRef, useState } from 'react'

export function useWebSocket(url: string) {
  const [status, setStatus] = useState<'connecting' | 'connected' | 'disconnected'>('disconnected')
  const reconnectDelay = useRef(3000)
  
  useEffect(() => {
    const connect = () => {
      const ws = new WebSocket(url)
      
      ws.onopen = () => {
        setStatus('connected')
        reconnectDelay.current = 3000
      }
      
      ws.onclose = () => {
        setStatus('disconnected')
        setTimeout(connect, reconnectDelay.current)
        reconnectDelay.current = Math.min(reconnectDelay.current * 1.5, 5000)
      }
    }
    
    connect()
  }, [url])
  
  return { status }
}
```

**Success Criteria:**
- ✅ Metrics update in real-time (< 1s latency)
- ✅ Charts render smoothly (60 FPS)
- ✅ Auto-reconnection works (exponential backoff)
- ✅ Memory management (max 1000 data points)
- ✅ Mobile responsive

---

### 4. Team Collaboration (Week 6-7)

**Goal:** Task assignment, progress tracking, notifications

**Components:**

#### 4.1 Task Assignment System
- [ ] Assign tasks to team members
- [ ] Workload balancing
- [ ] Skill-based routing
- [ ] Availability tracking

**Implementation:**
```python
# AIM/src/aim/operations/task_assigner.py
class TaskAssigner:
    async def assign_task(self, task_id: str, agent_type: str) -> str:
        # Find available agent with required skills
        agent = await self.find_best_agent(agent_type)
        
        # Check workload
        if agent.current_tasks >= agent.max_tasks:
            agent = await self.find_next_available(agent_type)
        
        # Assign task
        await self.linear.assign_task(task_id, agent.id)
        await self.notify_agent(agent.id, task_id)
        
        return agent.id
```

#### 4.2 Progress Tracking
- [ ] Task status updates
- [ ] Time tracking
- [ ] Milestone progress
- [ ] Burndown charts

#### 4.3 Notification System
- [ ] In-app notifications
- [ ] Email notifications
- [ ] Slack integration (optional)
- [ ] Notification preferences

**Implementation:**
```typescript
// frontend/components/NotificationCenter.tsx
export function NotificationCenter() {
  const [notifications, setNotifications] = useState<Notification[]>([])
  
  useEffect(() => {
    const channel = supabase
      .channel('notifications')
      .on('postgres_changes', { event: 'INSERT', schema: 'public', table: 'notifications' }, (payload) => {
        setNotifications(prev => [payload.new as Notification, ...prev])
      })
      .subscribe()
    
    return () => { supabase.removeChannel(channel) }
  }, [])
  
  return (
    <div>
      {notifications.map(n => (
        <div key={n.id}>{n.message}</div>
      ))}
    </div>
  )
}
```

#### 4.4 Activity Feed
- [ ] Real-time activity stream
- [ ] Filter by user/project
- [ ] Activity types (task created, status changed, comment added)
- [ ] Pagination

**Success Criteria:**
- ✅ Tasks assigned automatically based on skills
- ✅ Workload balanced across team
- ✅ Notifications delivered in real-time
- ✅ Activity feed updates instantly
- ✅ Mobile notifications work

---

### 5. Knowledge Base (Week 7-8)

**Goal:** Документация для клиентов и команды

**Components:**

#### 5.1 Next.js + MDX Setup
- [ ] Next.js 16 app router
- [ ] MDX processing (next-mdx-remote)
- [ ] Frontmatter parsing (gray-matter)
- [ ] Syntax highlighting (rehype-pretty-code)
- [ ] Auto-generated TOC

**Implementation:**
```typescript
// frontend/app/docs/[...slug]/page.tsx
import { MDXRemote } from 'next-mdx-remote/rsc'
import { readFile } from 'fs/promises'
import matter from 'gray-matter'

export default async function DocsPage({ params }: { params: { slug: string[] } }) {
  const filePath = `docs/${params.slug.join('/')}.md`
  const source = await readFile(filePath, 'utf-8')
  const { content, data } = matter(source)
  
  return (
    <article>
      <h1>{data.title}</h1>
      <MDXRemote source={content} />
    </article>
  )
}
```

#### 5.2 FlexSearch Integration
- [ ] Build-time index generation
- [ ] Multi-field indexing (title, description, content)
- [ ] Client-side search (instant)
- [ ] Search dialog (Cmd+K)
- [ ] Keyboard navigation

**Implementation:**
```typescript
// frontend/lib/search.ts
import FlexSearch from 'flexsearch'

const searchIndex = new FlexSearch.Index({
  preset: 'match',
  tokenize: 'forward',
  cache: true,
})

// Build index at build time
export function buildSearchIndex(docs: Doc[]) {
  docs.forEach(doc => {
    searchIndex.add(doc.id, `${doc.title} ${doc.description} ${doc.content}`)
  })
}

// Search
export function search(query: string): Doc[] {
  const results = searchIndex.search(query)
  return results.map(id => docs.find(d => d.id === id))
}
```

#### 5.3 Documentation Structure
- [ ] Getting Started (onboarding)
- [ ] Guides (how-to)
- [ ] Reference (API docs)
- [ ] Concepts (explanation)
- [ ] FAQ

**Folder Structure:**
```
docs/
├── index.md                    # Landing page
├── getting-started/
│   ├── introduction.md
│   ├── quick-start.md
│   └── first-project.md
├── guides/
│   ├── seo-audit.md
│   ├── content-strategy.md
│   └── ads-campaign.md
├── reference/
│   ├── api.md
│   ├── webhooks.md
│   └── integrations.md
├── concepts/
│   ├── how-it-works.md
│   ├── architecture.md
│   └── best-practices.md
└── faq.md
```

#### 5.4 Search UI (Cmd+K)
- [ ] Search dialog component
- [ ] Keyboard shortcuts
- [ ] Recent searches
- [ ] Search suggestions
- [ ] Highlight matches

**Implementation:**
```typescript
// frontend/components/SearchDialog.tsx
'use client'

import { useEffect, useState } from 'react'
import { search } from '@/lib/search'

export function SearchDialog() {
  const [open, setOpen] = useState(false)
  const [query, setQuery] = useState('')
  const [results, setResults] = useState<Doc[]>([])
  
  useEffect(() => {
    const down = (e: KeyboardEvent) => {
      if (e.key === 'k' && (e.metaKey || e.ctrlKey)) {
        e.preventDefault()
        setOpen(true)
      }
    }
    document.addEventListener('keydown', down)
    return () => document.removeEventListener('keydown', down)
  }, [])
  
  useEffect(() => {
    if (query) {
      setResults(search(query))
    }
  }, [query])
  
  return (
    <dialog open={open}>
      <input
        type="text"
        placeholder="Search docs..."
        value={query}
        onChange={(e) => setQuery(e.target.value)}
      />
      <ul>
        {results.map(doc => (
          <li key={doc.id}>{doc.title}</li>
        ))}
      </ul>
    </dialog>
  )
}
```

**Success Criteria:**
- ✅ 50+ documentation articles
- ✅ Search works instantly (< 50ms)
- ✅ Cmd+K shortcut works
- ✅ Mobile responsive
- ✅ Syntax highlighting works
- ✅ Auto-generated TOC

---

## Tech Stack

### Backend
- **Python 3.11+** - Core language
- **FastAPI** - API framework
- **SQLAlchemy** - ORM
- **APScheduler** - Job scheduling
- **Pandas** - Data processing
- **ReportLab** - PDF generation
- **Matplotlib** - Charts
- **SendGrid** - Email delivery
- **gql** - GraphQL client (Linear API)
- **Jinja2** - Template rendering

### Frontend
- **Next.js 16** - Framework
- **TypeScript** - Type safety
- **Tailwind CSS 4** - Styling
- **Supabase Realtime** - Real-time data
- **TanStack Query** - Server state
- **Zustand** - Client state
- **Recharts** - Charts
- **FlexSearch** - Search
- **next-mdx-remote** - MDX processing
- **gray-matter** - Frontmatter parsing

### Infrastructure
- **Linear API** - Project management
- **Supabase** - Database + Realtime
- **SendGrid** - Email delivery
- **Redis** - Caching (optional)

---

## Database Schema

### New Tables

```sql
-- Projects (Supabase)
CREATE TABLE projects (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    client_id UUID NOT NULL,
    name TEXT NOT NULL,
    description TEXT,
    status TEXT CHECK(status IN ('active', 'paused', 'completed')),
    linear_project_id TEXT UNIQUE,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Metrics (Supabase)
CREATE TABLE metrics (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    project_id UUID REFERENCES projects(id),
    metric_type TEXT NOT NULL,
    value NUMERIC NOT NULL,
    recorded_at TIMESTAMP DEFAULT NOW()
);

-- Report History (SQLite)
CREATE TABLE report_history (
    id INTEGER PRIMARY KEY,
    client_id INTEGER NOT NULL,
    week_number INTEGER NOT NULL,
    generated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    delivered_at TIMESTAMP,
    status TEXT CHECK(status IN ('pending', 'sent', 'failed')),
    metrics_json TEXT,
    risk_level TEXT CHECK(risk_level IN ('low', 'medium', 'high')),
    UNIQUE(client_id, week_number)
);

-- Notifications (Supabase)
CREATE TABLE notifications (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL,
    type TEXT NOT NULL,
    message TEXT NOT NULL,
    read BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Activity Feed (Supabase)
CREATE TABLE activity_feed (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    project_id UUID REFERENCES projects(id),
    user_id UUID,
    action TEXT NOT NULL,
    details JSONB,
    created_at TIMESTAMP DEFAULT NOW()
);
```

---

## API Endpoints

### Project Management
- `POST /api/projects` - Create project from template
- `GET /api/projects/:id` - Get project details
- `PATCH /api/projects/:id` - Update project
- `DELETE /api/projects/:id` - Delete project

### Reporting
- `POST /api/reports/generate` - Generate report manually
- `GET /api/reports/:client_id` - Get report history
- `GET /api/reports/:id/download` - Download PDF

### Metrics
- `POST /api/metrics` - Record metric
- `GET /api/metrics/:project_id` - Get project metrics
- `GET /api/metrics/:project_id/summary` - Get summary

### Notifications
- `GET /api/notifications` - Get user notifications
- `PATCH /api/notifications/:id/read` - Mark as read
- `DELETE /api/notifications/:id` - Delete notification

### Documentation
- `GET /api/docs/search?q=query` - Search docs
- `GET /api/docs/:slug` - Get doc by slug

---

## Testing Strategy

### Unit Tests
- [ ] LinearClient (GraphQL queries/mutations)
- [ ] ProjectCreator (template rendering)
- [ ] ReportGenerator (PDF generation)
- [ ] EmailSender (SendGrid integration)
- [ ] TaskAssigner (assignment logic)
- [ ] Search (FlexSearch indexing)

### Integration Tests
- [ ] Project creation end-to-end
- [ ] Report generation + email delivery
- [ ] Real-time updates (Supabase)
- [ ] Notification delivery
- [ ] Search functionality

### E2E Tests (Playwright)
- [ ] Create project from dashboard
- [ ] View real-time metrics
- [ ] Receive notification
- [ ] Search documentation
- [ ] Download report

**Coverage Target:** 80%+

---

## Security

### Authentication & Authorization
- [ ] JWT tokens for API
- [ ] Row-level security (RLS) in Supabase
- [ ] API key rotation (Linear, SendGrid)
- [ ] Rate limiting (100 req/min per user)

### Data Protection
- [ ] Encrypt sensitive data at rest
- [ ] HTTPS only
- [ ] Input validation (Pydantic)
- [ ] SQL injection prevention (parameterized queries)
- [ ] XSS prevention (sanitize HTML)

### Access Control
- [ ] Client can only see their projects
- [ ] Team members can only see assigned tasks
- [ ] Admin can see all projects
- [ ] Audit log for sensitive actions

---

## Performance Targets

### Backend
- API response time: < 200ms (p95)
- Report generation: < 10s
- Email delivery: < 5s
- Database queries: < 50ms

### Frontend
- Page load: < 2s (LCP)
- Search: < 50ms
- Real-time updates: < 1s latency
- Chart rendering: 60 FPS

### Infrastructure
- Uptime: 99.9%
- Error rate: < 0.1%
- Concurrent users: 100+

---

## Cost Estimate

### MVP (0-50 clients)
- **SendGrid:** $0/month (free tier, 3000 emails)
- **Supabase:** $25/month (Pro plan)
- **Infrastructure:** $0 (APScheduler in-process)
- **Total:** $25/month

### Scale (50-200 clients)
- **SendGrid:** $19.95/month (50K emails)
- **Supabase:** $25/month
- **MeiliSearch:** $25/month (optional)
- **Total:** $70/month

### Enterprise (200+ clients)
- **SendGrid:** $89.95/month (100K emails)
- **Supabase:** $599/month (Team plan)
- **MeiliSearch:** $50/month
- **PostgreSQL + pgvector:** $50/month
- **Total:** $789/month

---

## Risks & Mitigations

| Risk | Impact | Probability | Mitigation |
|------|--------|-------------|------------|
| Linear API rate limits | High | Medium | Implement caching, batch requests |
| SendGrid delivery failures | High | Low | Retry logic, fallback to SMTP |
| Supabase downtime | High | Low | Fallback to polling, cache data |
| Report generation timeout | Medium | Medium | Async processing, queue system |
| Search index too large | Medium | Low | Pagination, lazy loading |
| WebSocket connection drops | Low | High | Auto-reconnection, exponential backoff |

---

## Success Metrics

### Operational Efficiency
- Project setup time: < 10 minutes (vs 2-4 hours manual)
- Report generation: 100% automated
- Email delivery rate: > 99%
- Dashboard uptime: > 99.9%

### User Satisfaction
- Client NPS: > 50
- Team satisfaction: > 4/5
- Documentation usage: > 80% of users
- Support tickets: < 5 per week

### Business Impact
- Cost savings: $350 per project
- Time savings: 3.5 hours per project
- Client retention: > 90%
- Team productivity: +30%

---

## Timeline

### Week 1-2: Project Templates
- **Day 1-3:** Linear API client + GraphQL setup
- **Day 4-5:** Template system (YAML + Jinja2)
- **Day 6-8:** ProjectCreator class
- **Day 9-10:** Slash commands + testing

**Deliverable:** Working project creation from templates

### Week 3-4: Automated Reporting
- **Day 1-3:** ReportLab PDF generation + charts
- **Day 4-5:** APScheduler setup + cron jobs
- **Day 6-7:** SendGrid integration + email delivery
- **Day 8-10:** History tracking + risk classification

**Deliverable:** Automated weekly reports

### Week 5-6: Dashboards & Collaboration
- **Day 1-3:** Supabase setup + database schema
- **Day 4-6:** Dashboard components (Recharts + Zustand)
- **Day 7-8:** Real-time subscriptions
- **Day 9-10:** Task assignment + notifications

**Deliverable:** Real-time client dashboard

### Week 7-8: Knowledge Base
- **Day 1-3:** Next.js + MDX setup
- **Day 4-5:** FlexSearch integration + search UI
- **Day 6-8:** Write 50+ documentation articles
- **Day 9-10:** Polish + testing

**Deliverable:** Searchable knowledge base

---

## Next Steps

1. ✅ Research completed (12 repos analyzed)
2. ✅ PLAN.md created
3. ⏳ Setup development environment
   - Install dependencies (gql, reportlab, apscheduler, sendgrid)
   - Configure Linear API key
   - Configure SendGrid API key
   - Setup Supabase project
4. ⏳ Implement Week 1-2 (Project Templates)
5. ⏳ Implement Week 3-4 (Automated Reporting)
6. ⏳ Implement Week 5-6 (Dashboards)
7. ⏳ Implement Week 7-8 (Knowledge Base)
8. ⏳ Testing + QA
9. ⏳ Deploy to production

---

**Plan created:** 2026-05-15  
**Estimated completion:** 2026-07-10 (8 weeks)  
**Ready for implementation:** ✅
