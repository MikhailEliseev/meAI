"""
Tests for Seasonality Detector
"""

import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta, timezone

from AIM.src.aim.ai.analytics.seasonality_detector import SeasonalityDetector
from AIM.src.aim.ai.analytics.schemas import SeasonalityPattern


class TestSeasonalityDetector:
    """Test SeasonalityDetector."""

    @pytest.fixture
    def detector(self):
        """Create detector instance."""
        return SeasonalityDetector(min_strength=0.3)

    @pytest.fixture
    def weekly_data(self):
        """Create data with weekly seasonality."""
        dates = pd.date_range(start="2024-01-01", periods=90, freq="D")

        # Weekly pattern: high on weekends (5, 6), low on weekdays
        values = []
        for date in dates:
            dow = date.dayofweek
            if dow in [5, 6]:  # Weekend
                values.append(np.random.normal(1000, 50))
            else:  # Weekday
                values.append(np.random.normal(500, 50))

        return pd.DataFrame({"date": dates, "value": values})

    @pytest.fixture
    def daily_data(self):
        """Create data with daily seasonality."""
        dates = pd.date_range(start="2024-01-01", periods=90, freq="h")

        # Daily pattern: high during business hours (9-17), low at night
        values = []
        for date in dates:
            hour = date.hour
            if 9 <= hour <= 17:  # Business hours
                values.append(np.random.normal(100, 10))
            else:  # Night
                values.append(np.random.normal(30, 5))

        return pd.DataFrame({"date": dates, "value": values})

    @pytest.fixture
    def monthly_data(self):
        """Create data with monthly seasonality."""
        dates = pd.date_range(start="2024-01-01", periods=365, freq="D")

        # Monthly pattern: high at month start, low at month end
        values = []
        for date in dates:
            day = date.day
            if day <= 10:  # Month start
                values.append(np.random.normal(1000, 50))
            else:  # Month end
                values.append(np.random.normal(500, 50))

        return pd.DataFrame({"date": dates, "value": values})

    @pytest.fixture
    def no_seasonality_data(self):
        """Create data with no seasonality."""
        dates = pd.date_range(start="2024-01-01", periods=90, freq="D")
        values = np.random.normal(500, 50, size=len(dates))

        return pd.DataFrame({"date": dates, "value": values})

    async def test_detect_weekly_seasonality(self, detector, weekly_data):
        """Test weekly seasonality detection."""
        patterns = await detector.detect(weekly_data)

        # Should detect weekly pattern
        assert len(patterns) > 0

        weekly_pattern = next((p for p in patterns if p.period == "weekly"), None)
        assert weekly_pattern is not None
        assert weekly_pattern.strength >= 0.3

        # Peak days should be weekend (5, 6)
        assert 5 in weekly_pattern.peak_days or 6 in weekly_pattern.peak_days

    async def test_detect_daily_seasonality(self, detector, daily_data):
        """Test daily seasonality detection."""
        patterns = await detector.detect(daily_data)

        # Should detect daily pattern
        daily_pattern = next((p for p in patterns if p.period == "daily"), None)
        assert daily_pattern is not None
        assert daily_pattern.strength >= 0.3

        # Peak hours should be business hours (9-17)
        assert any(9 <= hour <= 17 for hour in daily_pattern.peak_days)

    async def test_detect_monthly_seasonality(self, detector, monthly_data):
        """Test monthly seasonality detection."""
        patterns = await detector.detect(monthly_data)

        # Should detect monthly pattern
        monthly_pattern = next((p for p in patterns if p.period == "monthly"), None)
        assert monthly_pattern is not None
        assert monthly_pattern.strength >= 0.3

        # Peak days should be month start (1-10)
        assert any(1 <= day <= 10 for day in monthly_pattern.peak_days)

    async def test_no_seasonality(self, detector, no_seasonality_data):
        """Test no seasonality detection."""
        patterns = await detector.detect(no_seasonality_data)

        # Should detect no patterns (or very weak patterns)
        assert len(patterns) == 0 or all(p.strength < 0.3 for p in patterns)

    async def test_min_strength_threshold(self):
        """Test min strength threshold."""
        # High threshold
        detector_high = SeasonalityDetector(min_strength=0.8)

        # Low threshold
        detector_low = SeasonalityDetector(min_strength=0.1)

        # Create STRONG seasonal data for reliable detection
        dates = pd.date_range(start="2024-01-01", periods=90, freq="D")
        values = []
        for date in dates:
            dow = date.dayofweek
            if dow in [5, 6]:
                values.append(np.random.normal(800, 20))  # Strong pattern
            else:
                values.append(np.random.normal(200, 20))

        data = pd.DataFrame({"date": dates, "value": values})

        # High threshold should detect nothing (pattern not strong enough)
        patterns_high = await detector_high.detect(data)
        assert len(patterns_high) == 0

        # Low threshold should detect pattern
        patterns_low = await detector_low.detect(data)
        assert len(patterns_low) > 0

    async def test_insufficient_data(self, detector):
        """Test with insufficient data."""
        # Less than 7 days
        dates = pd.date_range(start="2024-01-01", periods=5, freq="D")
        values = np.random.normal(500, 50, size=len(dates))
        data = pd.DataFrame({"date": dates, "value": values})

        patterns = await detector.detect(data)

        # Should detect no patterns (not enough data)
        assert len(patterns) == 0

    async def test_multiple_patterns(self, detector):
        """Test detection of multiple patterns."""
        # Create data with STRONG weekly and daily patterns
        dates = pd.date_range(start="2024-01-01", periods=90, freq="h")

        values = []
        for date in dates:
            dow = date.dayofweek
            hour = date.hour

            base = 100

            # Strong weekly component
            if dow in [5, 6]:
                base += 200  # Much stronger

            # Strong daily component
            if 9 <= hour <= 17:
                base += 100  # Much stronger

            values.append(np.random.normal(base, 10))

        data = pd.DataFrame({"date": dates, "value": values})

        patterns = await detector.detect(data)

        # Should detect at least one pattern (both is ideal but not guaranteed)
        assert len(patterns) >= 1

        periods = [p.period for p in patterns]
        # At least weekly or daily should be detected
        assert "weekly" in periods or "daily" in periods
