#!/usr/bin/env python3
"""Generate Telegram session string for Telethon user client.

Usage: python3 scripts/generate_telegram_session.py [+79991112233]
"""

import os
import sys
import re
from urllib.parse import urlparse

# Add AIM to path for .env loading
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "AIM", ".env"))

API_ID = int(os.getenv("TELEGRAM_API_ID", "0"))
API_HASH = os.getenv("TELEGRAM_API_HASH", "")

if not API_ID or not API_HASH:
    print("ERROR: TELEGRAM_API_ID and TELEGRAM_API_HASH must be set in AIM/.env")
    sys.exit(1)


def _build_proxy():
    """Build Telethon proxy config from environment variables."""
    raw = os.getenv("TELETHON_PROXY", "")
    if raw:
        m = re.match(r"(\w+)=([^:]+):(\d+)(?::([^:]*):(.*))?", raw)
        if m:
            ptype, host, port = m.group(1), m.group(2), int(m.group(3))
            username = m.group(4) or None
            password = m.group(5) or None
            return (ptype, host, port, True, username, password or None)

    proxy_url = os.getenv("HTTPS_PROXY") or os.getenv("HTTP_PROXY") or os.getenv("ALL_PROXY") or ""
    if not proxy_url:
        return None

    parsed = urlparse(proxy_url)
    ptype = "socks5" if parsed.scheme in ("socks5", "socks5h") else "http"
    host = parsed.hostname or ""
    port = parsed.port or 1080
    username = parsed.username or None
    password = parsed.password or None

    return (ptype, host, port, True, username, password)


async def main():
    proxy = _build_proxy()
    print(f"Proxy: {proxy[0]}://{proxy[1]}:{proxy[2]}" + (f" (auth: {proxy[4]})" if proxy and proxy[4] else " (no auth)") if proxy else "Proxy: NONE (direct connection)")

    # Accept phone from CLI arg
    if len(sys.argv) > 1:
        phone = sys.argv[1].strip()
        print(f"Phone: {phone}")
    else:
        phone = input("Phone number (+7...): ").strip()

    from telethon import TelegramClient
    from telethon.sessions import StringSession

    client = TelegramClient(StringSession(), API_ID, API_HASH, proxy=proxy)
    print("Connecting to Telegram...")
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
