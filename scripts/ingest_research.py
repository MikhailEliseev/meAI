#!/usr/bin/env python3
"""
Deep Research Ingest Script

Автоматически копирует результаты deep-research в Obsidian vault для отслеживания.

Usage:
    python scripts/ingest_research.py ~/Documents/Blog_Content_Research_20260510/
"""

import json
import shutil
from pathlib import Path
from datetime import datetime
import sys


def ingest_research(research_dir: Path, vault_dir: Path):
    """Ingest research results into Obsidian vault."""

    if not research_dir.exists():
        print(f"❌ Research directory not found: {research_dir}")
        return False

    # Extract metadata from directory name
    dir_name = research_dir.name
    # Format: Topic_Research_YYYYMMDD
    parts = dir_name.split('_')
    date_str = parts[-1] if parts else datetime.now().strftime('%Y%m%d')
    topic = '_'.join(parts[:-2]) if len(parts) > 2 else dir_name

    # Create target directory
    date_formatted = f"{date_str[:4]}-{date_str[4:6]}-{date_str[6:]}"
    target_dir = vault_dir / "raw" / f"{date_formatted}-{topic}"
    target_dir.mkdir(parents=True, exist_ok=True)

    print(f"📥 Ingesting research: {topic}")
    print(f"   Source: {research_dir}")
    print(f"   Target: {target_dir}")

    # Copy files
    files_copied = 0
    for file in research_dir.glob("*"):
        if file.is_file():
            shutil.copy2(file, target_dir / file.name)
            files_copied += 1
            print(f"   ✅ Copied: {file.name}")

    # Read manifest if exists
    manifest_path = research_dir / "run_manifest.json"
    manifest = {}
    if manifest_path.exists():
        with open(manifest_path) as f:
            manifest = json.load(f)

    # Create metadata
    metadata = {
        "topic": topic,
        "date": date_formatted,
        "mode": manifest.get("mode", "unknown"),
        "duration_minutes": 0,  # TODO: extract from manifest
        "tokens": {
            "input": 0,  # TODO: extract from manifest
            "output": 0,
            "total": 0
        },
        "cost_usd": 0.0,  # TODO: calculate
        "sources_count": len(list(research_dir.glob("sources.jsonl"))),
        "report_size_kb": (research_dir / f"{topic}_Research_Report.md").stat().st_size // 1024 if (research_dir / f"{topic}_Research_Report.md").exists() else 0,
        "used_for": [],
        "reused_by": []
    }

    # Save metadata
    with open(target_dir / "manifest.json", "w") as f:
        json.dump(metadata, f, indent=2)

    print(f"   ✅ Created manifest.json")

    # Update wiki/log.md
    log_path = vault_dir / "wiki" / "log.md"
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
    log_entry = f"\n## [{timestamp}] ingest | {topic}\n\n"
    log_entry += f"**Операция:** Ingest research results\n"
    log_entry += f"**Файлов скопировано:** {files_copied}\n"
    log_entry += f"**Размер отчёта:** {metadata['report_size_kb']} KB\n"
    log_entry += f"**Режим:** {metadata['mode']}\n\n"
    log_entry += "---\n"

    with open(log_path, "a") as f:
        f.write(log_entry)

    print(f"   ✅ Updated wiki/log.md")

    # TODO: Update wiki/index.md
    # TODO: Update wiki/statistics/usage.md
    # TODO: Create wiki/topics/{topic}.md

    print(f"✅ Ingest complete: {topic}")
    return True


def main():
    if len(sys.argv) < 2:
        print("Usage: python scripts/ingest_research.py <research_directory>")
        print("Example: python scripts/ingest_research.py ~/Documents/Blog_Content_Research_20260510/")
        sys.exit(1)

    research_dir = Path(sys.argv[1]).expanduser()
    vault_dir = Path(__file__).parent.parent / "obsidian" / "deep-research"

    success = ingest_research(research_dir, vault_dir)
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
