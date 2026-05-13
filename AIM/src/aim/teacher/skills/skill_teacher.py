"""
Skill Teacher - Orchestrates full teaching workflow.

Teaching process (CORRECT workflow):
1. Research domain-specific solutions (GitHub search)
2. Clone ALL found repositories
3. Extract skills from ALL repos
4. Compare and rank skills
5. Extract best implementation (deep)
6. Apply to codebase
7. Test
8. Commit

This is the main entry point for teaching subagents.
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any
import subprocess

import structlog

from AIM.src.aim.teacher.skills.skill_comparator import SkillComparator
from AIM.src.aim.teacher.skills.skill_extractor import SkillExtractor
from AIM.src.aim.teacher.skills.skill_selector import Skill, SkillSelector
from AIM.src.aim.teacher.skills.skill_applier import SkillApplier

logger = structlog.get_logger()


@dataclass
class TestResults:
    """Results of test execution."""
    success: bool
    summary: str
    output: str
    failures: list[str] = field(default_factory=list)


@dataclass
class CommitResult:
    """Result of git commit."""
    success: bool
    commit_hash: str | None
    message: str = ""
    error: str | None = None


@dataclass
class TeachingReport:
    """Report of teaching session."""

    subagent_name: str
    domain: str
    repos_found: int
    repos_cloned: int
    skills_extracted: int
    best_skill: Skill | None
    files_created: list[Path] = field(default_factory=list)
    files_modified: list[Path] = field(default_factory=list)
    dependencies_added: list[str] = field(default_factory=list)
    tests_created: list[Path] = field(default_factory=list)
    test_results: TestResults | None = None
    commit_hash: str | None = None
    success: bool = False
    error: str | None = None


@dataclass
class IntegrationPoint:
    """Where to integrate the skill."""
    file_path: Path
    class_name: str | None
    function_name: str | None
    line_number: int | None
    reason: str  # Why integrate here


@dataclass
class AdaptedCode:
    """Adapted code for our architecture."""
    original_pattern: str  # Original GitHub pattern
    adapted_pattern: str  # Our adapted version
    adaptation_notes: str  # What changed and why
    dependencies: list[str]  # New dependencies needed
    imports: list[str]  # New imports needed


@dataclass
class TeachingResult:
    """Result of teaching a skill."""
    skill_name: str
    skill_type: str
    target_subagent: str
    taught_successfully: bool
    integration_points: list[IntegrationPoint]
    before_metrics: dict[str, float]
    after_metrics: dict[str, float]
    improvement: float  # % improvement
    code_changes: list[str]  # Changed files
    tests_added: list[str]  # Added test files
    teaching_notes: str
    metadata: dict[str, Any]


class SkillTeacher:
    """
    Orchestrates full teaching workflow.

    Responsibilities:
    - Coordinate all skill components (Selector, Extractor, Comparator)
    - Manage full workflow from research to commit
    - Handle errors and rollback
    - Generate teaching reports

    Teaching philosophy:
    - Clone ALL repos (not just search)
    - Extract from ALL repos (not just one)
    - Take EVERYTHING valuable (not just easy stuff)
    - Deep extraction (parameters, edge cases, tests, metrics)
    - Apply to codebase (not just document)
    """

    def __init__(self, project_root: Path):
        self.logger = logger.bind(component="skill_teacher")
        self.selector = SkillSelector()
        self.extractor = SkillExtractor()
        self.comparator = SkillComparator()
        self.applier = SkillApplier(project_root)

    async def _run_tests(
        self,
        test_files: list[Path],
        subagent_name: str
    ) -> TestResults:
        """Run pytest on applied code."""

        if not test_files:
            return TestResults(
                success=True,
                summary="No tests to run",
                output=""
            )

        # Run pytest
        cmd = f"pytest {' '.join(str(f) for f in test_files)} -v"
        result = subprocess.run(
            cmd,
            shell=True,
            capture_output=True,
            text=True,
            timeout=300
        )

        return TestResults(
            success=result.returncode == 0,
            summary=f"{len(test_files)} test files",
            output=result.stdout + result.stderr,
            failures=[] if result.returncode == 0 else ["pytest failed"]
        )

    async def _commit_changes(
        self,
        files_created: list[Path],
        files_modified: list[Path],
        subagent_name: str,
        skill_name: str,
        source_repo: str
    ) -> CommitResult:
        """Commit applied changes with teaching metadata."""

        all_files = files_created + files_modified

        if not all_files:
            return CommitResult(
                success=True,
                commit_hash=None,
                message="No changes to commit"
            )

        # Stage files
        for file in all_files:
            subprocess.run(["git", "add", str(file)], check=True)

        # Create commit message
        message = f"""teach({subagent_name}): apply {skill_name}

Taught {subagent_name} with skill from {source_repo}

Files created: {len(files_created)}
Files modified: {len(files_modified)}

Source: {source_repo}
Skill: {skill_name}

Co-Authored-By: Teacher Agent <teacher@aim.ai>"""

        # Commit
        result = subprocess.run(
            ["git", "commit", "-m", message],
            capture_output=True,
            text=True
        )

        if result.returncode != 0:
            return CommitResult(
                success=False,
                commit_hash=None,
                error=result.stderr
            )

        # Get commit hash
        hash_result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            capture_output=True,
            text=True,
            check=True
        )

        return CommitResult(
            success=True,
            commit_hash=hash_result.stdout.strip(),
            message=message
        )

    async def teach_subagent(
        self, subagent_name: str, domain: str
    ) -> TeachingReport:
        """
        Teach subagent with domain-specific skills.

        Full workflow (CORRECT):
        1. Research and clone ALL repos
        2. Extract skills from ALL repos
        3. Compare and rank
        4. Extract best implementation
        5. Apply to codebase (TODO)
        6. Test (TODO)
        7. Commit (TODO)

        Args:
            subagent_name: Name of subagent (e.g., "ads", "seo")
            domain: Domain description (e.g., "advertising automation")

        Returns:
            TeachingReport with results
        """
        self.logger.info(
            "teaching_start",
            subagent=subagent_name,
            domain=domain,
        )

        report = TeachingReport(
            subagent_name=subagent_name,
            domain=domain,
            repos_found=0,
            repos_cloned=0,
            skills_extracted=0,
            best_skill=None,
        )

        try:
            # Step 1: Research and clone ALL repos
            self.logger.info("step_1_research_and_clone")
            cloned_repos = await self.selector.research_and_clone(
                subagent_name, domain
            )

            report.repos_found = len(cloned_repos)
            report.repos_cloned = len(cloned_repos)

            if not cloned_repos:
                self.logger.warning("no_repos_found")
                report.error = "No repositories found"
                return report

            # Step 2: Extract skills from ALL repos
            self.logger.info("step_2_extract_skills", repos=len(cloned_repos))
            all_skills = []

            for repo_url, repo_path in cloned_repos.items():
                skills = await self.selector.extract_skills(
                    repo_path, subagent_type=subagent_name
                )
                all_skills.extend(skills)
                self.logger.info(
                    "skills_extracted_from_repo",
                    repo=repo_url,
                    skills_count=len(skills),
                )

            report.skills_extracted = len(all_skills)

            if not all_skills:
                self.logger.warning("no_skills_extracted")
                report.error = "No skills extracted from repositories"
                return report

            # Step 3: Compare and rank skills
            self.logger.info("step_3_compare_skills", total_skills=len(all_skills))
            comparison = await self.comparator.compare(all_skills)

            if not comparison.best_skill:
                self.logger.warning("no_best_skill")
                report.error = "Could not determine best skill"
                return report

            report.best_skill = comparison.best_skill

            self.logger.info(
                "best_skill_selected",
                skill=comparison.best_skill.name,
                source=comparison.best_skill.source_repo,
                quality_score=comparison.best_skill.quality_score,
            )

            # Step 4: Extract best implementation
            self.logger.info("step_4_extract_implementation")
            implementation = await self.extractor.extract(
                comparison.best_skill, target_path=None
            )

            self.logger.info(
                "implementation_extracted",
                dependencies=len(implementation.dependencies),
                target_path=str(implementation.suggested_path)
                if implementation.suggested_path
                else None,
            )

            # Step 5: Apply to codebase
            self.logger.info("step_5_apply_to_codebase")
            application = await self.applier.apply(
                implementation,
                target_path=None,  # Use suggested path from implementation
                subagent_name=subagent_name,
            )

            if not application.success:
                self.logger.error(
                    "application_failed",
                    error=application.error,
                )
                report.error = f"Application failed: {application.error}"
                return report

            report.files_created = application.files_created
            report.files_modified = application.files_modified
            report.dependencies_added = application.dependencies_added
            report.tests_created = application.tests_created

            self.logger.info(
                "application_complete",
                files_created=len(application.files_created),
                files_modified=len(application.files_modified),
                dependencies_added=len(application.dependencies_added),
                tests_created=len(application.tests_created),
            )

            # Step 7: Test
            self.logger.info("step_7_test")

            test_results = await self._run_tests(
                test_files=application.tests_created,
                subagent_name=subagent_name
            )

            report.test_results = test_results

            if not test_results.success:
                self.logger.error("tests_failed", failures=test_results.failures)
                report.error = f"Tests failed: {test_results.summary}"
                return report

            # Step 8: Commit
            self.logger.info("step_8_commit")

            commit_result = await self._commit_changes(
                files_created=application.files_created,
                files_modified=application.files_modified,
                subagent_name=subagent_name,
                skill_name=report.best_skill.name if report.best_skill else "unknown",
                source_repo=report.best_skill.source_repo if report.best_skill else "unknown"
            )

            report.commit_hash = commit_result.commit_hash

            if not commit_result.success:
                self.logger.error("commit_failed", error=commit_result.error)
                report.error = f"Commit failed: {commit_result.error}"
                return report

            report.success = True
            report.dependencies_added = implementation.dependencies

            self.logger.info(
                "teaching_complete",
                subagent=subagent_name,
                repos_cloned=report.repos_cloned,
                skills_extracted=report.skills_extracted,
                best_skill=report.best_skill.name if report.best_skill else None,
            )

            return report

        except Exception as e:
            self.logger.error(
                "teaching_failed",
                subagent=subagent_name,
                error=str(e),
            )
            report.error = str(e)
            return report


# Old classes kept for backward compatibility (will be removed in future)


@dataclass
class IntegrationPoint:
    """Where to integrate the skill."""
    file_path: Path
    class_name: str | None
    function_name: str | None
    line_number: int | None
    reason: str  # Why integrate here


@dataclass
class AdaptedCode:
    """Adapted code for our architecture."""
    original_pattern: str  # Original GitHub pattern
    adapted_pattern: str  # Our adapted version
    adaptation_notes: str  # What changed and why
    dependencies: list[str]  # New dependencies needed
    imports: list[str]  # New imports needed


@dataclass
class TeachingResult:
    """Result of teaching a skill (old format)."""
    skill_name: str
    skill_type: str
    target_subagent: str
    taught_successfully: bool
    integration_points: list[IntegrationPoint]
    before_metrics: dict[str, float]
    after_metrics: dict[str, float]
    improvement: float  # % improvement
    code_changes: list[str]  # Changed files
    tests_added: list[str]  # Added test files
    teaching_notes: str
    metadata: dict[str, Any]

