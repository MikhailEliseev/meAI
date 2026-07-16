"""Tests for Decision Maker"""

import pytest
from meai.core.decision_maker import DecisionMaker, Strategy, StrategyOutcome
from meai.storage.database import Database


@pytest.mark.asyncio
async def test_select_strategy():
    """Test selecting optimal strategy"""
    db = Database("sqlite+aiosqlite:///:memory:")
    await db.connect()

    decision_maker = DecisionMaker(db)

    strategies = [
        Strategy(
            name="Strategy A",
            description="Fast but risky",
            expected_cost=50,
            expected_quality=7,
            risk_level="high",
        ),
        Strategy(
            name="Strategy B",
            description="Balanced approach",
            expected_cost=75,
            expected_quality=8,
            risk_level="medium",
        ),
        Strategy(
            name="Strategy C",
            description="Safe but slow",
            expected_cost=100,
            expected_quality=9,
            risk_level="low",
        ),
    ]

    selected = await decision_maker.select_strategy(
        strategies,
        criteria={"max_cost": 80, "min_quality": 7},
    )

    assert selected is not None
    assert selected.expected_cost <= 80
    assert selected.expected_quality >= 7

    await db.disconnect()


@pytest.mark.asyncio
async def test_track_outcome():
    """Test tracking strategy outcome"""
    db = Database("sqlite+aiosqlite:///:memory:")
    await db.connect()

    decision_maker = DecisionMaker(db)

    strategy = Strategy(
        name="Test Strategy",
        description="Test",
        expected_cost=50,
        expected_quality=8,
        risk_level="medium",
    )

    outcome = StrategyOutcome(
        strategy_name="Test Strategy",
        actual_cost=55,
        actual_quality=7,
        success=True,
        notes="Slightly over budget",
    )

    await decision_maker.track_outcome(strategy, outcome)

    # Verify outcome was stored
    history = await decision_maker.get_strategy_history("Test Strategy")
    assert len(history) > 0

    await db.disconnect()


@pytest.mark.asyncio
async def test_learn_from_outcomes():
    """Test learning from past outcomes"""
    db = Database("sqlite+aiosqlite:///:memory:")
    await db.connect()

    decision_maker = DecisionMaker(db)

    strategy = Strategy(
        name="Learning Strategy",
        description="Test learning",
        expected_cost=50,
        expected_quality=8,
        risk_level="medium",
    )

    # Track multiple outcomes
    for i in range(3):
        outcome = StrategyOutcome(
            strategy_name="Learning Strategy",
            actual_cost=50 + i * 5,
            actual_quality=8 - i * 0.5,
            success=True,
            notes=f"Iteration {i}",
        )
        await decision_maker.track_outcome(strategy, outcome)

    # Get insights
    insights = await decision_maker.get_strategy_insights("Learning Strategy")

    assert "success_rate" in insights
    assert "avg_cost" in insights
    assert "avg_quality" in insights

    await db.disconnect()


@pytest.mark.asyncio
async def test_compare_strategies():
    """Test comparing multiple strategies"""
    db = Database("sqlite+aiosqlite:///:memory:")
    await db.connect()

    decision_maker = DecisionMaker(db)

    strategies = [
        Strategy(
            name="Fast",
            description="Quick execution",
            expected_cost=30,
            expected_quality=6,
            risk_level="high",
        ),
        Strategy(
            name="Quality",
            description="High quality",
            expected_cost=100,
            expected_quality=10,
            risk_level="low",
        ),
    ]

    comparison = await decision_maker.compare_strategies(strategies)

    assert len(comparison) == 2
    assert "score" in comparison[0]

    await db.disconnect()


@pytest.mark.asyncio
async def test_strategy_scoring():
    """Test strategy scoring algorithm"""
    db = Database("sqlite+aiosqlite:///:memory:")
    await db.connect()

    decision_maker = DecisionMaker(db)

    strategy = Strategy(
        name="Test",
        description="Test",
        expected_cost=50,
        expected_quality=8,
        risk_level="medium",
    )

    score = decision_maker.score_strategy(
        strategy,
        criteria={"max_cost": 100, "min_quality": 7},
    )

    assert score > 0

    await db.disconnect()
