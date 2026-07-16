# Obsidian Vault API Reference

> Memory management with markdown files

## Overview

**Obsidian Vault** — компонент для работы с Obsidian vaults. Управляет файлами памяти агентов, создаёт snapshots для rollback и обеспечивает thread-safe операции.

## Class: `ObsidianVault`

### Constructor

```python
from meai.memory.obsidian import ObsidianVault

vault = ObsidianVault("./obsidian")
await vault.initialize()
```

**Parameters:**
- `vault_path` (str) — Path to vault root directory

---

## Methods

### `initialize() -> None`

Initialize vault directory.

**Parameters:**
- None

**Returns:**
- None

**Example:**

```python
vault = ObsidianVault("./obsidian")
await vault.initialize()

print("✅ Vault initialized")
```

**What happens:**
1. Creates vault directory if not exists
2. Creates subdirectories (agents/, snapshots/)
3. Sets up file locks

---

### `write_file(file_path: str, content: str) -> None`

Write file to vault.

**Parameters:**
- `file_path` (str) — Relative path within vault
- `content` (str) — File content

**Returns:**
- None

**Example:**

```python
# Write markdown file
await vault.write_file(
    "agents/seo-agent/memory/context.md",
    """# Current Context

Working on competitor analysis for medical marketing.

## Progress
- Analyzed 5 competitors
- Identified 50+ keywords
- Created report
"""
)

print("✅ File written")
```

**With frontmatter:**

```python
await vault.write_file(
    "agents/seo-agent/tasks/task-123.md",
    """---
task_id: task-123
status: completed
created: 2026-05-02
---

# Competitor Analysis

## Results
...
"""
)
```

---

### `read_file(file_path: str) -> str`

Read file from vault.

**Parameters:**
- `file_path` (str) — Relative path within vault

**Returns:**
- `str` — File content

**Raises:**
- `FileNotFoundError` — If file doesn't exist

**Example:**

```python
# Read file
content = await vault.read_file("agents/seo-agent/memory/context.md")

print(content)
```

---

### `create_agent_vault(agent_id: str) -> str`

Create vault for agent.

**Parameters:**
- `agent_id` (str) — Agent identifier

**Returns:**
- `str` — Path to agent vault

**Example:**

```python
# Create agent vault
vault_path = await vault.create_agent_vault("seo-agent")

print(f"Agent vault created: {vault_path}")
# Output: ./obsidian/agents/seo-agent
```

**What happens:**
1. Creates `agents/{agent_id}/` directory
2. Creates subdirectories (memory/, tasks/, decisions/)
3. Creates README.md with agent info

**Vault structure:**
```
agents/seo-agent/
├── README.md
├── memory/
├── tasks/
└── decisions/
```

---

### `create_snapshot(name: str) -> Path`

Create vault snapshot.

**Parameters:**
- `name` (str) — Snapshot name

**Returns:**
- `Path` — Path to snapshot directory

**Example:**

```python
# Create snapshot
snapshot_path = await vault.create_snapshot("before-migration")

print(f"Snapshot created: {snapshot_path}")
# Output: ./obsidian/.snapshots/before-migration
```

**What happens:**
1. Creates `.snapshots/{name}/` directory
2. Copies all vault files to snapshot
3. Returns snapshot path

---

### `restore_snapshot(name: str) -> None`

Restore vault from snapshot.

**Parameters:**
- `name` (str) — Snapshot name

**Returns:**
- None

**Raises:**
- `ValueError` — If snapshot not found

**Example:**

```python
# Restore from snapshot
await vault.restore_snapshot("before-migration")

print("✅ Vault restored")
```

**What happens:**
1. Deletes current vault files
2. Copies files from snapshot
3. Restores vault to snapshot state

---

### `delete_snapshot(name: str) -> None`

Delete snapshot.

**Parameters:**
- `name` (str) — Snapshot name

**Returns:**
- None

**Example:**

```python
# Delete old snapshot
await vault.delete_snapshot("old-snapshot")

print("✅ Snapshot deleted")
```

---

### `list_files(pattern: str = "**/*.md") -> list[str]`

List files in vault.

**Parameters:**
- `pattern` (str) — Glob pattern (default: "**/*.md")

**Returns:**
- `list[str]` — List of file paths

**Example:**

```python
# List all markdown files
files = await vault.list_files("**/*.md")

print(f"Found {len(files)} files:")
for file in files:
    print(f"  - {file}")
```

**With patterns:**

```python
# List files in specific directory
files = await vault.list_files("agents/seo-agent/**/*.md")

# List specific file types
files = await vault.list_files("**/*.json")
```

---

## File Locking

Vault использует file locking для thread-safety:

```python
# Automatic locking
await vault.write_file("test.md", "content")
# File is locked during write

# Concurrent writes are serialized
import asyncio

async def write_task(i):
    await vault.write_file(f"file-{i}.md", f"content {i}")

# All writes are safe
await asyncio.gather(*[write_task(i) for i in range(10)])
```

---

## Frontmatter Support

Vault поддерживает YAML frontmatter:

```python
# Write with frontmatter
await vault.write_file(
    "task.md",
    """---
task_id: task-123
status: completed
priority: high
tags:
  - seo
  - analysis
---

# Task Content

Task details here...
"""
)

# Read with frontmatter
content = await vault.read_file("task.md")

# Parse frontmatter (use external library)
import yaml

parts = content.split("---", 2)
if len(parts) >= 3:
    frontmatter = yaml.safe_load(parts[1])
    body = parts[2].strip()
    
    print(f"Task ID: {frontmatter['task_id']}")
    print(f"Status: {frontmatter['status']}")
```

---

## Use Cases

### 1. Agent Memory

```python
# Write to agent memory
await vault.write_file(
    "agents/seo-agent/memory/context.md",
    """# Current Context

## Active Tasks
- Competitor analysis
- Keyword research

## Recent Learnings
- Medical marketing requires specific terminology
- Competitors focus on long-tail keywords
"""
)

# Read from memory
context = await vault.read_file("agents/seo-agent/memory/context.md")
```

---

### 2. Task Logging

```python
# Log completed task
await vault.write_file(
    "agents/seo-agent/tasks/task-123.md",
    """---
task_id: task-123
status: completed
created: 2026-05-02T10:00:00Z
completed: 2026-05-02T11:30:00Z
---

# Competitor Analysis

## Objective
Analyze top 5 competitors in medical marketing

## Results
- Competitor A: DR 65, 500+ keywords
- Competitor B: DR 58, 300+ keywords
...

## Recommendations
1. Focus on long-tail keywords
2. Build quality backlinks
3. Increase content frequency
"""
)
```

---

### 3. Decision Logging

```python
# Log decision
await vault.write_file(
    "agents/seo-agent/decisions/decision-001.md",
    """---
decision_id: decision-001
date: 2026-05-02
confidence: 0.85
---

# Decision: Focus on Long-Tail Keywords

## Context
Analyzing competitor strategies revealed heavy focus on long-tail keywords.

## Options Considered
1. Compete on high-volume keywords (rejected - too competitive)
2. Focus on long-tail keywords (selected)
3. Mixed approach (rejected - dilutes effort)

## Decision
Focus on long-tail keywords with medical terminology.

## Rationale
- Lower competition
- Higher conversion rates
- Better match for medical audience
"""
)
```

---

### 4. Snapshots for Safety

```python
# Before risky operation
snapshot = await vault.create_snapshot("before-bulk-delete")

try:
    # Risky operation
    await delete_old_files()
    
    print("✅ Operation successful")
    
except Exception as e:
    print(f"❌ Operation failed: {e}")
    
    # Restore from snapshot
    await vault.restore_snapshot("before-bulk-delete")
    
    print("✅ Vault restored")
```

---

## Best Practices

### 1. Use Descriptive Paths

```python
# ✅ Good: Clear, organized paths
"agents/seo-agent/memory/context.md"
"agents/seo-agent/tasks/task-123.md"
"agents/seo-agent/decisions/decision-001.md"

# ❌ Bad: Unclear paths
"file1.md"
"data.md"
"temp.md"
```

### 2. Use Frontmatter for Metadata

```python
# ✅ Good: Structured metadata
"""---
task_id: task-123
status: completed
priority: high
---

# Task Content
"""

# ❌ Bad: No metadata
"""# Task Content"""
```

### 3. Create Snapshots Before Changes

```python
# ✅ Good: Snapshot before changes
snapshot = await vault.create_snapshot("before-migration")
await migrate_vault_structure()

# ❌ Bad: No snapshot
await migrate_vault_structure()  # No way to rollback!
```

### 4. Organize by Agent

```python
# ✅ Good: Agent-specific vaults
agents/
├── seo-agent/
│   ├── memory/
│   ├── tasks/
│   └── decisions/
├── content-agent/
│   ├── memory/
│   ├── tasks/
│   └── decisions/

# ❌ Bad: Mixed files
files/
├── seo-task-1.md
├── content-task-1.md
├── seo-memory.md
```

---

## Error Handling

```python
try:
    content = await vault.read_file("nonexistent.md")
except FileNotFoundError:
    print("File not found")

try:
    await vault.write_file("test.md", "content")
except PermissionError:
    print("Permission denied")

try:
    await vault.restore_snapshot("nonexistent")
except ValueError:
    print("Snapshot not found")
```

---

## Performance

- **Write file:** ~5-20ms
- **Read file:** ~2-10ms
- **Create snapshot:** ~100-500ms (depends on vault size)
- **Restore snapshot:** ~200-1000ms (depends on vault size)
- **List files:** ~10-50ms

---

## Storage

Vault хранит файлы в обычной файловой системе:

```
obsidian/
├── agents/
│   ├── seo-agent/
│   │   ├── README.md
│   │   ├── memory/
│   │   │   └── context.md
│   │   ├── tasks/
│   │   │   └── task-123.md
│   │   └── decisions/
│   │       └── decision-001.md
│   └── content-agent/
│       └── ...
├── .snapshots/
│   ├── before-migration/
│   │   └── ... (full vault copy)
│   └── checkpoint-1/
│       └── ... (full vault copy)
└── SYSTEM.md
```

---

## Integration with Obsidian App

Vault совместим с Obsidian app:

1. Open Obsidian
2. Open vault at `./obsidian`
3. View and edit agent memory
4. Use Obsidian features (graph view, search, etc.)

**Benefits:**
- Visual graph of connections
- Full-text search
- Rich markdown editing
- Plugins and themes

---

## See Also

- [Agent Factory API](agent-factory.md) — Agent creation
- [Rollback API](rollback.md) — Snapshot + replay
- [Tutorial: Memory System](../tutorials/02-memory-system.md)
