"""Tests for Architect"""

import pytest
from meai.core.architect import Architect, Decision, DecisionContext
from meai.storage.database import Database


@pytest.mark.asyncio
async def test_make_decision():
    """Test making a decision"""
    db = Database("sqlite+aiosqlite:///:memory:")
    await db.connect()

    architect = Architect(db)

    context = DecisionContext(
        goal="Create SEO agent",
        constraints=["budget: $100/month", "response_time: <2s"],
        available_resources={"agents": 0, "vault_space": "unlimited"},
    )

    decision = await architect.make_decision(context)

    assert decision is not None
    assert decision.action is not None
    assert decision.rationale is not None
    assert decision.confidence > 0

    await db.disconnect()


@pytest.mark.asyncio
async def test_evaluate_options():
    """Test evaluating multiple options"""
    db = Database("sqlite+aiosqlite:///:memory:")
    await db.connect()

    architect = Architect(db)

    options = [
        {"name": "Option A", "cost": 50, "quality": 8},
        {"name": "Option B", "cost": 100, "quality": 10},
        {"name": "Option C", "cost": 25, "quality": 5},
    ]

    context = DecisionContext(
        goal="Choose best option",
        constraints=["budget: $75"],
        available_resources={},
    )

    best_option = await architect.evaluate_options(options, context)

    assert best_option is not None
    assert best_option["cost"] <= 75

    await db.disconnect()


@pytest.mark.asyncio
async def test_analyze_context():
    """Test analyzing decision context"""
    db = Database("sqlite+aiosqlite:///:memory:")
    await db.connect()

    architect = Architect(db)

    context = DecisionContext(
        goal="Scale system",
        constraints=["max_agents: 10"],
        available_resources={"cpu": "50%", "memory": "2GB"},
    )

    analysis = await architect.analyze_context(context)

    assert "feasibility" in analysis
    assert "risks" in analysis
    assert "recommendations" in analysis

    await db.disconnect()


@pytest.mark.asyncio
async def test_decision_history():
    """Test tracking decision history"""
    db = Database("sqlite+aiosqlite:///:memory:")
    await db.connect()

    architect = Architect(db)

    context = DecisionContext(
        goal="Test decision",
        constraints=[],
        available_resources={},
    )

    # Make decision
    decision = await architect.make_decision(context)

    # Get history
    history = await architect.get_decision_history(limit=10)

    assert len(history) > 0
    assert history[0].action == decision.action

    await db.disconnect()


@pytest.mark.asyncio
async def test_confidence_scoring():
    """Test decision confidence scoring"""
    db = Database("sqlite+aiosqlite:///:memory:")
    await db.connect()

    architect = Architect(db)

    context = DecisionContext(
        goal="High confidence decision",
        constraints=["clear requirements"],
        available_resources={"all needed resources": "available"},
    )

    decision = await architect.make_decision(context)

    assert 0.0 <= decision.confidence <= 1.0

    await db.disconnect()
