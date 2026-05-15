"""Omni-Router provider for model rotation.

Connects to user's Omni-Router server that rotates between:
- Claude (Anthropic)
- Gemini (Google)
- DeepSeek

Provides automatic fallback and load balancing.
"""

import time
from typing import Optional

import httpx

from aim.ai.llm.providers.base import BaseLLMProvider, LLMProviderError
from aim.ai.llm.schemas import LLMRequest, LLMResponse


class OmniRouterProvider(BaseLLMProvider):
    """Provider that connects to Omni-Router for model rotation."""

    def __init__(
        self,
        base_url: str = "http://localhost:8000",
        api_key: Optional[str] = None,
        timeout: int = 60,
    ):
        """Initialize Omni-Router provider.

        Args:
            base_url: Omni-Router server URL (default: http://localhost:8000)
            api_key: API key for Omni-Router (if authentication enabled)
            timeout: Request timeout in seconds
        """
        super().__init__(api_key=api_key, base_url=base_url, timeout=timeout)
        self.client = httpx.AsyncClient(timeout=timeout)

    async def generate(self, request: LLMRequest) -> LLMResponse:
        """Generate response via Omni-Router.

        Args:
            request: LLM request

        Returns:
            LLM response

        Raises:
            LLMProviderError: If generation fails
        """
        start_time = time.time()

        try:
            # Prepare request payload
            payload = {
                "messages": [
                    {"role": msg.role, "content": msg.content}
                    for msg in request.messages
                ],
                "temperature": request.temperature,
                "max_tokens": request.max_tokens,
            }

            # Add system prompt if provided
            if request.system_prompt:
                payload["messages"].insert(
                    0, {"role": "system", "content": request.system_prompt}
                )

            # Add model preference if specified
            if request.model:
                payload["model"] = request.model

            # Add response format if specified
            if request.response_format:
                payload["response_format"] = request.response_format

            # Add metadata
            payload["metadata"] = request.metadata

            # Make request to Omni-Router
            headers = {}
            if self.api_key:
                headers["Authorization"] = f"Bearer {self.api_key}"

            response = await self.client.post(
                f"{self.base_url}/v1/chat/completions",
                json=payload,
                headers=headers,
            )

            # Check for errors
            if response.status_code != 200:
                error_data = response.json() if response.text else {}
                raise LLMProviderError(
                    message=error_data.get("error", f"HTTP {response.status_code}"),
                    provider="omnirouter",
                    error_type=self._classify_error(response.status_code),
                    retryable=response.status_code in [429, 500, 502, 503, 504],
                )

            # Parse response
            data = response.json()
            latency_ms = int((time.time() - start_time) * 1000)

            # Extract content
            content = data["choices"][0]["message"]["content"]
            finish_reason = data["choices"][0]["finish_reason"]

            # Extract usage
            usage = data.get("usage", {})
            input_tokens = usage.get("prompt_tokens", 0)
            output_tokens = usage.get("completion_tokens", 0)
            total_tokens = usage.get("total_tokens", input_tokens + output_tokens)

            # Extract provider info
            provider = data.get("model", "unknown").split("/")[0]  # e.g., "claude/opus"
            model = data.get("model", "unknown")

            # Calculate cost (approximate, depends on actual provider)
            cost_usd = self.calculate_cost(input_tokens, output_tokens)

            # Check if cached
            cached = data.get("cached", False)

            return LLMResponse(
                content=content,
                model=model,
                provider=provider,
                finish_reason=finish_reason,
                usage={
                    "input_tokens": input_tokens,
                    "output_tokens": output_tokens,
                    "total_tokens": total_tokens,
                },
                cost_usd=cost_usd,
                cached=cached,
                latency_ms=latency_ms,
                metadata=data.get("metadata", {}),
            )

        except LLMProviderError:
            # Re-raise LLMProviderError as-is (from HTTP error handling above)
            raise

        except httpx.TimeoutException as e:
            raise LLMProviderError(
                message=f"Request timeout after {self.timeout}s",
                provider="omnirouter",
                error_type="timeout",
                retryable=True,
            ) from e

        except httpx.ConnectError as e:
            raise LLMProviderError(
                message=f"Cannot connect to Omni-Router at {self.base_url}",
                provider="omnirouter",
                error_type="connection",
                retryable=True,
            ) from e

        except Exception as e:
            raise LLMProviderError(
                message=f"Unexpected error: {str(e)}",
                provider="omnirouter",
                error_type="unknown",
                retryable=False,
            ) from e

    def get_provider_name(self) -> str:
        """Get provider name."""
        return "omnirouter"

    def calculate_cost(self, input_tokens: int, output_tokens: int) -> float:
        """Calculate approximate cost.

        Uses average pricing across Claude, Gemini, DeepSeek.
        Actual cost depends on which model Omni-Router selected.

        Args:
            input_tokens: Number of input tokens
            output_tokens: Number of output tokens

        Returns:
            Approximate cost in USD
        """
        # Average pricing (Claude Sonnet as baseline)
        input_cost_per_mtok = 3.0  # $3 per million tokens
        output_cost_per_mtok = 15.0  # $15 per million tokens

        input_cost = (input_tokens / 1_000_000) * input_cost_per_mtok
        output_cost = (output_tokens / 1_000_000) * output_cost_per_mtok

        return input_cost + output_cost

    def get_model_name(self) -> str:
        """Get default model name."""
        return "omnirouter/auto"  # Router decides which model to use

    async def close(self):
        """Close HTTP client."""
        await self.client.aclose()

    def _classify_error(self, status_code: int) -> str:
        """Classify HTTP error by status code.

        Args:
            status_code: HTTP status code

        Returns:
            Error type string
        """
        if status_code == 429:
            return "rate_limit"
        elif status_code == 401:
            return "authentication"
        elif status_code == 403:
            return "permission"
        elif status_code == 404:
            return "not_found"
        elif status_code >= 500:
            return "server_error"
        else:
            return "unknown"
