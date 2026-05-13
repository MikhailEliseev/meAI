"""
ArchitectureAnalyzer - Orchestrate all architecture analysis components.

Coordinates:
- FileStructureAnalyzer
- ComponentRelationAnalyzer
- DesignPatternDetector
- TestCoverageAnalyzer

Generates complete architecture report.
"""

from dataclasses import dataclass, field
from pathlib import Path

import structlog

from AIM.src.aim.teacher.architecture.component_relation_analyzer import (
    ComponentRelationAnalyzer,
    ComponentRelations,
)
from AIM.src.aim.teacher.architecture.design_pattern_detector import (
    DesignPatternDetector,
    DesignPatterns,
)
from AIM.src.aim.teacher.architecture.file_structure_analyzer import (
    FileStructure,
    FileStructureAnalyzer,
)
from AIM.src.aim.teacher.architecture.test_coverage_analyzer import (
    TestCoverage,
    TestCoverageAnalyzer,
)

logger = structlog.get_logger()


@dataclass
class ArchitectureReport:
    """Complete architecture analysis report."""

    file_structure: FileStructure
    component_relations: ComponentRelations
    design_patterns: DesignPatterns
    test_coverage: TestCoverage
    summary: dict[str, any] = field(default_factory=dict)


class ArchitectureAnalyzer:
    """
    Orchestrate all architecture analysis components.

    Responsibilities:
    - Coordinate 4 analyzers (FileStructure, ComponentRelation, DesignPattern, TestCoverage)
    - Generate complete architecture report
    - Calculate summary statistics
    - Handle errors gracefully
    """

    def __init__(self):
        self.logger = logger.bind(component="architecture_analyzer")

        # Initialize all analyzers
        self.file_structure_analyzer = FileStructureAnalyzer()
        self.component_relation_analyzer = ComponentRelationAnalyzer()
        self.design_pattern_detector = DesignPatternDetector()
        self.test_coverage_analyzer = TestCoverageAnalyzer()

    async def analyze(self, repo_path: Path) -> ArchitectureReport:
        """
        Analyze repository architecture.

        Runs all 4 analyzers and generates complete report.

        Args:
            repo_path: Path to repository root

        Returns:
            ArchitectureReport with all analysis results
        """
        self.logger.info("analyzing_architecture", repo_path=str(repo_path))

        # Run all analyzers
        file_structure = await self.file_structure_analyzer.analyze(repo_path)
        component_relations = await self.component_relation_analyzer.analyze(repo_path)
        design_patterns = await self.design_pattern_detector.analyze(repo_path)
        test_coverage = await self.test_coverage_analyzer.analyze(repo_path)

        # Generate summary statistics
        summary = self._generate_summary(
            file_structure, component_relations, design_patterns, test_coverage
        )

        self.logger.info(
            "architecture_analyzed",
            total_files=summary["total_files"],
            total_modules=summary["total_modules"],
            patterns_detected=summary["patterns_detected"],
            coverage_estimate=summary["coverage_estimate"],
        )

        return ArchitectureReport(
            file_structure=file_structure,
            component_relations=component_relations,
            design_patterns=design_patterns,
            test_coverage=test_coverage,
            summary=summary,
        )

    def _generate_summary(
        self,
        file_structure: FileStructure,
        component_relations: ComponentRelations,
        design_patterns: DesignPatterns,
        test_coverage: TestCoverage,
    ) -> dict[str, any]:
        """
        Generate summary statistics.

        Args:
            file_structure: File structure analysis
            component_relations: Component relations analysis
            design_patterns: Design patterns analysis
            test_coverage: Test coverage analysis

        Returns:
            Summary statistics dict
        """
        # Calculate total files from all categories
        total_files = (
            len(file_structure.entry_points)
            + len(file_structure.clients)
            + len(file_structure.models)
            + len(file_structure.tests)
            + len(file_structure.configs)
            + len(file_structure.utils)
        )

        return {
            "total_files": total_files,
            "total_modules": len(component_relations.dependency_graph),
            "patterns_detected": len(design_patterns.patterns),
            "architecture_style": design_patterns.architecture_style,
            "coupling_score": component_relations.coupling_score,
            "circular_deps_count": len(component_relations.circular_deps),
            "core_components_count": len(component_relations.core_components),
            "coverage_estimate": test_coverage.coverage_estimate,
            "has_fixtures": test_coverage.has_fixtures,
            "has_mocks": test_coverage.has_mocks,
            "test_scenarios_count": len(test_coverage.test_scenarios),
        }
