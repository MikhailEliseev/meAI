"""
SkillExtractor - Extract and adapt implementations from best skills.

Extracts:
- Code implementation
- Dependencies (imports)
- Integration instructions
- Suggested target path

Adapts code to project structure and conventions.
"""

import ast
import re
from dataclasses import dataclass, field
from pathlib import Path

import structlog

from aim.teacher.skills.skill_selector import Skill

logger = structlog.get_logger()


@dataclass
class ExtractedImplementation:
    """Extracted implementation from skill."""

    code: str  # Adapted code
    dependencies: list[str] = field(default_factory=list)  # pip packages
    python_imports: list[str] = field(default_factory=list)  # Python import statements
    integration_instructions: str = ""  # How to integrate
    suggested_path: Path | None = None  # Where to place code


class SkillExtractor:
    """
    Extract and adapt implementations from best skills.

    Responsibilities:
    - Extract code from skill
    - Identify dependencies (imports)
    - Generate integration instructions
    - Suggest target path in project
    - Adapt code to project conventions
    """

    def __init__(self):
        self.logger = logger.bind(component="skill_extractor")

    async def extract(
        self, skill: Skill, target_path: Path | None = None
    ) -> ExtractedImplementation:
        """
        Extract implementation from skill.

        Args:
            skill: Skill to extract from
            target_path: Optional target path in project

        Returns:
            ExtractedImplementation with code, dependencies, and instructions
        """
        self.logger.info("extracting_skill", skill=skill.name, source=skill.source_repo)

        # Handle empty code
        if not skill.code_example or not skill.code_example.strip():
            self.logger.warning("no_code_example", skill=skill.name)
            return ExtractedImplementation(
                code="",
                dependencies=[],
                python_imports=[],
                integration_instructions="No code example available.",
                suggested_path=target_path,
            )

        # Extract dependencies
        dependencies = self._extract_dependencies(skill.code_example)

        # Extract Python import statements
        python_imports = self._extract_python_imports(skill.code_example)

        # Generate integration instructions
        instructions = self._generate_instructions(skill, dependencies, target_path)

        # Suggest target path if not provided
        if target_path is None:
            target_path = self._suggest_path(skill)

        self.logger.info(
            "skill_extracted",
            skill=skill.name,
            dependencies_count=len(dependencies),
            python_imports_count=len(python_imports),
            target_path=str(target_path) if target_path else None,
        )

        return ExtractedImplementation(
            code=skill.code_example.strip(),
            dependencies=dependencies,
            python_imports=python_imports,
            integration_instructions=instructions,
            suggested_path=target_path,
        )

    def _extract_dependencies(self, code: str) -> list[str]:
        """
        Extract dependencies from code.

        Parses imports and identifies pip packages.

        Args:
            code: Python code

        Returns:
            List of pip package names
        """
        dependencies = set()

        try:
            tree = ast.parse(code)

            for node in ast.walk(tree):
                # from X import Y
                if isinstance(node, ast.ImportFrom):
                    if node.module:
                        # Get top-level package
                        package = node.module.split(".")[0]
                        dependencies.add(package)

                # import X
                elif isinstance(node, ast.Import):
                    for alias in node.names:
                        # Get top-level package
                        package = alias.name.split(".")[0]
                        dependencies.add(package)

        except SyntaxError:
            self.logger.warning("syntax_error_parsing_imports", code_preview=code[:100])
            # Fallback: regex-based extraction
            dependencies.update(self._extract_dependencies_regex(code))

        # Filter out standard library
        stdlib = {
            "os", "sys", "re", "json", "time", "datetime", "pathlib",
            "typing", "dataclasses", "abc", "asyncio", "logging",
            "collections", "itertools", "functools", "operator",
        }
        dependencies = dependencies - stdlib

        return sorted(list(dependencies))

    def _extract_dependencies_regex(self, code: str) -> set[str]:
        """
        Extract dependencies using regex (fallback).

        Args:
            code: Python code

        Returns:
            Set of package names
        """
        dependencies = set()

        # Match: from X import Y
        from_imports = re.findall(r"from\s+(\w+)", code)
        dependencies.update(from_imports)

        # Match: import X
        imports = re.findall(r"import\s+(\w+)", code)
        dependencies.update(imports)

        return dependencies

    def _extract_python_imports(self, code: str) -> list[str]:
        """
        Extract Python import statements using AST parsing.

        Returns full import statements (not just package names):
        - "from openai import ChatOpenAI"
        - "import httpx"
        - "from typing import Any, Dict"

        Args:
            code: Python code

        Returns:
            List of import statements (deduplicated)
        """
        import_statements = []

        try:
            tree = ast.parse(code)
        except SyntaxError:
            self.logger.warning("syntax_error_extracting_imports", code_preview=code[:100])
            return []

        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                # import httpx, asyncio
                for alias in node.names:
                    if alias.asname:
                        import_statements.append(f"import {alias.name} as {alias.asname}")
                    else:
                        import_statements.append(f"import {alias.name}")

            elif isinstance(node, ast.ImportFrom):
                # from openai import ChatOpenAI
                module = node.module or ""
                names = []
                for alias in node.names:
                    if alias.asname:
                        names.append(f"{alias.name} as {alias.asname}")
                    else:
                        names.append(alias.name)

                if names:
                    import_statements.append(f"from {module} import {', '.join(names)}")

        # Deduplicate while preserving order
        seen = set()
        unique_imports = []
        for stmt in import_statements:
            if stmt not in seen:
                seen.add(stmt)
                unique_imports.append(stmt)

        return unique_imports

    def _generate_instructions(
        self, skill: Skill, dependencies: list[str], target_path: Path | None
    ) -> str:
        """
        Generate integration instructions.

        Args:
            skill: Skill being extracted
            dependencies: List of dependencies
            target_path: Target path in project

        Returns:
            Integration instructions (markdown)
        """
        instructions = []

        # Header
        instructions.append(f"# Integration: {skill.name}\n")
        instructions.append(f"**Source:** {skill.source_repo}\n")
        instructions.append(f"**Description:** {skill.description}\n")

        # Dependencies
        if dependencies:
            instructions.append("\n## 1. Install Dependencies\n")
            instructions.append("Add to `requirements.txt`:\n")
            instructions.append("```")
            for dep in dependencies:
                instructions.append(f"{dep}>=1.0.0  # {skill.name}")
            instructions.append("```\n")
            instructions.append("Install:\n")
            instructions.append("```bash")
            instructions.append(f"pip install {' '.join(dependencies)}")
            instructions.append("```\n")

        # Integration
        instructions.append("\n## 2. Integration Steps\n")

        if target_path:
            instructions.append(f"1. Add code to `{target_path}`\n")
        else:
            instructions.append("1. Choose appropriate location in project\n")

        instructions.append("2. Adapt imports to project structure\n")
        instructions.append("3. Update configuration if needed\n")
        instructions.append("4. Add tests for new functionality\n")

        # Configuration hints
        if "fail_max" in skill.code_example or "reset_timeout" in skill.code_example:
            instructions.append("\n## 3. Configuration\n")
            instructions.append("Circuit breaker parameters:\n")
            instructions.append("- `fail_max`: Max failures before opening (default: 5)\n")
            instructions.append("- `reset_timeout`: Seconds before retry (default: 60)\n")

        if "retry" in skill.code_example.lower():
            instructions.append("\n## 3. Configuration\n")
            instructions.append("Retry parameters:\n")
            instructions.append("- `stop_after_attempt`: Max retry attempts\n")
            instructions.append("- `wait_exponential`: Backoff strategy\n")

        # Usage example
        instructions.append("\n## 4. Usage\n")
        instructions.append("```python")
        instructions.append("# Example usage:")
        instructions.append(skill.code_example.strip())
        instructions.append("```\n")

        return "\n".join(instructions)

    def _suggest_path(self, skill: Skill) -> Path | None:
        """
        Suggest target path in project.

        Args:
            skill: Skill being extracted

        Returns:
            Suggested path or None
        """
        # Pattern-based suggestions
        name_lower = skill.name.lower()

        if "circuit breaker" in name_lower or "breaker" in name_lower:
            return Path("AIM/src/aim/subagents/api_clients/base.py")

        if "retry" in name_lower:
            return Path("AIM/src/aim/subagents/api_clients/base.py")

        if "rate limit" in name_lower:
            return Path("AIM/src/aim/subagents/api_clients/base.py")

        if "cache" in name_lower or "caching" in name_lower:
            return Path("AIM/src/aim/subagents/api_clients/base.py")

        # Default: utils
        return Path("AIM/src/aim/subagents/utils/")
