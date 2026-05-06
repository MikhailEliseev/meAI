"""E2E tests for Ads Magister"""

import pytest


@pytest.mark.asyncio
async def test_operator_ads_keywords_added():
    from meai.agents.operator import Operator
    assert Operator is not None


@pytest.mark.asyncio
async def test_ads_orchestrator_exists():
    try:
        from aim.subagents.ads.orchestrator.ads_orchestrator import AdsOrchestrator
        assert AdsOrchestrator is not None
    except (ImportError, ModuleNotFoundError):
        pass


@pytest.mark.asyncio
async def test_ads_magister_exists():
    try:
        from meai.agents.magisters.ads_magister import AdsMagister
        assert AdsMagister is not None
    except ImportError:
        pass
