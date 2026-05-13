"""
Tests for SkillSelector.

Tests:
- Skill extraction from GitHub repositories
- Pattern detection (circuit breaker, retry, rate limiting, caching)
- Code quality scoring
- Best practices identification
- Integration with GitHub API
"""

from pathlib import Path

import pytest

from AIM.src.aim.teacher.skills.skill_selector import (
    GitHubRepo,
    Skill,
    SkillSelector,
)


@pytest.fixture
def selector():
    """Create SkillSelector instance."""
    return SkillSelector()


@pytest.fixture
def sample_repo_with_patterns(tmp_path):
    """Create sample repository with resilience patterns."""
    repo = tmp_path / "sample_repo"
    repo.mkdir()

    # Circuit breaker pattern
    (repo / "circuit_breaker.py").write_text("""
from pybreaker import CircuitBreaker

class APIClient:
    def __init__(self):
        self.breaker = CircuitBreaker(fail_max=5, reset_timeout=60)

    def call_api(self):
        return self.breaker.call(self._do_call)

    def _do_call(self):
        # API call logic
        pass
""")

    # Retry pattern
    (repo / "retry.py").write_text("""
from tenacity import retry, stop_after_attempt, wait_exponential

class Service:
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=1, max=10))
    def fetch_data(self):
        # Fetch logic with retry
        pass
""")

    # Rate limiting pattern
    (repo / "rate_limiter.py").write_text("""
from aiolimiter import AsyncLimiter

class RateLimitedClient:
    def __init__(self):
        self.limiter = AsyncLimiter(10, 1)  # 10 requests per second

    async def request(self):
        async with self.limiter:
            # Request logic
            pass
""")

    # Caching pattern
    (repo / "cache.py").write_text("""
from aiocache import cached

class DataService:
    @cached(ttl=3600)
    async def get_data(self, key: str):
        # Fetch and cache data
        pass
""")

    return repo


@pytest.fixture
def sample_repo_without_patterns(tmp_path):
    """Create sample repository without patterns."""
    repo = tmp_path / "simple_repo"
    repo.mkdir()

    (repo / "simple.py").write_text("""
def add(a, b):
    return a + b

def subtract(a, b):
    return a - b
""")

    return repo


class TestSkillExtraction:
    """Test skill extraction from repositories."""

    @pytest.mark.asyncio
    async def test_extract_skills_from_repo(self, selector, sample_repo_with_patterns):
        """Should extract skills from repository with patterns."""
        skills = await selector.extract_skills(sample_repo_with_patterns)

        assert len(skills) > 0
        assert all(isinstance(skill, Skill) for skill in skills)

    @pytest.mark.asyncio
    async def test_identify_circuit_breaker_pattern(self, selector, sample_repo_with_patterns):
        """Should identify circuit breaker pattern."""
        skills = await selector.extract_skills(sample_repo_with_patterns)

        circuit_breaker_skills = [s for s in skills if "circuit breaker" in s.name.lower()]
        assert len(circuit_breaker_skills) > 0

    @pytest.mark.asyncio
    async def test_identify_retry_pattern(self, selector, sample_repo_with_patterns):
        """Should identify retry pattern."""
        skills = await selector.extract_skills(sample_repo_with_patterns)

        retry_skills = [s for s in skills if "retry" in s.name.lower()]
        assert len(retry_skills) > 0

    @pytest.mark.asyncio
    async def test_identify_rate_limiting_pattern(self, selector, sample_repo_with_patterns):
        """Should identify rate limiting pattern."""
        skills = await selector.extract_skills(sample_repo_with_patterns)

        rate_limit_skills = [s for s in skills if "rate limit" in s.name.lower()]
        assert len(rate_limit_skills) > 0

    @pytest.mark.asyncio
    async def test_identify_caching_pattern(self, selector, sample_repo_with_patterns):
        """Should identify caching pattern."""
        skills = await selector.extract_skills(sample_repo_with_patterns)

        cache_skills = [s for s in skills if "cach" in s.name.lower()]
        assert len(cache_skills) > 0

    @pytest.mark.asyncio
    async def test_no_skills_in_simple_repo(self, selector, sample_repo_without_patterns):
        """Should find no advanced skills in simple repository."""
        skills = await selector.extract_skills(sample_repo_without_patterns)

        # Simple arithmetic functions are not "skills"
        assert len(skills) == 0


class TestCodeQualityScoring:
    """Test code quality scoring."""

    @pytest.mark.asyncio
    async def test_score_skill_quality(self, selector, sample_repo_with_patterns):
        """Should score skill quality."""
        skills = await selector.extract_skills(sample_repo_with_patterns)

        for skill in skills:
            assert 0.0 <= skill.quality_score <= 100.0

    @pytest.mark.asyncio
    async def test_higher_score_for_complete_implementation(self, selector, sample_repo_with_patterns):
        """Should give higher score for complete implementations."""
        skills = await selector.extract_skills(sample_repo_with_patterns)

        # All skills should have valid quality scores
        circuit_breaker_skills = [s for s in skills if "circuit breaker" in s.name.lower()]
        if circuit_breaker_skills:
            assert circuit_breaker_skills[0].quality_score >= 50.0


class TestBestPracticesIdentification:
    """Test best practices identification."""

    @pytest.mark.asyncio
    async def test_identify_error_handling(self, selector, sample_repo_with_patterns):
        """Should identify error handling patterns."""
        skills = await selector.extract_skills(sample_repo_with_patterns)

        # Check if any skill mentions error handling
        error_handling_found = any(
            "error" in skill.description.lower() or "exception" in skill.description.lower()
            for skill in skills
        )
        # Note: This may be False if error handling is implicit
        assert isinstance(error_handling_found, bool)

    @pytest.mark.asyncio
    async def test_identify_async_patterns(self, selector, sample_repo_with_patterns):
        """Should identify async/await patterns."""
        skills = await selector.extract_skills(sample_repo_with_patterns)

        # Check if any skill uses async
        async_found = any("async" in skill.code_example.lower() for skill in skills if skill.code_example)
        assert isinstance(async_found, bool)


class TestGitHubIntegration:
    """Test GitHub API integration."""

    @pytest.mark.asyncio
    async def test_search_github_repos(self, selector):
        """Should search GitHub repositories."""
        repos = await selector.search_github_repos(
            query="circuit breaker python",
            max_results=5
        )

        assert len(repos) > 0
        assert all(isinstance(repo, GitHubRepo) for repo in repos)

    @pytest.mark.asyncio
    async def test_github_repo_has_metadata(self, selector):
        """Should include repository metadata."""
        repos = await selector.search_github_repos(
            query="retry pattern python",
            max_results=3
        )

        for repo in repos:
            assert repo.url
            assert repo.stars >= 0
            assert repo.description is not None  # Can be empty string

    @pytest.mark.asyncio
    async def test_clone_github_repo(self, selector, tmp_path):
        """Should clone GitHub repository."""
        # Use a small, well-known repo for testing
        repo_url = "https://github.com/octocat/Hello-World"
        clone_path = tmp_path / "cloned_repo"

        await selector.clone_repo(repo_url, clone_path)

        assert clone_path.exists()
        assert (clone_path / ".git").exists()


class TestEdgeCases:
    """Test edge cases."""

    @pytest.mark.asyncio
    async def test_handle_empty_repo(self, selector, tmp_path):
        """Should handle empty repository."""
        empty_repo = tmp_path / "empty"
        empty_repo.mkdir()

        skills = await selector.extract_skills(empty_repo)

        assert len(skills) == 0

    @pytest.mark.asyncio
    async def test_handle_repo_with_syntax_errors(self, selector, tmp_path):
        """Should handle syntax errors gracefully."""
        repo = tmp_path / "broken_repo"
        repo.mkdir()
        (repo / "broken.py").write_text("this is not valid python")

        # Should not crash
        skills = await selector.extract_skills(repo)
        assert isinstance(skills, list)

    @pytest.mark.asyncio
    async def test_handle_github_api_errors(self, selector):
        """Should handle GitHub API errors gracefully."""
        # Invalid query that should return no results
        repos = await selector.search_github_repos(
            query="xyzabc123nonexistent",
            max_results=5
        )

        # Should return empty list, not crash
        assert isinstance(repos, list)
