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
    assert any("pybreaker" in imp for imp in pattern.imports)


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
    assert any("tenacity" in imp for imp in pattern.imports)
    assert "stop_after_attempt" in pattern.code
