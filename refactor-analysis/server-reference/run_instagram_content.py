"""
run_instagram_content — Hermes tool: Deep Instagram Content Analysis

Fetches Instagram profile data via Apify Instagram Profile Scraper,
then analyses content performance: engagement rate, format breakdown,
content themes, top/flop posts, posting frequency, and content gaps.

Uses Apify actor apify~instagram-profile-scraper with key rotation.
Registered in Hermes internal registry under toolset "aim-operations".
"""

import asyncio
import json
import logging
import os
from collections import Counter
from datetime import datetime, timezone

import httpx

from tools.registry import registry

logger = logging.getLogger(__name__)

REQUEST_TIMEOUT = 180.0
APIFY_BASE = "https://api.apify.com/v2"
ACTOR_ID = "apify~instagram-profile-scraper"
APIFY_KEYS_PATH = "/opt/data/apify_keys.json"


APIFY_KEYS_PATH = "/opt/data/apify_keys.json"


def _load_apify_keys() -> list[str]:
    """Load active Apify API keys from the key bank file."""
    try:
        with open(APIFY_KEYS_PATH) as f:
            data = json.load(f)
        return [k["token"] for k in data.get("keys", []) if k.get("status") == "active"]
    except Exception:
        logger.warning("Cannot load Apify keys from %s", APIFY_KEYS_PATH)
        return []


async def handle_run_instagram_content(handle=None, **kwargs) -> str:
    """Deep Instagram content analysis for a competitor account.

    Fetches profile + 24 latest posts via Apify, computes engagement metrics,
    identifies content themes, top/flop posts, format preferences, and gaps.

    Args:
        handle: Instagram handle WITHOUT @ (e.g., "dr_ivanova")

    Returns:
        JSON with profile stats, content analysis, themes, and content gaps.
    """
    if isinstance(handle, dict):
        handle = handle.get("handle", "")

    if not handle:
        return json.dumps({"error": "handle is required (Instagram username without @)"})

    handle = handle.lstrip("@")
    logger.info("Instagram content analysis for: @%s", handle)

    from app.main import push_tool_progress

    push_tool_progress("instagram", f"Загружаю контент Instagram @{handle} через Apify…")

    keys = _load_apify_keys()
    if not keys:
        return json.dumps({"error": "No active Apify keys available"})

    # Try each key until one works (round-robin)
    profile_data = None
    last_error = None

    for key in keys[:3]:  # max 3 attempts
        try:
            profile_data = await _fetch_instagram_profile(key, handle)
            if profile_data:
                break
        except Exception as e:
            last_error = str(e)
            logger.warning("Apify key failed: %s… — %s", key[:20], e)
            continue

    if not profile_data:
        return json.dumps({
            "error": "Failed to fetch Instagram profile after key rotation",
            "detail": last_error or "All keys exhausted or returned empty data",
        })

    # Analyse the content
    push_tool_progress("instagram", "Анализирую контент: ER, форматы, темы…")

    analysis = _analyse_content(profile_data, handle)

    push_tool_progress(
        "instagram",
        f"✅ Instagram @{handle}: ER={analysis['engagement_rate']:.2f}%, "
        f"{analysis['posts_analyzed']} постов, формат: {analysis['dominant_format']}",
    )

    return json.dumps(analysis, ensure_ascii=False, indent=2)


async def _fetch_instagram_profile(api_key: str, handle: str) -> dict | None:
    """Fetch profile data via Apify Instagram Profile Scraper."""
    async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT) as client:
        # Start the actor run
        start_url = f"{APIFY_BASE}/acts/{ACTOR_ID}/runs?token={api_key}"
        start_resp = await client.post(
            start_url,
            json={"usernames": [handle], "maxPosts": 24},
        )
        start_resp.raise_for_status()
        run_data = start_resp.json()
        run_id = run_data["data"]["id"]
        logger.info("Apify run started: %s for @%s", run_id, handle)

        # Poll until finished (max 120s)
        for attempt in range(24):  # 24 * 5s = 120s max
            await asyncio.sleep(5)
            poll_url = f"{APIFY_BASE}/acts/{ACTOR_ID}/runs/{run_id}?token={api_key}"
            poll_resp = await client.get(poll_url)
            poll_resp.raise_for_status()
            poll_data = poll_resp.json()
            status = poll_data.get("data", {}).get("status")

            if status == "SUCCEEDED":
                break
            elif status in ("FAILED", "ABORTED", "TIMED-OUT"):
                logger.error("Apify run %s: %s", run_id, status)
                return None
        else:
            logger.error("Apify run %s timed out", run_id)
            return None

        # Get dataset items
        dataset_id = poll_data["data"]["defaultDatasetId"]
        dataset_url = f"{APIFY_BASE}/datasets/{dataset_id}/items?token={api_key}"
        dataset_resp = await client.get(dataset_url)
        dataset_resp.raise_for_status()
        items = dataset_resp.json()

        if not items:
            return None
        return items[0]  # first item = profile data


def _analyse_content(profile: dict, handle: str) -> dict:
    """Analyse Instagram profile content: ER, formats, themes, gaps."""
    followers = profile.get("followersCount", 0) or 1
    posts = profile.get("latestPosts") or profile.get("posts") or []

    # Engagement rate
    total_likes = sum(p.get("likesCount", 0) or 0 for p in posts)
    total_comments = sum(p.get("commentsCount", 0) or 0 for p in posts)
    total_views = sum(p.get("videoViewCount", 0) or 0 for p in posts)
    avg_likes = total_likes / len(posts) if posts else 0
    er = (avg_likes / followers * 100) if followers else 0

    # Format breakdown
    format_counter = Counter()
    for p in posts:
        t = p.get("type", "Image")
        format_counter[t] += 1
    total_posts = len(posts)
    formats = {
        fmt: {"count": cnt, "pct": round(cnt / total_posts * 100, 1)}
        for fmt, cnt in format_counter.most_common()
    }
    dominant = format_counter.most_common(1)
    dominant_format = dominant[0][0] if dominant else "Unknown"

    # Posting frequency
    dates = []
    for p in posts:
        ts = p.get("timestamp")
        if ts:
            try:
                dates.append(datetime.fromisoformat(ts.replace("Z", "+00:00")))
            except (ValueError, AttributeError):
                pass

    avg_interval_days = 0
    if len(dates) >= 2:
        dates.sort(reverse=True)
        intervals = [(dates[i] - dates[i + 1]).days for i in range(len(dates) - 1)]
        avg_interval_days = round(sum(intervals) / len(intervals), 1)

    # Top and flop posts
    sorted_by_likes = sorted(
        [p for p in posts if p.get("likesCount")],
        key=lambda p: p.get("likesCount", 0),
        reverse=True,
    )
    top_posts = []
    for p in sorted_by_likes[:3]:
        caption = (p.get("caption") or "")[:150]
        top_posts.append({
            "url": p.get("url", ""),
            "type": p.get("type", "Image"),
            "likes": p.get("likesCount", 0),
            "comments": p.get("commentsCount", 0),
            "views": p.get("videoViewCount"),
            "caption_preview": caption,
        })

    flop_post = None
    if sorted_by_likes:
        worst = sorted_by_likes[-1]
        flop_post = {
            "url": worst.get("url", ""),
            "type": worst.get("type", "Image"),
            "likes": worst.get("likesCount", 0),
            "caption_preview": (worst.get("caption") or "")[:150],
        }

    # Content themes (from captions)
    themes = _extract_content_themes(posts)

    # Content gaps
    gaps = _identify_content_gaps(posts, themes, formats)

    return {
        "handle": handle,
        "profile": {
            "full_name": profile.get("fullName", ""),
            "biography": profile.get("biography", ""),
            "followers": followers,
            "posts_count": profile.get("postsCount", 0),
            "is_business": profile.get("isBusinessAccount", False),
            "category": profile.get("businessCategoryName"),
            "external_url": profile.get("externalUrl"),
        },
        "posts_analyzed": len(posts),
        "engagement_rate": round(er, 2),
        "avg_likes": round(avg_likes, 1),
        "avg_comments": round(total_comments / len(posts), 1) if posts else 0,
        "avg_views": round(total_views / len(posts), 1) if posts else 0,
        "dominant_format": dominant_format,
        "formats": formats,
        "posting_frequency": {
            "avg_interval_days": avg_interval_days,
            "posts_per_week": round(7 / avg_interval_days, 1) if avg_interval_days else 0,
        },
        "content_themes": themes,
        "top_posts": top_posts,
        "flop_post": flop_post,
        "content_gaps": gaps,
    }


def _extract_content_themes(posts: list[dict]) -> list[dict]:
    """Extract content themes from post captions using keyword heuristics."""
    theme_keywords = {
        "До/После результатов": ["до/после", "результат", "до и после", "преображение"],
        "Закулисье / процесс": ["закулисье", "процесс", "как проходит", "на операции"],
        "Экспертный контент": ["совет", "рекомендаци", "важно знать", "разбор", "почему"],
        "Знакомство с врачами": ["врач", "доктор", "специалист", "команда"],
        "Акции и спецпредложения": ["акция", "скидка", "спецпредложение", "подарок"],
        "Отзывы пациентов": ["отзыв", "благодарность", "спасибо", "пациент"],
        "Социальные доказательства": ["сми", "телеканал", "журнал", "награда", "конференция"],
        "Личное / лайфстайл": ["жизнь", "семья", "путешествие", "утро", "выходные"],
    }

    theme_counter = Counter()
    theme_examples = {t: [] for t in theme_keywords}

    for post in posts:
        caption = (post.get("caption") or "").lower()
        for theme, keywords in theme_keywords.items():
            for kw in keywords:
                if kw in caption:
                    theme_counter[theme] += 1
                    if len(theme_examples[theme]) < 2:
                        theme_examples[theme].append((post.get("caption") or "")[:100])
                    break

    return [
        {
            "theme": theme,
            "count": count,
            "pct": round(count / len(posts) * 100, 1) if posts else 0,
        }
        for theme, count in theme_counter.most_common()
    ]


def _identify_content_gaps(
    posts: list[dict], themes: list[dict], formats: dict
) -> list[dict]:
    """Identify content strategy gaps."""
    gaps = []

    # Reels gap
    reel_pct = formats.get("Video", {}).get("pct", 0)
    if reel_pct < 20:
        gaps.append({
            "gap": "Мало Reels/Video",
            "detail": f"Только {reel_pct}% видео-контента — Reels дают в 2-3x больше охвата",
            "severity": "high",
        })

    # Educational content
    has_educational = any(t["theme"] == "Экспертный контент" and t["pct"] >= 10 for t in themes)
    if not has_educational:
        gaps.append({
            "gap": "Нет экспертного контента",
            "detail": "Отсутствуют образовательные посты — это снижает доверие и охваты",
            "severity": "critical",
        })

    # Behind-the-scenes
    has_behind = any(t["theme"] == "Закулисье / процесс" and t["pct"] >= 10 for t in themes)
    if not has_behind:
        gaps.append({
            "gap": "Нет закулисья",
            "detail": "Пациенты выбирают клинику по доверию — покажите процесс изнутри",
            "severity": "medium",
        })

    # Doctor features
    has_doctors = any(t["theme"] == "Знакомство с врачами" and t["pct"] >= 10 for t in themes)
    if not has_doctors:
        gaps.append({
            "gap": "Врачи не в кадре",
            "detail": "Лица врачей — главный фактор доверия. Без них клиника обезличена",
            "severity": "high",
        })

    return gaps


registry.register(
    name="run_instagram_content",
    toolset="aim-operations",
    schema={
        "type": "function",
        "function": {
            "name": "run_instagram_content",
            "description": (
                "Deep Instagram content analysis for a competitor or client account. "
                "Fetches profile + 24 latest posts via Apify, computes engagement rate, "
                "format breakdown (Reels/Carousel/Image), content themes (before-after, "
                "educational, behind-the-scenes, doctor features, etc.), top-3 and "
                "worst-performing posts, posting frequency, and content strategy gaps. "
                "Use this to understand HOW a competitor communicates on Instagram: "
                "what formats work, what themes resonate, what they're missing. "
                "Also works for client self-audit."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "handle": {
                        "type": "string",
                        "description": "[REQUIRED] Instagram username WITHOUT @ (e.g., 'dr_ivanova', 'clinic_name')",
                    },
                },
                "required": ["handle"],
            },
        },
    },
    handler=handle_run_instagram_content,
    check_fn=lambda: True,
    is_async=True,
    description="Deep Instagram content analysis: ER, formats, themes, top/flop posts, content gaps via Apify",
    emoji="📸",
)
