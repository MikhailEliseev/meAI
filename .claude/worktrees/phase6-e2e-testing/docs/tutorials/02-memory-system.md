# Tutorial: Memory System

> Working with Obsidian vaults for agent memory

## Overview

В этом туториале мы научимся работать с памятью агентов через Obsidian vaults.

**Time:** ~10 minutes  
**Level:** Beginner

---

## Step 1: Understanding Agent Memory

Каждый агент имеет свой Obsidian vault:

```
obsidian/agents/{agent_id}/
├── README.md          # Agent info
├── memory/            # Long-term memory
│   ├── context.md     # Current context
│   └── learnings.md   # Accumulated knowledge
├── tasks/             # Task logs
└── decisions/         # Decision logs
```

---

## Step 2: Writing to Memory

```python
from meai.memory.obsidian import ObsidianVault

# Access agent vault
vault = ObsidianVault("./obsidian/agents/seo-agent")

# Write context
await vault.write_file(
    "memory/context.md",
    """# Current Context

## Active Projects
- Competitor analysis for medical marketing
- Keyword research for Q2 campaign

## Recent Insights
- Medical terminology is crucial
- Long-tail keywords perform better
- Competitors focus on educational content
"""
)

# Write learnings
await vault.write_file(
    "memory/learnings.md",
    """# Accumulated Learnings

## SEO Best Practices
1. Focus on E-A-T (Expertise, Authority, Trust)
2. Medical content requires citations
3. User intent matters more than keyword density

## What Works
- Long-form educational content (2000+ words)
- Case studies with data
- FAQ sections for featured snippets
"""
)
```

---

## Step 3: Reading from Memory

```python
# Read context
context = await vault.read_file("memory/context.md")
print("Current context:", context[:200])

# Read learnings
learnings = await vault.read_file("memory/learnings.md")
print("Learnings:", learnings[:200])
```

---

## Step 4: Task Logging

```python
# Log completed task
await vault.write_file(
    "tasks/task-123.md",
    """---
task_id: task-123
status: completed
created: 2026-05-02T10:00:00Z
completed: 2026-05-02T11:30:00Z
---

# Competitor Analysis

## Objective
Analyze top 5 competitors in medical marketing

## Methodology
1. Identified competitors via Google search
2. Analyzed their content strategy
3. Reviewed backlink profiles
4. Assessed keyword targeting

## Results
- **Competitor A**: DR 65, 500+ keywords, focus on long-tail
- **Competitor B**: DR 58, 300+ keywords, focus on local SEO
- **Competitor C**: DR 72, 800+ keywords, comprehensive content

## Key Insights
- All competitors publish 2-3 articles per week
- Average article length: 2500 words
- Strong focus on medical terminology
- Active link building campaigns

## Recommendations
1. Increase content frequency to 3x per week
2. Target long-tail medical keywords
3. Build relationships for quality backlinks
4. Create comprehensive guides (3000+ words)
"""
)
```

---

## Step 5: Decision Logging

```python
# Log decision
await vault.write_file(
    "decisions/decision-001.md",
    """---
decision_id: decision-001
date: 2026-05-02
confidence: 0.85
---

# Decision: Focus on Long-Tail Keywords

## Context
Competitor analysis revealed heavy focus on long-tail keywords with medical terminology.

## Options Considered
1. **Compete on high-volume keywords** (rejected)
   - Too competitive (DR 70+ required)
   - High cost per click
   - Low conversion rates
   
2. **Focus on long-tail keywords** (selected)
   - Lower competition
   - Higher conversion rates
   - Better match for medical audience
   
3. **Mixed approach** (rejected)
   - Dilutes effort
   - Requires more resources

## Decision
Focus exclusively on long-tail keywords with medical terminology.

## Expected Outcomes
- 30% increase in organic traffic within 3 months
- 50% improvement in conversion rate
- Lower cost per acquisition

## Success Metrics
- Track keyword rankings weekly
- Monitor organic traffic monthly
- Measure conversion rate changes
"""
)
```

---

## Step 6: Using Frontmatter

Frontmatter помогает структурировать метаданные:

```python
await vault.write_file(
    "tasks/task-124.md",
    """---
task_id: task-124
status: in_progress
priority: high
assigned_to: seo-agent
created: 2026-05-02T12:00:00Z
deadline: 2026-05-03T18:00:00Z
tags:
  - seo
  - content
  - urgent
---

# Create SEO Content Calendar

## Objective
Plan content for Q2 2026

## Progress
- [x] Research topics
- [x] Identify keywords
- [ ] Create calendar
- [ ] Assign writers
"""
)
```

---

## Step 7: Viewing in Obsidian

1. Open Obsidian app
2. Open vault: `./obsidian`
3. Navigate to `agents/seo-agent/`
4. View files with rich formatting
5. Use graph view to see connections

**Benefits:**
- Visual graph of knowledge
- Full-text search
- Rich markdown editing
- Plugins (calendar, kanban, etc.)

---

## Best Practices

### 1. Organize by Type

```
memory/     → Long-term knowledge
tasks/      → Task logs
decisions/  → Decision records
reports/    → Generated reports
```

### 2. Use Frontmatter

Always include metadata:
```yaml
---
id: unique-id
date: 2026-05-02
status: completed
tags: [seo, analysis]
---
```

### 3. Link Related Notes

```markdown
See also: [[tasks/task-123]] and [[decisions/decision-001]]
```

### 4. Update Context Regularly

```python
# Update context after each task
context = await vault.read_file("memory/context.md")
updated = context + f"\n\n## Update {datetime.now()}\n- Completed task-123\n"
await vault.write_file("memory/context.md", updated)
```

---

## Complete Example

```python
import asyncio
from datetime import datetime, timezone
from meai.memory.obsidian import ObsidianVault

async def main():
    # Initialize vault
    vault = ObsidianVault("./obsidian/agents/seo-agent")
    
    # Write context
    await vault.write_file(
        "memory/context.md",
        "# Current Context\n\nWorking on Q2 SEO strategy..."
    )
    
    # Log task
    await vault.write_file(
        "tasks/task-123.md",
        """---
task_id: task-123
status: completed
---

# Competitor Analysis

Results: 5 competitors analyzed...
"""
    )
    
    # Log decision
    await vault.write_file(
        "decisions/decision-001.md",
        """---
decision_id: decision-001
confidence: 0.85
---

# Focus on Long-Tail Keywords

Rationale: Lower competition, higher conversion...
"""
    )
    
    print("✅ Memory updated")

if __name__ == "__main__":
    asyncio.run(main())
```

---

## Next Steps

- [Tutorial #3: Event Sourcing](03-event-sourcing.md)
- [Tutorial #4: Rollback & Recovery](04-rollback.md)
- [Obsidian Vault API](../api/obsidian.md)
