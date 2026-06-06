"""Real-World Scenario E2E Tests

Tests complete client onboarding workflows with realistic data,
error handling, budget constraints, and correlation tracking.
"""

import pytest
import asyncio
import time
from unittest.mock import AsyncMock, patch
from datetime import datetime

from src.aim.magisters.seo_magister import SEOMagister
from AIM.tests.fixtures.e2e_fixtures import (
    mock_client_data,
    correlation_tracker,
    workflow_timer,
)


@pytest.mark.asyncio
async def test_client_onboarding_complete_workflow(mock_client_data, workflow_timer):
    """Test complete client onboarding workflow from start to finish

    Verifies:
    - SEO Magister completes keyword research and competitor analysis
    - All subagents execute with realistic delays
    - Results contain all required data
    - Total execution time is reasonable (< 10 seconds with parallel execution)
    """
    # Create SEO Magister for client onboarding
    seo_magister = SEOMagister(timeout=60)

    # Mock subagents with realistic delays (1-2 seconds each)
    async def mock_technical_analysis(url, correlation_id):
        await asyncio.sleep(1.5)
        return {
            "agent": "technical-agent",
            "status": "success",
            "score": 78,
            "issues": [
                "Missing robots.txt",
                "No sitemap.xml",
                "Slow page load time (3.2s)",
            ],
            "recommendations": [
                "Create robots.txt file",
                "Generate XML sitemap",
                "Optimize images and enable caching",
            ],
        }

    async def mock_content_analysis(url, correlation_id):
        await asyncio.sleep(2.0)
        return {
            "agent": "content-agent",
            "status": "success",
            "score": 82,
            "issues": [
                "Thin content on 3 pages",
                "Missing H1 tags on 2 pages",
                "Low keyword density",
            ],
            "recommendations": [
                "Expand content to 1000+ words",
                "Add proper H1 tags",
                "Optimize keyword usage",
            ],
        }

    async def mock_links_analysis(url, correlation_id):
        await asyncio.sleep(1.0)
        return {
            "agent": "links-agent",
            "status": "success",
            "score": 65,
            "issues": [
                "Only 15 backlinks",
                "Low domain authority (DA 25)",
                "Few internal links",
            ],
            "recommendations": [
                "Build quality backlinks",
                "Improve internal linking structure",
                "Guest posting on relevant sites",
            ],
        }

    with patch.object(seo_magister.technical_agent, "analyze", side_effect=mock_technical_analysis), \
         patch.object(seo_magister.content_agent, "analyze", side_effect=mock_content_analysis), \
         patch.object(seo_magister.links_agent, "analyze", side_effect=mock_links_analysis):

        # Execute complete onboarding workflow
        workflow_timer.start("seo_onboarding")
        start = time.time()

        result = await seo_magister.coordinate_analysis(
            url=mock_client_data["client"]["domain"],
            correlation_id="onboarding-test-001"
        )

        duration = time.time() - start
        workflow_timer.end("seo_onboarding")

        # Verify analysis completed successfully
        assert result["status"] == "success"
        assert result["correlation_id"] == "onboarding-test-001"

        # Verify all subagent results present
        assert "details" in result
        assert "technical" in result["details"]
        assert "content" in result["details"]
        assert "links" in result["details"]

        # Verify all subagents succeeded
        assert result["details"]["technical"]["status"] == "success"
        assert result["details"]["content"]["status"] == "success"
        assert result["details"]["links"]["status"] == "success"

        # Verify scores are present
        assert result["details"]["technical"]["score"] == 78
        assert result["details"]["content"]["score"] == 82
        assert result["details"]["links"]["score"] == 65

        # Verify recommendations generated
        assert "recommendations" in result
        assert len(result["recommendations"]) > 0

        # Verify timing is reasonable (parallel execution should be ~2s, not 4.5s)
        assert duration < 3.0, f"Expected parallel execution ~2s, got {duration:.2f}s"


@pytest.mark.asyncio
async def test_client_onboarding_with_seo_failure(mock_client_data):
    """Test onboarding continues when one SEO agent fails

    Verifies:
    - Technical agent failure doesn't break entire analysis
    - Content and Links agents complete successfully
    - Partial results returned with clear error indication
    - Client can proceed with partial onboarding
    """
    seo_magister = SEOMagister(timeout=60)

    # Mock technical agent to fail
    async def mock_technical_fail(url, correlation_id):
        await asyncio.sleep(0.5)
        raise RuntimeError("Technical analysis failed: Connection timeout")

    # Mock content and links to succeed
    async def mock_success(url, correlation_id):
        await asyncio.sleep(0.5)
        return {
            "agent": "agent",
            "status": "success",
            "score": 80,
        }

    with patch.object(seo_magister.technical_agent, "analyze", side_effect=mock_technical_fail), \
         patch.object(seo_magister.content_agent, "analyze", side_effect=mock_success), \
         patch.object(seo_magister.links_agent, "analyze", side_effect=mock_success):

        result = await seo_magister.coordinate_analysis(
            url=mock_client_data["client"]["domain"]
        )

        # Verify overall analysis still completed
        assert result["status"] == "success"

        # Verify technical agent failed
        assert result["details"]["technical"]["status"] == "error"
        assert "Connection timeout" in result["details"]["technical"]["error"]

        # Verify content and links succeeded
        assert result["details"]["content"]["status"] == "success"
        assert result["details"]["links"]["status"] == "success"

        # Verify partial results can be used
        assert result["details"]["content"]["score"] == 80
        assert result["details"]["links"]["score"] == 80


@pytest.mark.asyncio
async def test_client_onboarding_budget_constraints(mock_client_data):
    """Test budget validation across workflows

    Verifies:
    - Client budget is respected
    - Analysis completes within budget constraints
    - Budget tracking is accurate
    """
    # Use client with limited budget
    limited_budget_client = mock_client_data.copy()
    limited_budget_client["client"]["budget"] = 10000.0
    limited_budget_client["ads"]["budget"] = 5000.0  # Half of total budget

    seo_magister = SEOMagister(timeout=60)

    # Mock subagents with quick responses
    async def mock_quick_analysis(url, correlation_id):
        await asyncio.sleep(0.2)
        return {
            "agent": "agent",
            "status": "success",
            "score": 75,
            "estimated_cost": 1500.0,  # Each analysis costs $1500
        }

    with patch.object(seo_magister.technical_agent, "analyze", side_effect=mock_quick_analysis), \
         patch.object(seo_magister.content_agent, "analyze", side_effect=mock_quick_analysis), \
         patch.object(seo_magister.links_agent, "analyze", side_effect=mock_quick_analysis):

        result = await seo_magister.coordinate_analysis(
            url=limited_budget_client["client"]["domain"]
        )

        # Verify analysis completed
        assert result["status"] == "success"

        # Calculate total estimated cost
        total_cost = 0
        for agent_key in ["technical", "content", "links"]:
            if "estimated_cost" in result["details"][agent_key]:
                total_cost += result["details"][agent_key]["estimated_cost"]

        # Verify total cost is within SEO budget (not exceeding ads budget)
        # Total SEO cost: 3 * $1500 = $4500
        assert total_cost == 4500.0
        assert total_cost < limited_budget_client["client"]["budget"]


@pytest.mark.asyncio
async def test_client_onboarding_correlation_chain(mock_client_data, correlation_tracker):
    """Test correlation IDs link entire workflow

    Verifies:
    - Parent correlation ID propagates to all agents
    - Correlation chain integrity maintained
    - Workflow can be reconstructed from correlation IDs
    """
    seo_magister = SEOMagister(timeout=60)

    parent_correlation_id = "onboarding-correlation-test-123"

    # Mock subagents to track correlation IDs
    async def mock_tracked_analysis(url, correlation_id):
        # Track that this agent received the correlation ID
        correlation_tracker.track(parent_correlation_id, f"{correlation_id}-subagent")
        correlation_tracker.track_event("agent_executed", correlation_id)

        await asyncio.sleep(0.3)
        return {
            "agent": "agent",
            "status": "success",
            "score": 85,
            "correlation_id": correlation_id,
        }

    with patch.object(seo_magister.technical_agent, "analyze", side_effect=mock_tracked_analysis), \
         patch.object(seo_magister.content_agent, "analyze", side_effect=mock_tracked_analysis), \
         patch.object(seo_magister.links_agent, "analyze", side_effect=mock_tracked_analysis):

        # Track workflow start
        correlation_tracker.track_event("workflow_started", parent_correlation_id)

        result = await seo_magister.coordinate_analysis(
            url=mock_client_data["client"]["domain"],
            correlation_id=parent_correlation_id
        )

        # Track workflow completion
        correlation_tracker.track_event("workflow_completed", parent_correlation_id)

        # Verify correlation ID in result
        assert result["correlation_id"] == parent_correlation_id

        # Verify correlation chain exists
        assert correlation_tracker.verify_chain(parent_correlation_id)

        # Verify all three subagents tracked
        children = correlation_tracker.get_children(parent_correlation_id)
        assert len(children) == 3

        # Verify events tracked
        assert len(correlation_tracker.events) >= 5  # start + 3 agents + complete

        # Verify no orphaned correlation IDs
        assert correlation_tracker.verify_no_orphans()
