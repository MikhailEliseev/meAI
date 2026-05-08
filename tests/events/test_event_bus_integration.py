"""Integration tests for Event Bus and Event Store"""

from datetime import datetime, timezone

import pytest
from meai.events.event_bus import EventBus
from meai.events.event_store import EventStore
from meai.events import ProjectCreatedEvent
from meai.events.project_events import ProjectCreatedData
from meai.events.base import ProjectStatus


@pytest.mark.asyncio
async def test_event_bus_auto_appends_to_store():
    """Test Event Bus automatically appends to Event Store"""
    bus = EventBus()
    store = EventStore()

    await bus.initialize()
    await store.initialize()

    # Connect store to bus
    bus.set_event_store(store)

    # Publish event
    event = ProjectCreatedEvent(
        source="operator",
        target="brand-magister",
        data=ProjectCreatedData(
            project_id="proj-001",
            client_name="Test Client",
            client_domain="testclient.com",
            client_contact="contact@testclient.com",
            industry="medical",
            initial_status=ProjectStatus.LEAD,
            source="Website Form",
            created_at=datetime.now(timezone.utc),
            notes="Test project for integration"
        )
    )

    await bus.publish(event)

    # Verify event in store
    stored = await store.get_by_id(str(event.id))
    assert stored is not None
    assert str(stored.id) == str(event.id)
    assert stored.type == "project.created"
    assert stored.source == "operator"
    assert stored.target == "brand-magister"

    await bus.close()
    await store.close()
