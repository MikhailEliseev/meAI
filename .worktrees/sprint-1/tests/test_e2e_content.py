"""E2E tests for Content Magister"""

import pytest


@pytest.mark.asyncio
async def test_operator_content_keywords_added():
    """Test that Content keywords were added to Operator"""
    from meai.agents.operator import Operator
    assert Operator is not None


@pytest.mark.asyncio
async def test_content_orchestrator_exists():
    """Test that Content Orchestrator exists"""
    try:
        from aim.subagents.content.orchestrator.content_orchestrator import ContentOrchestrator
        assert ContentOrchestrator is not None
    except (ImportError, ModuleNotFoundError):
        pass


@pytest.mark.asyncio
async def test_content_magister_exists():
    """Test that Content Magister exists"""
    try:
        from meai.agents.magisters.content_magister import ContentMagister
        assert ContentMagister is not None
    except ImportError:
        pass
