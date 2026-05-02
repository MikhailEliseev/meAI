# Magisters - Domain Specialists

## Overview

Magisters — это специализированные агенты, которые выполняют задачи в своих доменах (SEO, Content, Ads, SMM, Analytics, Intelligence). Каждый Magister имеет:

- **Hybrid Search** - трёхуровневый поиск знаний
- **Local Memory** - Obsidian vault для кэширования
- **Domain Expertise** - специализированные capabilities
- **Event-Driven** - асинхронная коммуникация

## Architecture

```
Magister
  ├─ Hybrid Search
  │   ├─ Local Cache (SQLite + Obsidian)
  │   ├─ Teacher Query (Qdrant)
  │   └─ Researcher Request
  │
  ├─ Domain Capabilities
  │   ├─ Base: search, cache, query, request
  │   └─ Specific: domain-specific methods
  │
  └─ Memory System
      ├─ knowledge/ - Cached knowledge
      ├─ tasks/ - Task execution logs
      └─ decisions/ - Decision records
```

## Base Magister

### Initialization

```python
from meai.agents.magisters import BaseMagister
from meai.events.event_bus import EventBus
from pathlib import Path

event_bus = EventBus()

magister = BaseMagister(
    agent_id="custom-magister-1",
    magister_type="custom",
    domain="custom_domain",
    event_bus=event_bus,
    vault_path=Path("./obsidian/custom-magister"),
    database_url="sqlite+aiosqlite:///./data/meai.db",
)

await magister.initialize()
```

### Base Capabilities

All Magisters inherit these capabilities:

- `search_knowledge` - Hybrid search for knowledge
- `cache_knowledge` - Cache knowledge locally
- `query_teacher` - Query Teacher's Qdrant
- `request_research` - Request Researcher to investigate

### Hybrid Search

```python
# Search with all levels
results = await magister.search_knowledge(
    query="SEO best practices",
    search_local=True,      # Search local cache first
    search_teacher=True,    # Query Teacher if not found
    search_researcher=True, # Request Researcher if needed
)

# Local only (fastest)
results = await magister.search_knowledge(
    query="SEO best practices",
    search_local=True,
    search_teacher=False,
    search_researcher=False,
)
```

### Caching Knowledge

```python
knowledge = {
    "content": "SEO best practices for 2026...",
    "source": "perplexity",
    "quality_score": 8.5,
    "metadata": {"topic": "seo", "year": "2026"},
}

await magister.cache_knowledge(knowledge, "SEO best practices")
```

## SEO Magister

**Domain:** SEO optimization

### Capabilities

- `analyze_keywords` - Keyword research and analysis
- `optimize_content` - On-page SEO optimization
- `analyze_competitors` - Competitor SEO analysis
- `track_rankings` - Position tracking
- `audit_technical_seo` - Technical SEO audit

### Usage

```python
from meai.agents.magisters import SEOMagister
from meai.agents.base_agent import Task

seo = SEOMagister(event_bus=event_bus)
await seo.initialize()

# Analyze keywords
task = Task(
    task_id="task-1",
    description="Analyze keywords for medical SEO",
    metadata={
        "capability": "analyze_keywords",
        "keywords": ["medical SEO", "healthcare marketing", "patient acquisition"],
    }
)

result = await seo.execute_task(task)
print(f"Analyzed {result.result['keywords_analyzed']} keywords")
```

## Content Magister

**Domain:** Content marketing

### Capabilities

- `generate_content` - Content creation
- `edit_content` - Content editing and improvement
- `plan_content` - Content calendar planning
- `analyze_performance` - Content performance analysis
- `optimize_for_seo` - SEO content optimization

### Usage

```python
from meai.agents.magisters import ContentMagister

content = ContentMagister(event_bus=event_bus)
await content.initialize()

# Generate content
task = Task(
    task_id="task-2",
    description="Generate blog post about medical marketing",
    metadata={
        "capability": "generate_content",
        "topic": "Medical marketing trends 2026",
        "content_type": "article",
    }
)

result = await content.execute_task(task)
```

## Ads Magister

**Domain:** Advertising (PPC, Display, Social)

### Capabilities

- `create_campaign` - Ad campaign creation
- `optimize_budget` - Budget optimization
- `analyze_performance` - Campaign performance analysis
- `ab_test` - A/B testing
- `target_audience` - Audience targeting

### Usage

```python
from meai.agents.magisters import AdsMagister

ads = AdsMagister(event_bus=event_bus)
await ads.initialize()

# Create campaign
task = Task(
    task_id="task-3",
    description="Create Google Ads campaign",
    metadata={
        "capability": "create_campaign",
        "campaign_type": "search",
        "budget": 5000,
    }
)

result = await ads.execute_task(task)
```

## SMM Magister

**Domain:** Social Media Marketing

### Capabilities

- `create_post` - Social media post creation
- `schedule_posts` - Content scheduling
- `engage_audience` - Community engagement
- `analyze_metrics` - Social media analytics
- `manage_campaigns` - Social media campaigns

### Usage

```python
from meai.agents.magisters import SMMMagister

smm = SMMMagister(event_bus=event_bus)
await smm.initialize()

# Create post
task = Task(
    task_id="task-4",
    description="Create LinkedIn post",
    metadata={
        "capability": "create_post",
        "platform": "linkedin",
        "topic": "Medical marketing insights",
    }
)

result = await smm.execute_task(task)
```

## Analytics Magister

**Domain:** Data analytics

### Capabilities

- `analyze_data` - Data analysis
- `create_report` - Report generation
- `track_metrics` - Metrics tracking
- `predict_trends` - Trend prediction
- `optimize_performance` - Performance optimization

### Usage

```python
from meai.agents.magisters import AnalyticsMagister

analytics = AnalyticsMagister(event_bus=event_bus)
await analytics.initialize()

# Analyze data
task = Task(
    task_id="task-5",
    description="Analyze website traffic",
    metadata={
        "capability": "analyze_data",
        "data_source": "google_analytics",
        "metrics": ["sessions", "conversions", "bounce_rate"],
    }
)

result = await analytics.execute_task(task)
```

## Intelligence Magister

**Domain:** Market intelligence

### Capabilities

- `research_market` - Market research
- `analyze_trends` - Trend analysis
- `monitor_competitors` - Competitor monitoring
- `identify_opportunities` - Opportunity identification
- `strategic_insights` - Strategic recommendations

### Usage

```python
from meai.agents.magisters import IntelligenceMagister

intelligence = IntelligenceMagister(event_bus=event_bus)
await intelligence.initialize()

# Research market
task = Task(
    task_id="task-6",
    description="Research medical marketing market",
    metadata={
        "capability": "research_market",
        "market": "medical marketing",
        "industry": "healthcare",
    }
)

result = await intelligence.execute_task(task)
```

## Custom Magister

Create your own domain specialist:

```python
from meai.agents.magisters import BaseMagister
from meai.agents.base_agent import Task, TaskResult

class CustomMagister(BaseMagister):
    """Custom domain specialist"""
    
    def __init__(self, agent_id: str = "custom-magister-1", **kwargs):
        super().__init__(
            agent_id=agent_id,
            magister_type="custom",
            domain="custom_domain",
            **kwargs
        )
    
    def get_capabilities(self) -> list[str]:
        """Add custom capabilities"""
        base = super().get_capabilities()
        return base + [
            "custom_capability_1",
            "custom_capability_2",
        ]
    
    async def execute_task(self, task: Task) -> TaskResult:
        """Handle custom capabilities"""
        capability = task.metadata.get("capability")
        
        if capability == "custom_capability_1":
            return await self._handle_custom_1(task)
        else:
            return await super().execute_task(task)
    
    async def _handle_custom_1(self, task: Task) -> TaskResult:
        """Implement custom capability"""
        # Your logic here
        return TaskResult(
            task_id=task.task_id,
            status="completed",
            result={"custom": "result"},
        )
```

## Memory System

Each Magister has an Obsidian vault:

```
obsidian/
└── {magister-name}/
    ├── INDEX.md              # Vault index
    ├── knowledge/            # Cached knowledge
    │   ├── seo-best-practices.md
    │   └── keyword-research.md
    ├── tasks/                # Task logs
    │   └── 2026-05-02.md
    └── decisions/            # Decision records
        └── 2026-05-02.md
```

### Knowledge Format

```markdown
---
query: SEO best practices
source: teacher
quality_score: 8.5
cached_at: 2026-05-02T19:15:00Z
---

# SEO best practices

Content here...

## Metadata

{
  "topic": "seo",
  "year": "2026"
}
```

## Performance

| Operation | Latency | Cache Hit Rate |
|-----------|---------|----------------|
| Local cache hit | 1-5ms | 80-90% (after 1 month) |
| Teacher query | 50-200ms | - |
| Researcher request | 2-10s | - |

## Configuration

### Cache TTL

```python
magister = BaseMagister(
    agent_id="seo-magister-1",
    magister_type="seo",
    domain="seo",
    event_bus=event_bus,
    vault_path=Path("./obsidian/seo-magister"),
)

# Set cache TTL (default: 24 hours)
magister.cache_ttl_hours = 48  # 48 hours
```

### Teacher ID

```python
# Set Teacher agent ID (default: "teacher-1")
magister.teacher_id = "teacher-custom"
```

## Events

Magisters subscribe to and publish events:

### Subscribed Events

- `knowledge.distributed` - Teacher distributes new knowledge

### Published Events

- `magister.query` - Query Teacher for knowledge
- `research.requested` - Request Researcher to investigate

## Best Practices

1. **Use hybrid search** - Start with local, fallback to Teacher, request Researcher only when needed
2. **Cache aggressively** - Cache all Teacher results locally
3. **Domain-specific** - Keep capabilities focused on domain
4. **Event-driven** - Use Event Bus for async communication
5. **Memory management** - Clean up old cache entries periodically

## Troubleshooting

### Knowledge not found

```python
# Check all search levels
results = await magister.search_knowledge(
    query="your query",
    search_local=True,
    search_teacher=True,
    search_researcher=True,
)

if not results:
    print("Knowledge not found in any source")
    # Request Researcher to investigate
```

### Cache not working

```python
# Verify cache
stats = await magister.tracker.get_knowledge_stats("knowledge-id")
print(f"Usage count: {stats['total_uses']}")
print(f"Last used: {stats['last_used_at']}")
```

### Slow queries

```python
# Use local cache only for speed
results = await magister.search_knowledge(
    query="your query",
    search_local=True,
    search_teacher=False,
    search_researcher=False,
)
```

## See Also

- [Hybrid Search](hybrid-search.md) - Detailed search documentation
- [Experience Learning](experience-learning.md) - Learning system
- [Teacher Agent](teacher.md) - Knowledge management
- [Researcher Agent](researcher.md) - Knowledge collection
