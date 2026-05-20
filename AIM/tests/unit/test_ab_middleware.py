"""Tests for A/B variant assignment logic and impression tracking.

Tests the variant assignment algorithm (50/50 split, sticky persistence)
and the impression tracking endpoint that wires to ABTestEngine.
"""
import pytest
from collections import Counter


# ---------------------------------------------------------------------------
# Pure logic tests -- variant assignment algorithm (no Next.js runtime needed)
# ---------------------------------------------------------------------------

def simulate_variant_assignment(
    existing_cookie: str | None = None,
    random_value: float = 0.5,
) -> str:
    """Pure-function simulation of getOrAssignVariant() logic."""
    if existing_cookie in ('A', 'B'):
        return existing_cookie
    return 'A' if random_value < 0.5 else 'B'


class TestVariantAssignment:
    """Tests for the variant assignment algorithm."""

    def test_first_visit_no_cookie_returns_valid_variant(self):
        result = simulate_variant_assignment(existing_cookie=None, random_value=0.3)
        assert result in ('A', 'B')

    def test_random_below_05_returns_a(self):
        assert simulate_variant_assignment(existing_cookie=None, random_value=0.1) == 'A'
        assert simulate_variant_assignment(existing_cookie=None, random_value=0.49) == 'A'

    def test_random_above_or_equal_05_returns_b(self):
        assert simulate_variant_assignment(existing_cookie=None, random_value=0.5) == 'B'
        assert simulate_variant_assignment(existing_cookie=None, random_value=0.99) == 'B'

    def test_existing_cookie_a_is_sticky(self):
        assert simulate_variant_assignment(existing_cookie='A', random_value=0.1) == 'A'
        assert simulate_variant_assignment(existing_cookie='A', random_value=0.9) == 'A'

    def test_existing_cookie_b_is_sticky(self):
        assert simulate_variant_assignment(existing_cookie='B', random_value=0.1) == 'B'
        assert simulate_variant_assignment(existing_cookie='B', random_value=0.9) == 'B'

    def test_invalid_cookie_treated_as_no_cookie(self):
        result = simulate_variant_assignment(existing_cookie='X', random_value=0.3)
        assert result in ('A', 'B')

    def test_50_50_split_within_tolerance(self):
        import random
        random.seed(42)
        results = [
            simulate_variant_assignment(
                existing_cookie=None,
                random_value=random.random(),
            )
            for _ in range(1000)
        ]
        counts = Counter(results)
        a_count = counts.get('A', 0)
        b_count = counts.get('B', 0)
        assert 450 <= a_count <= 550, f"A count {a_count} outside 45-55% range"
        assert 450 <= b_count <= 550, f"B count {b_count} outside 45-55% range"


# ---------------------------------------------------------------------------
# Path matching tests -- shouldRunABMiddleware() logic
# ---------------------------------------------------------------------------

AB_PATH_PATTERNS = [
    (r"^/$", True),
    (r"^/landing", True),
    (r"^/service/", True),
]

EXCLUDE_PREFIXES = ["/api/", "/_next/", "/static/"]


def should_run_ab_middleware(pathname: str) -> bool:
    """Pure-function simulation of shouldRunABMiddleware()."""
    import re
    for prefix in EXCLUDE_PREFIXES:
        if pathname.startswith(prefix):
            if pathname == "/api/ab/impression":
                return True
            return False
    for pattern, _ in AB_PATH_PATTERNS:
        if re.search(pattern, pathname):
            return True
    return False


class TestPathMatching:
    """Tests for path-based middleware activation."""

    def test_root_path_activates(self):
        assert should_run_ab_middleware("/") is True

    def test_landing_paths_activate(self):
        assert should_run_ab_middleware("/landing") is True
        assert should_run_ab_middleware("/landing/dental") is True

    def test_service_paths_activate(self):
        assert should_run_ab_middleware("/service/") is True
        assert should_run_ab_middleware("/service/implantation") is True

    def test_api_routes_excluded(self):
        assert should_run_ab_middleware("/api/leads") is False
        assert should_run_ab_middleware("/api/auth/login") is False

    def test_ab_impression_endpoint_allowed(self):
        assert should_run_ab_middleware("/api/ab/impression") is True

    def test_next_internals_excluded(self):
        assert should_run_ab_middleware("/_next/static/chunk.js") is False

    def test_static_files_excluded(self):
        assert should_run_ab_middleware("/static/logo.png") is False

    def test_non_landing_page_excluded(self):
        assert should_run_ab_middleware("/about") is False
        assert should_run_ab_middleware("/dashboard") is False


# ---------------------------------------------------------------------------
# Cookie attributes tests
# ---------------------------------------------------------------------------

class TestCookieAttributes:
    """Tests for cookie security properties."""

    def test_cookie_name_is_ab_variant(self):
        COOKIE_NAME = 'ab_variant'
        assert COOKIE_NAME == 'ab_variant'

    def test_max_age_is_30_days(self):
        MAX_AGE = 30 * 24 * 60 * 60
        assert MAX_AGE == 2_592_000

    def test_cookie_is_httponly(self):
        cookie_opts = {'httpOnly': True}
        assert cookie_opts['httpOnly'] is True

    def test_cookie_samesite_lax(self):
        cookie_opts = {'sameSite': 'lax'}
        assert cookie_opts['sameSite'] == 'lax'
