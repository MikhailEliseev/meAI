# Teacher Agent Vault Schema

**Version:** 1.0  
**Created:** 2026-05-13  
**Pattern:** LLM Wiki (Andrej Karpathy)

## Purpose

Teacher Agent vault tracks continuous learning and skill adoption across the system. This vault is the **Chief Learning Officer's memory** — monitoring GitHub, industry updates, and teaching other agents.

## Structure

```
teacher/
├── raw/                    # Immutable sources
│   ├── github-repos/       # Cloned repositories for analysis
│   ├── research-reports/   # Deep research outputs
│   └── industry-updates/   # Articles, docs, API changes
├── wiki/                   # Structured knowledge (LLM-generated)
│   ├── index.md           # Content-oriented catalog
│   ├── log.md             # Chronological operations log
│   ├── concepts/          # Learning concepts, patterns
│   ├── technologies/      # Tools, libraries, frameworks
│   ├── strategies/        # Teaching strategies, adoption methods
│   ├── agents/            # Agent profiles and capabilities
│   ├── workflows/         # Learning cycles, processes
│   ├── projects/          # Adoption projects
│   ├── sources/           # Processed sources (summaries)
│   ├── connections/       # Cross-domain insights
│   └── adoption-reports/  # Skill adoption reports (MOVED HERE)
├── decisions/             # Strategic learning decisions
│   ├── learning-strategy.md
│   ├── adoption-criteria.md
│   └── priority-framework.md
└── SCHEMA.md             # This file
```

## Operations

### 1. Ingest (raw/ → wiki/)

**Trigger:** New GitHub repo found, research completed, industry update received

**Process:**
1. Save immutable source to `raw/`
2. Extract key insights
3. Create/update wiki pages in appropriate categories
4. Update `wiki/index.md` and `wiki/log.md`

**Example:**
```bash
# GitHub repo found
raw/github-repos/throttled-py/
  ├── README.md
  ├── src/
  └── manifest.json

# Processed to wiki
wiki/technologies/rate-limiting-libraries.md
wiki/concepts/token-bucket-algorithm.md
wiki/sources/throttled-py-analysis.md
```

### 2. Query (wiki/ → answer)

**Trigger:** Question about learning, skills, or adoption

**Process:**
1. Search relevant wiki pages
2. Synthesize answer with citations
3. Create new page if gap found
4. Update `wiki/log.md`

**Example:**
```
Q: "What rate limiting libraries are production-ready?"
A: Based on wiki/technologies/rate-limiting-libraries.md:
   - throttled-py (635 stars, token bucket)
   - limits (628 stars, multiple strategies)
   [creates wiki/connections/rate-limiting-comparison.md]
```

### 3. Lint (health check)

**Trigger:** Weekly, or before major adoption cycle

**Checks:**
- Contradictions between pages
- Orphaned pages (no links)
- Gaps in coverage (missing categories)
- Stale data (>4 weeks old)

**Output:** `decisions/vault-health-YYYY-MM-DD.md`

## Frontmatter Standards

### Raw Sources

```yaml
---
type: github-repo | research-report | industry-update
source_url: https://...
collected_date: YYYY-MM-DD
status: pending | processed
output: wiki/path/to/processed.md  # if processed
---
```

### Wiki Pages

```yaml
---
category: concepts | technologies | strategies | agents | workflows | projects | sources | connections
created: YYYY-MM-DD
updated: YYYY-MM-DD
tags: [tag1, tag2]
related: [page1.md, page2.md]
confidence: high | medium | low
---
```

### Decisions

```yaml
---
type: strategy | criteria | framework
date: YYYY-MM-DD
status: active | superseded | archived
supersedes: decision-file.md  # if applicable
---
```

## Adoption Reports

**Location:** `wiki/adoption-reports/`

**Naming:** `<subagent>-<skill-name>.md`

**Format:**
```markdown
# Skill Adoption Report: [Skill Name]

**Status:** ✅ SUCCESS | ❌ FAILED | ⏳ IN PROGRESS
**Date:** YYYY-MM-DD HH:MM:SS

## Skill Metadata
- Name, Source, Quality Score, Description

## Adoption Details
- Files Created
- Dependencies Added
- Code Adaptation
- Integration Report

## Next Steps
- Installation commands
- Testing instructions
- Documentation updates
```

## Learning Cycles

**Frequency:** Every 2-4 weeks

**Process:**
1. Read critical subagents list
2. For each subagent:
   - Check last learning date
   - GitHub search (new repos)
   - Deep research (best practices)
   - Gap analysis (compare with current)
3. Prioritize updates (🔴 CRITICAL, 🟡 HIGH, 🟢 LOW)
4. Create adoption tasks
5. Save to `wiki/workflows/learning-cycle-YYYY-MM-DD.md`

## Index Structure

`wiki/index.md` format:
```markdown
# Teacher Agent Knowledge Index

**Last Updated:** YYYY-MM-DD HH:MM:SS
**Total Pages:** N
**Categories:** 8

## Statistics
- Concepts: N pages
- Technologies: N pages
- Strategies: N pages
- Agents: N pages
- Workflows: N pages
- Projects: N pages
- Sources: N pages
- Connections: N pages

## Recent Updates
- [YYYY-MM-DD] Page title (category)
- ...

## By Category
### Concepts
- [Page Title](concepts/page.md) — brief description
...
```

## Log Format

`wiki/log.md` format:
```markdown
# Teacher Agent Operations Log

## [YYYY-MM-DD HH:MM] operation | Description
- Details
- Files affected
- Outcome

...
```

## Rules

1. **Immutability:** `raw/` files are NEVER modified after creation
2. **Processing:** All `raw/` must have `status: processed` before use
3. **Citations:** Wiki pages MUST cite sources from `raw/`
4. **Freshness:** Pages >4 weeks old flagged in Lint
5. **Completeness:** All 8 wiki categories must have content
6. **Connections:** Cross-reference related pages in frontmatter
7. **Decisions:** All strategic changes documented in `decisions/`
8. **Adoption:** All skill adoptions tracked in `wiki/adoption-reports/`

## Metrics

Track in `wiki/index.md`:
- **Coverage:** % of critical subagents monitored
- **Freshness:** Average age of wiki pages
- **Adoption Rate:** % of recommendations implemented
- **Impact:** Performance improvement after adoption
- **Cost:** Average cost per learning cycle

## Maintenance

- **Daily:** Update `wiki/log.md` for all operations
- **Weekly:** Run Lint, update `wiki/index.md`
- **Monthly:** Review `decisions/`, archive stale content
- **Quarterly:** Full vault audit, update SCHEMA.md
