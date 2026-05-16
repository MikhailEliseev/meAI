"""
Tests for LLM cost tracker.
"""

import pytest
from datetime import datetime, timedelta

from aim.ai.llm.cost_tracker import CostTracker, CostMetrics
from aim.ai.llm.schemas import LLMProvider, LLMBudgetExceededError


class TestCostTracker:
    """Test CostTracker."""
    
    def test_initialization(self):
        """Test tracker initialization."""
        tracker = CostTracker(
            max_cost_per_request=5.0,
            daily_budget=100.0,
            monthly_budget=1000.0,
        )
        
        assert tracker.max_cost_per_request == 5.0
        assert tracker.daily_budget == 100.0
        assert tracker.monthly_budget == 1000.0
    
    def test_check_budget_per_request_limit(self):
        """Test per-request budget limit."""
        tracker = CostTracker(max_cost_per_request=1.0)
        
        # Within limit
        tracker.check_budget(0.5)
        
        # Exceeds limit
        with pytest.raises(LLMBudgetExceededError) as exc:
            tracker.check_budget(1.5)
        assert "exceeds max $1.00" in str(exc.value)
    
    def test_check_budget_daily_limit(self):
        """Test daily budget limit."""
        tracker = CostTracker(
            max_cost_per_request=10.0,
            daily_budget=5.0,
        )
        
        # First request OK
        tracker.check_budget(2.0)
        tracker.track_request(
            provider=LLMProvider.ANTHROPIC,
            model="claude-sonnet-4",
            tokens_used=1000,
            cost_usd=2.0,
        )
        
        # Second request OK
        tracker.check_budget(2.0)
        tracker.track_request(
            provider=LLMProvider.ANTHROPIC,
            model="claude-sonnet-4",
            tokens_used=1000,
            cost_usd=2.0,
        )
        
        # Third request exceeds daily budget
        with pytest.raises(LLMBudgetExceededError) as exc:
            tracker.check_budget(2.0)
        assert "Daily budget" in str(exc.value)
    
    def test_check_budget_monthly_limit(self):
        """Test monthly budget limit."""
        tracker = CostTracker(
            max_cost_per_request=100.0,
            monthly_budget=10.0,
        )
        
        # First request OK
        tracker.check_budget(8.0)
        tracker.track_request(
            provider=LLMProvider.ANTHROPIC,
            model="claude-sonnet-4",
            tokens_used=10000,
            cost_usd=8.0,
        )
        
        # Second request exceeds monthly budget
        with pytest.raises(LLMBudgetExceededError) as exc:
            tracker.check_budget(5.0)
        assert "Monthly budget" in str(exc.value)
    
    def test_track_request(self):
        """Test request tracking."""
        tracker = CostTracker()
        
        tracker.track_request(
            provider=LLMProvider.ANTHROPIC,
            model="claude-sonnet-4",
            tokens_used=1500,
            cost_usd=0.015,
        )
        
        metrics = tracker.get_daily_metrics()
        assert metrics.total_requests == 1
        assert metrics.total_tokens == 1500
        assert metrics.total_cost_usd == 0.015
        assert metrics.by_provider["anthropic"] == 0.015
        assert metrics.by_model["claude-sonnet-4"] == 0.015
    
    def test_track_cached_request(self):
        """Test cached request tracking."""
        tracker = CostTracker()
        
        tracker.track_request(
            provider=LLMProvider.ANTHROPIC,
            model="claude-sonnet-4",
            tokens_used=1000,
            cost_usd=0.0,
            cached=True,
            cache_savings_usd=0.01,
        )
        
        metrics = tracker.get_daily_metrics()
        assert metrics.cached_requests == 1
        assert metrics.cached_cost_saved_usd == 0.01
    
    def test_multiple_providers(self):
        """Test tracking multiple providers."""
        tracker = CostTracker()
        
        # Anthropic request
        tracker.track_request(
            provider=LLMProvider.ANTHROPIC,
            model="claude-sonnet-4",
            tokens_used=1000,
            cost_usd=0.01,
        )
        
        # OpenAI request
        tracker.track_request(
            provider=LLMProvider.OPENAI,
            model="gpt-4-turbo",
            tokens_used=1000,
            cost_usd=0.02,
        )
        
        metrics = tracker.get_daily_metrics()
        assert metrics.total_requests == 2
        assert metrics.total_cost_usd == 0.03
        assert metrics.by_provider["anthropic"] == 0.01
        assert metrics.by_provider["openai"] == 0.02
    
    def test_get_daily_metrics(self):
        """Test getting daily metrics."""
        tracker = CostTracker()
        
        tracker.track_request(
            provider=LLMProvider.ANTHROPIC,
            model="claude-sonnet-4",
            tokens_used=1000,
            cost_usd=0.01,
        )
        
        metrics = tracker.get_daily_metrics()
        assert isinstance(metrics, CostMetrics)
        assert metrics.total_requests == 1
    
    def test_get_monthly_metrics(self):
        """Test getting monthly metrics."""
        tracker = CostTracker()
        
        tracker.track_request(
            provider=LLMProvider.ANTHROPIC,
            model="claude-sonnet-4",
            tokens_used=1000,
            cost_usd=0.01,
        )
        
        metrics = tracker.get_monthly_metrics()
        assert isinstance(metrics, CostMetrics)
        assert metrics.total_requests == 1


class TestCostMetrics:
    """Test CostMetrics dataclass."""
    
    def test_initialization(self):
        """Test metrics initialization."""
        metrics = CostMetrics()
        
        assert metrics.total_requests == 0
        assert metrics.total_tokens == 0
        assert metrics.total_cost_usd == 0.0
        assert metrics.cached_requests == 0
        assert metrics.cached_cost_saved_usd == 0.0
        assert metrics.by_provider == {}
        assert metrics.by_model == {}
