"""
OmniRoute Provider — единый LLM-провайдер для всех моделей.

Все вызовы идут через один endpoint (OpenAI-совместимый API).
OmniRoute сам маршрутизирует модель в зависимости от имени.
"""

import time
from openai import AsyncOpenAI

from .base import BaseLLMProvider
from ..schemas import (
    LLMRequest,
    LLMResponse,
    LLMProvider,
    LLMProviderError,
)


class OmniRouteProvider(BaseLLMProvider):
    """
    Единый провайдер, ходящий через OmniRoute endpoint.

    Использует OpenAI-совместимый API. Все модели (claude, gpt, etc.)
    доступны через один endpoint с одним API ключом.
    """

    PRICING = {
        "claude-opus-4": {"input": 15.0, "output": 75.0},
        "claude-sonnet-4": {"input": 3.0, "output": 15.0},
        "claude-sonnet-4-20250514": {"input": 3.0, "output": 15.0},
        "claude-haiku-4": {"input": 0.25, "output": 1.25},
        "gpt-4-turbo": {"input": 10.0, "output": 30.0},
        "gpt-4": {"input": 30.0, "output": 60.0},
        "gpt-4o": {"input": 5.0, "output": 15.0},
        "gpt-4o-mini": {"input": 0.15, "output": 0.60},
        "gpt-3.5-turbo": {"input": 0.5, "output": 1.5},
    }

    def __init__(self, api_key: str, base_url: str):
        super().__init__(api_key)
        self.base_url = base_url
        self.client = AsyncOpenAI(api_key=api_key, base_url=base_url)

    @property
    def provider_name(self) -> LLMProvider:
        return LLMProvider.OMNI_ROUTE

    async def generate(self, request: LLMRequest) -> LLMResponse:
        start_time = time.time()

        try:
            messages = []
            if request.system_prompt:
                messages.append({"role": "system", "content": request.system_prompt})
            messages.append({"role": "user", "content": request.prompt})

            kwargs = {
                "model": request.model,
                "messages": messages,
                "max_tokens": request.max_tokens,
                "temperature": request.temperature,
            }

            if request.response_format:
                kwargs["response_format"] = {"type": "json_object"}

            response = await self.client.chat.completions.create(**kwargs)

            content = response.choices[0].message.content or ""

            input_tokens = response.usage.prompt_tokens
            output_tokens = response.usage.completion_tokens
            total_tokens = response.usage.total_tokens
            cost_usd = self.estimate_cost(input_tokens, output_tokens, request.model)

            latency_ms = int((time.time() - start_time) * 1000)

            return LLMResponse(
                content=content,
                model=request.model,
                provider=self.provider_name,
                tokens_used=total_tokens,
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                cost_usd=cost_usd,
                cached=False,
                latency_ms=latency_ms,
                cache_key=request.cache_key,
            )

        except Exception as e:
            raise LLMProviderError(
                self.provider_name,
                f"OmniRoute error: {str(e)}",
            )

    def estimate_cost(
        self,
        input_tokens: int,
        output_tokens: int,
        model: str,
    ) -> float:
        if model not in self.PRICING:
            model = "claude-sonnet-4"

        pricing = self.PRICING[model]
        input_cost = (input_tokens / 1_000_000) * pricing["input"]
        output_cost = (output_tokens / 1_000_000) * pricing["output"]

        return input_cost + output_cost

    def count_tokens(self, text: str, model: str) -> int:
        try:
            import tiktoken
            try:
                encoding = tiktoken.encoding_for_model(model)
            except KeyError:
                encoding = tiktoken.get_encoding("cl100k_base")
            return len(encoding.encode(text))
        except Exception:
            return len(text) // 4
