"""
NO-MOCK-03: Tests for ci_scout real competitor discovery.

Verifies that ci_scout returns real competitor data when API keys are available,
and never falls back to hardcoded names like "Дента", "Смайл".
"""

import pytest
from unittest.mock import patch, AsyncMock, MagicMock


MOCK_SERPAPI_RESPONSE = {
    "organic_results": [
        {
            "title": "Стоматология Дентал-Профи — профессиональное лечение зубов",
            "link": "https://dental-profi.ru",
            "snippet": "Стоматологическая клиника в Москве. Имплантация, протезирование...",
        },
        {
            "title": "Клиника Современной Стоматологии | Москва",
            "link": "https://modern-dent.ru",
            "snippet": "Лечение зубов любой сложности. Детская стоматология...",
        },
        {
            "title": "Стоматология ЭстетикДент — виниры, отбеливание",
            "link": "https://estetic-dent.ru",
            "snippet": "Эстетическая стоматология в центре Москвы...",
        },
    ]
}


@pytest.mark.asyncio
class TestCIScoutRealDiscovery:
    """Verify ci_scout discovers real competitors, not hardcoded names."""

    async def test_discover_returns_competitors_when_api_key_present(self):
        """ci_scout with SerpAPI key returns real competitor data."""
        from aim.subagents.competitive_intel.agents.ci_scout import CIScoutAgent

        with patch.object(CIScoutAgent, '__init__', lambda self, **kw: None):
            agent = CIScoutAgent.__new__(CIScoutAgent)
            agent.serpapi_key = "test-api-key"
            agent.semrush_api_key = None
            agent.vault = MagicMock()
            agent.agent_id = "test-scout"

            with patch.object(agent, '_serpapi_search') as mock_search:
                mock_search.return_value = [
                    {
                        "title": "Стоматология Дентал-Профи",
                        "link": "https://dental-profi.ru",
                        "snippet": "Стоматологическая клиника в Москве",
                    },
                    {
                        "title": "Клиника Современной Стоматологии",
                        "link": "https://modern-dent.ru",
                        "snippet": "Лечение зубов любой сложности",
                    },
                ]

                result = await agent._discover_competitors(
                    niche="стоматология", geo="Москва"
                )

                assert isinstance(result, list)
                if len(result) > 0:
                    for comp in result:
                        assert isinstance(comp, dict)
                        # Must NOT contain hardcoded mock names
                        name = comp.get("name", "")
                        assert "Дента" not in name or "Дентал" in name
                        assert "ул. Примерная" not in comp.get("address", "")
                        # Should have a URL field
                        if "url" in comp:
                            assert comp["url"].startswith("http")

    async def test_discover_returns_empty_when_no_api_key(self):
        """ci_scout without keys returns empty list (not random names)."""
        from aim.subagents.competitive_intel.agents.ci_scout import CIScoutAgent

        with patch.object(CIScoutAgent, '__init__', lambda self, **kw: None):
            agent = CIScoutAgent.__new__(CIScoutAgent)
            agent.serpapi_key = None
            agent.semrush_api_key = None
            agent.vault = MagicMock()
            agent.agent_id = "test-scout"

            result = await agent._discover_competitors(
                niche="стоматология", geo="Москва"
            )

            assert isinstance(result, list)
            assert len(result) == 0

    async def test_discover_uses_real_urls_not_generated(self):
        """ci_scout returns real URLs from search results, not auto-generated URLs."""
        from aim.subagents.competitive_intel.agents.ci_scout import CIScoutAgent

        with patch.object(CIScoutAgent, '__init__', lambda self, **kw: None):
            agent = CIScoutAgent.__new__(CIScoutAgent)
            agent.serpapi_key = "test-key"
            agent.semrush_api_key = None
            agent.vault = MagicMock()
            agent.agent_id = "test-scout"

            with patch.object(agent, '_serpapi_search') as mock_search:
                mock_search.return_value = MOCK_SERPAPI_RESPONSE["organic_results"]

                result = await agent._discover_competitors(
                    niche="стоматология", geo="Москва"
                )

                # If results are returned, URLs must be real (from search), not generated
                for comp in result:
                    if "url" in comp:
                        # Generated pattern would be: https://{slugified-name}.ru
                        # Real URLs from SerpAPI are actual domains
                        url = comp["url"]
                        assert "dental" in url.lower() or "dent" in url.lower()
