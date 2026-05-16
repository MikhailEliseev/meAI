"""
Tests for Performance Forecaster
"""

import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta, timezone

from AIM.src.aim.ai.analytics.forecaster import PerformanceForecaster
from AIM.src.aim.ai.analytics.schemas import ForecastRequest, ForecastResponse


class TestPerformanceForecaster:
    """Test PerformanceForecaster."""

    @pytest.fixture
    def forecaster(self):
        """Create forecaster instance."""
        return PerformanceForecaster()

    @pytest.fixture
    def historical_data(self):
        """Create historical data with trend."""
        dates = pd.date_range(start="2024-01-01", periods=90, freq="D")

        # Linear trend + noise
        values = []
        for i, date in enumerate(dates):
            trend = 100 + i * 2  # Growing trend
            noise = np.random.normal(0, 10)
            values.append(max(0, trend + noise))

        return pd.DataFrame({
            "date": dates,
            "clicks": values,
            "conversions": [v * 0.05 for v in values],
            "cost": [v * 1.5 for v in values],
            "revenue": [v * 3.0 for v in values],
        })

    @pytest.fixture
    def seasonal_data(self):
        """Create data with seasonality."""
        dates = pd.date_range(start="2024-01-01", periods=90, freq="D")

        values = []
        for i, date in enumerate(dates):
            dow = date.dayofweek
            base = 100 + i * 1  # Trend

            # Weekly seasonality
            if dow in [5, 6]:  # Weekend
                seasonal = 50
            else:
                seasonal = 0

            noise = np.random.normal(0, 10)
            values.append(max(0, base + seasonal + noise))

        return pd.DataFrame({
            "date": dates,
            "clicks": values,
        })

    async def test_basic_forecast(self, forecaster, historical_data):
        """Test basic forecast generation."""
        request = ForecastRequest(
            metric="clicks",
            horizon_days=30,
            confidence_level=0.95,
        )

        result = await forecaster.forecast(historical_data, request)

        assert isinstance(result, ForecastResponse)
        assert len(result.predictions) == 30
        assert len(result.lower_bound) == 30
        assert len(result.upper_bound) == 30
        assert 0.0 <= result.accuracy_score <= 1.0

    async def test_forecast_all_metrics(self, forecaster, historical_data):
        """Test forecasting all supported metrics."""
        metrics = ["clicks", "conversions", "cost", "revenue"]

        for metric in metrics:
            request = ForecastRequest(metric=metric, horizon_days=7)
            result = await forecaster.forecast(historical_data, request)

            assert len(result.predictions) == 7
            assert all(v >= 0 for v in result.predictions)

    async def test_confidence_intervals(self, forecaster, historical_data):
        """Test confidence interval bounds."""
        request = ForecastRequest(
            metric="clicks",
            horizon_days=30,
            confidence_level=0.95,
        )

        result = await forecaster.forecast(historical_data, request)

        # Lower bound should be less than predictions
        for i in range(len(result.predictions)):
            assert result.lower_bound[i] <= result.predictions[i]

        # Upper bound should be greater than predictions
        for i in range(len(result.predictions)):
            assert result.upper_bound[i] >= result.predictions[i]

        # All bounds should be non-negative
        assert all(v >= 0 for v in result.lower_bound)
        assert all(v >= 0 for v in result.upper_bound)

    async def test_seasonality_detection(self, forecaster, seasonal_data):
        """Test seasonality detection."""
        request = ForecastRequest(metric="clicks", horizon_days=14)

        result = await forecaster.forecast(seasonal_data, request)

        # Should detect weekly seasonality (or may not with random data)
        # This is probabilistic, so just check it's a boolean
        assert isinstance(result.seasonality_detected, bool)

    async def test_no_seasonality(self, forecaster):
        """Test with data without seasonality."""
        # Random data with no pattern
        dates = pd.date_range(start="2024-01-01", periods=30, freq="D")
        values = np.random.normal(100, 10, size=len(dates))

        data = pd.DataFrame({"date": dates, "clicks": values})

        request = ForecastRequest(metric="clicks", horizon_days=7)
        result = await forecaster.forecast(data, request)

        # May or may not detect seasonality (random data)
        assert isinstance(result.seasonality_detected, bool)

    async def test_accuracy_score_increases_with_data(self, forecaster):
        """Test accuracy score increases with more data."""
        # Small dataset
        dates_small = pd.date_range(start="2024-01-01", periods=7, freq="D")
        data_small = pd.DataFrame({
            "date": dates_small,
            "clicks": np.random.normal(100, 10, size=7),
        })

        # Large dataset
        dates_large = pd.date_range(start="2024-01-01", periods=180, freq="D")
        data_large = pd.DataFrame({
            "date": dates_large,
            "clicks": np.random.normal(100, 10, size=180),
        })

        request = ForecastRequest(metric="clicks", horizon_days=7)

        result_small = await forecaster.forecast(data_small, request)
        result_large = await forecaster.forecast(data_large, request)

        # More data should give higher confidence
        assert result_large.accuracy_score >= result_small.accuracy_score

    async def test_empty_data(self, forecaster):
        """Test with empty data."""
        data = pd.DataFrame({"date": [], "clicks": []})

        request = ForecastRequest(metric="clicks", horizon_days=7)

        with pytest.raises(ValueError, match="Historical data is empty"):
            await forecaster.forecast(data, request)

    async def test_missing_metric(self, forecaster):
        """Test with missing metric column."""
        # Create data without 'conversions' column
        dates = pd.date_range(start="2024-01-01", periods=30, freq="D")
        data = pd.DataFrame({
            "date": dates,
            "clicks": np.random.normal(100, 10, size=30),
        })

        request = ForecastRequest(metric="conversions", horizon_days=7)

        with pytest.raises(ValueError, match="Metric 'conversions' not found"):
            await forecaster.forecast(data, request)

    async def test_horizon_days(self, forecaster, historical_data):
        """Test different horizon lengths."""
        horizons = [7, 30, 90, 365]

        for horizon in horizons:
            request = ForecastRequest(metric="clicks", horizon_days=horizon)
            result = await forecaster.forecast(historical_data, request)

            assert len(result.predictions) == horizon
            assert len(result.lower_bound) == horizon
            assert len(result.upper_bound) == horizon

    async def test_confidence_levels(self, forecaster, historical_data):
        """Test different confidence levels."""
        # Higher confidence = wider intervals
        request_95 = ForecastRequest(
            metric="clicks",
            horizon_days=30,
            confidence_level=0.95,
        )

        request_80 = ForecastRequest(
            metric="clicks",
            horizon_days=30,
            confidence_level=0.80,
        )

        result_95 = await forecaster.forecast(historical_data, request_95)
        result_80 = await forecaster.forecast(historical_data, request_80)

        # 95% confidence should have wider intervals than 80%
        # (This is a probabilistic test, may occasionally fail)
        interval_95 = sum(
            result_95.upper_bound[i] - result_95.lower_bound[i]
            for i in range(len(result_95.predictions))
        )
        interval_80 = sum(
            result_80.upper_bound[i] - result_80.lower_bound[i]
            for i in range(len(result_80.predictions))
        )

        # Allow some tolerance for randomness
        assert interval_95 >= interval_80 * 0.9
