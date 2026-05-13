# AIM/src/aim/teacher/code_analyzer.py
"""Code analyzer for subagent pattern detection."""

import ast
import re
from typing import Any


class CodeAnalyzer:
    """Analyze Python code for patterns and complexity."""

    def extract_imports(self, code: str) -> list[str]:
        """
        Extract all imports from code.

        Args:
            code: Python source code

        Returns:
            List of imported module names (full paths)
        """
        imports = []

        try:
            tree = ast.parse(code)

            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        imports.append(alias.name)  # Full path, not just first part
                elif isinstance(node, ast.ImportFrom):
                    if node.module:
                        imports.append(node.module)  # Full path, not just first part
        except SyntaxError:
            pass

        return list(set(imports))

    def detect_patterns(self, code: str) -> list[str]:
        """
        Detect common patterns in code.

        Args:
            code: Python source code

        Returns:
            List of detected pattern names
        """
        patterns = []

        # Circuit breaker
        if any(x in code for x in ["CircuitBreaker", "circuit_breaker", "pybreaker"]):
            patterns.append("circuit_breaker")

        # Retry logic
        if any(x in code for x in ["@retry", "tenacity", "max_attempts", "backoff"]):
            patterns.append("retry")

        # Caching
        if any(x in code for x in ["cache", "Cache", "aiocache", "@lru_cache"]):
            patterns.append("caching")

        # Rate limiting
        if any(x in code for x in ["rate_limit", "RateLimiter", "aiolimiter"]):
            patterns.append("rate_limiting")

        # Metrics
        if any(x in code for x in ["prometheus", "metrics", "Counter", "Gauge"]):
            patterns.append("metrics")

        # Logging
        if any(x in code for x in ["structlog", "logger", "logging"]):
            patterns.append("logging")

        return patterns

    def count_complexity(self, code: str) -> dict[str, Any]:
        """
        Calculate code complexity metrics.

        Args:
            code: Python source code

        Returns:
            Dictionary with complexity metrics
        """
        try:
            tree = ast.parse(code)

            functions = []
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    complexity = self._calculate_cyclomatic_complexity(node)
                    functions.append(complexity)

            return {
                "functions": len(functions),
                "avg_complexity": sum(functions) / len(functions) if functions else 0,
                "max_complexity": max(functions) if functions else 0,
            }
        except SyntaxError:
            return {"functions": 0, "avg_complexity": 0, "max_complexity": 0}

    def _calculate_cyclomatic_complexity(self, node: ast.FunctionDef) -> int:
        """Calculate cyclomatic complexity for a function."""
        complexity = 1

        for child in ast.walk(node):
            if isinstance(child, (ast.If, ast.While, ast.For, ast.ExceptHandler)):
                complexity += 1
            elif isinstance(child, ast.BoolOp):
                complexity += len(child.values) - 1

        return complexity
