"""Obsidian vault integration for meAI memory system"""

import asyncio
import shutil
from pathlib import Path
from typing import Any

import aiofiles
import yaml


class ObsidianVault:
    """Manages Obsidian vault operations with async file I/O"""

    def __init__(self, vault_path: str):
        """Initialize Obsidian vault manager

        Args:
            vault_path: Path to Obsidian vault directory
        """
        self.vault_path = Path(vault_path)
        self._locks: dict[str, asyncio.Lock] = {}

    async def initialize(self) -> None:
        """Initialize vault directory structure"""
        self.vault_path.mkdir(parents=True, exist_ok=True)

    async def create_agent_vault(self, agent_id: str) -> Path:
        """Create agent-specific vault directory

        Args:
            agent_id: Unique agent identifier

        Returns:
            Path to agent vault directory
        """
        agent_vault = self.vault_path / agent_id
        agent_vault.mkdir(parents=True, exist_ok=True)
        return agent_vault

    def _get_lock(self, file_path: str) -> asyncio.Lock:
        """Get or create lock for file path

        Args:
            file_path: Relative file path

        Returns:
            Lock for the file
        """
        if file_path not in self._locks:
            self._locks[file_path] = asyncio.Lock()
        return self._locks[file_path]

    async def write_file(
        self, file_path: str, content: str, metadata: dict[str, Any] | None = None
    ) -> None:
        """Write file to vault with optional frontmatter

        Args:
            file_path: Relative path within vault
            content: File content
            metadata: Optional YAML frontmatter metadata
        """
        full_path = self.vault_path / file_path
        full_path.parent.mkdir(parents=True, exist_ok=True)

        # Use file lock to prevent concurrent writes
        lock = self._get_lock(file_path)
        async with lock:
            # Build content with frontmatter if provided
            if metadata:
                frontmatter = yaml.dump(metadata, default_flow_style=False)
                full_content = f"---\n{frontmatter}---\n{content}"
            else:
                full_content = content

            async with aiofiles.open(full_path, "w", encoding="utf-8") as f:
                await f.write(full_content)

    async def read_file(self, file_path: str) -> str:
        """Read file from vault

        Args:
            file_path: Relative path within vault

        Returns:
            File content
        """
        full_path = self.vault_path / file_path

        async with aiofiles.open(full_path, "r", encoding="utf-8") as f:
            return await f.read()

    async def create_snapshot(self, snapshot_name: str) -> Path:
        """Create snapshot of current vault state

        Args:
            snapshot_name: Name for the snapshot

        Returns:
            Path to snapshot directory
        """
        snapshot_path = self.vault_path.parent / f".snapshots/{snapshot_name}"
        snapshot_path.parent.mkdir(parents=True, exist_ok=True)

        # Copy vault to snapshot (sync operation, but fast for small vaults)
        await asyncio.to_thread(
            shutil.copytree, self.vault_path, snapshot_path, dirs_exist_ok=True
        )

        return snapshot_path

    async def restore_snapshot(self, snapshot_name: str) -> None:
        """Restore vault from snapshot

        Args:
            snapshot_name: Name of snapshot to restore
        """
        snapshot_path = self.vault_path.parent / f".snapshots/{snapshot_name}"

        if not snapshot_path.exists():
            raise FileNotFoundError(f"Snapshot not found: {snapshot_name}")

        # Remove current vault
        await asyncio.to_thread(shutil.rmtree, self.vault_path)

        # Restore from snapshot
        await asyncio.to_thread(
            shutil.copytree, snapshot_path, self.vault_path, dirs_exist_ok=True
        )
