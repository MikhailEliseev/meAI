"""Perplexity API client for deep research"""

import httpx
from typing import Any


class PerplexityClient:
    """Async Perplexity API client for deep research

    Uses Perplexity AI API to perform deep research with citations.
    """

    def __init__(
        self,
        api_key: str,
        base_url: str = "https://api.perplexity.ai",
        model: str = "llama-3.1-sonar-large-128k-online",
    ):
        """Initialize Perplexity client

        Args:
            api_key: Perplexity API key
            base_url: API base URL
            model: Model to use for research
        """
        self.api_key = api_key
        self.base_url = base_url
        self.model = model

    async def research(self, query: str) -> dict[str, Any]:
        """Perform deep research on a query

        Args:
            query: Research query

        Returns:
            Dictionary with 'content' and 'sources' keys

        Example:
            result = await client.research("What are SEO best practices?")
            print(result["content"])
            print(result["sources"])
        """
        response = await self._make_request(query)

        # Extract content and citations
        message = response["choices"][0]["message"]
        content = message.get("content", "")
        sources = message.get("citations", [])

        return {
            "content": content,
            "sources": sources,
        }

    async def _make_request(self, prompt: str) -> dict[str, Any]:
        """Make API request to Perplexity

        Args:
            prompt: Research prompt

        Returns:
            API response
        """
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": self.model,
                    "messages": [
                        {
                            "role": "system",
                            "content": "You are a research assistant. Provide detailed, well-sourced answers.",
                        },
                        {
                            "role": "user",
                            "content": prompt,
                        },
                    ],
                },
                timeout=60.0,
            )
            response.raise_for_status()
            return response.json()
