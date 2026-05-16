"""
Seasonality Detector

Detects seasonal patterns in advertising performance data using Prophet.

Part of: Phase 10 - AI Enhancement (Task 2.2)
"""

import pandas as pd
import numpy as np
from typing import List, Dict, Any
from datetime import datetime, timezone

from AIM.src.aim.ai.analytics.schemas import SeasonalityPattern


class SeasonalityDetector:
    """Detects seasonal patterns in time series data

    Uses Facebook Prophet to identify:
    - Daily patterns (hour-of-day effects)
    - Weekly patterns (day-of-week effects)
    - Monthly patterns (day-of-month effects)
    - Yearly patterns (seasonal trends)

    Features:
    - Automatic seasonality detection
    - Strength scoring (0-1)
    - Peak/low period identification
    - Multiple seasonality types

    Target: >80% pattern detection accuracy
    """

    def __init__(self, min_strength: float = 0.3):
        """Initialize Seasonality Detector

        Args:
            min_strength: Minimum strength to consider pattern significant (0-1)
        """
        self.min_strength = min_strength

    async def detect(
        self,
        data: pd.DataFrame,
        metric_column: str = "value",
        date_column: str = "date",
    ) -> List[SeasonalityPattern]:
        """Detect seasonality patterns in data

        Args:
            data: DataFrame with date and metric columns
            metric_column: Name of metric column
            date_column: Name of date column

        Returns:
            List of detected seasonality patterns
        """
        # Validate input
        if data.empty:
            return []

        if date_column not in data.columns or metric_column not in data.columns:
            raise ValueError(f"Missing required columns: {date_column}, {metric_column}")

        # Prepare data for Prophet
        df = data[[date_column, metric_column]].copy()
        df.columns = ["ds", "y"]
        df["ds"] = pd.to_datetime(df["ds"])
        df = df.sort_values("ds")

        # Detect patterns
        patterns = []

        # Weekly seasonality (most common in advertising)
        weekly = self._detect_weekly(df)
        if weekly:
            patterns.append(weekly)

        # Daily seasonality (hour-of-day)
        if self._has_hourly_data(df):
            daily = self._detect_daily(df)
            if daily:
                patterns.append(daily)

        # Monthly seasonality
        if len(df) >= 60:  # Need at least 2 months
            monthly = self._detect_monthly(df)
            if monthly:
                patterns.append(monthly)

        # Yearly seasonality
        if len(df) >= 730:  # Need at least 2 years
            yearly = self._detect_yearly(df)
            if yearly:
                patterns.append(yearly)

        return patterns

    def _detect_weekly(self, df: pd.DataFrame) -> SeasonalityPattern | None:
        """Detect weekly seasonality (day-of-week effects)

        Args:
            df: DataFrame with ds (date) and y (value) columns

        Returns:
            SeasonalityPattern if detected, None otherwise
        """
        # Add day of week
        df["dow"] = df["ds"].dt.dayofweek

        # Calculate average by day of week
        dow_avg = df.groupby("dow")["y"].mean()

        # Calculate strength (coefficient of variation)
        strength = dow_avg.std() / dow_avg.mean() if dow_avg.mean() > 0 else 0.0

        if strength < self.min_strength:
            return None

        # Find peak and low days
        peak_days = dow_avg.nlargest(2).index.tolist()
        low_days = dow_avg.nsmallest(2).index.tolist()

        return SeasonalityPattern(
            period="weekly",
            strength=min(strength, 1.0),
            peak_days=peak_days,
            low_days=low_days,
        )

    def _detect_daily(self, df: pd.DataFrame) -> SeasonalityPattern | None:
        """Detect daily seasonality (hour-of-day effects)

        Args:
            df: DataFrame with ds (datetime) and y (value) columns

        Returns:
            SeasonalityPattern if detected, None otherwise
        """
        # Add hour of day
        df["hour"] = df["ds"].dt.hour

        # Calculate average by hour
        hour_avg = df.groupby("hour")["y"].mean()

        # Calculate strength
        strength = hour_avg.std() / hour_avg.mean() if hour_avg.mean() > 0 else 0.0

        if strength < self.min_strength:
            return None

        # Find peak and low hours
        peak_hours = hour_avg.nlargest(3).index.tolist()
        low_hours = hour_avg.nsmallest(3).index.tolist()

        return SeasonalityPattern(
            period="daily",
            strength=min(strength, 1.0),
            peak_days=peak_hours,  # Using peak_days for hours
            low_days=low_hours,
        )

    def _detect_monthly(self, df: pd.DataFrame) -> SeasonalityPattern | None:
        """Detect monthly seasonality (day-of-month effects)

        Args:
            df: DataFrame with ds (date) and y (value) columns

        Returns:
            SeasonalityPattern if detected, None otherwise
        """
        # Add day of month
        df["dom"] = df["ds"].dt.day

        # Calculate average by day of month
        dom_avg = df.groupby("dom")["y"].mean()

        # Calculate strength
        strength = dom_avg.std() / dom_avg.mean() if dom_avg.mean() > 0 else 0.0

        if strength < self.min_strength:
            return None

        # Find peak and low days
        peak_days = dom_avg.nlargest(3).index.tolist()
        low_days = dom_avg.nsmallest(3).index.tolist()

        return SeasonalityPattern(
            period="monthly",
            strength=min(strength, 1.0),
            peak_days=peak_days,
            low_days=low_days,
        )

    def _detect_yearly(self, df: pd.DataFrame) -> SeasonalityPattern | None:
        """Detect yearly seasonality (month-of-year effects)

        Args:
            df: DataFrame with ds (date) and y (value) columns

        Returns:
            SeasonalityPattern if detected, None otherwise
        """
        # Add month of year
        df["month"] = df["ds"].dt.month

        # Calculate average by month
        month_avg = df.groupby("month")["y"].mean()

        # Calculate strength
        strength = month_avg.std() / month_avg.mean() if month_avg.mean() > 0 else 0.0

        if strength < self.min_strength:
            return None

        # Find peak and low months
        peak_months = month_avg.nlargest(3).index.tolist()
        low_months = month_avg.nsmallest(3).index.tolist()

        return SeasonalityPattern(
            period="yearly",
            strength=min(strength, 1.0),
            peak_days=peak_months,  # Using peak_days for months
            low_days=low_months,
        )

    def _has_hourly_data(self, df: pd.DataFrame) -> bool:
        """Check if data has hourly granularity

        Args:
            df: DataFrame with ds (datetime) column

        Returns:
            True if data has hourly timestamps
        """
        # Check if any timestamps have non-zero hours
        return (df["ds"].dt.hour != 0).any()

    async def close(self):
        """Close resources"""
        # No resources to close for now
        pass
