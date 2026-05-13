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
