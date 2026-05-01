"""Obsidian vault integration for memory management."""

from pathlib import Path
from typing import Optional
import re
from datetime import datetime


class ObsidianMemory:
    """Manages reading and writing to Obsidian vault."""

    def __init__(self, vault_path: str = "./obsidian"):
        self.vault_path = Path(vault_path)
        self.vault_path.mkdir(parents=True, exist_ok=True)

    def read_note(self, path: str) -> Optional[str]:
        """Read a note from the vault."""
        note_path = self.vault_path / path
        if not note_path.exists():
            return None
        return note_path.read_text(encoding="utf-8")

    def write_note(self, path: str, content: str, frontmatter: Optional[dict] = None) -> None:
        """Write a note to the vault with optional frontmatter."""
        note_path = self.vault_path / path
        note_path.parent.mkdir(parents=True, exist_ok=True)

        if frontmatter:
            fm_lines = ["---"]
            for key, value in frontmatter.items():
                fm_lines.append(f"{key}: {value}")
            fm_lines.append("---\n")
            content = "\n".join(fm_lines) + content

        note_path.write_text(content, encoding="utf-8")

    def append_to_note(self, path: str, content: str) -> None:
        """Append content to an existing note."""
        note_path = self.vault_path / path
        note_path.parent.mkdir(parents=True, exist_ok=True)

        existing = note_path.read_text(encoding="utf-8") if note_path.exists() else ""
        note_path.write_text(existing + "\n" + content, encoding="utf-8")

    def create_daily_note(self) -> str:
        """Create or get today's daily note path."""
        today = datetime.now().strftime("%Y-%m-%d")
        daily_path = f"daily/{today}.md"

        if not (self.vault_path / daily_path).exists():
            self.write_note(
                daily_path,
                f"# {today}\n\n## Tasks\n\n## Notes\n\n## Learnings\n",
                frontmatter={"date": today, "type": "daily"},
            )

        return daily_path

    def search_notes(self, query: str) -> list[Path]:
        """Search for notes containing the query."""
        results = []
        for note_path in self.vault_path.rglob("*.md"):
            content = note_path.read_text(encoding="utf-8")
            if re.search(query, content, re.IGNORECASE):
                results.append(note_path.relative_to(self.vault_path))
        return results
