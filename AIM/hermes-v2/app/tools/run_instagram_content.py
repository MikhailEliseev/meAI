"""Instagram-тул через Apify (перенос из старого hermes, упрощённый).

Actor: apify~instagram-profile-scraper. Ротация ключей из /opt/data/apify_keys.json.
"""
import asyncio
import json
import logging
from collections import Counter

import httpx

from app.lib.apify_client import APIFY_BASE, ACTOR_ID, REQUEST_TIMEOUT, load_apify_keys
from app.tools.registry import register

logger = logging.getLogger(__name__)


def _normalize_handle(handle) -> str:
    if isinstance(handle, dict):
        handle = handle.get("handle", "")
    return str(handle).lstrip("@")


async def _fetch_instagram_profile(api_key: str, handle: str) -> dict | None:
    """Apify: start run → poll → dataset items."""
    async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT) as client:
        start_url = f"{APIFY_BASE}/acts/{ACTOR_ID}/runs?token={api_key}"
        start_resp = await client.post(start_url, json={"usernames": [handle], "maxPosts": 24})
        start_resp.raise_for_status()
        run_id = start_resp.json()["data"]["id"]
        logger.info("apify run started: %s for @%s", run_id, handle)

        poll_data = None
        for _ in range(24):  # 24 × 5с = 120с max
            await asyncio.sleep(5)
            poll_resp = await client.get(f"{APIFY_BASE}/acts/{ACTOR_ID}/runs/{run_id}?token={api_key}")
            poll_resp.raise_for_status()
            poll_data = poll_resp.json()
            status = poll_data.get("data", {}).get("status")
            if status == "SUCCEEDED":
                break
            if status in ("FAILED", "ABORTED", "TIMED-OUT"):
                return None
        else:
            return None

        dataset_id = poll_data["data"]["defaultDatasetId"]
        items = (await client.get(f"{APIFY_BASE}/datasets/{dataset_id}/items?token={api_key}")).json()
        return items[0] if items else None


def _analyse_content(profile: dict, handle: str) -> dict:
    """Анализ профиля: ER, форматы, топ-посты."""
    followers = profile.get("followersCount", 0) or 1
    posts = profile.get("latestPosts") or profile.get("posts") or []

    total_likes = sum(p.get("likesCount", 0) or 0 for p in posts)
    avg_likes = total_likes / len(posts) if posts else 0
    er = (avg_likes / followers * 100) if followers else 0

    fmt_counter = Counter(p.get("type", "Image") for p in posts)
    dominant = fmt_counter.most_common(1)
    return {
        "handle": handle,
        "followers": followers,
        "posts_analyzed": len(posts),
        "engagement_rate": round(er, 2),
        "avg_likes": round(avg_likes),
        "dominant_format": dominant[0][0] if dominant else "Unknown",
        "format_breakdown": dict(fmt_counter),
        "bio": profile.get("bio", "")[:200],
    }


async def handle_run_instagram_content(handle=None, **kwargs) -> str:
    """Анализ Instagram-аккаунта через Apify."""
    handle = _normalize_handle(handle)
    if not handle:
        return json.dumps({"error": "handle is required (Instagram username without @)"})

    keys = load_apify_keys()
    if not keys:
        return json.dumps({"error": "No active Apify keys available"})

    profile = None
    last_error = None
    for key in keys[:3]:
        try:
            profile = await _fetch_instagram_profile(key, handle)
            if profile:
                break
        except Exception as e:
            last_error = str(e)
            logger.warning("apify key failed: %s… — %s", key[:20], e)

    if not profile:
        return json.dumps({"error": "failed to fetch profile", "detail": last_error})

    analysis = _analyse_content(profile, handle)
    logger.info("instagram OK: @%s ER=%.2f%%", handle, analysis["engagement_rate"])
    return json.dumps(analysis, ensure_ascii=False, indent=2)


register(
    name="run_instagram_content",
    schema={
        "type": "function",
        "function": {
            "name": "run_instagram_content",
            "description": (
                "Анализ Instagram-аккаунта: ER (engagement rate), подписчики, "
                "форматы контента (Reels/Photo/Video), средние лайки. "
                "ВЫЗЫВАЙ когда клиент попросил 'проверить соцсети' или дал Instagram-аккаунт. "
                "Параметр handle — username БЕЗ @."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "handle": {"type": "string", "description": "Instagram username без @ (например 'dr_ivanova')"},
                },
                "required": ["handle"],
            },
        },
    },
    handler=handle_run_instagram_content,
)
