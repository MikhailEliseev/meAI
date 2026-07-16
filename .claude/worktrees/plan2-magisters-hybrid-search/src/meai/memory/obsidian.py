"""Obsidian vault integration for agent memory"""

import os
from pathlib import Path


class ObsidianVault:
    """Obsidian vault manager for agent memory"""

    def __init__(self, vault_path: str = "./obsidian"):
        """Initialize vault

        Args:
            vault_path: Path to Obsidian vault root
        """
        self.vault_path = Path(vault_path)

    async def initialize(self) -> None:
        """Initialize vault (create directories if needed)"""
        self.vault_path.mkdir(parents=True, exist_ok=True)

    async def write_file(self, relative_path: str, content: str) -> None:
        """Write file to vault

        Args:
            relative_path: Path relative to vault root (e.g., "operator/tasks/task-001.md")
            content: File content
        """
        file_path = self.vault_path / relative_path
        file_path.parent.mkdir(parents=True, exist_ok=True)

        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content)

    async def read_file(self, relative_path: str) -> str:
        """Read file from vault

        Args:
            relative_path: Path relative to vault root

        Returns:
            File content
        """
        file_path = self.vault_path / relative_path

        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {relative_path}")

        with open(file_path, "r", encoding="utf-8") as f:
            return f.read()

    async def file_exists(self, relative_path: str) -> bool:
        """Check if file exists

        Args:
            relative_path: Path relative to vault root

        Returns:
            True if file exists
        """
        file_path = self.vault_path / relative_path
        return file_path.exists()

    async def list_files(self, relative_dir: str = "", pattern: str = "*.md") -> list[str]:
        """List files in directory

        Args:
            relative_dir: Directory relative to vault root
            pattern: File pattern (e.g., "*.md")

        Returns:
            List of file paths relative to vault root
        """
        dir_path = self.vault_path / relative_dir

        if not dir_path.exists():
            return []

        files = []
        for file_path in dir_path.glob(pattern):
            if file_path.is_file():
                relative = file_path.relative_to(self.vault_path)
                files.append(str(relative))

        return sorted(files)

    async def search(self, query: str, folder: str = "", limit: int = 10) -> list[dict]:
        """Search for content in vault files

        Args:
            query: Search query
            folder: Folder to search in (relative to vault root)
            limit: Maximum number of results

        Returns:
            List of matching files with content
        """
        results = []
        search_path = self.vault_path / folder if folder else self.vault_path

        if not search_path.exists():
            return results

        # Search in all markdown files
        for file_path in search_path.rglob("*.md"):
            if not file_path.is_file():
                continue

            try:
                content = file_path.read_text(encoding="utf-8")

                # Simple case-insensitive search
                if query.lower() in content.lower():
                    relative_path = file_path.relative_to(self.vault_path)
                    results.append({
                        "path": str(relative_path),
                        "content": content,
                    })

                    if len(results) >= limit:
                        break
            except Exception:
                # Skip files that can't be read
                continue

        return results

    async def write_note(
        self,
        content: str,
        folder: str = "",
        metadata: dict | None = None,
    ) -> str:
        """Write a note with optional frontmatter

        Args:
            content: Note content
            folder: Folder to write to (relative to vault root)
            metadata: Optional metadata for frontmatter

        Returns:
            Path to created note (relative to vault root)
        """
        import uuid
        from datetime import datetime, timezone

        # Generate unique filename
        note_id = uuid.uuid4().hex[:8]
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
        filename = f"{timestamp}-{note_id}.md"

        # Build full content with frontmatter
        full_content = ""
        if metadata:
            full_content += "---\n"
            for key, value in metadata.items():
                full_content += f"{key}: {value}\n"
            full_content += "---\n\n"
        full_content += content

        # Write file
        relative_path = f"{folder}/{filename}" if folder else filename
        await self.write_file(relative_path, full_content)

        return relative_path
