# Test Agent - Schema

**Agent:** Test Agent
**Domain:** test agent
**Created:** 2026-05-09 01:44

---

## Vault Structure

This vault follows the LLM Wiki Pattern:

### Layer 1: raw/
Immutable sources. Never modify files here.

### Layer 2: wiki/
LLM-generated structured knowledge:
- **concepts/** - Domain concepts and patterns
- **technologies/** - Tools and technologies
- **strategies/** - Methods and strategies
- **agents/** - System agents and their roles
- **workflows/** - Processes and workflows
- **projects/** - Project documentation
- **sources/** - Processed source summaries
- **connections/** - Cross-references and syntheses

### Layer 3: decisions/
Strategic decisions with rationale.

---

## Operations

### Ingest
Process raw sources → create wiki pages

### Query
Answer questions → create new wiki pages with citations

### Lint
Check for contradictions, orphans, gaps, stale data

---

## Conventions

- All wiki pages have frontmatter with `status: processed`
- log.md format: `## [YYYY-MM-DD HH:MM] operation | Description`
- index.md updated after each wiki page creation
- Cross-references use [[wiki/category/page]] format
