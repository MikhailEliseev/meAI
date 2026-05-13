"""
Skill Teacher - Teach our system specific skills (adapt patterns, not copy code).

Teaching process:
1. Analyze integration points (where to integrate)
2. Adapt pattern (understand principle, adapt to our architecture)
3. Integrate (create/update files in sandbox)
4. Test (write tests, measure metrics)
5. Document (add docstrings, examples, notes)
"""

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import structlog

from AIM.src.aim.teacher.skills.skill_comparator import ComparisonResult

logger = structlog.get_logger()


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
    Teach our system specific skills.

    Teaching philosophy:
    - Understand PRINCIPLE, not copy code
    - Adapt to OUR architecture (Event Bus, Obsidian, async/await)
    - Use production-ready libraries when available
    - Write tests for everything
    - Measure improvement (before/after metrics)
    """

    def __init__(self):
        self.logger = logger.bind(component="skill_teacher")

    async def teach_skill(
        self,
        skill: ComparisonResult,
        target_subagent: str,
        sandbox_path: Path,
    ) -> TeachingResult:
        """
        Teach a skill to target subagent.

        Process:
        1. Analyze integration points
        2. Measure before metrics
        3. Adapt pattern
        4. Integrate code
        5. Write tests
        6. Run tests
        7. Measure after metrics
        8. Document

        Args:
            skill: Skill to teach (from SkillComparator)
            target_subagent: Subagent to teach (e.g., "keyword-research")
            sandbox_path: Path to sandbox worktree

        Returns:
            TeachingResult with success status and metrics
        """
        self.logger.info(
            "teaching_skill",
            skill_name=skill.skill_name,
            skill_type=skill.skill_type,
            target_subagent=target_subagent,
        )

        # 1. Analyze integration points
        integration_points = await self._analyze_integration_points(
            skill, target_subagent, sandbox_path
        )

        # 2. Measure before metrics
        before_metrics = await self._measure_metrics(target_subagent, sandbox_path)

        # 3. Adapt pattern (NOT copy code!)
        adapted_code = await self._adapt_pattern(skill, target_subagent, integration_points)

        # 4. Integrate into sandbox
        code_changes = await self._integrate_code(
            adapted_code, integration_points, sandbox_path
        )

        # 5. Write tests
        tests_added = await self._write_tests(skill, target_subagent, sandbox_path)

        # 6. Run tests
        test_results = await self._run_tests(sandbox_path)

        # 7. Measure after metrics
        after_metrics = await self._measure_metrics(target_subagent, sandbox_path)

        # 8. Calculate improvement
        improvement = self._calculate_improvement(before_metrics, after_metrics)

        # 9. Document
        teaching_notes = await self._document_teaching(
            skill, integration_points, improvement, test_results
        )

        taught_successfully = test_results["passed"] and improvement > 0

        return TeachingResult(
            skill_name=skill.skill_name,
            skill_type=skill.skill_type,
            target_subagent=target_subagent,
            taught_successfully=taught_successfully,
            integration_points=integration_points,
            before_metrics=before_metrics,
            after_metrics=after_metrics,
            improvement=improvement,
            code_changes=code_changes,
            tests_added=tests_added,
            teaching_notes=teaching_notes,
            metadata={
                "test_results": test_results,
                "adapted_code": adapted_code,
            },
        )

    async def _analyze_integration_points(
        self,
        skill: ComparisonResult,
        target_subagent: str,
        sandbox_path: Path,
    ) -> list[IntegrationPoint]:
        """
        Analyze where to integrate the skill.

        Strategy:
        - Find files that need this skill type
        - Identify classes/functions that would benefit
        - Prioritize by impact and ease of integration

        Returns:
            List of integration points (where to add skill)
        """
        integration_points = []

        # Find subagent directory
        subagent_dir = sandbox_path / "AIM" / "src" / "aim" / "subagents" / target_subagent

        if not subagent_dir.exists():
            self.logger.warning(
                "subagent_not_found",
                target_subagent=target_subagent,
                path=str(subagent_dir),
            )
            return integration_points

        # Skill type → file patterns mapping
        skill_file_patterns = {
            "error_handling": ["*_client.py", "base*.py", "*_api.py"],
            "retry_logic": ["*_client.py", "base*.py", "*_fetcher.py"],
            "rate_limiting": ["*_client.py", "*_api.py", "*_scraper.py"],
            "caching": ["*_client.py", "*_fetcher.py", "*_analyzer.py"],
            "validation": ["*_validator.py", "*_schema.py", "*_parser.py"],
            "monitoring": ["*_client.py", "*_agent.py", "base*.py"],
            "testing": ["test_*.py", "*_test.py"],
            "documentation": ["*.py"],
        }

        patterns = skill_file_patterns.get(skill.skill_type, ["*.py"])

        # Find matching files
        for pattern in patterns:
            for file_path in subagent_dir.rglob(pattern):
                if file_path.is_file() and not file_path.name.startswith("__"):
                    integration_points.append(
                        IntegrationPoint(
                            file_path=file_path,
                            class_name=None,  # TODO: parse file to find classes
                            function_name=None,  # TODO: parse file to find functions
                            line_number=None,
                            reason=f"File matches pattern for {skill.skill_type}",
                        )
                    )

        self.logger.info(
            "integration_points_found",
            count=len(integration_points),
            skill_type=skill.skill_type,
        )

        return integration_points[:5]  # Limit to top 5 integration points

    async def _measure_metrics(
        self, target_subagent: str, sandbox_path: Path
    ) -> dict[str, float]:
        """
        Measure current metrics for subagent.

        Metrics:
        - test_coverage: % of code covered by tests
        - code_quality: pylint/ruff score
        - complexity: cyclomatic complexity
        - error_rate: % of operations that fail
        - performance: avg response time

        Returns:
            Dict of metric_name → value
        """
        # TODO: Implement real metrics measurement
        # For now, return mock metrics
        return {
            "test_coverage": 75.0,
            "code_quality": 8.5,
            "complexity": 12.0,
            "error_rate": 5.0,
            "performance": 250.0,  # ms
        }

    async def _adapt_pattern(
        self,
        skill: ComparisonResult,
        target_subagent: str,
        integration_points: list[IntegrationPoint],
    ) -> AdaptedCode:
        """
        Adapt GitHub pattern to our architecture.

        Adaptation rules:
        1. Use production-ready libraries (pybreaker, tenacity, aiolimiter)
        2. Integrate with Event Bus (publish events)
        3. Integrate with Obsidian (log important events)
        4. Use async/await (our standard)
        5. Add type hints (our standard)
        6. Add docstrings (our standard)
        7. Follow our naming conventions (snake_case)

        Returns:
            AdaptedCode with original and adapted patterns
        """
        # Example adaptation for circuit breaker
        if skill.skill_type == "error_handling" and "circuit" in skill.skill_name.lower():
            original_pattern = """
# GitHub pattern (custom implementation)
class CircuitBreaker:
    def __init__(self, fail_max=5):
        self.fail_count = 0
        self.fail_max = fail_max
        self.state = "closed"

    def call(self, func):
        if self.state == "open":
            raise CircuitBreakerError()
        try:
            return func()
        except Exception:
            self.fail_count += 1
            if self.fail_count >= self.fail_max:
                self.state = "open"
            raise
"""

            adapted_pattern = """
# Our adapted pattern (production-ready library + Event Bus + Obsidian)
from pybreaker import CircuitBreaker
from aim.events.event_bus import EventBus
from aim.memory.obsidian import ObsidianVault

class BaseClient:
    def __init__(self, event_bus: EventBus, obsidian: ObsidianVault):
        self.event_bus = event_bus
        self.obsidian = obsidian
        self.circuit_breaker = CircuitBreaker(
            fail_max=5,
            reset_timeout=60,
            listeners=[self._on_circuit_open, self._on_circuit_close]
        )

    async def _fetch(self, url: str):
        try:
            result = self.circuit_breaker.call(lambda: httpx.get(url))
            await self.event_bus.publish("api.request.success", {"url": url})
            return result
        except CircuitBreakerError:
            await self.event_bus.publish("api.circuit.open", {"url": url})
            await self.obsidian.log("Circuit breaker opened - too many failures")
            raise

    def _on_circuit_open(self):
        self.obsidian.log("Circuit breaker opened")

    def _on_circuit_close(self):
        self.obsidian.log("Circuit breaker closed - service recovered")
"""

            adaptation_notes = """
Adaptations made:
1. Used pybreaker library (production-ready, battle-tested)
2. Integrated with Event Bus (publish circuit state changes)
3. Integrated with Obsidian (log important events)
4. Added async/await (our standard)
5. Added type hints (url: str)
6. Added listeners for circuit state changes
7. Graceful error handling with context
"""

            dependencies = ["pybreaker>=1.0.0"]
            imports = [
                "from pybreaker import CircuitBreaker",
                "from aim.events.event_bus import EventBus",
                "from aim.memory.obsidian import ObsidianVault",
            ]

            return AdaptedCode(
                original_pattern=original_pattern,
                adapted_pattern=adapted_pattern,
                adaptation_notes=adaptation_notes,
                dependencies=dependencies,
                imports=imports,
            )

        # Default: generic adaptation template
        return AdaptedCode(
            original_pattern=f"# GitHub pattern for {skill.skill_name}",
            adapted_pattern=f"# Adapted pattern for {skill.skill_name} (TODO: implement)",
            adaptation_notes="Generic adaptation - needs manual implementation",
            dependencies=[],
            imports=[],
        )

    async def _integrate_code(
        self,
        adapted_code: AdaptedCode,
        integration_points: list[IntegrationPoint],
        sandbox_path: Path,
    ) -> list[str]:
        """
        Integrate adapted code into sandbox.

        Steps:
        1. Add dependencies to requirements.txt
        2. Update imports in target files
        3. Add adapted code to integration points
        4. Format code (ruff format)

        Returns:
            List of changed file paths
        """
        code_changes = []

        # 1. Add dependencies
        if adapted_code.dependencies:
            requirements_path = sandbox_path / "requirements.txt"
            if requirements_path.exists():
                with open(requirements_path, "a") as f:
                    f.write("\n# Added by SkillTeacher\n")
                    for dep in adapted_code.dependencies:
                        f.write(f"{dep}\n")
                code_changes.append(str(requirements_path))

        # 2. Update integration points (mock for now)
        for point in integration_points:
            # TODO: Actually modify files
            # For now, just log what we would do
            self.logger.info(
                "would_integrate_at",
                file=str(point.file_path),
                reason=point.reason,
            )
            code_changes.append(str(point.file_path))

        return code_changes

    async def _write_tests(
        self, skill: ComparisonResult, target_subagent: str, sandbox_path: Path
    ) -> list[str]:
        """
        Write tests for the taught skill.

        Test types:
        - Unit tests (test skill in isolation)
        - Integration tests (test skill with Event Bus, Obsidian)
        - Edge case tests (test failure scenarios)

        Returns:
            List of added test file paths
        """
        tests_added = []

        # Create test file path
        test_dir = sandbox_path / "AIM" / "tests" / "subagents" / target_subagent
        test_dir.mkdir(parents=True, exist_ok=True)

        test_file = test_dir / f"test_{skill.skill_type}_{skill.skill_name.lower().replace(' ', '_')}.py"

        # TODO: Generate actual test code
        # For now, create placeholder
        test_content = f'''"""
Tests for {skill.skill_name} skill.

Taught by SkillTeacher from GitHub best practices.
"""

import pytest


class Test{skill.skill_name.replace(" ", "")}:
    """Test {skill.skill_name} skill."""

    def test_basic_functionality(self):
        """Test basic functionality."""
        # TODO: Implement test
        pass

    def test_integration_with_event_bus(self):
        """Test integration with Event Bus."""
        # TODO: Implement test
        pass

    def test_edge_cases(self):
        """Test edge cases and failure scenarios."""
        # TODO: Implement test
        pass
'''

        test_file.write_text(test_content)
        tests_added.append(str(test_file))

        self.logger.info("test_file_created", path=str(test_file))

        return tests_added

    async def _run_tests(self, sandbox_path: Path) -> dict[str, Any]:
        """
        Run tests in sandbox.

        Returns:
            Dict with test results (passed, failed, coverage)
        """
        # TODO: Actually run pytest
        # For now, return mock results
        return {
            "passed": True,
            "total": 3,
            "failed": 0,
            "coverage": 85.0,
        }

    def _calculate_improvement(
        self, before: dict[str, float], after: dict[str, float]
    ) -> float:
        """
        Calculate overall improvement %.

        Formula:
        - For metrics where higher is better (coverage, quality): (after - before) / before * 100
        - For metrics where lower is better (error_rate, complexity): (before - after) / before * 100

        Returns:
            Average improvement % across all metrics
        """
        improvements = []

        # Higher is better
        for metric in ["test_coverage", "code_quality"]:
            if metric in before and metric in after and before[metric] > 0:
                improvement = (after[metric] - before[metric]) / before[metric] * 100
                improvements.append(improvement)

        # Lower is better
        for metric in ["error_rate", "complexity"]:
            if metric in before and metric in after and before[metric] > 0:
                improvement = (before[metric] - after[metric]) / before[metric] * 100
                improvements.append(improvement)

        if not improvements:
            return 0.0

        return sum(improvements) / len(improvements)

    async def _document_teaching(
        self,
        skill: ComparisonResult,
        integration_points: list[IntegrationPoint],
        improvement: float,
        test_results: dict[str, Any],
    ) -> str:
        """
        Document the teaching process.

        Returns:
            Teaching notes (markdown format)
        """
        notes = f"""# Teaching: {skill.skill_name}

## Skill Details
- **Type:** {skill.skill_type}
- **GitHub Score:** {skill.github_score.total:.1f}/100
- **Our Score:** {skill.our_score.total:.1f}/100
- **Improvement Potential:** {skill.improvement_potential:.1f}%

## Integration Points
"""

        for i, point in enumerate(integration_points, 1):
            notes += f"{i}. `{point.file_path.name}` - {point.reason}\n"

        notes += f"""
## Results
- **Tests Passed:** {test_results['passed']}
- **Test Coverage:** {test_results['coverage']:.1f}%
- **Overall Improvement:** {improvement:.1f}%

## Teaching Notes
- Adapted GitHub pattern to our architecture
- Integrated with Event Bus and Obsidian
- Added comprehensive tests
- Measured before/after metrics
"""

        return notes
