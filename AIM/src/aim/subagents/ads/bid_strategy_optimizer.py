"""
Bid Strategy Optimizer - Automated Bid Strategy Optimization.

Analyzes campaign performance and recommends optimal bid strategies for
Yandex Direct and Google Ads campaigns.

Based on: Yandex Direct Bid Strategies + Google Ads Smart Bidding Best Practices
"""

import asyncio
from dataclasses import dataclass
from datetime import datetime
from typing import Any

import structlog


@dataclass
class PerformanceMetrics:
    """Campaign performance metrics."""

    impressions: int
    clicks: int
    conversions: int
    cost: float  # RUB
    revenue: float  # RUB
    ctr: float  # Click-through rate (%)
    cpc: float  # Cost per click (RUB)
    cpa: float  # Cost per acquisition (RUB)
    roas: float  # Return on ad spend
    conversion_rate: float  # %


@dataclass
class BidStrategyAnalysis:
    """Bid strategy analysis."""

    current_strategy: str  # manual, auto, target_cpa, target_roas, maximize_conversions
    strategy_performance: float  # 0-100 score
    is_optimal: bool
    recommended_strategy: str
    expected_improvement: float  # % improvement
    confidence: float  # 0-100
    reasons: list[str]
    warnings: list[str]


@dataclass
class BudgetAnalysis:
    """Budget utilization analysis."""

    daily_budget: float  # RUB
    spent_today: float  # RUB
    utilization_rate: float  # %
    is_limited: bool  # Budget limiting performance
    recommended_budget: float  # RUB
    budget_efficiency: float  # 0-100 score
    recommendations: list[str]


@dataclass
class BidAdjustments:
    """Recommended bid adjustments."""

    device_adjustments: dict[str, float]  # device -> adjustment %
    location_adjustments: dict[str, float]  # location -> adjustment %
    time_adjustments: dict[str, float]  # hour -> adjustment %
    audience_adjustments: dict[str, float]  # audience -> adjustment %
    overall_impact: float  # Expected % improvement


@dataclass
class CompetitorAnalysis:
    """Competitor bidding analysis."""

    avg_position: float  # 1-10
    impression_share: float  # %
    lost_impression_share_rank: float  # % lost due to rank
    lost_impression_share_budget: float  # % lost due to budget
    competitive_intensity: str  # low, medium, high
    recommended_actions: list[str]


@dataclass
class BidOptimizationReport:
    """Complete bid optimization report."""

    campaign_id: str
    campaign_name: str
    platform: str  # yandex, google
    timestamp: str

    # Core analyses
    performance: PerformanceMetrics
    strategy: BidStrategyAnalysis
    budget: BudgetAnalysis
    adjustments: BidAdjustments
    competitors: CompetitorAnalysis

    # Overall metrics
    optimization_score: float  # 0-100
    priority_actions: list[str]
    quick_wins: list[str]


class BidStrategyOptimizer:
    """
    Bid Strategy Optimizer.

    Analyzes campaign performance and recommends optimal bid strategies.
    """

    def __init__(self):
        """Initialize Bid Strategy Optimizer."""
        self.logger = structlog.get_logger()

    async def optimize(
        self,
        campaign_id: str,
        campaign_name: str,
        platform: str,
        performance_data: dict[str, Any] | None = None,
    ) -> BidOptimizationReport:
        """
        Optimize bid strategy for campaign.

        Args:
            campaign_id: Campaign ID
            campaign_name: Campaign name
            platform: Platform (yandex, google)
            performance_data: Performance data (if None, will fetch)

        Returns:
            Complete bid optimization report
        """
        self.logger.info(
            "bid_optimization_start",
            campaign_id=campaign_id,
            platform=platform,
        )

        # Fetch performance data if not provided
        if performance_data is None:
            performance_data = await self._fetch_performance_data(
                campaign_id, platform
            )

        # Step 1: Analyze performance metrics
        performance = await self._analyze_performance(performance_data)

        # Step 2: Analyze bid strategy
        strategy = await self._analyze_strategy(performance_data, performance)

        # Step 3: Analyze budget
        budget = await self._analyze_budget(performance_data, performance)

        # Step 4: Calculate bid adjustments
        adjustments = await self._calculate_adjustments(performance_data, performance)

        # Step 5: Analyze competitors
        competitors = await self._analyze_competitors(performance_data)

        # Step 6: Calculate optimization score
        optimization_score = self._calculate_optimization_score(
            strategy, budget, adjustments, competitors
        )

        # Step 7: Identify priority actions and quick wins
        priority_actions = self._identify_priority_actions(
            strategy, budget, competitors
        )
        quick_wins = self._identify_quick_wins(adjustments, budget)

        report = BidOptimizationReport(
            campaign_id=campaign_id,
            campaign_name=campaign_name,
            platform=platform,
            timestamp=datetime.now().isoformat(),
            performance=performance,
            strategy=strategy,
            budget=budget,
            adjustments=adjustments,
            competitors=competitors,
            optimization_score=optimization_score,
            priority_actions=priority_actions,
            quick_wins=quick_wins,
        )

        self.logger.info(
            "bid_optimization_complete",
            campaign_id=campaign_id,
            score=optimization_score,
        )

        return report

    async def _fetch_performance_data(
        self, campaign_id: str, platform: str
    ) -> dict[str, Any]:
        """Fetch performance data from platform API."""
        # Mock data for now (will integrate with real APIs)
        return {
            "impressions": 10000,
            "clicks": 500,
            "conversions": 50,
            "cost": 25000.0,
            "revenue": 150000.0,
            "current_strategy": "manual",
            "daily_budget": 5000.0,
            "spent_today": 4800.0,
            "avg_position": 3.5,
            "impression_share": 65.0,
            "lost_is_rank": 20.0,
            "lost_is_budget": 15.0,
            "device_performance": {
                "desktop": {"clicks": 200, "conversions": 25, "cost": 10000.0},
                "mobile": {"clicks": 250, "conversions": 20, "cost": 12500.0},
                "tablet": {"clicks": 50, "conversions": 5, "cost": 2500.0},
            },
            "location_performance": {
                "moscow": {"clicks": 300, "conversions": 35, "cost": 15000.0},
                "spb": {"clicks": 150, "conversions": 12, "cost": 7500.0},
                "other": {"clicks": 50, "conversions": 3, "cost": 2500.0},
            },
            "time_performance": {
                "9-12": {"clicks": 150, "conversions": 20, "cost": 7500.0},
                "12-15": {"clicks": 200, "conversions": 18, "cost": 10000.0},
                "15-18": {"clicks": 100, "conversions": 8, "cost": 5000.0},
                "18-21": {"clicks": 50, "conversions": 4, "cost": 2500.0},
            },
        }

    async def _analyze_performance(
        self, data: dict[str, Any]
    ) -> PerformanceMetrics:
        """Analyze performance metrics."""
        impressions = data.get("impressions", 0)
        clicks = data.get("clicks", 0)
        conversions = data.get("conversions", 0)
        cost = data.get("cost", 0.0)
        revenue = data.get("revenue", 0.0)

        # Calculate metrics
        ctr = (clicks / impressions * 100) if impressions > 0 else 0.0
        cpc = (cost / clicks) if clicks > 0 else 0.0
        cpa = (cost / conversions) if conversions > 0 else 0.0
        roas = (revenue / cost) if cost > 0 else 0.0
        conversion_rate = (conversions / clicks * 100) if clicks > 0 else 0.0

        return PerformanceMetrics(
            impressions=impressions,
            clicks=clicks,
            conversions=conversions,
            cost=cost,
            revenue=revenue,
            ctr=round(ctr, 2),
            cpc=round(cpc, 2),
            cpa=round(cpa, 2),
            roas=round(roas, 2),
            conversion_rate=round(conversion_rate, 2),
        )

    async def _analyze_strategy(
        self, data: dict[str, Any], performance: PerformanceMetrics
    ) -> BidStrategyAnalysis:
        """Analyze bid strategy."""
        current_strategy = data.get("current_strategy", "manual")

        # Evaluate current strategy performance
        strategy_score = 0.0
        reasons = []
        warnings = []

        # Check ROAS
        if performance.roas >= 6.0:
            strategy_score += 40
            reasons.append(f"Excellent ROAS: {performance.roas}")
        elif performance.roas >= 4.0:
            strategy_score += 30
            reasons.append(f"Good ROAS: {performance.roas}")
        elif performance.roas >= 2.0:
            strategy_score += 20
            warnings.append(f"Low ROAS: {performance.roas}")
        else:
            strategy_score += 10
            warnings.append(f"Very low ROAS: {performance.roas}")

        # Check conversion rate
        if performance.conversion_rate >= 10.0:
            strategy_score += 30
            reasons.append(f"High conversion rate: {performance.conversion_rate}%")
        elif performance.conversion_rate >= 5.0:
            strategy_score += 20
        else:
            strategy_score += 10
            warnings.append(f"Low conversion rate: {performance.conversion_rate}%")

        # Check CPA
        target_cpa = 500.0  # Example target
        if performance.cpa <= target_cpa:
            strategy_score += 30
            reasons.append(f"CPA within target: {performance.cpa} RUB")
        else:
            strategy_score += 15
            warnings.append(f"CPA above target: {performance.cpa} RUB")

        # Recommend strategy
        recommended_strategy = current_strategy
        expected_improvement = 0.0
        confidence = 70.0

        if current_strategy == "manual":
            if performance.conversions >= 30:  # Enough data for auto
                recommended_strategy = "target_roas"
                expected_improvement = 15.0
                confidence = 80.0
                reasons.append("Enough conversion data for Target ROAS")
            elif performance.conversions >= 15:
                recommended_strategy = "target_cpa"
                expected_improvement = 10.0
                confidence = 75.0
                reasons.append("Enough conversion data for Target CPA")

        is_optimal = current_strategy == recommended_strategy

        return BidStrategyAnalysis(
            current_strategy=current_strategy,
            strategy_performance=round(strategy_score, 2),
            is_optimal=is_optimal,
            recommended_strategy=recommended_strategy,
            expected_improvement=expected_improvement,
            confidence=confidence,
            reasons=reasons,
            warnings=warnings,
        )

    async def _analyze_budget(
        self, data: dict[str, Any], performance: PerformanceMetrics
    ) -> BudgetAnalysis:
        """Analyze budget utilization."""
        daily_budget = data.get("daily_budget", 0.0)
        spent_today = data.get("spent_today", 0.0)

        utilization_rate = (
            (spent_today / daily_budget * 100) if daily_budget > 0 else 0.0
        )
        is_limited = utilization_rate >= 95.0

        # Calculate recommended budget
        if is_limited and performance.roas >= 4.0:
            # Good ROAS, increase budget
            recommended_budget = daily_budget * 1.5
        elif utilization_rate < 70.0 and performance.roas < 2.0:
            # Low utilization and poor ROAS, decrease budget
            recommended_budget = daily_budget * 0.8
        else:
            recommended_budget = daily_budget

        # Budget efficiency score
        efficiency = 0.0
        if 80 <= utilization_rate <= 95:
            efficiency = 100.0
        elif 70 <= utilization_rate < 80 or 95 < utilization_rate <= 100:
            efficiency = 80.0
        else:
            efficiency = 60.0

        recommendations = []
        if is_limited:
            recommendations.append(
                f"Budget limited. Increase to {recommended_budget:.0f} RUB"
            )
        if utilization_rate < 70:
            recommendations.append(
                f"Low budget utilization ({utilization_rate:.1f}%). Review targeting"
            )

        return BudgetAnalysis(
            daily_budget=daily_budget,
            spent_today=spent_today,
            utilization_rate=round(utilization_rate, 2),
            is_limited=is_limited,
            recommended_budget=round(recommended_budget, 2),
            budget_efficiency=efficiency,
            recommendations=recommendations,
        )

    async def _calculate_adjustments(
        self, data: dict[str, Any], performance: PerformanceMetrics
    ) -> BidAdjustments:
        """Calculate bid adjustments."""
        device_perf = data.get("device_performance", {})
        location_perf = data.get("location_performance", {})
        time_perf = data.get("time_performance", {})

        # Device adjustments
        device_adjustments = {}
        for device, perf in device_perf.items():
            device_roas = (
                (perf.get("revenue", 0) / perf["cost"])
                if perf.get("cost", 0) > 0
                else 0
            )
            if device_roas > performance.roas * 1.2:
                device_adjustments[device] = 20.0  # Increase 20%
            elif device_roas < performance.roas * 0.8:
                device_adjustments[device] = -20.0  # Decrease 20%
            else:
                device_adjustments[device] = 0.0

        # Location adjustments
        location_adjustments = {}
        for location, perf in location_perf.items():
            conv_rate = (
                (perf["conversions"] / perf["clicks"] * 100)
                if perf.get("clicks", 0) > 0
                else 0
            )
            if conv_rate > performance.conversion_rate * 1.3:
                location_adjustments[location] = 30.0
            elif conv_rate < performance.conversion_rate * 0.7:
                location_adjustments[location] = -30.0
            else:
                location_adjustments[location] = 0.0

        # Time adjustments
        time_adjustments = {}
        for time_slot, perf in time_perf.items():
            conv_rate = (
                (perf["conversions"] / perf["clicks"] * 100)
                if perf.get("clicks", 0) > 0
                else 0
            )
            if conv_rate > performance.conversion_rate * 1.2:
                time_adjustments[time_slot] = 25.0
            elif conv_rate < performance.conversion_rate * 0.8:
                time_adjustments[time_slot] = -25.0
            else:
                time_adjustments[time_slot] = 0.0

        # Audience adjustments (mock for now)
        audience_adjustments = {
            "remarketing": 50.0,
            "similar": 20.0,
            "cold": 0.0,
        }

        # Calculate overall impact
        overall_impact = 10.0  # Expected improvement from adjustments

        return BidAdjustments(
            device_adjustments=device_adjustments,
            location_adjustments=location_adjustments,
            time_adjustments=time_adjustments,
            audience_adjustments=audience_adjustments,
            overall_impact=overall_impact,
        )

    async def _analyze_competitors(
        self, data: dict[str, Any]
    ) -> CompetitorAnalysis:
        """Analyze competitor bidding."""
        avg_position = data.get("avg_position", 5.0)
        impression_share = data.get("impression_share", 50.0)
        lost_is_rank = data.get("lost_is_rank", 0.0)
        lost_is_budget = data.get("lost_is_budget", 0.0)

        # Determine competitive intensity
        if lost_is_rank > 30:
            competitive_intensity = "high"
        elif lost_is_rank > 15:
            competitive_intensity = "medium"
        else:
            competitive_intensity = "low"

        # Recommendations
        recommendations = []
        if avg_position > 3.0:
            recommendations.append(
                f"Improve position from {avg_position:.1f} to top 3"
            )
        if lost_is_rank > 20:
            recommendations.append(
                f"Increase bids to reduce rank loss ({lost_is_rank:.1f}%)"
            )
        if lost_is_budget > 20:
            recommendations.append(
                f"Increase budget to reduce budget loss ({lost_is_budget:.1f}%)"
            )

        return CompetitorAnalysis(
            avg_position=avg_position,
            impression_share=impression_share,
            lost_impression_share_rank=lost_is_rank,
            lost_impression_share_budget=lost_is_budget,
            competitive_intensity=competitive_intensity,
            recommended_actions=recommendations,
        )

    def _calculate_optimization_score(
        self,
        strategy: BidStrategyAnalysis,
        budget: BudgetAnalysis,
        adjustments: BidAdjustments,
        competitors: CompetitorAnalysis,
    ) -> float:
        """Calculate overall optimization score."""
        # Weighted components
        strategy_weight = 0.4
        budget_weight = 0.3
        adjustments_weight = 0.2
        competitors_weight = 0.1

        # Adjustments score (based on potential impact)
        adjustments_score = min(100, 70 + adjustments.overall_impact * 3)

        # Competitors score (based on impression share)
        competitors_score = competitors.impression_share

        score = (
            strategy.strategy_performance * strategy_weight
            + budget.budget_efficiency * budget_weight
            + adjustments_score * adjustments_weight
            + competitors_score * competitors_weight
        )

        return round(score, 2)

    def _identify_priority_actions(
        self,
        strategy: BidStrategyAnalysis,
        budget: BudgetAnalysis,
        competitors: CompetitorAnalysis,
    ) -> list[str]:
        """Identify priority actions."""
        actions = []

        # Strategy issues
        if not strategy.is_optimal:
            actions.append(
                f"CRITICAL: Switch to {strategy.recommended_strategy} "
                f"(+{strategy.expected_improvement:.1f}% expected)"
            )

        if strategy.strategy_performance < 60:
            actions.append("HIGH: Current strategy underperforming")

        # Budget issues
        if budget.is_limited:
            actions.append(
                f"HIGH: Budget limited. Increase to {budget.recommended_budget:.0f} RUB"
            )

        # Competitor issues
        if competitors.competitive_intensity == "high":
            actions.append("MEDIUM: High competitive pressure. Review bids")

        if competitors.avg_position > 4.0:
            actions.append(
                f"MEDIUM: Low position ({competitors.avg_position:.1f}). Increase bids"
            )

        return actions

    def _identify_quick_wins(
        self, adjustments: BidAdjustments, budget: BudgetAnalysis
    ) -> list[str]:
        """Identify quick wins."""
        wins = []

        # Device adjustments
        for device, adj in adjustments.device_adjustments.items():
            if abs(adj) >= 20:
                wins.append(
                    f"Adjust {device} bids by {adj:+.0f}% (5 min)"
                )

        # Location adjustments
        top_locations = sorted(
            adjustments.location_adjustments.items(),
            key=lambda x: abs(x[1]),
            reverse=True,
        )[:2]
        for location, adj in top_locations:
            if abs(adj) >= 20:
                wins.append(
                    f"Adjust {location} bids by {adj:+.0f}% (5 min)"
                )

        # Budget
        if budget.utilization_rate < 70:
            wins.append("Review targeting to increase budget utilization (10 min)")

        return wins


# ==============================================================================
# Added by Teacher Agent: bid-optimizer
# ==============================================================================

async def ndpointer(dtype=None, ndim=None, shape=None, flags=None):
    """
    Array-checking restype/argtypes.

    An ndpointer instance is used to describe an ndarray in restypes
    and argtypes specifications.  This approach is more flexible than
    using, for example, ``POINTER(c_double)``, since several restrictions
    can be specified, which are verified upon calling the ctypes function.
    These include data type, number of dimensions, shape and flags.  If a
    given array does not satisfy the specified restrictions,
    a ``TypeError`` is raised.

    Parameters
    ----------
    dtype : data-type, optional
        Array data-type.
    ndim : int, optional
        Number of array dimensions.
    shape : tuple of ints, optional
        Array shape.
    flags : str or tuple of str
        Array flags; may be one or more of:

        - C_CONTIGUOUS / C / CONTIGUOUS
        - F_CONTIGUOUS / F / FORTRAN
        - OWNDATA / O
        - WRITEABLE / W
        - ALIGNED / A
        - WRITEBACKIFCOPY / X

    Returns
    -------
    klass : ndpointer type object
        A type object, which is an ``_ndtpr`` instance containing
        dtype, ndim, shape and flags information.

    Raises
    ------
    TypeError
        If a given array does not satisfy the specified restrictions.

    Examples
    --------
    >>> clib.somefunc.argtypes = [np.ctypeslib.ndpointer(dtype=np.float64,
    ...                                                  ndim=1,
    ...                                                  flags='C_CONTIGUOUS')]
    ... #doctest: +SKIP
    >>> clib.somefunc(np.array([1, 2, 3], dtype=np.float64))
    ... #doctest: +SKIP

    """

    # normalize dtype to an Optional[dtype]
    if dtype is not None:
        dtype = _dtype(dtype)

    # normalize flags to an Optional[int]
    num = None
    if flags is not None:
        if isinstance(flags, str):
            flags = flags.split(',')
        elif isinstance(flags, (int, integer)):
            num = flags
            flags = _flags_fromnum(num)
        elif isinstance(flags, flagsobj):
            num = flags.num
            flags = _flags_fromnum(num)
        if num is None:
            try:
                flags = [x.strip().upper() for x in flags]
            except Exception as e:
                raise TypeError("invalid flags specification") from e
            num = _num_fromflags(flags)

    # normalize shape to an Optional[tuple]
    if shape is not None:
        try:
            shape = tuple(shape)
        except TypeError:
            # single integer -> 1-tuple
            shape = (shape,)

    cache_key = (dtype, ndim, shape, num)

    try:
        return _pointer_type_cache[cache_key]
    except KeyError:
        pass

    # produce a name for the new type
    if dtype is None:
        name = 'any'
    elif dtype.names is not None:
        name = str(id(dtype))
    else:
        name = dtype.str
    if ndim is not None:
        name += "_%dd" % ndim
    if shape is not None:
        name += "_"+"x".join(str(x) for x in shape)
    if flags is not None:
        name += "_"+"_".join(flags)

    if dtype is not None and shape is not None:
        base = _concrete_ndptr
    else:
        base = _ndptr

    klass = type("ndpointer_%s"%name, (base,),
                 {"_dtype_": dtype,
                  "_shape_" : shape,
                  "_ndim_" : ndim,
                  "_flags_" : num})
    _pointer_type_cache[cache_key] = klass
    return klass