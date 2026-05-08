#!/usr/bin/env python3
"""Restructure Obsidian vaults to follow LLM Wiki Pattern

This script:
1. Detects existing vaults in obsidian/
2. Creates LLM Wiki structure (raw/, wiki/, decisions/)
3. Migrates existing content to appropriate locations
4. Creates SCHEMA.md, index.md, log.md for each vault
5. Preserves all existing data
"""

import os
import shutil
from pathlib import Path
from datetime import datetime
from typing import List


class VaultRestructurer:
    """Restructure vaults to LLM Wiki Pattern"""

    def __init__(self, base_path: Path):
        self.base_path = base_path
        self.timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")

    def detect_vaults(self) -> List[Path]:
        """Detect existing vaults"""
        vaults = []
        for item in self.base_path.iterdir():
            if item.is_dir() and not item.name.startswith("."):
                vaults.append(item)
        return sorted(vaults)

    def create_structure(self, vault: Path) -> None:
        """Create LLM Wiki structure"""
        print(f"  Creating structure for {vault.name}...")

        # Create directories
        (vault / "raw").mkdir(exist_ok=True)
        (vault / "wiki").mkdir(exist_ok=True)
        (vault / "wiki" / "concepts").mkdir(exist_ok=True)
        (vault / "wiki" / "technologies").mkdir(exist_ok=True)
        (vault / "wiki" / "strategies").mkdir(exist_ok=True)
        (vault / "wiki" / "agents").mkdir(exist_ok=True)
        (vault / "wiki" / "workflows").mkdir(exist_ok=True)
        (vault / "wiki" / "projects").mkdir(exist_ok=True)
        (vault / "wiki" / "sources").mkdir(exist_ok=True)
        (vault / "wiki" / "connections").mkdir(exist_ok=True)
        (vault / "decisions").mkdir(exist_ok=True)

    def migrate_content(self, vault: Path) -> None:
        """Migrate existing content to new structure"""
        print(f"  Migrating content for {vault.name}...")

        # Migrate knowledge/ → wiki/concepts/
        if (vault / "knowledge").exists():
            for file in (vault / "knowledge").glob("*.md"):
                target = vault / "wiki" / "concepts" / file.name
                if not target.exists():
                    shutil.copy2(file, target)

        # Migrate tasks/ → wiki/workflows/
        if (vault / "tasks").exists():
            for file in (vault / "tasks").glob("*.md"):
                target = vault / "wiki" / "workflows" / file.name
                if not target.exists():
                    shutil.copy2(file, target)

        # Migrate results/ → raw/
        if (vault / "results").exists():
            for file in (vault / "results").glob("*"):
                target = vault / "raw" / file.name
                if not target.exists():
                    if file.is_file():
                        shutil.copy2(file, target)
                    elif file.is_dir():
                        shutil.copytree(file, target, dirs_exist_ok=True)

        # Keep decisions/ as is (already correct location)
        # INDEX.md will be replaced by wiki/index.md

    def create_schema_md(self, vault: Path) -> None:
        """Create SCHEMA.md for vault"""
        vault_name = vault.name.replace("-", " ").title()
        agent_type = vault.name.replace("-magister", "").replace("-", " ").title()

        content = f"""# {vault_name} - Schema

**Agent:** {agent_type}
**Domain:** {agent_type.lower()}
**Created:** {self.timestamp}

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
"""

        schema_path = vault / "SCHEMA.md"
        schema_path.write_text(content)
        print(f"    ✅ Created SCHEMA.md")

    def create_index_md(self, vault: Path) -> None:
        """Create wiki/index.md"""
        vault_name = vault.name.replace("-", " ").title()

        # Count pages in each category
        categories = [
            "concepts", "technologies", "strategies", "agents",
            "workflows", "projects", "sources", "connections"
        ]

        category_counts = {}
        for cat in categories:
            cat_path = vault / "wiki" / cat
            if cat_path.exists():
                category_counts[cat] = len(list(cat_path.glob("*.md")))
            else:
                category_counts[cat] = 0

        total = sum(category_counts.values())

        content = f"""# {vault_name} - Index

**Last updated:** {self.timestamp}
**Total pages:** {total}

---

## Categories

### Concepts ({category_counts['concepts']})
{self._list_pages(vault / "wiki" / "concepts")}

### Technologies ({category_counts['technologies']})
{self._list_pages(vault / "wiki" / "technologies")}

### Strategies ({category_counts['strategies']})
{self._list_pages(vault / "wiki" / "strategies")}

### Agents ({category_counts['agents']})
{self._list_pages(vault / "wiki" / "agents")}

### Workflows ({category_counts['workflows']})
{self._list_pages(vault / "wiki" / "workflows")}

### Projects ({category_counts['projects']})
{self._list_pages(vault / "wiki" / "projects")}

### Sources ({category_counts['sources']})
{self._list_pages(vault / "wiki" / "sources")}

### Connections ({category_counts['connections']})
{self._list_pages(vault / "wiki" / "connections")}

---

## Statistics

- Total wiki pages: {total}
- Last ingest: {self.timestamp}
- Last query: Never
- Last lint: Never
"""

        index_path = vault / "wiki" / "index.md"
        index_path.write_text(content)
        print(f"    ✅ Created wiki/index.md")

    def _list_pages(self, category_path: Path) -> str:
        """List pages in category"""
        if not category_path.exists():
            return "_(empty)_"

        pages = list(category_path.glob("*.md"))
        if not pages:
            return "_(empty)_"

        lines = []
        for page in sorted(pages):
            page_name = page.stem
            lines.append(f"- [[wiki/{category_path.name}/{page_name}]]")

        return "\n".join(lines)

    def create_log_md(self, vault: Path) -> None:
        """Create wiki/log.md"""
        vault_name = vault.name.replace("-", " ").title()

        content = f"""# {vault_name} - Operations Log

Chronological record of all vault operations.

---

## [{self.timestamp}] vault.restructured | Vault restructured to LLM Wiki Pattern

Created structure:
- raw/ (immutable sources)
- wiki/ (8 categories)
- decisions/ (strategic decisions)
- SCHEMA.md (vault rules)

Migrated existing content:
- knowledge/ → wiki/concepts/
- tasks/ → wiki/workflows/
- results/ → raw/
- decisions/ → decisions/ (preserved)

---

## [{self.timestamp}] ingest | Initial content migration

Migrated existing content from old structure to LLM Wiki Pattern.
All existing data preserved.
"""

        log_path = vault / "wiki" / "log.md"
        log_path.write_text(content)
        print(f"    ✅ Created wiki/log.md")

    def restructure_vault(self, vault: Path) -> None:
        """Restructure single vault"""
        print(f"\n📁 Restructuring {vault.name}...")

        # Create structure
        self.create_structure(vault)

        # Migrate content
        self.migrate_content(vault)

        # Create files
        self.create_schema_md(vault)
        self.create_index_md(vault)
        self.create_log_md(vault)

        print(f"  ✅ {vault.name} restructured")

    def run(self) -> None:
        """Run restructuring on all vaults"""
        print("🚀 Starting vault restructuring...")
        print(f"Base path: {self.base_path}")

        vaults = self.detect_vaults()
        print(f"\nFound {len(vaults)} vaults:")
        for vault in vaults:
            print(f"  - {vault.name}")

        print("\n" + "=" * 60)

        for vault in vaults:
            self.restructure_vault(vault)

        print("\n" + "=" * 60)
        print(f"\n✅ All {len(vaults)} vaults restructured!")
        print("\nNext steps:")
        print("1. Review SCHEMA.md in each vault")
        print("2. Check wiki/index.md for migrated content")
        print("3. Verify wiki/log.md for operation history")


def main():
    """Main entry point"""
    base_path = Path(__file__).parent.parent / "obsidian"

    if not base_path.exists():
        print(f"❌ Error: {base_path} does not exist")
        return

    restructurer = VaultRestructurer(base_path)
    restructurer.run()


if __name__ == "__main__":
    main()
