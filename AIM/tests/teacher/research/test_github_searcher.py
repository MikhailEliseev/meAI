"""
Tests for GitHubSearcher.
"""

import pytest
from datetime import datetime

from src.aim.teacher.research.github_searcher import (
    GitHubSearcher,
    GitHubRepo,
)


@pytest.fixture
def github_searcher():
    """Create GitHubSearcher instance."""
    return GitHubSearcher()


@pytest.mark.asyncio
async def test_search_returns_repos(github_searcher):
    """Test that search returns list of repositories."""
    repos = await github_searcher.search(
        query="SEO analysis",
        language="Python",
        min_stars=100,
        max_results=10,
    )

    assert isinstance(repos, list)
    assert len(repos) > 0
    assert all(isinstance(repo, GitHubRepo) for repo in repos)


@pytest.mark.asyncio
async def test_search_respects_min_stars(github_searcher):
    """Test that search filters by minimum stars."""
    repos = await github_searcher.search(
        query="test",
        language="Python",
        min_stars=500,
        max_results=10,
    )

    # All repos should have >= min_stars
    assert all(repo.stars >= 500 for repo in repos)


@pytest.mark.asyncio
async def test_search_respects_max_results(github_searcher):
    """Test that search respects max_results limit."""
    repos = await github_searcher.search(
        query="test",
        language="Python",
        min_stars=100,
        max_results=5,
    )

    assert len(repos) <= 5


@pytest.mark.asyncio
async def test_search_sorted_by_stars(github_searcher):
    """Test that results are sorted by stars (descending)."""
    repos = await github_searcher.search(
        query="test",
        language="Python",
        min_stars=100,
        max_results=10,
    )

    # Check that stars are in descending order
    stars = [repo.stars for repo in repos]
    assert stars == sorted(stars, reverse=True)


@pytest.mark.asyncio
async def test_repo_structure(github_searcher):
    """Test that GitHubRepo has correct structure."""
    repos = await github_searcher.search(
        query="test",
        language="Python",
        min_stars=100,
        max_results=1,
    )

    repo = repos[0]

    assert hasattr(repo, "url")
    assert hasattr(repo, "name")
    assert hasattr(repo, "description")
    assert hasattr(repo, "stars")
    assert hasattr(repo, "forks")
    assert hasattr(repo, "last_updated")
    assert hasattr(repo, "language")
    assert hasattr(repo, "topics")
    assert hasattr(repo, "readme_summary")

    assert isinstance(repo.url, str)
    assert isinstance(repo.name, str)
    assert isinstance(repo.stars, int)
    assert isinstance(repo.forks, int)
    assert isinstance(repo.last_updated, datetime)
    assert isinstance(repo.topics, list)


@pytest.mark.asyncio
async def test_search_with_different_languages(github_searcher):
    """Test search with different programming languages."""
    python_repos = await github_searcher.search(
        query="test",
        language="Python",
        min_stars=100,
        max_results=5,
    )

    javascript_repos = await github_searcher.search(
        query="test",
        language="JavaScript",
        min_stars=100,
        max_results=5,
    )

    # Should return repos for each language
    assert len(python_repos) > 0
    assert len(javascript_repos) > 0

    # Languages should match
    assert all(repo.language == "Python" for repo in python_repos)
    assert all(repo.language == "JavaScript" for repo in javascript_repos)


@pytest.mark.asyncio
async def test_repo_urls_valid(github_searcher):
    """Test that repository URLs are valid GitHub URLs."""
    repos = await github_searcher.search(
        query="test",
        language="Python",
        min_stars=100,
        max_results=5,
    )

    for repo in repos:
        assert repo.url.startswith("https://github.com/")


@pytest.mark.asyncio
async def test_repo_topics_included(github_searcher):
    """Test that repositories include topics."""
    repos = await github_searcher.search(
        query="SEO analysis",
        language="Python",
        min_stars=100,
        max_results=5,
    )

    for repo in repos:
        assert len(repo.topics) > 0


@pytest.mark.asyncio
async def test_merge_and_deduplicate(github_searcher):
    """Test merging and deduplication of results."""
    repo1 = GitHubRepo(
        url="https://github.com/user/repo1",
        name="user/repo1",
        description="Test repo",
        stars=100,
        forks=10,
        last_updated=datetime.now(),
        language="Python",
        topics=["test"],
        readme_summary="Summary",
    )

    repo2 = GitHubRepo(
        url="https://github.com/user/repo2",
        name="user/repo2",
        description="Test repo 2",
        stars=200,
        forks=20,
        last_updated=datetime.now(),
        language="Python",
        topics=["test"],
        readme_summary="Summary 2",
    )

    # Duplicate of repo1
    repo1_dup = GitHubRepo(
        url="https://github.com/user/repo1",
        name="user/repo1",
        description="Test repo",
        stars=100,
        forks=10,
        last_updated=datetime.now(),
        language="Python",
        topics=["test"],
        readme_summary="Summary",
    )

    merged = github_searcher._merge_and_deduplicate(
        [repo1, repo2],
        [repo1_dup],
    )

    # Should have 2 unique repos (repo1 and repo2)
    assert len(merged) == 2


@pytest.mark.asyncio
async def test_sort_by_stars(github_searcher):
    """Test sorting repositories by stars."""
    repo1 = GitHubRepo(
        url="https://github.com/user/repo1",
        name="user/repo1",
        description="Test",
        stars=100,
        forks=10,
        last_updated=datetime.now(),
        language="Python",
        topics=[],
        readme_summary="",
    )

    repo2 = GitHubRepo(
        url="https://github.com/user/repo2",
        name="user/repo2",
        description="Test",
        stars=500,
        forks=50,
        last_updated=datetime.now(),
        language="Python",
        topics=[],
        readme_summary="",
    )

    repo3 = GitHubRepo(
        url="https://github.com/user/repo3",
        name="user/repo3",
        description="Test",
        stars=300,
        forks=30,
        last_updated=datetime.now(),
        language="Python",
        topics=[],
        readme_summary="",
    )

    sorted_repos = github_searcher._sort_by_stars([repo1, repo2, repo3])

    # Should be sorted: repo2 (500), repo3 (300), repo1 (100)
    assert sorted_repos[0].stars == 500
    assert sorted_repos[1].stars == 300
    assert sorted_repos[2].stars == 100
