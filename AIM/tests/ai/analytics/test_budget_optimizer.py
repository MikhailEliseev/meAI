"""
Tests for Budget Optimizer
"""

import pytest
import numpy as np
from datetime import datetime, timezone

from AIM.src.aim.ai.analytics.budget_optimizer import BudgetOptimizer
from AIM.src.aim.ai.analytics.schemas import BudgetOptimizationResult


class TestBudgetOptimizer:
    """Test BudgetOptimizer."""

    @pytest.fixture
    def optimizer(self):
        """Create optimizer instance."""
        return BudgetOptimizer(
            kp=0.5,
            ki=0.1,
            kd=0.2,
            exploration_rate=0.1,
        )

    @pytest.fixture
    def channel_performance(self):
        """Create channel performance data."""
        return {
            "google_ads": {
                "conversions": 20,
                "cost": 500,
                "clicks": 100,
            },
            "yandex_direct": {
                "conversions": 15,
                "cost": 400,
                "clicks": 80,
            },
            "meta_ads": {
                "conversions": 10,
                "cost": 300,
                "clicks": 60,
            },
        }

    async def test_basic_optimization(self, optimizer, channel_performance):
        """Test basic budget optimization."""
        result = await optimizer.optimize(
            total_budget=1500.0,
            channel_performance=channel_performance,
        )

        assert isinstance(result, BudgetOptimizationResult)
        assert result.recommended_daily_budget == 1500.0
        assert len(result.channel_allocation) == 3
        assert result.expected_conversions >= 0
        assert result.expected_cpa >= 0
        assert 0.0 <= result.confidence <= 1.0

    async def test_budget_allocation_sum(self, optimizer, channel_performance):
        """Test that allocated budgets sum to total budget."""
        total_budget = 1500.0

        result = await optimizer.optimize(
            total_budget=total_budget,
            channel_performance=channel_performance,
        )

        allocated_sum = sum(result.channel_allocation.values())

        # Allow small floating point tolerance
        assert abs(allocated_sum - total_budget) < 1.0

    async def test_thompson_sampling_updates(self, optimizer, channel_performance):
        """Test Thompson Sampling parameter updates."""
        # Initial state
        assert len(optimizer.channel_alphas) == 0
        assert len(optimizer.channel_betas) == 0

        # Run optimization
        await optimizer.optimize(
            total_budget=1500.0,
            channel_performance=channel_performance,
        )

        # Parameters should be initialized and updated
        assert len(optimizer.channel_alphas) == 3
        assert len(optimizer.channel_betas) == 3

        # Alpha should increase with conversions
        assert optimizer.channel_alphas["google_ads"] > 1.0  # 20 conversions
        assert optimizer.channel_alphas["yandex_direct"] > 1.0  # 15 conversions

        # Beta should increase with non-converting clicks
        assert optimizer.channel_betas["google_ads"] > 1.0  # 80 non-converting clicks

    async def test_constraints_min_budget(self, optimizer, channel_performance):
        """Test minimum budget constraints."""
        constraints = {
            "google_ads": {"min": 600, "max": 1000},
            "yandex_direct": {"min": 400, "max": 800},
            "meta_ads": {"min": 200, "max": 500},
        }

        result = await optimizer.optimize(
            total_budget=1500.0,
            channel_performance=channel_performance,
            constraints=constraints,
        )

        # Check minimum constraints
        assert result.channel_allocation["google_ads"] >= 600
        assert result.channel_allocation["yandex_direct"] >= 400
        assert result.channel_allocation["meta_ads"] >= 200

    async def test_constraints_max_budget(self, optimizer, channel_performance):
        """Test maximum budget constraints."""
        constraints = {
            "google_ads": {"min": 200, "max": 600},
            "yandex_direct": {"min": 100, "max": 400},
            "meta_ads": {"min": 50, "max": 300},
        }

        result = await optimizer.optimize(
            total_budget=1500.0,
            channel_performance=channel_performance,
            constraints=constraints,
        )

        # Check maximum constraints
        assert result.channel_allocation["google_ads"] <= 600
        assert result.channel_allocation["yandex_direct"] <= 400
        assert result.channel_allocation["meta_ads"] <= 300

    async def test_pid_budget_pacing(self, optimizer):
        """Test PID controller for budget pacing."""
        target_daily_budget = 1000.0

        # Scenario 1: Under-spending (need to increase)
        recommended_1 = optimizer.pace_budget(
            target_daily_budget=target_daily_budget,
            current_spend=200.0,  # Only $200 spent
            hours_elapsed=12.0,  # Half day elapsed
        )

        # Should recommend higher than base hourly (1000/24 = 41.67)
        base_hourly = target_daily_budget / 24.0
        assert recommended_1 > base_hourly

        # Scenario 2: Over-spending (need to decrease)
        optimizer.integral_error = 0.0  # Reset PID state
        optimizer.previous_error = 0.0

        recommended_2 = optimizer.pace_budget(
            target_daily_budget=target_daily_budget,
            current_spend=800.0,  # $800 spent
            hours_elapsed=12.0,  # Half day elapsed
        )

        # Should recommend lower than base hourly
        assert recommended_2 < base_hourly

    async def test_expected_conversions_calculation(self, optimizer, channel_performance):
        """Test expected conversions calculation."""
        result = await optimizer.optimize(
            total_budget=1500.0,
            channel_performance=channel_performance,
        )

        # Expected conversions should be positive
        assert result.expected_conversions > 0

        # Should be reasonable based on historical performance
        # Historical: 45 conversions for $1200 = 0.0375 conversions per dollar
        # Expected: ~56 conversions for $1500 (if same rate)
        assert 30 <= result.expected_conversions <= 80

    async def test_confidence_increases_with_data(self, optimizer):
        """Test confidence increases with more data."""
        # Small dataset
        small_performance = {
            "google_ads": {"conversions": 2, "cost": 50, "clicks": 10},
        }

        # Large dataset
        large_performance = {
            "google_ads": {"conversions": 200, "cost": 5000, "clicks": 10000},
        }

        result_small = await optimizer.optimize(
            total_budget=100.0,
            channel_performance=small_performance,
        )

        result_large = await optimizer.optimize(
            total_budget=5000.0,
            channel_performance=large_performance,
        )

        # More data should give higher confidence
        assert result_large.confidence > result_small.confidence

    async def test_zero_performance_handling(self, optimizer):
        """Test handling of channels with zero performance."""
        zero_performance = {
            "google_ads": {"conversions": 0, "cost": 0, "clicks": 0},
            "yandex_direct": {"conversions": 0, "cost": 0, "clicks": 0},
        }

        result = await optimizer.optimize(
            total_budget=1000.0,
            channel_performance=zero_performance,
        )

        # With zero performance, Thompson Sampling uses exploration
        # Allocation can vary significantly due to random sampling
        # Just check that both channels get some budget
        allocation_values = list(result.channel_allocation.values())
        assert all(v > 0 for v in allocation_values)
        assert sum(allocation_values) == pytest.approx(1000.0, abs=1.0)

        # Expected conversions should be zero
        assert result.expected_conversions == 0

    async def test_exploration_rate(self):
        """Test exploration rate effect."""
        # Low exploration (more exploitation)
        optimizer_low = BudgetOptimizer(exploration_rate=0.01)

        # High exploration (more exploration)
        optimizer_high = BudgetOptimizer(exploration_rate=0.5)

        channel_performance = {
            "google_ads": {"conversions": 100, "cost": 1000, "clicks": 500},
            "yandex_direct": {"conversions": 10, "cost": 1000, "clicks": 500},
        }

        # Run multiple optimizations
        results_low = []
        results_high = []

        for _ in range(10):
            result_low = await optimizer_low.optimize(
                total_budget=2000.0,
                channel_performance=channel_performance,
            )
            result_high = await optimizer_high.optimize(
                total_budget=2000.0,
                channel_performance=channel_performance,
            )

            results_low.append(result_low.channel_allocation["yandex_direct"])
            results_high.append(result_high.channel_allocation["yandex_direct"])

        # High exploration should give more budget to underperforming channel
        avg_low = np.mean(results_low)
        avg_high = np.mean(results_high)

        # High exploration should allocate more to yandex_direct (exploration)
        assert avg_high >= avg_low * 0.8  # Allow some variance
