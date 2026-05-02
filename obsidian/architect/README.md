# Architect's Knowledge Base

**Created:** 2026-05-02  
**Purpose:** Personal knowledge base for system improvement ideas

## Structure

```
architect/
├── raw/           # Raw inbox - your unprocessed notes
├── wiki/          # Compiled knowledge - Architect's wiki
├── assets/        # Images, files, attachments
└── ARCHITECT-WIKI.md  # Schema - how Architect processes notes
```

## How It Works

### 1. You Drop Notes
Любые мысли, идеи, информация → `raw/`

### 2. Architect Processes
Периодически читает `raw/`, анализирует, интегрирует в `wiki/`

### 3. Knowledge Compounds
Wiki растёт, связи укрепляются, знания не переоткрываются

## Quick Start

```bash
# Add a note
echo "Idea: improve retry logic with exponential backoff" > raw/$(date +%Y%m%d-%H%M)-retry-idea.md

# Ask Architect to process
# Architect will read, analyze, and update wiki
```

## Files

- `ARCHITECT-WIKI.md` - Schema and workflows
- `wiki/index.md` - Content catalog
- `wiki/log.md` - Chronological record
- `raw/*.md` - Your raw notes (inbox)
- `wiki/*.md` - Compiled knowledge pages

---

**Pattern:** LLM Wiki by Karpathy  
**Implementation:** meAI Architect
