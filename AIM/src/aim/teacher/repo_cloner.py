# AIM/src/aim/teacher/repo_cloner.py
"""GitHub repository cloner."""

import subprocess
from dataclasses import dataclass
from pathlib import Path


@dataclass
class CloneResult:
    """Result of cloning operation."""
    success: bool
    path: Path
    skipped: bool = False
    error: str | None = None


class RepoCloner:
    """Clone GitHub repositories for analysis."""

    def __init__(self, base_dir: str = "~/temp/research-repos"):
        self.base_dir = Path(base_dir).expanduser()
        self.base_dir.mkdir(parents=True, exist_ok=True)

    def clone(self, url: str) -> CloneResult:
        """
        Clone a GitHub repository.

        Args:
            url: GitHub repository URL

        Returns:
            CloneResult with success status and path
        """
        # Extract repo name from URL
        repo_name = url.rstrip("/").split("/")[-1]
        if repo_name.endswith(".git"):
            repo_name = repo_name[:-4]

        target_path = self.base_dir / repo_name

        # Skip if already exists
        if target_path.exists():
            return CloneResult(
                success=True,
                path=target_path,
                skipped=True,
            )

        # Clone repository
        try:
            result = subprocess.run(
                ["git", "clone", url, str(target_path)],
                capture_output=True,
                text=True,
                timeout=300,
            )

            if result.returncode == 0:
                return CloneResult(
                    success=True,
                    path=target_path,
                )
            else:
                return CloneResult(
                    success=False,
                    path=target_path,
                    error=result.stderr,
                )
        except Exception as e:
            return CloneResult(
                success=False,
                path=target_path,
                error=str(e),
            )
