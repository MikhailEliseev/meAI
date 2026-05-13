# Teacher Agent Audit - Part 3: Upgrade Engine

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build upgrade engine that applies GitHub patterns to old subagents

**Architecture:** Read gap report → Extract patterns from GitHub → Generate upgrade code → Apply to subagent

**Tech Stack:** Python 3.11+, AST manipulation, code generation, pytest

**Prerequisites:** Part 1 & 2 completed (inventory, audit engine)

---

## Task 8: Create Pattern Extractor

**Files:**
- Create: `AIM/src/aim/teacher/pattern_extractor.py`
- Create: `AIM/tests/teacher/test_pattern_extractor.py`

- [ ] **Step 1: Write failing test**

```python
# AIM/tests/teacher/test_pattern_extractor.py
import pytest
from pathlib import Path
from AIM.src.aim.teacher.pattern_extractor import PatternExtractor, ExtractedPattern


def test_extract_circuit_breaker():
    """Test extracting circuit breaker pattern."""
    code = """
from pybreaker import CircuitBreaker

class Client:
    def __init__(self):
        self.breaker = CircuitBreaker(
            fail_max=5,
            reset_timeout=60,
        )
    
    def fetch(self):
        return self.breaker.call(self._do_fetch)
"""
    
    extractor = PatternExtractor()
    pattern = extractor.extract("circuit_breaker", code)
    
    assert pattern is not None
    assert pattern.name == "circuit_breaker"
    assert "fail_max=5" in pattern.code
    assert "pybreaker" in pattern.imports


def test_extract_retry():
    """Test extracting retry pattern."""
    code = """
from tenacity import retry, stop_after_attempt, wait_exponential

class Client:
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, max=30),
    )
    def fetch(self):
        return requests.get(url)
"""
    
    extractor = PatternExtractor()
    pattern = extractor.extract("retry", code)
    
    assert pattern is not None
    assert pattern.name == "retry"
    assert "tenacity" in pattern.imports
    assert "stop_after_attempt" in pattern.code
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest AIM/tests/teacher/test_pattern_extractor.py -v`
Expected: FAIL with "No module named 'AIM.src.aim.teacher.pattern_extractor'"

- [ ] **Step 3: Write minimal implementation**

```python
# AIM/src/aim/teacher/pattern_extractor.py
"""Pattern extractor from GitHub repositories."""

import ast
import re
from dataclasses import dataclass
from pathlib import Path


@dataclass
class ExtractedPattern:
    """Extracted code pattern."""
    name: str
    code: str
    imports: list[str]
    parameters: dict[str, str]
    description: str


class PatternExtractor:
    """Extract code patterns from GitHub repositories."""
    
    def extract(self, pattern_name: str, code: str) -> ExtractedPattern | None:
        """
        Extract a specific pattern from code.
        
        Args:
            pattern_name: Pattern to extract (e.g., "circuit_breaker")
            code: Source code to extract from
        
        Returns:
            ExtractedPattern or None if not found
        """
        if pattern_name == "circuit_breaker":
            return self._extract_circuit_breaker(code)
        elif pattern_name == "retry":
            return self._extract_retry(code)
        elif pattern_name == "rate_limiting":
            return self._extract_rate_limiting(code)
        elif pattern_name == "caching":
            return self._extract_caching(code)
        else:
            return None
    
    def _extract_circuit_breaker(self, code: str) -> ExtractedPattern | None:
        """Extract circuit breaker pattern."""
        if "CircuitBreaker" not in code:
            return None
        
        # Extract imports
        imports = []
        if "from pybreaker import" in code:
            imports.append("from pybreaker import CircuitBreaker")
        elif "import pybreaker" in code:
            imports.append("import pybreaker")
        
        # Extract parameters
        params = {}
        fail_max_match = re.search(r"fail_max\s*=\s*(\d+)", code)
        if fail_max_match:
            params["fail_max"] = fail_max_match.group(1)
        
        reset_timeout_match = re.search(r"reset_timeout\s*=\s*(\d+)", code)
        if reset_timeout_match:
            params["reset_timeout"] = reset_timeout_match.group(1)
        
        # Extract code snippet
        snippet = """
self.circuit_breaker = CircuitBreaker(
    fail_max={fail_max},
    reset_timeout={reset_timeout},
)
""".format(
            fail_max=params.get("fail_max", "5"),
            reset_timeout=params.get("reset_timeout", "60"),
        )
        
        return ExtractedPattern(
            name="circuit_breaker",
            code=snippet,
            imports=imports,
            parameters=params,
            description="Circuit breaker with fail_max and reset_timeout",
        )
    
    def _extract_retry(self, code: str) -> ExtractedPattern | None:
        """Extract retry pattern."""
        if "retry" not in code.lower():
            return None
        
        # Extract imports
        imports = []
        if "from tenacity import" in code:
            match = re.search(r"from tenacity import ([^\n]+)", code)
            if match:
                imports.append(f"from tenacity import {match.group(1)}")
        
        # Extract parameters
        params = {}
        attempts_match = re.search(r"stop_after_attempt\((\d+)\)", code)
        if attempts_match:
            params["max_attempts"] = attempts_match.group(1)
        
        # Extract code snippet
        snippet = """
@retry(
    stop=stop_after_attempt({max_attempts}),
    wait=wait_exponential(multiplier=1, max=30),
)
""".format(max_attempts=params.get("max_attempts", "3"))
        
        return ExtractedPattern(
            name="retry",
            code=snippet,
            imports=imports,
            parameters=params,
            description="Retry with exponential backoff",
        )
    
    def _extract_rate_limiting(self, code: str) -> ExtractedPattern | None:
        """Extract rate limiting pattern."""
        if "rate" not in code.lower() and "limiter" not in code.lower():
            return None
        
        imports = ["from aiolimiter import AsyncLimiter"]
        
        snippet = """
self.rate_limiter = AsyncLimiter(
    max_rate=10,
    time_period=1.0,
)
"""
        
        return ExtractedPattern(
            name="rate_limiting",
            code=snippet,
            imports=imports,
            parameters={"max_rate": "10", "time_period": "1.0"},
            description="Rate limiting with token bucket",
        )
    
    def _extract_caching(self, code: str) -> ExtractedPattern | None:
        """Extract caching pattern."""
        if "cache" not in code.lower():
            return None
        
        imports = ["from aiocache import Cache"]
        
        snippet = """
self.cache = Cache(Cache.MEMORY)
self.cache_ttl = 3600  # 1 hour
"""
        
        return ExtractedPattern(
            name="caching",
            code=snippet,
            imports=imports,
            parameters={"ttl": "3600"},
            description="In-memory caching with TTL",
        )
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest AIM/tests/teacher/test_pattern_extractor.py -v`
Expected: PASS (2 tests)

- [ ] **Step 5: Commit**

```bash
git add AIM/src/aim/teacher/pattern_extractor.py AIM/tests/teacher/test_pattern_extractor.py
git commit -m "feat(teacher): add pattern extractor from GitHub code"
```

---

## Task 9: Create Code Generator

**Files:**
- Create: `AIM/src/aim/teacher/code_generator.py`
- Create: `AIM/tests/teacher/test_code_generator.py`

- [ ] **Step 1: Write failing test**

```python
# AIM/tests/teacher/test_code_generator.py
import pytest
from AIM.src.aim.teacher.code_generator import CodeGenerator
from AIM.src.aim.teacher.pattern_extractor import ExtractedPattern


def test_add_imports():
    """Test adding imports to code."""
    original = """
import requests

class Client:
    pass
"""
    
    pattern = ExtractedPattern(
        name="circuit_breaker",
        code="",
        imports=["from pybreaker import CircuitBreaker"],
        parameters={},
        description="",
    )
    
    generator = CodeGenerator()
    updated = generator.add_imports(original, pattern)
    
    assert "from pybreaker import CircuitBreaker" in updated
    assert "import requests" in updated


def test_add_to_init():
    """Test adding code to __init__ method."""
    original = """
class Client:
    def __init__(self):
        self.url = "http://example.com"
"""
    
    pattern = ExtractedPattern(
        name="circuit_breaker",
        code="self.breaker = CircuitBreaker(fail_max=5)",
        imports=[],
        parameters={},
        description="",
    )
    
    generator = CodeGenerator()
    updated = generator.add_to_init(original, pattern)
    
    assert "self.breaker = CircuitBreaker(fail_max=5)" in updated
    assert "self.url" in updated
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest AIM/tests/teacher/test_code_generator.py -v`
Expected: FAIL with "No module named 'AIM.src.aim.teacher.code_generator'"

- [ ] **Step 3: Write minimal implementation**

```python
# AIM/src/aim/teacher/code_generator.py
"""Code generator for applying patterns to subagents."""

import ast
import re
from typing import Any

from AIM.src.aim.teacher.pattern_extractor import ExtractedPattern


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
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest AIM/tests/teacher/test_code_generator.py -v`
Expected: PASS (2 tests)

- [ ] **Step 5: Commit**

```bash
git add AIM/src/aim/teacher/code_generator.py AIM/tests/teacher/test_code_generator.py
git commit -m "feat(teacher): add code generator for applying patterns"
```

---

## Task 10: Create Upgrade Applier

**Files:**
- Create: `AIM/src/aim/teacher/upgrade_applier.py`
- Create: `AIM/tests/teacher/test_upgrade_applier.py`

- [ ] **Step 1: Write failing test**

```python
# AIM/tests/teacher/test_upgrade_applier.py
import pytest
import tempfile
from pathlib import Path
from AIM.src.aim.teacher.upgrade_applier import UpgradeApplier
from AIM.src.aim.teacher.gap_detector import Gap, GapSeverity


def test_apply_upgrade():
    """Test applying upgrade to subagent."""
    original_code = """
import requests

class Client:
    def __init__(self):
        self.url = "http://example.com"
    
    def fetch(self):
        return requests.get(self.url)
"""
    
    gaps = [
        Gap(
            pattern="circuit_breaker",
            severity=GapSeverity.CRITICAL,
            description="Missing circuit breaker",
            recommendation="Add pybreaker",
        ),
    ]
    
    github_code = """
from pybreaker import CircuitBreaker

class Client:
    def __init__(self):
        self.breaker = CircuitBreaker(fail_max=5)
"""
    
    applier = UpgradeApplier()
    
    with tempfile.TemporaryDirectory() as tmpdir:
        file_path = Path(tmpdir) / "client.py"
        file_path.write_text(original_code)
        
        result = applier.apply(file_path, gaps, github_code)
        
        assert result.success
        updated = file_path.read_text()
        assert "from pybreaker import CircuitBreaker" in updated
        assert "self.breaker" in updated


def test_backup_original():
    """Test backing up original file."""
    applier = UpgradeApplier()
    
    with tempfile.TemporaryDirectory() as tmpdir:
        file_path = Path(tmpdir) / "test.py"
        file_path.write_text("original")
        
        backup_path = applier.backup(file_path)
        
        assert backup_path.exists()
        assert backup_path.read_text() == "original"
        assert ".backup" in str(backup_path)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest AIM/tests/teacher/test_upgrade_applier.py -v`
Expected: FAIL with "No module named 'AIM.src.aim.teacher.upgrade_applier'"

- [ ] **Step 3: Write minimal implementation**

```python
# AIM/src/aim/teacher/upgrade_applier.py
"""Upgrade applier for subagents."""

import shutil
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from AIM.src.aim.teacher.code_generator import CodeGenerator
from AIM.src.aim.teacher.gap_detector import Gap
from AIM.src.aim.teacher.pattern_extractor import PatternExtractor


@dataclass
class UpgradeResult:
    """Result of upgrade operation."""
    success: bool
    file_path: Path
    backup_path: Path | None = None
    patterns_applied: list[str] = None
    error: str | None = None


class UpgradeApplier:
    """Apply upgrades to subagent files."""
    
    def __init__(self):
        self.extractor = PatternExtractor()
        self.generator = CodeGenerator()
    
    def apply(
        self,
        file_path: Path,
        gaps: list[Gap],
        github_code: str,
    ) -> UpgradeResult:
        """
        Apply upgrades to a subagent file.
        
        Args:
            file_path: Path to subagent file
            gaps: List of gaps to fix
            github_code: GitHub code to extract patterns from
        
        Returns:
            UpgradeResult with success status
        """
        try:
            # Backup original
            backup_path = self.backup(file_path)
            
            # Read original code
            code = file_path.read_text()
            
            # Apply each gap fix
            patterns_applied = []
            for gap in gaps:
                # Extract pattern from GitHub code
                pattern = self.extractor.extract(gap.pattern, github_code)
                if not pattern:
                    continue
                
                # Add imports
                code = self.generator.add_imports(code, pattern)
                
                # Add to __init__
                code = self.generator.add_to_init(code, pattern)
                
                patterns_applied.append(gap.pattern)
            
            # Write updated code
            file_path.write_text(code)
            
            return UpgradeResult(
                success=True,
                file_path=file_path,
                backup_path=backup_path,
                patterns_applied=patterns_applied,
            )
        
        except Exception as e:
            return UpgradeResult(
                success=False,
                file_path=file_path,
                error=str(e),
            )
    
    def backup(self, file_path: Path) -> Path:
        """
        Create backup of file.
        
        Args:
            file_path: File to backup
        
        Returns:
            Path to backup file
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = file_path.with_suffix(f".backup.{timestamp}{file_path.suffix}")
        shutil.copy2(file_path, backup_path)
        return backup_path
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest AIM/tests/teacher/test_upgrade_applier.py -v`
Expected: PASS (2 tests)

- [ ] **Step 5: Commit**

```bash
git add AIM/src/aim/teacher/upgrade_applier.py AIM/tests/teacher/test_upgrade_applier.py
git commit -m "feat(teacher): add upgrade applier for subagents"
```

---

**Part 3 Complete!** Continue with Part 4: Execution (2026-05-13-teacher-agent-audit-part4.md)
