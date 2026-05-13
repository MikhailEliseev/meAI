"""
TestCoverageAnalyzer - Analyze test coverage and quality.

Analyzes:
- Test types (unit, integration, e2e)
- Coverage estimation (test count vs function count)
- Fixture usage (pytest fixtures)
- Mock usage (unittest.mock)
- Test scenarios (extracted from test names)
"""

import ast
from dataclasses import dataclass, field
from pathlib import Path

import structlog

logger = structlog.get_logger()


@dataclass
class TestCoverage:
    """Test coverage analysis result."""

    test_types: dict[str, int] = field(default_factory=dict)  # {"unit": 5, "integration": 2}
    coverage_estimate: float = 0.0  # 0-100 (estimated coverage %)
    has_fixtures: bool = False
    has_mocks: bool = False
    test_scenarios: list[str] = field(default_factory=list)  # ["add", "subtract"]


class TestCoverageAnalyzer:
    """
    Analyze test coverage and quality.

    Responsibilities:
    - Identify test types (unit, integration, e2e)
    - Estimate coverage based on test count vs function count
    - Detect fixture usage (pytest fixtures)
    - Detect mock usage (unittest.mock)
    - Extract test scenarios from test names
    """

    def __init__(self):
        self.logger = logger.bind(component="test_coverage_analyzer")

    async def analyze(self, repo_path: Path) -> TestCoverage:
        """
        Analyze test coverage.

        Args:
            repo_path: Path to repository root

        Returns:
            TestCoverage with test types, coverage estimate, and quality metrics
        """
        self.logger.info("analyzing_test_coverage", repo_path=str(repo_path))

        # Count test functions by type
        test_types = await self._identify_test_types(repo_path)

        # Estimate coverage
        coverage_estimate = await self._estimate_coverage(repo_path, test_types)

        # Detect fixtures
        has_fixtures = await self._detect_fixtures(repo_path)

        # Detect mocks
        has_mocks = await self._detect_mocks(repo_path)

        # Extract test scenarios
        test_scenarios = await self._extract_test_scenarios(repo_path)

        self.logger.info(
            "test_coverage_analyzed",
            test_types=test_types,
            coverage_estimate=coverage_estimate,
            has_fixtures=has_fixtures,
            has_mocks=has_mocks,
            scenarios_count=len(test_scenarios),
        )

        return TestCoverage(
            test_types=test_types,
            coverage_estimate=coverage_estimate,
            has_fixtures=has_fixtures,
            has_mocks=has_mocks,
            test_scenarios=test_scenarios,
        )

    async def _identify_test_types(self, repo_path: Path) -> dict[str, int]:
        """
        Identify test types (unit, integration, e2e).

        Unit tests: test single functions/classes
        Integration tests: test multiple components together
        E2E tests: test full user workflows

        Args:
            repo_path: Repository root path

        Returns:
            Dict mapping test type to count
        """
        test_types = {}

        # Find tests directory
        tests_dir = repo_path / "tests"
        if not tests_dir.exists():
            return test_types

        # Scan test files
        for test_file in tests_dir.rglob("test_*.py"):
            if self._should_skip_file(test_file):
                continue

            try:
                content = test_file.read_text()
                tree = ast.parse(content)

                # Count test functions
                for node in ast.walk(tree):
                    if isinstance(node, ast.FunctionDef) and node.name.startswith("test_"):
                        # Classify test type based on file name and function name
                        test_type = self._classify_test_type(test_file, node)
                        test_types[test_type] = test_types.get(test_type, 0) + 1

            except (SyntaxError, UnicodeDecodeError):
                continue

        return test_types

    def _classify_test_type(self, test_file: Path, test_func: ast.FunctionDef) -> str:
        """
        Classify test as unit, integration, or e2e.

        Heuristics:
        - File name contains "integration" → integration
        - File name contains "e2e" or "end_to_end" → e2e
        - Function name contains "integration" → integration
        - Default → unit

        Args:
            test_file: Path to test file
            test_func: Test function AST node

        Returns:
            Test type: "unit", "integration", or "e2e"
        """
        file_name = test_file.name.lower()
        func_name = test_func.name.lower()

        # Check file name
        if "integration" in file_name:
            return "integration"
        if "e2e" in file_name or "end_to_end" in file_name:
            return "e2e"

        # Check function name
        if "integration" in func_name:
            return "integration"
        if "e2e" in func_name or "end_to_end" in func_name:
            return "e2e"

        # Default to unit
        return "unit"

    async def _estimate_coverage(
        self, repo_path: Path, test_types: dict[str, int]
    ) -> float:
        """
        Estimate test coverage.

        Formula: (test_count / function_count) * 100, capped at 100%

        Args:
            repo_path: Repository root path
            test_types: Test counts by type

        Returns:
            Coverage estimate (0-100)
        """
        # Count total tests
        total_tests = sum(test_types.values())
        if total_tests == 0:
            return 0.0

        # Count total functions in source code
        total_functions = await self._count_functions(repo_path)
        if total_functions == 0:
            return 0.0

        # Calculate coverage estimate
        coverage = (total_tests / total_functions) * 100.0

        # Cap at 100%
        return min(coverage, 100.0)

    async def _count_functions(self, repo_path: Path) -> int:
        """
        Count total functions in source code.

        Args:
            repo_path: Repository root path

        Returns:
            Total function count
        """
        function_count = 0

        # Scan all Python files (excluding tests)
        for file_path in repo_path.rglob("*.py"):
            if self._should_skip_file(file_path):
                continue

            # Skip test files
            if "test" in file_path.parts or file_path.name.startswith("test_"):
                continue

            try:
                content = file_path.read_text()
                tree = ast.parse(content)

                # Count function definitions
                for node in ast.walk(tree):
                    if isinstance(node, ast.FunctionDef):
                        function_count += 1

            except (SyntaxError, UnicodeDecodeError):
                continue

        return function_count

    async def _detect_fixtures(self, repo_path: Path) -> bool:
        """
        Detect pytest fixtures.

        Looks for @pytest.fixture decorators in test files.

        Args:
            repo_path: Repository root path

        Returns:
            True if fixtures found, False otherwise
        """
        tests_dir = repo_path / "tests"
        if not tests_dir.exists():
            return False

        # Scan test files and conftest.py
        for test_file in tests_dir.rglob("*.py"):
            if self._should_skip_file(test_file):
                continue

            try:
                content = test_file.read_text()
                tree = ast.parse(content)

                # Look for @pytest.fixture decorator
                for node in ast.walk(tree):
                    if isinstance(node, ast.FunctionDef):
                        for decorator in node.decorator_list:
                            # Check for @pytest.fixture
                            if isinstance(decorator, ast.Attribute):
                                if (
                                    isinstance(decorator.value, ast.Name)
                                    and decorator.value.id == "pytest"
                                    and decorator.attr == "fixture"
                                ):
                                    return True
                            # Check for @fixture (from pytest import fixture)
                            elif isinstance(decorator, ast.Name) and decorator.id == "fixture":
                                return True

            except (SyntaxError, UnicodeDecodeError):
                continue

        return False

    async def _detect_mocks(self, repo_path: Path) -> bool:
        """
        Detect unittest.mock usage.

        Looks for imports from unittest.mock.

        Args:
            repo_path: Repository root path

        Returns:
            True if mocks found, False otherwise
        """
        tests_dir = repo_path / "tests"
        if not tests_dir.exists():
            return False

        # Scan test files
        for test_file in tests_dir.rglob("test_*.py"):
            if self._should_skip_file(test_file):
                continue

            try:
                content = test_file.read_text()
                tree = ast.parse(content)

                # Look for unittest.mock imports
                for node in ast.walk(tree):
                    if isinstance(node, ast.ImportFrom):
                        if node.module and "unittest.mock" in node.module:
                            return True
                        if node.module == "mock":  # from mock import ...
                            return True

            except (SyntaxError, UnicodeDecodeError):
                continue

        return False

    async def _extract_test_scenarios(self, repo_path: Path) -> list[str]:
        """
        Extract test scenarios from test function names.

        Converts test_function_name → "function name" scenario.

        Args:
            repo_path: Repository root path

        Returns:
            List of test scenarios
        """
        scenarios = []

        tests_dir = repo_path / "tests"
        if not tests_dir.exists():
            return scenarios

        # Scan test files
        for test_file in tests_dir.rglob("test_*.py"):
            if self._should_skip_file(test_file):
                continue

            try:
                content = test_file.read_text()
                tree = ast.parse(content)

                # Extract test function names
                for node in ast.walk(tree):
                    if isinstance(node, ast.FunctionDef) and node.name.startswith("test_"):
                        # Convert test_function_name → "function name"
                        scenario = node.name[5:]  # Remove "test_" prefix
                        scenario = scenario.replace("_", " ")  # Replace underscores with spaces
                        scenarios.append(scenario)

            except (SyntaxError, UnicodeDecodeError):
                continue

        return scenarios

    def _should_skip_file(self, file_path: Path) -> bool:
        """Check if file should be skipped."""
        if any(part.startswith(".") for part in file_path.parts):
            return True
        if "__pycache__" in file_path.parts:
            return True
        return False
