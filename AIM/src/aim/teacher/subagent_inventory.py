# AIM/src/aim/teacher/subagent_inventory.py
"""Subagent inventory scanner."""

import os
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path


@dataclass
class SubagentInfo:
    """Subagent metadata."""
    name: str
    path: str
    created_date: datetime
    has_github_integration: bool
    lines_of_code: int


class SubagentInventory:
    """Scan and inventory all subagents."""

    def __init__(self, subagents_dir: str = "AIM/src/aim/subagents"):
        self.subagents_dir = Path(subagents_dir)

    def scan(self) -> list[SubagentInfo]:
        """Scan subagents directory and return metadata."""
        subagents = []

        # Scan main subagents directory
        for file in self.subagents_dir.glob("*.py"):
            if file.name == "__init__.py":
                continue

            info = self._extract_metadata(file)
            if info:
                subagents.append(info)

        return subagents

    def _extract_metadata(self, file_path: Path) -> SubagentInfo | None:
        """Extract metadata from subagent file."""
        try:
            content = file_path.read_text()

            # Check for GitHub integration markers
            has_github = any([
                "Adapted from" in content,
                "Source:" in content and "github.com" in content,
                "pybreaker" in content,
                "trafilatura" in content,
            ])

            # Get creation date from git
            import subprocess
            result = subprocess.run(
                ["git", "log", "--follow", "--format=%aI", "--", str(file_path)],
                capture_output=True,
                text=True,
            )
            dates = result.stdout.strip().split("\n")
            created_date = datetime.fromisoformat(dates[-1]) if dates and dates[0] else datetime.now()

            # Count lines
            lines = len(content.split("\n"))

            return SubagentInfo(
                name=file_path.stem,
                path=str(file_path),
                created_date=created_date,
                has_github_integration=has_github,
                lines_of_code=lines,
            )
        except Exception:
            return None
