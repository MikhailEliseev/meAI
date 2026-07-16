"""YouTube API client for channel monitoring and transcript extraction"""

import asyncio
import httpx
from typing import Any
from youtube_transcript_api import YouTubeTranscriptApi


class YouTubeClient:
    """Async YouTube API client for video content monitoring

    Uses YouTube Data API v3 for channel monitoring and
    youtube-transcript-api for transcript extraction.
    """

    def __init__(self, api_key: str):
        """Initialize YouTube client

        Args:
            api_key: YouTube Data API v3 key
        """
        self.api_key = api_key
        self.base_url = "https://www.googleapis.com/youtube/v3"

    async def get_channel_videos(
        self, channel_id: str, max_results: int = 10
    ) -> list[dict[str, Any]]:
        """Get recent videos from a channel

        Args:
            channel_id: YouTube channel ID
            max_results: Maximum number of videos to return

        Returns:
            List of video dictionaries with video_id, title, description, published_at
        """
        response = await self._make_request(
            "search",
            {
                "part": "snippet",
                "channelId": channel_id,
                "maxResults": max_results,
                "order": "date",
                "type": "video",
            },
        )

        videos = []
        for item in response.get("items", []):
            videos.append(
                {
                    "video_id": item["id"]["videoId"],
                    "title": item["snippet"]["title"],
                    "description": item["snippet"]["description"],
                    "published_at": item["snippet"]["publishedAt"],
                }
            )

        return videos

    async def get_video_transcript(self, video_id: str) -> str:
        """Extract transcript from a video

        Args:
            video_id: YouTube video ID

        Returns:
            Full transcript text
        """
        # Run in executor to avoid blocking
        loop = asyncio.get_event_loop()
        transcript_list = await loop.run_in_executor(
            None, YouTubeTranscriptApi.fetch, video_id
        )

        # Combine all text segments
        transcript = " ".join([entry["text"] for entry in transcript_list])
        return transcript

    async def monitor_channels(
        self, channel_ids: list[str], max_results: int = 10
    ) -> dict[str, list[dict[str, Any]]]:
        """Monitor multiple channels for new videos

        Args:
            channel_ids: List of YouTube channel IDs
            max_results: Maximum videos per channel

        Returns:
            Dictionary mapping channel_id to list of videos
        """
        results = {}

        # Fetch videos from all channels concurrently
        tasks = [
            self.get_channel_videos(channel_id, max_results)
            for channel_id in channel_ids
        ]
        videos_lists = await asyncio.gather(*tasks)

        # Map results to channel IDs
        for channel_id, videos in zip(channel_ids, videos_lists):
            results[channel_id] = videos

        return results

    async def _make_request(
        self, endpoint: str, params: dict[str, Any]
    ) -> dict[str, Any]:
        """Make API request to YouTube

        Args:
            endpoint: API endpoint (e.g., 'search', 'videos')
            params: Query parameters

        Returns:
            API response
        """
        params["key"] = self.api_key

        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/{endpoint}",
                params=params,
                timeout=30.0,
            )
            response.raise_for_status()
            return response.json()
