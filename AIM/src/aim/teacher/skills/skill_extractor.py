"""
Skill Extractor - Extract patterns from GitHub repositories.

Detects and extracts common patterns:
- Circuit breaker
- Retry with exponential backoff
- Rate limiting
- Caching
- Error handling
"""

import ast
import re
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any

import structlog

logger = structlog.get_logger()


class SkillType(str, Enum):
    """Types of skills that can be extracted."""
    CIRCUIT_BREAKER = "circuit_breaker"
    RETRY = "retry"
    RATE_LIMITING = "rate_limiting"
    CACHING = "caching"
    ERROR_HANDLING = "error_handling"
    LOGGING = "logging"
    METRICS = "metrics"
    VALIDATION = "validation"


@dataclass
class ExtractedSkill:
    """Extracted skill from GitHub repository."""
    skill_type: SkillType
    name: str
    description: str
    code_snippet: str
    file_path: str
    line_start: int
    line_end: int
    confidence: float  # 0.0-1.0
    dependencies: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)


class SkillExtractor:
    """
    Extract patterns from GitHub repositories.

    Detection strategies:
    1. AST parsing (Python code)
    2. Import detection (libraries used)
    3. Pattern matching (code structure)
    4. Decorator detection (@retry, @circuit_breaker)
    5. Class/function naming (CircuitBreaker, RateLimiter)

    Confidence scoring:
    - 1.0: Perfect match (decorator + implementation)
    - 0.8: Strong match (class name + methods)
    - 0.6: Medium match (imports + usage)
    - 0.4: Weak match (naming only)
    """

    def __init__(self):
        logger.info("skill_extractor_initialized")

    async def extract_skills(
        self,
        repo_path: Path,
        skill_types: list[SkillType] | None = None,
    ) -> list[ExtractedSkill]:
        """
        Extract skills from repository.

        Args:
            repo_path: Path to cloned repository
            skill_types: Types of skills to extract (None = all)

        Returns:
            List of extracted skills
        """
        logger.info(
            "extracting_skills",
            repo_path=str(repo_path),
            skill_types=skill_types,
        )

        if skill_types is None:
            skill_types = list(SkillType)

        skills = []

        # Find all Python files
        python_files = list(repo_path.rglob("*.py"))

        logger.info(
            "scanning_files",
            count=len(python_files),
        )

        for file_path in python_files:
            try:
                file_skills = await self._extract_from_file(
                    file_path=file_path,
                    skill_types=skill_types,
                )
                skills.extend(file_skills)
            except Exception as e:
                logger.warning(
                    "file_extraction_failed",
                    file_path=str(file_path),
                    error=str(e),
                )

        logger.info(
            "extraction_complete",
            skills_found=len(skills),
        )

        return skills

    async def _extract_from_file(
        self,
        file_path: Path,
        skill_types: list[SkillType],
    ) -> list[ExtractedSkill]:
        """
        Extract skills from single file.

        Returns:
            List of skills found in file
        """
        skills = []

        # Read file content
        try:
            content = file_path.read_text(encoding="utf-8")
        except Exception as e:
            logger.warning(
                "file_read_failed",
                file_path=str(file_path),
                error=str(e),
            )
            return skills

        # Remove leading whitespace from each line (for test code)
        lines = content.split("\n")
        # Find minimum indentation (excluding empty lines)
        min_indent = float('inf')
        for line in lines:
            if line.strip():  # Non-empty line
                indent = len(line) - len(line.lstrip())
                min_indent = min(min_indent, indent)

        # Remove minimum indentation from all lines
        if min_indent != float('inf') and min_indent > 0:
            dedented_lines = []
            for line in lines:
                if len(line) >= min_indent:
                    dedented_lines.append(line[min_indent:])
                else:
                    dedented_lines.append(line)
            content = "\n".join(dedented_lines)

        # Parse AST
        try:
            tree = ast.parse(content)
        except SyntaxError:
            # Not valid Python, skip
            return skills

        # Extract each skill type
        for skill_type in skill_types:
            if skill_type == SkillType.CIRCUIT_BREAKER:
                skills.extend(
                    self._extract_circuit_breaker(tree, content, file_path)
                )
            elif skill_type == SkillType.RETRY:
                skills.extend(
                    self._extract_retry(tree, content, file_path)
                )
            elif skill_type == SkillType.RATE_LIMITING:
                skills.extend(
                    self._extract_rate_limiting(tree, content, file_path)
                )
            elif skill_type == SkillType.CACHING:
                skills.extend(
                    self._extract_caching(tree, content, file_path)
                )
            elif skill_type == SkillType.ERROR_HANDLING:
                skills.extend(
                    self._extract_error_handling(tree, content, file_path)
                )

        return skills

    def _extract_circuit_breaker(
        self,
        tree: ast.AST,
        content: str,
        file_path: Path,
    ) -> list[ExtractedSkill]:
        """
        Extract circuit breaker patterns.

        Detection:
        - pybreaker library import
        - CircuitBreaker class
        - @circuit decorator
        - fail_max, reset_timeout parameters
        """
        skills = []

        # Check imports
        has_pybreaker = self._has_import(tree, "pybreaker")

        # Find CircuitBreaker usage
        for node in ast.walk(tree):
            # Class definition with CircuitBreaker in name
            if isinstance(node, ast.ClassDef):
                if "CircuitBreaker" in node.name or "circuit" in node.name.lower():
                    skill = self._create_skill_from_node(
                        skill_type=SkillType.CIRCUIT_BREAKER,
                        node=node,
                        content=content,
                        file_path=file_path,
                        confidence=0.8 if has_pybreaker else 0.6,
                        dependencies=["pybreaker"] if has_pybreaker else [],
                    )
                    skills.append(skill)
                # Class that uses pybreaker.CircuitBreaker
                elif has_pybreaker:
                    # Check if class body contains CircuitBreaker usage
                    class_code = ast.get_source_segment(content, node)
                    if class_code and "CircuitBreaker" in class_code:
                        skill = self._create_skill_from_node(
                            skill_type=SkillType.CIRCUIT_BREAKER,
                            node=node,
                            content=content,
                            file_path=file_path,
                            confidence=0.8,
                            dependencies=["pybreaker"],
                        )
                        skills.append(skill)

            # Decorator usage (both sync and async functions)
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                for decorator in node.decorator_list:
                    decorator_name = self._get_decorator_name(decorator)
                    if decorator_name and "circuit" in decorator_name.lower():
                        skill = self._create_skill_from_node(
                            skill_type=SkillType.CIRCUIT_BREAKER,
                            node=node,
                            content=content,
                            file_path=file_path,
                            confidence=1.0,
                            dependencies=["pybreaker"] if has_pybreaker else [],
                        )
                        skills.append(skill)

        return skills

    def _extract_retry(
        self,
        tree: ast.AST,
        content: str,
        file_path: Path,
    ) -> list[ExtractedSkill]:
        """
        Extract retry patterns.

        Detection:
        - tenacity library import
        - @retry decorator
        - exponential backoff
        - max_attempts parameter
        """
        skills = []

        # Check imports
        has_tenacity = self._has_import(tree, "tenacity")

        # Find retry usage
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                for decorator in node.decorator_list:
                    decorator_name = self._get_decorator_name(decorator)
                    if decorator_name and "retry" in decorator_name.lower():
                        skill = self._create_skill_from_node(
                            skill_type=SkillType.RETRY,
                            node=node,
                            content=content,
                            file_path=file_path,
                            confidence=1.0,
                            dependencies=["tenacity"] if has_tenacity else [],
                        )
                        skills.append(skill)

        return skills

    def _extract_rate_limiting(
        self,
        tree: ast.AST,
        content: str,
        file_path: Path,
    ) -> list[ExtractedSkill]:
        """
        Extract rate limiting patterns.

        Detection:
        - aiolimiter library import
        - RateLimiter class
        - Token bucket algorithm
        - capacity, refill_rate parameters
        """
        skills = []

        # Check imports
        has_aiolimiter = self._has_import(tree, "aiolimiter")

        # Find RateLimiter usage
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                if "RateLimiter" in node.name or "ratelimit" in node.name.lower():
                    skill = self._create_skill_from_node(
                        skill_type=SkillType.RATE_LIMITING,
                        node=node,
                        content=content,
                        file_path=file_path,
                        confidence=0.8 if has_aiolimiter else 0.6,
                        dependencies=["aiolimiter"] if has_aiolimiter else [],
                    )
                    skills.append(skill)

        return skills

    def _extract_caching(
        self,
        tree: ast.AST,
        content: str,
        file_path: Path,
    ) -> list[ExtractedSkill]:
        """
        Extract caching patterns.

        Detection:
        - aiocache library import
        - @cached decorator
        - Cache class
        - TTL parameter
        """
        skills = []

        # Check imports
        has_aiocache = self._has_import(tree, "aiocache")

        # Find caching usage
        for node in ast.walk(tree):
            # Decorator usage
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                for decorator in node.decorator_list:
                    decorator_name = self._get_decorator_name(decorator)
                    if decorator_name and "cache" in decorator_name.lower():
                        skill = self._create_skill_from_node(
                            skill_type=SkillType.CACHING,
                            node=node,
                            content=content,
                            file_path=file_path,
                            confidence=1.0,
                            dependencies=["aiocache"] if has_aiocache else [],
                        )
                        skills.append(skill)

            # Class usage
            if isinstance(node, ast.ClassDef):
                if "Cache" in node.name:
                    skill = self._create_skill_from_node(
                        skill_type=SkillType.CACHING,
                        node=node,
                        content=content,
                        file_path=file_path,
                        confidence=0.8 if has_aiocache else 0.6,
                        dependencies=["aiocache"] if has_aiocache else [],
                    )
                    skills.append(skill)

        return skills

    def _extract_error_handling(
        self,
        tree: ast.AST,
        content: str,
        file_path: Path,
    ) -> list[ExtractedSkill]:
        """
        Extract error handling patterns.

        Detection:
        - try/except blocks
        - Custom exception classes
        - Error recovery logic
        - Logging on errors
        """
        skills = []

        # Find try/except blocks with recovery
        for node in ast.walk(tree):
            if isinstance(node, ast.Try):
                # Check if has recovery logic (not just pass/raise)
                has_recovery = False
                for handler in node.handlers:
                    if len(handler.body) > 1:  # More than just pass/raise
                        has_recovery = True
                        break

                if has_recovery:
                    skill = self._create_skill_from_node(
                        skill_type=SkillType.ERROR_HANDLING,
                        node=node,
                        content=content,
                        file_path=file_path,
                        confidence=0.7,
                        dependencies=[],
                    )
                    skills.append(skill)

        return skills

    def _has_import(self, tree: ast.AST, module_name: str) -> bool:
        """Check if module is imported."""
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    if module_name in alias.name:
                        return True
            elif isinstance(node, ast.ImportFrom):
                if node.module and module_name in node.module:
                    return True
        return False

    def _get_decorator_name(self, decorator: ast.expr) -> str | None:
        """
        Extract decorator name from AST node.

        Handles:
        - Simple: @retry
        - Call: @retry(...)
        - Attribute: @module.retry
        """
        if isinstance(decorator, ast.Name):
            return decorator.id
        elif isinstance(decorator, ast.Call):
            if isinstance(decorator.func, ast.Name):
                return decorator.func.id
            elif isinstance(decorator.func, ast.Attribute):
                return decorator.func.attr
        elif isinstance(decorator, ast.Attribute):
            return decorator.attr
        return None

    def _create_skill_from_node(
        self,
        skill_type: SkillType,
        node: ast.AST,
        content: str,
        file_path: Path,
        confidence: float,
        dependencies: list[str],
    ) -> ExtractedSkill:
        """Create ExtractedSkill from AST node."""
        # Get line numbers
        line_start = node.lineno if hasattr(node, "lineno") else 0
        line_end = node.end_lineno if hasattr(node, "end_lineno") else line_start

        # For functions with decorators, include decorators in snippet
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.decorator_list:
            # Get first decorator line
            first_decorator = node.decorator_list[0]
            if hasattr(first_decorator, "lineno"):
                line_start = first_decorator.lineno

        # Extract code snippet
        lines = content.split("\n")
        code_snippet = "\n".join(lines[line_start - 1:line_end])

        # Get name
        if isinstance(node, (ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)):
            name = node.name
        else:
            name = f"{skill_type.value}_pattern"

        # Create description
        description = f"{skill_type.value.replace('_', ' ').title()} pattern"

        return ExtractedSkill(
            skill_type=skill_type,
            name=name,
            description=description,
            code_snippet=code_snippet,
            file_path=str(file_path),
            line_start=line_start,
            line_end=line_end,
            confidence=confidence,
            dependencies=dependencies,
        )
