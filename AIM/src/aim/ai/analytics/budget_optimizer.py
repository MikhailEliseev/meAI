"""
Budget Optimizer

Optimizes budget allocation across channels using Thompson Sampling and PID control.

Part of: Phase 10 - AI Enhancement (Task 2.2)
"""

import numpy as np
from typing import Dict, List, Any
from datetime import datetime, timezone

from src.aim.ai.analytics.schemas import BudgetOptimizationResult


class BudgetOptimizer:
    """Optimizes advertising budget allocation

    Uses:
    - Thompson Sampling for channel allocation (exploration vs exploitation)
    - PID controller for budget pacing (smooth spending)
    - Multi-objective optimization (conversions, CPA, quality score)

    Features:
    - Channel-level budget allocation
    - Real-time budget pacing
    - Performance-based reallocation
    - Constraint handling (min/max budgets)

    Target: <5% budget pacing variance, maximize conversions
    """

    def __init__(
        self,
        kp: float = 0.5,
        ki: float = 0.1,
        kd: float = 0.2,
        exploration_rate: float = 0.1,
    ):
        """Initialize Budget Optimizer

        Args:
            kp: Proportional gain for PID controller
            ki: Integral gain for PID controller
            kd: Derivative gain for PID controller
            exploration_rate: Thompson Sampling exploration rate (0-1)
        """
        self.kp = kp
        self.ki = ki
        self.kd = kd
        self.exploration_rate = exploration_rate

        # PID state
        self.integral_error = 0.0
        self.previous_error = 0.0

        # Thompson Sampling state (Beta distribution parameters)
        self.channel_alphas: Dict[str, float] = {}
        self.channel_betas: Dict[str, float] = {}

    async def optimize(
        self,
        total_budget: float,
        channel_performance: Dict[str, Dict[str, float]],
        constraints: Dict[str, Dict[str, float]] | None = None,
    ) -> BudgetOptimizationResult:
        """Optimize budget allocation across channels

        Args:
            total_budget: Total daily budget to allocate
            channel_performance: Performance data by channel
                {
                    "google_ads": {"conversions": 20, "cost": 500, "clicks": 100},
                    "yandex_direct": {"conversions": 15, "cost": 400, "clicks": 80},
                }
            constraints: Optional min/max budget constraints by channel
                {
                    "google_ads": {"min": 200, "max": 1000},
                    "yandex_direct": {"min": 100, "max": 800},
                }

        Returns:
            BudgetOptimizationResult with recommended allocation
        """
        # Initialize Thompson Sampling for new channels
        for channel in channel_performance.keys():
            if channel not in self.channel_alphas:
                self.channel_alphas[channel] = 1.0
                self.channel_betas[channel] = 1.0

        # Update Thompson Sampling parameters based on performance
        self._update_thompson_sampling(channel_performance)

        # Sample from Beta distributions for each channel
        channel_scores = self._sample_channel_scores()

        # Allocate budget proportionally to scores
        allocation = self._allocate_budget(
            total_budget, channel_scores, constraints
        )

        # Calculate expected performance
        expected_conversions = self._calculate_expected_conversions(
            allocation, channel_performance
        )
        expected_cpa = (
            total_budget / expected_conversions if expected_conversions > 0 else 0
        )

        # Calculate confidence (based on data volume)
        confidence = self._calculate_confidence(channel_performance)

        return BudgetOptimizationResult(
            recommended_daily_budget=total_budget,
            channel_allocation=allocation,
            expected_conversions=int(expected_conversions),
            expected_cpa=expected_cpa,
            confidence=confidence,
        )

    def pace_budget(
        self,
        target_daily_budget: float,
        current_spend: float,
        hours_elapsed: float,
    ) -> float:
        """Calculate optimal hourly budget using PID controller

        Args:
            target_daily_budget: Target daily budget
            current_spend: Current spend so far today
            hours_elapsed: Hours elapsed in current day

        Returns:
            Recommended hourly budget for next hour
        """
        # Calculate expected spend at this point
        expected_spend = target_daily_budget * (hours_elapsed / 24.0)

        # Calculate error
        error = expected_spend - current_spend

        # PID calculation
        self.integral_error += error
        derivative_error = error - self.previous_error

        # PID output
        adjustment = (
            self.kp * error
            + self.ki * self.integral_error
            + self.kd * derivative_error
        )

        # Calculate base hourly budget
        base_hourly = target_daily_budget / 24.0

        # Apply adjustment
        recommended_hourly = max(0, base_hourly + adjustment)

        # Update state
        self.previous_error = error

        return recommended_hourly

    def _update_thompson_sampling(
        self, channel_performance: Dict[str, Dict[str, float]]
    ):
        """Update Thompson Sampling parameters based on performance

        Args:
            channel_performance: Performance data by channel
        """
        for channel, metrics in channel_performance.items():
            conversions = metrics.get("conversions", 0)
            clicks = metrics.get("clicks", 0)

            if clicks > 0:
                # Update Beta distribution parameters
                # Alpha = successes (conversions)
                # Beta = failures (clicks - conversions)
                self.channel_alphas[channel] += conversions
                self.channel_betas[channel] += (clicks - conversions)

    def _sample_channel_scores(self) -> Dict[str, float]:
        """Sample scores from Beta distributions for each channel

        Returns:
            Dict of channel scores (0-1)
        """
        scores = {}

        for channel in self.channel_alphas.keys():
            # Sample from Beta distribution
            alpha = self.channel_alphas[channel]
            beta = self.channel_betas[channel]

            # Add exploration bonus
            exploration_bonus = np.random.uniform(0, self.exploration_rate)

            score = np.random.beta(alpha, beta) + exploration_bonus
            scores[channel] = min(1.0, score)

        return scores

    def _allocate_budget(
        self,
        total_budget: float,
        channel_scores: Dict[str, float],
        constraints: Dict[str, Dict[str, float]] | None,
    ) -> Dict[str, float]:
        """Allocate budget proportionally to channel scores

        Args:
            total_budget: Total budget to allocate
            channel_scores: Scores by channel (0-1)
            constraints: Optional min/max constraints

        Returns:
            Budget allocation by channel
        """
        # Normalize scores to sum to 1
        total_score = sum(channel_scores.values())
        if total_score == 0:
            # Equal allocation if no scores
            equal_share = total_budget / len(channel_scores)
            return {channel: equal_share for channel in channel_scores.keys()}

        # Proportional allocation
        allocation = {}
        for channel, score in channel_scores.items():
            allocation[channel] = total_budget * (score / total_score)

        # Apply constraints if provided
        if constraints:
            allocation = self._apply_constraints(allocation, constraints, total_budget)

        return allocation

    def _apply_constraints(
        self,
        allocation: Dict[str, float],
        constraints: Dict[str, Dict[str, float]],
        total_budget: float,
    ) -> Dict[str, float]:
        """Apply min/max budget constraints

        Args:
            allocation: Initial allocation
            constraints: Min/max constraints by channel
            total_budget: Total budget

        Returns:
            Constrained allocation
        """
        constrained = {}

        # First pass: ensure minimum budgets
        for channel in allocation.keys():
            if channel in constraints:
                min_budget = constraints[channel].get("min", 0)
                max_budget = constraints[channel].get("max", float("inf"))

                # Start with at least minimum
                constrained[channel] = max(min_budget, allocation[channel])
                # But don't exceed maximum
                constrained[channel] = min(max_budget, constrained[channel])
            else:
                constrained[channel] = allocation[channel]

        # Calculate how much we've allocated
        allocated_sum = sum(constrained.values())

        # Second pass: adjust to match total budget
        if abs(allocated_sum - total_budget) > 0.01:
            if allocated_sum < total_budget:
                # We have budget left - distribute to channels with room
                remaining = total_budget - allocated_sum
                redistributable = []

                for channel in constrained.keys():
                    if channel in constraints:
                        max_budget = constraints[channel].get("max", float("inf"))
                        if constrained[channel] < max_budget:
                            redistributable.append(channel)
                    else:
                        redistributable.append(channel)

                if redistributable:
                    per_channel = remaining / len(redistributable)
                    for channel in redistributable:
                        if channel in constraints:
                            max_budget = constraints[channel].get("max", float("inf"))
                            constrained[channel] = min(
                                max_budget,
                                constrained[channel] + per_channel
                            )
                        else:
                            constrained[channel] += per_channel
            else:
                # We've over-allocated - scale down proportionally
                # But respect minimums
                scale_factor = total_budget / allocated_sum

                for channel in constrained.keys():
                    if channel in constraints:
                        min_budget = constraints[channel].get("min", 0)
                        # Scale down but not below minimum
                        constrained[channel] = max(
                            min_budget,
                            constrained[channel] * scale_factor
                        )
                    else:
                        constrained[channel] *= scale_factor

        return constrained

    def _calculate_expected_conversions(
        self,
        allocation: Dict[str, float],
        channel_performance: Dict[str, Dict[str, float]],
    ) -> float:
        """Calculate expected conversions from allocation

        Args:
            allocation: Budget allocation by channel
            channel_performance: Historical performance by channel

        Returns:
            Expected total conversions
        """
        total_conversions = 0.0

        for channel, budget in allocation.items():
            if channel in channel_performance:
                metrics = channel_performance[channel]
                cost = metrics.get("cost", 1)
                conversions = metrics.get("conversions", 0)

                # Calculate conversion rate per dollar
                conversion_rate = conversions / cost if cost > 0 else 0

                # Estimate conversions from allocated budget
                expected = budget * conversion_rate
                total_conversions += expected

        return total_conversions

    def _calculate_confidence(
        self, channel_performance: Dict[str, Dict[str, float]]
    ) -> float:
        """Calculate confidence in optimization

        Args:
            channel_performance: Performance data by channel

        Returns:
            Confidence score (0-1)
        """
        # Confidence based on data volume
        total_clicks = sum(
            metrics.get("clicks", 0) for metrics in channel_performance.values()
        )

        if total_clicks < 100:
            return 0.5  # Low confidence
        elif total_clicks < 1000:
            return 0.7  # Medium confidence
        elif total_clicks < 10000:
            return 0.85  # Good confidence
        else:
            return 0.95  # High confidence

    async def close(self):
        """Close resources"""
        # No resources to close for now
        pass
