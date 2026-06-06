"""
Tests for Anomaly Detector
"""

import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timezone

from src.aim.ai.analytics.anomaly_detector import AnomalyDetector
from src.aim.ai.analytics.schemas import AnomalyAlert


class TestAnomalyDetector:
    """Test AnomalyDetector."""

    @pytest.fixture
    def detector(self):
        """Create detector instance."""
        return AnomalyDetector(
            performance_drop_threshold=0.3,
            budget_variance_threshold=0.2,
            quality_drop_threshold=2.0,
            z_score_threshold=3.0,
        )

    @pytest.fixture
    def normal_historical_data(self):
        """Create normal historical data."""
        return pd.DataFrame({
            "clicks": [100] * 30,
            "impressions": [5000] * 30,
            "conversions": [5] * 30,
            "cost": [500] * 30,
            "quality_score": [8.0] * 30,
        })

    @pytest.fixture
    def normal_current_data(self):
        """Create normal current data."""
        return pd.DataFrame({
            "clicks": [100] * 2,
            "impressions": [5000] * 2,
            "conversions": [5] * 2,
            "cost": [500] * 2,
            "quality_score": [8.0] * 2,
        })

    async def test_no_anomalies(
        self, detector, normal_current_data, normal_historical_data
    ):
        """Test with no anomalies."""
        alerts = await detector.detect(
            normal_current_data, normal_historical_data, budget_plan=1000.0
        )

        assert len(alerts) == 0

    async def test_ctr_drop_detection(self, detector, normal_historical_data):
        """Test CTR drop detection."""
        # Current data with 50% CTR drop
        current_data = pd.DataFrame({
            "clicks": [50] * 2,  # Half the clicks
            "impressions": [5000] * 2,
            "conversions": [5] * 2,
        })

        alerts = await detector.detect(current_data, normal_historical_data)

        # Should detect CTR drop
        ctr_alerts = [a for a in alerts if a.type == "performance_drop" and "CTR" in a.description]
        assert len(ctr_alerts) > 0

        alert = ctr_alerts[0]
        assert alert.severity in ["medium", "high", "critical"]
        assert "50" in alert.description  # 50% drop

    async def test_conversion_rate_drop_detection(
        self, detector, normal_historical_data
    ):
        """Test conversion rate drop detection."""
        # Current data with 60% conversion rate drop
        current_data = pd.DataFrame({
            "clicks": [100] * 2,
            "impressions": [5000] * 2,
            "conversions": [2] * 2,  # 60% fewer conversions
        })

        alerts = await detector.detect(current_data, normal_historical_data)

        # Should detect conversion rate drop
        cvr_alerts = [
            a
            for a in alerts
            if a.type == "performance_drop" and "Conversion rate" in a.description
        ]
        assert len(cvr_alerts) > 0

        alert = cvr_alerts[0]
        assert alert.severity in ["medium", "high", "critical"]

    async def test_click_fraud_zero_conversions(self, detector, normal_historical_data):
        """Test click fraud detection with zero conversions."""
        # High clicks, zero conversions
        current_data = pd.DataFrame({
            "clicks": [150] * 2,
            "impressions": [5000] * 2,
            "conversions": [0] * 2,  # Zero conversions
        })

        alerts = await detector.detect(current_data, normal_historical_data)

        # Should detect click fraud
        fraud_alerts = [a for a in alerts if a.type == "click_fraud"]
        assert len(fraud_alerts) > 0

        alert = fraud_alerts[0]
        assert alert.severity == "high"
        assert "0 conversions" in alert.description

    async def test_click_fraud_high_ctr(self, detector, normal_historical_data):
        """Test click fraud detection with abnormally high CTR."""
        # 25% CTR (very suspicious)
        current_data = pd.DataFrame({
            "clicks": [1250] * 2,
            "impressions": [5000] * 2,
            "conversions": [5] * 2,
        })

        alerts = await detector.detect(current_data, normal_historical_data)

        # Should detect click fraud
        fraud_alerts = [a for a in alerts if a.type == "click_fraud"]
        assert len(fraud_alerts) > 0

        alert = fraud_alerts[0]
        assert alert.severity == "critical"
        assert "Abnormally high CTR" in alert.description

    async def test_budget_overspend_detection(self, detector, normal_historical_data):
        """Test budget overspend detection."""
        # 30% over budget
        current_data = pd.DataFrame({
            "clicks": [100] * 2,
            "impressions": [5000] * 2,
            "conversions": [5] * 2,
            "cost": [650] * 2,  # 30% over budget
        })

        alerts = await detector.detect(
            current_data, normal_historical_data, budget_plan=500.0
        )

        # Should detect budget overspend
        budget_alerts = [a for a in alerts if a.type == "budget_overspend"]
        assert len(budget_alerts) > 0

        alert = budget_alerts[0]
        assert alert.severity in ["medium", "high", "critical"]
        assert "30" in alert.description  # 30% over

    async def test_quality_score_drop_detection(self, detector, normal_historical_data):
        """Test quality score drop detection."""
        # Quality score drops from 8.0 to 5.0 (3 points)
        current_data = pd.DataFrame({
            "clicks": [100] * 2,
            "impressions": [5000] * 2,
            "conversions": [5] * 2,
            "quality_score": [5.0] * 2,
        })

        alerts = await detector.detect(current_data, normal_historical_data)

        # Should detect quality score drop
        quality_alerts = [a for a in alerts if a.type == "quality_drop"]
        assert len(quality_alerts) > 0

        alert = quality_alerts[0]
        assert alert.severity in ["medium", "high"]
        assert "3.0" in alert.description  # 3 point drop

    async def test_severity_calculation(self, detector, normal_historical_data):
        """Test severity calculation for different drop percentages."""
        # 40% drop = medium
        current_40 = pd.DataFrame({
            "clicks": [60] * 2,
            "impressions": [5000] * 2,
            "conversions": [5] * 2,
        })

        # 60% drop = high
        current_60 = pd.DataFrame({
            "clicks": [40] * 2,
            "impressions": [5000] * 2,
            "conversions": [5] * 2,
        })

        # 80% drop = critical
        current_80 = pd.DataFrame({
            "clicks": [20] * 2,
            "impressions": [5000] * 2,
            "conversions": [5] * 2,
        })

        alerts_40 = await detector.detect(current_40, normal_historical_data)
        alerts_60 = await detector.detect(current_60, normal_historical_data)
        alerts_80 = await detector.detect(current_80, normal_historical_data)

        # Get CTR drop alerts
        alert_40 = next(
            (a for a in alerts_40 if a.type == "performance_drop" and "CTR" in a.description),
            None,
        )
        alert_60 = next(
            (a for a in alerts_60 if a.type == "performance_drop" and "CTR" in a.description),
            None,
        )
        alert_80 = next(
            (a for a in alerts_80 if a.type == "performance_drop" and "CTR" in a.description),
            None,
        )

        assert alert_40 is not None
        assert alert_60 is not None
        assert alert_80 is not None

        assert alert_40.severity == "medium"
        assert alert_60.severity == "high"
        assert alert_80.severity == "critical"

    async def test_multiple_anomalies(self, detector, normal_historical_data):
        """Test detection of multiple anomalies."""
        # CTR drop + budget overspend + quality drop
        current_data = pd.DataFrame({
            "clicks": [50] * 2,  # 50% CTR drop
            "impressions": [5000] * 2,
            "conversions": [5] * 2,
            "cost": [650] * 2,  # 30% over budget
            "quality_score": [5.0] * 2,  # 3 point drop
        })

        alerts = await detector.detect(
            current_data, normal_historical_data, budget_plan=500.0
        )

        # Should detect all three anomalies
        assert len(alerts) >= 3

        types = [a.type for a in alerts]
        assert "performance_drop" in types
        assert "budget_overspend" in types
        assert "quality_drop" in types

    async def test_no_budget_plan(self, detector, normal_current_data, normal_historical_data):
        """Test without budget plan."""
        # Should not check budget overspend
        alerts = await detector.detect(
            normal_current_data, normal_historical_data, budget_plan=None
        )

        # No budget alerts
        budget_alerts = [a for a in alerts if a.type == "budget_overspend"]
        assert len(budget_alerts) == 0

    async def test_missing_columns(self, detector, normal_historical_data):
        """Test with missing columns."""
        # Missing conversions column
        current_data = pd.DataFrame({
            "clicks": [100] * 2,
            "impressions": [5000] * 2,
        })

        # Should not crash, just skip conversion rate check
        alerts = await detector.detect(current_data, normal_historical_data)

        # No conversion rate alerts
        cvr_alerts = [
            a
            for a in alerts
            if a.type == "performance_drop" and "Conversion rate" in a.description
        ]
        assert len(cvr_alerts) == 0
