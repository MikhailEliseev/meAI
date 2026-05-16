# AIM/src/aim/teacher/upgrade_applier.py
"""Upgrade applier for subagents."""

import shutil
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from aim.teacher.code_generator import CodeGenerator
from aim.teacher.gap_detector import Gap
from aim.teacher.pattern_extractor import PatternExtractor


@dataclass
class UpgradeResult:
    """Result of upgrade operation."""
    success: bool
    file_path: Path
    backup_path: Path | None = None
    patterns_applied: list[str] = None
    error: str | None = None


class UpgradeApplier:
    """Apply upgrades to subagent files."""

    def __init__(self):
        self.extractor = PatternExtractor()
        self.generator = CodeGenerator()

    def apply(
        self,
        file_path: Path,
        gaps: list[Gap],
        github_code: str,
    ) -> UpgradeResult:
        """
        Apply upgrades to a subagent file.

        Args:
            file_path: Path to subagent file
            gaps: List of gaps to fix
            github_code: GitHub code to extract patterns from

        Returns:
            UpgradeResult with success status
        """
        try:
            # Backup original
            backup_path = self.backup(file_path)

            # Read original code
            code = file_path.read_text()

            # Apply each gap fix
            patterns_applied = []
            for gap in gaps:
                # Extract pattern from GitHub code
                pattern = self.extractor.extract(gap.pattern, github_code)
                if not pattern:
                    continue

                # Add imports
                code = self.generator.add_imports(code, pattern)

                # Add to __init__
                code = self.generator.add_to_init(code, pattern)

                patterns_applied.append(gap.pattern)

            # Write updated code
            file_path.write_text(code)

            return UpgradeResult(
                success=True,
                file_path=file_path,
                backup_path=backup_path,
                patterns_applied=patterns_applied,
            )

        except Exception as e:
            return UpgradeResult(
                success=False,
                file_path=file_path,
                error=str(e),
            )

    def backup(self, file_path: Path) -> Path:
        """
        Create backup of file.

        Args:
            file_path: File to backup

        Returns:
            Path to backup file
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = file_path.with_suffix(f".backup.{timestamp}{file_path.suffix}")
        shutil.copy2(file_path, backup_path)
        return backup_path
