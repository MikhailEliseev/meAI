"""
Tests for ComponentRelationAnalyzer.

Tests:
- Dependency graph building
- Coupling score calculation
- Circular dependency detection
- Core component identification
"""

from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.aim.teacher.architecture.component_relation_analyzer import (
    ComponentRelationAnalyzer,
    ComponentRelations,
)


@pytest.fixture
def analyzer():
    """Create ComponentRelationAnalyzer instance."""
    return ComponentRelationAnalyzer()


@pytest.fixture
def simple_repo(tmp_path):
    """Create simple repository with clear dependencies."""
    repo = tmp_path / "simple_repo"
    repo.mkdir()

    # Module A (no dependencies)
    (repo / "module_a.py").write_text("""
def function_a():
    return "A"
""")

    # Module B (depends on A)
    (repo / "module_b.py").write_text("""
from module_a import function_a

def function_b():
    return function_a() + "B"
""")

    # Module C (depends on B)
    (repo / "module_c.py").write_text("""
from module_b import function_b

def function_c():
    return function_b() + "C"
""")

    return repo


@pytest.fixture
def circular_repo(tmp_path):
    """Create repository with circular dependencies."""
    repo = tmp_path / "circular_repo"
    repo.mkdir()

    # Module A depends on B
    (repo / "module_a.py").write_text("""
from module_b import function_b

def function_a():
    return function_b()
""")

    # Module B depends on A (circular!)
    (repo / "module_b.py").write_text("""
from module_a import function_a

def function_b():
    return function_a()
""")

    return repo


@pytest.fixture
def complex_repo(tmp_path):
    """Create complex repository with multiple dependencies."""
    repo = tmp_path / "complex_repo"
    repo.mkdir()

    # Core module (many dependents)
    (repo / "core.py").write_text("""
def core_function():
    return "core"
""")

    # Client A depends on core
    (repo / "client_a.py").write_text("""
from core import core_function

def client_a():
    return core_function()
""")

    # Client B depends on core
    (repo / "client_b.py").write_text("""
from core import core_function

def client_b():
    return core_function()
""")

    # Client C depends on core
    (repo / "client_c.py").write_text("""
from core import core_function

def client_c():
    return core_function()
""")

    # Peripheral module (no dependents)
    (repo / "peripheral.py").write_text("""
def peripheral_function():
    return "peripheral"
""")

    return repo


class TestDependencyGraphBuilding:
    """Test dependency graph building."""

    @pytest.mark.asyncio
    async def test_build_simple_dependency_graph(self, analyzer, simple_repo):
        """Should build dependency graph for simple repo."""
        relations = await analyzer.analyze(simple_repo)

        assert isinstance(relations, ComponentRelations)
        assert "module_a.py" in relations.dependency_graph
        assert "module_b.py" in relations.dependency_graph
        assert "module_c.py" in relations.dependency_graph

    @pytest.mark.asyncio
    async def test_identify_dependencies(self, analyzer, simple_repo):
        """Should identify module dependencies correctly."""
        relations = await analyzer.analyze(simple_repo)

        # Module B depends on A
        assert "module_a" in relations.dependency_graph["module_b.py"]

        # Module C depends on B
        assert "module_b" in relations.dependency_graph["module_c.py"]

    @pytest.mark.asyncio
    async def test_handle_no_dependencies(self, analyzer, simple_repo):
        """Should handle modules with no dependencies."""
        relations = await analyzer.analyze(simple_repo)

        # Module A has no dependencies
        assert len(relations.dependency_graph["module_a.py"]) == 0

    @pytest.mark.asyncio
    async def test_handle_empty_repo(self, analyzer, tmp_path):
        """Should handle empty repository."""
        empty_repo = tmp_path / "empty"
        empty_repo.mkdir()

        relations = await analyzer.analyze(empty_repo)

        assert len(relations.dependency_graph) == 0


class TestCouplingScore:
    """Test coupling score calculation."""

    @pytest.mark.asyncio
    async def test_low_coupling_high_score(self, analyzer, simple_repo):
        """Should give high score for low coupling (linear dependencies)."""
        relations = await analyzer.analyze(simple_repo)

        # Linear dependencies = low coupling = high score
        assert relations.coupling_score >= 70.0

    @pytest.mark.asyncio
    async def test_high_coupling_low_score(self, analyzer, complex_repo):
        """Should give lower score for high coupling (many dependencies on core)."""
        relations = await analyzer.analyze(complex_repo)

        # Many modules depend on core = high coupling = lower score
        assert relations.coupling_score < 100.0

    @pytest.mark.asyncio
    async def test_perfect_score_for_independent_modules(self, analyzer, tmp_path):
        """Should give perfect score for independent modules."""
        repo = tmp_path / "independent"
        repo.mkdir()

        # Two independent modules
        (repo / "module_a.py").write_text("def a(): return 'A'")
        (repo / "module_b.py").write_text("def b(): return 'B'")

        relations = await analyzer.analyze(repo)

        # No dependencies = perfect coupling score
        assert relations.coupling_score == 100.0


class TestCircularDependencyDetection:
    """Test circular dependency detection."""

    @pytest.mark.asyncio
    async def test_detect_circular_dependencies(self, analyzer, circular_repo):
        """Should detect circular dependencies."""
        relations = await analyzer.analyze(circular_repo)

        assert len(relations.circular_deps) > 0

    @pytest.mark.asyncio
    async def test_identify_circular_pair(self, analyzer, circular_repo):
        """Should identify both modules in circular dependency."""
        relations = await analyzer.analyze(circular_repo)

        # Should find A->B and B->A cycle
        circular_modules = set()
        for dep1, dep2 in relations.circular_deps:
            circular_modules.add(dep1)
            circular_modules.add(dep2)

        assert "module_a.py" in circular_modules
        assert "module_b.py" in circular_modules

    @pytest.mark.asyncio
    async def test_no_circular_deps_in_simple_repo(self, analyzer, simple_repo):
        """Should find no circular dependencies in simple repo."""
        relations = await analyzer.analyze(simple_repo)

        assert len(relations.circular_deps) == 0


class TestCoreComponentIdentification:
    """Test core component identification."""

    @pytest.mark.asyncio
    async def test_identify_core_components(self, analyzer, complex_repo):
        """Should identify core components (most depended upon)."""
        relations = await analyzer.analyze(complex_repo)

        assert len(relations.core_components) > 0

    @pytest.mark.asyncio
    async def test_core_is_most_depended_upon(self, analyzer, complex_repo):
        """Should identify core.py as core component."""
        relations = await analyzer.analyze(complex_repo)

        # core.py has 3 dependents (client_a, client_b, client_c)
        assert "core.py" in relations.core_components

    @pytest.mark.asyncio
    async def test_peripheral_not_core(self, analyzer, complex_repo):
        """Should not identify peripheral modules as core."""
        relations = await analyzer.analyze(complex_repo)

        # peripheral.py has no dependents
        assert "peripheral.py" not in relations.core_components

    @pytest.mark.asyncio
    async def test_no_core_in_linear_dependencies(self, analyzer, simple_repo):
        """Should handle repos with no clear core (linear dependencies)."""
        relations = await analyzer.analyze(simple_repo)

        # Linear dependencies: each module has at most 1 dependent
        # No clear "core" component
        assert len(relations.core_components) <= 1


class TestEdgeCases:
    """Test edge cases."""

    @pytest.mark.asyncio
    async def test_handle_import_errors(self, analyzer, tmp_path):
        """Should handle files with syntax errors gracefully."""
        repo = tmp_path / "error_repo"
        repo.mkdir()

        # File with syntax error
        (repo / "broken.py").write_text("import this is broken syntax")

        # Should not crash
        relations = await analyzer.analyze(repo)
        assert isinstance(relations, ComponentRelations)

    @pytest.mark.asyncio
    async def test_handle_relative_imports(self, analyzer, tmp_path):
        """Should handle relative imports."""
        repo = tmp_path / "relative_repo"
        repo.mkdir()

        (repo / "module_a.py").write_text("def a(): return 'A'")
        (repo / "module_b.py").write_text("""
from .module_a import a

def b():
    return a()
""")

        relations = await analyzer.analyze(repo)

        # Should detect dependency despite relative import
        assert "module_a" in relations.dependency_graph.get("module_b.py", [])

    @pytest.mark.asyncio
    async def test_handle_external_imports(self, analyzer, tmp_path):
        """Should ignore external library imports."""
        repo = tmp_path / "external_repo"
        repo.mkdir()

        (repo / "module.py").write_text("""
import os
import sys
from pathlib import Path

def function():
    return Path.cwd()
""")

        relations = await analyzer.analyze(repo)

        # Should not include external libraries in dependency graph
        deps = relations.dependency_graph.get("module.py", [])
        assert "os" not in deps
        assert "sys" not in deps
        assert "pathlib" not in deps
