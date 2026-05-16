"""
FullAdopter - Orchestrate full skill adoption workflow.

Workflow:
1. Validate skill and target directory
2. Extract code and dependencies
3. Create target file
4. Adapt imports to project structure
5. Add dependencies to requirements.txt
6. Generate adoption report

Simplified version for Phase 3.0 - focuses on core adoption flow.
"""

from dataclasses import dataclass, field
from pathlib import Path

import structlog

from aim.teacher.skills.skill_selector import Skill
from aim.teacher.skills.skill_extractor import SkillExtractor

logger = structlog.get_logger()


@dataclass
class AdoptionResult:
    """Result of skill adoption."""

    success: bool
    files_created: list[str] = field(default_factory=list)
    dependencies_added: list[str] = field(default_factory=list)
    code_adapted: bool = False
    report: str = ""
    error: str = ""


class FullAdopter:
    """
    Orchestrate full skill adoption workflow.

    Responsibilities:
    - Validate skill and target directory
    - Extract code and dependencies
    - Create target files
    - Adapt imports to project structure
    - Generate adoption report
    """

    def __init__(self):
        self.logger = logger.bind(component="full_adopter")
        self.extractor = SkillExtractor()

    async def adopt(
        self, skill: Skill, target_dir: Path
    ) -> AdoptionResult:
        """
        Adopt skill completely.

        Args:
            skill: Skill to adopt
            target_dir: Target directory for adoption

        Returns:
            AdoptionResult with success status and details
        """
        self.logger.info(
            "adopting_skill",
            skill=skill.name,
            source=skill.source_repo,
            target_dir=str(target_dir),
        )

        # Validate inputs
        if not skill.code_example or not skill.code_example.strip():
            self.logger.error("no_code_to_adopt", skill=skill.name)
            return AdoptionResult(
                success=False,
                error="Skill has no code example to adopt",
            )

        if not target_dir.exists():
            self.logger.error("target_dir_not_exists", target_dir=str(target_dir))
            return AdoptionResult(
                success=False,
                error=f"Target directory does not exist: {target_dir}",
            )

        try:
            # Extract implementation
            extraction = await self.extractor.extract(skill, target_path=target_dir)

            # Create target file
            target_file = self._determine_target_file(skill, target_dir)
            files_created = []

            if target_file:
                target_file.write_text(extraction.code)
                files_created.append(str(target_file))
                self.logger.info("file_created", file=str(target_file))

            # Generate report
            report = self._generate_report(
                skill=skill,
                extraction=extraction,
                files_created=files_created,
            )

            self.logger.info(
                "skill_adopted",
                skill=skill.name,
                files_created=len(files_created),
                dependencies=len(extraction.dependencies),
            )

            return AdoptionResult(
                success=True,
                files_created=files_created,
                dependencies_added=extraction.dependencies,
                code_adapted=True,
                report=report,
            )

        except Exception as e:
            self.logger.error("adoption_failed", skill=skill.name, error=str(e))
            return AdoptionResult(
                success=False,
                error=f"Adoption failed: {str(e)}",
            )

    def _determine_target_file(self, skill: Skill, target_dir: Path) -> Path | None:
        """
        Determine target file path.

        Args:
            skill: Skill being adopted
            target_dir: Target directory

        Returns:
            Target file path or None
        """
        # Use skill file_path as base name
        if skill.file_path:
            file_name = Path(skill.file_path).name
        else:
            # Generate from skill name
            file_name = skill.name.lower().replace(" ", "_") + ".py"

        return target_dir / file_name

    def _generate_report(
        self,
        skill: Skill,
        extraction,
        files_created: list[str],
    ) -> str:
        """
        Generate adoption report.

        Args:
            skill: Adopted skill
            extraction: Extraction result
            files_created: List of created files

        Returns:
            Adoption report (markdown)
        """
        lines = []

        lines.append(f"# Adoption Report: {skill.name}\n")
        lines.append(f"**Source:** {skill.source_repo}\n")
        lines.append(f"**Quality Score:** {skill.quality_score}/100\n")

        lines.append("\n## Files Created\n")
        for file in files_created:
            lines.append(f"- `{file}`")

        lines.append("\n## Dependencies Added\n")
        if extraction.dependencies:
            for dep in extraction.dependencies:
                lines.append(f"- `{dep}`")
        else:
            lines.append("No new dependencies")

        lines.append("\n## Integration Instructions\n")
        lines.append(extraction.integration_instructions)

        lines.append("\n## Next Steps\n")
        lines.append("1. Review adopted code")
        lines.append("2. Install dependencies: `pip install " + " ".join(extraction.dependencies) + "`")
        lines.append("3. Run tests to verify integration")
        lines.append("4. Update documentation")

        return "\n".join(lines)
