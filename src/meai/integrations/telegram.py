"""Telegram API client for channel monitoring"""

import asyncio
from typing import Any
from telethon import TelegramClient as TelethonClient


class TelegramClient:
    """Async Telegram client for channel monitoring

    Uses Telethon library for Telegram API access.
    """

    def __init__(self, session_name: str = "meai_session"):
        """Initialize Telegram client

        Args:
            session_name: Session file name for Telethon
        """
        self.session_name = session_name
        self.client: TelethonClient | None = None
        self.connected = False

    async def connect(self, api_id: str, api_hash: str) -> None:
        """Connect to Telegram

        Args:
            api_id: Telegram API ID
            api_hash: Telegram API hash
        """
        self.client = TelethonClient(self.session_name, api_id, api_hash)
        await self.client.connect()

        # Check if authorized
        if not await self.client.is_user_authorized():
            raise RuntimeError(
                "User not authorized. Please run authorization flow first."
            )

        self.connected = True

    async def disconnect(self) -> None:
        """Disconnect from Telegram"""
        if self.client:
            await self.client.disconnect()
            self.connected = False

    async def get_channel_messages(
        self, channel: str, limit: int = 100
    ) -> list[dict[str, Any]]:
        """Get messages from a channel

        Args:
            channel: Channel username or ID
            limit: Maximum number of messages

        Returns:
            List of message dictionaries with message_id, text, date
        """
        if not self.connected:
            raise RuntimeError("Not connected. Call connect() first.")

        messages = await self.client.get_messages(channel, limit=limit)

        result = []
        for msg in messages:
            result.append(
                {
                    "message_id": msg.id,
                    "text": msg.text or "",
                    "date": msg.date.isoformat(),
                }
            )

        return result

    async def monitor_channels(
        self, channels: list[str], limit: int = 100
    ) -> dict[str, list[dict[str, Any]]]:
        """Monitor multiple channels for new messages

        Args:
            channels: List of channel usernames or IDs
            limit: Maximum messages per channel

        Returns:
            Dictionary mapping channel to list of messages
        """
        if not self.connected:
            raise RuntimeError("Not connected. Call connect() first.")

        results = {}

        # Fetch messages from all channels concurrently
        tasks = [self.get_channel_messages(channel, limit) for channel in channels]
        messages_lists = await asyncio.gather(*tasks)

        # Map results to channels
        for channel, messages in zip(channels, messages_lists):
            results[channel] = messages

        return results
