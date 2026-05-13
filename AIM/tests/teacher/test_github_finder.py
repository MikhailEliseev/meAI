# AIM/tests/teacher/test_github_finder.py
import pytest
from AIM.src.aim.teacher.github_finder import GitHubFinder


def test_find_repos_for_topic():
    """Test finding GitHub repos for a topic."""
    finder = GitHubFinder()
    repos = finder.find_repos("content writing SEO")

    assert len(repos) > 0
    assert all(hasattr(r, "url") for r in repos)
    assert all(hasattr(r, "stars") for r in repos)
    assert all(hasattr(r, "description") for r in repos)


def test_filter_by_stars():
    """Test filtering repos by star count."""
    finder = GitHubFinder(min_stars=100)
    repos = finder.find_repos("SEO analysis")

    assert all(r.stars >= 100 for r in repos)
