"""Abstract base for channel monitors — Telegram, Instagram, VK, WhatsApp, Web Chat.

Each channel monitor is responsible for:
- Receiving incoming messages from its channel
- Publishing them to EventBus as sales.message.received
- Listening for sales.message.send events and delivering responses

Part of Phase 13: AI Sales Admin Agent.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any


@dataclass
class ChannelMessage:
    """Normalised incoming message from any channel."""

    channel: str
    channel_user_id: str
    text: str
    message_id: str = ""
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    metadata: dict[str, Any] = field(default_factory=dict)


class BaseChannelMonitor(ABC):
    """Abstract channel monitor.

    Subclass per channel: TelegramMonitor, InstagramMonitor, VKMonitor, etc.
    """

    def __init__(self, channel: str, event_bus=None) -> None:
        self.channel = channel
        self._event_bus = event_bus
        self._running = False

    @property
    def running(self) -> bool:
        return self._running

    @abstractmethod
    async def start(self) -> None:
        """Start listening for incoming messages."""

    @abstractmethod
    async def stop(self) -> None:
        """Stop listening and clean up resources."""

    @abstractmethod
    async def send_message(self, channel_user_id: str, text: str) -> bool:
        """Deliver an outgoing message to the channel.

        Returns True if delivery succeeded.
        """

    async def publish_incoming(self, message: ChannelMessage) -> str | None:
        """Publish an incoming message to EventBus for the SalesAdminMagister.

        Returns the event ID, or None if no EventBus is configured.
        """
        if self._event_bus is None:
            return None

        from meai.events.event_bus import Event
        from datetime import datetime, timezone

        event = Event(
            event_type="sales.message.received",
            payload={
                "channel": message.channel,
                "channel_user_id": message.channel_user_id,
                "text": message.text,
                "message_id": message.message_id,
                "timestamp": message.timestamp.isoformat(),
                "metadata": message.metadata,
            },
        )
        await self._event_bus.publish(event)
        return event.event_id
