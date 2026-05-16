"""
LLM Cost Tracker

Tracks LLM usage costs and enforces budget limits.
"""

import time
from typing import Dict, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass, field

from .schemas import LLMProvider, LLMBudgetExceededError


@dataclass
class CostMetrics:
    """Cost metrics for a time period."""
    
    total_requests: int = 0
    total_tokens: int = 0
    total_cost_usd: float = 0.0
    cached_requests: int = 0
    cached_cost_saved_usd: float = 0.0
    by_provider: Dict[str, float] = field(default_factory=dict)
    by_model: Dict[str, float] = field(default_factory=dict)


class CostTracker:
    """
    Tracks LLM costs and enforces budget limits.
    
    Features:
    - Per-request cost tracking
    - Daily/monthly budget enforcement
    - Cost breakdown by provider/model
    - Cache savings tracking
    """
    
    def __init__(
        self,
        max_cost_per_request: float = 5.0,
        daily_budget: Optional[float] = None,
        monthly_budget: Optional[float] = None,
    ):
        """
        Initialize cost tracker.
        
        Args:
            max_cost_per_request: Maximum cost per request in USD
            daily_budget: Daily budget limit in USD (None = no limit)
            monthly_budget: Monthly budget limit in USD (None = no limit)
        """
        self.max_cost_per_request = max_cost_per_request
        self.daily_budget = daily_budget
        self.monthly_budget = monthly_budget
        
        # Current period metrics
        self.daily_metrics = CostMetrics()
        self.monthly_metrics = CostMetrics()
        
        # Reset timestamps
        self.daily_reset_time = datetime.now()
        self.monthly_reset_time = datetime.now()
    
    def check_budget(self, estimated_cost: float) -> None:
        """
        Check if request is within budget limits.
        
        Args:
            estimated_cost: Estimated cost for the request
            
        Raises:
            LLMBudgetExceededError: If budget would be exceeded
        """
        # Check per-request limit
        if estimated_cost > self.max_cost_per_request:
            raise LLMBudgetExceededError(
                f"Request cost ${estimated_cost:.4f} exceeds max ${self.max_cost_per_request:.2f}"
            )
        
        # Reset metrics if needed
        self._reset_if_needed()
        
        # Check daily budget
        if self.daily_budget is not None:
            if self.daily_metrics.total_cost_usd + estimated_cost > self.daily_budget:
                raise LLMBudgetExceededError(
                    f"Daily budget ${self.daily_budget:.2f} would be exceeded "
                    f"(current: ${self.daily_metrics.total_cost_usd:.2f}, "
                    f"request: ${estimated_cost:.4f})"
                )
        
        # Check monthly budget
        if self.monthly_budget is not None:
            if self.monthly_metrics.total_cost_usd + estimated_cost > self.monthly_budget:
                raise LLMBudgetExceededError(
                    f"Monthly budget ${self.monthly_budget:.2f} would be exceeded "
                    f"(current: ${self.monthly_metrics.total_cost_usd:.2f}, "
                    f"request: ${estimated_cost:.4f})"
                )
    
    def track_request(
        self,
        provider: LLMProvider,
        model: str,
        tokens_used: int,
        cost_usd: float,
        cached: bool = False,
        cache_savings_usd: float = 0.0,
    ) -> None:
        """
        Track a completed request.
        
        Args:
            provider: Provider used
            model: Model used
            tokens_used: Total tokens used
            cost_usd: Actual cost in USD
            cached: Whether response was cached
            cache_savings_usd: Cost saved by caching
        """
        # Reset metrics if needed
        self._reset_if_needed()
        
        # Update daily metrics
        self.daily_metrics.total_requests += 1
        self.daily_metrics.total_tokens += tokens_used
        self.daily_metrics.total_cost_usd += cost_usd
        
        if cached:
            self.daily_metrics.cached_requests += 1
            self.daily_metrics.cached_cost_saved_usd += cache_savings_usd
        
        provider_key = provider.value
        self.daily_metrics.by_provider[provider_key] = (
            self.daily_metrics.by_provider.get(provider_key, 0.0) + cost_usd
        )
        self.daily_metrics.by_model[model] = (
            self.daily_metrics.by_model.get(model, 0.0) + cost_usd
        )
        
        # Update monthly metrics
        self.monthly_metrics.total_requests += 1
        self.monthly_metrics.total_tokens += tokens_used
        self.monthly_metrics.total_cost_usd += cost_usd
        
        if cached:
            self.monthly_metrics.cached_requests += 1
            self.monthly_metrics.cached_cost_saved_usd += cache_savings_usd
        
        self.monthly_metrics.by_provider[provider_key] = (
            self.monthly_metrics.by_provider.get(provider_key, 0.0) + cost_usd
        )
        self.monthly_metrics.by_model[model] = (
            self.monthly_metrics.by_model.get(model, 0.0) + cost_usd
        )
    
    def get_daily_metrics(self) -> CostMetrics:
        """Get daily cost metrics."""
        self._reset_if_needed()
        return self.daily_metrics
    
    def get_monthly_metrics(self) -> CostMetrics:
        """Get monthly cost metrics."""
        self._reset_if_needed()
        return self.monthly_metrics
    
    def _reset_if_needed(self) -> None:
        """Reset metrics if period has elapsed."""
        now = datetime.now()
        
        # Reset daily metrics if day changed
        if now.date() > self.daily_reset_time.date():
            self.daily_metrics = CostMetrics()
            self.daily_reset_time = now
        
        # Reset monthly metrics if month changed
        if now.month != self.monthly_reset_time.month or now.year != self.monthly_reset_time.year:
            self.monthly_metrics = CostMetrics()
            self.monthly_reset_time = now
