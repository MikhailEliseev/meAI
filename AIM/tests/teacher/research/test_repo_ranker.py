"""
Tests for RepoRanker.
"""

import pytest
from datetime import datetime, timedelta

from AIM.src.aim.teacher.research.repo_ranker import (
    RepoRanker,
    RepoScore,
)
from AIM.src.aim.teacher.research.github_searcher import GitHubRepo


@pytest.fixture
def repo_ranker():
    """Create RepoRanker instance."""
    return RepoRanker()


@pytest.fixture
def sample_repos():
    """Create sample repositories for testing."""
    now = datetime.now()

    return [
        GitHubRepo(
            url="https://github.com/user1/repo1",
            name="user1/repo1",
            description="High quality SEO analysis tool with comprehensive features",
            stars=1000,
            forks=200,
            last_updated=now - timedelta(days=5),
            language="Python",
            topics=["seo", "analysis", "python"],
            readme_summary="Comprehensive SEO analysis tool with detailed documentation and examples.",
        ),
        GitHubRepo(
            url="https://github.com/user2/repo2",
            name="user2/repo2",
            description="Basic SEO tool",
            stars=500,
            forks=50,
            last_updated=now - timedelta(days=100),
            language="Python",
            topics=["seo"],
            readme_summary="Basic tool",
        ),
        GitHubRepo(
            url="https://github.com/user3/repo3",
            name="user3/repo3",
            description="Advanced SEO analysis with AI",
            stars=800,
            forks=150,
            last_updated=now - timedelta(days=10),
            language="Python",
            topics=["seo", "ai", "analysis", "machine-learning"],
            readme_summary="Advanced SEO analysis tool using machine learning for better insights.",
        ),
    ]


@pytest.mark.asyncio
async def test_rank_returns_sorted_scores(repo_ranker, sample_repos):
    """Test that rank returns scores sorted by total_score."""
    scores = await repo_ranker.rank(sample_repos, query="SEO analysis")

    assert len(scores) == 3
    assert all(isinstance(score, RepoScore) for score in scores)

    # Check that scores are sorted (descending)
    for i in range(len(scores) - 1):
        assert scores[i].total_score >= scores[i + 1].total_score


@pytest.mark.asyncio
async def test_rank_empty_list(repo_ranker):
    """Test ranking empty list."""
    scores = await repo_ranker.rank([], query="test")
    assert scores == []


@pytest.mark.asyncio
async def test_stars_score_normalized(repo_ranker, sample_repos):
    """Test that stars score is normalized by max stars."""
    scores = await repo_ranker.rank(sample_repos, query="test")

    # Repo with most stars should have stars_score = 100
    max_stars_repo = max(scores, key=lambda s: s.repo.stars)
    assert max_stars_repo.stars_score == 100.0

    # Other repos should have proportional scores
    for score in scores:
        if score.repo.stars < max_stars_repo.repo.stars:
            assert score.stars_score < 100.0


@pytest.mark.asyncio
async def test_activity_score_recent_update(repo_ranker):
    """Test that recently updated repos get higher activity score."""
    now = datetime.now()

    recent_repo = GitHubRepo(
        url="https://github.com/user/recent",
        name="user/recent",
        description="Recently updated",
        stars=100,
        forks=10,
        last_updated=now - timedelta(days=5),
        language="Python",
        topics=[],
        readme_summary="",
    )

    old_repo = GitHubRepo(
        url="https://github.com/user/old",
        name="user/old",
        description="Old repo",
        stars=100,
        forks=10,
        last_updated=now - timedelta(days=200),
        language="Python",
        topics=[],
        readme_summary="",
    )

    scores = await repo_ranker.rank([recent_repo, old_repo], query="test")

    recent_score = next(s for s in scores if s.repo.name == "user/recent")
    old_score = next(s for s in scores if s.repo.name == "user/old")

    assert recent_score.activity_score > old_score.activity_score


@pytest.mark.asyncio
async def test_quality_score_with_readme_and_topics(repo_ranker):
    """Test that repos with README and topics get higher quality score."""
    high_quality = GitHubRepo(
        url="https://github.com/user/high",
        name="user/high",
        description="High quality repo with detailed description",
        stars=100,
        forks=10,
        last_updated=datetime.now(),
        language="Python",
        topics=["python", "seo", "analysis", "tool", "library"],
        readme_summary="Comprehensive README with detailed documentation, examples, and usage instructions.",
    )

    low_quality = GitHubRepo(
        url="https://github.com/user/low",
        name="user/low",
        description="Low",
        stars=100,
        forks=10,
        last_updated=datetime.now(),
        language="Python",
        topics=[],
        readme_summary="",
    )

    scores = await repo_ranker.rank([high_quality, low_quality], query="test")

    high_score = next(s for s in scores if s.repo.name == "user/high")
    low_score = next(s for s in scores if s.repo.name == "user/low")

    assert high_score.quality_score > low_score.quality_score


@pytest.mark.asyncio
async def test_relevance_score_with_query_match(repo_ranker):
    """Test that repos matching query get higher relevance score."""
    relevant_repo = GitHubRepo(
        url="https://github.com/user/relevant",
        name="seo-analysis-tool",
        description="SEO analysis tool for Python",
        stars=100,
        forks=10,
        last_updated=datetime.now(),
        language="Python",
        topics=["seo", "analysis"],
        readme_summary="",
    )

    irrelevant_repo = GitHubRepo(
        url="https://github.com/user/irrelevant",
        name="random-tool",
        description="Random tool",
        stars=100,
        forks=10,
        last_updated=datetime.now(),
        language="Python",
        topics=["random"],
        readme_summary="",
    )

    scores = await repo_ranker.rank(
        [relevant_repo, irrelevant_repo],
        query="SEO analysis",
    )

    relevant_score = next(s for s in scores if s.repo.name == "seo-analysis-tool")
    irrelevant_score = next(s for s in scores if s.repo.name == "random-tool")

    assert relevant_score.relevance_score > irrelevant_score.relevance_score


@pytest.mark.asyncio
async def test_relevance_score_no_query(repo_ranker, sample_repos):
    """Test that all repos get same relevance score when no query."""
    scores = await repo_ranker.rank(sample_repos, query="")

    # All should have relevance_score = 100 (no query = all equally relevant)
    for score in scores:
        assert score.relevance_score == 100.0


@pytest.mark.asyncio
async def test_total_score_calculation(repo_ranker):
    """Test that total score is calculated correctly."""
    repo = GitHubRepo(
        url="https://github.com/user/repo",
        name="user/repo",
        description="Test repo",
        stars=100,
        forks=10,
        last_updated=datetime.now(),
        language="Python",
        topics=["test"],
        readme_summary="Test",
    )

    scores = await repo_ranker.rank([repo], query="test")
    score = scores[0]

    # Total score should be weighted sum of component scores
    expected_total = (
        score.stars_score * 0.30 +
        score.activity_score * 0.25 +
        score.quality_score * 0.25 +
        score.relevance_score * 0.20
    )

    assert abs(score.total_score - expected_total) < 0.01


@pytest.mark.asyncio
async def test_custom_weights(sample_repos):
    """Test that custom weights affect scoring."""
    # Create ranker with stars weight = 1.0 (100%)
    stars_ranker = RepoRanker(
        stars_weight=1.0,
        activity_weight=0.0,
        quality_weight=0.0,
        relevance_weight=0.0,
    )

    scores = await stars_ranker.rank(sample_repos, query="test")

    # Total score should equal stars score
    for score in scores:
        assert abs(score.total_score - score.stars_score) < 0.01


@pytest.mark.asyncio
async def test_score_range(repo_ranker, sample_repos):
    """Test that all scores are in 0-100 range."""
    scores = await repo_ranker.rank(sample_repos, query="SEO analysis")

    for score in scores:
        assert 0 <= score.total_score <= 100
        assert 0 <= score.stars_score <= 100
        assert 0 <= score.activity_score <= 100
        assert 0 <= score.quality_score <= 100
        assert 0 <= score.relevance_score <= 100


@pytest.mark.asyncio
async def test_repo_score_structure(repo_ranker, sample_repos):
    """Test that RepoScore has correct structure."""
    scores = await repo_ranker.rank(sample_repos, query="test")
    score = scores[0]

    assert hasattr(score, "repo")
    assert hasattr(score, "total_score")
    assert hasattr(score, "stars_score")
    assert hasattr(score, "activity_score")
    assert hasattr(score, "quality_score")
    assert hasattr(score, "relevance_score")

    assert isinstance(score.repo, GitHubRepo)
    assert isinstance(score.total_score, float)
    assert isinstance(score.stars_score, float)
    assert isinstance(score.activity_score, float)
    assert isinstance(score.quality_score, float)
    assert isinstance(score.relevance_score, float)
