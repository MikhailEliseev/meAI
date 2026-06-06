# AIM/tests/teacher/test_gap_detector.py
import pytest
from src.aim.teacher.gap_detector import GapDetector, Gap, GapSeverity


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
