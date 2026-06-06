# AIM/src/aim/teacher/gap_detector.py
"""Gap detector for comparing our code vs GitHub best practices."""

from dataclasses import dataclass
from enum import Enum

from src.aim.teacher.code_analyzer import CodeAnalyzer


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
