# AIM/src/aim/teacher/code_generator.py
"""Code generator for applying patterns to subagents."""

import ast
import re
from typing import Any

from src.aim.teacher.pattern_extractor import ExtractedPattern


class CodeGenerator:
    """Generate code to apply patterns to subagents."""

    def add_imports(self, code: str, pattern: ExtractedPattern) -> str:
        """
        Add imports from pattern to code.

        Args:
            code: Original code
            pattern: Pattern with imports

        Returns:
            Updated code with new imports
        """
        lines = code.split("\n")

        # Find last import line
        last_import_idx = -1
        for i, line in enumerate(lines):
            if line.strip().startswith(("import ", "from ")):
                last_import_idx = i

        # Add new imports after last import
        if last_import_idx >= 0:
            for imp in pattern.imports:
                if imp not in code:
                    lines.insert(last_import_idx + 1, imp)
                    last_import_idx += 1
        else:
            # No imports yet, add at top
            for imp in reversed(pattern.imports):
                if imp not in code:
                    lines.insert(0, imp)
            lines.insert(len(pattern.imports), "")  # Blank line

        return "\n".join(lines)

    def add_to_init(self, code: str, pattern: ExtractedPattern) -> str:
        """
        Add pattern code to __init__ method.

        Args:
            code: Original code
            pattern: Pattern with code to add

        Returns:
            Updated code with pattern in __init__
        """
        lines = code.split("\n")

        # Find __init__ method
        init_start = -1
        init_indent = 0
        for i, line in enumerate(lines):
            if "def __init__" in line:
                init_start = i
                init_indent = len(line) - len(line.lstrip())
                break

        if init_start < 0:
            return code  # No __init__ found

        # Find last line of __init__ (before next method or class end)
        init_end = init_start + 1
        for i in range(init_start + 1, len(lines)):
            line = lines[i]
            if line.strip() and not line.startswith(" " * (init_indent + 4)):
                init_end = i
                break
            if line.strip():
                init_end = i + 1

        # Add pattern code before init_end
        pattern_lines = pattern.code.strip().split("\n")
        indent = " " * (init_indent + 8)  # Double indent for method body

        for line in reversed(pattern_lines):
            if line.strip():
                lines.insert(init_end, indent + line.strip())

        return "\n".join(lines)

    def add_decorator(self, code: str, method_name: str, decorator: str) -> str:
        """
        Add decorator to a method.

        Args:
            code: Original code
            method_name: Method to decorate
            decorator: Decorator to add

        Returns:
            Updated code with decorator
        """
        lines = code.split("\n")

        # Find method
        for i, line in enumerate(lines):
            if f"def {method_name}" in line:
                # Get indent
                indent = len(line) - len(line.lstrip())

                # Add decorator above method
                lines.insert(i, " " * indent + decorator)
                break

        return "\n".join(lines)
