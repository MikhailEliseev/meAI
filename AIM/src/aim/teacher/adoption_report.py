"""
AdoptionReportGenerator - Generate markdown reports about skill adoption.

Generates detailed markdown reports including:
- Skill metadata (name, source, quality score)
- Adoption details (files created, dependencies added)
- Integration instructions
- Success/failure status
"""

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

import structlog

from aim.teacher.skills.skill_selector import Skill
from aim.teacher.adoption.full_adopter import AdoptionResult

logger = structlog.get_logger()


@dataclass
class AdoptionReport:
    """Generated adoption report."""

    skill_name: str
    success: bool
    markdown: str
    timestamp: datetime


class AdoptionReportGenerator:
    """
    Generate markdown reports about skill adoption.

    Responsibilities:
    - Generate detailed markdown reports
    - Include skill metadata and adoption details
    - Format success and failure reports
    - Save reports to files
    """

    def __init__(self):
        self.logger = logger.bind(component="adoption_report_generator")

    def generate(self, skill: Skill, result: AdoptionResult) -> AdoptionReport:
        """
        Generate adoption report.

        Args:
            skill: Skill that was adopted
            result: Adoption result

        Returns:
            AdoptionReport with markdown content
        """
        self.logger.info(
            "generating_report",
            skill=skill.name,
            success=result.success,
        )

        timestamp = datetime.now()

        if result.success:
            markdown = self._generate_success_report(skill, result, timestamp)
        else:
            markdown = self._generate_failure_report(skill, result, timestamp)

        return AdoptionReport(
            skill_name=skill.name,
            success=result.success,
            markdown=markdown,
            timestamp=timestamp,
        )

    def _generate_success_report(
        self, skill: Skill, result: AdoptionResult, timestamp: datetime
    ) -> str:
        """Generate success report."""
        lines = [
            f"# Skill Adoption Report: {skill.name}",
            "",
            f"**Status:** ✅ SUCCESS",
            f"**Date:** {timestamp.strftime('%Y-%m-%d %H:%M:%S')}",
            "",
            "## Skill Metadata",
            "",
            f"- **Name:** {skill.name}",
            f"- **Source:** {skill.source_repo}",
            f"- **Quality Score:** {skill.quality_score:.1f}/100",
            f"- **Description:** {skill.description}",
            "",
            "## Adoption Details",
            "",
        ]

        # Files created
        if result.files_created:
            lines.append("### Files Created")
            lines.append("")
            for file_path in result.files_created:
                lines.append(f"- `{file_path}`")
            lines.append("")

        # Dependencies added
        if result.dependencies_added:
            lines.append("### Dependencies Added")
            lines.append("")
            for dep in result.dependencies_added:
                lines.append(f"- `{dep}`")
            lines.append("")

        # Code adaptation
        if result.code_adapted:
            lines.append("### Code Adaptation")
            lines.append("")
            lines.append("✅ Code was successfully adapted to project structure")
            lines.append("")

        # Report details
        if result.report:
            lines.append("### Integration Report")
            lines.append("")
            lines.append(result.report)
            lines.append("")

        return "\n".join(lines)

    def _generate_failure_report(
        self, skill: Skill, result: AdoptionResult, timestamp: datetime
    ) -> str:
        """Generate failure report."""
        lines = [
            f"# Skill Adoption Report: {skill.name}",
            "",
            f"**Status:** ❌ FAILED",
            f"**Date:** {timestamp.strftime('%Y-%m-%d %H:%M:%S')}",
            "",
            "## Skill Metadata",
            "",
            f"- **Name:** {skill.name}",
            f"- **Source:** {skill.source_repo}",
            f"- **Quality Score:** {skill.quality_score:.1f}/100",
            f"- **Description:** {skill.description}",
            "",
            "## Error Details",
            "",
            f"**Error:** {result.error}",
            "",
        ]

        # Partial results (if any)
        if result.files_created or result.dependencies_added:
            lines.append("## Partial Results")
            lines.append("")

            if result.files_created:
                lines.append("### Files Created (before failure)")
                lines.append("")
                for file_path in result.files_created:
                    lines.append(f"- `{file_path}`")
                lines.append("")

            if result.dependencies_added:
                lines.append("### Dependencies Added (before failure)")
                lines.append("")
                for dep in result.dependencies_added:
                    lines.append(f"- `{dep}`")
                lines.append("")

        return "\n".join(lines)

    def save(self, report: AdoptionReport, output_path: Path) -> None:
        """
        Save report to file.

        Args:
            report: Report to save
            output_path: Path to save report to
        """
        self.logger.info(
            "saving_report",
            skill=report.skill_name,
            path=str(output_path),
        )

        # Create parent directories
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Write report
        output_path.write_text(report.markdown)

        self.logger.info(
            "report_saved",
            skill=report.skill_name,
            path=str(output_path),
        )
