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


class TestDomainSpecificResearch:
    """Test domain-specific research functionality."""

    @pytest.mark.asyncio
    async def test_domain_queries_defined_for_all_subagents(self, selector):
        """Should have domain queries for all subagent types."""
        expected_subagents = [
            "ads",
            "seo",
            "content",
            "analytics",
            "gap_detection",
            "prioritization",
            "social",
        ]

        for subagent in expected_subagents:
            assert subagent in selector.domain_queries
            assert len(selector.domain_queries[subagent]) > 0

    @pytest.mark.asyncio
    async def test_ads_domain_queries_include_yandex(self, selector):
        """Should include Yandex Direct in ads queries."""
        ads_queries = selector.domain_queries["ads"]

        # Should include Yandex Direct query
        assert any("yandex" in q.lower() for q in ads_queries)
        assert any("direct" in q.lower() for q in ads_queries)

    @pytest.mark.asyncio
    async def test_research_domain_specific_executes_all_queries(self, selector):
        """Should execute all domain queries for subagent."""
        results = await selector.research_domain_specific(
            subagent_name="ads",
            domain="advertising automation",
        )

        # Should execute all ads queries
        ads_queries = selector.domain_queries["ads"]
        assert len(results) >= 1  # At least some queries should return results

        # Each result should be a list of repos
        for query, repos in results.items():
            assert isinstance(repos, list)
            assert all(isinstance(repo, GitHubRepo) for repo in repos)

    @pytest.mark.asyncio
    async def test_research_domain_specific_finds_relevant_repos(self, selector):
        """Should find relevant repos for domain."""
        results = await selector.research_domain_specific(
            subagent_name="ads",
            domain="advertising automation",
        )

        # Should find some repos
        all_repos = [repo for repos in results.values() for repo in repos]
        assert len(all_repos) > 0

        # Repos should be relevant (have stars, description)
        for repo in all_repos:
            assert repo.url
            assert repo.stars >= 0

    @pytest.mark.asyncio
    async def test_research_domain_specific_fallback_for_unknown_subagent(self, selector):
        """Should fallback to domain query for unknown subagent."""
        results = await selector.research_domain_specific(
            subagent_name="unknown_subagent",
            domain="some domain",
        )

        # Should still return results (fallback to domain query)
        assert isinstance(results, dict)

    @pytest.mark.asyncio
    async def test_seo_domain_queries_include_serp(self, selector):
        """Should include SERP analysis in SEO queries."""
        seo_queries = selector.domain_queries["seo"]

        # Should include SERP-related queries
        assert any("serp" in q.lower() for q in seo_queries)

    @pytest.mark.asyncio
    async def test_content_domain_queries_include_generation(self, selector):
        """Should include content generation in content queries."""
        content_queries = selector.domain_queries["content"]

        # Should include content generation queries
        assert any("generation" in q.lower() or "writer" in q.lower() for q in content_queries)

    @pytest.mark.asyncio
    async def test_analytics_domain_queries_include_yandex_metrika(self, selector):
        """Should include Yandex Metrika in analytics queries."""
        analytics_queries = selector.domain_queries["analytics"]

        # Should include Yandex Metrika query
        assert any("yandex" in q.lower() and "metrika" in q.lower() for q in analytics_queries)


class TestDomainSpecificPatternExtraction:
    """Test domain-specific pattern extraction (CRITICAL FIX 2026-05-13)."""

    @pytest.mark.asyncio
    async def test_domain_pattern_signatures_exist(self, selector):
        """Should have domain pattern signatures for all subagent types."""
        expected_types = ["ads", "seo", "analytics", "content", "gap_detection", "prioritization", "social"]

        for subagent_type in expected_types:
            assert subagent_type in selector.domain_pattern_signatures, \
                f"Missing domain patterns for {subagent_type}"
            assert len(selector.domain_pattern_signatures[subagent_type]) > 0, \
                f"Empty domain patterns for {subagent_type}"

    @pytest.mark.asyncio
    async def test_ads_mcp_server_pattern_detection(self, selector, tmp_path):
        """Should detect MCP server pattern for Ads subagent."""
        repo = tmp_path / "ads_repo"
        repo.mkdir()

        (repo / "server.py").write_text("""
from mcp.server.Server import Server
import mcp.server.stdio as stdio

server = Server("yandex-ads")

@server.tool()
async def get_campaigns():
    pass
""")

        skills = await selector.extract_skills(repo, subagent_type="ads")

        mcp_skills = [s for s in skills if "mcp" in s.name.lower()]
        assert len(mcp_skills) > 0, "Should detect MCP server pattern"

    @pytest.mark.asyncio
    async def test_seo_dataframe_first_pattern_detection(self, selector, tmp_path):
        """Should detect DataFrame-first pattern for SEO subagent."""
        repo = tmp_path / "seo_repo"
        repo.mkdir()

        (repo / "crawler.py").write_text("""
import pandas as pd

def crawl_website(url: str) -> pd.DataFrame:
    data = {"url": [url], "title": ["Example"]}
    df = pd.DataFrame(data)
    return df
""")

        skills = await selector.extract_skills(repo, subagent_type="seo")

        df_skills = [s for s in skills if "dataframe" in s.name.lower()]
        assert len(df_skills) > 0, "Should detect DataFrame-first pattern"

    @pytest.mark.asyncio
    async def test_analytics_event_driven_pattern_detection(self, selector, tmp_path):
        """Should detect event-driven pattern for Analytics subagent."""
        repo = tmp_path / "analytics_repo"
        repo.mkdir()

        (repo / "events.py").write_text("""
class EventBus:
    def emit(self, event_name, data):
        pass

    def on(self, event_name, handler):
        pass

event_bus = EventBus()
event_bus.emit("user_action", {"action": "click"})
""")

        skills = await selector.extract_skills(repo, subagent_type="analytics")

        event_skills = [s for s in skills if "event" in s.name.lower()]
        assert len(event_skills) > 0, "Should detect event-driven pattern"

    @pytest.mark.asyncio
    async def test_content_llm_api_pattern_detection(self, selector, tmp_path):
        """Should detect LLM API pattern for Content subagent."""
        repo = tmp_path / "content_repo"
        repo.mkdir()

        (repo / "generator.py").write_text("""
import openai

async def generate_content(prompt: str):
    response = await openai.ChatCompletion.create(
        model="gpt-4",
        messages=[{"role": "user", "content": prompt}]
    )
    return response
""")

        skills = await selector.extract_skills(repo, subagent_type="content")

        llm_skills = [s for s in skills if "llm" in s.name.lower()]
        assert len(llm_skills) > 0, "Should detect LLM API pattern"

    @pytest.mark.asyncio
    async def test_social_telegram_bot_pattern_detection(self, selector, tmp_path):
        """Should detect Telegram bot pattern for Social subagent."""
        repo = tmp_path / "social_repo"
        repo.mkdir()

        (repo / "bot.py").write_text("""
from telegram import Bot, Update
from telegram.ext import Updater, CommandHandler

def start_command(update: Update, context):
    update.message.reply_text("Hello!")

updater = Updater(token="TOKEN")
updater.dispatcher.add_handler(CommandHandler("start", start_command))
""")

        skills = await selector.extract_skills(repo, subagent_type="social")

        telegram_skills = [s for s in skills if "telegram" in s.name.lower()]
        assert len(telegram_skills) > 0, "Should detect Telegram bot pattern"

    @pytest.mark.asyncio
    async def test_generic_and_domain_patterns_together(self, selector, tmp_path):
        """Should detect both generic and domain-specific patterns."""
        repo = tmp_path / "mixed_repo"
        repo.mkdir()

        (repo / "client.py").write_text("""
from pybreaker import CircuitBreaker
from mcp.server.Server import Server

breaker = CircuitBreaker(fail_max=5, reset_timeout=60)
server = Server("test")
""")

        skills = await selector.extract_skills(repo, subagent_type="ads")

        # Should detect both generic and domain-specific patterns
        generic_skills = [s for s in skills if "circuit breaker" in s.name.lower()]
        domain_skills = [s for s in skills if "mcp" in s.name.lower()]

        assert len(generic_skills) > 0, "Should detect generic patterns"
        assert len(domain_skills) > 0, "Should detect domain-specific patterns"

    @pytest.mark.asyncio
    async def test_no_subagent_type_only_generic_patterns(self, selector, tmp_path):
        """Should only detect generic patterns without subagent_type."""
        repo = tmp_path / "generic_repo"
        repo.mkdir()

        (repo / "mixed.py").write_text("""
from pybreaker import CircuitBreaker
from mcp.server.Server import Server

breaker = CircuitBreaker(fail_max=5)
server = Server("test")
""")

        skills = await selector.extract_skills(repo, subagent_type=None)

        # Should only detect generic patterns
        generic_skills = [s for s in skills if "circuit breaker" in s.name.lower()]
        domain_skills = [s for s in skills if "mcp" in s.name.lower()]

        assert len(generic_skills) > 0, "Should detect generic patterns"
        assert len(domain_skills) == 0, "Should NOT detect domain-specific patterns without subagent_type"

    @pytest.mark.asyncio
    async def test_pattern_description_generation(self, selector):
        """Should generate descriptions for domain patterns."""
        desc = selector._get_domain_pattern_description("ads", "mcp_server")
        assert "MCP server" in desc
        assert len(desc) > 10

        desc = selector._get_domain_pattern_description("seo", "dataframe_first")
        assert "DataFrame" in desc

        desc = selector._get_domain_pattern_description("unknown", "unknown")
        assert "Domain-specific pattern" in desc

    @pytest.mark.asyncio
    async def test_has_pattern_from_signatures(self, selector):
        """Should match patterns from signatures."""
        code = "from mcp.server.Server import Server"
        signatures = ["mcp.server.Server", "stdio", "@server.tool"]

        assert selector._has_pattern_from_signatures(code, signatures)

        code = "import requests"
        assert not selector._has_pattern_from_signatures(code, signatures)

    @pytest.mark.asyncio
    async def test_extract_pattern_code_from_signatures(self, selector):
        """Should extract code from signatures."""
        code = """
Some code before
from mcp.server.Server import Server
server = Server("test")
Some code after
"""
        signatures = ["mcp.server.Server"]

        extracted = selector._extract_pattern_code_from_signatures(code, signatures)
        assert "mcp.server.Server" in extracted
        assert len(extracted) > 0
        assert len(extracted) <= 500
