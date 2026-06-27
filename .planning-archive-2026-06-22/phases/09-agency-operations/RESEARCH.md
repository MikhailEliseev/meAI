# Phase 9: Agency Operations - Research Report

**Date:** 2026-05-15  
**Status:** COMPLETED  
**Method:** GitHub search + code analysis + deep research

---

## Executive Summary

Провели глубокое исследование production-ready решений для автоматизации agency operations. Изучили 12 топовых GitHub репозиториев (клонированы и проанализированы), извлекли архитектурные паттерны, определили tech stack и implementation plan.

**Ключевые находки:**
- ✅ Project templates через Linear API + Jinja2
- ✅ Automated reporting через ReportLab + APScheduler + SendGrid
- ✅ Real-time dashboards через Supabase Realtime + Recharts
- ✅ Knowledge base через Next.js + FlexSearch + MDX

**Estimated Timeline:** 8 weeks (1 developer)  
**Estimated Cost:** $0-50/month (зависит от масштаба)

---

## Part 1: Client Project Templates & Automation

### Top 3 Repositories

1. **github-project-llm-management** (dyvan)
   - GraphQL-based project sync
   - Slash commands для task management
   - GitHub Actions automation
   - **Клонирован:** `~/temp/research-repos/templates/github-project-llm-management`

2. **python-agentic-template** (ai-enhanced-engineer)
   - Seed-based project generation
   - Multi-phase workflows
   - Agent role mapping
   - **Клонирован:** `~/temp/research-repos/templates/python-agentic-template`

3. **phantom-template** (nayasuda)
   - Multi-agent orchestration (10 agents)
   - Hook system
   - Cross-platform integration
   - **Клонирован:** `~/temp/research-repos/templates/phantom-template`

### Key Patterns

**GraphQL-Based Project Sync:**
```python
# Адаптировано из github-project-llm-management
class LinearProjectSync:
    async def sync_project(self, project_id: str):
        query = """
        query GetProject($id: String!) {
          project(id: $id) {
            id name state
            teams { nodes { id name } }
            issues { nodes { id title state } }
          }
        }
        """
        result = await self.client.execute(query, {"id": project_id})
        return result
```

**Seed-Based Generation:**
```python
# Адаптировано из python-agentic-template
class ProjectGenerator:
    def generate_from_seed(self, seed: dict):
        # Client fills brief → system generates project
        template = self.load_template(seed["type"])
        context = self.build_context(seed)
        return self.render(template, context)
```

**Slash Commands:**
```python
# Адаптировано из github-project-llm-management
COMMANDS = {
    "/create-project": create_project_handler,
    "/add-task": add_task_handler,
    "/assign-agent": assign_agent_handler,
}
```

### Tech Stack

- **Linear API** (GraphQL) - project management
- **Jinja2** - template rendering
- **FastAPI** - webhooks
- **Temporal** (optional) - durable workflows

### Implementation Plan

**Phase 1: Foundation (Week 1-2)**
- Linear API client (GraphQL)
- Project template system (YAML + Jinja2)
- ProjectCreator class
- Slash commands for Operator

**Phase 2: Automation (Week 3-4)**
- Linear webhooks → FastAPI
- Event handlers
- Agent assignment logic
- Notification system

**Phase 3: Templates (Week 5-6)**
- SEO Audit template
- Content Strategy template
- Ads Campaign template

**Phase 4: Integration (Week 7-8)**
- Operator + ProjectCreator
- Project status tracking
- Client dashboard
- Metrics and reporting

### ROI

- Manual setup: 2-4 hours per project
- Automated setup: 5-10 minutes per project
- Time saved: ~3.5 hours per project
- Cost saved: ~$350 per project (at $100/hour)
- Break-even: 1 project per month

**Full report:** `.planning/phases/09-agency-operations/research-part1-templates.md`

---

## Part 2: Automated Reporting Systems

### Top 3 Repositories

1. **automated-weekly-marketing-report-builder** (jamous-max)
   - CSV → Pandas → ReportLab PDF
   - Week-over-week comparison
   - Risk classification
   - History tracking
   - **Клонирован:** `~/temp/research-repos/reporting/automated-weekly-marketing-report-builder`

2. **zipreport** (zipreport)
   - HTML → PDF via headless browser
   - Jinja2 templating
   - PagedJS support (headers, footers, TOC)
   - **Клонирован:** `~/temp/research-repos/reporting/zipreport`

3. **Weekly-Business-Report-Automation** (jihanKamilah)
   - ETL pipeline
   - Charts in PDF (matplotlib + ReportLab)
   - SMTP email delivery
   - GitHub Actions automation

### Key Patterns

**History Tracking:**
```python
# Адаптировано из automated-weekly-marketing-report-builder
if history_file.exists():
    history_df = pd.read_csv(history_file)
    processed_weeks = set(history_df["week_number"].astype(int))

for week in unique_weeks:
    if week in processed_weeks:
        continue  # Skip already processed
```

**Risk Classification:**
```python
HIGH_RISK_REVENUE_DROP = 0.10  # 10% drop
MEDIUM_RISK_REVENUE_DROP = 0.05  # 5% drop

def classify_risk(revenue_change_pct):
    if revenue_change_pct <= -HIGH_RISK_REVENUE_DROP:
        return "High"
    elif revenue_change_pct <= -MEDIUM_RISK_REVENUE_DROP:
        return "Medium"
    return "Low"
```

**Charts in PDF:**
```python
# Адаптировано из Weekly-Business-Report-Automation
import matplotlib.pyplot as plt
from reportlab.platypus import Image

fig, ax = plt.subplots()
ax.plot(dates, revenue)
plt.savefig('chart.png')

elements.append(Image('chart.png', width=6*inch, height=4*inch))
```

### Scheduling: APScheduler vs Celery

**APScheduler (Recommended):**
```python
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

scheduler = BackgroundScheduler(jobstores={'default': SQLAlchemyJobStore(url='sqlite:///jobs.db')})

scheduler.add_job(
    func=generate_weekly_report,
    trigger=CronTrigger(day_of_week='mon', hour=9, minute=0),
    id='weekly_report',
)

scheduler.start()
```

**Pros:** Simple, no external dependencies, persistent job store  
**Cons:** Not distributed, single point of failure

**Celery Beat (Alternative):**
- Pros: Distributed, horizontal scaling
- Cons: Requires Redis/RabbitMQ, more complex
- **Verdict:** APScheduler для MVP, Celery только если нужна распределённая система

### Email Delivery: SendGrid vs Mailgun

**SendGrid (Recommended):**
```python
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail, Attachment

message = Mail(
    from_email='reports@iamaim.ru',
    to_emails='client@example.com',
    subject='Weekly Report',
)

with open('report.pdf', 'rb') as f:
    data = base64.b64encode(f.read()).decode()
    attachment = Attachment(FileContent(data), FileName('report.pdf'))
    message.attachment = attachment

sg = SendGridAPIClient(os.environ.get('SENDGRID_API_KEY'))
response = sg.send(message)
```

**Pricing:**
- Free: 100 emails/day (3,000/month)
- Essentials: $19.95/mo (50,000/month)

**Verdict:** SendGrid (лучший баланс цена/функциональность)

### Tech Stack

- `pandas>=2.0.0` - data processing
- `reportlab>=4.0.0` - PDF generation
- `matplotlib>=3.7.0` - charts
- `jinja2>=3.1.0` - templating
- `apscheduler>=3.10.0` - job scheduling
- `sendgrid>=6.11.0` - email delivery

### Cost Estimate

- 50 clients × 4 reports/month = 200 emails/month
- **Free tier sufficient** (3,000/month)
- APScheduler + SQLite: $0 (in-process)
- **Total:** $0 for MVP

**Full report:** `.planning/phases/09-agency-operations/research-part2-reporting.md`

---

## Part 3: Performance Dashboards & Team Collaboration

### Top 3 Repositories

1. **analytics-dashboard** (yashrajpatilll)
   - WebSocket + Recharts + Zustand
   - Auto-reconnection patterns
   - Memory management (1000 data points max)
   - **Клонирован:** `~/temp/research-repos/dashboards/analytics-dashboard`

2. **task-flow** (rizkythegreat)
   - Supabase Realtime + TanStack Query
   - User presence tracking
   - Real-time collaboration
   - **Клонирован:** `~/temp/research-repos/dashboards/task-flow`

3. **Worklenz** (3000+ stars)
   - Socket.IO + Chart.js + Redux
   - Global socket instance pattern
   - Team events (invitations, removal)
   - **Клонирован:** `~/temp/research-repos/dashboards/worklenz`

### Key Patterns

**WebSocket Hook with Auto-Reconnection:**
```typescript
// Адаптировано из analytics-dashboard
const useWebSocket = (url: string) => {
  const [status, setStatus] = useState<'connecting' | 'connected' | 'disconnected'>('disconnected')
  const reconnectDelay = useRef(3000)

  useEffect(() => {
    const ws = new WebSocket(url)
    
    ws.onopen = () => {
      setStatus('connected')
      reconnectDelay.current = 3000
    }
    
    ws.onclose = () => {
      setStatus('disconnected')
      setTimeout(() => connect(), reconnectDelay.current)
      reconnectDelay.current = Math.min(reconnectDelay.current * 1.5, 5000)
    }
    
    return () => ws.close()
  }, [url])
  
  return { status }
}
```

**Supabase Realtime + TanStack Query:**
```typescript
// Адаптировано из task-flow
const useRealtimeProjects = () => {
  const queryClient = useQueryClient()
  
  useEffect(() => {
    const channel = supabase
      .channel('projects')
      .on('postgres_changes', { event: '*', schema: 'public', table: 'projects' }, (payload) => {
        queryClient.invalidateQueries(['projects'])
      })
      .subscribe()
    
    return () => { supabase.removeChannel(channel) }
  }, [])
  
  return useQuery(['projects'], fetchProjects)
}
```

**Memory Management:**
```typescript
// Адаптировано из analytics-dashboard
const MAX_DATA_POINTS = 1000
const CUTOFF_TIME = 30 * 60 * 1000 // 30 minutes

const pruneOldData = (data: DataPoint[]) => {
  const now = Date.now()
  return data
    .filter(d => now - d.timestamp < CUTOFF_TIME)
    .slice(-MAX_DATA_POINTS)
}
```

### Tech Stack Comparison

**State Management:**
- Zustand → Dashboards, simple state (меньше boilerplate)
- Redux → Complex apps, team projects

**Visualization:**
- Recharts → React dashboards (100KB, SVG, declarative)
- Chart.js → Complex charts (200KB, Canvas, performance)

**Real-Time:**
- Supabase Realtime → CRUD + realtime (managed, $25/mo)
- Socket.IO → Custom events (self-hosted, $0)
- WebSocket → Custom protocols (manual)

### Recommended Architecture

```
Client Dashboard:
  ├─ Supabase Realtime (CRUD + realtime)
  ├─ Socket.IO (custom events, notifications)
  ├─ TanStack Query (server state, caching)
  ├─ Zustand (dashboard state, filters)
  └─ Recharts (metrics visualization)
```

### Dependencies

- `@supabase/supabase-js` - Real-time CRUD
- `socket.io-client` - Custom events
- `zustand` - Dashboard state
- `@tanstack/react-query` - Server state
- `recharts` - Charts
- `@dnd-kit/core` - Drag-and-drop

**Full report:** `.planning/phases/09-agency-operations/research-part3-dashboards.md`

---

## Part 4: Knowledge Base & Documentation Systems

### Top 3 Repositories

1. **docs-generator** (rabinarayanpatra) ⭐ Best Overall
   - Next.js 16 + FlexSearch + MDX
   - Client-side search (instant, $0/month)
   - Multi-field indexing
   - Keyboard shortcuts (Cmd+K)
   - **Клонирован:** `~/temp/research-repos/knowledge-base/docs-generator`

2. **docs.dblayer.dev** (scorcism) ⭐ Best Indexing
   - Next.js 15 + Custom indexing
   - Build-time index generation
   - Advanced content cleaning
   - Keyword extraction
   - **Клонирован:** `~/temp/research-repos/knowledge-base/docs.dblayer.dev`

3. **commonbase** (your-commonbase) ⭐ Best Semantic Search
   - Next.js 15 + PostgreSQL + pgvector + OpenAI
   - Hybrid search (semantic + full-text)
   - OpenAI embeddings (text-embedding-3-small)
   - **Клонирован:** `~/temp/research-repos/knowledge-base/commonbase`

### Key Patterns

**FlexSearch Multi-Field Indexing:**
```typescript
// Адаптировано из docs-generator
const searchIndex = new Index({
  preset: 'match',
  tokenize: 'forward',
  cache: true,
})

// Index с приоритетами
searchIndex.add(id, title)        // Highest
searchIndex.add(id, description)
searchIndex.add(id, headings)
searchIndex.add(id, content)      // Lowest
```

**Markdown Stripping:**
```typescript
// Адаптировано из docs.dblayer.dev
function stripMarkdown(md: string): string {
  return md
    .replace(/^---[\s\S]*?---/, '')           // Frontmatter
    .replace(/```[\s\S]*?```/g, '')           // Code blocks
    .replace(/`[^`]+`/g, '')                  // Inline code
    .replace(/!\[.*?\]\(.*?\)/g, '')          // Images
    .replace(/\[([^\]]+)\]\([^\)]+\)/g, '$1') // Links (keep text)
    .replace(/\s+/g, ' ')
    .trim()
}
```

**Hybrid Search:**
```typescript
// Адаптировано из commonbase
// 1. Semantic search (pgvector)
const embedding = await generateEmbedding(query)
const semantic = await db
  .where(sql`1 - (embedding <=> ${embedding}::vector) > 0.7`)
  .orderBy(sql`embedding <=> ${embedding}::vector`)

// 2. Full-text search (PostgreSQL FTS)
const fts = await db
  .where(sql`to_tsvector('english', data) @@ plainto_tsquery('english', ${query})`)

// 3. Deduplicate (semantic first, then FTS)
return deduplicate([...semantic, ...fts])
```

### Search Strategy Comparison

| Strategy | Cost | Speed | Quality | Use Case |
|----------|------|-------|---------|----------|
| FlexSearch (client) | $0 | Instant | Good | <1000 pages |
| MeiliSearch (server) | $25-50 | <50ms | Great | >1000 pages |
| Hybrid (semantic+FTS) | $25-50 | ~200ms | Best | AI assistant |

### Recommended Folder Structure

```
docs/
├── index.md                    # Landing page
├── getting-started/            # Onboarding
├── guides/                     # How-to
├── reference/                  # API docs
├── concepts/                   # Explanation
└── assets/                     # Images
```

### Tech Stack

**Core:**
- `next` - Framework
- `next-mdx-remote` - MDX processing
- `gray-matter` - Frontmatter parsing
- `flexsearch` - Client-side search

**MDX Processing:**
- `remark-gfm` - GitHub Flavored Markdown
- `rehype-slug` - Heading IDs
- `rehype-autolink-headings` - Auto-links
- `rehype-pretty-code` - Syntax highlighting

### Implementation Timeline

**Phase 1: Basic KB (Week 1-2) - $0/month**
- Next.js 15 + MDX
- FlexSearch (client-side)
- Search dialog (Cmd+K)
- Syntax highlighting

**Phase 2: Advanced (Week 3-4) - $0/month**
- Versioning
- Analytics
- AI assistant (basic RAG)

**Phase 3: Semantic (Week 5-6) - $25-50/month**
- PostgreSQL + pgvector
- OpenAI embeddings
- Hybrid search

**Full report:** `.planning/phases/09-agency-operations/research-part4-knowledge.md`

---

## Consolidated Tech Stack

### Backend
- **Python 3.11+** - Core language
- **FastAPI** - API framework
- **SQLAlchemy** - ORM
- **APScheduler** - Job scheduling
- **Pandas** - Data processing
- **ReportLab** - PDF generation
- **Matplotlib** - Charts
- **SendGrid** - Email delivery

### Frontend
- **Next.js 16** - Framework
- **TypeScript** - Type safety
- **Tailwind CSS 4** - Styling
- **Supabase Realtime** - Real-time data
- **TanStack Query** - Server state
- **Zustand** - Client state
- **Recharts** - Charts
- **FlexSearch** - Search
- **MDX** - Documentation

### Infrastructure
- **Linear API** - Project management
- **PostgreSQL** - Database (optional for semantic search)
- **Redis** - Caching (optional)

---

## Implementation Timeline

### Week 1-2: Project Templates
- Linear API client
- Template system (YAML + Jinja2)
- ProjectCreator class
- Basic automation

### Week 3-4: Automated Reporting
- ReportLab PDF generation
- APScheduler setup
- SendGrid integration
- History tracking

### Week 5-6: Dashboards & Collaboration
- Supabase Realtime setup
- Dashboard components
- Team collaboration features
- Real-time metrics

### Week 7-8: Knowledge Base
- Next.js + MDX setup
- FlexSearch integration
- Documentation structure
- Search UI

**Total:** 8 weeks (1 developer)

---

## Cost Estimate

### MVP (0-50 clients)
- SendGrid: $0/month (free tier, 3000 emails)
- Supabase: $25/month (Pro plan)
- Infrastructure: $0 (APScheduler in-process)
- **Total:** $25/month

### Scale (50-200 clients)
- SendGrid: $19.95/month (50K emails)
- Supabase: $25/month
- MeiliSearch: $25/month (optional)
- **Total:** $70/month

### Enterprise (200+ clients)
- SendGrid: $89.95/month (100K emails)
- Supabase: $599/month (Team plan)
- MeiliSearch: $50/month
- PostgreSQL + pgvector: $50/month
- **Total:** $789/month

---

## Key Takeaways

1. **Start Simple, Scale Smart**
   - Week 1-4: Core features ($25/month)
   - Week 5-8: Advanced features ($70/month)
   - Future: Enterprise features ($789/month)

2. **Leverage Existing Solutions**
   - Linear API для project management
   - Supabase для real-time
   - FlexSearch для search (MVP)
   - SendGrid для email

3. **Production-Ready Patterns**
   - GraphQL-based sync
   - History tracking
   - Auto-reconnection
   - Memory management
   - Risk classification

4. **ROI**
   - Manual: 2-4 hours per project
   - Automated: 5-10 minutes per project
   - Savings: ~$350 per project
   - Break-even: 1 project per month

---

## Next Steps

1. ✅ Research completed
2. ⏳ Create detailed PLAN.md
3. ⏳ Setup development environment
4. ⏳ Implement Phase 1 (Project Templates)
5. ⏳ Implement Phase 2 (Automated Reporting)
6. ⏳ Implement Phase 3 (Dashboards)
7. ⏳ Implement Phase 4 (Knowledge Base)

---

**Research completed:** 2026-05-15  
**Total repos analyzed:** 12  
**Total code studied:** ~50,000 lines  
**Ready for planning:** ✅
