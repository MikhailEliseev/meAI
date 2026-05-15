"""Pydantic schemas for LLM requests and responses."""

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, field_validator


class LLMMessage(BaseModel):
    """Single message in LLM conversation."""

    role: str = Field(..., description="Message role: system, user, or assistant")
    content: str = Field(..., description="Message content")

    @field_validator("role")
    @classmethod
    def validate_role(cls, v: str) -> str:
        """Validate message role."""
        if v not in ["system", "user", "assistant"]:
            raise ValueError(f"Invalid role: {v}. Must be system, user, or assistant")
        return v


class LLMRequest(BaseModel):
    """Request to LLM provider."""

    messages: List[LLMMessage] = Field(..., description="Conversation messages")
    model: Optional[str] = Field(
        None, description="Specific model to use (if None, router decides)"
    )
    temperature: float = Field(
        0.7, ge=0.0, le=2.0, description="Sampling temperature"
    )
    max_tokens: int = Field(4096, ge=1, le=100000, description="Max tokens to generate")
    system_prompt: Optional[str] = Field(
        None, description="System prompt (alternative to system message)"
    )
    response_format: Optional[Dict[str, Any]] = Field(
        None, description="Structured output format (JSON schema)"
    )
    metadata: Dict[str, Any] = Field(
        default_factory=dict, description="Request metadata for tracking"
    )


class LLMResponse(BaseModel):
    """Response from LLM provider."""

    content: str = Field(..., description="Generated content")
    model: str = Field(..., description="Model that generated response")
    provider: str = Field(..., description="Provider used (claude, gemini, deepseek)")
    finish_reason: str = Field(..., description="Why generation stopped")
    usage: Dict[str, int] = Field(
        ..., description="Token usage (input_tokens, output_tokens, total_tokens)"
    )
    cost_usd: float = Field(..., ge=0.0, description="Cost in USD")
    cached: bool = Field(False, description="Whether response was cached")
    latency_ms: int = Field(..., ge=0, description="Response latency in milliseconds")
    timestamp: datetime = Field(
        default_factory=datetime.utcnow, description="Response timestamp"
    )
    metadata: Dict[str, Any] = Field(
        default_factory=dict, description="Response metadata"
    )


class LLMError(BaseModel):
    """Error from LLM provider."""

    error_type: str = Field(..., description="Error type (rate_limit, timeout, etc)")
    message: str = Field(..., description="Error message")
    provider: str = Field(..., description="Provider that failed")
    retryable: bool = Field(..., description="Whether error is retryable")
    timestamp: datetime = Field(
        default_factory=datetime.utcnow, description="Error timestamp"
    )
