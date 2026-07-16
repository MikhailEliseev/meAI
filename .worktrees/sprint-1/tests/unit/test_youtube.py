# tests/unit/test_youtube.py
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from meai.integrations.youtube import YouTubeClient


@pytest.mark.asyncio
async def test_youtube_client_initialization():
    """Test YouTubeClient can be initialized"""
    client = YouTubeClient(api_key="test-key")

    assert client.api_key == "test-key"


@pytest.mark.asyncio
async def test_get_channel_videos():
    """Test getting recent videos from a channel"""
    client = YouTubeClient(api_key="test-key")

    # Mock YouTube API response
    mock_response = {
        "items": [
            {
                "id": {"videoId": "video1"},
                "snippet": {
                    "title": "SEO Tips 2024",
                    "description": "Learn SEO",
                    "publishedAt": "2024-01-01T00:00:00Z",
                },
            },
            {
                "id": {"videoId": "video2"},
                "snippet": {
                    "title": "Content Marketing",
                    "description": "Marketing tips",
                    "publishedAt": "2024-01-02T00:00:00Z",
                },
            },
        ]
    }

    with patch.object(client, '_make_request', new_callable=AsyncMock) as mock_request:
        mock_request.return_value = mock_response

        videos = await client.get_channel_videos("UC_test_channel", max_results=2)

        assert len(videos) == 2
        assert videos[0]["video_id"] == "video1"
        assert videos[0]["title"] == "SEO Tips 2024"
        assert videos[1]["video_id"] == "video2"


@pytest.mark.asyncio
async def test_get_video_transcript():
    """Test extracting video transcript"""
    client = YouTubeClient(api_key="test-key")

    mock_transcript = [
        {"text": "Hello everyone", "start": 0.0, "duration": 2.0},
        {"text": "Today we talk about SEO", "start": 2.0, "duration": 3.0},
    ]

    with patch('youtube_transcript_api.YouTubeTranscriptApi.fetch') as mock_fetch:
        mock_fetch.return_value = mock_transcript

        transcript = await client.get_video_transcript("video123")

        assert "Hello everyone" in transcript
        assert "Today we talk about SEO" in transcript


@pytest.mark.asyncio
async def test_monitor_channels():
    """Test monitoring multiple channels"""
    client = YouTubeClient(api_key="test-key")

    mock_response = {
        "items": [
            {
                "id": {"videoId": "video1"},
                "snippet": {
                    "title": "Video 1",
                    "description": "Description 1",
                    "publishedAt": "2024-01-01T00:00:00Z",
                },
            }
        ]
    }

    with patch.object(client, '_make_request', new_callable=AsyncMock) as mock_request:
        mock_request.return_value = mock_response

        results = await client.monitor_channels(
            ["channel1", "channel2"],
            max_results=1
        )

        assert len(results) == 2
        assert results["channel1"][0]["video_id"] == "video1"
        assert results["channel2"][0]["video_id"] == "video1"


@pytest.mark.asyncio
async def test_youtube_error_handling():
    """Test error handling for API failures"""
    client = YouTubeClient(api_key="test-key")

    with patch.object(client, '_make_request', new_callable=AsyncMock) as mock_request:
        mock_request.side_effect = Exception("API Error")

        with pytest.raises(Exception, match="API Error"):
            await client.get_channel_videos("channel123")


@pytest.mark.asyncio
async def test_youtube_empty_response():
    """Test handling of empty API response"""
    client = YouTubeClient(api_key="test-key")

    mock_response = {"items": []}

    with patch.object(client, '_make_request', new_callable=AsyncMock) as mock_request:
        mock_request.return_value = mock_response

        videos = await client.get_channel_videos("channel123")

        assert videos == []
