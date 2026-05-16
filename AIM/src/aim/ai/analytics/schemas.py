"""
Predictive Analytics Schemas

Pydantic models for forecasting, anomaly detection, and budget optimization.
"""

from datetime import datetime
from typing import Literal, List
from pydantic import BaseModel, Field, ConfigDict


class ForecastRequest(BaseModel):
    """Request for performance forecasting."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "metric": "conversions",
                "horizon_days": 30,
                "confidence_level": 0.95,
            }
        }
    )

    metric: Literal["clicks", "conversions", "cost", "revenue"] = Field(
        ..., description="Metric to forecast"
    )
    horizon_days: int = Field(
        default=30, ge=1, le=365, description="Forecast horizon in days"
    )
    confidence_level: float = Field(
        default=0.95, ge=0.5, le=0.99, description="Confidence level for intervals"
    )


class ForecastResponse(BaseModel):
    """Response with forecast predictions."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "predictions": [100.0, 105.0, 110.0],
                "lower_bound": [90.0, 95.0, 100.0],
                "upper_bound": [110.0, 115.0, 120.0],
                "accuracy_score": 0.85,
                "seasonality_detected": True,
            }
        }
    )

    predictions: List[float] = Field(..., description="Predicted values")
    lower_bound: List[float] = Field(..., description="Lower confidence bound")
    upper_bound: List[float] = Field(..., description="Upper confidence bound")
    accuracy_score: float = Field(
        ..., ge=0.0, le=1.0, description="Forecast accuracy (0-1)"
    )
    seasonality_detected: bool = Field(
        ..., description="Whether seasonality was detected"
    )


class AnomalyAlert(BaseModel):
    """Anomaly detection alert."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "type": "performance_drop",
                "severity": "high",
                "description": "CTR dropped by 45% in last 24 hours",
                "detected_at": "2026-05-16T13:00:00Z",
                "recommended_action": "Review ad creative and targeting settings",
            }
        }
    )

    type: Literal[
        "performance_drop", "click_fraud", "budget_overspend", "quality_drop"
    ] = Field(..., description="Type of anomaly")
    severity: Literal["low", "medium", "high", "critical"] = Field(
        ..., description="Alert severity"
    )
    description: str = Field(..., description="Human-readable description")
    detected_at: datetime = Field(..., description="Detection timestamp")
    recommended_action: str = Field(..., description="Recommended action to take")


class SeasonalityPattern(BaseModel):
    """Detected seasonality pattern."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "period": "weekly",
                "strength": 0.75,
                "peak_days": [5, 6],
                "low_days": [0, 1],
            }
        }
    )

    period: Literal["daily", "weekly", "monthly", "yearly"] = Field(
        ..., description="Seasonality period"
    )
    strength: float = Field(
        ..., ge=0.0, le=1.0, description="Seasonality strength (0-1)"
    )
    peak_days: List[int] = Field(..., description="Peak days/hours in period")
    low_days: List[int] = Field(..., description="Low days/hours in period")


class BudgetOptimizationResult(BaseModel):
    """Budget optimization recommendation."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "recommended_daily_budget": 1500.0,
                "channel_allocation": {
                    "google_ads": 800.0,
                    "yandex_direct": 500.0,
                    "meta_ads": 200.0,
                },
                "expected_conversions": 45,
                "expected_cpa": 33.33,
                "confidence": 0.85,
            }
        }
    )

    recommended_daily_budget: float = Field(
        ..., ge=0.0, description="Recommended daily budget"
    )
    channel_allocation: dict[str, float] = Field(
        ..., description="Budget allocation by channel"
    )
    expected_conversions: int = Field(
        ..., ge=0, description="Expected conversions"
    )
    expected_cpa: float = Field(..., ge=0.0, description="Expected cost per acquisition")
    confidence: float = Field(
        ..., ge=0.0, le=1.0, description="Confidence in recommendation (0-1)"
    )
