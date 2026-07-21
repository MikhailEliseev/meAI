"""Voice message transcription via AssemblyAI.

Handles:
1. Downloading voice files from Telegram Bot API (via NL proxy)
2. Transcribing OGG audio via AssemblyAI
3. Returning text for the Hermes pipeline

Telegram voice messages arrive as OGG (Opus codec, 16000 Hz mono).
AssemblyAI handles OGG natively — no conversion needed.
"""

import logging
import os
import tempfile
from pathlib import Path
from urllib.parse import urlparse

import httpx

logger = logging.getLogger(__name__)

ASSEMBLYAI_API_KEY = os.getenv("ASSEMBLYAI_API_KEY", "")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_PROXY_URL = os.getenv("TELEGRAM_PROXY_URL", "")
TELEGRAM_PROXY_AUTH = os.getenv("TELEGRAM_PROXY_AUTH", "")


def _get_proxy_url() -> str | None:
    """Build proxy URL for Telegram API calls (NL server workaround)."""
    if TELEGRAM_PROXY_URL and TELEGRAM_PROXY_AUTH:
        parsed = urlparse(TELEGRAM_PROXY_URL)
        host = parsed.netloc or parsed.path
        return f"http://{TELEGRAM_PROXY_AUTH}@{host}"
    return None


def _download_telegram_voice(file_id: str) -> bytes:
    """Download voice file from Telegram Bot API via getFile.

    Flow: getFile(file_id) → file_path → download file bytes.
    All HTTP calls routed through proxy (NL hosting blocks Telegram port 443).
    """
    if not TELEGRAM_BOT_TOKEN:
        raise RuntimeError("TELEGRAM_BOT_TOKEN not set")

    proxy = _get_proxy_url()

    # Step 1: get file_path from Telegram
    get_file_url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/getFile"
    with httpx.Client(timeout=15.0, proxy=proxy) as client:
        resp = client.post(get_file_url, json={"file_id": file_id})
        resp.raise_for_status()
        data = resp.json()

    if not data.get("ok"):
        raise RuntimeError(f"Telegram getFile failed: {data}")

    file_path = data["result"]["file_path"]
    file_size = data["result"].get("file_size", 0)
    logger.info(f"Voice file: {file_path} ({file_size} bytes)")

    # Step 2: download file
    download_url = f"https://api.telegram.org/file/bot{TELEGRAM_BOT_TOKEN}/{file_path}"
    with httpx.Client(timeout=30.0, proxy=proxy) as client:
        resp = client.get(download_url)
        resp.raise_for_status()
        return resp.content


def transcribe_voice(file_id: str) -> str:
    """Download voice message from Telegram and transcribe via AssemblyAI.

    Uses direct HTTP calls with NL proxy (NOT AssemblyAI SDK, which bypasses proxy).
    Returns transcribed text, or empty string on failure.
    Errors are logged but not raised — voice is best-effort.
    """
    if not ASSEMBLYAI_API_KEY:
        logger.error("ASSEMBLYAI_API_KEY not configured — voice messages cannot be transcribed")
        return ""

    try:
        audio_bytes = _download_telegram_voice(file_id)
    except Exception as e:
        logger.error(f"Failed to download voice file {file_id}: {e}")
        return ""

    proxy = _get_proxy_url()
    headers = {"authorization": ASSEMBLYAI_API_KEY}

    try:
        # Step 1: Upload audio to AssemblyAI
        upload_url = "https://api.assemblyai.com/v2/upload"
        with httpx.Client(timeout=60.0, proxy=proxy) as client:
            resp = client.post(upload_url, headers=headers, content=audio_bytes)
            resp.raise_for_status()
            upload_result = resp.json()

        audio_url = upload_result.get("upload_url")
        if not audio_url:
            logger.error(f"AssemblyAI upload failed: {upload_result}")
            return ""

        logger.info(f"Voice uploaded to AssemblyAI: {len(audio_bytes)} bytes")

        # Step 2: Request transcription
        transcript_url = "https://api.assemblyai.com/v2/transcript"
        body = {"audio_url": audio_url, "language_code": "ru"}
        with httpx.Client(timeout=30.0, proxy=proxy) as client:
            resp = client.post(transcript_url, headers=headers, json=body)
            resp.raise_for_status()
            transcript_result = resp.json()

        transcript_id = transcript_result.get("id")
        if not transcript_id:
            logger.error(f"AssemblyAI transcript request failed: {transcript_result}")
            return ""

        # Step 3: Poll for result (max 60 seconds)
        poll_url = f"https://api.assemblyai.com/v2/transcript/{transcript_id}"
        for attempt in range(20):
            import time as time_mod
            time_mod.sleep(3)
            with httpx.Client(timeout=15.0, proxy=proxy) as client:
                resp = client.get(poll_url, headers=headers)
                resp.raise_for_status()
                result = resp.json()

            status = result.get("status")
            if status == "completed":
                text = result.get("text") or ""
                logger.info(f"Voice transcribed: {len(text)} chars")
                return text
            elif status == "error":
                logger.error(f"AssemblyAI transcription error: {result.get('error')}")
                return ""

        logger.error("AssemblyAI transcription timed out after 60s")
        return ""

    except Exception as e:
        logger.error(f"AssemblyAI transcription failed: {e}")
        return ""
