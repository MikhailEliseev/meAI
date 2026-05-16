"""
LLM Request/Response Schemas

Pydantic models for type-safe LLM interactions.
"""

from enum import Enum
from typing import Optional, Type, Any, Dict
from pydantic import BaseModel, Field, field_validator


class LLMProvider(str, Enum):
    """Supported LLM providers."""
    ANTHROPIC = "anthropic"
    OPENAI = "openai"


class LLMModel(str, Enum):
    """Supported LLM models."""
    # Anthropic Claude
    CLAUDE_OPUS = "claude-opus-4"
    CLAUDE_SONNET = "claude-sonnet-4"
    CLAUDE_HAIKU = "claude-haiku-4"
    
    # OpenAI GPT
    GPT4_TURBO = "gpt-4-turbo"
    GPT4 = "gpt-4"
    GPT35_TURBO = "gpt-3.5-turbo"


class LLMRequest(BaseModel):
    """LLM request parameters."""
    
    prompt: str = Field(..., description="User prompt")
    system_prompt: Optional[str] = Field(None, description="System prompt (optional)")
    model: str = Field(default="claude-sonnet-4", description="Model to use")
    max_tokens: int = Field(default=4096, ge=1, le=200000, description="Max tokens to generate")
    temperature: float = Field(default=0.7, ge=0.0, le=2.0, description="Sampling temperature")
    response_format: Optional[Type[BaseModel]] = Field(None, description="Structured output schema")
    cache_key: Optional[str] = Field(None, description="Cache key for response caching")
    
    @field_validator("prompt")
    @classmethod
    def validate_prompt(cls, v: str) -> str:
        """Validate prompt is not empty."""
        if not v or not v.strip():
            raise ValueError("Prompt cannot be empty")
        return v.strip()
    
    @field_validator("model")
    @classmethod
    def validate_model(cls, v: str) -> str:
        """Validate model is supported."""
        valid_models = [m.value for m in LLMModel]
        if v not in valid_models:
            raise ValueError(f"Model {v} not supported. Valid models: {valid_models}")
        return v


class LLMResponse(BaseModel):
    """LLM response with metadata."""
    
    content: str = Field(..., description="Generated content")
    model: str = Field(..., description="Model used")
    provider: LLMProvider = Field(..., description="Provider used")
    tokens_used: int = Field(..., ge=0, description="Total tokens used (input + output)")
    input_tokens: int = Field(..., ge=0, description="Input tokens")
    output_tokens: int = Field(..., ge=0, description="Output tokens")
    cost_usd: float = Field(..., ge=0.0, description="Cost in USD")
    cached: bool = Field(default=False, description="Response from cache")
    latency_ms: int = Field(..., ge=0, description="Response latency in milliseconds")
    cache_key: Optional[str] = Field(None, description="Cache key used")
    
    class Config:
        """Pydantic config."""
        json_schema_extra = {
            "example": {
                "content": "This is a sample response from Claude.",
                "model": "claude-sonnet-4",
                "provider": "anthropic",
                "tokens_used": 150,
                "input_tokens": 50,
                "output_tokens": 100,
                "cost_usd": 0.0015,
                "cached": False,
                "latency_ms": 1200,
                "cache_key": None
            }
        }


class LLMError(Exception):
    """Base exception for LLM errors."""
    pass


class LLMProviderError(LLMError):
    """Provider-specific error."""
    
    def __init__(self, provider: LLMProvider, message: str):
        self.provider = provider
        super().__init__(f"[{provider.value}] {message}")


class LLMRateLimitError(LLMError):
    """Rate limit exceeded."""
    pass


class LLMBudgetExceededError(LLMError):
    """Budget limit exceeded."""
    pass


class LLMCostEstimate(BaseModel):
    """Cost estimate for LLM request."""
    
    provider: LLMProvider
    model: str
    input_tokens: int
    output_tokens: int
    input_cost_usd: float
    output_cost_usd: float
    total_cost_usd: float
    
    class Config:
        """Pydantic config."""
        json_schema_extra = {
            "example": {
                "provider": "anthropic",
                "model": "claude-sonnet-4",
                "input_tokens": 1000,
                "output_tokens": 500,
                "input_cost_usd": 0.003,
                "output_cost_usd": 0.015,
                "total_cost_usd": 0.018
            }
        }
