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
