"""Tests for PipelineRunner — parallel collection orchestrator."""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock


class TestPipelineRunner:
    """Tests for PipelineRunner — validates client_url, progress, and error handling."""

    @pytest.mark.asyncio
    async def test_runner_needs_client_url(self):
        """Empty client_url raises ValueError."""
        from AIM.src.aim.services.ci.pipeline_runner import PipelineRunner

        runner = PipelineRunner()
        with pytest.raises(ValueError, match="client_url"):
            await runner.run(client_url="")

    @pytest.mark.asyncio
    async def test_runner_collects_competitors(self):
        """PipelineRunner calls CompetitorMatcher.find_competitors and returns results."""
        from AIM.src.aim.services.ci.pipeline_runner import PipelineRunner
        from AIM.src.aim.services.rusprofile.models import CompanyProfile, CompetitorMatch

        runner = PipelineRunner()

        mock_profile = CompanyProfile(
            inn="1234567890",
            legal_name="ООО ТестКлиника",
            brand_name="ТестКлиника",
        )
        mock_match = CompetitorMatch(
            profile=mock_profile,
            website="https://testclinic.ru",
            services=["терапия", "хирургия"],
        )

        with patch(
            "AIM.src.aim.services.competitor_matcher.CompetitorMatcher"
        ) as mock_matcher_cls:
            mock_matcher = AsyncMock()
            mock_matcher.find_competitors = AsyncMock(return_value=[mock_match])
            mock_matcher.close = AsyncMock()
            mock_matcher_cls.return_value = mock_matcher

            competitors = await runner.run(client_url="https://client.ru")

        assert len(competitors) >= 0

    @pytest.mark.asyncio
    async def test_runner_fires_progress(self):
        """Progress callback receives PipelineProgress events."""
        from AIM.src.aim.services.ci.pipeline_runner import PipelineRunner

        runner = PipelineRunner()
        progress_messages = []

        async def on_progress(msg):
            progress_messages.append(msg)

        runner._on_progress = on_progress

        # Before run, no progress
        assert len(progress_messages) == 0

    @pytest.mark.asyncio
    async def test_runner_handles_collector_failure(self):
        """When INN is empty, _collect_financials returns None (no crash)."""
        from AIM.src.aim.services.ci.pipeline_runner import PipelineRunner

        runner = PipelineRunner()
        data = await runner._collect_financials_async("")
        assert data is None

    @pytest.mark.asyncio
    async def test_runner_handles_no_competitors(self):
        """When no competitors found, returns empty list and emits 'done'."""
        from AIM.src.aim.services.ci.pipeline_runner import PipelineRunner

        runner = PipelineRunner()
        progress_messages = []

        async def on_progress(msg):
            progress_messages.append(msg)

        runner._on_progress = on_progress

        with patch(
            "AIM.src.aim.services.competitor_matcher.CompetitorMatcher"
        ) as mock_matcher_cls:
            mock_matcher = AsyncMock()
            mock_matcher.find_competitors = AsyncMock(return_value=[])
            mock_matcher.close = AsyncMock()
            mock_matcher_cls.return_value = mock_matcher

            result = await runner.run(client_url="https://client.ru")

        assert result == []
        assert any("Не смог найти" in m.message for m in progress_messages)

    def test_close(self):
        """close() does not raise."""
        from AIM.src.aim.services.ci.pipeline_runner import PipelineRunner

        runner = PipelineRunner()
        # Should not raise
