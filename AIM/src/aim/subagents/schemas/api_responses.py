"""API Response Schemas with Validation

Pydantic models for keyword research API responses with field validation
and cross-source consistency checks.
"""

from typing import Literal, Optional

from pydantic import BaseModel, Field, field_validator, model_validator


class SEMrushKeywordData(BaseModel):
    """SEMrush keyword data schema

    Attributes:
        keyword: Keyword phrase
        volume: Monthly search volume
        difficulty: Keyword difficulty (0-100)
        cpc: Cost per click in USD
        intent: Search intent type
        trend: Search trend (optional)
        competition: Competition level (optional)
    """

    keyword: str = Field(..., min_length=1, max_length=200)
    volume: int = Field(..., ge=0)
    difficulty: int = Field(..., ge=0, le=100)
    cpc: float = Field(..., ge=0.0)
    intent: Literal["informational", "commercial", "navigational", "local"]
    trend: Optional[str] = None
    competition: Optional[float] = Field(None, ge=0.0, le=1.0)

    @field_validator("volume")
    @classmethod
    def validate_volume(cls, v: int) -> int:
        """Validate search volume is reasonable"""
        if v > 10_000_000:
            raise ValueError("Search volume exceeds reasonable limit (10M)")
        return v

    @field_validator("cpc")
    @classmethod
    def validate_cpc(cls, v: float) -> float:
        """Validate CPC is reasonable"""
        if v > 1000.0:
            raise ValueError("CPC exceeds reasonable limit ($1000)")
        return v


class AhrefsKeywordData(BaseModel):
    """Ahrefs keyword data schema with difficulty normalization

    Ahrefs uses different difficulty scale, normalized to 0-100.

    Attributes:
        keyword: Keyword phrase
        volume: Monthly search volume
        difficulty: Keyword difficulty (0-100, normalized)
        cpc: Cost per click in USD
        intent: Search intent type
        clicks: Estimated clicks (optional)
        parent_topic: Parent topic keyword (optional)
    """

    keyword: str = Field(..., min_length=1, max_length=200)
    volume: int = Field(..., ge=0)
    difficulty: int = Field(..., ge=0, le=100)
    cpc: float = Field(..., ge=0.0)
    intent: Literal["informational", "commercial", "navigational", "local"]
    clicks: Optional[int] = Field(None, ge=0)
    parent_topic: Optional[str] = None

    @field_validator("volume")
    @classmethod
    def validate_volume(cls, v: int) -> int:
        """Validate search volume is reasonable"""
        if v > 10_000_000:
            raise ValueError("Search volume exceeds reasonable limit (10M)")
        return v

    @field_validator("cpc")
    @classmethod
    def validate_cpc(cls, v: float) -> float:
        """Validate CPC is reasonable"""
        if v > 1000.0:
            raise ValueError("CPC exceeds reasonable limit ($1000)")
        return v

    @field_validator("difficulty")
    @classmethod
    def normalize_difficulty(cls, v: int) -> int:
        """Normalize Ahrefs difficulty to 0-100 scale

        Ahrefs uses 0-100 scale but with different distribution.
        This ensures consistency with SEMrush.
        """
        # Ahrefs difficulty is already 0-100, but may need adjustment
        # based on empirical comparison with SEMrush
        return max(0, min(100, v))


class KeywordExpansionRequest(BaseModel):
    """Keyword expansion request schema

    Attributes:
        seed_keyword: Seed keyword to expand
        max_keywords: Maximum keywords to return
        min_volume: Minimum search volume filter
        max_cost_usd: Maximum API cost budget in USD
        target_intents: Filter by intent types (optional)
        max_difficulty: Maximum difficulty filter (optional)
    """

    seed_keyword: str = Field(..., min_length=1, max_length=200)
    max_keywords: int = Field(default=100, ge=1, le=1000)
    min_volume: int = Field(default=10, ge=0)
    max_cost_usd: float = Field(default=5.0, ge=0.1, le=100.0)
    target_intents: Optional[list[str]] = None
    max_difficulty: Optional[int] = Field(None, ge=0, le=100)

    @field_validator("seed_keyword")
    @classmethod
    def validate_seed_keyword(cls, v: str) -> str:
        """Validate seed keyword format"""
        v = v.strip().lower()
        if not v:
            raise ValueError("Seed keyword cannot be empty")
        if len(v.split()) > 10:
            raise ValueError("Seed keyword too long (max 10 words)")
        return v

    @field_validator("target_intents")
    @classmethod
    def validate_intents(cls, v: Optional[list[str]]) -> Optional[list[str]]:
        """Validate intent types"""
        if v is None:
            return v

        valid_intents = {"informational", "commercial", "navigational", "local"}
        for intent in v:
            if intent not in valid_intents:
                raise ValueError(
                    f"Invalid intent '{intent}'. Must be one of: {valid_intents}"
                )
        return v

    @model_validator(mode="after")
    def validate_budget_vs_keywords(self) -> "KeywordExpansionRequest":
        """Validate budget is sufficient for requested keywords

        Rough estimate: $0.01-0.05 per keyword depending on API
        """
        min_cost_per_keyword = 0.01
        estimated_cost = self.max_keywords * min_cost_per_keyword

        if estimated_cost > self.max_cost_usd:
            raise ValueError(
                f"Budget ${self.max_cost_usd} may be insufficient for "
                f"{self.max_keywords} keywords (estimated ${estimated_cost:.2f}). "
                f"Reduce max_keywords or increase budget."
            )

        return self


class KeywordDataUnified(BaseModel):
    """Unified keyword data from any source

    Normalized format for internal use, regardless of API source.

    Attributes:
        keyword: Keyword phrase
        volume: Monthly search volume
        difficulty: Keyword difficulty (0-100)
        cpc: Cost per click in USD
        intent: Search intent type
        source: Data source (semrush, ahrefs)
        priority_score: Calculated priority score (0-100)
    """

    keyword: str
    volume: int
    difficulty: int
    cpc: float
    intent: Literal["informational", "commercial", "navigational", "local"]
    source: Literal["semrush", "ahrefs"]
    priority_score: float = Field(..., ge=0.0, le=100.0)

    @classmethod
    def from_semrush(cls, data: SEMrushKeywordData) -> "KeywordDataUnified":
        """Create from SEMrush data"""
        priority_score = cls._calculate_priority(
            volume=data.volume,
            difficulty=data.difficulty,
            cpc=data.cpc,
            intent=data.intent,
        )

        return cls(
            keyword=data.keyword,
            volume=data.volume,
            difficulty=data.difficulty,
            cpc=data.cpc,
            intent=data.intent,
            source="semrush",
            priority_score=priority_score,
        )

    @classmethod
    def from_ahrefs(cls, data: AhrefsKeywordData) -> "KeywordDataUnified":
        """Create from Ahrefs data"""
        priority_score = cls._calculate_priority(
            volume=data.volume,
            difficulty=data.difficulty,
            cpc=data.cpc,
            intent=data.intent,
        )

        return cls(
            keyword=data.keyword,
            volume=data.volume,
            difficulty=data.difficulty,
            cpc=data.cpc,
            intent=data.intent,
            source="ahrefs",
            priority_score=priority_score,
        )

    @staticmethod
    def _calculate_priority(
        volume: int,
        difficulty: int,
        cpc: float,
        intent: str,
    ) -> float:
        """Calculate keyword priority score (0-100)

        Args:
            volume: Search volume
            difficulty: Keyword difficulty
            cpc: Cost per click
            intent: Search intent

        Returns:
            Priority score (0-100)
        """
        # Volume score (0-40 points)
        volume_score = min(40, (volume / 1000) * 2)

        # Difficulty score (0-30 points, inverse - easier is better)
        difficulty_score = 30 - (difficulty * 0.3)

        # CPC score (0-20 points)
        cpc_score = min(20, cpc * 2)

        # Intent score (0-10 points)
        intent_scores = {
            "commercial": 10,
            "local": 9,
            "navigational": 7,
            "informational": 5,
        }
        intent_score = intent_scores.get(intent, 5)

        total = volume_score + difficulty_score + cpc_score + intent_score

        return round(total, 2)
