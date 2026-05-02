"""Rollback manager - orchestrate snapshot + event replay"""

from datetime import datetime, timezone
from typing import Any
import structlog

from ..memory.obsidian import ObsidianVault
from ..events.event_store import EventStore

logger = structlog.get_logger()


class RollbackManager:
    """Manage rollback using snapshots + event replay"""

    def __init__(self, vault: ObsidianVault, event_store: EventStore):
        self.vault = vault
        self.event_store = event_store

    async def create_checkpoint(self, name: str) -> str:
        """Create checkpoint (snapshot + event marker)"""
        logger.info("rollback.creating_checkpoint", name=name)

        # Create vault snapshot
        snapshot_path = await self.vault.create_snapshot(name)

        # Record checkpoint event
        checkpoint_time = datetime.now(timezone.utc)

        from ..events.event_store import Event

        event = Event(
            aggregate_id="system",
            aggregate_type="checkpoint",
            event_type="checkpoint_created",
            event_version=1,
            payload={
                "name": name,
                "snapshot_path": str(snapshot_path),
                "timestamp": checkpoint_time.isoformat(),
            },
            timestamp=checkpoint_time.isoformat(),
            idempotency_key=f"checkpoint_{name}",
        )

        await self.event_store.append_event(event)

        logger.info("rollback.checkpoint_created", name=name)

        return name

    async def rollback_to_checkpoint(self, checkpoint_id: str) -> None:
        """Rollback to checkpoint"""
        logger.info("rollback.starting", checkpoint=checkpoint_id)

        # Find checkpoint event
        events = await self.event_store.get_events(event_type="checkpoint_created")
        checkpoint_event = None

        for event in events:
            if event.payload["name"] == checkpoint_id:
                checkpoint_event = event
                break

        if not checkpoint_event:
            raise ValueError(f"Checkpoint not found: {checkpoint_id}")

        # Restore vault snapshot
        await self.vault.restore_snapshot(checkpoint_id)

        # Replay events after checkpoint (if needed)
        checkpoint_time = checkpoint_event.payload["timestamp"]

        events_to_replay = await self.event_store.replay_events(
            aggregate_id="system",
            from_timestamp=checkpoint_time,
        )

        logger.info(
            "rollback.completed",
            checkpoint=checkpoint_id,
            events_replayed=len(events_to_replay),
        )

    async def list_checkpoints(self) -> list[dict[str, Any]]:
        """List available checkpoints"""
        events = await self.event_store.get_events(event_type="checkpoint_created")

        checkpoints = []
        for event in events:
            checkpoints.append(
                {
                    "name": event.payload["name"],
                    "timestamp": event.payload["timestamp"],
                    "snapshot_path": event.payload["snapshot_path"],
                }
            )

        return checkpoints

    async def delete_checkpoint(self, checkpoint_id: str) -> None:
        """Delete checkpoint"""
        logger.info("rollback.deleting_checkpoint", checkpoint=checkpoint_id)

        # Find checkpoint event
        events = await self.event_store.get_events(event_type="checkpoint_created")
        checkpoint_event = None

        for event in events:
            if event.payload["name"] == checkpoint_id:
                checkpoint_event = event
                break

        if not checkpoint_event:
            raise ValueError(f"Checkpoint not found: {checkpoint_id}")

        # Delete snapshot
        snapshot_path = checkpoint_event.payload["snapshot_path"]
        await self.vault.delete_snapshot(checkpoint_id)

        # Record deletion event
        from ..events.event_store import Event

        deletion_event = Event(
            aggregate_id="system",
            aggregate_type="checkpoint",
            event_type="checkpoint_deleted",
            event_version=1,
            payload={
                "name": checkpoint_id,
                "snapshot_path": snapshot_path,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            },
            timestamp=datetime.now(timezone.utc).isoformat(),
            idempotency_key=f"checkpoint_delete_{checkpoint_id}",
        )

        await self.event_store.append_event(deletion_event)

        logger.info("rollback.checkpoint_deleted", checkpoint=checkpoint_id)
