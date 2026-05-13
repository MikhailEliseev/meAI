# AIM/src/aim/teacher/github_finder.py
"""GitHub repository finder for subagent topics."""

from dataclasses import dataclass
import httpx


@dataclass
class GitHubRepo:
    """GitHub repository metadata."""
    url: str
    name: str
    stars: int
    description: str
    language: str


class GitHubFinder:
    """Find relevant GitHub repositories for subagent topics."""

    def __init__(self, min_stars: int = 50):
        self.min_stars = min_stars
        self.client = httpx.Client(timeout=30.0)

    def find_repos(self, topic: str, max_results: int = 10) -> list[GitHubRepo]:
        """
        Find GitHub repos for a topic.

        Args:
            topic: Search topic (e.g., "content writing SEO")
            max_results: Maximum number of results

        Returns:
            List of GitHubRepo objects
        """
        # GitHub API search
        query = f"{topic} language:python stars:>={self.min_stars}"
        url = "https://api.github.com/search/repositories"

        params = {
            "q": query,
            "sort": "stars",
            "order": "desc",
            "per_page": max_results,
        }

        try:
            response = self.client.get(url, params=params)
            response.raise_for_status()
            data = response.json()

            repos = []
            for item in data.get("items", []):
                repo = GitHubRepo(
                    url=item["html_url"],
                    name=item["full_name"],
                    stars=item["stargazers_count"],
                    description=item.get("description", ""),
                    language=item.get("language", "Python"),
                )
                repos.append(repo)

            return repos
        except Exception as e:
            print(f"Error finding repos: {e}")
            return []

    def __del__(self):
        """Close HTTP client."""
        if hasattr(self, "client"):
            self.client.close()
