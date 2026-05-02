# Architect Wiki Schema

**Version:** 1.0  
**Created:** 2026-05-02  
**Purpose:** Define how Architect processes raw notes and maintains knowledge wiki

---

## Overview

This is a **persistent, compounding knowledge base** for system improvement ideas. You (human) drop raw notes into `raw/`. Architect reads them, extracts insights, and integrates them into a structured wiki. The wiki grows over time, building connections and synthesis that persist across sessions.

**Key principle:** Knowledge is compiled once and kept current, not re-derived on every query.

---

## Directory Structure

```
obsidian/architect/
├── raw/                    # Raw inbox (immutable sources)
│   ├── YYYYMMDD-HHMM-topic.md
│   └── ...
├── wiki/                   # Compiled knowledge (Architect-maintained)
│   ├── index.md           # Content catalog
│   ├── log.md             # Chronological record
│   ├── overview.md        # High-level synthesis
│   ├── concepts/          # Concept pages
│   ├── improvements/      # Improvement ideas
│   ├── decisions/         # Architecture decisions
│   └── connections/       # Cross-cutting insights
├── assets/                # Images, files
└── ARCHITECT-WIKI.md      # This schema
```

---

## Operations

### 1. Ingest (Process Raw Notes)

**Trigger:** User says "process raw notes" or "ingest new notes"

**Workflow:**
1. **Scan** `raw/` for unprocessed notes (check `log.md` for what's been processed)
2. **Read** each new note
3. **Discuss** key takeaways with user (optional, user preference)
4. **Extract** insights, ideas, decisions, concepts
5. **Integrate** into wiki:
   - Create/update concept pages
   - Create/update improvement pages
   - Update connections
   - Update overview
   - Update index
6. **Log** the ingest in `log.md`
7. **Mark** raw note as processed (add to log)

**Example:**
```
Raw note: "Idea: exponential backoff for retries"

Actions:
- Update wiki/improvements/retry-logic.md
- Update wiki/concepts/error-handling.md
- Add connection to wiki/concepts/resilience.md
- Update wiki/index.md
- Append to wiki/log.md
```

### 2. Query (Answer Questions)

**Trigger:** User asks a question about the system

**Workflow:**
1. **Search** `wiki/index.md` for relevant pages
2. **Read** relevant pages
3. **Synthesize** answer with citations
4. **Optionally:** File answer back into wiki as new page if valuable

**Example:**
```
Q: "What are our current ideas for improving error handling?"

Actions:
- Read wiki/index.md
- Find wiki/improvements/error-handling.md
- Find wiki/concepts/retry-logic.md
- Synthesize answer
- Optionally: Create wiki/connections/error-handling-synthesis.md
```

### 3. Lint (Health Check)

**Trigger:** User says "lint wiki" or periodically

**Workflow:**
1. **Check** for contradictions between pages
2. **Check** for stale claims (superseded by newer notes)
3. **Check** for orphan pages (no inbound links)
4. **Check** for missing concept pages (mentioned but not defined)
5. **Check** for missing cross-references
6. **Suggest** new questions to investigate
7. **Suggest** new sources to look for

**Output:** Report with findings and suggestions

---

## Page Types

### Concept Pages (`wiki/concepts/`)

**Purpose:** Define key concepts, patterns, principles

**Format:**
```markdown
---
type: concept
created: YYYY-MM-DD
updated: YYYY-MM-DD
sources: [raw/note1.md, raw/note2.md]
related: [concept2, concept3]
---

# Concept Name

## Definition
Clear, concise definition

## Why It Matters
Importance and context

## Current State
How it's implemented in meAI

## Connections
Links to related concepts, improvements, decisions

## Sources
- [[raw/note1]] - Initial idea
- [[raw/note2]] - Refinement
```

### Improvement Pages (`wiki/improvements/`)

**Purpose:** Track improvement ideas, proposals, enhancements

**Format:**
```markdown
---
type: improvement
status: proposed | in-progress | implemented | rejected
priority: high | medium | low
created: YYYY-MM-DD
updated: YYYY-MM-DD
sources: [raw/note1.md]
related: [concept1, improvement2]
---

# Improvement Title

## Problem
What problem does this solve?

## Proposal
What's the proposed solution?

## Benefits
Why is this valuable?

## Tradeoffs
What are the costs/risks?

## Implementation Notes
How would this be implemented?

## Status
Current status and next steps

## Sources
- [[raw/note1]] - Original idea
```

### Decision Pages (`wiki/decisions/`)

**Purpose:** Record architecture decisions and rationale

**Format:**
```markdown
---
type: decision
status: proposed | accepted | rejected | superseded
created: YYYY-MM-DD
updated: YYYY-MM-DD
sources: [raw/note1.md]
---

# Decision Title

## Context
What's the situation?

## Decision
What was decided?

## Rationale
Why this decision?

## Consequences
What are the implications?

## Alternatives Considered
What else was considered and why rejected?

## Sources
- [[raw/note1]] - Context
```

### Connection Pages (`wiki/connections/`)

**Purpose:** Synthesize cross-cutting insights

**Format:**
```markdown
---
type: connection
created: YYYY-MM-DD
updated: YYYY-MM-DD
concepts: [concept1, concept2]
---

# Connection Title

## Insight
What's the connection?

## Why It Matters
Significance of this connection

## Related Pages
- [[concept1]]
- [[concept2]]
- [[improvement1]]
```

---

## Index Format (`wiki/index.md`)

```markdown
# Architect Wiki Index

**Last updated:** YYYY-MM-DD HH:MM  
**Total pages:** N  
**Total sources:** M

## Concepts
- [[concepts/error-handling]] - Error handling patterns and strategies (3 sources)
- [[concepts/retry-logic]] - Retry mechanisms and backoff strategies (2 sources)

## Improvements
- [[improvements/exponential-backoff]] - Add exponential backoff to retries (proposed, high priority)
- [[improvements/circuit-breaker]] - Implement circuit breaker pattern (proposed, medium priority)

## Decisions
- [[decisions/event-bus-architecture]] - Why we chose event-driven architecture (accepted)

## Connections
- [[connections/resilience-patterns]] - How error handling, retries, and timeouts connect

## Overview
- [[overview]] - High-level synthesis of all knowledge
```

---

## Log Format (`wiki/log.md`)

```markdown
# Architect Wiki Log

Chronological record of all operations.

## [2026-05-02 19:54] ingest | Retry logic improvement idea
- Processed: raw/20260502-1954-retry-idea.md
- Created: wiki/improvements/exponential-backoff.md
- Updated: wiki/concepts/retry-logic.md
- Updated: wiki/index.md

## [2026-05-02 19:50] query | Error handling patterns
- Question: "What are our error handling patterns?"
- Pages read: concepts/error-handling.md, improvements/retry-logic.md
- Answer provided with citations

## [2026-05-02 19:45] lint | Health check
- Found 2 orphan pages
- Suggested 3 new concept pages
- Suggested 1 cross-reference
```

---

## Conventions

### File Naming
- Raw notes: `YYYYMMDD-HHMM-topic.md` (timestamped)
- Wiki pages: `kebab-case-title.md` (descriptive)

### Links
- Use `[[wikilinks]]` for internal links
- Use relative paths for assets: `![image](../assets/image.png)`

### Frontmatter
- Always include YAML frontmatter with metadata
- Track `created`, `updated`, `sources`, `related`

### Cross-References
- Link liberally - connections are valuable
- Update bidirectional links (if A links to B, B should mention A)

### Immutability
- Raw notes are **immutable** - never modify them
- Wiki pages are **mutable** - update freely as knowledge evolves

---

## User Preferences

### Ingest Style
- **Interactive** (default): Discuss key takeaways before integrating
- **Batch**: Process multiple notes silently, report summary

### Query Style
- **Concise**: Short answers with citations
- **Detailed**: Full synthesis with examples

### Lint Frequency
- **Manual**: Only when user requests
- **Periodic**: After every N ingests

---

## Tools (Optional)

### Search
- At small scale: Use `wiki/index.md`
- At large scale: Consider `qmd` or custom search

### Obsidian Plugins
- **Graph View**: Visualize connections
- **Dataview**: Query frontmatter
- **Marp**: Generate slide decks

---

## Example Session

```
User: "I have a new idea about retry logic"
User: *creates raw/20260502-1954-retry-idea.md*

User: "Process raw notes"

Architect:
1. Reads raw/20260502-1954-retry-idea.md
2. Extracts: "Use exponential backoff instead of fixed delay"
3. Discusses: "This would reduce load during outages. Should we implement?"
4. User: "Yes, high priority"
5. Creates: wiki/improvements/exponential-backoff.md
6. Updates: wiki/concepts/retry-logic.md
7. Updates: wiki/index.md
8. Logs: wiki/log.md

User: "What are all our retry-related improvements?"

Architect:
1. Reads wiki/index.md
2. Finds: improvements/exponential-backoff.md, improvements/retry-timeout.md
3. Synthesizes answer with links
```

---

## Evolution

This schema will evolve as we learn what works. Update this file as conventions change.

**Version history:**
- 1.0 (2026-05-02): Initial schema based on LLM Wiki pattern

---

**Pattern credit:** Andrej Karpathy's LLM Wiki  
**Implementation:** meAI Architect
