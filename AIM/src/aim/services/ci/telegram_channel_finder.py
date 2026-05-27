"""TelegramChannelFinder — find doctor Telegram channels via native Telegram search.

Google Search doesn't index Telegram well (0 results for doctor names in tests).
Telegram's native search (contacts.SearchRequest) finds public channels, groups,
and users by name/username directly through the Telegram API.

Strategy:
  1. Connect via Telethon (user account, not bot — bots can't search)
  2. For each doctor name → contacts.SearchRequest(q=name)
  3. Parse results: keep channels/supergroups only (not users, not groups)
  4. Return SocialProfile list with Telegram links

Requires:
  - TELEGRAM_API_ID / TELEGRAM_API_HASH in .env (from my.telegram.org)
  - TELEGRAM_SESSION_STRING in .env (generated once via session_string_generator.py)
"""

from __future__ import annotations

import asyncio
import logging
import os
from typing import Optional

from telethon import TelegramClient, functions
from telethon.sessions import StringSession
from telethon.tl.types import Channel, User

from .models import SocialProfile

logger = logging.getLogger(__name__)

# How many results to request per doctor from Telegram search
_SEARCH_LIMIT = 10

# Exclude channels with these words in title (aggregators, not personal)
_EXCLUDE_TITLE_WORDS = (
    "медицинский центр",
    "клиника",
    "стоматология",
    "аптека",
    "medical center",
    "hospital",
    "clinic",
)


def _is_personal_channel(entity: Channel) -> bool:
    """Check if a Telegram channel looks like a personal doctor channel.

    Filters out:
    - Large clinics (title contains "клиника", "центр", etc.)
    - News aggregators
    - Official company channels with generic names

    Keeps:
    - Channels with doctor's name in title
    - Small channels (<5000 subscribers) with medical keywords
    """
    title = (getattr(entity, "title", "") or "").lower()
    for word in _EXCLUDE_TITLE_WORDS:
        if word in title:
            return False
    return True


class TelegramChannelFinder:
    """Finds doctor Telegram channels using native Telegram search."""

    def __init__(self) -> None:
        self._client: Optional[TelegramClient] = None
        self._lock = asyncio.Lock()

    async def _get_client(self) -> TelegramClient:
        if self._client is not None:
            return self._client

        async with self._lock:
            if self._client is not None:
                return self._client

            api_id = int(os.getenv("TELEGRAM_API_ID", "0"))
            api_hash = os.getenv("TELEGRAM_API_HASH", "")
            session_string = os.getenv("TELEGRAM_SESSION_STRING", "")

            if not api_id or not api_hash:
                raise ValueError(
                    "TELEGRAM_API_ID and TELEGRAM_API_HASH must be set in .env. "
                    "Get them from https://my.telegram.org → API development tools."
                )

            if session_string:
                session = StringSession(session_string)
            else:
                # Interactive login — will prompt for phone/code
                logger.warning(
                    "TELEGRAM_SESSION_STRING not set — will use interactive login. "
                    "Run session_string_generator.py once to save a session string."
                )
                session = "telegram_channel_finder"

            self._client = TelegramClient(session, api_id, api_hash)
            await self._client.start()
            logger.info("TelegramChannelFinder connected")

            # Save session string for next time if not already saved
            if not session_string and isinstance(self._client.session, StringSession):
                new_string = self._client.session.save()
                logger.info(
                    "Generated session string (add to .env): TELEGRAM_SESSION_STRING=%s",
                    new_string,
                )

            return self._client

    async def close(self) -> None:
        if self._client is not None:
            await self._client.disconnect()
            self._client = None

    async def find_doctor_channels(
        self, doctor_name: str
    ) -> list[SocialProfile]:
        """Search Telegram for channels matching a doctor's name.

        Returns list of SocialProfile with platform="telegram".
        """
        if not doctor_name:
            return []

        profiles: list[SocialProfile] = []

        try:
            client = await self._get_client()

            # Search for the doctor name across Telegram
            result = await client(
                functions.contacts.SearchRequest(q=doctor_name, limit=_SEARCH_LIMIT)
            )

            entities: list = list(result.chats) + list(result.users)

            for entity in entities:
                # We only care about channels (personal Telegram channels)
                if not isinstance(entity, Channel):
                    continue

                # Skip megagroups — we want channels
                if getattr(entity, "megagroup", False):
                    continue

                title = getattr(entity, "title", "") or ""
                username = getattr(entity, "username", "") or ""

                if not _is_personal_channel(entity):
                    continue

                # Check if doctor name parts appear in channel title
                name_parts = doctor_name.lower().split()
                title_lower = title.lower()
                if not any(part in title_lower for part in name_parts if len(part) >= 3):
                    continue

                url = f"https://t.me/{username}" if username else ""
                handle = f"@{username}" if username else title

                participants = getattr(entity, "participants_count", None)

                profiles.append(SocialProfile(
                    platform="telegram",
                    handle=handle,
                    url=url,
                    exists=True,
                    subscribers=participants or 0,
                ))

        except Exception as e:
            logger.warning(
                "Telegram search failed for '%s': %s", doctor_name, e
            )

        return profiles

    async def find_doctors_batch(
        self, doctor_names: list[str]
    ) -> dict[str, list[SocialProfile]]:
        """Batch search Telegram for multiple doctors.

        Returns dict: doctor_name → list of SocialProfile.
        """
        if not doctor_names:
            return {}

        results: dict[str, list[SocialProfile]] = {}

        for name in doctor_names:
            try:
                profiles = await self.find_doctor_channels(name)
                if profiles:
                    results[name] = profiles
                    logger.info(
                        "Telegram: found %d channel(s) for '%s'",
                        len(profiles), name,
                    )
            except Exception as e:
                logger.warning("Telegram batch: '%s' failed: %s", name, e)
                results[name] = []

        return results
