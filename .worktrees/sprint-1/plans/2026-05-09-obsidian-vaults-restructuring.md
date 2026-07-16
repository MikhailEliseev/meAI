# Obsidian Vaults Restructuring Plan (LLM Wiki Pattern)

**Goal:** Restructure all Magister vaults to follow LLM Wiki Pattern from Andrej Karpathy

**Current state:** Vaults exist but don't follow pattern ❌  
**Target state:** All vaults follow LLM Wiki Pattern ✅

---

## LLM Wiki Pattern (FUNDAMENTAL)

**Three layers:**
1. **raw/** - Immutable sources
2. **wiki/** - LLM-generated structured knowledge (8 categories)
3. **decisions/** - Strategic decisions

**Three operations:**
1. **Ingest** - Process raw sources → wiki pages
2. **Query** - Answer questions → create new wiki pages
3. **Lint** - Check health (contradictions, orphans, gaps)

---

## Required Structure (EVERY vault)

```
vault/
├── raw/                    # Layer 1: Immutable sources
├── wiki/                   # Layer 2: Structured knowledge
│   ├── index.md           # Content-oriented catalog
│   ├── log.md             # Chronological operations log
│   ├── concepts/          # Concepts and patterns
│   ├── technologies/      # Technologies and tools
│   ├── strategies/        # Strategies and methods
│   ├── agents/            # System agents
│   ├── workflows/         # Processes and workflows
│   ├── projects/          # Projects
│   ├── sources/           # Processed sources (summaries)
│   └── connections/       # Links and syntheses
├── decisions/             # Layer 3: Strategic decisions
└── SCHEMA.md             # Vault rules and conventions
```

---

## Vaults to Restructure

**Magisters (9 total):**
1. obsidian/seo-magister/
2. obsidian/content-magister/
3. obsidian/ads-magister/
4. obsidian/analytics-magister/
5. obsidian/social-magister/
6. obsidian/intelligence-magister/
7. obsidian/email-magister/
8. Need to create: brand-magister/
9. Need to create: reputation-magister/
10. Need to create: ai-magister/

**Other agents:**
- obsidian/operator/
- obsidian/architect/ (already exists, check structure)
- obsidian/teacher/

---

## Implementation Strategy

### Option 1: Automated Script (Recommended)
**Pros:**
- Fast (all vaults in minutes)
- Consistent structure
- No manual errors

**Cons:**
- Need to write script

### Option 2: Manual per vault
**Pros:**
- Full control

**Cons:**
- Time-consuming (12+ vaults)
- Risk of inconsistency

**Decision:** Option 1 (Automated Script)

---

## Implementation Plan

### Phase 1: Create Restructuring Script

**Script:** `scripts/restructure_vaults.py`

**Features:**
1. Detect existing vaults
2. Create LLM Wiki structure
3. Migrate existing content to appropriate locations
4. Create SCHEMA.md for each vault
5. Create initial index.md and log.md
6. Preserve existing data

**Logic:**
```python
for vault in vaults:
    # Create structure
    create_directory(vault / "raw")
    create_directory(vault / "wiki" / "concepts")
    create_directory(vault / "wiki" / "technologies")
    create_directory(vault / "wiki" / "strategies")
    create_directory(vault / "wiki" / "agents")
    create_directory(vault / "wiki" / "workflows")
    create_directory(vault / "wiki" / "projects")
    create_directory(vault / "wiki" / "sources")
    create_directory(vault / "wiki" / "connections")
    create_directory(vault / "decisions")
    
    # Create files
    create_schema_md(vault)
    create_index_md(vault)
    create_log_md(vault)
    
    # Migrate existing content
    migrate_content(vault)
```

### Phase 2: Run Script on All Vaults

**Execution:**
```bash
python scripts/restructure_vaults.py --vaults obsidian/
```

**Output:**
- All vaults restructured
- Existing content migrated
- SCHEMA.md created for each
- index.md and log.md initialized

### Phase 3: Verification

**Checks:**
1. All vaults have correct structure
2. Existing content preserved
3. SCHEMA.md present
4. index.md and log.md created

---

## SCHEMA.md Template

```markdown
# {Vault Name} - Schema

**Agent:** {Agent Type}  
**Domain:** {Domain}  
**Created:** {Date}

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
```

---

## index.md Template

```markdown
# {Vault Name} - Index

**Last updated:** {Date}  
**Total pages:** {Count}

---

## Categories

### Concepts ({count})
- [[wiki/concepts/page1]]
- [[wiki/concepts/page2]]

### Technologies ({count})
- [[wiki/technologies/page1]]

### Strategies ({count})
- [[wiki/strategies/page1]]

### Agents ({count})
- [[wiki/agents/page1]]

### Workflows ({count})
- [[wiki/workflows/page1]]

### Projects ({count})
- [[wiki/projects/page1]]

### Sources ({count})
- [[wiki/sources/page1]]

### Connections ({count})
- [[wiki/connections/page1]]

---

## Statistics

- Total wiki pages: {count}
- Last ingest: {date}
- Last query: {date}
- Last lint: {date}
```

---

## log.md Template

```markdown
# {Vault Name} - Operations Log

Chronological record of all vault operations.

---

## [YYYY-MM-DD HH:MM] vault.created | Vault initialized with LLM Wiki Pattern

Created structure:
- raw/ (immutable sources)
- wiki/ (8 categories)
- decisions/ (strategic decisions)
- SCHEMA.md (vault rules)

---

## [YYYY-MM-DD HH:MM] ingest | Initial content migration

Migrated existing content from old structure to LLM Wiki Pattern.
```

---

## Migration Strategy

**Existing content mapping:**
- `knowledge/` → `wiki/concepts/` or `wiki/technologies/`
- `tasks/` → `wiki/workflows/` or `wiki/projects/`
- `decisions/` → `decisions/` (keep as is)
- `results/` → `raw/` (immutable sources)
- `INDEX.md` → `wiki/index.md` (restructure)

---

## Execution

**Approach:** Automated script + verification
- Task 1: Create restructuring script
- Task 2: Run on all vaults
- Task 3: Verify structure
- Task 4: Update BaseMagister to use new structure

**Estimated time:** 1-2 hours

---

## Success Criteria

✅ All vaults follow LLM Wiki Pattern
✅ Existing content preserved and migrated
✅ SCHEMA.md created for each vault
✅ index.md and log.md initialized
✅ BaseMagister updated to use new structure
✅ All 3 operations (Ingest, Query, Lint) documented
