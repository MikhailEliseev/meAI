"""
Tests for TestCoverageAnalyzer.

Tests:
- Test type identification (unit, integration, e2e)
- Coverage estimation
- Fixture and mock detection
- Test scenario extraction
"""

from pathlib import Path

import pytest

from src.aim.teacher.architecture.test_coverage_analyzer import (
    TestCoverage,
    TestCoverageAnalyzer,
)


@pytest.fixture
def analyzer():
    """Create TestCoverageAnalyzer instance."""
    return TestCoverageAnalyzer()


@pytest.fixture
def unit_test_repo(tmp_path):
    """Create repo with unit tests."""
    repo = tmp_path / "unit_test_repo"
    repo.mkdir()

    # Source code
    (repo / "calculator.py").write_text("""
def add(a, b):
    return a + b

def subtract(a, b):
    return a - b
""")

    # Unit tests
    tests_dir = repo / "tests"
    tests_dir.mkdir()
    (tests_dir / "test_calculator.py").write_text("""
import pytest
from calculator import add, subtract

def test_add():
    assert add(2, 3) == 5

def test_subtract():
    assert subtract(5, 3) == 2
""")

    return repo


@pytest.fixture
def integration_test_repo(tmp_path):
    """Create repo with integration tests."""
    repo = tmp_path / "integration_test_repo"
    repo.mkdir()

    # Source code
    (repo / "api.py").write_text("# API code")
    (repo / "database.py").write_text("# Database code")

    # Integration tests
    tests_dir = repo / "tests"
    tests_dir.mkdir()
    (tests_dir / "test_integration_api_database.py").write_text("""
def test_api_with_database():
    # Integration test
    pass
""")

    return repo


@pytest.fixture
def fixture_repo(tmp_path):
    """Create repo with fixtures."""
    repo = tmp_path / "fixture_repo"
    repo.mkdir()

    tests_dir = repo / "tests"
    tests_dir.mkdir()
    (tests_dir / "conftest.py").write_text("""
import pytest

@pytest.fixture
def sample_data():
    return {"key": "value"}
""")

    (tests_dir / "test_with_fixture.py").write_text("""
def test_with_fixture(sample_data):
    assert sample_data["key"] == "value"
""")

    return repo


@pytest.fixture
def mock_repo(tmp_path):
    """Create repo with mocks."""
    repo = tmp_path / "mock_repo"
    repo.mkdir()

    tests_dir = repo / "tests"
    tests_dir.mkdir()
    (tests_dir / "test_with_mock.py").write_text("""
from unittest.mock import Mock, patch

def test_with_mock():
    mock_obj = Mock()
    mock_obj.method.return_value = 42
    assert mock_obj.method() == 42
""")

    return repo


@pytest.fixture
def comprehensive_test_repo(tmp_path):
    """Create repo with comprehensive test coverage."""
    repo = tmp_path / "comprehensive_repo"
    repo.mkdir()

    # Source code (5 functions)
    (repo / "module.py").write_text("""
def func1():
    pass

def func2():
    pass

def func3():
    pass

def func4():
    pass

def func5():
    pass
""")

    # Tests (4 test functions covering 4/5 functions)
    tests_dir = repo / "tests"
    tests_dir.mkdir()
    (tests_dir / "test_module.py").write_text("""
def test_func1():
    pass

def test_func2():
    pass

def test_func3():
    pass

def test_func4():
    pass
""")

    return repo


class TestTestTypeIdentification:
    """Test test type identification."""

    @pytest.mark.asyncio
    async def test_identify_unit_tests(self, analyzer, unit_test_repo):
        """Should identify unit tests."""
        coverage = await analyzer.analyze(unit_test_repo)

        assert coverage.test_types.get("unit", 0) > 0

    @pytest.mark.asyncio
    async def test_identify_integration_tests(self, analyzer, integration_test_repo):
        """Should identify integration tests."""
        coverage = await analyzer.analyze(integration_test_repo)

        assert coverage.test_types.get("integration", 0) > 0

    @pytest.mark.asyncio
    async def test_count_test_functions(self, analyzer, unit_test_repo):
        """Should count test functions correctly."""
        coverage = await analyzer.analyze(unit_test_repo)

        # 2 unit tests (test_add, test_subtract)
        assert coverage.test_types.get("unit", 0) == 2


class TestCoverageEstimation:
    """Test coverage estimation."""

    @pytest.mark.asyncio
    async def test_estimate_coverage_from_test_count(self, analyzer, comprehensive_test_repo):
        """Should estimate coverage based on test count vs function count."""
        coverage = await analyzer.analyze(comprehensive_test_repo)

        # 4 tests for 5 functions = 80% coverage estimate
        assert 70.0 <= coverage.coverage_estimate <= 90.0

    @pytest.mark.asyncio
    async def test_zero_coverage_for_no_tests(self, analyzer, tmp_path):
        """Should return 0% coverage for repo with no tests."""
        repo = tmp_path / "no_tests"
        repo.mkdir()
        (repo / "code.py").write_text("def func(): pass")

        coverage = await analyzer.analyze(repo)

        assert coverage.coverage_estimate == 0.0

    @pytest.mark.asyncio
    async def test_high_coverage_estimate(self, analyzer, tmp_path):
        """Should estimate high coverage when tests >= functions."""
        repo = tmp_path / "high_coverage"
        repo.mkdir()

        # 2 functions
        (repo / "module.py").write_text("""
def func1():
    pass

def func2():
    pass
""")

        # 3 tests (more than functions)
        tests_dir = repo / "tests"
        tests_dir.mkdir()
        (tests_dir / "test_module.py").write_text("""
def test_func1():
    pass

def test_func2():
    pass

def test_edge_case():
    pass
""")

        coverage = await analyzer.analyze(repo)

        # 3 tests for 2 functions = 100% coverage estimate (capped)
        assert coverage.coverage_estimate == 100.0


class TestFixtureDetection:
    """Test fixture detection."""

    @pytest.mark.asyncio
    async def test_detect_fixtures(self, analyzer, fixture_repo):
        """Should detect pytest fixtures."""
        coverage = await analyzer.analyze(fixture_repo)

        assert coverage.has_fixtures is True

    @pytest.mark.asyncio
    async def test_no_fixtures_when_absent(self, analyzer, unit_test_repo):
        """Should return False when no fixtures present."""
        coverage = await analyzer.analyze(unit_test_repo)

        assert coverage.has_fixtures is False


class TestMockDetection:
    """Test mock detection."""

    @pytest.mark.asyncio
    async def test_detect_mocks(self, analyzer, mock_repo):
        """Should detect unittest.mock usage."""
        coverage = await analyzer.analyze(mock_repo)

        assert coverage.has_mocks is True

    @pytest.mark.asyncio
    async def test_no_mocks_when_absent(self, analyzer, unit_test_repo):
        """Should return False when no mocks present."""
        coverage = await analyzer.analyze(unit_test_repo)

        assert coverage.has_mocks is False


class TestScenarioExtraction:
    """Test test scenario extraction."""

    @pytest.mark.asyncio
    async def test_extract_scenarios_from_test_names(self, analyzer, unit_test_repo):
        """Should extract test scenarios from test function names."""
        coverage = await analyzer.analyze(unit_test_repo)

        assert "add" in coverage.test_scenarios
        assert "subtract" in coverage.test_scenarios

    @pytest.mark.asyncio
    async def test_extract_descriptive_scenarios(self, analyzer, tmp_path):
        """Should extract descriptive scenarios."""
        repo = tmp_path / "descriptive_tests"
        repo.mkdir()

        tests_dir = repo / "tests"
        tests_dir.mkdir()
        (tests_dir / "test_user.py").write_text("""
def test_user_can_login():
    pass

def test_user_cannot_login_with_invalid_password():
    pass
""")

        coverage = await analyzer.analyze(repo)

        assert "user can login" in coverage.test_scenarios
        assert "user cannot login with invalid password" in coverage.test_scenarios


class TestEdgeCases:
    """Test edge cases."""

    @pytest.mark.asyncio
    async def test_handle_empty_repo(self, analyzer, tmp_path):
        """Should handle empty repository."""
        empty_repo = tmp_path / "empty"
        empty_repo.mkdir()

        coverage = await analyzer.analyze(empty_repo)

        assert coverage.coverage_estimate == 0.0
        assert len(coverage.test_types) == 0
        assert coverage.has_fixtures is False
        assert coverage.has_mocks is False

    @pytest.mark.asyncio
    async def test_handle_repo_without_tests_directory(self, analyzer, tmp_path):
        """Should handle repo without tests directory."""
        repo = tmp_path / "no_tests_dir"
        repo.mkdir()
        (repo / "code.py").write_text("def func(): pass")

        coverage = await analyzer.analyze(repo)

        assert coverage.coverage_estimate == 0.0

    @pytest.mark.asyncio
    async def test_handle_syntax_errors_in_tests(self, analyzer, tmp_path):
        """Should handle syntax errors in test files."""
        repo = tmp_path / "broken_tests"
        repo.mkdir()

        tests_dir = repo / "tests"
        tests_dir.mkdir()
        (tests_dir / "test_broken.py").write_text("this is not valid python")

        # Should not crash
        coverage = await analyzer.analyze(repo)
        assert isinstance(coverage, TestCoverage)
