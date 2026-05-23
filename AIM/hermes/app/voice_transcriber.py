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

    try:
        import assemblyai as aai

        aai.settings.api_key = ASSEMBLYAI_API_KEY

        # Write to temp file — AssemblyAI SDK needs a file path
        with tempfile.NamedTemporaryFile(suffix=".ogg", delete=False) as tmp:
            tmp.write(audio_bytes)
            tmp_path = tmp.name

        try:
            transcriber = aai.Transcriber()
            transcript = transcriber.transcribe(tmp_path)

            if transcript.status == aai.TranscriptStatus.error:
                logger.error(f"AssemblyAI transcription error: {transcript.error}")
                return ""

            text = transcript.text or ""
            logger.info(f"Voice transcribed: {len(text)} chars")
            return text

        finally:
            Path(tmp_path).unlink(missing_ok=True)

    except ImportError:
        logger.error("assemblyai package not installed — run: pip install assemblyai")
        return ""
    except Exception as e:
        logger.error(f"AssemblyAI transcription failed: {e}")
        return ""
