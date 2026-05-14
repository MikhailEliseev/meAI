"""
SkillApplier - Apply extracted skills to codebase.

Applies:
- Code to target files
- Dependencies to requirements.txt
- Tests for new code
- Documentation updates

Adapts code to project structure and conventions.
"""

import re
from dataclasses import dataclass, field
from pathlib import Path

import structlog

from AIM.src.aim.teacher.skills.skill_extractor import ExtractedImplementation

logger = structlog.get_logger()


@dataclass
class TargetContext:
    """Context of target file where code will be applied."""
    is_async: bool
    libraries: set[str]  # httpx, aiohttp, requests, urllib
    error_style: str  # "raise" or "exit" or "return"
    base_classes: list[str]  # ABC, BaseModel, etc.
    imports: set[str]  # existing imports
    subagent_name: str  # For domain-specific scoring


@dataclass
class ApplicationResult:
    """Result of applying skill to codebase."""

    files_created: list[Path] = field(default_factory=list)
    files_modified: list[Path] = field(default_factory=list)
    dependencies_added: list[str] = field(default_factory=list)
    tests_created: list[Path] = field(default_factory=list)
    success: bool = False
    error: str | None = None


class SkillApplier:
    """
    Apply extracted skills to codebase.

    Responsibilities:
    - Create/update files with extracted code
    - Add dependencies to requirements.txt
    - Adapt code to project structure
    - Generate tests for new code
    - Update documentation
    """

    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.logger = logger.bind(component="skill_applier")

    async def _analyze_target_context(self, target_path: Path, subagent_name: str) -> TargetContext:
        """Analyze target file to understand context."""
        if not target_path.exists():
            return TargetContext(
                is_async=False,
                libraries=set(),
                error_style="raise",
                base_classes=[],
                imports=set(),
                subagent_name=subagent_name
            )

        content = target_path.read_text()

        # Detect async
        is_async = "async def" in content or "await " in content

        # Detect libraries
        libraries = set()
        if "import httpx" in content or "from httpx" in content:
            libraries.add("httpx")
        if "import aiohttp" in content or "from aiohttp" in content:
            libraries.add("aiohttp")
        if "import requests" in content or "from requests" in content:
            libraries.add("requests")
        if "import urllib" in content or "from urllib" in content:
            libraries.add("urllib")

        # Detect error style
        error_style = "raise"
        if "sys.exit(" in content:
            error_style = "exit"
        elif "return None" in content and "raise" not in content:
            error_style = "return"

        # Detect base classes
        base_classes = []
        for match in re.finditer(r"class \w+\(([^)]+)\)", content):
            base_classes.extend(m.strip() for m in match.group(1).split(","))

        # Detect imports
        imports = set()
        for match in re.finditer(r"^(?:from|import)\s+(\S+)", content, re.MULTILINE):
            imports.add(match.group(1))

        self.logger.info(
            "target_context_analyzed",
            path=str(target_path),
            is_async=is_async,
            libraries=list(libraries),
            error_style=error_style,
            base_classes=base_classes[:3] if base_classes else []
        )

        return TargetContext(
            is_async=is_async,
            libraries=libraries,
            error_style=error_style,
            base_classes=base_classes,
            imports=imports,
            subagent_name=subagent_name
        )

    async def apply_with_validation(
        self,
        implementation: ExtractedImplementation,
        target_path: Path | None = None,
        subagent_name: str | None = None,
    ) -> ApplicationResult:
        """
        Apply with context validation and adaptation.

        Args:
            implementation: Extracted implementation to apply
            target_path: Target path in project (overrides suggested_path)
            subagent_name: Name of subagent (for context)

        Returns:
            ApplicationResult with created/modified files
        """
        self.logger.info(
            "applying_with_validation",
            target_path=str(target_path) if target_path else None,
            subagent=subagent_name,
        )

        result = ApplicationResult()

        try:
            # Determine target path
            final_path = target_path or implementation.suggested_path
            if not final_path:
                result.error = "No target path specified"
                return result

            # Make path absolute relative to project root
            if not final_path.is_absolute():
                path_str = str(final_path)
                project_name = self.project_root.name

                if path_str.startswith(project_name + "/"):
                    final_path = self.project_root.parent / final_path
                else:
                    final_path = self.project_root / final_path

            # Step 1: Analyze target context
            self.logger.info("step_1_analyze_context", target=str(final_path))
            target_context = await self._analyze_target_context(final_path, subagent_name or "unknown")

            # Step 2: Check compatibility
            self.logger.info("step_2_check_compatibility")
            is_compatible, reason = self._check_code_compatibility(
                implementation.code,
                target_context
            )

            if not is_compatible:
                self.logger.error(
                    "code_incompatible",
                    reason=reason,
                    target=str(final_path)
                )
                result.error = f"Code incompatible: {reason}"
                result.success = False
                return result

            # Step 3: Adapt code to context
            self.logger.info("step_3_adapt_code")
            adapted_code = self._adapt_to_context(
                implementation.code,
                target_context
            )

            # Step 4: Apply adapted code
            self.logger.info("step_4_apply_code")
            adapted_implementation = ExtractedImplementation(
                code=adapted_code,
                dependencies=implementation.dependencies,
                integration_instructions=implementation.integration_instructions,
                suggested_path=implementation.suggested_path,
            )

            return await self.apply(
                adapted_implementation,
                target_path=target_path,
                subagent_name=subagent_name
            )

        except Exception as e:
            self.logger.error("validation_failed", error=str(e))
            result.error = str(e)
            result.success = False
            return result

    async def apply(
        self,
        implementation: ExtractedImplementation,
        target_path: Path | None = None,
        subagent_name: str | None = None,
    ) -> ApplicationResult:
        """
        Apply extracted implementation to codebase.

        Args:
            implementation: Extracted implementation to apply
            target_path: Target path in project (overrides suggested_path)
            subagent_name: Name of subagent (for context)

        Returns:
            ApplicationResult with created/modified files
        """
        self.logger.info(
            "applying_implementation",
            target_path=str(target_path) if target_path else None,
            subagent=subagent_name,
        )

        result = ApplicationResult()

        try:
            # Determine target path
            final_path = target_path or implementation.suggested_path
            if not final_path:
                result.error = "No target path specified"
                return result

            # Make path absolute relative to project root
            if not final_path.is_absolute():
                # Check if path already starts with project_root name
                path_str = str(final_path)
                project_name = self.project_root.name  # "AIM"

                if path_str.startswith(project_name + "/"):
                    # Path already includes project root, use as-is
                    final_path = self.project_root.parent / final_path
                else:
                    # Path is relative to project root
                    final_path = self.project_root / final_path

            # Step 1: Create/update code file
            if implementation.code:
                created = await self._apply_code(
                    implementation.code,
                    final_path,
                    subagent_name,
                )
                if created:
                    result.files_created.append(final_path)
                else:
                    result.files_modified.append(final_path)

            # Step 2: Add dependencies
            if implementation.dependencies:
                added = await self._add_dependencies(implementation.dependencies)
                result.dependencies_added = added

            # Step 3: Generate tests
            if implementation.code:
                test_file = await self._generate_tests(
                    final_path,
                    implementation.code,
                    subagent_name,
                )
                if test_file:
                    result.tests_created.append(test_file)

            result.success = True
            self.logger.info(
                "application_complete",
                files_created=len(result.files_created),
                files_modified=len(result.files_modified),
                dependencies_added=len(result.dependencies_added),
                tests_created=len(result.tests_created),
            )

        except Exception as e:
            self.logger.error("application_failed", error=str(e))
            result.error = str(e)
            result.success = False

        return result

    def _check_code_compatibility(
        self,
        code: str,
        target_context: TargetContext
    ) -> tuple[bool, str]:
        """Check if code is compatible with target context."""

        # Check async/sync compatibility
        code_is_async = "async def" in code or "await " in code
        if target_context.is_async and not code_is_async:
            return False, "Target is async, code is sync"

        # Check library compatibility
        code_libraries = set()
        if "httpx" in code:
            code_libraries.add("httpx")
        if "aiohttp" in code:
            code_libraries.add("aiohttp")
        if "requests" in code:
            code_libraries.add("requests")
        if "urllib" in code:
            code_libraries.add("urllib")

        # If code uses libraries, check if target uses compatible ones
        if code_libraries and target_context.libraries:
            if not code_libraries.intersection(target_context.libraries):
                return False, f"Library mismatch: code uses {code_libraries}, target uses {target_context.libraries}"

        # Check error handling compatibility
        if "sys.exit(" in code and target_context.error_style == "raise":
            return False, "Code uses sys.exit(), target uses raise"

        return True, "Compatible"

    def _adapt_to_context(
        self,
        code: str,
        target_context: TargetContext
    ) -> str:
        """Adapt code to match target context."""

        adapted = code

        # Adapt async/sync
        if target_context.is_async and "async def" not in code:
            # Convert sync to async
            adapted = adapted.replace("def ", "async def ")
            # Add await to blocking calls (basic heuristic)
            adapted = re.sub(
                r"(\w+)\.(get|post|put|delete|request)\(",
                r"await \1.\2(",
                adapted
            )

        # Adapt libraries
        if "urllib" in code and "httpx" in target_context.libraries:
            # Replace urllib with httpx (basic patterns)
            adapted = adapted.replace("urllib.request.urlopen", "httpx.AsyncClient().get")
            adapted = adapted.replace("urllib.request.Request", "httpx.Request")
            adapted = adapted.replace("import urllib", "import httpx")

        # Adapt error handling
        if "sys.exit(" in code and target_context.error_style == "raise":
            # Replace sys.exit with raise
            adapted = re.sub(
                r"sys\.exit\((\d+)\)",
                r"raise RuntimeError(f'Exit code: \1')",
                adapted
            )
            adapted = re.sub(
                r"sys\.exit\(\)",
                r"raise RuntimeError('Operation failed')",
                adapted
            )

        self.logger.info(
            "code_adapted",
            async_converted=target_context.is_async and "async def" not in code,
            urllib_to_httpx="urllib" in code and "httpx" in target_context.libraries,
            exit_to_raise="sys.exit(" in code and target_context.error_style == "raise"
        )

        return adapted

    async def _apply_code(
        self,
        code: str,
        target_path: Path,
        subagent_name: str | None = None,
    ) -> bool:
        """
        Apply code to target file.

        Args:
            code: Code to apply
            target_path: Target file path
            subagent_name: Subagent name for context

        Returns:
            True if file was created, False if modified
        """
        created = not target_path.exists()

        # Create parent directories
        target_path.parent.mkdir(parents=True, exist_ok=True)

        # Adapt code to project conventions
        adapted_code = self._adapt_code(code, subagent_name)

        if created:
            # New file: write with header
            header = self._generate_header(subagent_name)
            with open(target_path, "w") as f:
                f.write(header)
                f.write("\n\n")
                f.write(adapted_code)
        else:
            # Existing file: append code with separator
            with open(target_path, "a") as f:
                f.write("\n\n")
                f.write("# " + "=" * 78 + "\n")
                f.write(f"# Added by Teacher Agent: {subagent_name or 'skill extraction'}\n")
                f.write("# " + "=" * 78 + "\n\n")
                f.write(adapted_code)

        self.logger.info(
            "code_applied",
            path=str(target_path),
            created=created,
        )

        return created

    def _adapt_code(self, code: str, subagent_name: str | None = None) -> str:
        """
        Adapt code to project conventions.

        Args:
            code: Original code
            subagent_name: Subagent name for context

        Returns:
            Adapted code
        """
        # Remove common prefixes/suffixes from extracted code
        code = code.strip()

        # Ensure proper imports
        if "import" not in code and "from" not in code:
            # Add basic imports if missing
            imports = []

            # Typing imports
            typing_types = []
            if "Optional[" in code:
                typing_types.append("Optional")
            if "List[" in code:
                typing_types.append("List")
            if "Dict[" in code:
                typing_types.append("Dict")
            if "Any" in code:
                typing_types.append("Any")
            if typing_types:
                imports.append(f"from typing import {', '.join(typing_types)}")

            # Standard library imports
            if "async" in code or "await" in code:
                imports.append("import asyncio")
            if "Path" in code:
                imports.append("from pathlib import Path")

            # Third-party imports
            if "httpx" in code:
                imports.append("import httpx")
            if "structlog" in code:
                imports.append("import structlog")

            if imports:
                code = "\n".join(imports) + "\n\n" + code

        # Ensure proper indentation
        lines = code.split("\n")
        if lines and not lines[0].startswith(" "):
            # Code is at module level, keep as is
            pass
        else:
            # Code might be indented, dedent it
            min_indent = min(
                len(line) - len(line.lstrip())
                for line in lines
                if line.strip()
            )
            if min_indent > 0:
                lines = [line[min_indent:] if line.strip() else line for line in lines]
                code = "\n".join(lines)

        return code

    def _generate_header(self, subagent_name: str | None = None) -> str:
        """
        Generate file header comment.

        Args:
            subagent_name: Subagent name for context

        Returns:
            Header comment
        """
        header = '"""\n'
        if subagent_name:
            header += f"{subagent_name.title()} - Extracted skill implementation.\n"
        else:
            header += "Extracted skill implementation.\n"
        header += "\n"
        header += "Source: Teacher Agent skill extraction\n"
        header += "Adapted for AIM project structure\n"
        header += '"""'
        return header

    async def _add_dependencies(self, dependencies: list[str]) -> list[str]:
        """
        Add dependencies to requirements.txt.

        Args:
            dependencies: List of pip packages

        Returns:
            List of actually added dependencies (not duplicates)
        """
        requirements_path = self.project_root / "requirements.txt"

        # Read existing requirements
        existing = set()
        if requirements_path.exists():
            with open(requirements_path, "r") as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith("#"):
                        # Extract package name (before ==, >=, etc.)
                        pkg_name = re.split(r"[=<>!]", line)[0].strip()
                        existing.add(pkg_name.lower())

        # Filter out duplicates
        to_add = []
        for dep in dependencies:
            pkg_name = re.split(r"[=<>!]", dep)[0].strip()
            if pkg_name.lower() not in existing:
                to_add.append(dep)

        # Add new dependencies
        if to_add:
            with open(requirements_path, "a") as f:
                f.write("\n# Added by Teacher Agent\n")
                for dep in to_add:
                    f.write(f"{dep}\n")

            self.logger.info(
                "dependencies_added",
                count=len(to_add),
                packages=to_add,
            )

        return to_add

    async def _generate_tests(
        self,
        target_path: Path,
        code: str,
        subagent_name: str | None = None,
    ) -> Path | None:
        """
        Generate tests for applied code.

        Args:
            target_path: Path to code file
            code: Code content
            subagent_name: Subagent name for context

        Returns:
            Path to test file if created, None otherwise
        """
        # Determine test file path
        # Convert src/aim/subagents/X.py -> tests/subagents/test_X.py
        relative_path = target_path.relative_to(self.project_root)

        if "src" in relative_path.parts:
            # Replace src with tests
            parts = list(relative_path.parts)
            src_idx = parts.index("src")
            parts[src_idx] = "tests"

            # Add test_ prefix to filename
            filename = parts[-1]
            if not filename.startswith("test_"):
                parts[-1] = f"test_{filename}"

            test_path = self.project_root / Path(*parts)
        else:
            # Fallback: put in tests/ directory
            test_path = self.project_root / "tests" / f"test_{target_path.name}"

        # Create test directory
        test_path.parent.mkdir(parents=True, exist_ok=True)

        # Generate basic test structure
        test_content = self._generate_test_content(
            target_path,
            code,
            subagent_name,
        )

        # Write test file
        with open(test_path, "w") as f:
            f.write(test_content)

        self.logger.info("test_generated", path=str(test_path))

        return test_path

    def _generate_test_content(
        self,
        target_path: Path,
        code: str,
        subagent_name: str | None = None,
    ) -> str:
        """
        Generate test file content.

        Args:
            target_path: Path to code file
            code: Code content
            subagent_name: Subagent name for context

        Returns:
            Test file content
        """
        # Extract module path for import
        relative_path = target_path.relative_to(self.project_root)
        module_parts = list(relative_path.parts)

        # Remove .py extension
        module_parts[-1] = module_parts[-1].replace(".py", "")

        # Build import path
        import_path = ".".join(module_parts)

        # Extract class/function names from code
        classes = re.findall(r"class\s+(\w+)", code)
        functions = re.findall(r"(?:async\s+)?def\s+(\w+)", code)

        # Generate test content
        content = '"""\n'
        if subagent_name:
            content += f"Tests for {subagent_name} skill implementation.\n"
        else:
            content += "Tests for extracted skill implementation.\n"
        content += '"""\n\n'
        content += "import pytest\n\n"

        # Add imports for detected classes/functions (only if there are any)
        public_functions = [f for f in functions if not f.startswith("_")]
        if classes or public_functions:
            content += f"from {import_path} import (\n"
            for cls in classes:
                content += f"    {cls},\n"
            for func in public_functions:
                content += f"    {func},\n"
            content += ")\n\n"

        # Generate test class for each detected class
        for cls in classes:
            content += f"\n\nclass Test{cls}:\n"
            content += f'    """Tests for {cls}."""\n\n'
            content += "    @pytest.mark.asyncio\n"
            content += f"    async def test_{cls.lower()}_creation(self):\n"
            content += f'        """Should create {cls} instance."""\n'
            content += f"        instance = {cls}()\n"
            content += "        assert instance is not None\n"

        # Generate test functions for each detected function
        for func in functions:
            if not func.startswith("_"):  # Skip private functions
                content += f"\n\n@pytest.mark.asyncio\n"
                content += f"async def test_{func}():\n"
                content += f'    """Should test {func} function."""\n'
                content += "    # TODO: Implement test\n"
                content += "    pass\n"

        # If no classes/functions detected, add placeholder
        if not classes and not functions:
            content += "\n\ndef test_placeholder():\n"
            content += '    """Placeholder test."""\n'
            content += "    # TODO: Add tests for extracted implementation\n"
            content += "    pass\n"

        return content
