"""
Skill Extraction Orchestrator - Orchestrate full skill extraction and teaching workflow.

Workflow:
1. Clone GitHub repo
2. Extract skills (SkillExtractor)
3. Compare each skill (SkillComparator)
4. Select best skills (SkillSelector)
5. Teach selected skills (SkillTeacher)
6. Aggregate results
7. Return report
"""

import time
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

import structlog

from AIM.src.aim.teacher.skills.skill_comparator import (
    ComparisonResult,
    SkillComparator,
)
from AIM.src.aim.teacher.skills.skill_extractor import (
    ExtractedSkill,
    SkillExtractor,
)
from AIM.src.aim.teacher.skills.skill_selector import (
    SelectionCriteria,
    SkillSelector,
)
from AIM.src.aim.teacher.skills.skill_teacher import (
    SkillTeacher,
    TeachingResult,
)

logger = structlog.get_logger()


@dataclass
class SkillExtractionReport:
    """Complete report of skill extraction and teaching."""
    github_repo_url: str
    target_subagent: str
    extraction_result: list[ExtractedSkill]
    comparisons: list[ComparisonResult]
    selection_result: dict[str, Any]  # From SkillSelector.select_skills()
    teaching_results: list[TeachingResult]
    overall_improvement: float  # % improvement
    skills_adopted: int
    skills_kept: int
    skills_skipped: int
    total_time: float  # seconds
    report_timestamp: datetime


class SkillExtractionOrchestrator:
    """
    Orchestrate full skill extraction and teaching workflow.

    Responsibilities:
    - Coordinate all skill extraction components
    - Clone GitHub repos
    - Extract, compare, select, and teach skills
    - Generate comprehensive reports
    - Handle errors and rollback
    """

    def __init__(self):
        self.extractor = SkillExtractor()
        self.comparator = SkillComparator()
        self.selector = SkillSelector()
        self.teacher = SkillTeacher()
        self.logger = logger.bind(component="skill_extraction_orchestrator")

    async def extract_and_teach(
        self,
        github_repo_url: str,
        target_subagent: str,
        adoption_strategy: str = "balanced",
        sandbox_path: Path | None = None,
    ) -> SkillExtractionReport:
        """
        Extract skills from GitHub repo and teach to target subagent.

        Process:
        1. Clone GitHub repo
        2. Extract skills from repo
        3. Compare each skill with ours
        4. Select best skills based on strategy
        5. Create sandbox for safe teaching
        6. Teach selected skills
        7. Aggregate results and generate report

        Args:
            github_repo_url: GitHub repo URL to learn from
            target_subagent: Subagent to teach (e.g., "keyword-research")
            adoption_strategy: "aggressive" | "conservative" | "balanced"
            sandbox_path: Optional sandbox path (for testing)

        Returns:
            SkillExtractionReport with full results
        """
        start_time = time.time()

        self.logger.info(
            "starting_skill_extraction",
            github_repo_url=github_repo_url,
            target_subagent=target_subagent,
            adoption_strategy=adoption_strategy,
        )

        # 1. Clone repo
        repo_path = await self._clone_repo(github_repo_url)

        # 2. Extract skills
        self.logger.info("extracting_skills", repo_path=str(repo_path))
        extraction_result = await self.extractor.extract_skills(repo_path)

        self.logger.info(
            "skills_extracted",
            count=len(extraction_result),
            types=list(set(s.skill_type for s in extraction_result)),
        )

        # 3. Compare each skill
        self.logger.info("comparing_skills")
        our_repo_path = Path(f"AIM/src/aim/subagents/{target_subagent}")

        comparisons = []
        for skill in extraction_result:
            comparison = await self.comparator.compare_skill(
                skill, our_repo_path
            )
            comparisons.append(comparison)

        self.logger.info(
            "skills_compared",
            total=len(comparisons),
            adopt=sum(1 for c in comparisons if c.recommendation == "adopt"),
            consider=sum(1 for c in comparisons if c.recommendation == "improve"),
            skip=sum(1 for c in comparisons if c.recommendation == "keep_ours"),
        )

        # 4. Select best skills
        self.logger.info("selecting_skills", strategy=adoption_strategy)
        selection_criteria = self._get_selection_criteria(adoption_strategy)
        selection_result = self.selector.select_skills(
            comparisons, selection_criteria
        )

        self.logger.info(
            "skills_selected",
            to_adopt=len(selection_result["skills_to_adopt"]),
            to_keep=len(selection_result["skills_to_keep"]),
            to_skip=len(selection_result["skills_to_skip"]),
        )

        # 5. Create sandbox (or use provided)
        if sandbox_path is None:
            sandbox_path = await self._create_sandbox(target_subagent)

        # 6. Teach selected skills
        self.logger.info("teaching_skills", count=len(selection_result["skills_to_adopt"]))
        teaching_results = []

        for selected_skill in selection_result["skills_to_adopt"]:
            try:
                teaching_result = await self.teacher.teach_skill(
                    selected_skill.comparison,
                    target_subagent,
                    sandbox_path,
                )
                teaching_results.append(teaching_result)

                self.logger.info(
                    "skill_taught",
                    skill_name=teaching_result.skill_name,
                    success=teaching_result.taught_successfully,
                    improvement=teaching_result.improvement,
                )
            except Exception as e:
                self.logger.error(
                    "skill_teaching_failed",
                    skill_name=selected_skill.comparison.skill_type.value,
                    error=str(e),
                )

        # 7. Calculate overall improvement
        successful_teachings = [
            tr for tr in teaching_results if tr.taught_successfully
        ]

        if successful_teachings:
            overall_improvement = sum(
                tr.improvement for tr in successful_teachings
            ) / len(successful_teachings)
        else:
            overall_improvement = 0.0

        total_time = time.time() - start_time

        self.logger.info(
            "skill_extraction_complete",
            overall_improvement=overall_improvement,
            skills_adopted=len(teaching_results),
            total_time=total_time,
        )

        return SkillExtractionReport(
            github_repo_url=github_repo_url,
            target_subagent=target_subagent,
            extraction_result=extraction_result,
            comparisons=comparisons,
            selection_result=selection_result,
            teaching_results=teaching_results,
            overall_improvement=overall_improvement,
            skills_adopted=len(teaching_results),
            skills_kept=len(selection_result["skills_to_keep"]),
            skills_skipped=len(selection_result["skills_to_skip"]),
            total_time=total_time,
            report_timestamp=datetime.now(),
        )

    async def _clone_repo(self, github_repo_url: str) -> Path:
        """
        Clone GitHub repo to temp directory.

        Args:
            github_repo_url: GitHub repo URL

        Returns:
            Path to cloned repo
        """
        # TODO: Implement actual git clone
        # For now, return mock path
        repo_name = github_repo_url.split("/")[-1].replace(".git", "")
        repo_path = Path(f"/tmp/teacher-repos/{repo_name}")

        self.logger.info("repo_cloned", url=github_repo_url, path=str(repo_path))

        return repo_path

    async def _create_sandbox(self, target_subagent: str) -> Path:
        """
        Create sandbox worktree for safe teaching.

        Args:
            target_subagent: Subagent name

        Returns:
            Path to sandbox worktree
        """
        # TODO: Implement actual git worktree creation
        # For now, return mock path
        sandbox_path = Path(f".claude/worktrees/teacher-{target_subagent}")

        self.logger.info(
            "sandbox_created",
            target_subagent=target_subagent,
            path=str(sandbox_path),
        )

        return sandbox_path

    def _get_selection_criteria(self, adoption_strategy: str) -> SelectionCriteria:
        """
        Get selection criteria based on adoption strategy.

        Strategies:
        - aggressive: Low threshold, prioritize adoption
        - conservative: High threshold, prioritize safety
        - balanced: Medium threshold, balance adoption and safety

        Args:
            adoption_strategy: "aggressive" | "conservative" | "balanced"

        Returns:
            SelectionCriteria for SkillSelector
        """
        if adoption_strategy == "aggressive":
            return SelectionCriteria(
                min_score_threshold=60.0,
                min_improvement_threshold=5.0,
                max_skills_per_type=5,
                prioritize_security=False,
                budget_limit=None,
            )
        elif adoption_strategy == "conservative":
            return SelectionCriteria(
                min_score_threshold=80.0,
                min_improvement_threshold=15.0,
                max_skills_per_type=2,
                prioritize_security=True,
                budget_limit=10,
            )
        else:  # balanced
            return SelectionCriteria(
                min_score_threshold=70.0,
                min_improvement_threshold=10.0,
                max_skills_per_type=3,
                prioritize_security=True,
                budget_limit=None,
            )

    def format_report(self, report: SkillExtractionReport) -> str:
        """
        Format report as human-readable markdown.

        Args:
            report: SkillExtractionReport to format

        Returns:
            Markdown-formatted report
        """
        md = f"""# Skill Extraction Report

**GitHub Repo:** {report.github_repo_url}
**Target Subagent:** {report.target_subagent}
**Timestamp:** {report.report_timestamp.strftime('%Y-%m-%d %H:%M:%S') if report.report_timestamp else 'N/A'}
**Total Time:** {report.total_time:.1f}s

---

## Summary

- **Skills Extracted:** {len(report.extraction_result)}
- **Skills Compared:** {len(report.comparisons)}
- **Skills Adopted:** {report.skills_adopted}
- **Skills Kept:** {report.skills_kept}
- **Skills Skipped:** {report.skills_skipped}
- **Overall Improvement:** {report.overall_improvement:.1f}%

---

## Extracted Skills

"""

        for skill in report.extraction_result:
            md += f"- **{skill.name}** ({skill.skill_type.value})\n"

        md += "\n---\n\n## Comparisons\n\n"

        for comp in report.comparisons:
            md += f"""### {comp.skill_type.value}

- **Type:** {comp.skill_type.value}
- **GitHub Score:** {comp.github_score.total_score:.1f}/100
- **Our Score:** {comp.our_score.total_score:.1f}/100
- **Gap Analysis:** {comp.gap_analysis}
- **Recommendation:** {comp.recommendation}

"""

        md += "---\n\n## Selection Results\n\n"

        md += f"**Skills to Adopt:** {len(report.selection_result['skills_to_adopt'])}\n\n"
        for selected in report.selection_result['skills_to_adopt']:
            md += f"- {selected.comparison.skill_type.value} (priority {selected.priority}, score {selected.selection_score:.1f})\n"

        md += f"\n**Skills to Keep:** {len(report.selection_result['skills_to_keep'])}\n\n"
        for kept in report.selection_result['skills_to_keep']:
            md += f"- {kept.skill_type.value}\n"

        md += "\n---\n\n## Teaching Results\n\n"

        for teaching in report.teaching_results:
            status = "✅ SUCCESS" if teaching.taught_successfully else "❌ FAILED"
            md += f"""### {teaching.skill_name} {status}

- **Type:** {teaching.skill_type}
- **Improvement:** {teaching.improvement:.1f}%
- **Integration Points:** {len(teaching.integration_points)}
- **Code Changes:** {len(teaching.code_changes)}
- **Tests Added:** {len(teaching.tests_added)}

**Before Metrics:**
"""
            for metric, value in teaching.before_metrics.items():
                md += f"- {metric}: {value:.1f}\n"

            md += "\n**After Metrics:**\n"
            for metric, value in teaching.after_metrics.items():
                md += f"- {metric}: {value:.1f}\n"

            md += f"\n**Teaching Notes:**\n{teaching.teaching_notes}\n\n"

        md += "---\n\n## Conclusion\n\n"

        if report.overall_improvement > 0:
            md += f"✅ **Success!** Overall improvement of {report.overall_improvement:.1f}% achieved.\n"
        else:
            md += "⚠️ **No improvement** detected. Consider different adoption strategy.\n"

        return md
