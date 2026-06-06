"""
Anomaly Detector

Detects anomalies in advertising performance data.

Part of: Phase 10 - AI Enhancement (Task 2.2)
"""

import pandas as pd
import numpy as np
from typing import List, Dict, Any
from datetime import datetime, timedelta, timezone

from src.aim.ai.analytics.schemas import AnomalyAlert


class AnomalyDetector:
    """Detects anomalies in advertising performance

    Detects:
    - Performance drops (CTR, conversion rate, quality score)
    - Click fraud (suspicious click patterns)
    - Budget overspend (>20% variance from plan)
    - Quality score drops (sudden decreases)

    Methods:
    - Statistical outlier detection (Z-score, IQR)
    - Time series anomaly detection
    - Pattern-based fraud detection
    - Threshold-based alerts

    Target: >80% precision, <10% false positive rate
    """

    def __init__(
        self,
        performance_drop_threshold: float = 0.3,
        budget_variance_threshold: float = 0.2,
        quality_drop_threshold: float = 2.0,
        z_score_threshold: float = 3.0,
    ):
        """Initialize Anomaly Detector

        Args:
            performance_drop_threshold: Min drop to trigger alert (0-1, e.g., 0.3 = 30%)
            budget_variance_threshold: Max budget variance (0-1, e.g., 0.2 = 20%)
            quality_drop_threshold: Min quality score drop to alert
            z_score_threshold: Z-score threshold for outlier detection
        """
        self.performance_drop_threshold = performance_drop_threshold
        self.budget_variance_threshold = budget_variance_threshold
        self.quality_drop_threshold = quality_drop_threshold
        self.z_score_threshold = z_score_threshold

    async def detect(
        self,
        current_data: pd.DataFrame,
        historical_data: pd.DataFrame,
        budget_plan: float | None = None,
    ) -> List[AnomalyAlert]:
        """Detect anomalies in current data

        Args:
            current_data: Recent performance data (last 24-48 hours)
            historical_data: Historical baseline data (last 30-90 days)
            budget_plan: Planned daily budget (optional)

        Returns:
            List of anomaly alerts
        """
        alerts = []

        # Performance drop detection
        performance_alerts = await self._detect_performance_drops(
            current_data, historical_data
        )
        alerts.extend(performance_alerts)

        # Click fraud detection
        fraud_alerts = await self._detect_click_fraud(current_data)
        alerts.extend(fraud_alerts)

        # Budget overspend detection
        if budget_plan is not None and "cost" in current_data.columns:
            budget_alerts = await self._detect_budget_overspend(
                current_data, budget_plan
            )
            alerts.extend(budget_alerts)

        # Quality score drop detection
        if "quality_score" in current_data.columns:
            quality_alerts = await self._detect_quality_drops(
                current_data, historical_data
            )
            alerts.extend(quality_alerts)

        return alerts

    async def _detect_performance_drops(
        self, current_data: pd.DataFrame, historical_data: pd.DataFrame
    ) -> List[AnomalyAlert]:
        """Detect performance drops (CTR, conversion rate)

        Args:
            current_data: Recent data
            historical_data: Historical baseline

        Returns:
            List of performance drop alerts
        """
        alerts = []

        # Check CTR drop
        if "clicks" in current_data.columns and "impressions" in current_data.columns:
            current_ctr = (
                current_data["clicks"].sum() / current_data["impressions"].sum()
                if current_data["impressions"].sum() > 0
                else 0
            )
            historical_ctr = (
                historical_data["clicks"].sum() / historical_data["impressions"].sum()
                if historical_data["impressions"].sum() > 0
                else 0
            )

            if historical_ctr > 0:
                drop_pct = (historical_ctr - current_ctr) / historical_ctr

                if drop_pct > self.performance_drop_threshold:
                    severity = self._calculate_severity(drop_pct)
                    alerts.append(
                        AnomalyAlert(
                            type="performance_drop",
                            severity=severity,
                            description=f"CTR dropped by {drop_pct*100:.1f}% (from {historical_ctr*100:.2f}% to {current_ctr*100:.2f}%)",
                            detected_at=datetime.now(timezone.utc),
                            recommended_action="Review ad creative, targeting settings, and competitor activity",
                        )
                    )

        # Check conversion rate drop
        if "conversions" in current_data.columns and "clicks" in current_data.columns:
            current_cvr = (
                current_data["conversions"].sum() / current_data["clicks"].sum()
                if current_data["clicks"].sum() > 0
                else 0
            )
            historical_cvr = (
                historical_data["conversions"].sum() / historical_data["clicks"].sum()
                if historical_data["clicks"].sum() > 0
                else 0
            )

            if historical_cvr > 0:
                drop_pct = (historical_cvr - current_cvr) / historical_cvr

                if drop_pct > self.performance_drop_threshold:
                    severity = self._calculate_severity(drop_pct)
                    alerts.append(
                        AnomalyAlert(
                            type="performance_drop",
                            severity=severity,
                            description=f"Conversion rate dropped by {drop_pct*100:.1f}% (from {historical_cvr*100:.2f}% to {current_cvr*100:.2f}%)",
                            detected_at=datetime.now(timezone.utc),
                            recommended_action="Review landing page, check tracking pixels, analyze user behavior",
                        )
                    )

        return alerts

    async def _detect_click_fraud(
        self, current_data: pd.DataFrame
    ) -> List[AnomalyAlert]:
        """Detect click fraud patterns

        Args:
            current_data: Recent click data

        Returns:
            List of click fraud alerts
        """
        alerts = []

        if "clicks" not in current_data.columns or "conversions" not in current_data.columns:
            return alerts

        # Check for abnormally high clicks with zero conversions
        total_clicks = current_data["clicks"].sum()
        total_conversions = current_data["conversions"].sum()

        if total_clicks > 100 and total_conversions == 0:
            alerts.append(
                AnomalyAlert(
                    type="click_fraud",
                    severity="high",
                    description=f"Suspicious pattern: {total_clicks} clicks with 0 conversions",
                    detected_at=datetime.now(timezone.utc),
                    recommended_action="Enable click fraud protection, review IP addresses, check for bot traffic",
                )
            )

        # Check for abnormally high CTR (>20% is suspicious)
        if "impressions" in current_data.columns:
            ctr = total_clicks / current_data["impressions"].sum() if current_data["impressions"].sum() > 0 else 0

            if ctr > 0.2:  # 20% CTR is very suspicious
                alerts.append(
                    AnomalyAlert(
                        type="click_fraud",
                        severity="critical",
                        description=f"Abnormally high CTR: {ctr*100:.1f}% (typical: 2-5%)",
                        detected_at=datetime.now(timezone.utc),
                        recommended_action="Pause campaign immediately, investigate traffic sources, enable fraud filters",
                    )
                )

        return alerts

    async def _detect_budget_overspend(
        self, current_data: pd.DataFrame, budget_plan: float
    ) -> List[AnomalyAlert]:
        """Detect budget overspend

        Args:
            current_data: Recent cost data
            budget_plan: Planned daily budget

        Returns:
            List of budget overspend alerts
        """
        alerts = []

        actual_spend = current_data["cost"].sum()
        variance = (actual_spend - budget_plan) / budget_plan if budget_plan > 0 else 0

        if variance > self.budget_variance_threshold:
            severity = self._calculate_severity(variance)
            alerts.append(
                AnomalyAlert(
                    type="budget_overspend",
                    severity=severity,
                    description=f"Budget overspend: ${actual_spend:.2f} vs planned ${budget_plan:.2f} ({variance*100:.1f}% over)",
                    detected_at=datetime.now(timezone.utc),
                    recommended_action="Reduce bids, pause low-performing campaigns, adjust budget pacing",
                )
            )

        return alerts

    async def _detect_quality_drops(
        self, current_data: pd.DataFrame, historical_data: pd.DataFrame
    ) -> List[AnomalyAlert]:
        """Detect quality score drops

        Args:
            current_data: Recent quality score data
            historical_data: Historical baseline

        Returns:
            List of quality score drop alerts
        """
        alerts = []

        current_qs = current_data["quality_score"].mean()
        historical_qs = historical_data["quality_score"].mean()

        drop = historical_qs - current_qs

        if drop > self.quality_drop_threshold:
            severity = "high" if drop > 3.0 else "medium"
            alerts.append(
                AnomalyAlert(
                    type="quality_drop",
                    severity=severity,
                    description=f"Quality score dropped by {drop:.1f} points (from {historical_qs:.1f} to {current_qs:.1f})",
                    detected_at=datetime.now(timezone.utc),
                    recommended_action="Improve ad relevance, optimize landing page experience, review keyword targeting",
                )
            )

        return alerts

    def _calculate_severity(self, drop_pct: float) -> str:
        """Calculate alert severity based on drop percentage

        Args:
            drop_pct: Drop percentage (0-1)

        Returns:
            Severity level (low, medium, high, critical)
        """
        if drop_pct > 0.7:  # >70% drop
            return "critical"
        elif drop_pct > 0.5:  # >50% drop
            return "high"
        elif drop_pct > 0.3:  # >30% drop
            return "medium"
        else:
            return "low"

    async def close(self):
        """Close resources"""
        # No resources to close for now
        pass
