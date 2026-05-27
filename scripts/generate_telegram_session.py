#!/usr/bin/env python3
"""Generate Telegram session string for Telethon user client.

Usage: python3 scripts/generate_telegram_session.py
"""

import os
import sys

# Add AIM to path for .env loading
sys.path.insert(0, ".")
from dotenv import load_dotenv

load_dotenv("AIM/.env")

from telethon import TelegramClient
from telethon.sessions import StringSession

API_ID = int(os.getenv("TELEGRAM_API_ID", "0"))
API_HASH = os.getenv("TELEGRAM_API_HASH", "")

if not API_ID or not API_HASH:
    print("ERROR: TELEGRAM_API_ID and TELEGRAM_API_HASH must be set in AIM/.env")
    sys.exit(1)

async def main():
    phone = input("Phone number (+7...): ").strip()

    client = TelegramClient(StringSession(), API_ID, API_HASH)
    await client.start(phone=phone)

    session_string = client.session.save()
    print("\n" + "=" * 60)
    print("SESSION STRING (add to AIM/.env → TELEGRAM_SESSION_STRING):")
    print("=" * 60)
    print(session_string)
    print("=" * 60)

    me = await client.get_me()
    print(f"\nLogged in as: {me.first_name} (@{me.username})")

    await client.disconnect()

import asyncio
asyncio.run(main())
