# AIM/src/aim/teacher/reference_repos.py
"""Reference repositories with production patterns for comparison."""

REFERENCE_REPOS = {
    "api_client": [
        # Production API clients with resilience patterns
        "https://github.com/httpx-project/httpx",  # Modern HTTP client
        "https://github.com/psf/requests",  # Popular HTTP library
        "https://github.com/aio-libs/aiohttp",  # Async HTTP client
    ],
    "resilience": [
        # Resilience patterns (circuit breaker, retry, rate limiting)
        "https://github.com/Netflix/Hystrix",  # Circuit breaker pattern
        "https://github.com/jd/tenacity",  # Retry library
        "https://github.com/tomasbasham/ratelimit",  # Rate limiting
    ],
    "production_ready": [
        # Production-ready Python projects with best practices
        "https://github.com/tiangolo/fastapi",  # FastAPI framework
        "https://github.com/encode/starlette",  # ASGI framework
        "https://github.com/pallets/flask",  # Flask framework
    ],
}


def get_reference_repos(category: str = "api_client") -> list[str]:
    """
    Get reference repositories for a category.

    Args:
        category: Category of repos (api_client, resilience, production_ready)

    Returns:
        List of GitHub URLs
    """
    return REFERENCE_REPOS.get(category, REFERENCE_REPOS["api_client"])
