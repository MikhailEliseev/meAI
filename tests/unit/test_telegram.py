# tests/unit/test_telegram.py
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from datetime import datetime, timezone
from meai.integrations.telegram import TelegramClient


@pytest.mark.asyncio
async def test_telegram_client_initialization():
    """Test TelegramClient can be initialized"""
    client = TelegramClient()

    assert client.client is None
    assert not client.connected


@pytest.mark.asyncio
async def test_telegram_connect():
    """Test connecting to Telegram"""
    client = TelegramClient()

    mock_telethon_client = AsyncMock()
    mock_telethon_client.connect = AsyncMock()
    mock_telethon_client.is_user_authorized = AsyncMock(return_value=True)

    with patch('meai.integrations.telegram.TelethonClient', return_value=mock_telethon_client):
        await client.connect(api_id="12345", api_hash="test-hash")

        assert client.connected
        mock_telethon_client.connect.assert_called_once()
        mock_telethon_client.is_user_authorized.assert_called_once()


@pytest.mark.asyncio
async def test_get_channel_messages():
    """Test getting messages from a channel"""
    client = TelegramClient()
    client.connected = True

    # Mock Telegram messages
    mock_message_1 = MagicMock()
    mock_message_1.id = 1
    mock_message_1.text = "SEO tips for 2024"
    mock_message_1.date = datetime(2024, 1, 1, tzinfo=timezone.utc)

    mock_message_2 = MagicMock()
    mock_message_2.id = 2
    mock_message_2.text = "Content marketing strategies"
    mock_message_2.date = datetime(2024, 1, 2, tzinfo=timezone.utc)

    mock_client = AsyncMock()
    mock_client.get_messages = AsyncMock(return_value=[mock_message_1, mock_message_2])
    client.client = mock_client

    messages = await client.get_channel_messages("test_channel", limit=2)

    assert len(messages) == 2
    assert messages[0]["message_id"] == 1
    assert messages[0]["text"] == "SEO tips for 2024"
    assert messages[1]["message_id"] == 2


@pytest.mark.asyncio
async def test_monitor_channels():
    """Test monitoring multiple channels"""
    client = TelegramClient()
    client.connected = True

    mock_message = MagicMock()
    mock_message.id = 1
    mock_message.text = "Test message"
    mock_message.date = datetime(2024, 1, 1, tzinfo=timezone.utc)

    mock_client = AsyncMock()
    mock_client.get_messages = AsyncMock(return_value=[mock_message])
    client.client = mock_client

    results = await client.monitor_channels(
        ["channel1", "channel2"],
        limit=1
    )

    assert len(results) == 2
    assert "channel1" in results
    assert "channel2" in results
    assert len(results["channel1"]) == 1
    assert results["channel1"][0]["message_id"] == 1


@pytest.mark.asyncio
async def test_telegram_not_connected_error():
    """Test error when trying to get messages without connecting"""
    client = TelegramClient()

    with pytest.raises(RuntimeError, match="Not connected"):
        await client.get_channel_messages("test_channel")


@pytest.mark.asyncio
async def test_telegram_disconnect():
    """Test disconnecting from Telegram"""
    client = TelegramClient()
    client.connected = True

    mock_client = AsyncMock()
    mock_client.disconnect = AsyncMock()
    client.client = mock_client

    await client.disconnect()

    assert not client.connected
    mock_client.disconnect.assert_called_once()
