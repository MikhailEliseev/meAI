# Teacher Agent Audit - Part 2: Audit Engine

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build audit engine that analyzes subagents and identifies gaps vs GitHub best practices

**Architecture:** Read subagent code → Find GitHub repos → Clone & analyze → Generate gap report

**Tech Stack:** Python 3.11+, AST parsing, git, pytest

**Prerequisites:** Part 1 completed (inventory, finder, cloner)

---

## Task 5: Create Code Analyzer

**Files:**
- Create: `AIM/src/aim/teacher/code_analyzer.py`
- Create: `AIM/tests/teacher/test_code_analyzer.py`

- [ ] **Step 1: Write failing test**

```python
# AIM/tests/teacher/test_code_analyzer.py
import pytest
from pathlib import Path
from AIM.src.aim.teacher.code_analyzer import CodeAnalyzer


def test_extract_imports():
    """Test extracting imports from Python file."""
    code = """
import httpx
from pybreaker import CircuitBreaker
import trafilatura
"""
    
    analyzer = CodeAnalyzer()
    imports = analyzer.extract_imports(code)
    
    assert "httpx" in imports
    assert "pybreaker" in imports
    assert "trafilatura" in imports


def test_detect_patterns():
    """Test detecting code patterns."""
    code = """
class MyClient:
    def __init__(self):
        self.breaker = CircuitBreaker(fail_max=5)
        self.cache = {}
    
    @retry(max_attempts=3)
    def fetch(self):
        pass
"""
    
    analyzer = CodeAnalyzer()
    patterns = analyzer.detect_patterns(code)
    
    assert "circuit_breaker" in patterns
    assert "retry" in patterns
    assert "caching" in patterns


def test_count_complexity():
    """Test code complexity metrics."""
    code = """
def simple():
    return 1

def complex(x):
    if x > 0:
        for i in range(x):
            if i % 2 == 0:
                return i
    return 0
"""
    
    analyzer = CodeAnalyzer()
    metrics = analyzer.count_complexity(code)
    
    assert metrics["functions"] == 2
    assert metrics["avg_complexity"] > 1
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest AIM/tests/teacher/test_code_analyzer.py -v`
Expected: FAIL with "No module named 'AIM.src.aim.teacher.code_analyzer'"

- [ ] **Step 3: Write minimal implementation**

```python
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
            List of imported module names
        """
        imports = []
        
        try:
            tree = ast.parse(code)
            
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        imports.append(alias.name.split(".")[0])
                elif isinstance(node, ast.ImportFrom):
                    if node.module:
                        imports.append(node.module.split(".")[0])
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
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest AIM/tests/teacher/test_code_analyzer.py -v`
Expected: PASS (3 tests)

- [ ] **Step 5: Commit**

```bash
git add AIM/src/aim/teacher/code_analyzer.py AIM/tests/teacher/test_code_analyzer.py
git commit -m "feat(teacher): add code analyzer for pattern detection"
```

---

## Task 6: Create Gap Detector

**Files:**
- Create: `AIM/src/aim/teacher/gap_detector.py`
- Create: `AIM/tests/teacher/test_gap_detector.py`

- [ ] **Step 1: Write failing test**

```python
# AIM/tests/teacher/test_gap_detector.py
import pytest
from AIM.src.aim.teacher.gap_detector import GapDetector, Gap, GapSeverity


def test_detect_missing_patterns():
    """Test detecting missing patterns."""
    our_code = """
class Client:
    def fetch(self):
        return requests.get(url)
"""
    
    github_code = """
class Client:
    def __init__(self):
        self.breaker = CircuitBreaker(fail_max=5)
    
    @retry(max_attempts=3)
    def fetch(self):
        return requests.get(url)
"""
    
    detector = GapDetector()
    gaps = detector.detect(our_code, github_code)
    
    assert len(gaps) > 0
    assert any(g.pattern == "circuit_breaker" for g in gaps)
    assert any(g.pattern == "retry" for g in gaps)


def test_gap_severity():
    """Test gap severity classification."""
    detector = GapDetector()
    
    # Critical: no error handling
    gap1 = Gap(
        pattern="circuit_breaker",
        severity=GapSeverity.CRITICAL,
        description="Missing circuit breaker",
    )
    
    # High: no retry
    gap2 = Gap(
        pattern="retry",
        severity=GapSeverity.HIGH,
        description="Missing retry logic",
    )
    
    assert gap1.severity == GapSeverity.CRITICAL
    assert gap2.severity == GapSeverity.HIGH
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest AIM/tests/teacher/test_gap_detector.py -v`
Expected: FAIL with "No module named 'AIM.src.aim.teacher.gap_detector'"

- [ ] **Step 3: Write minimal implementation**

```python
# AIM/src/aim/teacher/gap_detector.py
"""Gap detector for comparing our code vs GitHub best practices."""

from dataclasses import dataclass
from enum import Enum

from AIM.src.aim.teacher.code_analyzer import CodeAnalyzer


class GapSeverity(Enum):
    """Gap severity levels."""
    CRITICAL = "critical"  # Production-breaking (no error handling)
    HIGH = "high"          # Performance/reliability (no retry, caching)
    MEDIUM = "medium"      # Quality (no metrics, logging)
    LOW = "low"            # Nice-to-have (documentation)


@dataclass
class Gap:
    """Detected gap between our code and best practices."""
    pattern: str
    severity: GapSeverity
    description: str
    github_example: str | None = None
    recommendation: str | None = None


class GapDetector:
    """Detect gaps between our code and GitHub best practices."""
    
    # Pattern severity mapping
    PATTERN_SEVERITY = {
        "circuit_breaker": GapSeverity.CRITICAL,
        "retry": GapSeverity.HIGH,
        "rate_limiting": GapSeverity.HIGH,
        "caching": GapSeverity.MEDIUM,
        "metrics": GapSeverity.MEDIUM,
        "logging": GapSeverity.MEDIUM,
    }
    
    def __init__(self):
        self.analyzer = CodeAnalyzer()
    
    def detect(self, our_code: str, github_code: str) -> list[Gap]:
        """
        Detect gaps between our code and GitHub code.
        
        Args:
            our_code: Our subagent code
            github_code: GitHub repository code
        
        Returns:
            List of detected gaps
        """
        our_patterns = set(self.analyzer.detect_patterns(our_code))
        github_patterns = set(self.analyzer.detect_patterns(github_code))
        
        # Find missing patterns
        missing = github_patterns - our_patterns
        
        gaps = []
        for pattern in missing:
            severity = self.PATTERN_SEVERITY.get(pattern, GapSeverity.LOW)
            
            gap = Gap(
                pattern=pattern,
                severity=severity,
                description=f"Missing {pattern} pattern found in GitHub repo",
                recommendation=self._get_recommendation(pattern),
            )
            gaps.append(gap)
        
        # Sort by severity
        severity_order = {
            GapSeverity.CRITICAL: 0,
            GapSeverity.HIGH: 1,
            GapSeverity.MEDIUM: 2,
            GapSeverity.LOW: 3,
        }
        gaps.sort(key=lambda g: severity_order[g.severity])
        
        return gaps
    
    def _get_recommendation(self, pattern: str) -> str:
        """Get recommendation for implementing a pattern."""
        recommendations = {
            "circuit_breaker": "Add pybreaker with fail_max=5, reset_timeout=60s",
            "retry": "Add tenacity with exponential backoff (1s → 30s max)",
            "rate_limiting": "Add aiolimiter with token bucket (10 req/s)",
            "caching": "Add aiocache with 1-hour TTL",
            "metrics": "Add prometheus_client counters and gauges",
            "logging": "Add structlog with context",
        }
        return recommendations.get(pattern, f"Implement {pattern} pattern")
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest AIM/tests/teacher/test_gap_detector.py -v`
Expected: PASS (2 tests)

- [ ] **Step 5: Commit**

```bash
git add AIM/src/aim/teacher/gap_detector.py AIM/tests/teacher/test_gap_detector.py
git commit -m "feat(teacher): add gap detector for pattern comparison"
```

---

## Task 7: Create Audit Report Generator

**Files:**
- Create: `AIM/src/aim/teacher/audit_report.py`
- Create: `AIM/tests/teacher/test_audit_report.py`

- [ ] **Step 1: Write failing test**

```python
# AIM/tests/teacher/test_audit_report.py
import pytest
from pathlib import Path
from AIM.src.aim.teacher.audit_report import AuditReportGenerator, AuditResult
from AIM.src.aim.teacher.gap_detector import Gap, GapSeverity


def test_generate_report():
    """Test generating audit report."""
    gaps = [
        Gap(
            pattern="circuit_breaker",
            severity=GapSeverity.CRITICAL,
            description="Missing circuit breaker",
            recommendation="Add pybreaker",
        ),
        Gap(
            pattern="retry",
            severity=GapSeverity.HIGH,
            description="Missing retry logic",
            recommendation="Add tenacity",
        ),
    ]
    
    result = AuditResult(
        subagent_name="content_writer_agent",
        github_repos=["user/repo1", "user/repo2"],
        gaps=gaps,
        score=60.0,
    )
    
    generator = AuditReportGenerator()
    report = generator.generate(result)
    
    assert "content_writer_agent" in report
    assert "circuit_breaker" in report
    assert "CRITICAL" in report
    assert "60.0" in report


def test_save_report():
    """Test saving report to file."""
    result = AuditResult(
        subagent_name="test_agent",
        github_repos=[],
        gaps=[],
        score=100.0,
    )
    
    generator = AuditReportGenerator()
    
    import tempfile
    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = Path(tmpdir) / "report.md"
        generator.save(result, output_path)
        
        assert output_path.exists()
        content = output_path.read_text()
        assert "test_agent" in content
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest AIM/tests/teacher/test_audit_report.py -v`
Expected: FAIL with "No module named 'AIM.src.aim.teacher.audit_report'"

- [ ] **Step 3: Write minimal implementation**

```python
# AIM/src/aim/teacher/audit_report.py
"""Audit report generator."""

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from AIM.src.aim.teacher.gap_detector import Gap, GapSeverity


@dataclass
class AuditResult:
    """Result of subagent audit."""
    subagent_name: str
    github_repos: list[str]
    gaps: list[Gap]
    score: float  # 0-100, higher is better


class AuditReportGenerator:
    """Generate audit reports in markdown format."""
    
    def generate(self, result: AuditResult) -> str:
        """
        Generate audit report.
        
        Args:
            result: Audit result
        
        Returns:
            Markdown report
        """
        report = f"""# Audit Report: {result.subagent_name}

**Date:** {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}  
**Score:** {result.score:.1f}/100  
**Status:** {"✅ PASS" if result.score >= 80 else "⚠️ NEEDS IMPROVEMENT" if result.score >= 60 else "❌ FAIL"}

---

## GitHub Repositories Analyzed

"""
        
        if result.github_repos:
            for repo in result.github_repos:
                report += f"- {repo}\n"
        else:
            report += "- No repositories found\n"
        
        report += "\n---\n\n## Gaps Detected\n\n"
        
        if not result.gaps:
            report += "✅ No gaps detected! Subagent follows all best practices.\n"
        else:
            # Group by severity
            by_severity = {}
            for gap in result.gaps:
                severity = gap.severity.value
                if severity not in by_severity:
                    by_severity[severity] = []
                by_severity[severity].append(gap)
            
            # Critical
            if "critical" in by_severity:
                report += "### 🔴 CRITICAL (implement immediately)\n\n"
                for gap in by_severity["critical"]:
                    report += f"**{gap.pattern}**\n"
                    report += f"- {gap.description}\n"
                    report += f"- **Action:** {gap.recommendation}\n\n"
            
            # High
            if "high" in by_severity:
                report += "### 🟡 HIGH (plan for next sprint)\n\n"
                for gap in by_severity["high"]:
                    report += f"**{gap.pattern}**\n"
                    report += f"- {gap.description}\n"
                    report += f"- **Action:** {gap.recommendation}\n\n"
            
            # Medium
            if "medium" in by_severity:
                report += "### 🟢 MEDIUM (backlog)\n\n"
                for gap in by_severity["medium"]:
                    report += f"**{gap.pattern}**\n"
                    report += f"- {gap.description}\n"
                    report += f"- **Action:** {gap.recommendation}\n\n"
        
        report += "---\n\n"
        report += "**Generated by Teacher Agent**\n"
        
        return report
    
    def save(self, result: AuditResult, output_path: Path) -> None:
        """
        Save report to file.
        
        Args:
            result: Audit result
            output_path: Output file path
        """
        report = self.generate(result)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(report)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest AIM/tests/teacher/test_audit_report.py -v`
Expected: PASS (2 tests)

- [ ] **Step 5: Commit**

```bash
git add AIM/src/aim/teacher/audit_report.py AIM/tests/teacher/test_audit_report.py
git commit -m "feat(teacher): add audit report generator"
```

---

**Part 2 Complete!** Continue with Part 3: Upgrade Engine (2026-05-13-teacher-agent-audit-part3.md)
