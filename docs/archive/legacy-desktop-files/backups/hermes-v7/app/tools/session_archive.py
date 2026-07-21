"""
session_archive — unified persistence for tool outputs.

Every tool that produces structured data saves it to
/opt/data/sessions-archive/{session_hash}/{key}.json

generate_html_report._load_session_data() then auto-discovers all
.json files and feeds them to the section builders.
"""

import json
import logging
import os
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

SESSIONS_ROOT = os.getenv("SESSIONS_ROOT", "/opt/data/sessions-archive")

# ── File → data key mapping ──────────────────────────────────────────────
# Keys not in this map still load (filename minus .json becomes the key).
DATA_FILE_MAP = {
    "prescan-data.json": "prescan",
    "ci-analysis.json": "ci_analysis",
    "doctor_dossiers.json": "doctor_dossiers",
    "instagram_content.json": "instagram_content",
    "smi_mentions.json": "smi_mentions",
    "pagespeed.json": "pagespeed",
    "review_platforms.json": "review_platforms",
    "financials.json": "financials",
    "seo_audit.json": "seo_audit",
    "content_analysis.json": "content_analysis",
    "content_gaps.json": "content_gaps",
    "ads_intelligence.json": "ads_intelligence",
    "hh_analysis.json": "hh_analysis",
    "web_search.json": "web_search",
    "competitors.json": "competitors",
    "competitor_financials.json": "competitor_financials",
    "validation.json": "validation",
}


def _session_dir(session_hash: str) -> str:
    return os.path.join(SESSIONS_ROOT, session_hash)


def ensure_session_dir(session_hash: str) -> str:
    d = _session_dir(session_hash)
    os.makedirs(d, exist_ok=True)
    return d


def save_tool_output(session_hash: str, key: str, data: dict | list) -> str:
    """Save a tool's output to the session archive.

    Returns the file path written.
    """
    ensure_session_dir(session_hash)
    path = os.path.join(_session_dir(session_hash), f"{key}.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    logger.info("Saved %s.json → %s (%d keys)", key, session_hash, len(data) if isinstance(data, dict) else len(data))
    return path


def load_tool_output(session_hash: str, key: str) -> dict | list | None:
    """Load a single tool output from the session archive."""
    path = os.path.join(_session_dir(session_hash), f"{key}.json")
    if not os.path.exists(path):
        return None
    try:
        with open(path, "r") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError) as e:
        logger.warning("Failed to read %s: %s", path, e)
        return None


def load_all_data(session_hash: str) -> dict:
    """Load all available data files from a session archive directory.

    Auto-discovers every .json file. Files named {key}.json become data[key].
    The DATA_FILE_MAP handles special cases (e.g. prescan-data.json → prescan).
    """
    data = {
        "session_hash": session_hash,
        "metadata": {},
        "prescan": {},
        "ci_analysis": {},
    }

    session_dir = _session_dir(session_hash)
    if not os.path.isdir(session_dir):
        logger.warning("Session directory not found: %s", session_dir)
        return data

    # metadata.json
    meta_path = os.path.join(session_dir, "metadata.json")
    if os.path.exists(meta_path):
        try:
            with open(meta_path, "r") as f:
                data["metadata"] = json.load(f)
        except (json.JSONDecodeError, OSError) as e:
            logger.warning("Failed to read metadata.json: %s", e)

    # Auto-discover all .json files
    for fname in sorted(os.listdir(session_dir)):
        if not fname.endswith(".json"):
            continue
        if fname == "metadata.json":
            continue  # already loaded

        path = os.path.join(session_dir, fname)

        # Use explicit mapping if available, otherwise strip .json
        key = DATA_FILE_MAP.get(fname, fname[:-5])

        try:
            with open(path, "r") as f:
                data[key] = json.load(f)
            logger.debug("Loaded %s → data[%s]", fname, key)
        except (json.JSONDecodeError, OSError) as e:
            logger.warning("Failed to read %s: %s", fname, e)

    return data


def upsert_metadata(session_hash: str, **fields) -> dict:
    """Create or update metadata.json with the given fields."""
    ensure_session_dir(session_hash)
    meta_path = os.path.join(_session_dir(session_hash), "metadata.json")
    meta = {}
    if os.path.exists(meta_path):
        try:
            with open(meta_path, "r") as f:
                meta = json.load(f)
        except (json.JSONDecodeError, OSError):
            pass
    meta.update(fields)
    meta.setdefault("session_hash", session_hash)
    meta.setdefault("updated_at", datetime.now(timezone.utc).isoformat())
    with open(meta_path, "w", encoding="utf-8") as f:
        json.dump(meta, f, ensure_ascii=False, indent=2)
    return meta
