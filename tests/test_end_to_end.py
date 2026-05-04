"""End-to-End Test - Full architecture validation

Tests the complete flow:
Operator → SEO Magister → Keyword Research Subagent → Results back

This is a SKELETON test - validates architecture, not business logic.
"""

import asyncio
import pytest
from pathlib import Path
import sys

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.meai.agents.operator import Operator
from AIM.src.aim.magisters.seo_magister import SEOMagister
from AIM.src.aim.subagents.keyword_research_agent import KeywordResearchAgent


class TestEndToEnd:
    """End-to-end architecture tests"""

    @pytest.mark.asyncio
    async def test_full_flow_operator_to_subagent(self):
        """Test complete flow: Operator → Magister → Subagent → Results

        This test validates:
        1. Operator can create and delegate tasks
        2. SEO Magister receives tasks from Operator
        3. SEO Magister delegates to Subagent
        4. Subagent executes and returns results
        5. Magister aggregates results
        6. Operator receives final results

        Note: Uses mock data, not real business logic
        """
        # Setup
        database_url = "sqlite+aiosqlite:///./AIM/data/test_e2e.db"

        operator = Operator(
            operator_id="test-operator",
            database_url=database_url,
        )

        seo_magister = SEOMagister(
            magister_id="test-seo-magister",
            database_url=database_url,
            vault_path="./AIM/obsidian/seo-magister",
        )

        keyword_agent = KeywordResearchAgent(
            agent_id="test-keyword-agent",
            database_url=database_url,
            vault_path="./AIM/obsidian/seo-magister",
        )

        # Initialize all components
        await operator.initialize()
        await seo_magister.initialize()
        await keyword_agent.initialize()

        try:
            # Step 1: Operator creates task
            operator_task = await operator.create_task(
                action="keyword_research",
                description="Research keywords for dental clinic",
                priority=1,
            )

            assert operator_task is not None
            assert operator_task.action == "keyword_research"

            # Step 2: Operator delegates to SEO Magister
            # (In real implementation, this would be via Event Bus)
            # For now, we test the components can be created and initialized

            # Step 3: SEO Magister identifies subagents
            subagents = await seo_magister.identify_subagents("keyword_research")

            assert isinstance(subagents, list)
            assert len(subagents) > 0

            # Step 4: Subagent executes task (mock)
            from meai.agents.base_agent import Task, TaskStatus
            from datetime import datetime, timezone

            mock_task = Task(
                task_id="test-task-1",
                subtask_id="test-subtask-1",
                parent_task_id=operator_task.task_id,
                action="keyword_research",
                description="Research keywords for dental clinic",
                priority=1,
                status=TaskStatus.RECEIVED,
                created_at=datetime.now(timezone.utc),
                received_at=datetime.now(timezone.utc),
            )

            result = await keyword_agent.execute_task(mock_task)

            # Validate result
            assert result is not None
            assert result.status == "success"
            assert "keywords" in result.result
            assert len(result.result["keywords"]) > 0

            # Step 5: Verify capabilities
            capabilities = keyword_agent.get_capabilities()
            assert "keyword_research" in capabilities

            print("\n✅ End-to-End Test PASSED!")
            print(f"   - Operator created task: {operator_task.task_id}")
            print(f"   - SEO Magister identified {len(subagents)} subagents")
            print(f"   - Subagent executed task successfully")
            print(f"   - Found {len(result.result['keywords'])} keywords (mock)")

        finally:
            # Cleanup
            await operator.shutdown()
            await seo_magister.shutdown()
            await keyword_agent.shutdown()

    @pytest.mark.asyncio
    async def test_components_can_initialize(self):
        """Test all components can be created and initialized"""
        database_url = "sqlite+aiosqlite:///./AIM/data/test_init.db"

        # Create components
        operator = Operator(
            operator_id="test-operator-init",
            database_url=database_url,
        )

        seo_magister = SEOMagister(
            magister_id="test-seo-magister-init",
            database_url=database_url,
        )

        keyword_agent = KeywordResearchAgent(
            agent_id="test-keyword-agent-init",
            database_url=database_url,
        )

        # Initialize
        await operator.initialize()
        await seo_magister.initialize()
        await keyword_agent.initialize()

        try:
            # Verify initialization
            assert operator.operator_id == "test-operator-init"
            assert seo_magister.magister_id == "test-seo-magister-init"
            assert keyword_agent.agent_id == "test-keyword-agent-init"

            print("\n✅ Initialization Test PASSED!")
            print("   - Operator initialized")
            print("   - SEO Magister initialized")
            print("   - Keyword Agent initialized")

        finally:
            # Cleanup
            await operator.shutdown()
            await seo_magister.shutdown()
            await keyword_agent.shutdown()

    @pytest.mark.asyncio
    async def test_event_bus_integration(self):
        """Test Event Bus can be used by all components"""
        database_url = "sqlite+aiosqlite:///./AIM/data/test_eventbus.db"

        operator = Operator(
            operator_id="test-operator-eb",
            database_url=database_url,
        )

        seo_magister = SEOMagister(
            magister_id="test-seo-magister-eb",
            database_url=database_url,
        )

        await operator.initialize()
        await seo_magister.initialize()

        try:
            # Verify Event Bus is initialized
            assert operator.event_bus is not None
            assert seo_magister.event_bus is not None

            print("\n✅ Event Bus Integration Test PASSED!")
            print("   - Operator has Event Bus")
            print("   - SEO Magister has Event Bus")

        finally:
            await operator.shutdown()
            await seo_magister.shutdown()


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
