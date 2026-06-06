# AIM/src/aim/teacher/teacher_agent.py
"""Teacher Agent - Chief Learning Officer for continuous system learning."""

from pathlib import Path
import structlog

from src.aim.teacher.audit_report import AuditReportGenerator, AuditResult
from src.aim.teacher.code_analyzer import CodeAnalyzer
from src.aim.teacher.gap_detector import GapDetector, GapSeverity
from src.aim.teacher.github_finder import GitHubFinder
from src.aim.teacher.reference_repos import get_reference_repos
from src.aim.teacher.repo_cloner import RepoCloner
from src.aim.teacher.subagent_inventory import SubagentInventory
from src.aim.teacher.upgrade_applier import UpgradeApplier
from src.aim.teacher.skills.skill_selector import SkillSelector, Skill
from src.aim.teacher.skills.skill_comparator import SkillComparator, ComparisonResult
from src.aim.teacher.adoption.full_adopter import FullAdopter, AdoptionResult
from src.aim.teacher.adoption_report import AdoptionReportGenerator


class TeacherAgent:
    """Teacher Agent - audits and upgrades subagents using GitHub best practices."""

    def __init__(self):
        self.logger = structlog.get_logger()
        self.inventory = SubagentInventory()
        self.github_finder = GitHubFinder(min_stars=50)
        self.repo_cloner = RepoCloner()
        self.analyzer = CodeAnalyzer()
        self.gap_detector = GapDetector()
        self.report_generator = AuditReportGenerator()
        self.upgrade_applier = UpgradeApplier()

        # Phase 2.0 components
        self.skill_selector = SkillSelector()
        self.skill_comparator = SkillComparator()
        self.full_adopter = FullAdopter()
        self.adoption_report_generator = AdoptionReportGenerator()

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

        # Extract imports from subagent to find related files
        imports = self.analyzer.extract_imports(our_code)

        # Find related files based on imports
        subagent_dir = subagent_path.parent
        related_files = []

        # Check if subagent imports api_clients, utils, schemas
        if any("api_clients" in imp for imp in imports):
            api_clients_dir = subagent_dir / "api_clients"
            if api_clients_dir.exists():
                related_files.extend(api_clients_dir.glob("**/*.py"))

        if any("utils" in imp for imp in imports):
            utils_dir = subagent_dir / "utils"
            if utils_dir.exists():
                related_files.extend(utils_dir.glob("**/*.py"))

        if any("schemas" in imp for imp in imports):
            schemas_dir = subagent_dir / "schemas"
            if schemas_dir.exists():
                related_files.extend(schemas_dir.glob("**/*.py"))

        # Combine code from related files (only if imported)
        for related_file in related_files:
            try:
                our_code += "\n" + related_file.read_text()
            except Exception:
                continue

        # Extract topic from subagent name
        topic = subagent_path.stem.replace("_", " ")

        # Use reference repos with production patterns instead of searching by topic
        reference_urls = get_reference_repos("api_client")

        # Also search for topic-specific repos (but prioritize reference repos)
        topic_repos = self.github_finder.find_repos(topic, max_results=2)

        # Combine: reference repos first, then topic repos
        all_repo_urls = reference_urls + [r.url for r in topic_repos]
        all_repo_names = [url.split("/")[-1] for url in reference_urls] + [r.name for r in topic_repos]

        # Clone and analyze repos
        all_gaps = []
        for repo_url in all_repo_urls[:3]:  # Analyze top 3 repos
            clone_result = self.repo_cloner.clone(repo_url)
            if not clone_result.success:
                continue

            # Find Python files with patterns (prioritize key files)
            py_files = list(clone_result.path.glob("**/*.py"))
            if not py_files:
                continue

            # Prioritize files likely to have patterns
            priority_patterns = ["client", "api", "base", "service", "agent", "http"]
            key_files = [
                f for f in py_files
                if any(pattern in f.stem.lower() for pattern in priority_patterns)
            ]

            # Use key files if found, otherwise use all files
            files_to_analyze = key_files[:5] if key_files else py_files[:5]

            # Analyze multiple files and aggregate patterns
            for py_file in files_to_analyze:
                try:
                    github_code = py_file.read_text()

                    # Detect gaps
                    gaps = self.gap_detector.detect(our_code, github_code)
                    all_gaps.extend(gaps)
                except Exception:
                    continue  # Skip files that can't be read

        # Deduplicate gaps by pattern (same gap from multiple files)
        unique_gaps = {}
        for gap in all_gaps:
            if gap.pattern not in unique_gaps:
                unique_gaps[gap.pattern] = gap

        deduplicated_gaps = list(unique_gaps.values())

        # Calculate score
        score = self._calculate_score(deduplicated_gaps)

        # Create result
        result = AuditResult(
            subagent_name=subagent_path.stem,
            github_repos=all_repo_names[:3],  # Use combined repo names
            gaps=deduplicated_gaps,
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

    async def deep_audit_subagent(
        self, subagent_path: Path, subagent_name: str, domain: str
    ) -> list[Skill]:
        """
        Deep audit subagent by finding domain-specific solutions from GitHub.

        Phase 2.0 method - uses domain-specific research instead of generic patterns.

        Args:
            subagent_path: Path to subagent file
            subagent_name: Name of subagent (e.g., "ads", "seo")
            domain: Domain description (e.g., "advertising automation")

        Returns:
            List of extracted skills from domain-specific GitHub repos
        """
        self.logger.info(
            "deep_audit_start",
            subagent=subagent_name,
            domain=domain,
            path=str(subagent_path),
        )

        # Phase 1: Domain-specific research
        research_results = await self.skill_selector.research_domain_specific(
            subagent_name=subagent_name,
            domain=domain,
        )

        # Phase 2: Clone and extract skills from all found repos
        all_skills = []
        for query, repos in research_results.items():
            self.logger.info(
                "processing_query_repos",
                query=query,
                repos_count=len(repos),
            )

            for repo in repos:
                try:
                    # Clone repo
                    repo_name = repo.url.split("/")[-1]
                    clone_path = Path(f"/tmp/teacher_repos/{subagent_name}/{repo_name}")
                    clone_path.parent.mkdir(parents=True, exist_ok=True)

                    # Skip cloning if repo already exists
                    if not clone_path.exists():
                        await self.skill_selector.clone_repo(repo.url, clone_path)
                    else:
                        self.logger.info(
                            "repo_already_cloned",
                            repo=repo.url,
                            path=str(clone_path),
                        )

                    # Extract skills with subagent_type for domain-specific extraction
                    skills = await self.skill_selector.extract_skills(clone_path, subagent_name)

                    # Add metadata
                    for skill in skills:
                        skill.source_repo = repo.url

                    all_skills.extend(skills)

                    self.logger.info(
                        "repo_processed",
                        repo=repo.url,
                        skills_extracted=len(skills),
                    )

                except Exception as e:
                    self.logger.error(
                        "repo_processing_failed",
                        repo=repo.url,
                        error=str(e),
                    )
                    continue

        self.logger.info(
            "deep_audit_complete",
            subagent=subagent_name,
            total_skills=len(all_skills),
        )

        return all_skills

    async def compare_solutions(self, skills: list[Skill]) -> ComparisonResult:
        """
        Compare multiple skill implementations and rank them.

        Phase 2.0 method - multi-dimensional comparison.

        Args:
            skills: List of skills to compare

        Returns:
            ComparisonResult with ranked skills and best implementation
        """
        return await self.skill_comparator.compare(skills)

    async def adopt_solution(
        self, skill: Skill, target_dir: Path
    ) -> AdoptionResult:
        """
        Adopt best skill implementation into project.

        Phase 2.0 method - full adoption with code adaptation.

        Args:
            skill: Skill to adopt
            target_dir: Target directory for adoption

        Returns:
            AdoptionResult with adoption details
        """
        return await self.full_adopter.adopt(skill, target_dir)
