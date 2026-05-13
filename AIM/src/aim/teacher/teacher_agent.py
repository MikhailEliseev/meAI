# AIM/src/aim/teacher/teacher_agent.py
"""Teacher Agent - Chief Learning Officer for continuous system learning."""

from pathlib import Path

from AIM.src.aim.teacher.audit_report import AuditReportGenerator, AuditResult
from AIM.src.aim.teacher.code_analyzer import CodeAnalyzer
from AIM.src.aim.teacher.gap_detector import GapDetector, GapSeverity
from AIM.src.aim.teacher.github_finder import GitHubFinder
from AIM.src.aim.teacher.repo_cloner import RepoCloner
from AIM.src.aim.teacher.subagent_inventory import SubagentInventory
from AIM.src.aim.teacher.upgrade_applier import UpgradeApplier


class TeacherAgent:
    """Teacher Agent - audits and upgrades subagents using GitHub best practices."""

    def __init__(self):
        self.inventory = SubagentInventory()
        self.github_finder = GitHubFinder(min_stars=50)
        self.repo_cloner = RepoCloner()
        self.analyzer = CodeAnalyzer()
        self.gap_detector = GapDetector()
        self.report_generator = AuditReportGenerator()
        self.upgrade_applier = UpgradeApplier()

    def audit_subagent(self, subagent_path: Path) -> AuditResult:
        """
        Audit a single subagent.

        Args:
            subagent_path: Path to subagent file

        Returns:
            AuditResult with gaps and score
        """
        # Read subagent code
        our_code = subagent_path.read_text()

        # Extract topic from subagent name
        topic = subagent_path.stem.replace("_", " ")

        # Find GitHub repos
        repos = self.github_finder.find_repos(topic, max_results=3)

        # Clone and analyze repos
        all_gaps = []
        for repo in repos[:1]:  # Start with top repo
            clone_result = self.repo_cloner.clone(repo.url)
            if not clone_result.success:
                continue

            # Find Python files in repo
            py_files = list(clone_result.path.glob("**/*.py"))
            if not py_files:
                continue

            # Analyze first main file
            github_code = py_files[0].read_text()

            # Detect gaps
            gaps = self.gap_detector.detect(our_code, github_code)
            all_gaps.extend(gaps)

        # Calculate score
        score = self._calculate_score(all_gaps)

        # Create result
        result = AuditResult(
            subagent_name=subagent_path.stem,
            github_repos=[r.name for r in repos],
            gaps=all_gaps,
            score=score,
        )

        return result

    def audit_all(self) -> list[AuditResult]:
        """
        Audit all subagents.

        Returns:
            List of AuditResult for each subagent
        """
        subagents = self.inventory.scan()
        results = []

        for subagent in subagents:
            try:
                result = self.audit_subagent(Path(subagent.path))
                results.append(result)
            except Exception as e:
                print(f"Error auditing {subagent.name}: {e}")

        return results

    def upgrade_subagent(self, subagent_path: Path, audit_result: AuditResult) -> bool:
        """
        Upgrade a subagent based on audit result.

        Args:
            subagent_path: Path to subagent file
            audit_result: Audit result with gaps

        Returns:
            True if upgrade successful
        """
        if not audit_result.gaps:
            return True  # Nothing to upgrade

        # Get GitHub code from first repo
        if not audit_result.github_repos:
            return False

        # Clone repo
        repo_name = audit_result.github_repos[0]
        # Simplified: assume we already have the code
        github_code = ""  # Would fetch from cloned repo

        # Apply upgrade
        result = self.upgrade_applier.apply(
            subagent_path,
            audit_result.gaps,
            github_code,
        )

        return result.success

    def _calculate_score(self, gaps: list) -> float:
        """Calculate score based on gaps."""
        score = 100.0

        for gap in gaps:
            if gap.severity == GapSeverity.CRITICAL:
                score -= 30
            elif gap.severity == GapSeverity.HIGH:
                score -= 20
            elif gap.severity == GapSeverity.MEDIUM:
                score -= 10

        return max(0.0, score)
