"""Session Archive API — serves archived chat sessions by hash.

GET /api/session/{hash} — returns session data in JSON format
"""

import json
import logging
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, HTTPException, status
from fastapi.responses import JSONResponse

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/session", tags=["session"])

SESSIONS_ROOT = Path("/opt/data/sessions-archive")


def _validate_hash(hash_str: str) -> bool:
    """Validate session hash format (8 hex chars)."""
    return bool(len(hash_str) == 8 and all(c in "0123456789abcdef" for c in hash_str))


def _load_session_data(session_hash: str) -> Optional[dict]:
    """Load session data from archive directory."""
    if not _validate_hash(session_hash):
        return None

    session_dir = SESSIONS_ROOT / session_hash
    if not session_dir.exists() or not session_dir.is_dir():
        return None

    data = {}

    # Load metadata
    metadata_file = session_dir / "metadata.json"
    if metadata_file.exists():
        try:
            with open(metadata_file, "r", encoding="utf-8") as f:
                data["metadata"] = json.load(f)
        except Exception as e:
            logger.warning(f"Failed to load metadata for {session_hash}: {e}")
            data["metadata"] = {}

    # Load conversation markdown
    conversation_md = session_dir / "conversation.md"
    if conversation_md.exists():
        try:
            with open(conversation_md, "r", encoding="utf-8") as f:
                data["conversation_markdown"] = f.read()
        except Exception as e:
            logger.warning(f"Failed to load conversation.md for {session_hash}: {e}")
            data["conversation_markdown"] = ""

    # Load conversation JSON (full history)
    conversation_json = session_dir / "conversation.json"
    if conversation_json.exists():
        try:
            with open(conversation_json, "r", encoding="utf-8") as f:
                data["conversation_json"] = json.load(f)
        except Exception as e:
            logger.warning(f"Failed to load conversation.json for {session_hash}: {e}")

    # Load prescan data if available
    prescan_file = session_dir / "prescan-data.json"
    if prescan_file.exists():
        try:
            with open(prescan_file, "r", encoding="utf-8") as f:
                data["prescan_data"] = json.load(f)
        except Exception as e:
            logger.warning(f"Failed to load prescan-data.json for {session_hash}: {e}")

    # Load CI analysis if available
    ci_file = session_dir / "ci-analysis.json"
    if ci_file.exists():
        try:
            with open(ci_file, "r", encoding="utf-8") as f:
                data["ci_analysis"] = json.load(f)
        except Exception as e:
            logger.warning(f"Failed to load ci-analysis.json for {session_hash}: {e}")

    return data if data else None


@router.get("/{session_hash}")
async def get_session(session_hash: str):
    """Retrieve archived session data by hash.

    Returns JSON with:
    - metadata: client info, timestamps
    - conversation_markdown: human-readable chat transcript
    - conversation_json: full message history
    - prescan_data: if prescan was run
    - ci_analysis: if CI analysis was run
    """
    if not _validate_hash(session_hash):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid session hash format (expected 8 hex chars)"
        )

    session_data = _load_session_data(session_hash)

    if not session_data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Session {session_hash} not found"
        )

    return JSONResponse(content=session_data)
