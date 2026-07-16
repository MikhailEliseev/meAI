# Operator Vault Schema

**Version:** 1.0  
**Created:** 2026-05-03  
**Owner:** Operator Agent

## Rules and Conventions

### 1. LLM Wiki Pattern (LAW)

This vault MUST follow Andrej Karpathy's LLM Wiki pattern:

- **Layer 1 (raw/):** Immutable sources
- **Layer 2 (wiki/):** LLM-generated structured knowledge
- **Layer 3 (decisions/):** Tactical decisions

### 2. Wiki Categories (8 required)

Every vault MUST have these 8 categories in `wiki/`:

1. **concepts/** - Concepts and patterns
2. **technologies/** - Technologies and tools
3. **strategies/** - Strategies and methods
4. **agents/** - Agents in the system
5. **workflows/** - Processes and workflows
6. **projects/** - Projects
7. **sources/** - Processed sources (summaries)
8. **connections/** - Links and syntheses

### 3. Special Files

- `wiki/index.md` - Content-oriented catalog (updated on every change)
- `wiki/log.md` - Chronological operations log (append-only)

### 4. Operations

**Ingest:** raw/ → wiki/ (process and categorize)  
**Query:** question → wiki/ → answer + new page  
**Lint:** check health (contradictions, orphans, gaps)

### 5. Frontmatter

Every wiki page MUST have:

```yaml
---
title: "Page Title"
category: concepts|technologies|strategies|agents|workflows|projects|sources|connections
created: YYYY-MM-DD
updated: YYYY-MM-DD
status: draft|active|archived
tags: [tag1, tag2]
---
```

### 6. Processing Status

Raw files MUST have frontmatter:

```yaml
---
status: unprocessed|processed
output: wiki/category/filename.md  # if processed
---
```

### 7. Cross-Vault Communication

- Read other vaults' `wiki/` (NOT raw/)
- Create syntheses in `connections/`
- Reference decisions in `decisions/`

### 8. Log Format

```markdown
## [YYYY-MM-DD HH:MM] operation | Description
```

Operations: `init`, `ingest`, `query`, `lint`, `update`, `archive`

---

**This schema is LAW for this vault.**
