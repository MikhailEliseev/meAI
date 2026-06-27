"""
run_instagram_content — Hermes tool: Deep Instagram Content Analysis (v2)

v2: Perplexity-based analysis. Visits Instagram profile, examines recent posts,
and produces structured analysis: content themes, style, format preferences,
top posts, content gaps, and recommendations.

No Apify dependency. No API keys beyond Perplexity/DeepSeek.
One Perplexity call per handle (~5-8s each).

v1 (deprecated): Apify Instagram Profile Scraper — removed (13 keys dead).
"""

import asyncio
import json
import logging
import os
import re
import time
from collections import Counter

import httpx

from tools.registry import registry

logger = logging.getLogger(__name__)

# ── Perplexity config ─────────────────────────────────────────────
PERPLEXITY_API_KEY = os.getenv("PERPLEXITY_API_KEY", "").strip()
PERPLEXITY_BASE_URL = "https://api.perplexity.ai"
PERPLEXITY_MODEL = "sonar-pro"
USE_PERPLEXITY = bool(PERPLEXITY_API_KEY)

# ── Fallback LLM (DeepSeek) ───────────────────────────────────────
LLM_BASE_URL = os.getenv("LLM_BASE_URL", os.getenv("OMNIROUTE_URL", "https://api.deepseek.com/v1"))
LLM_API_KEY = os.getenv("LLM_API_KEY", os.getenv("OMNIROUTE_AUTH", os.getenv("DEEPSEEK_API_KEY", "")))
LLM_MODEL = os.getenv("LLM_MODEL", "deepseek-chat")

REQUEST_TIMEOUT = 90.0
MAX_TOKENS = 6000


async def handle_run_instagram_content(handle=None, handles=None, **kwargs) -> str:
    """Deep Instagram content analysis via Perplexity for one or multiple accounts.

    Perplexity visits each Instagram profile, examines recent posts (last 20-24),
    and produces structured analysis: content themes, style, format preferences,
    top-performing content, gaps, and strategic recommendations.

    Args:
        handle: Single Instagram handle WITHOUT @ (e.g., "dr_ivanova").
                For backward compatibility. If handles array is provided, this is ignored.
        handles: Array of Instagram handles WITHOUT @. Up to 5 will be analysed.

    Returns:
        JSON with either single profile analysis or aggregated array of analyses.
    """
    # ── Normalize input ──────────────────────────────────────────
    if isinstance(handle, dict):
        if "handles" in handle:
            handles = handle.get("handles")
        handle = handle.get("handle", "")

    if handles and isinstance(handles, str):
        try:
            handles = json.loads(handles)
        except (json.JSONDecodeError, TypeError):
            handles = [h.strip() for h in handles.split(",") if h.strip()]

    targets: list[str] = []
    if handles and isinstance(handles, list):
        targets = [h.lstrip("@").strip() for h in handles if h and isinstance(h, str)]
    elif handle and isinstance(handle, str):
        targets = [handle.lstrip("@").strip()]

    if not targets:
        return json.dumps({"error": "handle or handles is required (Instagram username without @)"})

    targets = targets[:5]
    logger.info("Instagram content analysis (v2 Perplexity) for %d handles: %s", len(targets), targets)

    from app.main import push_tool_progress

    results = []
    errors = []

    for idx, h in enumerate(targets):
        push_tool_progress(
            "instagram",
            f"📸 Анализирую Instagram @{h} ({idx + 1}/{len(targets)}) через Perplexity…",
        )

        try:
            analysis = await _analyze_single_handle(h)
            if analysis:
                results.append(analysis)
                push_tool_progress(
                    "instagram",
                    f"✅ @{h}: {len(analysis.get('content_themes', []))} тем, "
                    f"ER≈{analysis.get('engagement_rate', 'N/A')}, "
                    f"{analysis.get('profile', {}).get('followers', 0)} подписчиков",
                )
            else:
                errors.append({"handle": h, "error": "No analysis produced"})
                push_tool_progress("instagram", f"⚠️ @{h}: не удалось проанализировать")
        except Exception as e:
            logger.warning("Analysis failed for @%s: %s", h, str(e)[:120])
            errors.append({"handle": h, "error": str(e)[:200]})
            push_tool_progress("instagram", f"⚠️ @{h}: ошибка — {str(e)[:80]}")

        # Small delay between handles
        if idx < len(targets) - 1:
            await asyncio.sleep(0.3)

    # ── Build response ───────────────────────────────────────────
    if not results and errors:
        return json.dumps({
            "error": "Failed to analyze any Instagram profiles",
            "detail": errors,
        }, ensure_ascii=False)

    if len(targets) == 1 and results:
        return json.dumps(results[0], ensure_ascii=False, indent=2)

    total_followers = sum(
        r.get("profile", {}).get("followers", 0) for r in results
    )
    top_by_followers = sorted(
        results,
        key=lambda r: r.get("profile", {}).get("followers", 0),
        reverse=True,
    )

    return json.dumps({
        "analyzed_count": len(results),
        "error_count": len(errors),
        "total_followers_all_handles": total_followers,
        "handles_analyzed": [r["handle"] for r in results],
        "handles_failed": [e["handle"] for e in errors],
        "top_by_followers": [
            {
                "handle": r["handle"],
                "followers": r.get("profile", {}).get("followers", 0),
                "full_name": r.get("profile", {}).get("full_name", ""),
            }
            for r in top_by_followers
        ],
        "profiles": results,
    }, ensure_ascii=False, indent=2)

    # Example wow-comment integration (COMMENTED OUT - LLM generates via prompt)
    # To enable manual triggers if LLM needs help, uncomment and customize:
    # from app.main import push_wow_comment  # Lazy import avoids circular dependency
    # if top_by_followers and top_by_followers[0].get("profile", {}).get("followers", 0) > 100000:
    #     top_handle = top_by_followers[0]["handle"]
    #     top_followers = top_by_followers[0]["profile"]["followers"]
    #     push_wow_comment(f"Врач @{top_handle} с {top_followers:,} подписчиков — серьёзное преимущество", "info")


# ═══════════════════════════════════════════════════════════════════════
# Perplexity analysis
# ═══════════════════════════════════════════════════════════════════════

async def _analyze_single_handle(handle: str) -> dict | None:
    """Analyze a single Instagram handle via Perplexity (or fallback LLM)."""
    prompt = _build_analysis_prompt(handle)

    # Try Perplexity first
    if USE_PERPLEXITY:
        answer = await _call_perplexity(prompt)
    else:
        answer = None

    # Fallback to DeepSeek
    if not answer:
        answer = await _call_deepseek(prompt)

    if not answer:
        return None

    return _parse_analysis(answer, handle)


def _build_analysis_prompt(handle: str) -> str:
    """Build Perplexity prompt for Instagram content analysis via web search."""
    return (
        f"Проанализируй Instagram-аккаунт @{handle}.\n"
        f"Используй web search чтобы найти информацию об этом аккаунте: "
        f"поищи на https://www.instagram.com/{handle}/ (открытый профиль), "
        f"а также на сайтах-агрегаторах соцсетей, в кэше Google, "
        f"на сторонних платформах где упоминается этот аккаунт.\n\n"
        "Сначала проведи анализ в свободной форме (текст с секциями, конкретные примеры).\n"
        "Затем в САМОМ КОНЦЕ ответа пришли JSON-блок с ВСЕМИ извлечёнными данными.\n\n"
        "Формат JSON-блока (ОБЯЗАТЕЛЬНО):\n"
        "```json\n"
        "{\n"
        '  "full_name": "полное имя (текст из bio/шапки)",\n'
        '  "bio": "текст bio полностью",\n'
        '  "followers": число,\n'
        '  "posts_count": число,\n'
        '  "category": "категория (врач/клиника/личный блог/бизнес)",\n'
        '  "external_url": "внешняя ссылка или пустая строка",\n'
        '  "content_themes": [\n'
        '    {"theme": "название темы", "count": число, "pct": число}\n'
        '  ],\n'
        '  "dominant_format": "Reels / Image / Carousel",\n'
        '  "formats": {"Video": {"count": число, "pct": число}, "Image": {"count": число, "pct": число}, "Carousel": {"count": число, "pct": число}},\n'
        '  "engagement_rate": число,\n'
        '  "posts_per_week": число,\n'
        '  "top_posts": [{"description": "описание топ-поста"}],\n'
        '  "flop_post": {"description": "описание провального поста"} или null,\n'
        '  "content_gaps": [{"gap": "краткое описание", "detail": "подробно", "severity": "critical/high/medium/low"}],\n'
        '  "recommendations": ["рекомендация 1", "рекомендация 2", ...]\n'
        "}\n"
        "```\n\n"
        "ВАЖНО:\n"
        "- JSON должен быть ПОСЛЕДНИМ в ответе (после свободного текста)\n"
        "- Все текстовые значения на русском\n"
        "- Если данных нет — используй null/0/[]\n"
        "- followers/posts_count: только числа (87K → 87000)\n"
        "- pct (проценты): числа от 0 до 100\n"
        "- content_themes: НЕ МЕНЕЕ 3 тем если есть хоть какие-то данные"
    )


async def _call_perplexity(prompt: str) -> str | None:
    """Call Perplexity API for Instagram analysis."""
    try:
        async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT) as client:
            payload = {
                "model": PERPLEXITY_MODEL,
                "messages": [
                    {
                        "role": "system",
                        "content": (
                            "Ты — эксперт по контент-маркетингу и SMM в медицине. "
                            "Анализируешь Instagram-аккаунты врачей и клиник. "
                            "Отвечай на русском. Будь конкретен: цифры, проценты, примеры. "
                            "В ответе используй маркдаун-заголовки для структуры."
                        ),
                    },
                    {"role": "user", "content": prompt},
                ],
                "max_tokens": MAX_TOKENS,
                "temperature": 0.1,
            }
            resp = await client.post(
                f"{PERPLEXITY_BASE_URL}/chat/completions",
                json=payload,
                headers={
                    "Authorization": f"Bearer {PERPLEXITY_API_KEY}",
                    "Content-Type": "application/json",
                },
            )
            if resp.status_code != 200:
                logger.warning("Perplexity returned %s", resp.status_code)
                return None

            data = resp.json()
            return data["choices"][0]["message"]["content"]
    except Exception as e:
        logger.warning("Perplexity call failed: %s", str(e)[:120])
        return None


async def _call_deepseek(prompt: str) -> str | None:
    """Call DeepSeek (fallback) for Instagram analysis."""
    try:
        async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT) as client:
            payload = {
                "model": LLM_MODEL,
                "messages": [
                    {
                        "role": "system",
                        "content": (
                            "Ты — эксперт по контент-маркетингу и SMM в медицине. "
                            "Анализируешь Instagram-аккаунты врачей и клиник. "
                            "Отвечай на русском. Будь конкретен: цифры, проценты, примеры."
                        ),
                    },
                    {"role": "user", "content": prompt},
                ],
                "max_tokens": MAX_TOKENS,
                "temperature": 0.1,
            }
            resp = await client.post(
                f"{LLM_BASE_URL}/chat/completions",
                json=payload,
                headers={
                    "Authorization": f"Bearer {LLM_API_KEY}",
                    "Content-Type": "application/json",
                },
            )
            if resp.status_code != 200:
                logger.warning("DeepSeek returned %s", resp.status_code)
                return None

            data = resp.json()
            return data["choices"][0]["message"]["content"]
    except Exception as e:
        logger.warning("DeepSeek call failed: %s", str(e)[:120])
        return None


# ═══════════════════════════════════════════════════════════════════════
# Response parsing
# ═══════════════════════════════════════════════════════════════════════

def _strip_markdown(text: str) -> str:
    """Strip markdown formatting and citation references from Perplexity output.
    Keeps newlines intact — they are needed for row-by-row parsing."""
    # Bold/italic markers
    text = re.sub(r'\*{1,3}', '', text)
    text = re.sub(r'_{1,3}', '', text)
    # Citation references like [1][3][6] or [12]
    text = re.sub(r'\[[\d,\s\]]+\]', '', text)
    # Backtick code spans
    text = re.sub(r'`{1,3}', '', text)
    # Collapse horizontal whitespace (spaces, tabs) but NOT newlines
    text = re.sub(r'[^\S\n]+', ' ', text)
    # Remove leading/trailing whitespace per line
    text = '\n'.join(line.strip() for line in text.splitlines())
    return text.strip()


def _parse_analysis(answer: str, handle: str) -> dict:
    """Parse Perplexity's response: extract JSON block, fall back to regex."""
    logger.info("Perplexity analysis for @%s:\n%s", handle, answer[:600])

    base = {
        "handle": handle,
        "profile": {"full_name": "", "biography": "", "followers": 0, "posts_count": 0, "is_business": False, "category": "", "external_url": ""},
        "posts_analyzed": 24,
        "engagement_rate": 0.0,
        "avg_likes": 0,
        "avg_comments": 0,
        "avg_views": 0,
        "dominant_format": "Unknown",
        "formats": {},
        "posting_frequency": {"avg_interval_days": 0, "posts_per_week": 0},
        "content_themes": [],
        "top_posts": [],
        "flop_post": None,
        "content_gaps": [],
        "recommendations": [],
        "raw_analysis": answer[:2000],
    }

    # ── Try JSON extraction first ────────────────────────────────
    json_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', answer, re.DOTALL)
    if not json_match:
        # Try without code fences
        json_match = re.search(r'(\{[^{]*"full_name"[^}]*(?:\{[^}]*\}[^}]*)*\})', answer, re.DOTALL)

    if json_match:
        try:
            data = json.loads(json_match.group(1))
            logger.info("JSON parsed successfully for @%s", handle)
            # Populate profile
            profile = base["profile"]
            profile["full_name"] = str(data.get("full_name", "") or "").strip('«»"\'\s')
            profile["biography"] = str(data.get("bio", "") or "")
            profile["followers"] = _safe_int(data.get("followers", 0))
            profile["posts_count"] = _safe_int(data.get("posts_count", 0))
            cat = str(data.get("category", "") or "")
            profile["category"] = cat
            profile["is_business"] = "бизнес" in cat.lower() or "клиник" in cat.lower()
            profile["external_url"] = str(data.get("external_url", "") or "")

            base["engagement_rate"] = round(_safe_float(data.get("engagement_rate", 0)), 2)
            base["dominant_format"] = str(data.get("dominant_format", "Unknown") or "Unknown")
            base["formats"] = data.get("formats", {}) or {}

            raw_themes = data.get("content_themes", []) or []
            base["content_themes"] = [
                {"theme": str(t.get("theme", "")), "count": _safe_int(t.get("count", 0)), "pct": _safe_float(t.get("pct", 0))}
                for t in raw_themes if t.get("theme")
            ]
            base["content_themes"].sort(key=lambda t: t["count"], reverse=True)

            raw_tops = data.get("top_posts", []) or []
            base["top_posts"] = [
                {"url": "", "type": "Video", "likes": 0, "comments": 0, "views": 0, "caption_preview": str(p.get("description", ""))[:150]}
                for p in raw_tops[:3]
            ]
            flop = data.get("flop_post")
            if flop and isinstance(flop, dict):
                base["flop_post"] = {"url": "", "type": "Image", "likes": 0, "caption_preview": str(flop.get("description", ""))[:150]}

            raw_gaps = data.get("content_gaps", []) or []
            base["content_gaps"] = [
                {"gap": str(g.get("gap", "")), "detail": str(g.get("detail", "")), "severity": str(g.get("severity", "medium"))}
                for g in raw_gaps[:6]
            ]

            recs = data.get("recommendations", []) or []
            base["recommendations"] = [str(r)[:200] for r in recs[:5]]

            ppw = _safe_float(data.get("posts_per_week", 0))
            if ppw:
                base["posting_frequency"] = {"avg_interval_days": round(7 / ppw, 1), "posts_per_week": round(ppw, 1)}

            return base
        except (json.JSONDecodeError, TypeError, KeyError) as e:
            logger.warning("JSON parse failed for @%s: %s, falling back to regex", handle, str(e)[:120])

    # ── Fallback: regex parsing ──────────────────────────────────
    try:
        cleaned = _strip_markdown(answer)
        profile = base["profile"]
        profile["full_name"] = _extract_field(cleaned, r'(?:Полное имя|Имя)[:\s\-\—]*([^\n]+)') or ""
        profile["biography"] = _extract_field(cleaned, r'(?:Биография|Bio|шапк[аи] профиля)[:\s\-\—]*([^\n]+)') or ""
        profile["followers"] = _extract_number(cleaned, r'(?:Подписчик[овиам]*|фолловер[овиам]*|followers)[:\s\-\—]*(?:около|примерно|≈|~)?\s*([\d\s,.KkMm]+)') or _extract_number(cleaned, r'([\d\s,.]+[KkMm]?)\s*(?:подписчик[овиам]*|фолловер[овиам]*|followers)')
        profile["posts_count"] = _extract_number(cleaned, r'(?:Пост[овиам]*|публикаци[йяи]+|posts)[:\s\-\—]*(?:около|примерно|≈|~)?\s*([\d\s,.KkMm]+)')
        profile["category"] = _extract_field(cleaned, r'(?:Категория)[:\s\-\—]*([^\n]+)') or ""
        base["content_themes"] = _extract_themes(cleaned)
        base["formats"] = _extract_formats(cleaned)
        base["dominant_format"] = _dominant_format(base["formats"])
        base["top_posts"] = _extract_top_posts(cleaned)[:3]
        base["flop_post"] = _extract_flop_post(cleaned)
        base["content_gaps"] = _extract_gaps(cleaned)
        base["recommendations"] = _extract_recommendations(cleaned)
    except Exception as e:
        logger.warning("Regex fallback also failed for @%s: %s", handle, str(e)[:120])

    return base


def _safe_int(val) -> int:
    try:
        return int(val)
    except (ValueError, TypeError):
        return 0


def _safe_float(val) -> float:
    try:
        return float(val)
    except (ValueError, TypeError):
        return 0.0


# ── Parsing helpers ──────────────────────────────────────────────────

def _clean_text(text: str) -> str:
    """Strip markdown bold/italic markers and citation references like [1][3]."""
    text = re.sub(r'\*{1,3}', '', text)  # bold/italic
    text = re.sub(r'\[[\d,\s]+\]', '', text)  # citations [1][3]
    text = re.sub(r'\s+', ' ', text)
    return text.strip()


def _extract_field(text: str, pattern: str) -> str | None:
    m = re.search(pattern, text, re.IGNORECASE)
    if not m:
        return None
    return _clean_text(m.group(1))


def _extract_number(text: str, pattern: str) -> int:
    m = re.search(pattern, text, re.IGNORECASE)
    if not m:
        return 0
    raw = _clean_text(m.group(1).replace(",", "").replace(" ", ""))
    # Strip trailing punctuation (. , ; ! etc)
    raw = raw.rstrip(".,;:!?)\"'»")
    # Handle Russian abbreviations: тыс, тысяч, млн, миллион, млрд
    raw_upper = raw.upper()
    if any(raw_upper.endswith(s) for s in ("K", "К")):
        return int(float(raw_upper.replace("K", "").replace("К", "")) * 1000)
    elif any(raw_upper.endswith(s) for s in ("M", "М")):
        return int(float(raw_upper.replace("M", "").replace("М", "")) * 1_000_000)
    elif any(raw_upper.endswith(s) for s in ("B", "B", "Г")):
        return int(float(raw_upper.replace("B", "").replace("B", "").replace("Г", "")) * 1_000_000_000)
    # Russian "тыс"/"тысяч" in the raw value (e.g., "87тыс" after cleanup)
    tys_match = re.match(r'([\d.]+)\s*тыс', raw, re.IGNORECASE)
    if tys_match:
        return int(float(tys_match.group(1)) * 1000)
    mln_match = re.match(r'([\d.]+)\s*млн', raw, re.IGNORECASE)
    if mln_match:
        return int(float(mln_match.group(1)) * 1_000_000)
    try:
        return int(float(raw))
    except (ValueError, TypeError):
        return 0


def _extract_themes(text: str) -> list[dict]:
    """Extract content themes from Perplexity response.

    Looks for patterns like:
    - "Тема: До/После — 8 постов (40%)"
    - "До/После результатов: 8 постов (40%)"
    - "- До/После: 8 (40%)"
    """
    themes = []

    # Find the themes section
    theme_section_match = re.search(
        r'(?:Шаг\s*3|Темы контента|Контент-темы)[:\s\-]*(.*?)(?=Шаг\s*4|##\s*Шаг|Вовлечённость|\Z)',
        text, re.IGNORECASE | re.DOTALL,
    )
    section = theme_section_match.group(1) if theme_section_match else text

    # Match individual theme lines
    # Pattern: "Theme Name: N постов (P%)" or "- Theme Name — N (P%)"
    theme_lines = re.findall(
        r'(?:^|\n)\s*(?:[-•*]\s*)?'
        r'([^:\-\n]{3,60}?)'
        r'\s*[:\-\–—]\s*'
        r'(\d+)\s*(?:пост|post|шт)'
        r'(?:[^(]*\((\d+(?:\.\d+)?)\s*%\))',
        section, re.IGNORECASE,
    )

    for name, count, pct in theme_lines:
        name = _clean_text(name)
        if len(name) < 3:
            continue
        try:
            themes.append({
                "theme": name,
                "count": int(count),
                "pct": float(pct),
            })
        except (ValueError, TypeError):
            continue

    # Sort by count descending
    themes.sort(key=lambda t: t["count"], reverse=True)
    return themes


def _extract_formats(text: str) -> dict:
    """Extract format breakdown from analysis."""
    formats = {}

    format_lines = re.findall(
        r'(Reels?|Видео|Video|Фото|Photo|Карусел[иь]|Carousel)'
        r'[:\s\-\–]*'
        r'(\d+)\s*(?:пост|post|шт)?'
        r'(?:[^(]*\((\d+(?:\.\d+)?)\s*%\))?',
        text, re.IGNORECASE,
    )

    for fmt, count, pct in format_lines:
        key = fmt.capitalize()
        if key in ("Reels", "Reel"):
            key = "Video"
        elif key in ("Фото", "Photo"):
            key = "Image"
        elif key in ("Карусели", "Карусель", "Carousel"):
            key = "Carousel"

        if key not in formats:
            pct_val = float(pct) if pct else 0
            formats[key] = {
                "count": int(count),
                "pct": round(pct_val, 1),
            }

    return formats


def _extract_top_posts(text: str) -> list[dict]:
    """Extract descriptions of top-performing posts."""
    top_section = re.search(
        r'(?:виральн|успешн|топ|лучш|самых популярн).*?'
        r'(.*?)'
        r'(?=провальн|худш|флоп|контент-пробел|шаг\s*[56]|\Z)',
        text, re.IGNORECASE | re.DOTALL,
    )
    if not top_section:
        return []

    posts = []
    # Match numbered or bulleted items describing posts
    items = re.findall(
        r'(?:^|\n)\s*(?:\d+[.)]\s*|[-•]\s*)'
        r'(.{30,300}?)(?=\n\s*(?:\d+[.)]\s*|[-•]\s*)|\Z)',
        top_section.group(1), re.DOTALL,
    )

    for item in items[:3]:
        posts.append({
            "url": "",
            "type": "Video" if "reel" in item.lower() else "Image",
            "likes": 0,
            "comments": 0,
            "views": 0,
            "caption_preview": item.strip()[:150],
        })

    return posts


def _extract_flop_post(text: str) -> dict | None:
    """Extract description of worst-performing post."""
    flop_section = re.search(
        r'(?:провальн|худш|флоп|меньше всего|слабы).*?'
        r'(.*?)'
        r'(?=контент-пробел|шаг\s*6|рекомендац|\Z)',
        text, re.IGNORECASE | re.DOTALL,
    )
    if not flop_section:
        return None

    item = re.search(r'(?:^|\n)\s*(?:[-•]|\d+[.)])\s*(.{30,200})', flop_section.group(1))
    if item:
        return {
            "url": "",
            "type": "Image",
            "likes": 0,
            "caption_preview": item.group(1).strip()[:150],
        }
    return None


def _extract_gaps(text: str) -> list[dict]:
    """Extract content gaps from analysis."""
    gaps = []

    gap_section = re.search(
        r'(?:Шаг\s*6|Контент-пробелы|Пробелы)[:\s\-]*(.*?)(?=Шаг\s*7|Рекомендац|\Z)',
        text, re.IGNORECASE | re.DOTALL,
    )
    section = gap_section.group(1) if gap_section else text

    # Severity keywords
    severity_map = {
        "critical": ["критич", "нет вообщ", "полное отсутств", "critical"],
        "high": ["важн", "значительн", "сильн", "high", "серьёзн"],
        "medium": ["средн", "умерен", "medium", "можно"],
        "low": ["незначительн", "мелк", "low", "косметическ"],
    }

    gap_items = re.findall(
        r'(?:^|\n)\s*(?:[-•]|\d+[.)])\s*(.{30,300}?)(?=\n\s*(?:[-•]|\d+[.)])|\Z)',
        section, re.DOTALL,
    )

    for item in gap_items[:6]:
        item = item.strip()
        severity = "medium"
        item_lower = item.lower()
        for sev, keywords in severity_map.items():
            if any(kw in item_lower for kw in keywords):
                severity = sev
                break

        gaps.append({
            "gap": item[:100],
            "detail": item,
            "severity": severity,
        })

    return gaps


def _extract_recommendations(text: str) -> list[str]:
    """Extract strategic recommendations."""
    rec_section = re.search(
        r'(?:Шаг\s*7|Рекомендаци[и]?)[:\s\-]*(.*?)(?=\Z)',
        text, re.IGNORECASE | re.DOTALL,
    )
    if not rec_section:
        return []

    recs = re.findall(
        r'(?:^|\n)\s*(?:\d+[.)]\s*|[-•]\s*)'
        r'(.{30,300}?)(?=\n\s*(?:\d+[.)]\s*|[-•]\s*)|\Z)',
        rec_section.group(1), re.DOTALL,
    )

    return [r.strip()[:200] for r in recs[:5]]


def _dominant_format(formats: dict) -> str:
    if not formats:
        return "Unknown"
    return max(formats, key=lambda f: formats[f].get("count", 0))


# ═══════════════════════════════════════════════════════════════════════
# Registry
# ═══════════════════════════════════════════════════════════════════════

registry.register(
    name="run_instagram_content",
    toolset="aim-operations",
    schema={
            "name": "run_instagram_content",
            "description": (
                "Deep Instagram content analysis for a competitor or client account. "
                "Uses Perplexity to visit the profile, examine 20-24 recent posts, "
                "and produce structured analysis: content themes with percentages, "
                "style, format breakdown (Reels/Image/Carousel), top/flop posts, "
                "posting frequency, content gaps, and strategic recommendations. "
                "Use this to understand HOW a competitor communicates on Instagram: "
                "what formats work, what themes resonate, what they're missing. "
                "Also works for client self-audit."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "handle": {
                        "type": "string",
                        "description": "Instagram username WITHOUT @ (e.g., 'dr_ivanova'). Use this OR handles array.",
                    },
                    "handles": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Array of Instagram usernames WITHOUT @. Up to 5 will be analysed. Use this to batch-analyze multiple doctors from find_doctor_handles.",
                    },
                },
            },
        },
    handler=handle_run_instagram_content,
    check_fn=lambda: True,
    is_async=True,
    description="Deep Instagram content analysis: themes, style, formats, gaps via Perplexity",
    emoji="📸",
)
