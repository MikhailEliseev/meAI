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
