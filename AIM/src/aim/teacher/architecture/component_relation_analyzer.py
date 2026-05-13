"""
ComponentRelationAnalyzer - Analyze component relationships and dependencies.

Builds dependency graph, calculates coupling, detects circular dependencies,
identifies core components.
"""

import ast
from dataclasses import dataclass
from pathlib import Path

import structlog

logger = structlog.get_logger()


@dataclass
class ComponentRelations:
    """Component relationship analysis result."""

    dependency_graph: dict[str, list[str]]  # module -> dependencies
    coupling_score: float  # 0-100 (100 = low coupling)
    circular_deps: list[tuple[str, str]]  # circular dependencies
    core_components: list[str]  # most depended upon


class ComponentRelationAnalyzer:
    """
    Analyze component relationships and dependencies.

    Responsibilities:
    - Build dependency graph from imports
    - Calculate coupling score
    - Detect circular dependencies
    - Identify core components (most depended upon)
    """

    def __init__(self):
        self.logger = logger.bind(component="component_relation_analyzer")

    async def analyze(self, repo_path: Path) -> ComponentRelations:
        """
        Analyze component relationships.

        Args:
            repo_path: Path to repository root

        Returns:
            ComponentRelations with dependency graph and metrics
        """
        self.logger.info("analyzing_component_relations", repo_path=str(repo_path))

        # Build dependency graph
        dependency_graph = await self._build_dependency_graph(repo_path)

        # Calculate coupling score
        coupling_score = self._calculate_coupling_score(dependency_graph)

        # Detect circular dependencies
        circular_deps = self._detect_circular_dependencies(dependency_graph)

        # Identify core components
        core_components = self._identify_core_components(dependency_graph)

        self.logger.info(
            "component_relations_analyzed",
            modules=len(dependency_graph),
            coupling_score=coupling_score,
            circular_deps=len(circular_deps),
            core_components=len(core_components),
        )

        return ComponentRelations(
            dependency_graph=dependency_graph,
            coupling_score=coupling_score,
            circular_deps=circular_deps,
            core_components=core_components,
        )

    async def _build_dependency_graph(
        self, repo_path: Path
    ) -> dict[str, list[str]]:
        """
        Build dependency graph from Python imports.

        Args:
            repo_path: Repository root path

        Returns:
            Dict mapping module name to list of dependencies
        """
        dependency_graph = {}

        # Scan all Python files
        for file_path in repo_path.rglob("*.py"):
            # Skip hidden files and __pycache__
            if any(part.startswith(".") for part in file_path.parts):
                continue
            if "__pycache__" in file_path.parts:
                continue

            # Get module name (relative to repo)
            module_name = file_path.name

            # Extract imports
            dependencies = self._extract_imports(file_path, repo_path)

            dependency_graph[module_name] = dependencies

        return dependency_graph

    def _extract_imports(self, file_path: Path, repo_path: Path) -> list[str]:
        """
        Extract imports from Python file.

        Args:
            file_path: Path to Python file
            repo_path: Repository root path

        Returns:
            List of imported module names (only local modules)
        """
        try:
            content = file_path.read_text()
            tree = ast.parse(content)
        except (SyntaxError, UnicodeDecodeError) as e:
            self.logger.warning(
                "failed_to_parse_file",
                file_path=str(file_path),
                error=str(e),
            )
            return []

        imports = []

        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    # Only include local modules (not external libraries)
                    if self._is_local_module(alias.name, repo_path):
                        imports.append(alias.name)

            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    # Handle relative imports (.module_a)
                    module_name = node.module.lstrip(".")
                    if self._is_local_module(module_name, repo_path):
                        imports.append(module_name)

        return imports

    def _is_local_module(self, module_name: str, repo_path: Path) -> bool:
        """
        Check if module is local (not external library).

        Args:
            module_name: Module name from import
            repo_path: Repository root path

        Returns:
            True if local module, False if external library
        """
        # Check if module file exists in repo
        module_file = repo_path / f"{module_name}.py"
        if module_file.exists():
            return True

        # Check if module is a package
        module_dir = repo_path / module_name
        if module_dir.is_dir() and (module_dir / "__init__.py").exists():
            return True

        return False

    def _calculate_coupling_score(self, dependency_graph: dict[str, list[str]]) -> float:
        """
        Calculate coupling score (0-100, higher = lower coupling).

        Coupling metrics:
        - Average dependencies per module (lower is better)
        - Dependency distribution (even distribution is better)

        Args:
            dependency_graph: Module dependency graph

        Returns:
            Coupling score (0-100)
        """
        if not dependency_graph:
            return 100.0

        total_modules = len(dependency_graph)
        total_dependencies = sum(len(deps) for deps in dependency_graph.values())

        # Average dependencies per module
        avg_dependencies = total_dependencies / total_modules if total_modules > 0 else 0

        # Score based on average dependencies
        # 0 deps = 100 score, 5+ deps = 0 score
        if avg_dependencies == 0:
            return 100.0
        elif avg_dependencies >= 5:
            return 0.0
        else:
            # Linear scale: 0 deps = 100, 5 deps = 0
            return 100.0 - (avg_dependencies * 20.0)

    def _detect_circular_dependencies(
        self, dependency_graph: dict[str, list[str]]
    ) -> list[tuple[str, str]]:
        """
        Detect circular dependencies using DFS.

        Args:
            dependency_graph: Module dependency graph

        Returns:
            List of circular dependency pairs
        """
        circular_deps = []
        visited = set()
        rec_stack = set()

        def dfs(module: str, path: list[str]) -> None:
            """DFS to detect cycles."""
            visited.add(module)
            rec_stack.add(module)
            path.append(module)

            for dep in dependency_graph.get(module, []):
                # Find actual module name in graph
                dep_module = self._find_module_in_graph(dep, dependency_graph)
                if not dep_module:
                    continue

                if dep_module not in visited:
                    dfs(dep_module, path.copy())
                elif dep_module in rec_stack:
                    # Found cycle
                    circular_deps.append((module, dep_module))

            rec_stack.remove(module)

        for module in dependency_graph:
            if module not in visited:
                dfs(module, [])

        return circular_deps

    def _find_module_in_graph(
        self, module_name: str, dependency_graph: dict[str, list[str]]
    ) -> str | None:
        """
        Find module in dependency graph by name.

        Args:
            module_name: Module name to find
            dependency_graph: Dependency graph

        Returns:
            Full module name from graph, or None if not found
        """
        # Try exact match
        if f"{module_name}.py" in dependency_graph:
            return f"{module_name}.py"

        # Try partial match
        for module in dependency_graph:
            if module_name in module:
                return module

        return None

    def _identify_core_components(
        self, dependency_graph: dict[str, list[str]]
    ) -> list[str]:
        """
        Identify core components (most depended upon).

        Core components are modules that many other modules depend on.

        Args:
            dependency_graph: Module dependency graph

        Returns:
            List of core component names
        """
        # Count how many modules depend on each module
        dependent_count: dict[str, int] = {}

        for module, dependencies in dependency_graph.items():
            for dep in dependencies:
                # Find actual module name
                dep_module = self._find_module_in_graph(dep, dependency_graph)
                if dep_module:
                    dependent_count[dep_module] = dependent_count.get(dep_module, 0) + 1

        if not dependent_count:
            return []

        # Find max dependent count
        max_dependents = max(dependent_count.values())

        # Core components have >= 2 dependents (arbitrary threshold)
        # or are in top 20% by dependent count
        threshold = max(2, max_dependents * 0.8)

        core_components = [
            module
            for module, count in dependent_count.items()
            if count >= threshold
        ]

        return core_components
