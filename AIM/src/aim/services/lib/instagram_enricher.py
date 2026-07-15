"""Instagram enrichment for competitor pipeline via SearXNG.

Finds Instagram accounts and extracts follower counts from search engine
snippets. This works because Google/Bing/DuckDuckGo index Instagram profile
meta-descriptions which contain follower counts (e.g. "175K Followers, 267
Following, 5,325 Posts").

Why SearXNG (not Apify/Firecrawl/website-scraping):
  - Instagram is legally restricted in Russia → clinics cannot link to it
    from their websites, so website scraping finds nothing
  - Apify instagram-profile-scraper works but polling adds 100-200s latency
  - Firecrawl explicitly blocks instagram.com
  - SearXNG aggregates Google/Bing/DDG → snippets already contain the data

Pipeline:
  1. SearXNG search: "instagram <brand> <city>"
  2. Extract handle from instagram.com/<handle> URLs in results
  3. Extract followers from snippet text ("31K Followers", "175K followers")
"""

import asyncio
import logging
import re
from typing import Optional

from src.aim.services.lib.searxng_client import searxng_search
from src.aim.services.rusprofile.models import CompetitorMatch

logger = logging.getLogger(__name__)

# Patterns for extracting data from search snippets
_IG_URL_PATTERN = re.compile(r"instagram\.com/([a-zA-Z0-9_.]+)", re.I)
_FOLLOWERS_PATTERN = re.compile(
    r"([\d.,]+)\s*([KMkmМм]?)\s*(?:Followers|followers|подписчиков|подписчика)",
    re.I,
)
# Russian "тыс" / "млн" suffixes
_RU_NUM_SUFFIX = {"тыс": 1_000, "тыс.": 1_000, "млн": 1_000_000, "млн.": 1_000_000}


def _parse_followers(text: str) -> Optional[int]:
    """Extract follower count from a search snippet text.

    Handles formats like:
      "175K Followers" → 175000
      "31K followers" → 31000
      "5,325 Followers" → 5
      "30K Followers" → 30000
    """
    match = _FOLLOWERS_PATTERN.search(text)
    if not match:
        return None

    num_str = match.group(1).replace(",", ".")
    suffix = match.group(2).upper()

    try:
        num = float(num_str)
    except ValueError:
        return None

    if suffix in ("K", "К"):
        num *= 1_000
    elif suffix in ("M", "М"):
        num *= 1_000_000

    return int(num)


def _extract_handle_from_url(url: str) -> Optional[str]:
    """Extract Instagram handle from a URL like instagram.com/<handle>."""
    match = _IG_URL_PATTERN.search(url)
    if not match:
        return None
    handle = match.group(1).lower()
    # Skip non-profile paths
    if handle in ("p", "reel", "reels", "explore", "accounts", "stories"):
        return None
    # Skip handles that look like domains (iphk.ru, clinic.com) — real IG
    # handles rarely have domain-like patterns with TLDs
    if "." in handle and any(handle.endswith(tld) for tld in (".ru", ".com", ".org", ".net")):
        return None
    return handle


def _score_profile_result(title: str, content: str, url: str, brand: str) -> int:
    """Score how likely a search result is the brand's main IG profile.

    Higher = more likely. Considers: has followers count, title contains
    brand name, URL is a profile (not a post/reel).
    """
    score = 0
    text = f"{title} {content}".lower()
    brand_lower = brand.lower()

    # Brand name in title or content
    if brand_lower in title.lower():
        score += 3
    if brand_lower in content.lower():
        score += 1

    # Has followers info
    if _FOLLOWERS_PATTERN.search(text):
        score += 2

    # Is a profile page (not /p/, /reel/, /explore/)
    if "/p/" not in url and "/reel/" not in url and "/explore/" not in url:
        score += 1

    return score


async def get_instagram_via_searxng(
    brand_name: str,
    city: str,
) -> tuple[Optional[str], Optional[int]]:
    """Find Instagram handle + follower count via SearXNG.

    Args:
        brand_name: Clinic brand name (e.g. "Фрау Клиник").
        city: City for disambiguation (e.g. "Москва").

    Returns:
        Tuple of (handle, followers). Either or both may be None.
    """
    query = f"instagram {brand_name}"
    if city:
        query += f" {city}"

    results = await searxng_search(query, limit=10)
    if not results:
        return None, None

    # Filter to Instagram results only
    ig_results = []
    for r in results:
        url = r.get("url", "")
        if "instagram.com/" not in url:
            continue
        ig_results.append(r)

    if not ig_results:
        return None, None

    # Score and rank — prefer the brand's main profile with followers info
    scored = []
    for r in ig_results:
        title = r.get("title", "")
        content = r.get("content", "") or ""
        url = r.get("url", "")
        score = _score_profile_result(title, content, url, brand_name)
        scored.append((score, r))

    scored.sort(key=lambda x: x[0], reverse=True)

    # Try top results until we find one with a handle
    best_handle = None
    best_followers = None

    for score, r in scored[:3]:
        url = r.get("url", "")
        content = r.get("content", "") or ""
        title = r.get("title", "")
        combined = f"{title} {content}"

        handle = _extract_handle_from_url(url)
        if not handle:
            continue

        if best_handle is None:
            best_handle = handle

        followers = _parse_followers(combined)
        if followers and best_followers is None:
            best_followers = followers
            # Prefer a result that has BOTH handle and followers
            if best_handle == handle:
                break

    return best_handle, best_followers


async def enrich_instagram_batch(
    competitors: list[CompetitorMatch],
    max_count: int = 5,
    city: str = "",
    use_apify_fallback: bool = True,
) -> None:
    """Enrich top-N competitors with Instagram data.

    Цепочка источников: SearXNG → Firecrawl search → Apify.
    Каждый инструмент пробует если предыдущий не дал результата.

    SearXNG: быстрый (~3с), но мёртвый движками → часто None.
    Firecrawl search: находит IG handle, но не подписчиков.
    Apify: точные followersCount + postsCount, но ~5-10с на профиль.

    Modifies competitors in place. Non-blocking on failure.
    """
    if not competitors:
        return

    targets = competitors[:max_count]
    semaphore = asyncio.Semaphore(3)

    async def _enrich_one(comp: CompetitorMatch) -> None:
        async with semaphore:
            brand = comp.profile.brand_name or comp.profile.legal_name or ""
            if not brand:
                return

            # Источник 1: SearXNG (быстрый, но ненадёжный)
            handle, followers = await get_instagram_via_searxng(brand, city)

            # Источник 2: Firecrawl search (если SearXNG не нашёл handle)
            if not handle:
                try:
                    from src.aim.services.lib.firecrawl_enricher import search_instagram_handle
                    handle = await search_instagram_handle(brand, city)
                except Exception:
                    pass

            # Источник 3: Apify (если handle найден, но нет followers; или вообще ничего)
            if use_apify_fallback and handle:
                # Если handle есть, но followers нет → Apify для точных данных
                if followers is None:
                    try:
                        apify_result = await _get_instagram_via_apify(handle)
                        if apify_result:
                            followers = apify_result.get("followers")
                            posts = apify_result.get("posts")
                            if posts is not None:
                                comp.profile.social_links["instagram_posts"] = str(posts)
                    except Exception as e:
                        logger.debug("Apify IG fallback failed for %s: %s", brand, str(e)[:60])
            elif use_apify_fallback and not handle:
                # Нет handle вообще → пробуем Apify по названию бренда
                try:
                    from src.aim.services.lib.firecrawl_enricher import search_instagram_handle
                    handle2 = await search_instagram_handle(brand, city)
                    if handle2:
                        handle = handle2
                        apify_result = await _get_instagram_via_apify(handle)
                        if apify_result:
                            followers = apify_result.get("followers")
                            posts = apify_result.get("posts")
                            if posts is not None:
                                comp.profile.social_links["instagram_posts"] = str(posts)
                except Exception:
                    pass

            if handle:
                comp.profile.social_links["instagram"] = f"@{handle}"
                if followers is not None:
                    comp.profile.social_links["instagram_followers"] = str(followers)
                    comp.match_reason += f", Instagram: {followers:,} подписчиков"
                    logger.info(
                        "instagram_enriched: %s @%s %s followers",
                        brand, handle, f"{followers:,}",
                    )
                else:
                    comp.match_reason += f", Instagram: @{handle}"
                    logger.info("instagram_handle_only: %s @%s", brand, handle)
            else:
                logger.debug("instagram_not_found: %s", brand)

    await asyncio.gather(
        *[_enrich_one(c) for c in targets],
        return_exceptions=True,
    )


async def _get_instagram_via_apify(handle: str) -> dict | None:
    """Получает Instagram профиль через Apify instagram-profile-scraper.

    Returns:
        {"followers": int, "posts": int} или None.
    """
    try:
        from src.aim.services import get_apify_client
        client = get_apify_client()
        run = await client.call_actor(
            actor_id="apify~instagram-profile-scraper",
            run_input={"usernames": [handle], "resultsLimit": 1},
        )
        items = await client.get_dataset_items(run.default_dataset_id)
        if items and isinstance(items, list) and items[0]:
            p = items[0]
            return {
                "followers": p.get("followersCount"),
                "posts": p.get("postsCount"),
            }
    except Exception as e:
        logger.debug("Apify IG failed for @%s: %s", handle, str(e)[:80])
    return None
