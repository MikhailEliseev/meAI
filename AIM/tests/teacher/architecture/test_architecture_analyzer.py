"""
Tests for ArchitectureAnalyzer.

Tests:
- Orchestration of all 4 analyzers
- Complete architecture report generation
- Error handling when analyzers fail
- Integration with all components
"""

from pathlib import Path

import pytest

from AIM.src.aim.teacher.architecture.architecture_analyzer import (
    ArchitectureAnalyzer,
    ArchitectureReport,
)


@pytest.fixture
def analyzer():
    """Create ArchitectureAnalyzer instance."""
    return ArchitectureAnalyzer()


@pytest.fixture
def sample_repo(tmp_path):
    """Create sample repository with all features."""
    repo = tmp_path / "sample_repo"
    repo.mkdir()

    # Source code with patterns
    (repo / "strategy.py").write_text("""
from abc import ABC, abstractmethod

class PaymentStrategy(ABC):
    @abstractmethod
    def pay(self, amount: float) -> bool:
        pass

class CreditCardStrategy(PaymentStrategy):
    def pay(self, amount: float) -> bool:
        return True

class PayPalStrategy(PaymentStrategy):
    def pay(self, amount: float) -> bool:
        return True
""")

    # Module with dependencies
    (repo / "service.py").write_text("""
from strategy import PaymentStrategy

class PaymentService:
    def __init__(self, strategy: PaymentStrategy):
        self.strategy = strategy

    def process_payment(self, amount: float) -> bool:
        return self.strategy.pay(amount)
""")

    # Tests
    tests_dir = repo / "tests"
    tests_dir.mkdir()
    (tests_dir / "test_strategy.py").write_text("""
import pytest
from strategy import CreditCardStrategy

def test_credit_card_payment():
    strategy = CreditCardStrategy()
    assert strategy.pay(100.0) is True
""")

    (tests_dir / "conftest.py").write_text("""
import pytest

@pytest.fixture
def sample_strategy():
    from strategy import CreditCardStrategy
    return CreditCardStrategy()
""")

    return repo


class TestOrchestration:
    """Test orchestration of all analyzers."""

    @pytest.mark.asyncio
    async def test_analyze_complete_repo(self, analyzer, sample_repo):
        """Should orchestrate all 4 analyzers and generate complete report."""
        report = await analyzer.analyze(sample_repo)

        assert isinstance(report, ArchitectureReport)

        # Check all components present
        assert report.file_structure is not None
        assert report.component_relations is not None
        assert report.design_patterns is not None
        assert report.test_coverage is not None

    @pytest.mark.asyncio
    async def test_file_structure_in_report(self, analyzer, sample_repo):
        """Should include file structure analysis."""
        report = await analyzer.analyze(sample_repo)

        # Check file structure
        assert report.file_structure is not None
        # Check that at least one category has files
        total_files = (
            len(report.file_structure.entry_points)
            + len(report.file_structure.clients)
            + len(report.file_structure.models)
            + len(report.file_structure.tests)
            + len(report.file_structure.configs)
            + len(report.file_structure.utils)
        )
        assert total_files > 0

    @pytest.mark.asyncio
    async def test_component_relations_in_report(self, analyzer, sample_repo):
        """Should include component relations analysis."""
        report = await analyzer.analyze(sample_repo)

        # Check dependency graph
        assert len(report.component_relations.dependency_graph) > 0
        assert "service.py" in report.component_relations.dependency_graph

    @pytest.mark.asyncio
    async def test_design_patterns_in_report(self, analyzer, sample_repo):
        """Should include design patterns analysis."""
        report = await analyzer.analyze(sample_repo)

        # Check patterns detected
        assert "Strategy" in report.design_patterns.patterns

    @pytest.mark.asyncio
    async def test_test_coverage_in_report(self, analyzer, sample_repo):
        """Should include test coverage analysis."""
        report = await analyzer.analyze(sample_repo)

        # Check test coverage
        assert report.test_coverage.test_types.get("unit", 0) > 0
        assert report.test_coverage.has_fixtures is True


class TestReportGeneration:
    """Test report generation."""

    @pytest.mark.asyncio
    async def test_report_has_summary(self, analyzer, sample_repo):
        """Should generate summary statistics."""
        report = await analyzer.analyze(sample_repo)

        # Check summary fields
        assert hasattr(report, "summary")
        assert "total_files" in report.summary
        assert "total_modules" in report.summary
        assert "patterns_detected" in report.summary
        assert "coverage_estimate" in report.summary

    @pytest.mark.asyncio
    async def test_summary_statistics_correct(self, analyzer, sample_repo):
        """Should calculate summary statistics correctly."""
        report = await analyzer.analyze(sample_repo)

        # Verify statistics
        assert report.summary["total_files"] > 0
        assert report.summary["total_modules"] > 0
        assert report.summary["patterns_detected"] >= 1  # At least Strategy
        assert 0.0 <= report.summary["coverage_estimate"] <= 100.0


class TestErrorHandling:
    """Test error handling."""

    @pytest.mark.asyncio
    async def test_handle_empty_repo(self, analyzer, tmp_path):
        """Should handle empty repository gracefully."""
        empty_repo = tmp_path / "empty"
        empty_repo.mkdir()

        report = await analyzer.analyze(empty_repo)

        # Should return valid report with empty data
        assert isinstance(report, ArchitectureReport)
        assert report.summary["total_files"] == 0

    @pytest.mark.asyncio
    async def test_handle_repo_with_syntax_errors(self, analyzer, tmp_path):
        """Should handle syntax errors in files."""
        repo = tmp_path / "broken_repo"
        repo.mkdir()
        (repo / "broken.py").write_text("this is not valid python")

        # Should not crash
        report = await analyzer.analyze(repo)
        assert isinstance(report, ArchitectureReport)

    @pytest.mark.asyncio
    async def test_handle_missing_tests_directory(self, analyzer, tmp_path):
        """Should handle repos without tests directory."""
        repo = tmp_path / "no_tests"
        repo.mkdir()
        (repo / "code.py").write_text("def func(): pass")

        report = await analyzer.analyze(repo)

        # Should return valid report with zero coverage
        assert report.test_coverage.coverage_estimate == 0.0


class TestIntegration:
    """Test integration between components."""

    @pytest.mark.asyncio
    async def test_all_analyzers_run_successfully(self, analyzer, sample_repo):
        """Should run all 4 analyzers without errors."""
        report = await analyzer.analyze(sample_repo)

        # All components should have data
        assert report.summary["total_files"] > 0
        assert len(report.component_relations.dependency_graph) > 0
        assert len(report.design_patterns.patterns) > 0
        assert report.test_coverage.coverage_estimate >= 0.0

    @pytest.mark.asyncio
    async def test_report_consistency(self, analyzer, sample_repo):
        """Should generate consistent report across components."""
        report = await analyzer.analyze(sample_repo)

        # File count from file structure analyzer (only categorized files)
        file_count = report.summary["total_files"]

        # Module count from component relation analyzer (all .py files including tests)
        module_count = len(report.component_relations.dependency_graph)

        # Both should be > 0 for non-empty repo
        assert file_count > 0
        assert module_count > 0
