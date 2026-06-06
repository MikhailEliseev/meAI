"""Integration tests for UTM-to-campaign attribution pipeline."""
import pytest
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock

from src.aim.subagents.ads.attribution_pipeline import AttributionPipeline
from src.aim.models.campaign_models import Campaign, CampaignAttribution
from meai.events.event_bus import Event


@pytest.fixture
def mock_event_bus():
    bus = MagicMock()
    bus.subscribe = MagicMock()
    bus.publish = AsyncMock()
    return bus


@pytest.fixture
def mock_db_factory():
    async def factory():
        session = AsyncMock()
        session.add = MagicMock()
        session.commit = AsyncMock()
        session.execute = AsyncMock()
        return session
    return factory


@pytest.fixture
def pipeline(mock_event_bus, mock_db_factory):
    return AttributionPipeline(
        event_bus=mock_event_bus,
        db_session_factory=mock_db_factory,
    )


@pytest.mark.asyncio
async def test_utm_to_lead_link(pipeline, mock_event_bus):
    """Lead with UTM params matching a campaign -> attribution created."""
    campaign = Campaign(
        id=1,
        external_id="yd-123",
        name="Medical Campaign",
        platform="yandex",
        utm_source="yandex",
        utm_campaign="med-1",
        start_date=datetime.now(timezone.utc),
    )

    db = await pipeline.db_factory()
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = campaign
    db.execute.return_value = mock_result

    event = Event(
        event_type="lead.created",
        payload={
            "id": "lead_20260520_001",
            "utm_source": "yandex",
            "utm_campaign": "med-1",
            "utm_medium": "cpc",
        },
    )

    await pipeline.on_lead_created(event)

    db.add.assert_called_once()
    db.commit.assert_called_once()
    mock_event_bus.publish.assert_called_once()
    published_event = mock_event_bus.publish.call_args[0][0]
    assert published_event.event_type == "campaign.attribution"
    assert published_event.payload["campaign_id"] == 1
    assert published_event.payload["lead_id"] == "lead_20260520_001"


@pytest.mark.asyncio
async def test_no_utm_skips_attribution(pipeline, mock_event_bus):
    """Lead without UTM params -> no attribution, no event."""
    event = Event(
        event_type="lead.created",
        payload={
            "id": "lead_20260520_002",
            "utm_source": None,
            "utm_campaign": None,
        },
    )

    await pipeline.on_lead_created(event)

    db = await pipeline.db_factory()
    db.add.assert_not_called()
    mock_event_bus.publish.assert_not_called()


@pytest.mark.asyncio
async def test_no_matching_campaign(pipeline, mock_event_bus):
    """Lead with UTM but no matching campaign -> skip."""
    db = await pipeline.db_factory()
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = None
    db.execute.return_value = mock_result

    event = Event(
        event_type="lead.created",
        payload={
            "id": "lead_20260520_003",
            "utm_source": "unknown",
            "utm_campaign": "no-match",
        },
    )

    await pipeline.on_lead_created(event)

    db.add.assert_not_called()
    mock_event_bus.publish.assert_not_called()


@pytest.mark.asyncio
async def test_pipeline_start_subscribes(pipeline, mock_event_bus):
    """start() subscribes to lead.created events."""
    pipeline.start()
    mock_event_bus.subscribe.assert_called_once()
    event_type = mock_event_bus.subscribe.call_args[0][0]
    assert event_type == "lead.created"
