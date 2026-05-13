"""
DesignPatternDetector - Detect design patterns and architecture styles.

Detects:
- Design patterns (Strategy, Factory, Observer, Singleton, DI)
- Architecture styles (Layered, Hexagonal, Clean)
- SOLID principles compliance
"""

import ast
from dataclasses import dataclass, field
from pathlib import Path

import structlog

logger = structlog.get_logger()


@dataclass
class DesignPatterns:
    """Design pattern detection result."""

    patterns: list[str] = field(default_factory=list)  # ["Strategy", "Factory"]
    architecture_style: str = "Unknown"  # "Layered" | "Hexagonal" | "Clean" | "Unknown"
    solid_compliance: dict[str, bool] = field(default_factory=dict)  # S, O, L, I, D


class DesignPatternDetector:
    """
    Detect design patterns and architecture styles.

    Responsibilities:
    - Detect common design patterns (Strategy, Factory, Observer, etc.)
    - Identify architecture style (Layered, Hexagonal, Clean)
    - Check SOLID principles compliance
    """

    def __init__(self):
        self.logger = logger.bind(component="design_pattern_detector")

    async def analyze(self, repo_path: Path) -> DesignPatterns:
        """
        Analyze repository for design patterns.

        Args:
            repo_path: Path to repository root

        Returns:
            DesignPatterns with detected patterns and architecture style
        """
        self.logger.info("analyzing_design_patterns", repo_path=str(repo_path))

        # Detect patterns
        patterns = []
        patterns.extend(await self._detect_strategy_pattern(repo_path))
        patterns.extend(await self._detect_factory_pattern(repo_path))
        patterns.extend(await self._detect_observer_pattern(repo_path))
        patterns.extend(await self._detect_singleton_pattern(repo_path))
        patterns.extend(await self._detect_dependency_injection(repo_path))

        # Identify architecture style
        architecture_style = await self._identify_architecture_style(repo_path)

        # Check SOLID compliance
        solid_compliance = await self._check_solid_compliance(repo_path, patterns)

        self.logger.info(
            "design_patterns_analyzed",
            patterns=patterns,
            architecture_style=architecture_style,
            solid_compliance=solid_compliance,
        )

        return DesignPatterns(
            patterns=patterns,
            architecture_style=architecture_style,
            solid_compliance=solid_compliance,
        )

    async def _detect_strategy_pattern(self, repo_path: Path) -> list[str]:
        """
        Detect Strategy pattern.

        Strategy pattern: multiple implementations of same interface/abstract class.
        """
        has_abstract_base = False
        concrete_implementations = 0

        for file_path in repo_path.rglob("*.py"):
            if self._should_skip_file(file_path):
                continue

            try:
                content = file_path.read_text()
                tree = ast.parse(content)

                for node in ast.walk(tree):
                    if isinstance(node, ast.ClassDef):
                        # Check for abstract base class
                        if self._is_abstract_class(node):
                            has_abstract_base = True

                        # Check for concrete implementation
                        if self._has_base_classes(node):
                            concrete_implementations += 1

            except (SyntaxError, UnicodeDecodeError):
                continue

        # Strategy pattern: 1 abstract base + 2+ concrete implementations
        if has_abstract_base and concrete_implementations >= 2:
            return ["Strategy"]

        return []

    async def _detect_factory_pattern(self, repo_path: Path) -> list[str]:
        """
        Detect Factory pattern.

        Factory pattern: method that returns different types based on input.
        """
        for file_path in repo_path.rglob("*.py"):
            if self._should_skip_file(file_path):
                continue

            try:
                content = file_path.read_text()
                tree = ast.parse(content)

                for node in ast.walk(tree):
                    if isinstance(node, ast.FunctionDef):
                        # Check for factory method pattern
                        if self._is_factory_method(node):
                            return ["Factory"]

            except (SyntaxError, UnicodeDecodeError):
                continue

        return []

    async def _detect_observer_pattern(self, repo_path: Path) -> list[str]:
        """
        Detect Observer pattern.

        Observer pattern: subscribe/notify mechanism.
        """
        for file_path in repo_path.rglob("*.py"):
            if self._should_skip_file(file_path):
                continue

            try:
                content = file_path.read_text()
                tree = ast.parse(content)

                for node in ast.walk(tree):
                    if isinstance(node, ast.ClassDef):
                        methods = [m.name for m in node.body if isinstance(m, ast.FunctionDef)]

                        # Observer pattern: subscribe + notify methods
                        if "subscribe" in methods and "notify" in methods:
                            return ["Observer"]

            except (SyntaxError, UnicodeDecodeError):
                continue

        return []

    async def _detect_singleton_pattern(self, repo_path: Path) -> list[str]:
        """
        Detect Singleton pattern.

        Singleton pattern: __new__ method with instance check.
        """
        for file_path in repo_path.rglob("*.py"):
            if self._should_skip_file(file_path):
                continue

            try:
                content = file_path.read_text()
                tree = ast.parse(content)

                for node in ast.walk(tree):
                    if isinstance(node, ast.ClassDef):
                        # Check for _instance class variable
                        has_instance_var = any(
                            isinstance(item, ast.Assign)
                            and any(
                                isinstance(target, ast.Name) and target.id == "_instance"
                                for target in item.targets
                            )
                            for item in node.body
                        )

                        # Check for __new__ method
                        has_new_method = any(
                            isinstance(item, ast.FunctionDef) and item.name == "__new__"
                            for item in node.body
                        )

                        if has_instance_var and has_new_method:
                            return ["Singleton"]

            except (SyntaxError, UnicodeDecodeError):
                continue

        return []

    async def _detect_dependency_injection(self, repo_path: Path) -> list[str]:
        """
        Detect Dependency Injection pattern.

        DI pattern: constructor injection (dependencies passed to __init__).
        """
        di_count = 0

        for file_path in repo_path.rglob("*.py"):
            if self._should_skip_file(file_path):
                continue

            try:
                content = file_path.read_text()
                tree = ast.parse(content)

                for node in ast.walk(tree):
                    if isinstance(node, ast.ClassDef):
                        # Find __init__ method
                        for item in node.body:
                            if isinstance(item, ast.FunctionDef) and item.name == "__init__":
                                # Check if has 2+ parameters (self + 1+ dependencies)
                                # self + 2 dependencies = 3 args minimum
                                if len(item.args.args) >= 3:
                                    di_count += 1

            except (SyntaxError, UnicodeDecodeError):
                continue

        # DI pattern: 1+ classes with constructor injection
        if di_count >= 1:
            return ["Dependency Injection"]

        return []

    async def _identify_architecture_style(self, repo_path: Path) -> str:
        """
        Identify architecture style.

        Layered: presentation/, business/, data/ directories
        Hexagonal: ports/, adapters/ directories
        Clean: entities/, use_cases/, interfaces/ directories
        """
        subdirs = [d.name for d in repo_path.iterdir() if d.is_dir()]

        # Check for Layered architecture
        layered_indicators = ["presentation", "business", "data", "api", "service", "repository"]
        if sum(1 for indicator in layered_indicators if indicator in subdirs) >= 2:
            return "Layered"

        # Check for Hexagonal architecture
        hexagonal_indicators = ["ports", "adapters", "domain"]
        if sum(1 for indicator in hexagonal_indicators if indicator in subdirs) >= 2:
            return "Hexagonal"

        # Check for Clean architecture
        clean_indicators = ["entities", "use_cases", "interfaces", "frameworks"]
        if sum(1 for indicator in clean_indicators if indicator in subdirs) >= 2:
            return "Clean"

        return "Unknown"

    async def _check_solid_compliance(
        self, repo_path: Path, detected_patterns: list[str]
    ) -> dict[str, bool]:
        """
        Check SOLID principles compliance.

        S - Single Responsibility: classes with focused purpose
        O - Open/Closed: Strategy pattern indicates OCP
        L - Liskov Substitution: inheritance without breaking contracts
        I - Interface Segregation: small, focused interfaces
        D - Dependency Inversion: DI pattern indicates DIP
        """
        solid = {
            "S": False,
            "O": False,
            "L": False,
            "I": False,
            "D": False,
        }

        # Check S (Single Responsibility)
        class_count = 0
        focused_classes = 0

        for file_path in repo_path.rglob("*.py"):
            if self._should_skip_file(file_path):
                continue

            try:
                content = file_path.read_text()
                tree = ast.parse(content)

                for node in ast.walk(tree):
                    if isinstance(node, ast.ClassDef):
                        class_count += 1
                        methods = [m for m in node.body if isinstance(m, ast.FunctionDef)]

                        # Focused class: 2-10 methods (arbitrary heuristic)
                        if 2 <= len(methods) <= 10:
                            focused_classes += 1

            except (SyntaxError, UnicodeDecodeError):
                continue

        if class_count > 0 and focused_classes / class_count >= 0.7:
            solid["S"] = True

        # Check O (Open/Closed)
        if "Strategy" in detected_patterns or "Factory" in detected_patterns:
            solid["O"] = True

        # Check D (Dependency Inversion)
        if "Dependency Injection" in detected_patterns:
            solid["D"] = True

        return solid

    def _should_skip_file(self, file_path: Path) -> bool:
        """Check if file should be skipped."""
        if any(part.startswith(".") for part in file_path.parts):
            return True
        if "__pycache__" in file_path.parts:
            return True
        return False

    def _is_abstract_class(self, node: ast.ClassDef) -> bool:
        """Check if class is abstract (has ABC base or abstractmethod)."""
        # Check for ABC base class
        for base in node.bases:
            if isinstance(base, ast.Name) and base.id == "ABC":
                return True

        # Check for abstractmethod decorator
        for item in node.body:
            if isinstance(item, ast.FunctionDef):
                for decorator in item.decorator_list:
                    if isinstance(decorator, ast.Name) and decorator.id == "abstractmethod":
                        return True

        return False

    def _has_base_classes(self, node: ast.ClassDef) -> bool:
        """Check if class has base classes."""
        return len(node.bases) > 0

    def _is_factory_method(self, node: ast.FunctionDef) -> bool:
        """Check if method is a factory method."""
        # Factory method indicators:
        # - Static method or class method
        # - Has if/elif branches returning different types
        # - Name contains "create" or "factory"

        is_static_or_class = any(
            isinstance(dec, ast.Name) and dec.id in ["staticmethod", "classmethod"]
            for dec in node.decorator_list
        )

        has_factory_name = "create" in node.name.lower() or "factory" in node.name.lower()

        # Count return statements in the method
        return_count = sum(1 for item in ast.walk(node) if isinstance(item, ast.Return))
        has_multiple_returns = return_count >= 2

        return (is_static_or_class or has_factory_name) and has_multiple_returns
