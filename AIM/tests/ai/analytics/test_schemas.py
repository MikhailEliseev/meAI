"""
Tests for Predictive Analytics Schemas
"""

import pytest
from datetime import datetime, timezone
from pydantic import ValidationError

from AIM.src.aim.ai.analytics.schemas import (
    ForecastRequest,
    ForecastResponse,
    AnomalyAlert,
    SeasonalityPattern,
    BudgetOptimizationResult,
)


class TestForecastRequest:
    """Test ForecastRequest schema."""

    def test_valid_request(self):
        """Test valid forecast request."""
        request = ForecastRequest(
            metric="conversions",
            horizon_days=30,
            confidence_level=0.95,
        )

        assert request.metric == "conversions"
        assert request.horizon_days == 30
        assert request.confidence_level == 0.95

    def test_default_values(self):
        """Test default values."""
        request = ForecastRequest(metric="clicks")

        assert request.horizon_days == 30
        assert request.confidence_level == 0.95

    def test_invalid_metric(self):
        """Test invalid metric."""
        with pytest.raises(ValidationError):
            ForecastRequest(metric="invalid_metric")

    def test_horizon_bounds(self):
        """Test horizon day bounds."""
        # Valid bounds
        ForecastRequest(metric="clicks", horizon_days=1)
        ForecastRequest(metric="clicks", horizon_days=365)

        # Invalid bounds
        with pytest.raises(ValidationError):
            ForecastRequest(metric="clicks", horizon_days=0)

        with pytest.raises(ValidationError):
            ForecastRequest(metric="clicks", horizon_days=366)

    def test_confidence_bounds(self):
        """Test confidence level bounds."""
        # Valid bounds
        ForecastRequest(metric="clicks", confidence_level=0.5)
        ForecastRequest(metric="clicks", confidence_level=0.99)

        # Invalid bounds
        with pytest.raises(ValidationError):
            ForecastRequest(metric="clicks", confidence_level=0.49)

        with pytest.raises(ValidationError):
            ForecastRequest(metric="clicks", confidence_level=1.0)


class TestForecastResponse:
    """Test ForecastResponse schema."""

    def test_valid_response(self):
        """Test valid forecast response."""
        response = ForecastResponse(
            predictions=[100.0, 105.0, 110.0],
            lower_bound=[90.0, 95.0, 100.0],
            upper_bound=[110.0, 115.0, 120.0],
            accuracy_score=0.85,
            seasonality_detected=True,
        )

        assert len(response.predictions) == 3
        assert len(response.lower_bound) == 3
        assert len(response.upper_bound) == 3
        assert response.accuracy_score == 0.85
        assert response.seasonality_detected is True

    def test_accuracy_bounds(self):
        """Test accuracy score bounds."""
        # Valid bounds
        ForecastResponse(
            predictions=[100.0],
            lower_bound=[90.0],
            upper_bound=[110.0],
            accuracy_score=0.0,
            seasonality_detected=False,
        )

        ForecastResponse(
            predictions=[100.0],
            lower_bound=[90.0],
            upper_bound=[110.0],
            accuracy_score=1.0,
            seasonality_detected=False,
        )

        # Invalid bounds
        with pytest.raises(ValidationError):
            ForecastResponse(
                predictions=[100.0],
                lower_bound=[90.0],
                upper_bound=[110.0],
                accuracy_score=-0.1,
                seasonality_detected=False,
            )

        with pytest.raises(ValidationError):
            ForecastResponse(
                predictions=[100.0],
                lower_bound=[90.0],
                upper_bound=[110.0],
                accuracy_score=1.1,
                seasonality_detected=False,
            )


class TestAnomalyAlert:
    """Test AnomalyAlert schema."""

    def test_valid_alert(self):
        """Test valid anomaly alert."""
        alert = AnomalyAlert(
            type="performance_drop",
            severity="high",
            description="CTR dropped by 45%",
            detected_at=datetime.now(timezone.utc),
            recommended_action="Review ad creative",
        )

        assert alert.type == "performance_drop"
        assert alert.severity == "high"
        assert "CTR" in alert.description
        assert alert.recommended_action == "Review ad creative"

    def test_invalid_type(self):
        """Test invalid anomaly type."""
        with pytest.raises(ValidationError):
            AnomalyAlert(
                type="invalid_type",
                severity="high",
                description="Test",
                detected_at=datetime.now(timezone.utc),
                recommended_action="Test",
            )

    def test_invalid_severity(self):
        """Test invalid severity."""
        with pytest.raises(ValidationError):
            AnomalyAlert(
                type="performance_drop",
                severity="invalid_severity",
                description="Test",
                detected_at=datetime.now(timezone.utc),
                recommended_action="Test",
            )

    def test_all_anomaly_types(self):
        """Test all anomaly types."""
        types = ["performance_drop", "click_fraud", "budget_overspend", "quality_drop"]

        for anomaly_type in types:
            alert = AnomalyAlert(
                type=anomaly_type,
                severity="medium",
                description=f"Test {anomaly_type}",
                detected_at=datetime.now(timezone.utc),
                recommended_action="Test action",
            )
            assert alert.type == anomaly_type

    def test_all_severities(self):
        """Test all severity levels."""
        severities = ["low", "medium", "high", "critical"]

        for severity in severities:
            alert = AnomalyAlert(
                type="performance_drop",
                severity=severity,
                description="Test",
                detected_at=datetime.now(timezone.utc),
                recommended_action="Test",
            )
            assert alert.severity == severity


class TestSeasonalityPattern:
    """Test SeasonalityPattern schema."""

    def test_valid_pattern(self):
        """Test valid seasonality pattern."""
        pattern = SeasonalityPattern(
            period="weekly",
            strength=0.75,
            peak_days=[5, 6],
            low_days=[0, 1],
        )

        assert pattern.period == "weekly"
        assert pattern.strength == 0.75
        assert pattern.peak_days == [5, 6]
        assert pattern.low_days == [0, 1]

    def test_strength_bounds(self):
        """Test strength bounds."""
        # Valid bounds
        SeasonalityPattern(
            period="weekly",
            strength=0.0,
            peak_days=[5],
            low_days=[0],
        )

        SeasonalityPattern(
            period="weekly",
            strength=1.0,
            peak_days=[5],
            low_days=[0],
        )

        # Invalid bounds
        with pytest.raises(ValidationError):
            SeasonalityPattern(
                period="weekly",
                strength=-0.1,
                peak_days=[5],
                low_days=[0],
            )

        with pytest.raises(ValidationError):
            SeasonalityPattern(
                period="weekly",
                strength=1.1,
                peak_days=[5],
                low_days=[0],
            )

    def test_all_periods(self):
        """Test all period types."""
        periods = ["daily", "weekly", "monthly", "yearly"]

        for period in periods:
            pattern = SeasonalityPattern(
                period=period,
                strength=0.5,
                peak_days=[1],
                low_days=[0],
            )
            assert pattern.period == period


class TestBudgetOptimizationResult:
    """Test BudgetOptimizationResult schema."""

    def test_valid_result(self):
        """Test valid optimization result."""
        result = BudgetOptimizationResult(
            recommended_daily_budget=1500.0,
            channel_allocation={
                "google_ads": 800.0,
                "yandex_direct": 500.0,
                "meta_ads": 200.0,
            },
            expected_conversions=45,
            expected_cpa=33.33,
            confidence=0.85,
        )

        assert result.recommended_daily_budget == 1500.0
        assert len(result.channel_allocation) == 3
        assert result.expected_conversions == 45
        assert result.expected_cpa == 33.33
        assert result.confidence == 0.85

    def test_budget_bounds(self):
        """Test budget bounds."""
        # Valid (zero budget)
        BudgetOptimizationResult(
            recommended_daily_budget=0.0,
            channel_allocation={},
            expected_conversions=0,
            expected_cpa=0.0,
            confidence=0.5,
        )

        # Invalid (negative budget)
        with pytest.raises(ValidationError):
            BudgetOptimizationResult(
                recommended_daily_budget=-100.0,
                channel_allocation={},
                expected_conversions=0,
                expected_cpa=0.0,
                confidence=0.5,
            )

    def test_conversions_bounds(self):
        """Test conversions bounds."""
        # Valid (zero conversions)
        BudgetOptimizationResult(
            recommended_daily_budget=1000.0,
            channel_allocation={"google_ads": 1000.0},
            expected_conversions=0,
            expected_cpa=0.0,
            confidence=0.5,
        )

        # Invalid (negative conversions)
        with pytest.raises(ValidationError):
            BudgetOptimizationResult(
                recommended_daily_budget=1000.0,
                channel_allocation={"google_ads": 1000.0},
                expected_conversions=-1,
                expected_cpa=0.0,
                confidence=0.5,
            )

    def test_confidence_bounds(self):
        """Test confidence bounds."""
        # Valid bounds
        BudgetOptimizationResult(
            recommended_daily_budget=1000.0,
            channel_allocation={"google_ads": 1000.0},
            expected_conversions=10,
            expected_cpa=100.0,
            confidence=0.0,
        )

        BudgetOptimizationResult(
            recommended_daily_budget=1000.0,
            channel_allocation={"google_ads": 1000.0},
            expected_conversions=10,
            expected_cpa=100.0,
            confidence=1.0,
        )

        # Invalid bounds
        with pytest.raises(ValidationError):
            BudgetOptimizationResult(
                recommended_daily_budget=1000.0,
                channel_allocation={"google_ads": 1000.0},
                expected_conversions=10,
                expected_cpa=100.0,
                confidence=-0.1,
            )

        with pytest.raises(ValidationError):
            BudgetOptimizationResult(
                recommended_daily_budget=1000.0,
                channel_allocation={"google_ads": 1000.0},
                expected_conversions=10,
                expected_cpa=100.0,
                confidence=1.1,
            )
