"""
Tests for Keyword Research Agent.
"""

import pytest
from unittest.mock import AsyncMock, patch

from src.aim.subagents.seo.keyword_research_agent import (
    KeywordResearchAgent,
    KeywordCluster,
    KeywordIntent,
    KeywordPriority,
)
from src.aim.subagents.schemas.api_responses import KeywordDataUnified


@pytest.fixture
def agent():
    """Create agent instance."""
    return KeywordResearchAgent(
        semrush_api_key="test_semrush_key",
        ahrefs_api_key="test_ahrefs_key",
    )


@pytest.fixture
def mock_keywords():
    """Mock keyword data."""
    return [
        KeywordDataUnified(
            keyword="how to dental implants",
            volume=1000,
            difficulty=30,
            cpc=5.0,
            intent="informational",
            source="semrush",
            priority_score=50.0,
        ),
        KeywordDataUnified(
            keyword="best dental implants",
            volume=2000,
            difficulty=50,
            cpc=8.0,
            intent="commercial",
            source="semrush",
            priority_score=60.0,
        ),
        KeywordDataUnified(
            keyword="buy dental implants",
            volume=500,
            difficulty=40,
            cpc=12.0,
            intent="commercial",
            source="semrush",
            priority_score=55.0,
        ),
        KeywordDataUnified(
            keyword="dental implants cost",
            volume=1500,
            difficulty=35,
            cpc=6.0,
            intent="commercial",
            source="semrush",
            priority_score=58.0,
        ),
        KeywordDataUnified(
            keyword="dental implants near me",
            volume=800,
            difficulty=25,
            cpc=10.0,
            intent="navigational",
            source="semrush",
            priority_score=52.0,
        ),
    ]


@pytest.mark.asyncio
async def test_expand_keywords_semrush(agent, mock_keywords):
    """Test keyword expansion using SEMrush."""
    with patch.object(agent.semrush_client, "expand_keywords", new_callable=AsyncMock) as mock_expand:
        mock_expand.return_value = mock_keywords

        keywords = await agent._expand_keywords(
            seed_keyword="dental implants",
            max_keywords=50,
            min_volume=100,
            max_difficulty=70.0,
        )

        assert len(keywords) == 5
        assert all(k.volume >= 100 for k in keywords)
        assert all(k.difficulty <= 70.0 for k in keywords)


@pytest.mark.asyncio
async def test_expand_keywords_ahrefs_fallback(agent, mock_keywords):
    """Test keyword expansion fallback to Ahrefs."""
    with patch.object(agent.semrush_client, "expand_keywords", new_callable=AsyncMock) as mock_semrush:
        with patch.object(agent.ahrefs_client, "expand_keywords", new_callable=AsyncMock) as mock_ahrefs:
            # SEMrush fails
            mock_semrush.side_effect = Exception("SEMrush API error")
            # Ahrefs succeeds
            mock_ahrefs.return_value = mock_keywords

            keywords = await agent._expand_keywords(
                seed_keyword="dental implants",
                max_keywords=50,
                min_volume=100,
                max_difficulty=70.0,
            )

            assert len(keywords) == 5
            mock_ahrefs.assert_called_once()


def test_classify_intent_informational(agent):
    """Test intent classification for informational keywords."""
    keywords = [
        KeywordDataUnified(
            keyword="how to dental implants",
            volume=1000,
            difficulty=30,
            cpc=5.0,
            intent="informational",
            source="semrush",
            priority_score=50.0,
        ),
    ]

    intents = agent._classify_intent(keywords)

    assert len(intents) == 1
    assert intents[0].intent == "informational"
    assert intents[0].confidence > 0
    assert "how" in intents[0].signals


def test_classify_intent_commercial(agent):
    """Test intent classification for commercial keywords."""
    keywords = [
        KeywordDataUnified(
            keyword="best dental implants review",
            volume=2000,
            difficulty=50,
            cpc=8.0,
            intent="commercial",
            source="semrush",
            priority_score=60.0,
        ),
    ]

    intents = agent._classify_intent(keywords)

    assert len(intents) == 1
    assert intents[0].intent == "commercial"
    assert intents[0].confidence > 0
    assert "best" in intents[0].signals or "review" in intents[0].signals


def test_classify_intent_transactional(agent):
    """Test intent classification for transactional keywords."""
    keywords = [
        KeywordDataUnified(
            keyword="buy dental implants online",
            volume=500,
            difficulty=40,
            cpc=12.0,
            intent="commercial",
            source="semrush",
            priority_score=55.0,
        ),
    ]

    intents = agent._classify_intent(keywords)

    assert len(intents) == 1
    assert intents[0].intent == "transactional"
    assert intents[0].confidence > 0
    assert "buy" in intents[0].signals


def test_cluster_keywords(agent, mock_keywords):
    """Test keyword clustering."""
    clusters = agent._cluster_keywords(mock_keywords)

    # Should create clusters for keywords with 2+ common words
    assert len(clusters) >= 1

    # Check cluster structure
    for cluster in clusters:
        assert cluster.cluster_size >= 2
        assert cluster.total_volume > 0
        assert cluster.avg_difficulty > 0
        assert len(cluster.keywords) == cluster.cluster_size


def test_score_priorities(agent, mock_keywords):
    """Test priority scoring."""
    intents = agent._classify_intent(mock_keywords)
    priorities = agent._score_priorities(mock_keywords, intents)

    assert len(priorities) == len(mock_keywords)

    # Check priority scores are in range 0-100
    for priority in priorities:
        assert 0 <= priority.priority_score <= 100
        assert priority.volume > 0
        assert priority.difficulty >= 0
        assert priority.intent in ["informational", "commercial", "transactional", "navigational"]

    # Priorities should be sorted descending
    for i in range(len(priorities) - 1):
        assert priorities[i].priority_score >= priorities[i + 1].priority_score


def test_score_priorities_high_volume_low_difficulty(agent):
    """Test that high volume + low difficulty = high priority."""
    keywords = [
        KeywordDataUnified(
            keyword="easy keyword",
            volume=5000,
            difficulty=20,
            cpc=10.0,
            intent="commercial",
            source="semrush",
            priority_score=70.0,
        ),
        KeywordDataUnified(
            keyword="hard keyword",
            volume=100,
            difficulty=80,
            cpc=2.0,
            intent="informational",
            source="semrush",
            priority_score=30.0,
        ),
    ]

    intents = agent._classify_intent(keywords)
    priorities = agent._score_priorities(keywords, intents)

    # Easy keyword should have higher priority
    assert priorities[0].keyword == "easy keyword"
    assert priorities[0].priority_score > priorities[1].priority_score


@pytest.mark.asyncio
async def test_research_complete_workflow(agent, mock_keywords):
    """Test complete research workflow."""
    with patch.object(agent.semrush_client, "expand_keywords", new_callable=AsyncMock) as mock_expand:
        mock_expand.return_value = mock_keywords

        result = await agent.research(
            seed_keyword="dental implants",
            max_keywords=50,
            min_volume=100,
            max_difficulty=70.0,
        )

        # Check result structure
        assert result.seed_keyword == "dental implants"
        assert result.total_keywords == len(mock_keywords)
        assert len(result.keywords) == len(mock_keywords)
        assert len(result.intents) == len(mock_keywords)
        assert len(result.priorities) == len(mock_keywords)
        assert result.total_volume > 0
        assert result.avg_difficulty > 0
        assert result.avg_cpc > 0


@pytest.mark.asyncio
async def test_research_top_opportunities(agent, mock_keywords):
    """Test top opportunities identification."""
    with patch.object(agent.semrush_client, "expand_keywords", new_callable=AsyncMock) as mock_expand:
        mock_expand.return_value = mock_keywords

        result = await agent.research(
            seed_keyword="dental implants",
            max_keywords=50,
            min_volume=100,
            max_difficulty=70.0,
        )

        # Top opportunities: high volume, low difficulty
        for opp in result.top_opportunities:
            assert opp.difficulty < 40
            assert opp.volume > 100


def test_agent_capabilities():
    """Test agent capabilities reporting."""
    agent = KeywordResearchAgent(
        semrush_api_key="test_key",
        ahrefs_api_key="test_key",
    )

    # Agent should have these capabilities
    assert hasattr(agent, "research")
    assert hasattr(agent, "_expand_keywords")
    assert hasattr(agent, "_classify_intent")
    assert hasattr(agent, "_cluster_keywords")
    assert hasattr(agent, "_score_priorities")


def test_intent_classification_navigational_default(agent):
    """Test that keywords without signals default to navigational."""
    keywords = [
        KeywordDataUnified(
            keyword="xyz brand",
            volume=500,
            difficulty=30,
            cpc=5.0,
            intent="navigational",
            source="semrush",
            priority_score=45.0,
        ),
    ]

    intents = agent._classify_intent(keywords)

    assert len(intents) == 1
    assert intents[0].intent == "navigational"
    assert intents[0].confidence == 0.5
    assert len(intents[0].signals) == 0
