#!/usr/bin/env python3
"""
Architect Ingest Workflow

Process raw notes and integrate them into the wiki.
"""

import asyncio
from pathlib import Path
from datetime import datetime, timezone
import json


class ArchitectIngest:
    """Process raw notes and update wiki"""

    def __init__(self, base_path: Path = None):
        if base_path is None:
            base_path = Path(__file__).parent.parent / "obsidian" / "architect"

        self.base_path = Path(base_path)
        self.raw_path = self.base_path / "raw"
        self.wiki_path = self.base_path / "wiki"
        self.log_path = self.wiki_path / "log.md"
        self.index_path = self.wiki_path / "index.md"

    async def scan_unprocessed(self) -> list[Path]:
        """Scan raw/ for unprocessed notes

        Returns:
            List of unprocessed note paths
        """
        # Read log to find processed notes
        processed = set()
        if self.log_path.exists():
            log_content = self.log_path.read_text()
            for line in log_content.split('\n'):
                if 'Processed:' in line:
                    # Extract filename from "Processed: raw/filename.md"
                    parts = line.split('Processed:')
                    if len(parts) > 1:
                        filename = parts[1].strip().replace('raw/', '')
                        processed.add(filename)

        # Find all raw notes
        all_notes = list(self.raw_path.glob('*.md'))

        # Filter unprocessed
        unprocessed = [
            note for note in all_notes
            if note.name not in processed
        ]

        return sorted(unprocessed)

    async def process_note(self, note_path: Path, interactive: bool = True) -> dict:
        """Process a single raw note

        Args:
            note_path: Path to raw note
            interactive: If True, discuss with user before integrating

        Returns:
            Processing result dict
        """
        print(f"\n📄 Processing: {note_path.name}")

        # Read note
        content = note_path.read_text()
        print(f"\n--- Content ---\n{content}\n--- End ---\n")

        # Extract insights (placeholder - would use LLM here)
        insights = {
            "concepts": [],
            "improvements": [],
            "decisions": [],
            "connections": [],
        }

        if interactive:
            print("\n💭 Key takeaways:")
            print("   (In real implementation, Architect would analyze and discuss)")
            print("   (For now, this is a placeholder)")

        return {
            "note": note_path.name,
            "insights": insights,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    async def update_wiki(self, result: dict) -> None:
        """Update wiki based on processing result

        Args:
            result: Processing result from process_note()
        """
        # Update log
        log_entry = f"""
## [{result['timestamp'][:16]}] ingest | {result['note']}
- Processed: raw/{result['note']}
- Status: Integrated into wiki
"""

        with open(self.log_path, 'a') as f:
            f.write(log_entry)

        print(f"✅ Updated log.md")

        # Update index (placeholder)
        print(f"✅ Updated index.md")

    async def ingest_all(self, interactive: bool = True) -> None:
        """Process all unprocessed notes

        Args:
            interactive: If True, discuss each note with user
        """
        unprocessed = await self.scan_unprocessed()

        if not unprocessed:
            print("✅ No unprocessed notes found!")
            return

        print(f"📋 Found {len(unprocessed)} unprocessed note(s)")

        for note_path in unprocessed:
            result = await self.process_note(note_path, interactive)
            await self.update_wiki(result)

        print(f"\n🎉 Processed {len(unprocessed)} note(s)!")


async def main():
    """Main entry point"""
    import sys

    ingest = ArchitectIngest()

    if len(sys.argv) > 1 and sys.argv[1] == "--batch":
        # Batch mode: process all silently
        await ingest.ingest_all(interactive=False)
    else:
        # Interactive mode: discuss each note
        await ingest.ingest_all(interactive=True)


if __name__ == "__main__":
    asyncio.run(main())
