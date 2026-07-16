"""Integration test: Magisters + EventStore"""

import pytest
from pathlib import Path
from datetime import datetime

from meai.events import EventBus, EventStore, ProjectCreatedEvent
from meai.agents.magisters.seo_magister import SEOMagister


@pytest.mark.asyncio
async def test_magister_events_stored_in_event_store():
    """Test that Magister events are automatically stored in EventStore"""

    # Setup
    bus = EventBus()
    store = EventStore()

    await bus.initialize()
    await store.initialize()

    # Create SEO Magister with EventStore
    magister = SEOMagister(
        agent_id="seo-test-1",
        event_bus=bus,
        event_store=store,
        vault_path=Path("./test_vault/seo-magister"),
    )

    await magister.initialize()

    # Publish event through Magister
    event = ProjectCreatedEvent(
        source="seo-test-1",
        target="operator",
        project_name="Test SEO Project",
        project_type="medical_marketing",
        client_name="Test Client"
    )

    await bus.publish(event)

    # Verify event in EventStore
    stored = await store.get_by_id(event.id)

    assert stored is not None, "Event should be in EventStore"
    assert stored.id == event.id
    assert stored.source == "seo-test-1"
    assert stored.type == "project.created"

    # Cleanup
    await bus.close()
    await store.close()


@pytest.mark.asyncio
async def test_magister_audit_trail():
    """Test complete audit trail for Magister operations"""

    # Setup
    bus = EventBus()
    store = EventStore()

    await bus.initialize()
    await store.initialize()

    # Create Magister
    magister = SEOMagister(
        agent_id="seo-audit-1",
        event_bus=bus,
        event_store=store,
        vault_path=Path("./test_vault/seo-magister"),
    )

    await magister.initialize()

    # Publish multiple events
    events = []
    for i in range(3):
        event = ProjectCreatedEvent(
            source="seo-audit-1",
            target="operator",
            project_name=f"Project {i}",
            project_type="medical_marketing",
            client_name=f"Client {i}"
        )
        await bus.publish(event)
        events.append(event)

    # Verify all events in EventStore
    from_time = datetime.min
    stored_events = await store.get_by_time_range(from_time=from_time)

    assert len(stored_events) >= 3, "Should have at least 3 events"

    # Verify events are from our Magister
    magister_events = [e for e in stored_events if e.source == "seo-audit-1"]
    assert len(magister_events) == 3, "Should have exactly 3 events from Magister"

    # Cleanup
    await bus.close()
    await store.close()


if __name__ == "__main__":
    import asyncio

    print("Running Magisters + EventStore integration tests...")

    asyncio.run(test_magister_events_stored_in_event_store())
    print("✅ Test 1: Magister events stored in EventStore - PASSED")

    asyncio.run(test_magister_audit_trail())
    print("✅ Test 2: Complete audit trail - PASSED")

    print("\n🎉 All integration tests PASSED!")
